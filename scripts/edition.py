"""The edition's own date, held in one place.

The date is a constant rather than the system clock on purpose. The verification
workflow rebuilds every generated file and compares it byte for byte against the
committed copy, so a date taken from the clock would make every rebuild a diff and
break the check that proves the build is deterministic. A constant has to be bumped
when the edition is republished, which is the honest thing to do anyway: the date
records when the figures were computed and the sources were last read, not when a
script happened to run.

Both the model metadata and the page footers import from here so the two cannot
drift apart. The text and the ISO form are kept adjacent because they are two
renderings of the same fact.
"""
from __future__ import annotations

BUILD_DATE_ISO = "2026-11-17"
BUILD_DATE_TEXT = "17 November 2026"

# The window the source ledger was read over. Every entry in the ledger carries its
# own check date; this is the range those dates fall in.
SOURCES_CHECKED_FROM = "13 November 2026"
SOURCES_CHECKED_TO = "17 November 2026"
