#!/usr/bin/env bash
# Gate: unit tests (build.py, schema), then page QA if tools/qa_page.py exists.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m unittest discover -s tests -t . -v

if [ -f tools/qa_page.py ]; then
  python3 tools/qa_page.py
fi

echo "ALL CHECKS PASSED"
