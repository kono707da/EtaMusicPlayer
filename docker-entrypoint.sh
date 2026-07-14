#!/bin/sh
set -e

DEPS_DIR="/app/deps"
PYLIBS_DIR="$DEPS_DIR/pylibs"
BIN_DIR="$DEPS_DIR/bin"
MARKER="$DEPS_DIR/.installed"

mkdir -p "$DEPS_DIR" "$PYLIBS_DIR" "$BIN_DIR" /app/node /app/plugins

if [ ! -f "$MARKER" ]; then
    echo "[DEPS] First run: installing runtime dependencies..."

    if [ ! -f "$BIN_DIR/ffmpeg" ]; then
        echo "[DEPS] Downloading ffmpeg static binary..."
        FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        TMP_DIR=$(mktemp -d)
        if wget -q -O "$TMP_DIR/ffmpeg.tar.xz" "$FFMPEG_URL"; then
            tar -xf "$TMP_DIR/ffmpeg.tar.xz" -C "$TMP_DIR"
            cp "$TMP_DIR"/ffmpeg-*-static/ffmpeg "$BIN_DIR/ffmpeg"
            cp "$TMP_DIR"/ffmpeg-*-static/ffprobe "$BIN_DIR/ffprobe"
            chmod +x "$BIN_DIR/ffmpeg" "$BIN_DIR/ffprobe"
            echo "[DEPS] ffmpeg installed to $BIN_DIR"
        else
            echo "[WARN] Failed to download ffmpeg static binary, continuing without it"
        fi
        rm -rf "$TMP_DIR"
    fi

    echo "[DEPS] Installing Python packages (web backend only)..."
    pip install --no-cache-dir --target="$PYLIBS_DIR" \
        -r /app/web/backend/requirements.txt

    touch "$MARKER"
    echo "[DEPS] Runtime dependencies installed successfully."
else
    echo "[DEPS] Runtime dependencies already installed, skipping."
fi

export PYTHONPATH="$PYLIBS_DIR${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$BIN_DIR:$PATH"

echo "[START] EtaMusic Web (port 8000)"
cd /app/web/backend
exec python -m uvicorn eta_web.main:app --host 0.0.0.0 --port 8000
