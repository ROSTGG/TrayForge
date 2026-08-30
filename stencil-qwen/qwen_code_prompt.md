# Prompt for Qwen-Code: Gerber → STL Stencil Generator — Web Application

---

## Context

You are working inside the repository `gerber_stencil_generator`. The repository already contains a complete, working Python core library and a Tkinter desktop GUI. Your task is to build a **web application** that exposes the exact same functionality through a browser, packaged as two Docker containers orchestrated with **docker-compose**.

Read the following files before writing any code:

- `app.md` — full description of the application: what it does, how the pipeline works, all parameters, GUI layout, aperture library format, and JSON report format.
- `stencil_core.py` — the geometry engine. **Do not modify it.** Import and call its public API from your FastAPI backend.
- `aperture_library.json` — the editable aperture preset library. Mount it as a Docker volume so it can be edited without rebuilding.
- `requirements.txt` — Python dependencies already needed by the core (gerbonara, shapely, trimesh, numpy). Your backend must install these plus `fastapi`, `uvicorn[standard]`, and `python-multipart`.

---

## Required Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Frontend | React 18+ (Vite scaffold), vanilla CSS (no Tailwind) |
| Container orchestration | docker-compose v2 |

**Backend container**: Python 3.12-slim base image. Installs all Python deps. Mounts `aperture_library.json` as a bind-mount volume so edits are live.

**Frontend container**: Node 20-alpine base image for the build stage; serves static files via Nginx alpine in the production stage (multi-stage Dockerfile). Proxies `/api/` requests to the backend container.

---

## Backend API (FastAPI)

Implement the following REST endpoints. All endpoints that receive files use `multipart/form-data`. All responses are JSON unless stated otherwise.

### `POST /api/preview`

Upload a Gerber paste-mask file and get back the list of apertures for the interactive editor.

**Request**: `multipart/form-data`
- `file`: the Gerber file (`.gtp`, `.gbp`, `.gbr`, `.ger`, `.gerber`)
- `arc_tolerance_mm`: float, default `0.01`
- `precision_grid_mm`: float, default `1e-6`

**Response** `200 application/json`:
```json
{
  "session_id": "<uuid>",
  "apertures": [
    {
      "id": "<sha1-key>",
      "type": "original",
      "bounds": [x_min, y_min, x_max, y_max],
      "centroid": [cx, cy],
      "area_mm2": 0.42,
      "polygon": [[x, y], ...]
    }
  ],
  "svg": "<full SVG string of the composed layer>",
  "bounds": [min_x, min_y, max_x, max_y]
}
```

Store the parsed Shapely geometry in a server-side session dict keyed by `session_id` (in-memory is fine; one Python process).

---

### `GET /api/library`

Return all aperture presets from `aperture_library.json`.

**Response** `200 application/json`:
```json
{
  "presets": [
    {"name": "Circle Ø0.5 mm", "shape": "circle", "diameter": 0.5},
    ...
  ]
}
```

---

### `POST /api/convert`

Perform the full conversion and return the STL file as a download.

**Request**: `multipart/form-data`
- `file`: Gerber file
- `options`: JSON string of `StencilOptions` fields (see below)
- `excluded_ids`: JSON array of aperture SHA-1 keys to exclude
- `added_apertures`: JSON array of aperture polygon coordinate lists `[[[x,y], ...], ...]`

**`options` JSON fields** (all optional, use `StencilOptions` defaults when absent):
```json
{
  "thickness_mm": 0.12,
  "margin_mm": 10.0,
  "corner_radius_mm": 2.0,
  "aperture_offset_mm": 0.0,
  "arc_tolerance_mm": 0.01,
  "sheet_width_mm": null,
  "sheet_height_mm": null,
  "mirror_x": false,
  "mirror_y": false,
  "rotate_deg": 0.0,
  "center_z": false,
  "min_opening_area_mm2": 0.0,
  "precision_grid_mm": 1e-6
}
```

**Response** `200 application/octet-stream`:  
Binary STL file. Set header `Content-Disposition: attachment; filename="stencil.stl"`.

Also include response header `X-Conversion-Report` containing a URL-encoded JSON string of the `ConversionReport` fields (the same fields described in `app.md`).

**Error response** `422 application/json`:
```json
{"detail": "Human-readable Russian error message from StencilError"}
```

---

### `POST /api/split-grid`

Split one aperture polygon into a grid of cells.

**Request** `application/json`:
```json
{
  "polygon": [[x, y], ...],
  "max_cell_width_mm": 3.0,
  "max_cell_height_mm": 3.0,
  "web_x_mm": 0.5,
  "web_y_mm": 0.5,
  "rotation_deg": 0.0,
  "min_fragment_area_mm2": 0.02
}
```

