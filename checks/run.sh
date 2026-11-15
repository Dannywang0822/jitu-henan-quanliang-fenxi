#!/usr/bin/env bash
# 固定检查入口。必须在仓库根目录可执行；也可从任意目录调用。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "[checks] cwd=$ROOT"
echo "[checks] python=$PYTHON"
"$PYTHON" -c "import sys; print('[checks] version', sys.version.split()[0])"

# 若测试层运行器存在，先根据夹具重放非正式输出（写入 test_layer/outputs，不写正式层）
if "$PYTHON" -c "import test_layer.run" >/dev/null 2>&1; then
  echo "[checks] 重放测试层非正式输出"
  "$PYTHON" -m test_layer.run
fi

echo "[checks] 运行 pytest"
"$PYTHON" -m pytest checks -q
echo "[checks] 全部通过"
