import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from invoice_utils.dal import TemplateFileRepository, Template


@pytest.fixture
def repo_dir(data_dir):
    result = tempfile.mkdtemp(dir=data_dir)
    try:
        yield Path(result)
    finally:
        shutil.rmtree(result)


@pytest.fixture
def sut(repo_dir):
    return TemplateFileRepository(repo_dir)


@pytest.fixture
def template_1():
    return Template(name="test-1", rules=[{"some": "rule"}])


def read_json(path):
    with open(path, "r") as f:
        return json.load(f)


def test_file_repo_create(sut, repo_dir, template_1):
    sut.create(template_1)

    actual = read_json(repo_dir / "test-1.json")

    assert actual["name"] == "test-1"
    assert actual["rules"] == [{"some": "rule"}]


def test_file_update_existing_file_with_rename(sut, repo_dir, template_1):
    with open(repo_dir / "file.json", "w") as f:
        f.write("[]")
    sut.update("file", template_1)

    actual = read_json(repo_dir / "test-1.json")

    assert actual["name"] == "test-1"
    assert actual["rules"] == [{"some": "rule"}]
    assert not Path(repo_dir/"file").exists()


def test_file_delete(sut, repo_dir):
    with open(repo_dir / "test-delete.json", "w") as f:
        f.write("[]")

    sut.delete("test-delete")

    assert not Path(repo_dir / "test-delete.json").exists()


def test_file_exists(sut, repo_dir):
    with open(repo_dir / "test-exists.json", "w") as f:
        f.write("[]")

    assert sut.exists("test-exists")
    assert not sut.exists("test-not-exists")


def test_get_by_name_exists(sut, repo_dir, template_1):
    sut.create(template_1)

    found, result = sut.get_by_key(template_1.name)

    assert found
    assert result == template_1


def test_get_by_name_not_exists(sut, repo_dir, template_1):
    found, result = sut.get_by_key(template_1.name)

    assert not found
    assert result is None


def test_list(sut, repo_dir):
    assert sut.list() == []


def test_list_template_exists(sut, repo_dir, template_1):
    sut.create(template_1)

    assert sut.list() == [template_1]
