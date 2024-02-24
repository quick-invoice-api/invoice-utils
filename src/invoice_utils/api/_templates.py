from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from invoice_utils.dal import Repository, Template
import invoice_utils.di as di

from invoice_utils.api._response import ListResponse

log = getLogger(__name__)
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
    try:
        return ListResponse(
            count=1,
            items=[
                TemplateItem(name=x.name)
                for x in repo.list()
            ]
        )
    except Exception as exc:
        log.error("exception while fetching templates from repo", exc_info=exc)
        raise HTTPException(
            status_code=507,
            detail="error reading from template repository"
        )
