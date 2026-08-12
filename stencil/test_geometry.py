from pathlib import Path

from shapely.geometry import Point, box
from shapely.ops import unary_union

from stencil_core import StencilOptions, build_sheet_and_material, extrude_material


def main() -> None:
    openings = unary_union([
        box(0, 0, 2, 1),
        box(4, 0, 6, 1),
        Point(3, 4).buffer(0.6, quad_segs=24),
    ])
    options = StencilOptions(
        thickness_mm=0.12,
        margin_mm=2.0,
        corner_radius_mm=1.0,
    )
    _, _, material, warnings = build_sheet_and_material(openings, options)
    mesh = extrude_material(material, options.thickness_mm)
    assert mesh.is_watertight
    assert mesh.body_count == 1
    target = Path(__file__).with_name("geometry_self_test.stl")
    mesh.export(target)
    print(f"OK: {target}")
    print(f"vertices={len(mesh.vertices)}, faces={len(mesh.faces)}, warnings={warnings}")


if __name__ == "__main__":
    main()
