EasyDiagrams
===================


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


EasyDiagrams Design
============================

Use cases
----------------
**Vocabulary:**

- Visitor - someone accessing the site without being logged in
- User - someone who is logged in
- Code - PlantUML code that can be rendered into an image
- Image - an image rendered from UML
- Rendering - a process of turning a code into an image
- Diagram - a document that stores UML and its Render

.. code-block:: text

    As a **visitor**,
    I want to sign up using my Google account
    And agree to the terms and conditions,
    So that I can become a **user** and use the service.

    As a **user**,
    I want to create a new **diagram** document,
    so that I can keep both the **UML** code and its **image** accessible online.

    As a **user**,
    I want a **diagram** editing page with a live preview of the **image**,
    so that editing is straightforward and easy.

    As a **user**,
    I want an embeddable **diagram** editing page,
    so that it can be easily and seamlessly integrated into third-party solutions.

    As a **user**,
    I want to be able to make my **diagram**’s **image** public,
    so that I can share it with any **visitors**.

    As a **user**,
    I want to see a list of all my **diagrams**,
    so that I can manage them effectively.

    As a **user**,
    I want to be able to delete a **diagram**,
    so that I can remove it when it’s no longer needed.

Constraints and assumptions
----------------------------------

- PlantUML takes a significant amount of time to render a diagram, around 1s on average, which may pose challenges to user experience and infrastructure requirements.

Access patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After creation, a diagram will have an initial spike of changes as people keep updating and refining it. But after that, the diagram will be rarely changed, if ever, and will mainly serve view requests. View requests are expected to be 100 times more common than change requests.

Initial MVP
----------------------------------

Goals
~~~~~~~~~~~~~~~~~~~~~~~~~~~


The main goal of the initial MVP is to **provide basic functionality** for storing and embedding diagrams at **minimal development, maintenance, and infrastructure costs**. Performance and scalability are not on the list of priorities for the initial stage. The MVP should be able to handle up to 20 active users with less than 1K diagrams each, with a top load expected to be less than 100 reps.

Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~


The initial model will accommodate the basic functionality of user and diagram records. Both code and image are stored as diagram properties; the `is_public` property is used for access control.

.. image:: https://easydiagrams.work/diagrams/jT3oIjGnZhLoSHJlYzOeP8XkRjmdUjmY/image.svg
    :align: center

Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given that the initial MVP doesn’t have to deal with large scale and load, most of the interactions are trivial to the point that many mainstream web frameworks provide needed functionality out-of-the-box. The only challenging part is the requests that involve PlantUML rendering, as it takes a long time to transform code into image, anywhere from 0.7 to 1.5  seconds. The right approach to deal with slow tasks is to decouple them from a request lifetime via any of the asynchronous processing methods (message queue, events, etc…). Nonetheless, for the initial MVP it makes more sense to keep it simple and have the synchronous execution flow for all requests, even ones that are slow and include PlantUML rendering:

.. image:: https://easydiagrams.work/diagrams/malJ31fEBmO1HqWXM1BcC46tYyRM5Ell/image.svg
    :align: center

The downside of this approach is that **PlantUML rendering requests will clog the system** as they are **30x times slower** than other types of requests (1400 ms for rendering image vs 40 ms viewing).  Introducing **non-rendering instances will mitigate the issue**, which can be easily achieved with reverse proxy redirecting all requests involving changes to UML to dedicated instances.

infrastructure
----------------------------------


Storage layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Except for the rendered diagram image, the data is well suited for storing in any classical relational database. However, to avoid adding any operational overhead or complexity,  it makes sense to store images in the same database, especially as the rendered diagram image is an SVG file that is not much bigger than the code itself, so it also may work as good long-term solution.

