# Gerber → STL Stencil Generator — Web Application Setup Guide

## 📋 Overview

This web application provides a modern, browser-based interface for converting Gerber paste-mask files to printable STL stencils. It combines:

- **Backend**: FastAPI (Python 3.12) with Shapely/Trimesh for geometry processing
- **Frontend**: React 18 + Vite with vanilla CSS (dark theme, glassmorphism design)
- **Deployment**: Docker Compose orchestration

## ⚡ Quick Start (30 seconds)

### Prerequisites
- Docker Desktop (includes Docker and Docker Compose)
- ~2GB free disk space
- Port 80 available (or configure in `docker-compose.yml`)

### Start the Application

**Windows:**
```bash
start.bat
```

**macOS/Linux:**
```bash
bash start.sh
```

**Or manually:**
```bash
docker-compose up --build
```

Then open: **http://localhost**

## 📁 Project Structure

```
gerber_stencil_generator/
│
├── 🔧 Configuration & Setup
│   ├── docker-compose.yml          # Service orchestration
│   ├── .dockerignore                # Docker build optimization
│   ├── .gitignore                   # Git ignore rules
│   ├── requirements.txt             # Python dependencies (inherited)
│   └── VERSION.txt                  # Version info
│
├── 🧬 Core Library (DO NOT MODIFY)
│   ├── stencil_core.py              # Geometry engine (immutable)
│   ├── aperture_library.json        # Editable aperture presets
│   └── app.md                       # Full application description
│
├── 🚀 Backend (FastAPI)
│   └── backend/
│       ├── Dockerfile               # Python 3.12-slim image
│       ├── main.py                  # REST API implementation
│       └── (mounts aperture_library.json as volume)
│
├── 🎨 Frontend (React + Vite)
│   └── frontend/
│       ├── Dockerfile               # Node 20 → Nginx alpine (multi-stage)
│       ├── nginx.conf               # Reverse proxy + SPA routing
│       ├── package.json             # npm dependencies
│       ├── vite.config.js          # Vite build configuration
│       ├── index.html               # HTML entry point
│       └── src/
│           ├── main.jsx             # React entry point
│           ├── App.jsx              # Main app component (state management)
│           ├── App.css              # Global styles + theme
│           └── components/          # Reusable UI components
│               ├── Header.jsx       # App header with branding
│               ├── Sidebar.jsx      # Left control panel (360px)
│               ├── ParamsTab.jsx    # Stencil parameter form
│               ├── EditTab.jsx      # Aperture editing tools
│               ├── Canvas.jsx       # SVG aperture viewer (zoomable)
│               ├── LogPanel.jsx     # Conversion log output
│               ├── Toast.jsx        # Notifications
│               └── ConversionModal.jsx  # Results report (slide-up)
│
└── 📚 Documentation
    ├── WEB_APP_README.md            # Full technical documentation
    ├── start.sh                      # Unix/Linux startup script
    └── start.bat                     # Windows startup script
```

## 🐳 Docker Architecture

### Service Topology

```
┌─────────────────────────────────────┐
│   Browser / Client                  │
│   http://localhost                  │
└────────────────┬────────────────────┘
                 │
         HTTP / REST / WebSocket
                 │
      ┌──────────▼────────────────┐
      │   Nginx (Port 80)         │
      │  • SPA routing            │
      │  • Static caching         │
      │  • Gzip compression       │
      │  • API proxy (/api/*)     │
      └──────────────┬────────────┘
                     │
          Docker Internal Network
              (stencil-net)
                     │
      ┌──────────────▼────────────────┐
      │  FastAPI Backend (Port 8000)  │
      │  • Gerber parsing             │
      │  • Geometry operations        │
      │  • 3D mesh generation         │
      │  • STL export                 │
      │  • Healthcheck: /api/health   │
      └───────────────────────────────┘
```

### Volume Mounts

**Backend container:**
- Host: `./aperture_library.json`
- Container: `/app/aperture_library.json` (read-write)
- Purpose: Live editing of aperture presets without rebuild

## 🔨 Building the Application

### First Build (includes downloads)

```bash
docker-compose up --build
```

This will:
1. Pull base images (python:3.12-slim, node:20-alpine, nginx:alpine)
2. Install Python dependencies (gerbonara, shapely, trimesh, fastapi, uvicorn, etc.)
3. Install Node dependencies (react, react-dom, vite)
4. Build frontend (Vite dev bundle)
5. Start both services on internal network

**First run takes ~3-5 minutes** depending on internet speed.

### Subsequent Runs

```bash
docker-compose up
```

