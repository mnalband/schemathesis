Schemathesis
============

|Build| |Coverage| |Version| |Python versions| |License|

Schemathesis is a tool for testing your web applications built with Open API / Swagger specifications.

It reads the application schema and generates test cases which will ensure that your application is compliant with its schema.

The application under test could be written in any language, the only thing you need is a valid API schema in a supported format.

**Supported specification versions**:

- Swagger 2.0
- Open API 3.0.x

More API specifications will be added in the future.

Built with:

- `hypothesis`_

- `hypothesis_jsonschema`_

- `pytest`_

Inspired by wonderful `swagger-conformance <https://github.com/olipratt/swagger-conformance>`_ project.

Installation
------------

To install Schemathesis via ``pip`` run the following command:

.. code:: bash

    pip install schemathesis

Optionally you could install ``requests`` for convenient HTTP calls.

Gitter: https://gitter.im/kiwicom/schemathesis

Usage
-----

To examine your application with Schemathesis you need to:

- Setup & run your application, so it is accessible via the network;
- Write a couple of tests in Python;
- Run the tests via ``pytest``.

Suppose you have your application running on ``http://0.0.0.0:8080`` and its
schema is available at ``http://0.0.0.0:8080/swagger.json``.

A basic test, that will verify that any data, that fit into the schema will not cause any internal server error could
look like this:

.. code:: python

    # test_api.py
    import requests
    import schemathesis

    BASE_URL = "http://0.0.0.0:8080"
    schema = schemathesis.from_uri(f"{BASE_URL}/swagger.json")

    @schema.parametrize()
    def test_no_server_errors(case):
        # `requests` will make an appropriate call under the hood
        response = case.call(BASE_URL)
        assert response.status_code < 500


It consists of four main parts:

1. Schema preparation; ``schemathesis`` package provides multiple ways to initialize the schema - ``from_path``, ``from_dict``, ``from_uri``, ``from_file``.

2. Test parametrization; ``@schema.parametrize()`` generates separate tests for all endpoint/method combination available in the schema.

3. A network call to the running application; ``requests`` will do the job, for example.

4. Verifying a property you'd like to test; In the example, we verify that any app response will not indicate a server-side error (HTTP codes 5xx).

Run the tests:

.. code:: bash

    pytest test_api.py

**Other properties that could be tested**:

- Any call will be processed in <50 ms - you can verify the app performance;
- Any unauthorized access will end with 401 HTTP response code;

Each test function should have the ``case`` fixture, that represents a single test case.

Important ``Case`` attributes:

- ``method`` - HTTP method
- ``formatted_path`` - full endpoint path
- ``headers`` - HTTP headers
- ``query`` - query parameters
- ``body`` - request body

You can use them manually in network calls or can convert to a dictionary acceptable by ``requests.request``:

.. code:: python

    import requests

    @schema.parametrize()
    def test_no_server_errors(case):
        kwargs = case.as_requests_kwargs("http://0.0.0.0:8080")
        response = requests.request(**kwargs)


For each test, Schemathesis will generate a bunch of random inputs acceptable by the schema.
This data could be used to verify that your application works in the way as described in the schema or that schema describes expected behavior.

By default, there will be 100 test cases per endpoint/method combination.
To limit the number of examples you could use ``hypothesis.settings`` decorator on your test functions:

.. code:: python

    from hypothesis import settings

    @schema.parametrize()
    @settings(max_examples=5)
    def test_something(client, case):
        ...

To narrow down the scope of the schemathesis tests it is possible to filter by method or endpoint:

.. code:: python

    @schema.parametrize(method="GET", endpoint="/pet")
    def test_no_server_errors(case):
        ...

The acceptable values are regexps or list of regexps (matched with ``re.search``).

CLI
~~~

The ``schemathesis`` command can be used to perform Schemathesis test cases:

.. code:: bash

    schemathesis run https://example.com/api/swagger.json

If your application requires authorization then you can use ``--auth`` option for Basic Auth and ``--header`` to specify
custom headers to be sent with each request.

CLI supports passing options to ``hypothesis.settings``. All of them are prefixed with ``--hypothesis-``:

.. code:: bash

    schemathesis run --hypothesis-max-examples=1000 https://example.com/api/swagger.json

For the full list of options, run:

.. code:: bash

    schemathesis --help

Explicit examples
~~~~~~~~~~~~~~~~~

If the schema contains parameters examples, then they will be additionally included in the generated cases.

.. code:: yaml

    paths:
      get:
        parameters:
        - in: body
          name: body
          required: true
          schema: '#/definitions/Pet'

    definitions:
      Pet:
        additionalProperties: false
        example:
          name: Doggo
        properties:
          name:
            type: string
        required:
        - name
        type: object


With this Swagger schema example, there will be a case with body ``{"name": "Doggo"}``.  Examples handled with
``example`` decorator from Hypothesis, more info about its behavior is `here`_.

NOTE. Schemathesis supports only examples in ``parameters`` at the moment, examples of individual properties are not supported.

Direct strategies access
~~~~~~~~~~~~~~~~~~~~~~~~

For convenience you can explore the schemas and strategies manually:

