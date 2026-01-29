# GitHub Pages 部署说明

## 部署步骤

### 1. 准备文件

确保以下文件在项目根目录：
- `index.html` - 主页面
- `static/rules.json` - 规则数据文件

### 2. 创建GitHub仓库

1. 在GitHub上创建一个新仓库（例如：`asia-concentration-checker`）
2. 将项目文件推送到仓库

```bash
git init
git add index.html static/rules.json README.md
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/asia-concentration-checker.git
git push -u origin main
```

### 3. 启用GitHub Pages

1. 进入仓库的 **Settings** 页面
2. 在左侧菜单找到 **Pages**
3. 在 **Source** 部分选择：
   - Branch: `main`
   - Folder: `/ (root)`
4. 点击 **Save**

### 4. 访问网站

几分钟后，你的网站将在以下地址可用：
```
https://你的用户名.github.io/asia-concentration-checker/
```

## 文件结构

```
项目根目录/
├── index.html          # 主页面（必须）
├── static/
│   └── rules.json      # 规则数据（必须）
├── README.md           # 说明文档（可选）
└── .gitignore          # Git忽略文件（可选）
```

## 更新规则数据

如果需要更新规则数据：

1. 运行导出脚本：
```bash
source .venv/bin/activate
python3 export_rules.py
```

2. 提交并推送更新：
```bash
git add static/rules.json
git commit -m "Update rules data"
git push
```

## 注意事项

- GitHub Pages 只支持静态文件（HTML、CSS、JavaScript）
- 所有逻辑都在浏览器中运行，无需后端服务器
- `rules.json` 文件较大（约380KB），首次加载可能需要几秒钟
- 确保 `static/rules.json` 文件路径正确

## 本地测试

在部署前，可以在本地测试：

```bash
# 使用Python简单HTTP服务器
python3 -m http.server 8000

# 然后在浏览器访问
# http://localhost:8000
```
