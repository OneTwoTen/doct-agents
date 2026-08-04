import assert from "node:assert/strict";
import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

import {
  PLAYWRIGHT_MCP,
  detectOpenCode,
  defaultTarget,
  getStatus,
  installAgents,
  loadManifest,
  openCodeConfigPath,
  patchOpenCodeConfig,
  renderOpenCodeAgent,
  uninstallAgents,
} from "../bin/doct-agents.js";
import { run } from "../bin/platform-runner.js";

function sourceAgent({ name, description = name, tools = [], agents = [], userInvocable = false, body = "body\n" }) {
  return `---\nname: ${name}\ndescription: ${JSON.stringify(description)}\ntools: ${JSON.stringify(tools)}\nagents: ${JSON.stringify(agents)}\nuser-invocable: ${userInvocable}\n---\n\n${body}`;
}

function assertContains(text, ...parts) {
  for (const part of parts) assert.equal(text.includes(part), true, `missing ${JSON.stringify(part)} in:\n${text}`);
}

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "doct-agents-opencode-"));
  return {
    root,
    sourceDir: join(root, "source"),
    targetDir: join(root, ".opencode", "agents"),
  };
}

function withoutConsole(callback) {
  const previousLog = console.log;
  const previousError = console.error;
  console.log = () => {};
  console.error = () => {};
  try {
    return callback();
  } finally {
    console.log = previousLog;
    console.error = previousError;
  }
}

test("OpenCode target paths coexist with legacy Copilot defaults", () => {
  assert.equal(defaultTarget("user", "/repo", "/home/dev"), resolve("/home/dev", ".copilot", "agents"));
  assert.equal(defaultTarget("workspace", "/repo", "/home/dev"), resolve("/repo", ".github", "agents"));
  assert.equal(
    defaultTarget("user", "/repo", "/home/dev", "opencode"),
    resolve("/home/dev", ".config", "opencode", "agents"),
  );
  assert.equal(
    defaultTarget("workspace", "/repo", "/home/dev", "opencode"),
    resolve("/repo", ".opencode", "agents"),
  );
});

test("renderer maps orchestrator routing and Copilot tools to OpenCode permissions", () => {
  const rendered = renderOpenCodeAgent(
    sourceAgent({
      name: "orchestrator",
      description: "route work",
      tools: ["agent", "read", "search", "todo", "vscode/askQuestions"],
      agents: ["review-agent", "implementation-agent"],
      userInvocable: true,
    }),
    "orchestrator.agent.md",
  );

  assert.equal(rendered.filename, "orchestrator.md");
  assertContains(
    rendered.text,
    "description: \"route work\"",
    "mode: primary",
    "read: allow",
    "glob: allow",
    "grep: allow",
    "todowrite: allow",
    "question: allow",
    "edit: deny",
    "bash: deny",
    '"*": deny',
    '"review-agent": allow',
    '"implementation-agent": allow',
    '"doct_playwright_*": deny',
    "body\n",
  );
  for (const copilotKey of ["name:", "tools:", "agents:", "user-invocable:", "argument-hint:"]) {
    assert.equal(rendered.text.includes(copilotKey), false, `${copilotKey} leaked into OpenCode output`);
  }
});

test("renderer preserves least privilege for representative workers", () => {
  const implementation = renderOpenCodeAgent(
    sourceAgent({ name: "implementation-agent", tools: ["read", "search", "edit"] }),
    "implementation-agent.agent.md",
  ).text;
  assertContains(implementation, "mode: subagent", "hidden: true", "edit: allow", "bash: deny", "task: deny");

  const cli = renderOpenCodeAgent(
    sourceAgent({ name: "cli-executor", tools: ["execute", "read"], userInvocable: true }),
    "cli-executor.agent.md",
  ).text;
  assertContains(cli, "mode: all", "bash: allow", "edit: deny", "task: deny");

  const research = renderOpenCodeAgent(
    sourceAgent({ name: "research-agent", tools: ["web", "read", "search"] }),
    "research-agent.agent.md",
  ).text;
  assertContains(research, "webfetch: allow", "websearch: allow", "edit: deny");

  const browser = renderOpenCodeAgent(
    sourceAgent({ name: "browser-agent", tools: ["read", "search", "execute", "openBrowserPage"] }),
    "browser-agent.agent.md",
  ).text;
  assertContains(browser, '"doct_playwright_*": allow');
});

