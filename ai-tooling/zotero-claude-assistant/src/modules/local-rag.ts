/**
 * Local RAG Service - Pure TypeScript implementation
 * No external Python server required
 *
 * Uses:
 * - Zotero's built-in SQLite for storage
 * - BM25 algorithm for text search (fast, free)
 * - Claude API for response generation
 */

import { Preferences } from '../prefs';

declare const Zotero: any;
declare const Components: any;
declare const PathUtils: any;
declare const IOUtils: any;  // Firefox 102+ / Zotero 7 file I/O API

export interface RAGSearchResult {
  item_key: string;
  item_id: number;
  chunk_index: number;
  chunk_text: string;
  text: string;  // Alias for chunk_text (for claude-api.ts compatibility)
  title: string;
  authors: string;
  year: string;
  score: number;
  page_num?: number;
  section?: string;    // 'title' | 'abstract' | 'body'
  journal?: string;
  doi?: string;
  tags?: string[];
  collections?: string[];
}

export interface IndexStats {
  indexedItems: number;
  totalChunks: number;
  lastIndexedAt: string | null;
  serverOnline: boolean;
}

// English stopwords - removed instead of length-filtering, so short scientific terms survive
const STOPWORDS = new Set([
  'a','an','the','and','or','but','in','on','at','to','for','of','with','by','from','as','is','it',
  'was','are','were','be','been','being','have','has','had','do','does','did','will','would','shall',
  'should','may','might','can','could','not','no','nor','so','if','then','than','that','this','these',
  'those','he','she','we','they','me','him','her','us','them','my','his','its','our','their','your',
  'who','whom','which','what','where','when','how','why','am','about','into','through','during',
  'before','after','above','below','between','out','off','over','under','again','further','once',
  'here','there','all','each','every','both','few','more','most','other','some','such','only','own',
  'same','very','just','because','until','while','also','any','up','down','too','very','much',
  'de','la','le','et','des','du','en','les','une','der','die','und','von','den'
]);

// Bidirectional synonym/abbreviation map for semiconductor process/materials science
const SYNONYM_MAP: Record<string, string[]> = {
  'hf': ['hafnium'], 'hafnium': ['hf'],
  'cu': ['copper'], 'copper': ['cu'],
  'al': ['aluminum', 'aluminium'], 'aluminum': ['al'], 'aluminium': ['al'],
  'au': ['gold'], 'gold': ['au'],
  'ag': ['silver'], 'silver': ['ag'],
  'zn': ['zinc'], 'zinc': ['zn'],
  'mg': ['magnesium'], 'magnesium': ['mg'],
  'na': ['sodium'], 'sodium': ['na'],
  'k': ['potassium'], 'potassium': ['k'],
  'fe': ['iron'], 'iron': ['fe'],
  'ni': ['nickel'], 'nickel': ['ni'],
  'ti': ['titanium'], 'titanium': ['ti'],
  'zr': ['zirconium'], 'zirconium': ['zr'],
  'si': ['silicon'], 'silicon': ['si'],
  'sn': ['tin'], 'tin': ['sn'],
  'mn': ['manganese'], 'manganese': ['mn'],
  'co': ['cobalt'], 'cobalt': ['co'],
  'cr': ['chromium'], 'chromium': ['cr'],
  'w': ['tungsten'], 'tungsten': ['w'],
  'pt': ['platinum'], 'platinum': ['pt'],
  'hkmg': ['high-k', 'metal', 'gate'], 'high-k metal gate': ['hkmg'],
  'ald': ['atomic', 'layer', 'deposition'], 'atomic layer deposition': ['ald'],
  'sti': ['shallow', 'trench', 'isolation'], 'shallow trench isolation': ['sti'],
  'rie': ['reactive', 'ion', 'etching'], 'reactive ion etching': ['rie'],
  'tsv': ['through', 'silicon', 'via'], 'through silicon via': ['tsv'],
  'cmp': ['chemical', 'mechanical', 'planarization'], 'chemical mechanical planarization': ['cmp'],
  'xrr': ['x-ray', 'reflectivity'], 'x-ray reflectivity': ['xrr'],
  'xrd': ['x-ray', 'diffraction'], 'x-ray diffraction': ['xrd'],
  'xps': ['x-ray', 'photoelectron', 'spectroscopy'],
  'sem': ['scanning', 'electron', 'microscopy'],
  'tem': ['transmission', 'electron', 'microscopy'],
  'afm': ['atomic', 'force', 'microscopy'],
  'cv': ['capacitance', 'voltage'], 'capacitance voltage': ['cv'],
  'pld': ['pulsed', 'laser', 'deposition'],
  'pvd': ['physical', 'vapor', 'deposition'],
  'cvd': ['chemical', 'vapor', 'deposition'],
  'hfo2': ['hafnium', 'oxide', 'high-k', 'dielectric'],
  'pecvd': ['plasma', 'enhanced', 'chemical', 'vapor'],
  'ito': ['indium', 'tin', 'oxide'],
  'finfet': ['fin', 'field', 'effect', 'transistor'],
  'mosfet': ['metal', 'oxide', 'semiconductor', 'transistor'],
  // General scientific abbreviations
  'dft': ['density', 'functional', 'theory'], 'density functional theory': ['dft'],
  'md': ['molecular', 'dynamics'], 'molecular dynamics': ['md'],
  'ml': ['machine', 'learning'], 'machine learning': ['ml'],
  'nn': ['neural', 'network'], 'neural network': ['nn'],
  'dnn': ['deep', 'neural', 'network'],
  'cnn': ['convolutional', 'neural', 'network'],
  'ftir': ['fourier', 'transform', 'infrared'],
  'nmr': ['nuclear', 'magnetic', 'resonance'],
  'xas': ['x-ray', 'absorption', 'spectroscopy'],
  'xanes': ['x-ray', 'absorption', 'near', 'edge'],
  'exafs': ['extended', 'x-ray', 'absorption', 'fine'],
  'saxs': ['small', 'angle', 'x-ray', 'scattering'],
  'waxs': ['wide', 'angle', 'x-ray', 'scattering'],
  'eds': ['energy', 'dispersive', 'spectroscopy'],
  'eels': ['electron', 'energy', 'loss', 'spectroscopy'],
  'sims': ['secondary', 'ion', 'mass', 'spectrometry'],
  'tga': ['thermogravimetric', 'analysis'],
  'dsc': ['differential', 'scanning', 'calorimetry'],
  'bet': ['brunauer', 'emmett', 'teller'],
  'rta': ['rapid', 'thermal', 'annealing'],
  'aes': ['auger', 'electron', 'spectroscopy'],
  // Spelling variants (bidirectional)
  'analyse': ['analyze'], 'analyze': ['analyse'],
  'behaviour': ['behavior'], 'behavior': ['behaviour'],
  'characterise': ['characterize'], 'characterize': ['characterise'],
  'optimise': ['optimize'], 'optimize': ['optimise'],
  'sulphate': ['sulfate'], 'sulfate': ['sulphate'],
  'sulphide': ['sulfide'], 'sulfide': ['sulphide'],
  // Common measurement/property terms
  'rt': ['room', 'temperature'], 'room temperature': ['rt'],
  'vth': ['threshold', 'voltage'], 'threshold voltage': ['vth'],
  'bti': ['bias', 'temperature', 'instability'],
  'tddb': ['time', 'dependent', 'dielectric', 'breakdown'],
  'hci': ['hot', 'carrier', 'injection'],
  'cd': ['critical', 'dimension'], 'critical dimension': ['cd'],
  'ler': ['line', 'edge', 'roughness'],
};

