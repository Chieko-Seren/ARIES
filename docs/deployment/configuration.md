# 配置说明

本文档详细说明 ARIES 系统的各项配置选项。

## 目录

1. [环境变量配置](#环境变量配置)
2. [数据库配置](#数据库配置)
3. [缓存配置](#缓存配置)
4. [消息队列配置](#消息队列配置)
5. [安全配置](#安全配置)
6. [日志配置](#日志配置)
7. [性能配置](#性能配置)

## 环境变量配置

### 后端环境变量

创建 `.env` 文件在 `backend` 目录下：

```ini
# 应用配置
APP_NAME=ARIES
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key
APP_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=info

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aries
DB_USER=aries
DB_PASSWORD=your-password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
REDIS_POOL_SIZE=100

# RabbitMQ 配置
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=aries
RABBITMQ_PASSWORD=your-rabbitmq-password
RABBITMQ_VHOST=/

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_FROM=ARIES <noreply@example.com>

# 文件存储配置
STORAGE_TYPE=local
STORAGE_PATH=/path/to/storage
MAX_UPLOAD_SIZE=10485760  # 10MB

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 前端环境变量

创建 `.env` 文件在 `frontend` 目录下：

```ini
# API 配置
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_API_VERSION=v1

# WebSocket 配置
VITE_WS_URL=ws://localhost:8000/ws

# 应用配置
VITE_APP_TITLE=ARIES
VITE_APP_DESCRIPTION=智能网络分析系统
VITE_APP_VERSION=1.0.0

# 认证配置
VITE_AUTH_TOKEN_KEY=aries_token
VITE_AUTH_REFRESH_KEY=aries_refresh_token

# 功能开关
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_DARK_MODE=true

# 第三方服务
VITE_GA_TRACKING_ID=your-ga-id
VITE_SENTRY_DSN=your-sentry-dsn
```

## 数据库配置

### PostgreSQL 配置

编辑 `postgresql.conf`：

```ini
# 连接设置
max_connections = 100
superuser_reserved_connections = 3

# 内存设置
shared_buffers = 2GB
work_mem = 16MB
maintenance_work_mem = 256MB

# 写入设置
wal_buffers = 16MB
checkpoint_timeout = 5min
max_wal_size = 1GB

# 查询优化
random_page_cost = 1.1
effective_cache_size = 6GB

# 日志设置
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
```

### 数据库扩展

```sql
-- 安装必要扩展
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

## 缓存配置

### Redis 配置

编辑 `redis.conf`：

```ini
# 基本配置
port 6379
bind 127.0.0.1
requirepass your-redis-password

# 内存管理
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# 日志
loglevel notice
logfile /var/log/redis/redis.log

# 连接
timeout 0
tcp-keepalive 300
maxclients 10000
```

## 消息队列配置

### RabbitMQ 配置

编辑 `rabbitmq.conf`：

```ini
# 基本配置
listeners.tcp.default = 5672
management.tcp.port = 15672
management.load_definitions = /etc/rabbitmq/definitions.json

# 内存管理
vm_memory_high_watermark.relative = 0.75
vm_memory_high_watermark_paging_ratio = 0.75

# 持久化
persistence_enabled = true
queue_index_embed_msgs_below = 4096

# 集群配置
cluster_formation.peer_discovery_backend = rabbit_peer_discovery_classic_config
cluster_formation.classic_config.nodes.1 = rabbit@node1
cluster_formation.classic_config.nodes.2 = rabbit@node2
cluster_formation.classic_config.nodes.3 = rabbit@node3
```

## 安全配置

### SSL/TLS 配置

Nginx SSL 配置示例：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### 防火墙配置

```bash
# 基本防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 8000/tcp  # 后端 API
sudo ufw allow 5672/tcp  # RabbitMQ
sudo ufw allow 15672/tcp # RabbitMQ 管理
```

## 日志配置

### 后端日志配置

编辑 `logging.conf`：

```ini
[loggers]
keys=root,app,access,error

[handlers]
keys=consoleHandler,fileHandler,errorFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_app]
level=INFO
handlers=fileHandler
qualname=app
propagate=0

[logger_access]
level=INFO
handlers=fileHandler
qualname=access
propagate=0

[logger_error]
level=ERROR
handlers=errorFileHandler
qualname=error
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('logs/app.log', 'a', 10485760, 10)

[handler_errorFileHandler]
class=handlers.RotatingFileHandler
level=ERROR
formatter=detailedFormatter
args=('logs/error.log', 'a', 10485760, 10)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s
```

## 性能配置

### 系统优化

编辑 `/etc/sysctl.conf`：

```ini
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 65535

# 文件系统优化
fs.file-max = 2097152
fs.aio-max-nr = 1048576

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2
```

### Nginx 性能优化

编辑 `nginx.conf`：

```nginx
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 65535;
    multi_accept on;
    use epoll;
}

http {
    # 基本设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # 缓冲区设置
    client_body_buffer_size 16k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;

    # 压缩设置
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # 缓存设置
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

## 监控配置

### Prometheus 配置

编辑 `prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'aries'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scheme: 'http'

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

### Grafana 配置

创建仪表板配置：

```json
{
  "dashboard": {
    "id": null,
    "title": "ARIES 监控面板",
    "tags": ["aries", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "title": "系统资源使用",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "node_cpu_seconds_total{mode='user'}"
          },
          {
            "expr": "node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes"
          }
        ]
      },
      {
        "title": "API 响应时间",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "http_request_duration_seconds_sum / http_request_duration_seconds_count"
          }
        ]
      }
    ]
  }
}
``` 