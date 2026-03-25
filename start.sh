#!/bin/bash

# Union AI API - 快速启动脚本
# 此脚本会检查 Docker、创建数据目录、启动服务（首次会自动构建）
# 特点：非首次启动秒开，不会重复构建镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="union-ai-api"
DATA_DIR="$SCRIPT_DIR/data"

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
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       Union AI API - 快速启动脚本                     ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查 Docker 是否安装
check_docker() {
    echo -e "${YELLOW}[1/4] 检查 Docker 安装...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装！${NC}"
        echo ""
        echo "请先安装 Docker Desktop："
        echo "  macOS: https://docs.docker.com/desktop/install/mac-install/"
        echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
        echo "  Linux: https://docs.docker.com/desktop/install/linux-install/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker 未运行！${NC}"
        echo "请启动 Docker Desktop 应用"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker 已就绪：$(docker --version | cut -d' ' -f3 | tr -d ',')${NC}"
}

# 检查 Docker Compose
check_docker_compose() {
    echo -e "${YELLOW}[2/4] 检查 Docker Compose...${NC}"
    if [ -z "$COMPOSE_CMD" ]; then
        echo -e "${RED}❌ Docker Compose 未安装！${NC}"
        echo "请安装 Docker Compose"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker Compose 已就绪${NC}"
}

# 创建数据目录
create_data_dir() {
    echo -e "${YELLOW}[3/4] 检查数据目录...${NC}"
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR"
        echo -e "${GREEN}✓ 创建数据目录：$DATA_DIR${NC}"
    else
        echo -e "${GREEN}✓ 数据目录已存在${NC}"
    fi
    
    # 检查目录是否可写
    if [ ! -w "$DATA_DIR" ]; then
        echo -e "${YELLOW}⚠️  数据目录不可写，修复权限...${NC}"
        chmod 755 "$DATA_DIR"
    fi
}

# 检查容器是否存在
check_container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${PROJECT_NAME}$"
}

# 检查容器是否正在运行
check_container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${PROJECT_NAME}$"
}

# 检查镜像是否存在
check_image_exists() {
    docker images --format '{{.Repository}}' | grep -q "^${PROJECT_NAME}$"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}[4/4] 启动服务...${NC}"
    cd "$SCRIPT_DIR"
    
    # 检查容器状态
    if check_container_running; then
        echo -e "${GREEN}✓ 服务已经在运行中${NC}"
        show_status
        return 0
    fi
    
    # 如果容器存在但已停止，直接启动（秒开）
    if check_container_exists; then
        echo -e "${CYAN}→ 检测到已停止的容器，正在快速启动...${NC}"
        $COMPOSE_CMD -f docker-compose.clean.yml start
        echo -e "${GREEN}✓ 服务已快速启动${NC}"
    else
        # 容器不存在，需要创建
        if check_image_exists; then
            echo -e "${CYAN}→ 使用已有镜像启动服务...${NC}"
        else
            echo -e "${CYAN}→ 首次启动，需要构建镜像（请稍候）...${NC}"
        fi
        $COMPOSE_CMD -f docker-compose.clean.yml up -d
        echo -e "${GREEN}✓ 服务已启动${NC}"
    fi
    
    show_status
}

# 显示状态
show_status() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              🎉 服务启动成功！                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 访问地址:${NC}"
    echo -e "  ${CYAN}├─${NC} API 服务：   http://localhost:18080"
    echo -e "  ${CYAN}└─${NC} 管理后台： http://localhost:18501"
    echo ""
    echo -e "${BLUE}📂 数据目录:${NC} $DATA_DIR"
    echo ""
    echo -e "${YELLOW}💡 常用命令:${NC}"
    echo -e "  ${CYAN}•${NC} 查看日志：docker logs -f union-ai-api"
    echo -e "  ${CYAN}•${NC} 停止服务：./stop.sh"
    echo -e "  ${CYAN}•${NC} 重启服务：./restart.sh"
    echo -e "  ${CYAN}•${NC} 查看状态：./status.sh"
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
    check_docker
    check_docker_compose
    create_data_dir
    start_services
}

# 执行主流程
main
