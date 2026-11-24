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
    coda_enqueue(&q, 10);
    coda_enqueue(&q, 20);
    int v = 0;
    while (coda_dequeue(&q, &v)) { printf("Servita richiesta %d\n", v); }
    coda_enqueue(&q, 30);
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
