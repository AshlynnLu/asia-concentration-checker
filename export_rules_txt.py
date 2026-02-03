#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出规则数据为TXT文件，便于查看
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import rules_85, rules_80

def export_rules_txt():
    """将规则导出为易读的TXT格式"""
    
    lines = []
    lines.append("=" * 80)
    lines.append("亚洲盘集中度规则列表")
    lines.append("=" * 80)
    lines.append("")
    
    # 条件1的规则
    lines.append("-" * 80)
    lines.append(f"条件1：(上+走)或(下+走)比例>85%，总场次>6，差值>3")
    lines.append(f"共 {len(rules_85)} 条规则")
    lines.append("-" * 80)
    lines.append("")
    
    for i, rule in enumerate(rules_85, 1):
        morph_str = f"{rule['morph'][0]}/{rule['morph'][1]}/{rule['morph'][2]}"
        lines.append(f"规则 {i}:")
        lines.append(f"  形态: {morph_str}")
        lines.append(f"  特征: {rule['feature']}")
        lines.append(f"  (上+走)比例: {rule['shang_zou_ratio']:.2f}%")
        lines.append(f"  (下+走)比例: {rule['xia_zou_ratio']:.2f}%")
        lines.append(f"  总场次: {rule['n_total']}")
        lines.append(f"  统计: 上{rule['shang']} 下{rule['xia']} 走{rule['zou']}")
        lines.append("")
    
    lines.append("")
    lines.append("-" * 80)
    lines.append(f"条件2：上/走/下任一比例>80%，总场次>4")
    lines.append(f"共 {len(rules_80)} 条规则")
    lines.append("-" * 80)
    lines.append("")
    
    for i, rule in enumerate(rules_80, 1):
        morph_str = f"{rule['morph'][0]}/{rule['morph'][1]}/{rule['morph'][2]}"
        lines.append(f"规则 {i}:")
        lines.append(f"  形态: {morph_str}")
        lines.append(f"  特征: {rule['feature']}")
        lines.append(f"  上比例: {rule['shang_ratio']:.2f}%")
        lines.append(f"  走比例: {rule['zou_ratio']:.2f}%")
        lines.append(f"  下比例: {rule['xia_ratio']:.2f}%")
        lines.append(f"  总场次: {rule['n_total']}")
        lines.append(f"  统计: 上{rule['shang']} 下{rule['xia']} 走{rule['zou']}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append(f"导出完成！")
    lines.append(f"条件1规则数: {len(rules_85)}")
    lines.append(f"条件2规则数: {len(rules_80)}")
    lines.append(f"总规则数: {len(rules_85) + len(rules_80)}")
    lines.append("=" * 80)
    
    # 保存为TXT文件
    output_file = 'rules_list.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"已导出规则到: {output_file}")
    print(f"  条件1规则数: {len(rules_85)}")
    print(f"  条件2规则数: {len(rules_80)}")
    print(f"  总规则数: {len(rules_85) + len(rules_80)}")
    
    # 统计各形态的规则数
    print("\n各形态规则统计:")
    morphs_count = {}
    for rule in rules_85 + rules_80:
        morph_str = f"{rule['morph'][0]}/{rule['morph'][1]}/{rule['morph'][2]}"
        morphs_count[morph_str] = morphs_count.get(morph_str, 0) + 1
    
    for morph_str in sorted(morphs_count.keys()):
        print(f"  {morph_str}: {morphs_count[morph_str]} 条")

if __name__ == '__main__':
    export_rules_txt()
