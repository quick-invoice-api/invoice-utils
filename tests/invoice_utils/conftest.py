import pathlib
from importlib import reload
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
import pytest


@pytest.fixture(scope="session")
def input_data_resolver():
    def f(name: str) -> str:
        data_dir = pathlib.Path(__file__).parent.parent / "data"
        desired_path = data_dir / name
        if desired_path.exists():
            return str(desired_path.absolute())
        raise FileNotFoundError(f"file {name} not found in the project's data dir")

    return f


@pytest.fixture()
def environment(monkeypatch, request):
    if hasattr(request, "param"):
        env = request.param
    else:
        env = {}
    invoice_utils_env_vars = [
        "INVOICE_UTILS_MAIL_LOGIN_USER",
        "INVOICE_UTILS_MAIL_LOGIN_PASSWORD"
    ]
    for k in invoice_utils_env_vars:
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from invoice_utils import config
    reload(config)
    return env


@pytest.fixture()
def http(environment, monkeypatch):
    with patch("dotenv.load_dotenv", MagicMock(name="load_dotenv")):
        import invoice_utils.web as web
        return TestClient(web.app)
