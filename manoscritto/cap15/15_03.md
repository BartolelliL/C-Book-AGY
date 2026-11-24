## 15.3 Progettare un vettore dinamico generico

Nel capitolo 11 hai costruito un array dinamico di `int` con crescita geometrica tramite `realloc`. Quella struttura funzionava bene, ma era inchiodata a un solo tipo: se ti serviva anche un array dinamico di `double` o di `struct misura`, dovevi riscrivere tutte le funzioni di inizializzazione, inserimento, rimozione e liberazione cambiando soltanto il tipo dell'array.

Ora hai tutti gli ingredienti — `void *`, conversione a `unsigned char *`, `memcpy` e `memmove` — per costruire un **contenitore generico** (*generic container*): una struttura dati che memorizza elementi di tipo qualsiasi, noto al programma solo a tempo di esecuzione.

### Architettura di `vettore_gen`

Per gestire un blocco contiguo sullo heap senza conoscere il tipo `T` a tempo di compilazione, basta un'unica informazione aggiuntiva rispetto a un array dinamico tipizzato: quanti byte occupa ciascun elemento (`dim_elem`, di tipo `size_t`, passato dal chiamante come `sizeof(T)` al momento dell'inizializzazione).

<!-- cod: id=15.3-b tipo=frammento -->
```c
typedef struct vettore_gen {
    void *dati;       // blocco contiguo sullo heap (nullptr se cap == 0)
    size_t dim_elem;  // dimensione in byte di un singolo elemento (sizeof(T))
    size_t len;       // numero di elementi attualmente memorizzati
    size_t cap;       // numero di elementi allocati nel blocco dati
} vettore_gen_t;
```

Osserva come lo stesso identico tipo `vettore_gen_t` gestisca in memoria un vettore di `int` (4 byte per elemento) e un vettore di `struct coppia_xy` (16 byte per elemento):

```text
Vettore di int (dim_elem = 4, len = 3, cap = 4):
  dati -> [  10  ][  20  ][  30  ][ libero ]
          +0      +4      +8      +12      (byte)

Vettore di struct coppia_xy (dim_elem = 16, len = 2, cap = 4):
  dati -> [ x=1.0, y=2.0 ][ x=3.5, y=4.0 ][ libero ][ libero ]
          +0              +16             +32       +48      (byte)
```

Il contenitore non sa se i byte dentro `dati` rappresentino interi, numeri reali o strutture: sa soltanto che ogni slot è largo `dim_elem` byte e che lo slot di indice `idx` inizia esattamente a `idx * dim_elem` byte dall'inizio del blocco.

### Indirizzamento, copia e scorrimento degli elementi

Poiché `v->dati` ha tipo `void *`, non possiamo scrivere `v->dati[idx]` né `v->dati + idx`. Ogni operazione del contenitore segue sempre questo schema:

1. **Calcolo dell'indirizzo**: converte `v->dati` in `unsigned char *base = v->dati;` (oppure `const unsigned char *base = v->dati;` in lettura) e calcola l'indirizzo dell'elemento `idx` come `base + idx * v->dim_elem`.
2. **Inserimento e copia**: riceve il nuovo elemento tramite `const void *elem` e ne copia i `v->dim_elem` byte nello slot di destinazione con `memcpy(base + pos * v->dim_elem, elem, v->dim_elem)`.
3. **Inserimento o rimozione in posizione intermedia**: sposta gli elementi di coda dentro lo stesso blocco usando `memmove` (perché l'area di origine e l'area di destinazione si sovrappongono). Per esempio, per rimuovere l'elemento in posizione `pos < v->len`, se `pos + 1 < v->len` sposta `(v->len - pos - 1) * v->dim_elem` byte da `pos + 1` a `pos` e poi decrementa `v->len`.

Nota che quando `v->len == 0` il puntatore `v->dati` può essere `nullptr`: proteggendo sempre `memmove` con condizioni come `if (pos < v->len)` o `if (pos + 1 < v->len)` rispetti anche la regola C23 vista nella sotto-sezione 15.2.

### Crescita geometrica e prevenzione dell'overflow

Quando `v->len == v->cap` occorre espandere il blocco sullo heap, tipicamente raddoppiando la capacità (`0 -> 2 -> 4 -> 8 -> ...`). Prima di calcolare `nuova_cap * v->dim_elem` e passarlo a `realloc`, devi applicare due difese essenziali:

