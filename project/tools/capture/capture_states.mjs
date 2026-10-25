// Capture a live Fixbyte design demo once per keystroke while its business name is retyped in the real DOM.
// usage: node tools/capture/capture_states.mjs <outDir> [jobId] [--phone]
// Writes <id>_orig|sel|tNN.webp (raw viewport screenshots) + meta_<id>.json (caret geometry + text colour, CSS px).
// --phone captures the mobile layout at 402x874 @3x (the reel); CHROME=<path> overrides the browser.
import puppeteer from "../../node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js";
import fs from "fs";
import os from "os";

const exe = process.env.CHROME || `${os.homedir()}/.cache/puppeteer/chrome-headless-shell/linux-145.0.7632.77/chrome-headless-shell-linux64/chrome-headless-shell`;
const args = process.argv.slice(2);
const PHONE = args.includes("--phone");
const [out, only] = args.filter((a) => a !== "--phone");

const JOBS = [
  {
    id: "foodee", url: "https://foodee-fixbyte.framer.website/", dpr: 1.5, name: "Rosa's", sel: ["#ffffff", "#8f0000"],
    // the big spotted wordmark: per-letter spans inside a Rubik Moonrocks <p>; collapse to one text node
    find: `[...document.querySelectorAll('p')].find(e => /Moonrocks/.test(getComputedStyle(e).fontFamily) && e.textContent.trim() === 'Foodee')`,
    collapse: true,
    final: [["FOODEE", "ROSA'S"]],
    phone: { dpr: 3 },
  },
  {
    // French version (fr/): the same wordmark, retyped as Luc's
    id: "foodee_fr", url: "https://foodee-fixbyte.framer.website/", dpr: 1.5, name: "Luc's", sel: ["#ffffff", "#8f0000"],
    find: `[...document.querySelectorAll('p')].find(e => /Moonrocks/.test(getComputedStyle(e).fontFamily) && e.textContent.trim() === 'Foodee')`,
    collapse: true,
    final: [["FOODEE", "LUC'S"]],
    phone: { dpr: 3 },
  },
  {
    id: "cantara", url: "https://cantara-fixbyte.framer.website/", dpr: 3, name: "MAISON NOOR", sel: ["rgb(18, 24, 32)", "#f5f2ec"],
    find: `[...document.querySelectorAll('h3')].find(e => e.textContent.trim() === 'CANTARA')`,
    // hide only the template's "Use This Template" button: deepest match, climbed while still button-sized
    prep: `const m = [...document.querySelectorAll('body *')].filter(e => /Use This Template/i.test(e.textContent));
      const deep = m.filter(e => ![...e.children].some(c => /Use This Template/i.test(c.textContent)));
      deep.forEach(e => { let x = e; while (x.parentElement && x.parentElement.getBoundingClientRect().width < 320) x = x.parentElement; x.style.visibility = 'hidden'; });`,
    final: [],
    // the mobile nav logo (the live demo now reads VANTARA)
    phone: { dpr: 3, find: `document.querySelector('nav h3, header h3') || [...document.querySelectorAll('h3')].find(e => e.getBoundingClientRect().top < 80)` },
  },
  {
    id: "azur", url: "https://alktravel.fixbyte.dev/", dpr: 1.5, name: "AZUR VOYAGES", sel: ["#ffffff", "#053a5c"],
    find: `[...document.querySelectorAll('p')].find(e => e.textContent.includes('DAR AL KHALILY'))`,
    suffix: "®", // the mark stays after the name; only the name is selected and retyped
    final: [["Dar Al Khalily Travel", "Azur Voyages"]],
    // on mobile the name on the first screen is the header logo
    phone: { dpr: 3, name: "Azur Voyages", suffix: "",
      find: `[...document.querySelectorAll('span')].find(e => e.textContent.trim() === 'Dar Al Khalily Travel' && e.getBoundingClientRect().top < 80)`,
      final: [["Dar Al Khalily Travel", "Azur Voyages"], ["DAR AL KHALILY", "AZUR VOYAGES"]] },
  },
];

if (PHONE) JOBS.forEach((j) => Object.assign(j, j.phone));

