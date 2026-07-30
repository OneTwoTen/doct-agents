#!/usr/bin/env node

import { run } from "./doct-agents.js";

try {
  process.exitCode = run();
} catch (error) {
  console.error(`error: ${error.message}`);
  process.exitCode = 1;
}
