# LLM 面试知识点 Web 页面

轻量级的面试知识点展示系统，自动读取 Markdown 文件并生成美观的网页。

## 功能特点

- 📖 **自动读取 MD 文件** - 自动扫描 `note/` 目录下的所有 Markdown 文件
- 🎨 **美观界面** - 现代化的响应式设计，支持桌面和移动端
- 🚀 **轻量部署** - 基于 Node.js + Express，资源占用少
- 🔍 **知识分类** - 左侧导航栏展示所有知识点

## 快速开始

### 1. 安装依赖

```bash
cd code/web
npm install
```

### 2. 启动服务

```bash
npm start
```

服务启动后访问：http://localhost:3000

### 3. 添加知识点

将 Markdown 文件放入项目根目录的 `note/` 文件夹中，刷新页面即可自动显示。

## 部署方式

### 本地开发

```bash
npm start
```

### 服务器部署

1. **上传代码到服务器**
```bash
# 将整个项目上传到服务器
scp -r code/web user@server:/path/to/deploy
```

2. **在服务器上安装依赖**
```bash
cd /path/to/deploy
npm install --production
```

3. **启动服务**
```bash
# 直接启动
npm start

# 或使用 PM2 进行进程管理（推荐）
npm install -g pm2
pm2 start server.js --name lm-interview
pm2 save
pm2 startup
```

4. **配置反向代理（可选）**

使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Docker 部署（可选）

创建 `Dockerfile`：

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

构建并运行：

```bash
docker build -t lm-interview .
docker run -p 3000:3000 -v /path/to/note:/app/../../note lm-interview
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| PORT | 服务端口 | 3000 |

## 目录结构

```
code/web/
├── server.js          # 后端服务
├── package.json       # 项目配置
├── public/
│   ├── index.html     # 主页面
│   ├── styles.css     # 样式文件
│   └── app.js         # 前端逻辑
└── README.md          # 说明文档

../../note/            # Markdown 文件目录
└── *.md
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/notes` | GET | 获取所有笔记列表 |
| `/api/notes/:filename` | GET | 获取单个笔记内容（已解析为 HTML） |

## 技术栈

- **后端**: Node.js + Express
- **前端**: 原生 HTML/CSS/JavaScript
- **Markdown 解析**: marked

## 注意事项

1. Markdown 文件需放在项目根目录的 `note/` 文件夹下
2. 文件名建议使用中文或英文，避免特殊字符
3. 建议 Markdown 文件第一行为标题（# 标题）
4. 生产环境建议使用 PM2 等进程管理工具
