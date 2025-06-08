# 安装步骤

本文档提供 ARIES 系统的详细安装步骤。

## 目录

1. [环境准备](#环境准备)
2. [基础服务安装](#基础服务安装)
3. [后端服务安装](#后端服务安装)
4. [前端服务安装](#前端服务安装)
5. [系统配置](#系统配置)
6. [验证安装](#验证安装)

## 环境准备

### 1. 系统更新

```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade -y

# CentOS
sudo yum update -y
```

### 2. 安装基础工具

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget vim build-essential

# CentOS
sudo yum install -y git curl wget vim gcc gcc-c++ make
```

## 基础服务安装

### 1. Node.js 安装

```bash
# 使用 nvm 安装 Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 16
nvm use 16
```

### 2. Python 安装

```bash
# Ubuntu/Debian
sudo apt install -y python3.8 python3.8-venv python3-pip

# CentOS
sudo yum install -y python38 python38-devel python38-pip
```

### 3. PostgreSQL 安装

```bash
# Ubuntu/Debian
sudo apt install -y postgresql-13 postgresql-contrib-13

# CentOS
sudo yum install -y postgresql13-server postgresql13-contrib
sudo postgresql-13-setup initdb
sudo systemctl enable postgresql-13
sudo systemctl start postgresql-13
```

### 4. Redis 安装

```bash
# Ubuntu/Debian
sudo apt install -y redis-server

# CentOS
sudo yum install -y redis
sudo systemctl enable redis
sudo systemctl start redis
```

### 5. RabbitMQ 安装

```bash
# Ubuntu/Debian
curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | sudo bash
sudo apt install -y rabbitmq-server

# CentOS
curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.rpm.sh | sudo bash
sudo yum install -y rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

## 后端服务安装

### 1. 克隆项目

```bash
git clone https://github.com/Chieko-Seren/ARIES.git
cd ARIES/backend
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

### 5. 初始化数据库

```bash
# 创建数据库用户
sudo -u postgres psql
postgres=# CREATE USER aries WITH PASSWORD 'your_password';
postgres=# CREATE DATABASE aries;
postgres=# GRANT ALL PRIVILEGES ON DATABASE aries TO aries;
postgres=# \q

# 初始化数据库
python manage.py init_db
```

### 6. 启动后端服务

```bash
# 开发环境
python manage.py run

# 生产环境
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## 前端服务安装

### 1. 进入前端目录

```bash
cd ../frontend
```

### 2. 安装依赖

```bash
npm install
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

### 4. 构建前端

```bash
# 开发环境
npm run dev

# 生产环境
npm run build
```

### 5. 配置 Nginx

```bash
# 安装 Nginx
sudo apt install -y nginx

# 配置 Nginx
sudo vim /etc/nginx/sites-available/aries
```

Nginx 配置示例：
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        root /path/to/ARIES/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/aries /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 系统配置

### 1. 配置 SSL 证书

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com
```

### 2. 配置防火墙

```bash
# 开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
```

### 3. 配置系统服务

创建后端服务文件：
```bash
sudo vim /etc/systemd/system/aries-backend.service
```

```ini
[Unit]
Description=ARIES Backend Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/ARIES/backend
Environment="PATH=/path/to/ARIES/backend/venv/bin"
ExecStart=/path/to/ARIES/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable aries-backend
sudo systemctl start aries-backend
```

## 验证安装

### 1. 检查服务状态

```bash
# 检查后端服务
sudo systemctl status aries-backend

# 检查数据库
sudo systemctl status postgresql

# 检查 Redis
sudo systemctl status redis

# 检查 RabbitMQ
sudo systemctl status rabbitmq-server

# 检查 Nginx
sudo systemctl status nginx
```

### 2. 测试 API

```bash
# 测试健康检查接口
curl http://localhost:8000/api/health

# 测试数据库连接
curl http://localhost:8000/api/db/status
```

### 3. 访问前端

在浏览器中访问：
- 开发环境：`http://localhost:5173`
- 生产环境：`https://your_domain.com`

### 4. 检查日志

```bash
# 后端日志
tail -f /path/to/ARIES/backend/logs/app.log

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## 故障排除

### 1. 常见问题

1. **数据库连接失败**
   - 检查 PostgreSQL 服务状态
   - 验证数据库连接信息
   - 检查数据库用户权限

2. **Redis 连接问题**
   - 检查 Redis 服务状态
   - 验证 Redis 连接配置
   - 检查 Redis 密码

3. **RabbitMQ 问题**
   - 检查 RabbitMQ 服务状态
   - 验证连接信息
   - 检查队列状态

4. **前端构建失败**
   - 清除 node_modules
   - 检查 Node.js 版本
   - 查看构建日志

### 2. 日志位置

- 后端日志：`/path/to/ARIES/backend/logs/`
- Nginx 日志：`/var/log/nginx/`
- 系统日志：`/var/log/syslog`

### 3. 获取帮助

- 查看[问题报告指南](/guide/contributing#问题报告)
- 提交 GitHub Issue
- 联系项目维护者 