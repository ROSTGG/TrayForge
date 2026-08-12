from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import GeometryCollection, MultiPolygon, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
import trimesh


class StencilError(RuntimeError):
    """User-facing conversion error."""


@dataclass(slots=True)
class StencilOptions:
    thickness_mm: float = 0.12
    margin_mm: float = 10.0
    corner_radius_mm: float = 2.0
    aperture_offset_mm: float = 0.0
    arc_tolerance_mm: float = 0.01
    sheet_width_mm: float | None = None
    sheet_height_mm: float | None = None
    mirror_x: bool = False
    mirror_y: bool = False
    rotate_deg: float = 0.0
    center_z: bool = False
    min_opening_area_mm2: float = 0.0
    precision_grid_mm: float = 1e-6

    def validate(self) -> None:
        if self.thickness_mm <= 0:
            raise StencilError("Толщина должна быть больше нуля.")
        if self.margin_mm < 0:
            raise StencilError("Поле не может быть отрицательным.")
        if self.corner_radius_mm < 0:
            raise StencilError("Радиус скругления не может быть отрицательным.")
        if self.arc_tolerance_mm <= 0:
            raise StencilError("Допуск аппроксимации дуг должен быть больше нуля.")
        if self.sheet_width_mm is not None and self.sheet_width_mm <= 0:
            raise StencilError("Ширина листа должна быть больше нуля.")
        if self.sheet_height_mm is not None and self.sheet_height_mm <= 0:
            raise StencilError("Высота листа должна быть больше нуля.")
        if (self.sheet_width_mm is None) != (self.sheet_height_mm is None):
            raise StencilError("Ширина и высота листа задаются вместе.")
        if self.precision_grid_mm <= 0:
            raise StencilError("Шаг геометрической сетки должен быть больше нуля.")


@dataclass(slots=True)
class ConversionReport:
    input_file: str
    output_file: str
    primitive_count: int
    opening_count: int
    excluded_opening_count: int
    added_opening_count: int
    opening_area_mm2: float
    sheet_width_mm: float
    sheet_height_mm: float
    thickness_mm: float
    vertex_count: int
    face_count: int
    body_count: int
    watertight: bool
    volume_mm3: float
    warnings: list[str]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _make_valid_polygonal(geometry, grid_size: float = 1e-6):
    """Repair geometry and keep polygonal parts only."""
    if geometry is None or geometry.is_empty:
        return GeometryCollection()

    try:
        geometry = shapely.set_precision(geometry, grid_size, mode="valid_output")
    except Exception:
        pass

    try:
        geometry = shapely.make_valid(geometry)
    except Exception:
        geometry = geometry.buffer(0)

    polygons: list[Polygon] = []

    def collect(item) -> None:
        if item.is_empty:
            return
        if isinstance(item, Polygon):
            polygons.append(item)
        elif isinstance(item, MultiPolygon):
            polygons.extend(item.geoms)
        elif hasattr(item, "geoms"):
            for child in item.geoms:
                collect(child)

    collect(geometry)
    if not polygons:
        return GeometryCollection()
    return unary_union(polygons)


def _iter_polygons(geometry) -> Iterator[Polygon]:
    if geometry.is_empty:
        return
    if isinstance(geometry, Polygon):
        yield geometry
    elif isinstance(geometry, MultiPolygon):
        yield from geometry.geoms
    elif hasattr(geometry, "geoms"):
        for item in geometry.geoms:
            yield from _iter_polygons(item)



def opening_key(polygon: Polygon, grid_size: float = 1e-6) -> str:
    """Return a stable identifier for one composed Gerber opening."""
    geometry = polygon
    try:
        geometry = shapely.set_precision(geometry, grid_size, mode="valid_output")
    except Exception:
        pass
    try:
        geometry = shapely.normalize(geometry)
    except Exception:
        pass
    payload = shapely.to_wkb(geometry, hex=False, include_srid=False)
    return hashlib.sha1(payload).hexdigest()


