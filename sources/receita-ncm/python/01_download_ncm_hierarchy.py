from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json"


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return re.sub(r"^\s*-{1,3}\s*", "", value).replace("\u00a0", " ").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official Portuguese SH2/SH4/SH6 hierarchy from Sistema Classif.")
    parser.add_argument("--output", default="data/nomenclature_pt.json")
    args = parser.parse_args()
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "official-data-api-toolkit/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        source = json.load(response)
    levels = {level: {} for level in ("2", "4", "6")}
    for row in source.get("Nomenclaturas", []):
        code = re.sub(r"\D", "", str(row.get("Codigo", "")))
        if len(code) in (2, 4, 6):
            levels[str(len(code))][code] = clean(row.get("Descricao", ""))
    payload = {"meta": {"source": SOURCE_URL, "retrieved_at": datetime.now(timezone.utc).isoformat(), "ncm_as_of": source.get("Data_Ultima_Atualizacao_NCM"), "act": source.get("Ato")}, **levels}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved SH2={len(levels['2'])}, SH4={len(levels['4'])}, SH6={len(levels['6'])} to {output}")


if __name__ == "__main__":
    main()
