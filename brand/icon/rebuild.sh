#!/bin/zsh
# Regenerates AppIcon.icon's sources into ./src/rule-legal with the settings this icon was cut with.
cd ${0:A:h}
W=470 H=640 AC=42 AP=17 PT=9 PG=5 GU=0.82 GRX=110 GRY=260 GB=75 INK=binary PALE_BACK=1 ONLY=rule-legal uv run -q make_codex.py src
