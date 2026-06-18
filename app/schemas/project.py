# Input/output validation
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    url: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    url: str

    class Config:
        from_attributes = True
