from http import HTTPStatus
from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from invoice_utils.dal import Repository, Template
import invoice_utils.di as di

from ._request import TemplateRequestBody
from ._response import ListResponse, TemplateResponse

log = getLogger(__name__)
router = APIRouter(prefix="/templates")


class TemplateItem(BaseModel):
    name: str


@router.get("/", response_model=ListResponse[TemplateItem])
def list_templates(
    repo: Repository[str, Template] = Depends(di.template_repo)
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
        log.error("repo exception on list", exc_info=exc)
        raise HTTPException(
            status_code=507,
            detail="error reading from template repository"
        )


@router.post("/", status_code=HTTPStatus.CREATED, response_model=TemplateResponse)
def create_template(
    body: TemplateRequestBody = Body(),
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    try:
        result = repo.create(body.to_model())
        return TemplateResponse.from_model(result)
    except Exception as exc:
        log.error("repo exception on create", exc_info=exc)
        raise HTTPException(
            status_code=507,
            detail="error creating template in template repository"
        )

