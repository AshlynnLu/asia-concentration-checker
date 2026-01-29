# GitHub Pages 部署指南

## 📋 部署前检查清单

确保以下文件存在：
- ✅ `index.html` - 主页面
- ✅ `static/rules.json` - 规则数据（约380KB）

## 🚀 快速部署步骤

### 1. 初始化Git仓库（如果还没有）

```bash
cd /Users/sorari/Desktop/apps/ly
git init
```

### 2. 添加必要文件

```bash
git add index.html static/rules.json README_github_pages.md .gitignore
git commit -m "Initial commit for GitHub Pages"
```

### 3. 创建GitHub仓库并推送

1. 在GitHub上创建新仓库（例如：`asia-concentration-checker`）
2. 推送代码：

```bash
git branch -M main
git remote add origin https://github.com/你的用户名/asia-concentration-checker.git
git push -u origin main
```

### 4. 启用GitHub Pages

1. 进入仓库的 **Settings** → **Pages**
2. 设置：
   - **Source**: Deploy from a branch
   - **Branch**: `main` / `/ (root)`
3. 点击 **Save**

### 5. 等待部署

几分钟后访问：
```
https://你的用户名.github.io/asia-concentration-checker/
```

## 📁 项目结构

```
.
├── index.html              # 主页面（GitHub Pages入口）
├── static/
│   └── rules.json          # 规则数据
├── app.py                  # Flask后端（本地开发用）
├── templates/              # Flask模板（本地开发用）
├── export_rules.py         # 规则导出脚本
├── README_github_pages.md  # 部署说明
└── .gitignore              # Git忽略文件
```

## 🔄 更新规则数据

如果规则数据有更新：

```bash
# 1. 重新导出规则
source .venv/bin/activate
python3 export_rules.py

# 2. 提交更新
git add static/rules.json
git commit -m "Update rules data"
git push
```

## 🧪 本地测试

部署前可以在本地测试：

```bash
# 启动本地服务器
python3 -m http.server 8000

# 访问 http://localhost:8000
```

## ⚠️ 注意事项

1. **文件路径**：确保 `static/rules.json` 路径正确
2. **文件大小**：rules.json 约380KB，首次加载需要几秒
3. **浏览器兼容性**：需要支持 ES6+ 和 Fetch API
4. **HTTPS**：GitHub Pages 自动使用 HTTPS

## 🐛 常见问题

### 规则数据加载失败
- 检查 `static/rules.json` 是否存在
- 检查浏览器控制台错误信息
- 确认文件路径正确

### 判断结果不正确
- 检查输入数据格式
- 确认 B、D、F 列的值正确（B=主/客，D=0，F=0）

## 📝 技术说明

- **纯前端实现**：所有逻辑在浏览器中运行
- **无后端依赖**：不需要服务器，完全静态
- **数据格式**：规则数据为JSON格式，约380KB
