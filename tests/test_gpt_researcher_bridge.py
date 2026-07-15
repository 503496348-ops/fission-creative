import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gpt_researcher_bridge.py"


def test_gpt_researcher_bridge_runs_and_reports_sample_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--sample", "--json", "--topic", "长文创作研究链路"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout, result.stderr

    payload = json.loads(result.stdout)
    assert payload["bridge"] == "ok"
    assert payload["topic"] == "长文创作研究链路"
    assert payload["queries_total"] >= 1
    assert payload["sources_total"] >= 1
    assert payload["outline_sections"] >= 1
    assert isinstance(payload["evidence_cards"], list)
    assert payload["evidence_cards"], "expected evidence cards from bridge"
