#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出手工规则类型库为 JSON，供前端快速匹配使用。

来源：
- 规则：docs/规则.xlsx
- 数据：docs/20252026欧洲FB.xlsx
"""

import os
import json

from manual_types import build_manual_types


def export_manual_types() -> None:
    data = build_manual_types()
    os.makedirs("static", exist_ok=True)
    output_file = os.path.join("static", "manual_types.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 人类可读的 TXT 结果（便于检查）
    txt_lines = []
    txt_lines.append("=" * 80)
    txt_lines.append("手工类型库结果（严格按 docs/规则.xlsx 条件，AI 重新筛选验证）")
    txt_lines.append("数据来源: docs/20252026欧洲FB.xlsx，按场次去重统计")
    txt_lines.append("=" * 80)
    txt_lines.append("")
    meta = data.get("meta", {})
    txt_lines.append(f"类型总数: {meta.get('total_types', 0)}")
    txt_lines.append(f"AI 与人工统计不一致条数: {meta.get('inconsistent_manual_vs_ai', 0)}")
    txt_lines.append("")
    txt_lines.append("-" * 80)
    txt_lines.append("各类型明细（上/走/下场次）")
    txt_lines.append("-" * 80)
    for t in data.get("types", []):
        morph_str = "/".join(t.get("morph", []))
        txt_lines.append("")
        txt_lines.append(f"【{t.get('id')}】形态: {morph_str}  分组: {t.get('df_group')}")
        txt_lines.append(f"  特征: {t.get('feature_text', '')}")
        txt_lines.append(f"  预测: {t.get('prediction', '')}")
        s = t.get("stats", {})
        m = t.get("manual_stats", {})
        txt_lines.append(f"  AI统计  - 总场次: {s.get('n_total')}  上: {s.get('shang')}  走: {s.get('zou')}  下: {s.get('xia')}")
        txt_lines.append(f"  人工统计 - 上: {m.get('shang')}  走: {m.get('zou')}  下: {m.get('xia')}")
        d = t.get("diff", {})
        if d.get("shang") or d.get("zou") or d.get("xia"):
            txt_lines.append(f"  ※ 与人工不一致: 上差{d.get('shang')} 走差{d.get('zou')} 下差{d.get('xia')}")
    txt_lines.append("")
    txt_lines.append("=" * 80)
    txt_lines.append("导出完成")
    txt_lines.append("=" * 80)
    txt_file = "手工类型库结果.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines))
    print(f"已导出可读 TXT 到: {txt_file}")

    print(f"已导出手工类型库到: {output_file}")
    print(f"  类型总数: {data['meta']['total_types']}")
    print(f"  AI 统计与人工统计不一致条数: {data['meta']['inconsistent_manual_vs_ai']}")

    # 简单打印几条差异较大的规则，便于人工复核
    diffs = [
        t
        for t in data["types"]
        if t["diff"]["shang"] or t["diff"]["zou"] or t["diff"]["xia"]
    ]
    if diffs:
        print(f"  其中存在差异的规则示例（最多 10 条）：")
        for t in diffs[:10]:
            print(
                f"    行 {t['row_index']} [{t['df_group']} {t['side']}] "
                f"特征: {t['feature_text']} "
                f"AI(上{t['stats']['shang']} 下{t['stats']['xia']} 走{t['stats']['zou']}) vs "
                f"人工(上{t['manual_stats']['shang']} 下{t['manual_stats']['xia']} 走{t['manual_stats']['zou']})"
            )


if __name__ == "__main__":
    export_manual_types()

