# Travel Planner API

REST API for managing travel projects and planned places to visit.
Places are validated against the Art Institute of Chicago API before they are attached to a project.

## Stack

- FastAPI
- SQLAlchemy
- SQLite
- HTTPX
- Pydantic
- Docker

## Features

- CRUD for travel projects
- Create a project with places in a single request
- Add a place to an existing project after third-party validation
- Update project place `notes` and `visited` status
- Automatic project completion when all places are marked as visited
- Prevent project deletion when at least one place is already visited
- Prevent duplicate external places inside the same project
- Enforce maximum of 10 places per project
- Swagger/OpenAPI documentation out of the box
- Basic pagination and filtering for project listing

## Project structure

```text
app/
  artic_client.py
  config.py
  database.py
  main.py
  models.py
  schemas.py
  services.py
requirements.txt
Dockerfile
.env.example
README.md
```

## Requirements

- Python 3.13+ recommended

## Run locally

1. Create and activate a virtual environment.

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create .env according to .env.example:

4. Start the server:

```bash
uvicorn app.main:app --reload
```

5. Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Run with Docker

```bash
docker build -t travel-planner .
docker run -p 8000:8000 travel-planner
```

## Environment variables

- `APP_TITLE`
- `APP_VERSION`
- `DATABASE_URL`
- `ARTIC_API_URL`
- `ARTIC_TIMEOUT`

## API overview

### Health

- `GET /health`

### Projects

- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`

### Project places

- `POST /projects/{project_id}/places`
- `GET /projects/{project_id}/places`
- `GET /projects/{project_id}/places/{place_id}`
- `PATCH /projects/{project_id}/places/{place_id}`

## Query parameters

### `GET /projects`

- `completed`: filter by project completion status
- `limit`: pagination size, default `20`, max `100`
- `offset`: pagination offset, default `0`

## Business rules

- A project cannot contain less than 1 and more than 10 places.
- The same Art Institute artwork cannot be added twice to the same project.
- A project cannot be deleted if any place is marked as visited.
- When all places in a project are marked as visited, the project becomes `completed=true`.
- If any place is switched back to `visited=false`, the project becomes `completed=false`.

## External API

The application validates artworks against the Art Institute of Chicago API using:

- `GET https://api.artic.edu/api/v1/artworks/{id}`

Reference:

- https://api.artic.edu/

