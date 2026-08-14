from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from gerber_stencil_generator.stencil_core import (
    StencilError,
    StencilOptions,
    convert_gerber_to_stencil,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
JOBS_DIR = Path(os.getenv("JOBS_DIR", "/tmp/gerber-stencil-jobs"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_MINUTES", "60")) * 60
ALLOWED_SUFFIXES = {".gtp", ".gbp", ".gbr", ".ger", ".pho"}
JOB_ID_RE = re.compile(r"^[a-f0-9]{32}$")


def cleanup_jobs() -> None:
    if not JOBS_DIR.exists():
        return
    cutoff = time.time() - JOB_TTL_SECONDS
    for item in JOBS_DIR.iterdir():
        try:
            if item.is_dir() and item.stat().st_mtime < cutoff:
                shutil.rmtree(item)
        except OSError:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI):
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_jobs()
    yield


app = FastAPI(title="Stencil Forge", version="1.0.0", lifespan=lifespan)


def optional_number(value: str, label: str) -> float | None:
    value = value.strip().replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise HTTPException(422, f"Поле «{label}» должно быть числом.") from exc


async def save_upload(upload: UploadFile, target: Path) -> None:
    size = 0
    with target.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "Файл слишком большой.")
            output.write(chunk)
    if size == 0:
        raise HTTPException(400, "Загружен пустой файл.")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    thickness: str = Form("0.12"),
    margin: str = Form("10"),
    corner_radius: str = Form("2"),
    aperture_offset: str = Form("0"),
    arc_tolerance: str = Form("0.01"),
    sheet_width: str = Form(""),
    sheet_height: str = Form(""),
    rotate: str = Form("0"),
    min_opening_area: str = Form("0"),
    mirror_x: bool = Form(False),
    mirror_y: bool = Form(False),
    center_z: bool = Form(False),
) -> dict:
    cleanup_jobs()
    original_name = Path(file.filename or "board.gbr").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(415, "Поддерживаются Gerber-файлы GTP, GBP, GBR, GER и PHO.")

    job_id = uuid.uuid4().hex
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True)
    input_path = job_dir / f"input{suffix}"
    output_path = job_dir / "stencil.stl"
    preview_path = job_dir / "preview.svg"
    report_path = job_dir / "report.json"

    try:
        await save_upload(file, input_path)
        options = StencilOptions(
            thickness_mm=optional_number(thickness, "Толщина"),
            margin_mm=optional_number(margin, "Поле"),
            corner_radius_mm=optional_number(corner_radius, "Радиус углов"),
            aperture_offset_mm=optional_number(aperture_offset, "Компенсация"),
            arc_tolerance_mm=optional_number(arc_tolerance, "Допуск дуг"),
            sheet_width_mm=optional_number(sheet_width, "Ширина"),
            sheet_height_mm=optional_number(sheet_height, "Высота"),
            rotate_deg=optional_number(rotate, "Поворот"),
            min_opening_area_mm2=optional_number(min_opening_area, "Минимальная площадь"),
            mirror_x=mirror_x,
            mirror_y=mirror_y,
            center_z=center_z,
        )
        report = await asyncio.to_thread(
            convert_gerber_to_stencil,
            input_path,
            output_path,
            options,
            preview_svg_path=preview_path,
            report_path=report_path,
        )
        payload = asdict(report)
        payload["input_file"] = original_name
        payload["output_file"] = "stencil.stl"
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "job_id": job_id,
            "preview_svg": preview_path.read_text(encoding="utf-8"),
            "report": payload,
            "downloads": {
                "stl": f"/api/jobs/{job_id}/stencil",
                "report": f"/api/jobs/{job_id}/report",
                "preview": f"/api/jobs/{job_id}/preview",
            },
        }
    except HTTPException:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise
    except StencilError as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(500, f"Не удалось обработать Gerber: {exc}") from exc
    finally:
        await file.close()


def job_file(job_id: str, filename: str) -> Path:
    if not JOB_ID_RE.fullmatch(job_id):
        raise HTTPException(404, "Результат не найден.")
    path = JOBS_DIR / job_id / filename
    if not path.is_file():
        raise HTTPException(404, "Результат не найден или уже удалён.")
    return path


@app.get("/api/jobs/{job_id}/stencil")
def download_stencil(job_id: str) -> FileResponse:
    return FileResponse(job_file(job_id, "stencil.stl"), filename="stencil.stl", media_type="model/stl")


@app.get("/api/jobs/{job_id}/report")
def download_report(job_id: str) -> FileResponse:
    return FileResponse(job_file(job_id, "report.json"), filename="stencil-report.json", media_type="application/json")


@app.get("/api/jobs/{job_id}/preview")
def download_preview(job_id: str) -> FileResponse:
    return FileResponse(job_file(job_id, "preview.svg"), filename="stencil-preview.svg", media_type="image/svg+xml")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
