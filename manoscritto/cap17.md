# Capitolo 17 — Strutture dati dinamiche

> **In questo capitolo imparerai a:**
> - Implementare liste semplicemente e doppiamente concatenate con inserimento, ricerca e rimozione
> - Costruire pile e code dinamiche rispettando le relative discipline di accesso
> - Implementare un albero binario di ricerca con inserimento, ricerca, visita e distruzione
> - Definire e rispettare regole esplicite di possesso della memoria nella distruzione delle strutture

> **Ti servono:** funzioni e ricorsione (capitolo 7), memoria dinamica e sanitizer (capitolo 11), `struct`, `typedef` e operatore `->` (capitolo 12), puntatori a puntatori e puntatori pendenti (capitolo 14), `void *` e contenitori generici (capitolo 15), puntatori a funzione e callback (capitolo 16).

Finora, quando dovevi conservare un numero variabile di elementi sullo heap, hai usato array dinamici ridimensionabili con `realloc`: tutti i dati risiedono in un unico blocco contiguo di memoria. Questa organizzazione è compatta e consente l'accesso immediato tramite indice, ma mostra i suoi limiti quando inserisci o rimuovi spesso elementi in testa o in mezzo alla sequenza, perché ogni modifica richiede di spostare tutti gli elementi successivi, oppure quando i dati hanno una struttura gerarchica che un semplice array lineare non rappresenta in modo naturale.

In questo capitolo impari a progettare le principali strutture dati dinamiche basate su nodi allocati singolarmente e collegati da puntatori: liste semplicemente e doppiamente concatenate, pile e code dinamiche (anche su buffer circolare) e alberi binari di ricerca. Metterai subito al lavoro gli strumenti dei capitoli precedenti: i puntatori a puntatori per semplificare inserimenti e rimozioni nelle liste, la ricorsione per visitare e distruggere gli alberi, i puntatori generici `void *` e le callback per costruire contenitori riutilizzabili.

Quando i dati vivono in decine o migliaia di blocchi separati sullo heap, tuttavia, scrivere gli algoritmi non basta: devi stabilire con precisione quale parte del programma è responsabile di liberare ciascun blocco e in quale ordine. L'ultima sotto-sezione codifica proprio queste regole di possesso della memoria, completando la preparazione per la tabella hash generica (lo vedremo nel capitolo 18) e per i moduli su più file (lo vedremo nel capitolo 19).

## 17.1 Liste semplicemente concatenate

Un array dinamico memorizza i propri elementi in byte contigui sullo heap. Se vuoi leggere l'elemento alla posizione `k`, ti basta calcolare un offset in tempo costante; se però devi inserire o rimuovere un elemento in testa o nel mezzo di una sequenza di diecimila elementi, devi spostare migliaia di elementi adiacenti per aprire o chiudere lo spazio. Inoltre, quando la capacità si esaurisce, `realloc` può spostare l'intero blocco a un nuovo indirizzo, invalidando eventuali puntatori agli elementi interni.

Quando le operazioni più frequenti sono inserimenti e rimozioni in posizioni arbitrarie e non hai bisogno dell'accesso diretto per indice, conviene separare i singoli elementi in blocchi indipendenti collegati tra loro. Questa struttura è chiamata **lista concatenata** (*linked list*): una struttura dati dinamica formata da nodi allocati singolarmente e collegati tra loro mediante puntatori. Il compromesso è simmetrico rispetto all'array dinamico: inserire o rimuovere un nodo richiede solo di aggiornare uno o due puntatori senza spostare gli altri dati, ma ogni nodo comporta una chiamata a `malloc` e un puntatore aggiuntivo in memoria, e raggiungere il `k`-esimo elemento richiede di seguire i collegamenti uno dopo l'altro dall'inizio.

### Strutture auto-referenziate e descrittore della lista

Per costruire una lista semplicemente concatenata, ogni nodo memorizza il dato e l'indirizzo del nodo successivo. In C una `struct` non può contenere un campo diretto del proprio stesso tipo (per esempio `struct nodo prox;`): il compilatore dovrebbe calcolare una dimensione ricorsiva infinita e rifiuta la definizione con un errore di compilazione. Può però contenere un puntatore a se stessa, perché la dimensione di un puntatore è fissa e nota al compilatore. Poiché l'alias `typedef` esiste solo alla fine della dichiarazione, all'interno della `struct` devi usare il tag `struct nodo`:

<!-- cod: id=17.1-b tipo=frammento -->
```c
typedef struct nodo {
    int valore;
    struct nodo *prox;
} nodo_t;

typedef struct lista {
    nodo_t *testa;
    size_t len;
} lista_t;
```

È buona pratica affiancare ai nodi una piccola `struct` descrittore (`lista_t`) che custodisce il puntatore al primo nodo (`testa`) e il contatore degli elementi (`len`). Quando la lista è vuota, `testa` vale `nullptr` e `len` vale `0`. L'ultimo nodo della lista ha sempre `prox == nullptr`, che funge da valore sentinella di fine sequenza. In memoria i nodi non sono contigui sullo heap, ma collegati dai puntatori:

```text
lista_t (stack)          nodo_t (heap)            nodo_t (heap)            nodo_t (heap)
+---------------+        +--------+------+        +--------+------+        +--------+---------+
| testa | len=3 |------->| val=10 | prox |------->| val=25 | prox |------->| val=40 | nullptr |
+---------------+        +--------+------+        +--------+------+        +--------+---------+
```

> **C23** — La parola chiave `nullptr` è stata introdotta in C23 per rappresentare il puntatore nullo in modo tipizzato. Con compilatori che supportano solo C11 o C17, usa `NULL` includendo `<stddef.h>`.

### Inserimento, ricerca e rimozione con puntatore a puntatore

L'inserimento in testa è immediato: allochi il nuovo nodo, imposti `nuovo->prox = lista->testa;`, aggiorni `lista->testa = nuovo;` e incrementi `lista->len`. La ricerca percorre i nodi con un semplice ciclo `for (const nodo_t *curr = l->testa; curr != nullptr; curr = curr->prox)`.

Quando però devi inserire un nodo in posizione ordinata oppure rimuovere un nodo cercato per valore, emerge una scomodità classica: se il punto di modifica è la testa della lista, devi cambiare `lista->testa`; se è un nodo interno o la coda, devi cambiare `prec->prox`. Tenere traccia sia di `curr` sia di `prec` costringe a scrivere un `if` separato per il caso della testa.

Puoi eliminare del tutto il ramo speciale applicando il **puntatore a puntatore** che hai visto nel capitolo 14. Invece di scorrere un puntatore al nodo (`nodo_t *curr`), scorri l'indirizzo del puntatore che punta al nodo corrente:

<!-- cod: id=17.1-c tipo=frammento -->
```c
nodo_t **cur = &lista->testa;
while (*cur != nullptr && (*cur)->valore < valore) {
    cur = &(*cur)->prox;
}
nuovo->prox = *cur;
*cur = nuovo;
```

All'inizio `cur` punta al campo `lista->testa`, quindi `*cur` è il puntatore al primo nodo. A ogni iterazione `cur = &(*cur)->prox;` sposta `cur` sull'indirizzo del campo `prox` del nodo corrente. Quando il ciclo termina, scrivere `*cur = nuovo;` aggiorna automaticamente `lista->testa` se il nodo va in testa, oppure `prec->prox` se va nel mezzo o in coda. La stessa tecnica funziona per la rimozione: una volta trovato il nodo tale che `(*cur)->valore == bersaglio`, salvi `nodo_t *da_lib = *cur;`, aggiorni `*cur = da_lib->prox;` e liberi `da_lib`.

### Distruzione iterativa sicura ed errore tipico

Per distruggere una lista semplicemente concatenata non devi mai scrivere un ciclo che legge `curr->prox` dopo aver liberato `curr`:

<!-- cod: id=17.1-d tipo=frammento -->
```c
// ERRORE: uso dopo la liberazione (comportamento indefinito)
for (nodo_t *curr = lista->testa; curr != nullptr; curr = curr->prox) {
    free(curr);
}
```

> **Attenzione — Uso dopo la liberazione**
> Il frammento precedente è sbagliato e non va mai scritto così: dopo `free(curr)` il blocco puntato da `curr` non appartiene più al programma, quindi l'espressione `curr = curr->prox` legge memoria già rilasciata. Secondo lo standard C23 questo è **comportamento indefinito** (i sanitizer lo segnalano immediatamente come *heap-use-after-free*).

