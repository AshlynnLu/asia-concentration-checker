#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 docs/规则.xlsx 读取人工统计规则，解析为程序可用的条件，
并基于 docs/20252026欧洲FB.xlsx 重新统计上/走/下场次，生成“手工类型库”。
"""

import os
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from analyze_asia_concentration import load_xlsx, filter_rows, unique_by_game


def _read_rules_xlsx(path: str) -> List[Dict[str, Any]]:
    """
    直接用标准库解析 docs/规则.xlsx。

    返回的每一条记录代表 Excel 中的一行“规则行”（不含分组标题和表头行）：
    {
        "row_index": int,          # Excel 行号（从 1 开始）
        "df_group": "0/0.25",      # A 列分组标题，例如 "0/0.25"
        "side": "主" / "客",        # A 列当前值
        "cols": {                  # B~H、I~L 的原始字符串
            "B": "...",
            "C": "...",
            ...
            "L": "..."
        }
    }
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path, "r") as z:
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

        # 读取 sharedStrings
        with z.open("xl/sharedStrings.xml") as f:
            ss_root = ET.parse(f).getroot()
        strings: List[str] = []
        for s in ss_root.findall(".//main:si", ns):
            texts = s.findall(".//main:t", ns)
            strings.append("".join(x.text or "" for x in texts) if texts else "")

        # 读取 sheet1
        with z.open("xl/worksheets/sheet1.xml") as f:
            root = ET.parse(f).getroot()

    # 把 sheet1 解析成行/列 → 文本
    rows_raw: Dict[int, Dict[str, str]] = defaultdict(dict)

    for row in root.findall(".//main:row", ns):
        r_idx_attr = row.get("r")
        # 有些文件不会给 row.r，直接按子节点推断也可以，但当前文件有 r，这里直接用
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
                try:
                    idx = int(v.text)
                except ValueError:
                    idx = None
                if t == "s" and idx is not None and 0 <= idx < len(strings):
                    val = strings[idx]
                else:
                    val = v.text
            else:
                val = ""
            # 记录列字母 → 文本
            # ref 形如 "A2" / "AA3"，只取前面的字母部分
            m = re.match(r"([A-Z]+)\d+", ref)
            if not m:
                continue
            col_letter = m.group(1)
            rows_raw[r_idx][col_letter] = (val or "").strip()

    # 识别分组标题行：A 列为形如 "0/0.25" 的盘口组
    def _is_group_header(s: str) -> bool:
        s = (s or "").strip()
        # 简单判断：形如 "数字/数字"（允许小数）
        return bool(re.match(r"^\d+(?:\.\d+)?/\d+(?:\.\d+)?$", s))

    group_for_row: Dict[int, str] = {}
    current_group: str = ""
    # 行号从小到大遍历，记录“向上最近的分组标题”
    for r_idx in sorted(rows_raw.keys()):
        a_val = rows_raw[r_idx].get("A", "")
        if _is_group_header(a_val):
            current_group = a_val
        # 对所有行都记录当前 group（没有则为空字符串）
        group_for_row[r_idx] = current_group

    rules: List[Dict[str, Any]] = []

    for r_idx in sorted(rows_raw.keys()):
        row = rows_raw[r_idx]
        a_val = row.get("A", "")
        # 跳过：空行、分组标题行、表头行（A="主客"）
        if not a_val or _is_group_header(a_val) or a_val == "主客":
            continue
        if a_val not in ("主", "客"):
            # 只要主/客行，其余全部忽略
            continue
        df_group = group_for_row.get(r_idx, "")
        if not df_group:
            # 理论上不会发生，无分组则跳过
            continue

        cols = {}
        for col in ("B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"):
            cols[col] = row.get(col, "").strip()

        rules.append(
            {
                "row_index": r_idx,
                "df_group": df_group,
                "side": a_val,
                "cols": cols,
            }
        )

    return rules


