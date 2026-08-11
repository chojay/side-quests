/**
 * Embedding Service - ChromeWorker manager for Transformers.js
 *
 * Manages a ChromeWorker that runs bge-small-en-v1.5 (34MB ONNX)
 * via Transformers.js for generating 384-dim embeddings.
 */

declare const Zotero: any;
declare const ChromeWorker: any;

const MODEL_VERSION = 'bge-small-en-v1.5';

export class EmbeddingService {
  private worker: any = null;
  private available: boolean = false;
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
        // Reject all pending requests
        for (const [id, pending] of this.pendingRequests) {
          pending.resolve(null);
        }
        this.pendingRequests.clear();
      };

      // Send init message with model path
      const modelPath = this.rootURI + 'content/models/bge-small-en-v1.5/';
      const transformersPath = this.rootURI + 'content/scripts/transformers.min.js';

      const ready = await this.sendRequest('init', {
        modelPath,
        transformersPath,
      }, 60000); // 60s timeout for model loading

      if (ready && ready.status === 'ready') {
        this.available = true;
        Zotero.debug('Claude Assistant: EmbeddingService ready');
      } else {
        Zotero.debug('Claude Assistant: EmbeddingService failed to initialize');
        this.available = false;
      }
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: EmbeddingService init failed: ${error.message}`);
      this.available = false;
      // Don't rethrow - unavailability is handled gracefully
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
   * Generate embedding for a single text
   */
  async embed(text: string): Promise<Float32Array | null> {
    if (!this.available || !this.worker) return null;

    try {
      const result = await this.sendRequest('embed', { text }, 30000);
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
    onProgress?: (completed: number, total: number) => void
  ): Promise<(Float32Array | null)[]> {
    if (!this.available || !this.worker) {
      return texts.map(() => null);
    }

    try {
      const result = await this.sendRequest('embed_batch', {
        texts,
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
      pending.resolve(null);
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
