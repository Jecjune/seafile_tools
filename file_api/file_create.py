import sys

import requests
from file_api.utils import get_api, TYPE_TOKEN_ERROR_HINT


try:
    repo = get_api()

    # 确保目标目录存在
    dir_path = "/test_files"
    try:
        result = repo.create_dir(dir_path)
        print(f"目录创建成功: {result}")
    except Exception as e:
        print(f"目录可能已存在: {e}")

    # 创建文件
    file_path = "/test_files/demo.txt"
    result = repo.create_file(file_path)
    print(f"文件创建成功: {result}")
except requests.exceptions.InvalidSchema:
    print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
    sys.exit(1)
except Exception as e:
    if "Token inactive" in str(e) or "not found" in str(e):
        print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
        sys.exit(1)
    raise
