#!/usr/bin/env bash
#
# fetch-model.sh
#
# Downloads the quantized ONNX weights for the intfloat/e5-base-v2 embedding
# model used by the semantic-search half of the hybrid retriever.
#
# The weights (~110 MB) are intentionally NOT committed to git. The model's
# config + tokenizer JSON files ARE committed (a few hundred KB) so the
# architecture is visible in the repo; this script only fetches the binary.
#
# Source: https://huggingface.co/Xenova/e5-base-v2 (Transformers.js ONNX port of
#         https://huggingface.co/intfloat/e5-base-v2)
#
# e5 was chosen over bge-small-en-v1.5 because an external indexer (not in this
# repo) had stored e5-base-v2 vectors when 2.4.0 was written. Same model and
# prefixes make the vectors intended to be comparable (not measured; this is the
# int8-quantized export).
#
# Usage:  ./scripts/fetch-model.sh

set -euo pipefail

REPO="Xenova/e5-base-v2"
FILE="onnx/model_quantized.onnx"
URL="https://huggingface.co/${REPO}/resolve/main/${FILE}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="${SCRIPT_DIR}/../addon/content/models/e5-base-v2/onnx"
DEST="${DEST_DIR}/model_quantized.onnx"

mkdir -p "${DEST_DIR}"

if [ -f "${DEST}" ]; then
  echo "Model already present at: ${DEST}"
  echo "Delete it and re-run to force a fresh download."
  exit 0
fi

# Minimum plausible size for the quantized e5-base weights (roughly 110 MB real).
# A truncated or HTML-error-page download used to land on disk looking like a
# success, and the build would then happily package a model file that could never load.
MIN_BYTES=50000000

echo "Downloading ${REPO} -> ${DEST}"
TMP="${DEST}.partial"
rm -f "${TMP}"

# Remove the partial file on any exit path (curl failure, size check, Ctrl-C).
# After the final mv the file no longer exists, so the cleanup is a no-op.
cleanup() { rm -f "${TMP}"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
curl -L --fail --progress-bar -o "${TMP}" "${URL}"

# Verify before moving into place, so a failed fetch never leaves a file that
# looks valid to scripts/build.js.
if [ ! -f "${TMP}" ]; then
  echo "ERROR: download produced no file." >&2
  exit 1
fi

SIZE=$(wc -c < "${TMP}" | tr -d ' ')
if [ "${SIZE}" -lt "${MIN_BYTES}" ]; then
  echo "ERROR: downloaded file is only ${SIZE} bytes, expected at least ${MIN_BYTES}." >&2
  echo "       This is usually an HTML error page rather than the model." >&2
  rm -f "${TMP}"
  exit 1
fi

# ONNX files start with the protobuf magic for the ir_version field (0x08).
if ! head -c 1 "${TMP}" | od -An -tx1 | grep -q '08'; then
  echo "WARNING: file does not begin with the expected ONNX protobuf byte." >&2
  echo "         Continuing, but run 'npm run doctor' to confirm." >&2
fi

mv "${TMP}" "${DEST}"

echo "Done. Model saved to: ${DEST} (${SIZE} bytes)"
echo
echo "Next: npm install && npm run build"
echo "Verify anytime with: npm run doctor"
