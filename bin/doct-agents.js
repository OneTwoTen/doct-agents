#!/usr/bin/env node

import { createHash } from "node:crypto";
import {
  copyFileSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { basename, delimiter, dirname, isAbsolute, join, parse, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BUNDLED_AGENTS = join(PACKAGE_ROOT, "agents");
const MANIFEST_NAME = ".doct-agents-manifest.json";
const PACKAGE_NAME = "doct-agents";
const REPOSITORY = "OneTwoTen/doct-agents";
const SHA256_PATTERN = /^[a-f0-9]{64}$/i;
const FRONTMATTER_PATTERN = /\A/;

export const PLAYWRIGHT_MCP = Object.freeze({
  type: "local",
  command: ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
  enabled: true,
});

const SOURCE_TOOL_PERMISSIONS = Object.freeze({
  read: ["read"],
  search: ["glob", "grep"],
  edit: ["edit"],
  execute: ["bash"],
  agent: ["task"],
  todo: ["todowrite"],
  "vscode/askQuestions": ["question"],
  web: ["webfetch", "websearch"],
});

const SIMPLE_PERMISSIONS = [
  "read",
  "glob",
  "grep",
  "edit",
  "bash",
  "todowrite",
  "webfetch",
  "websearch",
  "question",
];

export class InstallConflict extends Error {}

function entryAt(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function sha256Text(text) {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

function stableValue(value) {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, stableValue(value[key])]),
    );
  }
  return value;
}

function hashJsonValue(value) {
  return sha256Text(JSON.stringify(stableValue(value)));
}

function validatePlatform(platform) {
  if (!['copilot', 'opencode'].includes(platform)) {
    throw new InstallConflict(`Unsupported platform: ${JSON.stringify(platform)}`);
  }
  return platform;
}

function validateConfigMetadata(config) {
  if (config === undefined) return undefined;
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new InstallConflict("OpenCode manifest config must be an object");
  }
  const { filename, mcpEntrySha256 } = config;
  if (
    typeof filename !== "string" ||
    !["opencode.json", "opencode.jsonc"].includes(filename) ||
    basename(filename) !== filename
  ) {
    throw new InstallConflict(`Unsafe OpenCode config filename: ${JSON.stringify(filename)}`);
  }
  if (typeof mcpEntrySha256 !== "string" || !SHA256_PATTERN.test(mcpEntrySha256)) {
    throw new InstallConflict("Invalid OpenCode MCP entry SHA-256");
  }
  return { filename, mcpEntrySha256: mcpEntrySha256.toLowerCase() };
}

function canonicalManifest(files, platform = "copilot", metadata = null) {
  validatePlatform(platform);
  if (platform === "copilot") {
    return {
      schema: 1,
      package: PACKAGE_NAME,
      repository: REPOSITORY,
      files,
    };
  }
  const manifest = {
    schema: 2,
    package: PACKAGE_NAME,
    repository: REPOSITORY,
    platform: "opencode",
    files,
  };
  const config = metadata?.config ? validateConfigMetadata(metadata.config) : undefined;
  if (config) manifest.config = config;
  return manifest;
}

function manifestText(files, platform = "copilot", metadata = null) {
  return `${JSON.stringify(canonicalManifest(files, platform, metadata), null, 2)}\n`;
}

export function validateManagedFilename(filename, platform = "copilot") {
  validatePlatform(platform);
  const extensionMatches = platform === "copilot"
    ? filename?.endsWith(".agent.md")
    : filename?.endsWith(".md") && !filename?.endsWith(".agent.md");
  if (
    typeof filename !== "string" ||
    !filename ||
    filename === "." ||
    filename === ".." ||
    isAbsolute(filename) ||
    basename(filename) !== filename ||
    /[\0/\\:]/.test(filename) ||
    !extensionMatches
  ) {
    throw new InstallConflict(`Unsafe managed agent filename: ${JSON.stringify(filename)}`);
  }
  return filename;
}

