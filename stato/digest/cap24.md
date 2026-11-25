# Digest — Capitolo 24: Tecniche avanzate del linguaggio

## Termini definiti e glossario
- **Stringificazione** (`#`) e **concatenazione di token** (`##`): operatori del preprocessore che trasformano un parametro in stringa o fondono due token (con **doppio livello di espansione** per espandere eventuali macro argomento).
- **X-macro**: tecnica del preprocessore che definisce una lista tabellare `LISTA(X)` e la espande più volte con macro `X` diverse per generare in sincronia enum, tabelle e funzioni.
- **Sovraccarico statico**: simulazione del sovraccarico sul tipo a tempo di compilazione combinando `_Generic` (che seleziona solo il nome della funzione) e `inline`.
- **Qualificazione preservata**: uso di `_Generic` con rami distinti `T *` e `const T *` per restituire un puntatore con la stessa qualificazione `const` dell'argomento.
- **Salto non locale** (*non-local jump*): trasferimento del controllo tra frame diversi dello stack tramite `setjmp` e `[[noreturn]] longjmp` (`<setjmp.h>`, `jmp_buf`).
- **Lista intrusiva** (*intrusive list*): lista concatenata circolare con **testa sentinella** i cui puntatori `prev`/`next` sono incorporati nella struct ospitante e recuperati con `offsetof`.
- **Macchina a stati finiti** (*finite-state machine*): modello con stati, eventi, transizioni, azioni con **guardie** e **hook di ingresso** (*on-enter*), implementato con tabella 2D di puntatori a funzione.
- **CRC-8**: codice ridondante ciclico su 8 bit per la verifica di integrità dei frame binari.
- Termini del glossario usati: **campi di bit**, **unione etichettata**, **puntatore a funzione**, **comportamento dipendente dall'implementazione**, **comportamento indefinito**, **perdita di memoria**.

## Concetti spiegati
- Macro multi-istruzione con `do { ... } while (0)` senza `;` finale; macro variadiche con `__VA_ARGS__` e `__VA_OPT__(...)` (C23); X-macro con `#undef` e `static_assert`.
- `_Generic` per selezionare solo la funzione (valutazione unica dell'argomento) e scelta tra `static inline` nell'header vs `inline` nell'header + `extern inline` in un solo `.c`.
- Vincoli C23 di `setjmp`/`longjmp`: contesti sintattici ammessi (`if (setjmp(env) == 0)`), validità del frame, `volatile` sulle variabili locali modificate dopo `setjmp`, tracciamento risorse/arena.
- Liste intrusive circolari (`CONTENITORE_DI` via `offsetof` + `unsigned char *`), appartenenza simultanea a più liste, `LISTA_PER_OGNI_SICURO` per rimozione/free in iterazione.
- Macchine a stati con tabella 2D `static const transizione_t[ST_CONTEGGIO][EV_CONTEGGIO]`, inizializzatori designati, `static_assert` e controllo limiti.
- Campi di bit (`unsigned int`, `signed int`, `bool`, anonimi `: N` e `: 0`) separati dal codec esplicito big-endian a spostamenti/maschere e CRC-8.

## Esempi e scenari
- `24.1-a`: `LISTA_COLORI(X)` espansa in `colore_t`, `COLORI[]`, `e_colore_*`, `AGGIORNA_ESTREMI` (`do-while(0)`), `STAMPA_LOG` (`__VA_OPT__`).
- `24.2-a/b/c` (`stampa_gen`): `ABS_GEN`, `MOSTRA` con `inline`/`extern inline` e `prossimo_int` per valutazione unica.
- `24.3-a`: parser configurazione `ctx_parser_t` su 3 livelli con `volatile int fase` e liberazione di `buf_lavoro`.
- `24.4-a`: lista intrusiva su stack di `sensore_t` con `CONTENITORE_DI` e filtro con `LISTA_PER_OGNI_SICURO`.
- `24.5-a`: tornello automatico a 3 stati e 4 eventi con `TABELLA[ST_CONTEGGIO][EV_CONTEGGIO]`.
- `24.6-a`: `data_ora_bf_t` in 32 bit con `codifica_be` / `decodifica_be`.

## Esercizi
- **24.1 — Registro diagnostico generato con X-macro, `do-while(0)`, `#`/`##` e `__VA_OPT__`**: 2 file (`codici_x.h`, `main.c`) per registro errori con `LISTA_CODICI(X)`. Difficoltà: 4/5.
- **24.2 — Libreria numerica sovraccaricata su più file con `_Generic`, `inline`/`extern inline` e `const`-preservation**: 3 file (`num_gen.h/c`, `main.c`) su `int32_t`, `int64_t`, `double`, `vec2_t` con `ckd_add` saturante. Difficoltà: 4/5.
- **24.3 — Valutatore ricorsivo di espressioni con frame annidati `setjmp`/`longjmp`, `volatile` e pulizia risorse**: 3 file (`errore_jmp.h/c`, `main.c`) con pila di `frame_err_t`. Difficoltà: 5/5.
- **24.4 — Schedulatore di lavori con doppia lista intrusiva circolare basata su `offsetof`**: 3 file (`lista_intr.h/c`, `main.c`) con `lavoro_t` in `lista_tutti` e `coda_pronti`. Difficoltà: 4/5.
- **24.5 — Macchina a stati finiti opaca per sessioni di rete con tabella 2D di puntatori a funzione e guardie**: 3 file (`fsm_sess.h/c`, `main.c`) senza `switch`, con `ON_ENTER` e blocco dopo 3 errori. Difficoltà: 4/5.
- **24.6 — Codec binario portabile per frame di telemetria con intestazione a campi di bit, unione etichettata e CRC-8**: 3 file (`frame_bin.h/c`, `main.c`) con `intestazione_bf_t` e `payload_frame_t`. Difficoltà: 5/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 13 (campi di bit, unioni, `offsetof`, ordine dei byte), cap. 15 (`_Generic`, `static_assert`), cap. 16 (puntatori a funzione, tabelle di dispatch), cap. 17 (liste concatenate), cap. 19 (multi-file, `inline`), cap. 21 (macro con argomenti, `goto cleanup`, `volatile`), cap. 22 (arena, *strict aliasing*).
- Rinvii in avanti: cap. 25 (cache del processore in `24_04.md`).

## Affermazioni forti
- Produrre con `##` un token non valido è UB.
- Omettere `extern inline` in un `.c` per una funzione `inline` non-`static` usata con collegamento esterno causa errore del collegatore.
- `setjmp` fuori dai contesti sintattici consentiti (es. `int rc = setjmp(env);`), `longjmp` verso un frame già ritornato, o leggere una variabile locale non-`volatile` modificata dopo `setjmp` è UB.
- Applicare `CONTENITORE_DI` alla testa sentinella o usare `LISTA_PER_OGNI` durante rimozione/free è UB.
- Nei campi di bit non usare mai `int` semplice (segno dipendente dall'implementazione); non serializzare mai i byte grezzi di una struct a campi di bit con `memcpy`/`fwrite`.

## Stile del codice
- C23 (`[[maybe_unused]]`, `[[noreturn]]`, `__VA_OPT__`, `nullptr`, `bool`, `static_assert`, `= {}`).
- Indentazione a 4 spazi, graffe sempre presenti (salvo un esempio `if/else` senza graffe in `24.1-a` per dimostrare `do-while(0)`), `snake_case` italiano, `inline`/`extern inline` coerenti.
