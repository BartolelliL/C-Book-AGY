# Capitolo 23 — Strutture dati e algoritmi avanzati

> **In questo capitolo imparerai a:**
> - Analizzare la complessità asintotica con la notazione O verificandola tramite conteggio delle operazioni
> - Implementare un heap binario generico e usarlo come coda di priorità
> - Costruire un albero AVL con rotazioni semplici e doppie e un trie per ricerche su prefissi
> - Rappresentare grafi con liste di adiacenza ed eseguire visite in ampiezza, in profondità e l'algoritmo di Dijkstra

> **Ti servono:** memoria dinamica (capitolo 11), strutture (capitolo 12), programmazione generica con `void *` (capitolo 15), puntatori a funzione e callback (capitolo 16), strutture dati dinamiche e alberi binari di ricerca (capitolo 17), tabelle hash (capitolo 18), compilazione separata e tipi opachi (capitolo 19) e aritmetica controllata con `<stdckdint.h>` (capitolo 21).

Nel capitolo 22 hai imparato a controllare in modo esplicito come la memoria viene allineata, assegnata e liberata. A questo punto conosci gli strumenti del linguaggio C per costruire moduli riutilizzabili e sicuri: il passo successivo è scegliere le strutture dati e gli algoritmi che mantengono veloci i tuoi programmi anche quando i dati crescono di ordini di grandezza.

Un programma corretto su dieci elementi può diventare inutilizzabile su un milione se la struttura dati scelta degenera nel caso peggiore. Un albero binario di ricerca non bilanciato si riduce a una lista lineare se riceve chiavi ordinate; una scansione lineare per trovare il prossimo evento urgente rallenta ogni volta che la coda si allunga; una tabella hash non permette di elencare rapidamente tutte le parole che iniziano con un certo prefisso.

In questo capitolo impari prima a misurare la crescita del costo di un algoritmo in modo indipendente dall'hardware con la notazione O e il conteggio esatto delle operazioni. Costruirai poi quattro strutture dati fondamentali dell'informatica — l'heap binario come coda di priorità generica, l'albero AVL autobilanciato, il trie per le chiavi testuali e il grafo con liste di adiacenza — fino a integrare la coda di priorità generica nell'algoritmo di Dijkstra per i cammini minimi.

## 23.1 Complessità asintotica e notazione O

Quando confronti due algoritmi che risolvono lo stesso problema, la prima tentazione è cronometrarli e confrontare i secondi trascorsi. Quel numero, però, dipende dal processore, dalla frequenza di clock, dal compilatore, dai flag di ottimizzazione e dagli altri programmi in esecuzione in quel momento. Un algoritmo lento su un computer potente può battere temporaneamente un algoritmo migliore su un portatile carico di lavoro, ma appena la dimensione dei dati cresce la situazione si ribalta in modo irreversibile.

Per ragionare in modo rigoroso e indipendente dalla macchina si usa la **complessità asintotica** (*asymptotic complexity*): una misura di come cresce il numero di operazioni di un algoritmo al crescere della dimensione `n` dell'input, espressa con la **notazione O** (*Big-O notation*). La notazione O descrive come cresce il costo di un algoritmo — sia in tempo (numero di operazioni elementari, come confronti o assegnamenti) sia in spazio (memoria ausiliaria allocata oltre all'input) — fornendo un limite superiore al comportamento per `n` grande.

Nella notazione O si trascurano le costanti moltiplicative e i termini di ordine inferiore, perché al crescere di `n` è il termine dominante a determinare la curva di crescita. Un algoritmo che esegue `3n^2 + 12n + 5` operazioni appartiene alla classe `O(n^2)`: quando `n` raddoppia, il numero di operazioni quadruplica circa, qualunque sia la costante davanti a `n^2`. Le classi principali, ordinate dalla più veloce alla più lenta, sono:

```text
O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(2^n)
```

Molte di queste classi le hai già incontrate nei capitoli precedenti:

- **`O(1)` (costante)**: il costo non dipende da `n`. Esempi: l'accesso a un elemento di un array tramite indice `a[i]`, l'inserimento in testa a una lista concatenata, l'allocazione su un allocatore ad arena o l'accesso medio in una tabella hash ben dimensionata.
- **`O(log n)` (logaritmica)**: a ogni passo il problema si dimezza. Esempio: la ricerca binaria su un array ordinato del capitolo 8. Passare da 1.000 a 1.000.000 di elementi aggiunge appena una decina di confronti.
- **`O(n)` (lineare)**: il costo cresce in proporzione diretta a `n`. Esempi: la scansione lineare di un array, `strlen`, `memcpy` o la distruzione di una lista concatenata.
- **`O(n log n)` (linearitmica)**: tipica degli algoritmi di ordinamento efficienti basati su confronti come merge sort (e in media `qsort`), che dividono ricorsivamente i dati a metà (`log n` livelli) eseguendo lavoro lineare su ciascun livello.
- **`O(n^2)` (quadratica)**: tipica di due cicli annidati che confrontano ogni coppia di elementi, come l'ordinamento per inserzione o per selezione nel caso peggiore, o la ricerca di duplicati per forza bruta.
- **`O(2^n)` (esponenziale)**: il costo raddoppia a ogni elemento aggiunto, come nella generazione di tutti i sottoinsiemi di un insieme. Diventa impraticabile già per poche decine di elementi.

Un algoritmo non compie sempre lo stesso numero di operazioni su tutti gli input di dimensione `n`. Occorre quindi distinguere quattro prospettive di analisi:

- **Caso migliore**: l'input più favorevole (per esempio, cercare un elemento che si trova subito in prima posizione nella ricerca lineare: `O(1)`). Di rado basta per valutare un algoritmo.
- **Caso peggiore**: l'input più sfavorevole per ogni dimensione `n`. Offre una garanzia invalicabile: se un algoritmo è `O(log n)` nel caso peggiore, nessun input potrà farlo rallentare oltre quella curva.
- **Caso medio**: il costo atteso su una distribuzione di input tipici (come `O(1)` medio nella tabella hash del capitolo 18, a fronte di un caso peggiore `O(n)` se tutte le chiavi collidono).
- **Costo ammortizzato**: la media garantita su una *sequenza* di operazioni, anche nel caso peggiore. L'esempio classico è l'array dinamico del capitolo 11 che raddoppia la capacità con `realloc` quando è pieno. Un singolo inserimento che innesca il raddoppio costa `O(n)` per copiare gli elementi, ma ciò avviene solo dopo `1, 2, 4, 8, ...` inserimenti; su `n` inserimenti consecutivi il numero totale di copie resta minore di `2n`, quindi il costo medio garantito di ogni inserimento è `O(1)` ammortizzato. Se invece aumentassi la capacità di una quantità fissa (per esempio `+10` ogni volta), il costo totale di `n` inserimenti salirebbe a `O(n^2)`.

Come puoi verificare sperimentalmente la classe di complessità di un algoritmo senza dipendere dall'orologio di sistema (che vedremo nel capitolo 25)? La tecnica più pulita e riproducibile è inserire un contatore intero che registra le operazioni elementari eseguite — per esempio i confronti tra chiavi — e osservare come cresce quel numero quando raddoppi o quadruplichi `n`. Secondo lo standard C23, il conteggio delle operazioni tramite contatori `uint64_t` è completamente definito e deterministico su qualunque piattaforma; per prevenire overflow dei contatori o degli indici nei calcoli di dimensioni dinamiche si affiancano i tipi a larghezza fissa di `<stdint.h>` e le macro controllate di `<stdckdint.h>`.

### Esempio guidato

Il programma seguente genera un array ordinato strettamente crescente e misura, al quadruplicare di `n` (`16`, `64`, `256`, `1024`), il numero esatto di confronti eseguiti nel caso peggiore da tre algoritmi: ricerca binaria `O(log n)` (chiave assente), ricerca lineare `O(n)` (chiave assente) e rilevamento di duplicati tramite doppio ciclo `O(n^2)` (nessun duplicato presente).

<!-- cod: id=23.1-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static bool ricerca_binaria(const int32_t *a, size_t n, int32_t chiave,
                            uint64_t *confronti) {
    *confronti = 0;
    size_t sx = 0;
    size_t dx = n;
    while (sx < dx) {
        size_t mid = sx + (dx - sx) / 2;
        ++(*confronti);
        if (a[mid] == chiave) {
            return true;
        }
        if (a[mid] < chiave) {
            sx = mid + 1;
        } else {
            dx = mid;
        }
    }
    return false;
}

static bool ricerca_lineare(const int32_t *a, size_t n, int32_t chiave,
                            uint64_t *confronti) {
    *confronti = 0;
    for (size_t i = 0; i < n; ++i) {
        ++(*confronti);
        if (a[i] == chiave) {
            return true;
        }
    }
    return false;
}

static bool ha_duplicati(const int32_t *a, size_t n, uint64_t *confronti) {
    *confronti = 0;
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = i + 1; j < n; ++j) {
            ++(*confronti);
            if (a[i] == a[j]) {
                return true;
            }
        }
    }
    return false;
}

int main(void) {
    constexpr size_t TAGLIE[] = {16, 64, 256, 1024};
    constexpr size_t N_MAX = 1024;

    int32_t *dati = malloc(N_MAX * sizeof(*dati));
    if (dati == nullptr) {
        fprintf(stderr, "Errore: memoria insufficiente.\n");
        return EXIT_FAILURE;
    }
    for (size_t i = 0; i < N_MAX; ++i) {
        dati[i] = (int32_t)(i * 2);
    }

    printf("%6s | %10s | %10s | %12s\n", "n", "O(log n)", "O(n)", "O(n^2)");
    printf("-------+------------+------------+-------------\n");
    for (size_t t = 0; t < sizeof(TAGLIE) / sizeof(TAGLIE[0]); ++t) {
        size_t n = TAGLIE[t];
        uint64_t c_bin = 0, c_lin = 0, c_quad = 0;
        (void)ricerca_binaria(dati, n, -1, &c_bin);
        (void)ricerca_lineare(dati, n, -1, &c_lin);
        (void)ha_duplicati(dati, n, &c_quad);
        printf("%6zu | %10" PRIu64 " | %10" PRIu64 " | %12" PRIu64 "\n",
               n, c_bin, c_lin, c_quad);
    }

    free(dati);
    return 0;
}
```

```output
     n |   O(log n) |       O(n) |       O(n^2)
-------+------------+------------+-------------
    16 |          5 |         16 |          120
    64 |          7 |         64 |         2016
   256 |          9 |        256 |        32640
  1024 |         11 |       1024 |       523776
