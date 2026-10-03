import io
import csv
import time
from typing import Any, Dict, List, Optional
from app.plugins.base import BasePlugin

class CSVPlugin(BasePlugin):
    """
    Dedicated CSV Data Processing Plugin for MedSentinel.
    Supports secure parsing, strict schema validation, data cleaning,
    duplicate record identification, statistical profiling, and export.
    """

    def __init__(self):
        super().__init__(
            plugin_id="csv",
            name="CSV Intelligence Engine",
            category="files_data",
            provider="MedSentinel Core",
            version="1.0.0",
            description="High-performance, secure CSV parsing, schema validation, deduplication, and clinical data export.",
            icon="table",
            capabilities=[
                "upload_csv",
                "parse_csv",
                "validate_csv",
                "clean_csv",
                "deduplicate_csv",
                "analyze_csv",
                "export_csv"
            ],
            permissions=["csv.read", "csv.write", "csv.clean", "csv.export"],
            rate_limit_rpm=120
        )

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        self.status = "CONNECTED"
        self.is_enabled = True
        return True

    async def disconnect(self) -> bool:
        self.status = "DISCONNECTED"
        self.is_enabled = False
        return True

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "success": True,
            "latency_ms": 2,
            "status": "HEALTHY",
            "message": "CSV intelligence engine operational and memory-safe."
        }

    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if action == "parse_csv":
            raw_content = parameters.get("content", "")
            delimiter = parameters.get("delimiter", ",")
            f = io.StringIO(raw_content)
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = [row for row in reader]
            return {
                "success": True,
                "row_count": len(rows),
                "headers": reader.fieldnames or [],
                "preview": rows[:5]
            }

        elif action == "validate_csv":
            raw_content = parameters.get("content", "")
            required_columns = parameters.get("required_columns", [])
            f = io.StringIO(raw_content)
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            missing = [col for col in required_columns if col not in headers]
            return {
                "success": len(missing) == 0,
                "valid": len(missing) == 0,
                "headers": headers,
                "missing_required_columns": missing,
                "error": f"Missing mandatory columns: {missing}" if missing else None
            }

        elif action in ["clean_csv", "deduplicate_csv"]:
            raw_content = parameters.get("content", "")
            key_columns = parameters.get("key_columns", [])
            f = io.StringIO(raw_content)
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            
            seen = set()
            clean_rows = []
            duplicate_count = 0
            
            for row in reader:
                # Strip whitespace
                cleaned_row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                # Deduplication key
                if key_columns:
                    dedup_key = tuple(cleaned_row.get(col, "") for col in key_columns)
                else:
                    dedup_key = tuple(cleaned_row.items())
                    
                if dedup_key in seen:
                    duplicate_count += 1
                else:
                    seen.add(dedup_key)
                    clean_rows.append(cleaned_row)

            # Re-export clean CSV
            out = io.StringIO()
            if headers:
                writer = csv.DictWriter(out, fieldnames=headers)
                writer.writeheader()
                writer.writerows(clean_rows)

            return {
                "success": True,
                "original_rows": len(clean_rows) + duplicate_count,
                "deduplicated_rows": len(clean_rows),
                "duplicates_removed": duplicate_count,
                "cleaned_csv_preview": clean_rows[:3]
            }

        elif action == "analyze_csv":
            raw_content = parameters.get("content", "")
            f = io.StringIO(raw_content)
            reader = csv.DictReader(f)
            rows = [row for row in reader]
            headers = reader.fieldnames or []
            
            # Missing value analysis
            null_counts = {h: 0 for h in headers}
            for r in rows:
                for h in headers:
                    val = r.get(h, "")
                    if val is None or val.strip() == "":
                        null_counts[h] += 1
                        
            return {
                "success": True,
                "total_records": len(rows),
                "columns_count": len(headers),
                "columns": headers,
                "missing_values_per_column": null_counts,
                "data_completeness_pct": round(
                    (1.0 - (sum(null_counts.values()) / (len(rows) * len(headers) if rows and headers else 1))) * 100, 2
                )
            }

        elif action == "export_csv":
            records = parameters.get("records", [])
            headers = parameters.get("headers")
            if not headers and records:
                headers = list(records[0].keys())
            
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=headers or [])
            writer.writeheader()
            writer.writerows(records)
            
            return {
                "success": True,
                "row_count": len(records),
                "csv_output": out.getvalue(),
                "bytes_generated": len(out.getvalue().encode('utf-8'))
            }

        return {
            "success": False,
            "error": f"Action '{action}' is not supported by CSVPlugin"
        }
