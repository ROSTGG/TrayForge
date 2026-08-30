"""FastAPI backend for Gerber → STL Stencil Generator."""

import asyncio
import json
import tempfile
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
import shapely
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from shapely.geometry import Polygon

# Import core library
import sys
sys.path.insert(0, "/app")
from stencil_core import (
    StencilOptions,
    StencilError,
    load_gerber_image,
    list_openings,
    exclude_openings_by_key,
    add_openings,
    create_library_aperture,
    split_opening_grid,
    build_sheet_and_material,
    extrude_material,
    save_preview_svg,
    ConversionReport,
    _iter_polygons,
)

# Create FastAPI app
app = FastAPI(
    title="Gerber → STL Stencil Generator",
    version="1.0.0",
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store for parsed geometries
sessions: dict[str, Any] = {}


def polygon_to_coords(geom: Any) -> list[list[float]]:
    """Convert Shapely geometry to list of [x, y] coordinate pairs."""
    if isinstance(geom, Polygon):
        return [list(c) for c in geom.exterior.coords]
    elif hasattr(geom, "exterior"):
        return [list(c) for c in geom.exterior.coords]
    else:
        return []


def polygons_to_list(geom: Any) -> list[list[list[float]]]:
    """Convert Shapely geometry to list of polygon coordinate lists."""
    polys = []
    if geom.is_empty:
        return polys
    if isinstance(geom, Polygon):
        polys.append([list(c) for c in geom.exterior.coords])
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:
            if isinstance(g, Polygon):
                polys.append([list(c) for c in g.exterior.coords])
    return polys


def coords_to_polygon(coords: list[list[float]]) -> Polygon:
    """Convert [x, y] coordinate list to Shapely Polygon."""
    if len(coords) < 3:
        raise StencilError("Полигон должен содержать минимум 3 точки.")
    return Polygon(coords)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "ok"}


