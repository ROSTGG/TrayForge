"""Gerber → STL Stencil Generator — Web API."""
from __future__ import annotations

import io
import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from stencil_core import (
    ConversionReport,
    StencilError,
    StencilOptions,
    build_sheet_and_material,
    extrude_material,
    load_gerber_image,
    save_preview_svg,
)

app = FastAPI(title="Stencil Generator API", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/preview")
async def preview(
    file: UploadFile = File(...),
    arc_tolerance: float = Form(0.01),
):
    """Загрузить Gerber → получить SVG превью."""
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".gbr", delete=False)
        content = await file.read()
        tmp.write(content)
        tmp.close()

        openings, count = load_gerber_image(
            tmp.name,
            arc_tolerance_mm=arc_tolerance,
        )
        opts = StencilOptions(arc_tolerance_mm=arc_tolerance)
        sheet, clipped, material, warnings = build_sheet_and_material(openings, opts)

        svg_tmp = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        svg_tmp.close()
        save_preview_svg(material, svg_tmp.name)
        svg_content = Path(svg_tmp.name).read_text(encoding="utf-8")
        Path(svg_tmp.name).unlink(missing_ok=True)

        min_x, min_y, max_x, max_y = sheet.bounds
        return JSONResponse({
            "svg": svg_content,
            "aperture_count": count,
            "sheet_width": round(max_x - min_x, 2),
            "sheet_height": round(max_y - min_y, 2),
            "warnings": warnings,
        })
    except StencilError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Ошибка обработки: {e}"}, status_code=500)
    finally:
        if tmp:
            Path(tmp.name).unlink(missing_ok=True)


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    thickness: float = Form(0.12),
    margin: float = Form(10.0),
    corner_radius: float = Form(2.0),
    aperture_offset: float = Form(0.0),
    arc_tolerance: float = Form(0.01),
    mirror_x: bool = Form(False),
    mirror_y: bool = Form(False),
    rotate: float = Form(0.0),
    sheet_width: float | None = Form(None),
    sheet_height: float | None = Form(None),
):
    """Загрузить Gerber → получить STL файл."""
    tmp = None
    stl_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".gbr", delete=False)
        content = await file.read()
        tmp.write(content)
        tmp.close()

        opts = StencilOptions(
            thickness_mm=thickness,
            margin_mm=margin,
            corner_radius_mm=corner_radius,
            aperture_offset_mm=aperture_offset,
            arc_tolerance_mm=arc_tolerance,
            mirror_x=mirror_x,
            mirror_y=mirror_y,
            rotate_deg=rotate,
            sheet_width_mm=sheet_width if sheet_width and sheet_width > 0 else None,
            sheet_height_mm=sheet_height if sheet_height and sheet_height > 0 else None,
        )
        opts.validate()

        openings, primitive_count = load_gerber_image(
            tmp.name,
            arc_tolerance_mm=opts.arc_tolerance_mm,
            precision_grid_mm=opts.precision_grid_mm,
        )
        sheet, clipped_openings, material, warnings = build_sheet_and_material(
            openings, opts
        )
        mesh = extrude_material(material, opts.thickness_mm)

        stl_tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
        stl_tmp.close()
        stl_path = stl_tmp.name
        mesh.export(stl_path, file_type="stl")

        filename = Path(file.filename or "stencil").stem + "-stencil.stl"
        return FileResponse(
            stl_path,
            media_type="model/stl",
            filename=filename,
            headers={
                "X-Watertight": str(mesh.is_watertight),
                "X-Vertices": str(len(mesh.vertices)),
                "X-Faces": str(len(mesh.faces)),
                "X-Warnings": "; ".join(warnings) if warnings else "",
            },
        )
    except StencilError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Ошибка конвертации: {e}"}, status_code=500)
    finally:
        if tmp:
            Path(tmp.name).unlink(missing_ok=True)
        # stl_path cleaned up by FileResponse after send


# Статика — фронтенд (монтируется последним!)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
