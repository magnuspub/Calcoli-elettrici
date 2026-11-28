# Calcoli elettrici

Programma per il calcolo delle correnti di cortocircuito e per le verifiche che ne discendono, in impianti di bassa e media tensione.

È **una sola pagina HTML**: si scarica, si apre con un doppio clic e funziona senza installazione e senza collegamento a internet. I dati restano sul computer.

> Strumento di supporto al predimensionamento. Non sostituisce il calcolo di progetto né le verifiche di targa dei costruttori.

## Come si usa

1. Apri [`Calcoli_elettrici.html`](Calcoli_elettrici.html) e scaricalo con **Download raw file**.
2. Fai doppio clic sul file: si apre nel browser (Chrome, Edge, Firefox o Safari recenti).
3. Descrivi l'impianto nello **schema** a sinistra: con **+ Aggiungi** si inseriscono trasformatori, linee, interruttori, fusibili e motori; un clic su un oggetto apre la sua finestra. I risultati si aggiornano a ogni modifica.
4. Scegli il modulo dalle schede in alto.

Il lavoro si salva con **Salva** in un file `.json` e si riapre con **Apri**. Il modulo aperto si esporta con **PDF** (la relazione) ed **Excel** (un foglio con le formule). Passando con il mouse su un nome compare la sua descrizione; **Descrizioni** mostra anche le spiegazioni estese.

## I moduli

| Parte | A che cosa serve |
|---|---|
| Schema impianto | I componenti in sequenza, nella barra a sinistra: sorgente, trasformatori, linee, interruttori, fusibili, motori. Ogni oggetto ha la sua finestra; per ogni linea anche i dati di portata e caduta di tensione |
| Cortocircuito | Correnti di guasto in ogni punto, massime e minime (IEC 60909) |
| Coordinamento | Fusibili e interruttori sugli stessi grafici, con le verifiche di ogni dispositivo e della linea che protegge: portata, sovraccarico, guasto a fondo linea, caduta di tensione (CEI 64-8, CEI-UNEL 35024/1, 35026, 35023) |
| Protezioni MT | Relè 50/51, 67, 51N, 67N, selettività e tarature richieste dal distributore; importazione delle tarature da progetti PCM600 (REF615) e da file NA016 |
| Guasto a terra MT | Tensione totale di terra e sicurezza delle persone (CEI EN 50522) |
| Verifica quadro | Tenuta al cortocircuito del quadro (IEC 61439) |
| Rischio da fulmine | Valutazione del rischio (CEI EN IEC 62305-2) |
| Relazioni | Conversioni tra Icc, Icw, Ipk, I²t |

Le schede di media tensione compaiono solo con fornitura in MT.

## Che cosa c'è nel repository

| File o cartella | Contenuto |
|---|---|
| `Calcoli_elettrici.html` | Il programma |
| `Gestione_curve.html` | Strumento per consultare e ampliare la banca dati di fusibili e interruttori |
| `Manutenzione.html` | Strumento per chi sviluppa: indice del codice ed esecuzione delle prove |
| `versione.json` | Versione corrente e novità, letta dalla ricerca degli aggiornamenti |
| `icone/` | Icone per l'installazione come app |
| `prove/` | Casi campione e prove di regressione (vedi [`prove/LEGGIMI.md`](prove/LEGGIMI.md)) |

## Documentazione

La guida completa, con formule, norme e storico delle versioni, è nella [wiki](https://github.com/magnuspub/Calcoli-elettrici/wiki).

## Lingua

Il programma e la documentazione sono solo in italiano; altre lingue non sono supportate.

## Autore

Federico Magnani
