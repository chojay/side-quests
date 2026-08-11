#!/usr/bin/env bash
#
# fetch-model.sh
#
# Downloads the quantized ONNX weights for the bge-small-en-v1.5 embedding
# model used by the semantic-search half of the hybrid retriever.
#
# The weights (~32 MB) are intentionally NOT committed to git. The model's
# config + tokenizer JSON files ARE committed (a few hundred KB) so the
# architecture is visible in the repo; this script only fetches the binary.
#
# Source: https://huggingface.co/Xenova/bge-small-en-v1.5 (Transformers.js port)
#
# Usage:  ./scripts/fetch-model.sh

set -euo pipefail

REPO="Xenova/bge-small-en-v1.5"
FILE="onnx/model_quantized.onnx"
URL="https://huggingface.co/${REPO}/resolve/main/${FILE}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="${SCRIPT_DIR}/../addon/content/models/bge-small-en-v1.5/onnx"
DEST="${DEST_DIR}/model_quantized.onnx"

mkdir -p "${DEST_DIR}"

if [ -f "${DEST}" ]; then
  echo "Model already present at: ${DEST}"
  echo "Delete it and re-run to force a fresh download."
  exit 0
fi

echo "Downloading ${REPO} -> ${DEST}"
curl -L --fail --progress-bar -o "${DEST}" "${URL}"

echo "Done. Model saved to: ${DEST}"
