# pyre-ignore-all-errors
# flake8: noqa

import sys
from typing import Dict, List, Union  # noqa: F401

# Literal
from typing import Literal

# RichTypedDict
from typing import TypedDict as RichTypedDict

assert sys.version_info >= (3, 12)  # PEP 695


# forward reference
# TODO: Upgrade mypy to version that supports PEP 695
type Scatterplot = List[Point2D]  # type: ignore[valid-type, used-before-def]  # mypy


# forward reference
# TODO: Upgrade mypy to version that supports PEP 695
type PointForLabel = Dict[str, Point2D]  # type: ignore[valid-type, used-before-def]  # mypy


# forward reference
# TODO: Upgrade mypy to version that supports PEP 695
type Shape = Union[Circle, Rect]  # type: ignore[valid-type, used-before-def]  # mypy


class Rect(RichTypedDict):
    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float


class Circle(RichTypedDict):
    type: Literal["circle"]
    center: "Point2D"  # forward reference
    radius: float


class Point2D(RichTypedDict):
    x: float
    y: float
