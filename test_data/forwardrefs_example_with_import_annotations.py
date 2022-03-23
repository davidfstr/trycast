# NOTE: Unfortunately even with the "annotations" future-import,
#       it is *still* sometimes necessary to explicitly quote forward references
#       in type annotations.
from __future__ import annotations  # type: ignore[attr-defined]  # noqa: F407

import sys
from typing import Dict, List, Union  # noqa: F401

# Literal
if sys.version_info >= (3, 8):
    from typing import Literal  # Python 3.8+
else:
    from typing_extensions import Literal  # Python 3.5+

# RichTypedDict
if sys.version_info >= (3, 9):
    from typing import TypedDict as RichTypedDict  # Python 3.9+
else:
    from typing_extensions import TypedDict as RichTypedDict  # Python 3.5+


Scatterplot = "List[Point2D]"  # forward reference


PointForLabel = "Dict[str, Point2D]"  # forward reference


Shape = "Union[Circle, Rect]"  # forward reference


class Rect(RichTypedDict):
    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float


class Circle(RichTypedDict):
    type: Literal["circle"]
    center: Point2D
    radius: float


class Point2D(RichTypedDict):
    x: float
    y: float
