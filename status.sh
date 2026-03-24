#!/bin/bash

# Union AI API - 状态检查脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Union AI API - 服务状态                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查容器状态
if docker ps | grep -q "union-ai-api"; then
    echo -e "${GREEN}✓ 容器状态：运行中${NC}"
    
    # 检查 API 服务
    if curl -s http://localhost:18080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API 服务 (18080): 正常${NC}"
    else
        echo -e "${RED}✗ API 服务 (18080): 异常${NC}"
    fi
    
    # 检查管理后台
    if curl -s http://localhost:18501 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 管理后台 (18501): 正常${NC}"
    else
        echo -e "${YELLOW}⚠ 管理后台 (18501): 启动中${NC}"
    fi
    
    echo ""
    echo "访问地址："
    echo "  └─ API 服务：http://localhost:18080"
    echo "  └─ 管理后台：http://localhost:18501"
    echo ""
    echo "查看日志：docker logs -f union-ai-api"
    
else
    echo -e "${RED}✗ 容器状态：未运行${NC}"
    echo ""
    echo "启动服务：./start.sh"
fi