def list_openings(geometry, grid_size: float = 1e-6) -> list[tuple[str, Polygon]]:
    """Split composed Gerber image into selectable opening polygons."""
    records: list[tuple[str, Polygon]] = []
    for polygon in _iter_polygons(_make_valid_polygonal(geometry, grid_size)):
        records.append((opening_key(polygon, grid_size), polygon))
    records.sort(key=lambda item: (item[1].bounds[1], item[1].bounds[0], item[0]))
    return records


def exclude_openings_by_key(
    geometry,
    excluded_keys: Iterable[str] | None,
    grid_size: float = 1e-6,
):
    """Remove complete openings selected in the preview, preserving all others."""
    excluded = set(excluded_keys or ())
    if not excluded:
        return geometry, 0
    kept: list[Polygon] = []
    removed = 0
    for key, polygon in list_openings(geometry, grid_size):
        if key in excluded:
            removed += 1
        else:
            kept.append(polygon)
    result = unary_union(kept) if kept else GeometryCollection()
    return _make_valid_polygonal(result, grid_size), removed



def add_openings(geometry, added_openings: Iterable[object] | None, grid_size: float = 1e-6):
    """Union user-created opening polygons with the composed Gerber image."""
    additions = [
        _make_valid_polygonal(item, grid_size)
        for item in (added_openings or ())
        if item is not None and not item.is_empty
    ]
    additions = [item for item in additions if not item.is_empty]
    if not additions:
        return geometry, 0
    result = unary_union([geometry, *additions])
    return _make_valid_polygonal(result, grid_size), len(additions)


def _rounded_rectangle(width: float, height: float, radius: float, quad_segs: int = 12):
    """Create a centered rounded rectangle with exact overall dimensions."""
    width = float(width)
    height = float(height)
    radius = min(max(float(radius), 0.0), width / 2.0, height / 2.0)
    if width <= 0 or height <= 0:
        raise StencilError("Размеры апертуры должны быть больше нуля.")
    if radius <= 1e-12:
        return box(-width / 2.0, -height / 2.0, width / 2.0, height / 2.0)
    inner = box(
        -width / 2.0 + radius,
        -height / 2.0 + radius,
        width / 2.0 - radius,
        height / 2.0 - radius,
    )
    if inner.is_empty or inner.area <= 1e-18:
        # Covers circles and very narrow obrounds.  Buffer a line segment when
        # one dimension is longer, otherwise use a circle.
        if width > height:
            half = max(0.0, (width - height) / 2.0)
            return shapely.LineString([(-half, 0.0), (half, 0.0)]).buffer(
                height / 2.0, quad_segs=quad_segs
            )
        if height > width:
            half = max(0.0, (height - width) / 2.0)
            return shapely.LineString([(0.0, -half), (0.0, half)]).buffer(
                width / 2.0, quad_segs=quad_segs
            )
        return Point(0.0, 0.0).buffer(width / 2.0, quad_segs=quad_segs)
    return inner.buffer(radius, quad_segs=quad_segs, join_style="round")


