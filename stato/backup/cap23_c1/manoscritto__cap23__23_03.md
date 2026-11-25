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
