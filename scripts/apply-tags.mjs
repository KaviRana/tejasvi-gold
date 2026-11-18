// Reads tools/data/tags_review.csv and writes src/data/tags.json with ONLY the rows marked "checked".
// Runs before every dev start and build. Same CSV in, same JSON out.
// A checked row with a value outside the fixed lists, or an unknown code, stops with a clear message.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const CSV = "tools/data/tags_review.csv";
const OUT = "src/data/tags.json";
const FIELDS = ["motif", "finish", "work", "stones", "occasion"];
const STATUSES = ["suggested", "checked", ""];

export function parseCsv(text) {
  text = text.replace(/^﻿/, "");
  const rows = []; let row = []; let cell = ""; let q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') q = false;
      else cell += ch;
    } else if (ch === '"') q = true;
    else if (ch === ",") { row.push(cell); cell = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some((c) => c.trim() !== "")) rows.push(row);
      row = [];
    } else cell += ch;
  }
  row.push(cell);
  if (row.some((c) => c.trim() !== "")) rows.push(row);
  return rows;
}

export function applyTags(csvText, attributes, codes) {
  const [head, ...body] = parseCsv(csvText);
  const col = Object.fromEntries(head.map((h, i) => [h.trim().toLowerCase(), i]));
  for (const f of ["code", "status", ...FIELDS]) if (!(f in col)) throw new Error(`${CSV}: missing column "${f}"`);
  const errors = []; const out = []; const seen = new Set(); const names = new Map();
  body.forEach((r, n) => {
    const line = n + 2;
    const get = (f) => (r[col[f]] ?? "").trim();
    const code = get("code").toUpperCase();
    const status = get("status").toLowerCase();
    if (!STATUSES.includes(status)) errors.push(`line ${line}: status "${get("status")}" must be suggested or checked`);
    if (status !== "checked") return;
    if (!codes.has(code)) { errors.push(`line ${line}: code ${code} is not in the catalogue`); return; }
    if (seen.has(code)) { errors.push(`line ${line}: ${code} appears twice`); return; }
    seen.add(code);
    const tag = { id: code };
    for (const f of FIELDS) {
      const v = get(f);
      const match = attributes[f].find((a) => a.toLowerCase() === v.toLowerCase());
      if (!match) errors.push(`line ${line}: ${code} ${f} "${v}" must be one of: ${attributes[f].join(", ")}`);
      tag[f] = match;
    }
    // Optional own name (e.g. "Star Lily Necklace"). Used instead of the template; must be unique.
    const name = "name" in col ? get("name").replace(/\s+/g, " ") : "";
    if (name) {
      if (!/^[A-Za-z0-9][A-Za-z0-9 '\-]{2,48}$/.test(name)) errors.push(`line ${line}: ${code} name "${name}" may use letters, numbers, spaces, ' and - only (3 to 49 characters)`);
      const key = name.toLowerCase();
      if (names.has(key)) errors.push(`line ${line}: ${code} name "${name}" is already used by ${names.get(key)}`);
      names.set(key, code); tag.name = name;
    }
    out.push(tag);
  });
  if (errors.length) throw new Error(`Fix these rows in ${CSV}:\n  ${errors.join("\n  ")}`);
  return out.sort((a, b) => a.id.localeCompare(b.id));
}

// fileURLToPath, because a folder name with a space (like "Tejasvi Gold") is written %20 in the URL form.
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const attributes = JSON.parse(readFileSync("src/data/attributes.json", "utf8"));
  const codes = new Set(JSON.parse(readFileSync("src/data/designs.json", "utf8")).map((d) => d.id));
  try {
    const tags = existsSync(CSV) ? applyTags(readFileSync(CSV, "utf8"), attributes, codes) : [];
    writeFileSync(OUT, JSON.stringify(tags, null, 2) + "\n");
    console.log(`tags: ${tags.length} checked of ${codes.size} designs`);
  } catch (e) {
    console.error(`\n${e.message}\n`);
    process.exit(1);
  }
}
