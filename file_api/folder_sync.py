import hashlib
import json
import os
import sys
from pathlib import Path

import requests
from file_api.utils import get_api, TYPE_TOKEN_ERROR_HINT

# 为减少api调用，第一次调用时会将已上传的文件路径缓存到本地，缓存路径为~/.cache/file_api_sync
# 使用--refresh参数时，会强制同步远程文件列表
CACHE_DIR = Path.home() / ".cache" / "file_api_sync"

def _cache_key(remote_root: str) -> str:
    """为远程根路径生成唯一的缓存文件名。"""
    digest = hashlib.sha256(remote_root.encode()).hexdigest()[:16]
    return f"{digest}.json"


def _cache_path(remote_root: str) -> Path:
    """获取缓存文件的完整路径。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / _cache_key(remote_root)


def _load_cache(remote_root: str) -> set | None:
    """从本地缓存加载已上传的文件路径集合。无缓存时返回 None。"""
    path = _cache_path(remote_root)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        stored_root = data.get("remote_root", "")
        if stored_root != remote_root:
            return None
        return set(data.get("entries", []))
    except (json.JSONDecodeError, KeyError):
        return None


def _save_cache(remote_root: str, entries: set):
    """保存已上传的文件路径到本地缓存。"""
    path = _cache_path(remote_root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"remote_root": remote_root, "entries": sorted(entries)},
            f,
            ensure_ascii=False,
            indent=2,
        )


def list_remote_tree(repo, dir_path: str) -> set:
    """递归列出网盘上指定目录下的所有文件和子目录，返回路径集合。"""
    entries_set = set()
    try:
        entries = repo.list_dir(dir_path)
    except requests.exceptions.InvalidSchema:
        print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
        sys.exit(1)
    except Exception as e:
        print(f"  ⚠ 无法列出目录 {dir_path}: {e}")
        return entries_set

    for entry in entries:
        name = entry["name"]
        full_path = f"{dir_path.rstrip('/')}/{name}"
        entries_set.add(full_path)
        if entry["type"] == "dir":
            entries_set.update(list_remote_tree(repo, full_path))

    return entries_set


def ensure_dir(repo, dir_path: str) -> bool:
    """在网盘上创建目录（如果不存在）。"""
    if dir_path in ("", "/"):
        return True
    try:
        repo.create_dir(dir_path)
        return True
    except requests.exceptions.InvalidSchema:
        print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
        sys.exit(1)
    except Exception:
        return False


def sync_folder(
    local_folder: str,
    seafile_root: str,
    force_refresh: bool = False,
) -> dict:
    """
    同步本地文件夹到网盘（带本地缓存）。

    首次运行（无缓存）或指定 --refresh 时：
        1. 从网盘递归拉取完整文件列表
        2. 写入本地缓存
        3. 对比本地，只上传缺失的文件

    后续运行（有缓存）：
        1. 直接读缓存，不上网盘拉取
        2. 对比本地，只上传新的文件
        3. 更新缓存

    返回 { uploaded: int, skipped: int, failed: int, from_cache: bool }
    """
    repo = get_api()

    local_folder = os.path.abspath(local_folder)
    folder_name = os.path.basename(local_folder)
    stats = {"uploaded": 0, "skipped": 0, "failed": 0, "from_cache": False}

    remote_root = f"{seafile_root.rstrip('/')}/{folder_name}"

    # ── 加载 / 构建远程文件列表 ──
    remote_entries = None
    if not force_refresh:
        remote_entries = _load_cache(remote_root)

    if remote_entries is not None:
        stats["from_cache"] = True
        print(f"\n✓ 使用本地缓存（{len(remote_entries)} 条记录，缓存路径: {_cache_path(remote_root)}）")
    else:
        print(f"\n正在从网盘拉取目录: {remote_root}")
        remote_entries = list_remote_tree(repo, remote_root)
        print(f"网盘上已有 {len(remote_entries)} 个条目")
        _save_cache(remote_root, remote_entries)

    print()

    # ── 确保目标根目录存在 ──
    if not ensure_dir(repo, seafile_root):
        print(f"[ERROR] 无法创建根目录 {seafile_root}，终止同步")
        return stats
    if not ensure_dir(repo, remote_root):
        print(f"[ERROR] 无法创建目标目录 {remote_root}，终止同步")
        return stats

    # ── 遍历本地文件夹，逐个对比 ──
    for current_dir, subdirs, files in os.walk(local_folder):
        rel_path = os.path.relpath(current_dir, local_folder)
        if rel_path == ".":
            target_dir = remote_root
        else:
            target_dir = f"{remote_root}/{rel_path}"
        target_dir = target_dir.replace("\\", "/").replace("//", "/")

        if target_dir != remote_root:
            ensure_dir(repo, target_dir)

        for file_name in files:
            remote_file_path = f"{target_dir}/{file_name}"

            if remote_file_path in remote_entries:
                print(f"  - {remote_file_path} （已存在，跳过）")
                stats["skipped"] += 1
                continue

            local_path = os.path.join(current_dir, file_name)
            try:
                repo.upload_file(target_dir, local_path)
                print(f"  ✓ {remote_file_path}")
                stats["uploaded"] += 1
                remote_entries.add(remote_file_path)
            except requests.exceptions.InvalidSchema:
                print(f"  ✗ {remote_file_path}")
                print(f"\n[ERROR] {TYPE_TOKEN_ERROR_HINT}")
                return stats
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  - {remote_file_path} （已存在，跳过）")
                    stats["skipped"] += 1
                    remote_entries.add(remote_file_path)
                else:
                    print(f"  ✗ {remote_file_path} ({e})")
                    stats["failed"] += 1

    # ── 更新缓存 ──
    _save_cache(remote_root, remote_entries)

    return stats


def _print_help():
    print(
        "用法: python -m file_api.folder_sync <本地文件夹> [网盘目标目录] [选项]\n"
        "\n"
        "选项:\n"
        "  --refresh     强制从网盘拉取目录列表（忽略本地缓存）\n"
        "  --no-cache    本次不同步缓存（不上传时也会跳过缓存保存）\n"
        "  --clear-cache 清除所有本地缓存后退出\n"
        "  -h, --help    显示帮助信息\n"
        "\n"
        f"缓存目录: {CACHE_DIR}"
    )


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        _print_help()
        return 0

    force_refresh = "--refresh" in sys.argv
    no_cache = "--no-cache" in sys.argv
    clear_cache = "--clear-cache" in sys.argv

    # 过滤掉选项参数，剩下的作为位置参数
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if clear_cache:
        if CACHE_DIR.exists():
            cache_files = sorted(CACHE_DIR.glob("*.json"))
            if not cache_files:
                print(f"缓存目录为空: {CACHE_DIR}")
            else:
                for f in cache_files:
                    f.unlink()
                    print(f"  ✓ 已删除: {f}")
                print(f"\n共清除 {len(cache_files)} 个缓存文件")
        else:
            print(f"缓存目录不存在: {CACHE_DIR}")
        return 0

    # 获取本地文件夹路径
    if len(args) > 0:
        local_path = args[0]
    else:
        local_path = input("请输入要同步的本地文件夹路径: ").strip()

    if not os.path.isdir(local_path):
        print(f"[ERROR] 文件夹不存在: {local_path}")
        sys.exit(1)

    # 获取网盘目标根目录
    if len(args) > 1:
        seafile_root = args[1]
    else:
        folder_name = os.path.basename(os.path.abspath(local_path))
        seafile_root = input(f"请输入网盘目标目录 (默认: /{folder_name}): ").strip()
        if not seafile_root:
            seafile_root = f"/{folder_name}"

    if no_cache:
        folder_name = os.path.basename(os.path.abspath(local_path))
        remote_root = f"{seafile_root.rstrip('/')}/{folder_name}"
        cache_path = _cache_path(remote_root)
        if cache_path.exists():
            cache_path.unlink()
        print("[no-cache] 本次不使用缓存")

    print(f"\n本地文件夹: {local_path}")
    print(f"网盘目标:   {seafile_root}")
    if force_refresh:
        print("[refresh]    强制从网盘拉取")

    stats = sync_folder(local_path, seafile_root, force_refresh=force_refresh)

    print(f"\n{'=' * 40}")
    parts = [f"同步完成: {stats['uploaded']} 个文件已上传"]
    if stats["skipped"]:
        parts.append(f"{stats['skipped']} 个已跳过")
    if stats["failed"]:
        parts.append(f"{stats['failed']} 个失败")
    if stats["from_cache"]:
        parts.append("（使用本地缓存）")
    print(", ".join(parts))
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
