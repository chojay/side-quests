/**
 * Build script for Claude Research Assistant
 * Compiles TypeScript and bundles the addon
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Artifacts whose absence silently disables semantic search. Historically each
// of these only produced a console.warn while the build still exited 0, which
// meant a perfectly normal-looking .xpi could ship with half of retrieval dead.
// We now collect them and fail the build unless --allow-degraded is passed.
const missingSemanticArtifacts = [];
const ALLOW_DEGRADED =
  process.argv.includes('--allow-degraded') || process.env.ZCA_ALLOW_DEGRADED === '1';

function requireSemanticArtifact(label, remedy) {
  missingSemanticArtifacts.push({ label, remedy });
}

const BUILD_DIR = path.join(__dirname, '..', 'build');
const ADDON_DIR = path.join(__dirname, '..', 'addon');
const SRC_DIR = path.join(__dirname, '..', 'src');
const NODE_MODULES = path.join(__dirname, '..', 'node_modules');

console.log('Building Claude Research Assistant...\n');

// Step 1: Clean build directory
console.log('1. Cleaning build directory...');
if (fs.existsSync(BUILD_DIR)) {
  fs.rmSync(BUILD_DIR, { recursive: true });
}
fs.mkdirSync(BUILD_DIR, { recursive: true });

// Step 2: Compile TypeScript
console.log('2. Compiling TypeScript...');
try {
  // Resolve tsc from node_modules so `node scripts/build.js` also works outside npm scripts.
  const tscBin = require.resolve('typescript/bin/tsc');
  execSync(`"${process.execPath}" "${tscBin}"`, { stdio: 'inherit' });
  console.log('   ✓ TypeScript compiled');
} catch (error) {
  console.error('   ✗ TypeScript compilation failed');
  process.exit(1);
}

// Step 3: Prepare addon structure
console.log('3. Preparing addon structure...');

const addonBuildDir = path.join(BUILD_DIR, 'addon');

// Create directory structure
const dirs = [
  'content/scripts',
  'content/icons',
];

dirs.forEach((dir) => {
  fs.mkdirSync(path.join(addonBuildDir, dir), { recursive: true });
});

// Step 4: Bundle with esbuild
console.log('4. Bundling with esbuild...');
try {
  const esbuild = require('esbuild');

  esbuild.buildSync({
    entryPoints: [path.join(BUILD_DIR, 'index.js')],
    bundle: true,
    outfile: path.join(addonBuildDir, 'content', 'scripts', 'index.js'),
    platform: 'browser', // Zotero runs in a browser-like context
    target: 'firefox115', // Zotero 8 ships Firefox 115; Zotero 9 ships Firefox 140. firefox115 is the widest-compat baseline.
    format: 'iife',
    globalName: 'ClaudeAssistant',
    external: [],         // No external dependencies - everything is bundled
  });

  console.log('   ✓ Bundle created');
} catch (error) {
  console.error('   ✗ Bundling failed:', error);
  process.exit(1);
}

// Step 5: Copy addon files
console.log('5. Copying addon files...');

const filesToCopy = [
  { src: path.join(ADDON_DIR, 'manifest.json'), dest: 'manifest.json' },
  { src: path.join(ADDON_DIR, 'bootstrap.js'), dest: 'bootstrap.js' },
  // chrome.manifest removed - chrome resources registered programmatically in bootstrap.js
  {
    src: path.join(ADDON_DIR, 'content', 'preferences.xhtml'),
    dest: 'content/preferences.xhtml',
  },
  {
    src: path.join(ADDON_DIR, 'content', 'preferences.js'),
    dest: 'content/preferences.js',
  },
  {
    src: path.join(ADDON_DIR, 'content', 'chat-dialog.xhtml'),
    dest: 'content/chat-dialog.xhtml',
  },
  {
    src: path.join(ADDON_DIR, 'content', 'icons', 'icon-48.png'),
    dest: 'content/icons/icon-48.png',
  },
  {
    src: path.join(ADDON_DIR, 'content', 'icons', 'icon-96.png'),
    dest: 'content/icons/icon-96.png',
  },
];

filesToCopy.forEach(({ src, dest }) => {
  if (fs.existsSync(src)) {
    const destPath = path.join(addonBuildDir, dest);
    fs.mkdirSync(path.dirname(destPath), { recursive: true });
    fs.copyFileSync(src, destPath);
  } else {
    console.warn(`   ⚠ File not found: ${src}`);
  }
});

console.log('   ✓ Addon files copied');

// Step 6: Copy embedding worker and Transformers.js
console.log('6. Copying embedding infrastructure...');

// Copy embedding worker script
const workerSrc = path.join(ADDON_DIR, 'content', 'scripts', 'embedding-worker.js');
if (fs.existsSync(workerSrc)) {
  fs.copyFileSync(workerSrc, path.join(addonBuildDir, 'content', 'scripts', 'embedding-worker.js'));
  console.log('   ✓ embedding-worker.js');
}

// Copy Transformers.js from node_modules
const transformersSrc = path.join(NODE_MODULES, '@huggingface', 'transformers', 'dist', 'transformers.min.js');
if (fs.existsSync(transformersSrc)) {
  fs.copyFileSync(transformersSrc, path.join(addonBuildDir, 'content', 'scripts', 'transformers.min.js'));
  console.log('   ✓ transformers.min.js');
} else {
  console.warn(`   ⚠ transformers.min.js not found at ${transformersSrc}`);
  requireSemanticArtifact(
    'transformers.min.js',
    'Run "npm install" first; this file is vendored from node_modules/@huggingface/transformers/dist/.'
  );
}

// Copy ONNX runtime WASM files (needed by Transformers.js)
const wasmFiles = ['ort-wasm-simd-threaded.jsep.wasm', 'ort-wasm-simd-threaded.jsep.mjs'];
wasmFiles.forEach((wasmFile) => {
  const wasmSrc = path.join(NODE_MODULES, '@huggingface', 'transformers', 'dist', wasmFile);
  if (fs.existsSync(wasmSrc)) {
    fs.copyFileSync(wasmSrc, path.join(addonBuildDir, 'content', 'scripts', wasmFile));
    console.log(`   ✓ ${wasmFile}`);
  } else {
    console.warn(`   ⚠ ${wasmFile} not found`);
    requireSemanticArtifact(
      wasmFile,
      'Run "npm install"; ONNX Runtime WASM ships inside @huggingface/transformers/dist/.'
    );
  }
});

// Copy ONNX Runtime bundle from onnxruntime-web (referenced by the webpack bundle for sub-workers).
//
// onnxruntime-web arrives TRANSITIVELY via @huggingface/transformers, so it is
// not guaranteed to be hoisted to the top level of node_modules. Resolving it
// through Node's own resolver handles both the hoisted and the nested layout;
// the previous hardcoded top-level path silently missed the nested case and
// produced a build with broken semantic search.
// require.resolve('<pkg>/package.json') is not usable here: onnxruntime-web
// declares an "exports" map without "./package.json", so current Node throws
// ERR_PACKAGE_PATH_NOT_EXPORTED. Walk Node's lookup paths for the directory instead.
function resolvePackageDir(pkgName) {
  const projectRoot = path.join(__dirname, '..');
  const candidates = (require.resolve.paths(pkgName) || [])
    .concat([path.join(projectRoot, 'node_modules', '@huggingface', 'transformers', 'node_modules')])
    .map((dir) => path.join(dir, pkgName));
  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, 'package.json'))) return dir;
  }
  return null;
}

const ortDir = resolvePackageDir('onnxruntime-web');
const ortBundleSrc = ortDir
  ? path.join(ortDir, 'dist', 'ort.bundle.min.mjs')
  : path.join(NODE_MODULES, 'onnxruntime-web', 'dist', 'ort.bundle.min.mjs');
if (fs.existsSync(ortBundleSrc)) {
  fs.copyFileSync(ortBundleSrc, path.join(addonBuildDir, 'content', 'scripts', 'ort.bundle.min.mjs'));
  console.log('   ✓ ort.bundle.min.mjs');
} else {
  console.warn(`   ⚠ ort.bundle.min.mjs not found at ${ortBundleSrc}`);
  requireSemanticArtifact(
    'ort.bundle.min.mjs',
    'Run "npm install". onnxruntime-web arrives transitively via @huggingface/transformers.'
  );
}

// Copy license and third-party notices so the packaged .xpi carries them
// (required for the Apache-2.0 and MIT components bundled above)
['LICENSE', 'THIRD_PARTY_NOTICES.md'].forEach((noticeFile) => {
  const noticeSrc = path.join(__dirname, '..', noticeFile);
  if (fs.existsSync(noticeSrc)) {
    fs.copyFileSync(noticeSrc, path.join(addonBuildDir, noticeFile));
    console.log(`   ✓ ${noticeFile}`);
  } else {
    console.warn(`   ⚠ ${noticeFile} not found - the packaged .xpi must include license notices`);
  }
});

// Copy model files
const modelSrcDir = path.join(ADDON_DIR, 'content', 'models', 'e5-base-v2');
const modelDestDir = path.join(addonBuildDir, 'content', 'models', 'e5-base-v2');

function copyDirRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

if (fs.existsSync(modelSrcDir)) {
  copyDirRecursive(modelSrcDir, modelDestDir);
  console.log('   ✓ Model files (e5-base-v2)');
}

// The recursive copy above happily succeeds with only config/tokenizer JSON
// present, which is exactly the state a fresh clone is in. Check the weights
// explicitly: without them the worker cannot load the model at runtime.
const onnxWeights = path.join(modelSrcDir, 'onnx', 'model_quantized.onnx');
if (fs.existsSync(onnxWeights)) {
  const mb = fs.statSync(onnxWeights).size / (1024 * 1024);
  if (mb < 50) {
    console.warn(`   ⚠ model_quantized.onnx is only ${mb.toFixed(1)} MB, expected roughly 110 MB (truncated download?)`);
    requireSemanticArtifact(
      'model_quantized.onnx (truncated)',
      'Delete addon/content/models/e5-base-v2/onnx/model_quantized.onnx and re-run ./scripts/fetch-model.sh'
    );
  } else {
    console.log(`   ✓ model_quantized.onnx (${mb.toFixed(1)} MB)`);
  }
} else {
  console.warn('   ⚠ model_quantized.onnx not found');
  requireSemanticArtifact(
    'model_quantized.onnx',
    'Run "./scripts/fetch-model.sh" to download the ~110 MB quantized weights.'
  );
}

if (missingSemanticArtifacts.length > 0) {
  const summary = missingSemanticArtifacts
    .map((m) => `   - ${m.label}\n     ${m.remedy}`)
    .join('\n');

  if (ALLOW_DEGRADED) {
    console.warn('\n⚠ DEGRADED BUILD: semantic search will NOT work in this .xpi.');
    console.warn('  Missing artifacts:');
    console.warn(summary);
    console.warn('  Continuing because --allow-degraded or ZCA_ALLOW_DEGRADED=1 was given.\n');
  } else {
    console.error('\n✗ Build FAILED: semantic search artifacts are missing.');
    console.error('  This build would produce an .xpi where hybrid search silently');
    console.error('  degrades to keyword-only, with no indication to the user.\n');
    console.error('  Missing artifacts:');
    console.error(summary);
    console.error('\n  Fix the above, or build a keyword-only plugin on purpose:');
    console.error('    ZCA_ALLOW_DEGRADED=1 npm run package\n');
    process.exit(1);
  }
}

console.log('\n✓ Build complete!');
console.log(`   Output: ${addonBuildDir}`);
if (missingSemanticArtifacts.length === 0) {
  console.log('   Semantic search: enabled (all artifacts present)');
} else {
  console.log('   Semantic search: DISABLED (degraded build)');
}
