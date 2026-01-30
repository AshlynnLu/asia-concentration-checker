#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成主/0/0和客/0/0形态下的集中度汇总（两种计算方式）
格式与集中度按形态汇总.txt相同
"""
import sys
sys.path.insert(0, '/Users/sorari/Desktop/apps/ly')
from analyze_asia_concentration import load_xlsx, filter_rows, RED_CONDITIONS, _no_duplicate_col
from itertools import combinations
from collections import Counter

def get_matching_rows(rows, morph, cond_combo):
    """根据条件组合，返回匹配的比赛行（原始数据行）。"""
    if not _no_duplicate_col(cond_combo):
        return []
    kw = {c[1]: c[2] for c in cond_combo}
    return filter_rows(rows, morph, **kw)

def generate_summary():
    rows = load_xlsx('docs/20252026欧洲FB.xlsx')
    
    # 只分析主/0/0和客/0/0
    target_morphs = [('主', '0', '0'), ('客', '0', '0')]
    
    # 统计总场次
    total_main00 = len([r for r in rows if (r['B'], r['D'], r['F']) == ('主', '0', '0')])
    total_ke00 = len([r for r in rows if (r['B'], r['D'], r['F']) == ('客', '0', '0')])
    
    output_lines = []
    output_lines.append("# 主/0/0 和 客/0/0 形态下的高集中度数据特征")
    output_lines.append("")
    
    # 第一部分：除去走盘的，集中度≥85%
    output_lines.append("# 一、除去走盘的，集中度≥85%（总场次≥6）")
    output_lines.append("# 集中度 = 主要结果/(上+下)，符合条件样本数 = 上+下")
    output_lines.append("")
    
    results_90 = []
    
    for morph in target_morphs:
        morph_label = f"{morph[0]}/{morph[1]}/{morph[2]}"
        total_morph = len([r for r in rows if (r['B'], r['D'], r['F']) == morph])
        
        # 枚举所有条件组合（1-3列）
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                
                matched = get_matching_rows(rows, morph, cond_combo)
                if not matched:
                    continue
                
                # 计算集中度（不含走）
                c = Counter(r['U'] for r in matched)
                shang, xia, zou = c.get('上', 0), c.get('下', 0), c.get('走', 0)
                n_eff = shang + xia
                if n_eff == 0:
                    continue
                
                main_val = max(shang, xia)
                conc_no_zou = (main_val / n_eff * 100) if n_eff > 0 else 0
                
                # 只保留集中度≥85%且总场次≥6，且上/下/走至少有一项≥5
                n_total = len(matched)
                at_least_5 = shang >= 5 or xia >= 5 or zou >= 5
                if conc_no_zou >= 85 and n_total >= 6 and at_least_5:
                    feat = '，且'.join([c[0] for c in cond_combo])
                    pct = round(n_total / total_morph * 100, 1) if total_morph > 0 else 0
                    
                    results_90.append({
                        '类型': morph_label,
                        '特征': feat,
                        '集中度': conc_no_zou,
                        '符合条件样本数': n_eff,
                        '总场次': n_total,
                        '占比': pct,
                        '上': shang,
                        '下': xia,
                        '走': zou,
                    })
    
    # 去重：同一形态、同一场次分布只保留一条（保留集中度最高的）
    seen_90 = {}
    for r in results_90:
        key = (r['类型'], r['总场次'], r['上'], r['下'], r['走'])
        if key not in seen_90 or r['集中度'] > seen_90[key]['集中度']:
            seen_90[key] = r
    
    results_90_unique = list(seen_90.values())
    results_90_unique.sort(key=lambda x: (-x['集中度'], -x['符合条件样本数'], x['类型']))
    
    for r in results_90_unique:
        output_lines.append(
            f"类型：{r['类型']}；特征：{r['特征']}；集中度 {r['集中度']:.2f}%；"
            f"符合条件样本数 {r['符合条件样本数']}；总场次 {r['总场次']}（占比{r['占比']}%）；"
            f"上{r['上']}下{r['下']}走{r['走']}"
        )
    
    output_lines.append("")
    output_lines.append("")
    
    # 第二部分：算上走盘的，集中度≥80%
    output_lines.append("# 二、算上走盘的，集中度≥80%（总场次≥5）")
    output_lines.append("# 集中度 = 主要结果/(上+下+走)，符合条件样本数 = 上+下+走")
    output_lines.append("")
    
    results_80 = []
    
    for morph in target_morphs:
        morph_label = f"{morph[0]}/{morph[1]}/{morph[2]}"
        total_morph = len([r for r in rows if (r['B'], r['D'], r['F']) == morph])
        
        # 枚举所有条件组合（1-3列）
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                
                matched = get_matching_rows(rows, morph, cond_combo)
                if not matched:
                    continue
                
                # 计算集中度（含走）
                c = Counter(r['U'] for r in matched)
                shang, xia, zou = c.get('上', 0), c.get('下', 0), c.get('走', 0)
                n_total = len(matched)
                n_eff = shang + xia
                
                if n_total == 0:
                    continue
                
                main_val = max(shang, xia)
                conc_with_zou = (main_val / n_total * 100) if n_total > 0 else 0
                
                # 只保留集中度≥80%且总场次≥5（第二种计算方式不要求上/下/走≥5）
                if conc_with_zou >= 80 and n_total >= 5:
                    feat = '，且'.join([c[0] for c in cond_combo])
                    pct = round(n_total / total_morph * 100, 1) if total_morph > 0 else 0
                    
                    results_80.append({
                        '类型': morph_label,
                        '特征': feat,
                        '集中度': conc_with_zou,
                        '符合条件样本数': n_total,
                        '总场次': n_total,
                        '占比': pct,
                        '上': shang,
                        '下': xia,
                        '走': zou,
                    })
    
    # 去重
    seen_80 = {}
    for r in results_80:
        key = (r['类型'], r['总场次'], r['上'], r['下'], r['走'])
        if key not in seen_80 or r['集中度'] > seen_80[key]['集中度']:
            seen_80[key] = r
    
    results_80_unique = list(seen_80.values())
    results_80_unique.sort(key=lambda x: (-x['集中度'], -x['符合条件样本数'], x['类型']))
    
    for r in results_80_unique:
        output_lines.append(
            f"类型：{r['类型']}；特征：{r['特征']}；集中度 {r['集中度']:.2f}%；"
            f"符合条件样本数 {r['符合条件样本数']}；总场次 {r['总场次']}（占比{r['占比']}%）；"
            f"上{r['上']}下{r['下']}走{r['走']}"
        )
    
    # 写入文件
    output_file = '主客00集中度汇总.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"已生成: {output_file}")
    print(f"第一部分（不含走，集中度≥85%，总场次≥6）: {len(results_90_unique)} 条规则")
    print(f"第二部分（含走，集中度≥80%，总场次≥5）: {len(results_80_unique)} 条规则")

if __name__ == '__main__':
    generate_summary()
