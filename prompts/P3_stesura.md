# P3 — Stesura dei capitoli

**Modello:** Gemini 4 Neon · **Sessione:** nuova (meglio un capitolo per sessione) · **Parametri:** `CAPITOLI=lista` (es. `3` o `3-4`)

NN = N a due cifre (es. 03). K = numero della sotto-sezione. N e' il capitolo in corso.

**Lavoro sui capitoli:** se `CAPITOLI` contiene piu' capitoli, lavorali UNO ALLA VOLTA nell'ordine: finisci e controlla un capitolo prima di passare al successivo e non rileggere i capitoli gia' chiusi. Lavori da solo: non delegare ad altri agenti.

## Istruzioni (per ogni capitolo N)

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero: il formato dei file e i marcatori del codice sono OBBLIGATORI.
2. Leggi, nell'ordine:
   - `stato/blueprint/capNN.json` (la tua fonte di verita' per definizioni, regole, firme, esercizi);
   - `stato/stati/capNN.md` (cosa il lettore ha gia' visto e quali elementi puoi usare);
   - `stato/macro_scaletta.json`: solo la voce del capitolo N, il `glossario` e `non_trattati`;
   - `stato/esempio_stile.md` SE esiste: e' un testo gia' approvato dall'utente, imita tono, ritmo e livello di dettaglio
     (non copiarne i contenuti);
   - se N > 1 e esiste: `manoscritto/cap(N-1)/(N-1)_99.md`, solo per la continuita' dell'apertura.
3. Se `stato/verifica_capNN.json` esiste e contiene `errori` (rilancio dopo errori): modalita' correzione. NON riscrivere le
   parti corrette, correggi solo i file e i punti segnalati, poi vai al "Controllo finale".
4. Ripresa: se in `manoscritto/capNN/` esistono gia' dei file, non rifarli (a meno che siano segnalati come errati):
   scrivi solo quelli mancanti.

## Obiettivo
Scrivere in `manoscritto/capNN/` i file `NN_00.md`, `NN_01.md` ... (uno per sotto-sezione del blueprint) e `NN_99.md`,
nel formato ESATTO di `CONVENZIONI.md` §3. Non scrivere altro.

## Come scrivere ogni sotto-sezione (file `NN_KK.md`)
1. **Teoria**: copri TUTTI i punti di `contenuti` della sotto-sezione, e solo quelli. Segui l'ordine didattico di
   `CONVENZIONI.md` §5.1. Definizioni e regole: usa il testo di `concetti_introdotti` e `regole` del blueprint
   (puoi renderlo piu' leggibile ma non cambiarne il significato). Se la regola ha una `nota_standard` (comportamento
   indefinito, dipendente dall'implementazione), dillo chiaramente al lettore.
2. **Esempio guidato**: realizza la descrizione `esempio_guidato`. Programma completo, al massimo 40 righe (80 dal capitolo 13; su piu' file con `gruppo=` e `file=` come in `CONVENZIONI.md` §3.4), con marcatore
   `<!-- cod: id=N.K-a tipo=programma -->`, blocco ```` ```output ```` con l'output ESATTO e, se legge input, blocco
   ```` ```input ````. Poi spiegalo. Usa solo elementi consentiti da `stato/stati/capNN.md`. L'esempio NON deve essere la
   soluzione dell'esercizio della stessa sotto-sezione.
3. **Approfondimento**: solo se `approfondimento` nel blueprint non e' vuoto, come box `> **Approfondimento — ...**`.
4. **Esercizio** (`### Esercizio N.K — Titolo`, oppure `### Progetto N.K — Titolo` per il tipo `progetto`):
   - `**Descrizione**`: parti da `descrizione` del blueprint, senza cambiarne i requisiti.
   - `**Concetti da tenere a mente**`: dal blueprint.
   - `**Domande guida**`: dal blueprint (3 o piu', ognuna con `?`), eventualmente riformulate; mai codice.
   - `**Esempio di esecuzione**`: copia ESATTAMENTE `esempi_io` del blueprint (blocchi ```` ```input ```` e
     ```` ```output ````): i controlli confrontano il testo.
   - Per un progetto, aggiungi l'elenco numerato delle `fasi` del blueprint.
   - NESSUN codice risolutivo: al massimo una `traccia` (tipo=traccia, max 25 righe, con `TODO`).
5. Box `> **Se vieni da Python** — ...` solo se utile (max uno), usando `differenze_python` se presente.
6. Se usi una novita' C23, aggiungi il box `> **C23** ...`.

## `NN_00.md` e `NN_99.md`
- `NN_00.md`: titolo `# Capitolo N — ...`, riquadro obiettivi (dagli `obiettivi` del blueprint), "Ti servono", 2-3 paragrafi
  motivanti. Niente codice.
- `NN_99.md`: `## Riepilogo` (punti chiave), `## Errori comuni` (dal blueprint, spiegati), `## Prima di proseguire`
  (lista di auto-verifica). Rinvii in avanti solo come "(lo vedremo nel capitolo X)".

## Qualita' (autocontrollo mentre scrivi)
- Ogni affermazione tecnica deve essere vera secondo lo standard C23. Se non ne sei sicuro, riformula in modo che
  sia certamente vera.
- Usa SOLO i termini del glossario; mai i `sinonimi_vietati`; niente concetti fuori dal blueprint e dal registro.
- Non spiegare gli stessi concetti piu' volte: se serve richiamare qualcosa di un capitolo precedente, una frase e
  un rinvio.
- Niente riempitivi, niente frasi entusiastiche generiche, niente emoji.

## Controllo finale (obbligatorio)
1. Esegui `python3 scripts/libro.py controlla N`. Legge i file, compila ed esegue ogni programma, confronta gli output e
   controlla progressione, glossario, struttura e soluzioni esposte.
2. Correggi OGNI errore elencato (gli avvisi vanno valutati) e riesegui, fino a esito pulito (massimo 4 giri).
3. Se non puoi eseguire comandi: scrivilo nel messaggio finale; l'utente li lancera'.

## Non fare
- Non modificare il blueprint, la macro-scaletta, gli script o altri capitoli.
- Non inserire soluzioni agli esercizi. Non usare funzioni o sintassi non consentite dal capitolo.

## Messaggio finale
Formato di `CONVENZIONI.md` §7. In DUBBI: affermazioni tecniche di cui non sei certo al 100%.
