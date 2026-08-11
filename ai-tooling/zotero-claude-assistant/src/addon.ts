/**
 * Main Addon Class - Local RAG Implementation
 * Entry point for the Claude Research Assistant plugin
 *
 * No external Python server required - uses pure JavaScript BM25 search
 */

import { LocalRAGService, RAGSearchResult, IndexStats } from './modules/local-rag';
import { ClaudeClient, ClaudeResponse, ClaudeMessage } from './modules/claude-api';
import { EmbeddingStore } from './modules/embedding-store';
import { EmbeddingService } from './modules/embedding-service';
import { ConversationStore, ConversationMeta, StoredMessage } from './modules/conversation-store';
import { Preferences } from './prefs';

// Chat mode types
type ChatMode = 'auto' | 'research' | 'chat';

// Response with metadata
interface ChatResponse {
  text: string;
  sources: RAGSearchResult[] | null;
  mode: 'research' | 'chat';
  noResults?: boolean;  // true when research mode found 0 matching papers
  indexStats?: { indexedItems: number; totalChunks: number };  // diagnostic info
  suggestions?: string[];  // follow-up question suggestions
}

declare const Zotero: any;
declare const Components: any;
declare const PathUtils: any;

// Interface for selected paper context
interface PaperContext {
  itemId: number;
  itemKey: string;
  title: string;
  authors: string;
  year: string;
}

export class ClaudeAssistant {
  private localRAG: LocalRAGService | null = null;
  private claudeClient: ClaudeClient | null = null;
  private embeddingStore: EmbeddingStore | null = null;
  private embeddingService: EmbeddingService | null = null;
  private conversationStore: ConversationStore | null = null;
  private currentConversationId: string | null = null;
  private _initialized: boolean = false;
  private _chatWindow: any = null;
  private registeredWindows: Set<any> = new Set();
  private rootURI: string = '';

  // Context-aware paper tracking
  private selectedPapers: PaperContext[] = [];
  private selectionListenerRegistered: boolean = false;

  // Chat mode and conversation history
  private chatMode: ChatMode = 'auto';
  private conversationHistory: ClaudeMessage[] = [];

  // RAG readiness tracking
  private ragInitPromise: Promise<void> | null = null;
  private ragReady: boolean = false;

  /**
   * Initialize the addon
   */
  async init(options: { id: string; version: string; rootURI: string }): Promise<void> {
    Zotero.debug(`Claude Assistant: ===== INIT CALLED =====`);
    Zotero.debug(`Claude Assistant: Version ${options.version}`);
    Zotero.debug(`Claude Assistant: ID ${options.id}`);
    Zotero.debug(`Claude Assistant: Root URI ${options.rootURI}`);

    this.rootURI = options.rootURI;

    try {
      Zotero.debug(`Claude Assistant: Registering preferences...`);
      // Register preferences
      Preferences.registerDefaults();
      Zotero.debug(`Claude Assistant: Preferences registered`);

      // Register preference pane (Zotero 7 method)
      Zotero.debug(`Claude Assistant: Registering preference pane...`);
      Zotero.PreferencePanes.register({
        pluginID: options.id,
        src: options.rootURI + 'content/preferences.xhtml',
        scripts: [options.rootURI + 'content/preferences.js'],
        label: 'Claude Assistant',
        image: options.rootURI + 'content/icons/icon-48.png',
      });
      Zotero.debug(`Claude Assistant: Preference pane registered`);

      // Initialize Local RAG service (no external server needed)
      // Track the promise so smartChat can await it if needed
      Zotero.debug(`Claude Assistant: Starting Local RAG initialization...`);
      this.ragInitPromise = this.initializeLocalRAG().then(() => {
        this.ragReady = true;
        Zotero.debug(`Claude Assistant: RAG initialization complete, ready for queries`);
      }).catch((error) => {
        Zotero.debug(`Claude Assistant: Failed to initialize Local RAG: ${error.message || error}`);
        Zotero.debug(`Claude Assistant: Error stack: ${error.stack}`);
        this.showNotification('RAG initialization failed. Check debug output.', 'error');
      });

      // Initialize conversation store
      try {
        this.conversationStore = new ConversationStore();
        await this.conversationStore.initialize();
        Zotero.debug('Claude Assistant: Conversation store initialized');
      } catch (convError: any) {
        Zotero.debug(`Claude Assistant: Conversation store init failed (non-fatal): ${convError.message}`);
      }

      // Initialize Claude API client if API key is configured
      const apiKey = Preferences.getApiKey();
      if (apiKey && Preferences.validateApiKey(apiKey)) {
        this.claudeClient = new ClaudeClient({
          apiKey,
          model: Preferences.getModel(),
        });
        Zotero.debug('Claude Assistant: Claude API client initialized');
      } else {
        Zotero.debug('Claude Assistant: No valid Claude API key configured');
        this.showNotification(
          'Claude Assistant: Please configure your Claude API key in preferences',
          'warning'
        );
      }

      // Set up event listeners
      this.setupEventListeners();

      // Register localhost-only HTTP endpoint for embedding queries
      // (lets external local tools reuse the plugin's embedder)
      this.registerEmbeddingEndpoint();

      this._initialized = true;
      Zotero.debug('Claude Assistant: Initialization complete');
    } catch (error) {
      Zotero.debug(`Claude Assistant: Initialization error: ${error}`);
      this.showNotification(
        'Claude Assistant: Initialization failed. Check debug output.',
        'error'
      );
    }
  }