1. **Controllo di overflow sul prodotto**: verifica `if (nuova_cap > SIZE_MAX / v->dim_elem) { return false; }` (dopo esserti assicurato che `v->dim_elem > 0`). Senza questo controllo, una capacità enorme potrebbe andare in overflow e far allocare a `realloc` un blocco piccolissimo, aprendo un grave buffer overflow.
2. **Puntatore temporaneo per `realloc`**: assegna il risultato a `void *tmp = realloc(v->dati, nuova_cap * v->dim_elem);` e aggiorna `v->dati = tmp;` e `v->cap = nuova_cap;` solo se `tmp != nullptr`, preservando così il blocco precedente in caso di esaurimento della memoria.

### Perché l'allineamento è garantito automaticamente

A questo punto potresti porti una domanda legittima: nel capitolo 13 hai imparato che ogni tipo `T` ha un requisito di allineamento `alignof(T)` (per esempio 8 byte per `double` o per una `struct` che contiene `double`). Se il vettore generico calcola gli indirizzi con `unsigned char *` senza conoscere `T`, come fa a garantire che ogni elemento `base + idx * dim_elem` sia correttamente allineato?

La risposta combina due garanzie dello standard C23:
1. `malloc`, `calloc` e `realloc` restituiscono sempre un indirizzo allineato per **qualsiasi tipo con allineamento fondamentale** (quindi divisibile per `alignof(T)`).
2. Per qualunque tipo `T` (scalare o `struct`), lo standard garantisce che `sizeof(T)` sia sempre un **multiplo intero** di `alignof(T)` (proprio a questo serve il padding finale delle strutture visto nel capitolo 13).

Poiché `base` è multiplo di `alignof(T)` e `dim_elem == sizeof(T)` è multiplo di `alignof(T)`, anche `base + idx * dim_elem` è necessariamente multiplo di `alignof(T)` per ogni `idx`. L'allineamento è dunque garantito automaticamente per qualsiasi tipo omogeneo `T`.

### Limiti della genericità basata solo su `void *`

