from pydantic import BaseModel


class Template(BaseModel):
    name: str
    rules: list[dict]