  /**
   * Initialize the Local RAG service (pure JavaScript, no external server needed)
   */
  private async initializeLocalRAG(): Promise<void> {
    try {
      Zotero.debug('Claude Assistant: Initializing Local RAG service...');

      // Create local RAG service instance
      this.localRAG = new LocalRAGService();

      // Initialize (load existing index from disk if available)
      await this.localRAG.initialize();

      // Get initial stats
      const stats = this.localRAG.getStats();
      Zotero.debug(`Claude Assistant: Local RAG initialized - ${stats.indexedItems} items, ${stats.totalChunks} chunks`);

      if (stats.indexedItems === 0) {
        Zotero.debug('Claude Assistant: No items indexed yet. Use indexing buttons in preferences to index your library.');
      }

      // Initialize embedding infrastructure (non-blocking - BM25 works without it)
      try {
        this.embeddingStore = new EmbeddingStore();
        await this.embeddingStore.initialize();

        this.embeddingService = new EmbeddingService(this.rootURI);
        await this.embeddingService.initialize();

        if (this.embeddingService.isAvailable()) {
          const embCount = await this.embeddingStore.getEmbeddingCount();
          Zotero.debug(`Claude Assistant: Embedding service ready, ${embCount} embeddings stored`);
        } else {
          Zotero.debug('Claude Assistant: Embedding service not available - BM25 only');
        }

        // Inject embedding services into LocalRAGService for auto-embedding during indexItem()
        if (this.localRAG) {
          this.localRAG.setEmbeddingServices(this.embeddingService, this.embeddingStore);

          // Load embeddings into memory cache for fast search
          if (this.embeddingService.isAvailable()) {
            await this.localRAG.loadEmbeddingCache();
          }
        }
      } catch (embError: any) {
        Zotero.debug(`Claude Assistant: Embedding init failed (non-fatal): ${embError.message}`);
        // BM25 continues working fine
      }

    } catch (error: any) {
      Zotero.debug(`Claude Assistant: ===== LOCAL RAG INITIALIZATION FAILED =====`);
      Zotero.debug(`Claude Assistant: Error: ${error.message || error}`);
      if (error.stack) {
        Zotero.debug(error.stack);
      }
      Zotero.debug(`Claude Assistant: ===== END ERROR DETAILS =====`);
      throw error;
    }
  }

  /**
   * Set the chat mode
   */
  setChatMode(mode: ChatMode): void {
    this.chatMode = mode;
    Zotero.debug(`Claude Assistant: Chat mode set to ${mode}`);
  }

  /**
   * Get current chat mode
   */
  getChatMode(): ChatMode {
    return this.chatMode;
  }

  /**
   * Check if RAG index is loaded and ready for queries
   */
  isRAGReady(): boolean {
    return this.ragReady && this.localRAG !== null;
  }

  /**
   * Wait for RAG to finish initializing (max 10 seconds)
   */
  private async ensureRAGReady(): Promise<void> {
    if (this.ragReady) return;
    if (this.ragInitPromise) {
      const timeout = new Promise<void>((resolve) => setTimeout(resolve, 10000));
      await Promise.race([this.ragInitPromise, timeout]);
    }
  }

  /**
   * Clear conversation history (for new chat)
   */
  clearConversation(): void {
    this.conversationHistory = [];
    this.currentConversationId = null;
    Zotero.debug('Claude Assistant: Conversation history cleared');
  }

  /**
   * Parse follow-up suggestions from Claude's response text
   */
  private parseSuggestions(text: string): { cleanText: string; suggestions: string[] } {
    const suggestionsMatch = text.match(/<<<SUGGESTIONS:\s*([\s\S]*?)>>>/);
    let suggestions: string[] = [];
    let cleanText = text;

    if (suggestionsMatch) {
      cleanText = text.replace(/<<<SUGGESTIONS:[\s\S]*?>>>/, '').trim();
      suggestions = suggestionsMatch[1]
        .split('|||')
        .map(s => s.trim())
        .filter(s => s.length > 0 && s.length < 200)
        .slice(0, 3);
    }

    return { cleanText, suggestions };
  }

  /**
   * Generate a UUID for conversation IDs
   */
  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  // ===== Conversation persistence methods (exposed to dialog) =====

  async startNewConversation(): Promise<string> {
    const id = this.generateUUID();
    this.currentConversationId = id;
    this.conversationHistory = [];
    if (this.conversationStore) {
      await this.conversationStore.createConversation(id, 'New conversation', 'auto');
    }
    return id;
  }

  async loadConversation(id: string): Promise<{ meta: ConversationMeta | null; messages: StoredMessage[] }> {
    if (!this.conversationStore) return { meta: null, messages: [] };

    const conversations = await this.conversationStore.getConversations(100);
    const meta = conversations.find(c => c.id === id) || null;
    const messages = await this.conversationStore.getMessages(id);

    // Restore conversation history for Claude context
    this.currentConversationId = id;
    this.conversationHistory = messages.map(m => ({
      role: m.role as 'user' | 'assistant',
      content: m.content,
    }));
    // Keep manageable
    if (this.conversationHistory.length > 20) {
      this.conversationHistory = this.conversationHistory.slice(-20);
    }

    return { meta, messages };
  }

  async getConversationList(limit?: number): Promise<ConversationMeta[]> {
    if (!this.conversationStore) return [];
    return this.conversationStore.getConversations(limit);
  }

  async deleteConversation(id: string): Promise<void> {
    if (!this.conversationStore) return;
    await this.conversationStore.deleteConversation(id);
    if (this.currentConversationId === id) {
      this.currentConversationId = null;
      this.conversationHistory = [];
    }
  }

  async renameConversation(id: string, title: string): Promise<void> {
    if (!this.conversationStore) return;
    await this.conversationStore.updateConversationTitle(id, title);
  }

  // ===== Source selection methods (exposed to dialog) =====

  private dialogSelectedKeys: string[] = [];

  getIndexedPaperList(): Array<{ itemKey: string; title: string; authors: string; year: string; chunkCount: number }> {
    if (!this.localRAG) return [];
    return this.localRAG.getIndexedPaperList();
  }

  setDialogPaperSelection(keys: string[]): void {
    this.dialogSelectedKeys = keys;
    Zotero.debug(`Claude Assistant: Dialog paper selection updated: ${keys.length > 0 ? keys.length + ' papers' : 'all papers'}`);
  }