La distruzione iterativa corretta salva prima l'indirizzo del nodo successivo in una variabile locale `prossimo`, poi libera `curr` e avanza a `prossimo`. Al termine azzera sempre `lista->testa = nullptr;` e `lista->len = 0;` per non lasciare un puntatore pendente nel descrittore.

Riassumendo le regole della sotto-sezione:

- Una `struct` non può includere un campo diretto del proprio tipo, ma può contenere un puntatore a se stessa tramite il proprio tag (`struct nodo *prox;`).
- Prima di liberare un nodo durante una rimozione o una distruzione, aggiorna i collegamenti o salva `nodo_t *prossimo = curr->prox;` prima di chiamare `free(curr)`.
- Usare `nodo_t **cur = &lista->testa;` permette di gestire testa e nodi interni con la stessa logica.
- Secondo lo standard C23, le strutture auto-referenziate tramite puntatore sono completamente definite; leggere `curr->prox` dopo `free(curr)` o dereferenziare `testa` quando è `nullptr` provoca **comportamento indefinito**.

### Esempio guidato

Il programma seguente gestisce una lista semplicemente concatenata mantenuta ordinata in senso crescente. Inserisce cinque numeri in ordine sparso usando `nodo_t **cur`, esegue due ricerche, rimuove la testa (`10`), un nodo interno (`25`) e la coda (`40`), stampa lo stato dopo ogni modifica e distrugge la lista iterativamente senza perdite di memoria.

<!-- cod: id=17.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct nodo {
    int valore;
    struct nodo *prox;
} nodo_t;

typedef struct lista {
    nodo_t *testa;
    size_t len;
} lista_t;

bool lista_inserisci_ordinato(lista_t *l, int val) {
    nodo_t *nuovo = malloc(sizeof(*nuovo));
    if (nuovo == nullptr) { return false; }
    nuovo->valore = val;
    nodo_t **cur = &l->testa;
    while (*cur != nullptr && (*cur)->valore < val) {
        cur = &(*cur)->prox;
    }
    nuovo->prox = *cur;
    *cur = nuovo;
    ++l->len;
    return true;
}

const nodo_t *lista_cerca(const lista_t *l, int val) {
    for (const nodo_t *c = l->testa; c != nullptr; c = c->prox) {
        if (c->valore == val) { return c; }
    }
    return nullptr;
}

bool lista_rimuovi(lista_t *l, int val) {
    nodo_t **cur = &l->testa;
    while (*cur != nullptr && (*cur)->valore != val) {
        cur = &(*cur)->prox;
    }
    if (*cur == nullptr) { return false; }
    nodo_t *da_lib = *cur;
    *cur = da_lib->prox;
    free(da_lib);
    --l->len;
    return true;
}

void lista_stampa(const lista_t *l, const char *etichetta) {
    printf("%s (%zu):", etichetta, l->len);
    for (const nodo_t *c = l->testa; c != nullptr; c = c->prox) { printf(" %d", c->valore); }
    printf("\n");
}

void lista_distruggi(lista_t *l) {
    nodo_t *curr = l->testa;
    while (curr != nullptr) {
        nodo_t *prossimo = curr->prox;
        free(curr);
        curr = prossimo;
    }
    l->testa = nullptr;
    l->len = 0;
}

int main(void) {
    lista_t l = {.testa = nullptr, .len = 0};
    const int dati[] = {25, 10, 40, 15, 30};
    for (size_t i = 0; i < sizeof(dati) / sizeof(dati[0]); ++i) {
        if (!lista_inserisci_ordinato(&l, dati[i])) {
            lista_distruggi(&l);
            return EXIT_FAILURE;
        }
    }
    lista_stampa(&l, "Ordinata");
    printf("Cerca 25: %s\n", lista_cerca(&l, 25) != nullptr ? "trovato" : "assente");
    printf("Cerca 99: %s\n", lista_cerca(&l, 99) != nullptr ? "trovato" : "assente");
    lista_rimuovi(&l, 10);
    lista_stampa(&l, "Dopo rimozione testa (10)");
    lista_rimuovi(&l, 25);
    lista_stampa(&l, "Dopo rimozione interno (25)");
    lista_rimuovi(&l, 40);
    lista_stampa(&l, "Dopo rimozione coda (40)");
    lista_distruggi(&l);
    printf("Dopo distruzione: len=%zu\n", l.len);
    return 0;
}
```

```output
Ordinata (5): 10 15 25 30 40
Cerca 25: trovato
Cerca 99: assente
Dopo rimozione testa (10) (4): 15 25 30 40
Dopo rimozione interno (25) (3): 15 30 40
Dopo rimozione coda (40) (2): 15 30
Dopo distruzione: len=0
```

Osserva i punti chiave del programma:

- In `lista_inserisci_ordinato`, la `malloc(sizeof(*nuovo))` è controllata subito: in caso di fallimento la funzione restituisce `false` senza toccare la lista esistente, e `main` chiama `lista_distruggi(&l)` prima di uscire con `EXIT_FAILURE`.
- Il ciclo `while (*cur != nullptr && (*cur)->valore < val)` usa la valutazione a corto circuito: se `*cur` è `nullptr`, `(*cur)->valore` non viene mai valutato.
- In `lista_rimuovi`, lo stesso codice gestisce senza rami speciali la rimozione della testa (`10`), di un nodo interno (`25`) e della coda (`40`). Prima aggiorna `*cur = da_lib->prox;`, poi libera `da_lib`.
- `lista_distruggi` salva `curr->prox` in `prossimo` prima di `free(curr)` e alla fine azzera sia `l->testa` sia `l->len`.

> **Approfondimento — Perché il puntatore a puntatore elimina i rami speciali**
> Il motivo per cui `nodo_t **cur = &lista->testa;` unifica testa e nodi interni è strutturale: tanto `lista->testa` quanto il campo `prox` di un nodo precedente hanno esattamente lo stesso tipo (`nodo_t *`). Puntando al *contenitore del puntatore* anziché al nodo stesso, l'assegnamento `*cur = (*cur)->prox;` modifica il puntatore giusto in qualunque posizione della lista, riducendo la quantità di codice e il rischio di errori nei casi limite.

### Esercizio 17.1 — Registro ordinato di attività con lista semplicemente concatenata e rimozione tramite puntatore a puntatore

**Descrizione**

Scrivi un programma C che gestisca un registro dinamico di attività mediante una lista semplicemente concatenata ordinata. Definisci `typedef struct attivita { int id; int priorita; char nome[24]; struct attivita *prox; } attivita_t;` e `typedef struct lista_att { attivita_t *testa; size_t len; } lista_att_t;`. Implementa cinque funzioni: (1) `void lista_init(lista_att_t *l)`; (2) `const attivita_t *lista_cerca(const lista_att_t *l, int id)`; (3) `int lista_inserisci(lista_att_t *l, int id, int priorita, const char *nome)` che controlla prima se `id` è già presente (restituendo `0`), alloca il nodo con `malloc` (restituendo `-1` se fallisce) e lo inserisce tramite un puntatore a puntatore `attivita_t **cur = &l->testa;` mantenendo la lista ordinata per `priorita` decrescente e, a parità di priorità, per `id` crescente (restituendo `1`); (4) `bool lista_rimuovi(lista_att_t *l, int id)` che rimuove il nodo con `id` tramite `attivita_t **cur = &l->testa;` senza rami speciali per la testa; (5) `void lista_distruggi(lista_att_t *l)` che libera iterativamente tutti i nodi salvando `prox` prima di `free` e azzera `l->testa = nullptr` e `l->len = 0`. In `main` leggi da `stdin` fino a fine input i comandi `ADD <id> <priorita> <nome>`, `DEL <id>`, `FIND <id>` e `LIST` stampando gli esiti esatti dell'esempio (`ADD` stampa `DUPLICATO <id>` solo in caso di duplicato; nessun output per `ADD` riuscito). Al termine chiama `lista_distruggi(&lista)` e stampa `Pulizia completata (len=<len>, testa_nulla=<0|1>)`.

**Concetti da tenere a mente**

- struttura auto-referenziata con `struct attivita *prox` e descrittore con `testa` e `len`
- inserimento ordinato e rimozione tramite puntatore a puntatore `attivita_t **cur`
- gestione corretta dei duplicati e dei casi limite (lista vuota, unico nodo, testa, coda)
- distruzione iterativa sicura salvando `curr->prox` prima di `free(curr)`

**Domande guida**

1. Perché nella definizione della `struct` devi scrivere `struct attivita *prox;` anziché `attivita_t *prox;` prima che il `typedef` sia completato?
2. In che modo il ciclo su `attivita_t **cur = &l->testa;` riesce a inserire o rimuovere sia in testa sia in mezzo alla lista senza un `if` separato per la testa?
3. Quale errore di memoria si verifica se in `lista_distruggi` scrivi `free(curr); curr = curr->prox;`?
4. Quale condizione di confronto tra il nodo corrente e il nuovo elemento garantisce priorità decrescente e, a parità, `id` crescente?

**Esempio di esecuzione**

```input
ADD 10 2 Backup
ADD 5 5 Deploy
ADD 8 5 Audit
ADD 10 9 Duplicato
LIST
FIND 8
DEL 5
DEL 99
LIST
```

```output
DUPLICATO 10
Lista (3): [5] Deploy (p=5) -> [8] Audit (p=5) -> [10] Backup (p=2)
TROVATO 8: Audit (prio=5)
RIMOSSO 5
NON TROVATO 99
Lista (2): [8] Audit (p=5) -> [10] Backup (p=2)
Pulizia completata (len=0, testa_nulla=1)
```

## 17.2 Liste doppiamente concatenate

In una lista semplicemente concatenata puoi avanzare solo in una direzione. Se hai già in mano il puntatore `n` a un nodo nel mezzo della lista e vuoi rimuoverlo, oppure se vuoi tornare al nodo precedente (come nei pulsanti Indietro e Avanti di un browser), non conosci l'indirizzo del predecessore e sei costretto a ripartire da `testa` con una scansione lineare.

Per muoversi in entrambi i sensi e scollegare un nodo noto in tempo costante, ogni nodo memorizza due puntatori: `prec` (verso il predecessore) e `prox` (verso il successore). Il descrittore della **lista doppiamente concatenata** mantiene sia `testa` sia `coda`, insieme alla lunghezza `len`:

<!-- cod: id=17.2-b tipo=frammento -->
```c
typedef struct nodo_d {
    int valore;
    struct nodo_d *prec;
    struct nodo_d *prox;
} nodo_d_t;

