#!/usr/bin/env node
/**
 * Development server runner for og-media frontend
 * This script runs the Vite dev server as a Windows service
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('Starting Vite development server...');
console.log('Working directory:', __dirname);

// Run vite dev
const vite = spawn('node', ['node_modules/vite/bin/vite.js', 'dev'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
});

vite.on('error', (error) => {
  console.error('Failed to start Vite:', error);
  process.exit(1);
});

vite.on('close', (code) => {
  console.log(`Vite process exited with code ${code}`);
  process.exit(code);
});

// Handle termination signals
process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down...');
  vite.kill('SIGTERM');
});

process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down...');
  vite.kill('SIGINT');
});
