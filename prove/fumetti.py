#!/usr/bin/env python3
"""Controllo delle nuvolette delle descrizioni (le «i» dei campi, dei titoli e delle verifiche) di Calcoli_elettrici.html.

Dalla 0.2.26 la descrizione compare passando sul nome, in un'unica nuvoletta (#ttBox) che il programma mette vicino al
nome. Lo script mette a fuoco ogni «i», una larghezza di finestra alla volta, e misura dove finisce davvero la nuvoletta
confrontando due immagini della pagina: una prima e una con la nuvoletta aperta. Segnala quelle che non compaiono, che
hanno un testo diverso da quello della «i», che escono dalla finestra o che allargano la pagina. Serve soprattutto per
gli schermi stretti.

    python3 prove/fumetti.py                                   larghezze abituali, stato predefinito del programma
    python3 prove/fumetti.py altro.html                        controlla un altro file
    python3 prove/fumetti.py --largh 390                       solo una larghezza
    python3 prove/fumetti.py --caso prove/casi/cc40_....json   apre prima un caso, per avere più campi a video
    python3 prove/fumetti.py --salva /tmp/fumetti              salva l'immagine dei fumetti che non vanno

Con un caso di prova compaiono anche i fumetti delle righe aggiunte (trasformatori, cavi, motori): conviene usarne
uno ricco. Lo script apre da sé tutti i moduli, i sotto-moduli e i pannelli «avanzate», così quasi tutti i fumetti
sono raggiungibili; restano fuori quelli dei campi che compaiono solo con certe scelte.

Richiede Python con Playwright (Chromium) e Pillow. Esce con 1 se almeno una nuvoletta non va.
"""
import asyncio, io, json, os, sys
from PIL import Image, ImageChops
from playwright.async_api import async_playwright

QUI = os.path.dirname(os.path.abspath(__file__))
ARGV = sys.argv[1:]


def opzione(nome, pred=None):
    """Valore di un'opzione --nome, tolta da ARGV."""
    global ARGV
    if nome in ARGV:
        i = ARGV.index(nome); v = ARGV[i + 1]; del ARGV[i:i + 2]; return v
    return pred


LARGHEZZE = [int(x) for x in opzione('--largh', '320,360,390,480,768,1024,1400').split(',')]
CASO = opzione('--caso')
SALVA = opzione('--salva')
ARG = [a for a in ARGV if not a.startswith('--')]
HTML = os.path.abspath(ARG[0]) if ARG else os.path.join(QUI, '..', 'Calcoli_elettrici.html')
MARGINE = 4          # tolleranza sul bordo: sotto questa distanza il fumetto si considera fuori
SOGLIA = 28          # differenza di luminosità oltre la quale un pixel si considera cambiato

# tutto aperto, e ogni fumetto numerato per poterlo richiamare
APRI = '''() => {
  const f = document.getElementById("foldAll");
  if (f && /^Espandi/.test(f.textContent.trim())) f.click();
  document.querySelectorAll(".subfold.shut").forEach(e => e.classList.remove("shut"));
  document.querySelectorAll("details").forEach(d => d.open = true);
  document.querySelectorAll(".tip").forEach((e, i) => e.dataset.idx = i);
  return document.querySelectorAll(".tip").length;
}'''

# la nuvoletta aperta: dov'è e che cosa dice
LEGGI = '''() => {
  const b = document.getElementById("ttBox"); if (!b || b.hidden) return null;
  const r = b.getBoundingClientRect(); return { x0: r.left, y0: r.top, x1: r.right, y1: r.bottom, t: b.textContent };
}'''

DOVE = '''(i) => {
  const e = document.querySelector(`.tip[data-idx="${i}"]`);
  if (!e || e.offsetParent === null) return null;
  const et = e.closest("label,td,th,h2,h3,div");
  return { cls: e.className, dove: (e.closest("[id^=mod]") || {}).id || "",
           eti: ((et && et.textContent) || "").trim().slice(0, 36),
           testo: (e.dataset.tip || "").slice(0, 60) };
}'''


