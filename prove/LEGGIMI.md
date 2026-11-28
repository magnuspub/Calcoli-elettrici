# Prove di regressione di Calcoli elettrici

Servono a capire se una versione nuova di `Calcoli_elettrici.html` dà gli stessi risultati di quella di riferimento.

## Cosa c'è

- `casi/` — 119 casi campione nel formato di «Salva» (si possono aprire anche a mano con «Apri»):
  44 di cortocircuito, 11 di fusibili, 13 di interruttori, 13 di coordinamento delle protezioni BT, 20 di protezioni MT,
  4 di verifica quadro, 5 di guasto a terra MT, 3 di relazioni tra grandezze, 5 di rischio da fulmine.
  I primi 77 sono stati salvati con la versione 0.1.15: riaperti dalle versioni successive provano anche che
  i file vecchi danno gli stessi risultati.
  Dalla 0.1.25 il guasto fase-terra si calcola dalla sezione N/PE e dal rapporto X0/X dei cavi: i casi con cavi e
  fase-terra sono stati riscritti con quei campi, mentre `cc42` resta nel formato precedente, con la scheda «Guasto fase-terra», per
  provare l'apertura dei file vecchi.
  Dalla 0.2.0 la pagina è divisa in moduli numerati: sorgente, trasformatori, linee, motori, fusibili e interruttori sono
  componenti del modulo «Impianto», e i grafici di fusibili e interruttori stanno nel modulo «Coordinamento protezioni».
  I casi più vecchi sono scritti sulla struttura di prima (componenti nel cortocircuito, coppia A/B, correnti e sezioni a
  mano): il programma li apre ancora e li converte, quindi continuano a valere. I casi `co…` usano la struttura nuova:
  elenchi liberi, posizione di ogni dispositivo, circuito preso dalla sequenza, collegamenti tra moduli.
- `riferimento.json` — i risultati della versione di riferimento per ogni caso, più l'impronta della banca dati
  (tabelle, tre fusibili per famiglia, due interruttori per serie).
- `prova.py` — apre ogni caso nel programma, raccoglie i risultati e li confronta con il riferimento.
- `impronta.js` — che cosa viene raccolto da ogni modulo. Per i casi di fusibili e interruttori raccoglie da solo anche il
  modulo «Coordinamento protezioni».
- `banca.js` — che cosa viene raccolto della banca dati.
- `genera_casi.py` — come sono stati costruiti i casi; per aggiungerne si usa `--solo prefisso`, che scrive
  solo i casi nuovi e lascia gli altri come sono.
- `fumetti.py` — controllo a parte, non legato al riferimento: apre tutte le nuvolette delle descrizioni a varie
  larghezze di finestra e verifica che compaiano, con il testo giusto, dentro la finestra.

## Senza Python

Le stesse prove si eseguono anche da `Manutenzione.html`, scheda «Prove»: i casi girano nel browser e vengono
confrontati con `riferimento.json`. Manca solo il ricalcolo dei fogli Excel con LibreOffice, che resta a `prova.py --excel`.

## Cosa viene confrontato

Per ogni modulo del caso:

- **risultati**: i riquadri, le verifiche con il loro esito, le tabelle e le note mostrate a schermo, e i valori
  interni a dieci cifre (correnti, impedenze, curve, margini); per il cortocircuito anche le correnti massime
  e minime di ogni punto della catena;
- **esportazioni**: il contenuto dei fogli Excel (compreso il foglio «Punti») e del PDF; con `--excel` anche
  i valori dei fogli ricalcolati da LibreOffice, cioè le formule esportate rifatte da un altro programma;
- **aspetto**: legende e geometria dei grafici.

## Come si usa

    python3 prove/prova.py                 confronto con il riferimento (circa 40 secondi)
    python3 prove/prova.py --excel         anche il ricalcolo dei fogli Excel
    python3 prove/prova.py altro.html      confronto di un altro file
    python3 prove/prova.py --solo cc,pm    solo i casi il cui nome inizia così
    python3 prove/prova.py --aggiorna --excel    riscrive il riferimento

Servono Python con Playwright e Chromium; per `--excel` anche LibreOffice e openpyxl.

Il comando elenca i casi diversi con il valore di riferimento e quello attuale, e termina con 1 se cambiano
risultati o valori.

## Le nuvolette delle descrizioni

Dalla 0.2.26 ogni descrizione compare passando sul nome, in un'unica nuvoletta che il programma mette vicino al
nome. Le «i» restano nella pagina senza ingombro, per la tastiera: `fumetti.py` le mette a fuoco una per una e
misura dove finisce la nuvoletta, confrontando due immagini della pagina (prima e con la nuvoletta aperta). Segnala
quelle che non compaiono, quelle con un testo diverso da quello della «i», quelle che escono dalla finestra e
quelle che allargano la pagina.

    python3 prove/fumetti.py                                   larghezze abituali (da 320 a 1400 px)
    python3 prove/fumetti.py --largh 390                       solo una larghezza
    python3 prove/fumetti.py --caso prove/casi/cc40_....json   apre prima un caso, per avere più campi a video
    python3 prove/fumetti.py --salva /tmp/fumetti              salva l'immagine di quelli che non vanno

Servono Python con Playwright, Chromium e Pillow. Con un caso ricco di righe (trasformatori, cavi, motori) i
nuvolette controllate sono circa 150; senza, una decina in meno. Il comando termina con 1 se almeno una non va.

Va eseguito dopo le modifiche all'aspetto della pagina: `prova.py` non se ne accorge, perché confronta i risultati
e non la posizione delle nuvolette.

## Quando cambia qualcosa

Una differenza non è per forza un errore: può essere una correzione voluta. In quel caso si controlla che le
differenze siano solo quelle attese e si riscrive il riferimento con `--aggiorna --excel`, nella stessa modifica
che cambia il programma.