```

Osserva i numeri nella tabella mentre `n` quadruplica a ogni riga:

- Nella colonna `O(log n)`, ogni volta che `n` viene moltiplicato per `4` il numero di confronti aumenta di appena `2` (perché $\log_2 4 = 2$). Con `n = 1024` bastano `11` confronti.
- Nella colonna `O(n)`, il numero di confronti cresce esattamente di un fattore `4` a ogni riga: `16`, `64`, `256`, `1024`.
- Nella colonna `O(n^2)`, il doppio ciclo esegue esattamente $n(n - 1)/2$ confronti: al quadruplicare di `n` il conteggio cresce di quasi `16` volte, superando mezzo milione di operazioni già per `1024` elementi.
- L'uso di `uint64_t` e degli specificatori `PRIu64` garantisce che i contatori non vadano in overflow anche per taglie molto più grandi, e il risultato è identico su qualsiasi computer e sistema operativo.

> **Approfondimento — Costanti nascoste e dimensione pratica di `n`**
> La notazione O descrive la tendenza asintotica per `n` grande, ma trascura le costanti moltiplicative. Per input molto piccoli (per esempio una decina di elementi), un algoritmo `O(n^2)` dal ciclo interno compatto come l'ordinamento per inserzione può eseguire meno istruzioni reali di un algoritmo `O(n log n)` che alloca memoria ausiliaria e fa chiamate ricorsive. Per questo molte librerie ibride usano un algoritmo `O(n log n)` sui blocchi grandi e passano all'inserzione sotto una piccola soglia. Nel capitolo 25 vedremo inoltre come la cache del processore influenzi in modo decisivo le prestazioni reali a parità di classe asintotica.

### Esercizio 23.1 — Banco di analisi asintotica tramite conteggio esatto dei confronti (Selection Sort, Merge Sort e Two-Sum)

**Descrizione**

Scrivi un programma C che confronti sperimentalmente la **complessità asintotica** di algoritmi appartenenti a classi diverse della **notazione O** contando esattamente il numero di confronti elementari in contatori `uint64_t`. Implementa quattro funzioni:

1. `void ordina_selezione(int32_t *a, size_t n, uint64_t *confronti)` (`O(n^2)`, incrementa `*confronti` a ogni confronto `a[j] < a[min_idx]`);
2. `bool ordina_merge(int32_t *a, size_t n, uint64_t *confronti)` (`O(n log n)`, alloca un solo buffer temporaneo con `malloc`, divide a metà con `mid = sx + (dx - sx) / 2`, fonde incrementando `*confronti` a ogni confronto `a[i] <= a[j]` e libera il buffer);
3. `bool coppia_forza_bruta(const int32_t *a, size_t n, int64_t bersaglio, uint64_t *confronti)` (`O(n^2)`, verifica tutte le coppie `i < j`);
4. `bool coppia_due_indici(const int32_t *a, size_t n, int64_t bersaglio, uint64_t *confronti)` (`O(n)` su array ordinato crescente, muovendo `sx` e `dx` fino a `sx < dx`).

In `main` leggi da `stdin` comandi fino a fine input: `SORT <n> <v0> ... <v{n-1}>` (`0 <= n <= 128`, ordina due copie con entrambi gli algoritmi, verifica con `memcmp` che i risultati coincidano e stampa la sequenza ordinata e i due conteggi); `TWOSUM <bersaglio> <n> <v0> ... <v{n-1}>` (array già ordinato crescente, `0 <= n <= 128`, esegue entrambe le ricerche verificando che gli esiti coincidano); `SCALA <k>` (`1 <= k <= 128`, genera la sequenza decrescente `k, k-1, ..., 1` e confronta i confronti di `ordina_selezione` e `ordina_merge`). Riproduci esattamente il formato di output dell'esempio.

**Concetti da tenere a mente**

- classi asintotiche `O(n)`, `O(n log n)` e `O(n^2)` verificate tramite conteggio deterministico dei confronti
- implementazione ricorsiva di merge sort con un solo buffer ausiliario allocato sullo heap
- tecnica a due indici `O(n)` su sequenza ordinata confrontata con la forza bruta `O(n^2)`
- verifica di equivalenza dei risultati tramite `memcmp` e gestione corretta dei casi limite `n = 0` e `n = 1`

**Domande guida**

1. Quanti confronti esegue sempre `ordina_selezione` su un array di `n` elementi, e perché il risultato non cambia se l'array è già ordinato?
2. Come cambia il rapporto tra i confronti di `ordina_selezione` e quelli di `ordina_merge` quando `n` passa da `8` a `32` e poi a `128`?
3. Perché `coppia_due_indici` garantisce complessità `O(n)` e richiede come precondizione che l'array sia ordinato?
4. Perché conviene allocare un unico buffer temporaneo prima della ricorsione in `ordina_merge` anziché chiamare `malloc` a ogni chiamata ricorsiva?

**Esempio di esecuzione**

```input
SORT 6 5 2 8 1 9 3
TWOSUM 17 6 1 3 5 8 9 14
TWOSUM 100 6 1 3 5 8 9 14
SCALA 8
SCALA 32
SCALA 128
```

```output
SORT(6): 1 2 3 5 8 9 | sel_cmp=15 merge_cmp=10 ok=1
TWOSUM(17): TROVATA | bruta_cmp=9 lineare_cmp=2
TWOSUM(100): ASSENTE | bruta_cmp=15 lineare_cmp=5
SCALA(8): sel_cmp=28 merge_cmp=12 ok=1
SCALA(32): sel_cmp=496 merge_cmp=80 ok=1
SCALA(128): sel_cmp=8128 merge_cmp=448 ok=1
```

## 23.2 Heap binario e coda di priorità

Una coda FIFO (capitolo 17) serve gli elementi rigorosamente nell'ordine di arrivo. Molti programmi reali, però, devono estrarre sempre l'elemento più urgente: uno schedulatore di processi sceglie il task con priorità più alta, un simulatore a eventi estrae il prossimo evento nel tempo, e l'algoritmo di Dijkstra (sotto-sezione 23.6) seleziona il vertice più vicino non ancora definitivo. Questa astrazione si chiama **coda di priorità** (*priority queue*): una struttura dati da cui si estrae sempre l'elemento con priorità massima o minima.

Se provi a realizzare una coda di priorità con le strutture del capitolo 17, ottieni un compromesso sbilanciato:

- con un array non ordinato l'inserimento in fondo costa `O(1)` ammortizzato, ma trovare ed estrarre il minimo richiede una scansione `O(n)`;
- con una lista concatenata mantenuta ordinata l'estrazione in testa costa `O(1)`, ma l'inserimento richiede di cercare la posizione giusta in `O(n)`.

Un **heap binario** (*binary heap*) risolve il problema eseguendo sia l'inserimento sia l'estrazione della cima in tempo `O(log n)`, e la lettura della cima senza estrarla in `O(1)`. Attenzione a non confondere questo termine con l'**heap** della memoria dinamica (`malloc`/`free`, capitolo 11): condividono il nome inglese per ragioni storiche, ma sono concetti completamente distinti.

Un heap binario è un **albero binario completo** (tutti i livelli sono pieni tranne eventualmente l'ultimo, riempito da sinistra verso destra) in cui ogni nodo rispetta la **proprietà d'ordine** rispetto ai propri figli: in un **min-heap** ogni nodo ha valore minore o uguale a quello dei suoi figli (quindi il minimo assoluto sta sempre alla radice); in un **max-heap** ogni nodo ha valore maggiore o uguale a quello dei figli.

Poiché l'albero è completo e privo di buchi, non servono puntatori `sx` e `dx` in ogni nodo: l'intero albero si memorizza in modo implicito in un array contiguo a indice base `0`, leggendolo livello per livello da sinistra a destra:

```text
Albero logico (min-heap)              Array contiguo (indici 0..6)
          [3]                         indice:  0   1   2   3   4   5   6
        /     \                       valore: [3,  7,  9, 14, 18, 25, 12]
      [7]     [9]
     /   \   /   \                    Per il nodo a indice i:
   [14] [18][25] [12]                   genitore(i)  = (i - 1) / 2   (solo se i > 0)
                                        figlio_sx(i) = 2 * i + 1
                                        figlio_dx(i) = 2 * i + 2
```

Questa rappresentazione implicita elimina del tutto il costo in memoria dei puntatori e mantiene i dati contigui in RAM. Le formule di navigazione sono semplici operazioni aritmetiche: dal nodo `i = 1` (valore `7`), il genitore è `(1 - 1) / 2 = 0` (`3`), il figlio sinistro è `2 * 1 + 1 = 3` (`14`) e il figlio destro è `2 * 1 + 2 = 4` (`18`).

Fai attenzione a un dettaglio cruciale del C: gli indici hanno tipo `size_t` (senza segno). Calcolare `(i - 1) / 2` quando `i == 0` provoca l'avvolgimento di `0 - 1` a `SIZE_MAX`, generando un indice enorme e un successivo accesso fuori dai limiti, che nello standard C23 è **comportamento indefinito**. Occorre quindi verificare sempre `i > 0` prima di calcolare il genitore.

Le operazioni fondamentali su un min-heap binario sono tre:

1. **Inserimento con risalita (*sift-up*, `O(log n)`)**: aggiungi il nuovo elemento in coda all'array (indice `len`, allargando prima l'array con `realloc` e `ckd_mul` se `len == cap`). Finché `i > 0` e l'elemento a indice `i` è minore del proprio genitore `p = (i - 1) / 2`, li scambi e poni `i = p`. Poiché l'altezza di un albero completo di `n` nodi è $\lfloor \log_2 n \rfloor$, il ciclo esegue al più `O(log n)` scambi.
2. **Estrazione della radice con discesa (*sift-down*, `O(log n)`)**: la radice `dati[0]` è il minimo. Copiala nel parametro di uscita, decrementa `len` e sposta l'ultimo elemento `dati[len]` alla radice `dati[0]`. Poi fai scendere il nodo dalla radice: finché almeno uno dei suoi figli esistenti (`2 * i + 1 < len` o `2 * i + 2 < len`) è più piccolo del nodo corrente, scambia il nodo con il figlio *minore* tra i due e continua da quella posizione. Anche la discesa tocca al più un nodo per livello, quindi costa `O(log n)`.
3. **Costruzione bottom-up (*heapify* di Floyd, `O(n)`)**: se possiedi già un array di `n` elementi, invece di inserirli uno alla volta in `O(n log n)`, li copi nell'array dello heap e applichi la discesa (*sift-down*) a tutti i nodi interni partendo dall'ultimo genitore `(n / 2) - 1` fino alla radice `0`. Il ciclo si scrive in modo sicuro con `size_t` come `for (size_t i = n / 2; i > 0; --i) { scendi(h, i - 1); }`, evitando il decremento sotto zero di `size_t`.

Per rendere la struttura riutilizzabile con qualsiasi tipo di dato — interi, strutture `task_t` o coppie `(distanza, vertice)` nell'algoritmo di Dijkstra — si applicano le tecniche dei capitoli 15, 16 e 19: si incapsula lo heap come **tipo opaco** (`typedef struct heap_gen heap_gen_t;`), si memorizzano i dati in un buffer `unsigned char *dati` con dimensione elemento `dim_elem`, si indirizza l'elemento `i` con `dati + i * dim_elem`, si copiano e scambiano gli elementi con `memcpy` (usando un piccolo buffer temporaneo di `dim_elem` byte allocato una volta sola in creazione) e si delega l'ordine a una **callback** di confronto `int (*cmp)(const void *a, const void *b)`. Le operazioni su array dinamici generici tramite `memcpy` e callback di confronto sono completamente definite dallo standard C23.

> **Se vieni da Python** — In Python il modulo `heapq` fornisce già una coda di priorità pronta all'uso sulle liste, senza dover scrivere la gestione della memoria. In C progettare un heap binario generico su array contiguo richiede di gestire esplicitamente `realloc`, `memcpy` e la callback di confronto, ma ti permette di memorizzare strutture per valore senza allocazioni per singolo nodo e di avere pieno controllo su memoria e prestazioni.

### Esempio guidato

Il programma seguente implementa un min-heap binario di `int` su array dinamico con `risali` (*sift-up*), `scendi` (*sift-down*) e la costruzione bottom-up (*heapify* `O(n)`). Verifica la proprietà di min-heap dopo ogni operazione ed estrae gli elementi uno alla volta in ordine crescente.

<!-- cod: id=23.2-a tipo=programma -->
```c
#include <stdckdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int *dati;
    size_t len;
    size_t cap;
} min_heap_t;

