import pytest

from easy_diagrams.domain.folder import FolderEdit
from easy_diagrams.exceptions import DiagramNotFoundError
from easy_diagrams.services.folder_repo import FolderRepository


class TestFolderRepository:

    def test_create_folder(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)
        folder_id = repo.create("Test Folder")

        assert folder_id is not None
        folder = repo.get(folder_id)
        assert folder.name == "Test Folder"
        assert folder.parent_id is None
        assert folder.organization_id == organization.id

    def test_create_nested_folder(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)
        parent_id = repo.create("Parent Folder")
        child_id = repo.create("Child Folder", parent_id=parent_id)

        child = repo.get(child_id)
        assert child.name == "Child Folder"
        assert child.parent_id == parent_id

    def test_list_folders(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)
        _ = repo.create("Folder 1")
        _ = repo.create("Folder 2")

        folders = repo.list()
        assert len(folders) == 2
        folder_names = [f.name for f in folders]
        assert "Folder 1" in folder_names
        assert "Folder 2" in folder_names

    def test_list_nested_folders(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)
        parent_id = repo.create("Parent")
        _ = repo.create("Child 1", parent_id=parent_id)
        _ = repo.create("Child 2", parent_id=parent_id)

        # List root folders
        root_folders = repo.list()
        assert len(root_folders) == 1
        assert root_folders[0].name == "Parent"

        # List child folders
        child_folders = repo.list(parent_id=parent_id)
        assert len(child_folders) == 2
        child_names = [f.name for f in child_folders]
        assert "Child 1" in child_names
        assert "Child 2" in child_names

    def test_edit_folder(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)
        folder_id = repo.create("Original Name")

        changes = FolderEdit(name="New Name")
        updated_folder = repo.edit(folder_id, changes)

        assert updated_folder.name == "New Name"

    def test_delete_folder(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)
        folder_id = repo.create("To Delete")

        repo.delete(folder_id)

        with pytest.raises(DiagramNotFoundError):
            repo.get(folder_id)

    def test_get_nonexistent_folder(self, dbsession, user, organization):
        repo = FolderRepository(organization.id, dbsession)

        with pytest.raises(DiagramNotFoundError):
            repo.get("nonexistent")

    def test_user_isolation(
        self, dbsession, user, organization, user_factory, organization_factory
    ):
        repo1 = FolderRepository(organization.id, dbsession)
        other_org = organization_factory()
        _other_user = user_factory(organization=other_org)
        repo2 = FolderRepository(other_org.id, dbsession)

        folder_id = repo1.create("User 1 Folder")

        # User 2 should not be able to access User 1's folder
        with pytest.raises(DiagramNotFoundError):
            repo2.get(folder_id)
