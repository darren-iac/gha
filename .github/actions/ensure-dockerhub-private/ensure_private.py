#!/usr/bin/env python3
"""Create a missing Docker Hub repository privately and fail closed otherwise."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

HUB = "https://hub.docker.com/v2"
RETRYABLE = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 6


def request_once(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, dict, str | None]:
    request = urllib.request.Request(
        f"{HUB}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}, None
    except urllib.error.HTTPError as error:
        raw = error.read()
        retry_after = error.headers.get("Retry-After") if error.headers else None
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"raw": raw.decode(errors="replace")[:200]}
        return error.code, payload, retry_after


def request(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, dict]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        status, payload, retry_after = request_once(method, path, token, body)
        if status not in RETRYABLE or attempt == MAX_ATTEMPTS:
            return status, payload
        try:
            delay = min(float(retry_after), 120.0) if retry_after else min(15.0 * attempt * attempt, 120.0)
        except ValueError:
            delay = min(15.0 * attempt * attempt, 120.0)
        print(
            f"Docker Hub API {method} {path} returned {status}; "
            f"attempt {attempt}/{MAX_ATTEMPTS}, retrying in {delay:.0f}s",
            file=sys.stderr,
        )
        time.sleep(delay)
    raise AssertionError("unreachable")


def login(identifier: str, secret: str) -> str:
    request = urllib.request.Request(
        f"{HUB}/auth/token",
        method="POST",
        data=json.dumps({"identifier": identifier, "secret": secret}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)["access_token"]
    except Exception:
        # Docker Hub also accepts some scoped access tokens directly.
        return secret


def main() -> None:
    repo = os.environ.get("DOCKERHUB_REPO", "")
    if "/" not in repo:
        raise SystemExit(f"DOCKERHUB_REPO must be '<namespace>/<name>', got {repo!r}")
    namespace, name = repo.split("/", 1)
    if not namespace or not name or "/" in name:
        raise SystemExit(f"DOCKERHUB_REPO must name one repository, got {repo!r}")

    secret = os.environ.get("DOCKERHUB_TOKEN", "")
    if not secret:
        raise SystemExit("DOCKERHUB_TOKEN is not set")
    token = login(namespace, secret)

    status, existing = request("GET", f"/repositories/{namespace}/{name}/", token)
    if status == 404:
        status, response = request(
            "POST",
            "/repositories/",
            token,
            {"namespace": namespace, "name": name, "is_private": True},
        )
        if status not in (200, 201):
            raise SystemExit(f"failed to create {repo} privately: {status} {response}")

        # Read after write: a successful POST is not sufficient proof that the
        # registry stored the requested visibility.
        status, existing = request("GET", f"/repositories/{namespace}/{name}/", token)
        if status != 200 or not existing.get("is_private"):
            raise SystemExit(
                f"created {repo}, but could not prove it is private: {status} {existing}"
            )
        print(f"created {repo} as a private repository")
        return

    if status != 200:
        raise SystemExit(f"failed to read {repo}: {status} {existing}")
    if existing.get("is_private"):
        print(f"{repo} already exists and is private")
        return

    raise SystemExit(
        f"{repo} exists and is public; refusing to push. Make it private at "
        f"https://hub.docker.com/r/{repo}/settings and rerun the build."
    )


if __name__ == "__main__":
    main()
