# P6 — Revisione di coerenza globale sull'intero libro

**Modello:** Gemini 4 Argon (ragionamento alto) · **Sessione:** nuova · **Parametri:** nessuno

Lavori sui digest (`stato/digest/capNN.md`, uno per capitolo, scritti con P6D) e poi verifichi i sospetti sui testi
originali. NON leggere i capitoli per intero. NON modificare il manoscritto: scrivi solo il rapporto.

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi `stato/macro_scaletta.json` (capitoli, glossario) e TUTTI i digest `stato/digest/cap*.md`.
3. Confrontali cercando i problemi di "Cosa cercare". Per ogni sospetto, annota capitoli e file coinvolti
   (`manoscritto/capNN/NN_KK.md`).
4. Per ogni sospetto leggi SOLO i file coinvolti (uno alla volta), conferma o scarta, e se conferma prepara la patch.

## Cosa cercare
1. **Ridondanze** tra capitoli lontani (stessa spiegazione, esercizi quasi uguali).
2. **Incoerenze terminologiche**: stesso concetto con nomi diversi, termini del glossario usati male o prima del loro
   capitolo, `sinonimi_vietati`.
3. **Salti di difficolta'** tra capitoli o sezioni consecutive (confronta con le fasce di `PROGRAMMA.md`).
4. **Rinvii** sbagliati o a capitoli che non trattano quel tema.
5. **Contraddizioni tecniche** tra capitoli (una regola enunciata in due modi, una semplificazione smentita dopo senza
   dirlo).
6. **Stile del codice** incoerente tra capitoli.
7. **Progetto finale e tabella hash**: i capitoli precedenti preparano davvero quanto serve? Il progetto usa solo concetti
   gia' spiegati?
8. **Traguardo del libro**: il lettore, a fine libro, sa davvero scrivere da solo la tabella hash generica come tipo opaco?

## Output: `audit/globale_audit.json`
Stesso formato di `CONVENZIONI.md` §6 (senza `capitolo` e senza `ciclo`). Regole:
- Ogni patch riguarda UN file di `manoscritto/capNN/`. Per una ridondanza tra due capitoli proponi la modifica nel capitolo
  PIU' TARDO (sostituisci la spiegazione ripetuta con una frase e un rinvio).
- `old_text` ESATTO e unico nel file; `new_text` la correzione minima. `certezza` `alta` solo se sei sicuro.
- Massimo 30 patch in totale, solo cio' che conta. Se serve una riscrittura: `old_text` e `new_text` a `null`.
- Niente aggiunte di contenuti nuovi. Se non trovi problemi: `{"verdetto": "ok", "patch": []}`.

## Non fare
Non modificare il manoscritto. Non rifare i controlli di compilazione. Non leggere i capitoli per intero.

## Messaggio finale
Formato di `CONVENZIONI.md` §7, piu' il numero di patch per capitolo e i 3 problemi piu' gravi trovati.
