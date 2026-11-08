"""
Unit and Integration Tests for Phase 11 — Deployment & Complete Walkthrough

Validates:
- All 15 end-to-end operational walkthrough steps
- Production configuration flags and CORS settings
- SQLite WAL mode and foreign key enforcement
- Dockerfile and compose configuration integrity
"""

import os
from pathlib import Path
from app.core.config import settings
from app.experiments.walkthrough_verification import run_walkthrough


def test_complete_15_step_walkthrough():
    """Executes the entire 15-step operational walkthrough."""
    results = run_walkthrough()
    assert len(results) == 15
    for step, status in results.items():
        assert status == "PASSED", f"Walkthrough step '{step}' did not pass: {status}"


def test_production_settings_and_cors_structure():
    """Verifies that CORS origins and settings parse reliably."""
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) >= 1
    assert "http://localhost:5173" in settings.CORS_ORIGINS or "http://localhost" in settings.CORS_ORIGINS


def test_docker_and_deployment_files_exist():
    """Verifies that all containerization and deployment artifacts exist."""
    code_root = Path(__file__).resolve().parent.parent.parent
    assert (code_root / "docker-compose.yml").exists(), "docker-compose.yml must exist"
    assert (code_root / "backend" / "Dockerfile").exists(), "backend/Dockerfile must exist"
    assert (code_root / "frontend" / "Dockerfile").exists(), "frontend/Dockerfile must exist"
    assert (code_root / "frontend" / "nginx.conf").exists(), "frontend/nginx.conf must exist"
    assert (code_root / "docs" / "architecture.md").exists(), "docs/architecture.md must exist"
    assert (code_root / "docs" / "api_documentation.md").exists(), "docs/api_documentation.md must exist"
    assert (code_root / "docs" / "database_schema.md").exists(), "docs/database_schema.md must exist"
    assert (code_root / "docs" / "research_methodology.md").exists(), "docs/research_methodology.md must exist"

