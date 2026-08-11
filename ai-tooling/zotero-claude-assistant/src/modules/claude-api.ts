/**
 * Claude API Integration Module
 * Handles all interactions with Anthropic's Claude API
 */

declare const Zotero: any;
declare const Components: any;

import { RAGSearchResult } from './local-rag';

export interface ClaudeMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ClaudeResponse {
  id: string;
  type: string;
  role: string;
  // Blocks may be 'text' or 'thinking' (e.g. Claude Fable 5 always emits
  // thinking blocks), so always extract text via ClaudeClient.extractText()
  content: Array<{
    type: string;
    text?: string;
  }>;
  model: string;
  stop_reason: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

export interface ClaudeConfig {
  apiKey: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

export class ClaudeClient {
  private apiKey: string;
  private model: string;
  private maxTokens: number;
  private temperature: number;
  private baseUrl: string = 'https://api.anthropic.com/v1';
  private requestQueue: Array<() => Promise<any>> = [];
  private isProcessing: boolean = false;

  constructor(config: ClaudeConfig) {
    this.apiKey = config.apiKey;
    this.model = config.model || 'claude-sonnet-4-6';
    this.maxTokens = config.maxTokens || 8192;
    this.temperature = config.temperature || 0.7;
  }

  /**
   * Newer models (Opus 4.7+, Fable 5, Mythos 5) reject sampling parameters
   * (temperature/top_p/top_k) with a 400 error, so only send them to models
   * that still accept them.
   */
  private supportsSamplingParams(): boolean {
    const noSamplingPrefixes = [
      'claude-fable',
      'claude-mythos',
      'claude-opus-4-7',
      'claude-opus-4-8',
    ];
    return !noSamplingPrefixes.some((prefix) => this.model.startsWith(prefix));
  }

  /**
   * Extract the assistant's visible text from a response.
   * Filters to text blocks (skipping thinking blocks) and handles
   * safety refusals (stop_reason 'refusal' with empty content).
   */
  static extractText(response: ClaudeResponse): string {
    if (response.stop_reason === 'refusal') {
      return 'Claude declined to answer this request. Please rephrase and try again.';
    }
    return (response.content || [])
      .filter((block) => block.type === 'text' && block.text)
      .map((block) => block.text)
      .join('\n');
  }

  /**
   * Send a chat message to Claude
   */
  async chat(
    messages: ClaudeMessage[],
    systemPrompt?: string
  ): Promise<ClaudeResponse> {
    return this.queueRequest(() => this._chat(messages, systemPrompt));
  }

  private async _chat(
    messages: ClaudeMessage[],
    systemPrompt?: string
  ): Promise<ClaudeResponse> {
    const body: any = {
      model: this.model,
      max_tokens: this.maxTokens,
      messages: messages,
    };

    if (this.supportsSamplingParams()) {
      body.temperature = this.temperature;
    }

    if (systemPrompt) {
      body.system = systemPrompt;
    }

    const response = await this.makeRequest('/messages', body);
    return response;
  }

  /**
   * Analyze a document with Claude
   */
  async analyzeDocument(
    documentText: string,
    query: string,
    metadata?: Record<string, any>
  ): Promise<string> {
    const systemPrompt = `You are analyzing a research paper.
Metadata: ${JSON.stringify(metadata || {})}

Provide concise, accurate analysis based on the document content.`;

    const messages: ClaudeMessage[] = [
      {
        role: 'user',
        content: `Document:\n\n${documentText}\n\nQuery: ${query}`,
      },
    ];

    const response = await this.chat(messages, systemPrompt);
    return ClaudeClient.extractText(response);
  }

  /**
   * Generate semantic representation for a text chunk
   * Since Claude API doesn't provide direct embeddings, we use a structured prompt
   * to create a semantic summary that can be used for similarity matching
   */
  async generateEmbedding(text: string): Promise<string> {
    const systemPrompt = `Extract the key semantic content from the text as a structured summary.
Focus on: main concepts, entities, relationships, and core ideas.
Format: concise bullet points.`;

    const messages: ClaudeMessage[] = [
      {
        role: 'user',
        content: text,
      },
    ];

    const response = await this.chat(messages, systemPrompt);
    return ClaudeClient.extractText(response);
  }

