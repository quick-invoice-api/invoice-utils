import json
from pathlib import Path
from typing import Optional

from ._model import Template
from ._repo import Repository, K, T


class TemplateFileRepository(Repository[str, Template]):
    def __init__(self, dir_path: Path):
        self.__dir = dir_path

    def list(self) -> list[Template]:
        return [
            Template.parse_obj(json.loads(fpath.read_text()))
            for fpath in self.__dir.glob("*.json")
        ]

    def _path(self, name: str) -> Path:
        return self.__dir / f"{name}.json"

    def create(self, model: Template) -> Template:
        with open(self._path(model.name), "w") as f:
            json.dump(model.dict(), f, indent=4)
        return model

    def get_by_key(self, name: str) -> tuple[bool, Optional[Template]]:
        file_path = self._path(name)
        exists = file_path.exists()
        return exists, Template.parse_obj(json.loads(file_path.read_text())) if exists else None

    def delete(self, name: str) -> bool:
        file_path = self._path(name)
        if file_path.exists():
            file_path.unlink(missing_ok=False)
        return file_path.exists()

    def exists(self, name: str) -> bool:
        return self._path(name).exists()

    def update(self, name: str, model: Template) -> Template:
        file_path = self._path(name)
        if file_path.exists():
            file_path = file_path.rename(self.__dir / f"{model.name}.json")
        with open(file_path, "w") as f:
            json.dump(model.dict(), f, indent=4)
        return model