Un contenitore basato solo su `void *` e `dim_elem` è compatto e veloce, ma ha due limiti che devi conoscere bene:
- **Responsabilità del chiamante sui tipi**: il compilatore non può verificare che tu stia passando un `double *` a un vettore inizializzato con `sizeof(double)`. Passare un puntatore a un tipo o a una dimensione diversa da `dim_elem` provoca **comportamento indefinito** (lettura oltre i limiti dell'oggetto passato o errata interpretazione dei bit).
- **Copia superficiale (*shallow copy*)**: `memcpy` copia i byte dell'elemento così come sono. Se l'elemento è una `struct` che contiene al suo interno un puntatore a memoria allocata sullo heap (per esempio `char *nome`), `vg_free` libererà solo l'array `v->dati`, non le stringhe puntate dai singoli elementi; inoltre il contenitore non sa ancora confrontare due elementi per cercarli o ordinarli. Nei capitoli 16 e 17 supereremo questi limiti affiancando ai contenitori generici i **puntatori a funzione** per confronto e distruzione personalizzati.

> **Se vieni da Python** — In Python una lista può contenere oggetti di tipi diversi senza sforzo perché ogni elemento è un riferimento a un oggetto con informazioni di tipo a tempo di esecuzione; in C un contenitore generico manipola byte grezzi tramite `void *` e `dim_elem`, ottenendo compattezza e velocità al prezzo di richiedere rigore sui tipi.

### Esempio guidato

Il programma seguente implementa un vettore dinamico generico completo (`vg_init`, `vg_push`, `vg_get`, `vg_remove`, `vg_free`) e lo utilizza contemporaneamente per due tipi diversi: `double` e una struttura `coppia_xy_t`.

<!-- cod: id=15.3-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct vettore_gen {
    void *dati;
    size_t dim_elem;
    size_t len;
    size_t cap;
} vettore_gen_t;

typedef struct coppia_xy {
    int id;
    double x;
    double y;
} coppia_xy_t;

void vg_init(vettore_gen_t *v, size_t dim_elem) {
    *v = (vettore_gen_t){.dati = nullptr, .dim_elem = dim_elem, .len = 0, .cap = 0};
}

void vg_free(vettore_gen_t *v) {
    free(v->dati);
    *v = (vettore_gen_t){.dati = nullptr, .dim_elem = v->dim_elem, .len = 0, .cap = 0};
}

bool vg_push(vettore_gen_t *v, const void *elem) {
    if (v->dim_elem == 0 || elem == nullptr) { return false; }
    if (v->len == v->cap) {
        size_t nuova_cap = (v->cap == 0) ? 2 : (v->cap * 2);
        if (nuova_cap < v->cap || nuova_cap > SIZE_MAX / v->dim_elem) { return false; }
        void *tmp = realloc(v->dati, nuova_cap * v->dim_elem);
        if (tmp == nullptr) { return false; }
        v->dati = tmp;
        v->cap = nuova_cap;
    }
    unsigned char *base = v->dati;
    memcpy(base + v->len * v->dim_elem, elem, v->dim_elem);
    ++v->len;
    return true;
}

const void *vg_get(const vettore_gen_t *v, size_t idx) {
    if (idx >= v->len) { return nullptr; }
    return (const unsigned char *)v->dati + idx * v->dim_elem;
}

bool vg_remove(vettore_gen_t *v, size_t idx) {
    if (idx >= v->len) { return false; }
    unsigned char *base = v->dati;
    if (idx + 1 < v->len) {
        memmove(base + idx * v->dim_elem, base + (idx + 1) * v->dim_elem,
                (v->len - idx - 1) * v->dim_elem);
    }
    --v->len;
    return true;
}

int main(void) {
    vettore_gen_t reali, coppie;
    vg_init(&reali, sizeof(double));
    vg_init(&coppie, sizeof(coppia_xy_t));
    double campioni[3] = {1.5, 4.25, 9.0};
    for (size_t i = 0; i < 3; ++i) { vg_push(&reali, &campioni[i]); }
    vg_remove(&reali, 1);
    coppia_xy_t p1 = {1, 2.0, 3.5}, p2 = {2, -1.0, 0.5};
    vg_push(&coppie, &p1);
    vg_push(&coppie, &p2);
    printf("Reali (len=%zu, cap=%zu):", reali.len, reali.cap);
    for (size_t i = 0; i < reali.len; ++i) {
        const double *val = vg_get(&reali, i);
        printf(" %.2f", *val);
    }
    printf("\nCoppie (len=%zu, cap=%zu):", coppie.len, coppie.cap);
    for (size_t i = 0; i < coppie.len; ++i) {
        const coppia_xy_t *c = vg_get(&coppie, i);
        printf(" #%d(%.1f,%.1f)", c->id, c->x, c->y);
    }
    printf("\n");
    vg_free(&reali);
    vg_free(&coppie);
    return 0;
}
```

```output
Reali (len=2, cap=4): 1.50 9.00
Coppie (len=2, cap=2): #1(2.0,3.5) #2(-1.0,0.5)
```

Nota come lo stesso codice gestisce entrambi i tipi senza alcuna duplicazione:
- `vg_push` controlla sia il possibile overflow del raddoppio (`nuova_cap < v->cap`) sia l'overflow della moltiplicazione (`nuova_cap > SIZE_MAX / v->dim_elem`) prima di invocare `realloc`.
- In `reali`, inserire 3 elementi fa crescere la capacità da `0` a `2` e poi da `2` a `4`; la chiamata `vg_remove(&reali, 1)` sposta `9.0` sull'indice `1` tramite `memmove`, riducendo `len` a `2` mentre `cap` resta `4`.
- In lettura, `vg_get` restituisce `const void *`, che viene assegnato implicitamente a `const double *` per `reali` e a `const coppia_xy_t *` per `coppie`.
- Al termine `vg_free` libera entrambi i blocchi sullo heap e azzera i campi, lasciando i due vettori in uno stato pulito e privo di puntatori pendenti.

> **Approfondimento — Valori in blocco contiguo contro array di puntatori `void **`**
> Esistono due modelli principali per realizzare un contenitore generico in C. Il modello che hai appena costruito memorizza i valori direttamente uno accanto all'altro in un unico blocco `void *dati` con passo `dim_elem`: richiede una sola allocazione di memoria (e una sola `free`), garantisce migliore località di cache ed è ideale per tipi piccoli e omogenei. Il modello alternativo memorizza invece un array di puntatori `void **` a oggetti allocati separatamente sullo heap: introduce un'indirezione in più, ma permette di conservare oggetti grandi senza copiarli durante `realloc`, oppure oggetti di dimensioni diverse (lo ritroveremo nelle tabelle hash nel capitolo 18).

### Esercizio 15.3 — Vettore dinamico generico `vettore_gen_t` riutilizzato per `int64_t` e `struct misura_t`

**Descrizione**

Scrivi un programma C che implementi un contenitore generico `typedef struct vettore_gen { void *dati; size_t dim_elem; size_t len; size_t cap; } vettore_gen_t;` completamente indipendente dal tipo degli elementi. Implementa sette funzioni:
- `void vg_init(vettore_gen_t *v, size_t dim_elem)`
- `void vg_free(vettore_gen_t *v)`
- `bool vg_riserva(vettore_gen_t *v, size_t nuova_cap)` (controlla `nuova_cap <= SIZE_MAX / v->dim_elem` e usa `realloc` con puntatore temporaneo)
- `bool vg_inserisci(vettore_gen_t *v, size_t pos, const void *elem)` (`pos <= v->len`, raddoppia la capacità `0 -> 2 -> 4 -> ...` se necessario, sposta con `memmove` e copia con `memcpy`)
- `bool vg_rimuovi(vettore_gen_t *v, size_t pos, void *out)` (`pos < v->len`, copia in `out` se non nullo, sposta con `memmove` e decrementa `len`)
- `const void *vg_leggi(const vettore_gen_t *v, size_t pos)` (`nullptr` se fuori limiti)
- `bool vg_scambia(vettore_gen_t *v, size_t i, size_t j)` (scambia due elementi usando un buffer temporaneo dinamico di `v->dim_elem` byte e `memcpy`)

In `main` crea due `vettore_gen_t`: `v_num` per `int64_t` e `v_mis` per `typedef struct misura { int id; double valore; } misura_t;`. Leggi da `stdin` fino a fine input i comandi `NUM_INS <pos> <val64>`, `NUM_DEL <pos>` (stampa `DEL_NUM: <val>`), `NUM_SWAP <i> <j>`, `MIS_INS <pos> <id> <valore>`, `MIS_DEL <pos>` (stampa `DEL_MIS: #<id>=<valore:.2f>`) e `MIS_SWAP <i> <j>`; se un'operazione fallisce per posizione/indice non valido stampa `ERR` e prosegui. Al termine stampa contenuto, lunghezza e capacità di entrambi i vettori leggendo con `vg_leggi` e libera tutto con `vg_free`.

**Concetti da tenere a mente**

- progettazione di un contenitore generico con `void *dati`, `dim_elem`, `len` e `cap`
- calcolo dell'indirizzo dell'elemento `i`-esimo tramite `(unsigned char *)v->dati + i * v->dim_elem`
- inserimento, rimozione e scambio generici con `memcpy` e `memmove`
- controllo di overflow su `nuova_cap * dim_elem` con `SIZE_MAX / dim_elem`
- riutilizzo dello stesso codice su tipi scalari (`int64_t`) e strutture (`misura_t`)

**Domande guida**

1. Perché `vg_init` ha bisogno di ricevere `dim_elem = sizeof(tipo)` dal chiamante?
2. Come fa `vg_scambia` a scambiare due elementi di dimensione arbitraria senza conoscere a tempo di compilazione se siano `int64_t` o `misura_t`?
3. Quale condizione impedisce l'overflow del prodotto `nuova_cap * v->dim_elem` prima di chiamare `realloc`?
4. Perché dopo aver chiamato `vg_leggi(&v_mis, i)` devi assegnare il puntatore `const void *` restituito a `const misura_t *` prima di accedere a `->id` e `->valore`?

**Esempio di esecuzione**

```input
NUM_INS 0 100
NUM_INS 1 300
NUM_INS 1 200
NUM_SWAP 0 2
NUM_DEL 1
MIS_INS 0 10 12.5
MIS_INS 1 20 8.25
MIS_INS 0 30 4.0
MIS_SWAP 0 2
MIS_DEL 1
```

```output
DEL_NUM: 200
DEL_MIS: #10=12.50
NUM (len=2, cap=4): 300 100
MIS (len=2, cap=4): #20=8.25 #30=4.00
```