Skips the build and starts existing containers.

### Rebuild After Code Changes

```bash
docker-compose up --build
```

Or rebuild specific service:
```bash
docker-compose build backend
docker-compose build frontend
docker-compose up
```

## 📝 Configuration

### Change Backend Port

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Changed from 8000 to 8001
```

Then update `frontend/nginx.conf`:
```nginx
proxy_pass http://backend:8000/api/;  # Still 8000 (internal network)
```

### Change Frontend Port

Edit `docker-compose.yml`:
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Changed from 80 to 8080
```

Then open: `http://localhost:8080`

### Edit Aperture Library

Direct edit without rebuild:
1. Edit `./aperture_library.json` (while containers are running)
2. Refresh browser and upload a new Gerber file
3. Changes are live via volume mount

Supported shapes:
- `circle` — Circular aperture (diameter)
- `rectangle` — Rectangular aperture (width, height)
- `rounded_rectangle` — Rect with rounded corners (width, height, radius)
- `obround` / `oval` — Pill-shaped aperture (width, height)

Example addition:
```json
{
  "name": "QFP-100 Pad (1.4×1.4 mm)",
  "shape": "rounded_rectangle",
  "width": 1.4,
  "height": 1.4,
  "radius": 0.15,
  "rotation_deg": 0
}
```

### Environment Variables

Create `.env` file in root directory:
```env
# Optional: override defaults
BACKEND_PORT=8000
FRONTEND_PORT=80
```

*Note: Currently not used by default—edit docker-compose.yml directly.*

## 🌐 API Reference

All endpoints expect JSON and return JSON (except STL binary download).

### `POST /api/preview`

Upload Gerber and get aperture list.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/preview \
  -F "file=@board.gbp" \
  -F "arc_tolerance_mm=0.01" \
  -F "precision_grid_mm=0.000001"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "apertures": [
    {
      "id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
      "type": "original",
      "bounds": [10.5, 20.3, 15.8, 25.1],
      "centroid": [13.15, 22.7],
      "area_mm2": 18.52,
      "polygon": [[10.5, 20.3], [15.8, 20.3], [15.8, 25.1], [10.5, 25.1]]
    }
  ],
  "svg": "<?xml version...>",
  "bounds": [0, 0, 100, 100]
}
```

### `GET /api/library`

Fetch all aperture presets.

**cURL Example:**
```bash
curl http://localhost:8000/api/library
```

**Response:**
```json
{
  "presets": [
    {
      "name": "Circle Ø0.5 mm",
      "shape": "circle",
      "diameter": 0.5
    },
    {
      "name": "Rectangle 0.6×0.6 mm",
      "shape": "rectangle",
      "width": 0.6,
      "height": 0.6
    }
  ]
}
```

### `POST /api/convert`

Full conversion: Gerber → STL.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/convert \
  -F "file=@board.gbp" \
  -F 'options={"thickness_mm":0.12,"margin_mm":10.0,"center_z":false}' \
  -F 'excluded_ids=["key1","key2"]' \
  -F 'added_apertures=[[x1,y1],[x2,y2]]' \
  --output stencil.stl
```

**Headers in Response:**
- `X-Conversion-Report` — URL-encoded JSON with statistics

### `POST /api/split-grid`

Split aperture into grid cells.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/split-grid \
  -H "Content-Type: application/json" \
  -d '{
    "polygon": [[0,0],[10,0],[10,10],[0,10]],
    "max_cell_width_mm": 3.0,
    "max_cell_height_mm": 3.0,
    "web_x_mm": 0.5,
    "web_y_mm": 0.5,
    "rotation_deg": 0.0,
    "min_fragment_area_mm2": 0.02
  }'
```

### `POST /api/library-aperture`

Create aperture from preset at position.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/library-aperture \
  -H "Content-Type: application/json" \
  -d '{
    "preset": {"shape":"circle","diameter":1.0},
    "center_x": 12.5,
    "center_y": 7.3,
    "rotation_deg": 45.0
  }'
```

### `GET /api/health`

Health check for Docker (used by docker-compose).