typedef struct lista_d {
    nodo_d_t *testa;
    nodo_d_t *coda;
    size_t len;
} lista_d_t;
```

Lo schema in memoria evidenzia i collegamenti bidirezionali tra nodi adiacenti e i puntatori nulli alle due estremità:

```text
lista_d_t (stack)
+-------+-------+-------+
| testa | coda  | len=3 |
+---+---+---+---+-------+
    |       |
    |       +--------------------------------------------+
    v                                                    v
+---------+-----+------+     +------+-----+------+     +------+-----+---------+
| nullptr |  A  | prox |<--->| prec |  B  | prox |<--->| prec |  C  | nullptr |
+---------+-----+------+     +------+-----+------+     +------+-----+---------+
```

### Invarianti strutturali e verifica simmetrica

Avere il doppio dei puntatori rende le operazioni più potenti, ma raddoppia anche i punti in cui un aggiornamento dimenticato può corrompere la struttura. Per progettare e verificare una lista doppiamente concatenata conviene esplicitare il suo **invariante strutturale**, che deve valere prima e dopo ogni operazione:

- Se la lista è vuota (`len == 0`): `testa == nullptr` e `coda == nullptr`.
- Se la lista non è vuota (`len > 0`): `testa != nullptr`, `coda != nullptr`, `testa->prec == nullptr` e `coda->prox == nullptr`.
- Se la lista ha un solo nodo (`len == 1`): `testa == coda`.
- Simmetria dei collegamenti: per ogni coppia di nodi adiacenti `(a, b)`, vale `a->prox == b` se e solo se `b->prec == a`.

Un modo molto efficace per collaudare l'invariante durante lo sviluppo è stampare o attraversare la lista sia in avanti (da `testa` seguendo `prox`) sia all'indietro (da `coda` seguendo `prec`): se un solo puntatore `prec` è rimasto indietro o punta a un nodo rimosso, la visita all'indietro lo smaschera subito.

### Collegamento, scollegamento e i quattro casi limite

La forza di una lista doppiamente concatenata emerge quando hai già il puntatore `n` a un nodo e vuoi scollegarlo in tempo costante. Ogni operazione di collegamento o scollegamento deve preservare l'invariante nei quattro casi limite: lista vuota, unico nodo, nodo in testa e nodo in coda.

Osserva come `scollega_nodo` gestisce tutti i casi con due soli `if` simmetrici:

<!-- cod: id=17.2-c tipo=frammento -->
```c
void scollega_nodo(lista_d_t *l, nodo_d_t *n) {
    if (n->prec != nullptr) {
        n->prec->prox = n->prox;
    } else {
        l->testa = n->prox;
    }
    if (n->prox != nullptr) {
        n->prox->prec = n->prec;
    } else {
        l->coda = n->prec;
    }
    n->prec = nullptr;
    n->prox = nullptr;
    --l->len;
}
```

Controlla i casi limite uno per uno:

- **Nodo interno** (`n->prec != nullptr` e `n->prox != nullptr`): il predecessore punta al successore e il successore punta al predecessore; `testa` e `coda` restano invariati.
- **Nodo in testa** (`n->prec == nullptr`, `n->prox != nullptr`): `l->testa` avanza a `n->prox` e il nuovo primo nodo riceve `prec = nullptr`.
- **Nodo in coda** (`n->prec != nullptr`, `n->prox == nullptr`): `l->coda` arretra a `n->prec` e il nuovo ultimo nodo riceve `prox = nullptr`.
- **Unico nodo** (`n->prec == nullptr` e `n->prox == nullptr`): entrambi i rami `else` eseguono, portando sia `l->testa` sia `l->coda` a `nullptr` e `l->len` a `0`.

Azzerare `n->prec` e `n->prox` alla fine evita che il nodo scollegato conservi riferimenti residui alla lista. In modo analogo, `collega_in_testa` imposta `n->prec = nullptr; n->prox = l->testa;`, poi se `l->testa != nullptr` aggiorna `l->testa->prec = n;`, altrimenti (caso lista vuota) aggiorna `l->coda = n;`, e infine assegna `l->testa = n;` e incrementa `l->len`.

### Spostamento in testa senza riallocazione

Una conseguenza preziosa della separazione tra `scollega_nodo` e `collega_in_testa` è che puoi spostare un nodo già allocato in testa alla lista in tempo costante, senza chiamare né `malloc` né `free`:

<!-- cod: id=17.2-d tipo=frammento -->
```c
void sposta_in_testa(lista_d_t *l, nodo_d_t *n) {
    if (l->testa == n) {
        return;
    }
    scollega_nodo(l, n);
    collega_in_testa(l, n);
}
```

Questo schema non può fallire per mancanza di memoria (non alloca nulla) ed è il mattone fondamentale delle cache LRU (*Least Recently Used*), dove l'elemento consultato più di recente sale in testa e il meno recente scivola in coda pronto per essere rimosso.

Secondo lo standard C23, la manipolazione dei puntatori `prec` e `prox` su nodi allocati sullo heap è completamente definita; dereferenziare `prec` o `prox` quando vale `nullptr`, oppure lasciare un puntatore pendente (per esempio in `coda`) verso un nodo già liberato con `free`, provoca **comportamento indefinito**.

### Esempio guidato

Il programma seguente modella una cronologia di navigazione di pagine web con una lista doppiamente concatenata e un puntatore `corrente` alla pagina visualizzata. Aggiunge tre pagine in coda, si sposta indietro con `prec` e avanti con `prox`, elimina la pagina corrente gestendo i casi di bordo, verifica la lista in entrambi i sensi e libera tutti i nodi.

<!-- cod: id=17.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct pagina { const char *url; struct pagina *prec; struct pagina *prox; } pagina_t;
typedef struct cronologia { pagina_t *testa; pagina_t *coda; pagina_t *corrente; size_t len; } cronologia_t;

bool aggiungi_coda(cronologia_t *c, const char *url) {
    pagina_t *p = malloc(sizeof(*p));
    if (p == nullptr) { return false; }
    *p = (pagina_t){.url = url, .prec = c->coda, .prox = nullptr};
    if (c->coda != nullptr) { c->coda->prox = p; } else { c->testa = p; }
    c->coda = p;
    c->corrente = p;
    ++c->len;
    return true;
}

void elimina_corrente(cronologia_t *c) {
    if (c->corrente == nullptr) { return; }
    pagina_t *p = c->corrente;
    pagina_t *nuova = (p->prox != nullptr) ? p->prox : p->prec;
    if (p->prec != nullptr) { p->prec->prox = p->prox; } else { c->testa = p->prox; }
    if (p->prox != nullptr) { p->prox->prec = p->prec; } else { c->coda = p->prec; }
    free(p);
    c->corrente = nuova;
    --c->len;
}

void stampa_stato(const cronologia_t *c, const char *azione) {
    printf("%s -> corrente=%s | avanti:", azione,
           c->corrente != nullptr ? c->corrente->url : "(nessuna)");
    for (const pagina_t *p = c->testa; p != nullptr; p = p->prox) { printf(" %s", p->url); }
    printf(" | indietro:");
    for (const pagina_t *p = c->coda; p != nullptr; p = p->prec) { printf(" %s", p->url); }
    printf("\n");
}

void distruggi(cronologia_t *c) {
    pagina_t *curr = c->testa;
    while (curr != nullptr) {
        pagina_t *prossimo = curr->prox;
        free(curr);
        curr = prossimo;
    }
    *c = (cronologia_t){};
}

int main(void) {
    cronologia_t cr = {};
    const char *pagine[] = {"home", "guida", "esempi"};
    for (size_t i = 0; i < 3; ++i) {
        if (!aggiungi_coda(&cr, pagine[i])) {
            distruggi(&cr);
            return EXIT_FAILURE;
        }
    }
    stampa_stato(&cr, "Inizio");
    if (cr.corrente->prec != nullptr) {
        cr.corrente = cr.corrente->prec;
    }
    stampa_stato(&cr, "Indietro");
    elimina_corrente(&cr);
    stampa_stato(&cr, "Elimina corrente");
    elimina_corrente(&cr);
    stampa_stato(&cr, "Elimina coda");
    distruggi(&cr);
    return 0;
}
```

