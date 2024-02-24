from fastapi import APIRouter, Depends
from pydantic import BaseModel

from invoice_utils.dal import Repository, Template
import invoice_utils.di as di

from invoice_utils.api._response import ListResponse


router = APIRouter(
    prefix="/templates",
    dependencies=[]
)


class TemplateItem(BaseModel):
    name: str


@router.get("/", response_model=ListResponse[TemplateItem])
def list_templates(
    repo: Repository[Template] = Depends(di.template_repo)
):
    return ListResponse(
        count=1,
        items=[
            TemplateItem(name=x.name)
            for x in repo.list()
        ]
    )