  /**
   * Answer question using Python RAG search results
   */
  async answerWithRAGResults(
    question: string,
    searchResults: RAGSearchResult[],
    conversationHistory?: ClaudeMessage[]
  ): Promise<ClaudeResponse> {
    // Sort results by year ascending for temporal coherence
    const sorted = [...searchResults].sort((a, b) => {
      const yearA = parseInt(a.year) || 0;
      const yearB = parseInt(b.year) || 0;
      return yearA - yearB;
    });

    // Convert RAGSearchResult[] to the format answerWithContext expects
    const contextChunks = sorted.map(result => ({
      text: result.text,
      metadata: {
        title: result.title,
        authors: result.authors,
        year: result.year,
        score: result.score,
        section: result.section,
        journal: result.journal,
        doi: result.doi,
        tags: result.tags,
        collections: result.collections
      }
    }));

    return this.answerWithContext(question, contextChunks, conversationHistory);
  }

  /**
   * Perform RAG-based question answering
   */
  async answerWithContext(
    question: string,
    contextChunks: Array<{ text: string; metadata: any }>,
    conversationHistory?: ClaudeMessage[]
  ): Promise<ClaudeResponse> {
    const context = contextChunks
      .map((chunk, i) => {
        const m = chunk.metadata;
        const parts = [`Source ${i + 1}`];
        if (m.title) parts.push(m.title);
        if (m.authors) parts.push(m.authors);
        if (m.year) parts.push(`(${m.year})`);
        if (m.journal) parts.push(m.journal);
        if (m.section) parts.push(`[${m.section}]`);
        return `[${parts.join(' | ')}]\n${chunk.text}`;
      })
      .join('\n\n---\n\n');

    const systemPrompt = `You are a research assistant analyzing academic papers from the user's personal library (closed corpus).

## Citation Rules
- Cite every claim using [Source N] notation matching the provided sources.
- Never fabricate sources or cite papers not in the provided context.
- When sources disagree, note the conflict and cite both sides.

## Temporal Awareness
- Sources are sorted chronologically. Pay attention to publication years.
- When a user asks how understanding has "evolved" or "changed", trace the progression across years.
- Later papers may supersede, refine, or contradict earlier findings - flag this.

## Source Quality
- Distinguish review articles (broad surveys) from primary research (original data).
- Weight abstract and title sections as summaries; body sections contain detailed evidence.
- If a claim comes only from a title/abstract, note the limited evidence depth.

## Terminology
- Scientific terms may appear as abbreviations or full forms (e.g., ALD = atomic layer deposition). Treat them as equivalent.
- Spelling variants (e.g., behaviour/behavior) are equivalent.

## Response Format
- Be concise but thorough. Use structured formatting (headers, bullets) for complex answers.
- If the provided context is insufficient to answer confidently, say so explicitly rather than speculating.

## Follow-up Suggestions
After your main response, on a new line, output exactly 3 follow-up questions the user might ask next.
Format them as: <<<SUGGESTIONS: question1 ||| question2 ||| question3>>>
Keep each question under 80 characters. Focus on:
1. A comparison or relationship between the cited sources
2. A specific mechanism, method, or detail worth exploring deeper
3. A gap, limitation, or practical implication
Do NOT include the <<<SUGGESTIONS:>>> line in your visible answer - it is parsed programmatically.`;

    const messages: ClaudeMessage[] = [
      ...(conversationHistory || []),
      {
        role: 'user',
        content: `Context:\n\n${context}\n\nQuestion: ${question}`,
      },
    ];

    return this.chat(messages, systemPrompt);
  }

  /**
   * Generate a research synthesis across multiple papers
   */
  async synthesize(
    topic: string,
    papers: Array<{ title: string; content: string; authors: string }>
  ): Promise<string> {
    const papersText = papers
      .map(
        (paper, i) =>
          `[${i + 1}] ${paper.title} (${paper.authors})\n${paper.content}`
      )
      .join('\n\n---\n\n');

    const systemPrompt = `You are synthesizing research findings across multiple papers.
Identify common themes, contradictions, and key insights.
Cite papers using their numbers.`;

    const messages: ClaudeMessage[] = [
      {
        role: 'user',
        content: `Topic: ${topic}\n\nPapers:\n\n${papersText}\n\nProvide a comprehensive synthesis.`,
      },
    ];

    const response = await this.chat(messages, systemPrompt);
    return ClaudeClient.extractText(response);
  }

