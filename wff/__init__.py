"""Top-level package for wff"""

from .core import WFF, derivative, simplify
from .proof import Proof

__all__ = ["WFF", "derivative", "simplify", "Proof"]
