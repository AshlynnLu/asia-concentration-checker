#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算主/0/0和客/0/0形态下的场次覆盖统计：
1. 除去走盘的，集中度≥90%的比赛场次有多少
2. 算上走盘，集中度≥80%的比赛场次有多少
重叠的场次只按1计算（去重）
"""
import sys
sys.path.insert(0, '/Users/sorari/Desktop/apps/ly')
from analyze_asia_concentration import load_xlsx, filter_rows, RED_CONDITIONS, _no_duplicate_col
from itertools import combinations
from collections import defaultdict, Counter

def get_matching_rows(rows, morph, cond_combo):
    """根据条件组合，返回匹配的比赛行（原始数据行）。"""
    if not _no_duplicate_col(cond_combo):
        return []
    kw = {c[1]: c[2] for c in cond_combo}
    return filter_rows(rows, morph, **kw)

def calc_stats():
    rows = load_xlsx('20252026欧洲FB.xlsx')
    
    # 只分析主/0/0和客/0/0
    target_morphs = [('主', '0', '0'), ('客', '0', '0')]
    
    # 为每场比赛创建唯一标识（使用行号索引，因为同一场比赛可能有多行数据）
    # 但我们需要用实际数据字段来标识：B, D, F, S(强分), T(弱分), U(结果)
    def get_game_id(r):
        return (r['B'], r['D'], r['F'], r.get('S'), r.get('T'))
    
    # 收集所有符合条件的规则匹配的比赛
    games_no_zou_90 = set()  # 不含走，集中度≥90%的比赛
    games_with_zou_80 = set()  # 含走，集中度≥80%的比赛
    
    print("正在分析所有规则...")
    
    for morph in target_morphs:
        morph_label = f"{morph[0]}/{morph[1]}/{morph[2]}"
        print(f"  处理 {morph_label}...")
        
        # 枚举所有条件组合（1-3列）
        rule_count = 0
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                
                matched = get_matching_rows(rows, morph, cond_combo)
                if not matched:
                    continue
                
                # 计算集中度
                c = Counter(r['U'] for r in matched)
                shang, xia, zou = c.get('上', 0), c.get('下', 0), c.get('走', 0)
                n_eff = shang + xia
                if n_eff == 0:
                    continue
                
                main_val = max(shang, xia)
                conc_no_zou = (main_val / n_eff * 100) if n_eff > 0 else 0
                conc_with_zou = (main_val / len(matched) * 100) if len(matched) > 0 else 0
                
                # 如果规则满足条件，记录所有匹配的比赛
                n_total = len(matched)
                # 第一部分：集中度≥85%，总场次≥6
                if conc_no_zou >= 85 and n_total >= 6:
                    for r in matched:
                        games_no_zou_90.add(get_game_id(r))
                
                # 第二部分：集中度≥80%，总场次≥5
                if conc_with_zou >= 80 and n_total >= 5:
                    for r in matched:
                        games_with_zou_80.add(get_game_id(r))
                
                rule_count += 1
        
        print(f"    处理了 {rule_count} 个规则组合")
    
    # 统计结果
    print("\n" + "=" * 60)
    print("主/0/0 和 客/0/0 形态下的场次覆盖统计（去重后）")
    print("条件：第一部分 集中度≥85%，总场次≥6；第二部分 集中度≥80%，总场次≥5")
    print("=" * 60)
    
    # 找出这些比赛的实际数据
    all_target_rows = [r for r in rows if (r['B'], r['D'], r['F']) in target_morphs]
    
    games_90_list = []
    games_80_list = []
    
    seen_90 = set()
    seen_80 = set()
    
    for r in all_target_rows:
        gid = get_game_id(r)
        if gid in games_no_zou_90 and gid not in seen_90:
            games_90_list.append(r)
            seen_90.add(gid)
        if gid in games_with_zou_80 and gid not in seen_80:
            games_80_list.append(r)
            seen_80.add(gid)
    
    # 统计分布
    c90 = Counter(r['U'] for r in games_90_list)
    c80 = Counter(r['U'] for r in games_80_list)
    
    shang90, xia90, zou90 = c90.get('上', 0), c90.get('下', 0), c90.get('走', 0)
    shang80, xia80, zou80 = c80.get('上', 0), c80.get('下', 0), c80.get('走', 0)
    
    n_eff_90 = shang90 + xia90
    n_total_90 = len(games_90_list)
    n_eff_80 = shang80 + xia80
    n_total_80 = len(games_80_list)
    
    main_val_90 = max(shang90, xia90)
    main_val_80 = max(shang80, xia80)
    
    conc_90_no_zou = (main_val_90 / n_eff_90 * 100) if n_eff_90 > 0 else 0
    conc_80_with_zou = (main_val_80 / n_total_80 * 100) if n_total_80 > 0 else 0
    
    print(f"\n1. 除去走盘的，集中度≥85%（总场次≥6）的比赛场次数（去重）: {n_total_90}")
    print(f"   这些场次的分布：上 {shang90}, 下 {xia90}, 走 {zou90}")
    print(f"   说明：这些场次至少被一个'不含走集中度≥85%且总场次≥6'的规则匹配")
    
    print(f"\n2. 算上走盘，集中度≥80%（总场次≥5）的比赛场次数（去重）: {n_total_80}")
    print(f"   这些场次的分布：上 {shang80}, 下 {xia80}, 走 {zou80}")
    print(f"   说明：这些场次至少被一个'含走集中度≥80%且总场次≥5'的规则匹配")
    
    # 统计总场次
    total_main00 = len([r for r in rows if (r['B'], r['D'], r['F']) == ('主', '0', '0')])
    total_ke00 = len([r for r in rows if (r['B'], r['D'], r['F']) == ('客', '0', '0')])
    total_all = total_main00 + total_ke00
    
    print(f"\n总场次统计：")
    print(f"  主/0/0: {total_main00} 场")
    print(f"  客/0/0: {total_ke00} 场")
    print(f"  合计: {total_all} 场")
    
    print(f"\n覆盖率：")
    print(f"  集中度≥85%（不含走，总场次≥6）: {n_total_90}/{total_all} = {n_total_90/total_all*100:.1f}%")
    print(f"  集中度≥80%（含走，总场次≥5）: {n_total_80}/{total_all} = {n_total_80/total_all*100:.1f}%")
    
    # 输出详细比赛信息到txt文件
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("主/0/0 和 客/0/0 形态下的高集中度场次详情")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    output_lines.append("一、除去走盘的，集中度≥90%的比赛场次（去重后共 {} 场）".format(n_total_90))
    output_lines.append("-" * 80)
    output_lines.append("格式：类型 | G | I | K | N | P | Q | R | 强分 | 弱分 | 结果")
    output_lines.append("-" * 80)
    
    # 按类型和结果排序
    games_90_list_sorted = sorted(games_90_list, key=lambda x: (x['B'], x['U'], x.get('S', 0), x.get('T', 0)))
    
    for i, r in enumerate(games_90_list_sorted, 1):
        def fmt_val(v):
            if v is None or v == '':
                return 'N/A'
            if isinstance(v, (int, float)):
                return f"{v:.2f}" if abs(v) < 100 else f"{v:.1f}"
            return str(v)
        
        g_val = fmt_val(r.get('G'))
        i_val = fmt_val(r.get('I'))
        k_val = fmt_val(r.get('K'))
        n_val = fmt_val(r.get('N'))
        p_val = fmt_val(r.get('P'))
        q_val = fmt_val(r.get('Q'))
        r_val = fmt_val(r.get('R'))
        s_val = r.get('S', 'N/A')
        t_val = r.get('T', 'N/A')
        
        output_lines.append(
            f"{i:2d}. {r['B']}/{r['D']}/{r['F']} | "
            f"G:{g_val:>8} | I:{i_val:>8} | K:{k_val:>8} | N:{n_val:>8} | "
            f"P:{p_val:>8} | Q:{q_val:>8} | R:{r_val:>8} | "
            f"强分:{s_val:>4} | 弱分:{t_val:>4} | 结果:{r['U']}"
        )
    
    output_lines.append("")
    output_lines.append("")
    output_lines.append("二、算上走盘，集中度≥80%的比赛场次（去重后共 {} 场）".format(n_total_80))
    output_lines.append("-" * 80)
    output_lines.append("格式：类型 | G | I | K | N | P | Q | R | 强分 | 弱分 | 结果")
    output_lines.append("-" * 80)
    
    games_80_list_sorted = sorted(games_80_list, key=lambda x: (x['B'], x['U'], x.get('S', 0), x.get('T', 0)))
    
    for i, r in enumerate(games_80_list_sorted, 1):
        def fmt_val(v):
            if v is None or v == '':
                return 'N/A'
            if isinstance(v, (int, float)):
                return f"{v:.2f}" if abs(v) < 100 else f"{v:.1f}"
            return str(v)
        
        g_val = fmt_val(r.get('G'))
        i_val = fmt_val(r.get('I'))
        k_val = fmt_val(r.get('K'))
        n_val = fmt_val(r.get('N'))
        p_val = fmt_val(r.get('P'))
        q_val = fmt_val(r.get('Q'))
        r_val = fmt_val(r.get('R'))
        s_val = r.get('S', 'N/A')
        t_val = r.get('T', 'N/A')
        
        output_lines.append(
            f"{i:2d}. {r['B']}/{r['D']}/{r['F']} | "
            f"G:{g_val:>8} | I:{i_val:>8} | K:{k_val:>8} | N:{n_val:>8} | "
            f"P:{p_val:>8} | Q:{q_val:>8} | R:{r_val:>8} | "
            f"强分:{s_val:>4} | 弱分:{t_val:>4} | 结果:{r['U']}"
        )
    
    output_lines.append("")
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("统计汇总")
    output_lines.append("=" * 80)
    output_lines.append(f"总场次：主/0/0 {total_main00} 场，客/0/0 {total_ke00} 场，合计 {total_all} 场")
    output_lines.append(f"集中度≥90%（不含走）: {n_total_90} 场，覆盖率 {n_total_90/total_all*100:.1f}%")
    output_lines.append(f"集中度≥80%（含走）: {n_total_80} 场，覆盖率 {n_total_80/total_all*100:.1f}%")
    
    # 写入文件
    output_file = '主客00高集中度场次详情.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n详细场次信息已保存到: {output_file}")

if __name__ == '__main__':
    calc_stats()
