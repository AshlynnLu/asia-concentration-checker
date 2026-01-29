#!/bin/bash
# GitHub Pages 快速部署脚本

echo "=========================================="
echo "GitHub Pages 部署脚本"
echo "=========================================="

# 检查必要文件
if [ ! -f "index.html" ]; then
    echo "错误: index.html 不存在"
    exit 1
fi

if [ ! -f "static/rules.json" ]; then
    echo "错误: static/rules.json 不存在"
    echo "请先运行: python3 export_rules.py"
    exit 1
fi

# 检查git是否初始化
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git branch -M main
fi

# 添加文件
echo "添加文件到Git..."
git add index.html static/rules.json README_github_pages.md DEPLOY.md .gitignore

# 检查是否有未提交的更改
if git diff --staged --quiet; then
    echo "没有需要提交的更改"
else
    echo "提交更改..."
    git commit -m "Deploy to GitHub Pages"
fi

echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo "1. 在GitHub上创建新仓库（如果还没有）"
echo "2. 添加远程仓库："
echo "   git remote add origin https://github.com/你的用户名/仓库名.git"
echo "3. 推送代码："
echo "   git push -u origin main"
echo "4. 在GitHub仓库 Settings → Pages 中启用："
echo "   - Source: main branch"
echo "   - Folder: / (root)"
echo ""
echo "部署完成后，访问："
echo "https://你的用户名.github.io/仓库名/"
echo "=========================================="