def create_library_aperture(
    preset: dict[str, object],
    *,
    center_x: float = 0.0,
    center_y: float = 0.0,
    rotation_deg: float = 0.0,
    arc_tolerance_mm: float = 0.01,
):
    """Build one user-placeable aperture from an editable JSON preset."""
    shape_name = str(preset.get("shape", "")).strip().lower()
    if not shape_name:
        raise StencilError("В библиотечном пресете не указан тип shape.")

    def number(name: str, default: float | None = None) -> float:
        value = preset.get(name, default)
        if value is None:
            raise StencilError(f"В библиотечном пресете отсутствует параметр {name}.")
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise StencilError(f"Параметр {name} в библиотеке должен быть числом.") from exc
        if not math.isfinite(result):
            raise StencilError(f"Параметр {name} в библиотеке должен быть конечным числом.")
        return result

    if shape_name == "circle":
        diameter = number("diameter")
        if diameter <= 0:
            raise StencilError("Диаметр библиотечной апертуры должен быть больше нуля.")
        quad = _circle_quad_segs(diameter / 2.0, arc_tolerance_mm)
        geometry = Point(0.0, 0.0).buffer(diameter / 2.0, quad_segs=max(2, quad))
    elif shape_name == "rectangle":
        width = number("width")
        height = number("height")
        if width <= 0 or height <= 0:
            raise StencilError("Ширина и высота библиотечной апертуры должны быть больше нуля.")
        geometry = box(-width / 2.0, -height / 2.0, width / 2.0, height / 2.0)
    elif shape_name in {"rounded_rectangle", "rounded-rectangle"}:
        width = number("width")
        height = number("height")
        radius = number("radius", min(width, height) * 0.1)
        geometry = _rounded_rectangle(width, height, radius)
    elif shape_name in {"obround", "oval", "slot"}:
        width = number("width")
        height = number("height")
        geometry = _rounded_rectangle(width, height, min(width, height) / 2.0)
    else:
        raise StencilError(f"Неизвестный тип библиотечной апертуры: {shape_name}")

    preset_rotation = number("rotation_deg", 0.0)
    total_rotation = preset_rotation + float(rotation_deg)
    if not math.isclose(total_rotation % 360.0, 0.0):
        geometry = affinity.rotate(geometry, total_rotation, origin=(0.0, 0.0), use_radians=False)
    geometry = affinity.translate(geometry, xoff=float(center_x), yoff=float(center_y))
    return _make_valid_polygonal(geometry)


def split_opening_grid(
    polygon: Polygon,
    *,
    max_cell_width_mm: float,
    max_cell_height_mm: float,
    web_x_mm: float,
    web_y_mm: float,
    rotation_deg: float = 0.0,
    min_fragment_area_mm2: float = 0.0,
) -> list[Polygon]:
    """Split one opening into clipped rectangular cells separated by solid webs.

    Cell dimensions are treated as maxima.  The algorithm chooses the minimum
    row/column count that satisfies those maxima and distributes the available
    width evenly, so the grid remains centered and reaches the aperture edges.
    """
    values = {
        "Максимальная ширина ячейки": max_cell_width_mm,
        "Максимальная высота ячейки": max_cell_height_mm,
        "Перемычка X": web_x_mm,
        "Перемычка Y": web_y_mm,
        "Минимальная площадь фрагмента": min_fragment_area_mm2,
    }
    for label, value in values.items():
        if not math.isfinite(float(value)):
            raise StencilError(f"{label} должна быть конечным числом.")
    if max_cell_width_mm <= 0 or max_cell_height_mm <= 0:
        raise StencilError("Размеры ячейки должны быть больше нуля.")
    if web_x_mm < 0 or web_y_mm < 0:
        raise StencilError("Ширина перемычек не может быть отрицательной.")
    if min_fragment_area_mm2 < 0:
        raise StencilError("Минимальная площадь фрагмента не может быть отрицательной.")
    if polygon is None or polygon.is_empty:
        return []

    origin = polygon.centroid.coords[0]
    working = affinity.rotate(polygon, -float(rotation_deg), origin=origin, use_radians=False)
    min_x, min_y, max_x, max_y = working.bounds
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return []

    columns = max(1, math.ceil((width + web_x_mm) / (max_cell_width_mm + web_x_mm)))
    rows = max(1, math.ceil((height + web_y_mm) / (max_cell_height_mm + web_y_mm)))
    if columns * rows > 100_000:
        raise StencilError(
            f"Сетка содержит слишком много ячеек ({columns} × {rows}). "
            "Увеличьте размер ячейки."
        )

    available_width = width - (columns - 1) * web_x_mm
    available_height = height - (rows - 1) * web_y_mm
    if available_width <= 0 or available_height <= 0:
        raise StencilError("Перемычки слишком широкие для выбранной апертуры.")
    cell_width = available_width / columns
    cell_height = available_height / rows

    fragments: list[Polygon] = []
    for row in range(rows):
        y0 = min_y + row * (cell_height + web_y_mm)
        y1 = y0 + cell_height
        for column in range(columns):
            x0 = min_x + column * (cell_width + web_x_mm)
            x1 = x0 + cell_width
            clipped = working.intersection(box(x0, y0, x1, y1))
            clipped = _make_valid_polygonal(clipped)
            for fragment in _iter_polygons(clipped):
                if fragment.area + 1e-12 < min_fragment_area_mm2:
                    continue
                if not math.isclose(float(rotation_deg) % 360.0, 0.0):
                    fragment = affinity.rotate(
                        fragment, float(rotation_deg), origin=origin, use_radians=False
                    )
                fragments.append(fragment)
    return fragments

