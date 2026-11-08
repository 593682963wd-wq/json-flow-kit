from __future__ import annotations
import re
import json
from typing import Any
_MISSING=object()

def _split_filter(part: str) -> tuple[str, str, str] | None:
    """解析形如 data[iso2=CN] 的段：返回 (base, key, value)；非筛选段返回 None。"""
    if not (part.endswith("]") and "[" in part):
        return None
    base, inner = part[:-1].split("[", 1)
    key, _, value = inner.partition("=")
    value = value.strip().strip('"').strip("'")
    if not key or not value:
        return None
    return base, key, value

def _resolve_path(obj: Any, path: str, default: Any = None) -> Any:
    """点分路径取值：a.b.0.c 支持 dict/list 混合与数字索引；
    支持列表筛选段 data[iso2=CN]（在 dict 列表里按 key=value 找第一项）。"""
    cur = obj
    for part in path.split("."):
        if cur is _MISSING:
            return default
        filt = _split_filter(part)
        if filt is not None:
            base, key, value = filt
            if isinstance(cur, dict):
                cur = cur.get(base, _MISSING)
            else:
                return default
            if cur is _MISSING:
                return default
            if isinstance(cur, list):
                found = [x for x in cur if isinstance(x, dict) and key in x and str(x[key]) == value]
                cur = found[0] if found else _MISSING
            else:
                return default
            continue
        if isinstance(cur, dict):
            cur = cur.get(part, _MISSING)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        else:
            return default
    return cur if cur is not _MISSING else default

def _to_rows(data: Any) -> list[dict[str, Any]]:
    """export 用：把数据规整为行（list[dict] 直接、单 dict 包一层、list[标量] 转 dict）。"""
    _INTERNAL = ("_template", "_truncated")
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return [{k: v for k, v in row.items() if k not in _INTERNAL}
                    for row in data]
        return [{"value": v} for v in data]
    if isinstance(data, dict):
        return [{k: v for k, v in data.items() if k not in _INTERNAL}]
    return [{"value": data}]

def _to_markdown(data: Any) -> str:
    """把结果渲染成 Markdown 片段：dict → 摘要文本+单行表格，list[dict] → 表格，标量 → 文本。

    内部字段（_template/_truncated）不进表格列；_template 文本作为开头摘要展示。
    """
    _INTERNAL = ("_template", "_truncated")

    def _cell(v: Any) -> str:
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False, default=str)
        return str(v).replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\r", "<br>").replace("\n", "<br>")

    if isinstance(data, dict):
        parts: list[str] = []
        tmpl = data.get("_template")
        if isinstance(tmpl, str) and tmpl.strip():
            parts.append(tmpl.strip())
        headers = [h for h in data.keys() if h not in _INTERNAL]
        if headers:
            parts.append("\n".join([
                "| " + " | ".join(_cell(h) for h in headers) + " |",
                "|" + "|".join("---" for _ in headers) + "|",
                "| " + " | ".join(_cell(data[h]) for h in headers) + " |",
            ]))
        return "\n\n".join(parts)
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            headers = list(dict.fromkeys(h for row in data for h in row if h not in _INTERNAL))
            lines = ["| " + " | ".join(_cell(h) for h in headers) + " |",
                     "|" + "|".join("---" for _ in headers) + "|"]
            for row in data:
                lines.append("| " + " | ".join(_cell(row.get(h, "")) for h in headers) + " |")
            return "\n".join(lines)
        return "\n".join(f"- {v}" for v in data)
    return str(data)

def _dedupe_rows(rows: list[dict[str, Any]], key: str | None) -> list[dict[str, Any]]:
    seen: set[Any] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        if key:
            marker = _resolve_path(row, key, _MISSING)
            if marker is _MISSING:
                out.append(row)
                continue
        else:
            marker = row
        marker = json.dumps(marker, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(row)
    return out
