from unittest.mock import call, ANY

import pytest
from pydantic import BaseModel


def test_get_by_name_success_returns_200(http):
    res = http.get("/api/v1/template/irrelevant-name")

    assert res.status_code == 200


def test_get_by_name_success_calls_repo(http, template_repo):
    expected = "template-name"
    http.get(f"/api/v1/template/{expected}")

    assert template_repo.get_by_key.call_count == 1
    assert template_repo.get_by_key.call_args_list == [call(expected)]


def test_get_by_name_success_returns_template_from_repo(http, template_repo):
    res = http.get("/api/v1/template/some-name")

    assert res.json() == {
        "name": "test-template-1",
        "rules": []
    }


def test_get_by_name_template_not_found_return_404(http, template_repo):
    template_repo.get_by_key.return_value = False, None

    res = http.get("/api/v1/template/some-name")

    assert res.status_code == 404


def test_get_by_name_template_repo_exception_return_5xx(http, template_repo):
    template_repo.get_by_key.side_effect = Exception()

    res = http.get("/api/v1/template/some-name")

    assert res.status_code == 507
    assert res.json() == {"detail": "repo error on get template by name"}


def test_get_by_name_template_repo_exception_log(http, template_repo, caplog):
    expected = Exception()
    template_repo.get_by_key.side_effect = expected

    with caplog.at_level("ERROR"):
        http.get("/api/v1/template/some-name")

    assert caplog.messages == ["repo error on get by key"]
    assert caplog.records[0].exc_info[1] == expected


def test_delete_success_returns_2xx(http):
    res = http.delete("/api/v1/template/some-name")

    assert res.status_code == 204


def test_delete_success_deletes_from_repo_expected_template(http, template_repo):
    expected = "expected-name"

    http.delete(f"/api/v1/template/{expected}")

    assert template_repo.delete.call_count == 1
    assert template_repo.delete.call_args_list == [call(expected)]


def test_delete_name_not_found_return_404(http, template_repo):
    template_repo.delete.return_value = False

    res = http.delete("/api/v1/template/not-found")

    assert res.status_code == 404
    assert res.json() == {"detail": "template 'not-found' not found"}


def test_delete_repo_exception_return_5xx(http, template_repo):
    template_repo.delete.side_effect = Exception

    res = http.delete("/api/v1/template/error")

    assert res.status_code == 507
    assert res.json() == {"detail": "repo error on delete template by name"}


def test_delete_repo_exception_log_exception(http, template_repo, caplog):
    expected = Exception()
    template_repo.delete.side_effect = expected

    with caplog.at_level("ERROR"):
        http.delete("/api/v1/template/error")

    assert caplog.messages == ["repo error on delete"]
    assert caplog.records[0].exc_info[1] == expected


def test_put_template_success_returns_accepted(http, template_req_body):
    res = http.put("/api/v1/template/some-name", json=template_req_body)

    assert res.status_code == 202


def test_put_template_success_checks_template_exists(
    http, template_req_body, template_repo
):
    expected = "some-name"
    http.put(f"/api/v1/template/{expected}", json=template_req_body)

    assert template_repo.exists.call_count == 1
    assert template_repo.exists.call_args_list == [call(expected)]


def test_put_template_that_already_exists_calls_repo_update(
    http, template_req_body, template_repo
):
    template_repo.exists.return_value = True

    http.put(f"/api/v1/template/some-template", json=template_req_body)

    assert template_repo.update.call_count == 1
    assert template_repo.update.call_args_list == [call("some-template", ANY)]
    template = template_repo.update.call_args_list[0][0][1]
    assert isinstance(template, BaseModel)
    assert template.dict() == {
        "name": "create-template-stub-1",
        "rules": [{"create-stub": "different-from-repo-create"}]
    }


def test_put_template_that_does_not_exist_calls_repo_create(
    http, template_req_body, template_repo
):
    template_repo.exists.return_value = False

    http.put(f"/api/v1/template/some-template", json=template_req_body)

    assert template_repo.create.call_count == 1
    template = template_repo.create.call_args_list[0][0][0]
    assert isinstance(template, BaseModel)
    assert template.dict() == {
        "name": "create-template-stub-1",
        "rules": [{"create-stub": "different-from-repo-create"}]
    }


def test_put_template_repo_create_error_returns_5xx(http, template_req_body, template_repo):
    template_repo.exists.return_value = False
    template_repo.create.side_effect = Exception()
    res = http.put("/api/v1/template/some-template", json=template_req_body)

    assert res.status_code == 507
    assert res.json() == {"detail": "repo error on insert template on update"}


def test_put_template_repo_create_error_logs_exception(http, template_req_body, template_repo, caplog):
    expected = Exception()
    template_repo.exists.return_value = False
    template_repo.create.side_effect = expected

    with caplog.at_level("ERROR"):
        http.put("/api/v1/template/some-template", json=template_req_body)

    assert caplog.messages == ["repo error on create"]
    assert caplog.records[0].exc_info[1] == expected


def test_put_template_repo_update_error_returns_5xx(http, template_req_body, template_repo):
    template_repo.exists.return_value = True
    template_repo.update.side_effect = Exception()
    res = http.put("/api/v1/template/some-template", json=template_req_body)

    assert res.status_code == 507
    assert res.json() == {"detail": "repo error on update template by name"}


def test_put_template_repo_update_error_logs_exception(http, template_req_body, template_repo, caplog):
    expected = Exception()
    template_repo.exists.return_value = True
    template_repo.update.side_effect = expected

    with caplog.at_level("ERROR"):
        http.put("/api/v1/template/some-template", json=template_req_body)

    assert caplog.messages == ["repo error on update"]
    assert caplog.records[0].exc_info[1] == expected


def test_put_already_existing_template_returns_repo_result(http, template_req_body, template_repo):
    res = http.put("/api/v1/template/some-template", json=template_req_body)

    assert res.json() == {"name": "test-template-1", "rules": []}


@pytest.mark.parametrize("changed,expected", [(True, "changed"), (False, "not changed")])
def test_put_already_existing_template_logs_when_changed(
    http, template_req_body, template_repo, changed, expected, default_template, caplog
):
    template_repo.update.return_value = changed, default_template

    with caplog.at_level("INFO"):
        http.put("/api/v1/template/some-template", json=template_req_body)

    assert caplog.messages[0] == f"template 'some-template' was {expected}."


def test_put_repo_existence_check_unhandled_exception_is_logged_and_handled(
    http, template_req_body, template_repo, caplog
):
    expected = Exception()
    template_repo.exists.side_effect = expected

    with caplog.at_level("ERROR"):
        res = http.put("/api/v1/template/some-template", json=template_req_body)

    assert res.status_code == 507
    assert res.json() == {"detail": "repo error on find template by name"}
    assert caplog.messages == ["repo error on exists"]
    assert caplog.records[0].exc_info[1] == expected