def _arc_poly_to_shapely(arc_poly, max_error: float) -> Polygon:
    approximated = arc_poly.approximate_arcs(
        max_error=max_error,
        clip_max_error=True,
    )
    coordinates = list(approximated.outline)
    if len(coordinates) < 3:
        return Polygon()
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    return Polygon(coordinates)


def _circle_quad_segs(radius: float, max_error: float) -> int:
    """Return robust Shapely quadrant segmentation for a circle.

    The direct acos(1 - error/radius) formula loses all precision when the
    ratio is extremely small and may produce angle == 0, followed by a
    division by zero.  For small ratios we use the equivalent small-angle
    approximation instead and cap pathological input sizes.
    """
    radius = abs(float(radius))
    max_error = float(max_error)
    if not math.isfinite(radius) or radius <= 0:
        return 0
    if not math.isfinite(max_error) or max_error <= 0:
        raise StencilError(
            "Допуск аппроксимации дуг должен быть конечным числом больше нуля."
        )
    if max_error >= radius:
        return 2

    ratio = max_error / radius
    if ratio < 1e-8:
        angle = math.sqrt(2.0 * ratio)
    else:
        cosine = min(1.0, max(-1.0, 1.0 - ratio))
        angle = math.acos(cosine)

    if not math.isfinite(angle) or angle <= 0:
        # Defensive fallback for malformed or astronomically scaled input.
        return 2048
    return min(2048, max(2, math.ceil(math.pi / (2.0 * angle))))


def _full_circle_arc_to_geometry(primitive, max_error: float):
    """Convert a full-circle stroked Gerber arc without Arc.to_arc_poly().

    Altium commonly encodes a circular pad as a 360-degree G02/G03 arc whose
    start and end points are identical.  Gerbonara correctly marks this as a
    circle, but Arc.to_arc_poly() produces an ArcPoly with coincident vertices;
    some Gerbonara releases then divide by zero while approximating its end-cap
    arcs.  A full circular stroke is simply an annulus (or a filled disk when
    the inner radius collapses), so construct that geometry directly.
    """
    center_x = float(primitive.cx)
    center_y = float(primitive.cy)
    centerline_radius = math.dist(
        (float(primitive.x1), float(primitive.y1)),
        (center_x, center_y),
    )
    half_width = abs(float(primitive.width)) / 2.0

    if not math.isfinite(centerline_radius) or not math.isfinite(half_width):
        raise StencilError("Дуга Gerber содержит неконечные координаты или ширину.")

    outer_radius = centerline_radius + half_width
    if outer_radius <= 0:
        return Polygon()

    outer_segments = _circle_quad_segs(outer_radius, max_error)
    outer = Point(center_x, center_y).buffer(
        outer_radius,
        quad_segs=max(2, outer_segments),
    )

    inner_radius = centerline_radius - half_width
    # A non-positive inner radius means the circular stroke closes into a disk.
    if inner_radius <= max(max_error * 1e-6, 1e-12):
        return outer

    inner_segments = _circle_quad_segs(inner_radius, max_error)
    inner = Point(center_x, center_y).buffer(
        inner_radius,
        quad_segs=max(2, inner_segments),
    )
    return outer.difference(inner)


