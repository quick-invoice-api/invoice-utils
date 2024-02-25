from contextlib import contextmanager
from http import HTTPStatus
from logging import getLogger

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from invoice_utils.dal import Repository, Template
import invoice_utils.depends as di

from ._request import TemplateRequestBody
from ._response import TemplateResponse

log = getLogger(__name__)
router = APIRouter(prefix="/template")


class TemplateItem(BaseModel):
    name: str


@contextmanager
def error_handler(operation: str, http_detail_text: str):
    try:
        yield
    except Exception as exc:
        log.error("repo error on %s", operation, exc_info=exc)
        raise HTTPException(status_code=507, detail=http_detail_text)


@router.get("/{name}", response_model=TemplateResponse)
def get_template_by_name(
    name: str,
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    with error_handler("get by key", "repo error on get template by name"):
        found, result = repo.get_by_key(name)
    if not found:
        raise HTTPException(status_code=404, detail="template not found in repo")
    return TemplateResponse.from_model(result)


@router.delete("/{name}", status_code=HTTPStatus.NO_CONTENT)
def delete_template(
    name: str,
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    with error_handler("delete", "repo error on delete template by name"):
        found = repo.delete(name)
    if not found:
        raise HTTPException(status_code=404, detail=f"template '{name}' not found")


@router.put("/{name}", status_code=HTTPStatus.ACCEPTED, response_model=TemplateResponse)
def upsert_template(
    name: str,
    body: TemplateRequestBody = Body(),
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    with error_handler("exists", "repo error on find template by name"):
        found = repo.exists(name)

    if found:
        with error_handler("update", "repo error on update template by name"):
            changed, result = repo.update(name, body.to_model())
            log.info(
                "template '%s' was %s.", name, "changed" if changed else "not changed"
            )
    else:
        with error_handler("create", "repo error on insert template on update"):
            result = repo.create(body.to_model())
    return result
