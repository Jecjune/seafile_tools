#!/bin/bash

# 交互式输入 BASE_URL
read -r -p "请输入 BASE_URL(如: https://seafile.com): " BASE_URL
AUTH_URL="${BASE_URL}/api2/auth-token/"

echo "BASE_URL = ${BASE_URL}"
echo "AUTH_URL = ${AUTH_URL}"

# 交互式输入账号和密码
read -r -p "请输入账号 (邮箱/用户名): " USERNAME
read -r -s -p "请输入密码: " PASSWORD
echo ""  # 换行

echo "正在请求 token ..."

# 发送请求获取 token
response=$(curl -s -w "\n%{http_code}" \
    -X POST "${AUTH_URL}" \
    -d "username=${USERNAME}" \
    -d "password=${PASSWORD}" \
    -H "Referer: ${BASE_URL}")

# 分离响应体和状态码
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

echo "HTTP 状态码: ${http_code}"

if [ "$http_code" = "200" ]; then
    token=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)
    if [ -n "$token" ]; then
        echo "您的 API Token 是: ${token}"
    else
        echo "获取 token 失败，响应内容："
        echo "$body"
    fi
else
    echo "请求失败，状态码: ${http_code}"
    echo "响应内容:"
    echo "$body"
fi
