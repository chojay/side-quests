/**
 * Embedding Store - SQLite wrapper for vector embeddings
 *
 * Uses Zotero.DBConnection to create a separate SQLite database
 * at {ZoteroDataDir}/claude-assistant-embeddings.sqlite
 *
 * Schema:
 *   meta(key TEXT PK, value TEXT)  - model version, dimension, etc.
 *   embeddings(chunk_id TEXT PK, item_key TEXT, embedding BLOB, model_version TEXT)
 */

import { EMBEDDING_DIM, MODEL_VERSION } from './embedding-service';

declare const Zotero: any;

const SCHEMA_VERSION = 1;
// EMBEDDING_DIM is imported from embedding-service so the store can never drift
// from the model that actually produces the vectors. It was previously a second,
// independent literal here (384 for bge-small-en-v1.5), which is exactly the kind
// of duplicate constant that silently goes stale on a model change.

export class EmbeddingStore {
  private db: any = null;
  /** True when initialize() discarded vectors because the model or dimension changed.
   *  Callers should tell the user to re-run Generate Embeddings. */
  public wipedOnUpgrade: boolean = false;
  private _initialized: boolean = false;

  /**
   * Initialize the SQLite database and ensure schema exists
   */
  async initialize(): Promise<void> {
    if (this._initialized) return;

    try {
      // Zotero.DBConnection creates {name}.sqlite in the Zotero data directory
      this.db = new Zotero.DBConnection('claude-assistant-embeddings');

      // Create tables if they don't exist
      await this.db.queryAsync(`
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT
        )
      `);

      await this.db.queryAsync(`
        CREATE TABLE IF NOT EXISTS embeddings (
          chunk_id TEXT PRIMARY KEY,
          item_key TEXT NOT NULL,
          embedding BLOB NOT NULL,
          model_version TEXT NOT NULL
        )
      `);

      // Create index on item_key for fast removal by item
      await this.db.queryAsync(`
        CREATE INDEX IF NOT EXISTS idx_embeddings_item_key ON embeddings(item_key)
      `);

      // Set meta if not exists
      const version = await this.db.valueQueryAsync(
        `SELECT value FROM meta WHERE key = 'schema_version'`
      );
      // Check if model has changed - if so, clear stale embeddings
      const storedModel = await this.db.valueQueryAsync(
        `SELECT value FROM meta WHERE key = 'model'`
      );
      // Imported, NOT re-declared. This was previously a hardcoded second copy of
      // the model name. Because it was independent of MODEL_VERSION, changing the
      // shipped model would leave this literal stale, the wipe below would never
      // fire, and vectors from the old model would be silently compared against the
      // new model's query vectors. That is exactly what the 2.4.0 bge to e5 switch
      // would have triggered.
      const currentModel = MODEL_VERSION;
      const storedDim = await this.db.valueQueryAsync(
        `SELECT value FROM meta WHERE key = 'dim'`
      );

      const modelChanged = !!storedModel && storedModel !== currentModel;
      // Dimension is checked independently: a model can keep its name across a
      // re-export that changes output shape, and a length mismatch is unrecoverable.
      const dimChanged = !!storedDim && String(storedDim) !== String(EMBEDDING_DIM);

      if (modelChanged || dimChanged) {
        const why = modelChanged
          ? `model changed (${storedModel} to ${currentModel})`
          : `dimension changed (${storedDim} to ${EMBEDDING_DIM})`;
        Zotero.debug(`Claude Assistant: ${why}, clearing stale embeddings`);
        await this.db.queryAsync(`DELETE FROM embeddings`);
        this.wipedOnUpgrade = true;
      }

      // Set/update meta
      await this.db.queryAsync(
        `INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)`,
        [String(SCHEMA_VERSION)]
      );
      await this.db.queryAsync(
        `INSERT OR REPLACE INTO meta (key, value) VALUES ('model', ?)`,
        [currentModel]
      );
      await this.db.queryAsync(
        `INSERT OR REPLACE INTO meta (key, value) VALUES ('dim', ?)`,
        [String(EMBEDDING_DIM)]
      );

      this._initialized = true;
      Zotero.debug('Claude Assistant: EmbeddingStore initialized');
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: EmbeddingStore init failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Check if a chunk already has an embedding
   */
  async hasEmbedding(chunkId: string): Promise<boolean> {
    if (!this.db) return false;
    const count = await this.db.valueQueryAsync(
      `SELECT COUNT(*) FROM embeddings WHERE chunk_id = ?`,
      [chunkId]
    );
    return count > 0;
  }

  /**
   * Decode a BLOB column into a Float32Array.
   *
   * The previous one-liner was `new Float32Array(row.embedding.buffer || row.embedding)`.
   * When Zotero's storage layer hands a BLOB back as a plain array of octets rather
   * than a typed array, `.buffer` is undefined and the fallback ran the array-LIKE
   * constructor, producing a 1536-element Float32Array holding byte magnitudes 0 to 255
   * instead of 384 unit-norm floats. Neither branch threw and no length was checked, so
   * cosine similarity silently ranked against garbage. Validate instead of guessing.
   */
  private static decodeVector(value: any): Float32Array | null {
    let bytes: Uint8Array;
    if (value instanceof Uint8Array) {
      bytes = value;
    } else if (value && value.buffer instanceof ArrayBuffer) {
      bytes = new Uint8Array(value.buffer, value.byteOffset || 0, value.byteLength);
    } else if (Array.isArray(value)) {
      bytes = Uint8Array.from(value);
    } else {
      Zotero.debug('Claude Assistant: embedding BLOB has unrecognized representation; dropping');
      return null;
    }
    if (bytes.byteLength !== EMBEDDING_DIM * 4) {
      Zotero.debug(
        `Claude Assistant: embedding BLOB is ${bytes.byteLength} bytes, expected ` +
        `${EMBEDDING_DIM * 4} for ${EMBEDDING_DIM}-dim vectors; dropping. ` +
        'This usually means the store still holds vectors from a previous model.'
      );
      return null;
    }
    if (bytes.byteLength === 0 || bytes.byteLength % 4 !== 0) {
      Zotero.debug(
        `Claude Assistant: embedding BLOB length ${bytes.byteLength} is not a multiple of 4; dropping`
      );
      return null;
    }
    // Copy so the view owns aligned memory regardless of the source byteOffset.
    return new Float32Array(bytes.slice().buffer);
  }

  /**
   * Get embedding for a single chunk
   */
  async getEmbedding(chunkId: string): Promise<Float32Array | null> {
    if (!this.db) return null;
    const row = await this.db.rowQueryAsync(
      `SELECT embedding FROM embeddings WHERE chunk_id = ?`,
      [chunkId]
    );
    if (!row || !row.embedding) return null;
    return EmbeddingStore.decodeVector(row.embedding);
  }

  /**
   * Store embedding for a single chunk
   */
  async setEmbedding(chunkId: string, itemKey: string, embedding: Float32Array, modelVersion: string): Promise<void> {
    if (!this.db) return;
    // Convert Float32Array to ArrayBuffer for BLOB storage
    const buffer = new Uint8Array(embedding.buffer, embedding.byteOffset, embedding.byteLength);
    await this.db.queryAsync(
      `INSERT OR REPLACE INTO embeddings (chunk_id, item_key, embedding, model_version) VALUES (?, ?, ?, ?)`,
      [chunkId, itemKey, buffer, modelVersion]
    );
  }

  /**
   * Store embeddings in batch (within a transaction for performance)
   */
  async setBatchEmbeddings(
    entries: Array<{ chunkId: string; itemKey: string; embedding: Float32Array }>,
    modelVersion: string
  ): Promise<void> {
    if (!this.db || entries.length === 0) return;

    await this.db.executeTransaction(async () => {
      for (const entry of entries) {
        const buffer = new Uint8Array(
          entry.embedding.buffer,
          entry.embedding.byteOffset,
          entry.embedding.byteLength
        );
        await this.db.queryAsync(
          `INSERT OR REPLACE INTO embeddings (chunk_id, item_key, embedding, model_version) VALUES (?, ?, ?, ?)`,
          [entry.chunkId, entry.itemKey, buffer, modelVersion]
        );
      }
    });
  }

  /**
   * Remove all embeddings for a given item
   */
  async removeItemEmbeddings(itemKey: string): Promise<void> {
    if (!this.db) return;
    await this.db.queryAsync(
      `DELETE FROM embeddings WHERE item_key = ?`,
      [itemKey]
    );
  }

  /**
   * Get all embeddings (for loading into memory cache)
   * Returns Map<chunkId, Float32Array>
   */
  async getAllEmbeddings(): Promise<Map<string, Float32Array>> {
    const result = new Map<string, Float32Array>();
    if (!this.db) return result;

    const rows = await this.db.queryAsync(
      `SELECT chunk_id, embedding FROM embeddings`
    );

    let dropped = 0;
    for (const row of rows) {
      if (!row.embedding) continue;
      const v = EmbeddingStore.decodeVector(row.embedding);
      if (v) {
        result.set(row.chunk_id, v);
      } else {
        dropped++;
      }
    }
    if (dropped > 0) {
      Zotero.debug(`Claude Assistant: dropped ${dropped} stored embeddings that failed validation`);
    }

    return result;
  }

  /**
   * Get the number of stored embeddings
   */
  async getEmbeddingCount(): Promise<number> {
    if (!this.db) return 0;
    const count = await this.db.valueQueryAsync(
      `SELECT COUNT(*) FROM embeddings`
    );
    return Number(count) || 0;
  }

  /**
   * Get model version from meta table
   */
  async getModelVersion(): Promise<string | null> {
    if (!this.db) return null;
    return await this.db.valueQueryAsync(
      `SELECT value FROM meta WHERE key = 'model'`
    );
  }

  /**
   * Clear all embeddings
   */
  async clear(): Promise<void> {
    if (!this.db) return;
    await this.db.queryAsync(`DELETE FROM embeddings`);
    Zotero.debug('Claude Assistant: EmbeddingStore cleared');
  }

  /**
   * Close the database connection
   */
  async close(): Promise<void> {
    if (this.db) {
      await this.db.closeDatabase();
      this.db = null;
      this._initialized = false;
    }
  }
}
