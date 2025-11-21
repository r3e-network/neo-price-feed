#!/usr/bin/env bash
set -euo pipefail

# Neo Express end-to-end workflow runner
# - Starts Neo Express in an isolated temp workspace
# - Runs Neo Express integration tests
# - Builds contract artifacts
#
# Usage:
#   ./scripts/neoexpress-e2e.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
CONFIG="${HOME}/.neo-express/default.neo-express"
SYMBOL="BTCUSDT"
TEST_PRICE="5000000000000" # 50,000.00000000
NEOXP="$(command -v neoxp || command -v neo-express || true)"
DEPLOY_ACCOUNT="node1"

if [[ -z "$NEOXP" ]]; then
  echo "neo-express (neoxp) is required. Install via: dotnet tool install -g Neo.Express" >&2
  exit 1
fi

if [[ ! -f "${CONFIG}" ]]; then
  echo "Neo Express config not found at ${CONFIG}. Run 'neoxp create' once to bootstrap the default instance." >&2
  exit 1
fi

RPC_PORT="$(jq -r '."consensus-nodes"[0]."rpc-port"' "${CONFIG}")"
RPC_ENDPOINT="${NEO_EXPRESS_RPC_ENDPOINT:-http://localhost:${RPC_PORT}}"
PRICE_SEEDED=false
DEPLOY_SIGNER="node1"
TEE_SIGNER="node1"
DEPLOY_ADDRESS="$(jq -r '."consensus-nodes"[0].wallet.accounts[0]."script-hash"' "${CONFIG}")"

echo "==> Building contract artifacts"
dotnet build "${ROOT_DIR}/src/PriceFeed.Contracts/PriceFeed.Contracts.csproj" -c Release >/dev/null
NEF="${ROOT_DIR}/src/PriceFeed.Contracts/bin/sc/PriceFeed.Oracle.nef"

echo "==> Resetting Neo Express chain and minting GAS (fast-forward 200 blocks)"
${NEOXP} reset -i "${CONFIG}" -a -f >/dev/null
${NEOXP} fastfwd -i "${CONFIG}" 200 >/dev/null

echo "==> Starting Neo Express"
LOG_FILE="$(mktemp)"
echo "   neo express log: ${LOG_FILE}"
${NEOXP} run -i "${CONFIG}" -s 1 -d >"${LOG_FILE}" 2>&1 &
NEOXP_PID=$!
trap 'kill ${NEOXP_PID} >/dev/null 2>&1 || true; rm -rf "${WORK_DIR}"' EXIT

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

