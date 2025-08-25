import pytest
from sqlalchemy.exc import IntegrityError

from easy_diagrams import models


@pytest.fixture(name="patched_code_version")
def patched_code_version_fixture(monkeypatch):
    """Making Diagram code version deterministic for testing."""
    value = 173326130290680676

    def gen_code_version():
        return value

    monkeypatch.setattr(models.diagram, "_gen_code_version", gen_code_version)
    yield value


@pytest.fixture(name="diagram")
def diagram_fixture(dbsession, user, organization, patched_code_version):
    """Dummy diagram instance for tests."""
    diagram = models.DiagramTable(
        organization_id=organization.id,
        code="1",
    )
    diagram.set_image(b"1", diagram.code_version)
    dbsession.add(diagram)
    dbsession.flush()
    assert diagram.code_version == patched_code_version
    assert diagram.code == "1"
    assert diagram.image_version == patched_code_version
    assert diagram.image == b"1"
    yield diagram


def test_diagram_is_required_to_have_a_user(dbsession):
    diagram = models.DiagramTable()
    dbsession.add(diagram)
    with pytest.raises(IntegrityError, match='null value in column "organization_id"'):
        dbsession.flush()


def test_diagram_id_is_auto_generated(dbsession, user, organization):
    diagram = models.DiagramTable(organization_id=organization.id)
    assert diagram.id is None
    dbsession.add(diagram)
    dbsession.flush()
    assert diagram.id is not None


def test_create_all_empty(dbsession, user, organization):
    diagram = models.DiagramTable(organization_id=organization.id)
    assert diagram.id is None
    dbsession.add(diagram)
    dbsession.flush()
    assert diagram.id is not None
    assert diagram.code_version is None
    assert diagram.code is None
    assert diagram.image_version is None
    assert diagram.image is None


def test_create_all_set(dbsession, user, organization, patched_code_version):
    diagram = models.DiagramTable(organization_id=organization.id)
    diagram.code = "1"
    diagram.set_image(b"1", diagram.code_version)
    dbsession.add(diagram)
    dbsession.flush()
    assert diagram.code_version == patched_code_version
    assert diagram.code == "1"
    assert diagram.image_version == patched_code_version
    assert diagram.image == b"1"


def test_create_no_image(dbsession, user, organization, patched_code_version):
    diagram = models.DiagramTable(organization_id=organization.id)
    diagram.code = "1"
    dbsession.add(diagram)
    dbsession.flush()
    assert diagram.code_version == patched_code_version
    assert diagram.code == "1"
    assert diagram.image_version is None
    assert diagram.image is None


def test_update_code(dbsession, diagram, monkeypatch):
    monkeypatch.setattr(models.diagram, "_gen_code_version", lambda: 222222222222222222)
    diagram.code = "2"
    dbsession.flush()
    assert diagram.code == "2"
    assert diagram.code_version == 222222222222222222


def test_update_image(dbsession, diagram):
    diagram.set_image(b"2", 222222222222222222)
    dbsession.flush()
    assert diagram.image == b"2"
    assert diagram.image_version == 222222222222222222
