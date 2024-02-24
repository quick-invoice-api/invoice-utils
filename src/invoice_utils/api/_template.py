from http import HTTPStatus
from logging import getLogger

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from invoice_utils.dal import Repository, Template
import invoice_utils.di as di

from ._request import TemplateRequestBody
from ._response import TemplateResponse

log = getLogger(__name__)
router = APIRouter(prefix="/template")


class TemplateItem(BaseModel):
    name: str


@router.get("/{name}", response_model=TemplateResponse)
def get_template_by_name(
    name: str,
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    try:
        found, result = repo.get_by_key(name)
    except Exception as exc:
        log.error("repo exception on get", exc_info=exc)
        raise HTTPException(status_code=507, detail="repo error while getting template by name")

    if not found:
        raise HTTPException(status_code=404, detail="template not found in repo")
    return TemplateResponse.from_model(result)


@router.delete("/{name}", status_code=HTTPStatus.NO_CONTENT)
def delete_template(
    name: str,
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    try:
        found = repo.delete(name)
    except Exception as exc:
        log.error("repo exception on delete", exc_info=exc)
        raise HTTPException(status_code=507, detail="repo error while deleting template by name")
    if not found:
        raise HTTPException(status_code=404, detail=f"template '{name}' not found")


@router.put("/{name}", status_code=HTTPStatus.ACCEPTED, response_model=TemplateResponse)
def upsert_template(
    name: str,
    body: TemplateRequestBody = Body(),
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    if repo.exists(name):
        try:
            repo.update(name, body.to_model())
        except Exception as exc:
            raise HTTPException(
                status_code=507,
                detail="error updating template in template repository"
            )
    else:
        try:
            repo.create(body.to_model())
        except Exception as exc:
            log.error("repo exception on create", exc_info=exc)
            raise HTTPException(
                status_code=507,
                detail="error creating template in template repository"
            )
    return TemplateResponse(name="stub", rules=[])
