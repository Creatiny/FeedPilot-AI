#!/bin/bash
# FeedSales AI Telegram 真实测试
# 发送 105 条测试用例，记录发送时间

BOT_TOKEN="8154564272:AAEbMYfLaEZ8VRdJV1kK9Y58lpCfjx2Ol5U"
CHAT_ID="7972653610"
LOG_FILE="/home/kenny/.openclaw/workspace/feed-sales-ai-mvp/tests/telegram_test_results.log"

# 清空日志
echo "=== FeedSales AI Telegram Test Results ===" > "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

send_message() {
    local msg="$1"
    local result=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="$CHAT_ID" \
        -d text="$msg" \
        -d parse_mode="HTML")
    
    local success=$(echo "$result" | jq -r '.ok')
    local msg_id=$(echo "$result" | jq -r '.result.message_id')
    
    if [ "$success" = "true" ]; then
        echo "✅ Sent: $msg (msg_id: $msg_id)" >> "$LOG_FILE"
    else
        echo "❌ Failed: $msg - $(echo "$result" | jq -r '.description')" >> "$LOG_FILE"
    fi
    
    echo "$msg_id"
}

# 测试用例数组
TEST_CASES=(
    # Formula Cost (38)
    "Nursery Diet 1成本"
    "Beef Cattle Finisher cost"
    "Broiler Starter formula price"
    "Layer Diet cost per ton"
    "Grower Diet 1多少钱"
    "Finishing pig feed cost"
    "Gestating Sow Diet price"
    "Lactating sow diet cost"
    "Dairy Calf Starter cost"
    "Heifer grower feed price"
    "Turkey Starter diet cost"
    "Lamb starter feed price"
    "Goat kid starter cost"
    "Duck starter feed price"
    "Cat Food Adult price"
    "Dog Food Adult cost"
    "Trout Starter feed cost"
    "Catfish Grower price"
    "Beef Cattle Starter cost"
    "Beef Cattle Grower price"
    "Dairy Heifer Grower cost"
    "Lactating Cow Diet price"
    "Broiler Grower cost"
    "Broiler Finisher price"
    "Layer Starter cost"
    "Layer Grower price"
    "Turkey Grower cost"
    "Turkey Finisher price"
    "Lamb Finisher cost"
    "Ewe Gestating price"
    "Ewe Lactating cost"
    "Goat Doe Gestating price"
    "Goat Doe Lactating cost"
    "Duck Grower price"
    "Duck Breeder cost"
    "Trout Grower price"
    
    # Ingredient Price (21)
    "corn price today"
    "soybean meal price"
    "wheat price per ton"
    "fish meal cost"
    "DDGS price"
    "limestone price"
    "salt price"
    "premix for swine price"
    "alfalfa hay price"
    "corn silage price"
    "molasses price"
    "dicalcium phosphate price"
    "L-Lysine price"
    "barley price"
    "canola meal price"
    "cottonseed meal cost"
    "grass hay price"
    "rice price"
    "show all ingredient prices"
    
    # Nutrition (10)
    "protein content in Nursery Diet 1"
    "calcium level in Broiler Starter"
    "phosphorus in Grower Diet"
    "analyze Layer Diet nutrition"
    "compare NRC standards for swine"
    "lysine content in sow feed"
    "nutrition profile for trout"
    "energy level in beef cattle feed"
    "which formula has highest protein"
    "analyze all swine formulas nutrition"
    
    # Customer (8)
    "add customer Test User 1, pig farmer"
    "add customer Test User 2, cattle rancher"
    "show all my customers"
    "find customer Test"
    "update customer Test User 1 phone 555-0001"
    "which customers raise pigs"
    "delete customer Test User 2"
    "how many customers do I have"
    
    # Reminder (6)
    "remind me to check corn price tomorrow"
    "alert when soybean meal drops below 300"
    "weekly cost report every Monday"
    "notify when nursery feed exceeds 280"
    "reminder for customer delivery"
    "show all my reminders"
    
    # Language modes (12)
    "保育料1号成本"
    "玉米今天价格"
    "Nursery Diet 1 成本是多少"
    "Soybean meal 今天价格"
    "cost of Nursery Diet 1"
    "today corn price"
    
    # Error handling (10)
    "cost of Unknown Formula XYZ"
    "price of imaginary ingredient"
    "calculate cost"
    "add customer"
    "remind me"
    "show customer Nonexistent"
    "delete formula Nursery Diet 1"
    "update price corn to 0"
    "feed cost for dinosaur"
    "what is the price"
)

total=${#TEST_CASES[@]}
passed=0
failed=0

echo "Sending $total test messages..." 
echo ""

for i in "${!TEST_CASES[@]}"; do
    msg="${TEST_CASES[$i]}"
    msg_num=$((i+1))
    
    printf "[%3d/%3d] Sending: %s\n" "$msg_num" "$total" "${msg:0:40}..."
    
    msg_id=$(send_message "$msg")
    
    if [ -n "$msg_id" ] && [ "$msg_id" != "null" ]; then
        passed=$((passed+1))
    else
        failed=$((failed+1))
    fi
    
    # 等待避免速率限制
    sleep 2
done

echo "" >> "$LOG_FILE"
echo "=== Summary ===" >> "$LOG_FILE"
echo "Total: $total" >> "$LOG_FILE"
echo "Sent: $passed" >> "$LOG_FILE"
echo "Failed: $failed" >> "$LOG_FILE"
echo "Completed: $(date)" >> "$LOG_FILE"

echo ""
echo "=== Test Complete ==="
echo "Total messages: $total"
echo "Successfully sent: $passed"
echo "Failed: $failed"
echo ""
echo "Results logged to: $LOG_FILE"
echo "Check Telegram for OpenClaw responses"