@app.post("/api/preview")
async def preview(
    file: UploadFile = File(...),
    arc_tolerance_mm: float = 0.01,
    precision_grid_mm: float = 1e-6,
):
    """
    Upload a Gerber paste-mask file and get list of apertures.
    Returns session_id for later use in /api/convert.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        if not content:
            raise StencilError("Файл пуст.")
        
        # Parse Gerber in executor to avoid blocking
        def parse_gerber():
            # Save to temporary file since load_gerber_image expects a file path
            with tempfile.NamedTemporaryFile(suffix='.gbp', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                gerber_geom, primitive_count = load_gerber_image(
                    tmp_path,
                    arc_tolerance_mm=arc_tolerance_mm,
                    precision_grid_mm=precision_grid_mm,
                )
                return gerber_geom, primitive_count
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        
        loop = asyncio.get_event_loop()
        gerber_geom, primitive_count = await loop.run_in_executor(None, parse_gerber)
        
        # List apertures
        openings = list_openings(gerber_geom, grid_size=precision_grid_mm)
        
        # Store geometry in session
        sessions[session_id] = {
            "gerber_geom": gerber_geom,
            "openings": openings,
            "excluded_ids": set(),
            "added_openings": [],
            "arc_tolerance_mm": arc_tolerance_mm,
            "precision_grid_mm": precision_grid_mm,
            "primitive_count": primitive_count,
        }
        
        # Build apertures list for response
        apertures = []
        for aperture_id, polygon in openings:
            bounds = polygon.bounds  # (min_x, min_y, max_x, max_y)
            centroid = polygon.centroid.coords[0]
            apertures.append({
                "id": aperture_id,
                "type": "original",
                "bounds": list(bounds),
                "centroid": list(centroid),
                "area_mm2": float(polygon.area),
                "polygon": polygon_to_coords(polygon),
            })
        
        # Generate preview SVG
        def make_svg():
            with tempfile.NamedTemporaryFile(suffix='.svg', delete=False, mode='w') as tmp:
                tmp_path = tmp.name
            try:
                save_preview_svg(gerber_geom, tmp_path)
                with open(tmp_path, 'r') as f:
                    svg_str = f.read()
                return svg_str
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        
        svg_str = await loop.run_in_executor(None, make_svg)
        
        # Get bounds
        if gerber_geom.is_empty:
            bounds = [0, 0, 100, 100]
        else:
            bounds = list(gerber_geom.bounds)
        
        return {
            "session_id": session_id,
            "apertures": apertures,
            "svg": svg_str,
            "bounds": bounds,
        }
    
    except StencilError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка обработки Gerber: {str(e)}")


@app.get("/api/library")
async def get_library():
    """Return all aperture presets from aperture_library.json."""
    try:
        lib_path = Path("/app/aperture_library.json")
        if not lib_path.exists():
            return {"presets": []}
        
        with open(lib_path, "r", encoding="utf-8") as f:
            library = json.load(f)
        
        presets = library.get("presets", [])
        return {"presets": presets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения библиотеки: {str(e)}")


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    options: str = Form(default="{}"),
    excluded_ids: str = Form(default="[]"),
    added_apertures: str = Form(default="[]"),
):
    """
    Perform full conversion and return STL file as download.
    """
    try:
        loop = asyncio.get_event_loop()
        
        # Parse JSON from form fields
        try:
            opts_dict = json.loads(options)
        except json.JSONDecodeError:
            opts_dict = {}
        
        try:
            excluded = set(json.loads(excluded_ids))
        except (json.JSONDecodeError, TypeError):
            excluded = set()
        
        try:
            added_coords = json.loads(added_apertures)
        except json.JSONDecodeError:
            added_coords = []
        
        # Build options object
        stencil_opts = StencilOptions(
            thickness_mm=float(opts_dict.get("thickness_mm", 0.12)),
            margin_mm=float(opts_dict.get("margin_mm", 10.0)),
            corner_radius_mm=float(opts_dict.get("corner_radius_mm", 2.0)),
            aperture_offset_mm=float(opts_dict.get("aperture_offset_mm", 0.0)),
            arc_tolerance_mm=float(opts_dict.get("arc_tolerance_mm", 0.01)),
            sheet_width_mm=opts_dict.get("sheet_width_mm"),
            sheet_height_mm=opts_dict.get("sheet_height_mm"),
            mirror_x=bool(opts_dict.get("mirror_x", False)),
            mirror_y=bool(opts_dict.get("mirror_y", False)),
            rotate_deg=float(opts_dict.get("rotate_deg", 0.0)),
            center_z=bool(opts_dict.get("center_z", False)),
            min_opening_area_mm2=float(opts_dict.get("min_opening_area_mm2", 0.0)),
            precision_grid_mm=float(opts_dict.get("precision_grid_mm", 1e-6)),
        )
        stencil_opts.validate()
        
        # Convert added apertures from coordinates to geometry
        added_geoms = []
        for coords_list in added_coords:
            try:
                poly = coords_to_polygon(coords_list)
                added_geoms.append(poly)
            except Exception:
                pass
        
        # Read and parse Gerber
        content = await file.read()
        if not content:
            raise StencilError("Файл пуст.")
        
        def full_convert():
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.gbp', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                gerber_geom, primitive_count = load_gerber_image(
                    tmp_path,
                    arc_tolerance_mm=stencil_opts.arc_tolerance_mm,
                    precision_grid_mm=stencil_opts.precision_grid_mm,
                )
            finally:
                Path(tmp_path).unlink(missing_ok=True)
            
            # Apply exclusions
            working_geom, excluded_count = exclude_openings_by_key(
                gerber_geom,
                excluded,
                grid_size=stencil_opts.precision_grid_mm,
            )
            
            # Apply additions
            working_geom, added_count = add_openings(
                working_geom,
                added_geoms,
                grid_size=stencil_opts.precision_grid_mm,
            )
            
            # Build sheet and material
            sheet_geom, clipped_openings, material, warnings = build_sheet_and_material(
                working_geom,
                options=stencil_opts,
            )
            
            # Extrude to 3D
            mesh = extrude_material(
                material,
                stencil_opts.thickness_mm,
                center_z=stencil_opts.center_z,
            )
            
            # Build report
            min_x, min_y, max_x, max_y = sheet_geom.bounds
            report = ConversionReport(
                input_file=file.filename or "unknown",
                output_file="stencil.stl",
                primitive_count=primitive_count,
                opening_count=sum(1 for _ in _iter_polygons(working_geom)),
                excluded_opening_count=excluded_count,
                added_opening_count=added_count,
                opening_area_mm2=float(working_geom.area) if not working_geom.is_empty else 0.0,
                sheet_width_mm=float(max_x - min_x),
                sheet_height_mm=float(max_y - min_y),
                thickness_mm=float(stencil_opts.thickness_mm),
                vertex_count=int(len(mesh.vertices)),
                face_count=int(len(mesh.faces)),
                body_count=int(mesh.body_count),
                watertight=bool(mesh.is_watertight),
                volume_mm3=float(abs(mesh.volume)),
                warnings=warnings,
            )
            
            return mesh, report
        
        mesh, report = await loop.run_in_executor(None, full_convert)
        
        # Export STL
        stl_bytes = mesh.export(file_type="stl")
        
        # Encode report as URL-encoded JSON for header
        report_dict = {
            "input_file": file.filename,
            "output_file": "stencil.stl",
            "primitive_count": report.primitive_count,
            "opening_count": report.opening_count,
            "excluded_opening_count": report.excluded_opening_count,
            "added_opening_count": report.added_opening_count,
            "opening_area_mm2": report.opening_area_mm2,
            "sheet_width_mm": report.sheet_width_mm,
            "sheet_height_mm": report.sheet_height_mm,
            "thickness_mm": report.thickness_mm,
            "vertex_count": report.vertex_count,
            "face_count": report.face_count,
            "body_count": report.body_count,
            "watertight": report.watertight,
            "volume_mm3": report.volume_mm3,
            "warnings": report.warnings,
        }
        report_json = json.dumps(report_dict, ensure_ascii=False)
        report_encoded = quote(report_json)
        
        return Response(
            content=stl_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": 'attachment; filename="stencil.stl"',
                "X-Conversion-Report": report_encoded,
            },
        )
    
    except StencilError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка конвертации: {str(e)}")


@app.post("/api/split-grid")
async def split_grid(body: dict):
    """
    Split one aperture polygon into a grid of cells.
    """
    try:
        polygon_coords = body.get("polygon", [])
        max_cell_width = float(body.get("max_cell_width_mm", 3.0))
        max_cell_height = float(body.get("max_cell_height_mm", 3.0))
        web_x = float(body.get("web_x_mm", 0.5))
        web_y = float(body.get("web_y_mm", 0.5))
        rotation = float(body.get("rotation_deg", 0.0))
        min_fragment = float(body.get("min_fragment_area_mm2", 0.02))
        
        polygon = coords_to_polygon(polygon_coords)
        
        loop = asyncio.get_event_loop()
        
        def do_split():
            fragments = split_opening_grid(
                polygon,
                max_cell_width_mm=max_cell_width,
                max_cell_height_mm=max_cell_height,
                web_x_mm=web_x,
                web_y_mm=web_y,
                rotation_deg=rotation,
                min_fragment_area_mm2=min_fragment,
            )
            return fragments
        
        fragments = await loop.run_in_executor(None, do_split)
        
        result_fragments = []
        for frag in fragments:
            frag_id = f"added:{uuid.uuid4()}"
            bounds = frag.bounds
            centroid = frag.centroid.coords[0]
            result_fragments.append({
                "id": frag_id,
                "polygon": polygon_to_coords(frag),
                "bounds": list(bounds),
                "centroid": list(centroid),
                "area_mm2": float(frag.area),
            })
        
        return {"fragments": result_fragments}
    
    except StencilError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка разбиения сеткой: {str(e)}")


@app.post("/api/library-aperture")
async def library_aperture(body: dict):
    """
    Create an aperture from a library preset at a given position.
    """
    try:
        preset = body.get("preset", {})
        center_x = float(body.get("center_x", 0.0))
        center_y = float(body.get("center_y", 0.0))
        rotation = float(body.get("rotation_deg", 0.0))
        arc_tolerance = float(body.get("arc_tolerance_mm", 0.01))
        
        loop = asyncio.get_event_loop()
        
        def make_aperture():
            geom = create_library_aperture(
                preset,
                center_x=center_x,
                center_y=center_y,
                rotation_deg=rotation,
                arc_tolerance_mm=arc_tolerance,
            )
            return geom
        
        geom = await loop.run_in_executor(None, make_aperture)
        
        aperture_id = f"added:{uuid.uuid4()}"
        bounds = geom.bounds if not geom.is_empty else [0, 0, 0, 0]
        centroid = geom.centroid.coords[0] if not geom.is_empty else [0, 0]
        
        return {
            "id": aperture_id,
            "polygon": polygon_to_coords(geom),
            "bounds": list(bounds),
            "centroid": list(centroid),
            "area_mm2": float(geom.area) if not geom.is_empty else 0.0,
        }
    
    except StencilError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка создания апертуры: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=2)
