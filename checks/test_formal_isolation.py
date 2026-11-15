"""测试结果不能写入正式层；未点头的 promote 必须失败。"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kernel.isolation import FormalWriteForbidden, list_non_placeholder, write_text_from_test_layer
from kernel.promotion import (
    DannyApproval,
    FormalStore,
    IncompletePackageError,
    PromotionDenied,
    PromotionPackage,
)


def _package() -> PromotionPackage:
    return PromotionPackage(
        package_id="test-pack-1",
        plan="测试方案",
        detailed_calc="测试测算",
        input_snapshot={"as_of": "2026-11-08"},
        targets={"揽收量": "530"},
        ruling_record={"裁定人": "Danny", "方案": "测试方案", "依据": "夹具", "生效时间": "未定"},
    )


def test_test_layer_cannot_write_formal_layer(repo_root: Path, tmp_path: Path):
    target = repo_root / "formal_layer" / "should_not_exist.md"
    with pytest.raises(FormalWriteForbidden):
        write_text_from_test_layer(repo_root, target, "测试结果")
    assert not target.exists()

    formal_dict = repo_root / "dictionary" / "formal" / "should_not_exist.json"
    with pytest.raises(FormalWriteForbidden):
        write_text_from_test_layer(repo_root, formal_dict, "{}")
    assert not formal_dict.exists()


def test_unapproved_promote_fails_and_does_not_write(tmp_path: Path):
    store = FormalStore(tmp_path / "formal_layer")
    approval = DannyApproval(
        approved=False,
        package_id="test-pack-1",
        signed_off_by="Danny",
        note="未点头",
    )
    with pytest.raises(PromotionDenied):
        store.promote(_package(), approval)
    assert store.published_entries() == []


def test_promote_without_danny_signoff_fails(tmp_path: Path):
    store = FormalStore(tmp_path / "formal_layer")
    approval = DannyApproval(approved=True, package_id="test-pack-1", signed_off_by="他人")
    with pytest.raises(PromotionDenied):
        store.promote(_package(), approval)
    assert store.published_entries() == []


def test_incomplete_package_rejected(tmp_path: Path):
    store = FormalStore(tmp_path / "formal_layer")
    with pytest.raises((IncompletePackageError, ValidationError)):
        PromotionPackage(
            package_id="x",
            plan="",
            detailed_calc="测算",
            input_snapshot={"a": 1},
            targets={"t": 1},
            ruling_record={"裁定人": "Danny", "方案": "a", "依据": "b", "生效时间": "c"},
        )
    pkg = PromotionPackage(
        package_id="x",
        plan="方案",
        detailed_calc="测算",
        input_snapshot={},
        targets={"t": 1},
        ruling_record={"裁定人": "Danny", "方案": "a", "依据": "b", "生效时间": "c"},
    )
    with pytest.raises(IncompletePackageError):
        pkg.assert_complete()
    with pytest.raises(PromotionDenied):
        store.promote(
            _package(),
            DannyApproval(approved=False, package_id="test-pack-1", signed_off_by="Danny"),
        )


def test_rollback_interface_exists(tmp_path: Path):
    store = FormalStore(tmp_path / "formal_layer")
    # 空库回滚应可调用，不把测试包写进仓库正式层
    store.rollback()
    assert store.published_entries() == []


def test_repo_formal_layer_and_formal_dictionary_are_empty(repo_root: Path):
    formal = list_non_placeholder(repo_root / "formal_layer")
    assert formal == [], formal
    formal_dict = list_non_placeholder(repo_root / "dictionary" / "formal")
    assert formal_dict == [], formal_dict
