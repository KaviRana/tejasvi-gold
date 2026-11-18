// Deterministic names and descriptions. The code (TG-####) stays the unique ID;
// the name is a readable label built only from the checked tags.
import { grams } from "./whatsapp.js";

const FINISH_ADJ = { "High polish": "high-polish", "Matte": "matte", "Polish and matte": "polished and matte", "Textured": "textured" };
const WORK_ADJ = { "Cast": "cast", "Filigree": "filigree", "Cut work": "cut-work", "Beaded": "beaded" };
const STONES_LINE = { "CZ": "Set with CZ stones.", "Enamel": "With enamel colour work." };
const STATUS_LINE = { "in-stock": "Ready stock.", "on-approval": "On approval.", "made-to-order": "Made to order." };
const title = (s) => s.replace(/\b\w/g, (c) => c.toUpperCase());

// Bands use the middle of the weight range.
export function weightBand(min, max) {
  const mid = (min + max) / 2;
  return mid < 3 ? "Under 3 g" : mid <= 5 ? "3–5 g" : "Over 5 g";
}

// What the details table does not say: the look, in one short sentence. Nothing for a piece without checked tags.
export function pieceLook(tag) {
  if (!tag) return "";
  const finish = `${FINISH_ADJ[tag.finish]} ${WORK_ADJ[tag.work]} finish`;
  const look = tag.motif === "Plain" ? `Plain ${finish}.` : `${tag.motif} motif in a ${finish}.`;
  return [look, STONES_LINE[tag.stones]].filter(Boolean).join(" ");
}

// "Wave Cast Ring". No tags yet: the category alone, "Ladies Ring".
export function pieceName(cat, tag) {
  if (!tag) return cat.single;
  if (tag.name) return tag.name;
  return `${tag.motif} ${title(tag.work)} ${cat.one}`;
}

// "A 22K gold ladies' ring with a wave motif in a high-polish cast finish, weighing 3.18 g. BIS hallmarked with HUID. Made to order."
export function pieceDescription(d, cat, tag) {
  const w = grams(d.weight_min_g, d.weight_max_g);
  const parts = [];
  if (!tag) parts.push(`A ${d.purity} gold ${cat.noun}, weighing ${w}.`);
  else {
    const finish = `${FINISH_ADJ[tag.finish]} ${WORK_ADJ[tag.work]} finish`;
    const look = tag.motif === "Plain" ? `in a plain ${finish}` : `with a ${tag.motif.toLowerCase()} motif in a ${finish}`;
    parts.push(`A ${d.purity} gold ${cat.noun} ${look}, weighing ${w}.`);
    if (STONES_LINE[tag.stones]) parts.push(STONES_LINE[tag.stones]);
  }
  parts.push("BIS hallmarked with HUID.", STATUS_LINE[d.status]);
  return parts.join(" ");
}
