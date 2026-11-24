## 17.4 Alberi binari di ricerca

In una lista concatenata, anche se mantieni gli elementi in ordine crescente, cercare un valore richiede comunque di scorrere i nodi uno a uno dall'inizio, perché non puoi saltare direttamente a metà della sequenza come fai nella ricerca binaria su un array ordinato. Se però vuoi sia mantenere i dati ordinati con inserimenti e rimozioni dinamici, sia scartare una grossa parte dei candidati a ogni confronto, devi passare da una catena lineare a una struttura gerarchica ramificata.

Un **albero binario di ricerca** (*binary search tree*, BST) è una struttura dati gerarchica in cui ogni nodo ha al più due figli (`sx` a sinistra e `dx` a destra) e rispetta un preciso **invariante d'ordine**: tutte le chiavi presenti nel sottoalbero sinistro sono strettamente minori della chiave del nodo, e tutte le chiavi presenti nel sottoalbero destro sono strettamente maggiori.

### Struttura del nodo e rappresentazione in memoria

Ogni nodo dell'albero conserva la chiave (ed eventualmente un valore associato) e due puntatori ai figli, entrambi `nullptr` quando il nodo è una foglia:

<!-- cod: id=17.4-b tipo=frammento -->
```c
typedef struct nodo_bst {
    int chiave;
    int valore;
    struct nodo_bst *sx;
    struct nodo_bst *dx;
} nodo_bst_t;
```

L'albero intero è rappresentato dal puntatore alla sua `radice` (`nullptr` quando l'albero è vuoto). Osserva l'invariante su un piccolo esempio:

```text
                [ 50 ]             <-- radice
               /      \
          [ 30 ]      [ 70 ]
          /    \      /    \
      [ 20 ] [ 40 ] [ 60 ] [ 80 ]  <-- foglie (sx = nullptr, dx = nullptr)
```

Nota che l'invariante vale per l'*intero* sottoalbero, non solo per il figlio diretto: ogni nodo nel sottoalbero sinistro di `50` (compreso `40`, che è figlio destro di `30`) deve essere minore di `50`.

### Ricerca e inserimento

La ricerca parte dalla radice e, a ogni passo, confronta la chiave cercata `k` con `cur->chiave`: se `k < cur->chiave` scende in `cur->sx`, se `k > cur->chiave` scende in `cur->dx`, se `k == cur->chiave` ha trovato il nodo. Se raggiunge `nullptr`, la chiave non è presente.

L'inserimento segue lo stesso percorso fino a trovare il puntatore `nullptr` dove agganciare il nuovo nodo. La politica per le **chiavi duplicate** va sempre dichiarata esplicitamente: nei dizionari chiave-valore si aggiorna il valore del nodo esistente, mentre negli insiemi di sole chiavi si rifiuta l'inserimento segnalando il duplicato. Con un puntatore a puntatore `nodo_bst_t **cur = &radice;`, puoi scendere iterativamente fino al punto d'innesto e scrivere `*cur = nuovo;` senza gestire la radice come caso speciale.

### Visite ricorsive e potatura per intervallo

La forma ricorsiva dell'albero rende naturali tre visite fondamentali, che si distinguono solo per il momento in cui elaborano il nodo corrente rispetto ai due figli:

- **In-ordine** (`sx`, nodo, `dx`): grazie all'invariante BST, produce tutte le chiavi in **ordine strettamente crescente**.
- **Pre-ordine** (nodo, `sx`, `dx`): elabora la radice prima dei sottoalberi; è utile per copiare o salvare la struttura dell'albero.
- **Post-ordine** (`sx`, `dx`, nodo): elabora entrambi i figli prima del nodo padre.

