Plantuml Easy Share
===================

For more context on system design see Design.rst


Getting Started
---------------

System dependencies
~~~~~~~~~~~~~~~~~~~

Before you start, make sure you have the following dependencies installed:

* Python 3.11
* Docker
* pipx - https://pipx.pypa.io/stable/installation/


Installation
~~~~~~~~~~~~~~~~~~~

Use ``pipx`` to install build requirements::

    pipx install poetry pre-commit doit

Now you can use ``doit`` to install dependencies and setup the project::

    doit install

Update ``.env`` file with your settings.


Running the tests
~~~~~~~~~~~~~~~~~~~

To run the tests, use the following command::

    doit test -p "--pdb"

You can provide additional arguments to ``pytest`` by passing them to the
``-p`` option.


Running the server
~~~~~~~~~~~~~~~~~~~

To run the server, use the following command::

    doit serve


Deployment
~~~~~~~~~~~~~~~~~~~

To deploy the application to production, use the following command::

    doit deploy

``Dockerfile`` is used to build the production image and push it to the registry.


Configuration
~~~~~~~~~~~~~~~~~~~

Application configuration lives in ``easy_diagrams/config/development.ini`` and
``easy_diagrams/config/production.ini`` files. You can override these settings
by providing environment variables with the same name prefixed with ``ED_``.


CI/CD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The project uses GitHub Actions for CI/CD. The configuration is stored in
``.github/workflows`` directory.

Heroku Docker is used for deployment.

Docker images
^^^^^^^^^^^^^^^^^^^^

The project uses ``enkidulan/plantuml`` Docker images as a base for the PlantUML,
the image is build from ``Dockerfile.plantuml`` and pushed to Docker:

.. code-block:: bash

    docker build -t enkidulan/plantuml:1.2024.8 -t enkidulan/plantuml:latest --build-arg PLANTUML_VERSION=1.2024.8 -f Dockerfile.plantuml .
    docker push enkidulan/plantuml:1.2024.8
