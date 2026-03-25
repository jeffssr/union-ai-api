#!/bin/bash

# Union AI API - 完全清理脚本
# 此脚本会停止并删除容器、删除镜像，但保留数据
# 用于完全重置环境或释放磁盘空间

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

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
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║       Union AI API - 完全清理脚本                     ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查 Docker Compose
check_docker_compose() {
    if [ -z "$COMPOSE_CMD" ]; then
        echo -e "${RED}❌ Docker Compose 未安装！${NC}"
        exit 1
    fi
}

# 确认操作
confirm_cleanup() {
    echo -e "${YELLOW}⚠️  警告：此操作将执行以下清理：${NC}"
    echo ""
    echo -e "  ${RED}•${NC} 停止并删除容器"
    echo -e "  ${RED}•${NC} 删除 Docker 镜像"
    echo -e "  ${RED}•${NC} 删除 Docker 网络"
    echo ""
    echo -e "  ${GREEN}✓${NC} 数据目录将保留：$DATA_DIR"
    echo ""
    echo -e "${CYAN}💡 提示：${NC}"
    echo "  如果只想停止服务而不删除容器，请使用 ./stop.sh"
    echo "  这样下次启动时可以秒开。"
    echo ""
    
    read -p "确定要继续清理吗？(y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}操作已取消${NC}"
        exit 0
    fi
}

# 执行清理
do_cleanup() {
    cd "$SCRIPT_DIR"
    
    echo ""
    echo -e "${YELLOW}⏳ 正在清理...${NC}"
    echo ""
    
    # 停止并删除容器
    echo -e "${BLUE}1. 停止并删除容器...${NC}"
    $COMPOSE_CMD -f docker-compose.clean.yml down 2>/dev/null || true
    docker rm -f "$PROJECT_NAME" 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 容器已删除"
    
    # 删除镜像
    echo -e "${BLUE}2. 删除镜像...${NC}"
    local images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^$PROJECT_NAME" 2>/dev/null || true)
    if [ -n "$images" ]; then
        echo "$images" | xargs -r docker rmi -f 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} 镜像已删除"
    else
        echo -e "  ${GRAY}  无镜像需要删除${NC}"
    fi
    
    # 清理悬空镜像
    echo -e "${BLUE}3. 清理悬空镜像...${NC}"
    docker image prune -f 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 悬空镜像已清理"
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✅ 清理完成！                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📋 清理结果:${NC}"
    echo -e "  ${GREEN}✓${NC} 容器已删除"
    echo -e "  ${GREEN}✓${NC} 镜像已删除"
    echo -e "  ${GREEN}✓${NC} 网络已删除"
    echo ""
    echo -e "${BLUE}💾 数据状态:${NC}"
    if [ -d "$DATA_DIR" ]; then
        local size=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
        echo -e "  ${GREEN}✓${NC} 数据目录已保留：$DATA_DIR ($size)"
    fi
    echo ""
    echo -e "${YELLOW}💡 如需重新启动:${NC}"
    echo -e "  ${CYAN}./start.sh${NC}（会重新构建镜像并启动）"
    echo ""
}

# 主流程
main() {
    print_header
    check_docker_compose
    confirm_cleanup
    do_cleanup
}

main