function managedDestination(target, filename, platform = "copilot") {
  validateManagedFilename(filename, platform);
  const destination = resolve(target, filename);
  if (dirname(destination) !== target) {
    throw new InstallConflict(`Managed path escapes target directory: ${filename}`);
  }
  return destination;
}

function assertRegularPath(path, label) {
  const entry = entryAt(path);
  if (!entry) return null;
  if (entry.isSymbolicLink()) {
    throw new InstallConflict(`${label} is a symbolic link`);
  }
  if (!entry.isFile()) {
    throw new InstallConflict(`${label} is not a regular file`);
  }
  return entry;
}

function assertRegularManagedFile(path, filename) {
  return assertRegularPath(path, `Managed agent ${filename}`);
}

function validatePathComponents(targetDir) {
  const target = resolve(targetDir);
  const root = parse(target).root;
  const parts = target.slice(root.length).split(sep).filter(Boolean);
  let current = root;

  for (const part of parts) {
    current = join(current, part);
    const entry = entryAt(current);
    if (!entry) break;
    if (entry.isSymbolicLink()) {
      throw new InstallConflict(`Target path component is a symbolic link: ${current}`);
    }
    if (current !== target && !entry.isDirectory()) {
      throw new InstallConflict(`Target path component is not a directory: ${current}`);
    }
  }
  return target;
}

function validateExistingTarget(targetDir) {
  const target = validatePathComponents(targetDir);
  const entry = entryAt(target);
  if (entry && !entry.isDirectory()) {
    throw new InstallConflict(`Target must be a directory: ${target}`);
  }
  return target;
}

function prepareTarget(targetDir) {
  const target = validateExistingTarget(targetDir);
  mkdirSync(target, { recursive: true });
  validatePathComponents(target);
  const entry = entryAt(target);
  if (!entry || !entry.isDirectory() || entry.isSymbolicLink()) {
    throw new InstallConflict(`Target must be a real directory: ${target}`);
  }
  return target;
}

function manifestPath(target) {
  return join(target, MANIFEST_NAME);
}

function writeManifest(target, files, platform = "copilot", metadata = null) {
  const path = manifestPath(target);
  assertRegularPath(path, `Installer manifest ${path}`);
  writeFileSync(path, manifestText(files, platform, metadata), "utf8");
}

export function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function defaultTarget(
  scope,
  workspace = process.cwd(),
  home = homedir(),
  platform = "copilot",
) {
  validatePlatform(platform);
  if (platform === "opencode") {
    return scope === "workspace"
      ? resolve(workspace, ".opencode", "agents")
      : resolve(home, ".config", "opencode", "agents");
  }
  return scope === "workspace"
    ? resolve(workspace, ".github", "agents")
    : resolve(home, ".copilot", "agents");
}

export function loadManifest(targetDir, platform = "copilot") {
  validatePlatform(platform);
  const target = validateExistingTarget(targetDir);
  const path = manifestPath(target);
  const entry = entryAt(path);
  if (!entry) return canonicalManifest({}, platform);
  assertRegularPath(path, `Installer manifest ${path}`);

  try {
    const manifest = JSON.parse(readFileSync(path, "utf8"));
    if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
      throw new Error("manifest root must be an object");
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

    let manifestPlatform;
    let metadata = null;
    if (manifest.schema === 1) {
      manifestPlatform = "copilot";
    } else if (manifest.schema === 2) {
      manifestPlatform = manifest.platform;
      if (manifestPlatform !== "opencode") {
        throw new Error(`unsupported platform ${JSON.stringify(manifestPlatform)}`);
      }
      if (manifest.config !== undefined) metadata = { config: validateConfigMetadata(manifest.config) };
    } else {
      throw new Error(`unsupported schema ${JSON.stringify(manifest.schema)}`);
    }
    if (manifestPlatform !== platform) {
      throw new Error(`manifest platform ${manifestPlatform} does not match requested ${platform}`);
    }
    if (!manifest.files || typeof manifest.files !== "object" || Array.isArray(manifest.files)) {
      throw new Error("files must be an object");
    }

    const files = {};
    for (const [filename, expected] of Object.entries(manifest.files)) {
      validateManagedFilename(filename, platform);
      if (typeof expected !== "string" || !SHA256_PATTERN.test(expected)) {
        throw new Error(`invalid SHA-256 for ${filename}`);
      }
      files[filename] = expected.toLowerCase();
    }
    return canonicalManifest(files, platform, metadata);
  } catch (error) {
    if (error instanceof InstallConflict) throw error;
    throw new InstallConflict(`Cannot read installer manifest ${path}: ${error.message}`);
  }
}