test("OpenCode managed files use schema 2 while schema 1 remains Copilot compatible", () => {
  const { sourceDir, targetDir } = fixture();
  mkdirSync(sourceDir, { recursive: true });
  writeFileSync(join(sourceDir, "orchestrator.md"), "rendered\n", "utf8");

  installAgents({
    sourceDir,
    targetDir,
    platform: "opencode",
    manifestMetadata: {
      config: {
        filename: "opencode.json",
        mcpEntrySha256: "0".repeat(64),
      },
    },
  });

  const manifest = loadManifest(targetDir, "opencode");
  assert.equal(manifest.schema, 2);
  assert.equal(manifest.platform, "opencode");
  assert.equal(manifest.config.filename, "opencode.json");
  assert.deepEqual(getStatus(targetDir, { platform: "opencode" }).modified, []);

  writeFileSync(join(targetDir, "orchestrator.md"), "changed\n", "utf8");
  assert.deepEqual(getStatus(targetDir, { platform: "opencode" }).modified, ["orchestrator.md"]);
  uninstallAgents(targetDir, { platform: "opencode", force: true });
});

test("OpenCode config path prefers existing jsonc and otherwise creates json beside agents", () => {
  const { root, targetDir } = fixture();
  mkdirSync(join(root, ".opencode"), { recursive: true });
  assert.equal(openCodeConfigPath(targetDir), join(root, ".opencode", "opencode.json"));
  writeFileSync(join(root, ".opencode", "opencode.jsonc"), "{}\n", "utf8");
  assert.equal(openCodeConfigPath(targetDir), join(root, ".opencode", "opencode.jsonc"));
});

test("Playwright MCP config is pinned, isolated, and preserves unrelated JSON config", () => {
  assert.deepEqual(PLAYWRIGHT_MCP, {
    type: "local",
    command: ["npx", "-y", "@playwright/mcp@0.0.78", "--isolated"],
    enabled: true,
  });

  const input = `${JSON.stringify({ model: "example/model", mcp: { other: { type: "local", command: ["other"] } } }, null, 2)}\n`;
  const patched = patchOpenCodeConfig(input);
  const parsed = JSON.parse(patched.text);
  assert.equal(parsed.model, "example/model");
  assert.deepEqual(parsed.mcp.other, { type: "local", command: ["other"] });
  assert.deepEqual(parsed.mcp.doct_playwright, PLAYWRIGHT_MCP);
  assert.match(patched.mcpEntrySha256, /^[a-f0-9]{64}$/);

  const removed = patchOpenCodeConfig(patched.text, {
    expectedHash: patched.mcpEntrySha256,
    remove: true,
  });
  const removedParsed = JSON.parse(removed.text);
  assert.equal("doct_playwright" in removedParsed.mcp, false);
  assert.deepEqual(removedParsed.mcp.other, { type: "local", command: ["other"] });
});

test("JSONC patch preserves comments, trailing commas, and unrelated MCP entries", () => {
  const input = `{
  // keep this comment
  "model": "example/model",
  "mcp": {
    "other": {
      "type": "local",
      "command": ["other"],
    },
  },
}\n`;
  const patched = patchOpenCodeConfig(input);
  assertContains(patched.text, "// keep this comment", '"model": "example/model"', '"other"', '"doct_playwright"');

  const removed = patchOpenCodeConfig(patched.text, {
    expectedHash: patched.mcpEntrySha256,
    remove: true,
  });
  assertContains(removed.text, "// keep this comment", '"model": "example/model"', '"other"');
  assert.equal(removed.text.includes('"doct_playwright"'), false);
});

test("modified managed Playwright MCP entry is protected unless force is explicit", () => {
  const installed = patchOpenCodeConfig("{}\n");
  const customized = installed.text.replace("--isolated", "--headless");
  assert.throws(
    () => patchOpenCodeConfig(customized, { expectedHash: installed.mcpEntrySha256 }),
    /modified/i,
  );
  const forced = patchOpenCodeConfig(customized, {
    expectedHash: installed.mcpEntrySha256,
    force: true,
  });
  assert.equal(forced.text.includes("--isolated"), true);
});

