"""
Test checklist:
* a user can access only resources that belong to him
* a user can access only public resources
* for any request, except GET, a user is redirected to provide a valid CSRF token
* listings are paginated

"""

import re

import pytest


@pytest.fixture(name="csrf_headers")
def csrf_headers_fixture(testapp):
    return dict(headers={"X-CSRF-Token": testapp.get_csrf_token()})


def create_diagram(testapp, csrf_headers):
    return testapp.post("/diagrams", status=303, **csrf_headers).location.split("/")[-2]


@pytest.fixture(name="diagram")
def diagram_fixture(testapp, csrf_headers):
    testapp.login()
    diagram_id = create_diagram(testapp, csrf_headers)
    testapp.put(
        f"/diagrams/{diagram_id}",
        params={
            "title": f"Initial title for {diagram_id}",
            "code": f"Initial code for {diagram_id}",
        },
        status=200,
        **csrf_headers,
    )
    diagram = testapp.get(f"/diagrams/{diagram_id}/json", status=200).json
    return diagram


class TestDiagramCreate:

    def test_csrf_token_is_required(self, testapp):
        testapp.login()
        res = testapp.post("/diagrams", status=400)
        assert "400 Bad CSRF Token" in res.text

    def test_user_must_be_logged_in(self, testapp, csrf_headers, request_host):
        res = testapp.post("/diagrams", status=303, **csrf_headers)
        assert res.location.startswith(f"http://{request_host}/login?next=")

    def test_create_diagram(self, testapp, csrf_headers, request_host):
        testapp.login()
        res = testapp.post("/diagrams", status=303, **csrf_headers)
        assert res.location.startswith(f"http://{request_host}/diagrams/")


class TestDiagramList:

    def test_user_must_be_logged_in(self, testapp, request_host):
        res = testapp.get("/diagrams", status=303)
        assert res.location.startswith(f"http://{request_host}/login?next=")

    def test_empty_list(self, testapp):
        testapp.login()
        res = testapp.get("/diagrams", status=200)
        assert not res.lxml.xpath("//table[@id='diagrams']/tbody/tr/th/a/@href")

    def test_list(self, testapp, csrf_headers, request_host):
        testapp.login()

        # create two diagrams
        for _ in range(2):
            testapp.post("/diagrams", status=303, **csrf_headers)

        res = testapp.get("/diagrams", status=200)
        listed_diagrams = res.lxml.xpath("//table[@id='diagrams']/tbody/tr/th/a/@href")
        assert len(listed_diagrams) == 2
        for diagram_link in listed_diagrams:
            # checking if the link is valid
            assert re.match(
                rf"^http:\/\/{request_host}\/diagrams\/[A-Za-z0-9]{{32}}/editor$",
                diagram_link,
            )
            # checking if the link is accessible
            testapp.get(diagram_link, status=200)


class TestDiagramResourceDelete:
    """Tests for the diagram resource delete view."""

    def test_diagram_delete_success(self, testapp, csrf_headers, diagram):
        testapp.delete(f"/diagrams/{diagram['id']}", status=204, **csrf_headers)
        testapp.get(f"/diagrams/{diagram['id']}/editor", status=404)

    def test_user_must_be_logged_in(self, testapp, csrf_headers, request_host):
        res = testapp.delete("/diagrams/abcd", status=303, **csrf_headers)
        assert res.status_code == 303
        assert res.location.startswith(f"http://{request_host}/login?next=")

    def test_csrf_token_is_required(self, testapp, diagram):
        res = testapp.delete(f"/diagrams/{diagram['id']}", status=400)
        assert res.status_code == 400
        assert "400 Bad CSRF Token" in res.text

    def test_user_can_delete_only_own_diagrams(
        self, testapp, csrf_headers, user_factory, diagram
    ):
        testapp.login(user_factory().email)
        testapp.delete(f"/diagrams/{diagram['id']}", status=404, **csrf_headers)

    def test_delete_not_existing_diagram(self, testapp, csrf_headers):
        testapp.login()
        res = testapp.delete("/diagrams/abcd", status=404, **csrf_headers)
        assert res.status_code == 404


