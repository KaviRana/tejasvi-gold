import { defineConfig } from "astro/config";

// Static site: plain HTML built ahead of time. Fast on cheap phones, free on Vercel.
// The address used in links (WhatsApp messages, page links for Google) comes from, in order:
// SITE_URL if set (use this once the real domain is bought), Vercel's production address, or local preview.
const site = process.env.SITE_URL
  ?? (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : "http://localhost:4321");

export default defineConfig({
  site,
  output: "static",
  trailingSlash: "always",
});
