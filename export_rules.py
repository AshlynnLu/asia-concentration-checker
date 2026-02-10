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
        d = {
            'morph': list(rule['morph']),  # 兼容：单形态
            'feature': rule['feature'],
            'conditions': {k: (list(v) if isinstance(v, tuple) else v) for k, v in rule['conditions'].items()},
            'shang_zou_ratio': rule['shang_zou_ratio'],
            'xia_zou_ratio': rule['xia_zou_ratio'],
            'shang_ratio': rule['shang_ratio'],
            'zou_ratio': rule['zou_ratio'],
            'xia_ratio': rule['xia_ratio'],
            'n_total': rule['n_total'],
            'shang': rule['shang'],
            'xia': rule['xia'],
            'zou': rule['zou'],
        }
        if rule.get('morph_group'):
            d['morph_group'] = [list(m) for m in rule['morph_group']]
        return d

    rules_85_json = [rule_to_dict(r) for r in rules_85]
    rules_80_json = [rule_to_dict(r) for r in rules_80]
    
    output = {
        'rules_85': rules_85_json,
        'rules_80': rules_80_json,
        'meta': {
            'count_85': len(rules_85_json),
            'count_80': len(rules_80_json),
            'description': {
                'condition1': '(上+走)或(下+走)比例>85%，总场次>6，差值>3',
                'condition2': '上/走/下任一比例>80%，总场次>4'
            },
            'source': 'AI 自动从 docs/20252026欧洲FB.xlsx 按 RED_CONDITIONS 和条件1/2 生成的高集中度规则'
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
