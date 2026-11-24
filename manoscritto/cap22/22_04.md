## 22.4 L'allocatore con lista libera

Finora hai visto due casi specializzati: l'arena (tutti gli oggetti si liberano insieme) e il pool (tutti gli oggetti hanno la stessa dimensione). Ma che cosa succede quando il programma ha bisogno di allocare e liberare in ordine arbitrario oggetti di **dimensioni diverse**, come messaggi di testo, pacchetti di rete o vettori di lunghezza variabile?

Prima di progettare un allocatore capace di gestire dimensioni variabili, conviene conoscere uno strumento del C pensato proprio per oggetti la cui lunghezza si conosce solo a tempo di esecuzione: il **campo array flessibile** (*flexible array member*). Si tratta dell'ultimo campo di una `struct`, dichiarato come array senza dimensione (`tipo nome[]`), che permette di allocare l'intestazione fissa e i dati variabili in un **unico blocco contiguo** di memoria, risparmiando una seconda allocazione e un puntatore indiretto:

<!-- cod: id=22.4-b tipo=frammento -->
```c
typedef struct messaggio {
    uint32_t id;
    size_t lunghezza;
    char testo[];   // campo array flessibile (sempre per ultimo)
} messaggio_t;
```

Lo standard C23 fissa regole precise per i campi array flessibili:

- Un campo array flessibile può comparire **solo come ultimo campo** di una `struct` che contenga **almeno un altro campo con nome** prima di esso.
- Non può appartenere a una `union`, né una `struct` che contiene un campo array flessibile può essere elemento di un array o campo di un'altra `struct`.
- `sizeof(messaggio_t)` **non include** gli elementi di `testo[]`, ma può includere eventuale padding finale dopo `lunghezza`. Per calcolare la dimensione esatta in byte per `N` elementi si usa `offsetof(messaggio_t, testo) + N * sizeof(char)` (oppure `sizeof(messaggio_t) + N * sizeof(char)`), verificando sempre l'assenza di overflow con `ckd_mul` e `ckd_add`.
- Copiare per assegnazione due strutture (`*dst = *src`) copia **solo i campi fissi** e ignora gli elementi del campo array flessibile; inoltre accedere oltre gli `N` elementi allocati provoca **comportamento indefinito**.

Ora passiamo al problema dell'allocatore generico. Se le richieste hanno dimensioni arbitrarie, non possiamo più usare slot a passo fisso come nel pool: l'allocatore deve tenere traccia della dimensione e dello stato (libero o occupato) di ogni singolo blocco. Il modo classico per farlo è una **lista libera** a blocchi di dimensione variabile, in cui ogni blocco di memoria è preceduto da una piccola **intestazione** (*header*) nascosta all'utente:

```text
Area gestita dall'allocatore (buffer unico diviso in blocchi):
+------------------+--------------------+------------------+---------------------------+
| Header 1         | Payload 1          | Header 2         | Payload 2                 |
| dim=32, lib=0    | (restituito)       | dim=96, lib=1    | (spazio libero residuo)   |
| prox -> Header 2 |                    | prox -> nullptr  |                           |
+------------------+--------------------+------------------+---------------------------+
                   ^ ptr utente 1
```

Affinché il payload restituito al chiamante sia sempre allineato ad `alignof(max_align_t)` (o a un allineamento minimo scelto come `ALLIN`), sono necessarie due condizioni:

