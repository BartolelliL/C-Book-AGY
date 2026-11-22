# P6D — Digest dei capitoli (preparazione della revisione globale)

**Modello:** Gemini 4 Hydrogen · **Sessione:** nuova · **Parametri:** `CAPITOLI=lista` (es. `1-4`)

Il libro intero e' troppo lungo per essere riletto in una volta: per la revisione globale (P6) servono dei riassunti
strutturati ("digest"), uno per capitolo. Lavora UN capitolo alla volta, nell'ordine, senza rileggere i precedenti.

## Per ogni capitolo N (NN = N a due cifre)
1. Leggi `CONVENZIONI.md` (una volta sola) e tutti i file di `manoscritto/capNN/`.
2. Scrivi `stato/digest/capNN.md` (400-600 parole) con questa struttura:
   - **Termini definiti** nel capitolo (con la definizione in una riga) e termini del glossario usati.
   - **Concetti spiegati** (elenco puntato).
   - **Esempi e scenari** usati (nomi di variabili ricorrenti, contesti degli esercizi, programmi principali).
   - **Esercizi**: id, titolo, idea in una riga, difficolta' percepita (1-5).
   - **Rinvii**: ogni "(lo vedremo nel capitolo X)" o richiamo a capitoli precedenti, con il numero.
   - **Affermazioni forti** sul linguaggio (regole, divieti, "sempre"/"mai") che altri capitoli potrebbero contraddire.
   - **Stile del codice**: convenzioni effettivamente usate (nomi, formattazione, gestione degli errori).

## Non fare
Non giudicare e non correggere: descrivi soltanto cio' che c'e'. Non modificare il manoscritto. Non eseguire comandi.

## Messaggio finale
Formato di `CONVENZIONI.md` §7.
