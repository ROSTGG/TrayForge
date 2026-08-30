# Quick Reference Card — Gerber Stencil Generator Web App

## 🚀 Start/Stop

```bash
# Start (quick)
docker-compose up

# Start (rebuild)
docker-compose up --build

# Stop
docker-compose down

# Stop + remove volumes
docker-compose down -v

# View logs
docker-compose logs -f backend   # Backend logs
docker-compose logs -f frontend  # Frontend logs
docker-compose logs              # All logs
```

## 🌐 Access

| Component | URL | Purpose |
|---|---|---|
| **Application** | http://localhost | User interface |
| **Backend API** | http://localhost:8000/api | REST endpoints |
| **API Docs** | http://localhost:8000/docs | Swagger UI (if added) |
| **Health Check** | http://localhost:8000/api/health | Docker health |

## 📝 Key Endpoints

```bash
# Preview Gerber
curl -X POST http://localhost:8000/api/preview \
  -F "file=@board.gbp"

# Get aperture library
curl http://localhost:8000/api/library

# Convert to STL
curl -X POST http://localhost:8000/api/convert \
  -F "file=@board.gbp" \
  -F 'options={"thickness_mm":0.12}' \
  --output stencil.stl

# Health check
curl http://localhost:8000/api/health
```

## 🔧 Configuration

### Change Ports
Edit `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # External:Internal

frontend:
  ports:
    - "8080:80"    # External:Internal
```

### Edit Apertures
Direct edit of `aperture_library.json` (volume mounted):
```json
{
  "name": "Custom Circle",
  "shape": "circle",
  "diameter": 2.0
}
```
Changes live without rebuild.

### Change Stencil Parameters
Edit via UI or API `options` field:
```json
{
  "thickness_mm": 0.12,
  "margin_mm": 10.0,
  "corner_radius_mm": 2.0,
  "arc_tolerance_mm": 0.01,
  "precision_grid_mm": 1e-6,
  "mirror_x": false,
  "mirror_y": false,
  "rotate_deg": 0.0,
  "center_z": false,
  "min_opening_area_mm2": 0.0,
  "sheet_width_mm": null,
  "sheet_height_mm": null
}
```

## 📁 File Structure

```
.
├── backend/
│   ├── Dockerfile
│   └── main.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       └── components/
├── docker-compose.yml
├── aperture_library.json     ← Editable!
├── requirements.txt
├── stencil_core.py          ← Do NOT modify
├── start.sh
├── start.bat
├── WEB_APP_README.md
├── SETUP_GUIDE.md
└── BUILD_SUMMARY.md
```

## 🖥️ UI Keyboard Shortcuts

| Key | Action |
|---|---|
| `F` or `Home` | Fit all apertures in view |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `Scroll Wheel` | Zoom (centered on cursor) |
| `Middle-Click + Drag` | Pan |
| `Space + Left-Drag` | Pan (alternative) |
| `Left-Click` | Select/deselect aperture |
| `Left-Drag` | Rubber-band select multiple |
| `Shift + Click/Drag` | Add to selection |
| `Ctrl + A` | Select all |
| `Esc` | Cancel placement mode |

## 🐛 Troubleshooting

### Docker won't start
```bash
docker ps                    # Check if daemon running
docker system prune -a       # Clean up
docker-compose up --build    # Rebuild everything
```

### Backend connection error
```bash
curl http://localhost:8000/api/health  # Should return {"status": "ok"}
docker-compose logs backend             # Check for errors
```

### Frontend can't reach API
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check proxy in `frontend/nginx.conf`: `proxy_pass http://backend:8000/api/;`
3. Verify service name in docker-compose.yml matches

### Conversion fails with 422 error
- Increase `arc_tolerance_mm` (0.01 → 0.05)
- Increase `precision_grid_mm` (1e-6 → 1e-5)
- Check Gerber file validity
- See logs: `docker-compose logs backend`

### STL not watertight
- Increase precision/arc tolerance in params
- Simplify Gerber (merge gaps, remove slivers)
- Check file with external tools (gerbv, KiCad)

