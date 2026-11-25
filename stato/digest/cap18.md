# Digest — Capitolo 18: Tabelle hash

## Termini definiti e glossario
- **Tabella hash** (*hash table*): struttura dati associativa che mappa chiavi a valori in tempo medio costante tramite una funzione di hash.
- **Funzione di hash** (*hash function*): funzione deterministica che trasforma una chiave di dimensione arbitraria in un intero senza segno (`uint64_t` o `size_t`) usato per scegliere il secchio (*bucket*) tramite `h % num_secchi`.
- **Collisione** (*collision*): evento inevitabile per il principio dei cassetti in cui due chiavi distinte producono lo stesso indice di secchio.
- **Concatenamento** (*separate chaining*): strategia di risoluzione delle collisioni in cui ogni secchio (`nodo_t **secchi`) è la testa di una lista semplicemente concatenata.
- **Indirizzamento aperto** (*open addressing*): alternativa citata in cui tutte le coppie risiedono direttamente nell'array dei secchi.
- **Fattore di carico** (*load factor*): rapporto `alpha = (double)len / (double)cap` tra numero di elementi e numero di secchi.
- **Ridimensionamento** (*rehashing*): riallocazione dell'array dei secchi a una capacità maggiore e ricalcolo delle posizioni delle chiavi.
- Altri termini usati: FNV-1a, djb2, mescolamento di bit (*bit mixing*), hash crittografici, *wraparound*, costo ammortizzato, padding, `void *`, callback, `distruggi_chiave`/`distruggi_valore`, possesso vs prestito, comportamento dipendente dall'implementazione, valori non specificati, comportamento indefinito, doppia liberazione, uso dopo la liberazione, puntatore pendente.

## Concetti spiegati
- Proprietà di una buona funzione di hash (determinismo, distribuzione uniforme, efficienza); FNV-1a a 64 bit, djb2 e mescolamento bit a 64 bit (`mescola_u64`).
- Uso obbligatorio di `const unsigned char *` e aritmetica `uint64_t` (evitando il segno dipendente di `char` e l'overflow con segno).
- Concatenamento: array `nodo_t **secchi` inizializzato esplicitamente con ciclo a `nullptr` (per portabilità standard C23 rispetto a `calloc`), semantica dizionario (no duplicati, aggiornamento in-place), rimozione con `nodo_t **cur`, distruzione salvando `curr->prox`.
- Controllo soglia `0.75` in aritmetica intera `(len + 1) * 4 > cap * 3` con guardia overflow (`SIZE_MAX / sizeof(nodo_t *)`), raddoppio capacità spostando i nodi esistenti tramite `c->hash % nuova_cap` senza riallocare nodi e preservando l'integrità in caso di `malloc == nullptr`.
- Tabella generica su `void *` con callback `hash_fn`, `uguali_fn`, `visita_fn` (con `void *ctx`), invariante `uguali(a, b) => hash(a) == hash(b)`, filtro rapido `curr->hash == h && t->uguali(...)` e divieto di hash su byte grezzi delle `struct` per via del padding.
- Possesso separato di chiavi e valori tramite `distruggi_chiave` e `distruggi_valore` (`nullptr` per prestito), protezione dell'auto-aggiornamento (`curr->valore != v`), trasferimento di possesso con `ht_estrai`, immutabilità delle chiavi inserite e coerenza tra tabella proprietaria e tabella di alias in prestito.

## Esempi e scenari
- `18.1-a`: confronto `hash_somma` vs `hash_fnv1a` su anagrammi (`"roma"`, `"amor"`, `"mora"`, `"sole"`).
- `18.2-a`: rubrica telefonica (`rubrica_t`, `voce_t`) a 8 secchi fissi.
- `18.3-a`: listino prezzi (`listino_t`, `voce_prezzo_t`) con rehash automatico `4 -> 8 -> 16`.
- `18.4-a`: `tab_ht_t` usata contemporaneamente per `citta` (`char * -> int`) e `mappa` (`coord_t -> char *`) con `ht_visita`.
- `18.5-a`: `tab_ht_t` con `arch` proprietaria (`free`, `dis_item`) e `ind` di alias in prestito (`free`, `nullptr`), con `ht_estrai` e bilancio `creati/distrutti`.

## Esercizi
- **18.1 — Analizzatore di funzioni di hash e distribuzione sui secchi per stringhe e interi**: confronta FNV-1a vs djb2 su stringhe e `x % m` vs `hash_mix64` su interi stampando statistiche. Difficoltà: 3/5.
- **18.2 — Contatore di frequenze su tabella hash con concatenamento e ispezione dei secchi**: `INC`/`GET`/`DEL`/`DUMP` su `tab_freq_t` a capacità fissa. Difficoltà: 3/5.
- **18.3 — Tabella hash auto-ridimensionante con soglia intera, hash memorizzato nel nodo e spostamento a zero allocazioni**: `PUT`/`GET`/`DEL`/`RESERVE`/`STAT` con controllo `nodi_allocati`. Difficoltà: 4/5.
- **18.4 — Tabella hash generica riutilizzata per chiavi stringa case-insensitive e chiavi struct con padding**: `ht_str` e `ht_celle` con `memset` `0x55`/`0xAA` per smascherare bug sul padding. Difficoltà: 5/5.
- **18.5 — Tabella hash generica con possesso configurabile, indice di alias in prestito ed estrazione del possesso**: `tab_prop` + `tab_alias` con `PUT`/`ALIAS`/`GET`/`GET_ALIAS`/`DEL`/`EXTRACT`/`BILANCIO`. Difficoltà: 5/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 11 (allocazione dinamica), cap. 12 (`struct`), cap. 13 (tipi a dimensione fissa e padding), cap. 15 (`void *`), cap. 16 (puntatori a funzione, callback, `ctx`), cap. 17 (liste concatenate, `nodo **`, possesso della memoria).
- Rinvii in avanti: cap. 19 (incapsulamento e librerie modulari su più file).

## Affermazioni forti
- Il segno di `char` è dipendente dall'implementazione; negli hash sui byte occorre convertire a `const unsigned char *` e usare `uint64_t` (l'overflow su interi con segno e `% 0` sono comportamento indefinito).
- Non usare mai `sizeof(*s)` sui byte grezzi di una `struct` per calcolarne l'hash (padding non inizializzato).
- Inizializzare `secchi` con `malloc` + ciclo a `nullptr` è portabile C23 (a differenza di `calloc` su architetture dove `nullptr` non fosse tutti bit zero).
- Se `uguali(a, b)` è `true`, deve valere `hash(a) == hash(b)`.
- Non modificare mai una chiave mentre è inserita nella tabella hash.

## Stile del codice
- Standard C23 (`constexpr`, `nullptr`, `bool`, `strdup`, `{}`), box `> **C23**` assente qui (già introdotti prima).
- Tipi `_t`, callback `_fn`, `snake_case` italiano, costanti MAIUSCOLO (`NUM_SECCHI`), `PRIx64` di `<inttypes.h>`, indentazione 4 spazi (alcune funzioni compatte su poche righe negli esempi).
- Controllo sistematico di `malloc`/`strdup` contro `nullptr` e pulizia su errore.