_COL_BASE_MAP = {
    # 规则表列 -> 数据表字段名
    "B": "G",  # 马会 -> G（上水/马会）
    "C": "I",  # 水差 -> I
    "D": "K",  # 马主 -> K
    "E": "N",  # 马平 -> N
    "F": "P",  # 主差 -> P
    "G": "Q",  # 平差 -> Q
    "H": "R",  # 客差 -> R
}

_HEADER_NAME_MAP = {
    "B": "马会",
    "C": "水差",
    "D": "马主",
    "E": "马平",
    "F": "主差",
    "G": "平差",
    "H": "客差",
}


def _normalize_condition_text(s: str) -> str:
    """统一去掉全角符号等，便于解析。"""
    if not s:
        return ""
    s = s.strip()
    # 全角符号替换
    s = (
        s.replace("（", "(")
        .replace("）", ")")
        .replace("－", "-")
        .replace("，", ",")
        .replace("＞", ">")
        .replace("＜", "<")
        .replace("＝", "=")
        .replace("～", "~")
    )
    # 去掉空格
    s = re.sub(r"\s+", "", s)
    return s


def _parse_numeric(s: str) -> float:
    return float(s)


def _parse_single_condition(base_col: str, text: str) -> Tuple[str, Any]:
    """
    将类似 ">3.4" / "<=0" / "≥0" / "3~3.1" / "(-0.3~-0.4)" 解析成
    (filter_key, value) 形式，例如：
    - ("N_gt", 3.4)
    - ("I_le", -0.05)
    - ("G_range", (0.8, 0.86))
    """
    s = _normalize_condition_text(text)
    if not s:
        raise ValueError("empty condition")

    # 范围：可能带括号，如 "(a~b)" 或 "a~b"
    if "~" in s:
        # 去掉括号
        if s.startswith("(") and s.endswith(")"):
            s_inner = s[1:-1]
        else:
            s_inner = s
        parts = s_inner.split("~")
        if len(parts) != 2:
            raise ValueError(f"invalid range: {text}")
        v1 = _parse_numeric(parts[0])
        v2 = _parse_numeric(parts[1])
        lo, hi = (v1, v2) if v1 <= v2 else (v2, v1)
        return f"{base_col}_range", (lo, hi)

    # 处理 ≥ ≤ >= <= > < 之类
    # 先统一成 ASCII
    s = s.replace("≥", ">=").replace("≧", ">=").replace("≤", "<=").replace("≦", "<=")

    op = None
    num_str = None

    if s.startswith(">="):
        op = "_ge"
        num_str = s[2:]
    elif s.startswith("<="):
        op = "_le"
        num_str = s[2:]
    elif s.startswith(">"):
        op = "_gt"
        num_str = s[1:]
    elif s.startswith("<"):
        op = "_lt"
        num_str = s[1:]
    elif s.startswith("="):
        # 严格等于可以视作 [v,v] 的 range
        num = _parse_numeric(s[1:])
        return f"{base_col}_range", (num, num)
    else:
        # 没有显式符号，尽量按“等于”的范围处理
        num = _parse_numeric(s)
        return f"{base_col}_range", (num, num)

    num = _parse_numeric(num_str)
    return f"{base_col}{op}", num


def _build_feature_text(cols: Dict[str, str]) -> str:
    """
    把 B~H 的条件列 + I(预测) 拼成一段人工可读的特征描述。
    例如：“客；马会:0.8~0.86，马平:>3.2，平差:>0.05；预测:下盘”
    具体格式不影响程序逻辑，只为人工查看。
    """
    parts: List[str] = []
    for col in ("B", "C", "D", "E", "F", "G", "H"):
        val = cols.get(col, "")
        if not val:
            continue
        name = _HEADER_NAME_MAP.get(col, col)
        parts.append(f"{name}:{val}")
    feat = "，".join(parts) if parts else ""

    pred = cols.get("I", "")
    if pred:
        if feat:
            return f"{feat}；预测:{pred}"
        return f"预测:{pred}"
    return feat


