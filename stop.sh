#!/bin/bash

# Union AI API - 快速停止脚本
# 此脚本会停止容器但保留容器，下次启动可秒开
# 特点：停止速度快，数据不会丢失，下次启动无需重建

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="union-ai-api"

# Docker Compose 命令检测
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        echo ""
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

# 打印标题
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║       Union AI API - 快速停止脚本                     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查 Docker Compose
check_docker_compose() {
    if [ -z "$COMPOSE_CMD" ]; then
        echo -e "${RED}❌ Docker Compose 未安装！${NC}"
        exit 1
    fi
}

# 检查容器是否正在运行
check_container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${PROJECT_NAME}$"
}

# 停止服务（保留容器，下次可秒开）
stop_services() {
    cd "$SCRIPT_DIR"
    
    if ! check_container_running; then
        echo -e "${YELLOW}⚠️  服务未在运行${NC}"
        echo ""
        echo -e "${CYAN}提示：${NC}如需完全删除容器和镜像，请使用 ./clean.sh"
        exit 0
    fi
    
    echo -e "${YELLOW}⏳ 正在停止服务（保留容器，下次可秒开）...${NC}"
    echo ""
    
    # 使用 stop 而不是 down，保留容器以便快速重启
    $COMPOSE_CMD -f docker-compose.clean.yml stop
    
    echo ""
    echo -e "${GREEN}✅ 服务已停止${NC}"
    echo ""
    echo -e "${BLUE}📋 状态信息:${NC}"
    echo -e "  ${CYAN}•${NC} 容器已停止但保留（下次启动秒开）"
    echo -e "  ${CYAN}•${NC} 数据已保存至：./data/"
    echo -e "  ${CYAN}•${NC} 镜像仍然保留"
    echo ""
    echo -e "${YELLOW}💡 常用命令:${NC}"
    echo -e "  ${CYAN}•${NC} 启动服务：./start.sh（秒开）"
    echo -e "  ${CYAN}•${NC} 重启服务：./restart.sh"
    echo -e "  ${CYAN}•${NC} 完全清理：./clean.sh（删除容器和镜像）"
}

# 主流程
main() {
    print_header
    check_docker_compose
    stop_services
}

main