1. L'intestazione `blocco_t` deve essere allineata ad `ALLIN` e avere `sizeof(blocco_t)` multiplo di `ALLIN` (da verificare con `static_assert(sizeof(blocco_t) % ALLIN == 0)`).
2. Ogni dimensione richiesta `dim` viene arrotondata al multiplo superiore di `ALLIN` (controllando l'overflow con `ckd_add`).

All'avvio, l'intera memoria gestita dall'allocatore è un unico grande blocco libero. Quando arriva una richiesta di `req` byte arrotondati, l'allocatore applica una strategia di ricerca come **first-fit**: scorre i blocchi dall'inizio e sceglie il primo blocco libero con `cur->dim >= req`. Se quel blocco è molto più grande di `req` — in particolare se lo spazio residuo basta per una nuova intestazione più almeno `ALLIN` byte di payload (`cur->dim >= req + sizeof(blocco_t) + ALLIN`) — l'allocatore esegue una **suddivisione** (*splitting*): ritaglia i primi `req` byte per il chiamante e crea un nuovo blocco libero subito dopo per la parte rimanente.

Qui emergono i due tipi fondamentali di spreco di memoria:

- **Frammentazione interna**: byte sprecati *dentro* un blocco assegnato a causa dell'arrotondamento all'allineamento (o perché il residuo era troppo piccolo per eseguire lo splitting).
- **Frammentazione esterna**: memoria libera sufficiente *in totale*, ma spezzettata in tanti piccoli blocchi non contigui, nessuno dei quali è abbastanza grande per soddisfare una nuova richiesta.

Per combattere la frammentazione esterna, al momento del rilascio l'allocatore non si limita a marcare il blocco come `libero = true`: esegue la **fusione** (*coalescing*), unendo due o più blocchi liberi fisicamente adiacenti in un unico blocco libero più grande (recuperando anche i byte delle intestazioni intermedie). Senza coalescing, dopo una serie di allocazioni e rilasci l'intera memoria resterebbe frammentata in ritagli inutilizzabili.

### Esempio guidato

Il programma seguente mostra prima una `struct` con campo array flessibile (`messaggio_t`) allocata in un solo blocco con `offsetof`, e poi un allocatore didattico con lista libera (`ALLIN = 16`) che alloca blocchi di dimensioni diverse tramite first-fit e splitting, mette in evidenza la frammentazione esterna quando un blocco intermedio resta occupato e ricompatta completamente lo spazio libero con il coalescing.

<!-- cod: id=22.4-a tipo=programma -->
```c
#include <stdckdint.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct messaggio {
    uint32_t id;
    size_t len;
    char testo[];
} messaggio_t;

static constexpr size_t ALLIN = (alignof(max_align_t) > 16) ? alignof(max_align_t) : 16;

typedef struct blocco {
    alignas(ALLIN) size_t dim;
    struct blocco *prox;
    bool libero;
} blocco_t;

static_assert(sizeof(blocco_t) % ALLIN == 0);

static void *fl_alloca(blocco_t *testa, size_t dim) {
    size_t somma = 0;
    if (dim == 0 || ckd_add(&somma, dim, ALLIN - 1)) { return nullptr; }
    size_t req = somma & ~(ALLIN - 1);
    for (blocco_t *c = testa; c != nullptr; c = c->prox) {
        if (!c->libero || c->dim < req) { continue; }
        unsigned char *pay = (unsigned char *)c + sizeof(blocco_t);
        if (c->dim >= req + sizeof(blocco_t) + ALLIN) {
            blocco_t *resto = (blocco_t *)(void *)(pay + req);
            resto->dim = c->dim - req - sizeof(blocco_t);
            resto->prox = c->prox;
            resto->libero = true;
            c->dim = req;
            c->prox = resto;
        }
        c->libero = false;
        return pay;
    }
    return nullptr;
}

static void fl_libera(blocco_t *testa, void *ptr) {
    for (blocco_t *c = testa; c != nullptr; c = c->prox) {
        if ((void *)((unsigned char *)c + sizeof(blocco_t)) == ptr) {
            c->libero = true;
            break;
        }
    }
    for (blocco_t *b = testa; b != nullptr && b->prox != nullptr; ) {
        if (b->libero && b->prox->libero) {
            b->dim += sizeof(blocco_t) + b->prox->dim;
            b->prox = b->prox->prox;
        } else {
            b = b->prox;
        }
    }
}

static void stampa_mappa(const char *fase, const blocco_t *testa) {
    printf("%s:", fase);
    for (const blocco_t *c = testa; c != nullptr; c = c->prox) {
        printf(" [%s:%zu]", c->libero ? "LIB" : "OCC", c->dim);
    }
    printf("\n");
}

int main(void) {
    const char *testo = "ciao C23";
    size_t n = strlen(testo) + 1;
    messaggio_t *m = malloc(offsetof(messaggio_t, testo) + n);
    if (m == nullptr) { return 1; }
    m->id = 7;
    m->len = n - 1;
    memcpy(m->testo, testo, n);
    printf("Messaggio #%u (%zu char): %s\n", m->id, m->len, m->testo);
    free(m);

    unsigned char *buf = malloc(256);
    if (buf == nullptr) { return 1; }
    blocco_t *testa = (blocco_t *)(void *)buf;
    *testa = (blocco_t){.dim = 256 - sizeof(blocco_t), .prox = nullptr, .libero = true};
    void *a = fl_alloca(testa, 32);
    void *b = fl_alloca(testa, 48);
    void *c = fl_alloca(testa, 32);
    stampa_mappa("Dopo 3 alloc", testa);
    fl_libera(testa, a);
    stampa_mappa("Libero a (framm.)", testa);
    printf("Richiesta 96 byte ora: %s\n", (fl_alloca(testa, 96) == nullptr) ? "OOM" : "OK");
    fl_libera(testa, b);
    stampa_mappa("Libero b (coalesc.)", testa);
    fl_libera(testa, c);
    stampa_mappa("Libero c (intero)", testa);
    free(buf);
    return 0;
}
```

```output
Messaggio #7 (8 char): ciao C23
Dopo 3 alloc: [OCC:32] [OCC:48] [OCC:32] [LIB:16]
Libero a (framm.): [LIB:32] [OCC:48] [OCC:32] [LIB:16]
Richiesta 96 byte ora: OOM
Libero b (coalesc.): [LIB:112] [OCC:32] [LIB:16]
Libero c (intero): [LIB:224]
```

Segui l'evoluzione della memoria riga per riga:

- Nella prima parte `offsetof(messaggio_t, testo) + n` calcola i byte esatti per intestazione e testo in un'unica `malloc`, liberata con una sola `free(m)`.
- Nella seconda parte il buffer iniziale da `256` byte ospita un'intestazione `blocco_t` da `32` byte e `224` byte liberi. Le tre allocazioni eseguono lo splitting fino a lasciare `16` byte liberi in fondo.
- Liberando `a`, ci sono `32 + 16 = 48` byte liberi ma separati (frammentazione esterna), e una richiesta da `96` byte fallisce (`OOM`). Appena liberiamo anche `b`, il coalescing fonde `a` e `b` (più i `32` byte dell'intestazione di `b`) in un unico blocco libero da `32 + 32 + 48 = 112` byte; liberando infine `c`, il buffer torna intero (`224` byte).

> **Approfondimento — Confronto tra i tre allocatori**
> Scegliere l'allocatore giusto dipende dal ciclo di vita dei dati: l'**arena** è ideale per dati con vita comune e rilascio in blocco ($O(1)$, zero metadati per oggetto); il **pool** è ideale per molti oggetti della stessa dimensione con rilascio individuale ($O(1)$, zero frammentazione esterna); la **lista libera** offre massima flessibilità per dimensioni variabili e rilasci arbitrari, al prezzo di metadati per ogni blocco e di un costo di ricerca proporzionale al numero di blocchi.

### Esercizio 22.4 — Allocatore con lista libera (first-fit, splitting, coalescing) per serie con campo array flessibile

**Descrizione**

Realizza su tre file (`alloc_libera.h`, `alloc_libera.c`, `main.c`) un allocatore a dimensione variabile con **lista libera** (`alloc_fl_t`, tipo opaco) usato per allocare record a lunghezza variabile dotati di **campo array flessibile**. (1) In `alloc_libera.h` (protetto da `ALLOC_LIBERA_H`) definisci `typedef struct alloc_fl alloc_fl_t;`, `typedef struct fl_stats { size_t blocchi_tot; size_t blocchi_occ; size_t blocchi_lib; size_t byte_occ; size_t byte_lib; size_t max_blocco_lib; } fl_stats_t;` e la struttura con campo array flessibile `typedef struct serie_dati { uint32_t id; size_t len; int32_t valori[]; } serie_dati_t;`, e dichiara `alloc_fl_t *fl_crea(size_t cap_byte);`, `void fl_distruggi(alloc_fl_t *a);`, `void *fl_alloca(alloc_fl_t *a, size_t dim);`, `bool fl_libera(alloc_fl_t *a, void *ptr);` e `void fl_statistiche(const alloc_fl_t *a, fl_stats_t *st);`. (2) In `alloc_libera.c` fissa `ALLIN_FL = (alignof(max_align_t) > 16) ? alignof(max_align_t) : 16` e definisci un'intestazione `blocco_fl_t` (allineata ad `ALLIN_FL` con `dim`, `prox`, `magico`, `libero`, verificando `static_assert(sizeof(blocco_fl_t) % ALLIN_FL == 0)`). `fl_crea` arrotonda per difetto `cap_byte` a multiplo di `ALLIN_FL`, alloca il buffer grezzo con `malloc` e inizializza un unico blocco libero. `fl_alloca` arrotonda `dim` a multiplo di `ALLIN_FL` (controllando overflow con `ckd_add`), applica **first-fit** ed esegue lo **splitting** quando lo spazio residuo è almeno `sizeof(blocco_fl_t) + ALLIN_FL`. `fl_libera` riconosce solo blocchi occupati validi della lista (rifiutando `nullptr`, puntatori estranei e doppie liberazioni) ed esegue il **coalescing** di tutti i blocchi liberi adiacenti. (3) In `main.c` gestisci `16` slot `serie_dati_t *handle[16]` con i comandi: `INIT <cap>`, `NEW <slot> <id> <k> <v1>...<vk>` (calcola i byte con `offsetof(serie_dati_t, valori) + k * sizeof(int32_t)` controllando overflow con `ckd_mul`/`ckd_add`, verifica allineamento a `alignof(serie_dati_t)`), `SUM <slot>`, `FREE <slot>` e `MAP`, riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- `struct` con campo array flessibile (`int32_t valori[]`) e calcolo della dimensione con `offsetof + k * sizeof(int32_t)`
- intestazione di blocco allineata ad `alignof(max_align_t)` affinché il payload successivo resti sempre allineato
- ricerca first-fit e suddivisione (splitting) di un blocco libero grande
- fusione dei blocchi liberi adiacenti (coalescing) per recuperare la frammentazione esterna

**Domande guida**

1. Perché `sizeof(serie_dati_t)` non include gli elementi di `valori[]` e come calcoli la dimensione esatta in byte per `k` interi senza overflow?
2. Quale condizione deve soddisfare un blocco libero di dimensione `cur->dim` affinché `fl_alloca` possa dividerlo in due blocchi separati?
3. Che cosa succede alla frammentazione esterna quando liberi due blocchi adiacenti senza eseguire il coalescing?
4. Perché l'intestazione `blocco_fl_t` deve avere dimensione multipla di `ALLIN_FL`?

**Esempio di esecuzione**

```input
INIT 256
MAP
NEW 0 101 4 10 20 30 40
NEW 1 102 8 1 2 3 4 5 6 7 8
NEW 2 103 4 5 5 5 5
SUM 0
SUM 1
MAP
FREE 0
MAP
NEW 3 104 8 1 1 1 1 1 1 1 1
FREE 1
MAP
NEW 3 104 8 1 1 1 1 1 1 1 1
SUM 3
FREE 2
FREE 3
MAP
```

```output
INIT: cap=256
MAP: blocchi=1 occ=0 lib=1 byte_occ=0 byte_lib=224 max_lib=224
NEW[0]: OK id=101 len=4 allin_ok=1
NEW[1]: OK id=102 len=8 allin_ok=1
NEW[2]: OK id=103 len=4 allin_ok=1
SUM[0]: id=101 somma=100
SUM[1]: id=102 somma=36
MAP: blocchi=4 occ=3 lib=1 byte_occ=112 byte_lib=16 max_lib=16
FREE[0]: OK
MAP: blocchi=4 occ=2 lib=2 byte_occ=80 byte_lib=48 max_lib=32
NEW[3]: OOM
FREE[1]: OK
MAP: blocchi=3 occ=1 lib=2 byte_occ=32 byte_lib=128 max_lib=112
NEW[3]: OK id=104 len=8 allin_ok=1
SUM[3]: id=104 somma=8
FREE[2]: OK
FREE[3]: OK
MAP: blocchi=1 occ=0 lib=1 byte_occ=0 byte_lib=224 max_lib=224
```
