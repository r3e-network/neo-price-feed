#!/usr/bin/env bash
set -euo pipefail

# Neo Express end-to-end workflow runner
# - Starts Neo Express using the provided config
# - Starts Neo Express using the provided config
# - Runs Neo Express integration tests
# - Builds contract artifacts
#
# Usage:
#   ./scripts/neoexpress-e2e.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${ROOT_DIR}/src/PriceFeed.Contracts/neo-express.config.json"
NEOXP="$(command -v neoxp || command -v neo-express || true)"

if [[ -z "$NEOXP" ]]; then
  echo "neo-express (neoxp) is required. Install via: dotnet tool install -g Neo.Express" >&2
  exit 1
fi

RPC_ENDPOINT="http://localhost:20332"
OWNER_WIF="KxDgvEKzgSBPPfuVfw67oPQBSjidEiqTHURKSDL1R7yGaGYAeYnr"

echo "==> Building contract artifacts"
dotnet build "${ROOT_DIR}/src/PriceFeed.Contracts/PriceFeed.Contracts.csproj" -c Release >/dev/null
NEF="${ROOT_DIR}/src/PriceFeed.Contracts/bin/sc/PriceFeed.Oracle.nef"
MANIFEST="${ROOT_DIR}/src/PriceFeed.Contracts/bin/sc/PriceFeed.Oracle.manifest.json"

echo "==> Starting Neo Express (config: ${CONFIG})"
LOG_FILE="$(mktemp)"
echo "   neo express log: ${LOG_FILE}"
"${NEOXP}" run -i "${CONFIG}" -s 1 -d >"${LOG_FILE}" 2>&1 &
NEOXP_PID=$!
trap 'kill ${NEOXP_PID} >/dev/null 2>&1 || true' EXIT

# Wait for RPC to respond
echo "==> Waiting for Neo Express RPC at ${RPC_ENDPOINT}"
READY=0
for i in {1..30}; do
  if curl -s "${RPC_ENDPOINT}" -d '{"jsonrpc":"2.0","method":"getblockcount","params":[],"id":1}' >/dev/null; then
    READY=1
    break
  fi
  sleep 1
done
if [[ "${READY}" -ne 1 ]]; then
  echo "Neo Express RPC not reachable. Log output:"
  cat "${LOG_FILE}"
  exit 1
fi

echo "==> Running Neo Express integration tests"
RUN_NEO_EXPRESS_TESTS=true \
NEO_EXPRESS_RPC_ENDPOINT="${RPC_ENDPOINT}" \
dotnet test "${ROOT_DIR}/PriceFeed.sln" --filter NeoExpressIntegrationTests --nologo

echo "==> Done. Stopping Neo Express."
kill "${NEOXP_PID}" >/dev/null 2>&1 || true
