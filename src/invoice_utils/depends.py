from pathlib import Path

from invoice_utils.dal import TemplateFileRepository
from invoice_utils.config import DEFAULT_TEMPLATES_DIRECTORY


def template_repo():
    return TemplateFileRepository(Path(DEFAULT_TEMPLATES_DIRECTORY))
