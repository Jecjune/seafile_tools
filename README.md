# File API

一个基于 [seafileapi2](https://github.com/haiwen/python-seafile) 的 Seafile 文件管理工具包，支持文件/文件夹的上传、列表查看、增量同步等操作。

更多 API 请查看官方文档：
- [Web API v2.1](http://manual.seafile.com/11.0/develop/web_api_v2.1/)
- [python-seafile](https://github.com/haiwen/python-seafile)

---

## 目录

- [环境准备](#环境准备)
- [初始化配置](#初始化配置)
- [使用用例](#使用用例)
  - [1. 创建文件](#1-创建文件)
  - [2. 列出目录](#2-列出目录)
  - [3. 上传单个文件](#3-上传单个文件)
  - [4. 上传文件夹](#4-上传文件夹)
  - [5. 增量同步文件夹](#5-增量同步文件夹)
- [配置说明](#配置说明)
- [缓存说明](#缓存说明)

---

## 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

---

## 初始化配置

首次使用前，必须通过初始化脚本配置 Seafile 服务器地址和认证令牌：

```bash
bash script/init.sh
```

脚本会引导你完成以下步骤：
1. 选择令牌类型（用户令牌 / 仓库令牌 / 不保存）
2. 输入服务器地址（如 `https://seafile.com`）
3. 输入对应的 API 令牌

初始化完成后会在 `script/config.json` 中生成配置文件。

> **Token 类型说明：**
> - **仓库令牌 (repo token)**：40 位十六进制字符串，对应一个资料库，权限范围最小。
> - **用户令牌 (user token)**：通过用户名密码获取，可操作该用户下所有资料库。
>
> 如选择"不保存"，每次运行时会提示手动输入令牌。

辅助脚本 `script/get_user_api_token.sh` 可用于单独获取用户令牌：

```bash
bash script/get_user_api_token.sh
```

---

## 使用用例

所有用例支持两种运行模式：
- **命令行传参模式**：直接传入参数，适合脚本调用
- **交互模式**：不传参数，程序会依次提示输入

### 1. 创建文件

在 Seafile 资料库中创建目录和文件。

```bash
# 默认为交互模式，按提示操作
python -m file_api.file_create
```

程序会在资料库根目录下创建 `/test_files` 目录及其中的 `demo.txt` 文件。

---

### 2. 列出目录

列出 Seafile 资料库中指定目录的内容（文件/文件夹），以表格形式展示类型、大小和名称。

```bash
# 列出根目录
python -m file_api.file_list

# 列出指定目录
python -m file_api.file_list /test_files

# 交互模式（不传参数）
python -m file_api.file_list
```

---

### 3. 上传单个文件

将本地文件上传到 Seafile 资料库的指定目录。

```bash
# 命令行传参：上传文件到指定目录
python -m file_api.file_upload /path/to/local/file.txt /target/dir

# 仅指定本地文件，目标目录默认为 /
python -m file_api.file_upload /path/to/local/file.txt

# 交互模式（不传参数，按提示输入）
python -m file_api.file_upload
```

---

### 4. 上传文件夹

将本地文件夹递归上传到 Seafile 资料库，保持目录结构不变。

```bash
# 上传整个文件夹，默认目标路径为 /<文件夹名>
python -m file_api.folder_upload /path/to/local/folder

# 指定上传到资料库的某个子目录
python -m file_api.folder_upload /path/to/local/folder /seafile/target/path

# 交互模式（不传参数）
python -m file_api.folder_upload
```

---

### 5. 增量同步文件夹

增量同步本地文件夹到 Seafile 资料库。与文件夹上传不同，此模式会**缓存远程目录结构**，后续运行时只上传新增或变更的文件。

```bash
# 基本用法：首次运行会拉取远程文件列表并缓存，后续只上传新增文件
python -m file_api.folder_sync /path/to/local/folder

# 指定远程目标路径
python -m file_api.folder_sync /path/to/local/folder /seafile/target/path

# 强制刷新远程列表（忽略缓存，重新拉取）
python -m file_api.folder_sync /path/to/local/folder --refresh

# 不使用缓存（每次重新拉取远程列表）
python -m file_api.folder_sync /path/to/local/folder --no-cache

# 清除所有缓存数据
python -m file_api.folder_sync --clear-cache

# 交互模式（不传参数）
python -m file_api.folder_sync
```

**同步结果说明**：运行结束后会显示上传数、跳过数、失败数以及是否使用缓存。

---

## 配置说明

配置文件 `script/config.json` 结构：

```json
{
  "base_url": "https://seafile.com",
  "api_token": "your_api_token_here",
  "token_type": "repo"
}
```

| 字段 | 说明 |
|------|------|
| `base_url` | Seafile 服务器地址 |
| `api_token` | API 认证令牌 |
| `token_type` | 令牌类型：`repo`（仓库令牌）、`user`（用户令牌）、`no`/`none`（无令牌，运行时交互输入） |

---

## 缓存说明

`folder_sync` 的缓存文件存储在 `~/.cache/file_api_sync/` 目录下，以目标路径的 SHA-256 哈希值命名。

可通过如下命令清理所有缓存：

```bash
python -m file_api.folder_sync --clear-cache
```
