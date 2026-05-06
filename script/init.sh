#!/bin/bash

# 将写入token信息写入config.json文件中。
# 字段：base_url, api_token, token_type
# base_url: 必填，seafile的base_url
# api_token: seafile的api_token
# token_type: token的类型，0: 不提供默认token，1: 用户token，2: 仓库token

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JSON_FILE="${SCRIPT_DIR}/config.json"

# 如果 config.json 已存在，询问是否覆盖
if [ -f "$JSON_FILE" ]; then
    echo "检测到已存在配置文件: ${JSON_FILE}"
    read -r -p "是否覆盖重写？(y/N): " OVERWRITE
    case "$OVERWRITE" in
        [Yy])
            echo ""
            ;;
        *)
            echo "[SKIP] 保留现有配置文件"
            exit 0
            ;;
    esac
fi

echo "请选择 token 类型："
echo "  1) 用户 token — 使用账号密码登录获取，可访问整个账号下的仓库"
echo "  2) 仓库 token — 使用 Seafile 目录生成的专属 token，仅限该目录"
read -r -p "请输入选择 (1/2，默认 1): " TOKEN_TYPE
TOKEN_TYPE="${TOKEN_TYPE:-1}"

if [ "$TOKEN_TYPE" = "2" ]; then
    # --- 仓库 token 模式：直接输入 ---
    read -r -p "请输入 BASE_URL (如: https://seafile.com): " BASE_URL
    read -r -p "请输入仓库 API Token: " API_TOKEN

    if [ -z "$BASE_URL" ] || [ -z "$API_TOKEN" ]; then
        echo "[ERROR] BASE_URL 和 API Token 不能为空"
        exit 1
    fi

    echo ""
    echo "⚠️  注意：仓库 API Token 将以明文形式写入到 ${JSON_FILE}"
    echo "·如果您的环境足够安全，建议写入 Token 以避免每次执行程序时的 token 输入步骤"
    echo "·您可以在稍后手动删除 config.json 文件，每次执行程序前再重新运行这个脚本。"
    echo "·您也可以选择不写入 Token，每次执行程序前再手动输入。"
    read -r -p "是否继续写入 Token？(Y/n): " CONFIRM

    case "$CONFIRM" in
        [Yy]|"")
            cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}",
  "api_token": "${API_TOKEN}",
  "token_type": "repo"
}
EOF
            echo "[OK] 已写入 ${JSON_FILE}（包含 BASE_URL 和 API Token）"
            ;;
        *)
            cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}",
  "token_type": "0"
}
EOF
            echo "[OK] 已写入 ${JSON_FILE}（仅包含 BASE_URL）"
            ;;
    esac
else
    # --- 用户 token 模式：调用 get_user_api_token.sh ---
    TMP_OUTPUT=$(mktemp)

    # 调用 get_user_api_token.sh，输出同时显示在终端和写入临时文件
    stdbuf -oL bash "${SCRIPT_DIR}/get_user_api_token.sh" | tee "$TMP_OUTPUT"

    BASE_URL=$(sed -n 's/^BASE_URL = //p' "$TMP_OUTPUT")
    API_TOKEN=$(sed -n 's/^您的 API Token 是: //p' "$TMP_OUTPUT")

    rm -f "$TMP_OUTPUT"

    if [ -z "$BASE_URL" ]; then
        echo "[ERROR] 未能获取到 BASE_URL"
        exit 1
    fi

    if [ -n "$API_TOKEN" ]; then
        echo ""
        echo "⚠️  注意：API Token 将以明文形式写入到 ${JSON_FILE}"
        echo "·如果您的环境足够安全，建议写入 API Token 以避免每次执行程序的 token 输入步骤"
        echo "·您可以在稍后手动删除 config.json 文件，每次执行程序前再重新运行这个脚本。"
        echo "·您也可以选择不写入 API Token，每次执行程序前再手动输入。"
        read -r -p "是否继续写入 API Token？(Y/n): " CONFIRM

        case "$CONFIRM" in
            [Yy]|"")
                cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}",
  "api_token": "${API_TOKEN}",
  "token_type": "user"
}
EOF
                echo "[OK] 已写入 ${JSON_FILE}（包含 BASE_URL 和 API Token）"
                ;;
            *)
                cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}",
  "token_type": "none"
}
EOF
                echo "[OK] 已写入 ${JSON_FILE}（仅包含 BASE_URL）"
                ;;
        esac
    else
        cat > "$JSON_FILE" <<EOF
{
  "base_url": "${BASE_URL}",
  "token_type": "no"
}
EOF
        echo "[OK] 已写入 ${JSON_FILE}（仅包含 BASE_URL，未获取到 API Token）"
    fi
fi
