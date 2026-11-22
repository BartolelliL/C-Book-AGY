# P2B — Coerenza dei blueprint tra loro

**Modello:** Gemini 4 Argon (ragionamento alto): un modello DIVERSO da quello che ha scritto i blueprint (Neon) ·
**Sessione:** nuova · **Parametri:** nessuno

I blueprint sono molti e lunghi: NON leggerli tutti. Lavora per sospetti, partendo da un riepilogo.

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi `stato/riepilogo_blueprint.md` (generato dallo script: per ogni capitolo obiettivi, concetti, funzioni, regole,
   esercizi, piu' una sezione "Segnali automatici") e da `stato/macro_scaletta.json` il `registro` e il `glossario`.
3. Individua i sospetti secondo "Cosa controllare". Poi leggi SOLO i blueprint `stato/blueprint/capNN.json` coinvolti, uno
   alla volta, e verifica che il sospetto sia fondato.

## Cosa controllare
1. **Duplicati**: lo stesso concetto introdotto (`concetti_introdotti`) in due capitoli, o esercizi quasi identici.
2. **Dipendenze mancanti**: un capitolo usa (negli esempi, nelle regole, nelle soluzioni) qualcosa che nessun capitolo
   precedente introduce; un `concetti_richiesti` che nessuno introduce prima.
3. **Glossario**: termini diversi dal glossario, uso di `sinonimi_vietati`, termine usato prima del suo capitolo.
4. **Difficolta'**: salti bruschi tra capitoli consecutivi (vedi le fasce in `PROGRAMMA.md`).
5. **Copertura**: obiettivi della macro-scaletta non coperti da nessuna sotto-sezione o esercizio; il traguardo del libro
   (tabella hash generica, progetto finale) e' preparato dai capitoli giusti?
6. **Correttezza**: enunciati di `regole` e firme di `funzioni_usate` sbagliati rispetto allo standard C23.
7. **Progetto finale**: usa solo concetti dei capitoli precedenti?

## Correzioni
Puoi correggere SOLO se la correzione e' locale ai file `stato/blueprint/capNN.json` e non cambia registro, glossario o
macro-scaletta (sostituire un termine, togliere un concetto duplicato, riscrivere una regola sbagliata, cambiare un
esercizio). Dopo ogni modifica esegui `python3 scripts/libro.py controlla-bp N` sul capitolo toccato e correggi gli errori.
Se serve cambiare la macro-scaletta o fare una scelta didattica: NON farlo, segnalalo come `da_decidere`.

## Output: `stato/coerenza_blueprint.json` (JSON valido)

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

- `verdetto`: `ok` (nessun problema), `corretto` (problemi trovati e TUTTI corretti), `da_decidere` (almeno uno richiede una
  scelta dell'utente: in tal caso `"applicata": false` per quel problema).
- `tipo`: `duplicato`, `dipendenza_mancante`, `glossario`, `difficolta`, `sovrapposizione_esercizi`, `copertura`,
  `correttezza`, `progetto`.

## Non fare
Non riscrivere interi blueprint senza motivo. Non toccare la macro-scaletta. Non scrivere testo del libro.

## Messaggio finale
Formato di `CONVENZIONI.md` §7, piu' il numero di problemi trovati / corretti / da decidere.
