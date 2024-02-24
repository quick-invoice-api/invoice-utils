from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from invoice_utils.dal import Repository, Template
import invoice_utils.di as di

from ._response import TemplateResponse

log = getLogger(__name__)
router = APIRouter(prefix="/template")


class TemplateItem(BaseModel):
    name: str


@router.get("/{name}", response_model=TemplateResponse)
def list_templates(
    name: str,
    repo: Repository[str, Template] = Depends(di.template_repo)
):
    try:
        found, result = repo.get_by_key(name)
    except:
        raise HTTPException(status_code=507, detail="repo error while getting template by name")

    if not found:
        raise HTTPException(status_code=404, detail="template not found in repo")
    return TemplateResponse.from_model(result)
