#!/bin/bash

# Union AI API - 一键启动脚本
# 此脚本会检查 Docker、创建数据目录、构建并启动服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="union-ai-api"
DATA_DIR="$SCRIPT_DIR/data"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Union AI API - 一键启动脚本                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Docker 是否安装
check_docker() {
    echo -e "${YELLOW}[1/5] 检查 Docker 安装...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装！${NC}"
        echo ""
        echo "请先安装 Docker Desktop："
        echo "  macOS: https://docs.docker.com/desktop/install/mac-install/"
        echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
        echo "  Linux: https://docs.docker.com/desktop/install/linux-install/"
        exit 1
    fi
    
    if ! docker --version &> /dev/null; then
        echo -e "${RED}❌ Docker 未运行！${NC}"
        echo "请启动 Docker Desktop 应用"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker 已安装：$(docker --version)${NC}"
}

# 检查 docker-compose
check_docker_compose() {
    echo -e "${YELLOW}[2/5] 检查 Docker Compose...${NC}"
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo -e "${RED}❌ Docker Compose 未安装！${NC}"
        echo "请安装 Docker Compose"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker Compose 已就绪${NC}"
}

# 创建数据目录
create_data_dir() {
    echo -e "${YELLOW}[3/5] 创建数据目录...${NC}"
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR"
        echo -e "${GREEN}✓ 创建数据目录：$DATA_DIR${NC}"
    else
        echo -e "${GREEN}✓ 数据目录已存在：$DATA_DIR${NC}"
    fi
    
    # 检查目录是否可写
    if [ ! -w "$DATA_DIR" ]; then
        echo -e "${RED}⚠️  数据目录不可写，尝试修复权限...${NC}"
        chmod 755 "$DATA_DIR"
    fi
}

# 构建 Docker 镜像
build_image() {
    echo -e "${YELLOW}[4/5] 构建 Docker 镜像...${NC}"
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD -f docker-compose.clean.yml build --no-cache
    echo -e "${GREEN}✓ Docker 镜像构建完成${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}[5/5] 启动服务...${NC}"
    cd "$SCRIPT_DIR"
    $COMPOSE_CMD -f docker-compose.clean.yml up -d
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              🎉 服务启动成功！                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📍 服务信息:${NC}"
    echo "  └─ API 服务：http://localhost:18080"
    echo "  └─ 管理后台：http://localhost:18501"
    echo ""
    echo -e "${BLUE}📂 数据存储:${NC}"
    echo "  └─ $DATA_DIR"
    echo ""
    echo -e "${YELLOW}💡 常用命令:${NC}"
    echo "  查看日志：docker logs -f union-ai-api"
    echo "  停止服务：./stop.sh"
    echo "  重启服务：./restart.sh"
    echo "  查看状态：./status.sh"
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
    check_docker
    check_docker_compose
    create_data_dir
    build_image
    start_services
}

# 执行主流程
main