```output
Inizio -> corrente=esempi | avanti: home guida esempi | indietro: esempi guida home
Indietro -> corrente=guida | avanti: home guida esempi | indietro: esempi guida home
Elimina corrente -> corrente=esempi | avanti: home esempi | indietro: esempi home
Elimina coda -> corrente=home | avanti: home | indietro: home
```

Osserva come l'esempio mette alla prova gli invarianti:

- In `aggiungi_coda`, il nuovo nodo collega subito `p->prec = c->coda;`. Se la lista era vuota aggiorna `c->testa = p;`, altrimenti collega `c->coda->prox = p;`.
- In `elimina_corrente`, prima di liberare `p` si sceglie la nuova pagina corrente (`p->prox` se esiste, altrimenti `p->prec`) e si aggiornano entrambi i collegamenti `prec` e `prox` (oltre a `testa` e `coda` nei casi limite).
- `stampa_stato` attraversa la lista in avanti e all'indietro a ogni passo: le due sequenze restano sempre esattamente speculari.
- `distruggi` libera i nodi in modo iterativo salvando `curr->prox` e azzera tutti i campi del descrittore con il letterale composto `(cronologia_t){}`.

> **Approfondimento — Scollegare e ricollegare un nodo senza riallocarlo**
> Separare le primitive `scollega_nodo` e `collega_in_testa` permette di spostare un nodo esistente in qualsiasi posizione in tempo costante e con zero allocazioni. Oltre a evitare il costo di `malloc` e `free`, questa tecnica garantisce che lo spostamento non possa mai fallire per memoria esaurita: per questo è lo schema standard alla base delle cache LRU e delle code degli schedulatori di sistema.

### Esercizio 17.2 — Cache LRU a capacità fissa con lista doppiamente concatenata

**Descrizione**

Scrivi un programma C che implementi una cache LRU (Least Recently Used) di capacità fissata `cap` (`1 <= cap <= 32`) mediante una lista doppiamente concatenata in cui `testa` è l'elemento usato più di recente e `coda` è il meno recente. Definisci `typedef struct nodo_lru { int chiave; int valore; struct nodo_lru *prec; struct nodo_lru *prox; } nodo_lru_t;` e `typedef struct cache_lru { nodo_lru_t *testa; nodo_lru_t *coda; size_t len; size_t cap; } cache_lru_t;`. Implementa le primitive di collegamento e scollegamento: `void scollega_nodo(cache_lru_t *c, nodo_lru_t *n)`, `void collega_in_testa(cache_lru_t *c, nodo_lru_t *n)`, `void sposta_in_testa(cache_lru_t *c, nodo_lru_t *n)` (senza chiamare `malloc` né `free`!), `nodo_lru_t *cerca_nodo(cache_lru_t *c, int chiave)` e `void cache_distruggi(cache_lru_t *c)`. In `main` leggi dalla prima riga `cap` (`1 <= cap <= 32`), poi leggi comandi fino a fine input: (1) `PUT <chiave> <valore>`: se la chiave esiste aggiorna il valore, sposta il nodo esistente in testa e stampa `UPDATE <k>=<v>`; se non esiste e `len == cap`, scollega e libera `c->coda` stampando `EVICT <chiave_rimossa>`, poi alloca e collega in testa il nuovo nodo stampando `INSERT <k>=<v>`; (2) `GET <chiave>`: se presente sposta il nodo in testa e stampa `HIT <k>=<v>`, altrimenti `MISS <k>`; (3) `DEL <chiave>`: se presente scollega e libera il nodo stampando `DEL <k>`, altrimenti `NON TROVATO <k>`; (4) `DUMP`: stampa prima la lista da `testa` a `coda` (`AVANTI (<len>): ...`) e poi da `coda` a `testa` tramite `prec` (`INDIETRO (<len>): ...`) per verificare la perfetta simmetria dei collegamenti doppi. Libera tutta la memoria al termine.

**Concetti da tenere a mente**

- invarianti di una lista doppiamente concatenata (`testa->prec == nullptr`, `coda->prox == nullptr`, simmetria `prec`/`prox`)
- scollegamento di un nodo nei quattro casi limite (unico nodo, testa, coda, nodo interno)
- spostamento in testa in tempo costante senza allocare né liberare nodi
- verifica simmetrica tramite attraversamento in avanti (`prox`) e all'indietro (`prec`)

**Domande guida**

1. Quali puntatori deve aggiornare `scollega_nodo` quando il nodo rimosso è contemporaneamente `testa` e `coda` (unico elemento della lista)?
2. Perché `sposta_in_testa` non deve chiamare `malloc` né `free`, e quale controllo iniziale evita lavoro inutile se il nodo è già in testa?
3. In che modo il comando `DUMP` (stampando sia `AVANTI` sia `INDIETRO`) rivela subito un eventuale errore nell'aggiornamento dei puntatori `prec`?
4. Che cosa succede durante `PUT` quando `cap == 1` e la cache è già piena?

**Esempio di esecuzione**

```input
3
PUT 1 100
PUT 2 200
PUT 3 300
GET 1
PUT 4 400
PUT 3 350
DUMP
DEL 1
DUMP
```

```output
INSERT 1=100
INSERT 2=200
INSERT 3=300
HIT 1=100
EVICT 2
INSERT 4=400
UPDATE 3=350
AVANTI (3): 3=350 4=400 1=100
INDIETRO (3): 1=100 4=400 3=350
DEL 1
AVANTI (2): 3=350 4=400
INDIETRO (2): 4=400 3=350
```

## 17.3 Pile e code dinamiche

Molti problemi non richiedono di inserire o rimuovere elementi in una posizione qualunque: impongono invece una disciplina rigida su quale elemento esca per primo. Limitare le operazioni disponibili non è un ostacolo, ma un vantaggio progettuale: rende esplicita l'intenzione del codice e permette di garantire inserimento ed estrazione in tempo costante.

### La pila (LIFO)

Una **pila** (*stack*) è una struttura dati lineare con politica ultimo entrato primo uscito (LIFO, *Last In, First Out*) in cui inserimento e rimozione avvengono entrambi in cima. Le operazioni fondamentali sono tre: `push` (inserisce un elemento in cima), `pop` (estrae l'elemento in cima) e `peek` (legge l'elemento in cima senza rimuoverlo). Ritrovi questa disciplina nella verifica di parentesi bilanciate, nella cronologia delle azioni di annullamento (*undo*) e nella gestione delle chiamate di funzione sullo stack del processore.