**cURL Example:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{"status": "ok"}
```

## 🚨 Troubleshooting

### Application won't start

**Check Docker daemon:**
```bash
docker ps
```

If Docker not running:
- Windows: Open Docker Desktop app
- macOS: Open Docker Desktop app
- Linux: `sudo systemctl start docker`

**Check logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Common errors:**
- `bind: address already in use` — Another app using port 80 or 8000
  - Change ports in docker-compose.yml
- `no space left on device` — Clean up Docker:
  ```bash
  docker system prune -a
  ```

### Backend returns 422 (conversion error)

This is a user error (usually Gerber-related). Check the log:
- Frontend log panel shows error message
- Backend logs: `docker-compose logs backend`

Common issues:
- Gerber file is invalid or corrupted
- Try increasing `arc_tolerance_mm` to 0.05
- Try increasing `precision_grid_mm` to 1e-5

### Frontend can't reach API

1. Verify backend is healthy:
   ```bash
   curl http://localhost:8000/api/health
   ```
   Should return `{"status": "ok"}`

2. Check service name in Nginx proxy matches docker-compose.yml:
   ```bash
   grep "proxy_pass" frontend/nginx.conf
   grep "services:" docker-compose.yml
   ```

3. Check internal networking:
   ```bash
   docker-compose logs frontend | grep "error"
   ```

### STL file is not watertight

Mesh issues are usually due to precision. Try:
1. Increase `precision_grid_mm` (default 1e-6, try 1e-5)
2. Increase `arc_tolerance_mm` (default 0.01, try 0.05)
3. Simplify Gerber (merge small gaps, remove slivers)
4. Check Gerber validity with external tools (gerbv, KiCad, etc.)

### Performance is slow

**Backend:**
- Only runs with 1 Uvicorn worker by default
- Edit `backend/Dockerfile` to increase workers:
  ```dockerfile
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
  ```

**Frontend:**
- Browser is slow on old machines
- Use Chrome/Firefox (not older versions of Safari)
- Close other tabs/apps

**Network:**
- Large Gerber files need good upload speed
- Max file size: 50 MB (set in nginx.conf + FastAPI)

## 🔐 Security Notes

- **No authentication** — Application runs on internal network by default
- **CORS enabled** — All origins allowed (for development)
- **No rate limiting** — Can be abused; add reverse proxy for production
- **File uploads** — Max 50 MB; increase in `nginx.conf` + backend if needed

For production:
1. Run behind reverse proxy (nginx, Caddy, etc.) with HTTPS
2. Enable authentication (OAuth2, JWT, etc.)
3. Restrict CORS origin in FastAPI
4. Add rate limiting
5. Use environment-based configuration (not committed to git)

## 📦 Dependency Versions

| Component | Image | Version |
|---|---|---|
| Backend | `python:3.12-slim` | 3.12.x |
| Frontend Build | `node:20-alpine` | 20.x |
| Frontend Serve | `nginx:alpine` | Latest |
| gerbonara | PyPI | >=1.6, <2 |
| shapely | PyPI | >=2.1, <3 |
| trimesh | PyPI | >=4.0, <6 |
| react | npm | ^18.3.1 |
| vite | npm | ^5.2.10 |

## 🛠️ Local Development (Without Docker)

### Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r ../requirements.txt
pip install fastapi uvicorn[standard] python-multipart

# Copy files from parent
cp ../stencil_core.py .
cp ../aperture_library.json .

python main.py
# Backend runs on http://localhost:8000
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173 with hot reload
```

Configure frontend to proxy API calls to backend. Edit `vite.config.js`:
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### Full Local Dev (No Docker)

1. Start backend (terminal 1):
   ```bash
   cd backend && python main.py
   ```

2. Start frontend (terminal 2):
   ```bash
   cd frontend && npm run dev
   ```

3. Open http://localhost:5173

## 📚 Additional Resources

- **Gerber Specification**: IPC-2581 / RS-274X
- **Shapely Documentation**: https://shapely.readthedocs.io/
- **Trimesh Documentation**: https://trimesh.org/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Vite Documentation**: https://vitejs.dev/

## 🎯 Next Steps

1. **Customize UI Theme**
   - Edit `frontend/src/App.css` (CSS variables at top)
   - Change logo/branding in `frontend/src/components/Header.jsx`

2. **Add More Aperture Presets**
   - Edit `aperture_library.json` directly
   - No restart needed (volume mount)

3. **Enable Production Features**
   - Add HTTPS (Let's Encrypt + reverse proxy)
   - Add authentication
   - Set up monitoring/logging (ELK, Prometheus, etc.)

4. **Scale to Multiple Workers**
   - Edit `backend/Dockerfile` (increase workers)
   - Add load balancer (docker-compose: multiple backend services)

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify Docker is running: `docker ps`
3. Try rebuild: `docker-compose up --build`
4. Clean and restart: `docker-compose down -v && docker-compose up`

---

**Version**: 1.0.0  
**Last Updated**: 2024-08-29  
**License**: See LICENSE.txt
