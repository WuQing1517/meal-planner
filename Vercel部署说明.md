# 部署到Vercel（免费）

## 方式1: 通过Vercel网站部署（最简单）

### 步骤1: 注册Vercel账号
1. 访问 https://vercel.com/
2. 点击 "Sign Up" 注册（可用GitHub账号）

### 步骤2: 推送代码到GitHub
1. 在GitHub创建新仓库
2. 推送代码：

```bash
cd D:\meal-planner
git init
git add .
git commit -m "初始提交"
git remote add origin https://github.com/你的用户名/meal-planner.git
git push -u origin main
```

### 步骤3: 在Vercel导入项目
1. 登录Vercel控制台
2. 点击 "Add New..." → "Project"
3. 选择 "Import Git Repository"
4. 选择你的GitHub仓库
5. 点击 "Deploy"

### 步骤4: 访问应用
部署完成后，Vercel会提供一个URL，类似：
`https://meal-planner-xxx.vercel.app`

---

## 方式2: 通过Vercel CLI部署

### 步骤1: 安装Vercel CLI
```bash
npm install -g vercel
```

### 步骤2: 登录Vercel
```bash
vercel login
```

### 步骤3: 部署
```bash
cd D:\meal-planner
vercel
```

### 步骤4: 按提示操作
- Set up and deploy? → Y
- Which scope? → 选择你的账号
- Link to existing project? → N
- Project name: meal-planner
- Directory is ./? → Y
- Want to override settings? → N

---

## 注意事项
1. Vercel免费版有限制，但足够个人使用
2. 文件系统写入可能受限，建议使用环境变量或外部存储
3. 冷启动可能需要几秒钟
