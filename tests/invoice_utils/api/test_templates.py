import pytest

from invoice_utils.dal import Template


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


def test_create_template_success_return_2xx(http):
    res = http.post("/api/v1/templates")

    assert res.status_code == 201