class TestDiagramResourceUpdate:
    """Tests for the diagram resource update view."""

    def test_diagram_update_success(self, testapp, csrf_headers, diagram):

        testapp.put(
            f"/diagrams/{diagram['id']}",
            params={"title": "hi title", "is_public": True, "code": "hi code"},
            status=200,
            **csrf_headers,
        )

        diagram = testapp.get(f"/diagrams/{diagram['id']}/json", status=200).json

        assert diagram == {
            "id": diagram["id"],
            "title": "hi title",
            "is_public": True,
            "code": "hi code",
        }

    def test_diagram_update_validation(self, testapp, csrf_headers, diagram):

        # empty values are fine
        testapp.put(f"/diagrams/{diagram['id']}", params={}, status=200, **csrf_headers)

        # extra values
        resp = testapp.put(
            f"/diagrams/{diagram['id']}",
            params={
                "title": "hi title",
                "is_public": True,
                "code": "hi code",
                "user_id": "23",
            },
            status=400,
            **csrf_headers,
        )
        assert "Unexpected keyword argument" in resp.text

        # invalid types
        resp = testapp.put(
            f"/diagrams/{diagram['id']}",
            params={"title": 1234, "is_public": "Nope", "code": True},
            status=400,
            **csrf_headers,
        )
        assert "unable to interpret input" in resp.text

        # title is limited to 300 characters
        resp = testapp.put(
            f"/diagrams/{diagram['id']}",
            params={"title": "a" * 301},
            status=400,
            **csrf_headers,
        )
        assert "should have at most 300 characters" in resp.text

        # code is limited to 10K characters
        resp = testapp.put(
            f"/diagrams/{diagram['id']}",
            params={"code": "a" * 10_241},
            status=400,
            **csrf_headers,
        )
        assert "should have at most 10240 characters" in resp.text

    def test_user_must_be_logged_in(
        self,
        testapp,
        csrf_headers,
        request_host,
        diagram,
    ):
        testapp.logout()

        res = testapp.put(
            f"/diagrams/{diagram['id']}", params={}, status=303, **csrf_headers
        )
        assert res.status_code == 303
        assert res.location.startswith(f"http://{request_host}/login?next=")

    def test_csrf_token_is_required(self, testapp, diagram):
        res = testapp.put(f"/diagrams/{diagram['id']}", params={}, status=400)
        assert "400 Bad CSRF Token" in res.text

    def test_user_can_update_only_own_diagrams(
        self, testapp, csrf_headers, user_factory, diagram
    ):
        # checking if another user can delete the diagram
        testapp.login(user_factory().email)
        res = testapp.put(
            f"/diagrams/{diagram['id']}",
            params={"title": "hi"},
            status=404,
            **csrf_headers,
        )
        assert res.status_code == 404

    def test_update_not_existing_diagram(self, testapp, csrf_headers):
        testapp.login()
        res = testapp.put("/diagrams/abcd", params={}, status=404, **csrf_headers)
        assert res.status_code == 404


class TestDiagramResourceGET:
    """Tests for the diagram resource GET view."""

    def test_get_request_is_redirected_to_editor_view(self, testapp, diagram):
        res = testapp.get(f"/diagrams/{diagram['id']}", status=303)
        assert res.location.endswith(f"/diagrams/{diagram['id']}/editor")


class TestDiagramEditorView:
    """Tests for the diagram editor view.

    This view is used for on site editing and must be accessible to only
    logged in users."""

    def test_editor_view(self, testapp, diagram):
        testapp.get(f"/diagrams/{diagram['id']}/editor", status=200)

    def test_user_must_be_logged_in(self, testapp, request_host):
        res = testapp.get("/diagrams/abcd/editor", status=303)
        assert res.location.startswith(f"http://{request_host}/login?next=")

    def test_editor_view_can_be_invoked_only_own_diagrams(
        self, testapp, user_factory, diagram
    ):
        testapp.login(user_factory().email)
        testapp.get(f"/diagrams/{diagram['id']}/editor", status=404)

    def test_not_existing_diagram(self, testapp):
        testapp.login()
        testapp.get("/diagrams/abcd/editor", status=404)


class TestDiagramBuiltinEditor:
    """Tests for the diagram builtin editor view.

    This view is embedded via iframe to 3rd party sites."""

    def test_builtin_view(self, testapp, diagram):
        testapp.get(f"/diagrams/{diagram['id']}/builtin", status=200)

    def test_user_must_be_logged_in(self, testapp, request_host):
        res = testapp.get("/diagrams/abcd/builtin", status=303)
        assert res.location.startswith(f"http://{request_host}/login?next=")

    def test_builtin_view_can_be_invoked_only_own_diagrams(
        self, testapp, user_factory, diagram
    ):
        testapp.login(user_factory().email)
        testapp.get(f"/diagrams/{diagram['id']}/builtin", status=404)

    def test_not_existing_diagram(self, testapp):
        testapp.login()
        testapp.get("/diagrams/abcd/builtin", status=404)


class TestDiagramImage:
    """Image view.

    This view is used to render the diagram as an image, that can be publicly
    accessible based on the ``is_public`` property.
    """

    def test_image_view(self, testapp, csrf_headers, diagram):
        resp = testapp.get(f"/diagrams/{diagram['id']}/image.svg", status=200)
        assert resp.body == b"dummy_image"

    def test_not_public_images_accessible_only_to_owner(
        self, testapp, user_factory, diagram
    ):
        # only owner can access the image if it's not public
        testapp.login(user_factory().email)
        testapp.get(f"/diagrams/{diagram['id']}/image.svg", status=404)

        # the view is accessible to not logged in users,
        # but they will get 404 if the diagram it's not public
        testapp.logout()
        testapp.get(f"/diagrams/{diagram['id']}/image.svg", status=404)

    def test_view_not_existing_diagram(self, testapp, csrf_headers):
        testapp.login()
        res = testapp.get("/diagrams/abcd/image.svg", status=404, **csrf_headers)
        assert res.status_code == 404

    def test_no_image(self, testapp, csrf_headers):
        diagram_id = create_diagram(
            testapp, csrf_headers
        )  # create a diagram without image
        testapp.get(f"/diagrams/{diagram_id}/image.svg", status=404)

    def test_public_image(self, testapp, csrf_headers, user_factory, diagram):

        # ensuring that the image is public
        testapp.put(
            f"/diagrams/{diagram['id']}",
            params={"is_public": True},
            status=200,
            **csrf_headers,
        )

        # checking if the owner can access the image
        testapp.get(f"/diagrams/{diagram['id']}/image.svg", status=200)

        # checking if any user can access the image
        testapp.login(user_factory().email)
        testapp.get(f"/diagrams/{diagram['id']}/image.svg", status=200)

        # checking not logged in user can access the image
        testapp.logout()
        testapp.get(f"/diagrams/{diagram['id']}/image.svg", status=200)
