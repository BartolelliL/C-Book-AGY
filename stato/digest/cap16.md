# Digest Capitolo 16 — Puntatori a funzione

## Termini definiti e glossario
- **Puntatore a funzione** (*function pointer*): variabile che memorizza l'indirizzo di una funzione con firma specifica (`tipo_ritorno (*nome)(tipi_parametri);`) e ne consente l'invocazione indiretta.
- **Callback** (*funzione di richiamo*): funzione passata come argomento tramite puntatore a funzione affinché un algoritmo generico la invochi al momento opportuno.
- **Parametro di contesto** (`void *ctx` / `const void *ctx`): parametro opaco inoltrato dall'algoritmo alla callback per passare stato o configurazione senza variabili globali.
- **Comparatore**: callback `int cmp(const void *a, const void *b)` per `qsort` e `bsearch` che restituisce `< 0`, `0` o `> 0`.
- **Tabella di puntatori a funzione** (*dispatch table*): array di puntatori a funzione (indicizzato da intero/`enum`) o di `struct` `{ nome, fn }` (cercato linearmente o con `bsearch`) per sostituire lunghi `switch` o `if-else`.
- Termini del glossario usati: *decadimento automatico*, *comportamento indefinito*, *comportamento non specificato*, *chiusura*, *tie-breaker* (chiave secondaria di spareggio), *regola a spirale*.

## Concetti spiegati
- Sintassi `tipo_ritorno (*nome)(tipi_parametri)`, necessità delle parentesi rispetto a `tipo *nome(...)`, decadimento del nome funzione (`p = f` ≡ `p = &f`), invocazione `p(x)` ≡ `(*p)(x)`, alias `typedef ... (*nome_fn)(...)`.
- Separazione da `void *` (conversione non portabile tra puntatore a funzione e `void *`), conversione temporanea ad altro puntatore a funzione solo con riconversione esatta prima della chiamata.
- Algoritmi generici parametrizzati (visita, trasformazione, filtraggio, riduzione) con `void *base`, `n`, `dim_elem` (`unsigned char *`), callback e `ctx`, controlli difensivi (`fn != nullptr`, `dim_elem > 0`, `n > 0 && base != nullptr`).
- `qsort` e `bsearch` (`<stdlib.h>`): contratto del comparatore, trappola della sottrazione `*pa - *pb` (overflow, wraparound, troncamento `double`) sostituita da `(*pa > *pb) - (*pa < *pb)`, instabilità di `qsort` e chiave secondaria di spareggio, doppio livello `const char *const *` per array di stringhe, preservazione di `const` in `bsearch` (C23), protezione `nmemb == 0`.
- Tabelle di puntatori a funzione: firma uniforme con struct di stato, controllo limiti indice e `!= nullptr`, sincronizzazione `enum` + `static_assert`, ricerca con `bsearch` su tabella ordinata alfabeticamente.

## Esempi e scenari
- `16.1-a` (`16.1-b` errore): convertitore di temperature (`celsius_a_fahrenheit`, `fahrenheit_a_celsius`, `celsius_a_kelvin`) con `conv_fn` e `scegli_conversione`.
- `16.2-a`: `visita_generica`, `conta_se`, `trova_primo` applicati a `int` (soglia) e `prodotto_t` (budget).
- `16.3-a`: `qsort` su `int` (con `INT_MIN`/`INT_MAX`) e `const char *parole[]`, ricerca con `bsearch` su vista `const`.
- `16.4-a`: calcolatrice a 4 operazioni con `TABELLA_OP` cercata via `bsearch` e `STAMPATORI` indicizzata da `stile_out_t` con `static_assert`.

## Esercizi
- `16.1` — *Pipeline configurabile di filtri numerici con puntatori a funzione*: `stadio_t`, `risolvi_filtro`, `applica_pipeline` con `raddoppia`, `dimezza`, `opposto`, `satura`. Difficoltà: 3/5.
- `16.2` — *Motore generico di filtraggio e riduzione con callback e contesto `ctx`*: `filtra_generico` e `riduci_generico` su `int32_t` ed `esame_t`. Difficoltà: 4/5.
- `16.3` — *Catalogo di libri con ordinamento multi-criterio (`qsort`) e ricerca binaria (`bsearch`)*: `libro_t`, tre comparatori senza overflow e vista `const`. Difficoltà: 3/5.
- `16.4` — *Interprete di istruzioni su registri con tabella di comandi (`bsearch`) e tabella di stampa indicizzata da `enum`*: `macchina_t` a 4 registri con 7 comandi e 3 formati protetti da `static_assert`. Difficoltà: 4/5.

## Rinvii
- Richiami indietro: cap. 7 (funzioni/prototipi), cap. 8 (ordinamento e ricerca binaria), cap. 10 (puntatori, `ptrdiff_t`, `nullptr`), cap. 12 (`struct`, `enum`, `typedef`), cap. 14 (`const` su più livelli), cap. 15 (`void *`, `mem*`, `memchr` const-preserving, `static_assert`).
- Rinvii in avanti: cap. 17 e 18 (strutture dati dinamiche), cap. 24 (macchine a stati finiti), cap. 26 (interprete finale).

## Affermazioni forti
- Invocare un puntatore a funzione nullo, non inizializzato o convertito a firma incompatibile provoca UB.
- Un puntatore a funzione non è convertibile in modo portabile a `void *` né da `void *`.
- Mai usare `*pa - *pb` nei comparatori di `qsort`/`bsearch`; un comparatore incoerente, `bsearch` su array non ordinato o `base == nullptr` (anche con `nmemb == 0`) provocano UB.
- L'ordine relativo di elementi equivalenti in `qsort` e quale elemento equivalente restituisca `bsearch` sono comportamento non specificato.

## Stile del codice
- Standard C23 (`nullptr`, `bool`, `true`, `false`, `constexpr`, `static_assert`, `bsearch` const-preserving).
- `typedef` con suffisso `_fn` per puntatori a funzione e `_t` per `struct`/`enum`; `(void)param;` per parametri inutilizzati.
- Controlli sistematici `!= nullptr`, `dim_elem > 0`, limiti indici, niente variabili globali nelle callback.
