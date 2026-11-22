# P6 — Revisione di coerenza globale sull'intero manoscritto

**Orchestratore:** Gemini 4 Neon (o Argon) · **Esecutori:** Gemini 4 Hydrogen · **Sessione:** nuova · **Parametri:** nessuno

Il libro intero e' troppo lungo per essere letto da un solo agente: si lavora per "digest" (riassunti strutturati), poi
si verificano i sospetti sui testi originali.

## Per l'orchestratore
Leggi `CONVENZIONI.md` §8. Piano in tre fasi:
1. **Digest.** Un sub-agente per ogni gruppo di 2-3 capitoli (al massimo 3 in parallelo) legge SOLO i propri capitoli in
   `manoscritto/capNN/` e scrive, per ciascuno, `stato/digest/capNN.md` (400-600 parole, con la struttura qui sotto).
2. **Analisi.** Leggi tu tutti i digest, `stato/macro_scaletta.json` (capitoli, glossario) e confrontali cercando i
   problemi della lista "Cosa cercare". Per ogni sospetto, annota capitoli e file coinvolti.
3. **Verifica e patch.** Per ogni sospetto un sub-agente legge i soli file coinvolti, conferma o scarta, e se conferma scrive
   le patch in `audit/globale/NNN_<nome>.json` (un file per sub-agente, NNN progressivo: 001, 002, ...). Alla fine un
   sub-agente scrive `audit/globale/000_esito.json` con `{"verdetto": "ok", "patch": []}` se non ci sono problemi (o
   `{"verdetto": "da_correggere", "patch": []}` con le patch negli altri file): serve a segnalare che l'audit e' finito.
Non scrivere tu i file e non modificare il manoscritto.

## Struttura del digest `stato/digest/capNN.md`
- **Termini definiti** nel capitolo (con la definizione in una riga) e termini del glossario usati.
- **Concetti spiegati** (elenco puntato).
- **Esempi e scenari** usati (nomi di variabili ricorrenti, contesti degli esercizi, programmi principali).
- **Esercizi**: id, titolo, idea in una riga, difficolta' percepita (1-5).
- **Rinvii**: ogni "(lo vedremo nel capitolo X)" o richiamo a capitoli precedenti, con il numero.
- **Affermazioni forti** sul linguaggio (regole, divieti, "sempre"/"mai") che altri capitoli potrebbero contraddire.
- **Stile del codice**: convenzioni effettivamente usate (nomi, formattazione, gestione errori).

## Cosa cercare (tu, sui digest)
1. **Ridondanze** tra capitoli lontani (stessa spiegazione, esercizi quasi uguali).
2. **Incoerenze terminologiche**: stesso concetto con nomi diversi, termini del glossario usati male o prima del loro
   capitolo, `sinonimi_vietati`.
3. **Salti di difficolta'** tra capitoli o sezioni consecutive (confronta con le fasce di `PROGRAMMA.md`).
4. **Rinvii** sbagliati o a capitoli che non trattano quel tema.
5. **Contraddizioni tecniche** tra capitoli (una regola enunciata in due modi, una semplificazione smentita dopo senza
   dirlo).
6. **Stile del codice** incoerente tra capitoli.
7. **Progetto finale e tabella hash**: i capitoli precedenti preparano davvero quanto serve? Il progetto usa solo
   concetti gia' spiegati?
8. **Traguardo del libro**: il lettore, a fine libro, sa davvero scrivere da solo la tabella hash generica come tipo opaco?

## Formato delle patch (`audit/globale/NNN_<nome>.json`)
Stesso formato di `CONVENZIONI.md` §6 (senza `capitolo` e senza `ciclo`). Regole:
- Ogni patch riguarda UN file di `manoscritto/capNN/`. Per una ridondanza tra due capitoli proponi la modifica nel capitolo
  PIU' TARDO (sostituisci la spiegazione ripetuta con una frase e un rinvio).
- `old_text` ESATTO e unico nel file; `new_text` la correzione minima. `certezza` `alta` solo se sei sicuro.
- Massimo 30 patch in totale, solo cio' che conta. Se serve una riscrittura: `old_text` e `new_text` a `null`.
- Niente aggiunte di contenuti nuovi.

## Non fare
Non modificare il manoscritto. Non rifare i controlli di compilazione. Non leggere tu i capitoli per intero: usa i digest.

## Messaggio finale (orchestratore)
Formato di `CONVENZIONI.md` §7, piu' il numero di patch per capitolo e i 3 problemi piu' gravi trovati.
