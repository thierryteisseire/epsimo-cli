#!/usr/bin/env node
const { spawn } = require("child_process");
const path = require("path");
const epsimoDir = path.join(__dirname, "..");
const args = process.argv.slice(2);
const child = spawn("python3", ["-m", "epsimo", ...args], {
  stdio: "inherit",
  env: { ...process.env, PYTHONPATH: epsimoDir },
});
child.on("close", (code) => process.exit(code));
child.on("error", (err) => {
  if (err.code === "ENOENT") {
    console.error("Error: python3 is required but not found. Install Python 3.8+ first.");
    process.exit(1);
  }
  throw err;
});
