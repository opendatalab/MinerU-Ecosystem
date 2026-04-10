"""Configuration for the MinerU MCP server."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

MINERU_API_TOKEN = os.getenv("MINERU_API_TOKEN", "")

# Default output directory for converted files.
# Use an absolute path under the user's home directory so the server works correctly
# when launched by MCP clients (e.g. Cherry Studio) whose CWD may be read-only.
DEFAULT_OUTPUT_DIR = os.getenv(
    "OUTPUT_DIR",
    str(Path.home() / "mineru-downloads"),
)


def setup_logging() -> logging.Logger:
    """Configure and return the module logger.

    Log level is controlled by the ``MINERU_LOG_LEVEL`` env var (default ``INFO``).
    """
    log_level = os.getenv("MINERU_LOG_LEVEL", "INFO").upper()
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        log_level = "INFO"

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=getattr(logging, log_level), format=log_format)

    logger = logging.getLogger("mineru")
    logger.setLevel(getattr(logging, log_level))
    return logger


# Module-level logger
logger = setup_logging()


def ensure_output_dir(output_dir=None) -> Path:
    """Create and return the output directory, defaulting to DEFAULT_OUTPUT_DIR."""
    output_path = Path(output_dir or DEFAULT_OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path