export function findAgentFiles(sourceDir = BUNDLED_AGENTS, platform = "copilot") {
  validatePlatform(platform);
  const files = readdirSync(sourceDir)
    .filter((name) => platform === "copilot"
      ? name.endsWith(".agent.md")
      : name.endsWith(".md") && !name.endsWith(".agent.md"))
    .sort();
  if (files.length === 0) {
    throw new Error(`No ${platform === "copilot" ? "*.agent.md" : "*.md"} files found in ${sourceDir}`);
  }
  for (const filename of files) {
    validateManagedFilename(filename, platform);
    const source = join(sourceDir, filename);
    const entry = entryAt(source);
    if (!entry || entry.isSymbolicLink() || !entry.isFile()) {
      throw new InstallConflict(`Bundled agent ${filename} must be a regular file`);
    }
  }
  return files;
}

function stageInstall(
  sourceDir,
  target,
  files,
  preservedObsolete,
  platform = "copilot",
  manifestMetadata = null,
) {
  const stage = mkdtempSync(join(dirname(target), `.${basename(target)}.doct-agents-stage-`));
  const installed = { ...preservedObsolete };
  try {
    for (const filename of files) {
      const staged = join(stage, filename);
      copyFileSync(join(sourceDir, filename), staged);
      installed[filename] = sha256(staged);
    }
    writeFileSync(
      join(stage, MANIFEST_NAME),
      manifestText(installed, platform, manifestMetadata),
      "utf8",
    );
    return { stage, installed };
  } catch (error) {
    rmSync(stage, { recursive: true, force: true });
    throw error;
  }
}

function commitStagedInstall(target, stage, files, obsoleteToRemove, platform = "copilot") {
  const backup = mkdtempSync(join(dirname(target), `.${basename(target)}.doct-agents-backup-`));
  const records = [];
  let preserveBackup = false;

  function replaceFromStage(staged, destination, backupName, label) {
    const existing = assertRegularPath(destination, label);
    const backupPath = join(backup, backupName);
    const record = { destination, backupPath, hadOriginal: Boolean(existing), installedNew: false };
    if (existing) renameSync(destination, backupPath);
    records.push(record);
    renameSync(staged, destination);
    record.installedNew = true;
  }

  try {
    validatePathComponents(target);
    for (const filename of files) {
      const destination = managedDestination(target, filename, platform);
      replaceFromStage(
        join(stage, filename),
        destination,
        filename,
        `Managed agent ${filename}`,
      );
    }

    for (const destination of obsoleteToRemove) {
      const filename = basename(destination);
      assertRegularManagedFile(destination, filename);
      const backupPath = join(backup, filename);
      renameSync(destination, backupPath);
      records.push({ destination, backupPath, hadOriginal: true, installedNew: false });
    }

    const destinationManifest = manifestPath(target);
    replaceFromStage(
      join(stage, MANIFEST_NAME),
      destinationManifest,
      MANIFEST_NAME,
      `Installer manifest ${destinationManifest}`,
    );
  } catch (error) {
    const rollbackErrors = [];
    for (const record of [...records].reverse()) {
      try {
        if (record.installedNew && entryAt(record.destination)) unlinkSync(record.destination);
        if (record.hadOriginal && entryAt(record.backupPath)) {
          renameSync(record.backupPath, record.destination);
        }
      } catch (rollbackError) {
        rollbackErrors.push(rollbackError.message);
      }
    }
    if (rollbackErrors.length) {
      preserveBackup = true;
      throw new InstallConflict(
        `${error.message}; rollback also failed: ${rollbackErrors.join("; ")}; ` +
          `backup preserved at ${backup}`,
      );
    }
    throw error;
  } finally {
    rmSync(stage, { recursive: true, force: true });
    if (!preserveBackup) rmSync(backup, { recursive: true, force: true });
  }
}

