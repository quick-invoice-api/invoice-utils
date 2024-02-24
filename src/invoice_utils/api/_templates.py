from fastapi import APIRouter


router = APIRouter(prefix="/templates")


@router.get("/")
def list_templates():
    return []
