import json
import pathlib
from importlib import reload
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
import pytest

from invoice_utils.dal import Template, Repository
import invoice_utils.di as di


@pytest.fixture(scope="session")
def resolve_path():
    def f(name: str) -> str:
        data_dir = pathlib.Path(__file__).parent.parent / "data"
        desired_path = data_dir / name
        if desired_path.exists():
            return str(desired_path.absolute())
        raise FileNotFoundError(f"file {name} not found in the test data dir")
    return f


@pytest.fixture
def read_text(resolve_path):
    def f(name: str) -> str:
        with open(resolve_path(name)) as f:
            return f.read()
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


@pytest.fixture
def default_template(read_text):
    template_str = read_text("empty.json")

    return Template(
        name="test-template-1",
        rules=json.loads(template_str)
    )


@pytest.fixture
def template_repo(default_template, request):
    result = MagicMock(spec=Repository)
    result.list.return_value = (
        request.param
        if hasattr(request, "param") and request.param is not None
        else [default_template]
    )
    result.create.return_value = (
        request.param
        if hasattr(request, "param") and request.param is not None
        else default_template
    )
    result.get_by_key.return_value = (
        request.param
        if hasattr(request, "param") and request.param is not None
        else True, default_template
    )
    result.delete.return_value = True
    return result


@pytest.fixture()
def http(environment, monkeypatch, template_repo):
    with patch("dotenv.load_dotenv", MagicMock(name="load_dotenv")):
        import invoice_utils.web as web
        web.app.dependency_overrides[di.template_repo] = lambda: template_repo

        return TestClient(web.app)
