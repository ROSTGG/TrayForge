from __future__ import annotations

import math
import sys
import types
from dataclasses import dataclass

# stencil_core imports gerbonara lazily.  Provide only the primitive classes
# needed by this regression test, so it also runs in a geometry-only setup.
fake_package = types.ModuleType("gerbonara")
fake_gp = types.ModuleType("gerbonara.graphic_primitives")

@dataclass
class Circle:
    x: float
    y: float
    r: float

@dataclass
class Arc:
    x1: float
    y1: float
    x2: float
    y2: float
    cx: float
    cy: float
    clockwise: bool
    width: float
    polarity_dark: bool = True

    @property
    def is_circle(self):
        return math.isclose(self.x1, self.x2, abs_tol=1e-6) and math.isclose(self.y1, self.y2, abs_tol=1e-6)

class ArcPoly: pass
class Line: pass
class Rectangle: pass

fake_gp.Circle = Circle
fake_gp.Arc = Arc
fake_gp.ArcPoly = ArcPoly
fake_gp.Line = Line
fake_gp.Rectangle = Rectangle
fake_package.graphic_primitives = fake_gp
sys.modules.setdefault("gerbonara", fake_package)
sys.modules.setdefault("gerbonara.graphic_primitives", fake_gp)

from stencil_core import _primitive_to_geometry


def test_altium_full_circle_stroke_becomes_filled_disk():
    # Corresponds to D13 in pl2.GBP: centerline r=0.25 mm, aperture width=0.5 mm.
    arc = Arc(36.75, 132.0, 36.75, 132.0, 36.50, 132.0, False, 0.5)
    geom = _primitive_to_geometry(arc, 0.01)
    assert not geom.is_empty
    assert geom.geom_type == "Polygon"
    assert abs(geom.area - math.pi * 0.5**2) < 0.01
    min_x, min_y, max_x, max_y = geom.bounds
    assert abs((max_x-min_x) - 1.0) < 0.01
    assert abs((max_y-min_y) - 1.0) < 0.01


def test_full_circle_stroke_can_be_annulus():
    arc = Arc(2.0, 0.0, 2.0, 0.0, 0.0, 0.0, True, 0.4)
    geom = _primitive_to_geometry(arc, 0.005)
    expected = math.pi * (2.2**2 - 1.8**2)
    assert abs(geom.area - expected) < 0.03
    assert len(geom.interiors) == 1
