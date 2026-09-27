import { readFile } from 'node:fs/promises';

const required = [
  'index.html',
  'src/core/boot/BootConfig.js',
  'src/core/boot/BootPipeline.js',
  'src/core/scene/SceneManager.js',
  'src/core/data/AssetManifest.js',
];

for (const file of required) {
  await readFile(new URL(`../${file}`, import.meta.url), 'utf8');
}

console.log(`Phase 1 structure check passed: ${required.length} files verified.`);
