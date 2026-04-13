"""Shared SDK constants."""

import httpx

DEFAULT_BASE_URL = "https://mineru.net/api/v4"

DEFAULT_FLASH_BASE_URL = "https://mineru.net/api/v1/agent"

# Timeout for normal API requests (post, get).
REQUEST_TIMEOUT = httpx.Timeout(30.0, read=120.0)

# Timeout for file uploads (put). More generous because large files need time.
UPLOAD_TIMEOUT = httpx.Timeout(30.0, read=300.0, write=300.0)
