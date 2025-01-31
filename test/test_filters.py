import pytest

from .utils import integer


@pytest.mark.parametrize("endpoint", ("'/foo'", "'/v1/foo'", ["/foo"], "'/.*oo'"))
def test_endpoint_filter(testdir, endpoint):
    # When `endpoint` is specified
    parameters = {"parameters": [integer(name="id", required=True)]}
    testdir.make_test(
        """
@schema.parametrize(endpoint={})
@settings(max_examples=5)
def test_(request, case):
    request.config.HYPOTHESIS_CASES += 1
    assert case.path == "/v1/foo"
    assert case.method == "GET"
""".format(
            endpoint
        ),
        paths={"/foo": {"get": parameters}, "/bar": {"get": parameters}},
    )
    result = testdir.runpytest("-v", "-s")
    result.assert_outcomes(passed=1)
    # Then only tests for this endpoints should be generated
    result.stdout.re_match_lines([r"test_endpoint_filter.py::test_\[GET:/v1/foo\] PASSED"])


@pytest.mark.parametrize("method", ("'get'", "'GET'", ["GET"], ["get"]))
def test_method_filter(testdir, method):
    # When `method` is specified
    parameters = {"parameters": [integer(name="id", required=True)]}
    testdir.make_test(
        """
@schema.parametrize(method={})
@settings(max_examples=1)
def test_(request, case):
    request.config.HYPOTHESIS_CASES += 1
    assert case.path in ("/v1/foo", "/v1/users")
    assert case.method == "GET"
""".format(
            method
        ),
        paths={"/foo": {"get": parameters}, "/bar": {"post": parameters}},
    )
    result = testdir.runpytest("-v", "-s")
    result.assert_outcomes(passed=2)
    # Then only tests for this method should be generated
    result.stdout.re_match_lines(
        [r"test_method_filter.py::test_\[GET:/v1/foo\] PASSED", r"test_method_filter.py::test_\[GET:/v1/users\] PASSED"]
    )


def test_loader_filter(testdir):
    testdir.make_test(
        """
@schema.parametrize()
@settings(max_examples=1)
def test_(request, case):
    request.config.HYPOTHESIS_CASES += 1
    assert case.path == "/v1/foo"
    assert case.method == "POST"
""",
        paths={
            "/foo": {"post": {"parameters": []}, "get": {"parameters": []}},
            "/bar": {"post": {"parameters": []}, "get": {"parameters": []}},
        },
        method="POST",
        endpoint="/v1/foo",
    )
    result = testdir.runpytest("-v", "-s")
    result.assert_outcomes(passed=1)
    result.stdout.re_match_lines([r"Hypothesis calls: 1$"])


def test_override_filter(testdir):
    testdir.make_test(
        """
@schema.parametrize(method=None, endpoint="/v1/users")
@settings(max_examples=1)
def test_(request, case):
    request.config.HYPOTHESIS_CASES += 1
    assert case.path == "/v1/users"
    assert case.method == "GET"
""",
        paths={"/foo": {"post": {"parameters": [integer(name="id", required=True)]}}},
        method="POST",
        endpoint="/v1/foo",
    )
    result = testdir.runpytest("-v", "-s")
    result.assert_outcomes(passed=1)
    result.stdout.re_match_lines([r"Hypothesis calls: 1$"])
