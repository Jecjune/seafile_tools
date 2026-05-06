import os
import sys

import requests
from file_api.utils import get_api


def upload_file(repo, local_path: str, target_dir: str) -> dict:
    # 确保目标目录存在
    try:
        repo.create_dir(target_dir)
        print(f"目录已创建: {target_dir}")
    except Exception:
        pass  # 目录可能已存在

    print(f"正在上传: {local_path} -> {target_dir}")
    result = repo.upload_file(target_dir, local_path)
    return result


def main():
    # 获取本地文件路径
    if len(sys.argv) > 1:
        local_path = sys.argv[1]
    else:
        local_path = input("请输入要上传的本地文件路径: ").strip()

    if not os.path.isfile(local_path):
        print(f"[ERROR] 文件不存在: {local_path}")
        sys.exit(1)

    # 获取目标 Seafile 目录
    if len(sys.argv) > 2:
        target_dir = sys.argv[2]
    else:
        target_dir = input("请输入 Seafile 目标目录 (默认: /): ").strip() or "/"

    file_name = os.path.basename(local_path)
    file_size = os.path.getsize(local_path)
    print(f"\n文件: {file_name}  ({file_size} bytes)")

    repo = get_api()
    try:
        result = upload_file(repo, local_path, target_dir)
        print(f"上传成功: {result}")
    except requests.exceptions.InvalidSchema as e:
        err_msg = str(e)
        if "Token inactive" in err_msg or "Token" in err_msg:
            print()
            print("[ERROR] 可能使用了错误的 Token，请注意：")
            print("       仓库 Token 是一串 40 位的字母数字（如：d817af60...）")
            print("       不是用户 API Token，也不是仓库 ID（如：6f42c7e0-...）")
        else:
            print(f"[ERROR] 上传失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
