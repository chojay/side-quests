/**
 * Embedding Service - ChromeWorker manager for Transformers.js
 *
 * Manages a ChromeWorker that runs intfloat/e5-base-v2 (quantized ONNX)
 * via Transformers.js for generating 768-dim embeddings.
 *
 * WHY e5-base-v2 rather than bge-small-en-v1.5:
 * an external indexer (not in this repo) had produced e5-base-v2 vectors when
 * 2.4.0 was written, so e5 was the model that actually had data. Using the same
 * model and prefixes makes the /claude-assistant/embed query vectors intended to be
 * comparable with such a store. This plugin uses the int8-quantized ONNX export,
 * so the agreement has not been measured.
 *
 * E5 IS PREFIX-SENSITIVE. Documents must be embedded as "passage: <text>" and
 * queries as "query: <text>". Mixing them up does not error, it just quietly
 * degrades retrieval, so the prefix is applied here from an explicit, required
 * argument rather than being left to each call site to remember.
 */

declare const Zotero: any;
declare const ChromeWorker: any;

export const MODEL_VERSION = 'e5-base-v2';
/** Output dimensionality of e5-base-v2. Written to the store meta and reported by /status; the worker-reported dim is not checked yet. */
export const EMBEDDING_DIM = 768;

/** Which side of the retrieval pair a text is. e5 requires a different prefix for each. */
export type EmbedKind = 'query' | 'passage';

function applyE5Prefix(text: string, kind: EmbedKind): string {
  return (kind === 'query' ? 'query: ' : 'passage: ') + text;
}

/**
 * Why the service is not available. Kept as a machine-readable code plus a
 * human-readable message so callers (the /embed endpoint, the preferences
 * pane, scripts/doctor.js) can tell the user what to actually DO about it,
 * instead of reporting a bare "not available".
 */
export type EmbeddingUnavailableCode =
  | 'ok'
  | 'worker_spawn_failed'
  | 'init_timeout'
  | 'runtime_missing'
  | 'model_weights_missing'
  | 'worker_error'
  | 'unknown';

export interface EmbeddingStatus {
  available: boolean;
  code: EmbeddingUnavailableCode;
  message: string;
  modelVersion: string;
  /** Output dimensionality, so a caller can reject a mismatched vector store. */
  dim: number;
  remedy: string | null;
}

const REMEDIES: Record<EmbeddingUnavailableCode, string | null> = {
  ok: null,
  worker_spawn_failed:
    'The embedding ChromeWorker could not be started. Reinstall the plugin from a build produced by "npm run build".',
  init_timeout:
    'The embedding model did not finish loading within 60 s. This is usually a missing or truncated model_quantized.onnx. Run "npm run doctor" in the source tree to check, then "./scripts/fetch-model.sh" and rebuild.',
  runtime_missing:
    'Transformers.js or the ONNX Runtime WASM files are missing from the packaged plugin. Run "npm install" then "npm run build"; do not package from a tree without node_modules.',
  model_weights_missing:
    'The e5-base-v2 ONNX weights are missing. Run "./scripts/fetch-model.sh" and rebuild the plugin.',
  worker_error:
    'The embedding worker crashed. Check the Zotero debug output for the underlying error.',
  unknown: 'Check the Zotero debug output for the underlying error.',
};

export class EmbeddingService {
  private worker: any = null;
  private available: boolean = false;
  private statusCode: EmbeddingUnavailableCode = 'unknown';
  private statusMessage: string = 'Embedding service has not been initialized yet.';
  private pendingRequests: Map<number, {
    resolve: (value: any) => void;
    reject: (reason: any) => void;
  }> = new Map();
  private nextRequestId: number = 0;
  private rootURI: string = '';

  constructor(rootURI: string) {
    this.rootURI = rootURI;
  }

