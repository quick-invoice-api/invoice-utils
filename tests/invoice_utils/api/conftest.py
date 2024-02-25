import pytest


@pytest.fixture
def template_req_body():
    return dict(
        name="create-template-stub-1",
        rules=[
            {"create-stub": "different-from-repo-create"}
        ]
    )


