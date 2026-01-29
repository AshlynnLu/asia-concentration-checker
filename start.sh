#!/bin/bash
# 启动Web应用的脚本
cd "$(dirname "$0")"
source .venv/bin/activate
python3 app.py
