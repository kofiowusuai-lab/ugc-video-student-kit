#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
./scripts/setup-linux.sh
read -r -p "Press Enter to close..."
