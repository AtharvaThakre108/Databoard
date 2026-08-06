from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, Dataset
from app.schemas.analytics import ComputeRequest, ComputeResponse, PlotResponse
from app.services.compute_service import compute_stat, ComputeError
from app.services.plot_service import build_plot_points, PlotError
from app.services.dataset_service import get_owned_dataset_or_404

router = APIRouter(prefix="/dataset", tags=["analytics"])

@router.post("/{dataset_id}/compute", response_model=ComputeResponse)
def compute(
    dataset_id: int,
    body: ComputeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = get_owned_dataset_or_404(dataset_id, user, db)
    try:
        return compute_stat(dataset.rows, dataset.columns, body.column, body.operation)
    except ComputeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{dataset_id}/plot", response_model=PlotResponse)
def plot(
    dataset_id: int,
    col1: str = Query(...),
    col2: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = get_owned_dataset_or_404(dataset_id, user, db)
    try:
        points = build_plot_points(dataset.rows, dataset.columns, col1, col2)
    except PlotError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PlotResponse(col1=col1, col2=col2, points=points)