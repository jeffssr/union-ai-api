#!/bin/bash

# Union AI API - 服务状态检查脚本
# 显示容器、服务、端口等详细状态信息

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

# 打印标题
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          Union AI API - 服务状态检查                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查 Docker 状态
check_docker() {
    echo -e "${YELLOW}🔍 Docker 状态${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "  ${RED}✗${NC} Docker 未安装"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "  ${RED}✗${NC} Docker 未运行"
        return 1
    fi
    
    local docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "  ${GREEN}✓${NC} Docker 版本：$docker_version"
    
    # 检查 Docker Compose
    if command -v docker-compose &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker Compose：$(docker-compose --version | cut -d' ' -f3 | tr -d ',')"
    elif docker compose version &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker Compose：$(docker compose version --short)"
    else
        echo -e "  ${RED}✗${NC} Docker Compose 未安装"
    fi
    echo ""
}

# 检查容器状态
check_container() {
    echo -e "${YELLOW}📦 容器状态${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────${NC}"
    
    local container_info=$(docker ps -a --filter "name=$PROJECT_NAME" --format "{{.Status}}|{{.CreatedAt}}|{{.Ports}}" 2>/dev/null)
    
    if [ -z "$container_info" ]; then
        echo -e "  ${YELLOW}⚠${NC} 容器未创建"
        echo ""
        echo -e "  ${CYAN}→ 启动命令：./start.sh${NC}"
        return 1
    fi
    
    local status=$(echo "$container_info" | cut -d'|' -f1)
    local created=$(echo "$container_info" | cut -d'|' -f2)
    local ports=$(echo "$container_info" | cut -d'|' -f3)
    
    if echo "$status" | grep -q "Up"; then
        echo -e "  ${GREEN}✓${NC} 状态：运行中"
        echo -e "  ${GREEN}✓${NC} 创建时间：$created"
    elif echo "$status" | grep -q "Exited"; then
        echo -e "  ${YELLOW}⚠${NC} 状态：已停止"
        echo -e "  ${GRAY}  ${NC} 创建时间：$created"
        echo ""
        echo -e "  ${CYAN}→ 启动命令：./start.sh（秒开）${NC}"
    else
        echo -e "  ${YELLOW}⚠${NC} 状态：$status"
    fi
    
    if [ -n "$ports" ]; then
        echo -e "  ${BLUE}ℹ${NC} 端口映射："
        echo "$ports" | tr ',' '\n' | while read -r port; do
            echo -e "      ${CYAN}•${NC} $port"
        done
    fi
    echo ""
}

# 检查服务状态
check_services() {
    echo -e "${YELLOW}🌐 服务状态${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────${NC}"
    
    # 检查 API 服务
    if curl -s http://localhost:18080/health > /dev/null 2>&1; then
        local health=$(curl -s http://localhost:18080/health 2>/dev/null)
        echo -e "  ${GREEN}✓${NC} API 服务 (18080)：正常"
        echo -e "    ${GRAY}└─ 健康检查：$health${NC}"
        echo -e "    ${GRAY}└─ 地址：http://localhost:18080${NC}"
    else
        echo -e "  ${RED}✗${NC} API 服务 (18080)：未响应"
        echo -e "    ${GRAY}└─ 地址：http://localhost:18080${NC}"
    fi
    
    # 检查管理后台
    if curl -s http://localhost:18501 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} 管理后台 (18501)：正常"
        echo -e "    ${GRAY}└─ 地址：http://localhost:18501${NC}"
    else
        echo -e "  ${YELLOW}⚠${NC} 管理后台 (18501)：未就绪"
        echo -e "    ${GRAY}└─ 地址：http://localhost:18501${NC}"
    fi
    echo ""
}

# 检查数据目录
check_data() {
    echo -e "${YELLOW}💾 数据存储${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────${NC}"
    
    if [ -d "$DATA_DIR" ]; then
        local size=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
        local file_count=$(find "$DATA_DIR" -type f 2>/dev/null | wc -l)
        echo -e "  ${GREEN}✓${NC} 数据目录：$DATA_DIR"
        echo -e "  ${GREEN}✓${NC} 占用空间：$size"
        echo -e "  ${GREEN}✓${NC} 文件数量：$file_count"
        
        if [ -f "$DATA_DIR/proxy.db" ]; then
            local db_size=$(ls -lh "$DATA_DIR/proxy.db" 2>/dev/null | awk '{print $5}')
            echo -e "  ${GREEN}✓${NC} 数据库文件：proxy.db ($db_size)"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} 数据目录不存在"
        echo -e "    ${GRAY}└─ 路径：$DATA_DIR${NC}"
    fi
    echo ""
}

# 检查镜像
check_image() {
    echo -e "${YELLOW}🖼️  镜像状态${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────${NC}"
    
    local image_info=$(docker images --format "{{.Repository}}|{{.Tag}}|{{.Size}}|{{.CreatedAt}}" | grep "^$PROJECT_NAME" 2>/dev/null)
    
    if [ -n "$image_info" ]; then
        local tag=$(echo "$image_info" | cut -d'|' -f2)
        local size=$(echo "$image_info" | cut -d'|' -f3)
        local created=$(echo "$image_info" | cut -d'|' -f4)
        echo -e "  ${GREEN}✓${NC} 镜像：$PROJECT_NAME:$tag"
        echo -e "  ${GREEN}✓${NC} 大小：$size"
        echo -e "  ${GREEN}✓${NC} 创建时间：$created"
    else
        echo -e "  ${YELLOW}⚠${NC} 镜像未构建"
        echo -e "    ${CYAN}└─ 首次启动时会自动构建${NC}"
    fi
    echo ""
}

# 显示快捷命令
show_commands() {
    echo -e "${YELLOW}💡 快捷命令${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────${NC}"
    echo -e "  ${CYAN}./start.sh${NC}    启动服务（首次构建，后续秒开）"
    echo -e "  ${CYAN}./stop.sh${NC}     停止服务（保留容器，快速重启）"
    echo -e "  ${CYAN}./restart.sh${NC}  重启服务"
    echo -e "  ${CYAN}./status.sh${NC}   查看状态"
    echo -e "  ${CYAN}./clean.sh${NC}    完全清理（删除容器和镜像）"
    echo -e "  ${CYAN}docker logs -f $PROJECT_NAME${NC}  查看实时日志"
    echo ""
}

# 主流程
main() {
    print_header
    check_docker
    check_container
    check_services
    check_data
    check_image
    show_commands
}

main
