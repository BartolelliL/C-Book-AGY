# Digest — Capitolo 4: Decisioni

## Termini definiti e glossario
- **flusso di controllo** (*control flow*): ordine con cui vengono eseguite le istruzioni di un programma attraverso selezioni, cicli e chiamate di funzione.
- **valutazione a corto circuito** (*short-circuit evaluation*): proprietà di `&&` e `||` per cui viene valutato sempre prima l'operando sinistro e l'operando destro non viene valutato se l'esito è già determinato.
- **fall-through**: prosecuzione automatica dell'esecuzione da un ramo `case` di uno `switch` al successivo in assenza di `break;`.
- **attributo** (*attribute*): annotazione standard C23 tra doppie parentesi quadre `[[...]]` che fornisce informazioni aggiuntive al compilatore (es. `[[fallthrough]];`).
- **operatore condizionale** (`?:`): unico operatore ternario del C, che valuta una condizione e poi esclusivamente uno dei due rami producendo un valore.
- Altri termini usati: selezioni annidate (*nested*), *dangling else*, guardia, istruzione vuota, punto di sequenza.

## Concetti spiegati
- Costrutto `if`, `else`, catene `if / else if / else` mutuamente esclusive con soglie ordinate; `0` / `0.0` / `false` / `'\0'` falsi, diverso da zero vero; obbligo stilistico delle parentesi graffe per evitare il *dangling else* e gli errori da `;` dopo `if (...)` o `=` al posto di `==`.
- Valutazione a corto circuito di `&&` e `||` (comportamento definito dallo standard C23 con punto di sequenza): uso di guardie a sinistra per prevenire divisione per zero (`n != 0 && somma / n >= 6`) e errori di dominio di `sqrt` (`x >= 0.0 && sqrt(x) > 3.0`); divieto di effetti collaterali nell'operando destro; confronto `double` con `fabs(a - b) <= tol`.
- Costrutto `switch (espressione)` su tipi interi (`int`, `long`, `char`, `bool`), etichette `case` costanti distinte (anche `constexpr` in C23), ramo `default` consigliato, raggruppamento di etichette vuote, `[[fallthrough]];` (C23 vs `/* fallthrough */` in C17/C11), blocchi `{ ... }` nei `case` per variabili locali.
- Operatore condizionale `?:`: differenza tra espressione e istruzione, determinazione del tipo tramite conversioni aritmetiche usuali, precedenza molto bassa (uso obbligatorio delle parentesi in espressioni composte), utilità per `const` e massimo/minimo, divieto di annidamenti lunghi.

## Esempi e scenari
- Variabili ricorrenti: `temperatura`, `sintomi_gravi`, `numero_prove_1..2`, `punti_totali_1..2`, `area`, `giorno`, `livello_abbonamento`, `residente`, `fascia_notturna`, `tariffa_oraria`.
- Programmi guidati: classificazione temperatura corporea (`4.1-a`), medie studenti e `sqrt` con guardie (`4.2-a`), giorni lavorativi e livelli di abbonamento con `switch` e `[[fallthrough]]` (`4.3-a`), tariffa parcheggio con `?:` e `const` (`4.4-a`).

## Esercizi
- **4.1 — Tariffa di spedizione a scaglioni**: `if / else if / else` per peso pacco e `if` annidato per consegna prioritaria. Difficoltà: 2/5.
- **4.2 — Controlli difensivi con valutazione a corto circuito**: guardie su divisione intera per due sensori, equazione di secondo grado con `sqrt` e controllo tensione con `fabs`. Difficoltà: 3/5.
- **4.3 — Biglietteria ferroviaria con `switch` e `[[fallthrough]]`**: due `switch` su `char` (etichette raggruppate maiuscole/minuscole) e su livello servizio con `[[fallthrough]];`. Difficoltà: 3/5.
- **4.4 — Valutazione di una gara di salto in lungo con `?:`**: inizializzazione di sette variabili `const` tramite `?:` con parentesi esplicite e stampa finale con `if / else`. Difficoltà: 3/5.

## Rinvii
- Capitolo 5: lettura di dati dalla tastiera per rendere dinamiche le decisioni (4.99).
- Capitolo 6: cicli nel flusso di controllo (4.1).
- Capitolo 7: chiamate di funzione nel flusso di controllo (4.1).
- Capitolo 12: enumerazioni dentro `switch` (4.3).

## Affermazioni forti
- Ogni ramo di `if` ed `else` va sempre racchiuso tra parentesi graffe anche con una sola istruzione.
- Non inserire effetti collaterali (`++`, `--`, assegnamenti) nell'operando destro di `&&` o `||`.
- Non usare mai `double` o `float` dentro `switch`; `const int` non `constexpr` non è ammessa nelle etichette `case`.
- Non annidare più operatori `?:` in catene lunghe; racchiudere sempre `?:` tra parentesi dentro espressioni aritmetiche o di confronto.

## Stile del codice
- Header in ordine alfabetico (`<math.h>`, `<stdio.h>`).
- Rientro di 4 spazi; `case` rientrati di 4 spazi rispetto a `switch`, istruzioni dei `case` rientrate di altri 4 spazi.
- `const` usata con `?:` per rendere immutabili i valori scelti in base a una condizione.
