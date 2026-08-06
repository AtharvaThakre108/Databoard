import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Dataset
from app.schemas.dataset import (
    DatasetSummary,
    DatasetListResponse,
    DatasetPreview,
    DeleteResponse,
)
from app.services.csv_service import parse_csv
from app.services.dataset_service import get_owned_dataset_or_404

router = APIRouter(prefix="/dataset", tags=["datasets"])

@router.post("", response_model=DatasetSummary, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="A dataset 'name' is required.")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    raw = await file.read()
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large (25MB max).")

    columns, rows = parse_csv(raw)
    if not columns:
        raise HTTPException(status_code=400, detail="CSV appears to have no header row.")

    # Store the raw file too, namespaced by uuid so two uploads named
    # "data.csv" never collide on disk.
    stored_filename = f"{uuid.uuid4().hex}_{file.filename}"
    os.makedirs(settings.upload_folder, exist_ok=True)
    with open(os.path.join(settings.upload_folder, stored_filename), "wb") as f:
        f.write(raw)

    dataset = Dataset(
        name=name,
        filename=stored_filename,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        user_id=user.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    page: int = 1,
    limit: int = settings.default_page_size,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    limit = max(1, min(limit, settings.max_page_size))

    query = db.query(Dataset).filter(Dataset.user_id == user.id).order_by(
        Dataset.created_at.desc()
    )
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()

    return DatasetListResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        total_pages=(total + limit - 1) // limit if limit else 0,
    )


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
def preview_dataset(dataset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dataset = get_owned_dataset_or_404(dataset_id, user, db)
    n = 25
    return DatasetPreview(
        columns=dataset.columns,
        rows=dataset.rows[:n],
        row_count=dataset.row_count,
        previewed=min(n, dataset.row_count),
    )


@router.delete("/{dataset_id}", response_model=DeleteResponse)
def delete_dataset(dataset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    dataset = get_owned_dataset_or_404(dataset_id, user, db)

    file_path = os.path.join(settings.upload_folder, dataset.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(dataset)
    db.commit()
    return DeleteResponse(deleted=dataset_id)