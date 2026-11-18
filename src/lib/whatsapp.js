// Deterministic WhatsApp messages: the same input always gives the same text.

export const CODE = /^TG-\d{3,4}$/;

// The message a shop sends from a piece. Fixed Hindi text, approved by the owner.
export function pieceMessage(name, code, spec, url) {
  return ["Namaste,", "Mujhe ye design ke baare mein jaankari chahiye:", `${name} – ${code} (${spec})`, url, "", "Aaj ka bhav aur delivery bataiye."].join("\n");
}

// Sent by a retailer who wants the broadcast list. Shop and town are filled in by them, so each one can be sorted into a regional list.
export const UPDATES_MESSAGE = "Namaste Tejasvi Gold! Please add me to your new design updates.\nShop name: \nTown: ";
export const CATALOGUE_MESSAGE = "Namaste, mujhe aapka naya catalogue bhejiye.";

export function enquiryMessage(f) {
  const rows = [
    ["Name", f.name], ["Shop", f.shop], ["Town", f.town], ["Mobile", f.mobile],
    ["Looking for", f.category], ["Quantity", f.quantity], ["Note", f.note],
  ].filter(([, v]) => v && String(v).trim());
  return ["Namaste Tejasvi Gold! New enquiry:", ...rows.map(([k, v]) => `${k}: ${String(v).trim()}`)].join("\n");
}

export function waLink(number, text) {
  if (!/^91\d{10}$/.test(number)) throw new Error("WhatsApp number must be 91 followed by 10 digits");
  return `https://wa.me/${number}?text=${encodeURIComponent(text)}`;
}

export function safeWa(number, text) {
  try { return waLink(number, text); } catch { return null; }
}

// Grams shown the same way everywhere: "2.4–3 g" (no trailing zeros).
export function grams(min, max) {
  const f = (n) => String(Number(n.toFixed(2)));
  return min === max ? `${f(min)} g` : `${f(min)}–${f(max)} g`;
}

// "New" = added within 3 days of the newest design. Pass today (YYYY-MM-DD) and nothing stays "New" once the
// last upload is more than 3 days old. Without today it depends only on the data.
export function newest(designs, days = 3, today = null) {
  if (!designs.length) return [];
  const last = designs.map((d) => d.added).sort().at(-1);
  const cut = new Date((today || last) + "T00:00:00Z"); cut.setUTCDate(cut.getUTCDate() - days);
  return designs
    .filter((d) => new Date(d.added + "T00:00:00Z") >= cut)
    .sort((a, b) => b.added.localeCompare(a.added) || a.id.localeCompare(b.id));
}