export function installAgents({
  sourceDir = BUNDLED_AGENTS,
  targetDir,
  force = false,
  platform = "copilot",
  manifestMetadata = null,
}) {
  validatePlatform(platform);
  const target = prepareTarget(targetDir);
  const files = findAgentFiles(sourceDir, platform);
  const currentNames = new Set(files);
  const previous = loadManifest(target, platform);
  const conflicts = [];
  const obsoleteToRemove = [];
  const preservedObsolete = {};

  for (const filename of files) {
    const destination = managedDestination(target, filename, platform);
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
    const destination = managedDestination(target, filename, platform);
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

  const metadata = platform === "opencode"
    ? manifestMetadata ?? (previous.config ? { config: previous.config } : null)
    : null;
  const { stage } = stageInstall(
    sourceDir,
    target,
    files,
    preservedObsolete,
    platform,
    metadata,
  );
  commitStagedInstall(target, stage, files, obsoleteToRemove, platform);
  return { installed: files.length, target };
}

export function getStatus(targetDir, { platform = "copilot" } = {}) {
  const target = validateExistingTarget(targetDir);
  const manifest = loadManifest(target, platform);
  const installed = [];
  const modified = [];
  const missing = [];

  for (const [filename, expected] of Object.entries(manifest.files).sort()) {
    const destination = managedDestination(target, filename, platform);
    if (!assertRegularManagedFile(destination, filename)) missing.push(filename);
    else if (sha256(destination) !== expected) modified.push(filename);
    else installed.push(filename);
  }
  return { installed, modified, missing, target, manifest };
}

export function uninstallAgents(targetDir, { force = false, platform = "copilot" } = {}) {
  const target = validateExistingTarget(targetDir);
  const manifest = loadManifest(target, platform);
  const preserved = [];
  const remaining = {};
  const removePaths = [];

  for (const [filename, expected] of Object.entries(manifest.files).sort()) {
    const destination = managedDestination(target, filename, platform);
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
    const metadata = platform === "opencode" && manifest.config
      ? { config: manifest.config }
      : null;
    writeManifest(target, remaining, platform, metadata);
  } else {
    const entry = entryAt(path);
    if (entry?.isSymbolicLink()) {
      throw new InstallConflict(`Installer manifest is a symbolic link: ${path}`);
    }
    if (entry) unlinkSync(path);
  }

  return { removed: removePaths.length, preserved, target, manifest };
}

function parseSourceScalar(value) {
  const trimmed = value.trim();
  if (trimmed === "true") return true;
  if (trimmed === "false") return false;
  if (trimmed.startsWith("[") || trimmed.startsWith('"')) {
    try {
      return JSON.parse(trimmed);
    } catch {
      // Fall through to the raw scalar for source frontmatter that does not need conversion.
    }
  }
  if (
    trimmed.length >= 2 &&
    ((trimmed.startsWith("'") && trimmed.endsWith("'")) ||
      (trimmed.startsWith('"') && trimmed.endsWith('"')))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseSourceFrontmatter(sourceText) {
  if (!sourceText.startsWith("---\n")) {
    throw new InstallConflict("Agent source is missing YAML frontmatter");
  }
  const closing = sourceText.indexOf("\n---", 4);
  if (closing < 0) throw new InstallConflict("Agent source has unterminated YAML frontmatter");
  const block = sourceText.slice(4, closing);
  const bodyStart = closing + 4;
  const body = sourceText.slice(bodyStart).replace(/^\r?\n/, "");
  const data = {};
  for (const [index, rawLine] of block.split(/\r?\n/).entries()) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const colon = line.indexOf(":");
    if (colon < 1) {
      throw new InstallConflict(`Invalid agent frontmatter line ${index + 2}`);
    }
    const key = line.slice(0, colon).trim();
    const value = line.slice(colon + 1);
    if (Object.hasOwn(data, key)) {
      throw new InstallConflict(`Duplicate agent frontmatter field: ${key}`);
    }
    data[key] = parseSourceScalar(value);
  }
  return { data, body };
}

function yamlPermissionLine(key, action, indent = "  ") {
  const renderedKey = key.includes("*") ? JSON.stringify(key) : key;
  return `${indent}${renderedKey}: ${action}`;
}

export function renderOpenCodeAgent(sourceText, sourceFilename) {
  validateManagedFilename(sourceFilename, "copilot");
  const { data, body } = parseSourceFrontmatter(sourceText);
  if (typeof data.name !== "string" || !data.name) {
    throw new InstallConflict(`${sourceFilename} is missing a valid name`);
  }
  if (typeof data.description !== "string" || !data.description) {
    throw new InstallConflict(`${sourceFilename} is missing a valid description`);
  }
  if (!Array.isArray(data.tools) || !data.tools.every((tool) => typeof tool === "string")) {
    throw new InstallConflict(`${sourceFilename} has invalid tools`);
  }
  if (!Array.isArray(data.agents) || !data.agents.every((agent) => typeof agent === "string")) {
    throw new InstallConflict(`${sourceFilename} has invalid agents`);
  }
  if (typeof data["user-invocable"] !== "boolean") {
    throw new InstallConflict(`${sourceFilename} has invalid user-invocable`);
  }

  const granted = new Set();
  for (const tool of data.tools) {
    for (const permission of SOURCE_TOOL_PERMISSIONS[tool] ?? []) granted.add(permission);
  }

  const isOrchestrator = data.name === "orchestrator";
  const mode = isOrchestrator
    ? "primary"
    : data["user-invocable"]
      ? "all"
      : "subagent";
  const lines = [
    "---",
    `description: ${JSON.stringify(data.description)}`,
    `mode: ${mode}`,
  ];
  if (mode === "subagent") lines.push("hidden: true");
  lines.push("permission:");
  for (const permission of SIMPLE_PERMISSIONS) {
    lines.push(yamlPermissionLine(permission, granted.has(permission) ? "allow" : "deny"));
  }
  if (isOrchestrator) {
    lines.push("  task:");
    lines.push('    "*": deny');
    for (const agent of data.agents) lines.push(`    ${JSON.stringify(agent)}: allow`);
  } else {
    lines.push("  task: deny");
  }
  lines.push(
    yamlPermissionLine(
      "doct_playwright_*",
      data.name === "browser-agent" ? "allow" : "deny",
    ),
    "---",
    "",
    body,
  );
  const filename = `${data.name}.md`;
  validateManagedFilename(filename, "opencode");
  return { filename, text: lines.join("\n") };
}

export function renderOpenCodeAgents(sourceDir = BUNDLED_AGENTS, outputDir) {
  const output = prepareTarget(outputDir);
  const rendered = [];
  for (const filename of findAgentFiles(sourceDir, "copilot")) {
    const result = renderOpenCodeAgent(readFileSync(join(sourceDir, filename), "utf8"), filename);
    writeFileSync(join(output, result.filename), result.text, "utf8");
    rendered.push(result.filename);
  }
  return rendered.sort();
}

function stripJsonc(text) {
  let output = "";
  let i = 0;
  let inString = false;
  let escaped = false;
  while (i < text.length) {
    const char = text[i];
    const next = text[i + 1];
    if (inString) {
      output += char;
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      i += 1;
      continue;
    }
    if (char === '"') {
      inString = true;
      output += char;
      i += 1;
      continue;
    }
    if (char === "/" && next === "/") {
      output += "  ";
      i += 2;
      while (i < text.length && text[i] !== "\n") {
        output += " ";
        i += 1;
      }
      continue;
    }
    if (char === "/" && next === "*") {
      output += "  ";
      i += 2;
      while (i < text.length) {
        if (text[i] === "*" && text[i + 1] === "/") {
          output += "  ";
          i += 2;
          break;
        }
        output += text[i] === "\n" ? "\n" : " ";
        i += 1;
      }
      continue;
    }
    output += char;
    i += 1;
  }
  return output.replace(/,\s*([}\]])/g, "$1");
}

