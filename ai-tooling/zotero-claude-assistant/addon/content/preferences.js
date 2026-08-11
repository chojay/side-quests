/**
 * Preferences pane script for Claude Assistant
 * Simplified for local RAG (no Python required)
 */

(function() {
  'use strict';

  const PREF_BRANCH = 'extensions.claudeassistant.';

  // Preference keys
  const PREFS = {
    claudeApiKey: 'claudeApiKey',
    claudeModel: 'claudeModel',
    chunkSize: 'chunkSize',
    chunkOverlap: 'chunkOverlap',
    maxResults: 'maxResults',
    queryRewriting: 'queryRewriting',
  };

  // Initialize when script loads
  function initPreferences() {
    console.log('Claude Assistant: Initializing preferences...');

    const claudeApiKey = document.getElementById('claude-api-key');
    if (!claudeApiKey) {
      console.log('Claude Assistant: Elements not ready, retrying...');
      setTimeout(initPreferences, 100);
      return;
    }

    try {
      loadPreferences();
      loadStats();
      console.log('Claude Assistant: Preferences loaded successfully');
    } catch (error) {
      console.error('Claude Assistant: Error loading preferences:', error);
    }
  }

  setTimeout(initPreferences, 0);

  function loadPreferences() {
    // Load Claude API key
    loadTextPref('claude-api-key', PREFS.claudeApiKey);

    // Load configuration
    loadTextPref('chunk-size', PREFS.chunkSize);
    loadTextPref('chunk-overlap', PREFS.chunkOverlap);
    loadTextPref('max-results', PREFS.maxResults);

    // Load model selection
    loadMenulistPref('claude-model', PREFS.claudeModel);

    // Load query-rewriting checkbox
    loadCheckboxPref('query-rewriting', PREFS.queryRewriting);

    // Add change listeners
    addChangeListeners();
  }

  function loadTextPref(elementId, prefKey) {
    const element = document.getElementById(elementId);
    if (element) {
      const fullPrefKey = PREF_BRANCH + prefKey;
      const value = Zotero.Prefs.get(fullPrefKey, true);

      if (value !== undefined && value !== null && value !== '') {
        element.value = value;
      }
    }
  }

  function loadMenulistPref(elementId, prefKey) {
    const element = document.getElementById(elementId);
    if (element) {
      const value = Zotero.Prefs.get(PREF_BRANCH + prefKey, true);
      if (value !== undefined) {
        element.value = value;
      }
    }
  }

  function loadCheckboxPref(elementId, prefKey) {
    const element = document.getElementById(elementId);
    if (element) {
      const value = Zotero.Prefs.get(PREF_BRANCH + prefKey, true);
      element.checked = value === 'true' || value === true;
    }
  }

  function addChangeListeners() {
    // Text inputs - save on change
    addTextListener('claude-api-key', PREFS.claudeApiKey);
    addTextListener('chunk-size', PREFS.chunkSize);
    addTextListener('chunk-overlap', PREFS.chunkOverlap);
    addTextListener('max-results', PREFS.maxResults);

    // Model selection
    addMenulistListener('claude-model', PREFS.claudeModel);

    // Checkbox
    addCheckboxListener('query-rewriting', PREFS.queryRewriting);
  }

  function addTextListener(elementId, prefKey) {
    const element = document.getElementById(elementId);
    if (element) {
      const saveValue = function() {
        const value = element.value || '';
        Zotero.Prefs.set(PREF_BRANCH + prefKey, value, true);
      };
      element.addEventListener('change', saveValue);
      element.addEventListener('blur', saveValue);
    }
  }

  function addMenulistListener(elementId, prefKey) {
    const element = document.getElementById(elementId);
    if (element) {
      element.addEventListener('command', function() {
        Zotero.Prefs.set(PREF_BRANCH + prefKey, element.value, true);
      });
    }
  }

  function addCheckboxListener(elementId, prefKey) {
    const element = document.getElementById(elementId);
    if (element) {
      element.addEventListener('command', function() {
        Zotero.Prefs.set(PREF_BRANCH + prefKey, element.checked.toString(), true);
      });
    }
  }

  async function loadStats() {
    try {
      if (Zotero.ClaudeAssistant) {
        const stats = await Zotero.ClaudeAssistant.getStats();
        if (stats) {
          const indexedCount = document.getElementById('indexed-count');
          const chunkCount = document.getElementById('chunk-count');
          const lastIndexed = document.getElementById('last-indexed');

          if (indexedCount) indexedCount.value = stats.indexedItems || 0;
          if (chunkCount) chunkCount.value = stats.totalChunks || 0;

          // Update embedding count
          const embeddingCount = document.getElementById('embedding-count');
          if (embeddingCount) {
            embeddingCount.value = stats.embeddingCount || 0;
            if (stats.embeddingServiceAvailable) {
              embeddingCount.value += ' (service ready)';
            }
          }

          if (lastIndexed && stats.lastIndexedAt) {
            const date = new Date(stats.lastIndexedAt);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            let timeAgo;
            if (diffMins < 1) {
              timeAgo = 'Just now';
            } else if (diffMins < 60) {
              timeAgo = `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
            } else if (diffHours < 24) {
              timeAgo = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
            } else if (diffDays < 7) {
              timeAgo = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
            } else {
              timeAgo = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            }

            lastIndexed.value = timeAgo;
            lastIndexed.setAttribute('tooltiptext', date.toLocaleString());
          } else if (lastIndexed) {
            lastIndexed.value = 'Never';
          }
        }
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Global functions for button handlers
  // ═══════════════════════════════════════════════════════════════

  window.saveClaudeApiKey = function() {
    const element = document.getElementById('claude-api-key');
    const value = element?.value || '';
    const prefKey = PREF_BRANCH + PREFS.claudeApiKey;
    const statusLabel = document.getElementById('claude-api-status');

    // Validate API key format
    if (value && !value.startsWith('sk-ant-')) {
      if (statusLabel) {
        statusLabel.value = '⚠ Warning: Claude API keys usually start with "sk-ant-"';
        statusLabel.style.color = 'orange';
      }
    }

    try {
      Zotero.Prefs.set(prefKey, value, true);

      if (statusLabel) {
        statusLabel.value = value ? '✓ API key saved' : '✓ API key cleared';
        statusLabel.style.color = 'green';
      }
    } catch (error) {
      if (statusLabel) {
        statusLabel.value = '✗ Save failed: ' + error.message;
        statusLabel.style.color = 'red';
      }
    }
  };

  window.testClaudeConnection = async function() {
    const statusLabel = document.getElementById('claude-api-status');
    const apiKeyInput = document.getElementById('claude-api-key');
    const modelSelect = document.getElementById('claude-model');

    if (!apiKeyInput.value) {
      statusLabel.value = 'Please enter API key first';
      statusLabel.style.color = 'orange';
      return;
    }

    statusLabel.value = 'Testing connection...';
    statusLabel.style.color = 'blue';

    try {
      // Use Zotero's HTTP API
      const response = await Zotero.HTTP.request('POST', 'https://api.anthropic.com/v1/messages', {
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKeyInput.value,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: modelSelect?.value || 'claude-sonnet-4-6',
          max_tokens: 10,
          messages: [{ role: 'user', content: 'Hi' }],
        }),
        timeout: 30000,
        responseType: 'json',
      });

      if (response.status >= 200 && response.status < 300) {
        statusLabel.value = '✓ Connection successful!';
        statusLabel.style.color = 'green';
        // Auto-save on successful test
        window.saveClaudeApiKey();
      } else {
        const errorBody = typeof response.response === 'string'
          ? JSON.parse(response.response)
          : response.response;
        statusLabel.value = `✗ Error: ${errorBody?.error?.message || 'Connection failed'}`;
        statusLabel.style.color = 'red';
      }
    } catch (error) {
      statusLabel.value = `✗ Error: ${error.message || 'Connection failed'}`;
      statusLabel.style.color = 'red';
    }
  };

  // ═══════════════════════════════════════════════════════════════
  // Indexing functions
  // ═══════════════════════════════════════════════════════════════

  window.indexLibrary = async function() {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (!Zotero.ClaudeAssistant) {
      if (statusLabel) statusLabel.value = 'Error: Plugin not loaded';
      return;
    }

    statusLabel.value = 'Indexing...';
    statusLabel.style.color = 'blue';
    detailsLabel.textContent = 'Starting incremental indexing...';

    try {
      await Zotero.ClaudeAssistant.indexLibrary((current, total, message) => {
        detailsLabel.textContent = message || `Processing ${current}/${total}...`;
      });

      statusLabel.value = 'Complete';
      statusLabel.style.color = 'green';
      detailsLabel.textContent = 'Indexing finished successfully';

      // Reload stats
      await loadStats();
    } catch (error) {
      statusLabel.value = 'Error';
      statusLabel.style.color = 'red';
      detailsLabel.textContent = `Error: ${error.message}`;
    }
  };

  window.indexRandom10 = async function() {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (!Zotero.ClaudeAssistant) {
      if (statusLabel) statusLabel.value = 'Error: Plugin not loaded';
      return;
    }

    statusLabel.value = 'Testing...';
    statusLabel.style.color = 'blue';
    detailsLabel.textContent = 'Indexing 10 random papers...';

    try {
      await Zotero.ClaudeAssistant.indexRandom10();

      statusLabel.value = 'Complete';
      statusLabel.style.color = 'green';
      detailsLabel.textContent = 'Test indexing finished';

      // Reload stats
      await loadStats();
    } catch (error) {
      statusLabel.value = 'Error';
      statusLabel.style.color = 'red';
      detailsLabel.textContent = `Error: ${error.message}`;
    }
  };

  window.reindexLibrary = async function() {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (!Zotero.ClaudeAssistant) {
      if (statusLabel) statusLabel.value = 'Error: Plugin not loaded';
      return;
    }

    statusLabel.value = 'Re-indexing...';
    statusLabel.style.color = 'blue';
    detailsLabel.textContent = 'Starting full re-index...';

    try {
      await Zotero.ClaudeAssistant.reindexAll((current, total, message) => {
        detailsLabel.textContent = message || `Processing ${current}/${total}...`;
      });

      statusLabel.value = 'Complete';
      statusLabel.style.color = 'green';
      detailsLabel.textContent = 'Re-indexing finished successfully';

      // Reload stats
      await loadStats();
    } catch (error) {
      statusLabel.value = 'Error';
      statusLabel.style.color = 'red';
      detailsLabel.textContent = `Error: ${error.message}`;
    }
  };

  window.clearIndex = async function() {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (!Zotero.ClaudeAssistant) {
      if (statusLabel) statusLabel.value = 'Error: Plugin not loaded';
      return;
    }

    // Confirm with user
    const confirmed = confirm('Are you sure you want to clear the entire index? You will need to re-index your library.');
    if (!confirmed) return;

    statusLabel.value = 'Clearing...';
    statusLabel.style.color = 'blue';
    detailsLabel.textContent = 'Clearing index...';

    try {
      await Zotero.ClaudeAssistant.clearIndex();

      statusLabel.value = 'Cleared';
      statusLabel.style.color = 'green';
      detailsLabel.textContent = 'Index cleared successfully';

      // Reload stats
      await loadStats();
    } catch (error) {
      statusLabel.value = 'Error';
      statusLabel.style.color = 'red';
      detailsLabel.textContent = `Error: ${error.message}`;
    }
  };

  window.verifyIndex = async function() {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (!Zotero.ClaudeAssistant) {
      if (statusLabel) statusLabel.value = 'Error: Plugin not loaded';
      return;
    }

    statusLabel.value = 'Verifying...';
    statusLabel.style.color = 'blue';

    try {
      await Zotero.ClaudeAssistant.verifyEmbeddings();

      statusLabel.value = 'Ready';
      statusLabel.style.color = 'green';

      // Reload stats to show current state
      await loadStats();
    } catch (error) {
      statusLabel.value = 'Error';
      statusLabel.style.color = 'red';
      detailsLabel.textContent = `Error: ${error.message}`;
    }
  };

  window.generateEmbeddings = async function() {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (!Zotero.ClaudeAssistant) {
      if (statusLabel) statusLabel.value = 'Error: Plugin not loaded';
      return;
    }

    statusLabel.value = 'Generating embeddings...';
    statusLabel.style.color = 'blue';
    detailsLabel.textContent = 'Starting embedding generation...';

    try {
      const result = await Zotero.ClaudeAssistant.generateEmbeddings((current, total, message) => {
        detailsLabel.textContent = message || `Processing ${current}/${total}...`;
      });

      statusLabel.value = 'Complete';
      statusLabel.style.color = 'green';
      detailsLabel.textContent = `Embeddings: ${result.generated} generated, ${result.skipped} skipped, ${result.errors} errors`;

      // Reload stats
      await loadStats();
    } catch (error) {
      statusLabel.value = 'Error';
      statusLabel.style.color = 'red';
      detailsLabel.textContent = `Error: ${error.message}`;
    }
  };

  // Update activity status (called from addon.ts)
  window.updateActivityStatus = function(status, details) {
    const statusLabel = document.getElementById('activity-status');
    const detailsLabel = document.getElementById('activity-details');

    if (statusLabel) {
      statusLabel.value = status;

      if (status.includes('Error') || status.includes('Failed')) {
        statusLabel.style.color = 'red';
      } else if (status.includes('Complete') || status.includes('Ready')) {
        statusLabel.style.color = 'green';
      } else {
        statusLabel.style.color = 'blue';
      }
    }

    if (detailsLabel && details) {
      detailsLabel.textContent = details;
    }
  };
})();
