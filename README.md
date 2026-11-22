# Calcoli elettrici

Programma per il calcolo delle correnti di cortocircuito e per le verifiche che ne discendono, in impianti di bassa e media tensione.

È **una sola pagina HTML**: si scarica, si apre con un doppio clic e funziona senza installazione e senza collegamento a internet. I dati restano sul computer.

> Strumento di supporto al predimensionamento. Non sostituisce il calcolo di progetto né le verifiche di targa dei costruttori.

## Come si usa

1. Apri [`Calcoli_elettrici.html`](Calcoli_elettrici.html) e scaricalo con **Download raw file**.
2. Fai doppio clic sul file: si apre nel browser (Chrome, Edge, Firefox o Safari recenti).
3. Descrivi l'impianto nel primo modulo: i risultati si aggiornano a ogni modifica.

Il lavoro si salva con **Salva tutto** in un file `.json` e si riapre con **Apri tutto…**. Ogni modulo esporta una relazione in **PDF** e un foglio **Excel** con le formule.

## I moduli

| Modulo | A che cosa serve |
|---|---|
| Impianto | I componenti in sequenza: sorgente, trasformatori, linee, motori, fusibili, interruttori |
| Calcolo corrente di cortocircuito | Correnti di guasto in ogni punto, massime e minime (IEC 60909) |
| Progettazione protezioni MT | Relè 50/51, 51N, 67N, selettività e tarature richieste dal distributore |
| Verifica guasto a terra MT | Tensione totale di terra e sicurezza delle persone (CEI EN 50522) |
| Coordinamento protezioni BT | Fusibili e interruttori sugli stessi grafici, scelti accanto alle curve, con le verifiche di ogni dispositivo |
| Verifica cortocircuito quadri | Tenuta al cortocircuito del quadro (IEC 61439) |
| Verifica rischio da fulmine | Valutazione del rischio (CEI EN IEC 62305-2) |
| Relazioni tra grandezze di corrente | Conversioni tra Icc, Icw, Ipk, I²t |

I moduli di media tensione compaiono solo con fornitura in MT.

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
