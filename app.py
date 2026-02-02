#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web应用：判断新数据是否满足高集中度条件
"""
from flask import Flask, render_template, request, jsonify
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_asia_concentration import load_xlsx, filter_rows, unique_by_game, RED_CONDITIONS, _no_duplicate_col, _RANGE_EPS
from itertools import combinations
from collections import Counter

app = Flask(__name__)

# 预加载数据和规则
print("正在加载数据...")
all_rows = load_xlsx('docs/20252026欧洲FB.xlsx')
print(f"已加载 {len(all_rows)} 条数据")

# 预计算符合条件的规则
def precompute_rules():
    """预计算所有符合条件的规则"""
    target_morphs = [('主', '0', '0'), ('客', '0', '0')]
    rules_85 = []  # 集中度≥85%，总场次≥6
    rules_80 = []  # 集中度≥80%，总场次≥5
    
    for morph in target_morphs:
        for n_cond in range(1, min(4, len(RED_CONDITIONS) + 1)):
            for cond_combo in combinations(RED_CONDITIONS, n_cond):
                if not _no_duplicate_col(cond_combo):
                    continue
                
                kw = {c[1]: c[2] for c in cond_combo}
                matched = filter_rows(all_rows, morph, **kw)
                if not matched:
                    continue
                matched_unique = unique_by_game(matched)
                c = Counter(r['U'] for r in matched_unique)
                shang, xia, zou = c.get('上', 0), c.get('下', 0), c.get('走', 0)
                n_total = len(matched_unique)
                
                if n_total == 0:
                    continue
                
                # 新条件1的计算
                shang_zou_ratio = ((shang + zou) / n_total * 100) if n_total > 0 else 0
                xia_zou_ratio = ((xia + zou) / n_total * 100) if n_total > 0 else 0
                
                # 新条件2的计算
                shang_ratio = (shang / n_total * 100) if n_total > 0 else 0
                zou_ratio = (zou / n_total * 100) if n_total > 0 else 0
                xia_ratio = (xia / n_total * 100) if n_total > 0 else 0
                
                feat = '，且'.join([c[0] for c in cond_combo])
                rule_info = {
                    'morph': morph,
                    'feature': feat,
                    'conditions': kw,
                    'shang_zou_ratio': shang_zou_ratio,
                    'xia_zou_ratio': xia_zou_ratio,
                    'shang_ratio': shang_ratio,
                    'zou_ratio': zou_ratio,
                    'xia_ratio': xia_ratio,
                    'n_total': n_total,
                    'shang': shang,
                    'xia': xia,
                    'zou': zou,
                }
                
                # 新条件1：((上+走)/(上+走+下) > 85% AND (上+走+下) > 6 AND (上-走) > 3) OR ((下+走)/(上+走+下) > 85% AND (上+走+下) > 6 AND (下-走) > 3)
                cond1_shang = shang_zou_ratio > 85 and n_total > 6 and (shang - zou) > 3
                cond1_xia = xia_zou_ratio > 85 and n_total > 6 and (xia - zou) > 3
                if cond1_shang or cond1_xia:
                    rules_85.append(rule_info)
                
                # 新条件2：(上/(上+走+下) > 80% OR 走/(上+走+下) > 80% OR 下/(上+走+下) > 80%) AND (上+走+下) > 4
                if (shang_ratio > 80 or zou_ratio > 80 or xia_ratio > 80) and n_total > 4:
                    rules_80.append(rule_info)
    
    return rules_85, rules_80

print("正在预计算规则...")
rules_85, rules_80 = precompute_rules()
print(f"已计算规则：集中度≥85%（总场次≥6）: {len(rules_85)} 条")
print(f"已计算规则：集中度≥80%（总场次≥5）: {len(rules_80)} 条")

def parse_input_data(data):
    """解析用户输入的A-R列数据"""
    # A-R列：A=0, B=1, ..., R=17
    # 根据之前的分析，关键列：
    # B=主客, D=澳门, F=马会, G=上水, H=盘差, I=水差, K=?, N=?, P=主差, Q=平差, R=客差
    try:
        # 假设输入是字典，键为列名 A-R
        row = {}
        # B, D, F 保持为字符串（主/客、0等）
        string_cols = {'A', 'B', 'C', 'D', 'F'}
        for col in 'ABCDEFGHIJKLMNOPQR':
            val = data.get(col, '')
            if isinstance(val, str):
                val = val.strip()
            if not val:
                row[col] = None
            else:
                # B, D, F 保持为字符串，其他列尝试转换为数字
                if col in string_cols:
                    row[col] = str(val)
                else:
                    try:
                        row[col] = float(val)
                    except (ValueError, TypeError):
                        row[col] = str(val) if val else None
        return row
    except Exception as e:
        return None

def check_conditions(row_data, rules):
    """检查数据是否匹配规则"""
    matched_rules = []
    
    # 提取关键字段
    B = str(row_data.get('B', '')).strip()  # 主/客
    D = str(row_data.get('D', '')).strip()  # 澳门
    F = str(row_data.get('F', '')).strip()  # 马会
    
    # 只检查主/0/0和客/0/0
    if B not in ('主', '客') or D != '0' or F != '0':
        return matched_rules
    
    morph = (B, D, F)
    
    # 提取数值列
    def get_num(col):
        val = row_data.get(col)
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str):
            val = val.strip()
            if not val:
                return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    G, I, K, N, P, Q, R = get_num('G'), get_num('I'), get_num('K'), get_num('N'), get_num('P'), get_num('Q'), get_num('R')
    
    # 检查每个规则
    for rule in rules:
        if rule['morph'] != morph:
            continue
        
        # 检查条件是否满足（使用浮点容差，与 filter_rows 一致）
        match = True
        e = _RANGE_EPS
        for key, val in rule['conditions'].items():
            col_name = key.split('_')[0]  # G_ge -> G
            col_val = {'G': G, 'I': I, 'K': K, 'N': N, 'P': P, 'Q': Q, 'R': R}.get(col_name)
            
            if col_val is None:
                match = False
                break
            
            if key.endswith('_ge'):
                if col_val < val - e:
                    match = False
                    break
            elif key.endswith('_le'):
                if col_val > val + e:
                    match = False
                    break
            elif key.endswith('_gt'):
                if col_val <= val - e:
                    match = False
                    break
            elif key.endswith('_lt'):
                if col_val >= val + e:
                    match = False
                    break
            elif key.endswith('_range'):
                if not (val[0] - e <= col_val <= val[1] + e):
                    match = False
                    break
        
        if match:
            matched_rules.append(rule)
    
    return matched_rules

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    try:
        data = request.json
        row_data = parse_input_data(data)
        
        if row_data is None:
            return jsonify({'error': '数据格式错误'}), 400
        
        # 检查两个条件
        matched_85 = check_conditions(row_data, rules_85)
        matched_80 = check_conditions(row_data, rules_80)
        
        result = {
            'condition1': {
                'matched': len(matched_85) > 0,
                'count': len(matched_85),
                'rules': []
            },
            'condition2': {
                'matched': len(matched_80) > 0,
                'count': len(matched_80),
                'rules': []
            }
        }
        
        # 添加匹配的规则信息（最多显示5条）
        # 对于每个匹配的规则，重新筛选数据以显示实际结果
        for rule in matched_85[:5]:
            # 重新筛选数据、按场次去重后统计
            actual_matched = filter_rows(all_rows, rule['morph'], **rule['conditions'])
            actual_matched = unique_by_game(actual_matched)
            actual_c = Counter(r['U'] for r in actual_matched)
            actual_shang, actual_xia, actual_zou = actual_c.get('上', 0), actual_c.get('下', 0), actual_c.get('走', 0)
            actual_n_total = len(actual_matched)
            
            # 计算新条件1的集中度显示值（取较大的一个比例）
            actual_shang_zou_ratio = ((actual_shang + actual_zou) / actual_n_total * 100) if actual_n_total > 0 else 0
            actual_xia_zou_ratio = ((actual_xia + actual_zou) / actual_n_total * 100) if actual_n_total > 0 else 0
            actual_cond1_ratio = max(actual_shang_zou_ratio, actual_xia_zou_ratio)
            
            result['condition1']['rules'].append({
                'feature': rule['feature'],
                'conc': round(actual_cond1_ratio, 2),
                'n_total': actual_n_total,
                'shang': actual_shang,
                'xia': actual_xia,
                'zou': actual_zou,
            })
        
        for rule in matched_80[:5]:
            # 重新筛选数据、按场次去重后统计
            actual_matched = filter_rows(all_rows, rule['morph'], **rule['conditions'])
            actual_matched = unique_by_game(actual_matched)
            actual_c = Counter(r['U'] for r in actual_matched)
            actual_shang, actual_xia, actual_zou = actual_c.get('上', 0), actual_c.get('下', 0), actual_c.get('走', 0)
            actual_n_total = len(actual_matched)
            
            # 计算新条件2的集中度显示值（取三者中最大的比例）
            actual_shang_ratio = (actual_shang / actual_n_total * 100) if actual_n_total > 0 else 0
            actual_zou_ratio = (actual_zou / actual_n_total * 100) if actual_n_total > 0 else 0
            actual_xia_ratio = (actual_xia / actual_n_total * 100) if actual_n_total > 0 else 0
            actual_cond2_ratio = max(actual_shang_ratio, actual_zou_ratio, actual_xia_ratio)
            
            result['condition2']['rules'].append({
                'feature': rule['feature'],
                'conc': round(actual_cond2_ratio, 2),
                'n_total': actual_n_total,
                'shang': actual_shang,
                'xia': actual_xia,
                'zou': actual_zou,
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Web应用已启动！")
    print("=" * 60)
    print("请在浏览器中访问：http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    try:
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n错误：端口5000已被占用，请尝试：")
            print("1. 关闭占用5000端口的程序")
            print("2. 或修改app.py中的端口号")
        else:
            print(f"\n启动错误：{e}")
