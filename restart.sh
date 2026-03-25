#!/bin/bash

# Union AI API - 快速重启脚本
# 此脚本会快速重启服务，不会删除容器或重新构建镜像
# 特点：重启速度快，适合配置更新后使用

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
    echo -e "${BLUE}║       Union AI API - 快速重启脚本                     ║${NC}"
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

# 检查容器是否存在
check_container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${PROJECT_NAME}$"
}

# 重启服务
restart_services() {
    cd "$SCRIPT_DIR"
    
    # 如果容器不存在，提示先启动
    if ! check_container_exists; then
        echo -e "${YELLOW}⚠️  容器不存在，请先启动服务${NC}"
        echo ""
        echo -e "${CYAN}→ 正在为您启动服务...${NC}"
        ./start.sh
        return 0
    fi
    
    echo -e "${YELLOW}⏳ 正在快速重启服务...${NC}"
    echo ""
    
    # 使用 restart 命令快速重启
    $COMPOSE_CMD -f docker-compose.clean.yml restart
    
    echo ""
    echo -e "${GREEN}✅ 服务已重启${NC}"
    echo ""
    echo -e "${BLUE}📍 访问地址:${NC}"
    echo -e "  ${CYAN}├─${NC} API 服务：   http://localhost:18080"
    echo -e "  ${CYAN}└─${NC} 管理后台： http://localhost:18501"
    echo ""
    
    # 等待服务就绪
    echo -e "${YELLOW}⏳ 等待服务就绪...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:18080/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务已就绪！${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️  服务启动中，请稍后访问...${NC}"
        fi
        sleep 1
    done
}

# 主流程
main() {
    print_header
    check_docker_compose
    restart_services
}

main
