from pydantic import BaseModel

from invoice_utils.dal import Template


class CreateTemplateRequestBody(BaseModel):
    name: str
    rules: list[dict]

    def to_model(self) -> Template:
        return Template(name=self.name, rules=self.rules)
