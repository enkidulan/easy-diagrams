import os
import os.path
import random
import time

import base36
import pytest
import transaction
from pyramid.paster import get_appsettings
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import text

import alembic
import alembic.command
import alembic.config
from easy_diagrams import main
from easy_diagrams import models
from easy_diagrams.models.meta import Base


@pytest.fixture(name="test_id")
def fixture_test_id():
    return f"{base36.dumps(time.time_ns() * 10000 + random.randint(0, 9999))}"


def pytest_addoption(parser):
    parser.addoption(
        "--ini",
        action="store",
        metavar="INI_FILE",
        help="Location of the .ini file to use for testing. Note that some values will be overridden by fixtures.",
    )
    parser.addoption(
        "--db-migration",
        action="store_true",
        help="Don't run alembic migrations, instead call `Base.metadata.create_all` to speed development",
    )


@pytest.fixture(scope="session")
def ini_file(request):
    return os.path.abspath(
        request.config.option.ini or "easy_diagrams/config/development.ini"
    )


@pytest.fixture(scope="session")
def app_settings(ini_file):
    return get_appsettings(ini_file)


@pytest.fixture(scope="session")
def app(app_settings):
    """Pyramid WSGI application for the tests with the database engine."""
    return main({}, **app_settings)


@pytest.fixture
def request_host():
    """Request host."""
    yield "example.com"


@pytest.fixture
def tm():
    """Transaction manager for the tests. It creates a new transaction at the beginning of the test and aborts it at the end."""
    tm = transaction.TransactionManager(explicit=True)
    tm.begin()
    tm.doom()

    yield tm

    tm.abort()


@pytest.fixture
def dbsession(app, tm, dbengine):
    """Database session for the tests."""
    session_factory = app.registry["dbsession_factory"]
    return models.get_tm_session(session_factory, tm)


@pytest.fixture(scope="session")
def db_janitor(app_settings):
    """Create a new test database and delete it after testing is done. Fixture patches the app settings `sqlalchemy.url` to use the new database."""

    with DatabaseJanitor(
        user="admin",
        password="admin",
        dbname=f"test_db_{base36.dumps(int(time.time()) * 10000 + random.randint(0, 9999))}",
        host="localhost",
        port=5432,
        version=17,
    ) as db_janitor:
        db_uri = f"postgresql+psycopg://admin:admin@localhost:5432/{db_janitor.dbname}"
        # setting config and env variables to use the new database
        app_settings["sqlalchemy.url"] = db_uri
        os.environ["ED_SQLALCHEMY_URL"] = db_uri
        yield db_janitor


@pytest.fixture(scope="session")
def dbengine(app_settings, ini_file, request, db_janitor):
    """Database engine for the tests. It creates the database schema or runs migrations based on `--db-migration` flag."""

    engine = models.get_engine(app_settings)
    alembic_cfg = alembic.config.Config(ini_file)

    Base.metadata.drop_all(bind=engine)
    alembic.command.stamp(alembic_cfg, None, purge=True)

    # run migrations to initialize the database
    # depending on how we want to initialize the database from scratch
    # we could alternatively call:
    if request.config.getoption("--db-migration"):
        Base.metadata.create_all(bind=engine)
        alembic.command.stamp(alembic_cfg, "head")
    else:
        alembic.command.upgrade(alembic_cfg, "head")

    yield engine

    Base.metadata.drop_all(bind=engine)
    alembic.command.stamp(alembic_cfg, None, purge=True)


@pytest.fixture(autouse=True)
def db_savepoint(dbengine):
    """Create a database savepoint before each e2e test and rollback after."""
    connection = dbengine.connect()
    trans = connection.begin()

    # Create savepoint
    connection.execute(text("SAVEPOINT test_savepoint"))

    yield connection

    # Rollback to savepoint
    connection.execute(text("ROLLBACK TO SAVEPOINT test_savepoint"))
    trans.rollback()
    connection.close()