def build_manual_types(
    rules_xlsx_path: str = "docs/规则.xlsx",
    data_xlsx_path: str = "docs/20252026欧洲FB.xlsx",
) -> Dict[str, Any]:
    """
    构建“手工类型库”：
    - 从 docs/规则.xlsx 读取所有手工规则；
    - 按条件解析为 filter_rows 可用的条件；
    - 基于 docs/20252026欧洲FB.xlsx 重新统计上/下/走场次。
    """
    all_rows = load_xlsx(data_xlsx_path)
    raw_rules = _read_rules_xlsx(rules_xlsx_path)

    types: List[Dict[str, Any]] = []
    inconsistent_count = 0

    for idx, r in enumerate(raw_rules, start=1):
        df_group = r["df_group"]  # 例如 "0/0.25"
        side = r["side"]  # "主"/"客"
        cols = r["cols"]

        # 解析 df_group 为 D/F 盘口
        try:
            d_str, f_str = [x.strip() for x in df_group.split("/", 1)]
        except ValueError:
            # 非法分组，跳过
            continue

        morph = (side, d_str, f_str)

        # 条件解析
        conditions: Dict[str, Any] = {}
        parse_errors: List[str] = []

        for col_letter, base_col in _COL_BASE_MAP.items():
            text = cols.get(col_letter, "")
            if not text:
                continue
            try:
                key, val = _parse_single_condition(base_col, text)
            except Exception as e:
                parse_errors.append(f"{col_letter}:{text} -> {e}")
                continue
            # 若同一 base_col 出现多个条件，以“后覆盖前”的方式处理，避免重复列
            conditions[key] = val

        # 人工统计
        try:
            shang_manual = int(cols.get("J") or 0)
        except ValueError:
            shang_manual = 0
        try:
            zou_manual = int(cols.get("K") or 0)
        except ValueError:
            zou_manual = 0
        try:
            xia_manual = int(cols.get("L") or 0)
        except ValueError:
            xia_manual = 0

        # 重新筛选并统计
        matched = filter_rows(all_rows, morph, **conditions)
        matched_unique = unique_by_game(matched)
        c = Counter(r2["U"] for r2 in matched_unique)
        shang = c.get("上", 0)
        xia = c.get("下", 0)
        zou = c.get("走", 0)
        n_total = len(matched_unique)

        # 预测列
        prediction = cols.get("I", "")

        feature_text = _build_feature_text(cols)

        diff = {
            "shang": shang - shang_manual,
            "zou": zou - zou_manual,
            "xia": xia - xia_manual,
        }
        if diff["shang"] or diff["zou"] or diff["xia"]:
            inconsistent_count += 1

        types.append(
            {
                "id": idx,
                "row_index": r["row_index"],
                "df_group": df_group,
                "side": side,
                "morph": [side, d_str, f_str],
                "feature_text": feature_text,
                "prediction": prediction,
                "conditions": conditions,
                "stats": {
                    "n_total": n_total,
                    "shang": shang,
                    "xia": xia,
                    "zou": zou,
                },
                "manual_stats": {
                    "shang": shang_manual,
                    "zou": zou_manual,
                    "xia": xia_manual,
                },
                "diff": diff,
                "parse_errors": parse_errors,
            }
        )

    result = {
        "meta": {
            "source_rules_file": rules_xlsx_path,
            "data_file": data_xlsx_path,
            "total_types": len(types),
            "inconsistent_manual_vs_ai": inconsistent_count,
        },
        "types": types,
    }
    return result


def main() -> None:
    data = build_manual_types()
    os.makedirs("static", exist_ok=True)
    output_file = os.path.join("static", "manual_types.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已导出手工类型库到: {output_file}")
    print(f"  类型总数: {data['meta']['total_types']}")
    print(f"  AI 统计与人工统计不一致条数: {data['meta']['inconsistent_manual_vs_ai']}")

    # 按 df_group 简单汇总数量
    by_group: Dict[str, int] = defaultdict(int)
    for t in data["types"]:
        by_group[t["df_group"]] += 1
    print("  各盘口组规则数:")
    for k in sorted(by_group.keys()):
        print(f"    {k}: {by_group[k]} 条")


if __name__ == "__main__":
    main()

