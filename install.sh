#!/usr/bin/env bash
set -euo pipefail

# Install vivid-clean and its preferred dependency, watermarks-remover.
# Run: ./install.sh

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${REPO_DIR}/vendor"
SKILLS_DIR="${HOME}/.agents/skills"
SKILL_NAME="vivid-clean"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=10

check_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not installed." >&2
    exit 1
  fi

  local version
  version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  local major minor
  major="$(echo "$version" | cut -d. -f1)"
  minor="$(echo "$version" | cut -d. -f2)"

  if [ "$major" -lt "$PYTHON_MIN_MAJOR" ] || { [ "$major" -eq "$PYTHON_MIN_MAJOR" ] && [ "$minor" -lt "$PYTHON_MIN_MINOR" ]; }; then
    echo "Error: Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ is required (found ${version})." >&2
    exit 1
  fi

  echo "Python ${version} is OK."
}

check_markitdown() {
  if command -v markitdown >/dev/null 2>&1; then
    echo "markitdown is already installed."
    return 0
  fi

  echo "Installing markitdown..."
  pip3 install markitdown
}

check_pandoc() {
  if command -v pandoc >/dev/null 2>&1; then
    echo "pandoc is already installed."
    return 0
  fi

  echo "Warning: pandoc is required but not installed." >&2
  echo "Please install it manually:" >&2
  echo "  macOS: brew install pandoc" >&2
  echo "  Debian/Ubuntu: sudo apt-get install pandoc" >&2
  return 1
}

clone_watermarks_remover() {
  local target="${VENDOR_DIR}/watermarks-remover"

  if [ -d "${target}/.git" ]; then
    echo "watermarks-remover is already cloned at ${target}. Pulling latest..."
    git -C "${target}" pull --ff-only
    return 0
  fi

  echo "Cloning watermarks-remover into ${target}..."
  mkdir -p "${VENDOR_DIR}"
  git clone --depth 1 https://github.com/guillaumemeyer/watermarks-remover.git "${target}"
}

install_skill() {
  local target="${SKILLS_DIR}/${SKILL_NAME}"

  echo "Installing skill to ${target}..."
  mkdir -p "${target}"
  cp "${REPO_DIR}/SKILL.md" "${target}/SKILL.md"

  echo "Skill installed. Trigger it with /${SKILL_NAME}"
}

print_next_steps() {
  echo ""
  echo "Installation complete. Next steps:"
  echo ""
  echo "1. Start the watermarks-remover service:"
  echo "   cd ${VENDOR_DIR}/watermarks-remover"
  echo "   python3 service/scripts/server.py --host 127.0.0.1 --port 8765"
  echo ""
  echo "2. Make sure pandoc is installed and on your PATH."
  echo ""
  echo "3. Use the skill from your agent with /${SKILL_NAME} or run the pipeline directly."
  echo ""
}

main() {
  echo "Installing ${SKILL_NAME}..."
  check_python
  check_markitdown
  check_pandoc || true
  clone_watermarks_remover
  install_skill
  print_next_steps
}

main "$@"
