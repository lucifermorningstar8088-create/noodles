"""Public Hugging Face catalog access and bounded, resumable GGUF downloads."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

import httpx

from noodles.models.registry import ModelRegistry
from noodles.models.schemas import ModelManifest


class ModelDownloadError(RuntimeError):
    """Raised when catalog metadata or a model download cannot be trusted."""


_ALLOWED_DOWNLOAD_HOSTS = (
    "huggingface.co",
    "hf.co",
    "cdn-lfs.huggingface.co",
    "cas-bridge.xethub.hf.co",
    "cas-server.xethub.hf.co",
)


def _allowed_host(host: str | None) -> bool:
    if not host:
        return False
    return any(host == allowed or host.endswith("." + allowed) for allowed in _ALLOWED_DOWNLOAD_HOSTS)


def _safe_repo(repo: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ModelDownloadError("repository must be an owner/name identifier")
    return repo


def _safe_filename(filename: str) -> str:
    path = PurePosixPath(filename)
    if (path.is_absolute() or ".." in path.parts or "\\\\" in filename
            or not filename.lower().endswith(".gguf")):
        raise ModelDownloadError("filename must be a safe relative GGUF path")
    return filename


class HuggingFaceModelService:
    """Reads public model metadata and downloads exact-revision GGUF files only."""

    def __init__(self, storage_dir: Path, registry: ModelRegistry, max_download_bytes: int,
                 *, timeout_seconds: float = 30.0) -> None:
        self.storage_dir = storage_dir.expanduser().resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry
        self.max_download_bytes = max_download_bytes
        self.timeout_seconds = timeout_seconds

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
                            follow_redirects=False, headers={"User-Agent": "Noodles/0.1"})

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query = query.strip()
        if not query or len(query) > 120:
            raise ModelDownloadError("query must contain 1 to 120 characters")
        if not 1 <= limit <= 25:
            raise ModelDownloadError("limit must be between 1 and 25")
        with self._client() as client:
            response = client.get("https://huggingface.co/api/models", params={
                "search": query, "filter": "gguf", "limit": limit,
                "sort": "downloads", "direction": -1,
            })
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, list):
            raise ModelDownloadError("unexpected Hugging Face catalog response")
        results: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            results.append({
                "repository": item["id"],
                "revision": item.get("sha"),
                "downloads": item.get("downloads"),
                "likes": item.get("likes"),
                "gated": item.get("gated", False),
                "license": (item.get("cardData") or {}).get("license"),
            })
        return results

    def inspect(self, repository: str, revision: str = "main") -> dict[str, Any]:
        repository = _safe_repo(repository)
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", revision):
            raise ModelDownloadError("revision must be a branch, tag, or commit identifier")
        url = f"https://huggingface.co/api/models/{quote(repository, safe='/')}/revision/{quote(revision, safe='')}"
        with self._client() as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("sha"), str):
            raise ModelDownloadError("Hugging Face did not return a resolved commit revision")
        resolved = payload["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", resolved):
            raise ModelDownloadError("Hugging Face returned an invalid commit revision")
        siblings = payload.get("siblings", [])
        files: list[dict[str, Any]] = []
        for item in siblings:
            if not isinstance(item, dict) or not isinstance(item.get("rfilename"), str):
                continue
            name = item["rfilename"]
            if name.lower().endswith(".gguf"):
                lfs = item.get("lfs") or {}
                files.append({
                    "filename": name,
                    "size_bytes": lfs.get("size", item.get("size")),
                    "sha256": lfs.get("oid") if isinstance(lfs.get("oid"), str)
                        and re.fullmatch(r"[0-9a-f]{64}", lfs["oid"]) else None,
                })
        card = payload.get("cardData") or {}
        return {
            "repository": repository, "revision": resolved,
            "gated": bool(payload.get("gated", False)),
            "private": bool(payload.get("private", False)),
            "license": card.get("license"), "files": files,
        }

    def download(self, repository: str, revision: str, filename: str, model_id: str,
                 *, accept_license: bool = False) -> ModelManifest:
        repository = _safe_repo(repository)
        filename = _safe_filename(filename)
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", model_id):
            raise ModelDownloadError("model_id contains unsupported characters")
        metadata = self.inspect(repository, revision)
        if metadata["private"] or metadata["gated"]:
            raise ModelDownloadError("private or gated repositories are not supported in this version")
        if not metadata["license"]:
            raise ModelDownloadError("model license is missing; cannot proceed without license metadata")
        if not accept_license:
            raise ModelDownloadError("explicit license acceptance is required before download")
        file_info = next((f for f in metadata["files"] if f["filename"] == filename), None)
        if file_info is None:
            raise ModelDownloadError("selected GGUF file is not present at the pinned revision")
        expected_size = file_info["size_bytes"]
        if not isinstance(expected_size, int) or expected_size <= 0:
            raise ModelDownloadError("Hugging Face did not provide a trustworthy file size")
        if expected_size > self.max_download_bytes:
            raise ModelDownloadError("model exceeds the configured download size limit")
        if self.registry.get_model(model_id) is not None:
            raise ModelDownloadError("model_id is already registered")
        free_bytes = shutil.disk_usage(self.storage_dir).free
        if free_bytes < expected_size + 128 * 1024 * 1024:
            raise ModelDownloadError("insufficient disk space; 128 MiB safety reserve is required")
        target_dir = (self.storage_dir / model_id).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = (target_dir / Path(*PurePosixPath(filename).parts)).resolve()
        try:
            target.relative_to(target_dir)
        except ValueError as exc:
            raise ModelDownloadError("resolved model path escaped its storage directory") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".part")
        url = f"https://huggingface.co/{quote(repository, safe='/')}/resolve/{metadata['revision']}/{quote(filename, safe='/')}?download=true"
        digest = hashlib.sha256()
        downloaded = 0
        if partial.exists():
            if partial.is_symlink() or not partial.is_file():
                raise ModelDownloadError("partial download path is not a regular file")
            downloaded = partial.stat().st_size
            if downloaded > expected_size:
                partial.unlink()
                downloaded = 0
        if downloaded:
            with partial.open("rb") as handle:
                for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                    digest.update(chunk)
        with self._client() as client:
            for _ in range(6):
                parsed = urlsplit(url)
                if parsed.scheme != "https" or not _allowed_host(parsed.hostname):
                    raise ModelDownloadError("download redirect target is not an approved HTTPS host")
                headers = {"Range": f"bytes={downloaded}-"} if downloaded else {}
                with client.stream("GET", url, headers=headers) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location:
                            raise ModelDownloadError("download redirect omitted Location header")
                        url = urljoin(url, location)
                        continue
                    if downloaded and response.status_code == 200:
                        downloaded = 0
                        digest = hashlib.sha256()
                        mode = "wb"
                    elif downloaded and response.status_code == 206:
                        mode = "ab"
                    elif not downloaded and response.status_code == 200:
                        mode = "wb"
                    else:
                        response.raise_for_status()
                        raise ModelDownloadError(f"unexpected download status: {response.status_code}")
                    content_range = response.headers.get("content-range")
                    if mode == "ab" and (not content_range or not content_range.startswith(f"bytes {downloaded}-")):
                        raise ModelDownloadError("server returned an invalid range response")
                    with partial.open(mode) as handle:
                        for chunk in response.iter_bytes(1024 * 1024):
                            if not chunk:
                                continue
                            downloaded += len(chunk)
                            if downloaded > expected_size or downloaded > self.max_download_bytes:
                                raise ModelDownloadError("download exceeded declared or configured size")
                            handle.write(chunk)
                            digest.update(chunk)
                        handle.flush()
                        os.fsync(handle.fileno())
                    break
            else:
                raise ModelDownloadError("too many download redirects")
        if downloaded != expected_size:
            raise ModelDownloadError(f"download incomplete: expected {expected_size} bytes, received {downloaded}")
        actual_hash = digest.hexdigest()
        expected_hash = file_info.get("sha256")
        if expected_hash and actual_hash != expected_hash:
            raise ModelDownloadError("download SHA-256 does not match Hugging Face LFS metadata")
        with partial.open("rb") as handle:
            if handle.read(4) != b"GGUF":
                raise ModelDownloadError("downloaded file does not have a GGUF signature")
        if target.exists() or target.is_symlink():
            raise ModelDownloadError("target model file already exists; refusing to overwrite")
        os.replace(partial, target)
        source_url = f"https://huggingface.co/{repository}/resolve/{metadata['revision']}/{quote(filename, safe='/')}"
        manifest = ModelManifest(
            model_id=model_id, repository=repository, revision=metadata["revision"],
            filename=filename, local_path=str(target), sha256=actual_hash,
            source_checksum_verified=bool(expected_hash), size_bytes=expected_size,
            license=metadata["license"], source_url=source_url,
        )
        try:
            self.registry.register(manifest)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return manifest
