# Gerber → STL Stencil Generator — Web Application

A modern web application for converting Gerber paste-mask files to printable STL stencils. Built with FastAPI (Python backend) and React (frontend), deployed with Docker Compose.

## Features

✨ **Interactive Aperture Editor**
- Upload Gerber files and preview apertures
- Click-based selection and rubber-band multi-select
- Exclude/restore individual apertures
- Duplicate apertures with X/Y offset

🧩 **Library Apertures**
- Place library apertures (circles, rectangles, ovals) at custom positions
- Rotate and position with precision
- Editable aperture library (JSON format)

⊞ **Grid Splitting**
- Split large apertures into grid cells
- Configurable cell size and web width
- Minimum fragment area filtering

📋 **Parameter Control**
- Sheet thickness and margin
- Mirror and rotation options
- Corner radius and aperture offset
- Precision tuning

💾 **STL Generation**
- Full 3D mesh generation with watertight validation
- Detailed conversion report with statistics
- Automatic STL download

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** v2+ installed
- ~2GB free disk space

### Running the Application

```bash
# Navigate to the project directory
cd gerber_stencil_generator

# Start all services
docker-compose up --build

# Open browser to http://localhost
```

On first run, Docker will:
1. Build the Python backend (Python 3.12-slim)
2. Build the frontend (Node 20 → Nginx alpine)
3. Start both services on the internal network

The application is ready when you see:
```
frontend  | 2024/... ... nginx: master process started
backend   | INFO: Application startup complete
```

### Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Browser (Frontend)              │
│  React 18 + Vite + Vanilla CSS         │
└──────────────┬──────────────────────────┘
               │
        HTTP Requests (REST)
               │
┌──────────────▼──────────────────────────┐
│      Nginx Reverse Proxy (Port 80)      │
│  • SPA routing (/index.html fallback)   │
│  • API proxy (/api/ → backend:8000)     │
│  • Gzip compression                     │
│  • Static file caching                  │
└──────────────┬──────────────────────────┘
               │
        Docker Internal Network
               │
┌──────────────▼──────────────────────────┐
│     FastAPI Backend (Port 8000)         │
│  • Gerber parsing (gerbonara)           │
│  • Geometry operations (Shapely)        │
│  • 3D mesh generation (Trimesh)         │
│  • STL export & validation              │
└─────────────────────────────────────────┘
```

## API Endpoints

All endpoints use JSON (except STL download).

### `POST /api/preview`
Upload Gerber and get aperture list.

**Parameters:**
- `file` — Gerber file (.gtp, .gbp, .gbr, .ger, .gerber)
- `arc_tolerance_mm` — Arc approximation tolerance (default 0.01)
- `precision_grid_mm` — Geometry grid size (default 1e-6)

**Response:**
```json
{
  "session_id": "uuid",
  "apertures": [
    {
      "id": "sha1-key",
      "type": "original",
      "bounds": [x_min, y_min, x_max, y_max],
      "centroid": [cx, cy],
      "area_mm2": 0.42,
      "polygon": [[x, y], ...]
    }
  ],
  "svg": "<SVG string>",
  "bounds": [min_x, min_y, max_x, max_y]
}
```

### `GET /api/library`
Get all aperture presets.

**Response:**
```json
{
  "presets": [
    {
      "name": "Circle Ø0.5 mm",
      "shape": "circle",
      "diameter": 0.5
    }
  ]
}
```

### `POST /api/convert`
Perform full conversion and download STL.

**Parameters:**
- `file` — Gerber file
- `options` — JSON with StencilOptions fields
- `excluded_ids` — JSON array of aperture SHA-1 keys to exclude
- `added_apertures` — JSON array of polygon coordinate lists

**Response:**
- HTTP 200: Binary STL file (octet-stream)
- Header `X-Conversion-Report`: URL-encoded JSON with ConversionReport

### `POST /api/split-grid`
Split aperture into grid cells.

**Parameters (JSON):**
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

**Response:**
```json
{
  "fragments": [
    {
      "id": "added:<uuid>",
      "polygon": [[x, y], ...],
      "bounds": [...],
      "centroid": [...],
      "area_mm2": 0.0
    }
  ]
}
```

### `POST /api/library-aperture`
Create aperture from preset.

**Parameters (JSON):**
```json
{
  "preset": {"shape": "circle", "diameter": 1.0},
  "center_x": 12.5,
  "center_y": 7.3,
  "rotation_deg": 0.0
}
```

**Response:**
```json
{
  "id": "added:<uuid>",
  "polygon": [[x, y], ...],
  "bounds": [...],
  "centroid": [...],
  "area_mm2": 0.0
}
```

## Customization

### Aperture Library

Edit `aperture_library.json` to add or modify presets. Changes are live (no rebuild needed):

```json
{
  "presets": [
    {
      "name": "Circle Ø0.5 mm",
      "shape": "circle",
      "diameter": 0.5
    },
    {
      "name": "Rounded Rectangle 1.5×2.0",
      "shape": "rounded_rectangle",
      "width": 1.5,
      "height": 2.0,
      "radius": 0.3
    }
  ]
}
```

Supported shapes: `circle`, `rectangle`, `rounded_rectangle`, `obround`/`oval`

### UI Theming

Edit color variables in `frontend/src/App.css`:

```css
:root {
  --bg-primary: #0f1117;      /* Dark background */
  --accent-blue: #4f8ef7;     /* Primary accent */
  --accent-amber: #f59e0b;    /* Selection highlight */
  --success: #22c55e;
  --danger: #ef4444;
}
```

### Port Configuration

Change exposed ports in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8000:8000"  # Backend API (change left side)
  frontend:
    ports:
      - "80:80"      # Frontend (change left side)
```