Nelle **ricerche per intervallo** `[lo, hi]` puoi sfruttare l'invariante per evitare di esplorare interi sottoalberi inutili (*potatura*): durante una visita in-ordine scendi in `rad->sx` solo se `rad->chiave > lo` (altrimenti tutto il sottoalbero sinistro è minore di `lo`), stampi `rad` se `lo <= rad->chiave <= hi` e scendi in `rad->dx` solo se `rad->chiave < hi` (altrimenti tutto il sottoalbero destro è maggiore di `hi`).

### Rimozione nei tre casi

La rimozione di una chiave da un BST deve preservare l'invariante d'ordine e distingue tre casi:

1. **Foglia (0 figli)**: liberi il nodo e sostituisci il puntatore nel padre con `nullptr`.
2. **Un solo figlio**: salvi il puntatore all'unico figlio non nullo, liberi il nodo e colleghi il figlio direttamente al padre (i casi 1 e 2 si possono unificare: se `rad->sx == nullptr`, restituisci `rad->dx` dopo `free(rad)`; se `rad->dx == nullptr`, restituisci `rad->sx` dopo `free(rad)`).
3. **Due figli**: non puoi scollegare il nodo direttamente. Trovi il suo **successore in-ordine**, cioè il nodo con la chiave minima nel sottoalbero destro (partendo da `rad->dx` e scendendo sempre su `sx` finché `succ->sx != nullptr`). Copi chiave e valore di `succ` dentro `rad`, poi rimuovi ricorsivamente `succ->chiave` dal sottoalbero destro `rad->dx`. Poiché `succ` è il minimo del sottoalbero destro, non ha mai un figlio sinistro: la sua rimozione ricade quindi sempre nel caso 1 o nel caso 2.

### Distruzione in post-ordine, altezza e degenerazione

La distruzione ricorsiva di un BST deve avvenire **rigorosamente in post-ordine**: prima distruggi `rad->sx`, poi `rad->dx` e solo alla fine chiami `free(rad)`. Se liberassi `rad` prima di leggere `rad->sx` e `rad->dx` (in pre-ordine), commetteresti un uso dopo la liberazione.

L'**altezza** di un albero è `0` se è vuoto, altrimenti `1 + max(altezza(sx), altezza(dx))`. Su un albero ben bilanciato l'altezza cresce molto lentamente rispetto al numero `n` di nodi; se però inserisci chiavi già ordinate (crescenti o decrescenti), ogni nodo ha un solo figlio e l'albero degenera in una lista lineare di altezza `n`.

Secondo lo standard C23, la gestione dinamica dei nodi di un BST è completamente definita; liberare un nodo prima di visitarne i figli provoca uso dopo la liberazione (**comportamento indefinito**), e una ricorsione troppo profonda su un albero degenere può esaurire lo stack del programma (**comportamento indefinito**). Per evitare la degenerazione si usano alberi autobilanciati come gli alberi AVL (lo vedremo nel capitolo 23).

### Esempio guidato

Il programma seguente costruisce un albero binario di ricerca di chiavi intere, stampa le tre visite (in-ordine, pre-ordine e post-ordine), calcola minimo, massimo e altezza dell'albero e libera tutti i nodi con una distruzione ricorsiva in post-ordine.

<!-- cod: id=17.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct nodo_bst {
    int chiave;
    struct nodo_bst *sx;
    struct nodo_bst *dx;
} nodo_bst_t;

bool bst_inserisci(nodo_bst_t **rad, int chiave) {
    nodo_bst_t **cur = rad;
    while (*cur != nullptr) {
        if (chiave < (*cur)->chiave) { cur = &(*cur)->sx; }
        else if (chiave > (*cur)->chiave) { cur = &(*cur)->dx; }
        else { return true; }
    }
    nodo_bst_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return false; }
    *n = (nodo_bst_t){.chiave = chiave, .sx = nullptr, .dx = nullptr};
    *cur = n;
    return true;
}

void stampa_inorder(const nodo_bst_t *r) {
    if (r == nullptr) { return; }
    stampa_inorder(r->sx);
    printf(" %d", r->chiave);
    stampa_inorder(r->dx);
}

