from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


GERBER = b"""G04 Minimal paste layer*
%FSLAX46Y46*%
%MOMM*%
%ADD10R,2.000X1.000*%
D10*
X00000000Y00000000D03*
X04000000Y00000000D03*
M02*
"""


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp:
        os.environ["JOBS_DIR"] = temp
        web = importlib.import_module("app")
        with TestClient(web.app) as client:
            health = client.get("/api/health")
            assert health.status_code == 200
            assert health.json()["status"] == "ok"

            response = client.post(
                "/api/convert",
                files={"file": ("board.gtp", GERBER, "application/octet-stream")},
                data={"thickness": "0.12", "margin": "2", "corner_radius": "1"},
            )
            assert response.status_code == 200, response.text
            result = response.json()
            assert result["report"]["watertight"] is True
            assert result["report"]["opening_count"] == 2
            assert "<svg" in result["preview_svg"]
            assert client.get(result["downloads"]["stl"]).content
            assert client.get(result["downloads"]["preview"]).status_code == 200
            assert client.get(result["downloads"]["report"]).json()["input_file"] == "board.gtp"

            invalid = client.post(
                "/api/convert",
                files={"file": ("board.txt", b"bad", "text/plain")},
            )
            assert invalid.status_code == 415

    print("OK: web API converts Gerber and serves STL/SVG/JSON")


if __name__ == "__main__":
    main()
