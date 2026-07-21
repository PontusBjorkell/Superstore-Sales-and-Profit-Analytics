"""Central path and project configuration."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DASHBOARD_DATA_DIR = DATA_DIR / "dashboard"
DATABASE_DIR = DATA_DIR / "database"

REPORTS_DIR = PROJECT_ROOT / "reports"
SQL_REPORTS_DIR = REPORTS_DIR / "sql"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SQL_DIR = PROJECT_ROOT / "sql"
IMAGES_DIR = PROJECT_ROOT / "images"

RAW_DATA_PATH = RAW_DATA_DIR / "superstore.csv"
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "superstore_clean.csv"
DATA_QUALITY_REPORT_PATH = REPORTS_DIR / "data_quality_summary.csv"

DATABASE_PATH = DATABASE_DIR / "superstore.db"
DATABASE_VALIDATION_REPORT_PATH = REPORTS_DIR / "database_validation.csv"

SCHEMA_SQL_PATH = SQL_DIR / "create_schema.sql"
VIEWS_SQL_PATH = SQL_DIR / "create_views.sql"
ANALYSIS_SQL_PATH = SQL_DIR / "analysis_queries.sql"

ANALYSIS_MANIFEST_PATH = SQL_REPORTS_DIR / "analysis_manifest.csv"


def create_output_directories() -> None:
    """Create all directories used for generated outputs."""

    directories = [
        PROCESSED_DATA_DIR,
        DASHBOARD_DATA_DIR,
        DATABASE_DIR,
        REPORTS_DIR,
        SQL_REPORTS_DIR,
        ARTIFACTS_DIR,
        IMAGES_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
