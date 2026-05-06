import json
from pathlib import Path

from seafileapi import Repo, SeafileAPI

TYPE_TOKEN_ERROR_HINT = "可能使用了错误的 Token，请注意：\n" \
                        "       仓库 Token 是一串 40 位的字母数字（如：d817af60...）\n" \
                        "       不是用户 API Token，也不是仓库 ID（如：6f42c7e0-...）"


def load_config(config_path: str | None = None) -> dict:
    """
    从 config.json 读取配置信息。

    默认路径为项目根目录下的 script/config.json。
    可通过 config_path 参数指定其他路径。

    返回包含 base_url 和 api_token 的字典。
    """
    if config_path is None:
        config_path = (
            Path(__file__).resolve().parent.parent / "script" / "config.json"
        )
    else:
        config_path = Path(config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_api(repo_id: str | None = None) -> Repo:
    """从配置文件读取凭证，返回已认证的 Repo 实例。

    如果 token_type 为 "repo"（目录 token），直接创建 Repo 对象。
    如果 token_type 为 "user"（用户 token），通过 SeafileAPI 查找仓库：
      - 指定 repo_id 则直接返回该仓库
      - 未指定则列出所有仓库供用户选择
    如果 token_type 为 "no"（未保存 token），要求用户输入仓库 token 后创建实例。
    """
    config = load_config()
    base_url = config["base_url"]
    token_type = config.get("token_type", "user")

    if token_type == "no":
        token = input("请输入仓库 API Token: ").strip()
        if not token:
            raise ValueError("API Token 不能为空")
        repo = Repo(token, base_url)
        repo.auth()
        return repo

    token = config["api_token"]

    if token_type == "repo":
        repo = Repo(token, base_url)
        repo.auth()
        return repo

    # 用户 token 模式
    api = SeafileAPI.from_auth_token(token, base_url)
    api.auth()

    if repo_id:
        return api.get_repo(repo_id)

    repos = api.list_repos()
    print("\n可用的仓库列表：")
    for i, r in enumerate(repos, 1):
        print(f"  {i}. {r['name']}  ({r['id']})")
    print()
    choice = input("请选择仓库编号: ").strip()
    idx = int(choice) - 1
    selected = repos[idx]
    return api.get_repo(selected["id"])
