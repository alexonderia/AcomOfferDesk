import { cpSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
for (const directory of ['cmaps', 'standard_fonts', 'wasm']) {
  const destination = resolve(webRoot, 'public/pdfjs', directory);
  mkdirSync(destination, { recursive: true });
  cpSync(resolve(webRoot, 'node_modules/pdfjs-dist', directory), destination, { recursive: true });
}
cpSync(resolve(webRoot, 'node_modules/pdfjs-dist/LICENSE'), resolve(webRoot, 'public/pdfjs/LICENSE'));
