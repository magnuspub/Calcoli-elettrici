#!/usr/bin/env python3
"""Prove di regressione di Calcoli_elettrici.html.

Apre ogni caso di prove/casi/ nel programma (come farebbe «Apri tutto»), raccoglie l'impronta dei risultati
e la confronta con prove/riferimento.json. Serve a capire se una versione nuova risponde come quella di riferimento.

    python3 prove/prova.py                      confronta Calcoli_elettrici.html con il riferimento
    python3 prove/prova.py altro.html           confronta un altro file
    python3 prove/prova.py --excel              ricalcola anche i fogli Excel con LibreOffice (più lento)
    python3 prove/prova.py --aggiorna           riscrive il riferimento con i risultati attuali
    python3 prove/prova.py --solo cc,pm         solo i casi il cui nome inizia così

Richiede Python con Playwright (Chromium); per --excel anche LibreOffice e openpyxl.
Esce con 1 se cambiano risultati o valori, con 0 se cambiano solo aspetto ed esportazioni o nulla.
"""
import asyncio, base64, glob, json, os, shutil, subprocess, sys, tempfile, time
from playwright.async_api import async_playwright

QUI = os.path.dirname(os.path.abspath(__file__))
ARGV = sys.argv[1:]
SOLO = None
if '--solo' in ARGV:
    i = ARGV.index('--solo'); SOLO = tuple(ARGV[i + 1].split(',')); del ARGV[i:i + 2]
ARG = [a for a in ARGV if not a.startswith('--')]
OPZ = [a for a in ARGV if a.startswith('--')]
HTML = os.path.abspath(ARG[0]) if ARG else os.path.join(QUI, '..', 'Calcoli_elettrici.html')
RIF = os.path.join(QUI, 'riferimento.json')
IMPRONTA = open(os.path.join(QUI, 'impronta.js'), encoding='utf-8').read()
CON_EXCEL = '--excel' in OPZ
XLS = {"modCC": "xlsCC", "modFUS": "xlsFUS", "modCB": "xlsCB", "modPMT": "xlsPMT", "modVK": "xlsVK", "modMT": "xlsMT", "modREL": "xlsREL"}

# impronta della banca dati: tabelle e curve grezze, più le curve calcolate di un interruttore per serie e di tre fusibili per famiglia
BANCA = open(os.path.join(QUI, 'banca.js'), encoding='utf-8').read()   # impronta della banca dati (usata anche dall'ambiente di manutenzione)


def differenze(a, b, percorso=''):
    """Elenco delle differenze tra due impronte: (percorso, valore di riferimento, valore attuale)."""
    if isinstance(a, dict) and isinstance(b, dict):
        d = []
        for k in sorted(set(a) | set(b)):
            if k not in a: d.append((percorso + '/' + k, '(assente)', b[k]))
            elif k not in b: d.append((percorso + '/' + k, a[k], '(assente)'))
            else: d += differenze(a[k], b[k], percorso + '/' + k)
        return d
    if isinstance(a, list) and isinstance(b, list):
        d = []
        if len(a) != len(b): d.append((percorso + ' (numero di voci)', len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)): d += differenze(x, y, f'{percorso}[{i}]')
        return d
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return [] if abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)) else [(percorso, a, b)]
    return [] if a == b else [(percorso, a, b)]


def categoria(percorso):
    if '/aspetto' in percorso: return 'aspetto'
    if '/esportazioni' in percorso or '/excel_ricalcolato' in percorso: return 'esportazioni'
    return 'risultati'