def riquadro(prima, dopo):
    """Riquadro dei pixel cambiati tra le due immagini: è il fumetto comparso."""
    a = Image.open(io.BytesIO(prima)).convert('L')
    b = Image.open(io.BytesIO(dopo)).convert('L')
    return ImageChops.difference(a, b).point(lambda v: 255 if v > SOGLIA else 0).getbbox()


async def una_larghezza(browser, largh, stato):
    c = await browser.new_context(viewport={'width': largh, 'height': 880})
    p = await c.new_page()
    errori = []
    p.on('pageerror', lambda e: errori.append(str(e)[:150]))
    await p.goto('file://' + HTML)
    await p.wait_for_timeout(600)
    if stato:
        await p.evaluate('([t]) => allOpenText(t, "caso.json")', [json.dumps(stato)])
        await p.wait_for_timeout(500)
    n = await p.evaluate(APRI)
    await p.wait_for_timeout(300)
    # la pagina può già essere più larga della finestra per conto suo: quella larghezza non va addebitata ai fumetti
    base = await p.evaluate('document.documentElement.scrollWidth')
    alto = 880                                # l'altezza della finestra aperta qui sopra
    guai, visti = [], 0
    for i in range(n):
        info = await p.evaluate(DOVE, i)
        if not info:
            continue
        visti += 1
        el = p.locator(f'.tip[data-idx="{i}"]')
        await el.evaluate('e => { document.activeElement && document.activeElement.blur(); e.scrollIntoView({block: "center"}); }')
        await p.wait_for_timeout(60)
        prima = await p.screenshot()
        await el.focus()
        await p.wait_for_timeout(140)
        dopo = await p.screenshot()
        largo_ora = await p.evaluate('document.documentElement.scrollWidth')
        rq = riquadro(prima, dopo)
        box = await p.evaluate(LEGGI)
        testo = await el.evaluate('e => e.dataset.tip || ""')
        await p.evaluate('() => document.activeElement && document.activeElement.blur()')
        if not rq or not box:
            guai.append((i, info, 'la nuvoletta non compare')); continue
        x0, y0, x1, y1 = rq
        if box['t'] != testo:
            msg = 'il testo della nuvoletta non è quello della «i»'
        elif box['x0'] < MARGINE or box['x1'] > largh - MARGINE or box['y0'] < MARGINE or box['y1'] > alto - MARGINE:
            msg = f'esce dalla finestra: da {box["x0"]:.0f},{box["y0"]:.0f} a {box["x1"]:.0f},{box["y1"]:.0f} in {largh}×{alto} px'
        elif largo_ora > max(base, largh) + 1:
            msg = f'allarga la pagina a {largo_ora} px (era {base})'
        elif x1 - x0 < (box['x1'] - box['x0']) - 24:
            msg = f'coperta: se ne vedono {x1 - x0} px su {box["x1"] - box["x0"]:.0f}'
        else:
            continue
        guai.append((i, info, msg))
        if SALVA:
            os.makedirs(SALVA, exist_ok=True)
            Image.open(io.BytesIO(dopo)).save(os.path.join(SALVA, f'{largh}_{i}.png'))
    print(f'{largh} px: {visti} nuvolette controllate su {n} · da sistemare {len(guai)}')
    for i, info, msg in guai:
        print(f'   #{i} [{info["dove"]}] «{info["eti"]}» class="{info["cls"]}" → {msg}')
    if errori:
        print('   ERRORI della pagina:', errori[:3])
    await c.close()
    return len(guai)


async def esegui():
    stato = json.load(open(CASO, encoding='utf-8'))['stato'] if CASO else None
    tot = 0
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        print(f'{os.path.basename(HTML)}' + (f' · caso {os.path.basename(CASO)}' if CASO else ' · stato predefinito'))
        for largh in LARGHEZZE:
            tot += await una_larghezza(b, largh, stato)
        await b.close()
    print(('nessuna nuvoletta fuori posto' if not tot else f'nuvolette da sistemare: {tot}')
          + (f' · immagini in {SALVA}' if SALVA and tot else ''))
    return 1 if tot else 0


if __name__ == '__main__':
    sys.exit(asyncio.run(esegui()))