/**
 * Simple BM25 implementation for keyword search
 */
class BM25Index {
  private k1: number = 1.5;
  private b: number = 0.75;
  private documents: Map<string, { termFreqs: Map<string, number>; length: number }> = new Map();
  private documentFreqs: Map<string, number> = new Map();
  private avgDocLength: number = 0;
  private totalDocs: number = 0;
  private totalDocLength: number = 0; // Running total for O(1) avg recalculation

  /**
   * Tokenize text into terms.
   * Preserves short scientific tokens (Hf, Cu, Al, eV, nm, 2D, D*, pH).
   * Uses stopword list instead of length filter.
   */
  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      // Preserve D* as "d*", keep hyphens in compound terms like solid-state
      .replace(/[^\w\s*-]/g, ' ')
      // Collapse hyphens into single token: solid-state → solid-state
      .split(/\s+/)
      .filter(term => term.length > 0 && !STOPWORDS.has(term));
  }

  /**
   * Expand query terms with synonyms. Expanded terms are tagged for half-weighting.
   * Returns array of { term, weight } objects.
   */
  private expandQuery(queryTerms: string[]): Array<{ term: string; weight: number }> {
    const expanded: Array<{ term: string; weight: number }> = [];
    const seen = new Set<string>();

    for (const term of queryTerms) {
      if (!seen.has(term)) {
        expanded.push({ term, weight: 1.0 });
        seen.add(term);
      }
      const synonyms = SYNONYM_MAP[term];
      if (synonyms) {
        for (const syn of synonyms) {
          if (!seen.has(syn)) {
            expanded.push({ term: syn, weight: 0.5 });
            seen.add(syn);
          }
        }
      }
    }
    return expanded;
  }

  /**
   * Add a document to the index
   */
  addDocument(docId: string, text: string): void {
    const terms = this.tokenize(text);
    const termFreqs = new Map<string, number>();

    for (const term of terms) {
      termFreqs.set(term, (termFreqs.get(term) || 0) + 1);
    }

    // Update document frequencies
    for (const term of termFreqs.keys()) {
      this.documentFreqs.set(term, (this.documentFreqs.get(term) || 0) + 1);
    }

    // No text stored in BM25 docs - chunk text lives in LocalRAGService.chunks
    this.documents.set(docId, {
      termFreqs,
      length: terms.length
    });

    // Update average doc length using running total (O(1) instead of O(n))
    this.totalDocs++;
    this.totalDocLength += terms.length;
    this.avgDocLength = this.totalDocLength / this.totalDocs;
  }

  /**
   * Remove a document from the index
   */
  removeDocument(docId: string): void {
    const doc = this.documents.get(docId);
    if (!doc) return;

    // Update document frequencies
    for (const term of doc.termFreqs.keys()) {
      const freq = this.documentFreqs.get(term) || 0;
      if (freq <= 1) {
        this.documentFreqs.delete(term);
      } else {
        this.documentFreqs.set(term, freq - 1);
      }
    }

    this.totalDocLength -= doc.length;
    this.documents.delete(docId);
    this.totalDocs--;

    // Update average doc length using running total
    this.avgDocLength = this.totalDocs > 0 ? this.totalDocLength / this.totalDocs : 0;
  }

  /**
   * Search for documents matching the query
   */
  search(query: string, limit: number = 25): Array<{ docId: string; score: number }> {
    const queryTerms = this.tokenize(query);
    const expandedTerms = this.expandQuery(queryTerms);
    const scores: Array<{ docId: string; score: number }> = [];

    for (const [docId, doc] of this.documents) {
      let score = 0;

      for (const { term, weight } of expandedTerms) {
        const tf = doc.termFreqs.get(term) || 0;
        if (tf === 0) continue;

        const df = this.documentFreqs.get(term) || 0;
        const idf = Math.log((this.totalDocs - df + 0.5) / (df + 0.5) + 1);

        const numerator = tf * (this.k1 + 1);
        const denominator = tf + this.k1 * (1 - this.b + this.b * (doc.length / this.avgDocLength));

        score += weight * idf * (numerator / denominator);
      }

      if (score > 0) {
        scores.push({ docId, score });
      }
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    return scores.slice(0, limit);
  }

  /**
   * Get the number of indexed documents
   */
  get size(): number {
    return this.totalDocs;
  }

  /**
   * Clear the index
   */
  clear(): void {
    this.documents.clear();
    this.documentFreqs.clear();
    this.avgDocLength = 0;
    this.totalDocs = 0;
    this.totalDocLength = 0;
  }

  /**
   * Export index to JSON for persistence
   */
  toJSON(): string {
    return JSON.stringify({
      documents: Array.from(this.documents.entries()).map(([id, doc]) => ({
        id,
        termFreqs: Array.from(doc.termFreqs.entries()),
        length: doc.length
      })),
      documentFreqs: Array.from(this.documentFreqs.entries()),
      avgDocLength: this.avgDocLength,
      totalDocs: this.totalDocs
    });
  }

  /**
   * Import index from JSON
   */
  fromJSON(json: string): void {
    const data = JSON.parse(json);

    this.documents.clear();
    for (const doc of data.documents) {
      // Accept both v1 (with text) and v2 (without text) format
      this.documents.set(doc.id, {
        termFreqs: new Map(doc.termFreqs),
        length: doc.length
      });
    }

    this.documentFreqs = new Map(data.documentFreqs);
    this.totalDocs = data.totalDocs;
    // Recompute running total from loaded data
    this.totalDocLength = Array.from(this.documents.values()).reduce((sum, doc) => sum + doc.length, 0);
    this.avgDocLength = this.totalDocs > 0 ? this.totalDocLength / this.totalDocs : 0;
  }
}