def _primitive_to_geometry(primitive, max_error: float):
    # Imported lazily so geometry-only tests do not require gerbonara.
    from gerbonara import graphic_primitives as gp

    if isinstance(primitive, gp.Circle):
        radius = abs(float(primitive.r))
        quad_segs = _circle_quad_segs(radius, max_error)
        if quad_segs == 0:
            return Polygon()
        return Point(primitive.x, primitive.y).buffer(radius, quad_segs=quad_segs)

    if isinstance(primitive, gp.Arc):
        is_full_circle = bool(getattr(primitive, "is_circle", False)) or (
            math.isclose(float(primitive.x1), float(primitive.x2), abs_tol=1e-9)
            and math.isclose(float(primitive.y1), float(primitive.y2), abs_tol=1e-9)
        )
        if is_full_circle:
            return _full_circle_arc_to_geometry(primitive, max_error)
        return _arc_poly_to_shapely(primitive.to_arc_poly(), max_error)

    if isinstance(primitive, (gp.ArcPoly, gp.Line, gp.Rectangle)):
        return _arc_poly_to_shapely(primitive.to_arc_poly(), max_error)

    # Future Gerbonara primitives should generally expose to_arc_poly().
    if hasattr(primitive, "to_arc_poly"):
        return _arc_poly_to_shapely(primitive.to_arc_poly(), max_error)

    raise StencilError(
        f"Неподдерживаемый графический примитив Gerber: {type(primitive).__name__}"
    )


def load_gerber_image(
    gerber_path: str | Path,
    *,
    arc_tolerance_mm: float = 0.01,
    precision_grid_mm: float = 1e-6,
) -> tuple[object, int]:
    """Parse Gerber and compose dark/clear primitives into one 2D geometry."""
    try:
        from gerbonara.rs274x import GerberFile
        from gerbonara.utils import MM
    except ImportError as exc:
        raise StencilError(
            "Не установлена библиотека gerbonara. Выполните: "
            "python -m pip install -r requirements.txt"
        ) from exc

    if not math.isfinite(arc_tolerance_mm) or arc_tolerance_mm <= 0:
        raise StencilError(
            "Допуск аппроксимации дуг должен быть конечным числом больше нуля. "
            "Обычно подходит 0,01 мм."
        )
    if not math.isfinite(precision_grid_mm) or precision_grid_mm <= 0:
        raise StencilError(
            "Шаг геометрической сетки должен быть конечным числом больше нуля."
        )

    path = Path(gerber_path)
    if not path.is_file():
        raise StencilError(f"Файл не найден: {path}")

    try:
        gerber = GerberFile.open(path)
    except Exception as exc:
        raise StencilError(f"Не удалось прочитать Gerber: {exc}") from exc

    composed = GeometryCollection()
    primitive_count = 0
    batch: list[object] = []
    batch_polarity: bool | None = None

    def flush_batch() -> None:
        nonlocal composed, batch, batch_polarity
        if not batch:
            return
        merged = _make_valid_polygonal(unary_union(batch), precision_grid_mm)
        if batch_polarity:
            composed = _make_valid_polygonal(composed.union(merged), precision_grid_mm)
        else:
            composed = _make_valid_polygonal(composed.difference(merged), precision_grid_mm)
        batch = []
        batch_polarity = None

    try:
        for object_index, obj in enumerate(gerber.objects, start=1):
            object_type = type(obj).__name__
            try:
                for primitive_index, primitive in enumerate(
                    obj.to_primitives(unit=MM), start=1
                ):
                    primitive_count += 1
                    primitive_type = type(primitive).__name__
                    try:
                        polarity = bool(primitive.polarity_dark)
                        shape = _primitive_to_geometry(primitive, arc_tolerance_mm)
                        shape = _make_valid_polygonal(shape, precision_grid_mm)
                    except ZeroDivisionError as exc:
                        raise StencilError(
                            "В Gerber обнаружен вырожденный примитив: "
                            f"объект #{object_index} ({object_type}), "
                            f"примитив #{primitive_index} ({primitive_type}). "
                            "Попробуйте допуск дуг 0,01 мм; если ошибка повторится, "
                            "нужен сам Gerber-файл для разбора."
                        ) from exc
                    if shape.is_empty:
                        continue
                    if batch_polarity is None:
                        batch_polarity = polarity
                    elif polarity != batch_polarity:
                        flush_batch()
                        batch_polarity = polarity
                    batch.append(shape)
            except StencilError:
                raise
            except ZeroDivisionError as exc:
                raise StencilError(
                    "Gerber содержит вырожденную апертуру или макрос: "
                    f"объект #{object_index} ({object_type}). "
                    "Нужен исходный Gerber-файл, чтобы корректно обработать "
                    "именно этот объект без потери апертуры."
                ) from exc
        flush_batch()
    except StencilError:
        raise
    except Exception as exc:
        raise StencilError(
            f"Ошибка преобразования Gerber-геометрии "
            f"({type(exc).__name__}): {exc}"
        ) from exc

    composed = _make_valid_polygonal(composed, precision_grid_mm)
    if composed.is_empty:
        raise StencilError("Gerber не содержит видимых тёмных областей.")
    return composed, primitive_count