**Notes on rendered image size:** The images stored as a compressed SVG are at most five times larger than the code. The raw SVG is ~20x larger than the size of the code, and, as the size of the code rarely exceeds 2KB, the image size in most cases will be under 40KB. Adding lz4 compression usually reduces the SVG image size by at least 4, so most SVG images in a compressed state will be smaller than 10KB.

Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For small applications, Heroku is the easiest option for managing infrastructure, as it takes care of many tasks: TLS/SSL, routing, discovery, code delivery, database management, logging, performance monitoring, and error tracking. Additionally, Heroku offers a good deal in terms of price and functionality. Web application will be shipped as a Docker container that is build with GitHub Actions as a CI/CD pipeline.

.. image:: https://easydiagrams.work/diagrams/uJXaWLmPOopwiWiEvWz0vLI32Ru7ZXG1/image.svg
    :align: center


**Backend**. For the backend web framework, Pyramid is a good choice for the MVP. It’s easy to use, offers good performance, and its design makes it straightforward to adopt a component-based architecture from the start, allowing the application to scale without turning into a “big ball of mud.” Pyramid also has a rich ecosystem of plugins that cover most of the MVP’s needs—not to mention that Pyramid is my favorite framework.

**Database**. For the database, PostgreSQL is the best choice (as it is best default choice for most applications). It’s well-suited for the MVP, fully supported by Heroku out of the box, provides ACID guaranties, and has great performance.

