from __future__ import annotations

from shapely.ops import unary_union
from shapely.geometry import box

from stencil_core import (
    StencilOptions,
    build_sheet_and_material,
    create_library_aperture,
    extrude_material,
    split_opening_grid,
)


def test_library_sma_aperture_has_requested_dimensions() -> None:
    aperture = create_library_aperture(
        {"shape": "rectangle", "width": 2.0, "height": 2.1},
        center_x=10.0,
        center_y=20.0,
    )
    min_x, min_y, max_x, max_y = aperture.bounds
    assert abs((max_x - min_x) - 2.0) < 1e-9
    assert abs((max_y - min_y) - 2.1) < 1e-9
    assert abs((min_x + max_x) / 2.0 - 10.0) < 1e-9
    assert abs((min_y + max_y) / 2.0 - 20.0) < 1e-9


def test_large_opening_can_be_split_into_watertight_grid() -> None:
    original = box(0.0, 0.0, 10.0, 7.0)
    cells = split_opening_grid(
        original,
        max_cell_width_mm=3.0,
        max_cell_height_mm=3.0,
        web_x_mm=0.5,
        web_y_mm=0.5,
        min_fragment_area_mm2=0.01,
    )
    assert len(cells) == 9
    assert all(cell.within(original) or cell.equals(original.intersection(cell)) for cell in cells)
    openings = unary_union(cells)
    assert openings.area < original.area

    _, _, material, _ = build_sheet_and_material(
        openings,
        StencilOptions(thickness_mm=0.12, margin_mm=2.0, corner_radius_mm=0.0),
    )
    mesh = extrude_material(material, 0.12)
    assert mesh.is_watertight
    assert mesh.body_count == 1


def test_every_bundled_library_preset_builds() -> None:
    import json
    from pathlib import Path

    payload = json.loads(Path(__file__).with_name("aperture_library.json").read_text(encoding="utf-8"))
    for preset in payload["presets"]:
        aperture = create_library_aperture(preset)
        assert not aperture.is_empty, preset["name"]
        assert aperture.area > 0, preset["name"]
