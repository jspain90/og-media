#!/usr/bin/env node
/**
 * Preview server runner for og-media frontend
 * This script runs the Vite preview server (production build) as a Windows service
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('Starting Vite preview server (production build)...');
console.log('Working directory:', __dirname);

// Run vite preview (serves production build)
const vite = spawn('node', ['node_modules/vite/bin/vite.js', 'preview'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
});

vite.on('error', (error) => {
  console.error('Failed to start Vite preview:', error);
  process.exit(1);
});

vite.on('close', (code) => {
  console.log(`Vite preview process exited with code ${code}`);
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
