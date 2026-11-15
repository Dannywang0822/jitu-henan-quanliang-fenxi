"""不存在极兔内部系统连接器。"""

import pytest

from kernel.connectors import InternalSystemConnectorForbidden, assert_no_internal_connector_modules, connect_jitu_internal


def test_connect_jitu_internal_forbidden():
    with pytest.raises(InternalSystemConnectorForbidden):
        connect_jitu_internal(endpoint="https://internal.example")


def test_repo_has_no_internal_connector_module(repo_root):
    assert_no_internal_connector_modules(str(repo_root))
