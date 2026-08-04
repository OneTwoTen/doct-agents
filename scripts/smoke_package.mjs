#!/usr/bin/env node

import assert from "node:assert/strict";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";
const npmOptions = { shell: isWindows };

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: repositoryRoot,
    encoding: "utf8",
    stdio: options.capture ? ["ignore", "pipe", "pipe"] : "inherit",
    shell: options.shell ?? false,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    const output = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${command} ${args.join(" ")} failed with exit ${result.status}\n${output}`);
  }
  return result;
}

const root = mkdtempSync(join(tmpdir(), "doct-agents-package-smoke-"));
const packDir = join(root, "pack");
const installDir = join(root, "install");
const targetDir = join(root, "agents");
const workspaceDir = join(root, "workspace");
mkdirSync(packDir, { recursive: true });
mkdirSync(workspaceDir, { recursive: true });

try {
  const packed = run(
    npmCommand,
    ["pack", "--json", "--pack-destination", packDir],
    { ...npmOptions, capture: true },
  );
  const packResult = JSON.parse(packed.stdout);
  assert.equal(Array.isArray(packResult), true, "npm pack --json must return an array");
  assert.equal(packResult.length, 1, "npm pack must produce exactly one tarball");
  const tarball = join(packDir, packResult[0].filename);
  assert.equal(existsSync(tarball), true, "package tarball must exist");

  run(npmCommand, [
    "install",
    "--prefix",
    installDir,
    "--ignore-scripts",
    "--no-audit",
    "--no-fund",
    "--no-package-lock",
    tarball,
  ], npmOptions);

  const binary = join(
    installDir,
    "node_modules",
    ".bin",
    isWindows ? "doct-agents.cmd" : "doct-agents",
  );
  assert.equal(existsSync(binary), true, "installed package must expose doct-agents binary");

  const binaryOptions = { shell: isWindows };
  run(binary, ["install", "--target", targetDir], binaryOptions);
  const manifestPath = join(targetDir, ".doct-agents-manifest.json");
  assert.equal(existsSync(manifestPath), true, "install must create a manifest");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  assert.equal(manifest.package, "doct-agents");
  assert.equal(manifest.repository, "OneTwoTen/doct-agents");

  run(binary, ["status", "--target", targetDir], binaryOptions);
  run(binary, ["uninstall", "--target", targetDir], binaryOptions);
  assert.equal(existsSync(manifestPath), false, "uninstall must remove the manifest");

  run(binary, [
    "install",
    "--platform",
    "opencode",
    "--scope",
    "workspace",
    "--workspace",
    workspaceDir,
  ], binaryOptions);
  const openCodeAgent = join(workspaceDir, ".opencode", "agents", "orchestrator.md");
  const openCodeManifest = join(workspaceDir, ".opencode", "agents", ".doct-agents-manifest.json");
  const openCodeConfig = join(workspaceDir, ".opencode", "opencode.json");
  assert.equal(existsSync(openCodeAgent), true, "OpenCode install must render orchestrator.md");
  assert.equal(existsSync(openCodeManifest), true, "OpenCode install must create a schema-2 manifest");
  assert.equal(existsSync(openCodeConfig), true, "OpenCode install must create opencode.json");
  const openCodeManifestData = JSON.parse(readFileSync(openCodeManifest, "utf8"));
  assert.equal(openCodeManifestData.schema, 2);
  assert.equal(openCodeManifestData.platform, "opencode");
  const openCodeConfigData = JSON.parse(readFileSync(openCodeConfig, "utf8"));
  assert.deepEqual(openCodeConfigData.mcp.doct_playwright, {
    type: "local",
    command: ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
    enabled: true,
  });

  run(binary, [
    "status",
    "--platform",
    "opencode",
    "--scope",
    "workspace",
    "--workspace",
    workspaceDir,
  ], binaryOptions);
  run(binary, [
    "uninstall",
    "--platform",
    "opencode",
    "--scope",
    "workspace",
    "--workspace",
    workspaceDir,
  ], binaryOptions);
  assert.equal(existsSync(openCodeAgent), false, "OpenCode uninstall must remove managed agents");
  const configAfterUninstall = JSON.parse(readFileSync(openCodeConfig, "utf8"));
  assert.equal(
    Boolean(configAfterUninstall.mcp?.doct_playwright),
    false,
    "OpenCode uninstall must remove only the managed Playwright MCP entry",
  );

  console.log("Packaged CLI smoke test passed.");
} finally {
  rmSync(root, { recursive: true, force: true });
}
