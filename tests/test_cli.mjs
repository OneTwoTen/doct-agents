import assert from "node:assert/strict";
import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { isAbsolute, join, resolve } from "node:path";
import test from "node:test";

import {
  InstallConflict,
  defaultTarget,
  getStatus,
  installAgents,
  loadManifest,
  sha256,
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

function writeManifest(targetDir, manifest) {
  mkdirSync(targetDir, { recursive: true });
  writeFileSync(
    join(targetDir, ".doct-agents-manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    "utf8",
  );
}

test("defaultTarget resolves user and workspace scopes", () => {
  assert.equal(
    defaultTarget("user", "/repo", "/home/dev"),
    resolve("/home/dev", ".copilot", "agents"),
  );
  assert.equal(
    defaultTarget("workspace", "/repo", "/home/dev"),
    resolve("/repo", ".github", "agents"),
  );
});

test("install copies agents and writes a canonical manifest", () => {
  const { sourceDir, targetDir } = fixture();
  const result = installAgents({ sourceDir, targetDir });

  assert.equal(result.installed, 2);
  assert.equal(readFileSync(join(targetDir, "orchestrator.agent.md"), "utf8"), "orchestrator-v1\n");
  const manifest = loadManifest(targetDir);
  assert.equal(manifest.schema, 1);
  assert.equal(manifest.package, "doct-agents");
  assert.equal(manifest.repository, "OneTwoTen/doct-agents");
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

test("manifest rejects parent traversal before uninstall even with force", () => {
  const { root, targetDir } = fixture();
  const outside = join(root, "outside.agent.md");
  writeFileSync(outside, "keep\n", "utf8");
  writeManifest(targetDir, {
    schema: 1,
    package: "doct-agents",
    files: { "../outside.agent.md": sha256(outside) },
  });

  assert.throws(() => uninstallAgents(targetDir, { force: true }), InstallConflict);
  assert.equal(readFileSync(outside, "utf8"), "keep\n");
});

test("manifest rejects absolute managed paths", () => {
  const { root, targetDir } = fixture();
  const outside = join(root, "absolute.agent.md");
  assert.equal(isAbsolute(outside), true);
  writeFileSync(outside, "keep\n", "utf8");
  writeManifest(targetDir, {
    schema: 1,
    repository: "OneTwoTen/doct-agents",
    files: { [outside]: sha256(outside) },
  });

  assert.throws(() => getStatus(targetDir), InstallConflict);
});

test("manifest rejects unsupported schemas and invalid checksums", () => {
  const { targetDir } = fixture();
  writeManifest(targetDir, {
    schema: 2,
    package: "doct-agents",
    files: { "orchestrator.agent.md": "0".repeat(64) },
  });
  assert.throws(() => loadManifest(targetDir), InstallConflict);

  writeManifest(targetDir, {
    schema: 1,
    package: "doct-agents",
    files: { "orchestrator.agent.md": "not-a-sha256" },
  });
  assert.throws(() => loadManifest(targetDir), InstallConflict);
});

test("manifest accepts legacy package-only and repository-only identifiers", () => {
  const { root } = fixture();
  for (const [name, identity] of [
    ["package", { package: "doct-agents" }],
    ["repository", { repository: "OneTwoTen/doct-agents" }],
  ]) {
    const targetDir = join(root, `legacy-${name}`);
    mkdirSync(targetDir);
    const destination = join(targetDir, "orchestrator.agent.md");
    writeFileSync(destination, "installed\n", "utf8");
    writeManifest(targetDir, {
      schema: 1,
      ...identity,
      files: { "orchestrator.agent.md": sha256(destination) },
    });

    assert.deepEqual(getStatus(targetDir).installed, ["orchestrator.agent.md"]);
  }
});

test("update removes unchanged obsolete managed agents", () => {
  const { sourceDir, targetDir } = fixture();
  installAgents({ sourceDir, targetDir });
  unlinkSync(join(sourceDir, "cli-executor.agent.md"));

  installAgents({ sourceDir, targetDir });

  assert.equal(existsSync(join(targetDir, "cli-executor.agent.md")), false);
  assert.equal("cli-executor.agent.md" in loadManifest(targetDir).files, false);
});

test("update preserves modified obsolete agents and keeps them managed", () => {
  const { sourceDir, targetDir } = fixture();
  installAgents({ sourceDir, targetDir });
  writeFileSync(join(targetDir, "cli-executor.agent.md"), "local-cli\n", "utf8");
  unlinkSync(join(sourceDir, "cli-executor.agent.md"));

  installAgents({ sourceDir, targetDir });

  assert.equal(readFileSync(join(targetDir, "cli-executor.agent.md"), "utf8"), "local-cli\n");
  assert.deepEqual(getStatus(targetDir).modified, ["cli-executor.agent.md"]);
  assert.equal("cli-executor.agent.md" in loadManifest(targetDir).files, true);
});

test(
  "install rejects a symbolic-link destination even with force",
  { skip: process.platform === "win32" },
  () => {
    const { root, sourceDir, targetDir } = fixture();
    mkdirSync(targetDir);
    const outside = join(root, "outside.agent.md");
    writeFileSync(outside, "outside\n", "utf8");
    symlinkSync(outside, join(targetDir, "orchestrator.agent.md"));

    assert.throws(
      () => installAgents({ sourceDir, targetDir, force: true }),
      (error) => error instanceof InstallConflict && error.message.includes("symbolic link"),
    );
    assert.equal(readFileSync(outside, "utf8"), "outside\n");
  },
);

test(
  "status and uninstall reject a symbolic-link target directory",
  { skip: process.platform === "win32" },
  () => {
    const { root, sourceDir } = fixture();
    const realTarget = join(root, "real-target");
    const linkedTarget = join(root, "linked-target");
    installAgents({ sourceDir, targetDir: realTarget });
    symlinkSync(realTarget, linkedTarget, "dir");

    assert.throws(() => getStatus(linkedTarget), InstallConflict);
    assert.throws(() => uninstallAgents(linkedTarget, { force: true }), InstallConflict);
    assert.equal(existsSync(join(realTarget, "orchestrator.agent.md")), true);
  },
);

test(
  "install rejects a symbolic-link ancestor before creating the target",
  { skip: process.platform === "win32" },
  () => {
    const { root, sourceDir } = fixture();
    const outside = join(root, "outside");
    const workspace = join(root, "workspace");
    mkdirSync(outside);
    mkdirSync(workspace);
    symlinkSync(outside, join(workspace, ".github"), "dir");
    const targetDir = join(workspace, ".github", "agents");

    assert.throws(
      () => installAgents({ sourceDir, targetDir }),
      (error) => error instanceof InstallConflict && error.message.includes("symbolic link"),
    );
    assert.equal(existsSync(join(outside, "agents")), false);
  },
);

test(
  "update stages every source before mutating the target",
  { skip: process.platform === "win32" },
  () => {
    const { sourceDir, targetDir } = fixture();
    installAgents({ sourceDir, targetDir });
    const manifestPath = join(targetDir, ".doct-agents-manifest.json");
    const originalManifest = readFileSync(manifestPath, "utf8");
    writeFileSync(join(sourceDir, "cli-executor.agent.md"), "cli-v2\n", "utf8");
    const unreadable = join(sourceDir, "orchestrator.agent.md");
    chmodSync(unreadable, 0o000);

    try {
      assert.throws(() => installAgents({ sourceDir, targetDir }));
    } finally {
      chmodSync(unreadable, 0o600);
    }

    assert.equal(readFileSync(join(targetDir, "cli-executor.agent.md"), "utf8"), "cli-v1\n");
    assert.equal(
      readFileSync(join(targetDir, "orchestrator.agent.md"), "utf8"),
      "orchestrator-v1\n",
    );
    assert.equal(readFileSync(manifestPath, "utf8"), originalManifest);
  },
);
