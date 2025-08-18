import pytest
from sqlalchemy import exc as sqlalchemy_exc

from easy_diagrams.domain.diagram import Diagram
from easy_diagrams.domain.diagram import DiagramEdit
from easy_diagrams.domain.diagram import DiagramListItem
from easy_diagrams.domain.diagram import DiagramRender
from easy_diagrams.exceptions import DiagramNotFoundError
from easy_diagrams.services.diagram_repo import DiagramRepository


def test_create_diagram(dbsession, user):
    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    diagram_id = repository.create()
    # assert type(diagram_id) is DiagramID
    diagram = repository.get(diagram_id)
    assert diagram.id is not None
    assert diagram.title is None
    assert diagram.is_public is False
    assert diagram.code is None
    assert diagram.render is None


def test_create_diagram_non_existing_user_id(dbsession):
    repository = DiagramRepository(
        organization_id="non-existent-org",
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    with pytest.raises(
        sqlalchemy_exc.IntegrityError,
        match='insert or update on table "diagrams" violates foreign key constraint.*organization.*',
    ):
        repository.create()


def test_edit_diagram(dbsession, user):
    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    diagram_id = repository.create()

    changes = DiagramEdit(
        title="test_title", is_public=True, code="test_code"  # , image=b"test_image"
    )
    diagram = repository.edit(diagram_id, changes)
    assert diagram.title == "test_title"
    assert diagram.is_public is True
    assert diagram.code == "test_code"
    assert diagram.render == DiagramRender(
        image=b"test_image", version=diagram.code_version
    )

    changes_2 = DiagramEdit(title="test_title_2")
    diagram = repository.edit(diagram_id, changes_2)
    assert diagram.title == "test_title_2"
    assert diagram.is_public is True
    assert diagram.code == "test_code"
    assert diagram.render == DiagramRender(
        image=b"test_image", version=diagram.code_version
    )

    changes_3 = DiagramEdit(is_public=False)
    diagram = repository.edit(diagram_id, changes_3)
    assert diagram.title == "test_title_2"
    assert diagram.is_public is False
    assert diagram.code == "test_code"
    assert diagram.render == DiagramRender(
        image=b"test_image", version=diagram.code_version
    )

    changes_4 = DiagramEdit(code="test_code_2")
    diagram = repository.edit(diagram_id, changes_4)
    assert diagram.title == "test_title_2"
    assert diagram.is_public is False
    assert diagram.code == "test_code_2"
    assert diagram.render == DiagramRender(
        image=b"test_image", version=diagram.code_version
    )


class FakeDiagramRenderer:
    def render(self, diagram):
        return b"test_image"


def test_edit_not_own_diagram(dbsession, user, user_factory):
    diagram_id = DiagramRepository(
        organization_id=user_factory().organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    ).create()

    changes = DiagramEdit(title="new_title")
    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    with pytest.raises(DiagramNotFoundError, match=f"Diagram {diagram_id} not found."):
        repository.edit(diagram_id, changes)


def test_get_diagram(dbsession, user):
    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    diagram_id = repository.create()
    diagram = repository.get(diagram_id)
    assert isinstance(diagram, Diagram)


def test_get_not_own_diagram(dbsession, user, user_factory):
    diagram_id = DiagramRepository(
        organization_id=user_factory().organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    ).create()

    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    with pytest.raises(DiagramNotFoundError, match=f"Diagram {diagram_id} not found."):
        repository.get(diagram_id)


def test_delete_diagram(dbsession, user):
    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    diagram_id = repository.create()
    repository.delete(diagram_id)
    with pytest.raises(DiagramNotFoundError, match=f"Diagram {diagram_id} not found."):
        repository.get(diagram_id)


def test_delete_not_own_diagram(dbsession, user, user_factory):
    diagram_id = DiagramRepository(
        organization_id=user_factory().organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    ).create()
    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )
    with pytest.raises(DiagramNotFoundError, match=f"Diagram {diagram_id} not found."):
        repository.delete(diagram_id)


def test_list_diagrams(dbsession, user, user_factory):
    # creating diagrams that don't belong to the user to make sure that the user
    # can see only his/her diagrams
    for _ in range(10):
        DiagramRepository(
            organization_id=user_factory().organization_id,
            dbsession=dbsession,
            diagram_renderer=FakeDiagramRenderer(),
        ).create()

    repository = DiagramRepository(
        organization_id=user.organization_id,
        dbsession=dbsession,
        diagram_renderer=FakeDiagramRenderer(),
    )

    # creating diagrams that belong to the user
    for i in range(10):
        diagram_id = repository.create()
        changes = DiagramEdit(
            title=f"test_title_{i}", is_public=bool(i // 2), code=f"test_code_{i}"
        )
        repository.edit(diagram_id, changes)

    # listing diagrams
    diagrams = repository.list()
    assert len(diagrams) == 10
    for counter, diagram in enumerate(diagrams):
        # to make sure that the order is correct as list is ordered by updated_at
        # desc, so the last updated diagram should be the first one
        i = 9 - counter
        assert isinstance(diagram, DiagramListItem)
        assert diagram.id is not None
        assert diagram.title == f"test_title_{i}"
        assert diagram.is_public is bool(i // 2)
        assert diagram.created_at is not None
        assert diagram.updated_at is not None

    # listing diagrams with pagination
    diagrams = repository.list(offset=5, limit=3)
    assert len(diagrams) == 3

    # listing diagrams with pagination
    diagrams = repository.list(offset=9, limit=3)
    assert len(diagrams) == 1
