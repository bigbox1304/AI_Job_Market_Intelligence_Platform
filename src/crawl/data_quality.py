import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd


def build_quality_report(
    df: pd.DataFrame,
    required_columns: Iterable[str],
    source_rows: int,
    invalid_rows: int = 0,
    duplicate_rows: int = 0,
) -> Dict[str, Any]:
    required_columns = list(required_columns)
    missing_values = {
        column: int(df[column].isna().sum()) if column in df else source_rows
        for column in required_columns
    }
    empty_required_rows = int(df[required_columns].isna().any(axis=1).sum()) if all(column in df for column in required_columns) else len(df)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_rows": source_rows,
        "clean_rows": int(len(df)),
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
        "rows_missing_required_fields": empty_required_rows,
        "missing_values_by_column": missing_values,
        "quality_status": "pass" if len(df) and empty_required_rows == 0 else "review",
    }


def write_quality_report(report: Dict[str, Any], output_dir: Path, name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"quality_{name}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