function parseJsonOrJsonc(text) {
  try {
    const value = JSON.parse(text);
    return { value, strict: true };
  } catch {
    try {
      return { value: JSON.parse(stripJsonc(text)), strict: false };
    } catch (error) {
      throw new InstallConflict(`Cannot parse OpenCode config: ${error.message}`);
    }
  }
}

function skipTrivia(text, start) {
  let i = start;
  while (i < text.length) {
    if (/\s/.test(text[i])) {
      i += 1;
      continue;
    }
    if (text[i] === "/" && text[i + 1] === "/") {
      i += 2;
      while (i < text.length && text[i] !== "\n") i += 1;
      continue;
    }
    if (text[i] === "/" && text[i + 1] === "*") {
      i += 2;
      while (i < text.length && !(text[i] === "*" && text[i + 1] === "/")) i += 1;
      if (i >= text.length) throw new InstallConflict("Unterminated block comment in OpenCode config");
      i += 2;
      continue;
    }
    break;
  }
  return i;
}

function stringEnd(text, start) {
  if (text[start] !== '"') throw new InstallConflict("Expected JSON string");
  let escaped = false;
  for (let i = start + 1; i < text.length; i += 1) {
    const char = text[i];
    if (escaped) escaped = false;
    else if (char === "\\") escaped = true;
    else if (char === '"') return i + 1;
  }
  throw new InstallConflict("Unterminated string in OpenCode config");
}

