"""不存在极兔内部系统连接器。"""


class InternalSystemConnectorForbidden(RuntimeError):
    """禁止对接极兔内部系统。"""


def connect_jitu_internal(*_args, **_kwargs) -> None:
    raise InternalSystemConnectorForbidden(
        "不存在极兔内部系统连接器。禁止对接极兔内部系统，禁止索取或保存公司明细。"
    )


def assert_no_internal_connector_modules(repo_root: str) -> None:
    """扫描仓库，不允许出现内部系统连接器模块。"""
    from pathlib import Path

    root = Path(repo_root)
    forbidden_name_parts = (
        "jitu_internal_connector",
        "jitu-internal-connector",
        "internal_system_connector",
    )
    hits: list[str] = []
    for path in root.rglob("*"):
        if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        name = path.name.lower()
        if any(part in name for part in forbidden_name_parts):
            hits.append(str(path.relative_to(root)))
    if hits:
        raise InternalSystemConnectorForbidden(f"发现内部系统连接器文件: {hits}")
