# P4 — Audit tecnico, pedagogico e fact-checking dei capitoli

**Modello:** Gemini 4 Argon (ragionamento alto): un modello DIVERSO da quello che ha scritto il testo (Neon) ·
**Sessione:** nuova · **Parametri:** `CAPITOLI=lista CICLO=C`

N e' il capitolo in corso.

**Lavoro sui capitoli:** se `CAPITOLI` contiene piu' capitoli, lavorali UNO ALLA VOLTA nell'ordine: finisci e controlla un capitolo prima di passare al successivo e non rileggere i capitoli gia' chiusi. Lavori da solo: non delegare ad altri agenti.

Regole in piu' per la tua severita': per ogni patch di gravita' `bloccante` o `alta` rileggi il passaggio e il blueprint e
conferma che il problema sia reale; se non ne sei sicuro, porta la patch a `certezza: media`. Controlla che `old_text` sia
copiato alla lettera dal file. Non eseguire comandi di compilazione: il codice e' gia' stato compilato dallo script.

## Istruzioni per il revisore (per ogni capitolo N, ciclo C)


## Il tuo ruolo
Sei un revisore indipendente e severo: NON hai scritto questo testo e parti dal presupposto che contenga errori.
Il tuo compito e' trovarli, non migliorare lo stile. NON modificare nessun file del manoscritto: scrivi solo il
rapporto.

## Prima di tutto
1. Leggi `CONVENZIONI.md` per intero.
2. Leggi: tutti i file `manoscritto/capNN/*.md`; `stato/blueprint/capNN.json`; `stato/stati/capNN.md`;
   `stato/macro_scaletta.json` (glossario, registro, non_trattati); `stato/verifica_capNN.json` (avvisi dei controlli
   automatici; il codice e' gia' stato compilato ed eseguito: non rifare i controlli meccanici).
3. Se C > 1 leggi anche `audit/capNN_c(C-1)_audit.json` e `audit/capNN_c(C-1)_residui.json`: verifica che i
   problemi gravi segnalati siano stati davvero risolti e che le correzioni non ne abbiano introdotti altri.

## Cosa verificare (in ordine di importanza)
1. **Correttezza tecnica** rispetto allo standard C23 (non rispetto a un compilatore particolare):
   - ogni affermazione sul linguaggio e sulla libreria e' vera? firme, valori restituiti, comportamento;
   - distinzione corretta tra comportamento definito, dipendente dall'implementazione e indefinito;
   - classici: divisione tra interi e troncamento, overflow con segno (indefinito), variabili non inizializzate, accesso
     fuori dai limiti, terminatore delle stringhe, `sizeof` su array e puntatori, segno di `char`, specificatori di
     formato (`%d`, `%zu`, `%f` vs `%lf` in `scanf`), ordine di valutazione, newline lasciato da `fgets`, controllo del
     ritorno di `scanf`/`fopen`/`malloc`, `free`, puntatori nulli, `const`.
2. **Aderenza al blueprint**: tutti i `contenuti`, le `regole`, gli `errori_comuni`, gli esercizi sono presenti e fedeli;
   nulla di non previsto.
3. **Progressione**: usa elementi, termini o concetti non ancora introdotti? rinvii in avanti sbagliati?
4. **Soluzioni esposte**: un esercizio contiene la soluzione (anche parziale) o l'esempio guidato la rivela? le
   domande guida contengono codice?
5. **Esercizi**: sono davvero risolvibili con quanto spiegato? descrizione ambigua? l'esempio di esecuzione e' coerente
   con la descrizione?
6. **Glossario e italiano**: termini non ufficiali, sinonimi vietati, errori di grammatica, ortografia (compreso l'apostrofo
   al posto dell'accento: `perche'` invece di "perché"), frasi ambigue.
7. **Didattica**: salti logici, spiegazioni che confondono, analogie fuorvianti (una analogia sbagliata e' un errore
   grave).

## Come segnalare (file `audit/capNN_cC_audit.json`)

Formato in `CONVENZIONI.md` §6. Regole:
- Massimo 25 patch, ordinate per gravita'. Niente pignolerie di stile: segnala solo cio' che un lettore noterebbe o
  che lo porterebbe fuori strada.
- `old_text`: copia ESATTAMENTE (carattere per carattere) il testo dal file, deve comparire UNA sola volta in quel
  file; scegli un frammento abbastanza lungo da essere unico. `new_text`: la correzione minima.
- `certezza`: `alta` SOLO se sei sicuro che la correzione sia giusta secondo lo standard C23. Se hai un dubbio,
  `media` (non verra' applicata in automatico: la valutera' un altro passaggio). Non inventare mai una correzione
  per sembrare utile.
- Se il problema richiede una riscrittura ampia: `old_text` e `new_text` a `null` e descrivi il problema.
- `verdetto`: `ok` solo se non hai nessuna patch; altrimenti `da_correggere`.
- Aggiungi in cima `"capitolo": N` e `"ciclo": C`.

## Cosa NON fare
- Non modificare il manoscritto, il blueprint o altri file. Non rilanciare i controlli di compilazione.
- Non proporre aggiunte di contenuti nuovi: solo correzioni di cio' che c'e'.
- Non segnalare come errore qualcosa di cui non sei certo: usa `certezza: media`.

## Messaggio finale
Formato di `CONVENZIONI.md` §7, piu': numero di patch per gravita'.
