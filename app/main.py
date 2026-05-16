from collections.abc import Sequence

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.artic_client import ArticAPIError, ArtworkNotFoundError, fetch_artwork
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import Project, ProjectPlace
from app.schemas import PlaceCreate, PlaceResponse, PlaceUpdate, ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import (
    apply_project_updates,
    build_project_place,
    create_project_entity,
    ensure_no_duplicate_place,
    ensure_project_place_limit,
    get_project_or_404,
    get_project_place_or_404,
    recalculate_project_completion,
)


Base.metadata.create_all(bind=engine)
settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    description="Manage travel projects and planned places backed by the Art Institute of Chicago API.",
    version=settings.APP_VERSION,
)


def artic_exception_to_http(exc: Exception) -> HTTPException:
    if isinstance(exc, ArtworkNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Art Institute API is unavailable.",
    )


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["projects"])
async def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = create_project_entity(project_in)
    db.add(project)
    db.flush()

    artwork_payloads = []
    for place in project_in.places:
        try:
            artwork_payloads.append((place, await fetch_artwork(place.external_id)))
        except (ArtworkNotFoundError, ArticAPIError) as exc:
            db.rollback()
            raise artic_exception_to_http(exc) from exc

    for place_in, artwork_data in artwork_payloads:
        project.places.append(build_project_place(project, place_in, artwork_data))

    recalculate_project_completion(project)
    db.commit()
    db.refresh(project)
    return get_project_or_404(db, project.id)


@app.get("/projects", response_model=list[ProjectResponse], tags=["projects"])
def list_projects(
    db: Session = Depends(get_db),
    completed: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Sequence[Project]:
    stmt = select(Project).options(selectinload(Project.places)).order_by(Project.id.desc())
    if completed is not None:
        stmt = stmt.where(Project.completed == completed)
    stmt = stmt.offset(offset).limit(limit)
    return db.scalars(stmt).all()


@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    return get_project_or_404(db, project_id)


@app.patch("/projects/{project_id}", response_model=ProjectResponse, tags=["projects"])
def update_project(project_id: int, project_in: ProjectUpdate, db: Session = Depends(get_db)) -> Project:
    project = get_project_or_404(db, project_id)
    apply_project_updates(project, project_in)
    db.commit()
    db.refresh(project)
    return get_project_or_404(db, project_id)


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
def delete_project(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = get_project_or_404(db, project_id)
    if any(place.visited for place in project.places):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project cannot be deleted because it contains visited places.",
        )
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/projects/{project_id}/places",
    response_model=PlaceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["places"],
)
async def add_place_to_project(
    project_id: int,
    place_in: PlaceCreate,
    db: Session = Depends(get_db),
) -> ProjectPlace:
    project = get_project_or_404(db, project_id)
    ensure_project_place_limit(project)
    ensure_no_duplicate_place(project, place_in.external_id)

    try:
        artwork_data = await fetch_artwork(place_in.external_id)
    except (ArtworkNotFoundError, ArticAPIError) as exc:
        raise artic_exception_to_http(exc) from exc

    place = build_project_place(project, place_in, artwork_data)
    db.add(place)
    db.flush()
    recalculate_project_completion(project)
    db.commit()
    db.refresh(place)
    return place


@app.get("/projects/{project_id}/places", response_model=list[PlaceResponse], tags=["places"])
def list_project_places(project_id: int, db: Session = Depends(get_db)) -> Sequence[ProjectPlace]:
    get_project_or_404(db, project_id)
    stmt = select(ProjectPlace).where(ProjectPlace.project_id == project_id).order_by(ProjectPlace.id.asc())
    return db.scalars(stmt).all()


@app.get("/projects/{project_id}/places/{place_id}", response_model=PlaceResponse, tags=["places"])
def get_project_place(project_id: int, place_id: int, db: Session = Depends(get_db)) -> ProjectPlace:
    get_project_or_404(db, project_id)
    return get_project_place_or_404(db, project_id, place_id)


@app.patch("/projects/{project_id}/places/{place_id}", response_model=PlaceResponse, tags=["places"])
def update_project_place(
    project_id: int,
    place_id: int,
    place_in: PlaceUpdate,
    db: Session = Depends(get_db),
) -> ProjectPlace:
    project = get_project_or_404(db, project_id)
    place = get_project_place_or_404(db, project_id, place_id)
    update_data = place_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(place, field, value)
    recalculate_project_completion(project)
    db.commit()
    db.refresh(place)
    return place
