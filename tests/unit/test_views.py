from easy_diagrams.views.home import home_view
from easy_diagrams.views.notfound import notfound_view


def test_home_view_success(app_request):
    info = home_view(app_request)
    assert app_request.response.status_int == 200
    assert info["one"] == "one"
    assert info["project"] == "easy_diagrams"


def test_notfound_view(app_request):
    info = notfound_view(app_request)
    assert app_request.response.status_int == 404
    assert info == {}
