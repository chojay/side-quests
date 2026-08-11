/**
 * ChromeWorker script for embedding generation via Transformers.js
 *
 * Runs in a separate thread. Communicates with EmbeddingService via postMessage.
 *
 * Messages received:
 *   { type: 'init', id, transformersPath, modelPath } -> load model
 *   { type: 'embed', id, text }                       -> embed single text
 *   { type: 'embed_batch', id, texts }                 -> embed batch of texts
 *
 * Messages sent:
 *   { type: 'ready', id, status: 'ready' }
 *   { type: 'result', id, embedding: ArrayBuffer }
 *   { type: 'result', id, embeddings: ArrayBuffer[] }
 *   { type: 'progress', id, completed, total }
 *   { type: 'error', id, message }
 */

/* globals importScripts, postMessage, onmessage */

var pipeline = null;
var extractor = null;

onmessage = async function(event) {
  var data = event.data;
  var id = data.id;
  var type = data.type;

  try {
    switch (type) {
      case 'init':
        await handleInit(id, data);
        break;
      case 'embed':
        await handleEmbed(id, data);
        break;
      case 'embed_batch':
        await handleEmbedBatch(id, data);
        break;
      default:
        postMessage({ type: 'error', id: id, message: 'Unknown message type: ' + type });
    }
  } catch (err) {
    postMessage({ type: 'error', id: id, message: err.message || String(err) });
  }
};

async function handleInit(id, data) {
  var transformersPath = data.transformersPath;
  var modelPath = data.modelPath;

  // @huggingface/transformers v3.x ships as an ES module (export{}, import.meta)
  // which is incompatible with importScripts(). Instead, fetch as text,
  // patch out ES module syntax, and eval in global scope.

  // 1. Fetch the bundle as text
  var response = await fetch(transformersPath);
  if (!response.ok) {
    throw new Error('Failed to fetch Transformers.js: HTTP ' + response.status);
  }
  var code = await response.text();

  // 2. Parse the export { internalName as exportedName, ... } block
  //    to discover minified variable names for 'pipeline' and 'env'
  var exportMatch = code.match(/export\s*\{([^}]+)\}\s*;?\s*(\/\/[^\n]*)?$/);
  if (!exportMatch) {
    throw new Error('Could not parse Transformers.js export block');
  }

  var exportMap = {};
  exportMatch[1].split(',').forEach(function(item) {
    var parts = item.trim().split(/\s+as\s+/);
    if (parts.length === 2) {
      exportMap[parts[1].trim()] = parts[0].trim();
    } else if (parts.length === 1) {
      exportMap[parts[0].trim()] = parts[0].trim();
    }
  });

  // 3. Remove the export statement (syntax error in non-module context)
  var classicCode = code.substring(0, exportMatch.index);

  // 4. Replace import.meta.url with the bundle's URL string
  //    (import.meta is also a syntax error in non-module context)
  var escapedPath = transformersPath.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  classicCode = classicCode.replace(/import\.meta\.url/g, '("' + escapedPath + '")');
  classicCode = classicCode.replace(/import\.meta/g, '({url:"' + escapedPath + '"})');

  // 5. Indirect eval runs in global scope - var declarations become self.*
  var indirectEval = eval;
  indirectEval(classicCode);

  // 6. Extract pipeline and env using the parsed internal variable names
  var pipelineFn = self[exportMap['pipeline']];
  var envObj = self[exportMap['env']];

  if (!pipelineFn) {
    throw new Error('pipeline function not found after eval (expected self.' + exportMap['pipeline'] + ')');
  }

  // 7. Configure for local-only, single-threaded operation
  if (envObj) {
    envObj.allowRemoteModels = false;
    envObj.allowLocalModels = true;
    envObj.localModelPath = modelPath;
    // Prevent ONNX Runtime from creating sub-workers (unsupported in ChromeWorker)
    if (envObj.backends && envObj.backends.onnx && envObj.backends.onnx.wasm) {
      envObj.backends.onnx.wasm.numThreads = 1;
    }
  }

  // 8. Create the feature extraction pipeline
  extractor = await pipelineFn('feature-extraction', modelPath, {
    quantized: true,
    revision: 'default',
  });

  // 9. Warm up with a test embedding
  var testResult = await extractor('test', { pooling: 'mean', normalize: true });
  var dim = testResult.dims ? testResult.dims[testResult.dims.length - 1] : 0;

  postMessage({
    type: 'ready',
    id: id,
    status: 'ready',
    dim: dim
  });
}

async function handleEmbed(id, data) {
  if (!extractor) {
    postMessage({ type: 'error', id: id, message: 'Model not initialized' });
    return;
  }

  var text = data.text || '';
  // Truncate to ~512 tokens (~2000 chars) to stay within model limits
  if (text.length > 2000) {
    text = text.substring(0, 2000);
  }

  var result = await extractor(text, { pooling: 'mean', normalize: true });

  // Extract the embedding data as a transferable ArrayBuffer
  var embedding;
  if (result.data) {
    // Transformers.js Tensor - .data is Float32Array or TypedArray
    embedding = new Float32Array(result.data).buffer;
  } else if (result instanceof Float32Array) {
    embedding = result.buffer;
  } else {
    embedding = new Float32Array(result).buffer;
  }

  postMessage(
    { type: 'result', id: id, embedding: embedding },
    [embedding] // Transfer ownership for zero-copy
  );
}

async function handleEmbedBatch(id, data) {
  if (!extractor) {
    postMessage({ type: 'error', id: id, message: 'Model not initialized' });
    return;
  }

  var texts = data.texts || [];
  var embeddings = [];
  var batchSize = 8; // Process in sub-batches to avoid memory pressure

  for (var i = 0; i < texts.length; i += batchSize) {
    var batch = texts.slice(i, Math.min(i + batchSize, texts.length));

    for (var j = 0; j < batch.length; j++) {
      var text = batch[j] || '';
      if (text.length > 2000) {
        text = text.substring(0, 2000);
      }

      try {
        var result = await extractor(text, { pooling: 'mean', normalize: true });

        var embedding;
        if (result.data) {
          embedding = new Float32Array(result.data).buffer;
        } else if (result instanceof Float32Array) {
          embedding = result.buffer;
        } else {
          embedding = new Float32Array(result).buffer;
        }

        embeddings.push(embedding);
      } catch (err) {
        // Push null for failed embeddings
        embeddings.push(null);
      }
    }

    // Report progress
    postMessage({
      type: 'progress',
      id: id,
      completed: Math.min(i + batchSize, texts.length),
      total: texts.length
    });
  }

  postMessage(
    { type: 'result', id: id, embeddings: embeddings },
    embeddings.filter(function(e) { return e !== null; }) // Transfer non-null buffers
  );
}
