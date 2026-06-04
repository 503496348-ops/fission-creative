"""
webfission-creative scripts package

This package contains all Python scripts for the webfission-creative plugin.
"""

__version__ = "6.0.0"
__author__ = "AtomCollide-AI-陈宇锋团队"

__all__ = [
    "security_utils",
    "project_locator",
    "chapter_paths",
]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module
