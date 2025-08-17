import pytest


@pytest.fixture(name="csrf_headers")
def csrf_headers_fixture(testapp):
    return dict(headers={"X-CSRF-Token": testapp.get_csrf_token()})


class TestFolderOperations:

    def test_create_folder(self, testapp, csrf_headers):
        testapp.login()

        res = testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "Test Folder"},
            status=303,
            **csrf_headers,
        )

        # Should redirect back to diagrams page
        assert res.location.endswith("/diagrams")

        # Check that folder appears in listing
        res = testapp.get("/diagrams", status=200)
        assert "Test Folder" in res.text
        assert "📁" in res.text  # Folder icon

    def test_create_folder_requires_name(self, testapp, csrf_headers):
        testapp.login()

        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": ""},
            status=400,
            **csrf_headers,
        )

    def test_create_nested_folder(self, testapp, csrf_headers):
        testapp.login()

        # Create parent folder
        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "Parent"},
            status=303,
            **csrf_headers,
        )

        # Get folder ID from listing
        res = testapp.get("/diagrams", status=200)
        folder_links = res.lxml.xpath("//a[contains(@href, 'folder_id=')]/@href")
        assert len(folder_links) == 1

        folder_id = folder_links[0].split("folder_id=")[1]

        # Create child folder
        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "Child", "parent_id": folder_id},
            status=303,
            **csrf_headers,
        )

        # Navigate to parent folder and check child exists
        res = testapp.get(f"/diagrams?folder_id={folder_id}", status=200)
        assert "Child" in res.text

    def test_navigate_folders(self, testapp, csrf_headers):
        testapp.login()

        # Create folder
        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "Navigation Test"},
            status=303,
            **csrf_headers,
        )

        # Get folder link
        res = testapp.get("/diagrams", status=200)
        folder_links = res.lxml.xpath("//a[contains(@href, 'folder_id=')]/@href")
        folder_url = folder_links[0]

        # Navigate into folder
        res = testapp.get(folder_url, status=200)
        assert "Navigation Test" in res.text
        assert "breadcrumb" in res.text

    def test_create_diagram_in_folder(self, testapp, csrf_headers):
        testapp.login()

        # Create folder
        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "Diagram Folder"},
            status=303,
            **csrf_headers,
        )

        # Get folder ID
        res = testapp.get("/diagrams", status=200)
        folder_links = res.lxml.xpath("//a[contains(@href, 'folder_id=')]/@href")
        folder_id = folder_links[0].split("folder_id=")[1]

        # Create diagram in folder
        res = testapp.post(
            "/diagrams",
            params={"action": "create_diagram", "folder_id": folder_id},
            status=303,
            **csrf_headers,
        )

        # Should redirect to editor
        assert "/editor" in res.location

        # Check diagram appears in folder listing
        res = testapp.get(f"/diagrams?folder_id={folder_id}", status=200)
        diagram_rows = res.lxml.xpath("//table[@id='diagrams']/tbody/tr")
        # Should have at least one diagram row (folders show first, then diagrams)
        assert len(diagram_rows) >= 1

    def test_folder_pagination_preserves_folder_id(self, testapp, csrf_headers):
        testapp.login()

        # Create folder
        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "Pagination Test"},
            status=303,
            **csrf_headers,
        )

        # Get folder ID
        res = testapp.get("/diagrams", status=200)
        folder_links = res.lxml.xpath("//a[contains(@href, 'folder_id=')]/@href")
        folder_id = folder_links[0].split("folder_id=")[1]

        # Navigate to folder
        res = testapp.get(f"/diagrams?folder_id={folder_id}", status=200)

        # Check that pagination links include folder_id
        pagination_links = res.lxml.xpath(
            "//nav[@aria-label='Diagrams pagination']//a/@href"
        )
        for link in pagination_links:
            if "page=" in link:
                assert f"folder_id={folder_id}" in link

    def test_user_isolation_folders(self, testapp, csrf_headers, user_factory):
        # User 1 creates folder
        testapp.login()
        testapp.post(
            "/diagrams",
            params={"action": "create_folder", "name": "User1 Folder"},
            status=303,
            **csrf_headers,
        )

        # User 2 should not see User 1's folder
        testapp.login(user_factory().email)
        res = testapp.get("/diagrams", status=200)
        assert "User1 Folder" not in res.text