  /**
   * Initialize the ChromeWorker and load the model
   */
  async initialize(): Promise<void> {
    try {
      // Create ChromeWorker pointing to our worker script
      const workerURL = this.rootURI + 'content/scripts/embedding-worker.js';
      this.worker = new ChromeWorker(workerURL);

      // Set up message handler
      this.worker.onmessage = (event: any) => {
        this.handleWorkerMessage(event.data);
      };

      this.worker.onerror = (error: any) => {
        Zotero.debug(`Claude Assistant: EmbeddingService worker error: ${error.message}`);
        this.available = false;
        this.statusCode = 'worker_error';
        this.statusMessage = error?.message || 'Unknown worker error.';
        // Reject all pending requests
        for (const [id, pending] of this.pendingRequests) {
          pending.resolve(null);
        }
        this.pendingRequests.clear();
      };

      // Send init message with model location.
      //
      // modelRoot and modelId are kept SEPARATE for clarity. A single combined
      // path for both roles would double in Transformers.js versions that always
      // join env.localModelPath; 3.8.1 skips the join for a URL model id, so
      // 2.2.0 should not have hit this (read from the library code).
      const modelRoot = this.rootURI + 'content/models/';
      const modelId = MODEL_VERSION;
      const transformersPath = this.rootURI + 'content/scripts/transformers.min.js';
      // Directory holding the vendored ONNX Runtime .wasm/.mjs files. Without this
      // the worker silently falls back to a jsdelivr CDN, which breaks offline use
      // and contradicts this project's "embedding never touches the network" claim.
      const ortWasmPath = this.rootURI + 'content/scripts/';

      const ready = await this.sendRequest('init', {
        modelRoot,
        modelId,
        transformersPath,
        ortWasmPath,
      }, 60000); // 60s timeout for model loading

      if (ready && ready.status === 'ready') {
        this.available = true;
        this.statusCode = 'ok';
        this.statusMessage = 'Embedding service ready.';
        Zotero.debug('Claude Assistant: EmbeddingService ready');
      } else if (ready === null) {
        // sendRequest() resolves null on timeout. Distinguish that from a
        // worker that answered but reported a problem, because the remedies differ.
        this.available = false;
        this.statusCode = 'init_timeout';
        this.statusMessage =
          'The embedding worker did not respond to init within 60 s. The model weights are most likely missing or truncated.';
        Zotero.debug(`Claude Assistant: EmbeddingService init timed out. ${REMEDIES.init_timeout}`);
      } else {
        this.available = false;
        this.statusCode = this.classifyWorkerFailure(ready);
        this.statusMessage =
          (ready && (ready.message || ready.error)) ||
          'The embedding worker reported that it could not initialize.';
        Zotero.debug(
          `Claude Assistant: EmbeddingService failed to initialize (${this.statusCode}): ${this.statusMessage}`
        );
      }
    } catch (error: any) {
      this.available = false;
      this.statusCode = 'worker_spawn_failed';
      this.statusMessage = error?.message || String(error);
      Zotero.debug(`Claude Assistant: EmbeddingService init failed: ${this.statusMessage}`);
      // Deliberately not rethrown: BM25 retrieval still works without embeddings.
      // The failure is NOT swallowed though; getStatus() carries the reason and
      // addon.ts surfaces it to the user on startup.
    }
  }

  /**
   * Check if the embedding service is available
   */
  isAvailable(): boolean {
    return this.available;
  }

  /**
   * Get the model version string
   */
  getModelVersion(): string {
    return MODEL_VERSION;
  }

  /**
   * Full status, including WHY the service is unavailable and what to do about it.
   * Callers should prefer this over the bare isAvailable() boolean whenever the
   * result is shown to a human.
   */
  getStatus(): EmbeddingStatus {
    return {
      available: this.available,
      code: this.statusCode,
      message: this.statusMessage,
      modelVersion: MODEL_VERSION,
      dim: EMBEDDING_DIM,
      remedy: REMEDIES[this.statusCode] ?? REMEDIES.unknown,
    };
  }