const b = await puppeteer.launch({ executablePath: exe, args: ["--no-sandbox", "--hide-scrollbars"] });
await Promise.all(JOBS.filter((j) => !only || j.id === only).map(async (j) => {
  const p = await b.newPage();
  if (PHONE) {
    await p.setUserAgent("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1");
    await p.setViewport({ width: 402, height: 874, deviceScaleFactor: j.dpr, isMobile: true, hasTouch: true });
  } else await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: j.dpr });
  try { await p.goto(j.url, { waitUntil: "networkidle2", timeout: 60000 }); } catch { console.log("nav timeout", j.id); }
  await new Promise((r) => setTimeout(r, 6500));
  // selection is drawn in the cursor's colour (the text colour), with the page colour as its ink
  await p.evaluate((prep, sel) => {
    document.querySelectorAll("#__framer-badge-container,[id*=badge]").forEach((e) => e.remove());
    [...document.querySelectorAll("body *")].forEach((e) => {
      const cs = getComputedStyle(e);
      if ((cs.position === "fixed" || cs.position === "sticky") && e.getBoundingClientRect().top > 300) e.remove();
    });
    const st = document.createElement("style");
    st.textContent = `*{caret-color:transparent!important} ::selection{background:${sel[0]}!important;color:${sel[1]}!important}`;
    document.head.appendChild(st);
    document.querySelectorAll("video").forEach((v) => v.pause());
    document.getAnimations().forEach((a) => a.pause());
    if (prep) (0, eval)(prep);
  }, j.prep || "", j.sel);
  await p.evaluate((find, collapse, suffix) => {
    const el = (0, eval)(find);
    if (collapse) el.textContent = el.textContent.trim();
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n, tn = null;
    while ((n = w.nextNode())) if (n.textContent.trim()) { tn = n; break; }
    window.__tn = tn;
    window.__suf = suffix;
    if (suffix && !tn.textContent.endsWith(suffix)) throw new Error("suffix not found in " + tn.textContent);
    window.__col = getComputedStyle(tn.parentElement).color;
  }, j.find, !!j.collapse, j.suffix || "");
  const caret = () => p.evaluate(() => {
    const tn = window.__tn, r = document.createRange(), suf = window.__suf;
    const L = tn.textContent.length - suf.length;   // caret sits at the end of the name, before any suffix
    if (suf && L === 0) {
      r.setStart(tn, 0); r.setEnd(tn, suf.length);
      const rect = r.getClientRects()[0];
      return { x: rect.left, y: rect.top, h: rect.height };
    }
    if (L === 0 || tn.textContent === "​") {
      r.setStart(tn, 0); r.setEnd(tn, L);
      const rect = r.getClientRects()[0] || tn.parentElement.getBoundingClientRect();
      return { x: rect.left, y: rect.top, h: rect.height };
    }
    r.setStart(tn, 0); r.setEnd(tn, L);
    const rs = [...r.getClientRects()], last = rs[rs.length - 1];
    return { x: last.right, y: last.top, h: last.height };
  });
  const shot = async (n) => {
    await p.evaluate(() => document.getAnimations().forEach((a) => a.pause()));
    await new Promise((r) => setTimeout(r, 200));
    await p.screenshot({ path: `${out}/${j.id}_${n}.webp`, type: "webp", quality: 94 });
  };
  const m = { color: await p.evaluate(() => window.__col), dpr: j.dpr, states: [] };
  const o = await caret(); await shot("orig"); m.states.push(["orig", o.x, o.y, o.h]);
  await p.evaluate(() => {
    const tn = window.__tn, r = document.createRange();
    r.setStart(tn, 0); r.setEnd(tn, tn.textContent.length - window.__suf.length);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
  });
  await shot("sel"); m.states.push(["sel", o.x, o.y, o.h]);
  await p.evaluate(() => getSelection().removeAllRanges());
  for (let k = 0; k <= j.name.length; k++) {
    const t = j.name.slice(0, k);
    await p.evaluate((t) => { const suf = window.__suf; window.__tn.textContent = (t || (suf ? "" : "​")) + suf; }, t);
    if (k === j.name.length) {
      await p.evaluate((ex) => {
        for (const [a, bb] of ex) {
          const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
          while ((n = w.nextNode())) if (n.textContent.includes(a)) n.textContent = n.textContent.replace(a, bb);
        }
      }, j.final);
    }
    const c = await caret();
    const id = "t" + String(k).padStart(2, "0");
    await shot(id); m.states.push([id, c.x, c.y, c.h]);
  }
  fs.writeFileSync(`${out}/meta_${j.id}.json`, JSON.stringify(m));
  console.log("done", j.id, m.color);
  await p.close();
}));
await b.close();
