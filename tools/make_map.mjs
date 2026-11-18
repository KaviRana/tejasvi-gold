// Draws the customers map for the home page: state outlines and one pin per town, as plain SVG paths in
// src/data/map.json. The same inputs always give the same file.
// Needs catalogue-sources/india_states.geojson: the India states from Natural Earth admin-1, 10m (public domain,
// github.com/nvkelso/natural-earth-vector), each with a NAME_1 property. Not committed. Run: npm run map
// Towns and their coordinates are in tools/data/map_towns.json; "cities" lists the names as typed in the accounts.
import fs from "node:fs";
import { geoMercator, geoPath } from "d3-geo";
import { topology } from "topojson-server";
import { presimplify, simplify } from "topojson-simplify";
import { feature } from "topojson-client";

const W = 800;
const BOX = { west: 71.6, east: 80.8, south: 15.3, north: 25.3 }; // Maharashtra and the border towns
const geo = JSON.parse(fs.readFileSync("catalogue-sources/india_states.geojson", "utf8"));
const pre = presimplify(topology({ states: geo }));
const fine = feature(simplify(pre, 0.0006), "states"), coarse = feature(simplify(pre, 0.004), "states");
const slim = { features: fine.features.map((f, i) => (f.properties.NAME_1 === "Maharashtra" ? f : coarse.features[i])) };
const box = { type: "Polygon", coordinates: [[[BOX.west, BOX.south], [BOX.west, BOX.north], [BOX.east, BOX.north], [BOX.east, BOX.south], [BOX.west, BOX.south]]] /* clockwise: d3 reads the other way round as the whole globe except the box */ };
const proj = geoMercator().fitWidth(W, box);
const path = geoPath(proj).digits(1);
const H = Math.ceil(path.bounds(box)[1][1]);

const states = slim.features
  .filter((f) => { const [[x0, y0], [x1, y1]] = path.bounds(f); return x1 > 0 && x0 < W && y1 > 0 && y0 < H; })
  .filter((f) => f.properties.NAME_1 !== "Puducherry")
  .map((f) => ({ n: f.properties.NAME_1, d: path(f) }))
  .sort((a, b) => a.n.localeCompare(b.n));
const towns = JSON.parse(fs.readFileSync("tools/data/map_towns.json", "utf8"));
const pins = towns.map((t) => { const [x, y] = proj([t.lng, t.lat]); return { n: t.name, x: +x.toFixed(1), y: +y.toFixed(1) }; });
fs.writeFileSync("src/data/map.json", JSON.stringify({ viewBox: `0 0 ${W} ${H}`, states, pins }));
console.log(`map: ${states.length} states, ${pins.length} pins, ${(fs.statSync("src/data/map.json").size / 1024).toFixed(0)} KB`);