  /**
   * Smart chat - automatically routes to RAG or direct chat based on query
   * This is the main entry point for the v2 chat interface
   */
  async smartChat(question: string, forceMode?: 'research' | 'chat'): Promise<ChatResponse> {
    try {
      // Ensure Claude client is initialized
      if (!this.claudeClient) {
        const apiKey = Preferences.getApiKey();
        if (!apiKey || !Preferences.validateApiKey(apiKey)) {
          throw new Error(
            'Claude API key not configured.\n\n' +
            'Go to Tools → Settings → Claude Assistant to set your API key.'
          );
        }
        this.claudeClient = new ClaudeClient({
          apiKey,
          model: Preferences.getModel(),
        });
      }

      // Determine which mode to use
      let useResearch = false;

      if (forceMode) {
        useResearch = forceMode === 'research';
      } else if (this.chatMode === 'auto') {
        // Auto-detect based on query content and paper context
        useResearch = this.selectedPapers.length > 0 ||
                      ClaudeClient.detectResearchIntent(question);
      } else {
        useResearch = this.chatMode === 'research';
      }

      Zotero.debug(`Claude Assistant: Processing query in ${useResearch ? 'research' : 'chat'} mode`);

      if (useResearch) {
        // Wait for RAG to be ready before searching
        await this.ensureRAGReady();
        return await this.askQuestionWithRAG(question);
      } else {
        // Direct chat mode
        return await this.askQuestionDirect(question);
      }

    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Error in smartChat: ${error.message || error}`);
      throw error;
    }
  }

  /**
   * Direct chat with Claude (no RAG context)
   * Used for general conversation
   */
  private async askQuestionDirect(question: string): Promise<ChatResponse> {
    if (!this.claudeClient) {
      throw new Error('Claude client not initialized');
    }

    Zotero.debug(`Claude Assistant: Direct chat query: ${question.substring(0, 50)}...`);

    const response = await this.claudeClient.directChat(question, this.conversationHistory);

    const responseText = ClaudeClient.extractText(response) || 'No response received.';

    // Update conversation history
    this.conversationHistory.push({ role: 'user', content: question });
    this.conversationHistory.push({ role: 'assistant', content: responseText });

    // Keep history manageable (last 20 messages)
    if (this.conversationHistory.length > 20) {
      this.conversationHistory = this.conversationHistory.slice(-20);
    }

    // Persist to conversation store
    if (this.conversationStore && this.currentConversationId) {
      try {
        await this.conversationStore.addMessage(this.currentConversationId, 'user', question, null, 'chat');
        await this.conversationStore.addMessage(this.currentConversationId, 'assistant', responseText, null, 'chat');
      } catch (e: any) {
        Zotero.debug(`Claude Assistant: Failed to persist messages: ${e.message}`);
      }
    }

    return {
      text: responseText,
      sources: null,
      mode: 'chat'
    };
  }

  /**
   * Research mode with RAG - searches papers and uses them as context
   */
  private async askQuestionWithRAG(question: string): Promise<ChatResponse> {
    if (!this.localRAG) {
      throw new Error(
        'Local RAG service not initialized.\n\n' +
        'Please restart Zotero or check Help → Debug Output Logging for errors.'
      );
    }

    if (!this.claudeClient) {
      throw new Error('Claude client not initialized');
    }

    // Get index stats for diagnostics
    const stats = this.localRAG.getStats();
    Zotero.debug(`Claude Assistant: Index has ${stats.indexedItems} items, ${stats.totalChunks} chunks`);

    // If index is empty, tell the user instead of silently falling back
    if (stats.totalChunks === 0) {
      Zotero.debug('Claude Assistant: Index is empty - no papers to search');
      const response = await this.claudeClient.directChat(question, this.conversationHistory);
      const responseText = ClaudeClient.extractText(response) || 'No response received.';

      this.conversationHistory.push({ role: 'user', content: question });
      this.conversationHistory.push({ role: 'assistant', content: responseText });
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }

      return {
        text: responseText,
        sources: [],
        mode: 'research',
        noResults: true,
        indexStats: { indexedItems: stats.indexedItems, totalChunks: stats.totalChunks }
      };
    }

    // Search using local index - use hybrid mode when embeddings are available
    // Scope search to selected papers if any are focused
    Zotero.debug(`Claude Assistant: RAG search for: ${question.substring(0, 50)}...`);
    const maxResults = Preferences.getMaxResults();
    const searchMode = this.embeddingService?.isAvailable() ? 'hybrid' : 'keyword';
    const itemKeys = this.dialogSelectedKeys.length > 0
      ? this.dialogSelectedKeys
      : (this.selectedPapers.length > 0
        ? this.selectedPapers.map(p => p.itemKey)
        : undefined);

    // Query rewriting: expand query into multiple formulations for better recall
    let sources: RAGSearchResult[];
    if (Preferences.getQueryRewriting() && this.claudeClient) {
      try {
        const altQueries = await this.claudeClient.rewriteQuery(question);
        if (altQueries.length > 0) {
          const allQueries = [question, ...altQueries];
          Zotero.debug(`Claude Assistant: Multi-query search with ${allQueries.length} queries`);
          const resultSets: RAGSearchResult[][] = [];
          for (const q of allQueries) {
            resultSets.push(await this.localRAG.search(q, maxResults, searchMode, itemKeys));
          }
          sources = this.localRAG.multiQueryMerge(resultSets, maxResults);
        } else {
          sources = await this.localRAG.search(question, maxResults, searchMode, itemKeys);
        }
      } catch (e: any) {
        Zotero.debug(`Claude Assistant: Query rewriting failed, using original: ${e.message}`);
        sources = await this.localRAG.search(question, maxResults, searchMode, itemKeys);
      }
    } else {
      sources = await this.localRAG.search(question, maxResults, searchMode, itemKeys);
    }

    Zotero.debug(`Claude Assistant: Found ${sources.length} chunks (${searchMode} mode${itemKeys ? `, scoped to ${itemKeys.length} paper(s)` : ''}), best score: ${sources[0]?.score || 0}`);

    // If no results found, still answer but signal to UI that search found nothing
    if (sources.length === 0) {
      Zotero.debug('Claude Assistant: No search results - answering without paper context');
      const response = await this.claudeClient.directChat(question, this.conversationHistory);
      const responseText = ClaudeClient.extractText(response) || 'No response received.';

      this.conversationHistory.push({ role: 'user', content: question });
      this.conversationHistory.push({ role: 'assistant', content: responseText });
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }

      return {
        text: responseText,
        sources: [],
        mode: 'research',
        noResults: true,
        indexStats: { indexedItems: stats.indexedItems, totalChunks: stats.totalChunks }
      };
    }

    // Call Claude API with search results
    const response = await this.claudeClient.answerWithRAGResults(
      question,
      sources,
      this.conversationHistory.slice(-10) // Include recent history
    );

    const rawResponseText = ClaudeClient.extractText(response) || 'No response received.';

    // Parse follow-up suggestions from response
    const { cleanText: responseText, suggestions } = this.parseSuggestions(rawResponseText);

    // Update conversation history
    this.conversationHistory.push({ role: 'user', content: question });
    this.conversationHistory.push({ role: 'assistant', content: responseText });

    // Keep history manageable
    if (this.conversationHistory.length > 20) {
      this.conversationHistory = this.conversationHistory.slice(-20);
    }

    // Persist to conversation store
    if (this.conversationStore && this.currentConversationId) {
      try {
        await this.conversationStore.addMessage(this.currentConversationId, 'user', question, null, 'research');
        await this.conversationStore.addMessage(
          this.currentConversationId, 'assistant', responseText,
          sources.length > 0 ? JSON.stringify(sources) : null, 'research'
        );
      } catch (e: any) {
        Zotero.debug(`Claude Assistant: Failed to persist messages: ${e.message}`);
      }
    }

    return {
      text: responseText,
      sources: sources,
      mode: 'research',
      suggestions
    };
  }

  /**
   * Answer a question using RAG + Claude (legacy method for backward compatibility)
   * This is the main entry point for chat queries
   * Returns both the response text AND the sources used
   */
  async askQuestion(question: string): Promise<{ text: string; sources: RAGSearchResult[] }> {
    try {
      // Check if Local RAG is initialized
      if (!this.localRAG) {
        throw new Error(
          'Local RAG service not initialized.\n\n' +
          'Please restart Zotero or check Help → Debug Output Logging for errors.'
        );
      }

      // Validate Claude API key
      if (!this.claudeClient) {
        const apiKey = Preferences.getApiKey();
        if (!apiKey || !Preferences.validateApiKey(apiKey)) {
          throw new Error(
            'Claude API key not configured.\n\n' +
            'Go to Tools → Settings → Claude Assistant to set your API key.'
          );
        }
        // Re-initialize client
        this.claudeClient = new ClaudeClient({
          apiKey,
          model: Preferences.getModel(),
        });
      }

      // Strip paper context prefix from query (UI may prepend it; we filter via itemKeys instead)
      const searchQuery = question.replace(/^\[Context:.*?\]\s*/s, '');
      Zotero.debug(`Claude Assistant: Searching for: ${searchQuery}`);
      const maxResults = Preferences.getMaxResults();
      const searchMode = this.embeddingService?.isAvailable() ? 'hybrid' : 'keyword';
      const itemKeys = this.selectedPapers.length > 0
        ? this.selectedPapers.map(p => p.itemKey)
        : undefined;
      const sources = await this.localRAG.search(searchQuery, maxResults, searchMode as any, itemKeys);

      Zotero.debug(`Claude Assistant: Found ${sources.length} relevant chunks`);

      // If no sources found, still ask Claude but note the lack of context
      if (sources.length === 0) {
        Zotero.debug('Claude Assistant: No relevant sources found, asking Claude without context');
      }

      // Call Claude API with search results
      const claudeResponse: ClaudeResponse = await this.claudeClient.answerWithRAGResults(
        question,
        sources
      );

      return {
        text: ClaudeClient.extractText(claudeResponse) || 'No response received.',
        sources: sources
      };

    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Error answering question: ${error.message || error}`);
      throw error;
    }
  }

  /**
   * Zotero 7 window hook - called when main window loads
   */
  onMainWindowLoad(window: any): void {
    Zotero.debug('Claude Assistant: onMainWindowLoad called');

    if (!window) {
      Zotero.debug('Claude Assistant: ERROR - No window provided');
      return;
    }

    // Track this window
    this.registeredWindows.add(window);

    const doc = window.document;

    // Add menu items to Tools menu
    const toolsMenu = doc.getElementById('menu_ToolsPopup');

    if (toolsMenu) {
      // Add separator
      const separator = doc.createXULElement('menuseparator');
      separator.id = 'claude-assistant-separator';
      toolsMenu.appendChild(separator);

      // Add "Ask Claude" menu item
      const menuItem = doc.createXULElement('menuitem');
      menuItem.id = 'claude-assistant-menu';
      menuItem.setAttribute('label', 'Ask Claude...');
      menuItem.setAttribute('oncommand', 'Zotero.ClaudeAssistant.openChatWindow();');
      toolsMenu.appendChild(menuItem);

      // Add preferences menu item
      const prefsItem = doc.createXULElement('menuitem');
      prefsItem.id = 'claude-assistant-prefs-menu';
      prefsItem.setAttribute('label', 'Claude Assistant Settings');
      prefsItem.setAttribute('oncommand', 'Zotero.ClaudeAssistant.openPreferences();');
      toolsMenu.appendChild(prefsItem);

      Zotero.debug('Claude Assistant: Menu items added');
    }

    // Add context menu item for "Chat with this paper"
    this.addContextMenuItem(window);

    // Register selection listener for context-aware chat
    this.registerSelectionListener(window);
  }

  /**
   * Add "Chat with this paper" to item context menu
   */
  private addContextMenuItem(window: any): void {
    try {
      const doc = window.document;

      // Find the item context menu
      const itemMenu = doc.getElementById('zotero-itemmenu');
      if (!itemMenu) {
        Zotero.debug('Claude Assistant: Item context menu not found');
        return;
      }

      // Create separator
      const separator = doc.createXULElement('menuseparator');
      separator.id = 'claude-assistant-context-separator';
      itemMenu.appendChild(separator);

      // Create "Chat with this paper" menu item
      const chatMenuItem = doc.createXULElement('menuitem');
      chatMenuItem.id = 'claude-assistant-chat-with-paper';
      chatMenuItem.setAttribute('label', 'Chat with this paper...');
      chatMenuItem.setAttribute('oncommand', 'Zotero.ClaudeAssistant.chatWithSelectedPapers();');
      itemMenu.appendChild(chatMenuItem);

      // Create "Chat with selected papers" menu item (shown when multiple selected)
      const chatMultipleItem = doc.createXULElement('menuitem');
      chatMultipleItem.id = 'claude-assistant-chat-with-papers';
      chatMultipleItem.setAttribute('label', 'Chat with selected papers...');
      chatMultipleItem.setAttribute('oncommand', 'Zotero.ClaudeAssistant.chatWithSelectedPapers();');
      chatMultipleItem.hidden = true; // Will be shown dynamically
      itemMenu.appendChild(chatMultipleItem);

      // Update menu item visibility based on selection count
      itemMenu.addEventListener('popupshowing', () => {
        const zoteroPane = window.ZoteroPane;
        if (zoteroPane) {
          const selectedItems = zoteroPane.getSelectedItems();
          const regularItems = selectedItems?.filter((item: any) =>
            item.isRegularItem() && !item.isNote() && !item.isAttachment()
          ) || [];

          if (regularItems.length === 0) {
            chatMenuItem.hidden = true;
            chatMultipleItem.hidden = true;
          } else if (regularItems.length === 1) {
            chatMenuItem.hidden = false;
            chatMultipleItem.hidden = true;
          } else {
            chatMenuItem.hidden = true;
            chatMultipleItem.hidden = false;
            chatMultipleItem.label = `Chat with ${regularItems.length} selected papers...`;
          }
        }
      });

      Zotero.debug('Claude Assistant: Context menu items added');
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Error adding context menu: ${error.message}`);
    }
  }

  /**
   * Open chat window with selected papers as context
   */
  chatWithSelectedPapers(): void {
    // First update selected papers from current selection
    const mainWindow = Zotero.getMainWindow();
    if (mainWindow) {
      this.updateSelectedPapers(mainWindow);
    }

    // Then open the chat window
    this.openChatWindow();
  }

  /**
   * Zotero 7 window hook - called when main window unloads
   */
  onMainWindowUnload(window: any): void {
    // Unregister the Notifier observer to prevent memory leaks
    const notifierID = (window as any)._claudeAssistantNotifierID;
    if (notifierID) {
      try {
        Zotero.Notifier.unregisterObserver(notifierID);
        Zotero.debug('Claude Assistant: Notifier observer unregistered');
      } catch (e) {
        // Ignore errors during cleanup
      }
      delete (window as any)._claudeAssistantNotifierID;
    }

    this.registeredWindows.delete(window);
  }

  /**
   * Register HTTP endpoint on Zotero's local server for embedding queries,
   * so external local tools can reuse the plugin's embedder
   * POST /claude-assistant/embed {text: string} -> {embedding: number[]}
   */
  private registerEmbeddingEndpoint(): void {
    try {
      const self = this;
      Zotero.Server.Endpoints['/claude-assistant/embed'] = function() {};
      Zotero.Server.Endpoints['/claude-assistant/embed'].prototype = {
        supportedMethods: ['POST'],
        supportedDataTypes: ['application/json'],
        permitBookmarklet: false,

        init: async function(options: any) {
          try {
            if (!self.embeddingService?.isAvailable()) {
              return [503, 'application/json', JSON.stringify({
                error: 'Embedding service not available'
              })];
            }

            const data = typeof options.data === 'string'
              ? JSON.parse(options.data)
              : options.data;

            if (!data?.text) {
              return [400, 'application/json', JSON.stringify({
                error: 'Missing "text" field'
              })];
            }

            const embedding = await self.embeddingService.embed(data.text);
            if (!embedding) {
              return [500, 'application/json', JSON.stringify({
                error: 'Embedding generation failed'
              })];
            }

            return [200, 'application/json', JSON.stringify({
              embedding: Array.from(embedding),
              model: self.embeddingService.getModelVersion(),
              dim: embedding.length
            })];
          } catch (error: any) {
            return [500, 'application/json', JSON.stringify({
              error: error.message || 'Internal error'
            })];
          }
        }
      };

      Zotero.debug('Claude Assistant: Registered /claude-assistant/embed endpoint');
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Failed to register embed endpoint: ${error.message}`);
    }
  }

  /**
   * Set up event listeners
   */
  private setupEventListeners(): void {
    // Selection listener will be set up per-window in onMainWindowLoad
    Zotero.debug('Claude Assistant: Event listeners setup complete');
  }

  /**
   * Register selection listener for a window
   * Tracks which papers are selected in Zotero's item pane
   */
  private registerSelectionListener(window: any): void {
    try {
      const zoteroPane = window.ZoteroPane;
      if (!zoteroPane) {
        Zotero.debug('Claude Assistant: ZoteroPane not available for selection listener');
        return;
      }

      // Listen for item selection changes
      const itemsView = zoteroPane.itemsView;
      if (itemsView) {
        // Use Zotero's notifier system for selection changes
        const notifierID = Zotero.Notifier.registerObserver(
          {
            notify: async (event: string, type: string, ids: number[], extraData: any) => {
              if (type === 'item' && (event === 'select' || event === 'modify')) {
                await this.updateSelectedPapers(window);
              }
            }
          },
          ['item'],
          'claudeAssistant'
        );

        // Store notifier ID for cleanup
        (window as any)._claudeAssistantNotifierID = notifierID;
        Zotero.debug('Claude Assistant: Selection notifier registered');

        // Also listen for direct selection events on the items tree
        // This catches immediate selection changes
        const originalOnSelect = itemsView.onSelect?.bind(itemsView);
        itemsView.onSelect = async () => {
          if (originalOnSelect) {
            await originalOnSelect();
          }
          await this.updateSelectedPapers(window);
        };

        // Initial update
        this.updateSelectedPapers(window);
      }
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Error registering selection listener: ${error.message}`);
    }
  }

  /**
   * Update the list of selected papers from Zotero's current selection
   */
  private async updateSelectedPapers(window: any): Promise<void> {
    try {
      const zoteroPane = window.ZoteroPane;
      if (!zoteroPane) return;

      const selectedItems = zoteroPane.getSelectedItems();
      if (!selectedItems || selectedItems.length === 0) {
        this.selectedPapers = [];
        this.notifyChatWindowOfContextChange();
        return;
      }

      // Filter to only regular items (not notes, attachments)
      // and extract paper context
      this.selectedPapers = selectedItems
        .filter((item: any) => item.isRegularItem() && !item.isNote() && !item.isAttachment())
        .slice(0, 10) // Limit to 10 papers max for context
        .map((item: any) => {
          const creators = item.getCreators();
          const authorNames = creators
            .filter((c: any) => c.creatorType === 'author')
            .map((c: any) => c.lastName || c.name || 'Unknown')
            .slice(0, 3);

          return {
            itemId: item.id,
            itemKey: item.key,
            title: item.getField('title') || 'Untitled',
            authors: authorNames.length > 0
              ? (authorNames.length > 2 ? `${authorNames[0]} et al.` : authorNames.join(', '))
              : 'Unknown',
            year: item.getField('year') || item.getField('date')?.substring(0, 4) || 'n.d.'
          };
        });

      Zotero.debug(`Claude Assistant: Updated selected papers: ${this.selectedPapers.length} items`);
      this.notifyChatWindowOfContextChange();
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Error updating selected papers: ${error.message}`);
    }
  }

  /**
   * Notify the chat window that paper context has changed
   */
  private notifyChatWindowOfContextChange(): void {
    if (this._chatWindow && !this._chatWindow.closed) {
      try {
        // Call a function in the chat window to update context display
        if (this._chatWindow.updatePaperContext) {
          this._chatWindow.updatePaperContext(this.selectedPapers);
        }
      } catch (error: any) {
        Zotero.debug(`Claude Assistant: Error notifying chat window: ${error.message}`);
      }
    }
  }

  /**
   * Get currently selected papers (called by chat window)
   */
  getSelectedPapers(): PaperContext[] {
    return this.selectedPapers;
  }

  /**
   * Clear paper context (called from chat window)
   */
  clearPaperContext(): void {
    this.selectedPapers = [];
    this.notifyChatWindowOfContextChange();
  }

  /**
   * Set specific papers as context (called from chat window or context menu)
   */
  setPaperContext(papers: PaperContext[]): void {
    this.selectedPapers = papers.slice(0, 10);
    this.notifyChatWindowOfContextChange();
  }

  /**
   * Open chat window
   */
  openChatWindow(): void {
    try {
      const windowArgs = {
        _window: null,
        claudeAssistant: this,
        initialPaperContext: this.selectedPapers, // Pass current selection as initial context
      };

      const win = Zotero.getMainWindow().openDialog(
        'chrome://claudeassistant/content/chat-dialog.xhtml',
        'claude-chat',
        'chrome,centerscreen,resizable,width=950,height=750',
        windowArgs
      );

      this._chatWindow = win;
    } catch (error) {
      Zotero.debug(`Claude Assistant: Error opening chat window: ${error}`);
      this.showNotification('Failed to open chat window. See debug output.', 'error');
    }
  }

  /**
   * Open preferences
   */
  openPreferences(): void {
    try {
      Zotero.Prefs.openPreferencesWindow();
    } catch (error) {
      this.showNotification('Please open Settings manually: Edit → Settings → Claude Assistant', 'info');
    }
  }

  /**
   * Show notification
   */
  showNotification(message: string, type: 'info' | 'warning' | 'error' = 'info'): void {
    try {
      const progressWindow = new Zotero.ProgressWindow();
      progressWindow.changeHeadline('Claude Assistant');
      progressWindow.addDescription(message);
      progressWindow.show();
      progressWindow.startCloseTimer(3000);
    } catch (error) {
      Zotero.debug(`Claude Assistant: Failed to show notification: ${error}`);
    }
  }

  /**
   * Index random 10 papers (for testing)
   */
  async indexRandom10(): Promise<void> {
    if (!this.localRAG) {
      this.showNotification('Local RAG not initialized', 'error');
      return;
    }

    this.showNotification('Indexing 10 random papers...', 'info');

    try {
      // Get all items
      const items = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID);
      const regularItems = items.filter((item: any) =>
        item.isRegularItem() && !item.isNote() && !item.isAttachment()
      );

      // Fisher-Yates shuffle for unbiased random selection
      for (let i = regularItems.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [regularItems[i], regularItems[j]] = [regularItems[j], regularItems[i]];
      }
      const selected = regularItems.slice(0, 10);

      let indexed = 0;
      for (const item of selected) {
        const chunksAdded = await this.localRAG.indexItem(item, false);
        if (chunksAdded > 0) indexed++;
      }

      await this.localRAG.saveIndex();
      this.showNotification(`Indexed ${indexed} papers successfully`, 'info');
    } catch (error: any) {
      this.showNotification(`Error indexing: ${error.message}`, 'error');
    }
  }

  /**
   * Get embedding statistics (called by preferences panel and chat window)
   * Returns stats from local BM25 index (always online since it's local)
   */
  async getStats(): Promise<{
    indexedItems: number;
    totalChunks: number;
    lastIndexedAt: string | null;
    databasePath?: string;
    serverOnline: boolean;
    embeddingCount?: number;
    embeddingModel?: string;
    embeddingServiceAvailable?: boolean;
  }> {
    if (!this.localRAG) {
      Zotero.debug('Claude Assistant: getStats() - Local RAG not initialized');
      return {
        indexedItems: 0,
        totalChunks: 0,
        lastIndexedAt: null,
        serverOnline: false
      };
    }

    const stats = this.localRAG.getStats();

    // Get embedding stats
    let embeddingCount = 0;
    let embeddingModel: string | null = null;
    try {
      if (this.embeddingStore) {
        embeddingCount = await this.embeddingStore.getEmbeddingCount();
        embeddingModel = await this.embeddingStore.getModelVersion();
      }
    } catch (e) {
      // Non-critical
    }

    Zotero.debug(`Claude Assistant: Stats - ${stats.indexedItems} items, ${stats.totalChunks} chunks, ${embeddingCount} embeddings`);

    return {
      indexedItems: stats.indexedItems,
      totalChunks: stats.totalChunks,
      lastIndexedAt: stats.lastIndexedAt,
      serverOnline: stats.serverOnline,
      embeddingCount,
      embeddingModel: embeddingModel || undefined,
      embeddingServiceAvailable: this.embeddingService?.isAvailable() || false,
    };
  }

  /**
   * Verify index
   */
  async verifyEmbeddings(): Promise<void> {
    if (!this.localRAG) {
      this.showNotification('Local RAG not initialized', 'error');
      return;
    }

    const stats = this.localRAG.getStats();
    this.showNotification(
      `Index OK: ${stats.indexedItems} items, ${stats.totalChunks} chunks`,
      'info'
    );
  }

  /**
   * Clear index
   */
  async clearIndex(): Promise<void> {
    if (!this.localRAG) {
      this.showNotification('Local RAG not initialized', 'error');
      return;
    }

    try {
      await this.localRAG.clearIndex();

      // Also clear embeddings
      if (this.embeddingStore) {
        await this.embeddingStore.clear();
      }

      this.showNotification('Index and embeddings cleared successfully', 'info');
    } catch (error: any) {
      this.showNotification(`Error clearing index: ${error.message}`, 'error');
    }
  }

  /**
   * Index library (incremental - skips already indexed items)
   */
  async indexLibrary(progressCallback?: (current: number, total: number, message: string) => void): Promise<void> {
    if (!this.localRAG) {
      this.showNotification('Local RAG not initialized', 'error');
      return;
    }

    try {
      this.showNotification('Starting incremental indexing...', 'info');

      const result = await this.localRAG.indexLibrary(
        (current, total) => {
          if (progressCallback) {
            const percent = Math.round((current / total) * 100);
            progressCallback(current, total, `Indexing... ${percent}% (${current}/${total})`);
          }
        },
        false  // Don't force re-index
      );

      const parts = [`Indexed ${result.indexed} new items`];
      if (result.skipped > 0) parts.push(`${result.skipped} already indexed`);
      if (result.noText && result.noText > 0) parts.push(`${result.noText} with no text`);
      if (result.errors > 0) parts.push(`${result.errors} errors`);
      this.showNotification(parts.join(', '), 'info');
    } catch (error: any) {
      this.showNotification(`Error indexing library: ${error.message}`, 'error');
    }
  }

  /**
   * Index new items only (same as incremental for local RAG)
   */
  async indexNewItems(progressCallback?: (current: number, total: number, message: string) => void): Promise<void> {
    // For local RAG, this is the same as incremental indexing
    await this.indexLibrary(progressCallback);
  }

  /**
   * Re-index everything (force)
   */
  async reindexAll(progressCallback?: (current: number, total: number, message: string) => void): Promise<void> {
    if (!this.localRAG) {
      this.showNotification('Local RAG not initialized', 'error');
      return;
    }

    try {
      this.showNotification('Starting full re-indexing...', 'info');

      const result = await this.localRAG.indexLibrary(
        (current, total) => {
          if (progressCallback) {
            const percent = Math.round((current / total) * 100);
            progressCallback(current, total, `Re-indexing... ${percent}% (${current}/${total})`);
          }
        },
        true  // Force re-index
      );

      const parts = [`Re-indexed ${result.indexed} items`];
      if (result.noText && result.noText > 0) parts.push(`${result.noText} with no text`);
      if (result.errors > 0) parts.push(`${result.errors} errors`);
      this.showNotification(parts.join(', '), 'info');
    } catch (error: any) {
      this.showNotification(`Error re-indexing library: ${error.message}`, 'error');
    }
  }

  /**
   * Generate embeddings for all indexed chunks that don't have them yet
   */
  async generateEmbeddings(
    progressCallback?: (current: number, total: number, message: string) => void
  ): Promise<{ generated: number; skipped: number; errors: number }> {
    if (!this.localRAG) {
      this.showNotification('Local RAG not initialized', 'error');
      return { generated: 0, skipped: 0, errors: 0 };
    }

    if (!this.embeddingService?.isAvailable()) {
      this.showNotification('Embedding service not available. Model files may be missing.', 'error');
      return { generated: 0, skipped: 0, errors: 0 };
    }

    if (!this.embeddingStore) {
      this.showNotification('Embedding store not initialized', 'error');
      return { generated: 0, skipped: 0, errors: 0 };
    }

    const chunks = this.localRAG.getChunks();
    const allChunkIds = Array.from(chunks.keys());
    let generated = 0;
    let skipped = 0;
    let errors = 0;

    // Find chunks that need embeddings
    const needsEmbedding: Array<{ chunkId: string; text: string; itemKey: string }> = [];
    for (const chunkId of allChunkIds) {
      const hasEmb = await this.embeddingStore.hasEmbedding(chunkId);
      if (hasEmb) {
        skipped++;
        continue;
      }
      const chunk = chunks.get(chunkId)!;
      needsEmbedding.push({ chunkId, text: chunk.text, itemKey: chunk.itemKey });
    }

    if (needsEmbedding.length === 0) {
      this.showNotification(`All ${skipped} chunks already have embeddings`, 'info');
      return { generated: 0, skipped, errors: 0 };
    }

    Zotero.debug(`Claude Assistant: Generating embeddings for ${needsEmbedding.length} chunks`);

    // Process in batches of 32
    const batchSize = 32;
    for (let i = 0; i < needsEmbedding.length; i += batchSize) {
      const batch = needsEmbedding.slice(i, i + batchSize);
      const texts = batch.map(b => b.text);

      if (progressCallback) {
        const progress = Math.min(i + batchSize, needsEmbedding.length);
        progressCallback(progress, needsEmbedding.length,
          `Generating embeddings... ${progress}/${needsEmbedding.length}`);
      }

      try {
        const embeddings = await this.embeddingService.embedBatch(texts);

        const entries: Array<{ chunkId: string; itemKey: string; embedding: Float32Array }> = [];
        for (let j = 0; j < batch.length; j++) {
          const emb = embeddings[j];
          if (emb) {
            entries.push({
              chunkId: batch[j].chunkId,
              itemKey: batch[j].itemKey,
              embedding: emb,
            });
            generated++;
          } else {
            errors++;
          }
        }

        if (entries.length > 0) {
          await this.embeddingStore.setBatchEmbeddings(
            entries,
            this.embeddingService.getModelVersion()
          );
        }
      } catch (error: any) {
        Zotero.debug(`Claude Assistant: Batch embedding error: ${error.message}`);
        errors += batch.length;
      }
    }

    // Reload embedding cache so hybrid search works immediately
    if (generated > 0 && this.localRAG) {
      await this.localRAG.loadEmbeddingCache();
    }

    Zotero.debug(`Claude Assistant: Embedding generation complete: ${generated} generated, ${skipped} skipped, ${errors} errors`);
    return { generated, skipped, errors };
  }

  /**
   * Get embedding count (for preferences UI)
   */
  async getEmbeddingCount(): Promise<number> {
    if (!this.embeddingStore) return 0;
    return await this.embeddingStore.getEmbeddingCount();
  }

  /**
   * Index PDFs for fulltext (prepare PDFs)
   * For local RAG, this is automatic during indexing
   */
  async indexFulltext(): Promise<void> {
    this.showNotification(
      'PDF fulltext extraction is automatic during indexing. Use "Index Library" button.',
      'info'
    );
  }

  /**
   * Cleanup on shutdown
   */
  cleanup(): void {
    Zotero.debug('Claude Assistant: Cleaning up');

    // Shut down embedding service
    if (this.embeddingService) {
      this.embeddingService.destroy();
      this.embeddingService = null;
    }

    // Close embedding store
    if (this.embeddingStore) {
      this.embeddingStore.close().catch((e) => {
        Zotero.debug(`Claude Assistant: Error closing embedding store: ${e.message}`);
      });
      this.embeddingStore = null;
    }

    // Save local RAG index before shutdown
    if (this.localRAG) {
      this.localRAG.saveIndex().catch((e) => {
        Zotero.debug(`Claude Assistant: Error saving index during cleanup: ${e.message}`);
      });
      this.localRAG = null;
    }

    // Close conversation store so its SQLite connection is released
    if (this.conversationStore) {
      this.conversationStore.close().catch((e) => {
        Zotero.debug(`Claude Assistant: Error closing conversation store: ${e.message}`);
      });
      this.conversationStore = null;
    }

    // Unregister the local server endpoint so a disabled plugin leaves
    // nothing live on Zotero's HTTP server
    delete Zotero.Server.Endpoints['/claude-assistant/embed'];

    // Remove UI elements from all registered windows
    for (const window of this.registeredWindows) {
      try {
        const doc = window.document;

        // Remove Tools menu items
        const idsToRemove = [
          'claude-assistant-menu',
          'claude-assistant-prefs-menu',
          'claude-assistant-separator',
          // Context menu items
          'claude-assistant-context-separator',
          'claude-assistant-chat-with-paper',
          'claude-assistant-chat-with-papers',
        ];

        for (const id of idsToRemove) {
          const el = doc.getElementById(id);
          if (el) el.remove();
        }

        // Unregister Notifier observer
        const notifierID = (window as any)._claudeAssistantNotifierID;
        if (notifierID) {
          Zotero.Notifier.unregisterObserver(notifierID);
          delete (window as any)._claudeAssistantNotifierID;
        }
      } catch (e) {
        // Ignore errors during cleanup
      }
    }

    this.registeredWindows.clear();
    this._initialized = false;
  }
}

// Create global instance
try {
  if (typeof Zotero !== 'undefined') {
    Zotero.debug('Claude Assistant: Creating global instance...');
    Zotero.ClaudeAssistant = new ClaudeAssistant();
    Zotero.debug('Claude Assistant: Global instance created successfully');
  } else {
    // This shouldn't happen, but log it if it does
    console.error('Claude Assistant: Zotero object not found!');
  }
} catch (error: any) {
  console.error(`Claude Assistant: Failed to create global instance: ${error.message}`);
  console.error(error.stack);
}
