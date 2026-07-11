#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi

  if [[ -x "${HOME}/.local/bin/uv" ]]; then
    export PATH="${HOME}/.local/bin:${PATH}"
    return
  fi

  echo "[INFO] 未检测到 uv，正在安装..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
}

ensure_uv

if [[ ! -d .venv ]]; then
  echo "[INFO] 创建虚拟环境..."
  uv venv
fi

echo "[INFO] 同步依赖..."
uv sync

PORT="${GRADIO_SERVER_PORT:-7860}"

stop_port_process() {
  if command -v fuser >/dev/null 2>&1 && fuser "${PORT}/tcp" >/dev/null 2>&1; then
    echo "[WARN] 端口 ${PORT} 已被占用，正在结束旧进程..."
    fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
    sleep 1
    return
  fi

  if ss -tlnp 2>/dev/null | grep -qE ":${PORT}[[:space:]]"; then
    echo "[WARN] 端口 ${PORT} 已被占用，正在结束旧进程..."
    pkill -f "${ROOT_DIR}/.venv/bin/python3 app.py" >/dev/null 2>&1 || true
    sleep 1
  fi
}

stop_port_process

echo "[INFO] 启动 UcubMQDraw -> http://127.0.0.1:${PORT}"
echo "[INFO] Mock 模式: UCUB_MQDRAW_USE_MOCK=${UCUB_MQDRAW_USE_MOCK:-true}"
exec uv run python app.py