  /**
   * Map a worker init failure payload onto a specific cause. The worker reports
   * the failing resource when it can, which lets us tell "you never ran
   * fetch-model.sh" apart from "you packaged without node_modules".
   */
  private classifyWorkerFailure(payload: any): EmbeddingUnavailableCode {
    const text = String(
      (payload && (payload.message || payload.error)) || ''
    ).toLowerCase();
    if (!text) return 'unknown';
    if (text.includes('.onnx') || text.includes('model_quantized') || text.includes('weights')) {
      return 'model_weights_missing';
    }
    if (text.includes('transformers') || text.includes('ort') || text.includes('wasm')) {
      return 'runtime_missing';
    }
    return 'unknown';
  }

  /**
   * Generate embedding for a single text
   */
  async embed(text: string, kind: EmbedKind): Promise<Float32Array | null> {
    if (!this.available || !this.worker) return null;

    try {
      const result = await this.sendRequest('embed', { text: applyE5Prefix(text, kind) }, 30000);
      if (result && result.embedding) {
        return new Float32Array(result.embedding);
      }
      return null;
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: embed() failed: ${error.message}`);
      return null;
    }
  }

  /**
   * Generate embeddings for a batch of texts
   */
  async embedBatch(
    texts: string[],
    kind: EmbedKind,
    onProgress?: (completed: number, total: number) => void
  ): Promise<(Float32Array | null)[]> {
    if (!this.available || !this.worker) {
      return texts.map(() => null);
    }

    try {
      const result = await this.sendRequest('embed_batch', {
        texts: texts.map((t) => applyE5Prefix(t, kind)),
      }, 600000, // 10 min timeout for large batches
        (data: any) => {
          // Handle progress messages
          if (data.type === 'progress' && onProgress) {
            onProgress(data.completed, data.total);
          }
        }
      );

      if (result && result.embeddings) {
        return result.embeddings.map((emb: any) =>
          emb ? new Float32Array(emb) : null
        );
      }
      return texts.map(() => null);
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: embedBatch() failed: ${error.message}`);
      return texts.map(() => null);
    }
  }

  /**
   * Send a request to the worker and await the response
   */
  private sendRequest(
    type: string,
    data: any,
    timeoutMs: number = 30000,
    onProgress?: (data: any) => void
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      const id = this.nextRequestId++;

      const timer = setTimeout(() => {
        this.pendingRequests.delete(id);
        resolve(null); // Timeout → null, not error
      }, timeoutMs);

      this.pendingRequests.set(id, {
        resolve: (value: any) => {
          clearTimeout(timer);
          this.pendingRequests.delete(id);
          resolve(value);
        },
        reject: (reason: any) => {
          clearTimeout(timer);
          this.pendingRequests.delete(id);
          reject(reason);
        },
      });

      // Store progress handler on the pending request
      if (onProgress) {
        (this.pendingRequests.get(id) as any).onProgress = onProgress;
      }

      this.worker.postMessage({ type, id, ...data });
    });
  }

  /**
   * Handle messages from the worker
   */
  private handleWorkerMessage(data: any): void {
    const { id, type } = data;

    if (type === 'progress') {
      // Route progress to the pending request's progress handler
      const pending = this.pendingRequests.get(id) as any;
      if (pending?.onProgress) {
        pending.onProgress(data);
      }
      return;
    }

    const pending = this.pendingRequests.get(id);
    if (!pending) return;

    if (type === 'error') {
      Zotero.debug(`Claude Assistant: Worker error for request ${id}: ${data.message}`);
      // Resolve the error payload, not null: null means timeout, and initialize()
      // needs the worker's message to pick the right remedy. embed() and
      // embedBatch() see no embedding field and return null as before.
      pending.resolve({ type: 'error', message: data.message });
    } else {
      pending.resolve(data);
    }
  }

  /**
   * Shut down the worker
   */
  destroy(): void {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    this.available = false;
    for (const [id, pending] of this.pendingRequests) {
      pending.resolve(null);
    }
    this.pendingRequests.clear();
  }
}
