# Docker 部署

本文档提供使用 Docker 和 Docker Compose 部署 ARIES 系统的详细说明。

## 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [配置说明](#配置说明)
4. [服务说明](#服务说明)
5. [数据持久化](#数据持久化)
6. [网络配置](#网络配置)
7. [监控配置](#监控配置)
8. [常见问题](#常见问题)

## 环境要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 4GB 可用内存
- 至少 20GB 可用磁盘空间

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Chieko-Seren/ARIES.git
cd ARIES
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

### 4. 访问服务

- 前端界面：`http://localhost:80`
- 后端 API：`http://localhost:8000`
- 管理界面：
  - RabbitMQ：`http://localhost:15672`
  - Grafana：`http://localhost:3000`
  - Prometheus：`http://localhost:9090`

## 配置说明

### Docker Compose 配置

`docker-compose.yml` 文件结构：

```yaml
version: '3.8'

services:
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    networks:
      - aries-network

  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - rabbitmq
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - RABBITMQ_HOST=rabbitmq
    volumes:
      - ./backend/logs:/app/logs
    networks:
      - aries-network

  # PostgreSQL 数据库
  postgres:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=aries
      - POSTGRES_USER=aries
      - POSTGRES_PASSWORD=your-password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - aries-network

  # Redis 缓存
  redis:
    image: redis:6
    ports:
      - "6379:6379"
    command: redis-server --requirepass your-redis-password
    volumes:
      - redis-data:/data
    networks:
      - aries-network

  # RabbitMQ 消息队列
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=aries
      - RABBITMQ_DEFAULT_PASS=your-rabbitmq-password
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    networks:
      - aries-network

  # Prometheus 监控
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    networks:
      - aries-network

  # Grafana 可视化
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - aries-network

volumes:
  postgres-data:
  redis-data:
  rabbitmq-data:
  prometheus-data:
  grafana-data:

networks:
  aries-network:
    driver: bridge
```

### 环境变量配置

`.env` 文件示例：

```ini
# 应用配置
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key

# 数据库配置
POSTGRES_DB=aries
POSTGRES_USER=aries
POSTGRES_PASSWORD=your-password

# Redis 配置
REDIS_PASSWORD=your-redis-password

# RabbitMQ 配置
RABBITMQ_DEFAULT_USER=aries
RABBITMQ_DEFAULT_PASS=your-rabbitmq-password

# 监控配置
PROMETHEUS_RETENTION_TIME=15d
GRAFANA_ADMIN_PASSWORD=your-grafana-password
```

## 服务说明

### 1. 前端服务

Dockerfile 示例：

```dockerfile
# 构建阶段
FROM node:16-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. 后端服务

Dockerfile 示例：

```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]
```

### 3. 数据库服务

PostgreSQL 配置：

```yaml
postgres:
  image: postgres:13
  environment:
    POSTGRES_DB: aries
    POSTGRES_USER: aries
    POSTGRES_PASSWORD: your-password
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./init-scripts:/docker-entrypoint-initdb.d
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U aries"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 4. 缓存服务

Redis 配置：

```yaml
redis:
  image: redis:6
  command: redis-server --requirepass your-redis-password
  volumes:
    - redis-data:/data
    - ./redis.conf:/usr/local/etc/redis/redis.conf
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 5. 消息队列服务

RabbitMQ 配置：

```yaml
rabbitmq:
  image: rabbitmq:3-management
  environment:
    RABBITMQ_DEFAULT_USER: aries
    RABBITMQ_DEFAULT_PASS: your-rabbitmq-password
  volumes:
    - rabbitmq-data:/var/lib/rabbitmq
    - ./rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
  healthcheck:
    test: ["CMD", "rabbitmqctl", "status"]
    interval: 30s
    timeout: 10s
    retries: 5
```

## 数据持久化

### 1. 数据卷配置

```yaml
volumes:
  postgres-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/postgres-data

  redis-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/redis-data

  rabbitmq-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/rabbitmq-data
```

### 2. 备份策略

创建备份脚本 `backup.sh`：

```bash
#!/bin/bash

# 设置备份目录
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 PostgreSQL
docker-compose exec -T postgres pg_dump -U aries aries > $BACKUP_DIR/postgres_$DATE.sql

# 备份 Redis
docker-compose exec -T redis redis-cli -a your-redis-password SAVE
docker cp aries_redis_1:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 压缩备份
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/postgres_$DATE.sql $BACKUP_DIR/redis_$DATE.rdb

# 删除原始备份文件
rm $BACKUP_DIR/postgres_$DATE.sql $BACKUP_DIR/redis_$DATE.rdb

# 保留最近 7 天的备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
```

## 网络配置

### 1. 网络设置

```yaml
networks:
  aries-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
```

### 2. 安全配置

```yaml
services:
  backend:
    networks:
      aries-network:
        aliases:
          - api.internal
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## 监控配置

### 1. Prometheus 配置

`prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'aries'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 2. Grafana 配置

`grafana.ini`：

```ini
[server]
http_port = 3000
domain = localhost
root_url = http://localhost:3000/

[security]
admin_user = admin
admin_password = your-grafana-password

[auth.anonymous]
enabled = true
org_role = Viewer
```

## 常见问题

### 1. 容器启动失败

检查步骤：
1. 查看容器日志：`docker-compose logs <service-name>`
2. 检查环境变量配置
3. 验证端口占用情况
4. 检查数据卷权限

### 2. 数据库连接问题

解决方案：
1. 确保数据库容器正常运行
2. 验证数据库连接信息
3. 检查网络连接
4. 查看数据库日志

### 3. 性能问题

优化建议：
1. 调整容器资源限制
2. 优化数据库配置
3. 配置缓存策略
4. 使用负载均衡

### 4. 数据备份恢复

备份恢复步骤：
1. 停止相关服务
2. 恢复数据文件
3. 重启服务
4. 验证数据完整性

### 5. 安全加固

安全建议：
1. 使用非 root 用户运行容器
2. 限制容器权限
3. 配置网络隔离
4. 定期更新镜像
5. 启用日志审计 