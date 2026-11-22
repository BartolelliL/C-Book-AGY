# P2B — Coerenza dei blueprint tra loro

**Orchestratore:** Gemini 4 Neon (o Argon) · **Esecutori:** Gemini 4 Hydrogen (famiglia diversa da chi ha scritto i
blueprint: Claude Sonnet 5.5) · **Sessione:** nuova · **Parametri:** nessuno

## Per l'orchestratore
Leggi `CONVENZIONI.md` §8. I blueprint sono molti e lunghi: NON leggerli tutti. Lavora cosi':
1. Leggi `stato/riepilogo_blueprint.md` (generato dallo script: per ogni capitolo obiettivi, concetti, funzioni, regole,
   esercizi, piu' una sezione "Segnali automatici") e la voce dei capitoli in `stato/macro_scaletta.json`
   (`registro`, `glossario`).
2. Individua i sospetti secondo la lista "Cosa controllare". Per ogni sospetto assegna un sub-agente (Hydrogen, al massimo
   3 in parallelo) che legge i soli blueprint coinvolti, ne verifica la fondatezza e, se la correzione e' locale e sicura,
   la applica ai file `stato/blueprint/capNN.json` coinvolti (un sub-agente per capitolo: mai due sulla stessa cartella).
3. Un ultimo sub-agente consolidatore scrive `stato/coerenza_blueprint.json` con tutti i problemi trovati.
4. Dopo ogni modifica a un blueprint esegui (o fai eseguire) `python3 scripts/libro.py controlla-bp N` sul capitolo toccato.
Non scrivere tu i file.

## Cosa controllare
1. **Duplicati**: lo stesso concetto introdotto (`concetti_introdotti`) in due capitoli, o esercizi quasi identici.
2. **Dipendenze mancanti**: un capitolo usa (negli esempi, nelle regole, nelle soluzioni) qualcosa che nessun capitolo
   precedente introduce; un `concetti_richiesti` che nessuno introduce prima.
3. **Glossario**: termini diversi dal glossario, uso di `sinonimi_vietati`, termine usato prima del suo capitolo.
4. **Difficolta'**: salti bruschi tra capitoli consecutivi (vedi le fasce in `PROGRAMMA.md`).
5. **Copertura**: obiettivi della macro-scaletta non coperti da nessuna sotto-sezione o esercizio; il traguardo del libro
   (tabella hash generica, progetto finale) e' preparato dai capitoli giusti?
6. **Correttezza delle regole**: enunciati di `regole` e firme di `funzioni_usate` sbagliati rispetto allo standard C23.
7. **Progetto finale**: usa solo concetti dei capitoli precedenti?

## Formato dell'output `stato/coerenza_blueprint.json` (JSON valido)

```json
{
  "verdetto": "corretto",
  "problemi": [
    {
      "id": "c1",
      "capitoli": [3, 5],
      "gravita": "alta",
      "tipo": "duplicato",
      "descrizione": "Il concetto 'precedenza degli operatori' e' introdotto sia nel cap. 3 sia nel cap. 5.",
      "correzione_proposta": "Rimuoverlo dal cap. 5 e lasciare solo un rinvio.",
      "applicata": true
    }
  ]
}
```

- `verdetto`: `ok` (nessun problema), `corretto` (problemi trovati e TUTTI corretti), `da_decidere` (almeno uno richiede
  una scelta dell'utente).
- `tipo`: `duplicato`, `dipendenza_mancante`, `glossario`, `difficolta`, `sovrapposizione_esercizi`, `copertura`,
  `correttezza`, `progetto`.

## Quando si puo' correggere da soli
SOLO se la correzione e' locale ai file `stato/blueprint/capNN.json` e non cambia registro, glossario o macro-scaletta (es.:
sostituire un termine, togliere un concetto duplicato, riscrivere una regola sbagliata, cambiare un esercizio). Allora
modifica il blueprint e metti `"applicata": true`. Se serve cambiare la macro-scaletta o fare una scelta didattica: NON farlo,
metti `"applicata": false` e `"verdetto": "da_decidere"`.

## Non fare
Non riscrivere interi blueprint senza motivo. Non toccare la macro-scaletta. Non scrivere testo del libro.

## Messaggio finale (orchestratore)
Formato di `CONVENZIONI.md` §7, piu' il numero di problemi trovati / corretti / da decidere.