Una pila dinamica può essere implementata in due modi:

- **Su lista semplicemente concatenata**: il campo `cima` punta al primo nodo; `push` alloca un nodo e lo inserisce in testa, `pop` scollega e libera la testa. Ogni operazione richiede tempo costante senza mai riallocare blocchi esistenti.
- **Su array dinamico ridimensionabile**: gli elementi vivono in un blocco contiguo e la cima è l'indice `len - 1`. Quando `len == cap` la capacità raddoppia con `realloc`.

### La coda (FIFO) su lista concatenata

Una **coda** (*queue*) è una struttura dati lineare con politica primo entrato primo uscito (FIFO, *First In, First Out*) con inserimento in fondo (`enqueue`) e rimozione in testa (`dequeue`), oltre alla lettura della testa senza estrazione (`peek`). È il modello naturale per richieste di stampa, pacchetti di rete o sportelli di attesa.

Se implementi una coda su una lista semplicemente concatenata, tenere solo il puntatore `testa` renderebbe `enqueue` lineare, perché dovresti scorrere tutta la lista fino all'ultimo nodo. Aggiungendo un secondo puntatore `coda` nel descrittore, sia `enqueue` in fondo sia `dequeue` in testa lavorano in tempo costante. C'è però un caso limite critico: quando `dequeue` estrae l'**ultimo elemento rimasto** (e quindi `q->testa` diventa `nullptr`), devi azzerare esplicitamente anche `q->coda = nullptr;`. Se dimentichi questo passaggio, `q->coda` diventa un puntatore pendente verso un nodo già liberato e il successivo `enqueue` scriverà in memoria non valida (comportamento indefinito).

### La coda su buffer circolare dinamico

Una coda può essere implementata anche su un array dinamico contiguo senza spostare gli elementi a ogni `dequeue`. L'idea è trattare il blocco di memoria come un anello, chiamato **buffer circolare**: il descrittore mantiene `dati`, l'indice `inizio` del primo elemento valido, il numero di elementi `len` e la capacità `cap`.

L'elemento in posizione `k` (con `0 <= k < len`) si trova all'indice `(inizio + k) % cap`. Di conseguenza:

- `enqueue` scrive all'indice `(inizio + len) % cap` e incrementa `len`.
- `dequeue` legge `dati[inizio]`, aggiorna `inizio = (inizio + 1) % cap` e decrementa `len`.

Quando `len == cap`, il buffer è pieno e occorre raddoppiare la capacità (verificando prima l'overflow del prodotto `nuova_cap <= SIZE_MAX / sizeof(T)`). Fai attenzione a un errore molto frequente: **non puoi chiamare semplicemente `realloc`** lasciando gli elementi dov'erano se `inizio > 0`, perché gli elementi avvolti all'inizio dell'array verrebbero separati da un buco vuoto nel nuovo blocco, corrompendo l'ordine FIFO:

```text
Prima del raddoppio (cap=4, inizio=2, len=4):
indici:  [  0  ][  1  ][  2  ][  3  ]
dati:    [ 30  ][ 40  ][ 10  ][ 20  ]   ordine FIFO: 10, 20, 30, 40
                         ^ inizio

Dopo allocazione di nuovo blocco (cap=8) e riallineamento (inizio=0):
indici:  [  0  ][  1  ][  2  ][  3  ][  4  ][  5  ][  6  ][  7  ]
dati:    [ 10  ][ 20  ][ 30  ][ 40  ][  -  ][  -  ][  -  ][  -  ]
           ^ inizio
```

La sequenza corretta alloca un nuovo blocco con `malloc`, copia i `len` elementi in ordine FIFO tramite `nuovo[i] = c->dati[(c->inizio + i) % c->cap]`, libera il vecchio blocco con `free(c->dati)` e imposta `c->dati = nuovo; c->inizio = 0; c->cap = nuova_cap;`.

### Interfacce sicure contro l'estrazione da struttura vuota

Sia nelle pile sia nelle code, estrarre o leggere un elemento da una struttura vuota senza controllo provoca dereferenziazione di `nullptr` o accesso fuori dai limiti. Progetta quindi `pop`, `dequeue` e `peek` restituendo `bool` (`true` in caso di successo, `false` se la struttura è vuota) e scrivendo il valore estratto in un parametro di uscita (`int *out`):

<!-- cod: id=17.3-b tipo=frammento -->
```c
bool pila_pop(pila_t *p, int *out);
bool coda_dequeue(coda_t *c, int *out);
```

Secondo lo standard C23, le implementazioni di pile e code tramite liste concatenate o buffer circolari dinamici sono pienamente definite; estrarre da una struttura vuota senza controllo, leggere `coda` dopo la liberazione dell'ultimo nodo o accedere fuori dai limiti del buffer circolare provoca **comportamento indefinito**.

> **Se vieni da Python** — In Python le liste e `collections.deque` sono già pronte e la memoria è gestita automaticamente dal conteggio dei riferimenti e dal garbage collector; in C ogni nodo o buffer è allocato esplicitamente con `malloc` e liberato con `free`, scegliendo tu la rappresentazione in memoria più adatta al problema.

### Esempio guidato

Il programma seguente combina una pila su lista concatenata (usata per verificare il bilanciamento delle parentesi `()`, `[]` e `{}` in due espressioni) e una coda su lista concatenata con `testa` e `coda` (usata per accodare richieste, svuotare completamente la coda e riempirla di nuovo).

<!-- cod: id=17.3-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct nodo_c { char ch; struct nodo_c *prox; } nodo_c_t;
typedef struct pila_c { nodo_c_t *cima; } pila_c_t;

bool pila_push(pila_c_t *p, char ch) {
    nodo_c_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return false; }
    n->ch = ch;
    n->prox = p->cima;
    p->cima = n;
    return true;
}

bool pila_pop(pila_c_t *p, char *out) {
    if (p->cima == nullptr) { return false; }
    nodo_c_t *n = p->cima;
    *out = n->ch;
    p->cima = n->prox;
    free(n);
    return true;
}

void pila_distruggi(pila_c_t *p) {
    char scarto = '\0';
    while (pila_pop(p, &scarto)) {}
}

bool parentesi_bilanciate(const char *s) {
    pila_c_t p = {.cima = nullptr};
    for (size_t i = 0; s[i] != '\0'; ++i) {
        char c = s[i];
        if (c == '(' || c == '[' || c == '{') {
            if (!pila_push(&p, c)) { pila_distruggi(&p); return false; }
        } else if (c == ')' || c == ']' || c == '}') {
            char aperta = '\0';
            if (!pila_pop(&p, &aperta) ||
                (c == ')' && aperta != '(') ||
                (c == ']' && aperta != '[') ||
                (c == '}' && aperta != '{')) {
                pila_distruggi(&p);
                return false;
            }
        }
    }
    bool ok = (p.cima == nullptr);
    pila_distruggi(&p);
    return ok;
}

typedef struct nodo_q { int id; struct nodo_q *prox; } nodo_q_t;
typedef struct coda_q { nodo_q_t *testa; nodo_q_t *coda; } coda_q_t;

bool coda_enqueue(coda_q_t *q, int id) {
    nodo_q_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return false; }
    n->id = id;
    n->prox = nullptr;
    if (q->coda != nullptr) { q->coda->prox = n; } else { q->testa = n; }
    q->coda = n;
    return true;
}

bool coda_dequeue(coda_q_t *q, int *out) {
    if (q->testa == nullptr) { return false; }
    nodo_q_t *n = q->testa;
    *out = n->id;
    q->testa = n->prox;
    if (q->testa == nullptr) { q->coda = nullptr; }
    free(n);
    return true;
}

int main(void) {
    printf("Espressione 1: %s\n", parentesi_bilanciate("{[a+b]*(c-d)}") ? "valida" : "non valida");
    printf("Espressione 2: %s\n", parentesi_bilanciate("([)]") ? "valida" : "non valida");
    coda_q_t q = {};
    if (!coda_enqueue(&q, 10) || !coda_enqueue(&q, 20)) {
        int scarto = 0;
        while (coda_dequeue(&q, &scarto)) {}
        return EXIT_FAILURE;
    }
    int v = 0;
    while (coda_dequeue(&q, &v)) { printf("Servita richiesta %d\n", v); }
    if (!coda_enqueue(&q, 30)) { return EXIT_FAILURE; }
    if (coda_dequeue(&q, &v)) { printf("Nuovo ciclo: servita %d\n", v); }
    return 0;
}
```

```output
Espressione 1: valida
Espressione 2: non valida
Servita richiesta 10
Servita richiesta 20
Nuovo ciclo: servita 30
```

Nota alcuni dettagli progettuali importanti:

- In `parentesi_bilanciate`, ogni percorso di uscita anticipata chiama `pila_distruggi(&p)` prima di restituire `false`: così non si verificano perdite di memoria nemmeno quando l'espressione non è bilanciata.
- In `coda_dequeue`, la riga `if (q->testa == nullptr) { q->coda = nullptr; }` garantisce che, dopo aver servito `10` e `20` svuotando la coda, il successivo `coda_enqueue(&q, 30)` trovi `q->coda == nullptr` e inizializzi di nuovo `q->testa` e `q->coda` in modo coerente.
- Tutte le estrazioni restituiscono `bool`, evitando dereferenziazioni nulle su pila o coda vuota.

> **Approfondimento — Lista concatenata contro buffer circolare dinamico**
> Per pile e code, una lista concatenata evita riallocazioni in blocco e mantiene stabili gli indirizzi dei nodi, ma paga una chiamata a `malloc` per ogni elemento, memoria extra per i puntatori e nodi sparsi sullo heap. Un buffer circolare dinamico, al contrario, concentra gli elementi in un unico blocco contiguo: riduce drasticamente il numero di allocazioni e favorisce la cache del processore (lo vedremo nel capitolo 25).

### Esercizio 17.3 — Gestore di ticket con coda su buffer circolare dinamico e pila di annullamento su lista concatenata

**Descrizione**

Scrivi un programma C che combini le due discipline di accesso in un gestore di sportello: (1) una **coda** FIFO implementata tramite buffer circolare dinamico `typedef struct coda { int *dati; size_t inizio; size_t len; size_t cap; } coda_t;` (capacità iniziale `0`, crescita `0 -> 2 -> 4 -> 8 -> ...` allocando un nuovo blocco con `malloc` dopo il controllo `nuova_cap <= SIZE_MAX / sizeof(int)`, copiando gli elementi in ordine FIFO tramite `(c->inizio + i) % c->cap` e reimpostando `c->inizio = 0`), con funzioni `coda_init`, `coda_distruggi`, `coda_enqueue`, `coda_dequeue` e `coda_peek`; (2) una **pila** LIFO implementata tramite lista concatenata `typedef struct nodo_pila { int id; struct nodo_pila *prox; } nodo_pila_t;` e `typedef struct pila { nodo_pila_t *cima; size_t len; } pila_t;` per conservare la cronologia dei ticket serviti, con funzioni `pila_init`, `pila_distruggi`, `pila_push`, `pila_pop` e `pila_peek`. In `main` leggi comandi da `stdin` fino a fine input: `ENQ <id>` accoda `<id>` e stampa `ENQ <id> (coda len=<len> cap=<cap>)`; `SERVE` estrae il prossimo ticket dalla coda (FIFO), lo inserisce sulla pila (LIFO) e stampa `SERVE <id>` (oppure `CODA VUOTA` se vuota); `UNDO` estrae l'ultimo ticket servito dalla pila (LIFO), lo riaccoda in fondo alla coda e stampa `UNDO <id>` (oppure `PILA VUOTA` se vuota); `PEEK` legge senza rimuovere la testa della coda e la cima della pila stampando `PEEK coda=<id|vuota> pila=<id|vuota>`; `STAT` stampa tutti gli elementi della coda in ordine FIFO e della pila dalla cima alla base esattamente come nell'esempio. Libera tutta la memoria prima di uscire.

**Concetti da tenere a mente**

- disciplina FIFO della coda con buffer circolare dinamico e indicizzazione modulare `(inizio + i) % cap`
- riallineamento obbligatorio degli elementi del buffer circolare al raddoppio della capacità
- disciplina LIFO della pila su lista concatenata con `push`, `pop`, `peek` e distruzione iterativa
- gestione sicura delle operazioni su coda vuota e pila vuota mediante ritorno `bool`

**Domande guida**

1. Perché quando il buffer circolare è pieno con `inizio > 0` non basta chiamare `realloc` sul blocco esistente senza spostare gli elementi?
2. Quale formula calcola l'indice di scrittura del nuovo elemento in `coda_enqueue` e come va aggiornato `inizio` in `coda_dequeue`?
3. In che ordine rientrano in coda gli elementi se esegui due `SERVE` consecutivi seguiti da due `UNDO` consecutivi?
4. Come ti assicuri in `SERVE` e `UNDO` di non perdere un ticket se l'allocazione sulla struttura di destinazione dovesse fallire?

**Esempio di esecuzione**

```input
ENQ 101
ENQ 102
SERVE
ENQ 103
ENQ 104
PEEK
STAT
UNDO
SERVE
STAT
```

```output
ENQ 101 (coda len=1 cap=2)
ENQ 102 (coda len=2 cap=2)
SERVE 101
ENQ 103 (coda len=2 cap=2)
ENQ 104 (coda len=3 cap=4)
PEEK coda=102 pila=101
Coda (len=3, cap=4): 102 103 104
Pila (len=1): 101
UNDO 101
SERVE 102
Coda (len=3, cap=4): 103 104 101
Pila (len=1): 102
```

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

Nelle **ricerche per intervallo** `[lo, hi]` puoi sfruttare l'invariante per evitare di esplorare interi sottoalberi inutili (*potatura*): durante una visita in-ordine scendi in `rad->sx` solo se `rad->chiave > lo` (altrimenti tutto il sottoalbero sinistro è minore di `lo`), stampi `rad` se `rad->chiave >= lo && rad->chiave <= hi` e scendi in `rad->dx` solo se `rad->chiave < hi` (altrimenti tutto il sottoalbero destro è maggiore di `hi`).

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

## 17.5 Regole di possesso della memoria e distruzione

Finché i nodi di una lista o di un albero contengono solo valori semplici come `int` o array a dimensione fissa dentro la `struct`, liberare la struttura è lineare: basta chiamare `free` su ogni nodo. Nei programmi reali, però, i contenitori generici basati su `void *` memorizzano puntatori a stringhe allocate con `strdup`, a `struct` con campi dinamici annidati, oppure a oggetti già posseduti da un'altra parte del programma. Se non decidi prima chi deve chiamare `free` su quei dati, finisci in uno di tre difetti: nessuno li libera (perdita di memoria), li liberano in due (doppia liberazione), oppure uno li libera mentre l'altro li sta ancora usando (puntatore pendente e uso dopo la liberazione).

Per eliminare l'ambiguità si definisce il **possesso della memoria** (*ownership*): un contratto chiaro che stabilisce quale modulo o struttura dati è responsabile di liberare un blocco allocato dinamicamente. La regola di fondo è semplice ma inderogabile: **ogni blocco allocato sullo heap deve avere un solo proprietario alla volta**, e solo il proprietario può chiamare `free` su quel blocco.

### I tre contratti di possesso per un contenitore generico

Quando progetti un contenitore generico su `void *` — come una lista generica o una tabella hash (lo vedremo nel capitolo 18) — puoi scegliere tra tre contratti ben distinti:

1. **Trasferimento di possesso**: il chiamante alloca l'oggetto sullo heap e lo consegna al contenitore; da quel momento il contenitore diventa il proprietario e si occupa di liberarlo alla rimozione o alla distruzione. Il chiamante non deve più chiamare `free` su quel puntatore.
2. **Copia (clonazione)**: il contenitore duplica il dato al momento dell'inserimento (per esempio con `strdup` o una callback di copia) e possiede la propria copia; il chiamante resta proprietario dell'originale e può modificarlo o liberarlo liberamente.
3. **Prestito (*borrowing*)**: il contenitore memorizza solo puntatori a oggetti posseduti altrove (sullo stack o dentro un altro contenitore proprietario) e **non libera mai** i dati puntati, ma solo i propri nodi interni.

### La callback distruttore e la convenzione `nullptr`

Un contenitore generico non conosce il tipo concreto nascosto dietro `void *`, quindi non sa se per liberare un dato basti `free(dato)` (come per una stringa di `strdup`) o se occorra prima liberare campi dinamici annidati dentro una `struct`. La soluzione idiomatica in C combina `void *` (capitolo 15) e callback (capitolo 16) definendo un tipo di funzione distruttore:

<!-- cod: id=17.5-b tipo=frammento -->
```c
typedef void (*distruggi_fn)(void *dato);
```

Il descrittore del contenitore memorizza il puntatore `distruggi_fn distruggi;`, ricevuto all'inizializzazione:

- Se il contenitore è **proprietario** di blocchi semplici (per esempio stringhe allocate con `strdup`), passi direttamente `free`, la cui firma `void free(void *)` coincide esattamente con `distruggi_fn`.
- Se il contenitore è **proprietario** di `struct` con risorse annidate sullo heap, passi una funzione dedicata (per esempio `distruggi_documento`) che libera prima i campi interni e solo alla fine la `struct` stessa.
- Se il contenitore opera in modalità **prestito**, passi `nullptr`: alla rimozione e alla distruzione il contenitore controlla `if (l->distruggi != nullptr) { l->distruggi(curr->dato); }` prima di `free(curr)`, liberando così soltanto i propri nodi.

> **C23** — La funzione `strdup` di `<string.h>` è stata standardizzata in C23. Con compilatori che supportano solo C11 o C17 in modalità stretta, puoi duplicare una stringa allocando `strlen(s) + 1` byte con `malloc` e copiando con `memcpy`.

### Ordine di distruzione ed errori di allocazione

Due regole operative completano il contratto:

- **Ordine di distruzione tra proprietario e viste in prestito**: se hai un contenitore proprietario (`lista_prop`) e una seconda struttura in prestito (`lista_vista`) che punta a un sottoinsieme degli stessi oggetti, devi sempre distruggere `lista_vista` **prima** di rimuovere elementi da `lista_prop` o di distruggere `lista_prop`. In caso contrario i nodi di `lista_vista` conserverebbero puntatori pendenti verso memoria già liberata.
- **Fallimento di allocazione durante l'inserimento**: se `inserisci(contenitore, dato)` fallisce perché `malloc` per il nuovo nodo restituisce `nullptr`, il contenitore non ha preso in carico `dato`. Il contratto deve stabilire chiaramente che, in caso di errore, **il chiamante conserva la responsabilità** di liberare `dato` per evitare una perdita di memoria nel ramo di errore.

Verifica sistematicamente ogni programma che usa strutture dinamiche compilando con i sanitizer (AddressSanitizer e UndefinedBehaviorSanitizer, capitolo 11): sono la rete di sicurezza che conferma l'assenza di perdite, doppie liberazioni e usi dopo la liberazione. Queste stesse regole di possesso saranno il fondamento della tabella hash generica (lo vedremo nel capitolo 18).

Secondo lo standard C23, l'uso di callback `distruggi_fn` per regolare il possesso della memoria è pienamente definito; liberare lo stesso oggetto sia nel chiamante sia nel contenitore provoca doppia liberazione (**comportamento indefinito**), usarlo dopo la distruzione del proprietario provoca uso dopo la liberazione (**comportamento indefinito**), e non liberarlo da nessuna parte genera una perdita di memoria.

> **Se vieni da Python** — In Python è normale che più strutture condividano riferimenti allo stesso oggetto senza preoccuparsi dell'ordine di distruzione; in C condividere puntatori tra una struttura proprietaria e una vista in prestito richiede di distruggere sempre la vista prima del proprietario per evitare puntatori pendenti e doppie liberazioni.

### Esempio guidato

Il programma seguente definisce una lista generica `lista_gen_t` con nodi `void *` e callback `distruggi_fn`. La usa prima come contenitore proprietario di stringhe duplicate con `strdup` (passando `free` come distruttore) e poi come vista in prestito su `struct` allocate sullo stack (passando `nullptr` come distruttore).

<!-- cod: id=17.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void (*distruggi_fn)(void *dato);

typedef struct nodo_gen { void *dato; struct nodo_gen *prox; } nodo_gen_t;
typedef struct lista_gen { nodo_gen_t *testa; size_t len; distruggi_fn distruggi; } lista_gen_t;
typedef struct sensore { const char *nome; int valore; } sensore_t;

void lg_init(lista_gen_t *l, distruggi_fn distruggi) {
    *l = (lista_gen_t){.testa = nullptr, .len = 0, .distruggi = distruggi};
}

// In caso di fallimento (false), il chiamante resta proprietario di dato.
bool lg_inserisci_testa(lista_gen_t *l, void *dato) {
    nodo_gen_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return false; }
    n->dato = dato;
    n->prox = l->testa;
    l->testa = n;
    ++l->len;
    return true;
}

void lg_distruggi(lista_gen_t *l) {
    nodo_gen_t *curr = l->testa;
    while (curr != nullptr) {
        nodo_gen_t *prossimo = curr->prox;
        if (l->distruggi != nullptr) { l->distruggi(curr->dato); }
        free(curr);
        curr = prossimo;
    }
    l->testa = nullptr;
    l->len = 0;
}

int main(void) {
    lista_gen_t etichette;
    lg_init(&etichette, free);
    const char *parole[] = {"alfa", "beta", "gamma"};
    for (size_t i = 0; i < 3; ++i) {
        char *copia = strdup(parole[i]);
        if (copia == nullptr || !lg_inserisci_testa(&etichette, copia)) {
            free(copia);
            lg_distruggi(&etichette);
            return EXIT_FAILURE;
        }
    }
    printf("Proprietaria (%zu):", etichette.len);
    for (const nodo_gen_t *n = etichette.testa; n != nullptr; n = n->prox) {
        printf(" %s", (const char *)n->dato);
    }
    printf("\n");
    lg_distruggi(&etichette);

    sensore_t sensori[] = {{"T1", 22}, {"T2", 31}, {"T3", 19}};
    lista_gen_t vista;
    lg_init(&vista, nullptr);
    for (size_t i = 0; i < 3; ++i) {
        if (sensori[i].valore >= 20 && !lg_inserisci_testa(&vista, &sensori[i])) {
            lg_distruggi(&vista);
            return EXIT_FAILURE;
        }
    }
    printf("Vista prestito (%zu):", vista.len);
    for (const nodo_gen_t *n = vista.testa; n != nullptr; n = n->prox) {
        const sensore_t *s = n->dato;
        printf(" %s=%d", s->nome, s->valore);
    }
    printf("\n");
    lg_distruggi(&vista);
    return 0;
}
```

