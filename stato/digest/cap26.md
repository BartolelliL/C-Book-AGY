# Digest — Capitolo 26: Progetto finale: un interprete per un piccolo linguaggio

## Termini definiti e glossario
- **MiniL**: piccolo linguaggio imperativo progettato nel capitolo (9 parole chiave, commenti `//`, valori `int64_t`, `bool`, `nullo`).
- **Albero di sintassi astratta** (*Abstract Syntax Tree*, AST): rappresentazione ad albero della struttura grammaticale di un programma, costruita dal parser ed eseguita dal valutatore.
- **Analizzatore lessicale** (*lexer*): componente iniziale che trasforma il codice sorgente in una sequenza di **token** (minime unità significative) con coordinate `(riga, col)`, usando `TOK_EOF` come **valore sentinella** e *lookahead* di un carattere.
- **Analizzatore sintattico** (*parser*) a **discesa ricorsiva** (*recursive descent*): componente che verifica la grammatica e costruisce l'AST tramite funzioni corrispondenti alle regole grammaticali.
- **Valutatore**: componente che percorre l'AST ed esegue espressioni e istruzioni su un **ambiente di esecuzione** (*environment*, catena di tabelle associative per ambiti annidati e oscuramento/*shadowing*).
- **Arità**: numero di argomenti attesi da una funzione; **ambito lessicale** (ambiente genitore uguale al globale per funzioni di primo livello) contro *ambito dinamico*.
- **Raccoglitore di memoria automatico** (*garbage collector*): estensione facoltativa a marcatura e scansione su lista intrusiva.
- **Termini del glossario usati**: *unione etichettata*, *allocatore ad arena*, *tabella hash generica come tipo opaco*, *possesso della memoria*, *valutazione a corto circuito*, *compilazione separata*, `goto cleanup`, *puntatori a funzione*, *test automatici*, *sanitizer*, *comportamento indefinito*.

## Concetti spiegati
- Architettura a tre stadi (lexer, parser, valutatore) con dipendenze acicliche su otto moduli (`arena`, `tabella_hash`, `valore`, `lexer`, `parser`, `eval`, `test_fw`, `main`) e struttura unica `errore_t`.
- Unioni etichettate (`valore_t`, `nodo_t`) con controllo obbligatorio dell'etichetta e `static_assert` sulla dimensione; allocatore ad arena (`alignof(max_align_t)`, `ckd_add`, rilascio `O(1)` anche su errore).
- Analizzatore lessicale senza allocazioni sullo heap (viste `inizio`/`len`), cast `(unsigned char)` per `<ctype.h>`, commenti `//`, interi con `ckd_mul`/`ckd_add` e lookahead per operatori a 1-2 caratteri.
- Analizzatore sintattico a discesa ricorsiva su 7 livelli di precedenza, cicli `while` per associatività a sinistra, guardia di profondità (`MAX_PROF_PARSE`) e verifica `TOK_EOF`.
- Valutatore sicuro: `<stdckdint.h>`, controlli preventivi su `-INT64_MIN`, `b == 0`, `INT64_MIN / -1` e `% -1`, corto circuito su `&&`/`||`, ambienti a catena su `tabella_hash_t` (`strdup` + `free`), controllo di flusso (`if`/`else`, `while` con `MAX_PASSI`), funzioni `fn` (`genitore = vm->globale`, `MAX_PROF_CHIAMATE`, flag `in_ritorno`) e predefinite tramite `builtin_fn`.
- Integrazione con `goto cleanup`, cattura output in `out_buf_t`, suite di test automatici con `test_fw.h` e verifica con `-fsanitize=address,undefined`.

