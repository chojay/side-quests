/**
 * Conversation Store - SQLite persistence for chat conversations
 *
 * Uses Zotero.DBConnection to create a separate SQLite database
 * at {ZoteroDataDir}/claude-assistant-conversations.sqlite
 *
 * Schema:
 *   conversations(id TEXT PK, title TEXT, mode TEXT, created_at TEXT, updated_at TEXT)
 *   messages(id INTEGER PK, conversation_id TEXT, role TEXT, content TEXT, sources TEXT, mode TEXT, timestamp TEXT)
 */

declare const Zotero: any;

export interface ConversationMeta {
  id: string;
  title: string;
  mode: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export interface StoredMessage {
  id: number;
  conversationId: string;
  role: string;
  content: string;
  sources: string | null;
  mode: string | null;
  timestamp: string;
}

export class ConversationStore {
  private db: any = null;
  private _initialized: boolean = false;

  async initialize(): Promise<void> {
    if (this._initialized) return;

    try {
      this.db = new Zotero.DBConnection('claude-assistant-conversations');

      await this.db.queryAsync(`
        CREATE TABLE IF NOT EXISTS conversations (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          mode TEXT NOT NULL DEFAULT 'auto',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
      `);

      await this.db.queryAsync(`
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          conversation_id TEXT NOT NULL,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          sources TEXT,
          mode TEXT,
          timestamp TEXT NOT NULL
        )
      `);

      await this.db.queryAsync(`
        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)
      `);

      await this.db.queryAsync(`
        CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC)
      `);

      this._initialized = true;
      Zotero.debug('Claude Assistant: Conversation store initialized');
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Conversation store init failed: ${error.message}`);
      throw error;
    }
  }

  async createConversation(id: string, title: string, mode: string = 'auto'): Promise<void> {
    const now = new Date().toISOString();
    await this.db.queryAsync(
      `INSERT INTO conversations (id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)`,
      [id, title, mode, now, now]
    );
  }

  async addMessage(
    conversationId: string,
    role: string,
    content: string,
    sources?: string | null,
    mode?: string | null
  ): Promise<number> {
    const now = new Date().toISOString();
    const result = await this.db.queryAsync(
      `INSERT INTO messages (conversation_id, role, content, sources, mode, timestamp) VALUES (?, ?, ?, ?, ?, ?)`,
      [conversationId, role, content, sources || null, mode || null, now]
    );

    // Update conversation timestamp
    await this.db.queryAsync(
      `UPDATE conversations SET updated_at = ? WHERE id = ?`,
      [now, conversationId]
    );

    return result;
  }

  async getConversations(limit: number = 50): Promise<ConversationMeta[]> {
    const rows = await this.db.queryAsync(
      `SELECT c.id, c.title, c.mode, c.created_at, c.updated_at,
              (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
       FROM conversations c
       ORDER BY c.updated_at DESC
       LIMIT ?`,
      [limit]
    );

    return (rows || []).map((r: any) => ({
      id: r.id,
      title: r.title,
      mode: r.mode,
      createdAt: r.created_at,
      updatedAt: r.updated_at,
      messageCount: r.message_count || 0,
    }));
  }

  async getMessages(conversationId: string): Promise<StoredMessage[]> {
    const rows = await this.db.queryAsync(
      `SELECT id, conversation_id, role, content, sources, mode, timestamp
       FROM messages
       WHERE conversation_id = ?
       ORDER BY timestamp ASC`,
      [conversationId]
    );

    return (rows || []).map((r: any) => ({
      id: r.id,
      conversationId: r.conversation_id,
      role: r.role,
      content: r.content,
      sources: r.sources || null,
      mode: r.mode || null,
      timestamp: r.timestamp,
    }));
  }

  async updateConversationTitle(id: string, title: string): Promise<void> {
    await this.db.queryAsync(
      `UPDATE conversations SET title = ? WHERE id = ?`,
      [title, id]
    );
  }

  async deleteConversation(id: string): Promise<void> {
    // No CASCADE in Zotero SQLite - delete manually in transaction
    await this.db.executeTransaction(async () => {
      await this.db.queryAsync(
        `DELETE FROM messages WHERE conversation_id = ?`,
        [id]
      );
      await this.db.queryAsync(
        `DELETE FROM conversations WHERE id = ?`,
        [id]
      );
    });
  }

  async close(): Promise<void> {
    if (this.db) {
      await this.db.closeDatabase();
      this.db = null;
      this._initialized = false;
    }
  }
}
