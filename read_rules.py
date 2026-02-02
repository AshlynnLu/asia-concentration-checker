#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取并总结 docs/规则.xlsx 文件"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def col_index(ref):
    m = re.match(r'([A-Z]+)(\d+)', ref)
    if not m:
        return None, None
    col_s, row_s = m.groups()
    col = 0
    for c in col_s:
        col = col * 26 + (ord(c) - ord('A') + 1)
    return col - 1, int(row_s) - 1

def load_xlsx_generic(path):
    """通用的Excel读取函数，返回所有单元格数据"""
    with zipfile.ZipFile(path, 'r') as z:
        # 读取共享字符串
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
        
        # 读取第一个工作表
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
    
    return grid

def main():
    excel_path = 'docs/规则.xlsx'
    if not os.path.exists(excel_path):
        print(f"文件不存在: {excel_path}")
        return
    
    print(f"正在读取文件: {excel_path}\n")
    grid = load_xlsx_generic(excel_path)
    
    if not grid:
        print("文件为空或无法读取")
        return
    
    # 获取最大行数和列数
    max_row = max(grid.keys()) if grid else 0
    max_col = max(max(row_data.keys()) for row_data in grid.values() if row_data) if grid else 0
    
    print(f"文件包含 {max_row + 1} 行，{max_col + 1} 列\n")
    print("=" * 80)
    print("逐行总结：")
    print("=" * 80)
    
    # 逐行显示
    for row_idx in range(max_row + 1):
        row_data = grid.get(row_idx, {})
        if not row_data:
            continue
        
        # 获取该行所有单元格内容
        cells = []
        for col_idx in range(max_col + 1):
            cell_value = row_data.get(col_idx, '')
            if cell_value:
                # 将列索引转换为字母
                col_letter = ''
                n = col_idx + 1
                while n > 0:
                    n, remainder = divmod(n - 1, 26)
                    col_letter = chr(65 + remainder) + col_letter
                cells.append(f"{col_letter}: {cell_value}")
        
        if cells:
            print(f"\n第 {row_idx + 1} 行:")
            for cell in cells:
                print(f"  {cell}")

if __name__ == '__main__':
    main()
