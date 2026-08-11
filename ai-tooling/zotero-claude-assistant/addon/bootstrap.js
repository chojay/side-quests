/* global Cc, Ci, Cu, Services, Zotero, ChromeUtils */

var rootURI = "";
var chromeHandle;

function log(msg) {
  if (typeof Zotero !== "undefined" && Zotero.debug) {
    Zotero.debug("Claude Assistant: " + msg);
  } else {
    dump("Claude Assistant: " + msg + "\n");
  }
}

function startup({ id, version, resourceURI, rootURI: aRootURI }, reason) {
  rootURI = aRootURI;
  log("Starting up");

  // Register chrome resources
  var aomStartup = Cc["@mozilla.org/addons/addon-manager-startup;1"]
    .getService(Ci.amIAddonManagerStartup);
  var manifestURI = Services.io.newURI(rootURI + "manifest.json");
  chromeHandle = aomStartup.registerChrome(manifestURI, [
    ["content", "claudeassistant", "content/"]
  ]);
  log("Chrome resources registered");

  // Load module
  Services.scriptloader.loadSubScript(rootURI + "content/scripts/index.js");

  // Initialize addon
  if (typeof Zotero.ClaudeAssistant !== "undefined") {
    log("ClaudeAssistant found, calling init()...");
    Zotero.ClaudeAssistant.init({ id, version, rootURI }).then(() => {
      log("Init completed successfully");

      // Register UI for any existing windows
      // onMainWindowLoad only fires for NEW windows, so we need to handle existing ones
      const windows = Zotero.getMainWindows();
      log(`Found ${windows.length} existing windows`);
      for (const win of windows) {
        log("Registering UI for existing window");
        Zotero.ClaudeAssistant.onMainWindowLoad(win);
      }
    }).catch((error) => {
      log(`Init failed: ${error.message}`);
      log(`Init error stack: ${error.stack}`);
    });
  } else {
    log("ERROR: ClaudeAssistant not defined after loading script!");
  }
}

function shutdown({ id, version, resourceURI, rootURI }, reason) {
  log("Shutting down");

  // Clean up UI from all registered windows
  if (typeof Zotero !== "undefined" && typeof Zotero.ClaudeAssistant !== "undefined") {
    const windows = Zotero.getMainWindows();
    log(`Cleaning up ${windows.length} windows`);
    for (const win of windows) {
      Zotero.ClaudeAssistant.onMainWindowUnload(win);
    }

    // General cleanup
    Zotero.ClaudeAssistant.cleanup();

    // Drop the global so re-enabling or upgrading loads a fresh instance
    delete Zotero.ClaudeAssistant;
  }

  // Unregister chrome resources
  if (chromeHandle) {
    chromeHandle.destruct();
    chromeHandle = null;
    log("Chrome resources unregistered");
  }
}

/**
 * Zotero 7 window hook - called when main window loads
 */
function onMainWindowLoad({ window }) {
  log("Main window loading, registering UI...");

  if (typeof Zotero.ClaudeAssistant !== "undefined") {
    Zotero.ClaudeAssistant.onMainWindowLoad(window);
  } else {
    log("ERROR: ClaudeAssistant not found in onMainWindowLoad");
  }
}

/**
 * Zotero 7 window hook - called when main window unloads
 */
function onMainWindowUnload({ window }) {
  log("Main window unloading, cleaning up UI...");

  if (typeof Zotero.ClaudeAssistant !== "undefined") {
    Zotero.ClaudeAssistant.onMainWindowUnload(window);
  }
}

function install(data, reason) {
  log("Installing");
}

function uninstall(data, reason) {
  log("Uninstalling");
}
