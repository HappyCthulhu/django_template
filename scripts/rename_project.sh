#!/usr/bin/env bash
set -eu

usage() {
  echo "Usage: ./scripts/rename_project.sh <project_name>" >&2
}

die() {
  echo "Error: $1" >&2
  exit 1
}

info() {
  echo "==> $1"
}

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd -- "${ROOT_DIR}"

if [ "${#}" -ne 1 ]; then
  usage
  exit 1
fi

PROJECT_NAME="$1"

if ! printf '%s' "${PROJECT_NAME}" | grep -Eq '^[a-z][a-z0-9_]*$'; then
  die "Invalid <project_name> '${PROJECT_NAME}'. It must match: ^[a-z][a-z0-9_]*$ (snake_case Python package name). Example: my_project"
fi

MARKER_FILE=".project_renamed"
if [ -f "${MARKER_FILE}" ]; then
  die "This template has already been renamed (marker '${MARKER_FILE}' exists). Refusing to run twice."
fi

if [ ! -d "server" ]; then
  die "Directory 'server/' not found. Either the project is already renamed or the template structure has changed."
fi

if [ -e "${PROJECT_NAME}" ]; then
  die "Target path '${PROJECT_NAME}' already exists. Choose a different project name."
fi

if command -v rg >/dev/null 2>&1; then
  SEARCH_TOOL="rg"
else
  SEARCH_TOOL="grep"
fi

info "Summary:"
info "- rename directory: server/ -> ${PROJECT_NAME}/"
info "- update Python imports and settings references from 'server' to '${PROJECT_NAME}' (excluding migrations)"
info "- update DJANGO_SETTINGS_MODULE references"
info "- update pyproject.toml project name and README header"

escape_sed_pattern() {
  # Escape chars that are special in BRE and in sed delimiter context.
  # shellcheck disable=SC2001
  printf '%s' "$1" | sed 's/[.[\*^$()+?{|\\]/\\&/g' | sed 's|/|\\/|g'
}

escape_sed_replacement() {
  # Escape '&' and '\' in replacement.
  printf '%s' "$1" | sed 's/[\\&]/\\&/g'
}

replace_in_file() {
  file="$1"
  from="$2"
  to="$3"

  [ -f "${file}" ] || return 0

  tmp="$(mktemp)"
  from_esc="$(escape_sed_pattern "${from}")"
  to_esc="$(escape_sed_replacement "${to}")"

  sed "s/${from_esc}/${to_esc}/g" "${file}" > "${tmp}"
  mv "${tmp}" "${file}"
}

collect_files() {
  # Collect only the files we are allowed/expected to edit.
  # - exclude .git/
  # - exclude venvs
  # - exclude migrations (content must not be modified)
  if [ "${SEARCH_TOOL}" = "rg" ]; then
    rg -l --hidden --glob '!**/.git/**' --glob '!**/.venv/**' --glob '!**/venv/**' --glob '!**/migrations/**' \
      --glob '**/*.py' --glob 'pyproject.toml' --glob 'README.md' --glob 'Dockerfile' \
      'server\.|server/|DJANGO_SETTINGS_MODULE' .
  else
    # grep fallback: gather a broad set and filter paths.
    grep -RIl 'server\.\|server/\|DJANGO_SETTINGS_MODULE' . \
      | grep -v '/\.git/' \
      | grep -v '/\.venv/' \
      | grep -v '/venv/' \
      | grep -v '/migrations/'
  fi
}

info "Renaming Django project directory: server/ -> ${PROJECT_NAME}/"

FILES="$(collect_files || true)"

info "Updating references (imports, settings module, docs)"
for f in ${FILES}; do
  # Fix legacy default in asgi/wsgi in the renamed project.
  replace_in_file "${f}" "server.settings" "${PROJECT_NAME}.configs.settings"
  replace_in_file "${f}" "server.configs.settings" "${PROJECT_NAME}.configs.settings"

  replace_in_file "${f}" "server.configs." "${PROJECT_NAME}.configs."
  replace_in_file "${f}" "server.apps." "${PROJECT_NAME}.apps."

  # Docs paths.
  replace_in_file "${f}" "server/" "${PROJECT_NAME}/"
done

info "Updating pyproject.toml project name"
replace_in_file "pyproject.toml" 'name = "template_django"' "name = \"${PROJECT_NAME}\""

info "Updating README title (if present)"
replace_in_file "README.md" "### django_template" "### ${PROJECT_NAME}"

mv "server" "${PROJECT_NAME}"

info "Creating compatibility shim for historical migrations (do not delete): server.apps.core.models.user"
mkdir -p "server/apps/core/models"
cat > "server/apps/core/models/user.py" <<EOF
from ${PROJECT_NAME}.apps.core.models.user import UserManager
EOF

# Ensure packages are importable on all Python setups (avoid namespace-package edge cases).
mkdir -p "server/apps/core"
touch "server/__init__.py" "server/apps/__init__.py" "server/apps/core/__init__.py" "server/apps/core/models/__init__.py"

info "Writing marker file: ${MARKER_FILE}"
touch "${MARKER_FILE}"

info "Done."
info "Project renamed to '${PROJECT_NAME}'."
