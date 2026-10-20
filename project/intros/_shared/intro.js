// shared helpers for the five intro pitches. Each page builds one paused GSAP timeline `tl`,
// then calls IK.tail(tl) for the hand-off and IK.done(tl) for the grain, and registers tl itself.
(() => {
  // Foodee capture metadata, from ../../index.html META (tools/capture/composite_states.py)
  const FOODEE = {"color":"rgb(255, 255, 255)","states":[["orig",1548.5,332,332],["sel",1548.5,332,332],["t00",960,332,332],["t01",1061,332,332],["t02",1164.5,332,332],["t03",1262,332,332],["t04",1366,332,332],["t05",1394.5,332,332],["t06",1492,332,332]]};
  const CK = 0.9375, CX = 60, CY = 33.75;
  const toScreen = (x, y) => [CX + x * CK, CY + y * CK];
  const E = { o3: "power3.out", i3: "power3.in", io3: "power3.inOut", o4: "expo.out" };

  function blink(tl, el, t0, t1, period = 0.5) {
    for (let t = t0; t < t1 - 0.01; t += period) {
      tl.set(el, { opacity: 1 }, t);
      tl.set(el, { opacity: 0 }, t + period * 0.55);
    }
    tl.set(el, { opacity: 1 }, t1);
  }
  const rise = (tl, sel, t, stagger = 0.09, d = 0.62) =>
    tl.fromTo(sel, { yPercent: 112 }, { yPercent: 0, duration: d, ease: E.o4, stagger }, t);

  // split `text` into hidden per-letter spans inside el (followed by an in-flow caret unless caret === false)
  function chars(el, text, caret = true) {
    el.textContent = "";
    const cs = [...text].map((c) => {
      const s = document.createElement("span"); s.className = "ch"; s.textContent = c; el.appendChild(s); return s;
    });
    let ic = null;
    if (caret) { ic = document.createElement("span"); ic.className = "icaret"; el.appendChild(ic); }
    return { cs, caret: ic };
  }
  // reveal letters one by one; returns the time of the last keystroke
  function type(tl, cs, t0, step) {
    cs.forEach((s, i) => tl.set(s, { display: "inline" }, t0 + i * step));
    return t0 + (cs.length - 1) * step;
  }
  function select(tl, selEl, t, d = 0.16) {
    gsap.set(selEl.querySelector(".hl"), { scaleX: 0 });
    tl.to(selEl.querySelector(".hl"), { scaleX: 1, duration: d, ease: "power2.out" }, t);
    tl.to(selEl.querySelector(".tx"), { color: "#000", duration: 0.06 }, t + 0.03);
  }
  // a teal diamond opening from (x, y) until it covers the frame at t + 0.4
  function flood(tl, el, x, y, t) {
    gsap.set(el, { left: x, top: y, rotation: 45, scale: 0, transformOrigin: "50% 50%" });
    tl.set(el, { scale: 1 }, t);
    tl.to(el, { scale: 180, duration: 0.4, ease: E.i3 }, t);
  }

  function makeCaret(el, h, color) {
    const w = Math.max(3, Math.round(h * 0.05));
    const stem = el.querySelector(".stem");
    stem.style.width = w + "px"; stem.style.height = Math.round(h * 0.80) + "px";
    if (color) stem.style.background = color;
  }

  // hand-off 7.98–10.0: identical to scene C of the film (teal -> diamond iris -> Foodee renamed ROSA'S)
  function tail(tl) {
    const sec = document.getElementById("tail");
    sec.innerHTML = '<div class="layer tealbg" id="rTeal"></div><div class="layer" id="rIris">' +
      '<div class="layer" style="background:#000"></div><div class="cam" id="camR"><div class="card" id="cardR"></div></div></div>';
    const card = document.getElementById("cardR");
    const imgs = FOODEE.states.map(([n]) => {
      const img = document.createElement("img"); img.className = "st"; img.alt = "";
      img.src = `assets/designs/foodee_${n}.webp`; card.appendChild(img); return img;
    });
    const caret = document.createElement("div"); caret.className = "caret"; caret.innerHTML = '<div class="stem"></div>';
    card.appendChild(caret);
    makeCaret(caret, FOODEE.states[0][3], FOODEE.color);

    const show = (i, t) => {
      imgs.forEach((im, k) => tl.set(im, { opacity: k === i ? 1 : 0 }, t));
      const [, x, y, h] = FOODEE.states[i];
      tl.set(caret, { x: x + Math.max(3, h * 0.03), y: y + h * 0.9 }, t);
    };
    const fo = FOODEE.states[0];
    const [rx, ry] = toScreen(fo[1], fo[2] + fo[3] / 2);
    const [rcx, rcy] = toScreen(960, fo[2] + fo[3] * 0.55);
    const R = (r) => `polygon(${rx}px ${ry - r}px, ${rx + r}px ${ry}px, ${rx}px ${ry + r}px, ${rx - r}px ${ry}px)`;
    tl.fromTo("#rIris", { clipPath: R(0) }, { clipPath: R(2600), duration: 0.62, ease: E.i3 }, 7.99);
    tl.set("#rTeal", { opacity: 0 }, 8.62);
    gsap.set("#camR", { transformOrigin: `${rcx}px ${rcy}px` });
    tl.fromTo("#camR", { scale: 1.0 }, { scale: 1.05, duration: 0.7, ease: "none" }, 7.98);
    tl.to("#camR", { scale: 1.3, duration: 1.55, ease: "power2.inOut" }, 8.68);

    show(0, 7.98);
    tl.set(caret, { opacity: 0 }, 7.98);
    blink(tl, caret, 8.0, 8.45);
    show(1, 8.45);
    show(2, 8.75);
    for (let k = 3; k < imgs.length; k++) show(k, 8.95 + (k - 3) * 0.09);
    blink(tl, caret, 8.95 + (imgs.length - 4) * 0.09 + 0.35, 10.0);
  }

  function done(tl, dur = 10) {
    tl.fromTo("#grain", { x: 0, y: 0 }, { x: 60, y: -44, duration: dur, ease: `steps(${dur * 10})` }, 0);
  }

  window.IK = { E, blink, rise, chars, type, select, flood, tail, done };
})();
