/**
 * Build script for Claude Research Assistant
 * Compiles TypeScript and bundles the addon
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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
  execSync('tsc', { stdio: 'inherit' });
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
  console.warn(`   ⚠ transformers.min.js not found at ${transformersSrc} - semantic search will not work in this build`);
}

// Copy ONNX runtime WASM files (needed by Transformers.js)
const wasmFiles = ['ort-wasm-simd-threaded.jsep.wasm', 'ort-wasm-simd-threaded.jsep.mjs'];
wasmFiles.forEach((wasmFile) => {
  const wasmSrc = path.join(NODE_MODULES, '@huggingface', 'transformers', 'dist', wasmFile);
  if (fs.existsSync(wasmSrc)) {
    fs.copyFileSync(wasmSrc, path.join(addonBuildDir, 'content', 'scripts', wasmFile));
    console.log(`   ✓ ${wasmFile}`);
  } else {
    console.warn(`   ⚠ ${wasmFile} not found - semantic search will not work in this build`);
  }
});

// Copy ONNX Runtime bundle from onnxruntime-web (referenced by the webpack bundle for sub-workers)
const ortBundleSrc = path.join(NODE_MODULES, 'onnxruntime-web', 'dist', 'ort.bundle.min.mjs');
if (fs.existsSync(ortBundleSrc)) {
  fs.copyFileSync(ortBundleSrc, path.join(addonBuildDir, 'content', 'scripts', 'ort.bundle.min.mjs'));
  console.log('   ✓ ort.bundle.min.mjs');
} else {
  console.warn(`   ⚠ ort.bundle.min.mjs not found - semantic search will not work in this build`);
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
const modelSrcDir = path.join(ADDON_DIR, 'content', 'models', 'bge-small-en-v1.5');
const modelDestDir = path.join(addonBuildDir, 'content', 'models', 'bge-small-en-v1.5');

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
  console.log('   ✓ Model files (bge-small-en-v1.5)');
}

console.log('\n✓ Build complete!');
console.log(`   Output: ${addonBuildDir}`);
