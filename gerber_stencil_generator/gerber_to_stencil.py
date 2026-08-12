from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from stencil_core import StencilError, StencilOptions, convert_gerber_to_stencil


def optional_float(value: str) -> float | None:
    value = value.strip()
    return None if value == "" else float(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Создание герметичного STL-трафарета из Gerber paste-mask.",
    )
    parser.add_argument("input", type=Path, help="Gerber-файл пасты: .gtp/.gbp/.gbr")
    parser.add_argument("output", type=Path, help="Выходной STL-файл")
    parser.add_argument("--thickness", type=float, default=0.12, help="Толщина, мм")
    parser.add_argument("--margin", type=float, default=10.0, help="Поле вокруг апертур, мм")
    parser.add_argument("--corner-radius", type=float, default=2.0, help="Радиус углов, мм")
    parser.add_argument(
        "--aperture-offset",
        type=float,
        default=0.0,
        help="Компенсация апертур: плюс расширяет, минус уменьшает, мм",
    )
    parser.add_argument("--arc-tolerance", type=float, default=0.01, help="Допуск дуг, мм")
    parser.add_argument("--width", type=optional_float, default=None, help="Фиксированная ширина листа, мм")
    parser.add_argument("--height", type=optional_float, default=None, help="Фиксированная высота листа, мм")
    parser.add_argument("--mirror-x", action="store_true", help="Зеркально по X относительно центра рисунка")
    parser.add_argument("--mirror-y", action="store_true", help="Зеркально по Y относительно центра рисунка")
    parser.add_argument("--rotate", type=float, default=0.0, help="Поворот, градусы против часовой стрелки")
    parser.add_argument("--center-z", action="store_true", help="Расположить толщину симметрично относительно Z=0")
    parser.add_argument("--min-opening-area", type=float, default=0.0, help="Удалять апертуры меньше площади, мм²")
    parser.add_argument("--precision-grid", type=float, default=1e-6, help="Шаг нормализации геометрии, мм")
    parser.add_argument("--preview", type=Path, default=None, help="Сохранить 2D-предпросмотр SVG")
    parser.add_argument("--report", type=Path, default=None, help="Сохранить отчёт JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    options = StencilOptions(
        thickness_mm=args.thickness,
        margin_mm=args.margin,
        corner_radius_mm=args.corner_radius,
        aperture_offset_mm=args.aperture_offset,
        arc_tolerance_mm=args.arc_tolerance,
        sheet_width_mm=args.width,
        sheet_height_mm=args.height,
        mirror_x=args.mirror_x,
        mirror_y=args.mirror_y,
        rotate_deg=args.rotate,
        center_z=args.center_z,
        min_opening_area_mm2=args.min_opening_area,
        precision_grid_mm=args.precision_grid,
    )
    try:
        report = convert_gerber_to_stencil(
            args.input,
            args.output,
            options,
            preview_svg_path=args.preview,
            report_path=args.report,
        )
    except StencilError as exc:
        print(f"ОШИБКА: {exc}", file=sys.stderr)
        return 2

    print("Готово")
    print(f"STL: {report.output_file}")
    print(f"Размер: {report.sheet_width_mm:.3f} × {report.sheet_height_mm:.3f} × {report.thickness_mm:.3f} мм")
    print(f"Отверстий/областей: {report.opening_count}")
    print(f"Сетка: {report.vertex_count} вершин, {report.face_count} граней")
    print(f"Герметичность: {'ДА' if report.watertight else 'НЕТ'}; тел: {report.body_count}")
    for warning in report.warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
