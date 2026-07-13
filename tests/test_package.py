import importlib.metadata
from pathlib import Path

import llm_system


def test_installed_package_reports_the_declared_distribution_version() -> None:
    assert llm_system.__file__ is not None
    assert Path(llm_system.__file__).is_file()
    assert importlib.metadata.version("llm-system") == "0.27.0"
