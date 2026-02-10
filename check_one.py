#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单行数据本地判断（只读 rules.json，不依赖 Flask/xlsx）"""
import json
import os

RANGE_EPS = 1e-9

# 意甲 客 3 0.5 1.1 0.25 0.75 0.25 0.35 2.1 2.9 3.42 1.92 2.96 3.65 -0.18 0.06 0.23
# 列: A    B  C  D   E    F     G    H    I    J   K   L    M    N    O    P     Q    R
row_raw = "意甲	客	3	0.5	1.1	0.25	0.75	0.25	0.35	2.1	2.9	3.42	1.92	2.96	3.65	-0.18	0.06	0.23"
vals = [x.strip() for x in row_raw.split("\t")]
cols = list("ABCDEFGHIJKLMNOPQR")
data = {c: v for c, v in zip(cols, vals)}

def get_num(row, col):
    val = row.get(col)
    if val is None or val == "": return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def morph_in_group(rule, morph):
    group = rule.get("morph_group")
    if not group:
        return tuple(rule["morph"]) == morph
    return any(tuple(m) == morph for m in group)

def check_conditions(row_data, rules):
    B = str(row_data.get("B", "")).strip()
    D = str(row_data.get("D", "")).strip()
    F = str(row_data.get("F", "")).strip()
    if B not in ("主", "客"):
        return []
    morph = (B, D, F)
    G = get_num(row_data, "G")
    I = get_num(row_data, "I")
    K = get_num(row_data, "K")
    N = get_num(row_data, "N")
    P = get_num(row_data, "P")
    Q = get_num(row_data, "Q")
    R = get_num(row_data, "R")
    col_val = {"G": G, "I": I, "K": K, "N": N, "P": P, "Q": Q, "R": R}
    e = RANGE_EPS
    matched = []
    for rule in rules:
        if not morph_in_group(rule, morph):
            continue
        ok = True
        for key, val in rule["conditions"].items():
            col_name = key.split("_")[0]
            cv = col_val.get(col_name)
            if cv is None:
                ok = False
                break
            if key.endswith("_ge"):
                if cv < val - e: ok = False
            elif key.endswith("_le"):
                if cv > val + e: ok = False
            elif key.endswith("_gt"):
                if cv <= val - e: ok = False
            elif key.endswith("_lt"):
                if cv >= val + e: ok = False
            elif key.endswith("_range"):
                if not (val[0] - e <= cv <= val[1] + e): ok = False
            if not ok:
                break
        if ok:
            matched.append(rule)
    return matched

path = os.path.join(os.path.dirname(__file__), "static", "rules.json")
with open(path, "r", encoding="utf-8") as f:
    rules_data = json.load(f)

rules_85 = rules_data["rules_85"]
rules_80 = rules_data["rules_80"]

matched_85 = check_conditions(data, rules_85)
matched_80 = check_conditions(data, rules_80)

print("输入: 意甲 客 | D=澳门 %.2f F=马会 %s" % (float(data.get("D", 0)), data.get("F")))
print("K=%.2f  N=%.2f  Q=%.2f  R=%.2f" % (
    get_num(data, "K") or 0, get_num(data, "N") or 0, get_num(data, "Q") or 0, get_num(data, "R") or 0,
))
print()
c1 = "满足" if matched_85 else "不满足"
print("条件1（(上+走)或(下+走)>85% 总场次>6 差值>3）:", c1, "匹配", len(matched_85), "条")
for r in matched_85[:5]:
    print("  特征:", r["feature"], "| 总场次:", r["n_total"], "上%d下%d走%d" % (r["shang"], r["xia"], r["zou"]))
print()
c2 = "满足" if matched_80 else "不满足"
print("条件2（上/走/下任一>80% 总场次>4）:", c2, "匹配", len(matched_80), "条")
for r in matched_80[:5]:
    print("  特征:", r["feature"], "| 总场次:", r["n_total"], "上%d下%d走%d" % (r["shang"], r["xia"], r["zou"]), "| 下比例 %.2f%%" % r["xia_ratio"])
