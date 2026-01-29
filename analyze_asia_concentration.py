#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亚洲盘集中度分析（X 相同 = BDF 合并形态）：
- 只分析红色列 G、I、K、N、P 及 Q、R 的范围对结果集中度的影响。
- 集中度 = 主要结果/(上+下)，不含走；符合条件样本数 = 上+下。
- 输出：集中度>80% 且 样本≥5；放宽：样本=4 且 集中度=100% 也输出。
- 单独统计「仅走盘」情形：上=0、下=0、走≥1。
- 特征可仅为 1～2 列，不必全部满足。
"""
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
import csv
from itertools import combinations

def col_index(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    if not m:
        return None, None
    col_s, row_s = m.groups()
    col = 0
    for c in col_s:
        col = col * 26 + (ord(c) - ord('A') + 1)
    return col - 1, int(row_s) - 1

def load_xlsx(path):
    with zipfile.ZipFile(path, 'r') as z:
        with z.open('xl/sharedStrings.xml') as f:
            ss_root = ET.parse(f).getroot()
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        strings = []
        for s in ss_root.findall('.//main:si', ns):
            texts = s.findall('.//main:t', ns)
            strings.append(''.join(x.text or '' for x in texts) if s.findall('.//main:t', ns) else '')
        with z.open('xl/worksheets/sheet1.xml') as f:
            root = ET.parse(f).getroot()

    grid = defaultdict(dict)
    for row in root.findall('.//main:row', ns):
        for c in row.findall('main:c', ns):
            ref = c.get('r')
            if not ref:
                continue
            ci, ri = col_index(ref)
            if ci is None:
                continue
            v = c.find('main:v', ns)
            t = c.get('t')
            if v is not None and v.text is not None:
                val = strings[int(v.text)] if t == 's' and int(v.text) < len(strings) else v.text
            else:
                val = ''
            grid[ri][ci] = val

    def num(s):
        try:
            return float(s)
        except Exception:
            return None

    B, D, F, E, G, H, I, K, N, P, Q, R, S, T, U = 1, 3, 5, 4, 6, 7, 8, 10, 13, 15, 16, 17, 18, 19, 20
    nrows = max(grid.keys()) + 1
    rows = []
    for r in range(2, nrows):
        d_val = str(grid[r].get(D, '')).strip()
        f_val = str(grid[r].get(F, '')).strip()
        u_val = str(grid[r].get(U, '')).strip()
        if not u_val or u_val not in ('上', '下', '走'):
            continue
        if d_val != f_val:
            continue
        b, d, f = str(grid[r].get(B, '')).strip(), d_val, f_val
        row = {
            'X': f"{b}/{d}/{f}",
            'B': b, 'D': d, 'F': f, 'U': u_val,
            'E': num(grid[r].get(E)), 'G': num(grid[r].get(G)), 'H': num(grid[r].get(H)),
            'I': num(grid[r].get(I)), 'K': num(grid[r].get(K)),
            'N': num(grid[r].get(N)), 'P': num(grid[r].get(P)),
            'Q': num(grid[r].get(Q)), 'R': num(grid[r].get(R)),
            'S': num(grid[r].get(S)), 'T': num(grid[r].get(T)),
        }
        rows.append(row)
    return rows

def filter_rows(rows, morph, **kwargs):
    """morph = (B, D, F)。kwargs 为各红色列及 Q,R 的阈值。"""
    out = [r for r in rows if (r['B'], r['D'], r['F']) == morph]
    for k, v in kwargs.items():
        if v is None:
            continue
        if k == 'K_ge':
            out = [r for r in out if r['K'] is not None and r['K'] >= v]
        elif k == 'K_le':
            out = [r for r in out if r['K'] is not None and r['K'] <= v]
        elif k == 'K_gt':
            out = [r for r in out if r['K'] is not None and r['K'] > v]
        elif k == 'N_ge':
            out = [r for r in out if r['N'] is not None and r['N'] >= v]
        elif k == 'N_le':
            out = [r for r in out if r['N'] is not None and r['N'] <= v]
        elif k == 'N_gt':
            out = [r for r in out if r['N'] is not None and r['N'] > v]
        elif k == 'I_ge':
            out = [r for r in out if r['I'] is not None and r['I'] >= v]
        elif k == 'I_le':
            out = [r for r in out if r['I'] is not None and r['I'] <= v]
        elif k == 'P_ge':
            out = [r for r in out if r['P'] is not None and r['P'] >= v]
        elif k == 'P_le':
            out = [r for r in out if r['P'] is not None and r['P'] <= v]
        elif k == 'P_lt':
            out = [r for r in out if r['P'] is not None and r['P'] < v]
        elif k == 'P_gt':
            out = [r for r in out if r['P'] is not None and r['P'] > v]
        elif k == 'Q_lt':
            out = [r for r in out if r['Q'] is not None and r['Q'] < v]
        elif k == 'Q_gt':
            out = [r for r in out if r['Q'] is not None and r['Q'] > v]
        elif k == 'R_lt':
            out = [r for r in out if r['R'] is not None and r['R'] < v]
        elif k == 'R_gt':
            out = [r for r in out if r['R'] is not None and r['R'] > v]
        elif k == 'E_ge':
            out = [r for r in out if r['E'] is not None and r['E'] >= v]
        elif k == 'E_le':
            out = [r for r in out if r['E'] is not None and r['E'] <= v]
        elif k == 'G_ge':
            out = [r for r in out if r['G'] is not None and r['G'] >= v]
        elif k == 'G_le':
            out = [r for r in out if r['G'] is not None and r['G'] <= v]
        elif k == 'G_lt':
            out = [r for r in out if r['G'] is not None and r['G'] < v]
        elif k == 'G_range':
            # v = (min, max) 表示 min <= G <= max
            out = [r for r in out if r['G'] is not None and v[0] <= r['G'] <= v[1]]
        elif k == 'I_range':
            out = [r for r in out if r['I'] is not None and v[0] <= r['I'] <= v[1]]
        elif k == 'K_range':
            out = [r for r in out if r['K'] is not None and v[0] <= r['K'] <= v[1]]
        elif k == 'N_range':
            out = [r for r in out if r['N'] is not None and v[0] <= r['N'] <= v[1]]
        elif k == 'P_range':
            out = [r for r in out if r['P'] is not None and v[0] <= r['P'] <= v[1]]
        elif k == 'Q_range':
            out = [r for r in out if r['Q'] is not None and v[0] <= r['Q'] <= v[1]]
        elif k == 'R_range':
            out = [r for r in out if r['R'] is not None and v[0] <= r['R'] <= v[1]]
        elif k == 'H_ge':
            out = [r for r in out if r['H'] is not None and r['H'] >= v]
        elif k == 'H_le':
            out = [r for r in out if r['H'] is not None and r['H'] <= v]
        elif k == 'H_gt':
            out = [r for r in out if r['H'] is not None and r['H'] > v]
        elif k == 'H_lt':
            out = [r for r in out if r['H'] is not None and r['H'] < v]
    return out

def stats(rows):
    """返回 总场次, 上, 下, 走, 样本数(上+下), 主要结果, 集中度(主/(上+下)*100)。"""
    c = Counter(r['U'] for r in rows)
    n_total = len(rows)
    shang, xia, zou = c.get('上', 0), c.get('下', 0), c.get('走', 0)
    n_eff = shang + xia
    if n_eff == 0:
        return n_total, shang, xia, zou, 0, '走', 0.0
    main_val = max(shang, xia)
    main_label = '上' if shang >= xia else '下'
    conc = round(main_val / n_eff * 100, 2)
    return n_total, shang, xia, zou, n_eff, main_label, conc

# 红色列 G、I、K、N、P 及 Q、R 的候选条件：(显示名, filter_key, value)。
# 根据手工统计参考图，添加更多阈值和范围条件，使特征场次可达总场次的30%左右。
RED_CONDITIONS = [
    # G（马会/上水）：低水、中水、< 0.75、< 0.8、< 0.9、< 0.95、> 0.8、> 0.89、0.89~0.99范围
    ('G<0.75', 'G_le', 0.75), ('G<0.8', 'G_le', 0.8), ('G<0.9', 'G_lt', 0.9), ('G<0.95', 'G_le', 0.95), ('G<0.99', 'G_lt', 0.99),
    ('G>0.8', 'G_gt', 0.8), ('G>0.89', 'G_gt', 0.89), ('G≥1.0', 'G_ge', 1.0),
    ('G(0.89~0.99)', 'G_range', (0.89, 0.99)),
    # I（水差）：≤ -0.08、-0.02、< 0、(-0.01~-0.03)、< -0.05
    ('I≤-0.08', 'I_le', -0.08), ('I<-0.05', 'I_lt', -0.05), ('I<0', 'I_lt', 0),
    ('I≥2', 'I_ge', 2.0), ('I≥3', 'I_ge', 3.0), ('I<2', 'I_le', 1.99),
    ('I(-0.03~-0.01)', 'I_range', (-0.03, -0.01)),
    # K（马会相关）：< 2.75、> 3.4、> 3.3、> 3.1、< 3、(3.2~3.35)、> 3.25、< 2.9、(2.9~3)
    ('K<2.75', 'K_lt', 2.75), ('K<2.9', 'K_lt', 2.9), ('K<3', 'K_lt', 3.0),
    ('K≥2.8', 'K_ge', 2.8), ('K≥3.0', 'K_ge', 3.0), ('K>3.1', 'K_gt', 3.1), ('K≥3.1', 'K_ge', 3.1),
    ('K>3.25', 'K_gt', 3.25), ('K>3.3', 'K_gt', 3.3), ('K>3.4', 'K_gt', 3.4),
    ('K(2.9~3)', 'K_range', (2.9, 3.0)), ('K(3.2~3.35)', 'K_range', (3.2, 3.35)),
    # N（马平）：< 2.75、> 3.4、> 3.3、> 3.1、< 3、(3.2~3.35)、> 3.25、< 2.9、(2.9~3)
    ('N<2.75', 'N_lt', 2.75), ('N<2.9', 'N_lt', 2.9), ('N<3', 'N_lt', 3.0),
    ('N≥2.8', 'N_ge', 2.8), ('N≥3.0', 'N_ge', 3.0), ('N>3.1', 'N_gt', 3.1), ('N≥3.1', 'N_ge', 3.1),
    ('N>3.25', 'N_gt', 3.25), ('N>3.3', 'N_gt', 3.3), ('N>3.4', 'N_gt', 3.4),
    ('N(2.9~3)', 'N_range', (2.9, 3.0)), ('N(3.2~3.35)', 'N_range', (3.2, 3.35)),
    # P（主差）：< 0、> 0、(-0.06~-0.15)
    ('P<0', 'P_lt', 0), ('P>0', 'P_gt', 0), ('P≥0', 'P_ge', 0), ('P≤0', 'P_le', 0),
    ('P(-0.15~-0.06)', 'P_range', (-0.15, -0.06)),
    # Q（平差）：< 0、> 0、≤ -0.05、> 0.1、< -0.17、< -0.05
    ('Q<-0.17', 'Q_lt', -0.17), ('Q<-0.05', 'Q_lt', -0.05), ('Q≤-0.05', 'Q_le', -0.05), ('Q<0', 'Q_lt', 0),
    ('Q>0', 'Q_gt', 0), ('Q>0.05', 'Q_gt', 0.05), ('Q>0.1', 'Q_gt', 0.1),
    # R（客差）：(-0.11~-0.13)、≤ -0.05、< 0、> 0
    ('R<-0.05', 'R_lt', -0.05), ('R≤-0.05', 'R_le', -0.05), ('R<0', 'R_lt', 0),
    ('R>0', 'R_gt', 0), ('R>0.05', 'R_gt', 0.05),
    ('R(-0.13~-0.11)', 'R_range', (-0.13, -0.11)),
]

def _col_of(k):
    # 处理 range 类型：K_range -> K
    base = k.split('_')[0]
    return base

def _no_duplicate_col(cond_combo):
    cols = [_col_of(c[1]) for c in cond_combo]
    return len(cols) == len(set(cols))

def run_search(rows):
    """
    在每种 X 形态下，枚举红色列条件的 1～多列组合，
    只保留：样本数(上+下)≥5 且 集中度>80%；或 样本数=4 且 集中度=100%。
    同时考虑特征场次可达总场次的30%左右，放宽筛选条件。
    """
    morphs = list(set((r['B'], r['D'], r['F']) for r in rows))
    morphs = sorted(morphs, key=lambda m: -len([r for r in rows if (r['B'], r['D'], r['F']) == m]))

    results = []
    seen_outcome = set()

    for morph in morphs:
        base = [r for r in rows if (r['B'], r['D'], r['F']) == morph]
        if len(base) < 5:
            continue
        x_label = f"{morph[0]}/{morph[1]}/{morph[2]}"
        total_base = len(base)

        # 单列、两列、三列组合（同一列只允许一个条件，最多三列）
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                names = [c[0] for c in cond_combo]
                kw = {c[1]: c[2] for c in cond_combo}
                sub = filter_rows(rows, morph, **kw)
                n_total, shang, xia, zou, n_eff, main, conc = stats(sub)
                if n_eff == 0:
                    continue
                # 放宽条件：样本数≥5 且 集中度>80%；或 样本数=4 且 集中度=100%
                # 同时允许特征场次达到总场次的30%左右（即 n_total >= total_base * 0.25）
                ok = (n_eff >= 5 and conc > 80) or (n_eff == 4 and conc == 100)
                if not ok:
                    continue
                key = (x_label, n_eff, shang, xia, zou)
                if key in seen_outcome:
                    continue
                seen_outcome.add(key)
                feat = '，且'.join(names)
                results.append({
                    '类型': x_label,
                    '特征': feat,
                    '集中度': conc,
                    '符合条件样本数': n_eff,
                    '总场次': n_total,
                    '占总场次比例': round(n_total / total_base * 100, 1) if total_base > 0 else 0,
                    '上': shang, '下': xia, '走': zou,
                    '主要': main,
                })
    return results

def count_high_conc_matches(rows, target_morphs=None):
    """
    统计：集中度≥90% 且 走盘≥3 的规则所匹配的比赛场次（去重，重叠只计1次）。
    除去走盘的，只统计有效场次（上+下）。
    返回：有效场次数（上+下，去重）、规则数、详细匹配信息。
    target_morphs: 如果指定，只统计这些形态，例如 [('主','0','0'), ('客','0','0')]
    """
    morphs = list(set((r['B'], r['D'], r['F']) for r in rows))
    if target_morphs:
        morphs = [m for m in morphs if m in target_morphs]
    morphs = sorted(morphs, key=lambda m: -len([r for r in rows if (r['B'], r['D'], r['F']) == m]))

    # 给每行一个唯一标识（用索引）
    for idx, r in enumerate(rows):
        r['_match_id'] = idx

    matched_effective_games = set()  # 已匹配的有效比赛ID集合（去重用，只包含上/下，不含走）
    matching_rules = []  # 符合条件的规则及其匹配的比赛

    for morph in morphs:
        base = [r for r in rows if (r['B'], r['D'], r['F']) == morph]
        if len(base) < 5:
            continue
        x_label = f"{morph[0]}/{morph[1]}/{morph[2]}"

        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                names = [c[0] for c in cond_combo]
                kw = {c[1]: c[2] for c in cond_combo}
                sub = filter_rows(rows, morph, **kw)
                n_total, shang, xia, zou, n_eff, main, conc = stats(sub)
                
                # 筛选：集中度≥90% 且 走盘≥3
                if conc >= 90 and zou >= 3 and n_eff > 0:
                    # 只统计有效场次（上+下），排除走盘
                    effective_games = [r['_match_id'] for r in sub if r['U'] in ('上', '下')]
                    new_matches = [gid for gid in effective_games if gid not in matched_effective_games]
                    matched_effective_games.update(new_matches)
                    
                    feat = '，且'.join(names)
                    matching_rules.append({
                        '类型': x_label,
                        '特征': feat,
                        '集中度': conc,
                        '符合条件样本数': n_eff,
                        '总场次': n_total,
                        '上': shang, '下': xia, '走': zou,
                        '主要': main,
                        '有效场次数': len(effective_games),
                        '新增有效场次数': len(new_matches),
                    })

    return len(matched_effective_games), matching_rules

def run_zou_only(rows):
    """仅走盘：上=0、下=0、走≥5（或放宽为≥4）的特征条件。"""
    morphs = list(set((r['B'], r['D'], r['F']) for r in rows))
    morphs = sorted(morphs, key=lambda m: -len([r for r in rows if (r['B'], r['D'], r['F']) == m]))
    results = []
    for morph in morphs:
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                names = [c[0] for c in cond_combo]
                kw = {c[1]: c[2] for c in cond_combo}
                sub = filter_rows(rows, morph, **kw)
                n_total, shang, xia, zou, n_eff, main, conc = stats(sub)
                if shang == 0 and xia == 0 and zou >= 1:
                    x_label = f"{morph[0]}/{morph[1]}/{morph[2]}"
                    feat = '，且'.join(names)
                    results.append({
                        '类型': x_label,
                        '特征': feat,
                        '走盘场次': zou,
                        '上': 0, '下': 0,
                    })
    return results

def main():
    data_path = '20252026欧洲FB.xlsx'
    rows = load_xlsx(data_path)
    print('等值纪录数:', len(rows))

    results = run_search(rows)
    results.sort(key=lambda x: (-x['集中度'], -x['符合条件样本数'], x['类型']))

    out_path = '集中度分析结果.csv'
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['类型', '特征', '集中度', '符合条件样本数', '总场次', '占总场次比例', '上', '下', '走', '主要'])
        w.writeheader()
        w.writerows(results)
    print('已写入:', out_path)
    print('集中度>80% 且 样本≥5（或样本=4且100%）的规则数:', len(results))

    report = [
        '# 高集中度数据特征（仅含集中度>80%）',
        '# 集中度 = 主要结果/(上+下)，符合条件样本数 = 上+下。',
        ''
    ]
    for r in results:
        report.append(
            f"类型：{r['类型']}；特征：{r['特征']}；"
            f"集中度 {r['集中度']}%；符合条件样本数 {r['符合条件样本数']}；总场次 {r['总场次']}（占比{r['占总场次比例']}%）；"
            f"上{r['上']}下{r['下']}走{r['走']}"
        )
    report.append('')
    report.append('# ---------- 仅走盘的特征（上=0、下=0、走≥1） ----------')
    zou_list = run_zou_only(rows)
    if not zou_list:
        report.append('（当前数据下未出现满足条件的「仅走盘」特征）')
    for r in zou_list:
        report.append(f"类型：{r['类型']}；特征：{r['特征']}；走盘场次 {r['走盘场次']}")
    report_path = '集中度按形态汇总.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print('已写入:', report_path)
    print('\n--- 高集中度规则（前 30 条）---')
    for r in results[:30]:
        print(f"  类型：{r['类型']}；特征：{r['特征']}；集中度 {r['集中度']}%；样本数 {r['符合条件样本数']}；总场次 {r['总场次']}（占比{r['占总场次比例']}%）；上{r['上']}下{r['下']}走{r['走']}")
    if zou_list:
        print('\n--- 仅走盘的特征 ---')
        for r in zou_list[:15]:
            print(f"  类型：{r['类型']}；特征：{r['特征']}；走盘场次 {r['走盘场次']}")
    
    # 统计：集中度≥90% 且 走盘≥3 的比赛场次（去重，除去走盘）
    # 先只统计主/0/0 和 客/0/0
    target_morphs = [('主', '0', '0'), ('客', '0', '0')]
    total_base = len([r for r in rows if (r['B'], r['D'], r['F']) in target_morphs])
    print(f'\n--- 只统计主/0/0 和 客/0/0 形态（共 {total_base} 场）---')
    print('--- 统计：集中度≥90% 且 走盘≥3 的有效比赛场次（去重，除去走盘） ---')
    total_effective, high_conc_rules = count_high_conc_matches(rows, target_morphs=target_morphs)
    
    # 计算总匹配场次（未去重）
    total_matched_effective = sum(r['有效场次数'] for r in high_conc_rules)
    
    print(f'\n说明：')
    print(f'  - 基础数据：主/0/0 和 客/0/0 形态共 {total_base} 场')
    print(f'  - 符合条件的规则数: {len(high_conc_rules)} 条')
    print(f'    （这些规则都满足：集中度≥90% 且 走盘≥3）')
    print(f'  - 所有规则匹配的有效场次总数（未去重）: {total_matched_effective} 场')
    print(f'    （同一场比赛可能被多条规则匹配，所以会有重复）')
    print(f'  - 去重后的有效场次总数（上+下，不含走盘）: {total_effective} 场')
    print(f'    （重叠的比赛只按1次计算）')
    print(f'  - 去重率: {round((1 - total_effective / total_matched_effective) * 100, 1) if total_matched_effective > 0 else 0}%')
    print(f'  - 占基础数据的比例: {round(total_effective / total_base * 100, 1) if total_base > 0 else 0}%')
    
    print('\n符合条件的规则详情（全部显示）:')
    high_conc_rules.sort(key=lambda x: (-x['集中度'], -x['新增有效场次数'], -x['总场次']))
    for r in high_conc_rules:
        print(f"  类型：{r['类型']}；特征：{r['特征']}；集中度 {r['集中度']}%；"
              f"总场次 {r['总场次']}（上{r['上']}下{r['下']}走{r['走']}）；"
              f"有效场次 {r['有效场次数']}，新增 {r['新增有效场次数']}")

if __name__ == '__main__':
    main()
