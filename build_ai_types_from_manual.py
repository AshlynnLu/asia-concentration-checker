#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 2026 手工形态汇总类型库（summary_types_v2.json）作为模板，
在全量比赛库 docs/20252026欧洲FB.xlsx 中重新统计，并生成 AI 类型库：

- 忽略手工条件中的“=”约束，只保留 >、<、>=、<=、range 等条件；
- 统计每个类型的 上/下/走 及总场次；
- 选出满足以下任一规则的类型写入 ai_types_from_manual.json：
  1）若 走/(上+走+下) == 1.0，则总场次 > 3 即纳入（纯走盘类型放宽样本数）；
  2）否则要求：
       - 总场次 > 5；
       - 且 max(上占比, 下占比, 走占比) > 0.8。

并根据占比归类到：
- ai_groups 包含 "cond1"：上占比或下占比 > 0.8；
- ai_groups 包含 "cond2"：走占比 > 0.8（含 100% 且样本>3 的情况）。
"""

import json
import os
from collections import Counter

from analyze_asia_concentration import load_xlsx, filter_rows, unique_by_game


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(PROJECT_ROOT, "docs", "20252026欧洲FB.xlsx")
MANUAL_TYPES_FILE = os.path.join(PROJECT_ROOT, "static", "summary_types_v2.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "static", "ai_types_from_manual.json")


def _load_manual_types():
    with open(MANUAL_TYPES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_ai_conditions(conditions):
    """
    从手工类型条件中构造 AI 用的条件字典：
    - 忽略等号条件（op == '='），避免浮点等值比较带来的干扰；
    - 仅保留 >、<、>=、<=、range 这些类型（映射到现有 filter_rows 的 *_gt/*_lt/*_ge/*_le/*_range 键）。

    summary_types_v2.json 中 conditions 的结构为：
    {
        "N": [{"op": ">", "value": 3.4}, ...],
        "Q": [{"op": "<", "value": 0.0}, ...],
        ...
    }
    """
    if not conditions:
        return {}

    ai_cond = {}
    for col, cond_list in conditions.items():
        if not cond_list:
            continue
        for c in cond_list:
            op = c.get("op")
            val = c.get("value")
            # 忽略 "=" 条件
            if op == "=":
                continue
            if op in (">", "<", ">=", "<=") and not isinstance(val, (int, float)):
                continue
            key = None
            if op == ">":
                key = f"{col}_gt"
            elif op == "<":
                key = f"{col}_lt"
            elif op == ">=":
                key = f"{col}_ge"
            elif op == "<=":
                key = f"{col}_le"
            elif op == "range":
                # 期望 value 为 [low, high]
                if (
                    isinstance(val, (list, tuple))
                    and len(val) == 2
                    and all(isinstance(x, (int, float)) for x in val)
                ):
                    key = f"{col}_range"
                else:
                    continue

            if key is None:
                continue

            # 同一列多个条件时，这里简单保留全部，交由 filter_rows 共同约束
            # 如果已有，则覆盖或合并；但为了简单起见，同一 key 只保留一次，后者覆盖前者。
            ai_cond[key] = val

    return ai_cond


def _stats_from_rows(rows):
    c = Counter(r["U"] for r in rows)
    shang = c.get("上", 0)
    xia = c.get("下", 0)
    zou = c.get("走", 0)
    n_total = len(rows)
    if n_total <= 0:
        return n_total, shang, xia, zou, 0.0, 0.0, 0.0
    shang_ratio = shang / n_total
    xia_ratio = xia / n_total
    zou_ratio = zou / n_total
    return n_total, shang, xia, zou, shang_ratio, xia_ratio, zou_ratio


def build_ai_types():
    print("加载比赛数据:", DATA_FILE)
    all_rows = load_xlsx(DATA_FILE)
    print(f"共有等值记录 {len(all_rows)} 条")

    print("加载手工形态汇总类型库:", MANUAL_TYPES_FILE)
    manual = _load_manual_types()
    manual_types = manual.get("types", [])

    ai_types = []
    total_cond1 = 0
    total_cond2 = 0

    for t in manual_types:
        morph = t.get("morph") or []
        if len(morph) != 3:
            continue

        side, d, f = morph
        if side not in ("主", "客"):
            continue

        # 构造形态组（单一形态）
        morph_arg = (side, str(d), str(f))

        conditions = t.get("conditions") or {}
        ai_conditions = _build_ai_conditions(conditions)
        if not ai_conditions:
            # 没有可用的阈值条件，则跳过
            continue

        matched = filter_rows(all_rows, morph_arg, **ai_conditions)
        if not matched:
            continue

        matched_unique = unique_by_game(matched)
        n_total, shang, xia, zou, shang_ratio, xia_ratio, zou_ratio = _stats_from_rows(
            matched_unique
        )

        if n_total == 0:
            continue

        # AI 选型规则：
        # 1）若全是走盘，则只要求总场次 > 3
        ai_groups = []
        if zou_ratio == 1.0:
            if n_total > 3:
                ai_groups.append("cond2")
        else:
            # 2）否则要求总场次 > 5 且任一占比 > 0.8
            max_ratio = max(shang_ratio, xia_ratio, zou_ratio)
            if n_total > 5 and max_ratio > 0.8:
                if shang_ratio > 0.8 or xia_ratio > 0.8:
                    ai_groups.append("cond1")
                if zou_ratio > 0.8:
                    ai_groups.append("cond2")

        if not ai_groups:
            continue

        # 推荐方向：按三者比例最大者决定
        prediction = None
        if shang_ratio >= xia_ratio and shang_ratio >= zou_ratio:
            prediction = "上"
        elif xia_ratio >= shang_ratio and xia_ratio >= zou_ratio:
            prediction = "下"
        else:
            prediction = "走"

        if "cond1" in ai_groups:
            total_cond1 += 1
        if "cond2" in ai_groups:
            total_cond2 += 1

        ai_types.append(
            {
                "id": t.get("id"),
                "source_manual_id": t.get("id"),
                "row_index": t.get("row_index"),
                "morph": [str(side), str(d), str(f)],
                "df_group": t.get("df_group"),
                "side": t.get("side"),
                "feature_text": t.get("feature_text"),
                "ai_conditions": ai_conditions,
                "stats": {
                    "n_total": n_total,
                    "shang": shang,
                    "xia": xia,
                    "zou": zou,
                },
                "ratios": {
                    "shang_ratio": shang_ratio,
                    "xia_ratio": xia_ratio,
                    "zou_ratio": zou_ratio,
                },
                "ai_groups": ai_groups,
                "prediction": prediction,
            }
        )

    meta = {
        "source_manual_types_file": os.path.relpath(
            MANUAL_TYPES_FILE, PROJECT_ROOT
        ),
        "data_file": os.path.relpath(DATA_FILE, PROJECT_ROOT),
        "total_types": len(ai_types),
        "total_cond1_types": total_cond1,
        "total_cond2_types": total_cond2,
    }

    out = {"meta": meta, "types": ai_types}

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"AI 类型库已生成：{OUTPUT_FILE}")
    print(
        f"总类型数: {len(ai_types)}, cond1: {total_cond1}, cond2: {total_cond2}"
    )


if __name__ == "__main__":
    build_ai_types()

