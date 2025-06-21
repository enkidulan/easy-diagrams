from logging import getLogger
from subprocess import PIPE
from subprocess import Popen

from pyramid.request import Request

from easy_diagrams import interfaces
from easy_diagrams.domain.diagram import Diagram

logger = getLogger(__name__)


class PlantUMLRendererService:

    def __init__(self, settings):
        self.settings = settings

    def render(self, diagram: Diagram) -> bytes:
        return convert(
            diagram.code,
            use_local_plantuml=self.settings.get("use_local_plantuml") == "true",
        )


def convert(puml, use_local_plantuml=False) -> bytes:

    if use_local_plantuml:
        cmd = ["plantuml", "-tpng", "-p"]
    else:
        cmd = ["java", "-jar", "/plantuml/plantuml.jar", "-tpng", "-p"]

    proc = Popen(
        cmd,
        stdout=PIPE,
        stdin=PIPE,
        stderr=PIPE,
        env={"PLANTUML_LIMIT_SIZE": "8192", "PLANTUML_SECURITY_PROFILE": "SANDBOX"},
        cwd="/tmp/",
    )
    stdout_data, stderrs = proc.communicate(input=puml.encode())
    if proc.returncode != 0:
        logger.warning("PlantUML error detected: %s", stderrs)
    return stdout_data


def renderer_factory(context, request: Request):
    return PlantUMLRendererService(request.registry.settings)


def includeme(config):
    config.register_service_factory(renderer_factory, interfaces.IDiagramRenderer)
