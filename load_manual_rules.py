#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加载手工规则（从 docs/规则.xlsx）
"""
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def col_index(ref):
    """将Excel引用转换为列索引和行索引"""
    m = re.match(r'([A-Z]+)(\d+)', ref)
    if not m:
        return None, None
    col_s, row_s = m.groups()
    col = 0
    for c in col_s:
        col = col * 26 + (ord(c) - ord('A') + 1)
    return col - 1, int(row_s) - 1

def parse_condition(col_name, condition_str):
    """
    解析条件字符串，返回 (key, value) 格式
    
    Excel列映射到原数据列：
    B(马会) → F列
    C(水差) → I列
    D(马主) → K列
    E(马平) → N列
    F(主差) → P列
    G(平差) → Q列
    H(客差) → R列
    """
    # 列名映射
    col_map = {
        'B': 'F',  # 马会
        'C': 'I',  # 水差
        'D': 'K',  # 马主
        'E': 'N',  # 马平
        'F': 'P',  # 主差
        'G': 'Q',  # 平差
        'H': 'R',  # 客差
    }
    
    if col_name not in col_map:
        return None, None
    
    target_col = col_map[col_name]
    condition_str = str(condition_str).strip()
    
    # 处理范围：(0.8~0.86) 或 0.8~0.86
    range_match = re.match(r'\(?([-\d.]+)~([-\d.]+)\)?', condition_str)
    if range_match:
        low, high = float(range_match.group(1)), float(range_match.group(2))
        # 确保low <= high
        if low > high:
            low, high = high, low
        return f'{target_col}_range', (low, high)
    
    # 处理 >= 或 ≥
    if condition_str.startswith('>=') or condition_str.startswith('≥'):
        val = float(re.search(r'[>=≥]([-\d.]+)', condition_str).group(1))
        return f'{target_col}_ge', val
    
    # 处理 <= 或 ≤
    if condition_str.startswith('<=') or condition_str.startswith('≤'):
        val = float(re.search(r'[<=≤]([-\d.]+)', condition_str).group(1))
        return f'{target_col}_le', val
    
    # 处理 >
    if condition_str.startswith('>'):
        val = float(re.search(r'>([-\d.]+)', condition_str).group(1))
        return f'{target_col}_gt', val
    
    # 处理 <
    if condition_str.startswith('<'):
        val = float(re.search(r'<([-\d.]+)', condition_str).group(1))
        return f'{target_col}_lt', val
    
    return None, None

def load_manual_rules(xlsx_path='docs/规则.xlsx'):
    """
    从Excel文件加载手工规则
    返回格式：{
        ('主', '0', '0.25'): [rule1, rule2, ...],
        ('客', '0', '0.25'): [rule3, rule4, ...],
        ...
    }
    每个rule: {
        'morph': ('主', '0', '0.25'),
        'feature': '马平>3.4，且平差<0',
        'conditions': {'N_gt': 3.4, 'Q_lt': 0},
        'expected_shang': 1,
        'expected_xia': 5,
        'expected_zou': 0,
    }
    """
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        with z.open('xl/sharedStrings.xml') as f:
            ss_root = ET.parse(f).getroot()
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        strings = []
        for s in ss_root.findall('.//main:si', ns):
            texts = s.findall('.//main:t', ns)
            strings.append(''.join(x.text or '' for x in texts) if texts else '')
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
    
    # 解析规则
    rules_by_morph = defaultdict(list)
    current_morph_str = None
    nrows = max(grid.keys()) + 1 if grid else 0
    
    for r in range(nrows):
        row = grid[r]
        col_a = str(row.get(0, '')).strip()  # A列
        
        # 检查是否是形态标识行
        if col_a in ('0/0.25', '0.25/0', '0.5/0.25'):
            current_morph_str = col_a
            continue
        
        # 跳过表头行
        if col_a == '主客':
            continue
        
        # 解析规则行
        if col_a in ('主', '客') and current_morph_str:
            # 解析形态
            d_val, f_val = current_morph_str.split('/')
            morph = (col_a, d_val, f_val)
            
            # 解析条件（B-H列）
            conditions = {}
            feature_parts = []
            
            col_names = ['B', 'C', 'D', 'E', 'F', 'G', 'H']
            col_labels = {
                'B': '马会', 'C': '水差', 'D': '马主', 
                'E': '马平', 'F': '主差', 'G': '平差', 'H': '客差'
            }
            
            for idx, col_name in enumerate(col_names):
                col_idx = idx + 1  # B列是索引1
                val = str(row.get(col_idx, '')).strip()
                if val:
                    key, value = parse_condition(col_name, val)
                    if key:
                        conditions[key] = value
                        # 构建特征描述
                        feature_parts.append(f'{col_labels[col_name]}{val}')
            
            if not conditions:
                continue
            
            feature = '，且'.join(feature_parts)
            
            # 解析预期结果（J、K、L列）
            try:
                expected_shang = int(row.get(9, 0) or 0)  # J列
                expected_zou = int(row.get(10, 0) or 0)   # K列
                expected_xia = int(row.get(11, 0) or 0)   # L列
            except (ValueError, TypeError):
                continue
            
            rule = {
                'morph': morph,
                'feature': feature,
                'conditions': conditions,
                'expected_shang': expected_shang,
                'expected_xia': expected_xia,
                'expected_zou': expected_zou,
            }
            
            rules_by_morph[morph].append(rule)
    
    return rules_by_morph

if __name__ == '__main__':
    # 测试
    rules = load_manual_rules()
    print('手工规则统计：')
    for morph, rule_list in sorted(rules.items()):
        print(f'  {morph[0]}/{morph[1]}/{morph[2]}: {len(rule_list)} 条规则')
    
    print('\n示例规则：')
    for morph, rule_list in sorted(rules.items()):
        if rule_list:
            print(f'\n{morph[0]}/{morph[1]}/{morph[2]} 的第一条规则：')
            rule = rule_list[0]
            print(f'  特征：{rule["feature"]}')
            print(f'  条件：{rule["conditions"]}')
            print(f'  预期：上{rule["expected_shang"]} 走{rule["expected_zou"]} 下{rule["expected_xia"]}')
