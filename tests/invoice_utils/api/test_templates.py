from pydantic import BaseModel
import pytest

from invoice_utils.dal import Template


@pytest.fixture
def post_template_body():
    return dict(
        name="create-template-stub-1",
        rules=[
            {"create-stub": "different-from-repo-create"}
        ]
    )


def test_list_templates_success_return_2xx(http):
    res = http.get("/api/v1/templates/")

    assert res.status_code == 200


@pytest.mark.parametrize(
    "template_repo,expected_items",
    [
        ([], []),
        ([Template(name="test-template-1", rules=[])], [{"name": "test-template-1"}]),
        ([
             Template(name="test-template-1", rules=[]),
             Template(name="test-template-2", rules=[{"something": "ignored"}])
         ], [
             {"name": "test-template-1"},
             {"name": "test-template-2"},
         ]),
    ],
    indirect=["template_repo"]
)
def test_list_templates_returns_all_templates_from_repo(http, template_repo, expected_items):
    res = http.get("/api/v1/templates/")

    assert template_repo.list.call_count == 1
    actual = res.json()
    assert actual == {
        "count": 1,
        "items": expected_items
    }


def test_list_templates_on_repo_error_return_5xx(http, template_repo):
    template_repo.list.side_effect = Exception()

    res = http.get("/api/v1/templates")

    assert res.status_code == 507
    assert res.json() == {"detail": "error reading from template repository"}


def test_list_templates_on_repo_error_logs_exception(http, template_repo, caplog):
    expected_exception = Exception()
    template_repo.list.side_effect = expected_exception

    with caplog.at_level("ERROR"):
        http.get("/api/v1/templates")

    assert caplog.messages[0] == "exception while fetching templates from repo"
    assert caplog.records[0].exc_info[1] == expected_exception


def test_create_template_success_return_2xx(http, post_template_body):
    res = http.post("/api/v1/templates", json=post_template_body)

    assert res.status_code == 201


def test_create_template_success_calls_repo_create(
    http, post_template_body, template_repo
):
    http.post("/api/v1/templates", json=post_template_body)

    assert template_repo.create.call_count == 1
    template = template_repo.create.call_args_list[0][0][0]
    assert isinstance(template, BaseModel)
    assert template.dict() == {
        "name": "create-template-stub-1",
        "rules": [{"create-stub": "different-from-repo-create"}]
    }


@pytest.mark.parametrize(
    "template_repo,expected",
    [
        (
                Template(name="create-test-1", rules=[{"stub": "value"}]),
                {"name": "create-test-1", "rules": [{"stub": "value"}]}
        )
    ],
    indirect=["template_repo"]
)
def test_create_template_success_return_repo_create_result(
    http, post_template_body, template_repo, expected
):
    res = http.post("/api/v1/templates", json=post_template_body)

    assert res.json() == expected


def test_create_template_error_returns_5xx(http, post_template_body, template_repo):
    template_repo.create.side_effect = Exception()
    res = http.post("/api/v1/templates", json=post_template_body)

    assert res.status_code == 507
    assert res.json() == {"detail": "error creating template in template repository"}


def test_create_template_error_logs_exception(
    http, post_template_body, template_repo, caplog
):
    expected = Exception()
    template_repo.create.side_effect = expected

    with caplog.at_level("ERROR"):
        http.post("/api/v1/templates", json=post_template_body)

    assert caplog.messages == ["exception while creating template in template repository"]
    assert caplog.records[0].exc_info[1] == expected