function compositeEnd(text, start) {
  const opener = text[start];
  const closer = opener === "{" ? "}" : opener === "[" ? "]" : null;
  if (!closer) throw new InstallConflict("Expected JSON object or array");
  const stack = [closer];
  let i = start + 1;
  while (i < text.length) {
    i = skipTrivia(text, i);
    const char = text[i];
    if (char === '"') {
      i = stringEnd(text, i);
      continue;
    }
    if (char === "{" || char === "[") {
      stack.push(char === "{" ? "}" : "]");
      i += 1;
      continue;
    }
    if (char === stack[stack.length - 1]) {
      stack.pop();
      i += 1;
      if (stack.length === 0) return i;
      continue;
    }
    i += 1;
  }
  throw new InstallConflict("Unterminated composite value in OpenCode config");
}

function valueEnd(text, start) {
  const i = skipTrivia(text, start);
  if (text[i] === '"') return stringEnd(text, i);
  if (text[i] === "{" || text[i] === "[") return compositeEnd(text, i);
  let cursor = i;
  while (cursor < text.length && ![",", "}", "]"].includes(text[cursor])) cursor += 1;
  while (cursor > i && /\s/.test(text[cursor - 1])) cursor -= 1;
  return cursor;
}

function objectClose(text, start) {
  return compositeEnd(text, start) - 1;
}

function findObjectProperty(text, objectStart, targetKey) {
  if (text[objectStart] !== "{") throw new InstallConflict("Expected object while patching OpenCode config");
  const close = objectClose(text, objectStart);
  let cursor = objectStart + 1;
  while (cursor < close) {
    cursor = skipTrivia(text, cursor);
    if (cursor >= close) break;
    if (text[cursor] === ",") {
      cursor += 1;
      continue;
    }
    if (text[cursor] !== '"') throw new InstallConflict("OpenCode config object keys must be quoted");
    const keyStart = cursor;
    const keyEnd = stringEnd(text, cursor);
    let key;
    try {
      key = JSON.parse(text.slice(keyStart, keyEnd));
    } catch (error) {
      throw new InstallConflict(`Invalid OpenCode config key: ${error.message}`);
    }
    cursor = skipTrivia(text, keyEnd);
    if (text[cursor] !== ":") throw new InstallConflict("Expected ':' after OpenCode config key");
    const colon = cursor;
    const start = skipTrivia(text, cursor + 1);
    const end = valueEnd(text, start);
    cursor = skipTrivia(text, end);
    const comma = text[cursor] === "," ? cursor : null;
    if (key === targetKey) {
      return { keyStart, keyEnd, colon, valueStart: start, valueEnd: end, comma, objectClose: close };
    }
    cursor = comma === null ? cursor : comma + 1;
  }
  return null;
}

