// Draws the Tejasvi Gold wordmark (the vector shapes the site uses) as a transparent PNG for the share cards.
// Output: tools/assets/logo.png in dark ink. Run once, or again if the wordmark changes:  node tools/make_logo.mjs
import { readFileSync, writeFileSync } from "node:fs";
import sharp from "sharp";
const glyphs = readFileSync("src/components/wordmark-glyphs.txt", "utf8");
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="626 43 793 406" width="1586" height="812" fill="#2b2116">${glyphs}</svg>`;
writeFileSync("tools/assets/logo.png", await sharp(Buffer.from(svg)).trim().png().toBuffer());
console.log("tools/assets/logo.png written");