```output
Proprietaria (3): gamma beta alfa
Vista prestito (2): T2=31 T1=22
```

Osserva come la stessa implementazione di `lista_gen_t` rispetta entrambi i contratti:

- In `etichette`, passando `free` a `lg_init`, la lista assume il possesso delle copie create con `strdup`: `lg_distruggi(&etichette)` chiama `free(curr->dato)` e poi `free(curr)` per ogni nodo. Se `lg_inserisci_testa` fallisse, `main` chiamerebbe `free(copia)` perché il trasferimento di possesso non è avvenuto.
- In `vista`, passando `nullptr` a `lg_init`, la lista contiene indirizzi di elementi sullo stack (`&sensori[i]`): `lg_distruggi(&vista)` libera soltanto i nodi `nodo_gen_t` e non tenta mai di chiamare `free` su memoria dello stack.

> **Approfondimento — Documentare il contratto di possesso nell'interfaccia**
> Quando il codice cresce su più file, chi usa una libreria non deve essere costretto a leggerne l'implementazione per capire chi libera la memoria. Specificare nei commenti dell'interfaccia chi alloca il dato, chi ne resta proprietario in caso di errore di inserimento e quale distruttore verrà invocato alla chiusura previene perdite di memoria, puntatori pendenti e doppie liberazioni nei progetti modulari su più file (lo vedremo nel capitolo 19).

### Esercizio 17.5 — Lista generica con contratti di possesso espliciti: proprietà profonda tramite distruttore e vista in prestito

**Descrizione**

