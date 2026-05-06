import sys

import requests
from file_api.utils import get_api, TYPE_TOKEN_ERROR_HINT


def list_entries(repo, dir_path: str) -> list[dict]:
    return repo.list_dir(dir_path)


def format_size(size: int) -> str:
    """将字节数格式化为可读大小"""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def print_entries(entries: list[dict]):
    """打印目录条目"""
    if not entries:
        print("（空目录）")
        return

    print(f"{'类型':<6} {'大小':<10} {'名称':<30}")
    print("-" * 60)
    for entry in entries:
        typ = "📁" if entry["type"] == "dir" else "📄"
        name = entry["name"]
        if typ == "📁":
            name += "/"
            size_str = "-"
        else:
            size_str = format_size(entry.get("size", 0))
        print(f"{typ:<6} {size_str:<10} {name:<30}")


def _print_token_error():
    print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")


def main():
    # 从命令行参数或交互式输入获取目标目录
    if len(sys.argv) > 1:
        dir_path = sys.argv[1]
    else:
        dir_path = input("请输入目标目录路径 (默认: /): ").strip() or "/"

    print(f"\n正在获取目录: {dir_path}\n")

    repo = get_api()
    try:
        entries = list_entries(repo, dir_path)
        print_entries(entries)
    except requests.exceptions.InvalidSchema:
        _print_token_error()
        sys.exit(1)


if __name__ == "__main__":
    main()
