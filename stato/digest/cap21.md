# Digest — Capitolo 21: Robustezza e qualità

## Termini definiti e glossario
- **Modello `goto cleanup`**: schema che usa salti in avanti con `goto` verso un'unica etichetta finale `cleanup:` per rilasciare più risorse in ordine inverso senza perdite di memoria.
- **Asserzione** (*assertion*): controllo diagnostico espresso con `assert` (`<assert.h>`) che verifica un'ipotesi del programmatore a tempo di esecuzione durante lo sviluppo.
- **Funzione variadica** (*variadic function*): funzione che accetta un numero variabile di argomenti, dichiarata con `...` (ellissi) e letta tramite `<stdarg.h>`.
- **Promozioni predefinite degli argomenti** (*default argument promotions*): conversioni automatiche applicate agli argomenti passati nella parte `...` (`bool`, `char`, `short` -> `int`/`unsigned int`; `float` -> `double`).
- **Macro con argomenti** (*function-like macro*): macro `#define` che accetta parametri ed effettua sostituzione testuale prima della compilazione.
- **Debugger**: strumento (`gdb`, `lldb`) per eseguire il programma passo passo, ispezionare variabili, memoria e stack di chiamate (*backtrace*) con punti di arresto (*breakpoint*).
- **Segnale**: notifica asincrona o sincrona inviata al programma dal sistema operativo o tramite `raise` (`<signal.h>`).
- Termini del glossario usati: **canale del risultato**, **canale dell'esito**, **comportamento dipendente dall'implementazione**, **comportamento indefinito** (*undefined behavior*, UB), **asserzione statica** (`static_assert`), **attributo** (`[[nodiscard]]`, `[[maybe_unused]]`, `[[noreturn]]`), **tipo opaco**.

## Concetti spiegati
- Propagazione esplicita degli errori con `enum` di stato (successo = `0`), `bool`, puntatori (`nullptr`), valori sentinella e parametri di uscita.
- Uso di `errno` (`<errno.h>`), costanti standard (`EDOM`, `ERANGE`, `EILSEQ`), `perror` (`<stdio.h>`) e `strerror` (`<string.h>`).
- Aritmetica intera controllata C23 (`<stdckdint.h>`: `ckd_add`, `ckd_sub`, `ckd_mul`).
- Rilascio deterministico di più risorse con `goto cleanup`, chiusura controllata di `fclose` e rimozione di file parziali con `remove`.
- Asserzioni con `assert`, disabilitazione tramite `NDEBUG`, separazione tra errori di programmazione e errori operativi.
- Funzioni variadiche (`va_list`, `va_start`, `va_arg`, `va_copy`, `va_end`), pattern a due passaggi con `vsnprintf`, inoltro con `vprintf`/`vfprintf`.
- Trappole delle macro con argomenti vs `static inline`, `ARRAY_LEN`, `__FILE__`, `__LINE__`, `__func__` e attributi C23.
- Riepilogo delle sei fonti critiche di UB, flusso diagnostico (`-Wall -Wextra -Wpedantic -g`, `-fsanitize=address,undefined`, debugger), `volatile` e segnali (`<signal.h>`, `volatile sig_atomic_t`, `signal`, `raise`, `SIG_DFL`, `SIG_IGN`, `SIG_ERR`).

## Esempi e scenari
- `21.1-a`: verifica di `ckd_add`/`ckd_sub`/`ckd_mul` (`prova_aritmetica`), `fopen` fallita con `perror`/`strerror`, `radice_sicura(-4.0, &rad)` con `EDOM`.
- `21.2-a`: `filtra_righe_maiuscolo` su file e due buffer dinamici con `goto cleanup`; `21.2-b`/`c`: frammenti su `fclose` controllata e stile fragile.
- `21.3-a`: `lista_ord_t` con `controlla_invariante` dentro `#ifndef NDEBUG`.
- `21.4-a`: `somma_variadica`, `unisci_stringhe` (con `va_copy` e sentinella `(const char *)nullptr`), `log_messaggio`.
- `21.5-a`: `ARRAY_LEN`, `REGISTRA_EVENTO`, `massimo_i32` (`static inline`), `traccia_punto` (`[[nodiscard]]`), `stampa_config` (`[[maybe_unused]]`), `interrompi_fatale` (`[[noreturn]]`).
- `21.6-a`: gestore `gestore_sigint` con `static volatile sig_atomic_t arresto_richiesto`, `raise(SIGTERM)` ignorato e `raise(SIGINT)`.

