import pytest

from tools import CATEGORIES, ToolError, build_default_registry
from tools.academic import OpenAlexSearch
from tools.code import PythonExecutor
from tools.documents import PDFReader, WebPageReader, _TextExtractor


def test_default_registry_has_10_plus_tools_across_categories():
    reg = build_default_registry()
    assert len(reg) >= 10
    assert set(reg.categories()) == set(CATEGORIES)
    assert len({t.name for t in reg.all()}) == len(reg)


def test_python_exec_returns_stdout():
    out = PythonExecutor().run("print(sum(range(10)))")
    assert out[0].snippet == "45" and out[0].tool == "python_exec"


def test_python_exec_error_is_not_retryable():
    with pytest.raises(ToolError) as e:
        PythonExecutor().run("raise ValueError('boom')")
    assert not e.value.retryable and "boom" in str(e.value)


def test_python_exec_timeout():
    with pytest.raises(ToolError) as e:
        PythonExecutor(exec_timeout=1).run("while True: pass")
    assert not e.value.retryable


def test_python_exec_has_no_api_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    out = PythonExecutor().run("import os; print(os.environ.get('OPENAI_API_KEY'))")
    assert out[0].snippet == "None"


def test_python_exec_can_be_disabled(monkeypatch):
    monkeypatch.setenv("CODE_EXECUTION_ENABLED", "0")
    assert not PythonExecutor().available()


def test_openalex_rebuilds_inverted_abstract():
    assert OpenAlexSearch._abstract({"world": [1], "hello": [0]}) == "hello world"


def test_document_tools_reject_non_urls():
    for tool in (PDFReader(), WebPageReader()):
        with pytest.raises(ToolError) as e:
            tool.run("not a url")
        assert not e.value.retryable


def test_html_extractor_skips_scripts():
    p = _TextExtractor()
    p.feed("<html><head><title>T</title><script>x=1</script></head><body><p>Hello</p></body></html>")
    assert p.title == "T" and p.parts == ["Hello"]
