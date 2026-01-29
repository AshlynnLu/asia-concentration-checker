#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证GitHub Pages部署文件是否完整
"""
import os
import json

print("=" * 60)
print("验证GitHub Pages部署文件")
print("=" * 60)

# 检查必要文件
required_files = [
    'index.html',
    'static/rules.json'
]

all_ok = True

for file in required_files:
    if os.path.exists(file):
        size = os.path.getsize(file) / 1024
        print(f"✓ {file} 存在 ({size:.1f} KB)")
    else:
        print(f"✗ {file} 不存在")
        all_ok = False

# 验证rules.json格式
if os.path.exists('static/rules.json'):
    try:
        with open('static/rules.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'rules_85' in data and 'rules_80' in data:
            print(f"\n✓ rules.json 格式正确")
            print(f"  条件1规则数: {len(data['rules_85'])}")
            print(f"  条件2规则数: {len(data['rules_80'])}")
        else:
            print("\n✗ rules.json 格式错误：缺少必要字段")
            all_ok = False
    except json.JSONDecodeError as e:
        print(f"\n✗ rules.json JSON格式错误: {e}")
        all_ok = False

# 检查index.html
if os.path.exists('index.html'):
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'static/rules.json' in content:
            print("\n✓ index.html 包含正确的规则数据路径")
        else:
            print("\n✗ index.html 中未找到规则数据路径")
            all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✓ 所有文件验证通过，可以部署到GitHub Pages！")
    print("\n下一步：")
    print("1. git add index.html static/rules.json")
    print("2. git commit -m 'Deploy to GitHub Pages'")
    print("3. git push")
    print("4. 在GitHub仓库Settings中启用Pages")
else:
    print("✗ 验证失败，请检查上述问题")
print("=" * 60)
