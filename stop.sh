#!/bin/bash

# Union AI API - 停止服务脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "正在停止 Union AI API 服务..."

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "错误：Docker Compose 未安装"
    exit 1
fi

cd "$SCRIPT_DIR"
$COMPOSE_CMD -f docker-compose.clean.yml down

echo "✅ 服务已停止"
