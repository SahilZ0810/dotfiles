REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v fastfetch >/dev/null 2>&1 && [ -n "$PS1" ]; then
  fastfetch -c "$REPO_DIR/shell/fastfetch-config.jsonc"
fi
