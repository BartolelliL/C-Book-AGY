# Digest — Capitolo 22: Gestione avanzata della memoria

## Termini definiti e glossario
- **Allocatore ad arena** (*arena allocator*, *bump allocator*): allocatore che assegna memoria in tempo costante ($O(1)$) avanzando un cursore su un buffer contiguo e libera tutti gli oggetti in un colpo solo (o tramite marche/checkpoint).
- **Allocatore a pool** (*pool allocator*, *fixed-size pool*): allocatore per blocchi di dimensione fissa che garantisce allocazione e rilascio in tempo $O(1)$ e zero frammentazione esterna.
- **Lista libera** (*free list*): sequenza collegata di blocchi di memoria disponibili mantenuta dall'allocatore per soddisfare nuove richieste e riciclare blocchi liberati.
- **Campo array flessibile** (*flexible array member*): ultimo campo di una `struct` dichiarato senza dimensione (`tipo nome[]`) per allocare intestazione e dati variabili in un unico blocco contiguo.
- **First-fit**, **suddivisione** (*splitting*), **fusione** (*coalescing*): strategie della lista libera a dimensione variabile per cercare il primo blocco sufficiente, dividerlo e fondere blocchi liberi adiacenti.
- **Frammentazione interna** / **frammentazione esterna**: spreco di byte dentro un blocco (padding/residui) vs memoria libera totale sufficiente ma spezzettata in blocchi non contigui.
- **Tipo effettivo** e **strict aliasing**: regole C23 che stabiliscono con quali tipi di puntatore è lecito accedere a un oggetto in memoria.
- **Canarini di confine** (*redzone*) e **avvelenamento** (*poisoning*): tecniche difensive per rilevare underflow, overflow, letture non inizializzate e uso dopo la liberazione.
- Termini del glossario usati: **allineamento**, **padding**, **wrap-around**, **puntatore pendente**, **perdita di memoria**, **doppia liberazione**, **tipo opaco**, **comportamento dipendente dall'implementazione**, **comportamento indefinito**.

## Concetti spiegati
- `alignas`, `alignof` (parole chiave C23) e `max_align_t` (`<stddef.h>`), arrotondamento sicuro a potenza di due con `ckd_add` e verifica tramite `uintptr_t`.
- Allineamento di `struct` e array (`alignas(64)` per linee di cache).
- Arena su buffer statico (`alignas(max_align_t)`), `arena_reset` e marche di salvataggio/ripristino.
- Pool opaco con memoria da `malloc` (senza tipo dichiarato), `memcpy` per il puntatore `prox` della lista libera, validazione tramite `uintptr_t` e tabella di stato contro doppie liberazioni.
- Campi array flessibili (`offsetof`) e allocatore con lista libera (intestazione allineata, first-fit, splitting, coalescing).
- Strict aliasing, *type punning* portabile con `memcpy` + `static_assert`, `restrict`, redzone e poisoning.

## Esempi e scenari
- `22.1-a`: `contatore_cache_t` (`alignas(64)`), buffer `deposito` (`alignas(max_align_t)`), `arrotonda_su` e `e_allineato`.
- `22.2-a/b/c` (`arena_token`): 3 file con `arena_t` e lista di `nodo_token_t` per tokenizzare frasi senza `malloc`/`free`.
- `22.3-a/b/c` (`pool_particelle`): 3 file con `pool_entita_t` opaco per `particella_t`.
- `22.4-a`: `messaggio_t` con campo array flessibile `char testo[]` e allocatore `blocco_t` con `fl_alloca`/`fl_libera` (`ALLIN = 16`).
- `22.5-a`: `double_a_bit` via `memcpy`, `scala_e_somma` con `restrict`, blocco protetto da `GUARDIA` (`CAN_SX=0xA5`, `CAN_DX=0x5A`, `VELENO_ALLOC=0xAA`, `VELENO_FREE=0xDD`).

## Esercizi
- **22.1 — Pianificatore di allineamento e layout di struct con `alignas`, `max_align_t` e `ckd_add`**: utilità di allineamento e simulatore di offset/padding di `struct`. Difficoltà: 3/5.
- **22.2 — Allocatore ad arena su buffer statico con allineamento esplicito e marche di ripristino**: modulo a 3 file (`arena_st.h/c`, `main.c`) con pila di marche e `memset`. Difficoltà: 4/5.
- **22.3 — Allocatore a pool generico opaco con rilevamento di doppia liberazione e puntatori estranei**: modulo a 3 file (`pool_blocchi.h/c`, `main.c`) con `pool_esito_t`. Difficoltà: 4/5.
- **22.4 — Allocatore con lista libera (first-fit, splitting, coalescing) per serie con campo array flessibile**: modulo a 3 file (`alloc_libera.h/c`, `main.c`) con `serie_dati_t`. Difficoltà: 5/5.
- **22.5 — Allocatore diagnostico con canarini di confine, poisoning, ispezione bit via `memcpy` e kernel `restrict`**: modulo a 3 file (`mem_diag.h/c`, `main.c`) con redzone, `FBITS` e `AXPY`. Difficoltà: 4/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 11 (memoria dinamica), cap. 13 (allineamento, padding, `alignof`, `uintptr_t`), cap. 14 (puntatori avanzati, `restrict`), cap. 15 (`void *`, `memcpy`/`memset`), cap. 19 (multi-file, tipi opachi), cap. 21 (`ckd_add`/`ckd_mul`, diagnostica).
- Rinvii in avanti: cap. 23 (notazione $O(1)$), cap. 25 (linee di cache, interazione UB e ottimizzazioni), cap. 26 (arena per nodi dell'albero di sintassi dell'interprete).

## Affermazioni forti
- `alignas` non può mai ridurre l'allineamento naturale di un tipo, né applicarsi a `typedef`, parametri o campi di bit; in C23 `<stdalign.h>` è superato e non va incluso.
- Un buffer statico per allocatori generici va dichiarato con `alignas(max_align_t)`, mai come semplice `unsigned char buf[N]`.
- Confrontare con `<` o `>=` puntatori a oggetti diversi è UB: usare `uintptr_t`.
- Non accedere mai a un blocco riciclato nel pool con cast diretti `*(void **)blocco`: usare `memcpy`; non fare *type punning* con cast di puntatore (`*(uint32_t *)&f`, UB per strict aliasing).
- Dereferenziare puntatori dell'arena dopo `reset` o `ripristina` è UB.
- Un campo array flessibile deve stare per ultimo in una `struct` con almeno un altro campo con nome; non può stare in `union`, array o dentro un'altra `struct`; `*dst = *src` lo ignora.

## Stile del codice
- C23 (`alignas`, `alignof`, `nullptr`, `bool`, `static constexpr`, `static_assert`, `= {}` per zero-init).
- Tipi opachi in `.h` con `typedef struct ...`, 4 spazi di indentazione, graffe sempre presenti, `snake_case` italiano, `(void *)` intermedio nei cast da `unsigned char *` a `blocco_t *`.
