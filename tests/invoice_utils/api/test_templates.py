def test_list_templates_success(http):
    res = http.get("/api/v1/templates/")

    assert res.status_code == 200
