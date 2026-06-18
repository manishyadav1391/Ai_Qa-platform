from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Project

from app.schemas.project import (
    ProjectCreate,
    ProjectResponse
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

@router.post(
    "",
    response_model=ProjectResponse
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):

    new_project = Project(
        name=project.name,
        url=project.url
    )

    db.add(new_project)

    db.commit()

    db.refresh(new_project)

    return new_project

@router.get(
    "",
    response_model=list[ProjectResponse]
)
def get_projects(
    db: Session = Depends(get_db)
):

    return db.query(Project).all()



@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    return (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )



