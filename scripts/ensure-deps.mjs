// Runs before `npm run dev` and `npm run build`.
// If any package listed in package.json is missing or at the wrong version, it runs
// `npm install` once, so a changed package.json never breaks the site again.
import { readFileSync, existsSync } from "node:fs";
import { execSync } from "node:child_process";

const pkg = JSON.parse(readFileSync("package.json", "utf8"));
const wanted = { ...pkg.dependencies, ...pkg.devDependencies };
const missing = Object.entries(wanted).filter(([name, version]) => {
  const p = `node_modules/${name}/package.json`;
  if (!existsSync(p)) return true;
  const exact = /^\d+\.\d+\.\d+$/.test(version);
  return exact && JSON.parse(readFileSync(p, "utf8")).version !== version;
});

if (missing.length) {
  console.log(`Installing missing packages: ${missing.map(([n]) => n).join(", ")}`);
  execSync("npm install --no-audit --no-fund", { stdio: "inherit" });
}
