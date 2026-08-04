import {
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  renameSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, join, parse, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import {
  InstallConflict,
  defaultTarget,
  detectOpenCode,
  getStatus,
  installAgents,
  loadManifest,
  openCodeConfigPath,
  patchOpenCodeConfig,
  renderOpenCodeAgents,
  uninstallAgents,
} from "./doct-agents.js";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BUNDLED_AGENTS = join(PACKAGE_ROOT, "agents");

function entryAt(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function validateDirectoryComponents(path) {
  const target = resolve(path);
  const root = parse(target).root;
  const parts = target.slice(root.length).split(sep).filter(Boolean);
  let current = root;
  for (const part of parts) {
    current = join(current, part);
    const entry = entryAt(current);
    if (!entry) break;
    if (entry.isSymbolicLink()) {
      throw new InstallConflict(`Path component is a symbolic link: ${current}`);
    }
    if (!entry.isDirectory()) {
      throw new InstallConflict(`Path component is not a directory: ${current}`);
    }
  }
  return target;
}

function prepareDirectory(path) {
  const target = validateDirectoryComponents(path);
  mkdirSync(target, { recursive: true });
  validateDirectoryComponents(target);
  const entry = entryAt(target);
  if (!entry?.isDirectory() || entry.isSymbolicLink()) {
    throw new InstallConflict(`Directory must be a real directory: ${target}`);
  }
  return target;
}

function readRegularText(path, fallback = null) {
  const entry = entryAt(path);
  if (!entry) return fallback;
  if (entry.isSymbolicLink()) throw new InstallConflict(`Config is a symbolic link: ${path}`);
  if (!entry.isFile()) throw new InstallConflict(`Config is not a regular file: ${path}`);
  return readFileSync(path, "utf8");
}

function writeRegularTextAtomic(path, text) {
  const parent = prepareDirectory(dirname(path));
  const current = entryAt(path);
  if (current?.isSymbolicLink()) throw new InstallConflict(`Config is a symbolic link: ${path}`);
  if (current && !current.isFile()) throw new InstallConflict(`Config is not a regular file: ${path}`);

  const stage = mkdtempSync(join(parent, `.${basename(path)}.doct-agents-config-`));
  const staged = join(stage, "next");
  const backup = join(stage, "previous");
  writeFileSync(staged, text, "utf8");
  let movedOriginal = false;
  try {
    if (current) {
      renameSync(path, backup);
      movedOriginal = true;
    }
    renameSync(staged, path);
  } catch (error) {
    try {
      if (entryAt(path)) unlinkSync(path);
      if (movedOriginal && entryAt(backup)) renameSync(backup, path);
    } catch (rollbackError) {
      throw new InstallConflict(
        `${error.message}; config rollback also failed: ${rollbackError.message}; backup at ${stage}`,
      );
    }
    throw error;
  } finally {
    rmSync(stage, { recursive: true, force: true });
  }
}

function restoreConfig(path, previousText, existed) {
  if (existed) {
    writeRegularTextAtomic(path, previousText);
  } else {
    const entry = entryAt(path);
    if (entry?.isSymbolicLink()) throw new InstallConflict(`Config is a symbolic link: ${path}`);
    if (entry) unlinkSync(path);
  }
}

function configPathFromManifest(target, manifest) {
  if (manifest.config?.filename) {
    return join(dirname(resolve(target)), manifest.config.filename);
  }
  return openCodeConfigPath(target);
}

export function installOpenCode({
  targetDir,
  sourceDir = BUNDLED_AGENTS,
  force = false,
}) {
  const target = resolve(targetDir);
  const previousManifest = loadManifest(target, "opencode");
  const configPath = configPathFromManifest(target, previousManifest);
  const previousConfigText = readRegularText(configPath, "{}\n");
  const configExisted = existsSync(configPath);
  const configPatch = patchOpenCodeConfig(previousConfigText, {
    expectedHash: previousManifest.config?.mcpEntrySha256 ?? null,
    force,
  });

  prepareDirectory(dirname(configPath));
  const renderDir = mkdtempSync(join(dirname(configPath), ".doct-agents-opencode-render-"));
  try {
    renderOpenCodeAgents(sourceDir, renderDir);
    writeRegularTextAtomic(configPath, configPatch.text);
    try {
      const result = installAgents({
        sourceDir: renderDir,
        targetDir: target,
        force,
        platform: "opencode",
        manifestMetadata: {
          config: {
            filename: basename(configPath),
            mcpEntrySha256: configPatch.mcpEntrySha256,
          },
        },
      });
      return { ...result, configPath };
    } catch (error) {
      restoreConfig(configPath, previousConfigText, configExisted);
      throw error;
    }
  } finally {
    rmSync(renderDir, { recursive: true, force: true });
  }
}

export function getOpenCodeStatus(targetDir) {
  const target = resolve(targetDir);
  const agentStatus = getStatus(target, { platform: "opencode" });
  const manifest = agentStatus.manifest;
  if (!manifest.config) {
    return { ...agentStatus, config: "missing", configPath: openCodeConfigPath(target) };
  }
  const configPath = configPathFromManifest(target, manifest);
  const text = readRegularText(configPath, null);
  if (text === null) return { ...agentStatus, config: "missing", configPath };
  try {
    const probe = patchOpenCodeConfig(text, {
      expectedHash: manifest.config.mcpEntrySha256,
    });
    return { ...agentStatus, config: probe.changed ? "missing" : "installed", configPath };
  } catch (error) {
    if (error instanceof InstallConflict && /modified/i.test(error.message)) {
      return { ...agentStatus, config: "modified", configPath };
    }
    throw error;
  }
}

export function uninstallOpenCode(targetDir, { force = false } = {}) {
  const target = resolve(targetDir);
  const manifest = loadManifest(target, "opencode");
  let configPreserved = false;
  let configPath = null;
  let originalConfigText = null;
  let configChanged = false;

  if (manifest.config) {
    configPath = configPathFromManifest(target, manifest);
    originalConfigText = readRegularText(configPath, null);
    if (originalConfigText !== null) {
      try {
        const patch = patchOpenCodeConfig(originalConfigText, {
          expectedHash: manifest.config.mcpEntrySha256,
          force,
          remove: true,
        });
        if (patch.changed) {
          writeRegularTextAtomic(configPath, patch.text);
          configChanged = true;
        }
      } catch (error) {
        if (!force && error instanceof InstallConflict && /modified/i.test(error.message)) {
          configPreserved = true;
        } else {
          throw error;
        }
      }
    }
  }

  try {
    const result = uninstallAgents(target, { force, platform: "opencode" });
    return { ...result, configPreserved, configPath };
  } catch (error) {
    if (configChanged && configPath && originalConfigText !== null) {
      writeRegularTextAtomic(configPath, originalConfigText);
    }
    throw error;
  }
}

function parseArgs(argv) {
  const args = [...argv];
  let command = "install";
  if (args[0] && !args[0].startsWith("-")) command = args.shift();
  if (!["install", "update", "status", "uninstall"].includes(command)) {
    throw new Error(`Unknown command: ${command}`);
  }

  const options = {
    command,
    scope: "user",
    workspace: process.cwd(),
    target: null,
    force: false,
    platform: null,
  };
  while (args.length > 0) {
    const flag = args.shift();
    if (flag === "--force") options.force = true;
    else if (flag === "--scope") options.scope = args.shift();
    else if (flag === "--workspace") options.workspace = args.shift();
    else if (flag === "--target") options.target = args.shift();
    else if (flag === "--platform") options.platform = args.shift();
    else if (flag === "--help" || flag === "-h") options.help = true;
    else throw new Error(`Unknown option: ${flag}`);
  }
  if (!["user", "workspace"].includes(options.scope)) {
    throw new Error("--scope must be user or workspace");
  }
  if (options.platform !== null && !["copilot", "opencode", "all"].includes(options.platform)) {
    throw new Error("--platform must be copilot, opencode, or all");
  }
  if (options.platform === "all" && options.target) {
    throw new Error("--target cannot be combined with --platform all");
  }
  return options;
}

function selectedPlatforms(options) {
  if (options.platform === "all") return ["copilot", "opencode"];
  if (options.platform) return [options.platform];
  if (options.target) return ["copilot"];
  if (["status", "uninstall"].includes(options.command)) return ["copilot"];
  return detectOpenCode({ workspace: options.workspace })
    ? ["copilot", "opencode"]
    : ["copilot"];
}

function printHelp() {
  console.log(`doct-agents - manage Copilot and OpenCode custom agents\n\nUsage:\n  doct-agents [install|update|status|uninstall] [options]\n\nOptions:\n  --platform copilot|opencode|all\n                           Select an explicit host platform\n  --scope user|workspace   Install for all projects or current workspace\n  --workspace <path>       Workspace root for workspace scope\n  --target <path>          Override one platform destination directory\n  --force                  Replace or remove modified managed files/config\n  -h, --help               Show this help\n`);
}

function platformTarget(options, platform) {
  if (options.target) return resolve(options.target);
  return defaultTarget(options.scope, options.workspace, homedir(), platform);
}

function printStatus(platform, status, prefix) {
  console.log(`${prefix}Target: ${status.target}`);
  console.log(`${prefix}Installed: ${status.installed.length}`);
  console.log(`${prefix}Modified: ${status.modified.join(", ") || "none"}`);
  console.log(`${prefix}Missing: ${status.missing.join(", ") || "none"}`);
  if (platform === "opencode") console.log(`${prefix}Browser MCP config: ${status.config}`);
}

function runPlatform(options, platform, multiple) {
  const target = platformTarget(options, platform);
  const prefix = multiple ? `[${platform}] ` : "";

  if (options.command === "status") {
    const status = platform === "opencode"
      ? getOpenCodeStatus(target)
      : getStatus(target, { platform: "copilot" });
    if (!(status.installed.length || status.modified.length || status.missing.length)) {
      console.log(`${prefix}doct-agents is not installed in ${status.target}`);
      return 1;
    }
    printStatus(platform, status, prefix);
    return status.modified.length || status.missing.length || status.config === "modified" || status.config === "missing"
      ? 2
      : 0;
  }

  if (options.command === "uninstall") {
    const result = platform === "opencode"
      ? uninstallOpenCode(target, { force: options.force })
      : uninstallAgents(target, { force: options.force, platform: "copilot" });
    console.log(`${prefix}Removed ${result.removed} managed agent files from ${result.target}`);
    if (result.preserved.length) {
      console.log(`${prefix}Preserved modified files: ${result.preserved.join(", ")}`);
    }
    if (result.configPreserved) {
      console.log(`${prefix}Preserved modified OpenCode doct_playwright MCP config`);
    }
    return result.preserved.length || result.configPreserved ? 2 : 0;
  }

  const result = platform === "opencode"
    ? installOpenCode({ targetDir: target, force: options.force })
    : installAgents({ targetDir: target, force: options.force, platform: "copilot" });
  const verb = options.command === "update" ? "Updated" : "Installed";
  console.log(`${prefix}${verb} ${result.installed} agents in ${result.target}`);
  if (platform === "opencode") {
    console.log(`${prefix}Configured isolated Playwright MCP in ${result.configPath}`);
  }
  return 0;
}

export function run(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  if (options.help) {
    printHelp();
    return 0;
  }

  const platforms = selectedPlatforms(options);
  let exitCode = 0;
  for (const platform of platforms) {
    try {
      exitCode = Math.max(exitCode, runPlatform(options, platform, platforms.length > 1));
    } catch (error) {
      if (platforms.length === 1) throw error;
      console.error(`[${platform}] error: ${error.message}`);
      exitCode = Math.max(exitCode, 1);
    }
  }
  return exitCode;
}
