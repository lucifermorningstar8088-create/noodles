from pathlib import Path

from noodles.models.hardware import inspect_hardware


def test_hardware_report_contains_observed_cpu_ram_and_unknown_gpu(tmp_path: Path) -> None:
    result = inspect_hardware(tmp_path)

    assert result["logical_cpu_count"] is not None
    assert result["model_storage_free_bytes"] >= 0
    assert result["inference_baseline"] == "cpu"
    assert result["gpu"] == {"status": "not_probed", "details": None}
