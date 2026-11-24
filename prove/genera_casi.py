#!/usr/bin/env python3
"""Genera i casi campione di prove/casi/ a partire dallo stato predefinito del programma.

Ogni caso è un file nel formato di «Salva tutto»: si può aprire anche a mano con «Apri tutto».
Va rieseguito solo per aggiungere o cambiare casi; il confronto tra versioni si fa con prova.py.

    python3 prove/genera_casi.py [percorso di Calcoli_elettrici.html]
    python3 prove/genera_casi.py --solo cc27,pm12      scrive solo i casi con questi prefissi e lascia gli altri come sono

I casi già scritti non vanno rigenerati senza motivo: aperti da una versione più recente provano anche che i file
salvati con le versioni precedenti si riaprono con gli stessi risultati.
"""
import asyncio, copy, json, os, sys
from playwright.async_api import async_playwright

QUI = os.path.dirname(os.path.abspath(__file__))
ARGV = sys.argv[1:]
SOLO = None
if '--solo' in ARGV:
    i = ARGV.index('--solo'); SOLO = tuple(ARGV[i + 1].split(',')); del ARGV[i:i + 2]
HTML = os.path.abspath(ARGV[0]) if ARGV else os.path.join(QUI, '..', 'Calcoli_elettrici.html')
SALVA = '''(()=>{ let s=null; const o=window._saveFile; window._saveFile=(n,c)=>{s=c}; document.getElementById("allSave").click(); window._saveFile=o; return s; })()'''
TUTTI = ["modCC", "modFUS", "modCB", "modPMT", "modVK", "modMT", "modREL"]
CASI = []


def caso(nome, moduli, grezzo=False):
    # grezzo: lo stato è scritto com'è, senza farlo risalvare dal programma (serve per i file nel formato di versioni precedenti)
    def reg(f):
        CASI.append((nome, moduli, f, grezzo)); return f
    return reg


# ---- piccoli aiuti per modificare lo stato -------------------------------------------------
def cc(s): return s['moduli']['modCC']['campi']
def ccm(s): return s['moduli']['modCC']
def fu(s): return s['moduli']['modFUS']
def cb(s): return s['moduli']['modCB']
def pm(s): return s['moduli']['modPMT']
def campi(s, m, **kw):
    s['moduli'][m]['campi'].update({k: (v if isinstance(v, bool) else str(v)) for k, v in kw.items()})
