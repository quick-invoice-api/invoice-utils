import pytest

from invoice_utils.dal import Template


def test_list_templates_success(http):
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
