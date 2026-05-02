#!/bin/bash
#
# FeedSales Bot 用户授权脚本 (无需重启版)
#
# 用法: ./verify_invite_code.sh <telegram_user_id> <invite_code>
#
# 示例:
#   ./verify_invite_code.sh 123456789 FEED2024
#

set -e

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 配置
PAIRING_STORE="$PROJECT_ROOT/data/telegram-feedsales-allowFrom.json"
INVITE_CODES="FEED2024,SALES2024"  # 可配置多个，逗号分隔

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 参数检查
if [ $# -lt 2 ]; then
    echo -e "${RED}用法: $0 <telegram_user_id> <invite_code>${NC}"
    echo ""
    echo "当前有效测试码: ${INVITE_CODES//,/, }"
    echo ""
    echo "示例:"
    echo "  $0 123456789 FEED2024"
    exit 1
fi

USER_ID="$1"
CODE="$2"

# 验证测试码
if [[ ! ",$INVITE_CODES," =~ ",$CODE," ]]; then
    echo -e "${RED}❌ 测试码无效: $CODE${NC}"
    echo "有效测试码: ${INVITE_CODES//,/, }"
    exit 1
fi

echo -e "${YELLOW}验证测试码...${NC}"
echo -e "${GREEN}✓ 测试码正确${NC}"

# 创建 pairing store 目录
mkdir -p "$(dirname "$PAIRING_STORE")"

# 检查用户是否已授权
if [ -f "$PAIRING_STORE" ]; then
    if grep -q "$USER_ID" "$PAIRING_STORE" 2>/dev/null; then
        echo -e "${GREEN}✅ 用户 $USER_ID 已授权${NC}"
        exit 0
    fi
fi

# 添加用户到 pairing store（无需重启 Gateway）
echo -e "${YELLOW}添加用户到授权列表...${NC}"

# 创建或更新 JSON 文件
if [ -f "$PAIRING_STORE" ]; then
    # 使用 jq 添加用户（数字类型）
    if command -v jq &> /dev/null; then
        TMP_FILE=$(mktemp)
        jq --argjson user "$USER_ID" '. + [$user]' "$PAIRING_STORE" > "$TMP_FILE"
        mv "$TMP_FILE" "$PAIRING_STORE"
    else
        # 简单追加（如果最后一个字符是 ]）
        sed -i "s/]/, $USER_ID]/" "$PAIRING_STORE" 2>/dev/null || \
            echo "[$USER_ID]" > "$PAIRING_STORE"
    fi
else
    # 创建新文件
    echo "[$USER_ID]" > "$PAIRING_STORE"
fi

echo -e "${GREEN}✅ 用户 $USER_ID 已添加到授权列表${NC}"
echo ""
echo "用户现在可以使用 FeedSales Bot。"
echo "请让用户重新发送消息。"

# 记录授权日志
LOG_FILE="$PROJECT_ROOT/data/auth.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date '+%Y-%m-%d %H:%M:%S') | User: $USER_ID | Code: $CODE" >> "$LOG_FILE"

echo ""
echo "授权日志: $LOG_FILE"
