"""
main.py — FastAPI backend for School AI BAV Dashboard.

Serves API endpoints for all 4 governance levels:
  - State Commissioner
  - District Education Officer
  - Block Education Officer
  - School Headmaster

Plus proposal submission and configurable budget simulation.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import state, district, school, proposals

app = FastAPI(
    title="School AI BAV — Dashboard API",
    version="1.0.0",
    description="Multi-level governance dashboard for 67,000+ schools across Andhra Pradesh",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ────────────────────────────────────────────
app.include_router(state.router,     prefix="/api/state",     tags=["State Dashboard"])
app.include_router(district.router,  prefix="/api/district",  tags=["District Dashboard"])
app.include_router(school.router,    prefix="/api/school",    tags=["School & Block Dashboard"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["Proposals & Budget"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "school-ai-bav"}


# ── Serve React frontend (built files) ──────────────────────
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
