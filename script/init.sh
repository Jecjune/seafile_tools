#!/bin/bash

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_OUTPUT=$(mktemp)

# 调用 get_user_api_token.sh，输出同时显示在终端和写入临时文件
stdbuf -oL bash "${SCRIPT_DIR}/get_user_api_token.sh" | tee "$TMP_OUTPUT"

# 从输出中提取 BASE_URL
BASE_URL=$(sed -n 's/^BASE_URL = //p' "$TMP_OUTPUT")

# 从输出中提取 API Token（如果存在）
API_TOKEN=$(sed -n 's/^您的 API Token 是: //p' "$TMP_OUTPUT")

rm -f "$TMP_OUTPUT"

if [ -z "$BASE_URL" ]; then
    echo "[ERROR] 未能获取到 BASE_URL"
    exit 1
fi

JSON_FILE="${SCRIPT_DIR}/config.json"

if [ -n "$API_TOKEN" ]; then
    echo ""
    echo "⚠️  注意：API Token 将以明文形式写入到 ${JSON_FILE}"
    echo "如果您的环境足够安全，建议写入 API Token以避免每次执行程序的token输入步骤。"
    echo "您也可以选择稍后再手动该删除config.json文件，然后每次执行程序前再重新运行这个脚本。"
    read -r -p "是否继续写入 API Token？(Y/n): " CONFIRM

    case "$CONFIRM" in
        [Yy]|"")
            cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}",
  "api_token": "${API_TOKEN}"
}
EOF
            echo "[OK] 已写入 ${JSON_FILE}（包含 BASE_URL 和 API Token）"
            ;;
        *)
            cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}"
}
EOF
            echo "[OK] 已写入 ${JSON_FILE}（仅包含 BASE_URL）"
            ;;
    esac
else
    cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}"
}
EOF
    echo "[OK] 已写入 ${JSON_FILE}（仅包含 BASE_URL，未获取到 API Token）"
fi
