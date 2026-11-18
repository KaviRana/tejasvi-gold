// After the build: keep only the photos of live designs in dist, so catalogue pages still under review are never published.
import fs from "node:fs";
const live = new Set(JSON.parse(fs.readFileSync("src/data/designs.json", "utf8")).map((d) => d.id));
let n = 0, bytes = 0;
for (const f of fs.readdirSync("dist/designs")) {
  const m = f.match(/^(TG-\d+)\.jpg$/);
  if (m && !live.has(m[1])) { bytes += fs.statSync(`dist/designs/${f}`).size; fs.rmSync(`dist/designs/${f}`); n++; }
}
console.log(`pruned ${n} unpublished photos (${(bytes / 1048576).toFixed(1)} MB) from dist`);
