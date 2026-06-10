#!/bin/bash

# 飞书发送消息脚本
# 用法: ./send-message.sh --chat_id <群聊ID> --title <标题> --content <内容>

# 应用凭证（当前使用飞书插件配置的应用）
APP_ID="cli_a93aa1cc63389cee"
APP_SECRET="KOIpik0vS2wOJIBKyIwtTdIoKBB4sXNp"

# API 地址
TOKEN_URL="https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
MESSAGE_URL="https://open.feishu.cn/open-apis/im/v1/messages"

# 解析参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --chat_id)
      CHAT_ID="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --content)
      CONTENT="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      exit 1
      ;;
  esac
done

# 检查必要参数
if [ -z "$CHAT_ID" ] || [ -z "$TITLE" ] || [ -z "$CONTENT" ]; then
  echo "错误: 缺少必要参数"
  echo "用法: ./send-message.sh --chat_id <群聊ID> --title <标题> --content <内容>"
  exit 1
fi

# 获取 tenant_access_token
TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_URL" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\": \"$APP_ID\", \"app_secret\": \"$APP_SECRET\"}")

TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.tenant_access_token // empty')

if [ -z "$TOKEN" ]; then
  echo "获取访问令牌失败: $TOKEN_RESPONSE"
  exit 1
fi

# 发送消息
# 判断是群聊还是用户
if [[ "$CHAT_ID" == oc_* ]]; then
  RECEIVE_ID_TYPE="chat_id"
elif [[ "$CHAT_ID" == ou_* ]]; then
  RECEIVE_ID_TYPE="open_id"
else
  echo "错误: chat_id 必须是 oc_xxx (群聊) 或 ou_xxx (用户)"
  exit 1
fi

# 使用 jq 构建完整请求
REQUEST_BODY=$(jq -n \
  --arg chat_id "$CHAT_ID" \
  --arg title "$TITLE" \
  --arg content "$CONTENT" \
  '{
    receive_id: $chat_id,
    msg_type: "interactive",
    content: ({
      config: { wide_screen_mode: true },
      header: {
        title: { content: $title, tag: "plain_text" },
        template: "blue"
      },
      elements: [
        { tag: "markdown", content: $content }
      ]
    } | tostring)
  }')

MESSAGE_RESPONSE=$(curl -s -X POST "$MESSAGE_URL?receive_id_type=$RECEIVE_ID_TYPE" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_BODY")

# 检查结果
CODE=$(echo "$MESSAGE_RESPONSE" | jq -r '.code // 1')

if [ "$CODE" -eq 0 ]; then
  MESSAGE_ID=$(echo "$MESSAGE_RESPONSE" | jq -r '.data.message_id // empty')
  echo "消息发送成功! message_id: $MESSAGE_ID"
  exit 0
else
  MSG=$(echo "$MESSAGE_RESPONSE" | jq -r '.msg // "未知错误"')
  echo "消息发送失败: $MSG (code: $CODE)"
  exit 1
fi
