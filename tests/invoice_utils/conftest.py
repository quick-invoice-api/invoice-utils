import pathlib
import pytest


@pytest.fixture(scope="session")
def input_data_resolver():
    def f(name: str) -> str:
        data_dir = pathlib.Path(__file__).parent.parent/"data"
        desired_path = data_dir/name
        if desired_path.exists():
            return str(desired_path.absolute())
        raise FileNotFoundError(f"file {name} not found in the project's data dir")
    return f