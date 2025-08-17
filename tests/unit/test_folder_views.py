from datetime import datetime
from unittest.mock import Mock

import pytest
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPSeeOther

from easy_diagrams.domain.folder import FolderListItem
from easy_diagrams.views.diagrams import Diagrams


class TestFolderViews:

    def test_create_folder_success(self):
        request = Mock()
        request.params = {
            "name": "Test Folder",
            "parent_id": None,
            "action": "create_folder",
        }
        request.route_url = Mock(return_value="/diagrams")

        folder_repo = Mock()
        folder_repo.create = Mock(return_value="folder123")
        request.find_service = Mock(return_value=folder_repo)

        view = Diagrams(request)

        result = view.create_item()

        assert isinstance(result, HTTPSeeOther)
        folder_repo.create.assert_called_once_with(name="Test Folder", parent_id=None)

    def test_create_folder_missing_name(self):
        request = Mock()
        request.params = {"name": "", "parent_id": None, "action": "create_folder"}

        view = Diagrams(request)

        with pytest.raises(HTTPBadRequest):
            view.create_item()

    def test_list_diagrams_with_folders(self):
        request = Mock()
        request.params = {"folder_id": "folder123"}
        request.registry.settings = {"diagrams.page_size": "10"}

        # Mock diagram repo
        diagram_repo = Mock()
        diagram_repo.list = Mock(return_value=[])
        diagram_repo.count = Mock(return_value=0)

        # Mock folder repo
        folder_repo = Mock()
        folders = [
            FolderListItem(
                id="subfolder1",
                name="Subfolder",
                parent_id="folder123",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        folder_repo.list = Mock(return_value=folders)
        folder_repo.count = Mock(return_value=1)
        folder_repo.get = Mock(return_value=Mock(name="Parent Folder"))

        def mock_find_service(interface):
            if "IDiagramRepo" in str(interface):
                return diagram_repo
            elif "IFolderRepo" in str(interface):
                return folder_repo

        request.find_service = mock_find_service

        view = Diagrams(request)

        result = view.list_diagrams()

        assert "folders" in result
        assert len(result["folders"]) == 1
        assert result["folders"][0].name == "Subfolder"
        assert result["current_folder"] is not None
        diagram_repo.list.assert_called_once_with(
            offset=0, limit=9, folder_id="folder123"
        )
        folder_repo.list.assert_called_once_with(
            parent_id="folder123", offset=0, limit=1
        )
