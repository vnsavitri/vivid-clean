"""Fail-closed client for the pinned watermarks-remover service."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_INPUT_BYTES = 256 << 20
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class ServiceError(RuntimeError):
    """The cleaner couldn't give a trustworthy result."""


class WatermarksClient:
    def __init__(
        self, base_url: str | None = None, token: str | None = None, timeout: float = 60
    ):
        self.base_url = (
            base_url
            or os.environ.get("WATERMARKS_SERVICE_URL")
            or "http://127.0.0.1:8765"
        ).rstrip("/")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS:
            raise ServiceError(
                "WATERMARKS_SERVICE_URL must use HTTP on localhost, 127.0.0.1 or ::1"
            )
        self.token = (
            token
            if token is not None
            else os.environ.get("WATERMARKS_SERVER_API_KEY", "")
        )
        self.timeout = timeout

    def _request(
        self, method: str, endpoint: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(
            f"{self.base_url}{endpoint}", data=body, headers=headers, method=method
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            message = exc.read().decode("utf-8", "replace")[:300]
            raise ServiceError(
                f"cleaning service returned HTTP {exc.code}: {message}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ServiceError(
                f"cleaning service isn't available at {self.base_url}: {exc}"
            ) from exc
        try:
            result = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ServiceError("cleaning service returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise ServiceError("cleaning service returned the wrong response type")
        if result.get("ok") is not True:
            raise ServiceError(
                str(
                    result.get("error")
                    or "cleaning service reported an incomplete result"
                )
            )
        return result

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def capabilities(self) -> dict[str, Any]:
        return self._request("GET", "/capabilities")

    def clean(self, source: str | Path) -> tuple[bytes, dict[str, Any]]:
        path = Path(source)
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise ServiceError("input exceeds the 256 MiB safety limit")
        result = self._request(
            "POST",
            "/clean",
            {
                "file": base64.b64encode(path.read_bytes()).decode("ascii"),
                "name": path.name,
                "options": {"detect_before": True, "detect_after": True},
            },
        )
        encoded = result.get("cleaned")
        report = result.get("report")
        if not isinstance(encoded, str) or not isinstance(report, dict):
            raise ServiceError("cleaning service omitted cleaned bytes or its report")
        try:
            cleaned = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise ServiceError(
                "cleaning service returned invalid cleaned bytes"
            ) from exc
        if not cleaned:
            raise ServiceError("cleaning service returned an empty file")
        return cleaned, {"kind": result.get("kind", "unknown"), **report}
