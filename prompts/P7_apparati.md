# P7 — Commenti alle soluzioni e metadati

**Orchestratore:** Gemini 4 Neon (o Argon) · **Esecutori:** Gemini 4 Hydrogen · **Sessione:** nuova · **Parametri:** nessuno

## Per l'orchestratore
Leggi `CONVENZIONI.md` §8. Piano: un sub-agente per ogni gruppo di 4-5 capitoli (al massimo 3 in parallelo) che scrive i
commenti dei propri capitoli, e un sub-agente per i metadati. Dopo il lavoro controlla a campione (tre esercizi, uno
facile e due avanzati) che il commento corrisponda al codice della soluzione di riferimento; se non corrisponde rimanda
il gruppo al sub-agente. Non scrivere tu i file.

## Istruzioni per il sub-agente dei commenti (capitoli assegnati)
Leggi `CONVENZIONI.md`, `stato/macro_scaletta.json` (glossario) e i blueprint `stato/blueprint/capNN.json` dei capitoli
assegnati (esercizi e `soluzione_riferimento` oppure `soluzione_file`).

Per ogni capitolo scrivi `docente/commenti/capNN.json`: un oggetto JSON `{ "id_esercizio": "commento" }` con UNA voce per
ogni esercizio con `"verificabile": true` (chiave = `id`, es. `"10.3"`). Ogni commento (50-180 parole, in italiano) e'
per il docente e spiega:
- l'idea della soluzione di riferimento (leggila: il commento deve corrispondere a quel codice);
- come procedere e perche' funziona (per i capitoli avanzati: strutture dati, possesso della memoria, casi limite);
- gli errori piu' probabili degli studenti;
- come riconoscere una soluzione corretta anche se diversa.
**Non riscrivere il codice** (lo inserisce lo script, identico al blueprint): al massimo nomi di variabili, funzioni o file
tra apici inversi. Usa i termini del glossario.

## Istruzioni per il sub-agente dei metadati
Scrivi `apparati/metadati.json`:
```json
{
  "titolo": "...",
  "sottotitolo": "...",
  "descrizione": "120-180 parole che presentano il libro a studenti e docenti",
  "parole_chiave": ["C", "programmazione", "..."],
  "livello": "dal principiante assoluto all'autonomia in C",
  "requisiti_software": "un compilatore C con supporto allo standard C23 (per esempio GCC 14 o successivo, Clang 18 o successivo) e un editor di testo o un IDE a scelta"
}
```
`parole_chiave`: da 8 a 12. Descrivi solo cio' che c'e' nella macro-scaletta: non inventare caratteristiche.

## Non fare
Non modificare altri file. Non inserire codice nei commenti. Non generare l'indice analitico ne' le soluzioni (le generano
gli script).

## Messaggio finale (orchestratore)
Formato di `CONVENZIONI.md` §7.
