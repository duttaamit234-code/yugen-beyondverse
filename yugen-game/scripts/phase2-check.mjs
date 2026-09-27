import { readFile } from 'node:fs/promises';

const required = [
  'src/phase2/Phase2World.js',
  'src/phase2/Phase2Test.js',
];

for (const file of required) {
  const source = await readFile(new URL(`../${file}`, import.meta.url), 'utf8');
  if (!source.includes('export')) throw new Error(`${file}: no export found`);
  console.log(`PASS ${file}`);
}

const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
if (!pkg.dependencies.three) throw new Error('Three.js dependency missing');
console.log('PASS Three.js dependency registered');
console.log('Phase 2 structure check passed. Browser/WebGL runtime testing is still required.');
