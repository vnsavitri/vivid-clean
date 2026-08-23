#!/usr/bin/env bash
set -euo pipefail

# Install vivid-clean into a repo-local virtual environment and pin its engines.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${REPO_DIR}/vendor"
VENV_DIR="${REPO_DIR}/.venv"
INSTALL_HOME="${VIVID_CLEAN_USER_HOME:-${HOME}}"
BIN_DIR="${INSTALL_HOME}/.local/bin"
WATERMARKS_REMOVER_URL="https://github.com/guillaumemeyer/watermarks-remover.git"
WATERMARKS_REMOVER_REF="104aacd212d7a262c32bd7f1f4aa380c26a5d4b5"
ANTHROPIES_URL="https://github.com/CharlesHoskinson/anthropies.git"
ANTHROPIES_REF="6d1dba6870b9a01a1c088e18d8eed44366bbbe36"
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=11

info() {
  printf '%s\n' "$*"
}

warn() {
  printf 'Warning: %s\n' "$*" >&2
}

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "Error: %s is required but wasn't found.\n" "$1" >&2
    exit 1
  fi
}

check_python() {
  check_command python3
  python3 - "${PYTHON_MIN_MAJOR}" "${PYTHON_MIN_MINOR}" <<'PY'
import sys

required = tuple(map(int, sys.argv[1:3]))
found = sys.version_info[:2]
if found < required:
    raise SystemExit(f"Error: Python {required[0]}.{required[1]}+ is required (found {found[0]}.{found[1]}).")
print(f"Python {found[0]}.{found[1]} is OK.")
PY
}

checkout_pinned() {
  local name="$1"
  local url="$2"
  local ref="$3"
  local target="${VENDOR_DIR}/${name}"

  mkdir -p "${VENDOR_DIR}"
  if [[ ! -d "${target}/.git" ]]; then
    info "Cloning ${name}..."
    git clone --filter=blob:none --no-checkout "${url}" "${target}"
  fi
  if [[ "$(git -C "${target}" remote get-url origin)" != "${url}" ]]; then
    printf 'Error: %s has an unexpected origin. Refusing to update it.\n' "${target}" >&2
    exit 1
  fi
  git -C "${target}" fetch --depth 1 origin "${ref}"
  git -C "${target}" checkout --detach --force FETCH_HEAD
  if [[ "$(git -C "${target}" rev-parse HEAD)" != "${ref}" ]]; then
    printf "Error: %s didn't resolve to the audited commit.\n" "${name}" >&2
    exit 1
  fi
  info "${name}: pinned at ${ref}"
}

install_python() {
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    info "Creating ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
  fi
  info "Installing vivid-clean and document support..."
  "${VENV_DIR}/bin/python" -m pip install --disable-pip-version-check --quiet -e "${REPO_DIR}[documents]"
  mkdir -p "${BIN_DIR}"
  local command_link="${BIN_DIR}/vivid-clean"
  if [[ -e "${command_link}" && ! -L "${command_link}" ]]; then
    printf "Error: %s already exists and isn't a symlink. Move it, then run the installer again.\n" "${command_link}" >&2
    exit 1
  fi
  if [[ -L "${command_link}" && "$(readlink "${command_link}")" != "${VENV_DIR}/bin/vivid-clean" ]]; then
    printf 'Error: %s points to another installation. Move it, then run the installer again.\n' "${command_link}" >&2
    exit 1
  fi
  ln -sfn "${VENV_DIR}/bin/vivid-clean" "${command_link}"
}

install_anthropies_if_available() {
  if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
    warn "anthropies wasn't installed because Node 22+ isn't available. The core tool still works."
    warn "Install Node 22 and pnpm, then run ./install.sh again to enable the fallback."
    return 0
  fi
  if ! command -v pnpm >/dev/null 2>&1; then
    warn "anthropies wasn't installed because pnpm isn't available. The core tool still works."
    warn "Run corepack enable (or install pnpm), then run ./install.sh again."
    return 0
  fi
  checkout_pinned "anthropies" "${ANTHROPIES_URL}" "${ANTHROPIES_REF}"
  info "Building the optional anthropies fallback..."
  pnpm --dir "${VENDOR_DIR}/anthropies" install --frozen-lockfile
  pnpm --dir "${VENDOR_DIR}/anthropies" build
}

install_skill_copy() {
  local base="$1"
  local target="${base}/vivid-clean"
  mkdir -p "${target}"
  cp "${REPO_DIR}/SKILL.md" "${target}/SKILL.md"
  cp "${REPO_DIR}/PROMPT.md" "${target}/PROMPT.md"
}

install_skills() {
  install_skill_copy "${INSTALL_HOME}/.agents/skills"
  install_skill_copy "${INSTALL_HOME}/.cursor/skills"
  install_skill_copy "${INSTALL_HOME}/.claude/skills"
  install_skill_copy "${INSTALL_HOME}/.codex/skills"
  info "Installed the skill for compatible agents, Cursor, Claude and Codex."
}

check_pandoc() {
  if command -v pandoc >/dev/null 2>&1; then
    info "pandoc: $(command -v pandoc)"
    return 0
  fi
  warn "pandoc isn't installed. DOCX, PPTX and PDF rebuilds won't work until it's installed."
  warn "macOS: brew install pandoc"
  warn "Debian/Ubuntu: sudo apt-get install pandoc"
}

print_next_steps() {
  info ""
  info "Installation complete."
  info ""
  info "Make sure ${BIN_DIR} is on PATH, then run:"
  info "  vivid-clean doctor"
  info ""
  info "Prepare a file (the local cleaner starts and stops automatically):"
  info "  vivid-clean prepare /path/to/document.docx"
}

main() {
  info "Installing vivid-clean..."
  check_command git
  check_python
  checkout_pinned "watermarks-remover" "${WATERMARKS_REMOVER_URL}" "${WATERMARKS_REMOVER_REF}"
  install_python
  install_anthropies_if_available
  install_skills
  check_pandoc
  print_next_steps
}

main "$@"
