/**
 * Single source of truth for the plugin version.
 *
 * Lives in its own module rather than in index.ts because index.ts imports
 * addon.ts, so addon.ts importing VERSION back from index.ts would be a cycle.
 * scripts/doctor.js cross-checks this value against package.json,
 * addon/manifest.json, updates.json and preferences.xhtml, so version drift
 * across those five files fails the build instead of shipping quietly.
 */
export const VERSION = '2.4.0';