/**
 * Local RAG Service - manages indexing and search
 */
export class LocalRAGService {
  private bm25Index: BM25Index;
  private chunks: Map<string, {
    itemId: number;
    itemKey: string;
    chunkIndex: number;
    text: string;
    title: string;
    authors: string;
    year: string;
    section?: string;  // 'title' | 'abstract' | 'body'
    tags?: string[];
    collections?: string[];
    doi?: string;
    journal?: string;
    pageNum?: number;
  }> = new Map();
  private indexedItemKeys: Set<string> = new Set();
  private lastIndexedAt: Date | null = null;
  private dbPath: string;
  private isLoaded: boolean = false;

  // Optional embedding infrastructure (injected after construction)
  private embeddingService: any = null;
  private embeddingStore: any = null;
  // In-memory cache of embeddings for fast cosine similarity search
  private embeddingCache: Map<string, Float32Array> = new Map();

  constructor() {
    this.bm25Index = new BM25Index();

    // Get Zotero data directory for storing our index
    const dataDir = Zotero.DataDirectory.dir;
    this.dbPath = PathUtils.join(dataDir, 'claude-assistant-index.json');
  }

  /**
   * Inject embedding services (called from addon.ts after both are initialized)
   */
  setEmbeddingServices(embeddingService: any, embeddingStore: any): void {
    this.embeddingService = embeddingService;
    this.embeddingStore = embeddingStore;
  }

