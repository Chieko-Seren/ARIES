#!/bin/bash

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "请以root权限运行此脚本"
    exit 1
fi

# 设置环境变量
export NIPS_CONFIG=${NIPS_CONFIG:-"/etc/nips/nips.yaml"}
export NIPS_LOG=${NIPS_LOG:-"/var/log/nips/nips.log"}

# 创建日志目录
mkdir -p "$(dirname "$NIPS_LOG")"
touch "$NIPS_LOG"
chmod 644 "$NIPS_LOG"

# 检查配置文件
if [ ! -f "$NIPS_CONFIG" ]; then
    echo "错误：配置文件 $NIPS_CONFIG 不存在"
    exit 1
fi

# 检查可执行文件
NIPS_BIN="/usr/local/bin/nips"
if [ ! -x "$NIPS_BIN" ]; then
    echo "错误：可执行文件 $NIPS_BIN 不存在或没有执行权限"
    exit 1
fi

# 启动服务
echo "正在启动 NIPS 服务..."
exec "$NIPS_BIN" --config "$NIPS_CONFIG" --log "$NIPS_LOG" 