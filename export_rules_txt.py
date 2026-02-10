#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出 AI 类型库（条件1、条件2）为人类可读的 TXT 文件。
数据来源：static/rules.json（由 export_rules.py 生成，不依赖 Flask 运行）
"""
import os
import json

def _morph_str(rule):
    m = rule.get("morph") or rule.get("morph_group", [None])[0]
    if not m:
        return "—"
    if isinstance(m, (list, tuple)) and len(m) >= 3:
        return f"{m[0]}/{m[1]}/{m[2]}"
    if isinstance(m, (list, tuple)) and len(m) > 0:
        return "/".join(str(x) for x in m)
    return str(m)

def export_rules_txt():
    """从 static/rules.json 读取并导出为易读的 TXT"""
    json_path = os.path.join(os.path.dirname(__file__), "static", "rules.json")
    if not os.path.exists(json_path):
        print(f"未找到 {json_path}，请先运行: python3 export_rules.py")
        return
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rules_85 = data.get("rules_85", [])
    rules_80 = data.get("rules_80", [])

    lines = []
    lines.append("=" * 80)
    lines.append("AI 类型库（条件1、条件2）— 由 AI 根据数据自动生成，与以往一致")
    lines.append("=" * 80)
    lines.append("")

    lines.append("-" * 80)
    lines.append("条件1：(上+走)或(下+走)比例>85%，总场次>6，差值>3")
    lines.append(f"共 {len(rules_85)} 条规则")
    lines.append("-" * 80)
    lines.append("")

    for i, rule in enumerate(rules_85, 1):
        morph_str = _morph_str(rule)
        lines.append(f"规则 {i}:")
        lines.append(f"  形态: {morph_str}")
        lines.append(f"  特征: {rule.get('feature', '')}")
        lines.append(f"  (上+走)比例: {rule.get('shang_zou_ratio', 0):.2f}%")
        lines.append(f"  (下+走)比例: {rule.get('xia_zou_ratio', 0):.2f}%")
        lines.append(f"  总场次: {rule.get('n_total', 0)}")
        lines.append(f"  统计: 上{rule.get('shang', 0)} 下{rule.get('xia', 0)} 走{rule.get('zou', 0)}")
        lines.append("")

    lines.append("-" * 80)
    lines.append("条件2：上/走/下任一比例>80%，总场次>4")
    lines.append(f"共 {len(rules_80)} 条规则")
    lines.append("-" * 80)
    lines.append("")

    for i, rule in enumerate(rules_80, 1):
        morph_str = _morph_str(rule)
        lines.append(f"规则 {i}:")
        lines.append(f"  形态: {morph_str}")
        lines.append(f"  特征: {rule.get('feature', '')}")
        lines.append(f"  上比例: {rule.get('shang_ratio', 0):.2f}%")
        lines.append(f"  走比例: {rule.get('zou_ratio', 0):.2f}%")
        lines.append(f"  下比例: {rule.get('xia_ratio', 0):.2f}%")
        lines.append(f"  总场次: {rule.get('n_total', 0)}")
        lines.append(f"  统计: 上{rule.get('shang', 0)} 下{rule.get('xia', 0)} 走{rule.get('zou', 0)}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("说明: 本规则库由 AI 根据条件1、条件2 从数据自动生成（与以往一致）")
    lines.append(f"条件1规则数: {len(rules_85)}")
    lines.append(f"条件2规则数: {len(rules_80)}")
    lines.append(f"总规则数: {len(rules_85) + len(rules_80)}")
    lines.append("=" * 80)

    output_file = os.path.join(os.path.dirname(__file__), "AI类型库_条件1条件2.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"已导出可读 TXT 到: {output_file}")
    print(f"  条件1规则数: {len(rules_85)}")
    print(f"  条件2规则数: {len(rules_80)}")
    print(f"  总规则数: {len(rules_85) + len(rules_80)}")

    morphs_count = {}
    for rule in rules_85 + rules_80:
        morph_str = _morph_str(rule)
        morphs_count[morph_str] = morphs_count.get(morph_str, 0) + 1
    print("\n各形态规则统计:")
    for morph_str in sorted(morphs_count.keys()):
        print(f"  {morph_str}: {morphs_count[morph_str]} 条")


if __name__ == "__main__":
    export_rules_txt()
