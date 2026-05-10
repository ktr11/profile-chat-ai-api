"""
openapi.json を docs/ に出力するスクリプト。
使い方: python scripts/export_openapi.py
"""
import json
from pathlib import Path

from app.main import app

output_path = Path(__file__).parent.parent / "docs" / "openapi.json"
output_path.parent.mkdir(exist_ok=True)

openapi_schema = app.openapi()
output_path.write_text(json.dumps(openapi_schema, ensure_ascii=False, indent=2))
print(f"Generated: {output_path}")
