#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出规则数据为JSON，供前端使用
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import rules_85, rules_80

def export_rules():
    # 转换规则为JSON可序列化的格式
    def rule_to_dict(rule):
        return {
            'morph': list(rule['morph']),  # tuple转list
            'feature': rule['feature'],
            'conditions': {k: (list(v) if isinstance(v, tuple) else v) for k, v in rule['conditions'].items()},
            'conc_no_zou': rule['conc_no_zou'],
            'conc_with_zou': rule['conc_with_zou'],
            'n_total': rule['n_total'],
            'n_eff': rule['n_eff'],
            'shang': rule['shang'],
            'xia': rule['xia'],
            'zou': rule['zou'],
        }
    
    rules_85_json = [rule_to_dict(r) for r in rules_85]
    rules_80_json = [rule_to_dict(r) for r in rules_80]
    
    output = {
        'rules_85': rules_85_json,
        'rules_80': rules_80_json,
        'meta': {
            'count_85': len(rules_85_json),
            'count_80': len(rules_80_json),
            'description': {
                'condition1': '除去走盘的，集中度≥85%（总场次≥6）',
                'condition2': '算上走盘的，集中度≥80%（总场次≥5）'
            }
        }
    }
    
    # 保存为JSON文件
    output_file = 'static/rules.json'
    os.makedirs('static', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"已导出规则数据到: {output_file}")
    print(f"  条件1规则数: {len(rules_85_json)}")
    print(f"  条件2规则数: {len(rules_80_json)}")
    print(f"  文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")

if __name__ == '__main__':
    export_rules()
