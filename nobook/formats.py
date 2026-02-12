"""Marker constants and regex patterns for pybooks format."""

import re

BLOCK_START_RE = re.compile(r"^#\s*@block=(\S+)\s*$")
OUTPUT_PREFIX = "# >>> "
ERROR_PREFIX = "# !!! "
