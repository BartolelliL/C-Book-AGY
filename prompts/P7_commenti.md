# P7 — Commenti alle soluzioni per il docente

**Modello:** Gemini 4 Hydrogen · **Sessione:** nuova · **Parametri:** `CAPITOLI=lista` (es. `1-4`)

Lavora UN capitolo alla volta, nell'ordine, senza rileggere i precedenti.

## Per ogni capitolo N (NN = N a due cifre)
1. Leggi `CONVENZIONI.md` (una volta sola), la voce `glossario` di `stato/macro_scaletta.json` e il blueprint
   `stato/blueprint/capNN.json` (esercizi e `soluzione_riferimento` oppure `soluzione_file`).
2. Scrivi `docente/commenti/capNN.json`: un oggetto JSON `{ "id_esercizio": "commento" }` con UNA voce per ogni esercizio
   con `"verificabile": true` (chiave = `id`, es. `"10.3"`). Ogni commento (50-180 parole, in italiano) e' per il docente e
   spiega:
   - l'idea della soluzione di riferimento (leggila: il commento deve corrispondere a quel codice);
   - come procedere e perche' funziona (per i capitoli avanzati: strutture dati, possesso della memoria, casi limite);
   - gli errori piu' probabili degli studenti;
   - come riconoscere una soluzione corretta anche se diversa.
3. **Non riscrivere il codice** (lo inserisce lo script, identico al blueprint): al massimo nomi di variabili, funzioni o
   file tra apici inversi. Usa i termini del glossario.

## Non fare
Non modificare altri file. Non inserire codice nei commenti. Non generare le soluzioni ne' l'indice (lo fanno gli script).

## Messaggio finale
Formato di `CONVENZIONI.md` §7.
