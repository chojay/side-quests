# e5-base-v2 ONNX weights

The quantized model weights (`model_quantized.onnx`, roughly 110 MB) are not committed to git.
Fetch them before building:

```bash
./scripts/fetch-model.sh
```

Source: https://huggingface.co/Xenova/e5-base-v2 (Transformers.js ONNX port of
https://huggingface.co/intfloat/e5-base-v2)

Note: e5 requires input prefixes. Documents are embedded as `passage: <text>` and queries as
`query: <text>`. This matches the convention of an external indexer that uses the same
e5 prefixes, so the vectors are intended to be comparable (this is the int8-quantized
export; the agreement has not been measured).