async def esegui():
    casi = sorted(glob.glob(os.path.join(QUI, 'casi', '*.json')))
    if SOLO: casi = [c for c in casi if os.path.basename(c).startswith(SOLO)]
    tmp = tempfile.mkdtemp(prefix='prove_xlsx_') if CON_EXCEL else None
    ris, righe_xls = {}, {}
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        sem = asyncio.Semaphore(4)

        async def pagina():
            p = await b.new_page(viewport={'width': 1300, 'height': 900}); err = []
            p.on('pageerror', lambda e: err.append(str(e)))
            p.on('console', lambda m: err.append(m.text) if m.type == 'error' and 'ERR_' not in m.text else None)
            p.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
            await p.goto('file://' + HTML); await p.wait_for_timeout(600)
            await p.evaluate('(()=>{ const f=document.getElementById("foldAll"); if(f&&/^Espandi/.test(f.textContent.trim())) f.click(); })()')
            return p, err

        async def uno(f):
            async with sem:
                c = json.load(open(f, encoding='utf-8')); p, err = await pagina()
                rep = await p.evaluate('([t])=>{ const r=allOpenText(t,"caso.json"); return r?{saltati:r.skip,mancanti:r.miss,nota:r.note||null}:"non aperto"; }', [json.dumps(c['stato'])])
                await p.wait_for_timeout(350)
                # dalla 0.2.1 i grafici di fusibili e interruttori stanno nel modulo «Coordinamento protezioni BT»
                if ('modFUS' in c['moduli'] or 'modCB' in c['moduli']) and 'modCOO' not in c['moduli']: c['moduli'] = c['moduli'] + ['modCOO']
                imp = await p.evaluate(IMPRONTA, c['moduli'])
                imp['apertura'] = rep; imp['errori'] = err[:]
                if CON_EXCEL:
                    for m in c['moduli']:
                        if m not in XLS: continue
                        dati = await p.evaluate('''async([m,fn])=>{ const S=window[fn](); const righe=S.rows.map((r,i)=>[i+1,r[0]&&r[0].v,r[1]&&r[1].s]).filter(r=>r[2]===5).map(r=>[r[0],r[1]]);
                            const buf=await buildXlsx(m).arrayBuffer(); let s=""; new Uint8Array(buf).forEach(x=>s+=String.fromCharCode(x)); return [btoa(s),righe]; }''', [m, XLS[m]])
                        nome = f"{c['nome']}__{m}.xlsx"; open(os.path.join(tmp, nome), 'wb').write(base64.b64decode(dati[0])); righe_xls[(c['nome'], m)] = dati[1]
                await p.close(); ris[c['nome']] = imp
                print('.', end='', flush=True)

        await asyncio.gather(*[uno(f) for f in casi])
        banca = None
        if not SOLO:
            p, err = await pagina(); banca = await p.evaluate(BANCA); banca['errori'] = err[:]; await p.close()
        versione = None
        p, err = await pagina(); versione = await p.evaluate('typeof APP_VER!=="undefined"?APP_VER:null'); await p.close()
        await b.close()
    print()
    if CON_EXCEL:   # ricalcolo indipendente delle formule con LibreOffice
        import openpyxl
        out = os.path.join(tmp, 'ricalcolati'); os.makedirs(out)
        files = sorted(glob.glob(os.path.join(tmp, '*.xlsx')))
        for i in range(0, len(files), 40):
            subprocess.run(['soffice', '--headless', '--calc', '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', out] + files[i:i + 40], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        for (nome, m), righe in righe_xls.items():
            f = os.path.join(out, f'{nome}__{m}.xlsx'); r = {}
            if os.path.exists(f):
                wb = openpyxl.load_workbook(f, data_only=True); ws = wb.worksheets[0]
                for n, lab in righe:
                    v = ws.cell(row=n, column=2).value
                    r[f'{n} · {lab}'] = (float(f'{v:.9g}') if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
                for ws in wb.worksheets[1:]:   # fogli aggiuntivi (per esempio «Punti»): tabella con intestazione e una riga per voce
                    tab = [x for x in ws.iter_rows(values_only=True)]; it = next((i for i, x in enumerate(tab) if x and x[0] == 'Punto'), None)
                    if it is None: continue
                    for x in tab[it + 1:]:
                        if not x or not x[0]: break
                        for j, v in enumerate(x[2:], 2):
                            if isinstance(v, (int, float)) and not isinstance(v, bool): r[f'{ws.title} · {x[0]} · {tab[it][j]}'] = float(f'{v:.9g}')
            else: r = {'errore': 'foglio non ricalcolato'}
            ris[nome][m]['excel_ricalcolato'] = r
        shutil.rmtree(tmp, ignore_errors=True)
    return {'programma': versione, 'casi': ris, 'banca_dati': banca}


def main():
    t0 = time.time(); att = asyncio.run(esegui())
    n = len(att['casi']); print(f"{os.path.basename(HTML)} versione {att['programma']}: {n} casi eseguiti in {time.time() - t0:.0f} s")
    err = {k: v['errori'] for k, v in att['casi'].items() if v.get('errori')}
    ap = {k: v['apertura'] for k, v in att['casi'].items() if v['apertura'] == 'non aperto' or v['apertura'].get('saltati') or v['apertura'].get('mancanti')}
    if err: print('ERRORI della pagina:', json.dumps(err, ensure_ascii=False)[:1500])
    if ap: print('CASI aperti con avvisi:', json.dumps(ap, ensure_ascii=False)[:1500])
    if '--aggiorna' in OPZ:
        if SOLO: sys.exit('--aggiorna va usato senza --solo')
        if not CON_EXCEL and os.path.exists(RIF):   # senza --excel si conservano i ricalcoli già presenti nel riferimento
            vecchio = json.load(open(RIF, encoding='utf-8'))
            for k, v in att['casi'].items():
                for m, o in v.items():
                    x = vecchio.get('casi', {}).get(k, {}).get(m)
                    if isinstance(o, dict) and isinstance(x, dict) and 'excel_ricalcolato' in x: o['excel_ricalcolato'] = x['excel_ricalcolato']
        att['riferimento_scritto_il'] = time.strftime('%d/%m/%Y')
        json.dump(att, open(RIF, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
        print(f'riferimento scritto: {RIF} ({os.path.getsize(RIF) / 1024:.0f} kB)'); return 1 if err else 0
    if not os.path.exists(RIF): sys.exit('manca prove/riferimento.json: crearlo con --aggiorna')
    rif = json.load(open(RIF, encoding='utf-8'))
    print(f"riferimento: versione {rif.get('programma')} del {rif.get('riferimento_scritto_il')}")
    tot = {'risultati': 0, 'aspetto': 0, 'esportazioni': 0}; cambiati = []
    for k in sorted(att['casi']):
        if k not in rif['casi']: print(f'  {k}: caso nuovo, assente nel riferimento'); continue
        a = rif['casi'][k]; b = att['casi'][k]
        if not CON_EXCEL:   # senza ricalcolo non si confrontano i valori ricalcolati del riferimento
            a = json.loads(json.dumps(a))
            for m in a.values():
                if isinstance(m, dict): m.pop('excel_ricalcolato', None)
        d = differenze(a, b)
        if not d: continue
        cat = {}
        for x in d: cat.setdefault(categoria(x[0]), []).append(x)
        for c, l in cat.items(): tot[c] += len(l)
        cambiati.append(k)
        print(f"  {k}: " + ', '.join(f'{len(l)} {c}' for c, l in cat.items()))
        for x in (cat.get('risultati') or [])[:6] + (cat.get('esportazioni') or [])[:2] + (cat.get('aspetto') or [])[:1]:
            print(f"      {x[0]}\n         riferimento: {str(x[1])[:170]}\n         attuale:     {str(x[2])[:170]}")
    for k in sorted(set(rif['casi']) - set(att['casi'])):
        if not SOLO: print(f'  {k}: caso del riferimento non eseguito')
    if att['banca_dati'] is not None:
        d = differenze(rif.get('banca_dati'), att['banca_dati'])
        if d:
            print(f'  banca dati: {len(d)} differenze'); tot['risultati'] += len(d)
            for x in d[:8]: print(f"      {x[0]}: {str(x[1])[:90]} → {str(x[2])[:90]}")
    print(f"casi diversi dal riferimento: {len(cambiati)} su {n} · differenze nei risultati {tot['risultati']}, nelle esportazioni {tot['esportazioni']}, nell'aspetto {tot['aspetto']}")
    return 1 if (tot['risultati'] or err) else 0


if __name__ == '__main__':
    sys.exit(main())