def _filter_small_polygons(geometry, minimum_area: float):
    if minimum_area <= 0:
        return geometry
    kept = [poly for poly in _iter_polygons(geometry) if poly.area >= minimum_area]
    return unary_union(kept) if kept else GeometryCollection()


def _transform_openings(openings, options: StencilOptions):
    min_x, min_y, max_x, max_y = openings.bounds
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    if options.mirror_x:
        openings = affinity.scale(openings, xfact=-1, yfact=1, origin=(center_x, center_y))
    if options.mirror_y:
        openings = affinity.scale(openings, xfact=1, yfact=-1, origin=(center_x, center_y))
    if not math.isclose(options.rotate_deg % 360.0, 0.0):
        openings = affinity.rotate(
            openings,
            options.rotate_deg,
            origin=(center_x, center_y),
            use_radians=False,
        )
    return openings


def _rounded_sheet(min_x: float, min_y: float, max_x: float, max_y: float, radius: float):
    width = max_x - min_x
    height = max_y - min_y
    radius = min(max(radius, 0.0), width / 2.0, height / 2.0)
    if math.isclose(radius, 0.0):
        return box(min_x, min_y, max_x, max_y)
    core = box(min_x + radius, min_y + radius, max_x - radius, max_y - radius)
    if core.is_empty:
        # Covers very narrow sheets where the central box degenerates.
        return box(min_x, min_y, max_x, max_y).buffer(-radius).buffer(radius)
    return core.buffer(radius, quad_segs=16)


