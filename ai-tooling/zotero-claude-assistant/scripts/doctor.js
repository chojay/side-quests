#!/usr/bin/env node
/**
 * doctor.js - preflight and diagnostic checks for Claude Research Assistant.
 *
 * Exists because of a real failure: an installed copy of this plugin ran
 * with a dead embedder. Hybrid search silently fell back to
 * BM25, the embeddings table stayed empty, and nothing in the build or the
 * UI ever said so. Every individual layer "handled it gracefully" and the sum
 * of that graceful handling was an invisible outage.
 *
 * Two classes of check:
 *   HARD  - repo integrity (version drift, missing committed files). Always exit 1.
 *   SOFT  - semantic-search artifacts that are fetched or installed rather than
 *           committed. Reported loudly, but the gate for those is scripts/build.js,
 *           which supports an explicit --allow-degraded opt-out.
 *
 * Usage:
 *   node scripts/doctor.js                 full report
 *   node scripts/doctor.js --quiet         only problems (used by npm run build)
 *   node scripts/doctor.js --check-runtime also probe a running Zotero plugin
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

const ROOT = path.join(__dirname, '..');
const QUIET = process.argv.includes('--quiet');
const CHECK_RUNTIME = process.argv.includes('--check-runtime');

const hard = [];
const soft = [];
const notes = [];

function ok(msg) { if (!QUIET) console.log(`  ✓ ${msg}`); }
function hardFail(msg, remedy) { hard.push({ msg, remedy }); }
function softFail(msg, remedy) { soft.push({ msg, remedy }); }
function read(p) { try { return fs.readFileSync(path.join(ROOT, p), 'utf8'); } catch (e) { return null; } }
function exists(p) { return fs.existsSync(path.join(ROOT, p)); }

if (!QUIET) console.log('\nClaude Research Assistant :: doctor\n');

// ---------------------------------------------------------------- versions
if (!QUIET) console.log('Version consistency');
const versionTs = read('src/version.ts');
const canonical = versionTs && (versionTs.match(/VERSION\s*=\s*'([^']+)'/) || [])[1];

if (!canonical) {
  hardFail('Could not read VERSION from src/version.ts', 'Ensure src/version.ts exports a VERSION string literal.');
} else {
  const sources = [
    ['package.json', (read('package.json') || '').match(/"version":\s*"([^"]+)"/)],
    ['addon/manifest.json', (read('addon/manifest.json') || '').match(/"version":\s*"([^"]+)"/)],
    ['updates.json', (read('updates.json') || '').match(/"version":\s*"([^"]+)"/)],
    ['addon/content/preferences.xhtml', (read('addon/content/preferences.xhtml') || '').match(/Claude Research Assistant v([0-9]+\.[0-9]+\.[0-9]+)/)],
  ];
  let drift = false;
  for (const [file, m] of sources) {
    const found = m && m[1];
    if (!found) { hardFail(`No version string found in ${file}`, 'Add one, or update doctor.js if the format changed.'); drift = true; }
    else if (found !== canonical) { hardFail(`Version drift: ${file} is ${found}, src/version.ts is ${canonical}`, `Set ${file} to ${canonical}.`); drift = true; }
  }
  const updLink = (read('updates.json') || '').match(/releases\/download\/(?:zotero-claude-assistant-)?v([0-9]+\.[0-9]+\.[0-9]+)\//);
  if (updLink && updLink[1] !== canonical) {
    hardFail(`updates.json update_link points at v${updLink[1]}, expected v${canonical}`, `Update the release URL to v${canonical}.`);
    drift = true;
  }
  if (!drift) ok(`All version strings agree at ${canonical}`);
}

// ------------------------------------------------------- committed sources
if (!QUIET) console.log('\nCommitted plugin files');
for (const f of [
  'addon/content/scripts/embedding-worker.js',
  'addon/content/models/e5-base-v2/config.json',
  'addon/content/models/e5-base-v2/tokenizer.json',
  'addon/content/models/e5-base-v2/tokenizer_config.json',
  'addon/bootstrap.js',
  'addon/manifest.json',
]) {
  if (exists(f)) ok(f); else hardFail(`Missing committed file: ${f}`, 'This file should be in git. Restore it.');
}

// ------------------------------------------------- semantic-search artifacts
if (!QUIET) console.log('\nSemantic search artifacts');

if (!exists('node_modules')) {
  softFail('node_modules/ is absent', 'Run "npm install". Without it the build cannot vendor Transformers.js or the ONNX runtime, and semantic search will be dead in the packaged .xpi.');
} else {
  ok('node_modules/ present');
  const tj = 'node_modules/@huggingface/transformers/dist/transformers.min.js';
  if (exists(tj)) ok('transformers.min.js resolvable');
  else softFail('transformers.min.js not found', 'Run "npm install".');

  // onnxruntime-web declares an "exports" map without "./package.json", so
  // require.resolve('onnxruntime-web/package.json') throws
  // ERR_PACKAGE_PATH_NOT_EXPORTED on current Node even when the package is
  // installed. Look for the package directory on Node's lookup paths instead
  // (hoisted layout first, then nested under @huggingface/transformers).
  let ortDir = null;
  const ortCandidates = (require.resolve.paths('onnxruntime-web') || [])
    .concat([path.join(ROOT, 'node_modules', '@huggingface', 'transformers', 'node_modules')])
    .map((dir) => path.join(dir, 'onnxruntime-web'));
  for (const dir of ortCandidates) {
    if (fs.existsSync(path.join(dir, 'package.json'))) { ortDir = dir; break; }
  }
  if (ortDir && fs.existsSync(path.join(ortDir, 'dist', 'ort.bundle.min.mjs'))) {
    ok(`onnxruntime-web resolvable (${path.relative(ROOT, ortDir)})`);
    notes.push('onnxruntime-web is a TRANSITIVE dependency via @huggingface/transformers. build.js resolves it through Node rather than assuming npm hoisted it to the top level.');
  } else {
    softFail('onnxruntime-web/dist/ort.bundle.min.mjs not resolvable', 'Run "npm install". It normally arrives transitively via @huggingface/transformers.');
  }
}

const weights = 'addon/content/models/e5-base-v2/onnx/model_quantized.onnx';
if (exists(weights)) {
  const mb = fs.statSync(path.join(ROOT, weights)).size / (1024 * 1024);
  if (mb < 50) softFail(`model_quantized.onnx is only ${mb.toFixed(1)} MB (expected ~110 MB)`, 'Delete it and re-run ./scripts/fetch-model.sh; the download was truncated.');
  else ok(`model_quantized.onnx present (${mb.toFixed(1)} MB)`);
} else {
  softFail('model_quantized.onnx is absent', 'Run "./scripts/fetch-model.sh" to download the ~110 MB quantized e5-base-v2 weights. They are gitignored by design.');
}

// -------------------------------------------------------------- runtime
function probeRuntime() {
  return new Promise((resolve) => {
    const req = http.request(
      { host: '127.0.0.1', port: 23119, path: '/claude-assistant/status', method: 'GET', timeout: 4000 },
      (res) => {
        let body = '';
        res.on('data', (c) => (body += c));
        res.on('end', () => { try { resolve({ status: res.statusCode, body: JSON.parse(body) }); } catch (e) { resolve({ status: res.statusCode, body }); } });
      }
    );
    req.on('error', (e) => resolve({ error: e.code || e.message }));
    req.on('timeout', () => { req.destroy(); resolve({ error: 'timeout' }); });
    req.end();
  });
}

(async () => {
  if (CHECK_RUNTIME) {
    if (!QUIET) console.log('\nRunning plugin (127.0.0.1:23119)');
    const r = await probeRuntime();
    if (r.error) {
      console.log(`  ? Could not reach the plugin: ${r.error}`);
      console.log('    Zotero may not be running, or this build is not installed. Not treated as a failure.');
    } else if (r.status === 404) {
      console.log('  ! /claude-assistant/status returned 404.');
      console.log('    The installed plugin predates v2.3.0. Install the current build to get health reporting.');
    } else if (r.body && r.body.embedding) {
      const e = r.body.embedding;
      if (e.available) {
        ok(`Embedder live (${e.modelVersion}), ${r.body.embeddingCount} embeddings, ${r.body.indexedItems} items indexed`);
      } else {
        console.log(`  ✗ Installed plugin has NO working embedder: ${e.code} - ${e.message}`);
        if (e.remedy) console.log(`    Remedy: ${e.remedy}`);
        console.log(`    Retrieval is currently ${r.body.retrievalMode}.`);
      }
    } else {
      console.log(`  ? Unexpected response: ${JSON.stringify(r).slice(0, 200)}`);
    }
  }

  if (soft.length) {
    console.log('\n⚠ Semantic search will NOT work until these are resolved:');
    for (const s of soft) console.log(`  - ${s.msg}\n    ${s.remedy}`);
    console.log('  (BM25 keyword search is unaffected. "npm run build" will refuse to');
    console.log('   produce an .xpi in this state unless ZCA_ALLOW_DEGRADED=1 is set.)');
  }

  if (hard.length) {
    console.error('\n✗ Repo integrity problems:');
    for (const h of hard) console.error(`  - ${h.msg}\n    ${h.remedy}`);
    console.error('');
    process.exit(1);
  }

  if (!QUIET) {
    if (notes.length) { console.log('\nNotes'); for (const n of notes) console.log(`  - ${n}`); }
    console.log(soft.length ? '\nRepo integrity OK; semantic artifacts incomplete.\n' : '\nAll checks passed.\n');
  }
})();