def riga(base, **kw):
    r = copy.deepcopy(base); r.update({k: (v if isinstance(v, bool) else str(v)) for k, v in kw.items()}); return r


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        p = await b.new_page(viewport={'width': 1300, 'height': 900})
        await p.goto('file://' + HTML); await p.wait_for_timeout(900)
        BASE = json.loads(await p.evaluate(SALVA))
        # Dalla 0.2.0 i componenti sono salvati sotto «Impianto» e dalla 0.2.1 le correnti di fusibili e interruttori seguono il punto.
        # I casi sono scritti sulla struttura precedente, che il programma apre ancora: qui la si ricostruisce, con le correnti a mano di allora.
        M = BASE['moduli']
        for k in ('trasformatori', 'cavi', 'motori'):
            if k in M.get('modIMP', {}): M['modCC'][k] = M['modIMP'].pop(k)
        M['modCC']['campi'].update(M.get('modIMP', {}).get('campi', {}))
        # dalla 0.2.12 fusibili e interruttori hanno «includi» (spento all'apertura dalla 0.2.14): nei casi i dispositivi sono sempre inclusi
        for k in ('onFus', 'onCb'):
            M['modCC']['campi'][k] = True; M.get('modIMP', {}).get('campi', {}).pop(k, None)
        # dalla 0.2.3 fusibili e interruttori sono elenchi liberi: i casi scritti sulla coppia A/B restano validi togliendo l'elenco
        for m in ('modFUS', 'modCB'): M[m].pop('elenco', None); M[m].pop('punti', None)
        M['modPMT'].pop('dispositivi', None)
        # dalla 0.2.4 il quadro e il guasto a terra MT seguono un dispositivo o le protezioni MT: i casi precedenti avevano i valori a mano
        M['modVK'].pop('derivatoDa', None); M['modVK']['campi'].update({'vk_Ik': '18.9', 'vk_ip': '38.2', 'vk_Ith': '19', 'vk_cutoff': '0'})
        M['modMT']['campi'].update({'mt_IE': '40', 'mt_tF': '10.01'})
        M['modFUS']['campi'].update({'fu_Ik': '18.9', 'fu_ip': '38.2', 'fu_Imin': '0'}); M['modCB']['campi'].update({'cb_Ik': '18.9', 'cb_ip': '38.2', 'cb_Imin': '0'})
        TR0 = BASE['moduli']['modCC']['trasformatori'][0]
        # righe predefinite di cavi e motori (le schede sono escluse: si leggono aggiungendone una)
        await p.evaluate('document.getElementById("addCable").click(); document.getElementById("addMot").click(); 0')
        tmp = json.loads(await p.evaluate(SALVA))
        CAV0 = tmp['moduli']['modIMP']['cavi'][-1]; MOT0 = tmp['moduli']['modIMP']['motori'][-1]
        PR0 = BASE['moduli']['modPMT']['protezioni'][0]
        # descrizione di fusibili e interruttori per nome, come nel file salvato
        FUS = await p.evaluate('''FUS_DB.p.map(p=>({gruppo:FUS_DB.g[p[1]][0],famiglia:FUS_DB.g[p[1]][1],tipo:p[0],In:p[3]}))''')
        CB = await p.evaluate('''(()=>{ const m={}; CB_DB.p.forEach(p=>{ const g=CB_DB.g[p[1]]; if(!m[p[0]]) m[p[0]]={gruppo:CB_DB.s[g[0]][0],serie:CB_DB.s[g[0]][1],esecuzione:cbFamTxt(g),tipo:p[0]}; }); return m; })()''')
        LPEX = await p.evaluate('JSON.parse(JSON.stringify(LP_EX))')
        await b.close()

    def fus(i): return copy.deepcopy(FUS[i])
    def fusn(testo, In):   # primo fusibile la cui famiglia contiene il testo, con la corrente nominale indicata
        return copy.deepcopy(next(f for f in FUS if testo in f['famiglia'] and f['In'] == In))
    def intr(tipo, **reg):
        o = copy.deepcopy(CB[tipo])
        if reg: o['regolazioni'] = {k: str(v) for k, v in reg.items()}
        return o
    def tr(**kw): return riga(TR0, **kw)
    def cav(**kw): return riga(CAV0, **kw)
    def mot(**kw): return riga(MOT0, **kw)
    def prot(**kw): return riga(PR0, **kw)

    # ============================ CORTOCIRCUITO ============================
    @caso('cc01_predefinito', TUTTI + ['modLP'])
    def _(s): pass

    @caso('cc02_correzione_KT', ['modCC'])
    def _(s): campi(s, 'modCC', onKT=True)

    @caso('cc03_rete_in_potenza', ['modCC'])
    def _(s): campi(s, 'modCC', gridMode='Sk', SkQ=350, rxGrid=0.05, SkQmin=200)

    @caso('cc04_due_trasformatori_uguali_metodo_B', ['modCC'])
    def _(s): ccm(s)['trasformatori'] = [tr(), tr(desc='Trasf. 2')]

    @caso('cc05_due_trasformatori_diversi_metodo_C', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=1000, uk=6, pcu=10.5, kin=10, tau=0.35), tr(desc='Trasf. 2', S=400, uk=4, pcu=4.6, kin=12, tau=0.25)]
        campi(s, 'modCC', ipMethod='C', onKT=True)

    @caso('cc06_tre_trasformatori_in_resina_gruppi_diversi', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=800, uk=6, pcu=9.4, tt='secco', vg='Dyn', kin=10, tau=0.3), tr(desc='Trasf. 2', S=800, uk=6, pcu=9.4, tt='secco', vg='Yyn', kin=10, tau=0.3),
                                   tr(desc='Trasf. 3', S=500, uk=6, pcu=6.4, tt='secco', vg='Dzn', kin=10, tau=0.25)]
        campi(s, 'modCC', onKT=True)

    @caso('cc07_gruppo_senza_neutro_e_fase_terra', ['modCC'])
    def _(s): ccm(s)['trasformatori'] = [tr(vg='Dd')]

    @caso('cc08_cavo_sorgente_in_alluminio', ['modCC'])
    def _(s): campi(s, 'modCC', sc_on=True, sc_tipo='mt', sc_mat='Al', sc_S=185, sc_L=1200, sc_n=1, sc_x=0.12, sc_te=160)

    @caso('cc09_cavi_del_trasformatore', ['modCC'])
    def _(s): ccm(s)['trasformatori'] = [tr(hvcab=True, hvS=50, hvL=400, hvte=90, hascab=True, cS=240, cL=18, cn=3, cte=160, cSn=120)]

    @caso('cc10_due_tratti_di_cavo', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Montante', tipo='uni', mat='Cu', S=240, L=30, n=2, x=0.10, te=250, Sn=120), cav(desc='Dorsale', tipo='mult', mat='Al', S=95, L=60, n=1, x=0.08, te=160, Sn=50)]
        campi(s, 'modCC', onCab=True)

    @caso('cc11_tre_motori', ['modCC'])
    def _(s):
        ccm(s)['motori'] = [mot(desc='Pompa', P=200, klr=6, poles=2), mot(desc='Ventilatore', P=90, klr=7, poles=4, eta=0.85), mot(desc='Compressore', P=315, klr=5.5, poles=1, rx=0.3, tmin=0.05)]
        campi(s, 'modCC', onMot=True)

    # Guasto fase-terra: si calcola dove tutti i cavi fino al centro stella hanno la sezione N/PE
    @caso('cc12_fase_terra_TN', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Linea', S=50, L=40, x=0.08, te=160, Sn=50)]
        campi(s, 'modCC', onCab=True)

    # N/PE a sezione ridotta nel primo tratto e non indicata nel secondo: a valle del secondo il fase-terra non è calcolato
    @caso('cc13_fase_terra_N_PE_ridotto_e_tratto_senza_sezione', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Montante', S=185, L=25, n=2, Sn=95), cav(desc='Dorsale', S=70, L=55, te=160)]
        campi(s, 'modCC', onCab=True)

    # Linea aerea con X0/X = 3 dopo un cavo con il rapporto predefinito 4; cavo di ramo con X0/X = 1,8
    @caso('cc43_linea_aerea_e_cavo_di_ramo_con_X0_X_diverso_da_4', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=400, uk=4, pcu=4.6, hascab=True, cS=240, cL=8, cn=2, cSn=240, ckx0=1.8)]
        ccm(s)['cavi'] = [cav(desc='Cavo', S=95, L=30, Sn=50), cav(desc='Linea aerea', tipo='aerea', S=50, L=120, x=0.3, te=160, Sn=50, kx0=3)]
        campi(s, 'modCC', onCab=True)

    @caso('cc14_60_Hz_guasto_breve', ['modCC'])
    def _(s): campi(s, 'modCC', freq=60, ccTk=0.2)

    @caso('cc15_guasto_di_3_secondi', ['modCC'])
    def _(s): campi(s, 'modCC', ccTk=3)

    @caso('cc16_guasto_in_media_tensione', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Linea MT', tipo='mt', S=95, L=850, x=0.12, te=250)]
        campi(s, 'modCC', onTr=False, UnQ=20000, IkQ=12.5, IkQmin=9, onCab=True, cfac=1.10, cfacMin=1.00)

    @caso('cc17_media_tensione_in_potenza', ['modCC'])
    def _(s): campi(s, 'modCC', onTr=False, gridMode='Sk', SkQ=500, SkQmin=300, UnQ=15000, cfac=1.10, cfacMin=1.00, rxGrid=0.1)

    @caso('cc18_fornitura_monofase_CEI_0_21', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Montante', S=10, L=25, te=160)]
        campi(s, 'modCC', gridPreset='cei_mono', gridMode='Ik', IkQ=6, UnQ=230, rxGrid=0.98, onTr=False, onCab=True, IkQmin=4.5)

    @caso('cc19_fornitura_trifase_10_kA', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Montante', S=25, L=40, te=160)]
        campi(s, 'modCC', gridPreset='cei_tri33', gridMode='Ik', IkQ=10, UnQ=400, rxGrid=0.577, onTr=False, onCab=True)

    @caso('cc20_fornitura_trifase_15_kA_con_motore', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Montante', S=95, L=30, te=250)]; ccm(s)['motori'] = [mot(P=55, klr=7, poles=2)]
        campi(s, 'modCC', gridPreset='cei_tri33p', gridMode='Ik', IkQ=15, UnQ=400, rxGrid=0.314, onTr=False, onCab=True, onMot=True)

    @caso('cc21_fattori_c_per_reti_10_per_cento', ['modCC'])
    def _(s): campi(s, 'modCC', cfac=1.10, cfacMin=0.90)

    @caso('cc22_alta_media_tensione', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='AT/MT', S=25000, uk=12, pcu=110, uhv=132000, ulv=20000, vg='Dyn', kin=8, tau=0.45)]
        campi(s, 'modCC', gridMode='Sk', SkQ=3000, UnQ=132000, cfac=1.10, cfacMin=1.00)

    @caso('cc23_trasformatore_BT_BT', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='Isolamento', S=100, uk=4, pcu=1.75, uhv=400, ulv=230, vg='Dyn', kin=14, tau=0.15)]
        campi(s, 'modCC', IkQ=10, UnQ=400, rxGrid=0.5)

    @caso('cc24_sistema_690_V_con_motori', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=2000, uk=6, pcu=18, uhv=20000, ulv=690, kin=8, tau=0.45)]
        ccm(s)['motori'] = [mot(P=400, U=690, klr=6.5, poles=2), mot(desc='Motore 2', P=250, U=690, klr=6, poles=3)]
        campi(s, 'modCC', UnQ=20000, IkQ=16, onMot=True, onKT=True)

    @caso('cc25_senza_rete_a_monte', ['modCC'])
    def _(s): campi(s, 'modCC', onGrid=False)

    # ---- punti della catena: consegna, primario, sbarre, fine di ogni tratto ----
    @caso('cc27_punti_cavo_sorgente_ramo_tre_tratti', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(hascab=True, cS=240, cL=12, cn=3, cSn=120)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2, Sn=240), cav(desc='Dorsale', S=95, L=42, te=160, Sn=50), cav(desc='Terminale', mat='Al', S=10, L=65, te=160, Sn=10)]
        ccm(s)['motori'] = [mot(P=110), mot(desc='Motore 2', P=45, klr=7, poles=2)]
        campi(s, 'modCC', sc_on=True, sc_mat='Al', sc_S=95, sc_L=350, sc_te=200, onCab=True, onMot=True, IkQmin=9)

    @caso('cc28_punti_due_trasformatori_metodo_C', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=800, uk=6, pcu=8.5, vg='Dzn', kin=10, tau=0.3), tr(desc='Trasf. 2', S=800, uk=6, pcu=8.5, kin=10, tau=0.3, hascab=True, cS=185, cL=20, cSn=95)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2, Sn=240), cav(desc='Dorsale', S=95, L=42, te=160, Sn=50)]
        campi(s, 'modCC', sc_on=True, sc_S=95, sc_L=200, onCab=True, onKT=True, ipMethod='C')

    @caso('cc29_punti_rete_MT_senza_trasformatore', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Linea MT 1', tipo='uni', S=95, L=800, x=0.12), cav(desc='Linea MT 2', tipo='uni', mat='Al', S=50, L=1500, x=0.13)]
        ccm(s)['motori'] = [mot(P=800, U=20000, klr=5.5)]
        campi(s, 'modCC', onTr=False, UnQ=20000, IkQ=16, IkQmin=9, cfac=1.10, cfacMin=1.00, sc_on=True, sc_S=95, sc_L=350, onCab=True, onMot=True)

    @caso('cc30_punti_fornitura_monofase', ['modCC'])
    def _(s):
        ccm(s)['cavi'] = [cav(desc='Dorsale', S=6, L=20), cav(desc='Presa', S=2.5, L=15, te=160)]
        campi(s, 'modCC', gridPreset='cei_mono', gridMode='Ik', IkQ=6, UnQ=230, rxGrid=0.98, onTr=False, onCab=True, sc_on=True, sc_S=16, sc_L=25)

    @caso('cc31_punti_trasformatore_BT_BT', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='Isolamento', S=100, uk=4, pcu=1.75, uhv=400, ulv=230, vg='Dyn', kin=14, tau=0.15)]
        ccm(s)['cavi'] = [cav(desc='Dorsale', S=95, L=42, te=160, Sn=50), cav(desc='Terminale', S=10, L=30, te=160, Sn=10)]
        campi(s, 'modCC', IkQ=20, IkQmin=12, UnQ=400, rxGrid=0.5, sc_on=True, sc_S=95, sc_L=80, onCab=True)

    @caso('cc32_punti_primario_e_secondario_del_trasformatore', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(hvcab=True, hvmat='Al', hvS=50, hvL=40, hvte=180, hascab=True, cS=240, cL=15, cn=2, cte=140, cSn=120)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2, Sn=120), cav(desc='Dorsale', S=95, L=42, te=160, Sn=50)]
        ccm(s)['motori'] = [mot(P=90), mot(desc='Motore 2', P=30, klr=7.5, tmin=0.05)]
        campi(s, 'modCC', sc_on=True, sc_mat='Al', sc_S=95, sc_L=350, sc_te=200, onCab=True, onMot=True, IkQmin=8)

    # ---- tensione nominale della rete nel punto di guasto ----
    # Esempio di IEC TR 60909-4, art. 5: trasformatori da 410 V di targa su rete a 400 V. Le sezioni danno esattamente le resistenze
    # per chilometro dell'esempio; le sezioni N/PE e i rapporti X0/X danno le impedenze omopolari dell'esempio:
    # L1 R0 = 3,7 R e X0 = 1,81 X · L2 4,23 R e 1,21 X · L3 3 R e 4,46 X · linea aerea L4 2 R e 3 X.
    # Attesi dal rapporto tecnico: I″k 34,12 kA e ip 69,07 kA alle sbarre, 6,94 kA e 10,36 kA a fine linea; I″k1 34,98 kA e 4,83 kA.
    # Le sezioni N/PE dei cavi di ramo danno le resistenze omopolari dell'esempio (R0 = 3,7 RL e 4,23 RL).
    @caso('cc33_esempio_IEC_TR_60909_4_rete_BT', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='T1', S=630, uk=4, pcu=6.5, uhv=20000, ulv=410, hascab=True, cmat='Cu', cS=240.506494, cL=10, cn=2, cx=0.079, cSn=267.229438, ckx0=1.81),
                                   tr(desc='T2', S=400, uk=4, pcu=4.6, uhv=20000, ulv=410, hascab=True, cmat='Al', cS=141.403846, cL=4, cn=2, cx=0.068, cSn=131.334841, ckx0=1.21)]
        ccm(s)['cavi'] = [cav(desc='L3', S=68.335793, L=20, x=0.087, Sn=102.50369, kx0=4.46), cav(desc='L4', S=49.99730, L=50, x=0.297, Sn=149.9919, kx0=3)]
        campi(s, 'modCC', gridMode='Ik', IkQ=10, UnQ=20000, rxGrid=0.1, onKT=True, ipMethod='C', ccTk=0.06, onCab=True)

    # Esempio di IEC TR 60909-4, art. 6: rete a 6 kV alimentata da due trasformatori 33/6,3 kV, motori asincroni sulle sbarre.
    # Attesi dal rapporto tecnico: senza motori I″k 14,74 kA; motori I″kM 2,54 + 2,24 kA, ipM 6,27 + 5,53 kA; Ib 17,04 kA.
    @caso('cc34_esempio_IEC_TR_60909_4_rete_MT_con_motori', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc=d, S=15000, uk=15, pcu=90, uhv=33000, ulv=6300, hvcab=True, hvmat='Cu', hvS=185.19, hvL=4850, hvn=1, hvx=0.1) for d in ('T1', 'T2')]
        ccm(s)['motori'] = [mot(desc='M1', P=5000, U=6000, eta=0.833333, klr=4, rx=0.1, poles=2, tmin=0.10)] + \
                           [mot(desc='M2-%d' % i, P=1000, U=6000, eta=0.78125, klr=5.5, rx=0.1, poles=1, tmin=0.10) for i in (1, 2, 3)]
        campi(s, 'modCC', gridMode='Ik', IkQ=13.12, UnQ=33000, rxGrid=0.1, cfac=1.10, cfacMin=1.00, onKT=True, ipMethod='C', onMot=True)

    # Lo stesso esempio dell'art. 6 con il metodo B: i rami in parallelo hanno R/X sotto 0,3, quindi il fattore 1,15 non si applica
    # (IEC 60909-0, 8.1.2 b). Atteso dal rapporto tecnico: ip senza motori 37,03 kA con κ = 1,78.
    @caso('cc38_esempio_IEC_TR_60909_4_rete_MT_picco_metodo_B', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc=d, S=15000, uk=15, pcu=90, uhv=33000, ulv=6300, hvcab=True, hvmat='Cu', hvS=185.19, hvL=4850, hvn=1, hvx=0.1) for d in ('T1', 'T2')]
        campi(s, 'modCC', gridMode='Ik', IkQ=13.12, UnQ=33000, rxGrid=0.1, cfac=1.10, cfacMin=1.00, onKT=True, ipMethod='B')

    # Due trasformatori piccoli in parallelo: R/X dei rami da 0,3 in su, il fattore 1,15 resta
    @caso('cc39_due_trasformatori_da_250_kVA_metodo_B_con_1_15', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='T1', S=250, uk=4, pcu=3.25), tr(desc='T2', S=250, uk=4, pcu=3.25)]
        campi(s, 'modCC', onKT=True, ipMethod='B')

    # Cavi di ramo con il conduttore di ritorno a sezione piena e ridotta, più motori nel fase-terra
    @caso('cc40_cavo_di_ramo_con_ritorno_e_motori_nel_fase_terra', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='T1', S=1000, uk=6, pcu=10.5, hascab=True, cS=240, cL=30, cn=3, cSn=240),
                                   tr(desc='T2', S=630, hascab=True, cS=240, cL=45, cn=2, cSn=120, cte=160)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2, Sn=120), cav(desc='Dorsale', S=95, L=42, te=160, Sn=50)]
        ccm(s)['motori'] = [mot(P=160, klr=6.5), mot(desc='Motore 2', P=75, klr=7, poles=2)]
        campi(s, 'modCC', onKT=True, ipMethod='B', onCab=True, onMot=True)

    # Due rami in parallelo, uno con il cavo senza la sezione N/PE: nella sequenza zero entra solo l'altro
    @caso('cc41_due_rami_uno_senza_N_PE', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(desc='T1', S=800, uk=6, pcu=8.5, hascab=True, cS=240, cL=20, cn=2),
                                   tr(desc='T2', S=800, uk=6, pcu=8.5, hascab=True, cS=185, cL=20, cn=2, cSn=95)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2, Sn=120)]
        campi(s, 'modCC', onKT=True, onCab=True)

    # File salvato con una versione fino alla 0.1.24, con la scheda «Guasto fase-terra» attiva: si apre con l'avviso e
    # con i campi N/PE vuoti, quindi il fase-terra è calcolato solo ai morsetti del trasformatore
    @caso('cc42_file_precedente_con_scheda_fase_terra', ['modCC'], grezzo=True)
    def _(s):
        t = tr(hascab=True, cS=240, cL=12, cn=3); t.pop('cSn', None); t.pop('ckx0', None)
        ccm(s)['trasformatori'] = [t]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2), cav(desc='Dorsale', S=95, L=42, te=160)]
        for c in ccm(s)['cavi']: c.pop('Sn', None); c.pop('kx0', None)
        campi(s, 'modCC', onCab=True, onLE=True, le_mat='Cu', le_S=50, le_L=60, le_n=1, le_x=0.08, le_te=160, le_RE=0.02)

    @caso('cc35_secondario_a_420_V_rete_a_400_V', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(ulv=420, hvcab=True, hvS=50, hvL=40, hascab=True, cS=240, cL=15, cn=2, cSn=120)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2, Sn=120), cav(desc='Dorsale', S=95, L=42, te=160, Sn=50)]
        ccm(s)['motori'] = [mot(P=90), mot(desc='Motore 2', P=30, klr=7.5, tmin=0.05)]
        campi(s, 'modCC', sc_on=True, sc_S=95, sc_L=350, onKT=True, onCab=True, onMot=True)

    @caso('cc36_secondario_a_380_V_rete_a_400_V', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(ulv=380)]
        ccm(s)['cavi'] = [cav(desc='Dorsale', S=95, L=42, te=160, Sn=50)]
        campi(s, 'modCC', onCab=True)

    # la tensione della sorgente prevale sulla targa del primario: sorgente a 15 kV, trasformatore 20 kV / 400 V, al secondario 300 V
    # motori in posizioni diverse (dalla 0.2.16): ognuno contribuisce dal punto a cui è collegato
    @caso('cc46_motori_in_due_posizioni_uno_sul_secondario_uno_a_fine_linea', ['modCC'])
    def _(s):
        campi(s, 'modCC', onCab=True, onMot=True)
        ccm(s)['trasformatori'] = [tr(S=630, hascab=True, cS=150, cL=8, cn=2, cSn=150)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=95, L=25, Sn=95), cav(desc='Linea', S=50, L=30, Sn=50)]
        ccm(s)['motori'] = [mot(desc='Pompa', P=200, klr=6, poles=2, pos=2), mot(desc='Ventilatore', P=90, klr=7, poles=4, eta=0.85)]

    @caso('cc45_tensione_della_sorgente_diversa_dalla_targa_del_primario', ['modCC', 'modCOO', 'modPMT'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=630, uhv=20000, ulv=400)]
        campi(s, 'modFUS', fu_Ik='', fu_ip='', fu_Imin=''); campi(s, 'modCB', cb_Ik='', cb_ip='', cb_Imin='', cb_onInr=True); campi(s, 'modPMT', pm_U='')

    @caso('cc37_tensione_nominale_imposta_690_V', ['modCC'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(ulv=720)]
        ccm(s)['cavi'] = [cav(desc='Montante', S=240, L=18, n=2), cav(desc='Dorsale', S=95, L=42, te=160)]
        ccm(s)['motori'] = [mot(P=55, U=690)]
        campi(s, 'modCC', ccUn=690, onCab=True, onMot=True)

    @caso('cc26_impianto_completo', TUTTI)
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=1000, uk=6, pcu=10.5, kin=10, tau=0.35, hvcab=True, hvS=95, hvL=60, hascab=True, cS=240, cL=12, cn=4, cSn=240),
                                   tr(desc='Trasf. 2', S=1000, uk=6, pcu=10.5, kin=10, tau=0.35, hvcab=True, hvS=95, hvL=75, hascab=True, cS=240, cL=15, cn=4, cSn=240)]
        ccm(s)['cavi'] = [cav(desc='Blindo', tipo='uni', S=300, L=25, n=3, x=0.09, te=160, Sn=150), cav(desc='Partenza', S=120, L=45, te=250, Sn=70)]
        ccm(s)['motori'] = [mot(P=160, klr=6.5), mot(desc='Motore 2', P=75, klr=7, poles=2)]
        campi(s, 'modCC', sc_on=True, sc_S=150, sc_L=300, sc_te=250, onKT=True, ipMethod='C', onCab=True, onMot=True, IkQ=16, IkQmin=10, ccTk=0.5)
        campi(s, 'modFUS', fu_Ik=28, fu_ip=62, fu_Imin=4.2, fu_S=120, fu_onInr=True, fu_onMot=True, fu_tavv=6)
        campi(s, 'modCB', cb_Ik=28, cb_ip=62, cb_Imin=4.2, cb_S=120, cb_onInr=True, cb_inrSide=2, cb_onOvl=True, cb_onMot=True)
        cb(s)['A'] = intr('NZMN4-AX1600', Ir=1440)
        campi(s, 'modPMT', pm_U=15, pm_Ik=16, pm_Ibt=1200, pm_onCb=True, pm_onWth=True)
        campi(s, 'modVK', vk_Ik=28, vk_ip=62, vk_Ith=28.5, Icw=36, tcw=1, Ipk=75.6, Tk=0.5)

    # ============================ FUSIBILI ============================
    @caso('fu01_gG_NH_160_con_corrente_minima', ['modFUS'])
    def _(s): campi(s, 'modFUS', fu_Imin=2, fu_S=50, fu_tmax=5)

    @caso('fu02_due_fusibili_gG_selettivita', ['modFUS'])
    def _(s): campi(s, 'modFUS', fu_onB=True, fu_Ik=12, fu_ip=24, fu_Imin=1.5, fu_S=70)

    @caso('fu03_aM_con_avviamento_motore', ['modCC', 'modFUS'])
    def _(s):
        ccm(s)['motori'] = [mot(P=45, klr=7, poles=2)]; campi(s, 'modCC', onMot=True)
        fu(s)['A'] = fusn('aM · Grandezza 000, 00', 100); campi(s, 'modFUS', fu_onMot=True, fu_tavv=8, fu_Ik=15, fu_ip=30, fu_Imin=1.2, fu_S=35)

    @caso('fu04_cilindrico_gG_32', ['modFUS'])
    def _(s): fu(s)['A'] = fusn('gG · C 10', 32); campi(s, 'modFUS', fu_Ik=6, fu_ip=9, fu_Imin=0.3, fu_S=6, fu_K=115, fu_tmax=0.4)

    @caso('fu05_gTr_per_trasformatore', ['modFUS'])
    def _(s): fu(s)['A'] = fus(264); campi(s, 'modFUS', fu_Ik=20, fu_ip=42, fu_Imin=3, fu_S=240, fu_K=143, fu_onInr=True, fu_inrSide=2)

    @caso('fu06_aR_semiconduttori', ['modFUS'])
    def _(s): fu(s)['A'] = fus(330); fu(s)['B'] = fus(312); campi(s, 'modFUS', fu_onB=True, fu_Ik=30, fu_ip=63, fu_Imin=2, fu_S=95)

    @caso('fu07_serie_D_e_D0', ['modFUS'])
    def _(s): fu(s)['A'] = fus(108); fu(s)['B'] = fus(122); campi(s, 'modFUS', fu_onB=True, fu_Ik=4.5, fu_ip=6.8, fu_Imin=0.25, fu_S=10, fu_tmax=0.4)

    @caso('fu08_media_tensione_24_kV_con_inserzione', ['modFUS'])
    def _(s): fu(s)['A'] = fusn('Un = 24 kV', 40); campi(s, 'modFUS', fu_Ik=12.5, fu_ip=30, fu_Imin=0.2, fu_onInr=True, fu_inrSide=1, fu_S=95, fu_K=143)

    @caso('fu09_media_tensione_12_kV_100_A', ['modFUS'])
    def _(s): fu(s)['A'] = fusn('Un = 12 kV', 100); fu(s)['B'] = fusn('Un = 12 kV', 63); campi(s, 'modFUS', fu_onB=True, fu_Ik=16, fu_ip=40, fu_Imin=0.6)

    @caso('fu10_NH_690_V_cavo_grande', ['modFUS'])
    def _(s): fu(s)['A'] = fusn('gG · Un = 690 V · Grandezza 3', 400); campi(s, 'modFUS', fu_Ik=35, fu_ip=77, fu_Imin=5, fu_S=240, fu_K=143, fu_tmax=0.4)

    @caso('fu11_corrente_oltre_il_potere_di_interruzione', ['modFUS'])
    def _(s): fu(s)['A'] = fus(110); campi(s, 'modFUS', fu_Ik=80, fu_ip=176, fu_Imin=0.05, fu_S=2.5)

    # ============================ INTERRUTTORI ============================
    @caso('cb01_scatolato_termomagnetico', ['modCB'])
    def _(s): campi(s, 'modCB', cb_Imin=3, cb_S=95)

    @caso('cb02_due_interruttori', ['modCB'])
    def _(s): campi(s, 'modCB', cb_onB=True, cb_Ik=12, cb_ip=24, cb_Imin=1.2, cb_S=16)

    @caso('cb03_modulare_residenziale', ['modCB'])
    def _(s): cb(s)['A'] = intr('PLSM-C16/1N-IN') if 'PLSM-C16/1N-IN' in CB else intr('PLSM-C6/1N-IN'); campi(s, 'modCB', cb_U=230, cb_Ik=4.5, cb_ip=6.8, cb_Imin=0.2, cb_S=2.5, cb_tmax=0.4)

    @caso('cb04_elettronico_LSI_regolato', ['modCB'])
    def _(s): cb(s)['A'] = intr('NZMN4-AX1000', Ir=900); campi(s, 'modCB', cb_Ik=22, cb_ip=46, cb_Imin=6, cb_S=240, cb_K=143, cb_onOvl=True)

    @caso('cb05_aperto_con_trasformatore_da_1000_kVA', ['modCC', 'modCB'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=1000, uk=6, pcu=10.5, kin=10, tau=0.35)]
        cb(s)['A'] = intr('IZMX16B3-V16F-1') if 'IZMX16B3-V16F-1' in CB else intr('IZMX16B3-V06F-1')
        campi(s, 'modCB', cb_Ik=24, cb_ip=52, cb_Imin=8, cb_S=300, cb_onOvl=True, cb_onInr=True, cb_inrSide=2)

    @caso('cb06_con_fusibile_BT_a_confronto', ['modFUS', 'modCB'])
    def _(s): fu(s)['A'] = fusn('gG · Un = 500 V · Grandezza 02, 2', 250); campi(s, 'modCB', cb_onFus=True, cb_Imin=2)

    @caso('cb07_con_fusibile_MT_riportato', ['modFUS', 'modCB'])
    def _(s): fu(s)['A'] = fusn('Un = 17,5 kV', 40); campi(s, 'modCB', cb_onFus=True, cb_Imin=4)

    @caso('cb08_salvamotore_con_avviamento', ['modCC', 'modCB'])
    def _(s):
        ccm(s)['motori'] = [mot(P=7.5, klr=7.5, poles=2, eta=0.88)]; campi(s, 'modCC', onMot=True)
        cb(s)['A'] = intr('PKZM0-20'); campi(s, 'modCB', cb_onMot=True, cb_tavv=6, cb_Ik=10, cb_ip=17, cb_Imin=0.4, cb_S=4)

    @caso('cb09_trasformatore_in_resina_e_inserzione', ['modCC', 'modCB'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(S=400, uk=6, pcu=5.5, tt='secco', kin=10, tau=0.25)]
        cb(s)['A'] = intr('NZMN3-AE630'); campi(s, 'modCB', cb_onOvl=True, cb_onInr=True, cb_inrSide=2, cb_Ik=9.5, cb_ip=20, cb_Imin=3)

    # tensione di esercizio scritta a mano: prevale su quella del punto
    @caso('cb10_tensione_690_V', ['modCB'])
    def _(s): cb(s)['A'] = intr('NZMH2-4-A80-SVE'); campi(s, 'modCB', cb_U=690, cb_Ik=8, cb_ip=15, cb_Imin=0.8, cb_S=25)

    # spunto del motore visto da un fusibile MT e da un interruttore scelti sul punto di consegna: corrente riportata a 15 kV;
    # campo della tensione vuoto, quindi l'interruttore prende la tensione del punto
    @caso('cb13_spunto_riportato_alla_tensione_del_punto', ['modCC', 'modFUS', 'modCB'])
    def _(s):
        ccm(s)['motori'] = [mot(P=200)]
        campi(s, 'modCC', onMot=True); campi(s, 'modFUS', fu_onMot=True); campi(s, 'modCB', cb_onMot=True)
        s['moduli']['modFUS']['punto'] = 0; cb(s)['punto'] = 0

    # ---- coordinamento protezioni BT (dalla 0.2.1): correnti dal punto, fusibile MT riportato alla BT, una sola famiglia ----
    @caso('co01_correnti_automatiche_dal_punto', ['modCC', 'modCOO'])
    def _(s): campi(s, 'modFUS', fu_Ik='', fu_ip='', fu_Imin=''); campi(s, 'modCB', cb_Ik='', cb_ip='', cb_Imin='')

    @caso('co02_fusibile_MT_sul_punto_di_consegna_e_interruttore_BT', ['modCC', 'modCOO'])
    def _(s):
        fu(s)['A'] = fusn('Un = 24 kV', 40); s['moduli']['modFUS']['punto'] = 0
        campi(s, 'modFUS', fu_Ik='', fu_ip='', fu_Imin='', fu_onInr=True); campi(s, 'modCB', cb_Ik='', cb_ip='', cb_Imin='')

    # elenco libero (dalla 0.2.3): tre interruttori in posizioni diverse, nessun fusibile, due interruttori riportati nelle protezioni MT
    @caso('co04_tre_interruttori_in_posizioni_diverse_senza_fusibili', ['modCC', 'modCOO', 'modPMT'])
    def _(s):
        M = s['moduli']
        ccm(s)['cavi'] = [cav(L=40, S=95)]; campi(s, 'modCC', onCab=True)
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin'): M['modCB']['campi'].pop(k, None)
        M['modFUS']['elenco'] = []
        for m in M.values():
            for k in ('fu_UA', 'fu_IkA', 'fu_ipA', 'fu_IminA'): (m.get('campi') or {}).pop(k, None)
        M['modCB']['elenco'] = ['A', 'B', 'C']; cb(s)['B'] = intr('NZMN1-A100'); cb(s)['C'] = intr('FAZ-C32/3')
        M['modCB']['punti'] = {'A': 1, 'B': 2, 'C': 2}; campi(s, 'modCB', cb_IkC=5)
        M['modPMT']['dispositivi'] = ['cbA', 'cbC']

    # trasformatori in parallelo (dalla 0.2.14): ogni ramo ha i suoi punti (da 100 in su: secondario e fine del cavo al secondario di ogni trasformatore)
    @caso('co10_due_trasformatori_in_parallelo_con_un_interruttore_per_ramo', ['modCC', 'modCOO', 'modVK'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, hascab=True, cS=150, cL=8, cn=2, cSn=150), tr(S=630, hascab=True, cS=150, cL=8, cn=2, cSn=150)]
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin', 'fu_Ik', 'fu_ip', 'fu_Imin'):
            for m in M.values(): (m.get('campi') or {}).pop(k, None)
        M['modFUS']['elenco'] = ['A']; M['modFUS']['punti'] = {'A': 0}
        M['modCB']['elenco'] = ['A', 'B']; cb(s)['B'] = intr('NZMN1-A100'); M['modCB']['punti'] = {'A': 101, 'B': 103}   # fine del cavo al secondario di ogni trasformatore
        M['modVK']['campi'].update({'vk_Ik': '', 'vk_ip': '', 'vk_Ith': '', 'vk_cutoff': ''}); M['modVK']['derivatoDa'] = 'p1'   # il parallelo dei trasformatori: picco condizionato dagli interruttori dei rami

    @caso('co11_tre_trasformatori_diversi_rientro_dagli_altri_rami_piu_alto_della_corrente_del_ramo', ['modCC', 'modCOO', 'modVK'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, hascab=True, cS=150, cL=8, cn=2, cSn=150), tr(S=630, hascab=True, cS=150, cL=8, cn=2, cSn=150), tr(S=1000, hascab=True, cS=240, cL=8, cn=2, cSn=240)]
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin', 'fu_Ik', 'fu_ip', 'fu_Imin'):
            for m in M.values(): (m.get('campi') or {}).pop(k, None)
        M['modFUS']['elenco'] = ['A']; M['modFUS']['punti'] = {'A': 0}
        M['modCB']['elenco'] = ['A', 'B']; cb(s)['B'] = intr('NZMN1-A100'); M['modCB']['punti'] = {'A': 101, 'B': 105}   # fine del cavo al secondario dei trasformatori 1 e 3
        M['modVK']['campi'].update({'vk_Ik': '', 'vk_ip': '', 'vk_Ith': '', 'vk_cutoff': ''}); M['modVK']['derivatoDa'] = 'p1'   # il parallelo dei trasformatori: picco condizionato dagli interruttori dei rami

    # corrente condizionata (dalla 0.2.14): a valle di un dispositivo limitatore il picco è quello lasciato passare
    @caso('co12_interruttore_a_fine_cavo_al_secondario_condiziona_i_punti_a_valle', ['modCC', 'modCOO', 'modVK'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, hvcab=True, hvL=30, hascab=True, cS=150, cL=8, cn=2, cSn=150)]
        campi(s, 'modCC', onCab=True, sc_on=True, sc_tipo='mt', sc_mat='Al', sc_S=185, sc_L=300, sc_n=1, sc_x=0.12, sc_te=160)
        ccm(s)['cavi'] = [cav(S=95, L=25), cav(S=50, L=30)]
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin', 'fu_Ik', 'fu_ip', 'fu_Imin'):
            for m in M.values(): (m.get('campi') or {}).pop(k, None)
        M['modFUS']['elenco'] = ['A']; M['modFUS']['punti'] = {'A': 0}
        M['modCB']['elenco'] = ['A']; M['modCB']['punti'] = {'A': 4}
        M['modVK']['campi'].update({'vk_Ik': '', 'vk_ip': '', 'vk_Ith': '', 'vk_cutoff': ''}); M['modVK']['derivatoDa'] = 'p6'

    @caso('co13_parallelo_con_dispositivi_sul_primario_sul_secondario_e_a_fine_cavo', ['modCC', 'modCOO'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, hvcab=True, hvL=30, hascab=True, cS=150, cL=8, cn=2, cSn=150), tr(S=630, hvcab=True, hvL=30, hascab=True, cS=150, cL=8, cn=2, cSn=150)]
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin', 'fu_Ik', 'fu_ip', 'fu_Imin'):
            for m in M.values(): (m.get('campi') or {}).pop(k, None)
        M['modFUS']['elenco'] = ['A']; fu(s)['A'] = fusn('Un = 24 kV', 40); M['modFUS']['punti'] = {'A': 100}   # sul primario del trasformatore 1
        M['modCB']['elenco'] = ['A', 'B']; cb(s)['B'] = intr('NZMN1-A100'); M['modCB']['punti'] = {'A': 102, 'B': 104}   # fine cavo al secondario T1, secondario T2

    # collegamenti tra moduli (dalla 0.2.4): quadro derivato da un interruttore, guasto a terra MT dai dati delle protezioni MT
    @caso('co05_quadro_derivato_da_un_interruttore_e_guasto_a_terra_dalle_protezioni_MT', ['modCC', 'modVK', 'modMT', 'modPMT'])
    def _(s):
        M = s['moduli']
        for k in ('vk_Ik', 'vk_ip', 'vk_Ith', 'vk_cutoff'): M['modVK']['campi'][k] = ''
        M['modVK']['derivatoDa'] = 'cbA'
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin'): M['modCB']['campi'].pop(k, None)
        campi(s, 'modMT', mt_IE='', mt_tF=''); campi(s, 'modPMT', pm_IF=50, pm_tF=0.69)

    # circuito di ogni dispositivo dalla sequenza (dalla 0.2.5): cavo a valle, spunto dei motori, inserzione ai capi del trasformatore
    @caso('co06_circuito_di_ogni_dispositivo_dalla_sequenza', ['modCC', 'modCOO'])
    def _(s):
        M = s['moduli']
        ccm(s)['cavi'] = [cav(L=40, S=95), cav(L=25, S=16)]; campi(s, 'modCC', onCab=True, onMot=True)
        for k in ('cb_Ik', 'cb_ip', 'cb_Imin'): M['modCB']['campi'].pop(k, None)
        for k in ('fu_Ik', 'fu_ip', 'fu_Imin'): M['modFUS']['campi'].pop(k, None)
        M['modCB']['elenco'] = ['A', 'B']; cb(s)['B'] = intr('FAZ-C32/3'); M['modCB']['punti'] = {'A': 1, 'B': 2}
        M['modFUS']['elenco'] = ['A']; fu(s)['A'] = fusn('Un = 24 kV', 40); M['modFUS']['punti'] = {'A': 0}
        campi(s, 'modCB', cb_onMot=True, cb_onInr=True, cb_onOvl=True); campi(s, 'modFUS', fu_onInr=True, fu_onMot=True)

    # cavo BT tra secondario e sbarre (dalla 0.2.7): protetto dal fusibile MT e dalla protezione MT a monte del trasformatore
    @caso('co07_cavo_al_secondario_protetto_dal_dispositivo_a_monte_del_trasformatore', ['modCC', 'modCOO', 'modPMT'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, hascab=True, cS=150, cL=8, cn=2)]
        for k in ('fu_Ik', 'fu_ip', 'fu_Imin'): M['modFUS']['campi'].pop(k, None)
        M['modFUS']['elenco'] = ['A']; fu(s)['A'] = fusn('Un = 24 kV', 40); M['modFUS']['punti'] = {'A': 0}
        campi(s, 'modPMT', pm_Ibt=590, pm_IbtMin=500)

    # guasto BT visto dal lato MT (dalla 0.2.9): fase-terra con il fattore del gruppo; con Yyn anche il bifase
    @caso('co08_cavo_al_secondario_guasto_fase_terra_visto_dal_primario_Dyn', ['modCC', 'modCOO', 'modPMT'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, hascab=True, cS=150, cL=8, cn=2, cSn=150)]
        for k in ('fu_Ik', 'fu_ip', 'fu_Imin'): M['modFUS']['campi'].pop(k, None)
        M['modFUS']['elenco'] = ['A']; fu(s)['A'] = fusn('Un = 24 kV', 40); M['modFUS']['punti'] = {'A': 0}
        campi(s, 'modPMT', pm_Ibt=590, pm_IbtMin=300)

    @caso('co09_cavo_al_secondario_guasti_bifase_e_fase_terra_con_gruppo_Yyn', ['modCC', 'modCOO', 'modPMT'])
    def _(s):
        M = s['moduli']
        ccm(s)['trasformatori'] = [tr(S=630, vg='Yyn', hascab=True, cS=150, cL=8, cn=2, cSn=150)]
        for k in ('fu_Ik', 'fu_ip', 'fu_Imin'): M['modFUS']['campi'].pop(k, None)
        M['modFUS']['elenco'] = ['A']; fu(s)['A'] = fusn('Un = 24 kV', 40); M['modFUS']['punti'] = {'A': 0}
        campi(s, 'modPMT', pm_Ibt=590, pm_IbtMin=300)

    @caso('co03_solo_fusibili', ['modCOO'])
    def _(s): campi(s, 'modFUS', fu_onB=True, co_onCb=False, fu_Imin=2)

    @caso('cb11_ABB_termomagnetico_e_elettronico', ['modCB'])
    def _(s): cb(s)['A'] = intr('XT4H 250 TMA 225'); cb(s)['B'] = intr('XT2N 160 Ekip Dip LSI 10'); campi(s, 'modCB', cb_onB=True, cb_Ik=30, cb_ip=63, cb_Imin=1, cb_S=70)

    @caso('cb12_solo_magnetico_e_limitatore', ['modCB'])
    def _(s): cb(s)['A'] = intr('NZMC2-S125'); cb(s)['B'] = intr('CL-PKZ0 + FAZ-C3,5/1'); campi(s, 'modCB', cb_onB=True, cb_Ik=40, cb_ip=84, cb_Imin=2.5, cb_S=35, cb_onOvl=True)

    # ============================ PROTEZIONI MT ============================
    @caso('pm01_neutro_isolato_20_kV', ['modPMT'])
    def _(s): campi(s, 'modPMT', pm_U=20, pm_neu='i', pm_T0=0.17, pm_L00=70, pm_IF=120, pm_Ik=16)

    @caso('pm02_due_protezioni_con_tempo_dipendente', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(), prot(desc='Linea trasformatore', mod='na016', dg=False, tcb=60, tmin=100, ei=4, et=5, etm=10,
                                            on_I1=True, v_I1=0.5, c_I1='IEC_VI', t_I1=0.15, on_I2=True, v_I2=2, c_I2='DT', t_I2=0.2, on_I3=True, v_I3=5, t_I3=0.05, on_E1=True, v_E1=0.02, t_E1=0.2, on_E2=False)]
        campi(s, 'modPMT', pm_Ibt=605, pm_onWth=True)

    @caso('pm03_tre_protezioni_in_ampere_curve_IEC', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(desc='Arrivo', mod='gen', unit='amp', ei=5, et=3, etm=20, tmin=0, on_I1=True, v_I1=120, c_I1='IEC_NI', t_I1=0.2, v_I2=250, t_I2=0.43, v_I3=600, t_I3=0.05, v_E1=2, t_E1=0.38, v_E2=56, t_E2=0.1),
                               prot(desc='Partenza 1', mod='gen', unit='amp', dg=False, ei=5, et=3, etm=20, tmin=0, on_I1=True, v_I1=60, c_I1='IEC_EI', t_I1=0.3, v_I2=200, t_I2=0.2, v_I3=500, t_I3=0.03, v_E1=1.5, t_E1=0.2, on_E2=False),
                               prot(desc='Partenza 2', mod='gen', unit='amp', dg=False, ei=5, et=3, etm=20, tmin=0, on_I1=True, v_I1=40, c_I1='IEC_LTI', t_I1=0.1, on_I2=True, v_I2=150, c_I2='IEC_STI', t_I2=0.3, on_I3=False, on_E1=False, on_E2=False)]
        campi(s, 'modPMT', pm_dt=0.15)

    @caso('pm04_curve_ANSI_RI_RD', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(desc='A', on_I1=True, v_I1=0.8, c_I1='ANSI_EI', t_I1=1, v_I2=3, c_I2='ANSI_VI', t_I2=0.5, on_I3=True, v_I3=8, c_I3='DT', t_I3=0.05),
                               prot(desc='B', dg=False, on_I1=True, v_I1=0.6, c_I1='ANSI_NI', t_I1=2, v_I2=2, c_I2='ANSI_MI', t_I2=1, on_I3=False),
                               prot(desc='C', dg=False, mod='gen', on_I1=True, v_I1=0.5, c_I1='RI', t_I1=0.3, v_I2=1.5, c_I2='RD', t_I2=0.6, on_I3=True, v_I3=4, c_I3='LT_VI', t_I3=0.5, on_E1=True, v_E1=0.03, c_E1='LT_I', t_E1=0.2, on_E2=True, v_E2=0.4, c_E2='LT_EI', t_E2=0.3)]

    @caso('pm05_soglie_direzionali_di_terra', ['modPMT'])
    def _(s): pm(s)['protezioni'] = [prot(on_D1=True, v_D1=0.02, t_D1=0.25, u_D1=5, on_D2=True, v_D2=0.015, t_D2=0.12, u_D2=2, on_E2=False)]; campi(s, 'modPMT', pm_IF=60)

    @caso('pm18_direzionale_neutro_isolato_con_contributo_capacitivo', ['modPMT'])
    def _(s): pm(s)['protezioni'] = [prot(on_D1=True, v_D1=0.02, t_D1=0.38, u_D1=5, on_D2=True, v_D2=0.02, t_D2=0.1, u_D2=2)]; campi(s, 'modPMT', pm_neu='i', pm_IF=120, pm_IC=3.2)

    @caso('pm19_direzionale_settore_errato_e_67N_mancante', ['modPMT'])
    def _(s): pm(s)['protezioni'] = [prot(on_D1=True, v_D1=0.02, t_D1=0.38, u_D1=5, a_D1='60–300'), prot(desc='Linea', dg=False, on_D2=True, v_D2=0.02, t_D2=0.1, a_D2='settore')]; campi(s, 'modPMT', pm_IF=50, pm_IC=4)

    @caso('pm20_direzionale_oltre_la_taratura_del_distributore', ['modPMT'])
    def _(s): pm(s)['protezioni'] = [prot(on_D1=True, v_D1=0.03, t_D1=0.5, u_D1=6, on_D2=True, v_D2=0.02, t_D2=0.1, u_D2=2, a_D2='60–130')]; campi(s, 'modPMT', pm_DcT=0.45, pm_DiA='60–120', pm_DiT=0.17)

    @caso('pm06_senza_fasce_di_tolleranza', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(), prot(desc='Linea', dg=False, v_I2=2, t_I2=0.25, v_I3=5, t_I3=0.05, v_E1=0.02, t_E1=0.2, on_E2=False)]
        campi(s, 'modPMT', pm_onTol=False)

    @caso('pm07_interruttori_BT_e_tenuta', ['modCC', 'modCB', 'modPMT'])
    def _(s):
        campi(s, 'modCB', cb_onB=True); campi(s, 'modPMT', pm_onCb=True, pm_onWth=True, pm_Ibt=605)
        pm(s)['protezioni'] = [prot(), prot(desc='Linea', dg=False, v_I2=1.6, t_I2=0.2, v_I3=5, t_I3=0.05, v_E1=0.02, t_E1=0.2, on_E2=False)]

    @caso('pm08_fusibile_MT_a_confronto', ['modFUS', 'modPMT'])
    def _(s): fu(s)['A'] = fusn('Un = 17,5 kV', 63); campi(s, 'modPMT', pm_onFus=True, pm_Ibt=605)

    @caso('pm09_due_trasformatori_uno_escluso_e_blocco_armonico', ['modCC', 'modPMT'])
    def _(s):
        ccm(s)['trasformatori'] = [tr(), tr(desc='Trasf. 2', S=1000, uk=6, pcu=10.5, kin=10, tau=0.35), tr(desc='Trasf. 3', S=400, uk=4, pcu=4.6, tt='secco', kin=10, tau=0.25)]
        pm(s)['trasformatoriEsclusi'] = [2]; pm(s)['trasformatore'] = 1
        pm(s)['protezioni'] = [prot(h2=True, v_I2=1.2, t_I2=0.3)]; campi(s, 'modPMT', pm_onWth=True)

    @caso('pm10_senza_distributore_e_senza_inserzione', ['modPMT'])
    def _(s): pm(s)['protezioni'] = [prot(dg=False, mod='na016', tmin=100, ei=4, et=5, etm=10, on_I1=True, v_I1=1, c_I1='IEC_STI', t_I1=0.4)]; campi(s, 'modPMT', pm_onDSO=False, pm_onInr=False, pm_IF=0)

    @caso('pm11_tarature_oltre_i_limiti', ['modPMT'])
    def _(s): pm(s)['protezioni'] = [prot(v_I2=3.2, t_I2=0.6, v_I3=7.5, t_I3=0.1, v_E1=0.04, t_E1=0.5, v_E2=0.9, t_E2=0.2)]

    @caso('pm12_correnti_minime_viste_dalla_protezione', ['modPMT'])
    def _(s): campi(s, 'modPMT', pm_Ik=11.6, pm_IkMin=9.75, pm_Ibt=602, pm_IbtMin=544)

    @caso('pm13_correnti_minime_sotto_le_soglie', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(v_I2=2.4, t_I2=0.5, v_I3=6, t_I3=0.12)]
        campi(s, 'modPMT', pm_Ik=12.5, pm_IkMin=0.2, pm_Ibt=380, pm_IbtMin=150, pm_onTol=False)

    # ---- limite del distributore con la I> a tempo dipendente ----
    DSO_I1 = dict(pm_U=15, pm_L1=59, pm_K1=0.12, pm_A1=0.02, pm_B1=0.14, pm_L2=250, pm_T2=0.5, pm_L2p=104, pm_L3=600, pm_T3=0.12,
                  pm_L0=2, pm_T0=0.45, pm_L00=56, pm_T00=0.17, pm_Ik=1.4, pm_IkMin=1.2, pm_IF=40)
    NA016 = dict(mod='na016', inp=150, ienp=100, unit='mult', tcb=70, tmin=100, ei=4, et=5, etm=10, on_I1=False, v_I1=1, c_I1='IEC_VI', t_I1=1, on_I2=True, v_I2=0.6, t_I2=0.43,
                 on_I3=True, v_I3=4, t_I3=0.05, on_E1=True, v_E1=0.02, t_E1=0.38, on_E2=True, v_E2=0.56, t_E2=0.1)

    @caso('pm14_limite_con_I1_rispettato_senza_I1', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(**NA016)]; campi(s, 'modPMT', **DSO_I1)

    @caso('pm15_limite_con_I1_soglia_I2_troppo_alta', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(**dict(NA016, v_I2=1.6))]; campi(s, 'modPMT', **DSO_I1)

    @caso('pm16_limite_con_I1_curva_dipendente_impostata', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(mod='gen', inp=150, ienp=100, unit='amp', tcb=70, tmin=0, ei=5, et=3, etm=20, on_I1=True, v_I1=59, c_I1='IEC_NI', t_I1=0.12,
                                    on_I2=True, v_I2=250, t_I2=0.43, on_I3=True, v_I3=600, t_I3=0.05, on_E1=True, v_E1=2, t_E1=0.38, on_E2=True, v_E2=56, t_E2=0.1)]
        campi(s, 'modPMT', **dict(DSO_I1, pm_L2p=0))

    @caso('pm17_limite_con_I1_curva_troppo_lenta', ['modPMT'])
    def _(s):
        pm(s)['protezioni'] = [prot(mod='gen', inp=150, ienp=100, unit='amp', tcb=70, tmin=0, ei=5, et=3, etm=20, on_I1=True, v_I1=59, c_I1='IEC_NI', t_I1=0.2,
                                    on_I2=True, v_I2=250, t_I2=0.43, on_I3=True, v_I3=600, t_I3=0.05)]
        campi(s, 'modPMT', **dict(DSO_I1, pm_L2p=0))

    # ============================ VERIFICA QUADRO ============================
    @caso('vk01_tenuta_insufficiente', ['modVK'])
    def _(s): campi(s, 'modVK', vk_Ik=35, vk_ip=77, vk_Ith=36, Icw=25, tcw=1, Ipk=52.5, Tk=1)

    @caso('vk02_guasto_breve_e_tcw_3_s', ['modVK'])
    def _(s): campi(s, 'modVK', vk_Ik=30, vk_ip=66, vk_Ith=31, Icw=25, tcw=3, Ipk=52.5, Tk=0.3)

    @caso('vk03_con_picco_limitato', ['modVK'])
    def _(s): campi(s, 'modVK', vk_Ik=50, vk_ip=110, vk_Ith=50, Icw=20, tcw=1, Ipk=40, vk_cutoff=16, Tk=0.2)

    @caso('vk04_con_corrente_condizionata', ['modVK'])
    def _(s): campi(s, 'modVK', vk_Ik=42, vk_ip=92, vk_Ith=42, Icw=0, Ipk=0, Icc=50, Tk=1)

    # ============================ GUASTO A TERRA MT ============================
    @caso('mt01_impianto_di_terra_globale', ['modMT'])
    def _(s): campi(s, 'modMT', mt_global=True)

    @caso('mt02_corrente_elevata_tempo_breve', ['modMT'])
    def _(s): campi(s, 'modMT', mt_IE=150, mt_tF=0.5, mt_RE=2, mt_r=1)

    @caso('mt03_fattore_di_riduzione', ['modMT'])
    def _(s): campi(s, 'modMT', mt_IE=300, mt_tF=0.17, mt_RE=0.8, mt_r=0.6)

    @caso('mt04_tempo_lungo_resistenza_alta', ['modMT'])
    def _(s): campi(s, 'modMT', mt_IE=50, mt_tF=10.01, mt_RE=3.5, mt_r=1)

    @caso('mt05_tempi_intermedi', ['modMT'])
    def _(s): campi(s, 'modMT', mt_IE=75, mt_tF=0.73, mt_RE=1.6, mt_r=0.85)

    # ============================ RELAZIONI RAPIDE ============================
    @caso('re01_partenza_dal_picco', ['modREL'])
    def _(s): s['moduli']['modREL']['datoDiPartenza'] = 'ipk'; campi(s, 'modREL', lk_ipk=105, r_mode='ik', r_rx=0.1, r_ip=80, n_mode='i', n_ipk=73.5, s_mode='icw', s_i=20, s_t=0.5, i2t_mode='I', i2t_val=4e8, i2t_t=0.5)

    @caso('re02_partenza_dalla_energia', ['modREL'])
    def _(s): s['moduli']['modREL']['datoDiPartenza'] = 'i2t'; campi(s, 'modREL', lk_i2t=1.6e9, lk_t=1, r_mode='ip', r_rx=0.5, r_ik=40, n_mode='ipk', n_i=40, s_mode='t', s_icw=31.5, s_i=50, i2t_mode='t', i2t_I=31.5, i2t_val=9.9e8)

    @caso('re03_partenza_dalla_Icw', ['modREL'])
    def _(s): s['moduli']['modREL']['datoDiPartenza'] = 'icw'; campi(s, 'modREL', lk_icw=50, lk_tcw=3, r_rx=0.07, r_ik=65, n_i=8, s_mode='i', s_icw=16, s_t=0.2, i2t_I=6, i2t_t=0.1)

    # ============================ RISCHIO DA FULMINE ============================
    for k in LPEX:
        @caso('lp_' + k, ['modLP'])
        def _(s, k=k): s['moduli']['modLP'] = copy.deepcopy(LPEX[k])

    @caso('lp_casa_con_protezioni', ['modLP'])
    def _(s):
        d = copy.deepcopy(LPEX['casa']); d['name'] = 'Casa con LPS e SPD'; d['st'].update({'PLPS': 0.05, 'bondNet': True}); d['site'].update({'NG': 4})
        s['moduli']['modLP'] = d

    @caso('lp_ospedale_isolato_in_altura', ['modLP'])
    def _(s):
        d = copy.deepcopy(LPEX['ospedale']); d['name'] = 'Ospedale isolato'; d['st'].update({'CD': 2, 'H': 25}); d['site'].update({'NG': 1.5})
        s['moduli']['modLP'] = d

    # ---- scrittura dei casi: ogni stato è aperto nel programma e risalvato, così il file è quello che il programma produce
    os.makedirs(os.path.join(QUI, 'casi'), exist_ok=True)
    for f in os.listdir(os.path.join(QUI, 'casi')):
        if f.endswith('.json') and not SOLO: os.remove(os.path.join(QUI, 'casi', f))
    elenco = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for nome, moduli, f, grezzo in CASI:
            if SOLO and not nome.startswith(SOLO): continue
            s = copy.deepcopy(BASE); f(s)
            p = await b.new_page(viewport={'width': 1300, 'height': 900}); err = []
            p.on('pageerror', lambda e: err.append(str(e))); p.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
            await p.goto('file://' + HTML); await p.wait_for_timeout(600)
            rep = await p.evaluate('([t])=>{ const r=allOpenText(t,"caso.json"); return r?{ok:r.ok,skip:r.skip,miss:r.miss}:null; }', [json.dumps(s)])
            await p.wait_for_timeout(300)
            out = copy.deepcopy(s) if grezzo else json.loads(await p.evaluate(SALVA)); out.pop('salvato', None)
            json.dump({'nome': nome, 'moduli': moduli, 'stato': out}, open(os.path.join(QUI, 'casi', nome + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            nota = ''
            if not rep or rep['skip'] or rep['miss'] or err: nota = f"  ATTENZIONE: {rep} {err}"
            print(f'{nome:58s} {",".join(m[3:] for m in moduli)}{nota}')
            elenco.append(nome); await p.close()
        await b.close()
    print(len(elenco), 'casi scritti in', os.path.join(QUI, 'casi'))

asyncio.run(main())
