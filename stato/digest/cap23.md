# Digest — Capitolo 23: Strutture dati e algoritmi avanzati

## Termini definiti e glossario
- **Complessità asintotica** e **notazione O** (*Big-O notation*): misura di crescita del costo in tempo o spazio al crescere di `n`, trascurando costanti e termini inferiori; analisi in caso migliore, peggiore, medio e **costo ammortizzato**.
- **Coda di priorità** (*priority queue*): struttura dati da cui si estrae sempre l'elemento con priorità massima o minima.
- **Heap binario** (*binary heap*, min-heap / max-heap): albero binario completo memorizzato in un array contiguo con proprietà d'ordine tra genitore e figli.
- **Albero AVL** (*AVL tree*): albero binario di ricerca autobilanciato in cui, per ogni nodo `u`, `|fb(u)| = |h(u->sx) - h(u->dx)| <= 1` (**fattore di bilanciamento**).
- **Rotazioni singole** (`LL`, `RR`) e **rotazioni doppie** (`LR`, `RL`): trasformazioni `O(1)` di puntatori e altezze per ripristinare l'invariante AVL.
- **Trie** (albero dei prefissi): albero di ricerca per stringhe in cui ogni arco rappresenta un carattere e le chiavi condividono i prefissi comuni.
- **Grafo** (*graph*, orientato/non orientato), **vertici** (`V`), **archi** (`E`), **grado**, **cammino**, **ciclo**, **DAG** (*Directed Acyclic Graph*).
- **BFS** (*Breadth-First Search*) e **DFS** (*Depth-First Search*): visite `O(V + E)` su liste di adiacenza; marcatura a **tre colori** (bianco/grigio/nero) per cicli e **ordinamento topologico**.
- **Algoritmo di Dijkstra**, **rilassamento** (*relaxation*) e **lazy deletion**: calcolo dei cammini minimi a sorgente singola su grafi con pesi non negativi (`w >= 0`).
- Termini del glossario usati: **tipo opaco**, **callback**, **coda** FIFO, **pila**, **ricerca binaria**, **albero binario di ricerca**, **tabella hash**, **perdita di memoria**, **comportamento indefinito**.

## Concetti spiegati
- Gerarchia asintotica `O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(2^n)` e misurazione deterministica tramite contatori `uint64_t`.
- Heap binario implicito (`(i - 1) / 2`, `2 * i + 1`, `2 * i + 2`), *sift-up*, *sift-down*, *heapify* bottom-up di Floyd `O(n)` e genericità con `void *`, `dim_elem`, `memcpy`, callback.
- Alberi AVL: calcolo altezza, `fb`, rotazioni LL/RR/LR/RL, aggiornamento altezze dal basso verso l'alto, distruzione post-ordine.
- Trie su `'a'..'z'` (`figli[26]`), `parole_sottoalbero`, ricerca, inserimento, conteggio prefissi `O(L)`, autocompletamento DFS e rimozione potata.
- Grafi con liste di adiacenza (`O(V + E)`) vs matrice di adiacenza (`O(V^2)`), BFS per cammini minimi non pesati, DFS a tre colori per cicli e ordinamento topologico.
- Dijkstra `O(V^2)` e `O((V + E) log V)` con min-heap, `UINT64_MAX`, `ckd_add` nel rilassamento, *lazy deletion* e ricostruzione cammini tramite `prec[]`.

## Esempi e scenari
- `23.1-a`: confronto confronti su `TAGLIE = {16, 64, 256, 1024}` tra `ricerca_binaria`, `ricerca_lineare` e `ha_duplicati`.
- `23.2-a`: `min_heap_t` di `int` con `risali`, `scendi` e *heapify* `O(n)`.
- `23.3-a`: `nodo_avl_t` con inserimento e rotazioni singole `ruota_dx`/`ruota_sx` su sequenze `10..60` e `60..10`.
- `23.4-a`: `nodo_trie_t` su vocabolario minuscolo con `valida_stringa` e `trie_conta_prefisso`.
- `23.5-a`: `grafo_t` non orientato di 6 vertici con `bfs` e `dfs_ric`.
- `23.6-a`: `dijkstra` `O(V^2)` su rete orientata di 5 nodi con `arco_p_t`, `UINT64_MAX` e `ckd_add`.

## Esercizi
- **23.1 — Banco di analisi asintotica tramite conteggio esatto dei confronti (Selection Sort, Merge Sort e Two-Sum)**: confronto `O(n^2)`, `O(n log n)` e `O(n)` con `memcmp`. Difficoltà: 3/5.
- **23.2 — Coda di priorità generica opaca su heap binario (con heapify O(n)) per uno schedulatore di task**: 3 file (`heap_gen.h/c`, `main.c`) su `task_t` con tie-breaking FIFO. Difficoltà: 4/5.
- **23.3 — Albero AVL completo con rotazioni singole (LL/RR) e doppie (LR/RL), rimozione e verifica dell'invariante**: 3 file (`avl.h/c`, `main.c`) con contatori rotazioni e verifica BST/AVL. Difficoltà: 5/5.
- **23.4 — Motore di autocompletamento su trie con conteggio prefissi O(L) e rimozione potata**: 3 file (`trie.h/c`, `main.c`) con suggerimenti DFS e potatura. Difficoltà: 4/5.
- **23.5 — Grafo orientato con liste di adiacenza: BFS, DFS, rilevamento cicli e ordinamento topologico**: 3 file (`grafo.h/c`, `main.c`) con vicini ordinati e DFS a 3 colori. Difficoltà: 4/5.
- **23.6 — Algoritmo di Dijkstra O((V + E) log V) integrato con la coda di priorità generica e ricostruzione dei cammini**: 5 file (`coda_prio.h/c`, `dijkstra.h/c`, `main.c`) con *lazy deletion* e rifiuto pesi negativi. Difficoltà: 5/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 8 (ricerca binaria), cap. 11 (memoria dinamica, array dinamici), cap. 12 (`struct`), cap. 15 (`void *`, `memcpy`), cap. 16 (puntatori a funzione/callback), cap. 17 (code FIFO, pile, liste, BST), cap. 18 (tabelle hash), cap. 19 (tipi opachi, compilazione separata), cap. 21 (`<stdckdint.h>`, `ckd_add`/`ckd_mul`).
- Rinvii in avanti: cap. 25 (orologio di sistema, misure temporali e cache del processore) in `23_01.md` e `23_99.md`.

## Affermazioni forti
- In un heap binario su `size_t`, verificare sempre `i > 0` prima di calcolare `(i - 1) / 2` (altrimenti wrap-around a `SIZE_MAX` e UB).
- Nelle rotazioni AVL aggiornare sempre prima l'altezza del vecchio nodo radice sceso di livello, poi quella della nuova radice.
- Nel trie validare sempre `c >= 'a' && c <= 'z'` prima di calcolare `c - 'a'` per evitare indici fuori dai limiti (UB).
- Nei grafi validare sempre `u < V` e `v < V`; usare 3 colori nella DFS per rilevare cicli orientati (un flag booleano non basta).
- In Dijkstra tutti i pesi devono essere non negativi (`w >= 0`): anche un solo peso negativo rompe l'invariante goloso.

## Stile del codice
- C23 (`constexpr`, `nullptr`, `bool`, `= {}` per zero-init, `PRIu64`/`PRId32`).
- Indentazione a 4 spazi, graffe sempre presenti, `snake_case` italiano, `size_t` per indici e dimensioni, `ckd_mul`/`ckd_add` per prevenire overflow.