.. code:: python

    >>> import schemathesis
    >>> schema = schemathesis.from_uri("http://0.0.0.0:8080/petstore.json")
    >>> endpoint = schema["/v2/pet"]["POST"]
    >>> strategy = endpoint.as_strategy()
    >>> strategy.example()
    Case(
        path='/v2/pet',
        method='POST',
        path_parameters={},
        headers={},
        cookies={},
        query={},
        body={
            'name': '\x15.\x13\U0008f42a',
            'photoUrls': ['\x08\U0009f29a', '\U000abfd6\U000427c4', '']
        },
        form_data={}
    )

Schema instances implement `Mapping` protocol.

Lazy loading
~~~~~~~~~~~~

If you have a schema that is not available when the tests are collected, for example it is build with tools
like ``apispec`` and requires an application instance available, then you can parametrize the tests from a pytest fixture.

.. code:: python

    # test_api.py
    import schemathesis

    schema = schemathesis.from_pytest_fixture("fixture_name")

    @schema.parametrize()
    def test_api(case):
        ...

In this case the test body will be used as a sub-test via ``pytest-subtests`` library.

**NOTE**: the used fixture should return a valid schema that could be created via ``schemathesis.from_dict`` or other
``schemathesis.from_`` variations.

Extending schemathesis
~~~~~~~~~~~~~~~~~~~~~~

If you're looking for a way to extend ``schemathesis`` or reuse it in your own application, then ``runner`` module might be helpful for you.
It can run tests against the given schema URI and will do some simple checks for you.

.. code:: python

    from schemathesis import runner

    runner.execute("http://127.0.0.1:8080/swagger.json")

The built-in checks list includes the following:

- Not a server error. Asserts that response's status code is less than 500;

You can provide your custom checks to the execute function, the check is a callable that accepts one argument of ``requests.Response`` type.

.. code:: python

    from datetime import timedelta
    from schemathesis import runner

    def not_too_long(response):
        assert response.elapsed < timedelta(milliseconds=300)

    runner.execute("http://127.0.0.1:8080/swagger.json", checks=[not_too_long])

Custom string strategies
########################

Some string fields could use custom format and validators,
e.g. ``card_number`` and Luhn algorithm validator.

For such cases it is possible to register custom strategies:

1. Create ``hypothesis.strategies.SearchStrategy`` object
2. Optionally provide predicate function to filter values
3. Register it via ``schemathesis.register_string_format``

.. code-block:: python

    schemathesis.register_string_format("visa_cards", strategies.from_regex(r"\A4[0-9]{15}\Z").filter(luhn_validator)

Documentation
-------------

For the full documentation, please see https://schemathesis.readthedocs.io/en/latest/ (WIP)

Or you can look at the ``docs/`` directory in the repository.

Local development
-----------------

First, you need to prepare a virtual environment with `poetry`_.
Install ``poetry`` (check out the `installation guide`_) and run this command inside the project root:

.. code:: bash

    poetry install

For simpler local development Schemathesis includes a ``aiohttp``-based server with 3 endpoints in Swagger 2.0 schema:

- ``/api/success`` - always returns ``{"success": true}``
- ``/api/failure`` - always returns 500
- ``/api/slow`` - always returns ``{"slow": true}`` after 250 ms delay

To start the server:

.. code:: bash

    ./test_server.sh 8081

It is possible to configure available endpoints via ``--endpoints`` option.
The value is expected to be a comma separated string with endpoint names (``success``, ``failure`` or ``slow``):

.. code:: bash

    ./test_server.sh 8081 --endpoints=success,slow

Then you could use CLI against this server:

.. code:: bash

    schemathesis run http://127.0.0.1:8081/swagger.yaml
    Running schemathesis test cases ...

    -------------------------------------------------------------
    not_a_server_error            2 / 2 passed          PASSED
    -------------------------------------------------------------

    Tests succeeded.


Contributing
------------

Any contribution in development, testing or any other area is highly appreciated and useful to the project.

Please, see the `CONTRIBUTING.rst`_ file for more details.

Python support
--------------

Schemathesis supports Python 3.6, 3.7 and 3.8.

License
-------

The code in this project is licensed under `MIT license`_.
By contributing to ``schemathesis``, you agree that your contributions
will be licensed under its MIT license.

.. |Build| image:: https://github.com/kiwicom/schemathesis/workflows/build/badge.svg
   :target: https://github.com/kiwicom/schemathesis/actions
.. |Coverage| image:: https://codecov.io/gh/kiwicom/schemathesis/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/kiwicom/schemathesis/branch/master
   :alt: codecov.io status for master branch
.. |Version| image:: https://img.shields.io/pypi/v/schemathesis.svg
   :target: https://pypi.org/project/schemathesis/
.. |Python versions| image:: https://img.shields.io/pypi/pyversions/schemathesis.svg
   :target: https://pypi.org/project/schemathesis/
.. |License| image:: https://img.shields.io/pypi/l/schemathesis.svg
   :target: https://opensource.org/licenses/MIT

.. _hypothesis: https://hypothesis.works/
.. _hypothesis_jsonschema: https://github.com/Zac-HD/hypothesis-jsonschema
.. _pytest: http://pytest.org/en/latest/
.. _poetry: https://github.com/sdispater/poetry
.. _installation guide: https://github.com/sdispater/poetry#installation
.. _here: https://hypothesis.readthedocs.io/en/latest/reproducing.html#providing-explicit-examples
.. _CONTRIBUTING.rst: https://github.com/kiwicom/schemathesis/blob/contributing/CONTRIBUTING.rst
.. _MIT license: https://opensource.org/licenses/MIT
