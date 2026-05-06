import os
import sys
from pathlib import Path

import requests
from file_api.utils import get_api, TYPE_TOKEN_ERROR_HINT


def ensure_dir(repo, dir_path: str) -> bool:
    """在 Seafile 上创建目录（如果不存在）。"""
    if dir_path in ("", "/"):
        return True  # 根目录始终存在
    try:
        repo.create_dir(dir_path)
        return True
    except requests.exceptions.InvalidSchema:
        print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
        sys.exit(1)
    except Exception as e:
        print(f"  ⚠ 目录创建失败: {dir_path} ({e})")
        return False


def upload_folder(local_folder: str, seafile_root: str) -> dict:
    """
    递归上传本地文件夹到 Seafile。

    返回统计信息：{ uploaded: int, skipped: int, failed: int }
    """
    repo = get_api()

    local_folder = os.path.abspath(local_folder)
    folder_name = os.path.basename(local_folder)
    stats = {"uploaded": 0, "skipped": 0, "failed": 0}

    if not ensure_dir(repo, seafile_root):
        print(f"[ERROR] 无法创建根目录 {seafile_root}，终止上传")
        return stats

    for current_dir, subdirs, files in os.walk(local_folder):
        rel_path = os.path.relpath(current_dir, local_folder)
        if rel_path == ".":
            target_dir = f"{seafile_root}/{folder_name}"
        else:
            target_dir = f"{seafile_root}/{folder_name}/{rel_path}"
        target_dir = target_dir.replace("\\", "/").replace("//", "/")

        dir_ready = ensure_dir(repo, target_dir)

        if not dir_ready:
            for file_name in files:
                print(f"  ✗ {target_dir}/{file_name} （目录不存在，跳过）")
                stats["failed"] += 1
            continue

        # 上传文件
        for file_name in files:
            local_path = os.path.join(current_dir, file_name)
            try:
                repo.upload_file(target_dir, local_path)
                print(f"  ✓ {target_dir}/{file_name}")
                stats["uploaded"] += 1
            except requests.exceptions.InvalidSchema:
                print(f"  ✗ {target_dir}/{file_name}")
                print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
                return stats
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  - {target_dir}/{file_name} （已存在，跳过）")
                    stats["skipped"] += 1
                else:
                    print(f"  ✗ {target_dir}/{file_name}  ({e})")
                    stats["failed"] += 1

    return stats


def main():
    # 获取本地文件夹路径
    if len(sys.argv) > 1:
        local_path = sys.argv[1]
    else:
        local_path = input("请输入要上传的本地文件夹路径: ").strip()

    if not os.path.isdir(local_path):
        print(f"[ERROR] 文件夹不存在: {local_path}")
        sys.exit(1)

    # 获取 Seafile 目标根目录
    if len(sys.argv) > 2:
        seafile_root = sys.argv[2]
    else:
        folder_name = os.path.basename(os.path.abspath(local_path))
        seafile_root = input(f"请输入 Seafile 目标目录 (默认: /{folder_name}): ").strip()
        if not seafile_root:
            seafile_root = f"/{folder_name}"

    print(f"\n上传文件夹: {local_path}")
    print(f"目标目录:   {seafile_root}\n")

    stats = upload_folder(local_path, seafile_root)

    print(f"\n{'='*40}")
    parts = [f"上传完成: {stats['uploaded']} 个文件已上传"]
    if stats["skipped"]:
        parts.append(f"{stats['skipped']} 个已跳过")
    if stats["failed"]:
        parts.append(f"{stats['failed']} 个失败")
    print(", ".join(parts))
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
