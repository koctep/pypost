"""Test configuration: set Qt offscreen platform before any Qt imports."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
