import tempfile
from functools import partial

import pytest
from click.testing import CliRunner

from schemathesis import commands, runner


@pytest.fixture()
def schemathesis_cmd(testcmd):
    return partial(testcmd, "schemathesis")


def test_commands_help(schemathesis_cmd):
    result = schemathesis_cmd()

    assert result.ret == 0
    assert result.stdout.get_lines_after("Commands:") == ["  run  Perform schemathesis test."]

    result_help = schemathesis_cmd("--help")
    result_h = schemathesis_cmd("-h")

    assert result.stdout.lines == result_h.stdout.lines == result_help.stdout.lines


def test_commands_version(schemathesis_cmd):
    result = schemathesis_cmd("--version")

    assert result.ret == 0
    assert "version" in result.stdout.lines[0]


def test_commands_run_errors(schemathesis_cmd):
    result_no_args = schemathesis_cmd("run")

    assert result_no_args.ret == 2
    assert "Missing argument" in result_no_args.stderr.lines[-1]

    result_invalid = schemathesis_cmd("run", "not-url")

    assert result_invalid.ret == 2
    assert "Invalid SCHEMA" in result_invalid.stderr.lines[-1]

    with tempfile.NamedTemporaryFile() as fp:
        result_missing = schemathesis_cmd("run", fp.name)

    assert result_missing.ret == 2
    assert 'Missing argument, "--url"' in result_missing.stderr.lines[-1]

    result_not_existing = schemathesis_cmd("run", "/does/not/exist.yaml")

    assert result_not_existing.ret == 2
    assert "Invalid SCHEMA" in result_not_existing.stderr.lines[-1]


def test_commands_run_help(schemathesis_cmd):
    result_help = schemathesis_cmd("run", "--help")

    assert result_help.ret == 0
    assert result_help.stdout.lines == [
        "Usage: schemathesis run [OPTIONS] SCHEMA",
        "",
        "  Perform schemathesis test against an API specified by SCHEMA.",
        "",
        "  SCHEMA must be a valid URL or file path pointing to an Open API / Swagger",
        "  specification.",
        "",
        "Options:",
        "  --url TEXT                      URL address of the API, required for SCHEMA",
        "                                  if specified by file.",
        "  -c, --checks [not_a_server_error]",
        "                                  List of checks to run.",
        "  -h, --help                      Show this message and exit.",
    ]


def test_commands_run_schema_uri(mocker):
    m_execute = mocker.patch("schemathesis.runner.execute")
    cli = CliRunner()

    schema_uri = "https://example.com/swagger.json"
    result_schema_uri = cli.invoke(commands.run, [schema_uri])

    assert result_schema_uri.exit_code == 0
    m_execute.assert_called_once_with(schema_uri, base_url=None, checks=runner.DEFAULT_CHECKS)


def test_commands_run_schema_path(mocker):
    m_execute = mocker.patch("schemathesis.runner.execute_from_path")
    cli = CliRunner()

    with tempfile.NamedTemporaryFile() as fp:
        schema_path = fp.name
        url = "https://example.com/api"
        result_schema_path = cli.invoke(commands.run, [schema_path, "--url", url])

    assert result_schema_path.exit_code == 0
    m_execute.assert_called_once_with(schema_path, base_url=url, checks=runner.DEFAULT_CHECKS)
