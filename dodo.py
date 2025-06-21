"""For setup instruction or design please look at the README.rst. For list of available command run:

doit list
"""

from doit import tools
from doit.tools import run_once

DOIT_CONFIG = {"default_tasks": ["_intro"]}


def task__intro():
    """Default task to show welcome message and list available tasks."""
    return {"actions": [lambda: print(__doc__)], "verbosity": 2}


def task__setup_pre_commit():
    """Setup pre-commit hooks."""
    return {
        "actions": ["pre-commit install"],
        "uptodate": [run_once],  # codespell:ignore
    }


def task__create_env_file():
    """Setup pre-commit hooks."""
    return {
        "actions": ["cp .env.template .env"],
        "uptodate": [run_once],  # codespell:ignore
    }


def task__docker_up():
    """Setup pre-commit hooks."""
    return {
        "actions": [
            "docker compose down",
            "docker compose build",
            "docker compose up -d",
        ],
    }


def task_install():
    """Install project."""
    return {
        "actions": ["poetry install"],
        "file_dep": ["pyproject.toml"],
        "targets": ["poetry.lock"],
        "task_dep": ["_create_env_file", "_setup_pre_commit"],
    }


def task_lint():
    """Run linter and formatters against code."""
    return {"actions": [tools.Interactive("pre-commit run -a")], "verbosity": 2}


def task_test():
    """Run tests."""
    return {
        "actions": [tools.Interactive("poetry run pytest %(params)s")],
        "task_dep": ["install", "_docker_up"],
        "verbosity": 2,
        "params": [
            {
                "name": "params",
                "short": "p",
                "default": "",
                "help": "pytest parameters",
            },
        ],
    }


def task_serve():
    """Run development server."""
    return {
        "actions": [
            tools.Interactive(
                "poetry run pserve easy_diagrams/config/development.ini %(params)s"
            )
        ],
        "verbosity": 2,
        "task_dep": ["_docker_up", "install"],
        "params": [
            {"name": "params", "short": "p", "default": "--reload"},
        ],
    }


def task_deploy():
    """Deploy code to production."""
    return {
        "actions": [
            "heroku container:push web",
            "heroku container:release web",
        ],
        "verbosity": 2,
    }


def task_alembic_make_revision():
    """Create new alembic revision to modify the database schema to reflect the model changes."""
    return {
        "actions": [
            tools.Interactive(
                "poetry run alembic -c easy_diagrams/config/development.ini  revision --autogenerate -m '%(comment)s'"
            )
        ],
        "verbosity": 2,
        "task_dep": ["install"],
        "pos_arg": "comment",
    }


def task_alembic_upgrade():
    """Run alembic upgrade to apply the latest revision to the database."""
    return {
        "actions": [
            tools.Interactive(
                "poetry run alembic -c easy_diagrams/config/development.ini upgrade head"
            )
        ],
        "verbosity": 2,
        "task_dep": ["install"],
        "pos_arg": "comment",
    }
