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

declare const Zotero: any;

const SCHEMA_VERSION = 1;
const EMBEDDING_DIM = 384; // bge-small-en-v1.5

export class EmbeddingStore {
  private db: any = null;
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
      const currentModel = 'bge-small-en-v1.5';

      if (storedModel && storedModel !== currentModel) {
        Zotero.debug(`Claude Assistant: Model changed (${storedModel} → ${currentModel}), clearing old embeddings`);
        await this.db.queryAsync(`DELETE FROM embeddings`);
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
   * Get embedding for a single chunk
   */
  async getEmbedding(chunkId: string): Promise<Float32Array | null> {
    if (!this.db) return null;
    const row = await this.db.rowQueryAsync(
      `SELECT embedding FROM embeddings WHERE chunk_id = ?`,
      [chunkId]
    );
    if (!row || !row.embedding) return null;
    return new Float32Array(row.embedding.buffer || row.embedding);
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

    for (const row of rows) {
      if (row.embedding) {
        const float32 = new Float32Array(
          row.embedding.buffer || row.embedding
        );
        result.set(row.chunk_id, float32);
      }
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
