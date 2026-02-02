#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手工规则模块：读取 docs/规则.xlsx 并提供匹配功能
支持三种盘口类型：0/0.25、0.25/0、0.5/0.25
"""
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def col_index(ref):
    """将Excel单元格引用转换为行列索引"""
    m = re.match(r'([A-Z]+)(\d+)', ref)
    if not m:
        return None, None
    col_s, row_s = m.groups()
    col = 0
    for c in col_s:
        col = col * 26 + (ord(c) - ord('A') + 1)
    return col - 1, int(row_s) - 1

def load_xlsx_rules(path):
    """加载Excel文件中的手工规则"""
    with zipfile.ZipFile(path, 'r') as z:
        try:
            with z.open('xl/sharedStrings.xml') as f:
                ss_root = ET.parse(f).getroot()
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            strings = []
            for s in ss_root.findall('.//main:si', ns):
                texts = s.findall('.//main:t', ns)
                strings.append(''.join(x.text or '' for x in texts) if texts else '')
        except KeyError:
            strings = []
        
        with z.open('xl/worksheets/sheet1.xml') as f:
            root = ET.parse(f).getroot()
    
    ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
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
                if t == 's' and int(v.text) < len(strings):
                    val = strings[int(v.text)]
                else:
                    val = v.text
            else:
                val = ''
            grid[ri][ci] = val
    
    return parse_rules_from_grid(grid)

def parse_rules_from_grid(grid):
    """从grid中解析规则，返回按盘口类型分组的规则字典"""
    rules_by_type = {
        '0/0.25': [],
        '0.25/0': [],
        '0.5/0.25': []
    }
    
    current_type = None
    max_row = max(grid.keys()) if grid else 0
    
    for row_idx in range(max_row + 1):
        row_data = grid.get(row_idx, {})
        cell_a = str(row_data.get(0, '')).strip()
        
        # 检测类型标题行
        if cell_a in ('0/0.25', '0.25/0', '0.5/0.25'):
            current_type = cell_a
            continue
        
        # 跳过列标题行
        if cell_a == '主客':
            continue
        
        # 解析规则行
        if current_type and cell_a in ('主', '客'):
            rule = parse_rule_row(row_data, current_type)
            if rule:
                rules_by_type[current_type].append(rule)
    
    return rules_by_type

def parse_rule_row(row_data, pankong_type):
    """解析一行规则数据"""
    # 列映射：A=主客, B=马会, C=水差, D=马主, E=马平, F=主差, G=平差, H=客差, I=预测, J=上, K=走, L=下
    zhu_ke = str(row_data.get(0, '')).strip()  # A列
    ma_hui = str(row_data.get(1, '')).strip()   # B列
    shui_cha = str(row_data.get(2, '')).strip() # C列
    ma_zhu = str(row_data.get(3, '')).strip()   # D列
    ma_ping = str(row_data.get(4, '')).strip()  # E列
    zhu_cha = str(row_data.get(5, '')).strip()  # F列
    ping_cha = str(row_data.get(6, '')).strip() # G列
    ke_cha = str(row_data.get(7, '')).strip()   # H列
    yu_ce = str(row_data.get(8, '')).strip()    # I列
    
    try:
        shang = int(row_data.get(9, 0))  # J列
        zou = int(row_data.get(10, 0))   # K列
        xia = int(row_data.get(11, 0))   # L列
    except (ValueError, TypeError):
        return None
    
    # 构建条件列表
    conditions = []
    if ma_hui:
        conditions.append(('马会', 'B', ma_hui))
    if shui_cha:
        conditions.append(('水差', 'C', shui_cha))
    if ma_zhu:
        conditions.append(('马主', 'D', ma_zhu))
    if ma_ping:
        conditions.append(('马平', 'E', ma_ping))
    if zhu_cha:
        conditions.append(('主差', 'F', zhu_cha))
    if ping_cha:
        conditions.append(('平差', 'G', ping_cha))
    if ke_cha:
        conditions.append(('客差', 'H', ke_cha))
    
    return {
        'zhu_ke': zhu_ke,
        'pankong': pankong_type,
        'conditions': conditions,
        'prediction': yu_ce,
        'shang': shang,
        'zou': zou,
        'xia': xia,
        'n_total': shang + zou + xia,
    }

def check_condition(value, condition_str):
    """检查数值是否满足条件字符串"""
    if value is None:
        return False
    
    condition_str = condition_str.strip()
    
    # 处理范围：(min~max) 或 min~max
    if '~' in condition_str:
        range_match = re.match(r'\(?([0-9.-]+)~([0-9.-]+)\)?', condition_str)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            return min_val <= value <= max_val
    
    # 处理比较运算符
    if condition_str.startswith('≥') or condition_str.startswith('>='):
        threshold = float(condition_str[1:])
        return value >= threshold
    elif condition_str.startswith('≤') or condition_str.startswith('<='):
        threshold = float(condition_str[1:])
        return value <= threshold
    elif condition_str.startswith('>'):
        threshold = float(condition_str[1:])
        return value > threshold
    elif condition_str.startswith('<'):
        threshold = float(condition_str[1:])
        return value < threshold
    
    # 处理等于
    try:
        threshold = float(condition_str)
        return abs(value - threshold) < 1e-6
    except ValueError:
        return False

def match_rule(row_data, rule):
    """检查数据行是否匹配规则"""
    # 检查主客
    B = str(row_data.get('B', '')).strip()
    if B != rule['zhu_ke']:
        return False
    
    # 检查盘口（D/F列）
    D = str(row_data.get('D', '')).strip()
    F = str(row_data.get('F', '')).strip()
    expected_pankong = f"{D}/{F}"
    if expected_pankong != rule['pankong']:
        return False
    
    # Excel列映射到数据列：B=马会对应G, C=水差对应I, D=马主对应K, E=马平对应N, F=主差对应P, G=平差对应Q, H=客差对应R
    col_mapping = {
        'B': 'G',  # 马会 -> G列（马会/上水）
        'C': 'I',  # 水差 -> I列
        'D': 'K',  # 马主 -> K列
        'E': 'N',  # 马平 -> N列
        'F': 'P',  # 主差 -> P列
        'G': 'Q',  # 平差 -> Q列
        'H': 'R',  # 客差 -> R列
    }
    
    # 检查所有条件
    for cond_name, excel_col, condition_str in rule['conditions']:
        data_col = col_mapping.get(excel_col)
        if not data_col:
            continue
        
        value = row_data.get(data_col)
        if value is None:
            return False
        
        if not check_condition(value, condition_str):
            return False
    
    return True

def find_matching_rules(row_data, all_rules):
    """查找所有匹配的手工规则"""
    D = str(row_data.get('D', '')).strip()
    F = str(row_data.get('F', '')).strip()
    pankong_type = f"{D}/{F}"
    
    if pankong_type not in all_rules:
        return []
    
    matched = []
    for rule in all_rules[pankong_type]:
        if match_rule(row_data, rule):
            matched.append(rule)
    
    return matched
