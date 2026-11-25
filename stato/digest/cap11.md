# Digest — Capitolo 11: Memoria dinamica

## Termini definiti e glossario
- **Stack**: area di memoria gestita automaticamente in ordine LIFO per i frame delle chiamate di funzione e le variabili locali automatiche.
- **Heap**: area di memoria da cui il programma richiede e rilascia blocchi a durata esplicita con `malloc`/`free`.
- **Allocazione dinamica** (*dynamic allocation*): richiesta di memoria a tempo di esecuzione sullo heap.
- **Perdita di memoria** (*memory leak*): errore in cui un blocco allocato dinamicamente non è più raggiungibile ma non viene mai liberato con `free`.
- **Uso dopo la liberazione** (*use-after-free*): accesso in lettura o scrittura a memoria dinamica già rilasciata con `free` (comportamento indefinito).
- **Doppia liberazione** (*double free*): chiamata ripetuta di `free` sullo stesso blocco senza una nuova allocazione intermedia (comportamento indefinito).
- **Sanitizer**: strumenti integrati nel compilatore che inseriscono controlli a tempo di esecuzione per rilevare errori di memoria o comportamento indefinito (`AddressSanitizer`, `UndefinedBehaviorSanitizer`).
- Altri termini del glossario usati: *frame* (record di attivazione), *stack overflow*, VLA, crescita geometrica, compattazione (*shrink-to-fit*), *heap buffer overflow*, aliasing, comportamento indefinito, comportamento dipendente dall'implementazione.

## Concetti spiegati
- Stack (LIFO, dimensione ridotta, durata automatica) vs heap (durata esplicita fino a `free`, verifica di `nullptr`, restituibile da funzioni); divieto di VLA e di restituire array locali sullo stack.
- `<stdlib.h>`: `malloc(n * sizeof(*p))` (contenuto indeterminato, nessun cast su `void *`), `calloc(nmemb, size)` (azzera bit a `0` e controlla overflow del prodotto), `free(ptr)` (`free(nullptr)` definito e innocuo; subito `ptr = nullptr;`), `exit(EXIT_FAILURE)`. Nota C23: `malloc(0)` dipendente dall'implementazione.
- C23 `<string.h>`: `strdup` e `strndup` (duplicano su heap, il chiamante deve controllare `nullptr` e chiamare `free`).
- `realloc(ptr, nuova_dim)`: salva sempre in `tmp` prima di aggiornare `ptr`; `realloc(nullptr, dim)` equivale a `malloc(dim)`; in C23 `realloc(ptr, 0)` è comportamento indefinito (usare `free`). Array dinamici con `(len, cap)` e crescita geometrica per raddoppio (`shrink-to-fit` finale se `len < cap`).
- Errori su heap e disciplina: un solo proprietario per blocco, copie indipendenti (`strdup`), azzeramento dopo `free`, pulizia su tutti i percorsi di errore; divieto di `free` su puntatori dello stack o spostati.
- Compilazione e test con `-g -fsanitize=address,undefined` su casi normali, vuoti, al limite e di errore.

## Esempi e scenari
- **11.1**: buffer fisso `MAX_MISURE = 100` (spreco stack) e `mostra_frame` ricorsiva (ordine LIFO).
- **11.2**: stazione meteo (`temp` con `calloc`, `stazione` con `strdup`, `sigla` con `strndup`, `termina_errore`).
- **11.3**: lettura misure `double` in array dinamico con raddoppio da `cap = 4`.
- **11.4**: `elabora_lotto` con pulizia ordinata su fallimento allocazione e ramo errore intermedio (`fattore <= 0`).
- **11.5**: concatenazione parole da `stdin` in `frase` con `strdup` + `realloc` (`nuova_len + 1`).

## Esercizi
- **11.1 — Simulatore di stack delle chiamate e soglia heap**: simulare comandi `CALL`, `RET`, `HEAP` su array paralleli senza `malloc`. Difficoltà: 3/5.
- **11.2 — Analisi dinamica di punteggi e targhette con `malloc`, `calloc`, `strdup` e `strndup`**: allocare punteggi, frequenze azzerate (`calloc(101, ...)`), etichetta e codice abbreviato con `errore_fatale`. Difficoltà: 3/5.
- **11.3 — Array dinamico a crescita geometrica e compattazione con `realloc`**: crescere da `cap = 0` (`2, 4, 8...`), filtrare `>= soglia`, compattare o liberare con `free` se `len_filt == 0`. Difficoltà: 4/5.
- **11.4 — Gestione sicura di buffer attivo e backup senza perdite né doppie liberazioni**: comandi `IMPOSTA`, `BACKUP`, `RIPRISTINA`, `SVUOTA A/B`, `STATO` con `strdup` indipendenti. Difficoltà: 4/5.
- **11.5 — Estrattore e concatenatore dinamico di sottostringhe verificato con sanitizer**: estrarre fette con `strndup` e concatenarle con `realloc` controllando limiti senza overflow. Difficoltà: 4/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 7–10 in apertura; cap. 8–9 (buffer overflow).
- Rinvii in avanti: cap. 14 (uso dopo la liberazione con copie di puntatori); cap. 15 (`void *`); cap. 17 (proprietà e liberazione in liste/alberi); cap. 21 (diagnostica avanzata).

## Affermazioni forti
- Non usare mai VLA né restituire indirizzi di array locali dallo stack.
- Evitare il cast su `malloc`/`calloc`/`realloc`; usare l'idioma `n * sizeof(*p)`.
- Controllare sempre `nullptr` dopo ogni allocazione; salvare sempre `realloc` in un puntatore temporaneo `tmp`.
- In C23 non chiamare mai `realloc(ptr, 0)` (comportamento indefinito).
- Impostare sempre `ptr = nullptr;` subito dopo `free(ptr);`.
- Verificare sempre i programmi con `-fsanitize=address,undefined -g` fino a zero segnalazioni.

## Stile del codice
- Standard C23 (`nullptr`, `bool`, `constexpr`, `strdup`, `strndup`).
- Funzione helper `termina_errore` / `errore_fatale` con `exit(EXIT_FAILURE)` su `stderr`.
- Pulizia esplicita di tutti i blocchi prima di ogni uscita, anche in caso di errore.
