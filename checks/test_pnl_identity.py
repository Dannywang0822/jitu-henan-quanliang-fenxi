"""有损益恒等式输入时，利润分项加总不平衡必须失败。"""

import pytest

from kernel.pnl import PnlIdentityError, assert_pnl_identity


def test_unbalanced_identity_rejected():
    with pytest.raises(PnlIdentityError):
        assert_pnl_identity(
            revenue="13435",
            cost="12853",
            expense="171",
            gross_profit="582",
            net_profit="100",
        )
    with pytest.raises(PnlIdentityError):
        assert_pnl_identity(
            revenue="13435",
            cost="12853",
            expense="171",
            gross_profit="1",
            net_profit="411",
        )


def test_legal_pnl_fixture_balances(pnl):
    ident = pnl.identity
    assert ident is not None
    assert_pnl_identity(
        revenue=ident["收入累计"],
        cost=ident["成本累计"],
        expense=ident["费用累计"],
        gross_profit=ident["毛利累计"],
        net_profit=ident["累计净利"],
    )
