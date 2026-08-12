from shapely import affinity
from shapely.geometry import box

from stencil_core import (
    StencilOptions,
    add_openings,
    build_sheet_and_material,
    extrude_material,
    list_openings,
)


def main() -> None:
    original = box(0, 0, 2.0, 1.0)
    _, source = list_openings(original)[0]
    duplicate = affinity.translate(source, xoff=3.6, yoff=0.0)
    openings, added = add_openings(original, [duplicate])

    assert added == 1
    assert len(list_openings(openings)) == 2
    assert openings.bounds == (0.0, 0.0, 5.6, 1.0)

    _, _, material, _ = build_sheet_and_material(
        openings,
        StencilOptions(thickness_mm=0.12, margin_mm=1.0, corner_radius_mm=0.0),
    )
    mesh = extrude_material(material, 0.12)
    assert mesh.is_watertight
    assert mesh.body_count == 1
    print("OK: duplicate aperture at 3.6 mm; watertight STL")


if __name__ == "__main__":
    main()
