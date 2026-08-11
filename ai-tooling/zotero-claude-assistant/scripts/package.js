/**
 * Package script for Claude Research Assistant
 * Creates a .xpi file for distribution using archiver (cross-platform,
 * no system zip binary required)
 */

const fs = require('fs');
const path = require('path');
const archiver = require('archiver');

const BUILD_DIR = path.join(__dirname, '..', 'build', 'addon');
const DIST_DIR = path.join(__dirname, '..', 'dist');
const XPI_NAME = 'claude-assistant.xpi';
const XPI_PATH = path.join(DIST_DIR, XPI_NAME);

console.log('Packaging Claude Research Assistant...\n');

if (!fs.existsSync(BUILD_DIR)) {
  console.error(`✗ Build directory not found: ${BUILD_DIR}`);
  console.error('  Run "npm run build" first.');
  process.exit(1);
}

// Create dist directory
if (!fs.existsSync(DIST_DIR)) {
  fs.mkdirSync(DIST_DIR, { recursive: true });
}

// Remove old XPI if it exists
if (fs.existsSync(XPI_PATH)) {
  fs.unlinkSync(XPI_PATH);
}

const output = fs.createWriteStream(XPI_PATH);
const archive = archiver('zip', { zlib: { level: 9 } });

output.on('close', () => {
  const stats = fs.statSync(XPI_PATH);
  console.log(`\n✓ Package created: ${XPI_NAME}`);
  console.log(`  Size: ${(stats.size / 1024).toFixed(2)} KB`);
  console.log(`  Location: ${DIST_DIR}`);
});

archive.on('warning', (err) => {
  console.warn('⚠ Packaging warning:', err.message);
});

archive.on('error', (err) => {
  console.error('✗ Packaging failed:', err.message);
  process.exit(1);
});

archive.pipe(output);
// dot: false skips dotfiles (.DS_Store etc.), matching the old `zip -x ".*"`
archive.glob('**/*', { cwd: BUILD_DIR, dot: false });
archive.finalize();
