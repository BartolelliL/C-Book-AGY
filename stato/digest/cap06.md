# Digest — Capitolo 6: Ripetizioni

## Termini definiti e glossario
- **Ciclo** (*loop*): costrutto di controllo che ripete un blocco di istruzioni finché una condizione rimane vera.
- **Iterazione** (*iteration*): ogni singola esecuzione del corpo di un ciclo.
- **Invariante di ciclo** (*loop invariant*): proprietà logica che vale prima del ciclo e resta vera al termine di ogni iterazione (verificata su inizializzazione, mantenimento e conclusione).
- Altri termini del glossario usati: fine dell'input, comportamento indefinito, contatore, accumulatore, *off-by-one*, ciclo infinito, cicli annidati.

## Concetti spiegati
- Ciclo `while`: controllo in testa (0 o più iterazioni); tre elementi necessari (inizializzazione, condizione di permanenza, aggiornamento verso terminazione).
- Idiomi di lettura fino a fine input: `while (fgets(...) != nullptr)` e `while ((c = getchar()) != EOF)` con `c` di tipo `int` e parentesi obbligatorie per la precedenza tra `=` e `!=`.
- Schemi su sequenze: contatore, accumulatore, minimo/massimo inizializzati al primo elemento valido (`conteggio == 0`), guardia contro 0 elementi prima della media.
- Ciclo `do-while`: controllo in coda (almeno 1 iterazione), `;` finale obbligatorio, visibilità delle variabili della condizione (dichiarate prima di `do`), gestione obbligatoria di `nullptr` su `fgets` per evitare cicli infiniti.
- Ciclo `for`: tre clausole (`inizializzazione; condizione; aggiornamento`), visibilità della variabile di controllo limitata al ciclo, clausole facoltative (`for (;;)` sempre vero).
- Errori tipici del `for`: off-by-one, underflow di contatori `unsigned` decrescenti (`i >= 0`), punto e virgola dopo `while`/`for`, uso di contatori `double` (da evitare: derivare `double` da un contatore intero).
- `break` e `continue`: agiscono solo sul costrutto/ciclo più interno; `continue` nel `for` esegue l'aggiornamento, in `while`/`do-while` salta al test; interazione tra `switch` e ciclo (`break` chiude lo `switch`, `continue` il ciclo).
- Cicli annidati: `R * C` iterazioni, contatori distinti, azzeramento locale, uscita multipla con variabile `bool trovato`.
- Prova di terminazione tramite grandezza decrescente e nota C23 sui cicli infiniti privi di effetti osservabili.

## Esempi e scenari
- **6.1**: conteggio caratteri/righe/cifre (`caratteri`, `righe`, `cifre`) e somma importi (`conteggio`, `totale`, `importo`).
- **6.2**: validazione PIN 100..999 (`pin`, `tentativi`, `valido`).
- **6.3**: tabella Celsius–Fahrenheit con passo `0.2` e primi `n` numeri di Fibonacci (`prec`, `corr`, `prox`).
- **6.4**: lettura campioni sensore con `SENTINELLA = 9999`, `SOGLIA_CRITICA = 500`, `stato`.
- **6.5**: tavola pitagorica `n x n` (`r`, `c`) e MCD con algoritmo di Euclide (`a`, `b`, `resto`).

## Esercizi
- **6.1 — Statistiche delle temperature giornaliere**: leggere temperature `double` fino a `EOF` con `while`, calcolare minima, massima, media e giorni con gelo, gestendo input vuoto. Difficoltà: 2/5.
- **6.2 — Analisi delle cifre di un intero non negativo con `do-while`**: leggere `long long` (`0..1'000'000'000`), estrarre cifre con `% 10` e `/= 10` in `do-while`, calcolare conteggio, somma, massimo e inverso. Difficoltà: 2/5.
- **6.3 — Piano di risparmio mensile con ciclo `for`**: simulare `mesi` mensilità con `for` (`1..mesi`), accumulando interessi e versamenti. Difficoltà: 2/5.
- **6.4 — Carico di un furgone con `break` e `continue`**: leggere pesi con `while`, saltare righe vuote e negativi con `continue`, fermarsi su `0.0` o superamento `CAPACITA_MAX` con `break` registrando la causa. Difficoltà: 3/5.
- **6.5 — Tabella di divisibilità con cicli annidati e invarianti**: stampare griglia `n x n` (`'X'`/`'.'`), contare divisori e primi, trovare numero con più divisori e documentare invarianti. Difficoltà: 3/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 1–5 in apertura; cap. 3 (precedenza operatori, aritmetica modulare `unsigned`, arrotondamento `0.1`); cap. 4 (corto circuito `&&`, `break` in `switch`); cap. 5 (`fgets`, `sscanf`, `getchar`, `EOF`, `nullptr`).
- Rinvii in avanti: cap. 7 (visibilità di blocco delle variabili); cap. 8 (array e indicizzazione `0..n-1`).

## Affermazioni forti
- Con `getchar()` usare sempre `int`, mai `char`.
- Non usare mai una variabile `double` come contatore di un `for`.
- Nei cicli decrescenti fino a `0` usare un tipo con segno (`int`), mai `unsigned`.
- Nei cicli `do-while` di lettura da `stdin` controllare sempre `fgets(...) == nullptr` per evitare cicli infiniti.
- Garantire sempre la terminazione dei cicli (evitare cicli infiniti senza effetti osservabili).

## Stile del codice
- Standard C23: `nullptr`, `bool`/`true`/`false`, `constexpr` (`06_04`, esercizio `6.4`), separatori di cifre (`1'000'000'000` in esercizio `6.2`).
- Gestione errori uniforme su `stderr` con `fprintf` e `EXIT_FAILURE`/`EXIT_SUCCESS` (`<stdlib.h>`), controllo formato `sscanf(..., "... %c", ..., &extra)`.
- Pre-incremento (`++i`, `++conteggio`) usato sistematicamente nei cicli e contatori.
- Commenti sintetici per invarianti e terminazione in `06_05`.