def build_sheet_and_material(openings, options: StencilOptions):
    options.validate()
    openings = _make_valid_polygonal(openings, options.precision_grid_mm)
    openings = _transform_openings(openings, options)

    if not math.isclose(options.aperture_offset_mm, 0.0):
        openings = openings.buffer(
            options.aperture_offset_mm,
            quad_segs=12,
            join_style="round",
        )
        openings = _make_valid_polygonal(openings, options.precision_grid_mm)

    openings = _filter_small_polygons(openings, options.min_opening_area_mm2)
    openings = _make_valid_polygonal(openings, options.precision_grid_mm)
    if openings.is_empty:
        raise StencilError("После фильтрации не осталось отверстий.")

    min_x, min_y, max_x, max_y = openings.bounds
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    if options.sheet_width_mm is None:
        sheet_min_x = min_x - options.margin_mm
        sheet_min_y = min_y - options.margin_mm
        sheet_max_x = max_x + options.margin_mm
        sheet_max_y = max_y + options.margin_mm
    else:
        sheet_min_x = center_x - options.sheet_width_mm / 2.0
        sheet_min_y = center_y - options.sheet_height_mm / 2.0
        sheet_max_x = center_x + options.sheet_width_mm / 2.0
        sheet_max_y = center_y + options.sheet_height_mm / 2.0

    sheet = _rounded_sheet(
        sheet_min_x,
        sheet_min_y,
        sheet_max_x,
        sheet_max_y,
        options.corner_radius_mm,
    )
    sheet = _make_valid_polygonal(sheet, options.precision_grid_mm)

    outside = openings.difference(sheet)
    warnings: list[str] = []
    if not outside.is_empty and outside.area > options.precision_grid_mm**2:
        warnings.append(
            f"Часть апертур выходит за лист на площадь {outside.area:.6f} мм² и была обрезана."
        )

    clipped_openings = _make_valid_polygonal(openings.intersection(sheet), options.precision_grid_mm)
    material = _make_valid_polygonal(sheet.difference(clipped_openings), options.precision_grid_mm)

    if material.is_empty:
        raise StencilError("Отверстия полностью удалили материал листа.")

    polygons = list(_iter_polygons(material))
    if len(polygons) > 1:
        warnings.append(
            f"После вычитания получилось {len(polygons)} несвязанных частей. "
            "Проверьте отверстия, пересекающие край трафарета."
        )

    return sheet, clipped_openings, material, warnings


def _signed_area_2d(coords: list[tuple[float, float]]) -> float:
    return 0.5 * sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(coords, coords[1:] + coords[:1])
    )


def _extrude_polygon_cdt(poly: Polygon, height: float, center_z: bool) -> trimesh.Trimesh:
    """Extrude one polygon with holes using Shapely constrained Delaunay triangulation."""
    poly = orient(poly, sign=1.0)
    triangles = shapely.constrained_delaunay_triangles(poly)
    triangle_polys = [g for g in triangles.geoms if isinstance(g, Polygon) and g.area > 0]
    if not triangle_polys:
        raise StencilError("Не удалось триангулировать трафарет.")

    z_bottom = -height / 2.0 if center_z else 0.0
    z_top = height / 2.0 if center_z else height

    coordinates: dict[tuple[float, float], int] = {}
    xy: list[tuple[float, float]] = []

    def vertex_index(point: tuple[float, float]) -> int:
        key = (round(float(point[0]), 12), round(float(point[1]), 12))
        if key not in coordinates:
            coordinates[key] = len(xy)
            xy.append(key)
        return coordinates[key]

    top_faces_2d: list[tuple[int, int, int]] = []
    for tri in triangle_polys:
        pts = [(float(x), float(y)) for x, y in list(tri.exterior.coords)[:-1]]
        if len(pts) != 3:
            continue
        if _signed_area_2d(pts) < 0:
            pts.reverse()
        top_faces_2d.append(tuple(vertex_index(p) for p in pts))

    # Ensure all side-wall vertices exist in the same vertex table.
    rings = [poly.exterior, *poly.interiors]
    ring_indices: list[list[int]] = []
    for ring in rings:
        pts = [(float(x), float(y)) for x, y in list(ring.coords)[:-1]]
        ring_indices.append([vertex_index(p) for p in pts])

    count = len(xy)
    vertices = np.empty((count * 2, 3), dtype=np.float64)
    vertices[:count, :2] = np.asarray(xy)
    vertices[:count, 2] = z_bottom
    vertices[count:, :2] = np.asarray(xy)
    vertices[count:, 2] = z_top

    faces: list[tuple[int, int, int]] = []
    # Bottom faces point down; top faces point up.
    for a, b, c in top_faces_2d:
        faces.append((c, b, a))
        faces.append((a + count, b + count, c + count))

    # All oriented rings have material to their left; right side is outward.
    for ring in ring_indices:
        for index, current in enumerate(ring):
            nxt = ring[(index + 1) % len(ring)]
            faces.append((current, nxt, nxt + count))
            faces.append((current, nxt + count, current + count))

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces, dtype=np.int64),
        process=True,
        validate=True,
    )
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals(multibody=True)
    return mesh