test("OpenCode auto-detection recognizes PATH commands and workspace config", () => {
  const root = mkdtempSync(join(tmpdir(), "doct-agents-detect-"));
  const bin = join(root, "bin");
  const workspace = join(root, "workspace");
  const home = join(root, "home");
  mkdirSync(bin, { recursive: true });
  mkdirSync(workspace, { recursive: true });
  mkdirSync(home, { recursive: true });

  const executable = join(bin, process.platform === "win32" ? "opencode.cmd" : "opencode");
  writeFileSync(executable, process.platform === "win32" ? "@echo off\r\n" : "#!/bin/sh\n", "utf8");
  if (process.platform !== "win32") chmodSync(executable, 0o755);
  assert.equal(detectOpenCode({ workspace, home, pathEnv: bin }), true);

  const emptyPath = join(root, "empty-bin");
  mkdirSync(emptyPath);
  assert.equal(detectOpenCode({ workspace, home, pathEnv: emptyPath }), false);
  mkdirSync(join(workspace, ".opencode"));
  assert.equal(detectOpenCode({ workspace, home, pathEnv: emptyPath }), true);
});

test("CLI explicitly installs, reports, and uninstalls OpenCode workspace support", () => {
  const workspace = mkdtempSync(join(tmpdir(), "doct-agents-cli-opencode-"));
  assert.equal(
    withoutConsole(() => run(["install", "--platform", "opencode", "--scope", "workspace", "--workspace", workspace])),
    0,
  );

  const agentPath = join(workspace, ".opencode", "agents", "orchestrator.md");
  const configPath = join(workspace, ".opencode", "opencode.json");
  assert.equal(existsSync(agentPath), true);
  assert.equal(existsSync(configPath), true);
  assert.deepEqual(JSON.parse(readFileSync(configPath, "utf8")).mcp.doct_playwright, PLAYWRIGHT_MCP);
  assert.equal(
    withoutConsole(() => run(["status", "--platform", "opencode", "--scope", "workspace", "--workspace", workspace])),
    0,
  );
  assert.equal(
    withoutConsole(() => run(["uninstall", "--platform", "opencode", "--scope", "workspace", "--workspace", workspace])),
    0,
  );
  assert.equal(existsSync(agentPath), false);
  const remainingConfig = JSON.parse(readFileSync(configPath, "utf8"));
  assert.equal(Boolean(remainingConfig.mcp?.doct_playwright), false);
});

test("CLI platform all installs both layouts and legacy uninstall remains Copilot-only", () => {
  const workspace = mkdtempSync(join(tmpdir(), "doct-agents-cli-all-"));
  assert.equal(
    withoutConsole(() => run(["install", "--platform", "all", "--scope", "workspace", "--workspace", workspace])),
    0,
  );
  const copilotAgent = join(workspace, ".github", "agents", "orchestrator.agent.md");
  const openCodeAgent = join(workspace, ".opencode", "agents", "orchestrator.md");
  assert.equal(existsSync(copilotAgent), true);
  assert.equal(existsSync(openCodeAgent), true);

  assert.equal(
    withoutConsole(() => run(["uninstall", "--scope", "workspace", "--workspace", workspace])),
    0,
  );
  assert.equal(existsSync(copilotAgent), false);
  assert.equal(existsSync(openCodeAgent), true);

  assert.equal(
    withoutConsole(() => run(["uninstall", "--platform", "opencode", "--scope", "workspace", "--workspace", workspace])),
    0,
  );
});

test("CLI auto-detect installs OpenCode in addition to Copilot", () => {
  const workspace = mkdtempSync(join(tmpdir(), "doct-agents-cli-auto-"));
  mkdirSync(join(workspace, ".opencode"), { recursive: true });
  assert.equal(
    withoutConsole(() => run(["install", "--scope", "workspace", "--workspace", workspace])),
    0,
  );
  assert.equal(existsSync(join(workspace, ".github", "agents", "orchestrator.agent.md")), true);
  assert.equal(existsSync(join(workspace, ".opencode", "agents", "orchestrator.md")), true);
});

test("CLI rejects invalid platforms and ambiguous all-platform custom targets", () => {
  assert.throws(() => run(["install", "--platform", "unknown"]), /platform/i);
  assert.throws(
    () => run(["install", "--platform", "all", "--target", join(tmpdir(), "agents")]),
    /target/i,
  );
});
