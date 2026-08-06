from typing import Literal
from pydantic import BaseModel


class ComputeRequest(BaseModel):
    column: str
    # Literal means an unsupported operation is rejected with a 422
    # before it ever reaches compute_service -- one less check the
    # service layer needs to make itself.
    operation: Literal["min", "max", "sum"]


class ComputeResponse(BaseModel):
    column: str
    operation: str
    result: float
    values_considered: int
    values_skipped: int


class PlotPoint(BaseModel):
    x: str | float | int | None
    y: str | float | int | None


class PlotResponse(BaseModel):
    col1: str
    col2: str
    points: list[PlotPoint]