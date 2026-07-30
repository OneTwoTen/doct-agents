#!/usr/bin/env node

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, rmSync, unlinkSync, writeFileSync, copyFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BUNDLED_AGENTS = join(PACKAGE_ROOT, "agents");
const MANIFEST_NAME = ".doct-agents-manifest.json";
const PACKAGE_NAME = "doct-agents";

export class InstallConflict extends Error {}

export function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function defaultTarget(scope, workspace = process.cwd(), home = homedir()) {
  return scope === "workspace"
    ? resolve(workspace, ".github", "agents")
    : resolve(home, ".copilot", "agents");
}

export function loadManifest(targetDir) {
  const path = join(targetDir, MANIFEST_NAME);
  if (!existsSync(path)) {
    return { schema: 1, package: PACKAGE_NAME, files: {} };
  }
  try {
    const manifest = JSON.parse(readFileSync(path, "utf8"));
    if (!manifest.files || typeof manifest.files !== "object" || Array.isArray(manifest.files)) {
      throw new Error("files must be an object");
    }
    return manifest;
  } catch (error) {
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
  return files;
}

export function installAgents({ sourceDir = BUNDLED_AGENTS, targetDir, force = false }) {
  const target = resolve(targetDir);
  mkdirSync(target, { recursive: true });
  const files = findAgentFiles(sourceDir);
  const previous = loadManifest(target);
  const conflicts = [];

  for (const filename of files) {
    const destination = join(target, filename);
    if (!existsSync(destination)) continue;
    const expected = previous.files[filename];
    if (!expected) {
      conflicts.push(`${filename} already exists and is not managed by doct-agents`);
    } else if (sha256(destination) !== expected) {
      conflicts.push(`${filename} was modified after installation`);
    }
  }

  if (conflicts.length > 0 && !force) {
    throw new InstallConflict(
      `Installation stopped to protect existing files:\n- ${conflicts.join("\n- ")}\n` +
        "Re-run with --force only when replacing those files is intentional.",
    );
  }

  const installed = {};
  for (const filename of files) {
    const source = join(sourceDir, filename);
    const destination = join(target, filename);
    copyFileSync(source, destination);
    installed[filename] = sha256(destination);
  }

  writeFileSync(
    join(target, MANIFEST_NAME),
    `${JSON.stringify({ schema: 1, package: PACKAGE_NAME, files: installed }, null, 2)}\n`,
    "utf8",
  );
  return { installed: files.length, target };
}

export function getStatus(targetDir) {
  const target = resolve(targetDir);
  const manifest = loadManifest(target);
  const installed = [];
  const modified = [];
  const missing = [];

  for (const [filename, expected] of Object.entries(manifest.files).sort()) {
    const destination = join(target, filename);
    if (!existsSync(destination)) missing.push(filename);
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
  let removed = 0;

  for (const [filename, expected] of Object.entries(manifest.files).sort()) {
    const destination = join(target, filename);
    if (!existsSync(destination)) continue;
    if (!force && sha256(destination) !== expected) {
      preserved.push(filename);
      remaining[filename] = expected;
      continue;
    }
    unlinkSync(destination);
    removed += 1;
  }

  const manifestPath = join(target, MANIFEST_NAME);
  if (Object.keys(remaining).length > 0) {
    writeFileSync(
      manifestPath,
      `${JSON.stringify({ ...manifest, files: remaining }, null, 2)}\n`,
      "utf8",
    );
  } else if (existsSync(manifestPath)) {
    unlinkSync(manifestPath);
  }

  return { removed, preserved, target };
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