  /**
   * Load all embeddings from SQLite into in-memory cache for fast search
   */
  async loadEmbeddingCache(): Promise<void> {
    if (!this.embeddingStore) return;
    try {
      this.embeddingCache = await this.embeddingStore.getAllEmbeddings();
      Zotero.debug(`Claude Assistant: Loaded ${this.embeddingCache.size} embeddings into cache`);
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Failed to load embedding cache: ${error.message}`);
    }
  }

  /**
   * Initialize the service - load existing index from disk
   */
  async initialize(): Promise<void> {
    if (this.isLoaded) return;

    try {
      Zotero.debug(`Claude Assistant: Loading index from ${this.dbPath}...`);
      const startTime = Date.now();
      await this.loadIndex();
      const elapsed = Date.now() - startTime;
      this.isLoaded = true;
      Zotero.debug(`Claude Assistant: Local RAG initialized with ${this.chunks.size} chunks, ${this.indexedItemKeys.size} items (loaded in ${elapsed}ms)`);
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: ===== INDEX LOAD FAILED =====`);
      Zotero.debug(`Claude Assistant: Path: ${this.dbPath}`);
      Zotero.debug(`Claude Assistant: Error: ${error.message}`);
      if (error.stack) Zotero.debug(`Claude Assistant: Stack: ${error.stack}`);
      Zotero.debug(`Claude Assistant: Starting with empty index. Papers will need to be re-indexed.`);
      Zotero.debug(`Claude Assistant: ===== END INDEX LOAD ERROR =====`);
      this.isLoaded = true;
    }
  }

  /**
   * Get indexing statistics
   */
  getStats(): IndexStats {
    return {
      indexedItems: this.indexedItemKeys.size,
      totalChunks: this.chunks.size,
      lastIndexedAt: this.lastIndexedAt?.toISOString() || null,
      serverOnline: true // Always online since it's local
    };
  }

  /**
   * Check if an item is already indexed
   */
  isIndexed(itemKey: string): boolean {
    return this.indexedItemKeys.has(itemKey);
  }

  /**
   * Get a list of all indexed papers with metadata
   * Used by the source selection panel in the chat dialog
   */
  getIndexedPaperList(): Array<{
    itemKey: string;
    title: string;
    authors: string;
    year: string;
    chunkCount: number;
  }> {
    const papers = new Map<string, {
      itemKey: string;
      title: string;
      authors: string;
      year: string;
      chunkCount: number;
    }>();

    for (const [, chunk] of this.chunks) {
      if (!papers.has(chunk.itemKey)) {
        papers.set(chunk.itemKey, {
          itemKey: chunk.itemKey,
          title: chunk.title,
          authors: chunk.authors,
          year: chunk.year,
          chunkCount: 0,
        });
      }
      papers.get(chunk.itemKey)!.chunkCount++;
    }

    return Array.from(papers.values()).sort((a, b) => {
      const yearDiff = (parseInt(b.year) || 0) - (parseInt(a.year) || 0);
      return yearDiff !== 0 ? yearDiff : a.title.localeCompare(b.title);
    });
  }

  /**
   * Index a Zotero item
   */
  async indexItem(item: any, forceReindex: boolean = false): Promise<number> {
    const itemKey = item.key;

    // Skip if already indexed (unless forcing)
    if (!forceReindex && this.isIndexed(itemKey)) {
      return 0;
    }

    // Remove existing chunks for this item if re-indexing
    if (this.isIndexed(itemKey)) {
      this.removeItem(itemKey);
    }

    // Get item metadata
    const title = item.getField('title') || 'Untitled';
    const creators = item.getCreators();
    // Prioritize 'author' type, but fall back to any creator type
    let authorNames = creators
      .filter((c: any) => c.creatorType === 'author')
      .map((c: any) => c.lastName || c.name || '')
      .filter((n: string) => n.length > 0)
      .slice(0, 3);
    // If no authors, use any creator (contributor, editor, etc.)
    if (authorNames.length === 0) {
      authorNames = creators
        .map((c: any) => c.lastName || c.name || '')
        .filter((n: string) => n.length > 0)
        .slice(0, 3);
    }
    const authors = authorNames.length > 0
      ? (authorNames.length > 2 ? `${authorNames[0]} et al.` : authorNames.join(', '))
      : '';  // Empty string instead of 'Unknown' - will be handled in UI
    const year = item.getField('year') || item.getField('date')?.substring(0, 4) || '';

    // Extract enriched metadata for index v2
    const abstractNote = item.getField('abstractNote') || '';
    const doi = item.getField('DOI') || '';
    const journal = item.getField('publicationTitle') || item.getField('journalAbbreviation') || '';

    // Get tags
    const tags: string[] = [];
    try {
      const itemTags = item.getTags();
      for (const t of itemTags) {
        tags.push(t.tag || t.name || '');
      }
    } catch (e) { /* tags not critical */ }

    // Get collections
    const collections: string[] = [];
    try {
      const collectionIDs = item.getCollections();
      for (const colId of collectionIDs) {
        const col = Zotero.Collections.get(colId);
        if (col) collections.push(col.name);
      }
    } catch (e) { /* collections not critical */ }

    // Get text content
    let text = '';

    // Try to get fulltext from Zotero's fulltext index
    try {
      const content = await Zotero.Fulltext.getItemContent(item.id);
      if (content && content.text) {
        text = content.text;
      }
    } catch (e) {
      Zotero.debug(`Claude Assistant: No fulltext for ${itemKey}`);
    }

    // If no fulltext, try to get from PDF attachment
    if (!text) {
      const attachments = await item.getBestAttachments();
      for (const attachment of attachments) {
        if (attachment.attachmentContentType === 'application/pdf') {
          try {
            const content = await Zotero.Fulltext.getItemContent(attachment.id);
            if (content && content.text) {
              text = content.text;
              break;
            }
          } catch (e) {
            // Continue to next attachment
          }
        }
      }
    }

    // If still no text, use abstract
    if (!text) {
      text = item.getField('abstractNote') || '';
    }

    if (!text || text.length < 100) {
      Zotero.debug(`Claude Assistant: Skipping ${itemKey} - insufficient text (${text.length} chars)`);
      return 0;
    }

    // Shared metadata for all chunks of this item
    const sharedMeta = {
      itemId: item.id,
      itemKey,
      title,
      authors,
      year,
      tags: tags.length > 0 ? tags : undefined,
      collections: collections.length > 0 ? collections : undefined,
      doi: doi || undefined,
      journal: journal || undefined,
    };

    let chunksAdded = 0;
    let chunkIdx = 0;

    // --- Title chunk (dedicated, section: 'title') ---
    if (title && title !== 'Untitled') {
      const titleChunkId = `${itemKey}_t`;
      this.bm25Index.addDocument(titleChunkId, title);
      this.chunks.set(titleChunkId, {
        ...sharedMeta,
        chunkIndex: chunkIdx++,
        text: title,
        section: 'title',
      });
      chunksAdded++;
    }

    // --- Abstract chunk (dedicated, section: 'abstract') ---
    if (abstractNote && abstractNote.length >= 50) {
      const abstractChunkId = `${itemKey}_a`;
      this.bm25Index.addDocument(abstractChunkId, abstractNote);
      this.chunks.set(abstractChunkId, {
        ...sharedMeta,
        chunkIndex: chunkIdx++,
        text: abstractNote,
        section: 'abstract',
      });
      chunksAdded++;
    }

    // --- Body chunks (section-aware) ---
    const maxBodyChunks = 20;
    let bodyChunkCount = 0;
    const detectedSections = this.detectSections(text);

    for (const section of detectedSections) {
      if (bodyChunkCount >= maxBodyChunks) break;

      // Skip low-value sections
      if (section.name === 'references' || section.name === 'acknowledgements') continue;

      // Skip abstract section if already captured as dedicated chunk
      if (section.name === 'abstract' && abstractNote && abstractNote.length >= 50) continue;

      const sectionChunks = this.chunkByParagraph(
        section.content,
        Preferences.getChunkSize(),
        Preferences.getChunkOverlap()
      );

      for (const chunk of sectionChunks) {
        if (bodyChunkCount >= maxBodyChunks) break;

        const chunkId = `${itemKey}_${chunkIdx}`;

        // Extract page number from chunk if present
        const pageMatch = chunk.match(/<<PAGE_(\d+)>>/);
        const pageNum = pageMatch ? parseInt(pageMatch[1]) : undefined;

        // Clean the chunk text (remove page markers)
        const cleanText = chunk.replace(/<<PAGE_\d+>>/g, '').trim();

        if (cleanText.length < 50) continue;

        // Add to BM25 index
        this.bm25Index.addDocument(chunkId, cleanText);

        // Store chunk metadata with detected section name
        this.chunks.set(chunkId, {
          ...sharedMeta,
          chunkIndex: chunkIdx,
          text: cleanText,
          section: section.name,
          pageNum
        });

        chunkIdx++;
        chunksAdded++;
        bodyChunkCount++;
      }
    }

    if (chunksAdded > 0) {
      this.indexedItemKeys.add(itemKey);
      this.lastIndexedAt = new Date();
    }

    // Generate embeddings for new chunks (non-blocking, never prevents BM25 indexing)
    if (chunksAdded > 0 && this.embeddingService?.isAvailable() && this.embeddingStore) {
      try {
        // Collect chunk IDs for this item that lack embeddings
        const newChunkIds: string[] = [];
        const newChunkTexts: string[] = [];
        for (const [cid, chunk] of this.chunks) {
          if (chunk.itemKey === itemKey) {
            const hasEmb = await this.embeddingStore.hasEmbedding(cid);
            if (!hasEmb) {
              newChunkIds.push(cid);
              newChunkTexts.push(chunk.text);
            }
          }
        }

        if (newChunkIds.length > 0) {
          const embeddings = await this.embeddingService.embedBatch(newChunkTexts);
          const entries: Array<{ chunkId: string; itemKey: string; embedding: any }> = [];
          for (let i = 0; i < newChunkIds.length; i++) {
            if (embeddings[i]) {
              entries.push({
                chunkId: newChunkIds[i],
                itemKey,
                embedding: embeddings[i],
              });
            }
          }
          if (entries.length > 0) {
            await this.embeddingStore.setBatchEmbeddings(
              entries,
              this.embeddingService.getModelVersion()
            );
            // Update in-memory cache for immediate search availability
            for (const entry of entries) {
              this.embeddingCache.set(entry.chunkId, entry.embedding);
            }
          }
        }
      } catch (embError: any) {
        Zotero.debug(`Claude Assistant: Embedding generation for ${itemKey} failed (non-fatal): ${embError.message}`);
      }
    }

    return chunksAdded;
  }

  /**
   * Remove an item from the index
   */
  removeItem(itemKey: string): void {
    // Collect chunk IDs first to avoid modifying the Map during iteration
    const chunkIdsToRemove: string[] = [];
    for (const [chunkId, chunk] of this.chunks) {
      if (chunk.itemKey === itemKey) {
        chunkIdsToRemove.push(chunkId);
      }
    }

    for (const chunkId of chunkIdsToRemove) {
      this.bm25Index.removeDocument(chunkId);
      this.chunks.delete(chunkId);
      this.embeddingCache.delete(chunkId);
    }

    this.indexedItemKeys.delete(itemKey);

    // Remove embeddings for this item (non-blocking)
    if (this.embeddingStore) {
      this.embeddingStore.removeItemEmbeddings(itemKey).catch((e: any) => {
        Zotero.debug(`Claude Assistant: Error removing embeddings for ${itemKey}: ${e.message}`);
      });
    }
  }

  /**
   * Get all chunks (used by embedding generation)
   */
  getChunks(): Map<string, {
    itemId: number;
    itemKey: string;
    chunkIndex: number;
    text: string;
    title: string;
    authors: string;
    year: string;
    section?: string;
    tags?: string[];
    collections?: string[];
    doi?: string;
    journal?: string;
    pageNum?: number;
  }> {
    return this.chunks;
  }

  /**
   * BM25 keyword search (extracted from search() for composability)
   */
  bm25Search(query: string, limit: number = 25, itemKeys?: string[]): RAGSearchResult[] {
    // Get more results than needed so field weighting can re-rank
    const rawResults = this.bm25Index.search(query, itemKeys ? limit * 5 : limit * 3);

    // Apply field-weight multipliers based on section metadata
    const fieldWeights: Record<string, number> = {
      title: 3.0, abstract: 2.0, results: 1.5, conclusion: 1.5,
      introduction: 1.3, discussion: 1.3, background: 1.1,
      methods: 1.0, body: 1.0, supplementary: 0.8
    };
    let weightedResults = rawResults.map(result => {
      const chunk = this.chunks.get(result.docId)!;
      const sectionWeight = fieldWeights[chunk.section || 'body'] || 1.0;
      return { ...result, score: result.score * sectionWeight };
    });

    // Filter by item keys if specified (paper-scoped search)
    if (itemKeys && itemKeys.length > 0) {
      const keySet = new Set(itemKeys);
      const filtered = weightedResults.filter(r => {
        const chunk = this.chunks.get(r.docId);
        return chunk && keySet.has(chunk.itemKey);
      });

      // If BM25 returned too few hits from the specified papers,
      // supplement with all chunks from those papers (handles vague queries
      // like "what does this paper say" where BM25 matches are sparse)
      if (filtered.length < limit) {
        const seen = new Set(filtered.map(r => r.docId));
        const sectionScore: Record<string, number> = { title: 0.003, abstract: 0.002, body: 0.001 };
        for (const [chunkId, chunk] of this.chunks) {
          if (keySet.has(chunk.itemKey) && !seen.has(chunkId)) {
            filtered.push({
              docId: chunkId,
              score: sectionScore[chunk.section || 'body'] ?? 0.001
            });
            seen.add(chunkId);
          }
        }
      }
      weightedResults = filtered;
    }

    // Re-sort after field weighting
    weightedResults.sort((a, b) => b.score - a.score);
    const topResults = weightedResults.slice(0, limit);

    // Normalize scores relative to the maximum score
    const maxScore = topResults.length > 0 ? topResults[0].score : 1;

    return topResults.map(result => {
      const chunk = this.chunks.get(result.docId)!;
      const normalizedScore = maxScore > 0 ? Math.min((result.score / maxScore) * 0.99, 0.99) : 0;
      return {
        item_key: chunk.itemKey,
        item_id: chunk.itemId,
        chunk_index: chunk.chunkIndex,
        chunk_text: chunk.text,
        text: chunk.text,
        title: chunk.title,
        authors: chunk.authors,
        year: chunk.year,
        score: normalizedScore,
        page_num: chunk.pageNum,
        section: chunk.section,
        journal: chunk.journal,
        doi: chunk.doi,
        tags: chunk.tags,
        collections: chunk.collections
      };
    });
  }

  /**
   * Cosine similarity between two L2-normalized vectors (reduces to dot product)
   */
  private cosineSimilarity(a: Float32Array, b: Float32Array): number {
    let dot = 0;
    for (let i = 0; i < a.length; i++) {
      dot += a[i] * b[i];
    }
    return dot;
  }

  /**
   * Semantic search using embedding cosine similarity
   */
  private async semanticSearch(query: string, limit: number, itemKeys?: string[]): Promise<RAGSearchResult[]> {
    if (!this.embeddingService?.isAvailable() || this.embeddingCache.size === 0) {
      return [];
    }

    // Get query embedding
    const queryEmbedding = await this.embeddingService.embed(query);
    if (!queryEmbedding) return [];

    const keySet = itemKeys && itemKeys.length > 0 ? new Set(itemKeys) : null;

    // Compute similarity against all cached embeddings
    const scored: Array<{ chunkId: string; score: number }> = [];
    for (const [chunkId, embedding] of this.embeddingCache) {
      // Only score chunks that still exist in the index
      if (!this.chunks.has(chunkId)) continue;
      // Filter by item keys if specified
      if (keySet) {
        const chunk = this.chunks.get(chunkId)!;
        if (!keySet.has(chunk.itemKey)) continue;
      }
      const sim = this.cosineSimilarity(queryEmbedding, embedding);
      if (sim > 0.2) { // Threshold to filter noise
        scored.push({ chunkId, score: sim });
      }
    }

    // Sort by similarity descending
    scored.sort((a, b) => b.score - a.score);
    const topResults = scored.slice(0, limit);

    // Normalize scores to 0-0.99
    const maxScore = topResults.length > 0 ? topResults[0].score : 1;

    return topResults.map(result => {
      const chunk = this.chunks.get(result.chunkId)!;
      const normalizedScore = maxScore > 0 ? Math.min((result.score / maxScore) * 0.99, 0.99) : 0;
      return {
        item_key: chunk.itemKey,
        item_id: chunk.itemId,
        chunk_index: chunk.chunkIndex,
        chunk_text: chunk.text,
        text: chunk.text,
        title: chunk.title,
        authors: chunk.authors,
        year: chunk.year,
        score: normalizedScore,
        page_num: chunk.pageNum,
        section: chunk.section,
        journal: chunk.journal,
        doi: chunk.doi,
        tags: chunk.tags,
        collections: chunk.collections
      };
    });
  }

  /**
   * Reciprocal Rank Fusion: merge BM25 and semantic results
   * RRF score = w1/(k + rank1) + w2/(k + rank2)
   * k=60 is standard; documents in only one list get penalty rank 1000
   */
  private rrfMerge(
    bm25Results: RAGSearchResult[],
    semanticResults: RAGSearchResult[],
    limit: number,
    k: number = 60,
    wBm25: number = 1.0,
    wSemantic: number = 1.0
  ): RAGSearchResult[] {
    // Build rank maps (chunkId → rank, 0-indexed)
    const bm25Ranks = new Map<string, number>();
    bm25Results.forEach((r, i) => {
      const key = `${r.item_key}_${r.chunk_index}`;
      bm25Ranks.set(key, i);
    });

    const semanticRanks = new Map<string, number>();
    semanticResults.forEach((r, i) => {
      const key = `${r.item_key}_${r.chunk_index}`;
      semanticRanks.set(key, i);
    });

    // Collect all unique documents
    const allDocs = new Map<string, RAGSearchResult>();
    for (const r of bm25Results) {
      allDocs.set(`${r.item_key}_${r.chunk_index}`, r);
    }
    for (const r of semanticResults) {
      const key = `${r.item_key}_${r.chunk_index}`;
      if (!allDocs.has(key)) {
        allDocs.set(key, r);
      }
    }

    // Compute RRF scores
    const penaltyRank = 1000;
    const scored: Array<{ key: string; result: RAGSearchResult; rrfScore: number }> = [];

    for (const [key, result] of allDocs) {
      const bm25Rank = bm25Ranks.has(key) ? bm25Ranks.get(key)! : penaltyRank;
      const semRank = semanticRanks.has(key) ? semanticRanks.get(key)! : penaltyRank;

      const rrfScore = wBm25 / (k + bm25Rank + 1) + wSemantic / (k + semRank + 1);
      scored.push({ key, result, rrfScore });
    }

    // Sort by RRF score descending
    scored.sort((a, b) => b.rrfScore - a.rrfScore);
    const topResults = scored.slice(0, limit);

    // Normalize to 0-0.99
    const maxRRF = topResults.length > 0 ? topResults[0].rrfScore : 1;

    return topResults.map(s => ({
      ...s.result,
      score: maxRRF > 0 ? Math.min((s.rrfScore / maxRRF) * 0.99, 0.99) : 0
    }));
  }

  /**
   * Merge results from multiple query formulations using RRF
   * Used by query rewriting to combine results from alternative phrasings
   */
  multiQueryMerge(resultSets: RAGSearchResult[][], limit: number, k: number = 60): RAGSearchResult[] {
    if (resultSets.length === 0) return [];
    if (resultSets.length === 1) return resultSets[0].slice(0, limit);

    const allDocs = new Map<string, RAGSearchResult>();
    const scores = new Map<string, number>();

    for (const results of resultSets) {
      results.forEach((r, rank) => {
        const key = `${r.item_key}_${r.chunk_index}`;
        if (!allDocs.has(key)) allDocs.set(key, r);
        scores.set(key, (scores.get(key) || 0) + 1 / (k + rank + 1));
      });
    }

    const scored = Array.from(allDocs.entries()).map(([key, result]) => ({
      key, result, score: scores.get(key) || 0
    }));

    scored.sort((a, b) => b.score - a.score);
    const topResults = scored.slice(0, limit);
    const maxScore = topResults.length > 0 ? topResults[0].score : 1;

    return topResults.map(s => ({
      ...s.result,
      score: maxScore > 0 ? Math.min((s.score / maxScore) * 0.99, 0.99) : 0
    }));
  }

  /**
   * Search the index - routes by mode (keyword, semantic, hybrid)
   * Defaults to 'keyword' for backward compatibility; callers can pass 'hybrid' when embeddings are available
   */
  async search(query: string, limit: number = 25, mode: 'keyword' | 'semantic' | 'hybrid' = 'keyword', itemKeys?: string[]): Promise<RAGSearchResult[]> {
    if (mode === 'keyword') {
      return this.bm25Search(query, limit, itemKeys);
    }

    if (mode === 'semantic') {
      const results = await this.semanticSearch(query, limit, itemKeys);
      // Fall back to BM25 if semantic returns nothing
      return results.length > 0 ? results : this.bm25Search(query, limit, itemKeys);
    }

    // Hybrid mode: merge BM25 + semantic via RRF
    const bm25Results = this.bm25Search(query, limit, itemKeys);
    const semanticResults = await this.semanticSearch(query, limit, itemKeys);

    // If no semantic results available, fall back to BM25 only
    if (semanticResults.length === 0) {
      return bm25Results;
    }

    return this.rrfMerge(bm25Results, semanticResults, limit);
  }

  /**
   * Index all items in the library
   */
  async indexLibrary(
    progressCallback?: (current: number, total: number) => void,
    forceReindex: boolean = false
  ): Promise<{ indexed: number; skipped: number; errors: number; noText?: number }> {
    const items = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID);
    const regularItems = items.filter((item: any) =>
      item.isRegularItem() && !item.isNote() && !item.isAttachment()
    );

    let indexed = 0;
    let skipped = 0;  // Already indexed items
    let noText = 0;   // Items with no extractable text
    let errors = 0;

    for (let i = 0; i < regularItems.length; i++) {
      const item = regularItems[i];

      if (progressCallback) {
        progressCallback(i + 1, regularItems.length);
      }

      try {
        // Check if already indexed before calling indexItem
        const alreadyIndexed = !forceReindex && this.isIndexed(item.key);
        const chunksAdded = await this.indexItem(item, forceReindex);

        if (chunksAdded > 0) {
          indexed++;
        } else if (alreadyIndexed) {
          skipped++;
        } else {
          noText++;
        }
      } catch (error: any) {
        Zotero.debug(`Claude Assistant: Error indexing ${item.key}: ${error.message}`);
        errors++;
      }
    }

    // Save the index
    await this.saveIndex();

    return { indexed, skipped, errors, noText };
  }

  /**
   * Clear the entire index
   */
  async clearIndex(): Promise<void> {
    this.bm25Index.clear();
    this.chunks.clear();
    this.indexedItemKeys.clear();
    this.embeddingCache.clear();
    this.lastIndexedAt = null;

    // Delete the index file using IOUtils (Zotero 7 / Firefox 102+)
    try {
      await IOUtils.remove(this.dbPath);
    } catch (e) {
      // File might not exist
    }
  }

  /**
   * Save the index to disk
   */
  async saveIndex(): Promise<void> {
    try {
      const data = {
        version: 3,
        lastIndexedAt: this.lastIndexedAt?.toISOString(),
        indexedItemKeys: Array.from(this.indexedItemKeys),
        chunks: Array.from(this.chunks.entries()),
        bm25Index: this.bm25Index.toJSON()
      };

      const jsonStr = JSON.stringify(data);
      const encoder = new TextEncoder();
      // Use IOUtils (Zotero 7 / Firefox 102+) instead of deprecated OS.File
      await IOUtils.write(this.dbPath, encoder.encode(jsonStr));

      Zotero.debug(`Claude Assistant: Index saved (${this.chunks.size} chunks)`);
    } catch (error: any) {
      Zotero.debug(`Claude Assistant: Error saving index: ${error.message}`);
      throw error;
    }
  }

  /**
   * Load the index from disk
   */
  private async loadIndex(): Promise<void> {
    // Use IOUtils (Zotero 7 / Firefox 102+) instead of deprecated OS.File
    const bytes = await IOUtils.read(this.dbPath);
    Zotero.debug(`Claude Assistant: Read ${bytes.byteLength} bytes from index file`);

    const decoder = new TextDecoder();
    const jsonStr = decoder.decode(bytes);
    Zotero.debug(`Claude Assistant: Decoded ${jsonStr.length} characters, parsing JSON...`);

    const data = JSON.parse(jsonStr);

    if (data.version !== 1 && data.version !== 2 && data.version !== 3) {
      throw new Error(`Unsupported index version: ${data.version}`);
    }

    this.lastIndexedAt = data.lastIndexedAt ? new Date(data.lastIndexedAt) : null;

    // Load chunks
    if (data.chunks && Array.isArray(data.chunks)) {
      this.chunks = new Map(data.chunks);
      Zotero.debug(`Claude Assistant: Loaded ${this.chunks.size} chunks`);
    } else {
      Zotero.debug(`Claude Assistant: WARNING - chunks data missing or invalid in index file`);
      this.chunks = new Map();
    }

    // Derive indexedItemKeys from actual chunks (authoritative source of truth)
    // This prevents drift where indexedItemKeys has entries with no corresponding chunks
    this.indexedItemKeys = new Set<string>();
    for (const [, chunk] of this.chunks) {
      this.indexedItemKeys.add(chunk.itemKey);
    }
    const savedKeyCount = data.indexedItemKeys ? data.indexedItemKeys.length : 0;
    if (savedKeyCount !== this.indexedItemKeys.size) {
      Zotero.debug(`Claude Assistant: Reconciled indexedItemKeys: ${savedKeyCount} saved → ${this.indexedItemKeys.size} actual (derived from chunks)`);
    }

    // Load BM25 index
    if (data.bm25Index) {
      this.bm25Index.fromJSON(data.bm25Index);
      Zotero.debug(`Claude Assistant: BM25 index loaded (${this.bm25Index.size} documents)`);
    } else {
      Zotero.debug(`Claude Assistant: WARNING - bm25Index data missing in index file`);
    }

    Zotero.debug(`Claude Assistant: Index loaded successfully - ${this.chunks.size} chunks, ${this.indexedItemKeys.size} items`);
  }

  /**
   * Detect academic paper sections from text
   * Returns array of { name, content } with normalized section names
   */
  private detectSections(text: string): Array<{ name: string; content: string }> {
    const sectionPatterns = [
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Abstract|Summary)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?Introduction\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Background|Literature\s+Review|Related\s+Work)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Methods?|Methodology|Materials?\s+and\s+Methods?|Experimental(?:\s+Section)?)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Results?|Findings)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Discussion|Results?\s+and\s+Discussion)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Conclusions?|Summary\s+and\s+Conclusions?|Concluding\s+Remarks?)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:References|Bibliography)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Supplementary|Supporting\s+Information|Appendix)\s*$/im,
      /^(?:#{1,3}\s+)?(?:\d+\.?\s*)?(?:Acknowledgements?|Funding)\s*$/im,
    ];

    const normalizeSection = (header: string): string => {
      const h = header.replace(/^\d+\.?\s*/, '').trim().toLowerCase();
      if (/^(?:abstract|summary)$/.test(h)) return 'abstract';
      if (/^intro/.test(h)) return 'introduction';
      if (/^(?:background|literature|related)/.test(h)) return 'background';
      if (/^(?:method|experimental|materials)/.test(h)) return 'methods';
      if (/^(?:result|finding)/.test(h)) return 'results';
      if (/^discussion|^results?\s+and\s+discussion/.test(h)) return 'discussion';
      if (/^conclu/.test(h)) return 'conclusion';
      if (/^(?:refer|biblio)/.test(h)) return 'references';
      if (/^(?:supple|support|appendix)/.test(h)) return 'supplementary';
      if (/^(?:acknowledge|funding)/.test(h)) return 'acknowledgements';
      return 'body';
    };

    const lines = text.split('\n');
    const sections: Array<{ name: string; startLine: number }> = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.length === 0 || line.length > 100) continue;

      for (const pattern of sectionPatterns) {
        if (pattern.test(line)) {
          sections.push({ name: normalizeSection(line), startLine: i });
          break;
        }
      }
    }

    // If no sections detected, return the whole text as one 'body' section
    if (sections.length === 0) {
      return [{ name: 'body', content: text }];
    }

    const result: Array<{ name: string; content: string }> = [];

    // Content before first section header
    if (sections[0].startLine > 0) {
      const preContent = lines.slice(0, sections[0].startLine).join('\n').trim();
      if (preContent.length > 50) {
        result.push({ name: 'body', content: preContent });
      }
    }

    for (let i = 0; i < sections.length; i++) {
      const startLine = sections[i].startLine + 1;
      const endLine = i + 1 < sections.length ? sections[i + 1].startLine : lines.length;
      const content = lines.slice(startLine, endLine).join('\n').trim();
      if (content.length > 50) {
        result.push({ name: sections[i].name, content });
      }
    }

    return result;
  }

  /**
   * Chunk text by paragraph boundaries, falling back to chunkText() for oversized paragraphs
   */
  private chunkByParagraph(text: string, maxChunkSize: number, overlap: number): string[] {
    if (text.length <= maxChunkSize) return [text];

    const paragraphs = text.split(/\n\s*\n/).filter(p => p.trim().length > 0);
    const chunks: string[] = [];
    let currentChunk = '';

    for (const para of paragraphs) {
      if (currentChunk.length + para.length + 2 > maxChunkSize && currentChunk.length > 0) {
        chunks.push(currentChunk.trim());
        // Keep overlap from end of current chunk
        const overlapText = currentChunk.length > overlap
          ? currentChunk.substring(currentChunk.length - overlap)
          : '';
        currentChunk = overlapText + '\n\n' + para;
      } else {
        currentChunk += (currentChunk ? '\n\n' : '') + para;
      }
    }

    if (currentChunk.trim().length > 50) {
      chunks.push(currentChunk.trim());
    }

    // Fallback: split chunks still too large using chunkText()
    const finalChunks: string[] = [];
    for (const chunk of chunks) {
      if (chunk.length > maxChunkSize * 1.5) {
        finalChunks.push(...this.chunkText(chunk, maxChunkSize, overlap));
      } else {
        finalChunks.push(chunk);
      }
    }

    return finalChunks;
  }

  /**
   * Chunk text into smaller pieces with overlap
   */
  private chunkText(text: string, chunkSize: number, overlap: number): string[] {
    const chunks: string[] = [];

    if (text.length <= chunkSize) {
      return [text];
    }

    let start = 0;
    while (start < text.length) {
      let end = start + chunkSize;

      // Try to end at a sentence boundary
      if (end < text.length) {
        const lastPeriod = text.lastIndexOf('.', end);
        const lastQuestion = text.lastIndexOf('?', end);
        const lastExclaim = text.lastIndexOf('!', end);
        const lastNewline = text.lastIndexOf('\n', end);

        const boundaryPos = Math.max(lastPeriod, lastQuestion, lastExclaim, lastNewline);

        if (boundaryPos > start + chunkSize / 2) {
          end = boundaryPos + 1;
        }
      }

      const chunk = text.substring(start, Math.min(end, text.length)).trim();
      if (chunk.length > 50) {
        chunks.push(chunk);
      }

      start = end - overlap;
      if (start >= text.length - overlap) break;
    }

    return chunks;
  }
}
