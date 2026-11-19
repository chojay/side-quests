/**
 * Main entry point for the Claude Research Assistant plugin
 * Local RAG with BM25 search - no external server required
 */

export { ClaudeAssistant } from './addon';
export { ClaudeClient } from './modules/claude-api';
export { LocalRAGService } from './modules/local-rag';
export { ConversationStore } from './modules/conversation-store';
export { Preferences } from './prefs';

// Version - single source of truth lives in version.ts and is cross-checked
// against package.json / manifest.json / updates.json by scripts/doctor.js
export { VERSION } from './version';