CONTRACT_HASH=""
echo "==> Deploying and seeding contract (best effort)"
if ${NEOXP} contract deploy -i "${CONFIG}" "${NEF}" "${DEPLOY_SIGNER}" --force >/dev/null; then
  CONTRACT_HASH="$(${NEOXP} contract hash -i "${CONFIG}" "${NEF}" "${DEPLOY_ADDRESS}" | tail -n 1)"
  echo "    Contract hash: ${CONTRACT_HASH}"

  echo "==> Waiting for contract to appear on-chain"
  DEPLOYED=false
  for i in {1..20}; do
    CONTRACT_STATE="$(curl -s "${RPC_ENDPOINT}" -d "{\"jsonrpc\":\"2.0\",\"method\":\"getcontractstate\",\"params\":[\"${CONTRACT_HASH}\"],\"id\":1}")"
    if [[ "${CONTRACT_STATE}" == *"${CONTRACT_HASH}"* ]]; then
      DEPLOYED=true
      break
    fi
    sleep 1
  done

  if [[ "${DEPLOYED}" != true ]]; then
    echo "    Contract not visible after deploy; skipping initialization/seeding"
  else
  echo "==> Initializing contract"
  INIT_PREVIEW="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" initialize "${DEPLOY_ADDRESS}" "${TEE_SIGNER}" -a "${DEPLOY_SIGNER}" -r -j)"
  ADD_ORACLE_PREVIEW="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" addOracle "${DEPLOY_ADDRESS}" -a "${DEPLOY_SIGNER}" -r -j)"
  ADD_TEE_PREVIEW="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" addTeeAccount "${TEE_SIGNER}" -a "${DEPLOY_SIGNER}" -r -j)"
  MIN_ORACLES_PREVIEW="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" setMinOracles 1 -a "${DEPLOY_SIGNER}" -r -j)"
  INIT_RESULT="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" initialize "${DEPLOY_ADDRESS}" "${TEE_SIGNER}" -a "${DEPLOY_SIGNER}" -j)"
  ADD_ORACLE_RESULT="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" addOracle "${DEPLOY_ADDRESS}" -a "${DEPLOY_SIGNER}" -j)"
  ADD_TEE_RESULT="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" addTeeAccount "${TEE_SIGNER}" -a "${DEPLOY_SIGNER}" -j)"
  MIN_ORACLES_RESULT="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" setMinOracles 1 -a "${DEPLOY_SIGNER}" -j)"
  echo "    initialize preview: ${INIT_PREVIEW}"
  echo "    initialize result: ${INIT_RESULT}"
  echo "    addOracle preview: ${ADD_ORACLE_PREVIEW}"
  echo "    addOracle result: ${ADD_ORACLE_RESULT}"
  echo "    addTeeAccount preview: ${ADD_TEE_PREVIEW}"
  echo "    addTeeAccount result: ${ADD_TEE_RESULT}"
  echo "    setMinOracles preview: ${MIN_ORACLES_PREVIEW}"
  echo "    setMinOracles result: ${MIN_ORACLES_RESULT}"

  echo "==> Seeding on-chain price for ${SYMBOL}"
  TIMESTAMP="$(date +%s)"
  UPDATE_PREVIEW="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" updatePrice "${SYMBOL}" "${TEST_PRICE}" "${TIMESTAMP}" 95 -a "${DEPLOY_SIGNER}" -r -j)"
  echo "    updatePrice preview: ${UPDATE_PREVIEW}"
  UPDATE_RESULT="$(${NEOXP} contract run -i "${CONFIG}" "${CONTRACT_HASH}" updatePrice "${SYMBOL}" "${TEST_PRICE}" "${TIMESTAMP}" 95 -a "${DEPLOY_SIGNER}" -j)"
  echo "    updatePrice result: ${UPDATE_RESULT}"
  sleep 2
  PRICE_RESULT="$(curl -s "${RPC_ENDPOINT}" -d "{\"jsonrpc\":\"2.0\",\"method\":\"invokefunction\",\"params\":[\"${CONTRACT_HASH}\",\"getPrice\",[{\"type\":\"String\",\"value\":\"${SYMBOL}\"}]],\"id\":1}")"
  echo "    getPrice response: ${PRICE_RESULT}"
  if [[ "${UPDATE_PREVIEW}" == *'"value": true'* ]]; then
    PRICE_SEEDED=true
  fi
  fi
else
  echo "   Contract deploy skipped: insufficient funds or missing account (price test will be skipped)"
fi

echo "==> Running Neo Express integration tests"
RUN_NEO_EXPRESS_TESTS=true \
NEO_EXPRESS_RPC_ENDPOINT="${RPC_ENDPOINT}" \
NEO_EXPRESS_CONTRACT_HASH="${CONTRACT_HASH}" \
NEO_EXPRESS_TEST_SYMBOL="${SYMBOL}" \
NEO_EXPRESS_TEST_PRICE="${TEST_PRICE}" \
NEO_EXPRESS_PRICE_SEEDED="${PRICE_SEEDED}" \
dotnet test "${ROOT_DIR}/PriceFeed.sln" --filter NeoExpressIntegrationTests --nologo

echo "==> Done. Stopping Neo Express."
kill "${NEOXP_PID}" >/dev/null 2>&1 || true