def extrude_material(material, thickness_mm: float, center_z: bool = False) -> trimesh.Trimesh:
    meshes = [
        _extrude_polygon_cdt(poly, thickness_mm, center_z)
        for poly in _iter_polygons(material)
    ]
    if not meshes:
        raise StencilError("Нет полигонов для создания STL.")
    mesh = meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals(multibody=True)
    return mesh


def _geometry_to_svg_path(geometry) -> str:
    commands: list[str] = []
    for poly in _iter_polygons(geometry):
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)
            if not coords:
                continue
            commands.append(f"M {coords[0][0]:.6f},{-coords[0][1]:.6f}")
            for x, y in coords[1:]:
                commands.append(f"L {x:.6f},{-y:.6f}")
            commands.append("Z")
    return " ".join(commands)


def save_preview_svg(material, output_path: str | Path) -> None:
    min_x, min_y, max_x, max_y = material.bounds
    width = max_x - min_x
    height = max_y - min_y
    path_d = _geometry_to_svg_path(material)
    # Y axis is flipped in the path, so the view box uses -max_y.
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.6f}mm" height="{height:.6f}mm"
     viewBox="{min_x:.6f} {-max_y:.6f} {width:.6f} {height:.6f}">
  <path d="{path_d}" fill="#202020" fill-rule="evenodd"/>
</svg>
'''
    Path(output_path).write_text(svg, encoding="utf-8")


def convert_gerber_to_stencil(
    input_path: str | Path,
    output_path: str | Path,
    options: StencilOptions,
    *,
    preview_svg_path: str | Path | None = None,
    report_path: str | Path | None = None,
    excluded_opening_keys: Iterable[str] | None = None,
    added_openings: Iterable[object] | None = None,
) -> ConversionReport:
    options.validate()
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    openings, primitive_count = load_gerber_image(
        input_path,
        arc_tolerance_mm=options.arc_tolerance_mm,
        precision_grid_mm=options.precision_grid_mm,
    )
    openings, excluded_count = exclude_openings_by_key(
        openings, excluded_opening_keys, options.precision_grid_mm
    )
    if openings.is_empty and not added_openings:
        raise StencilError("Все апертуры исключены из трафарета.")
    openings, added_count = add_openings(
        openings, added_openings, options.precision_grid_mm
    )
    if openings.is_empty:
        raise StencilError("После пользовательских изменений не осталось апертур.")
    sheet, openings, material, warnings = build_sheet_and_material(openings, options)
    mesh = extrude_material(material, options.thickness_mm, options.center_z)

    try:
        mesh.export(output_path, file_type="stl")
    except Exception as exc:
        raise StencilError(f"Не удалось сохранить STL: {exc}") from exc

    if preview_svg_path is not None:
        save_preview_svg(material, preview_svg_path)

    min_x, min_y, max_x, max_y = sheet.bounds
    report = ConversionReport(
        input_file=str(input_path.resolve()),
        output_file=str(output_path.resolve()),
        primitive_count=primitive_count,
        opening_count=sum(1 for _ in _iter_polygons(openings)),
        excluded_opening_count=excluded_count,
        added_opening_count=added_count,
        opening_area_mm2=float(openings.area),
        sheet_width_mm=float(max_x - min_x),
        sheet_height_mm=float(max_y - min_y),
        thickness_mm=float(options.thickness_mm),
        vertex_count=int(len(mesh.vertices)),
        face_count=int(len(mesh.faces)),
        body_count=int(mesh.body_count),
        watertight=bool(mesh.is_watertight),
        volume_mm3=float(abs(mesh.volume)),
        warnings=warnings,
    )

    if not report.watertight:
        raise StencilError(
            "STL создан, но проверка герметичности не пройдена. "
            "Увеличьте precision_grid_mm или arc_tolerance_mm и повторите."
        )

    if report_path is not None:
        report.save(report_path)
    return report
