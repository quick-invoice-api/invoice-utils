from unittest.mock import call


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
    assert res.json() == {"detail": "repo error while getting template by name"}


def test_get_by_name_template_repo_exception_log(http, template_repo, caplog):
    expected = Exception()
    template_repo.get_by_key.side_effect = expected

    with caplog.at_level("ERROR"):
        http.get("/api/v1/template/some-name")

    assert caplog.messages == ["repo exception on get"]
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
    assert res.json() == {"detail": "repo error while deleting template by name"}


def test_delete_repo_exception_log_exception(http, template_repo, caplog):
    expected = Exception()
    template_repo.delete.side_effect = expected

    with caplog.at_level("ERROR"):
        http.delete("/api/v1/template/error")

    assert caplog.messages == ["repo exception on delete"]
    assert caplog.records[0].exc_info[1] == expected