  /**
   * Make HTTP request to Claude API with retry logic
   */
  private async makeRequest(
    endpoint: string,
    body: any,
    retries: number = 3
  ): Promise<any> {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await this.httpRequest('POST', endpoint, body);
        return response;
      } catch (error: any) {
        // Don't retry client errors (4xx) except 429 (rate limit) and 529 (overloaded)
        const isClientError = error.message?.includes('Claude API error (4') &&
          !error.message?.includes('(429)');
        if (isClientError || attempt === retries - 1) throw error;

        // Exponential backoff
        const delay = Math.pow(2, attempt) * 1000;
        Zotero.debug(`Claude Assistant: Retrying in ${delay}ms (attempt ${attempt + 1}/${retries})`);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  /**
   * Make HTTP request using Zotero.HTTP.request (Zotero 7 compatible)
   * This is Zotero's built-in HTTP utility that works in the privileged context
   */
  private async httpRequest(method: string, endpoint: string, body?: any): Promise<any> {
    const url = this.baseUrl + endpoint;
    Zotero.debug(`Claude Assistant: HTTP ${method} ${url}`);

    try {
      const options: any = {
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          'anthropic-version': '2023-06-01',
        },
        timeout: 300000, // 5 minute timeout: no streaming via Zotero.HTTP, and long answers on Opus-tier models can exceed 2 minutes
        responseType: 'json',
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      // Use Zotero's built-in HTTP request method
      const response = await Zotero.HTTP.request(method, url, options);

      // Check if we got a valid response
      if (response.status >= 200 && response.status < 300) {
        // responseType: 'json' should auto-parse, but handle both cases
        const data = typeof response.response === 'string'
          ? JSON.parse(response.response)
          : response.response;
        Zotero.debug(`Claude Assistant: HTTP response status ${response.status}`);
        return data;
      } else {
        // Try to parse error response
        let errorMessage = response.statusText || 'Unknown error';
        try {
          const errorBody = typeof response.response === 'string'
            ? JSON.parse(response.response)
            : response.response;
          errorMessage = errorBody?.error?.message || errorMessage;
        } catch (e) {
          // If parsing fails, use status text
        }
        throw new Error(`Claude API error (${response.status}): ${errorMessage}`);
      }
    } catch (error: any) {
      // Re-throw with more context
      if (error.message?.includes('Claude API error')) {
        throw error;
      }
      throw new Error(`HTTP request failed: ${error.message || error}`);
    }
  }

  /**
   * Queue requests to respect rate limits
   */
  private async queueRequest<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestQueue.push(async () => {
        try {
          const result = await request();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      if (!this.isProcessing) {
        this.processQueue();
      }
    });
  }

  /**
   * Process queued requests with rate limiting
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.requestQueue.length === 0) return;

    this.isProcessing = true;

    while (this.requestQueue.length > 0) {
      const request = this.requestQueue.shift();
      if (request) {
        await request();
        // Rate limit: wait between requests
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
    }

    this.isProcessing = false;
  }

  /**
   * Get token count estimate (rough approximation)
   */
  estimateTokens(text: string): number {
    // Rough estimate: ~4 characters per token
    return Math.ceil(text.length / 4);
  }

  /**
   * Direct chat with Claude (no RAG context)
   * Used for general conversation when research context is not needed
   */
  async directChat(
    message: string,
    conversationHistory?: ClaudeMessage[]
  ): Promise<ClaudeResponse> {
    const systemPrompt = `You are Claude, a helpful AI assistant integrated into Zotero, a research management tool.

You can help users with:
- General questions and conversation
- Explaining concepts and ideas
- Writing and editing assistance
- Programming and technical help
- Research methodology advice

Be helpful, accurate, and concise. When appropriate, format your responses with clear structure using markdown.`;

    const messages: ClaudeMessage[] = [
      ...(conversationHistory || []).slice(-10), // Keep last 10 messages for context
      {
        role: 'user',
        content: message,
      },
    ];

    return this.chat(messages, systemPrompt);
  }

  /**
   * Lightweight chat for auxiliary tasks (query rewriting, etc.)
   * Uses lower max_tokens and temperature to minimize cost
   */
  private async _quickChat(
    messages: ClaudeMessage[],
    systemPrompt: string,
    maxTokens: number = 256
  ): Promise<ClaudeResponse> {
    const body: any = {
      model: this.model,
      max_tokens: maxTokens,
      messages,
    };
    if (this.supportsSamplingParams()) {
      body.temperature = 0.3;
    }
    if (systemPrompt) body.system = systemPrompt;
    return this.makeRequest('/messages', body);
  }

  /**
   * Generate alternative query formulations for improved retrieval
   * Returns 2-3 alternative phrasings of the original query
   */
  async rewriteQuery(originalQuery: string): Promise<string[]> {
    const systemPrompt = 'You generate alternative search queries for academic paper retrieval. Output ONLY a JSON array of 2-3 strings. No explanation.';

    const messages: ClaudeMessage[] = [{
      role: 'user',
      content: `Original query: "${originalQuery}"\n\nGenerate 2-3 alternative phrasings that would find relevant research papers. Use different terminology, synonyms, and phrasing. Keep scientific precision.\n\nReturn as JSON array of strings only.`
    }];

    try {
      const response = await this._quickChat(messages, systemPrompt, 256);
      const text = ClaudeClient.extractText(response) || '[]';
      const jsonMatch = text.match(/\[[\s\S]*?\]/);
      if (jsonMatch) {
        const queries = JSON.parse(jsonMatch[0]);
        return Array.isArray(queries) ? queries.slice(0, 3) : [];
      }
      return [];
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Query rewriting failed: ${error.message}`);
      return [];
    }
  }

  /**
   * Detect if a query likely needs research/paper context
   * Returns true if the query appears to be asking about papers/research
   * Returns false for greetings, tests, and general chat queries
   */
  static detectResearchIntent(query: string): boolean {
    const q = query.toLowerCase().trim();

    // ═══════════════════════════════════════════════════════════════
    // NEGATIVE PATTERNS - return false for these (chat mode)
    // ═══════════════════════════════════════════════════════════════

    // Greetings and test queries
    const chatStarters = [
      'test', 'hello', 'hi', 'hey', 'good morning', 'good afternoon',
      'good evening', 'thanks', 'thank you', 'ok', 'okay', 'yes', 'no',
      'help', 'what can you do', 'who are you', 'how are you'
    ];

    for (const starter of chatStarters) {
      if (q === starter || q.startsWith(starter + ' ') || q.startsWith(starter + ',')) {
        return false;
      }
    }

    // Very short queries without research keywords are likely chat
    const words = q.split(/\s+/).filter(w => w.length > 0);
    if (words.length < 3) {
      // Check if it contains any research keyword
      const hasResearchKeyword = ['paper', 'study', 'research', 'finding', 'method', 'data', 'result'].some(k => q.includes(k));
      if (!hasResearchKeyword) {
        return false;
      }
    }

    // ═══════════════════════════════════════════════════════════════
    // POSITIVE PATTERNS - return true for these (research mode)
    // ═══════════════════════════════════════════════════════════════

    // Research-oriented keywords
    const researchKeywords = [
      'paper', 'papers', 'study', 'studies', 'research',
      'author', 'authors', 'published', 'journal',
      'finding', 'findings', 'result', 'results',
      'method', 'methodology', 'experiment',
      'literature', 'citation', 'reference',
      'compare', 'contrast', 'review',
      'what does', 'what do', 'according to',
      'my library', 'my papers', 'my collection',
      'this paper', 'these papers', 'the paper',
      'abstract', 'conclusion', 'introduction',
      'figure', 'table', 'data', 'dataset',
      // Domain-specific terms that suggest research queries
      'wafer', 'dielectric', 'transistor', 'silicon', 'epitaxy',
      'dopant', 'etch', 'deposition', 'annealing', 'interconnect'
    ];

    // Check for research keywords
    for (const keyword of researchKeywords) {
      if (q.includes(keyword)) {
        return true;
      }
    }

    // Question patterns that suggest research needs
    const researchPatterns = [
      /what (?:is|are) (?:the )?(?:main|key)/i,
      /summarize/i,
      /explain (?:the|this)/i,
      /what (?:methods?|approach)/i,
      /\bfindings?\b/i,
      /how (?:does|do|did|can|could)/i,
      /what (?:are|were) the (?:results?|conclusions?)/i,
      /why (?:does|do|did|is|are)/i,
      /what causes/i,
      /how to (?:improve|reduce|increase|optimize)/i
    ];

    for (const pattern of researchPatterns) {
      if (pattern.test(q)) {
        return true;
      }
    }

    // Default to chat mode if no research intent detected
    return false;
  }
}
