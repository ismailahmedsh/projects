"""General helper utilities."""
from __future__ import annotations

from typing import Dict


def merge_dicts(base: Dict, override: Dict) -> Dict:
    result = base.copy()
    result.update(override)
    return result
