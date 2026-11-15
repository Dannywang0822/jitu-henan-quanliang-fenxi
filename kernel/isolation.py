"""测试层不能写正式层；测试识别不能改写正式字典。"""

from __future__ import annotations

from pathlib import Path


class FormalWriteForbidden(PermissionError):
    """测试层试图写入正式输出层或正式字典。"""


def repo_paths(repo_root: Path) -> dict[str, Path]:
    root = Path(repo_root).resolve()
    return {
        "root": root,
        "formal_layer": (root / "formal_layer").resolve(),
        "formal_dictionary": (root / "dictionary" / "formal").resolve(),
        "candidates": (root / "dictionary" / "candidates").resolve(),
        "test_layer": (root / "test_layer").resolve(),
    }


def assert_not_formal_target(repo_root: Path, target: Path) -> None:
    paths = repo_paths(repo_root)
    resolved = Path(target).resolve()
    for key in ("formal_layer", "formal_dictionary"):
        formal = paths[key]
        if resolved == formal or formal in resolved.parents:
            raise FormalWriteForbidden(
                f"测试层不能写入正式目录 {formal}: 目标为 {resolved}"
            )


def write_text_from_test_layer(repo_root: Path, target: Path, content: str) -> Path:
    assert_not_formal_target(repo_root, target)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def list_non_placeholder(directory: Path, allowed: set[str] | None = None) -> list[Path]:
    allowed = allowed or {".gitkeep", "README.md"}
    if not directory.exists():
        return []
    found: list[Path] = []
    for path in directory.iterdir():
        if path.is_file() and path.name not in allowed:
            found.append(path)
        if path.is_dir() and path.name not in {".git"}:
            found.extend(p for p in path.rglob("*") if p.is_file() and p.name not in allowed)
    return found