function lineIndent(text, position) {
  const lineStart = text.lastIndexOf("\n", position - 1) + 1;
  const prefix = text.slice(lineStart, position);
  return /^\s*$/.test(prefix) ? prefix : "";
}

function formatJsonValue(value, propertyIndent) {
  const json = JSON.stringify(value, null, 2);
  return json.replace(/\n/g, `\n${propertyIndent}`);
}

function insertJsoncProperty(text, objectStart, key, value) {
  const close = objectClose(text, objectStart);
  const closeLineStart = text.lastIndexOf("\n", close - 1) + 1;
  const closePrefix = text.slice(closeLineStart, close);
  const multilineClose = /^\s*$/.test(closePrefix);
  const closeIndent = multilineClose ? closePrefix : lineIndent(text, objectStart);
  const propertyIndent = `${closeIndent}  `;
  const entry = `${propertyIndent}${JSON.stringify(key)}: ${formatJsonValue(value, propertyIndent)},`;
  const semanticObject = JSON.parse(stripJsonc(text.slice(objectStart, close + 1)));
  const insertAt = multilineClose ? closeLineStart : close;
  if (Object.keys(semanticObject).length === 0) {
    const insertion = multilineClose
      ? `${entry}\n`
      : `\n${entry}\n${closeIndent}`;
    return text.slice(0, insertAt) + insertion + text.slice(insertAt);
  }
  const strippedPrefix = stripJsonc(text.slice(objectStart, insertAt)).trimEnd();
  const hasTrailingComma = strippedPrefix.endsWith(",");
  const insertion = multilineClose
    ? `${hasTrailingComma ? "" : ","}\n${entry}\n`
    : `${hasTrailingComma ? "" : ","}\n${entry}\n${closeIndent}`;
  return text.slice(0, insertAt) + insertion + text.slice(insertAt);
}

function replaceJsoncPropertyValue(text, property, value) {
  const indent = lineIndent(text, property.keyStart);
  return (
    text.slice(0, property.valueStart) +
    formatJsonValue(value, indent) +
    text.slice(property.valueEnd)
  );
}

function removeJsoncProperty(text, property, objectStart) {
  const lineStart = text.lastIndexOf("\n", property.keyStart - 1) + 1;
  const beforeKey = text.slice(lineStart, property.keyStart);
  if (property.comma !== null && /^\s*$/.test(beforeKey)) {
    let end = property.comma + 1;
    while (end < text.length && (text[end] === " " || text[end] === "\t")) end += 1;
    if (text[end] === "\r") end += 1;
    if (text[end] === "\n") end += 1;
    return text.slice(0, lineStart) + text.slice(end);
  }

  let start = property.keyStart;
  if (property.comma === null) {
    let cursor = property.keyStart - 1;
    while (cursor > objectStart && /\s/.test(text[cursor])) cursor -= 1;
    if (text[cursor] === ",") start = cursor;
  }
  const end = property.comma === null ? property.valueEnd : property.comma + 1;
  return text.slice(0, start) + text.slice(end);
}

