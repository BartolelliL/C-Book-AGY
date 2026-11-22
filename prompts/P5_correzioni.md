# P5 — Correzioni mirate (residui dell'audit ed errori dei controlli)

**Modello:** Gemini 4 Neon · **Sessione:** nuova · **Parametri:** `CAPITOLI=lista` e (`SORGENTE=capitolo` `CICLO=C`)
oppure `SORGENTE=globale`

N e' il capitolo in corso.

**Lavoro sui capitoli:** se `CAPITOLI` contiene piu' capitoli, lavorali UNO ALLA VOLTA nell'ordine: finisci e controlla un capitolo prima di passare al successivo e non rileggere i capitoli gia' chiusi. Lavori da solo: non delegare ad altri agenti.

Se dichiari `non_risolti` non decidere tu: la scelta spetta all'utente.

## Istruzioni (per ogni capitolo N)

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi `stato/blueprint/capNN.json` e i file di `manoscritto/capNN/`.
3. Individua i compiti:
   - `SORGENTE=capitolo`: `audit/capNN_cC_residui.json` (campo `residui`) ed eventuali errori in
     `stato/verifica_capNN.json`.
   - `SORGENTE=globale`: in `audit/globale_residui.json` SOLO i residui il cui `file` sta in `manoscritto/capNN/`, ed
     eventuali errori in `stato/verifica_capNN.json`.
4. Se dopo un precedente intervento restano errori in `stato/verifica_capNN.json`, correggi anche quelli.

## Come lavorare su ogni residuo
- `motivo_residuo` ti dice perche' non e' stato applicato in automatico.
- Se `certezza` era `media`: verifica TU con attenzione, secondo lo standard C23, se il problema e' reale.
  - Reale e correggibile con sicurezza → correggi con la modifica MINIMA.
  - Non reale o dubbio → NON modificare e mettilo tra i `non_risolti` spiegando perche': lo decidera' l'utente.
- Se `old_text`/`new_text` erano nulli: riscrivi solo il passaggio interessato.
- Se `old_text` non era univoco o non combaciava: trova tu il punto giusto nel file.
- Per gli errori di `verifica_capNN.json`: correggili nel punto indicato.
- Rispetta sempre le convenzioni (formato, marcatori, glossario, progressione, niente soluzioni).
- Non toccare nulla che non sia collegato a un residuo o a un errore.

## Controllo finale (obbligatorio)
1. Esegui `python3 scripts/libro.py controlla N` e correggi ogni errore (massimo 4 giri).
2. Scrivi il rapporto:
   - `SORGENTE=capitolo` → `audit/capNN_cC_p5.json`
   - `SORGENTE=globale` → `audit/globale_p5_capNN.json`

```json
{
  "capitolo": 3,
  "ciclo": 1,
  "sorgente": "capitolo",
  "risolti": ["p2", "p5"],
  "non_risolti": [{"id": "p7", "motivo": "perche' non e' un errore / serve una scelta dell'utente"}]
}
```

(`ciclo` assente o `null` per la sorgente globale.)

## Non fare
Non riscrivere sezioni intere "per migliorarle". Non modificare blueprint, macro-scaletta, script, altri capitoli.

## Messaggio finale
Formato di `CONVENZIONI.md` §7.
