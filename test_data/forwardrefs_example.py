from typing import Dict, List, Literal, Union

# RichTypedDict
from typing import TypedDict as RichTypedDict


Scatterplot = List["Point2D"]  # forward reference


PointForLabel = Dict["str", "Point2D"]  # forward reference


Shape = Union["Circle", "Rect"]  # forward reference


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
