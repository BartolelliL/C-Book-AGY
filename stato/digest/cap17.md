# Digest — Capitolo 17: Strutture dati dinamiche

## Termini definiti e glossario
- **Lista concatenata** (*linked list*): struttura dati dinamica formata da nodi allocati singolarmente sullo heap e collegati tramite puntatori.
- **Lista doppiamente concatenata**: lista in cui ogni nodo mantiene sia `prec` sia `prox` e il descrittore conserva `testa`, `coda` e `len`.
- **Invariante strutturale**: insieme di condizioni sui puntatori e sui contatori che deve valere prima e dopo ogni operazione (es. `testa->prec == nullptr`, `coda->prox == nullptr`, simmetria `a->prox == b` ↔ `b->prec == a`).
- **Pila** (*stack*): struttura dati lineare LIFO (*Last In, First Out*) con operazioni `push`, `pop` e `peek` in cima.
- **Coda** (*queue*): struttura dati lineare FIFO (*First In, First Out*) con `enqueue` in fondo, `dequeue` e `peek` in testa.
- **Buffer circolare**: coda su array dinamico trattato ad anello tramite indice `inizio`, lunghezza `len`, capacità `cap` e aritmetica modulare `(inizio + k) % cap`.
- **Albero binario di ricerca** (BST): struttura gerarchica in cui ogni nodo ha al più due figli (`sx`, `dx`) e rispetta l'invariante d'ordine (sottoalbero sinistro < chiave < sottoalbero destro).
- **Successore in-ordine**: nodo con la chiave minima nel sottoalbero destro, usato nella rimozione di un nodo con due figli.
- **Possesso della memoria** (*ownership*): contratto che stabilisce quale modulo o struttura è unico responsabile di liberare un blocco sullo heap (trasferimento, copia o prestito/*borrowing*).
- Altri termini usati: struttura auto-referenziata, descrittore, valore sentinella, uso dopo la liberazione, doppia liberazione, puntatore pendente, comportamento indefinito, ricerca binaria, visite (in-ordine, pre-ordine, post-ordine), potatura, degenerazione, cache LRU, callback, `void *`.

## Concetti spiegati
- Strutture auto-referenziate con tag `struct` (`struct nodo *prox;`) e descrittori (`testa`, `coda`, `len`).
- Inserimento ordinato e rimozione in liste semplici tramite puntatore a puntatore (`nodo_t **cur = &l->testa;`) senza rami speciali per la testa.
- Distruzione iterativa sicura salvando `curr->prox` prima di `free(curr)`.
- Liste doppiamente concatenate: `scollega_nodo`, `collega_in_testa` e `sposta_in_testa` in tempo costante senza riallocazioni nei quattro casi limite.
- Pile LIFO e code FIFO su lista concatenata (azzerando `coda = nullptr` sull'ultimo elemento) e su buffer circolare dinamico (riallineamento con `malloc` al raddoppio se `inizio > 0`, controllo overflow `SIZE_MAX / sizeof(T)`), con interfacce `bool` sicure.
- BST: ricerca, inserimento iterativo con `nodo_bst_t **`, visite ricorsive, potatura su intervalli `[lo, hi]`, rimozione nei tre casi (0, 1, 2 figli), altezza, degenerazione su chiavi ordinate e distruzione rigorosa in post-ordine.
- Contratti di possesso con `typedef void (*distruggi_fn)(void *dato);` (`free`, distruttore profondo, `nullptr` per prestito), ordine di distruzione vista-prima-del-proprietario e responsabilità del chiamante su errore di `malloc`.

## Esempi e scenari
- `17.1-a`: lista ordinata di interi (`lista_t`, `nodo_t`, `dati[] = {25, 10, 40, 15, 30}`), rimozione di testa, interno e coda.
- `17.2-a`: cronologia di navigazione web (`cronologia_t`, `pagina_t`, `url`, `corrente`) con stampa bidirezionale.
- `17.3-a`: verifica parentesi bilanciate con `pila_c_t` e coda di richieste `coda_q_t` svuotata e riusata.
- `17.4-a`: BST di chiavi intere (`50, 30, 70, 20, 40, 60, 80`) con tre visite, minimo/massimo e altezza.
- `17.5-a`: `lista_gen_t` proprietaria su stringhe `strdup` (`free`) e vista in prestito su `sensore_t` sullo stack (`nullptr`).

## Esercizi
- **17.1 — Registro ordinato di attività con lista semplicemente concatenata e rimozione tramite puntatore a puntatore**: gestione comandi `ADD`/`DEL`/`FIND`/`LIST` ordinati per priorità decrescente e `id` crescente. Difficoltà: 3/5.
- **17.2 — Cache LRU a capacità fissa con lista doppiamente concatenata**: cache `PUT`/`GET`/`DEL`/`DUMP` con `scollega_nodo`, `collega_in_testa`, `sposta_in_testa` senza allocazioni e verifica avanti/indietro. Difficoltà: 4/5.
- **17.3 — Gestore di ticket con coda su buffer circolare dinamico e pila di annullamento su lista concatenata**: comandi `ENQ`/`SERVE`/`UNDO`/`PEEK`/`STAT` con crescita esponenziale del buffer circolare. Difficoltà: 4/5.
- **17.4 — Indice chiave-valore su albero binario di ricerca con rimozione completa e query per intervallo**: comandi `PUT`/`GET`/`DEL`/`RANGE`/`INFO` con `int32_t`, rimozione a 2 figli e potatura. Difficoltà: 4/5.
- **17.5 — Lista generica con contratti di possesso espliciti: proprietà profonda tramite distruttore e vista in prestito**: `documento_t` con `strdup` e `calloc`, `lista_prop` vs `lista_vista`, `lg_rimuovi_se` e conteggio creati/distrutti. Difficoltà: 5/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 7 (funzioni/ricorsione), cap. 11 (memoria dinamica e sanitizer), cap. 12 (`struct`, `typedef`, `->`), cap. 14 (puntatori a puntatori e pendenti), cap. 15 (`void *`, contenitori generici), cap. 16 (puntatori a funzione e callback).
- Rinvii in avanti: cap. 18 (tabella hash generica), cap. 19 (moduli/librerie su più file), cap. 23 (alberi AVL autobilanciati), cap. 25 (cache del processore).

## Affermazioni forti
- Una `struct` non può contenere un campo diretto del proprio tipo, solo un puntatore tramite il tag `struct`.
- Ogni blocco sullo heap deve avere un solo proprietario alla volta; solo il proprietario può chiamare `free`.
- Leggere `curr->prox` dopo `free(curr)`, liberare un nodo BST in pre-ordine o estrarre da pila/coda vuota senza controllo provoca comportamento indefinito.
- Nel buffer circolare pieno con `inizio > 0` non si può usare `realloc` senza riallineamento.
- Una vista in prestito va sempre distrutta prima del contenitore proprietario; se l'inserimento fallisce, il chiamante resta proprietario del dato.

## Stile del codice
- Standard C23 (`nullptr`, `bool`/`true`/`false`, inizializzazione `{}`, `strdup`), box `> **C23**` per `nullptr` e `strdup`.
- Identificatori in italiano `snake_case` con suffisso `_t` per `typedef struct` e `_fn` per puntatori a funzione (`distruggi_fn`, `pred_dato_fn`).
- Indentazione 4 spazi, graffe sempre presenti (a volte funzioni brevi su una riga negli esempi), `int main(void)`, `return 0;` o `EXIT_FAILURE`, `malloc(sizeof(*p))` sempre controllata contro `nullptr`.
