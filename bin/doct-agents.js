#!/usr/bin/env node

import { createHash } from "node:crypto";
import {
  copyFileSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BUNDLED_AGENTS = join(PACKAGE_ROOT, "agents");
const MANIFEST_NAME = ".doct-agents-manifest.json";
const PACKAGE_NAME = "doct-agents";
const REPOSITORY = "OneTwoTen/doct-agents";
const SHA256_PATTERN = /^[a-f0-9]{64}$/i;

export class InstallConflict extends Error {}

function entryAt(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function canonicalManifest(files) {
  return {
    schema: 1,
    package: PACKAGE_NAME,
    repository: REPOSITORY,
    files,
  };
}

export function validateManagedFilename(filename) {
  if (
    typeof filename !== "string" ||
    !filename ||
    filename === "." ||
    filename === ".." ||
    isAbsolute(filename) ||
    basename(filename) !== filename ||
    /[\0/\\:]/.test(filename) ||
    !filename.endsWith(".agent.md")
  ) {
    throw new InstallConflict(`Unsafe managed agent filename: ${JSON.stringify(filename)}`);
  }
  return filename;
}

function managedDestination(target, filename) {
  validateManagedFilename(filename);
  const destination = resolve(target, filename);
  if (dirname(destination) !== target) {
    throw new InstallConflict(`Managed path escapes target directory: ${filename}`);
  }
  return destination;
}

function assertRegularManagedFile(path, filename) {
  const entry = entryAt(path);
  if (!entry) return null;
  if (entry.isSymbolicLink()) {
    throw new InstallConflict(`Managed agent ${filename} is a symbolic link`);
  }
  if (!entry.isFile()) {
    throw new InstallConflict(`Managed agent ${filename} is not a regular file`);
  }
  return entry;
}

function prepareTarget(targetDir) {
  const target = resolve(targetDir);
  mkdirSync(target, { recursive: true });
  const entry = entryAt(target);
  if (!entry || !entry.isDirectory() || entry.isSymbolicLink()) {
    throw new InstallConflict(`Target must be a real directory: ${target}`);
  }
  return target;
}

function manifestPath(target) {
  return join(target, MANIFEST_NAME);
}

function writeManifest(target, files) {
  const path = manifestPath(target);
  const entry = entryAt(path);
  if (entry?.isSymbolicLink()) {
    throw new InstallConflict(`Installer manifest is a symbolic link: ${path}`);
  }
  if (entry && !entry.isFile()) {
    throw new InstallConflict(`Installer manifest is not a regular file: ${path}`);
  }
  writeFileSync(path, `${JSON.stringify(canonicalManifest(files), null, 2)}\n`, "utf8");
}

export function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function defaultTarget(scope, workspace = process.cwd(), home = homedir()) {
  return scope === "workspace"
    ? resolve(workspace, ".github", "agents")
    : resolve(home, ".copilot", "agents");
}

export function loadManifest(targetDir) {
  const target = resolve(targetDir);
  const path = manifestPath(target);
  const entry = entryAt(path);
  if (!entry) return canonicalManifest({});
  if (entry.isSymbolicLink()) {
    throw new InstallConflict(`Installer manifest is a symbolic link: ${path}`);
  }
  if (!entry.isFile()) {
    throw new InstallConflict(`Installer manifest is not a regular file: ${path}`);
  }

  try {
    const manifest = JSON.parse(readFileSync(path, "utf8"));
    if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
      throw new Error("manifest root must be an object");
    }
    if (manifest.schema !== 1) {
      throw new Error(`unsupported schema ${JSON.stringify(manifest.schema)}`);
    }
    const packageMatches = manifest.package === PACKAGE_NAME;
    const repositoryMatches = manifest.repository === REPOSITORY;
    if (!packageMatches && !repositoryMatches) {
      throw new Error("manifest identity does not match doct-agents");
    }
    if (manifest.package !== undefined && !packageMatches) {
      throw new Error(`unexpected package ${JSON.stringify(manifest.package)}`);
    }
    if (manifest.repository !== undefined && !repositoryMatches) {
      throw new Error(`unexpected repository ${JSON.stringify(manifest.repository)}`);
    }
    if (!manifest.files || typeof manifest.files !== "object" || Array.isArray(manifest.files)) {
      throw new Error("files must be an object");
    }

    const files = {};
    for (const [filename, expected] of Object.entries(manifest.files)) {
      validateManagedFilename(filename);
      if (typeof expected !== "string" || !SHA256_PATTERN.test(expected)) {
        throw new Error(`invalid SHA-256 for ${filename}`);
      }
      files[filename] = expected.toLowerCase();
    }
    return canonicalManifest(files);
  } catch (error) {
    if (error instanceof InstallConflict) throw error;
    throw new InstallConflict(`Cannot read installer manifest ${path}: ${error.message}`);
  }
}

export function findAgentFiles(sourceDir = BUNDLED_AGENTS) {
  const files = readdirSync(sourceDir)
    .filter((name) => name.endsWith(".agent.md"))
    .sort();
  if (files.length === 0) {
    throw new Error(`No *.agent.md files found in ${sourceDir}`);
  }
  for (const filename of files) {
    validateManagedFilename(filename);
    const source = join(sourceDir, filename);
    const entry = entryAt(source);
    if (!entry || entry.isSymbolicLink() || !entry.isFile()) {
      throw new InstallConflict(`Bundled agent ${filename} must be a regular file`);
    }
  }
  return files;
}

export function installAgents({ sourceDir = BUNDLED_AGENTS, targetDir, force = false }) {
  const target = prepareTarget(targetDir);
  const files = findAgentFiles(sourceDir);
  const currentNames = new Set(files);
  const previous = loadManifest(target);
  const conflicts = [];
  const obsoleteToRemove = [];
  const preservedObsolete = {};

  for (const filename of files) {
    const destination = managedDestination(target, filename);
    if (!assertRegularManagedFile(destination, filename)) continue;
    const expected = previous.files[filename];
    if (!expected) {
      conflicts.push(`${filename} already exists and is not managed by doct-agents`);
    } else if (sha256(destination) !== expected) {
      conflicts.push(`${filename} was modified after installation`);
    }
  }

  for (const [filename, expected] of Object.entries(previous.files).sort()) {
    if (currentNames.has(filename)) continue;
    const destination = managedDestination(target, filename);
    if (!assertRegularManagedFile(destination, filename)) continue;
    if (sha256(destination) === expected) {
      obsoleteToRemove.push(destination);
    } else {
      preservedObsolete[filename] = expected;
    }
  }

  if (conflicts.length > 0 && !force) {
    throw new InstallConflict(
      `Installation stopped to protect existing files:\n- ${conflicts.join("\n- ")}\n` +
        "Re-run with --force only when replacing those files is intentional.",
    );
  }

  for (const path of obsoleteToRemove) unlinkSync(path);

  const installed = { ...preservedObsolete };
  for (const filename of files) {
    const source = join(sourceDir, filename);
    const destination = managedDestination(target, filename);
    copyFileSync(source, destination);
    installed[filename] = sha256(destination);
  }

  writeManifest(target, installed);
  return { installed: files.length, target };
}

export function getStatus(targetDir) {
  const target = resolve(targetDir);
  const manifest = loadManifest(target);
  const installed = [];
  const modified = [];
  const missing = [];

  for (const [filename, expected] of Object.entries(manifest.files).sort()) {
    const destination = managedDestination(target, filename);
    if (!assertRegularManagedFile(destination, filename)) missing.push(filename);
    else if (sha256(destination) !== expected) modified.push(filename);
    else installed.push(filename);
  }
  return { installed, modified, missing, target };
}

export function uninstallAgents(targetDir, { force = false } = {}) {
  const target = resolve(targetDir);
  const manifest = loadManifest(target);
  const preserved = [];
  const remaining = {};
  const removePaths = [];

  for (const [filename, expected] of Object.entries(manifest.files).sort()) {
    const destination = managedDestination(target, filename);
    if (!assertRegularManagedFile(destination, filename)) continue;
    if (!force && sha256(destination) !== expected) {
      preserved.push(filename);
      remaining[filename] = expected;
    } else {
      removePaths.push(destination);
    }
  }

  for (const path of removePaths) unlinkSync(path);

  const path = manifestPath(target);
  if (Object.keys(remaining).length > 0) {
    writeManifest(target, remaining);
  } else {
    const entry = entryAt(path);
    if (entry?.isSymbolicLink()) {
      throw new InstallConflict(`Installer manifest is a symbolic link: ${path}`);
    }
    if (entry) unlinkSync(path);
  }

  return { removed: removePaths.length, preserved, target };
}

function parseArgs(argv) {
  const args = [...argv];
  let command = "install";
  if (args[0] && !args[0].startsWith("-")) command = args.shift();
  if (!["install", "update", "status", "uninstall"].includes(command)) {
    throw new Error(`Unknown command: ${command}`);
  }

  const options = { command, scope: "user", workspace: process.cwd(), target: null, force: false };
  while (args.length > 0) {
    const flag = args.shift();
    if (flag === "--force") options.force = true;
    else if (flag === "--scope") options.scope = args.shift();
    else if (flag === "--workspace") options.workspace = args.shift();
    else if (flag === "--target") options.target = args.shift();
    else if (flag === "--help" || flag === "-h") options.help = true;
    else throw new Error(`Unknown option: ${flag}`);
  }
  if (!["user", "workspace"].includes(options.scope)) {
    throw new Error("--scope must be user or workspace");
  }
  return options;
}

function printHelp() {
  console.log(`doct-agents - manage VS Code custom agents\n\nUsage:\n  doct-agents [install|update|status|uninstall] [options]\n\nOptions:\n  --scope user|workspace   Install for all projects or current workspace\n  --workspace <path>       Workspace root for workspace scope\n  --target <path>          Override the destination directory\n  --force                  Replace or remove modified managed files\n  -h, --help               Show this help\n`);
}

export function run(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  if (options.help) {
    printHelp();
    return 0;
  }
  const target = options.target || defaultTarget(options.scope, options.workspace);

  if (options.command === "status") {
    const status = getStatus(target);
    if (!(status.installed.length || status.modified.length || status.missing.length)) {
      console.log(`doct-agents is not installed in ${status.target}`);
      return 1;
    }
    console.log(`Target: ${status.target}`);
    console.log(`Installed: ${status.installed.length}`);
    console.log(`Modified: ${status.modified.join(", ") || "none"}`);
    console.log(`Missing: ${status.missing.join(", ") || "none"}`);
    return status.modified.length || status.missing.length ? 2 : 0;
  }

  if (options.command === "uninstall") {
    const result = uninstallAgents(target, { force: options.force });
    console.log(`Removed ${result.removed} managed agent files from ${result.target}`);
    if (result.preserved.length) {
      console.log(`Preserved modified files: ${result.preserved.join(", ")}`);
      return 2;
    }
    return 0;
  }

  const result = installAgents({ targetDir: target, force: options.force });
  console.log(`${options.command === "update" ? "Updated" : "Installed"} ${result.installed} agents in ${result.target}`);
  console.log("Reload VS Code, open Copilot Chat, then select orchestrator or cli-executor.");
  return 0;
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  try {
    process.exitCode = run();
  } catch (error) {
    console.error(`error: ${error.message}`);
    process.exitCode = 1;
  }
}
