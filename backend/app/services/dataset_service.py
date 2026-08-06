"""
Shared dataset-lookup logic used by both the datasets router (upload/
list/preview/delete) and the analytics router (compute/plot). Living
here -- not in either router -- means neither router imports from the
other; both just import this service, keeping routers as a flat outer
layer instead of a dependency chain between them.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User, Dataset


def get_owned_dataset_or_404(dataset_id: int, user: User, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    # 404 (not 403) for datasets owned by someone else -- don't confirm
    # to the caller that the id exists at all.
    if dataset is None or dataset.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return dataset