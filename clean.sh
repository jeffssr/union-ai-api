#!/bin/bash

# Union AI API - 清理脚本（删除容器和镜像，保留数据）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  警告：此操作将删除容器和镜像，但保留数据${NC}"
echo ""
read -p "确定要继续吗？(y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "错误：Docker Compose 未安装"
    exit 1
fi

cd "$SCRIPT_DIR"

echo "正在停止服务..."
$COMPOSE_CMD -f docker-compose.clean.yml down

echo "正在删除容器..."
docker rm -f union-ai-api 2>/dev/null || true

echo "正在删除镜像..."
docker rmi $(docker images -q union-ai-api*) 2>/dev/null || true

echo ""
echo -e "${RED}✅ 清理完成${NC}"
echo ""
echo "数据已保留在：$SCRIPT_DIR/data"
echo "如需删除数据，请手动执行：rm -rf $SCRIPT_DIR/data"
