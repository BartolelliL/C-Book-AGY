# Digest Capitolo 15 — Programmazione generica con `void *`

## Termini definiti e glossario
- **Puntatore generico** (*generic pointer*, `void *` / `const void *`): puntatore capace di contenere l'indirizzo di qualsiasi oggetto in memoria, ma non dereferenziabile direttamente.
- **Contenitore generico** (*generic container*): struttura dati (come `vettore_gen_t`) che memorizza elementi di tipo qualsiasi noto solo a tempo di esecuzione tramite `void *dati` e `dim_elem`.
- **Asserzione statica** (*static assertion*, `static_assert`): controllo verificato dal compilatore su un'espressione costante intera che arresta la compilazione se falsa, a costo zero a tempo di esecuzione.
- Termini del glossario usati: *comportamento indefinito*, *strict aliasing*, *shallow copy* (copia superficiale), *restrict*, *nullptr_t*, *padding*, *alignof*, *offsetof*.

## Concetti spiegati
- Conversioni implicite bidirezionali `T *` ↔ `void *` e rispetto di `const` (`const T *` → solo `const void *`).
- Divieti su `void *`: nessuna dereferenziazione (`*p`), nessuna aritmetica (`p + 1`); indirizzamento portabile a byte tramite `unsigned char *` / `const unsigned char *`; `void *` solo per oggetti, non per funzioni; riconversione al tipo esatto originale guidata da `enum` o contratto del contenitore.
- Funzioni `mem*` di `<string.h>` su `n` byte (non si fermano a `0x00`): `memcpy` (`restrict`, aree disgiunte), `memmove` (aree sovrapposte), `memset` (scrive byte per byte, trappola su `int`), `memcmp` (ritorna segno `< 0`, `0`, `> 0`; non usare su `struct` con padding), `memchr` (preserva `const` in C23). Divieto di passare `nullptr` anche con `n == 0`.
- Architettura di `vettore_gen_t` (`dati`, `dim_elem`, `len`, `cap`), controllo overflow `nuova_cap > SIZE_MAX / dim_elem`, garanzia automatica di allineamento (`malloc`/`realloc` + `sizeof(T)` multiplo di `alignof(T)`), limiti (`void *` senza controllo di tipo a compilazione e copia superficiale).
- `_Generic(expr, ...)`: selezione statica a compilazione, nessuna valutazione di `expr`, conversione *lvalue* (rimuove `const` di primo livello, mantiene distinzione `char *` vs `const char *` e `nullptr_t`), controllo di esaustività omettendo `default:`, funzioni selezionate per nome con argomenti fuori dalle parentesi.
- C23 `typeof` (conserva `const`), `typeof_unqual` (rimuove qualificatori di primo livello), `auto` (deduzione statica con inizializzatore obbligatorio su singola variabile), `static_assert` a 1 o 2 argomenti vs controlli a tempo di esecuzione.

## Esempi e scenari
- `15.1-a` (`15.1-c`, `15.1-d` errori): `stampa_oggetto` su `int`, `double`, `punto_2d_t` e `calcola_indirizzo`.
- `15.2-a`: manipolazione trama binaria `uint8_t[10]` con `0x00` usando `memset`, `memcpy`, `memmove`, `memchr`, `memcmp`.
- `15.3-a`: `vettore_gen_t` (`vg_init`, `vg_push`, `vg_get`, `vg_remove`, `vg_free`) usato per `double` e `coppia_xy_t`.
- `15.4-a`: dispatch con `_Generic` su `int`, `double`, `char *`, `const char *`, `nullptr_t` e `tocca_contatore` non valutato.
- `15.5-a`: `voce_log_t` e `livello_t` con cinque `static_assert`, `typeof`, `typeof_unqual`, `auto` verificato via `_Generic`.

## Esercizi
- `15.1` — *Registro eterogeneo di parametri con puntatori generici `void *` e indirizzamento a byte*: `voce_reg_t[6]` con `GET`/`SET` e verifica indirizzi. Difficoltà: 3/5.
- `15.2` — *Editor di buffer binario con `memcpy`, `memmove`, `memset`, `memcmp` e `memchr`*: `buf_bin_t` con `INS`, `DEL`, `FILL`, `FIND`, `CMP`, `DUMP`. Difficoltà: 3/5.
- `15.3` — *Vettore dinamico generico `vettore_gen_t` riutilizzato per `int64_t` e `struct misura_t`*: 7 funzioni inclusa `vg_scambia`. Difficoltà: 4/5.
- `15.4` — *Dispatch a tempo di compilazione e riconoscimento dei tipi con `_Generic` e `nullptr_t`*: calcolo norme senza `#define`. Difficoltà: 3/5.
- `15.5` — *Verificatore di pacchetti C23 con `static_assert`, `typeof`, `typeof_unqual` e `auto`*: `pacchetto_t` ordinati e verifiche statiche. Difficoltà: 3/5.

## Rinvii
- Richiami indietro: cap. 9 (`str*`), cap. 10 (puntatori), cap. 11 (`malloc`/`calloc`/`realloc`/`free`), cap. 12 (`struct`, `enum`), cap. 13 (`alignof`, `offsetof`, padding), cap. 14 (`restrict`, puntatori pendenti).
- Rinvii in avanti: cap. 16 e 17 (puntatori a funzione per confronto e distruzione), cap. 18 (tabelle hash con `void **`), cap. 19/21/24 (`_Generic` con macro), cap. 21 (`assert`), cap. 22 (*strict aliasing*).

## Affermazioni forti
- Dereferenziare `void *` o applicarvi aritmetica dei puntatori è vietato dallo standard C23; riconvertirlo a un tipo incompatibile e dereferenziarlo è UB.
- `void *` riguarda solo puntatori a oggetti, non a funzioni.
- Passare `nullptr` a `memcpy`, `memmove`, `memset`, `memcmp` o `memchr` anche con `n == 0` è UB; usare `memcpy` su aree sovrapposte è UB.
- Mai usare `memcmp` per confrontare `struct` che possono avere byte di padding.
- L'espressione di controllo di `_Generic` e `typeof` non viene mai valutata; `auto` in C23 è inferenza statica, non tipizzazione dinamica.

## Stile del codice
- Standard C23 (`nullptr`, `nullptr_t`, `typeof`, `typeof_unqual`, `auto`, `static_assert` a 1 o 2 argomenti, `enum nome : tipo`, `bool`).
- Niente cast sul ritorno di `malloc`/`realloc` o nelle conversioni `T *` ↔ `void *`.
- Controlli espliciti `if (n > 0)` prima delle `mem*`, `SIZE_MAX / dim_elem` prima di `realloc`, `ptrdiff_t` (`%td`) per differenze tra puntatori.
