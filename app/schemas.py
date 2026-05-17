from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


MAX_PLACES_PER_PROJECT = 10


class PlaceCreate(BaseModel):
    external_id: int = Field(..., gt=0)
    notes: str | None = None


class PlaceUpdate(BaseModel):
    notes: str | None = None
    visited: bool | None = None

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    places: list[PlaceCreate] = Field(..., min_length=1, max_length=MAX_PLACES_PER_PROJECT)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("places")
    @classmethod
    def ensure_no_duplicate_external_ids(cls, places: list[PlaceCreate]) -> list[PlaceCreate]:
        external_ids = [place.external_id for place in places]
        if len(external_ids) != len(set(external_ids)):
            raise ValueError("Duplicate external_id values are not allowed in a project request.")
        return places


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class PlaceResponse(BaseModel):
    id: int
    project_id: int
    external_id: int
    title: str
    artist_display: str | None
    place_of_origin: str | None
    date_display: str | None
    notes: str | None
    visited: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    start_date: date | None
    completed: bool
    created_at: datetime
    updated_at: datetime
    places: list[PlaceResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
