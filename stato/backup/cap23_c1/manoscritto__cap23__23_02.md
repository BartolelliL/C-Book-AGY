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

Il programma seguente implementa un min-heap binario di `int` su array dinamico con `risali` (*sift-up*), `scendi` (*sift-down*) e `heap_costruisci` (heapify bottom-up `O(n)`). Verifica la proprietà di min-heap dopo ogni operazione ed estrae gli elementi uno alla volta in ordine crescente.

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