export function patchOpenCodeConfig(
  text,
  { expectedHash = null, force = false, remove = false } = {},
) {
  if (typeof text !== "string") throw new InstallConflict("OpenCode config text must be a string");
  const parsed = parseJsonOrJsonc(text || "{}\n");
  const root = parsed.value;
  if (!root || typeof root !== "object" || Array.isArray(root)) {
    throw new InstallConflict("OpenCode config root must be an object");
  }
  if (root.mcp !== undefined && (!root.mcp || typeof root.mcp !== "object" || Array.isArray(root.mcp))) {
    throw new InstallConflict("OpenCode config mcp must be an object");
  }
  const current = root.mcp?.doct_playwright;
  const currentHash = current === undefined ? null : hashJsonValue(current);
  if (current !== undefined && expectedHash && currentHash !== expectedHash.toLowerCase() && !force) {
    throw new InstallConflict("Managed OpenCode doct_playwright entry was modified after installation");
  }
  if (current !== undefined && !expectedHash && !force && currentHash !== hashJsonValue(PLAYWRIGHT_MCP)) {
    throw new InstallConflict("OpenCode doct_playwright entry already exists and is not managed by doct-agents");
  }

  const desiredHash = hashJsonValue(PLAYWRIGHT_MCP);
  if (parsed.strict) {
    const next = structuredClone(root);
    if (!next.mcp && !remove) next.mcp = {};
    if (remove) {
      if (next.mcp) delete next.mcp.doct_playwright;
    } else {
      next.mcp.doct_playwright = PLAYWRIGHT_MCP;
    }
    return {
      text: `${JSON.stringify(next, null, 2)}\n`,
      mcpEntrySha256: desiredHash,
      changed: currentHash !== (remove ? null : desiredHash),
    };
  }

  const rootStart = skipTrivia(text, 0);
  if (text[rootStart] !== "{") throw new InstallConflict("OpenCode config root must be an object");
  const mcpProperty = findObjectProperty(text, rootStart, "mcp");
  let nextText = text;
  if (!mcpProperty) {
    if (!remove) {
      nextText = insertJsoncProperty(text, rootStart, "mcp", { doct_playwright: PLAYWRIGHT_MCP });
    }
  } else {
    if (text[mcpProperty.valueStart] !== "{") {
      throw new InstallConflict("OpenCode config mcp must be an object");
    }
    const doctProperty = findObjectProperty(text, mcpProperty.valueStart, "doct_playwright");
    if (remove) {
      if (doctProperty) nextText = removeJsoncProperty(text, doctProperty, mcpProperty.valueStart);
    } else if (doctProperty) {
      nextText = replaceJsoncPropertyValue(text, doctProperty, PLAYWRIGHT_MCP);
    } else {
      nextText = insertJsoncProperty(text, mcpProperty.valueStart, "doct_playwright", PLAYWRIGHT_MCP);
    }
  }
  return {
    text: nextText,
    mcpEntrySha256: desiredHash,
    changed: nextText !== text,
  };
}

export function openCodeConfigPath(targetDir) {
  const configDir = dirname(resolve(targetDir));
  const jsonc = join(configDir, "opencode.jsonc");
  const json = join(configDir, "opencode.json");
  if (entryAt(jsonc)) return jsonc;
  if (entryAt(json)) return json;
  return json;
}

export function detectOpenCode({
  workspace = process.cwd(),
  home = homedir(),
  pathEnv = process.env.PATH ?? "",
} = {}) {
  const workspaceConfig = entryAt(resolve(workspace, ".opencode"));
  if (workspaceConfig?.isDirectory() && !workspaceConfig.isSymbolicLink()) return true;
  const userConfig = entryAt(resolve(home, ".config", "opencode"));
  if (userConfig?.isDirectory() && !userConfig.isSymbolicLink()) return true;

  const names = process.platform === "win32"
    ? ["opencode.exe", "opencode.cmd", "opencode.bat", "opencode2.exe", "opencode2.cmd", "opencode2.bat"]
    : ["opencode", "opencode2"];
  for (const directory of pathEnv.split(delimiter).filter(Boolean)) {
    for (const name of names) {
      const entry = entryAt(resolve(directory, name));
      if (entry?.isFile() && !entry.isSymbolicLink()) return true;
    }
  }
  return false;
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
