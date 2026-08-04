#!/usr/bin/env node

import { run } from "./platform-runner.js";

try {
  process.exitCode = run();
} catch (error) {
  console.error(`error: ${error.message}`);
  process.exitCode = 1;
}