Then rebuild:
```bash
docker-compose up --build
```

## Troubleshooting

### Backend won't start

Check logs:
```bash
docker-compose logs backend
```

Common issues:
- Missing system libraries: Rebuild the backend image
- File permission on `aperture_library.json`: Ensure it's readable

### Frontend can't connect to API

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check Nginx proxy in `frontend/nginx.conf`:
   - Ensure `proxy_pass http://backend:8000/api/;`
   - Service name must match `docker-compose.yml`

### Large file upload fails

Increase `client_max_body_size` in `frontend/nginx.conf` and `stencil_core.py` limits.

### STL file is corrupted or not watertight

Check conversion report for warnings. Most issues are fixed by:
- Increasing `precision_grid_mm`
- Adjusting `arc_tolerance_mm`
- Checking Gerber file validity with external tools

## Development

### Local Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt fastapi uvicorn[standard] python-multipart
python main.py
```

Backend runs on `http://localhost:8000`

### Local Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` with hot reload.

Configure proxy in `vite.config.js` for local API calls.

## Project Structure

```
gerber_stencil_generator/
├── stencil_core.py           # Geometry engine (do not modify)
├── aperture_library.json     # Editable aperture presets
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Service orchestration
│
├── backend/
│   ├── Dockerfile            # Python 3.12-slim image
│   └── main.py              # FastAPI application
│
└── frontend/
    ├── Dockerfile            # Node 20 → Nginx alpine
    ├── nginx.conf           # Reverse proxy config
    ├── package.json         # npm dependencies
    ├── vite.config.js       # Vite build config
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── App.css
        └── components/
            ├── Header.jsx
            ├── Sidebar.jsx
            ├── ParamsTab.jsx
            ├── EditTab.jsx
            ├── Canvas.jsx
            ├── LogPanel.jsx
            ├── Toast.jsx
            └── ConversionModal.jsx
```

## Performance Tips

1. **Larger apertures**: Split into grid cells to reduce mesh complexity
2. **Memory**: Backend uses single worker; add workers in Dockerfile if needed
3. **Caching**: Browser caches static assets (1 year TTL) via Nginx
4. **Compression**: Gzip enabled for text/JSON responses

## License

See `LICENSE.txt` in repository.

## Support

Report issues via GitHub Issues. Include:
- Gerber file (or minimal example)
- Docker version output
- Error message / log

---

**Version**: 1.0.0
**Updated**: 2024-08-29