static void scambia(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

static void risali(min_heap_t *h, size_t i) {
    while (i > 0) {
        size_t p = (i - 1) / 2;
        if (h->dati[i] >= h->dati[p]) {
            break;
        }
        scambia(&h->dati[i], &h->dati[p]);
        i = p;
    }
}

static void scendi(min_heap_t *h, size_t i) {
    while (true) {
        size_t sx = 2 * i + 1, dx = sx + 1, min_i = i;
        if (sx < h->len && h->dati[sx] < h->dati[min_i]) { min_i = sx; }
        if (dx < h->len && h->dati[dx] < h->dati[min_i]) { min_i = dx; }
        if (min_i == i) { break; }
        scambia(&h->dati[i], &h->dati[min_i]);
        i = min_i;
    }
}

static bool heap_inserisci(min_heap_t *h, int valore) {
    if (h->len == h->cap) {
        size_t nuova = (h->cap == 0) ? 4 : 0;
        if (h->cap > 0 && ckd_mul(&nuova, h->cap, 2)) { return false; }
        int *nb = realloc(h->dati, nuova * sizeof(*nb));
        if (nb == nullptr) { return false; }
        h->dati = nb;
        h->cap = nuova;
    }
    h->dati[h->len] = valore;
    risali(h, h->len);
    ++h->len;
    return true;
}

static bool heap_estrai(min_heap_t *h, int *out) {
    if (h->len == 0) { return false; }
    *out = h->dati[0];
    --h->len;
    if (h->len > 0) {
        h->dati[0] = h->dati[h->len];
        scendi(h, 0);
    }
    return true;
}

static bool verifica_heap(const min_heap_t *h) {
    for (size_t i = 0; i < h->len; ++i) {
        size_t sx = 2 * i + 1, dx = sx + 1;
        if (sx < h->len && h->dati[i] > h->dati[sx]) { return false; }
        if (dx < h->len && h->dati[i] > h->dati[dx]) { return false; }
    }
    return true;
}

int main(void) {
    min_heap_t h = {};
    int serie1[] = {14, 5, 19, 3, 8};
    for (size_t i = 0; i < 5; ++i) {
        if (!heap_inserisci(&h, serie1[i])) { free(h.dati); return EXIT_FAILURE; }
    }
    printf("Dopo inserimenti (valido=%d, cima=%d):", verifica_heap(&h) ? 1 : 0, h.dati[0]);
    int v = 0;
    while (heap_estrai(&h, &v)) {
        printf(" %d", v);
    }
    printf("\n");

    int serie2[] = {40, 12, 25, 7, 18, 3, 9};
    size_t n2 = sizeof(serie2) / sizeof(serie2[0]);
    int *nb = realloc(h.dati, n2 * sizeof(*nb));
    if (nb == nullptr) { free(h.dati); return EXIT_FAILURE; }
    h.dati = nb; h.cap = n2; h.len = n2;
    memcpy(h.dati, serie2, n2 * sizeof(*nb));
    for (size_t i = n2 / 2; i > 0; --i) { scendi(&h, i - 1); }

    printf("Dopo heapify O(n) (valido=%d, cima=%d):", verifica_heap(&h) ? 1 : 0, h.dati[0]);
    while (heap_estrai(&h, &v)) {
        printf(" %d", v);
    }
    printf("\n");
    free(h.dati);
    return 0;
}
```

```output
Dopo inserimenti (valido=1, cima=3): 3 5 8 14 19
Dopo heapify O(n) (valido=1, cima=3): 3 7 9 12 18 25 40
```

Analizza i punti chiave dell'implementazione:

- In `risali`, la condizione `while (i > 0)` garantisce che `(i - 1) / 2` non venga mai valutato per `i == 0`.
- In `scendi`, l'indice `min_i` viene confrontato prima con il figlio sinistro `sx` e poi con il destro `dx`, verificando sempre `sx < h->len` e `dx < h->len` prima di leggere l'array. Se nessuno dei due figli è più piccolo di `h->dati[i]`, la proprietà d'ordine è già soddisfatta e il ciclo termina.
- Nella seconda parte di `main`, i sette elementi di `serie2` vengono copiati in blocco e sistemati dal basso verso l'alto con `for (size_t i = n2 / 2; i > 0; --i) { scendi(&h, i - 1); }`. L'estrazione ripetuta produce esattamente la sequenza ordinata crescente, confermando la proprietà di min-heap.

> **Approfondimento — Perché l'algoritmo di Floyd costa `O(n)` e non `O(n log n)`**
> A prima vista chiamare `scendi` (che nel caso peggiore costa `O(log n)`) su `n / 2` nodi sembrerebbe costare `O(n log n)`. In un albero binario completo, però, la maggior parte dei nodi si trova vicino al fondo: metà dei nodi sono foglie che non scendono affatto (`0` livelli), un quarto sono genitori delle foglie e possono scendere al più di `1` livello, un ottavo al più di `2` livelli e così via. Il lavoro totale è limitato da $n \sum_{k=1}^{\infty} \frac{k}{2^{k+1}} = n$, cioè è strettamente lineare `O(n)`.

### Esercizio 23.2 — Coda di priorità generica opaca su heap binario (con heapify O(n)) per uno schedulatore di task

**Descrizione**

Realizza su tre file (`heap_gen.h`, `heap_gen.c`, `main.c`) una **coda di priorità** generica basata su un **heap binario** come **tipo opaco** `heap_gen_t`, applicata a uno schedulatore di attività.

1. In `heap_gen.h` (protetto da `HEAP_GEN_H`) definisci `typedef struct heap_gen heap_gen_t;`, `typedef int (*heap_cmp_fn)(const void *a, const void *b);` (valore `< 0` significa che `a` ha priorità più alta di `b` e sale verso la radice) e dichiara:
   - `heap_gen_t *heap_crea(size_t dim_elem, size_t cap_iniziale, heap_cmp_fn cmp);`
   - `void heap_distruggi(heap_gen_t *h);`
   - `bool heap_inserisci(heap_gen_t *h, const void *elem);` (`O(log n)` con raddoppio dinamico controllato da `ckd_mul`)
   - `bool heap_estrai(heap_gen_t *h, void *out);` (`O(log n)`)
   - `bool heap_cima(const heap_gen_t *h, void *out);` (`O(1)`)
   - `bool heap_costruisci(heap_gen_t *h, const void *dati, size_t n);` (sostituisce il contenuto dello heap copiando gli `n` elementi ed eseguendo *heapify* bottom-up di Floyd in tempo `O(n)`)
   - `size_t heap_len(const heap_gen_t *h);`
2. In `heap_gen.c` implementa le operazioni generiche usando `unsigned char *dati`, `memcpy` e un piccolo buffer di scambio `unsigned char *tmp_scambio` di `dim_elem` byte allocato una volta sola in `heap_crea`.
3. In `main.c` definisci `typedef struct task { int32_t priorita; uint32_t ordine; char nome[20]; } task_t;` con comparatore che ordina per `priorita` crescente (valore più basso = più urgente) e, a parità di priorità, per `ordine` crescente (FIFO). Gestisci da `stdin` i comandi `PUSH <prio> <nome>`, `PEEK`, `POP`, `BUILD <k>` (seguito da `k` righe `<prio> <nome>`, azzerando il contatore `ordine` a `0` per i nuovi `k` task) e `DRAIN`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- rappresentazione di un heap binario in array contiguo con formule `(i - 1) / 2`, `2 * i + 1` e `2 * i + 2`
- operazioni di risalita (*sift-up*), discesa (*sift-down*) e costruzione lineare bottom-up (*heapify* di Floyd)
- programmazione generica con `void *`, `dim_elem`, `memcpy` e callback di confronto
- stabilizzazione dell'ordine tra elementi a pari priorità mediante un contatore monotono di inserimento

**Domande guida**

1. Perché un heap binario non è naturalmente stabile su elementi con la stessa priorità e come risolve il problema il campo `ordine`?
2. Da quale indice parte il ciclo di `heap_costruisci` (heapify bottom-up di Floyd) e perché non è necessario chiamare `scendi` sulle foglie?
3. Come calcoli in `heap_gen.c` l'indirizzo dell'elemento a indice `i` quando il tipo concreto degli elementi è sconosciuto a tempo di compilazione?
4. Quale controllo devi fare prima di calcolare `(i - 1) / 2` dentro la funzione di risalita?

**Esempio di esecuzione**

```input
PUSH 5 Backup
PUSH 2 Rete
PUSH 2 Disco
PUSH 1 Allarme
PEEK
POP
POP
POP
POP
POP
BUILD 4
10 Report
3 Log
3 Audit
1 Critico
DRAIN
```

```output
PEEK: Allarme (prio=1, ord=3)
POP: Allarme (prio=1, ord=3)
POP: Rete (prio=2, ord=1)
POP: Disco (prio=2, ord=2)
POP: Backup (prio=5, ord=0)
POP: VUOTA
BUILD: n=4
DRAIN: Critico(1,3) Log(3,1) Audit(3,2) Report(10,0)
```

## 23.3 Alberi AVL e rotazioni di bilanciamento

Nel capitolo 17 hai costruito un albero binario di ricerca (BST) e hai visto che le operazioni di ricerca, inserimento e rimozione dipendono dall'altezza dell'albero. Se i nodi sono distribuiti in modo equilibrato, l'altezza è `O(log n)` e le operazioni sono rapide. Se però inserisci chiavi già ordinate (per esempio `10, 20, 30, 40, 50, 60`), ogni nuovo nodo finisce sempre sul ramo destro: il BST degenera in una lista concatenata di altezza `n` e tutte le operazioni scadono a `O(n)`.

Un **albero AVL** (*AVL tree*, dalle iniziali degli inventori Adelson-Velsky e Landis) elimina questa degenerazione mantenendo automaticamente l'albero bilanciato dopo ogni modifica. Un albero AVL è un albero binario di ricerca autobilanciato in cui, per ogni nodo `u`, le altezze dei suoi due sottoalberi differiscono al massimo di uno.

Per verificare questa proprietà in tempo `O(1)` senza ricalcolare ogni volta l'altezza dell'intero sottoalbero, ogni nodo memorizza il proprio campo `altezza`:

- un sottoalbero vuoto (`nullptr`) ha altezza `0`;
- una foglia ha altezza `1`;
- un nodo `u` qualsiasi ha `altezza = 1 + max(h(u->sx), h(u->dx))`.

Si definisce **fattore di bilanciamento** del nodo `u` la differenza tra l'altezza del sottoalbero sinistro e quella del sottoalbero destro:

```text
fb(u) = h(u->sx) - h(u->dx)
```

L'invariante AVL impone che per ogni nodo dell'albero valga `|fb(u)| <= 1`, cioè `fb(u)` appartenga sempre all'insieme `{-1, 0, +1}`. Quando un inserimento o una rimozione fa salire `fb(u)` a `+2` o scendere a `-2`, l'invariante viene violato e va ripristinato risalendo lungo il cammino fino alla radice.

Esistono esattamente quattro configurazioni di sbilanciamento, chiamate **LL**, **RR**, **LR** e **RL** dal percorso di due passi che scende nel ramo più pesante:

```text
Caso LL (fb(y) = +2, fb(x) >= 0)      Caso RR (fb(x) = -2, fb(y) <= 0)
-> rotazione singola a destra         -> rotazione singola a sinistra

       y                x                  x                   y
      / \              / \                / \                 / \
     x   T3   ===>   T1   y             T1   y     ===>      x   T3
    / \                  / \                / \             / \
  T1   T2              T2   T3            T2   T3         T1   T2
```

Osserva come la rotazione singola destra (`ruota_dx`) sul nodo `y` sposti `x` al posto della radice del sottoalbero, faccia diventare `y` il figlio destro di `x` e trasferisca il sottoalbero intermedio `T2` (`x->dx`) a figlio sinistro di `y`. L'ordine delle chiavi resta intatto (`T1 < x < T2 < y < T3`), quindi la proprietà di albero binario di ricerca è preservata e il fattore di bilanciamento rientra nell'intervallo `[-1, +1]`. La rotazione singola sinistra (`ruota_sx`) è perfettamente simmetrica.

Un dettaglio fondamentale riguarda l'aggiornamento delle altezze: in `ruota_dx`, dopo aver aggiornato i puntatori, `y` è diventato figlio di `x`, quindi devi aggiornare **prima** l'altezza di `y` e **solo dopo** quella di `x`. Aggiornare dal basso verso l'alto garantisce che la nuova radice legga l'altezza già corretta del proprio figlio.

Quando invece il sottoalbero pesante piega "a gomito" verso l'interno (`fb(y) = +2` con `fb(y->sx) < 0`, oppure `fb(x) = -2` con `fb(x->dx) > 0`), una sola rotazione non basta perché sposta lo sbilanciamento sull'altro lato. Servono allora le **rotazioni doppie**, composte da due rotazioni singole consecutive:

```text
Caso LR (fb(z) = +2, fb(x) < 0)       Caso RL (fb(z) = -2, fb(x) > 0)
1) ruota_sx(x)   2) ruota_dx(z)       1) ruota_dx(x)   2) ruota_sx(z)

     z           z          y              z           z            y
    /           /          / \              \           \          / \
   x    ===>   y    ===>  x   z              x   ===>    y  ===>  z   x
    \         /                             /             \
     y       x                             y               x
