// Prints, as JSON, what a share card needs for every live design: code, name, weight text and the business phone.
// The name comes from the same function the site uses, so the card and the page never disagree.
import { readFileSync } from "node:fs";
import { pieceName } from "../src/lib/piece.js";
import { grams } from "../src/lib/whatsapp.js";
const read = (p) => JSON.parse(readFileSync(new URL(`../src/data/${p}`, import.meta.url), "utf8"));
const cats = Object.fromEntries(read("categories.json").map((c) => [c.id, c]));
const tags = Object.fromEntries(read("tags.json").map((t) => [t.id, t]));
const biz = read("business.json");
const phone = biz.whatsapp;
const out = read("designs.json").map((d) => ({
  id: d.id, name: pieceName(cats[d.category], tags[d.id]), weight: grams(d.weight_min_g, d.weight_max_g),
  category: d.category, added: d.added, min_g: d.weight_min_g, max_g: d.weight_max_g,
}));
console.log(JSON.stringify({ phone, address: biz.address, categories: Object.values(cats).map((c) => ({ id: c.id, name: c.name, order: c.order })), designs: out }));
