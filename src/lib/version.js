// Adds ?v=<short hash of the file> to an image address. Photos are cached by the browser for a week, so a photo that is
// replaced under the same name (a new cutout, say) would keep showing the old one. A changed file gets a new address.
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";

const seen = new Map();
export function v(path) {
  if (!seen.has(path)) {
    const file = `public${path}`;
    seen.set(path, existsSync(file) ? createHash("sha1").update(readFileSync(file)).digest("hex").slice(0, 8) : "");
  }
  const h = seen.get(path);
  return h ? `${path}?v=${h}` : path;
}