void stampa_preorder(const nodo_bst_t *r) {
    if (r == nullptr) { return; }
    printf(" %d", r->chiave);
    stampa_preorder(r->sx);
    stampa_preorder(r->dx);
}

void stampa_postorder(const nodo_bst_t *r) {
    if (r == nullptr) { return; }
    stampa_postorder(r->sx);
    stampa_postorder(r->dx);
    printf(" %d", r->chiave);
}

size_t bst_altezza(const nodo_bst_t *r) {
    if (r == nullptr) { return 0; }
    size_t hs = bst_altezza(r->sx);
    size_t hd = bst_altezza(r->dx);
    return 1 + (hs > hd ? hs : hd);
}

int bst_estremo(const nodo_bst_t *r, bool cerca_max) {
    const nodo_bst_t *cur = r;
    while ((cerca_max ? cur->dx : cur->sx) != nullptr) {
        cur = cerca_max ? cur->dx : cur->sx;
    }
    return cur->chiave;
}

void bst_distruggi(nodo_bst_t *r) {
    if (r == nullptr) { return; }
    bst_distruggi(r->sx);
    bst_distruggi(r->dx);
    free(r);
}

int main(void) {
    nodo_bst_t *radice = nullptr;
    const int chiavi[] = {50, 30, 70, 20, 40, 60, 80};
    for (size_t i = 0; i < sizeof(chiavi) / sizeof(chiavi[0]); ++i) {
        if (!bst_inserisci(&radice, chiavi[i])) { bst_distruggi(radice); return EXIT_FAILURE; }
    }
    printf("In-ordine:  "); stampa_inorder(radice); printf("\n");
    printf("Pre-ordine: "); stampa_preorder(radice); printf("\n");
    printf("Post-ordine:"); stampa_postorder(radice); printf("\n");
    printf("Min=%d Max=%d Altezza=%zu\n",
           bst_estremo(radice, false), bst_estremo(radice, true), bst_altezza(radice));
    bst_distruggi(radice);
    return 0;
}
```

```output
In-ordine:   20 30 40 50 60 70 80
Pre-ordine:  50 30 20 40 70 60 80
Post-ordine: 20 40 30 60 80 70 50
Min=20 Max=80 Altezza=3
```

Osserva come funzionano le singole operazioni:

- `bst_inserisci` usa `nodo_bst_t **cur` per scendere nell'albero senza ricorsione e aggiorna direttamente `radice` al primo inserimento (`50`). Se incontra una chiave già presente, restituisce `true` senza duplicarla.
- La visita in-ordine stampa le chiavi ordinate (`20 30 40 50 60 70 80`), la visita pre-ordine inizia dalla radice (`50`) e la post-ordine termina con la radice (`50`).
- `bst_estremo` trova il minimo scendendo sempre a sinistra e il massimo scendendo sempre a destra (nel programma è chiamato solo dopo aver verificato che l'albero non sia vuoto).
- `bst_distruggi` segue lo stesso ordine della visita post-ordine: libera `r` solo dopo aver distrutto completamente `r->sx` e `r->dx`.

> **Approfondimento — Perché l'ordine di inserimento influisce sull'altezza di un BST**
> Un albero binario di ricerca non si ribilancia da solo: la sua forma dipende interamente dall'ordine con cui arrivano le chiavi. Inserire `10, 20, 30, 40, ...` in ordine crescente costruisce una catena solo verso destra di altezza `n`, degradando ogni ricerca a una scansione lineare e rischiando di esaurire lo stack nelle funzioni ricorsive. Risolveremo questo limite con gli alberi AVL autobilanciati (lo vedremo nel capitolo 23).

### Esercizio 17.4 — Indice chiave-valore su albero binario di ricerca con rimozione completa e query per intervallo

**Descrizione**

Scrivi un programma C che implementi un indice dizionario basato su un **albero binario di ricerca** (`typedef struct nodo_bst { int32_t chiave; char etichetta[24]; struct nodo_bst *sx; struct nodo_bst *dx; } nodo_bst_t;`). Implementa sette funzioni: (1) `bool bst_inserisci(nodo_bst_t **rad, int32_t chiave, const char *etichetta, bool *inserito)` che inserisce la coppia mantenendo l'invariante BST (se la chiave esiste già aggiorna `etichetta` e imposta `*inserito = false`; se nuova alloca il nodo e imposta `*inserito = true`; restituisce `false` solo se `malloc` fallisce); (2) `const nodo_bst_t *bst_cerca(const nodo_bst_t *rad, int32_t chiave)`; (3) `nodo_bst_t *bst_rimuovi(nodo_bst_t *rad, int32_t chiave, bool *rimosso)` che gestisce tutti e tre i casi di rimozione (foglia, un solo figlio e due figli tramite sostituzione con il successore in-ordine nel sottoalbero destro); (4) `void bst_range(const nodo_bst_t *rad, int32_t lo, int32_t hi, size_t *trovati)` che visita in-ordine potando i rami esclusi (scende a sinistra solo se `rad->chiave > lo`, a destra solo se `rad->chiave < hi`) e stampa `<chiave>=<etichetta>` per le chiavi in `[lo, hi]`; (5) `size_t bst_conta(const nodo_bst_t *rad)` e `size_t bst_altezza(const nodo_bst_t *rad)` (altezza `0` per albero vuoto, `1` per un singolo nodo); (6) `void bst_stampa_inorder(const nodo_bst_t *rad, bool *primo)`; (7) `void bst_distruggi(nodo_bst_t *rad)` in post-ordine rigoroso. In `main` leggi da `stdin` fino a fine input i comandi `PUT <chiave> <etichetta>`, `GET <chiave>`, `DEL <chiave>`, `RANGE <lo> <hi>` (`lo <= hi`) e `INFO`, producendo esattamente l'output mostrato nell'esempio e liberando l'albero prima di uscire.

**Concetti da tenere a mente**

- invariante dell'albero binario di ricerca (chiavi minori a sinistra, maggiori a destra)
- rimozione completa nei tre casi: 0 figli, 1 figlio e 2 figli con successore in-ordine
- visita in-ordine per chiavi ordinate e potatura dei sottoalberi nelle query per intervallo
- distruzione ricorsiva obbligatoria in post-ordine per evitare uso dopo la liberazione

**Domande guida**

1. Nel caso di rimozione di un nodo con due figli, perché il minimo del sottoalbero destro (successore in-ordine) ha sempre al massimo un figlio?
2. Come fa `bst_range` a evitare di visitare interi sottoalberi che non possono contenere chiavi nell'intervallo `[lo, hi]`?
3. Perché `bst_distruggi` deve ricorrere su `rad->sx` e `rad->dx` prima di chiamare `free(rad)`?
4. Che altezza assume l'albero se inserisci `n` chiavi già ordinate in modo strettamente decrescente?

**Esempio di esecuzione**

```input
PUT 50 Radice
PUT 30 Sinistra
PUT 70 Destra
PUT 20 FogliaSx
PUT 40 Interno
PUT 60 Succ
PUT 80 FogliaDx
PUT 30 SinistraAgg
GET 30
RANGE 25 65
DEL 20
DEL 30
DEL 50
INFO
```

```output
INSERT 50
INSERT 30
INSERT 70
INSERT 20
INSERT 40
INSERT 60
INSERT 80
UPDATE 30
GET 30: SinistraAgg
RANGE [25,65]: 30=SinistraAgg 40=Interno 50=Radice 60=Succ
DEL 20: OK
DEL 30: OK
DEL 50: OK
INFO: nodi=4 altezza=3 inorder=40 60 70 80
```
