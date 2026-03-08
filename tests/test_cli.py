"""Tests for CLI."""

from pathlib import Path

from typer.testing import CliRunner

from repo2ctx.cli import app

runner = CliRunner()


def test_cli_basic(tmp_path: Path):
    (tmp_path / "hello.py").write_text("print('hello')")
    result = runner.invoke(app, [str(tmp_path)])
    assert result.exit_code == 0
    assert "Repository Context" in result.stdout


def test_cli_max_tokens(tmp_path: Path):
    (tmp_path / "hello.py").write_text("print('hello')")
    result = runner.invoke(app, [str(tmp_path), "--max-tokens", "50000"])
    assert result.exit_code == 0
    assert "50000" in result.stdout


def test_cli_format_xml(tmp_path: Path):
    (tmp_path / "hello.py").write_text("x = 1")
    result = runner.invoke(app, [str(tmp_path), "--format", "xml"])
    assert result.exit_code == 0
    assert "<repository-context>" in result.stdout


def test_cli_format_json(tmp_path: Path):
    (tmp_path / "hello.py").write_text("x = 1")
    result = runner.invoke(app, [str(tmp_path), "--format", "json"])
    assert result.exit_code == 0
    assert '"files"' in result.stdout


def test_cli_invalid_path():
    result = runner.invoke(app, ["/nonexistent/path"])
    assert result.exit_code == 1


def test_cli_invalid_format(tmp_path: Path):
    result = runner.invoke(app, [str(tmp_path), "--format", "pdf"])
    assert result.exit_code == 1


def test_cli_include(tmp_path: Path):
    (tmp_path / "a.py").write_text("pass")
    (tmp_path / "b.js").write_text("pass")
    result = runner.invoke(app, [str(tmp_path), "--include", "*.py"])
    assert result.exit_code == 0
    assert "a.py" in result.stdout
    assert "b.js" not in result.stdout


def test_cli_exclude(tmp_path: Path):
    (tmp_path / "a.py").write_text("pass")
    (tmp_path / "b.py").write_text("pass")
    result = runner.invoke(app, [str(tmp_path), "--exclude", "b.py"])
    assert result.exit_code == 0
    assert "a.py" in result.stdout


def test_cli_output_file(tmp_path: Path):
    (tmp_path / "hello.py").write_text("print('hello')")
    out = tmp_path / "output.md"
    result = runner.invoke(app, [str(tmp_path), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "Repository Context" in content


def test_cli_model_claude(tmp_path: Path):
    (tmp_path / "hello.py").write_text("print('hello')")
    result = runner.invoke(app, [str(tmp_path), "--model", "claude"])
    assert result.exit_code == 0
    assert "claude" in result.stdout


def test_cli_no_args():
    result = runner.invoke(app, [])
    # Should show help or exit with non-zero
    assert result.exit_code != 0 or "Usage" in result.stdout
