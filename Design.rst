EasyDiagrams MVP
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

