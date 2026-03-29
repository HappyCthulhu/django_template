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
PROJECT_DIST_NAME="$(printf '%s' "${PROJECT_NAME}" | tr '_' '-')"

if ! printf '%s' "${PROJECT_NAME}" | grep -Eq '^[a-z][a-z0-9_]*$'; then
  die "Invalid <project_name> '${PROJECT_NAME}'. It must match: ^[a-z][a-z0-9_]*$ (snake_case Python package name). Example: my_project"
fi

MARKER_FILE=".project_renamed"
if [ -f "${MARKER_FILE}" ]; then
  die "This template has already been renamed (marker '${MARKER_FILE}' exists). Refusing to run twice."
fi

if [ ! -d "server" ]; then
  die "Directory 'server/' not found. Template structure has changed."
fi

info "Summary:"
info "- keep Django package directory: server/"
info "- keep Python imports and DJANGO_SETTINGS_MODULE pointing to server.configs.settings"
info "- update template-facing project names to '${PROJECT_NAME}'"
info "- update pyproject.toml, README.md, .env.example, docker-compose.yml and uv.lock (if present)"
info "- copy .env.example -> .env and .gitignore.example -> .gitignore when target files are absent"

escape_sed_pattern() {
  # Escape chars that are special in BRE and in sed delimiter context.
  # shellcheck disable=SC2001
  printf '%s' "$1" | sed 's/[.[\*^$()+?{|\\]/\\&/g' | sed 's|/|\\/|g'
}

escape_sed_replacement() {
  # Escape '/', '&' and '\' in replacement.
  printf '%s' "$1" | sed 's/[\\/&]/\\&/g'
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

info "Updating pyproject.toml project name"
replace_in_file "pyproject.toml" 'name = "template_django"' "name = \"${PROJECT_NAME}\""

info "Updating README title (if present)"
replace_in_file "README.md" "### django_template" "### ${PROJECT_NAME}"

info "Updating .env.example placeholders (if present)"
replace_in_file ".env.example" "VENV_NAME=dj-template" "VENV_NAME=${PROJECT_NAME}"
replace_in_file ".env.example" "/home/user/django-template/dumps/" "/home/user/${PROJECT_NAME}/dumps/"

info "Updating docker-compose container names (if present)"
replace_in_file "docker-compose.yml" "container_name: holidai_postgres" "container_name: ${PROJECT_NAME}_postgres"
replace_in_file "docker-compose.yml" "container_name: holidat_bot_django" "container_name: ${PROJECT_NAME}_django"

info "Updating uv.lock package name (if present)"
replace_in_file "uv.lock" 'name = "template-django"' "name = \"${PROJECT_DIST_NAME}\""

if [ -f ".env.example" ] && [ ! -e ".env" ]; then
  info "Creating .env from .env.example"
  cp ".env.example" ".env"
fi

if [ -f ".gitignore.example" ] && [ ! -e ".gitignore" ]; then
  info "Creating .gitignore from .gitignore.example"
  cp ".gitignore.example" ".gitignore"
fi

info "Writing marker file: ${MARKER_FILE}"
touch "${MARKER_FILE}"

info "Done."
info "Project renamed to '${PROJECT_NAME}'."
