from typing import List, Dict, Any

def flatten_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flattens Lightdash query results from:
    [{"field_id": {"value": {"raw": 123, "formatted": "123"}}}]
    to:
    [{"field_id": 123}]
    """
    flattened = []
    for row in rows:
        flat_row = {}
        for key, value in row.items():
            if isinstance(value, dict) and "value" in value and "raw" in value["value"]:
                flat_row[key] = value["value"]["raw"]
            else:
                flat_row[key] = value
        flattened.append(flat_row)
    return flattened
