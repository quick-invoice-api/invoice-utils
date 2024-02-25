from pathlib import Path

from invoice_utils.dal import TemplateFileRepository
from invoice_utils.config import DEFAULT_BODY_TEMPLATE_DIRECTORY


def template_repo():
    return TemplateFileRepository(Path(DEFAULT_BODY_TEMPLATE_DIRECTORY))