```

Ogni rotazione (singola o doppia) modifica un numero fisso di puntatori e ricalcola due o tre altezze: costa quindi tempo costante `O(1)`. Unendo tutte e quattro le casistiche in un'unica funzione `bilancia(n)` invocata al ritorno dalla ricorsione, ottieni il ribilanciamento automatico sia nell'inserimento sia nella rimozione. Nel caso dell'inserimento basta al più una rotazione (singola o doppia) sul primo antenato sbilanciato per riportare l'altezza del sottoalbero al valore precedente; nella rimozione, invece, una rotazione può ridurre l'altezza del sottoalbero di `1`, richiedendo di verificare e bilanciare anche gli antenati superiori fino alla radice — ma il tempo totale resta comunque `O(log n)`.

Secondo lo standard C23, la manipolazione dei puntatori `sx`/`dx` e delle altezze dei nodi AVL è completamente definita; tuttavia dereferenziare un sottoalbero nullo durante una rotazione (per esempio assumendo erroneamente che `y->sx` non sia `nullptr`) o dimenticare di liberare i nodi in post-ordine provoca rispettivamente **comportamento indefinito** o **perdite di memoria**.

> **Se vieni da Python** — In Python la ricorsione su alberi profondi incontra rapidamente il limite di ricorsione dell'interprete; in C non esiste un contatore software che arresti la ricorsione, ma la profondità massima dipende dalla dimensione dello stack del processo. Mantenere l'altezza garantita a `O(log n)` con un albero AVL elimina il rischio di esaurimento dello stack anche su milioni di nodi.

### Esempio guidato

Il programma seguente implementa un albero AVL minimale con inserimento e rotazioni singole (`ruota_sx` per il caso RR e `ruota_dx` per il caso LL). Inserisce prima la sequenza strettamente crescente `10..60` e poi quella decrescente `60..10`, mostrando come l'altezza resti logaritmica (`3` anziché `6`) mentre la visita in-ordine restituisce sempre le chiavi ordinate. Le rotazioni doppie LR/RL e la rimozione saranno il tema dell'esercizio 23.3.

<!-- cod: id=23.3-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

typedef struct nodo_avl {
    int chiave;
    int altezza;
    struct nodo_avl *sx;
    struct nodo_avl *dx;
} nodo_avl_t;

static int h_nodo(const nodo_avl_t *n) {
    return (n != nullptr) ? n->altezza : 0;
}

static void aggiorna_h(nodo_avl_t *n) {
    int hs = h_nodo(n->sx);
    int hd = h_nodo(n->dx);
    n->altezza = 1 + ((hs > hd) ? hs : hd);
}

static nodo_avl_t *ruota_dx(nodo_avl_t *y) {
    nodo_avl_t *x = y->sx;
    y->sx = x->dx;
    x->dx = y;
    aggiorna_h(y);
    aggiorna_h(x);
    return x;
}

static nodo_avl_t *ruota_sx(nodo_avl_t *x) {
    nodo_avl_t *y = x->dx;
    x->dx = y->sx;
    y->sx = x;
    aggiorna_h(x);
    aggiorna_h(y);
    return y;
}

static nodo_avl_t *inserisci_singole(nodo_avl_t *n, int k, bool *ok) {
    if (n == nullptr) {
        nodo_avl_t *nuovo = malloc(sizeof(*nuovo));
        if (nuovo == nullptr) { *ok = false; return nullptr; }
        *nuovo = (nodo_avl_t){.chiave = k, .altezza = 1};
        return nuovo;
    }
    if (k < n->chiave) { n->sx = inserisci_singole(n->sx, k, ok); }
    else if (k > n->chiave) { n->dx = inserisci_singole(n->dx, k, ok); }
    else { return n; }

    aggiorna_h(n);
    int fb = h_nodo(n->sx) - h_nodo(n->dx);
    if (fb > 1 && k < n->sx->chiave) { return ruota_dx(n); }
    if (fb < -1 && k > n->dx->chiave) { return ruota_sx(n); }
    return n;
}

static void stampa_inordine(const nodo_avl_t *n) {
    if (n == nullptr) { return; }
    stampa_inordine(n->sx);
    printf(" %d", n->chiave);
    stampa_inordine(n->dx);
}

static void distruggi(nodo_avl_t *n) {
    if (n == nullptr) { return; }
    distruggi(n->sx);
    distruggi(n->dx);
    free(n);
}

int main(void) {
    int cresc[] = {10, 20, 30, 40, 50, 60};
    int decr[] = {60, 50, 40, 30, 20, 10};
    nodo_avl_t *a = nullptr, *b = nullptr;
    bool ok = true;

    for (size_t i = 0; i < 6 && ok; ++i) {
        a = inserisci_singole(a, cresc[i], &ok);
        b = inserisci_singole(b, decr[i], &ok);
    }
    if (!ok) {
        distruggi(a);
        distruggi(b);
        return EXIT_FAILURE;
    }
    printf("Crescente: radice=%d altezza=%d inordine:", a->chiave, h_nodo(a));
    stampa_inordine(a);
    printf("\nDecrescente: radice=%d altezza=%d inordine:", b->chiave, h_nodo(b));
    stampa_inordine(b);
    printf("\n");

    distruggi(a);
    distruggi(b);
    return ok ? 0 : EXIT_FAILURE;
}
```

```output
Crescente: radice=40 altezza=3 inordine: 10 20 30 40 50 60
Decrescente: radice=30 altezza=3 inordine: 10 20 30 40 50 60
```

Osserva che cosa accade durante l'esecuzione:

- Senza rotazioni, inserire `10, 20, 30, 40, 50, 60` avrebbe prodotto un albero degenerato di altezza `6` con radice `10`. Con `ruota_sx`, l'albero si ribilancia progressivamente portando `40` alla radice con altezza `3`.
- Sulla sequenza decrescente `60..10`, `ruota_dx` interviene simmetricamente mantenendo l'altezza a `3` con radice `30`.
- In `ruota_dx` e `ruota_sx`, `aggiorna_h` è chiamata prima sul vecchio nodo radice (che è sceso di un livello) e poi sulla nuova radice.
- `distruggi` libera i nodi in post-ordine (figlio sinistro, figlio destro, poi il nodo corrente), garantendo che nessun puntatore venga letto dopo `free`.

> **Approfondimento — Perché l'altezza di un albero AVL è sempre `O(log n)`**
> Qual è il numero minimo $N(h)$ di nodi necessario per costruire un albero AVL di altezza $h$? Con $N(0) = 0$ e $N(1) = 1$, per ottenere l'altezza $h$ con il minor numero possibile di nodi un sottoalbero deve avere altezza $h - 1$ e l'altro almeno $h - 2$ (per rispettare $|fb| \le 1$). Vale quindi la ricorrenza $N(h) = N(h - 1) + N(h - 2) + 1$, che cresce esponenzialmente come i numeri di Fibonacci. Invertendo la relazione si dimostra che per qualunque albero AVL di $n$ nodi l'altezza non supera mai circa $1.44 \log_2(n + 2)$: anche con un milione di nodi l'altezza resta sotto i `30` livelli.

### Esercizio 23.3 — Albero AVL completo con rotazioni singole (LL/RR) e doppie (LR/RL), rimozione e verifica dell'invariante

**Descrizione**

Realizza su tre file (`avl.h`, `avl.c`, `main.c`) un **albero AVL** completo come **tipo opaco** `avl_t` che associa chiavi intere `int32_t` a valori `int32_t`, gestendo tutte e quattro le rotazioni di bilanciamento (singole **LL**, **RR** e doppie **LR**, **RL**) sia in inserimento sia in rimozione.

