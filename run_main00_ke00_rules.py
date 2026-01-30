#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只看主/0/0 和 客/0/0，计算并输出：
1. 除去走盘的，集中度≥85%（总场次≥6），且上/下/走至少有一项≥5
2. 算上走盘的，集中度≥80%（总场次≥5）（不要求上/下/走至少有一项≥5）
统计按场次去重。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collections import Counter
from itertools import combinations

from analyze_asia_concentration import (
    load_xlsx,
    filter_rows,
    unique_by_game,
    outcome_set,
    RED_CONDITIONS,
    _no_duplicate_col,
)

DATA_PATH = 'docs/20252026欧洲FB.xlsx'
TARGET_MORPHS = [('主', '0', '0'), ('客', '0', '0')]


def compute_rules(rows):
    """只针对主00、客00，计算条件1和条件2的规则。
    按匹配结果集去重：同一批场次（同一 outcome_set）只保留条件条数最少的一条，
    避免「北京人、海淀人、朝阳人」式包含重复。
    """
    # key = (morph, outcome_set), value = (n_cond, rec)；同结果集只保留条件最少
    seen_85 = {}
    seen_80 = {}
    # 有规则的比赛（任一条或多条）去重计数：同一场只记1次
    all_matched_game_keys = set()

    for morph in TARGET_MORPHS:
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                kw = {c[1]: c[2] for c in cond_combo}
                matched = filter_rows(rows, morph, **kw)
                if not matched:
                    continue
                matched_unique = unique_by_game(matched)
                outcome = outcome_set(matched_unique)
                c = Counter(r['U'] for r in matched_unique)
                shang, xia, zou = c.get('上', 0), c.get('下', 0), c.get('走', 0)
                n_eff = shang + xia
                n_total = len(matched_unique)
                if n_eff == 0:
                    continue
                main_val = max(shang, xia)
                conc_no_zou = (main_val / n_eff * 100) if n_eff > 0 else 0
                conc_with_zou = (main_val / n_total * 100) if n_total > 0 else 0
                feat = '，且'.join([c[0] for c in cond_combo])
                label = f"{morph[0]}/{morph[1]}/{morph[2]}"
                rec = {
                    '类型': label,
                    '特征': feat,
                    '总场次': n_total,
                    '上': shang, '下': xia, '走': zou,
                    '符合条件样本数': n_eff,
                    '集中度(不含走)': round(conc_no_zou, 2),
                    '集中度(含走)': round(conc_with_zou, 2),
                }
                key = (morph, outcome)
                at_least_5 = shang >= 5 or xia >= 5 or zou >= 5
                if conc_no_zou >= 85 and n_total >= 6 and at_least_5:
                    if key not in seen_85 or n_cond < seen_85[key][0]:
                        seen_85[key] = (n_cond, rec)
                    all_matched_game_keys.update(outcome)
                if conc_with_zou >= 80 and n_total >= 5:
                    if key not in seen_80 or n_cond < seen_80[key][0]:
                        seen_80[key] = (n_cond, rec)
                    all_matched_game_keys.update(outcome)

    rules_85 = [rec for _, rec in seen_85.values()]
    rules_80 = [rec for _, rec in seen_80.values()]
    return rules_85, rules_80, all_matched_game_keys


def main():
    if not os.path.exists(DATA_PATH):
        print(f"数据文件不存在: {DATA_PATH}")
        sys.exit(1)
    rows = load_xlsx(DATA_PATH)
    base = [r for r in rows if (r['B'], r['D'], r['F']) in TARGET_MORPHS]
    base_u = len(unique_by_game(base))
    print(f"数据: {DATA_PATH}")
    print(f"主/0/0 + 客/0/0 总行数: {len(base)}，按场次去重: {base_u}")
    print()

    rules_85, rules_80, all_matched_game_keys = compute_rules(rows)

    # 有规则的比赛（一条或多条）去重：同一场只记1次
    n_any = len(all_matched_game_keys)
    print("=" * 70)
    print("有规则的比赛（任一条或多条符合，去重）")
    print("=" * 70)
    print(f"  {n_any} 场 / {base_u} 场（主/0/0 + 客/0/0 总场次）")
    print()

    # 条件1：除去走盘，集中度≥85%，总场次≥6
    rules_85.sort(key=lambda x: (-x['集中度(不含走)'], -x['符合条件样本数'], x['类型'], x['特征']))
    print("=" * 70)
    print("1. 除去走盘的，集中度≥85%（总场次≥6）")
    print("=" * 70)
    print(f"规则数: {len(rules_85)}")
    for r in rules_85:
        print(f"  {r['类型']}；{r['特征']}；集中度 {r['集中度(不含走)']}%；"
              f"样本数 {r['符合条件样本数']}；总场次 {r['总场次']}；上{r['上']}下{r['下']}走{r['走']}")
    print()

    # 条件2：算上走盘，集中度≥80%，总场次≥5
    rules_80.sort(key=lambda x: (-x['集中度(含走)'], -x['总场次'], x['类型'], x['特征']))
    print("=" * 70)
    print("2. 算上走盘的，集中度≥80%（总场次≥5）")
    print("=" * 70)
    print(f"规则数: {len(rules_80)}")
    for r in rules_80:
        print(f"  {r['类型']}；{r['特征']}；集中度(含走) {r['集中度(含走)']}%；"
              f"总场次 {r['总场次']}；上{r['上']}下{r['下']}走{r['走']}")
    print()
    print("说明: 统计按场次去重；同一批匹配场次只保留条件条数最少的一条（避免 G/I/K 等包含重复）。")


if __name__ == '__main__':
    main()