**Response** `200 application/json`:
```json
{
  "fragments": [
    {"id": "added:<uuid>", "polygon": [[x, y], ...], "bounds": [...], "centroid": [...], "area_mm2": 0.0}
  ]
}
```

---

### `POST /api/library-aperture`

Create an aperture from a library preset at a given position.

**Request** `application/json`:
```json
{
  "preset": {"shape": "circle", "diameter": 1.0},
  "center_x": 12.5,
  "center_y": 7.3,
  "rotation_deg": 0.0
}
```

**Response** `200 application/json`:
```json
{
  "id": "added:<uuid>",
  "polygon": [[x, y], ...],
  "bounds": [...],
  "centroid": [...],
  "area_mm2": 0.0
}
```

---

## Frontend (React + Vite)

### Design Requirements

Apply modern, premium web design:
- **Dark theme** — background `#0f1117`, surface cards `#1a1d24`, accent `#4f8ef7` (blue), success `#22c55e`, danger `#ef4444`, selected aperture highlight `#f59e0b` (amber).
- **Font** — Inter from Google Fonts.
- **Smooth transitions** on all interactive elements (hover, selection, panel toggle).
- **Glassmorphism** for floating panels/tooltips.
- The app must look professional and polished — avoid plain grey boxes and default browser styles.

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER: app name + version badge + GitHub link (placeholder)               │
├─────────────────┬───────────────────────────────────────────────────────────┤
│  LEFT SIDEBAR   │  CANVAS AREA                                              │
│  (360px fixed)  │                                                           │
│                 │  Toolbar: [−][+][Fit] zoom controls + scale status        │
│  File upload    │                                                           │
│  drop zone      │  SVG/Canvas aperture editor                               │
│                 │  (interactive, full remaining height)                     │
│  ─────────────  │                                                           │
│  Tabs:          │  Status bar: zoom%, px/mm, cursor x/y mm                 │
│  [Params]       ├───────────────────────────────────────────────────────────┤
│  [Edit]         │  BOTTOM LOG PANEL (collapsible, ~120px)                   │
│                 │  Conversion log + warnings                                │
│  ─────────────  │                                                           │
│  [Convert STL]  │                                                           │
└─────────────────┴───────────────────────────────────────────────────────────┘
```

### File Upload

- Large drag-and-drop zone with a dashed border. Accepts `.gtp`, `.gbp`, `.gbr`, `.ger`, `.gerber`.
- On file drop/select: call `POST /api/preview`, show a loading spinner, then render apertures in the canvas.
- Show the filename and file size as a badge once loaded.

### Canvas / Aperture Editor

Use an SVG element (not `<canvas>`) for the aperture preview. Render:
- **Sheet outline** as a thin grey rectangle.
- **Original apertures** as white-filled SVG paths with a subtle stroke.
- **Excluded apertures** as semi-transparent red paths.
- **Selected apertures** as amber/yellow paths with a glowing drop-shadow filter.
- **Added (user) apertures** as cyan/teal paths.

Implement the following interactions on the SVG:
- **Scroll to zoom** (centered on cursor position).
- **Middle-click drag** or **Space + left-drag** to pan.
- **Left-click** on an aperture to select/deselect it.
- **Left-drag on empty space** draws a rubber-band selection rectangle; releases select all apertures whose bounding boxes intersect the rectangle.
- **Shift + click/drag** adds to selection.
- **Keyboard shortcuts**: `F` or `Home` to fit all, `+`/`=` zoom in, `−` zoom out, `Ctrl+A` select all, `Escape` cancel placement mode.
- **Placement mode**: when the user clicks "Place by click" from the library panel, the cursor changes to a crosshair; clicking on the SVG calls `POST /api/library-aperture` and adds the resulting polygon to the added apertures.

Show a **zoom/scale status bar** below the toolbar: e.g. `Zoom: 4.3×   12.3 px/mm   x: 5.21 mm   y: 3.87 mm`.

### Left Sidebar — Params Tab

Form fields mirroring all `StencilOptions` parameters:
- Thickness (mm)
- Margin (mm)
- Corner radius (mm)
- Aperture offset (mm)
- Arc tolerance (mm)
- Fixed width / height (mm) — optional, leave blank for auto
- Rotation (°)
- Min aperture area (mm²)
- Checkboxes: Mirror X, Mirror Y, Center Z

Use a two-column label+input grid layout with proper spacing.

### Left Sidebar — Edit Tab

Sections, each in a visually distinct card:

1. **Selection actions**: buttons "Exclude / Restore selected", "Select All", "Clear selection"

2. **Duplicate**: ΔX and ΔY inputs + "Duplicate Selected" button. Duplicates selected apertures (original or added) by offset.

3. **Library apertures**: dropdown (Combobox) populated from `GET /api/library`, rotation input, "Place by click" button. Show a highlighted banner when placement mode is active.

4. **Grid split**: inputs for max cell X/Y, web X/Y, rotation, min fragment area; "Split Selected" button. Calls `POST /api/split-grid` for each selected aperture and replaces it with the resulting fragments.

5. **Edit management**: "Delete Added" (removes user-added apertures from selection), "Reset All Edits" (clear excluded and added sets, re-render original apertures)

### Convert Button

Fixed at the bottom of the sidebar. Shows a spinner while conversion is running (non-blocking — use a background fetch so the UI stays interactive). On success, automatically downloads the STL file. Shows any warnings in the log panel. On error, shows an error toast notification.

### Conversion Report Modal

After successful conversion, show a modal dialog (slide-up animation) with a table of all `ConversionReport` fields: dimensions, aperture count, vertex/face count, watertight status, volume, and any warnings.

---

## Docker Setup

### File structure to create

```
gerber_stencil_generator/
├── backend/
│   ├── Dockerfile
│   ├── main.py                 ← FastAPI application
│   └── (symlink or copy stencil_core.py, aperture_library.json)
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── (Vite React project files)
└── docker-compose.yml
```

### `docker-compose.yml` requirements

- Service `backend`: builds from `./backend`, exposes port `8000` internally, mounts `../aperture_library.json:/app/aperture_library.json` as a bind volume.
- Service `frontend`: builds from `./frontend`, exposes port `80` to the host (configurable via `.env`).
- Both services on the same internal Docker network `stencil-net`.
- The Nginx config in the frontend container proxies `/api/` → `http://backend:8000/api/`.
- Include a `healthcheck` for the backend: `GET /api/health` must return `{"status": "ok"}`.

