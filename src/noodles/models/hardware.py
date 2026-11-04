"""Conservative hardware and storage inventory without shelling out to host commands."""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path


def _memory_bytes() -> int | None:
    if hasattr(os, "sysconf"):
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            if (
                isinstance(pages, int)
                and isinstance(page_size, int)
                and pages > 0
                and page_size > 0
            ):
                return pages * page_size
        except (ValueError, OSError):
            pass
    if platform.system() == "Windows":
        try:
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_phys", ctypes.c_ulonglong),
                    ("avail_phys", ctypes.c_ulonglong),
                    ("total_page", ctypes.c_ulonglong),
                    ("avail_page", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("avail_virtual", ctypes.c_ulonglong),
                    ("avail_extended", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            windows_api = getattr(ctypes, "windll", None)
            if windows_api is not None and windows_api.kernel32.GlobalMemoryStatusEx(
                ctypes.byref(status)
            ):
                return int(status.total_phys)
        except (AttributeError, OSError):
            pass
    return None


def inspect_hardware(model_dir: Path) -> dict[str, object]:
    """Return observed host facts; GPU details are explicitly unknown until probed safely."""
    disk = shutil.disk_usage(model_dir)
    return {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "unknown",
        "logical_cpu_count": os.cpu_count(),
        "total_ram_bytes": _memory_bytes(),
        "model_storage_free_bytes": disk.free,
        "gpu": {"status": "not_probed", "details": None},
        "inference_baseline": "cpu",
    }
