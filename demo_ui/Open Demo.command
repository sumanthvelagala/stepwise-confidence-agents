#!/bin/zsh
SCA_DEMO_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
if [[ -d "/Applications/Google Chrome.app" ]]; then
  open -a "Google Chrome" "$SCA_DEMO_DIR/dist/index.html"
else
  open -a Safari "$SCA_DEMO_DIR/dist/index.html"
fi
