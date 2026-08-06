from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.api import auth, datasets, analytics

# Table creation on startup, same shortcut as the Flask version --
# no Alembic migration step needed at this scope. In a real production
# app you'd swap this for `alembic upgrade head` run separately.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataBoard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to a real origin allowlist in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}