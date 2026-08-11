/**
 * Main entry point for the Claude Research Assistant plugin
 * Local RAG with BM25 search - no external server required
 */

export { ClaudeAssistant } from './addon';
export { ClaudeClient } from './modules/claude-api';
export { LocalRAGService } from './modules/local-rag';
export { ConversationStore } from './modules/conversation-store';
export { Preferences } from './prefs';

// Version - must match manifest.json and package.json
export const VERSION = '2.2.0';
