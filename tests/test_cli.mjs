import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  InstallConflict,
  defaultTarget,
  getStatus,
  installAgents,
  uninstallAgents,
} from "../bin/doct-agents.js";

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "doct-agents-node-"));
  const sourceDir = join(root, "source");
  const targetDir = join(root, "target");
  mkdirSync(sourceDir);
  writeFileSync(join(sourceDir, "orchestrator.agent.md"), "orchestrator-v1\n", "utf8");
  writeFileSync(join(sourceDir, "cli-executor.agent.md"), "cli-v1\n", "utf8");
  return { root, sourceDir, targetDir };
}

test("defaultTarget resolves user and workspace scopes", () => {
  assert.equal(defaultTarget("user", "/repo", "/home/dev"), "/home/dev/.copilot/agents");
  assert.equal(defaultTarget("workspace", "/repo", "/home/dev"), "/repo/.github/agents");
});

test("install copies agents and writes manifest", () => {
  const { sourceDir, targetDir } = fixture();
  const result = installAgents({ sourceDir, targetDir });

  assert.equal(result.installed, 2);
  assert.equal(readFileSync(join(targetDir, "orchestrator.agent.md"), "utf8"), "orchestrator-v1\n");
  assert.equal(existsSync(join(targetDir, ".doct-agents-manifest.json")), true);
  assert.deepEqual(getStatus(targetDir).modified, []);
});

test("install protects unmanaged files", () => {
  const { sourceDir, targetDir } = fixture();
  mkdirSync(targetDir);
  writeFileSync(join(targetDir, "orchestrator.agent.md"), "custom\n", "utf8");

  assert.throws(
    () => installAgents({ sourceDir, targetDir }),
    (error) => error instanceof InstallConflict && error.message.includes("not managed"),
  );
});

test("update protects modified managed files unless forced", () => {
  const { sourceDir, targetDir } = fixture();
  installAgents({ sourceDir, targetDir });
  writeFileSync(join(targetDir, "orchestrator.agent.md"), "local-change\n", "utf8");
  writeFileSync(join(sourceDir, "orchestrator.agent.md"), "orchestrator-v2\n", "utf8");

  assert.throws(() => installAgents({ sourceDir, targetDir }), InstallConflict);
  installAgents({ sourceDir, targetDir, force: true });
  assert.equal(readFileSync(join(targetDir, "orchestrator.agent.md"), "utf8"), "orchestrator-v2\n");
});

test("status reports modified and missing files", () => {
  const { sourceDir, targetDir } = fixture();
  installAgents({ sourceDir, targetDir });
  writeFileSync(join(targetDir, "orchestrator.agent.md"), "changed\n", "utf8");
  const { unlinkSync } = await import("node:fs");
  unlinkSync(join(targetDir, "cli-executor.agent.md"));

  const status = getStatus(targetDir);
  assert.deepEqual(status.modified, ["orchestrator.agent.md"]);
  assert.deepEqual(status.missing, ["cli-executor.agent.md"]);
});

test("uninstall preserves modified files by default", () => {
  const { sourceDir, targetDir } = fixture();
  installAgents({ sourceDir, targetDir });
  writeFileSync(join(targetDir, "orchestrator.agent.md"), "local-change\n", "utf8");

  const result = uninstallAgents(targetDir);
  assert.deepEqual(result.preserved, ["orchestrator.agent.md"]);
  assert.equal(existsSync(join(targetDir, "orchestrator.agent.md")), true);
  assert.equal(existsSync(join(targetDir, "cli-executor.agent.md")), false);
});
