#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 docs/2026欧洲FB手工形态汇总.xlsx 的「汇总」表导出最新人工确认的类型库，
仅用于网页快速判断，不再连数据库重算。

输出：static/summary_types.json
"""

import os
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any, Dict, List


def _load_summary_sheet(path: str) -> List[Dict[str, Any]]:
    """解析 2026欧洲FB手工形态汇总.xlsx 的 sheet2（汇总），返回规则行。"""
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path, "r") as z:
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

        # 读取 sharedStrings
        with z.open("xl/sharedStrings.xml") as f:
            ss_root = ET.parse(f).getroot()
        strings: List[str] = []
        for si in ss_root.findall(".//main:si", ns):
            texts = si.findall(".//main:t", ns)
            strings.append("".join(t.text or "" for t in texts) if texts else "")

        # 直接读取 sheet2.xml（已确认为“汇总”）
        with z.open("xl/worksheets/sheet2.xml") as f:
            sheet_root = ET.parse(f).getroot()

    rows_raw: Dict[int, Dict[str, str]] = defaultdict(dict)

    for row in sheet_root.findall(".//main:sheetData/main:row", ns):
        r_idx_attr = row.get("r")
        try:
            r_idx = int(r_idx_attr)
        except (TypeError, ValueError):
            continue
        for c in row.findall("main:c", ns):
            ref = c.get("r")  # 如 "A2"
            if not ref:
                continue
            v = c.find("main:v", ns)
            t = c.get("t")
            if v is not None and v.text is not None:
                if t == "s":
                    idx = int(v.text)
                    val = strings[idx] if 0 <= idx < len(strings) else ""
                else:
                    val = v.text
            else:
                val = ""
            m = re.match(r"([A-Z]+)\d+", ref)
            if not m:
                continue
            col = m.group(1)
            rows_raw[r_idx][col] = (val or "").strip()

    def is_group_header(s: str) -> bool:
        s = (s or "").strip()
        # 例如 "0/0", "0/0.25", "0.25/0", "0.5/0.25"
        return bool(re.match(r"^\d+(?:\.\d+)?/\d+(?:\.\d+)?$", s))

    rules: List[Dict[str, Any]] = []
    current_group = ""

    for r_idx in sorted(rows_raw.keys()):
        row = rows_raw[r_idx]
        a_val = row.get("A", "")
        if is_group_header(a_val):
            current_group = a_val
            continue

        if a_val not in ("主", "客"):
            continue
        if not current_group:
            continue

        # 忽略全空行
        if not any(row.get(col, "") for col in ("B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M")):
            continue

        cols = {}
        for col in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"):
            cols[col] = row.get(col, "").strip()

        rules.append(
            {
                "row_index": r_idx,
                "group": current_group,
                "cols": cols,
            }
        )

    return rules


_HEADER_NAME_MAP = {
    "B": "马会",
    "C": "水差",
    "D": "澳平",
    "E": "马主",
    "F": "马平",
    "G": "主差",
    "H": "平差",
    "I": "客差",
}

# 规则表列 -> 用户输入 A-R 列
_COL_TO_INPUT_COL = {
    "B": "F",  # 会：汇总「马会」 -> 数据 F 列（马会）
    "C": "I",  # 汇总「水差」      -> 数据 I 列（水差）
    "D": "K",  # 汇总「澳平」      -> 数据 K 列（澳 后面的那列）
    "E": "M",  # 汇总「马主」      -> 数据 M 列（马 后面的那列 = 马主）
    "F": "N",  # 汇总「马平」      -> 数据 N 列（马 后面的下一列 = 马平）
    "G": "P",  # 汇总「主差」      -> 数据 P 列（主差）
    "H": "Q",  # 汇总「平差」      -> 数据 Q 列（平差）
    "I": "R",  # 汇总「客差」      -> 数据 R 列（客差）
}


def _normalize_cond_text(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = (
        s.replace("（", "(")
        .replace("）", ")")
        .replace("＜", "<")
        .replace("＞", ">")
        .replace("≦", "<=")
        .replace("≧", ">=")
        .replace("≤", "<=")
        .replace("≥", ">=")
        .replace(" ", "")
    )
    # 用 "且" 作为 AND 分隔符
    s = s.replace("且", "&&")
    return s


def _parse_atom(atom: str) -> Dict[str, Any]:
    """解析一个原子条件字符串为 {op, value}。失败则抛异常。"""
    atom = atom.strip()
    if not atom:
        raise ValueError("empty atom")
    op = None
    val_str = None

    if atom.startswith(">="):
        op = ">="
        val_str = atom[2:]
    elif atom.startswith("<="):
        op = "<="
        val_str = atom[2:]
    elif atom.startswith(">"):
        op = ">"
        val_str = atom[1:]
    elif atom.startswith("<"):
        op = "<"
        val_str = atom[1:]
    else:
        # 纯数字，视为等号
        op = "="
        val_str = atom
    value = float(val_str)
    return {"op": op, "value": value}


def _parse_conditions_for_col(text: str) -> List[Dict[str, Any]]:
    """将单元格中的条件文本解析为原子条件列表。

    支持两种形式：
    1）用 “且” 连接的多个不等式：<3.36且>3.19
    2）用 “~” 表示区间：0.01~0.03  等价于 >=0.01 且 <=0.03
    """
    s = _normalize_cond_text(text)
    if not s:
        return []
    conds: List[Dict[str, Any]] = []

    # 先处理纯区间形式：形如 "a~b"（不含 且）
    if "&&" not in s and "~" in s:
        parts = s.split("~")
        if len(parts) == 2 and parts[0] and parts[1]:
            try:
                v1 = float(parts[0])
                v2 = float(parts[1])
                lo, hi = (v1, v2) if v1 <= v2 else (v2, v1)
                conds.append({"op": ">=", "value": lo})
                conds.append({"op": "<=", "value": hi})
                return conds
            except Exception:
                # 回退到普通解析
                pass

    # 普通形式：用 且/&& 连接的多个原子条件
    parts = s.split("&&")
    for p in parts:
        if not p:
            continue
        try:
            conds.append(_parse_atom(p))
        except Exception:
            # 解析失败就忽略该原子条件
            continue
    return conds


def _build_feature_text(cols: Dict[str, str]) -> str:
    parts: List[str] = []
    for col in ("B", "C", "D", "E", "F", "G", "H", "I"):
        v = cols.get(col, "")
        if not v:
            continue
        name = _HEADER_NAME_MAP.get(col, col)
        parts.append(f"{name}:{v}")
    feat = "，".join(parts)
    pred = cols.get("J", "")
    if pred:
        if feat:
            return f"{feat}；预测:{pred}"
        return f"预测:{pred}"
    return feat


def build_summary_types(
    xlsx_path: str = "docs/2026欧洲FB手工形态汇总.xlsx",
) -> Dict[str, Any]:
    """构建基于“汇总”表的手工类型库（只使用人工统计）。"""
    raw_rules = _load_summary_sheet(xlsx_path)
    types: List[Dict[str, Any]] = []

    for idx, r in enumerate(raw_rules, start=1):
        cols = r["cols"]
        group_str = r["group"]  # 例如 "0/0", "0/0.25"
        side = cols.get("A", "")
        if side not in ("主", "客"):
            continue

        try:
            d_group, f_group = [x.strip() for x in group_str.split("/", 1)]
        except ValueError:
            continue

        morph = [side, d_group, f_group]

        # 解析条件
        conds: Dict[str, List[Dict[str, Any]]] = {}
        for col_letter, input_col in _COL_TO_INPUT_COL.items():
            text = cols.get(col_letter, "")
            if not text:
                continue
            parsed = _parse_conditions_for_col(text)
            if parsed:
                conds[input_col] = parsed

        # 人工统计的上/走/下
        def _to_int(x: str) -> int:
            x = (x or "").strip()
            if not x:
                return 0
            try:
                return int(float(x))
            except Exception:
                return 0

        shang = _to_int(cols.get("K", ""))
        zou = _to_int(cols.get("L", ""))
        xia = _to_int(cols.get("M", ""))

        t = {
            "id": idx,
            "row_index": r["row_index"],
            "group": group_str,
            "morph": morph,
            "conditions": conds,
            "prediction": cols.get("J", ""),
            "feature_text": _build_feature_text(cols),
            "stats": {
                "shang": shang,
                "zou": zou,
                "xia": xia,
            },
        }
        types.append(t)

    return {
        "meta": {
            "source_file": xlsx_path,
            "sheet": "汇总",
            "total_types": len(types),
        },
        "types": types,
    }


def main() -> None:
    data = build_summary_types()
    os.makedirs("static", exist_ok=True)
    out_path = os.path.join("static", "summary_types_v2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已导出汇总类型库到: {out_path}")
    print(f"  类型总数: {data['meta']['total_types']}")


if __name__ == "__main__":
    main()

