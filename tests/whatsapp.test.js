import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { UPDATES_MESSAGE, pieceMessage, enquiryMessage, waLink, grams, newest } from "../src/lib/whatsapp.js";
import { pieceName, pieceDescription, weightBand } from "../src/lib/piece.js";
import { applyTags, parseCsv } from "../scripts/apply-tags.mjs";

const ring = { id: "TG-1006", category: "ladies-ring", purity: "22K", weight_min_g: 3.18, weight_max_g: 3.18, status: "made-to-order" };
const cat = { one: "Ring", single: "Ladies Ring", noun: "ladies' ring" };
const tag = { id: "TG-1006", motif: "Wave", finish: "High polish", work: "Cast", stones: "None", occasion: "Daily wear" };
const attributes = JSON.parse(readFileSync("src/data/attributes.json", "utf8"));

test("piece message is the approved Hindi text", () => {
  assert.equal(
    pieceMessage("Wave Cast Ring", "TG-1006", "3.18 g, 22K", "https://example.com/design/TG-1006/"),
    "Namaste,\nMujhe ye design ke baare mein jaankari chahiye:\nWave Cast Ring – TG-1006 (3.18 g, 22K)\nhttps://example.com/design/TG-1006/\n\nAaj ka bhav aur delivery bataiye."
  );
});

test("name and description follow the templates", () => {
  assert.equal(pieceName(cat, tag), "Wave Cast Ring");
  assert.equal(pieceName(cat, { ...tag, work: "Cut work" }), "Wave Cut Work Ring");
  assert.equal(pieceName(cat, undefined), "Ladies Ring");
  assert.equal(pieceDescription(ring, cat, tag), "A 22K gold ladies' ring with a wave motif in a high-polish cast finish, weighing 3.18 g. BIS hallmarked with HUID. Made to order.");
  assert.equal(pieceDescription(ring, cat, { ...tag, motif: "Plain", stones: "CZ" }), "A 22K gold ladies' ring in a plain high-polish cast finish, weighing 3.18 g. Set with CZ stones. BIS hallmarked with HUID. Made to order.");
  assert.equal(pieceDescription(ring, cat, undefined), "A 22K gold ladies' ring, weighing 3.18 g. BIS hallmarked with HUID. Made to order.");
});

test("weight bands", () => {
  assert.equal(weightBand(2.9, 2.9), "Under 3 g");
  assert.equal(weightBand(3, 3), "3–5 g");
  assert.equal(weightBand(5, 5), "3–5 g");
  assert.equal(weightBand(5.01, 5.01), "Over 5 g");
});

test("only checked rows feed the site, values are validated", () => {
  const codes = new Set(["TG-1001", "TG-1002"]);
  const csv = "﻿code,motif,finish,work,stones,occasion,status\r\nTG-1002,leaf,Matte,Cast,None,Festive,checked\r\nTG-1001,Leaf,Matte,Cast,None,Festive,suggested\r\n";
  assert.deepEqual(applyTags(csv, attributes, codes), [{ id: "TG-1002", motif: "Leaf", finish: "Matte", work: "Cast", stones: "None", occasion: "Festive" }]);
  assert.throws(() => applyTags("code,motif,finish,work,stones,occasion,status\nTG-1001,Star,Matte,Cast,None,Festive,checked\n", attributes, codes), /motif "Star"/);
  // An own name is kept, and two pieces may not share one.
  const named = "code,name,motif,finish,work,stones,occasion,status\nTG-1001,Star Lily Necklace,Leaf,Matte,Cast,None,Festive,checked\n";
  assert.equal(applyTags(named, attributes, codes)[0].name, "Star Lily Necklace");
  assert.throws(() => applyTags(named + "TG-1002,star lily necklace,Leaf,Matte,Cast,None,Festive,checked\n", attributes, codes), /already used by TG-1001/);
  assert.throws(() => applyTags("code,motif,finish,work,stones,occasion,status\nTG-9999,Leaf,Matte,Cast,None,Festive,checked\n", attributes, codes), /not in the catalogue/);
  assert.deepEqual(parseCsv('a,"b, c"\n'), [["a", "b, c"]]);
});

test("the review sheet only uses allowed values", () => {
  const [head, ...rows] = parseCsv(readFileSync("tools/data/tags_review.csv", "utf8"));
  for (const f of ["motif", "finish", "work", "stones", "occasion"]) {
    const i = head.indexOf(f);
    for (const r of rows) assert.ok(attributes[f].includes(r[i]), `${r[0]} ${f} ${r[i]}`);
  }
});

test("enquiry message skips empty fields", () => {
  assert.equal(enquiryMessage({ name: "Ravi", shop: "", town: "Niphad", quantity: "25" }), "Namaste Tejasvi Gold! New enquiry:\nName: Ravi\nTown: Niphad\nQuantity: 25");
});

test("waLink rejects placeholder and encodes", () => {
  assert.throws(() => waLink("91XXXXXXXXXX", "x"));
  assert.equal(waLink("919876543210", "a b"), "https://wa.me/919876543210?text=a%20b");
});

test("grams formatting", () => {
  assert.equal(grams(2.4, 3.0), "2.4–3 g");
  assert.equal(grams(5, 5), "5 g");
});

test("newest uses only the data", () => {
  const d = [{ id: "TG-001", added: "2026-11-02" }, { id: "TG-002", added: "2026-10-27" }, { id: "TG-003", added: "2026-10-20" }];
  assert.deepEqual(newest(d).map((x) => x.id), ["TG-001"]);
  assert.deepEqual(newest(d, 3, "2026-11-04").map((x) => x.id), ["TG-001"]);
  assert.deepEqual(newest(d, 3, "2026-11-20").map((x) => x.id), []);
});

test("every design uses a known category and a unique code", () => {
  const cats = new Set(JSON.parse(readFileSync("src/data/categories.json", "utf8")).map((c) => c.id));
  const ds = JSON.parse(readFileSync("src/data/designs.json", "utf8"));
  assert.equal(new Set(ds.map((d) => d.id)).size, ds.length);
  for (const d of ds) assert.ok(cats.has(d.category), d.id);
});

test("the look sentence says only what the details table does not", async () => {
  const { pieceLook } = await import("../src/lib/piece.js");
  const tag = { motif: "Wave", finish: "High polish", work: "Cast", stones: "None" };
  assert.equal(pieceLook(tag), "Wave motif in a high-polish cast finish.");
  assert.equal(pieceLook({ ...tag, motif: "Plain", stones: "CZ" }), "Plain high-polish cast finish. Set with CZ stones.");
  assert.equal(pieceLook(undefined), "");
});

test("the updates button opens a chat with the shop and town lines ready", () => {
  const url = waLink("919876543210", UPDATES_MESSAGE);
  assert.ok(url.startsWith("https://wa.me/919876543210?text="));
  assert.match(decodeURIComponent(url), /Shop name: \nTown: /);
});
