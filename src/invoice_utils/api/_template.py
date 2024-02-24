from logging import getLogger

from fastapi import APIRouter, Depends
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
    repo: Repository[Template] = Depends(di.template_repo)
):
    return TemplateResponse(name="stub", rules=[])