## 📊 Performance Tuning

### Faster Conversions
```dockerfile
# backend/Dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```
Increase workers (default 2) for multi-core utilization.

### Larger File Uploads
```nginx
# frontend/nginx.conf
client_max_body_size 100m;  # Increase from 50m
```

### Reduce UI Lag
- Close browser tabs
- Increase zoom on large aperture counts
- Use modern browser (Chrome/Firefox, not Safari)

## 🔐 Production Checklist

- [ ] Add HTTPS (reverse proxy)
- [ ] Add authentication (JWT/OAuth2)
- [ ] Restrict CORS origin
- [ ] Add rate limiting
- [ ] Enable request logging
- [ ] Use persistent database (Redis) for sessions
- [ ] Monitor resource usage
- [ ] Set up error tracking (Sentry)
- [ ] Add automatic backups
- [ ] Test disaster recovery

## 📚 Documentation Links

- **Setup Guide**: `SETUP_GUIDE.md`
- **Full README**: `WEB_APP_README.md`
- **Build Summary**: `BUILD_SUMMARY.md`
- **API Spec**: Inside `WEB_APP_README.md` (API Reference section)
- **App Description**: `app.md` (original specification)

## 🛠️ Local Development (No Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt fastapi uvicorn[standard] python-multipart
cp ../stencil_core.py ../aperture_library.json .
python main.py
# Backend: http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173 (hot reload)
```

## 💡 Tips & Tricks

### Copy output to clipboard (macOS)
```bash
docker-compose logs backend | pbcopy
```

### Execute command in container
```bash
docker exec stencil-backend python -c "print('hello')"
docker exec -it stencil-frontend sh
```

### Monitor live stats
```bash
docker stats
```

### Save logs to file
```bash
docker-compose logs > app.log
docker-compose logs backend > backend.log
```

### Rebuild single service
```bash
docker-compose build backend
docker-compose up  # (restarts with new backend image)
```

## ✨ Feature Quick Links

| Feature | Where | How |
|---|---|---|
| **Upload Gerber** | Sidebar | Drag-drop or click upload zone |
| **View Apertures** | Canvas | Rendered as SVG paths |
| **Select Apertures** | Canvas | Click or drag rubber-band |
| **Change Parameters** | Sidebar → Params Tab | Edit form fields |
| **Edit Apertures** | Sidebar → Edit Tab | Exclude, duplicate, split, place |
| **Convert & Download** | Sidebar | Click "Convert to STL" button |
| **View Report** | Modal | Auto-opens after conversion |
| **View Logs** | Bottom panel | Shows all API calls and errors |

## 🎨 UI Theme Colors

```css
--bg-primary: #0f1117        /* Main background */
--bg-secondary: #1a1d24      /* Cards/panels */
--bg-tertiary: #262c36       /* Hover/focus */
--text-primary: #e6edf3      /* Main text */
--text-secondary: #8b949e    /* Secondary text */
--accent-blue: #4f8ef7       /* Interactive elements */
--accent-amber: #f59e0b      /* Selection highlight */
--success: #22c55e           /* Success messages *)
--danger: #ef4444            /* Errors/warnings *)
--border: #30363d            /* Dividers *)
```

Edit in `frontend/src/App.css` at the top.

## 🚀 One-Liner Commands

```bash
# Start everything
docker-compose up --build

# Full restart (clean)
docker-compose down -v && docker-compose up --build

# View all logs
docker-compose logs -f

# Stop everything
docker-compose down

# Run single conversion (curl)
curl -X POST http://localhost:8000/api/convert -F "file=@board.gbp" --output stencil.stl

# Check service status
docker-compose ps

# Rebuild without cache
docker-compose up --build --no-cache

# Access bash in container
docker exec -it stencil-backend /bin/bash

# Monitor memory/CPU
docker stats --no-stream

# View Docker images
docker images | grep stencil

# View Docker volumes
docker volume ls | grep stencil
```

---

**Version**: 1.0.0  
**Last Updated**: 2024-08-29  

For detailed information, see `SETUP_GUIDE.md` or `WEB_APP_README.md`.