## Esercizi
- **21.1 — Calcolatrice controllata a 64 bit con `<stdckdint.h>`, `errno` e propagazione di codici di errore**: calcolatrice CLI su `int64_t` e `sqrt` con `esito_calc_t`, `strtoll`/`strtod` e `ckd_*`. Difficoltà: 3/5.
- **21.2 — Pipeline multi-risorsa con rilascio deterministico tramite `goto cleanup` e iniezione di guasti**: elaborazione file + buffer + array con simulazione di guasti ai passi 1–5 e conteggio risorse. Difficoltà: 4/5.
- **21.3 — Coda circolare dinamica con verifica di invarianti tramite `assert` su più file**: tipo opaco `coda_inv_t` su 3 file con invariante circolare verificato in `#ifndef NDEBUG`. Difficoltà: 4/5.
- **21.4 — Formattatore dinamico e aggregatore variadico con `<stdarg.h>`, `va_copy` e `vsnprintf` su più file**: modulo a 3 file con `formatta_alloc`, `log_su_stream` e `riepilogo_tipato`. Difficoltà: 4/5.
- **21.5 — Sistema diagnostico con macro con argomenti (`__FILE__`, `__LINE__`, `__func__`), `static inline` e attributi C23**: modulo a 3 file con `VERIFICA_PASSO`, `satura_i32` e attributi C23. Difficoltà: 3/5.
- **21.6 — Elaboratore batch con arresto controllato via `<signal.h>` (`volatile sig_atomic_t`, `signal`, `raise`) e difesa da UB**: loop a comandi con `ckd_add`, gestione `SIGINT`/`SIGTERM` e riepilogo finale. Difficoltà: 4/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 1 (`printf`/`fprintf`), cap. 2 (variabili non inizializzate), cap. 3 (overflow interi), cap. 4 (`[[fallthrough]]`), cap. 8 (array), cap. 10 (puntatori nulli e decadimento array), cap. 11 (memoria dinamica e sanitizer), cap. 14 (`errno`, `ERANGE`, conversioni numeriche, `restrict`), cap. 15 (`static_assert`, `restrict`), cap. 19 (preprocessore, `static inline`, tipi opachi, multi-file), cap. 20 (`<stdio.h>`, `fclose`).
- Rinvii in avanti: cap. 24 (costrutti avanzati del preprocessore: `do { ... } while (0)`, `#`, `##`, macro variadiche) in `21_05.md` e `21_99.md`; cap. 25 (interazione tra UB e ottimizzazioni del compilatore) in `21_06.md` e `21_99.md`.

## Affermazioni forti
- Azzerare sempre `errno = 0;` prima di chiamare funzioni che lo usano e salvarlo subito in una variabile locale (`int err = errno;`) prima di qualsiasi altra chiamata di libreria.
- Non modificare mai la stringa restituita da `strerror` (UB).
- `free(nullptr)` è sicuro; `fclose(nullptr)` e la doppia `fclose` provocano UB.
- Mai saltare con `goto` all'indietro o scavalcare l'inizializzazione di una variabile usata in `cleanup:`.
- Divieto assoluto di effetti collaterali dentro `assert(...)`; usare `assert` solo per bug interni, mai per input esterni o `malloc`.
- `va_end` deve bilanciare ogni `va_start` e `va_copy` su tutti i percorsi; mai passare tipi non promossi (`bool`, `char`, `short`, `float`) a `va_arg`.
- `volatile` non rende atomico l'accesso né sincronizza thread.
- Dentro un gestore di segnale non chiamare mai `printf`, `fprintf`, `malloc`, `free` o `exit` (UB); accedere solo a `volatile sig_atomic_t` statici.

## Stile del codice
- C23 (`nullptr`, `bool`/`true`/`false`, separatore di cifre `3'037'000'500`, attributi `[[...]]`, `= {}` per zero-init).
- Indentazione a 4 spazi, graffe sempre presenti, `static` sulle funzioni interne, `snake_case` italiano, `EXIT_FAILURE` / `return 0;`, cast espliciti `(unsigned char)` per `toupper` e `(const char *)nullptr` per sentinelle variadiche.