### Backend Dockerfile requirements

```dockerfile
FROM python:3.12-slim
WORKDIR /app
# Install system libs required by shapely and trimesh (libgeos, etc.)
# Copy requirements and install
# Copy stencil_core.py and main.py
# EXPOSE 8000
# CMD uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Install these system packages: `libgeos-dev`, `libgl1`, `libgomp1` (needed by trimesh/shapely on slim images).

### Frontend Dockerfile requirements

Multi-stage:
1. **Build stage** (`node:20-alpine`): `npm ci && npm run build` → produces `dist/`
2. **Serve stage** (`nginx:alpine`): copy `dist/` to `/usr/share/nginx/html`, copy `nginx.conf`

`nginx.conf` must:
- Serve static files from `/usr/share/nginx/html`
- Proxy `/api/` to `http://backend:8000/api/` with proper headers
- Set `client_max_body_size 50m` (for large Gerber files)
- Enable gzip compression
- Handle SPA routing: `try_files $uri $uri/ /index.html`

---

## Implementation Notes

1. **Session state**: Use a simple Python dict `sessions: dict[str, Any]` in the FastAPI app to hold parsed Shapely geometries between `/api/preview` and `/api/convert`. Sessions are not persisted — that's acceptable.

2. **Thread safety**: `stencil_core.py` functions are CPU-bound and not async. Wrap calls in `asyncio.get_event_loop().run_in_executor(None, ...)` or use `fastapi.concurrency.run_in_threadpool`.

3. **Polygon serialization**: Shapely Polygon → list of `[x, y]` coordinate pairs for JSON. Use `list(polygon.exterior.coords)`.

4. **SVG generation**: For the preview SVG, use the existing `save_preview_svg` logic from `stencil_core.py`, or generate it inline on the frontend by rendering aperture polygons as `<path>` elements using coordinate data from the API.

5. **Error handling**: Catch `StencilError` in every endpoint and return HTTP 422 with `{"detail": str(exc)}`. Show the Russian error message as-is in the frontend toast.

6. **CORS**: In development, allow all origins. In production (Docker), CORS is handled by Nginx so restrict to same origin.

7. **File size limit**: Set FastAPI's `max_upload_size` and Nginx's `client_max_body_size` both to 50 MB.

---

## Deliverables

When complete, running the following should give a fully working app at `http://localhost`:

```bash
docker-compose up --build
```

All desktop GUI functionality must work in the browser:
- Upload Gerber and see aperture preview
- Select apertures by click and rubber-band
- Exclude/restore apertures
- Duplicate apertures with X/Y offset
- Place library apertures by click on the canvas
- Split large apertures into a grid with configurable cells and webs
- Configure all stencil parameters
- Convert and download the STL
- See the conversion report

The UI must look premium and polished, not like a basic form. Impress the user on first load.
