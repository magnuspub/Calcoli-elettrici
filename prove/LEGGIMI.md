# Prove di regressione di Calcoli elettrici

Servono a capire se una versione nuova di `Calcoli_elettrici.html` dà gli stessi risultati di quella di riferimento.

## Cosa c'è

- `casi/` — 77 casi campione nel formato di «Salva tutto» (si possono aprire anche a mano con «Apri tutto»):
  26 di cortocircuito, 11 di fusibili, 12 di interruttori, 11 di protezioni MT, 4 di verifica quadro,
  5 di guasto a terra MT, 3 di relazioni rapide, 5 di rischio da fulmine.
- `riferimento.json` — i risultati della versione di riferimento per ogni caso, più l'impronta della banca dati
  (tabelle, tre fusibili per famiglia, due interruttori per serie).
- `prova.py` — apre ogni caso nel programma, raccoglie i risultati e li confronta con il riferimento.
- `impronta.js` — che cosa viene raccolto da ogni modulo.
- `genera_casi.py` — come sono stati costruiti i casi; va rieseguito solo per aggiungerne o cambiarli.

## Cosa viene confrontato

Per ogni modulo del caso:

- **risultati**: i riquadri, le verifiche con il loro esito, le tabelle e le note mostrate a schermo, e i valori
  interni a dieci cifre (correnti, impedenze, curve, margini);
- **esportazioni**: il contenuto del foglio Excel e del PDF; con `--excel` anche i valori dei fogli ricalcolati
  da LibreOffice, cioè le formule esportate rifatte da un altro programma;
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

## Quando cambia qualcosa

Una differenza non è per forza un errore: può essere una correzione voluta. In quel caso si controlla che le
differenze siano solo quelle attese e si riscrive il riferimento con `--aggiorna --excel`, nella stessa modifica
che cambia il programma.