Scrivi un programma C che implementi una lista generica `typedef struct lista_gen { nodo_gen_t *testa; nodo_gen_t *coda; size_t len; distruggi_fn distruggi; } lista_gen_t;` con nodi `typedef struct nodo_gen { void *dato; struct nodo_gen *prox; } nodo_gen_t;` e callback `typedef void (*distruggi_fn)(void *dato);` e `typedef bool (*pred_dato_fn)(const void *dato, const void *ctx);`. Implementa: `void lg_init(lista_gen_t *l, distruggi_fn distruggi)`, `bool lg_inserisci_coda(lista_gen_t *l, void *dato)` (in caso di errore di allocazione del nodo NON libera `dato`), `size_t lg_rimuovi_se(lista_gen_t *l, pred_dato_fn pred, const void *ctx)` (rimuove tutti i nodi per cui `pred` è vero, chiamando `l->distruggi(nodo->dato)` se non nullo prima di `free(nodo)` e mantenendo coerente `l->coda`) e `void lg_distruggi(lista_gen_t *l)` (libera ogni nodo invocando `l->distruggi` se non nullo e azzera la lista). Definisci una risorsa con campi dinamici annidati `typedef struct documento { char *titolo; int *voti; size_t num_voti; size_t *cont_distrutti; } documento_t;`, una funzione `documento_t *crea_documento(const char *titolo, const int *voti, size_t k, size_t *cont_distrutti)` che duplica `titolo` con `strdup` e copia `voti` in un array `calloc`, `double media_documento(const documento_t *d)` e il distruttore profondo `void distruggi_documento(void *p)` che incrementa `*(d->cont_distrutti)` e libera `d->titolo`, `d->voti` e `d`. In `main` leggi dalla prima riga `n soglia_vista soglia_elim` (`0 <= n <= 16`) e dalle successive `n` righe `<titolo> <k> <v1> ... <vk>` (`1 <= k <= 8`). Inserisci tutti gli `n` documenti creati in `lista_prop` (inizializzata con `distruggi_documento`: proprietaria), poi costruisci `lista_vista` (inizializzata con `nullptr`: prestito!) inserendovi i puntatori ai documenti con `media >= soglia_vista`. Stampa `lista_vista`, distruggila PRIMA di `lista_prop` e verifica che `distrutti == 0`; quindi chiama `lg_rimuovi_se` su `lista_prop` per rimuovere i documenti con `media < soglia_elim`, stampa la lista proprietaria residua, distruggi `lista_prop` e stampa il bilancio `creati`/`distrutti` esattamente come nell'esempio.

**Concetti da tenere a mente**

- contratto di possesso della memoria tramite callback `distruggi_fn` (proprietà) e `nullptr` (prestito)
- distruzione profonda di una `struct` contenente puntatori annidati (`titolo`, `voti` e `struct` stessa)
- ordine di distruzione obbligatorio: distruggere la vista in prestito prima del contenitore proprietario
- mantenimento dell'invariante di `testa` e `coda` durante la rimozione selettiva in una lista generica

**Domande guida**

1. Perché `lista_vista` deve essere distrutta prima che `lista_prop` rimuova elementi o venga distrutta?
2. Che cosa accadrebbe se passassi `distruggi_documento` sia a `lista_prop` sia a `lista_vista`?
3. Perché `lg_inserisci_coda` non libera `dato` se `malloc` per il nodo fallisce, e come si comporta `main` in quel caso?
4. In che ordine deve liberare la memoria `distruggi_documento` per evitare sia perdite di memoria sia uso dopo la liberazione?

**Esempio di esecuzione**

```input
3 25.0 20.0
RelazioneA 3 28 30 26
BozzaB 2 18 16
TesinaC 2 22 24
```

```output
Vista prestito (>= 25.00, len=1): RelazioneA(28.00)
Dopo distruzione vista: distrutti=0
Rimossi (< 20.00): 1 (distrutti=1)
Proprietaria residua (len=2): RelazioneA(28.00) TesinaC(23.00)
Fine programma: creati=3 distrutti=3
```

## Riepilogo

- Una **lista concatenata** alloca ogni nodo singolarmente sullo heap tramite una `struct` auto-referenziata (`struct nodo *prox;`). Consente inserimenti e rimozioni senza spostare gli altri elementi, a costo di allocazioni per nodo e assenza di accesso diretto per indice. L'uso di un puntatore a puntatore (`nodo_t **cur = &lista->testa;`) unifica la gestione della testa e dei nodi interni, e la distruzione iterativa deve salvare `curr->prox` prima di chiamare `free(curr)`.
- Una **lista doppiamente concatenata** aggiunge i puntatori `prec` e `coda` per scorrere in entrambi i sensi e scollegare o spostare un nodo noto in tempo costante senza riallocazioni. Ogni operazione deve preservare gli invarianti (`testa->prec == nullptr`, `coda->prox == nullptr`, simmetria `a->prox == b` e `b->prec == a`) nei quattro casi limite: lista vuota, unico nodo, testa e coda.
- Una **pila** applica la disciplina LIFO (`push`, `pop`, `peek`) e una **coda** applica la disciplina FIFO (`enqueue`, `dequeue`, `peek`). In una coda su lista concatenata l'estrazione dell'ultimo elemento deve azzerare anche `coda = nullptr`; in una coda su buffer circolare dinamico l'indice del `k`-esimo elemento è `(inizio + k) % cap` e al raddoppio della capacità gli elementi vanno riallineati in ordine FIFO prima di impostare `inizio = 0`.
- Un **albero binario di ricerca** mantiene chiavi strettamente minori nel sottoalbero sinistro e maggiori nel sottoalbero destro. La visita in-ordine produce le chiavi ordinate; la rimozione gestisce 0 figli, 1 figlio o 2 figli (tramite il successore in-ordine, minimo del sottoalbero destro); la distruzione ricorsiva deve avvenire rigorosamente in post-ordine. Su chiavi già ordinate il BST degenera in una catena lineare (lo vedremo nel capitolo 23 con gli alberi AVL).
- Il **possesso della memoria** assegna a ogni blocco sullo heap un unico proprietario. Un contenitore generico su `void *` realizza il contratto (trasferimento, copia o prestito) tramite una callback `typedef void (*distruggi_fn)(void *dato);` (oppure `nullptr` per le viste in prestito), distruggendo sempre le viste prima del proprietario e verificando l'assenza di errori con i sanitizer. Questi principi guidano direttamente la progettazione della tabella hash generica (lo vedremo nel capitolo 18) e delle librerie su più file (lo vedremo nel capitolo 19).

## Errori comuni

- **Leggere `curr->prox` dopo aver chiamato `free(curr)`** durante la distruzione di una lista: provoca uso dopo la liberazione (comportamento indefinito). Salva sempre `nodo_t *prossimo = curr->prox;` prima di liberare `curr`.
- **Dimenticare di azzerare `coda = nullptr`** quando si rimuove l'ultimo elemento di una coda o di una lista doppiamente concatenata: lascia un puntatore pendente in `coda` che corrompe l'inserimento successivo.
- **Ridimensionare una coda su buffer circolare chiamando semplicemente `realloc`** quando `inizio > 0`: senza riallineare gli elementi in ordine FIFO e reimpostare `inizio = 0`, l'ordine degli elementi viene corrotto.
- **Liberare un nodo di un albero binario di ricerca in pre-ordine** prima di ricorrere sui figli `sx` e `dx` (uso dopo la liberazione), oppure dimenticare di rimuovere il successore in-ordine dal sottoalbero destro dopo averne copiato la chiave (lasciando un duplicato nell'albero).
- **Non definire un contratto di possesso chiaro**: liberare lo stesso oggetto sia nel chiamante sia nel contenitore causa doppia liberazione, usare una vista in prestito dopo la distruzione del proprietario genera puntatori pendenti, e dimenticare di liberare i campi dinamici annidati dentro una `struct` produce perdite di memoria.

## Prima di proseguire

- [ ] So implementare una lista semplicemente concatenata con inserimento ordinato, ricerca, rimozione tramite `nodo_t **cur` e distruzione iterativa sicura.
- [ ] So progettare una lista doppiamente concatenata preservando gli invarianti di `testa`, `coda`, `prec` e `prox` in tutti i casi limite, e spostare un nodo in testa senza allocazioni.
- [ ] So costruire pile LIFO e code FIFO sia su lista concatenata sia su buffer circolare dinamico con riallineamento al raddoppio della capacità e interfacce `bool` sicure.
- [ ] So implementare un albero binario di ricerca completo di inserimento, ricerca, visite ricorsive, query per intervallo con potatura, rimozione nei tre casi e distruzione in post-ordine.
- [ ] So definire e applicare contratti espliciti di possesso della memoria con callback `distruggi_fn` (e `nullptr` per viste in prestito), verificando il programma con i sanitizer.
