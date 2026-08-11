/**
 * Preferences Management
 * Handles plugin settings and configuration
 */

declare const Zotero: any;

export class Preferences {
  private static readonly PREF_BRANCH = 'extensions.claudeassistant.';

  // Preference keys
  static readonly CLAUDE_API_KEY = 'claudeApiKey';
  static readonly CLAUDE_MODEL = 'claudeModel';
  static readonly CHUNK_SIZE = 'chunkSize';
  static readonly CHUNK_OVERLAP = 'chunkOverlap';
  static readonly MAX_RESULTS = 'maxResults';
  static readonly QUERY_REWRITING = 'queryRewriting';

  /**
   * Register default preferences
   */
  static registerDefaults(): void {
    const defaults: Record<string, string> = {
      [this.CLAUDE_API_KEY]: '',
      [this.CLAUDE_MODEL]: 'claude-sonnet-4-6',
      [this.CHUNK_SIZE]: '2000', // ~500 tokens per chunk; keeps section context together
      [this.CHUNK_OVERLAP]: '400', // 20% overlap for context continuity
      [this.MAX_RESULTS]: '25', // Claude's 200K context easily handles 25 chunks (~12K tokens)
      [this.QUERY_REWRITING]: 'false', // Optional: adds one API call per query for better recall
    };

    for (const [key, value] of Object.entries(defaults)) {
      const prefKey = this.PREF_BRANCH + key;
      // Only set if not already set
      if (!Zotero.Prefs.get(prefKey, true)) {
        Zotero.Prefs.set(prefKey, value, true);
      }
    }
  }

  /**
   * Get a preference value
   */
  static get(key: string): string {
    return Zotero.Prefs.get(this.PREF_BRANCH + key, true) || '';
  }

  /**
   * Set a preference value
   */
  static set(key: string, value: string | number | boolean): void {
    Zotero.Prefs.set(this.PREF_BRANCH + key, value, true);
  }

  /**
   * Get Claude API key
   */
  static getApiKey(): string {
    return this.get(this.CLAUDE_API_KEY);
  }

  /**
   * Set Claude API key
   */
  static setApiKey(key: string): void {
    this.set(this.CLAUDE_API_KEY, key);
  }

  /**
   * Get Claude model
   */
  static getModel(): string {
    return this.get(this.CLAUDE_MODEL);
  }

  /**
   * Get chunk size
   */
  static getChunkSize(): number {
    return parseInt(this.get(this.CHUNK_SIZE), 10) || 2000;
  }

  /**
   * Get chunk overlap
   */
  static getChunkOverlap(): number {
    return parseInt(this.get(this.CHUNK_OVERLAP), 10) || 400;
  }

  /**
   * Get max results
   */
  static getMaxResults(): number {
    return parseInt(this.get(this.MAX_RESULTS), 10) || 25;
  }

  /**
   * Get query rewriting setting
   */
  static getQueryRewriting(): boolean {
    return this.get(this.QUERY_REWRITING) === 'true';
  }

  /**
   * Validate API key format
   */
  static validateApiKey(key: string): boolean {
    // Basic validation - Claude API keys start with "sk-"
    return key.startsWith('sk-ant-') && key.length > 20;
  }

  /**
   * Get all preferences as an object
   */
  static getAll(): Record<string, any> {
    return {
      apiKey: this.getApiKey(),
      model: this.getModel(),
      chunkSize: this.getChunkSize(),
      chunkOverlap: this.getChunkOverlap(),
      maxResults: this.getMaxResults(),
      queryRewriting: this.getQueryRewriting(),
    };
  }
}
