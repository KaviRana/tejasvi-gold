// One place that joins designs, categories and checked tags into what the pages show.
import { getCollection } from "astro:content";
import business from "../data/business.json";
import tagList from "../data/tags.json";
import cutList from "../data/cutouts.json";
import { grams, pieceMessage, safeWa, newest } from "./whatsapp.js";
import { pieceName, pieceDescription, weightBand } from "./piece.js";

export async function loadPieces(site) {
  const cats = (await getCollection("categories")).map((c) => c.data).sort((a, b) => a.order - b.order);
  const catById = Object.fromEntries(cats.map((c) => [c.id, c]));
  // Read through the collection so every value is checked against the fixed lists. Skipped while no row is checked yet.
  const tagById = tagList.length ? Object.fromEntries((await getCollection("tags")).map((t) => [t.data.id, t.data])) : {};
  const designs = (await getCollection("designs")).map((x) => x.data);
  const cuts = new Set(cutList);
  const fresh = new Set(newest(designs, 3, new Date().toISOString().slice(0, 10)).map((d) => d.id));
  const pieces = (await getCollection("designs")).map((x) => x.data).sort((a, b) => a.id.localeCompare(b.id)).map((d) => {
    const cat = catById[d.category];
    const tag = tagById[d.id];
    const name = pieceName(cat, tag);
    const spec = `${grams(d.weight_min_g, d.weight_max_g)}, ${d.purity}`;
    const url = new URL(`/design/${d.id}/`, site).href;
    return {
      ...d, isNew: fresh.has(d.id), cut: cuts.has(d.id), image: d.image ?? `/designs/${d.id}.jpg`, cat, tag, name, spec, url,
      weight: grams(d.weight_min_g, d.weight_max_g),
      band: weightBand(d.weight_min_g, d.weight_max_g),
      description: pieceDescription(d, cat, tag),
      wa: safeWa(business.whatsapp, pieceMessage(name, d.id, spec, url)),
    };
  });
  return { pieces, cats };
}
