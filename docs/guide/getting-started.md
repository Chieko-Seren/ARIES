# 快速开始

本指南将帮助您快速搭建和运行 ARIES 系统。

## 环境要求

- Node.js >= 16.0.0
- Python >= 3.8
- PostgreSQL >= 13
- Redis >= 6.0
- RabbitMQ >= 3.8

## 克隆项目

```bash
git clone https://github.com/Chieko-Seren/ARIES.git
cd ARIES
```

## 后端设置

1. 创建并激活 Python 虚拟环境：

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置环境变量：

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

4. 初始化数据库：

```bash
python manage.py init_db
```

5. 启动后端服务：

```bash
python manage.py run
```

## 前端设置

1. 安装依赖：

```bash
cd frontend
npm install
```

2. 配置环境变量：

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

3. 启动开发服务器：

```bash
npm run dev
```

## 验证安装

1. 访问前端页面：`http://localhost:5173`
2. 检查后端 API：`http://localhost:8000/api/health`

## 常见问题

### 1. 数据库连接失败

- 检查 PostgreSQL 服务是否运行
- 验证数据库连接信息是否正确
- 确保数据库用户具有适当的权限

### 2. Redis 连接问题

- 确认 Redis 服务是否运行
- 检查 Redis 连接配置
- 验证 Redis 密码是否正确

### 3. 前端构建失败

- 清除 node_modules 并重新安装
- 检查 Node.js 版本是否符合要求
- 查看构建日志获取详细错误信息

## 下一步

- 查看[架构设计](/guide/architecture)了解系统架构
- 阅读[API 文档](/api/backend)了解接口使用
- 参考[部署指南](/deployment/installation)进行生产环境部署 