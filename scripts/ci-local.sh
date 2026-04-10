#!/usr/bin/env bash
# Run the same checks as .github/workflows/ci.yml (backend + frontend).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== Backend: pytest =="
python3 -m pytest tests/ -v --tb=short

echo "== Backend: mypy (same as GitHub Actions) =="
python3 -m pip install -q mypy httpx aiosqlite 2>/dev/null || true
python3 -m pip install -q "mypy>=1.8,<2"
python3 -m mypy app/ --ignore-missing-imports --no-strict-optional --allow-untyped-defs

echo "== Frontend: install, tsc, vitest, build =="
cd frontend
npm ci
npx tsc --noEmit
npx vitest run
npx vite build

echo "== All CI checks passed =="
