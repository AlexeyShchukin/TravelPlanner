from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Project, ProjectPlace
from app.schemas import MAX_PLACES_PER_PROJECT, PlaceCreate, ProjectCreate, ProjectUpdate


def get_project_or_404(db: Session, project_id: int) -> Project:
    stmt = select(Project).options(selectinload(Project.places)).where(Project.id == project_id)
    project = db.scalar(stmt)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def get_project_place_or_404(db: Session, project_id: int, place_id: int) -> ProjectPlace:
    stmt = select(ProjectPlace).where(
        ProjectPlace.project_id == project_id,
        ProjectPlace.id == place_id,
    )
    place = db.scalar(stmt)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project place not found.")
    return place


def ensure_project_place_limit(project: Project, additional_places: int = 1) -> None:
    if len(project.places) + additional_places > MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project cannot have more than {MAX_PLACES_PER_PROJECT} places.",
        )


def ensure_no_duplicate_place(project: Project, external_id: int) -> None:
    if any(place.external_id == external_id for place in project.places):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This artwork is already added to the project.",
        )


def recalculate_project_completion(project: Project) -> None:
    project.completed = bool(project.places) and all(place.visited for place in project.places)


def apply_project_updates(project: Project, project_update: ProjectUpdate) -> Project:
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    return project


def build_project_place(project: Project, place_data: PlaceCreate, artwork_data) -> ProjectPlace:
    return ProjectPlace(
        project=project,
        external_id=artwork_data.external_id,
        title=artwork_data.title,
        artist_display=artwork_data.artist_display,
        place_of_origin=artwork_data.place_of_origin,
        date_display=artwork_data.date_display,
        notes=place_data.notes,
        visited=False,
    )


def create_project_entity(project_in: ProjectCreate) -> Project:
    return Project(
        name=project_in.name,
        description=project_in.description,
        start_date=project_in.start_date,
        completed=False,
    )