1. In `avl.h` (protetto da `AVL_H`) definisci:
   - `typedef struct avl avl_t;`
   - `typedef struct avl_stats { size_t n; int altezza; size_t rot_ll; size_t rot_rr; size_t rot_lr; size_t rot_rl; } avl_stats_t;`
   - `typedef void (*avl_visita_fn)(int32_t chiave, int32_t valore, void *ctx);`
   e dichiara: `avl_t *avl_crea(void);`, `void avl_distruggi(avl_t *t);`, `bool avl_inserisci(avl_t *t, int32_t chiave, int32_t valore);` (se la chiave esiste aggiorna il valore senza duplicare il nodo), `bool avl_rimuovi(avl_t *t, int32_t chiave);` (gestisce 0, 1 o 2 figli usando il successore in-ordine e ribilancia risalendo), `bool avl_cerca(const avl_t *t, int32_t chiave, int32_t *valore_out);`, `void avl_inordine(const avl_t *t, avl_visita_fn fn, void *ctx);`, `bool avl_verifica_invariante(const avl_t *t);` (controlla ricorsivamente l'ordine stretto BST con estremi `int64_t`, la correttezza del campo `altezza` e `|fb| <= 1`) e `void avl_statistiche(const avl_t *t, avl_stats_t *st);`.
2. In `avl.c` implementa una funzione comune `bilancia(avl_t *t, nodo_avl_t *n)` usata sia dopo l'inserimento sia dopo la rimozione, distinguendo i casi `LL` (`fb > 1 && fb(sx) >= 0`), `LR` (`fb > 1 && fb(sx) < 0`), `RR` (`fb < -1 && fb(dx) <= 0`) e `RL` (`fb < -1 && fb(dx) > 0`), incrementando i rispettivi contatori e distruggendo i nodi in post-ordine.
3. In `main.c` gestisci da `stdin` i comandi `INS <k> <v>`, `DEL <k>`, `GET <k>`, `INORDER` e `STATS`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- fattore di bilanciamento `h(sx) - h(dx)` e aggiornamento dell'altezza dal basso verso l'alto dopo ogni rotazione
- distinzione tra rotazioni singole (`LL`, `RR`) e rotazioni doppie (`LR`, `RL`) in base al segno del fattore di bilanciamento del figlio
- riutilizzo della stessa routine di ribilanciamento sia nell'inserimento sia nella rimozione
- verifica automatica dell'invariante AVL (ordine BST, altezze esatte, `|fb| <= 1`) e distruzione in post-ordine

**Domande guida**

1. Perché nella rotazione doppia `LR` occorre ruotare prima a sinistra sul figlio sinistro e poi a destra sul nodo sbilanciato?
2. In quale ordine vanno aggiornate le altezze dei due nodi coinvolti in una rotazione destra (prima il vecchio nodo radice o prima la nuova radice)?
3. Perché dopo una rimozione in un albero AVL può essere necessario ribilanciare più nodi risalendo fino alla radice, a differenza dell'inserimento in cui basta al più una rotazione (singola o doppia)?
4. Come verifichi ricorsivamente in `avl_verifica_invariante` che anche le chiavi profonde nei sottoalberi rispettino l'ordine rispetto a tutti i loro antenati?

**Esempio di esecuzione**

```input
INS 10 1
INS 20 2
INS 30 3
INS 5 4
INS 2 5
INS 7 6
INS 25 7
STATS
INORDER
GET 7
GET 99
DEL 10
DEL 99
STATS
INORDER
```

```output
STATS: n=7 h=3 inv=1 rot(LL=1 RR=1 LR=1 RL=1)
INORDER: 2=5 5=4 7=6 10=1 20=2 25=7 30=3
GET 7: 6
GET 99: NON TROVATO
DEL 10: OK
DEL 99: NON TROVATO
STATS: n=6 h=3 inv=1 rot(LL=1 RR=1 LR=1 RL=1)
INORDER: 2=5 5=4 7=6 20=2 25=7 30=3
```

## 23.4 Trie per la ricerca su prefissi

Una tabella hash (capitolo 18) verifica in tempo medio `O(1)` se una stringa esatta è presente, ma non può rispondere in modo efficiente a domande come "quante parole nel dizionario iniziano con `"ca"`?" oppure "elenca in ordine alfabetico i primi 5 suggerimenti per `"pro"`". Un albero AVL (sotto-sezione 23.3) mantiene le parole ordinate, ma confronta intere stringhe a ogni nodo e impiega `O(L log n)` per una ricerca su `n` parole di lunghezza `L`.

Un **trie** (*trie*, o albero dei prefissi) affronta il problema da una prospettiva diversa: è un albero di ricerca in cui ogni arco rappresenta un singolo carattere e le chiavi condividono i prefissi comuni lungo il cammino dalla radice. Le operazioni di inserimento, ricerca esatta, conteggio su prefisso e rimozione dipendono unicamente dalla lunghezza `L` della parola (`O(L)`) e non dal numero totale `n` di chiavi memorizzate.

Ecco come appaiono le parole `"cane"`, `"casa"`, `"caso"` e `"gatto"` in un trie:

```text
          (radice, sub=4)
           /           \
         'c'           'g'
        (sub=3)       (sub=1)
          |             |
         'a'           'a'
        (sub=3)       (sub=1)
        /   \           |
      'n'   's'        't'
    (sub=1) (sub=2)   (sub=1)
      |     /   \       |
     'e'* 'a'*  'o'*   't'
                      (sub=1)
                        |
                       'o'*

  * = nodo con fine_parola = true
  sub = contatore parole_sottoalbero
```

Ogni nodo del trie per l'alfabeto ASCII minuscolo `'a'..'z'` (dimensione `A = 26`) contiene:

- un array di `26` puntatori ai figli (`struct nodo_trie *figli[26]`), inizializzati a `nullptr` (con `calloc` sulle piattaforme moderne, oppure — per stretta portabilità C23, come osservato nel capitolo 18 — allocando con `malloc` e inizializzando con `*n = (nodo_trie_t){};`);
- un flag booleano `fine_parola` che distingue una chiave realmente inserita da un semplice prefisso intermedio (nello schema sopra, `"cas"` esiste come cammino ma non ha `fine_parola = true`);
- un contatore `parole_sottoalbero` che registra quante parole terminano in quel nodo o nei suoi discendenti, permettendo di rispondere a una query di conteggio su prefisso in tempo `O(L)` senza visitare l'intero sottoalbero;
- un eventuale dato associato alla parola (per esempio un peso o una frequenza).

Il passaggio da un carattere `c` al figlio corrispondente avviene con l'indice `idx = (size_t)(c - 'a')`. Qui è indispensabile un controllo rigoroso: secondo lo standard C23, l'indicizzazione dell'array `figli` è definita soltanto per indici validi `0 <= idx < 26`. Calcolare `c - 'a'` su una lettera maiuscola, una cifra, uno spazio o un `char` negativo non verificato produce un indice fuori dai limiti dell'array e quindi **comportamento indefinito**. Prima di scendere nel trie occorre sempre validare esplicitamente che ogni carattere della stringa soddisfi `c >= 'a' && c <= 'z'`.

Le quattro operazioni principali funzionano così:

1. **Ricerca esatta (`O(L)`)**: parti dalla radice e, per ogni carattere `c` della parola, segui `figli[(size_t)(c - 'a')]`. Se incontri `nullptr` prima della fine della stringa, la parola è assente; se arrivi in fondo, la parola è presente solo se `fine_parola` vale `true`.
2. **Inserimento (`O(L)`)**: se la parola è valida, verifica se è già presente (per evitare di incrementare due volte `parole_sottoalbero` in caso di aggiornamento del dato associato). Poi percorri i caratteri allocando con `calloc` i nodi mancanti, incrementando `parole_sottoalbero` lungo il cammino se la parola è nuova e impostando `fine_parola = true` sul nodo finale.
3. **Conteggio su prefisso (`O(L)`) e autocompletamento**: segui i caratteri del prefisso fino al nodo corrispondente `n`. Se `n == nullptr`, il conteggio è `0`; altrimenti `n->parole_sottoalbero` è già la risposta esatta. Per elencare le parole in ordine lessicografico, basta eseguire una visita in profondità a partire da `n` scorrendo `figli[i]` da `i = 0` (`'a'`) a `i = 25` (`'z'`).
4. **Rimozione con potatura (`O(L)`) e distruzione**: azzerare soltanto `fine_parola` lascerebbe in memoria rami morti non più usati da alcuna parola. La rimozione corretta scende ricorsivamente fino al nodo finale, decrementa `parole_sottoalbero` al ritorno e libera con `free` ogni nodo (diverso dalla radice) che non marca più una fine parola e non ha più alcun figlio. Analogamente, la distruzione completa del trie libera tutti i figli prima del nodo padre (post-ordine), evitando perdite di memoria.

### Esempio guidato

Il programma seguente costruisce un trie per un piccolo vocabolario di parole minuscole, esegue ricerche esatte e conteggi di parole per prefisso in tempo `O(L)` (rifiutando parole con caratteri fuori da `'a'..'z'`) e libera l'intera struttura in post-ordine.

<!-- cod: id=23.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

static constexpr size_t ALFABETO = 26;

typedef struct nodo_trie {
    struct nodo_trie *figli[ALFABETO];
    size_t parole_sottoalbero;
    bool fine_parola;
} nodo_trie_t;

static bool valida_stringa(const char *s, bool consenti_vuota) {
    if (s == nullptr || (!consenti_vuota && s[0] == '\0')) { return false; }
    for (size_t i = 0; s[i] != '\0'; ++i) {
        if (s[i] < 'a' || s[i] > 'z') { return false; }
    }
    return true;
}

static const nodo_trie_t *scendi(const nodo_trie_t *radice, const char *s) {
    const nodo_trie_t *cur = radice;
    for (size_t i = 0; s[i] != '\0' && cur != nullptr; ++i) {
        cur = cur->figli[(size_t)(s[i] - 'a')];
    }
    return cur;
}

static bool trie_cerca(const nodo_trie_t *radice, const char *parola) {
    if (!valida_stringa(parola, false)) { return false; }
    const nodo_trie_t *n = scendi(radice, parola);
    return n != nullptr && n->fine_parola;
}

static bool trie_inserisci(nodo_trie_t *radice, const char *parola) {
    if (!valida_stringa(parola, false)) { return false; }
    if (trie_cerca(radice, parola)) { return true; }
    nodo_trie_t *cur = radice;
    ++cur->parole_sottoalbero;
    for (size_t i = 0; parola[i] != '\0'; ++i) {
        size_t idx = (size_t)(parola[i] - 'a');
        if (cur->figli[idx] == nullptr) {
            cur->figli[idx] = calloc(1, sizeof(*cur->figli[idx]));
            if (cur->figli[idx] == nullptr) { return false; }
        }
        cur = cur->figli[idx];
        ++cur->parole_sottoalbero;
    }
    cur->fine_parola = true;
    return true;
}

static size_t trie_conta_prefisso(const nodo_trie_t *radice, const char *pref) {
    if (!valida_stringa(pref, true)) { return 0; }
    const nodo_trie_t *n = scendi(radice, pref);
    return (n != nullptr) ? n->parole_sottoalbero : 0;
}

static void trie_distruggi(nodo_trie_t *n) {
    if (n == nullptr) { return; }
    for (size_t i = 0; i < ALFABETO; ++i) {
        trie_distruggi(n->figli[i]);
    }
    free(n);
}

int main(void) {
    nodo_trie_t *radice = calloc(1, sizeof(*radice));
    if (radice == nullptr) { return EXIT_FAILURE; }
    const char *voci[] = {"mare", "marea", "mano", "mela", "sole"};
    for (size_t i = 0; i < 5; ++i) {
        if (!trie_inserisci(radice, voci[i])) { trie_distruggi(radice); return EXIT_FAILURE; }
    }
    printf("cerca(mare)=%d cerca(mar)=%d cerca(Mare)=%d\n",
           trie_cerca(radice, "mare"), trie_cerca(radice, "mar"),
           trie_cerca(radice, "Mare"));
    printf("pref(ma)=%zu pref(mar)=%zu pref(m)=%zu pref(z)=%zu\n",
           trie_conta_prefisso(radice, "ma"), trie_conta_prefisso(radice, "mar"),
           trie_conta_prefisso(radice, "m"), trie_conta_prefisso(radice, "z"));
    trie_distruggi(radice);
    return 0;
}
```

```output
cerca(mare)=1 cerca(mar)=0 cerca(Mare)=0
pref(ma)=3 pref(mar)=2 pref(m)=4 pref(z)=0
```

Osserva i punti salienti del programma:

- `valida_stringa` controlla l'intera stringa prima di qualunque accesso a `figli`: così `"Mare"` viene respinta subito senza mai calcolare `'M' - 'a'` (che darebbe un valore negativo).
- `"mar"` restituisce `0` in `trie_cerca` (il nodo esiste ma `fine_parola` è `false`), mentre `trie_conta_prefisso(radice, "mar")` restituisce `2` in soli tre passi, leggendo `parole_sottoalbero` sul nodo `'r'`.
- `calloc(1, sizeof(*cur->figli[idx]))` azzera tutti i byte del nodo (sulle architetture moderne ciò coincide con `nullptr` per i `26` puntatori `figli`, oltre ad azzerare il contatore e `fine_parola`; per la portabilità stretta C23 sui puntatori nulli vale la nota del capitolo 18).
- `trie_distruggi` visita tutti i sottoalberi figli prima di chiamare `free(n)`.

> **Approfondimento — Compromesso spazio-tempo del trie**
> Un array fisso di `26` puntatori per nodo rende ogni transizione `O(1)` e il codice molto lineare, ma su un sistema a 64 bit ogni nodo occupa oltre `200` byte anche quando ha un solo figlio. Su alfabeti grandi (come l'intero insieme ASCII o Unicode) o su dizionari con parole lunghe e pochi prefissi condivisi, il consumo di memoria cresce rapidamente. Nei sistemi reali si attenuano questi costi comprimendo le catene di nodi con un solo figlio in un unico arco etichettato da una sottostringa (**radix tree** o trie compresso) oppure memorizzando solo i figli presenti in una piccola lista o tabella nei nodi sparsi.

### Esercizio 23.4 — Motore di autocompletamento su trie con conteggio prefissi O(L) e rimozione potata

**Descrizione**

Realizza su tre file (`trie.h`, `trie.c`, `main.c`) un **trie** come **tipo opaco** `trie_t` sull'alfabeto minuscolo `'a'..'z'` che associa a ciascuna parola un peso `uint32_t` e supporta conteggio su prefisso in tempo `O(L)`, autocompletamento lessicografico e rimozione con potatura dei nodi inutili.

1. In `trie.h` (protetto da `TRIE_H`) definisci `typedef struct trie trie_t;` e `typedef void (*trie_sugg_fn)(const char *parola, uint32_t peso, void *ctx);`, e dichiara:
   - `trie_t *trie_crea(void);`
   - `void trie_distruggi(trie_t *t);`
   - `bool trie_inserisci(trie_t *t, const char *parola, uint32_t peso);` (rifiuta parole vuote, lunghe oltre `31` caratteri o con caratteri fuori da `'a'..'z'`; se la parola esiste già aggiorna il peso senza incrementare i contatori di sottoalbero)
   - `bool trie_cerca(const trie_t *t, const char *parola, uint32_t *peso_out);`
   - `size_t trie_conta_prefisso(const trie_t *t, const char *prefisso);` (accetta anche `""` e risponde in `O(L)` leggendo il contatore `parole_sottoalbero` del nodo prefisso)
   - `size_t trie_suggerisci(const trie_t *t, const char *prefisso, size_t max_ris, trie_sugg_fn fn, void *ctx);` (visita i figli in ordine `'a'..'z'` invocando `fn` su al più `max_ris` parole)
   - `bool trie_rimuovi(trie_t *t, const char *parola);` (rimuove la parola, decrementa `parole_sottoalbero` lungo il cammino e libera con `free` ogni nodo non radice divenuto privo di figli e non terminale)
   - `size_t trie_num_parole(const trie_t *t);`
   - `size_t trie_num_nodi(const trie_t *t);` (include la radice)
2. In `main.c` leggi da `stdin` i comandi `ADD <parola> <peso>`, `FIND <parola>`, `COUNT <pref>` (`*` rappresenta il prefisso vuoto `""`), `SUGG <pref> [<k>]` (`*` per `""`, `1 <= k <= 32`, predefinito `32` se `<k>` è omesso), `DEL <parola>` e `NODES`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- validazione rigorosa dei caratteri nell'intervallo `'a'..'z'` prima di indicizzare `figli[26]`
- mantenimento del contatore `parole_sottoalbero` in ogni nodo per rispondere a `trie_conta_prefisso` in `O(L)`
- visita DFS in ordine `'a'..'z'` a partire dal nodo del prefisso per generare suggerimenti ordinati lessicograficamente
- potatura ricorsiva dei nodi orfani non terminali durante `trie_rimuovi` e verifica tramite `trie_num_nodi`

**Domande guida**

1. Perché `trie_inserisci` deve verificare se la parola è già presente prima di incrementare `parole_sottoalbero` lungo il cammino?
2. Quali condizioni deve soddisfare un nodo (diverso dalla radice) affinché `trie_rimuovi` possa liberarlo con `free` in sicurezza?
3. Come mai la visita DFS dei figli da `0` a `25` produce automaticamente le parole in ordine lessicografico senza doverle ordinare?
4. Quale rischio di comportamento indefinito correresti se calcolassi `(size_t)(c - 'a')` su un carattere maiuscolo o non alfabetico senza prima validarlo?

**Esempio di esecuzione**

```input
ADD casa 10
ADD caso 20
ADD cane 15
ADD gatto 5
ADD Casa 1
NODES
FIND caso
FIND cas
COUNT ca
COUNT cas
COUNT *
SUGG ca 2
SUGG ca 5
DEL gatto
DEL casa
DEL cas
NODES
SUGG *
```

```output
ADD casa: OK
ADD caso: OK
ADD cane: OK
ADD gatto: OK
ADD Casa: INVALIDA
NODES: parole=4 nodi=13
FIND caso: peso=20
FIND cas: ASSENTE
COUNT ca: 3
COUNT cas: 2
COUNT *: 4
SUGG ca: cane(15) casa(10)
SUGG ca: cane(15) casa(10) caso(20)
DEL gatto: OK
DEL casa: OK
DEL cas: ASSENTE
NODES: parole=2 nodi=7
SUGG *: cane(15) caso(20)
```

## 23.5 Grafi con liste di adiacenza: visite in ampiezza e in profondità

Alberi e liste modellano relazioni gerarchiche o lineari, ma molti problemi reali hanno collegamenti arbitrari: reti stradali, dipendenze tra moduli di compilazione, reti di calcolatori o collegamenti tra pagine web. La struttura dati generale per rappresentare queste relazioni è il **grafo** (*graph*): una coppia composta da un insieme di **vertici** (o nodi, indicati in numero con `V`) collegati da **archi** (in numero `E`).

Prima di passare al codice, fissiamo la terminologia essenziale:

- Un grafo è **orientato** (*directed*) se ogni arco `(u, v)` ha un verso da `u` a `v` (come una strada a senso unico o una dipendenza "`u` deve avvenire prima di `v`"); è **non orientato** (*undirected*) se ogni collegamento vale in entrambi i sensi (si rappresenta aggiungendo sia `(u, v)` sia `(v, u)`).
- Il **grado** di un vertice è il numero di archi incidenti (nei grafi orientati si distingue tra grado entrante e grado uscente).
- Un **cammino** è una sequenza di vertici collegati da archi consecutivi; un **ciclo** è un cammino non vuoto che parte e ritorna allo stesso vertice.
- Un **grafo aciclico orientato** (spesso abbreviato **DAG**, *Directed Acyclic Graph*) è un grafo orientato privo di cicli, fondamentale per modellare dipendenze senza circoli viziosi.

Come si rappresenta un grafo con vertici `0..V-1` in C? Esistono due scelte classiche:

- **Matrice di adiacenza**: una matrice `V x V` in cui la cella `[u][v]` vale `1` se esiste l'arco `(u, v)` e `0` altrimenti. Permette di verificare l'esistenza di un arco in `O(1)`, ma occupa `O(V^2)` di memoria e richiede `O(V)` per scorrere i vicini di un vertice, diventando proibitiva su grafi grandi e sparsi (dove `E` è molto minore di `V^2`).
- **Liste di adiacenza**: un array di `V` puntatori, in cui `adj[u]` è la testa di una lista concatenata contenente tutti i vicini uscenti da `u`. Occupa soltanto `O(V + E)` di memoria e permette di scorrere esattamente i vicini di `u` senza sprecare tempo sugli archi assenti.

```text
Grafo non orientato (V=6)        Liste di adiacenza (spazio O(V + E))
   0 --- 1 --- 3 --- 5           adj[0] -> 1 -> 2 -> nullptr
    \    |                       adj[1] -> 0 -> 3 -> 4 -> nullptr
     2 -- 4                      adj[2] -> 0 -> 4 -> nullptr
                                 adj[3] -> 1 -> 5 -> nullptr
                                 adj[4] -> 1 -> 2 -> nullptr
                                 adj[5] -> 3 -> nullptr
```

Le due strategie fondamentali per esplorare un grafo a partire da una sorgente `s` sono la visita in ampiezza e la visita in profondità, entrambe con complessità temporale `O(V + E)` su liste di adiacenza (ogni vertice entra nella visita al più una volta e ogni arco viene esaminato al più una volta nei grafi orientati, due volte in quelli non orientati):

1. **Visita in ampiezza (BFS, *Breadth-First Search*)**: usa una **coda** FIFO (anche un semplice array dinamico di `V` indici con due cursori `testa` e `fondo`, poiché ogni vertice viene accodato al più una volta) e un array `dist[]` inizializzato a `-1` (non scoperto). Poni `dist[s] = 0`, accoda `s`, e finché la coda non è vuota estrai `u` dalla testa e per ogni vicino `v` ancora a `-1` imposta `dist[v] = dist[u] + 1` e accoda `v`. Poiché la coda elabora prima tutti i vertici a distanza `0`, poi tutti quelli a distanza `1`, poi `2` e così via, la BFS scopre sempre il **cammino minimo in numero di archi** su grafi non pesati.
2. **Visita in profondità (DFS, *Depth-First Search*)**: scende il più a fondo possibile lungo un ramo prima di tornare indietro, usando la ricorsione oppure una **pila** esplicita (preferibile su grafi molto profondi per non rischiare l'esaurimento dello stack). Ogni vertice viene marcato come visitato appena scoperto.

Su un grafo orientato, la DFS permette di risolvere due problemi centrali — **rilevamento di cicli** e **ordinamento topologico** — usando una marcatura a **tre colori** invece di un solo booleano:

- **bianco (`0`)**: vertice non ancora visitato;
- **grigio (`1`)**: vertice in corso di visita (ancora attivo sullo stack delle chiamate);
- **nero (`2`)**: vertice completato (tutti i suoi discendenti sono stati esplorati).

Se durante la DFS da un vertice `u` incontri un arco `(u, v)` verso un vertice `v` **grigio**, significa che `v` è un antenato attivo di `u`: hai trovato un ciclo orientato. Un arco verso un vertice **nero**, invece, punta a un sottoalbero già concluso e *non* forma un ciclo. Se il grafo orientato non ha cicli (è un DAG), registrare ciascun vertice nel momento in cui diventa nero (post-ordine) e invertire l'elenco ottenuto produce un **ordinamento topologico**: una sequenza di tutti i vertici in cui per ogni arco `(u, v)` il vertice `u` compare sempre prima di `v`.

Secondo lo standard C23, la rappresentazione con liste di adiacenza e le visite BFS/DFS sono completamente definite; occorre però validare sempre `u < V` e `v < V` e marcare correttamente i vertici visitati: accedere a un vertice `>= V` o omettere la marcatura (generando cicli infiniti o esaurimento dello stack) provoca **comportamento indefinito**.

### Esempio guidato

Il programma seguente costruisce il grafo non orientato di `6` vertici dello schema precedente tramite liste di adiacenza, esegue una BFS dalla sorgente `0` stampando ordine di scoperta e distanza in archi di ogni vertice, esegue poi una DFS ricorsiva dalla stessa sorgente e libera infine tutti i nodi delle liste e l'array di adiacenza.

<!-- cod: id=23.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct arco {
    size_t dest;
    struct arco *prox;
} arco_t;

typedef struct {
    size_t v;
    arco_t **adj;
} grafo_t;

static bool aggiungi_dir(grafo_t *g, size_t u, size_t v) {
    if (u >= g->v || v >= g->v) { return false; }
    arco_t *a = malloc(sizeof(*a));
    if (a == nullptr) { return false; }
    a->dest = v;
    a->prox = g->adj[u];
    g->adj[u] = a;
    return true;
}

static bool aggiungi_non_orientato(grafo_t *g, size_t u, size_t v) {
    return aggiungi_dir(g, u, v) && aggiungi_dir(g, v, u);
}

static void bfs(const grafo_t *g, size_t sorgente) {
    int *dist = malloc(g->v * sizeof(*dist));
    size_t *coda = malloc(g->v * sizeof(*coda));
    if (dist == nullptr || coda == nullptr) { free(dist); free(coda); return; }
    for (size_t i = 0; i < g->v; ++i) { dist[i] = -1; }
    size_t testa = 0, fondo = 0;
    dist[sorgente] = 0;
    coda[fondo++] = sorgente;
    printf("BFS ordine:");
    while (testa < fondo) {
        size_t u = coda[testa++];
        printf(" %zu", u);
        for (const arco_t *a = g->adj[u]; a != nullptr; a = a->prox) {
            if (dist[a->dest] == -1) {
                dist[a->dest] = dist[u] + 1;
                coda[fondo++] = a->dest;
            }
        }
    }
    printf("\nBFS distanze:");
    for (size_t i = 0; i < g->v; ++i) { printf(" %zu:%d", i, dist[i]); }
    printf("\n");
    free(dist);
    free(coda);
}

static void dfs_ric(const grafo_t *g, size_t u, uint8_t *vis) {
    vis[u] = 1;
    printf(" %zu", u);
    for (const arco_t *a = g->adj[u]; a != nullptr; a = a->prox) {
        if (vis[a->dest] == 0) { dfs_ric(g, a->dest, vis); }
    }
}

static void distruggi_grafo(grafo_t *g) {
    for (size_t i = 0; i < g->v; ++i) {
        arco_t *c = g->adj[i];
        while (c != nullptr) { arco_t *p = c->prox; free(c); c = p; }
    }
    free(g->adj);
}

int main(void) {
    grafo_t g = {.v = 6, .adj = calloc(6, sizeof(arco_t *))};
    if (g.adj == nullptr) { return EXIT_FAILURE; }
    const size_t archi[][2] = {{3, 5}, {2, 4}, {1, 4}, {1, 3}, {0, 2}, {0, 1}};
    for (size_t i = 0; i < 6; ++i) {
        if (!aggiungi_non_orientato(&g, archi[i][0], archi[i][1])) {
            distruggi_grafo(&g); return EXIT_FAILURE;
        }
    }
    bfs(&g, 0);
    uint8_t vis[6] = {};
    printf("DFS ordine:");
    dfs_ric(&g, 0, vis);
    printf("\n");
    distruggi_grafo(&g);
    return 0;
}
```

```output
BFS ordine: 0 1 2 3 4 5
BFS distanze: 0:0 1:1 2:1 3:2 4:2 5:3
DFS ordine: 0 1 3 5 4 2
```

Osserva le differenze tra le due visite sullo stesso grafo:

- La BFS scopre i vertici per livelli di distanza crescente dalla sorgente `0`: prima `0` (distanza `0`), poi `1` e `2` (distanza `1`), poi `3` e `4` (distanza `2`), infine `5` (distanza `3`).
- La DFS, invece, entra in `1`, scende subito in profondità verso `3` e `5`, poi risale e raggiunge `4` e `2`, completando comunque tutti i `6` vertici senza rivisitare nodi già marcati in `vis[]`.
- `distruggi_grafo` libera ogni nodo `arco_t` di ciascuna delle `V` liste prima di chiamare `free(g->adj)`.

> **Approfondimento — Quando la BFS garantisce il cammino minimo e quando no**
> La BFS trova sempre il cammino con il *minor numero di archi* perché ogni passo aumenta la distanza esattamente di `1`. Se però gli archi hanno pesi diversi — per esempio chilometri di una strada o millisecondi di latenza di una rete — un percorso di `3` archi di peso `1` ciascuno (costo totale `3`) è migliore di un arco diretto di peso `10`. In presenza di pesi non uniformi la BFS non basta più: serve l'algoritmo di Dijkstra della prossima sotto-sezione.

### Esercizio 23.5 — Grafo orientato con liste di adiacenza: BFS, DFS, rilevamento cicli e ordinamento topologico

**Descrizione**

Realizza su tre file (`grafo.h`, `grafo.c`, `main.c`) un **grafo** orientato con liste di adiacenza come **tipo opaco** `grafo_t` (vertici `0..V-1`), supportando BFS, DFS, rilevamento cicli e ordinamento topologico in `O(V + E)`.

1. In `grafo.h` (protetto da `GRAFO_H`) definisci `typedef struct grafo grafo_t;` e dichiara:
   - `grafo_t *grafo_crea(size_t n_vertici);`
   - `void grafo_distruggi(grafo_t *g);`
   - `size_t grafo_num_vertici(const grafo_t *g);`
   - `bool grafo_aggiungi_arco(grafo_t *g, size_t u, size_t v);` (inserisce `v` nella lista di adiacenza di `u` in ordine crescente senza duplicati, rendendo deterministiche tutte le visite)
   - `bool grafo_bfs(const grafo_t *g, size_t sorgente, int32_t *dist_out, size_t *ordine_out, size_t *n_visitati);` (usa una coda dinamica FIFO per calcolare le distanze in archi, `-1` se irraggiungibile, e l'ordine di scoperta)
   - `bool grafo_dfs(const grafo_t *g, size_t sorgente, size_t *ordine_out, size_t *n_visitati);`
   - `bool grafo_ordina_topologico(const grafo_t *g, size_t *ordine_out);` (esegue una DFS a tre colori su `0..V-1`: restituisce `false` se incontra un arco verso un vertice in visita — ciclo orientato — altrimenti scrive in `ordine_out` il post-ordine invertito e restituisce `true`)
2. In `main.c` leggi da `stdin` i comandi `INIT <V>` (`1 <= V <= 64`), `EDGE <u> <v>`, `BFS <s>`, `DFS <s>` e `TOPO`, producendo esattamente l'output dell'esempio senza perdite di memoria.

**Concetti da tenere a mente**

- rappresentazione di un grafo orientato con array di liste di adiacenza in spazio `O(V + E)`
- BFS con coda FIFO per calcolare distanze minime in numero di archi in tempo `O(V + E)`
- DFS ricorsiva su grafo orientato con marcatura dei vertici visitati
- colorazione a tre stati (bianco, grigio, nero) per rilevare cicli orientati e costruire l'ordinamento topologico

**Domande guida**

1. Perché nella rilevazione dei cicli su un grafo orientato non basta un singolo array booleano di vertici visitati ma servono tre colori (bianco, grigio, nero)?
2. Perché la lista di adiacenza mantiene i vicini di ciascun vertice ordinati per indice crescente?
3. In che modo la coda FIFO della BFS garantisce che il primo momento in cui scopri un vertice `v` corrisponda alla distanza minima in archi dalla sorgente?
4. Perché per ottenere un ordinamento topologico da una DFS occorre invertire l'ordine di completamento (post-ordine) dei vertici?

**Esempio di esecuzione**

```input
INIT 5
EDGE 0 2
EDGE 0 1
EDGE 1 3
EDGE 2 3
EDGE 3 4
BFS 0
DFS 0
TOPO
EDGE 4 1
TOPO
```

```output
INIT: V=5
BFS(0): ordine=[0 1 2 3 4] dist=[0:0 1:1 2:1 3:2 4:3]
DFS(0): ordine=[0 1 3 4 2]
TOPO: 0 2 1 3 4
TOPO: CICLO RILEVATO
```

## 23.6 Cammini minimi con l'algoritmo di Dijkstra

In una rete stradale, in una rete di calcolatori o in una mappa di connessioni ferroviarie ogni arco `(u, v)` porta con sé un **peso** non negativo `w >= 0` (distanza, tempo, costo). Il problema dei **cammini minimi a sorgente singola** consiste nel trovare, dato un vertice di partenza `s`, il percorso di somma dei pesi minima da `s` verso ogni altro vertice raggiungibile del grafo.

La soluzione classica è l'**algoritmo di Dijkstra** (*Dijkstra's algorithm*): un algoritmo goloso che calcola i cammini minimi da una sorgente verso tutti i vertici raggiungibili di un grafo con pesi non negativi.

L'idea di fondo è mantenere due array di lunghezza `V`:

- `dist[v]`: la migliore stima nota della distanza minima da `s` a `v`, inizializzata a `0` per la sorgente (`dist[s] = 0`) e a $+\infty$ (rappresentato in C con la sentinella `UINT64_MAX` di `<stdint.h>`) per tutti gli altri vertici;
- `prec[v]`: il predecessore di `v` lungo il cammino minimo corrente, inizializzato a `-1`, che al termine permette di ricostruire l'intero percorso risalendo all'indietro da `dest` fino a `s`.

L'operazione elementare dell'algoritmo si chiama **rilassamento** (*relaxation*) di un arco `(u, v, w)`: se passare dal vertice `u` e percorrere l'arco di peso `w` porta a una distanza minore di quella finora registrata per `v`, aggiorni la stima:

```text
se dist[u] + w < dist[v]:
    dist[v] = dist[u] + w
    prec[v] = u
```

In C, per eseguire `dist[u] + w` senza rischiare un avvolgimento silenzioso vicino a `UINT64_MAX`, si usa la macro C23 `ckd_add(&nuova_dist, dist[u], w)` di `<stdckdint.h>`: se la somma va in overflow (restituisce `true`), l'arco viene semplicemente ignorato.

> **C23** — La macro `ckd_add` (`<stdckdint.h>`, introdotta nel capitolo 21) esegue la somma controllando l'overflow in modo espresso e portabile. Sui compilatori anteriori al C23, per evitare l'avvolgimento su `uint64_t` occorre controllare esplicitamente `dist[u] <= UINT64_MAX - w` prima di sommare `dist[u] + w`.

A ogni passo, l'algoritmo di Dijkstra sceglie il vertice non ancora definitivo `u` con la distanza `dist[u]` più piccola e rilassa tutti gli archi uscenti da `u`. Se la scelta del minimo viene fatta scorrendo linearmente l'array `dist[]`, l'algoritmo costa `O(V^2)`. Su grafi sparsi conviene invece usare la **coda di priorità** generica su **heap binario** (sotto-sezione 23.2), memorizzando coppie `{uint64_t dist; size_t v;}`:

1. inserisci `{0, s}` nella coda di priorità;
2. finché la coda non è vuota, estrai la coppia `cur` con distanza minima;
3. se `cur.dist > dist[cur.v]`, la coppia è una **voce obsoleta** (una stima più vecchia superata da un rilassamento successivo): la scarti subito con `continue` (**lazy deletion**);
4. altrimenti rilassi ogni arco `(cur.v, v, w)`: ogni volta che `dist[v]` migliora, aggiorni `dist[v]` e `prec[v]` e inserisci la nuova coppia `{dist[v], v}` nello heap.

Poiché ogni rilassamento inserisce al più una coppia per arco, nello heap entrano al più `E` elementi e la complessità complessiva con liste di adiacenza e min-heap binario scende a `O((V + E) log V)`.

Un vincolo è inderogabile: **tutti i pesi devono essere non negativi (`w >= 0`)**. La correttezza di Dijkstra poggia sull'invariante goloso secondo cui, quando un vertice `u` viene estratto come minimo dalla coda, nessun percorso futuro attraverso altri vertici ancora in coda (che hanno tutti distanza `>= dist[u]`) potrà mai accorciare `dist[u]`. Se esiste anche un solo arco con peso negativo, un percorso passato da un vertice più lontano potrebbe scendere sotto `dist[u]` *dopo* che `u` è già stato elaborato, producendo distanze errate. L'API del grafo pesato deve quindi rifiutare esplicitamente qualunque arco con `peso < 0`.

Secondo lo standard C23, il controllo preventivo di pesi negativi, l'uso di `UINT64_MAX` come sentinella di infinito e il controllo di overflow con `ckd_add` nel rilassamento garantiscono comportamento completamente definito su ogni piattaforma.

### Esempio guidato

Il programma compatto seguente modella una rete stradale orientata di `5` nodi con liste di adiacenza pesate (pesi non negativi) ed esegue l'algoritmo di Dijkstra dalla sorgente `0`, stampando la distanza minima e il predecessore di ogni nodo. Per brevità questo esempio seleziona il vertice minimo con una scansione lineare `O(V^2)`; nell'esercizio 23.6 integrerai l'algoritmo con la coda di priorità generica su heap binario per ottenere `O((V + E) log V)`.

<!-- cod: id=23.6-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdckdint.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct arco_p {
    size_t dest;
    uint64_t peso;
    struct arco_p *prox;
} arco_p_t;

static bool aggiungi_arco(arco_p_t **adj, size_t n, size_t u, size_t v, int64_t peso) {
    if (u >= n || v >= n || peso < 0) { return false; }
    arco_p_t *a = malloc(sizeof(*a));
    if (a == nullptr) { return false; }
    a->dest = v;
    a->peso = (uint64_t)peso;
    a->prox = adj[u];
    adj[u] = a;
    return true;
}

static void dijkstra(arco_p_t *const *adj, size_t n, size_t sorg,
                     uint64_t *dist, int32_t *prec) {
    bool fissato[16] = {};
    for (size_t i = 0; i < n; ++i) {
        dist[i] = UINT64_MAX;
        prec[i] = -1;
    }
    dist[sorg] = 0;

    for (size_t passo = 0; passo < n; ++passo) {
        size_t u = n;
        for (size_t i = 0; i < n; ++i) {
            if (!fissato[i] && (u == n || dist[i] < dist[u])) { u = i; }
        }
        if (u == n || dist[u] == UINT64_MAX) { break; }
        fissato[u] = true;
        for (const arco_p_t *a = adj[u]; a != nullptr; a = a->prox) {
            uint64_t nd = 0;
            if (!ckd_add(&nd, dist[u], a->peso) && nd < dist[a->dest]) {
                dist[a->dest] = nd;
                prec[a->dest] = (int32_t)u;
            }
        }
    }
}

int main(void) {
    constexpr size_t N = 5;
    arco_p_t *adj[N] = {};
    const size_t archi[][3] = {
        {0, 1, 6}, {0, 2, 2}, {2, 1, 3}, {1, 3, 4}, {2, 3, 9}, {2, 4, 7}, {3, 4, 2}
    };
    for (size_t i = 0; i < sizeof(archi) / sizeof(archi[0]); ++i) {
        if (!aggiungi_arco(adj, N, archi[i][0], archi[i][1], (int64_t)archi[i][2])) {
            return EXIT_FAILURE;
        }
    }
    uint64_t dist[N] = {};
    int32_t prec[N] = {};
    dijkstra(adj, N, 0, dist, prec);

    for (size_t i = 0; i < N; ++i) {
        printf("nodo %zu: dist=%" PRIu64 " prec=%" PRId32 "\n", i, dist[i], prec[i]);
    }
    for (size_t i = 0; i < N; ++i) {
        arco_p_t *c = adj[i];
        while (c != nullptr) { arco_p_t *p = c->prox; free(c); c = p; }
    }
    return 0;
}
```

```output
nodo 0: dist=0 prec=-1
nodo 1: dist=5 prec=2
nodo 2: dist=2 prec=0
nodo 3: dist=9 prec=1
nodo 4: dist=9 prec=2
```

Osserva come l'algoritmo aggiorna progressivamente le stime migliori:

- Dalla sorgente `0` il nodo `1` viene scoperto subito a distanza `6`, ma al passo successivo (quando viene fissato il nodo `2` a distanza `2`) l'arco `2 -> 1` di peso `3` riduce `dist[1]` da `6` a `5` e aggiorna `prec[1]` a `2`.
- Seguendo i predecessori all'indietro dal nodo `3` (`3 <- 1 <- 2 <- 0`) ricostruisci il cammino minimo `0 -> 2 -> 1 -> 3` di costo totale `2 + 3 + 4 = 9`, migliore dell'arco diretto `2 -> 3` di costo `2 + 9 = 11`.
- `aggiungi_arco` accetta `int64_t peso` e rifiuta i valori negativi prima di convertirli a `uint64_t`; il rilassamento usa `ckd_add` per impedire ogni overflow.

> **Approfondimento — *Lazy deletion* contro *decrease-key* nella coda di priorità**
> Nei testi teorici si descrive spesso Dijkstra con un'operazione `decrease-key` che modifica sul posto la priorità di un vertice già presente nello heap. In C, però, implementare `decrease-key` obbliga a mantenere un array di posizioni inverse (`pos[v]`) sincronizzato a ogni scambio dentro lo heap, complicando l'interfaccia e rompendo la genericità del contenitore. Con la tecnica della **lazy deletion**, invece, inserisci semplicemente una nuova coppia `(nuova_dist, v)` nello heap ogni volta che `dist[v]` migliora e scarti all'estrazione le voci obsolete con `cur.dist > dist[cur.v]`. Poiché gli inserimenti totali restano al più `E`, la complessità asintotica resta `O((V + E) log V)` con una coda di priorità generica standard e molto più semplice da verificare.

### Esercizio 23.6 — Algoritmo di Dijkstra O((V + E) log V) integrato con la coda di priorità generica e ricostruzione dei cammini

**Descrizione**

Integra in un programma su cinque file (`coda_prio.h`, `coda_prio.c`, `dijkstra.h`, `dijkstra.c`, `main.c`) la **coda di priorità** generica su **heap binario** e l'**algoritmo di Dijkstra** su un grafo orientato pesato con liste di adiacenza.

1. In `coda_prio.h` e `coda_prio.c` (protetto da `CODA_PRIO_H`) realizza il tipo opaco `coda_prio_t` (`cp_crea`, `cp_distruggi`, `cp_inserisci`, `cp_estrai`, `cp_vuota`) con elementi generici `void *` di dimensione `dim_elem` e comparatore `cp_cmp_fn`.
2. In `dijkstra.h` e `dijkstra.c` (protetto da `DIJKSTRA_H`) realizza il grafo pesato opaco `grafo_pesato_t` con:
   - `gp_crea(size_t n_vertici)`, `gp_distruggi`, `gp_num_vertici`;
   - `gp_aggiungi_arco(grafo_pesato_t *g, size_t u, size_t v, int64_t peso)` (rifiuta con `false` vertici fuori limiti o `peso < 0`);
   - `gp_dijkstra(const grafo_pesato_t *g, size_t sorgente, uint64_t *dist_out, int32_t *prec_out)` (inizializza `dist_out[i] = UINT64_MAX`, `prec_out[i] = -1`, usa `coda_prio_t` su coppie `{uint64_t dist; size_t v;}` con *lazy deletion* per le voci obsolete `voce.dist > dist_out[voce.v]` e `ckd_add` nel rilassamento per prevenire overflow);
   - `gp_ricostruisci_cammino(const int32_t *prec, size_t sorgente, size_t dest, size_t *cammino_out, size_t *len_out)`.
3. In `main.c` gestisci da `stdin` i comandi `INIT <V>` (`1 <= V <= 64`), `EDGE <u> <v> <peso>` (se `peso < 0` stampa `EDGE: PESO NEGATIVO RIFIUTATO` e prosegui), `DIJKSTRA <s>` (stampa per ogni vertice `0..V-1` distanza e cammino completo) e `PATH <s> <t>` (stampa distanza e cammino verso `t`, oppure `IRRAGGIUNGIBILE`), producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- integrazione modulare tra coda di priorità generica opaca e algoritmo di Dijkstra in `O((V + E) log V)`
- *lazy deletion* delle voci obsolete estratte dallo heap quando `voce.dist > dist[voce.v]`
- rilassamento degli archi con `ckd_add` e rifiuto preventivo dei pesi negativi
- ricostruzione del cammino minimo risalendo l'array dei predecessori `prec[]`

**Domande guida**

1. Perché quando `dist[v]` diminuisce durante il rilassamento puoi inserire una nuova voce nella coda di priorità invece di cercare e aggiornare quella vecchia?
2. Quale controllo all'uscita da `cp_estrai` garantisce che una voce obsoleta non rilassi inutilmente gli archi del vertice `v`?
3. Perché un arco con peso negativo rompe la correttezza dell'algoritmo di Dijkstra?
4. In che ordine ottieni i vertici risalendo `prec[t]` fino alla sorgente `s`, e come li riordini per stampare il cammino da `s` a `t`?

**Esempio di esecuzione**

```input
INIT 5
EDGE 0 1 10
EDGE 0 2 3
EDGE 2 1 4
EDGE 2 3 8
EDGE 1 3 2
EDGE 3 4 5
EDGE 1 2 -1
DIJKSTRA 0
PATH 2 4
```

```output
INIT: V=5
EDGE: PESO NEGATIVO RIFIUTATO
DIJKSTRA(0):
  v=0 dist=0 cammino=0
  v=1 dist=7 cammino=0->2->1
  v=2 dist=3 cammino=0->2
  v=3 dist=9 cammino=0->2->1->3
  v=4 dist=14 cammino=0->2->1->3->4
PATH(2->4): dist=11 cammino=2->1->3->4
```

## Riepilogo

- La **complessità asintotica** espressa con la **notazione O** confronta gli algoritmi in base alla crescita di tempo e spazio al crescere di `n`, trascurando costanti moltiplicative e termini di ordine inferiore (`O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(2^n)`). Si distinguono caso migliore, caso medio, caso peggiore e costo ammortizzato; contare le operazioni elementari in contatori `uint64_t` permette una verifica deterministica indipendente dall'hardware (nel capitolo 25 vedremo come affiancare misure temporali e analisi della cache).
- Un **heap binario** rappresenta un albero binario completo in un array contiguo a indice base `0` con `genitore(i) = (i - 1) / 2` (per `i > 0`), `figlio_sx(i) = 2 * i + 1` e `figlio_dx(i) = 2 * i + 2`. Realizza una **coda di priorità** con inserimento (*sift-up*) ed estrazione (*sift-down*) in `O(log n)`, lettura della cima in `O(1)` e costruzione bottom-up (*heapify* di Floyd) in `O(n)`. Con `void *`, `dim_elem`, `memcpy` e una callback di confronto diventa un contenitore generico riutilizzabile.
- Un **albero AVL** mantiene in ogni nodo l'altezza del sottoalbero e rispetta l'invariante `|h(sx) - h(dx)| <= 1`, garantendo ricerca, inserimento e rimozione in `O(log n)` anche nel caso peggiore. Uno sbilanciamento (`fb = +2` o `-2`) si ripristina in `O(1)` con una delle quattro rotazioni: singole `LL` (destra) e `RR` (sinistra), doppie `LR` (sinistra-destra) e `RL` (destra-sinistra), aggiornando le altezze dal basso verso l'alto.
- Un **trie** memorizza stringhe condividendo i prefissi comuni lungo gli archi: ricerca esatta, inserimento, conteggio su prefisso (tramite `parole_sottoalbero`) e rimozione potata costano `O(L)` in funzione della sola lunghezza `L` della chiave. Prima di indicizzare `figli[c - 'a']` occorre sempre validare che ogni carattere rientri in `'a'..'z'`.
- Un **grafo** sparso con `V` vertici ed `E` archi si rappresenta in `O(V + E)` di memoria con un array di liste di adiacenza. La BFS (con coda FIFO) e la DFS (ricorsiva o con pila) impiegano tempo `O(V + E)`: la BFS calcola i cammini minimi in numero di archi su grafi non pesati, mentre la DFS a tre colori (bianco, grigio, nero) su grafi orientati rileva i cicli e costruisce l'ordinamento topologico invertendo il post-ordine.
- L'**algoritmo di Dijkstra** calcola i cammini minimi da una sorgente su grafi con pesi non negativi (`w >= 0`), inizializzando `dist[]` a `UINT64_MAX`, proteggendo il rilassamento con `ckd_add` e integrandosi con una coda di priorità generica su heap binario con *lazy deletion* per raggiungere `O((V + E) log V)`.

## Errori comuni

- **Calcolare `(i - 1) / 2` in un heap binario su un indice `size_t` uguale a `0` senza controllare `i > 0`**: l'aritmetica senza segno avvolge `0 - 1` a `SIZE_MAX`, provocando un accesso fuori dai limiti e comportamento indefinito.
- **Aggiornare le altezze nell'ordine sbagliato durante una rotazione AVL**: se aggiorni prima la nuova radice e poi il vecchio genitore sceso di un livello, l'altezza della nuova radice usa un dato obsoleto e corrompe i fattori di bilanciamento di tutti gli antenati.
- **Indicizzare l'array dei figli di un trie con `c - 'a'` senza validare `c >= 'a' && c <= 'z'`**: lettere maiuscole, cifre, spazi o valori `char` negativi producono indici fuori da `0..25` e causano comportamento indefinito.
- **Usare un solo flag booleano `visitato[]` per rilevare cicli in un grafo orientato**: senza distinguere i nodi ancora attivi sullo stack (grigi) da quelli già completati (neri), un arco trasversale verso un nodo completato viene scambiato erroneamente per un ciclo.
- **Applicare l'algoritmo di Dijkstra a grafi con pesi negativi oppure dimenticare la *lazy deletion***: un peso negativo viola l'invariante goloso e produce distanze sbagliate, mentre non scartare le voci obsolete (`cur.dist > dist[cur.v]`) fa riesaminare inutilmente gli archi degradando le prestazioni.

## Prima di proseguire

- [ ] So determinare la classe asintotica (`O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n^2)`) di un algoritmo e verificarla contando le operazioni elementari in contatori `uint64_t`.
- [ ] So implementare un heap binario generico opaco con risalita, discesa e costruzione bottom-up `O(n)` di Floyd.
- [ ] So riconoscere i quattro casi di sbilanciamento AVL (`LL`, `RR`, `LR`, `RL`), applicare le rotazioni aggiornando le altezze dal basso verso l'alto e verificare l'invariante.
- [ ] So costruire un trie con validazione dei caratteri, conteggio su prefisso in `O(L)`, suggerimenti ordinati e rimozione con potatura.
- [ ] So rappresentare un grafo con liste di adiacenza, eseguire BFS, DFS, rilevamento cicli a tre colori e ordinamento topologico in `O(V + E)`.
- [ ] So implementare l'algoritmo di Dijkstra in `O((V + E) log V)` con coda di priorità generica, *lazy deletion*, rifiuto dei pesi negativi e ricostruzione dei cammini.
