#!/usr/bin/env bash

# Verify the committed checkout without requiring the untracked full data layers.
set -euo pipefail

readonly SCRIPT_PATH='scripts/verify_clean_clone.sh'
readonly REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"

run_checkout_verification() {
  (
    cd "$REPOSITORY_ROOT"

    if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
      printf 'The clean-clone checkout is not clean. Aborting.\n' >&2
      return 1
    fi

    python -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python -m pytest -q tests/test_presentation_export.py
    .venv/bin/python -m pytest -q

    (
      cd app
      npm ci
      npm run lint
      npm test
      npm run build
    )
  )
}

if [[ "${1:-}" == '--in-clean-clone' ]]; then
  run_checkout_verification
  exit 0
fi

if [[ $# -ne 0 ]]; then
  printf 'Usage: %s\n' "$SCRIPT_PATH" >&2
  exit 2
fi

readonly SOURCE_ROOT="$(git rev-parse --show-toplevel)"
if ! git -C "$SOURCE_ROOT" cat-file -e "HEAD:$SCRIPT_PATH" 2>/dev/null; then
  printf '%s must be committed before it can verify a clean clone.\n' "$SCRIPT_PATH" >&2
  exit 2
fi

readonly TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/antes-da-chuva-clean-clone.XXXXXX")"
cleanup() {
  rm -rf "$TEMP_ROOT"
}
trap cleanup EXIT

readonly CLONE_ROOT="$TEMP_ROOT/repository"
git clone --no-local --no-hardlinks "$SOURCE_ROOT" "$CLONE_ROOT"
"$CLONE_ROOT/$SCRIPT_PATH" --in-clean-clone