**Frontend**. For the frontend, HTMX is ideal because it allows you to create a dynamic web application with minimal effort and without writing any JavaScript or setting up a build pipeline. That’s a huge advantage for an MVP (especially that I'm short on good JS dev). The backend rendering will be handled by Pyramid, and for the design and layout, Bootstrap is a great option since it’s easy to use and comes with many ready-to-use components.



EasyDiagrams Roadmap
====================

Context
-------

EasyDiagrams' initial MVP has very limited functionality and throughput. Although it is fine
for now, the performance and lack of basic features will become problematic when the number
of active users reaches a few dozen.

Objective
---------

This document aims to define a multistage strategy for improving the system's performance
and functionality while maintaining an optimal performance-to-cost balance and allowing for
organic growth. The goal is to establish a refactoring framework/guideline with clearly
defined steps, where each step has an assigned priority and enables a class of features
while addressing certain functional/non-functional aspects. This approach minimizes the
likelihood of needing to redesign and rewrite the system in the future.

Restrictions
------------

Keep the budget as low as possible and minimize development and maintenance costs.

Analysis
--------

Access Patterns
^^^^^^^^^^^^^^^

There are several different types of traffic that the system will have to handle:

- **Image Viewing** traffic, including the built-in editor view, is the most common type of
  traffic in the system and easily exceeds hundreds of RPS.
- **Image Rendering** traffic is another common type of traffic that a user will generate
  frequently after creating a new diagram, measured in tens of requests per diagram. This
  is also the slowest part of the traffic, as image rendering takes approximately 1.2
  seconds.
- **Diagram Management** traffic includes listing, creation, deletion, access management,
  and renaming diagrams. It’s a common access pattern, but still not one that generates a
  lot of traffic.
- **Landing Page** traffic is not very common, as the landing page is visited only by
  newcomers or users wanting to create a diagram.
- **Static Resource** (non-diagram related) traffic consists of resources that are usually
  kept on a CDN.
- **Registration and Authentication** traffic is the least common type of traffic to the
  system.

The traffic generated by **registration, authentication**, and **diagram management**
activities is relatively low, and the initial MVP provides sufficient performance.
Therefore, there likely won’t be a need to worry about it until the system grows to
hundreds of users and millions of diagrams.

**Image Rendering** is another story, as the initial MVP can handle approximately 3 RPS at
most, which significantly limits the number of users working at the same time.

Since diagrams can be made public, **Image Viewing** traffic does not directly correlate
with the number of active users. The initial MVP can handle 3K RPS, which is quite good
for a demo project, but for production, it may be too low given the nature of the traffic.

Benchmarks
^^^^^^^^^^

Benchmarking is done on System76 24GB Intel i7-10510U laptop with 100/10 Mb internet speed
access against the following server configuration:

::

   DB: heroku-postgresql:essential-0
   Server: Heroku Basic Dyno 512MB RAM supporting up to 10 processes

**Public image**::

   » oha -n 10000 -c 100 https://easydiagrams.work/diagrams/{diagram_id}/image.svg
   Summary:
     Success rate: 100.00%
     Requests/sec: 3064.2384
     Size/request: 2.88 KiB

   Response time histogram:
     0.042 [9223] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
     0.067 [630]  |■■

**Builtin Editor**::

   » oha -n 10000 -c 100  https://easydiagrams.work/diagrams/{diagram_id}/builtin
   Summary:
     Success rate: 100.00%
     Requests/sec: 617.2529
     Size/request: 6.97 KiB

   Response time histogram:
     0.153 [5609] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
     0.209 [3424] |■■■■■■■■■■■■■■■■■■■
     0.264 [780]  |■■■■

**Update diagrams title**::

   » oha -n 10000 -c 100 -m PUT https://easydiagrams.work/diagrams/{diagram_id}?title=demo
   Summary:
     Success rate: 100.00%
     Requests/sec: 532.8398
     Size/request: 1.42 KiB

   Response time histogram:
     0.160 [4240] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
     0.224 [3544] |■■■■■■■■■■■■■■■■■■■■■■■■■■
     0.287 [1449] |■■■■■■■■■■
     0.350 [504]  |■■■
     0.413 [168]  |■

**Diagram rendering**::

   » oha -n 1000 -c 5 -m PUT https://easydiagrams.work/diagrams/{diagram_id}?code=
   Summary:
     Success rate: 100.00%
     Requests/sec: 1.9496
     Size/request: 1.30 KiB

   Response time histogram:
      2.034 [274] |■■■■■■■■■■■■■■■
      3.058 [583] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
      4.081 [76]  |■■■■
      5.104 [33]  |■

**Landing page**::

   » oha -n 10000 -c 100  'https://easydiagrams.work'
   Summary:
     Success rate: 100.00%
     Requests/sec: 940.5573
     Size/request: 2.48 KiB

   Response time histogram:
     0.113 [8634] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
     0.144 [1129] |■■■■

**Static resources**::

   » oha -n 10000 -c 100  'https://easydiagrams.work/static/js/scripts.js'
   Summary:
     Success rate: 100.00%
     Requests/sec: 3358.4031
     Size/request: 1.3 KB

   Response time histogram:
     0.050 [9681] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

Roadmap
-------

Given the access patterns and benchmark results, the diagram rendering view is the first
area that requires significant improvement. The next areas to address are the image and
built-in editor views, as they are the most common access patterns. Consequently, the
roadmap focuses primarily on these areas while also incorporating some functional
improvements. Broader performance optimizations will address the rest of the logic.

The most effective approach to implementing these improvements is as follows:

1. **Introduce image versioning**
2. **Make rendering asynchronous** with horizontally scalable renderers
3. **Implement an effective caching strategy**
4. **Extend the data model** and support database sharing
5. **Implement performance-critical parts in Rust** (for cases where Python becomes a
   bottleneck)
6. **Move static assets** to CDN

The roadmap places high-priority items at the top, with each step enabling the subsequent
one. Low-priority items remain at the bottom. While performance optimization and
horizontal scaling are top priorities, the plan also aims to keep scaling to a minimum.

Step 1. Image Versioning
^^^^^^^^^^^^^^^^^^^^^^^^

**Image versioning** is important because it enables asynchronous rendering and effective
caching. The approach involves adding two version fields, **code_version** and
**image_version**, to track changes in the code and the image:

1. **code_version** is generated immediately after the code is updated and can be returned
   to the user. This version is a unique, incrementing value (for instance, a timestamp
   combined with a random suffix).
2. **image_version** is set to the **code_version** of the code from which the image was
   rendered.

If **image_version** does not match **code_version**, it indicates that the image is
outdated and should be regenerated, or that the code is invalid.

`Image versioning example <https://easydiagrams.work/diagrams/gNeq7FKv3nVR7Fzi8XS0V11nsqcyrzyK/builtin>`_

Step 2. Async Image Rendering
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Context**: PlantUML requires about 0.5 to 1.5 seconds to render an image. Making a UI request wait
that long for a rendered image is detrimental to scalability because it blocks the server
and prevents it from handling other requests.

**Goal**: Implement a more efficient way of dealing with image rendering requests.

**Solution**:  By delegating image rendering to an asynchronous task, the server can immediately respond
with HTTP 204 and free itself to handle other requests, while background workers can be
scaled out to accommodate the rendering load.

To obtain a new rendered image, the UI uses long polling until the **image_version**
matches the **code_version**. Long polling is straightforward to implement and doesn’t
require additional infrastructure, but a backoff safeguard is necessary to mitigate the
possibility of DoS-ing the service. Eventually, long polling can be replaced with WebSockets
or server push notifications for more efficient updates.

`Async rendering example <https://easydiagrams.work/diagrams/d6FVp61ao9bTwqFRZNp0mNzcg7g9rbDH/builtin>`_

To communicate with workers, the server uses a queue table in the same database that stores
the diagram data. This design choice follows the **transactional outbox pattern** to
guarantee atomicity and consistency. Additionally, due to the nature of image rendering,
only the most recent message matters—something that is not trivial to implement with typical
messaging brokers like RabbitMQ or SQS. However, PostgreSQL naturally supports this via
``INSERT INTO … ON CONFLICT (id) DO UPDATE`` syntax. Since the database is already
provisioned, this approach also avoids introducing any additional infrastructure overhead.

`Transactional outbox example <https://easydiagrams.work/diagrams/Fge9fF4CaTCXqOJOaolVz0sCuTFq7b6V/builtin>`_

The downside of this approach is that managing the queue table is now the responsibility of
the application logic. However, there are many frameworks that provide the required
functionality. **Dramatiq** is especially well-suited because it supports PostgreSQL as a
task broker. By customizing the relevant parts of Dramatiq, you can insert or update tasks
based on the ``diagram_id``, ensuring that each diagram has at most one associated task.

- `Dramatiq Actor reference <https://github.com/Bogdanp/dramatiq/blob/b372f431ae40ff383a5b450dc37c8e5d5671bf49/dramatiq/actor.py#L124>`_
- `Dramatiq PostgreSQL broker <https://gitlab.com/dalibo/dramatiq-pg/-/blob/master/dramatiq_pg/broker.py?ref_type=heads#L108>`_

Step 3. Caching
^^^^^^^^^^^^^^^

**Goal**:Reduce database load.

**Context**:Diagrams have two access patterns:

1. **Editing:** Frequent changes during the active editing phase.
2. **Viewing:** After the initial editing phase, diagrams remain static, and users only
   view them.

The second pattern accounts for the majority of diagram endpoint traffic. It doesn’t make
sense to query the database repeatedly for content that no longer changes, making caching
especially beneficial. However, diagrams in the editing phase require quick propagation of
changes (within minutes). Simply caching database query results for a few minutes helps
alleviate hot spots but won’t greatly impact most diagrams, which might be viewed several
times per day over a few weeks. For meaningful performance benefits, **longer caching** is
necessary.

**Solution**: A more advanced caching strategy is needed to accommodate both editing (frequent changes)
and viewing (static content). A **local shared long-term cache** with an eviction strategy
that monitors changes alongside passing image versions for editorial workflow solves both
requirements.

- **Local cache on each instance** avoids additional infrastructure and reduces maintenance
  costs.
- **Scales with the number of instances**.

Leveraging tools like `diskcache <https://pypi.org/project/diskcache/>`_ for large,
long-term storage that doesn’t require significant RAM is the best option for a local cache,
especially as diskcache supports sharing the cache among multiple processes and can offer
performance similar to or better than Memcache or Redis.

Query Workflow for the Image Endpoint
'''''''''''''''''''''''''''''''''''''

1. Check if the requested diagram is in the cache.
2. If not, query the database.

The URL for viewing an image is ``/{id}/image.svg`` — this is the URL that is embedded
in external services. For editing, the editor explicitly provides the image version:
``/{id}/image.svg?v=123``. This versioning ensures the cache always returns an image
version that is equal to or newer than what the editor requested. Consequently, the editor
sees the latest version instead of any stale cached content.

`Caching example <https://easydiagrams.work/diagrams/vt9MBbfOHqgMTTGyxODev3xipiblIAYZ/builtin>`_

While an editor can see the updates right away, additional logic is needed to promote
changes to other users. This is where the eviction process comes in: every two minutes,
each instance runs a process that retrieves a list of images changed since the last run
and evicts them from the cache. The cache, by default, has an eviction timeout of 24 hours,
so even if the eviction process fails, the record won’t stay in the cache for more than a
day.

`Eviction process example <https://easydiagrams.work/diagrams/gDz2oz8WLArSguDWgkMsMsrUdQGcJuu6/builtin>`_

The eviction process uses long polling on the database, which does create some additional
load, but it’s much simpler and more reliable than using pub-sub, and it does not require
any additional infrastructure. The amount of data that the eviction process pulls is limited
to the IDs, so even in the case of tens of thousands of IDs, it should still perform well.
However, the ``image_version`` field must be indexed to support range queries. Additionally,
if the eviction process hasn’t run for more than three hours, it must evict all records in
the local cache without making any DB queries.

**Diskcache performance** (from the project's benchmarks)::

   In [1]: import pylibmc
   In [2]: client = pylibmc.Client(['127.0.0.1'], binary=True)
   In [3]: client[b'key'] = b'value'
   In [4]: %timeit client[b'key']

   10000 loops, best of 3: 25.4 µs per loop

   In [5]: import diskcache as dc
   In [6]: cache = dc.Cache('tmp')
   In [7]: cache[b'key'] = b'value'
   In [8]: %timeit cache[b'key']

   100000 loops, best of 3: 11.8 µs per loop

Step 4. Extending Model and Database Sharding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Goal**:Extend the existing model and provide a basis for effective DB sharding.

**Context**:The MVP’s initial model provides only the most basic feature and does not support much of
the functionality users usually want, such as organizing diagrams in folders or sharing
diagram ownership.

**Solution**: A diagram is UML code plus a rendered image that can be displayed. A user can create and
update diagrams. A diagram belongs to a single account, and each account always has exactly
one owner. A user can own multiple accounts. In addition to the owner, an account can
include multiple users who can access its diagrams, and a user can be a part of many
accounts. A diagram can be placed in a folder, and a folder can be placed in another folder.
A folder or diagram can belong to only one folder at most. A user can make a diagram
publicly accessible.

Extend the Existing Model for Effective Database Sharding
''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The MVP’s initial model offers only the most basic features and does not support many of
the functionalities users typically expect, such as organizing diagrams in folders or
sharing diagram ownership.

The extended model must support the following use cases:

- A **diagram** consists of UML code and a rendered image that can be displayed.
- A **user** can create and update diagrams.
- A **diagram** belongs to a single **account**, and each account always has exactly one
  owner.
- A user can own multiple accounts.
- In addition to the owner, an account can include multiple users who can access its
  diagrams; similarly, a user can belong to multiple accounts.
- A **diagram** can be placed in a **folder**, and folders can be nested within other
  folders.
- A folder or diagram can belong to only one folder at a time.
- A user can make a diagram publicly accessible.

`New model example <https://easydiagrams.work/diagrams/gcIoNGCclM1lMZ5P3ExT7Hu72FZx21VC/builtin>`_

SQL ERD for the new model:

`SQL ERD <https://easydiagrams.work/diagrams/LI3vzyrzPrUyk1fwdCgwwfiwiAgGDAyi/builtin>`_

In the new model, sharding is done by account, with minimal denormalization of the user
model. The constraint changes from requiring a globally unique user email to ensuring that
each email is unique within its account. This provides an effective solution for both
supporting users belonging to multiple accounts and enabling sharding.