## Esempi e scenari
- `26.1-a`/`c`/`d` (`gruppo=ast_demo`: `ast_demo.h`, `ast_demo.c`, `main.c`): `arena_demo_t` su buffer `alignas(max_align_t)`, `nodo_demo_t` per `-(3 + 4 * 2)`, `stampa_prefissa`, `arena_reset`.
- `26.2-a`: lexer didattico su `"var x = 12 + 34; x == 46;"` con `token_t`, `cerca_kw` e `prossimo`.
- `26.3-a`: mini parser su `"10 - 3 - 2"`, `"2 + 3 * 4"` e `"(1 + 2"`.
- `26.4-a`/`b`/`c` (`gruppo=env_demo`: `tab_opaca.h`, `tab_opaca.c`, `main.c`): `ambiente_t` globale e di blocco con shadowing di `x` e aggiornamento di `y`.
- `26.5-a`: `chiama_builtin` (`doppio`, `somma`) e `esegui_ciclo_con_return` con `stato_vm_t`.
- `26.6-a`: `esegui_pipeline` con `goto cleanup` e `VERIFICA_STR` per i numeri primi `<= 20`.

## Esercizi e progetto
- `26.1` — *Costruttore di AST tipizzato su arena con unioni etichettate e verifica dei tipi*: 3 file (`arena_ast.h/c`, `main.c`), `nodo_expr_t` e inferenza ricorsiva (difficoltà: 3/5).
- `26.2` — *Analizzatore lessicale completo per MiniL con coordinate, commenti e controllo di overflow*: 3 file (`lexer_minil.h/c`, `main.c`), token completi (difficoltà: 3/5).
- `26.3` — *Analizzatore sintattico a discesa ricorsiva per espressioni complete e chiamate su arena*: 3 file (`expr_parser.h/c`, `main.c`), 7 livelli e S-espressioni (difficoltà: 4/5).
- `26.4` — *Ambiente lessicale a catena su tabella hash opaca e valutatore sicuro con corto circuito*: 3 file (`tabella_hash.h/c`, `main.c`), comandi `ENTER`/`LEAVE`/`DEF`/`SET`/`GET`/`SHORT_AND` (difficoltà: 4/5).
- `26.5` — *Tabella di funzioni predefinite tramite puntatori a funzione e gestione sicura di chiamate ricorsive e cicli*: 3 file (`builtin.h/c`, `main.c`), `abs`, `min`, `max`, `pot`, `pari`, `FACT`, `WHILE_SUM` (difficoltà: 4/5).
- *Progetto 26.6* — *Interprete completo per il linguaggio MiniL su più file con suite di test automatici*: 8 moduli in 6 fasi con `RUN_TESTS` ed `EXEC ... END` (difficoltà: 5/5).

## Rinvii
- Richiami a capitoli precedenti: 4 (corto circuito), 9 (`<ctype.h>`), 11 (allocazione e sanitizer), 12 (`struct`/`enum`), 13 (unioni etichettate e allineamento), 15 (`void *`, `static_assert`), 16 (puntatori a funzione), 17 (strutture dinamiche), 18 (tabelle hash), 19 (più file e tipi opachi), 21 (`goto cleanup`, `<stdckdint.h>`), 22 (arena), 24 (lista intrusiva), 25 (test automatici).
- Rinvii in avanti: nessuno.

## Affermazioni forti
- Prima di leggere un campo della `union` occorre sempre controllare l'etichetta `tipo` tramite `switch` o `if`.
- Convertire sempre ogni carattere con `(unsigned char)` prima di passarlo alle funzioni di `<ctype.h>`.
- Gli operatori binari associativi a sinistra vanno sempre analizzati con un ciclo `while`, mai con ricorsione sinistra o destra.
- Il codice utente non deve mai poter provocare comportamento indefinito nel programma ospite C (intercettare sempre overflow, `b == 0`, `INT64_MIN / -1`, `INT64_MIN % -1`, `-INT64_MIN`, ricorsione e cicli infiniti).
- Ogni sotto-ambiente creato durante blocchi o chiamate va sempre distrutto sia su ritorno normale, sia su `return` anticipato, sia su errore.

## Stile del codice
- Standard C23: `alignof`, `alignas`, `static_assert`, `nullptr`, `bool`/`true`/`false`, `{}`, `strdup`, `<stdckdint.h>`.
- Indentazione a 4 spazi, `snake_case` italiano senza accenti, suffisso `_t` per i tipi, MAIUSCOLO per costanti/macro/tabelle `static const`, include guard `NOME_H`, `goto cleanup` con inizializzazione preventiva a `nullptr`.
