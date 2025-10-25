"""Compatibility wrapper kept for backward compatibility.

This module used to contain the implementation directly. It now forwards
to the `cli` module which is the canonical entry point. We keep this file
so existing scripts that import `rct_progress.main` keep working.
"""

from .cli import main  # re-export main for backwards compatibility

__all__ = ["main"]

    