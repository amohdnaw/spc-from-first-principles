"""spc-lab — Statistical Process Control formulas with nothing hidden.

Every constant and coefficient used here is derived or referenced
in the docstrings, so the library doubles as a teaching tool.
"""

__version__ = "0.1.0"

from .formulas import (
    control_limit_constants,
    xbar_r_limits,
    capability_indices,
    defects_per_million,
    ewma_limits,
    western_electric_violations,
)

__all__ = [
    "control_limit_constants",
    "xbar_r_limits",
    "capability_indices",
    "defects_per_million",
    "ewma_limits",
    "western_electric_violations",
]
