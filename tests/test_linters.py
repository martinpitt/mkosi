# SPDX-License-Identifier: LGPL-2.1-or-later

import glob
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from mkosi.run import run

# tolerate missing tools in some random dev environment, but enforce them in CI/mkosi box
SKIP_MISSING_TOOLS = "MKOSI_IN_BOX" not in os.environ

REPO_ROOT = Path(__file__).parent.parent


def _kernel_install_files() -> list[str]:
    """Get list of kernel-install/*.install files."""
    return glob.glob(os.fspath(REPO_ROOT / "kernel-install/*.install"))


def _skip_if_missing(tool: str) -> bool:
    """Return True if we should skip the test because tool is missing."""
    return SKIP_MISSING_TOOLS and shutil.which(tool) is None


@pytest.mark.skipif(_skip_if_missing("ruff"), reason="ruff not found")
def test_ruff_format_check() -> None:
    """Check that code is formatted with ruff format."""
    run(["ruff", "format", "--check", "--diff", "mkosi/", "tests/", *_kernel_install_files()], cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("ruff"), reason="ruff not found")
def test_ruff_check() -> None:
    """Check code quality with ruff."""
    run(
        ["ruff", "check", "--output-format=github", "mkosi/", "tests/", *_kernel_install_files()],
        cwd=REPO_ROOT,
    )


def test_no_tabs_in_code() -> None:
    """Ensure no tabs are used in Python code."""
    result = run(["git", "grep", "-P", r"\t", "*.py"], check=False, cwd=REPO_ROOT)
    assert result.returncode != 0, "Found tabs in Python code"


@pytest.mark.skipif(_skip_if_missing("codespell"), reason="codespell not found")
def test_codespell() -> None:
    """Check spelling with codespell."""
    run(["codespell", "--version"], cwd=REPO_ROOT)
    files = run(["git", "ls-files"], stdout=subprocess.PIPE, cwd=REPO_ROOT).stdout.strip().split("\n")
    # Filter out files we want to skip
    files_to_check = [f for f in files if f != "docs/style.css"]
    run(["codespell", *files_to_check], cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("reuse"), reason="reuse not found")
def test_reuse_lint() -> None:
    """Check license headers with reuse."""
    run(["reuse", "lint"], cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("mypy"), reason="mypy not found")
def test_mypy() -> None:
    """Type check with mypy."""
    run(["mypy", "mkosi/", *_kernel_install_files()], cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("mypy"), reason="mypy not found")
def test_mypy_python310() -> None:
    """Type check with mypy for Python 3.10 compatibility."""
    run(["mypy", "--python-version", "3.10", "mkosi/", "tests/", *_kernel_install_files()], cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("pyright"), reason="pyright not found")
def test_pyright() -> None:
    """Type check with pyright."""
    run(["pyright", "mkosi/", "tests/", *_kernel_install_files()], cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("shellcheck"), reason="shellcheck not found")
def test_shellcheck() -> None:
    """Check shell scripts with shellcheck."""
    # Check bin/mkosi and tools/*.sh
    run(["shellcheck", "bin/mkosi", *glob.glob(str(REPO_ROOT / "tools/*.sh"))], cwd=REPO_ROOT)

    # Also check bash completion script
    completion = run(["bin/mkosi", "completion", "bash"], stdout=subprocess.PIPE, cwd=REPO_ROOT).stdout
    run(["shellcheck", "-"], input=completion, cwd=REPO_ROOT)


@pytest.mark.skipif(_skip_if_missing("pandoc"), reason="pandoc not found")
def test_man_page_generation() -> None:
    """Test that man page can be generated."""
    run(["tools/make-man-page.sh"], cwd=REPO_ROOT)
