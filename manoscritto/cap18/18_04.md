## 18.4 La tabella hash generica con `void *` e puntatori a funzione

Le tabelle hash scritte nelle sotto-sezioni precedenti avevano un limite strutturale: i tipi della chiave (`char *`) e del valore (`int` o `double`), così come la funzione di hash (`hash_fnv1a`) e il confronto (`strcmp`), erano fissati nel codice della tabella. Se in uno stesso programma ti servono una mappa da codice fiscale a scheda studente e una mappa da coordinate `(x, y)` a nome di una zona, dovresti duplicare due volte l'intera implementazione della tabella hash.

Unendo il **puntatore generico** `void *` (capitolo 15) ai **puntatori a funzione** e alle **callback** (capitolo 16), puoi scrivere la tabella hash **una volta sola** e riutilizzarla con qualunque coppia di tipi.

### Nodi generici e tipi callback

Ogni nodo memorizza chiave e valore come `void *`, oltre all'hash precalcolato a 64 bit:

<!-- cod: id=18.4-b tipo=frammento -->
```c
typedef uint64_t (*hash_fn)(const void *chiave);
typedef bool (*uguali_fn)(const void *a, const void *b);
typedef void (*visita_fn)(const void *chiave, void *valore, void *ctx);

typedef struct nodo_ht {
    void *chiave;
    void *valore;
    uint64_t hash;
    struct nodo_ht *prox;
} nodo_ht_t;
```

La struttura della tabella `tab_ht_t` conserva `secchi`, `cap`, `len` e le due callback `hash` e `uguali` ricevute in fase di inizializzazione. La terza callback, `visita_fn`, viene passata a una funzione `ht_visita(const tab_ht_t *t, visita_fn fn, void *ctx)` che scorre tutti i secchi e invoca `fn(curr->chiave, curr->valore, ctx)` su ogni coppia. Grazie al parametro di contesto `void *ctx` (capitolo 16), il chiamante può accumulare somme, contare elementi che soddisfano un filtro o raccogliere risultati senza usare variabili globali e senza dover conoscere la struttura interna `nodo_ht_t`.

### L'invariante fondamentale e il filtro rapido sull'hash

Affinché una tabella hash generica funzioni correttamente, le due callback `hash_fn` e `uguali_fn` devono rispettare un contratto matematico rigoroso:

```text
se uguali(a, b) è true, allora deve valere hash(a) == hash(b)
```

Il contrario non è richiesto: due chiavi diverse possono avere lo stesso hash (è una collisione). Ma se due chiavi sono considerate uguali da `uguali_fn` e producono hash diversi, la ricerca finirà nel secchio sbagliato e dichiarerà assente una chiave che è in tabella.

Un esempio classico è la tabella con chiavi stringa **insensibili alle maiuscole e minuscole**: se `uguali_str_ci` confronta i caratteri convertendoli con `tolower((unsigned char)*p)`, allora anche `hash_str_ci` **deve** applicare `tolower((unsigned char)*p)` a ogni byte prima di aggiornarne l'hash. Se `hash_str_ci` usasse i caratteri originali, `"Alfa"` e `"alfa"` sarebbero uguali per `uguali_str_ci` ma produrrebbero hash diversi, rompendo la tabella.

Quando l'invariante vale, la ricerca lungo una catena può usare il **filtro rapido**:

<!-- cod: id=18.4-c tipo=frammento -->
```c
if (curr->hash == h && t->uguali(curr->chiave, chiave)) {
    return curr->valore;
}
```

Grazie alla valutazione a corto circuito di `&&`, `t->uguali` viene chiamata soltanto sui nodi che hanno già lo stesso hash a 64 bit `h`, evitando confronti costosi (come scansioni di stringhe lunghe) su tutti gli altri nodi in collisione sullo stesso secchio.

### Chiavi `struct` e il divieto di fare hash sui byte grezzi

Quando la chiave è una `struct`, è fortissima la tentazione di calcolare l'hash trattando l'intera struttura come un array di `sizeof(*s)` byte grezzi. **Questo è un errore grave.** Come hai visto nel capitolo 13, il compilatore può inserire byte di **padding** tra un campo e l'altro o in fondo alla `struct` per soddisfare i vincoli di allineamento. I byte di padding possono contenere valori indeterminati (residui lasciati sullo stack o sullo heap), quindi due variabili `struct` con gli stessi valori nei campi possono avere byte di padding diversi e produrre hash diversi, violando l'invariante `uguali(a, b) => hash(a) == hash(b)`.

La regola corretta è calcolare l'hash **combinando esplicitamente i singoli campi** uno per uno (per esempio estraendo i byte di ciascun campo intero con spostamenti e maschere `0xffU` e mescolandoli in FNV-1a). In questo modo l'hash dipende soltanto dal valore logico dei campi, è immune al padding ed è perfino indipendente dall'ordine dei byte della macchina.

Riassumiamo la regola precisa:

- Una tabella hash generica memorizza coppie `(void *chiave, void *valore)` e riceve le callback `hash_fn` e `uguali_fn`. Le due callback devono rispettare l'invariante fondamentale: se `uguali(a, b)` è `true`, allora deve valere `hash(a) == hash(b)`.
- Per chiavi di tipo `struct` non si deve mai calcolare l'hash sui byte grezzi della `struct` (`sizeof(*s)`), perché i byte di padding possono contenere valori indeterminati e far divergere l'hash di due chiavi logicamente uguali: occorre invece combinare esplicitamente i singoli campi.

Secondo lo standard C23, l'invocazione di callback su `const void *` e il calcolo dell'hash campo per campo sono completamente definiti; leggere byte di padding non inizializzati produce invece valori **non specificati** che violano il contratto dell'hash, e riconvertire `void *` a un tipo incompatibile con l'oggetto reale provoca **comportamento indefinito**.

> **Se vieni da Python** — In Python una tupla usata come chiave di un `dict` viene sottoposta a hash campo per campo in automatico; in C una `struct` contiene byte di padding che non vanno mai inclusi nell'hash, perciò devi scrivere una funzione di hash che combini esplicitamente i singoli campi.

### Esempio guidato

Il programma seguente definisce una tabella hash generica `tab_ht_t` e la istanzia due volte in `main` per due domini diversi: `citta` mappa sigle testuali (`"RM"`, `"MI"`, `"TO"`) a popolazioni (`int`), mentre `mappa` mappa coordinate `coord_t { int x; int y; }` a nomi di zona (`const char *`). Una callback di visita con `ctx` filtra le città sopra una soglia di popolazione.

<!-- cod: id=18.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint64_t (*hash_fn)(const void *);
typedef bool (*uguali_fn)(const void *, const void *);
typedef void (*visita_fn)(const void *, void *, void *);
typedef struct nodo { void *chiave; void *valore; uint64_t hash; struct nodo *prox; } nodo_t;
typedef struct { nodo_t **secchi; size_t cap, len; hash_fn hash; uguali_fn uguali; } tab_ht_t;
typedef struct { int x; int y; } coord_t;

bool ht_init(tab_ht_t *t, size_t cap, hash_fn h, uguali_fn u) {
    t->secchi = malloc(cap * sizeof(*t->secchi));
    if (t->secchi == nullptr) { return false; }
    for (size_t i = 0; i < cap; ++i) { t->secchi[i] = nullptr; }
    t->cap = cap; t->len = 0; t->hash = h; t->uguali = u;
    return true;
}

bool ht_imposta(tab_ht_t *t, void *k, void *v) {
    uint64_t h = t->hash(k); size_t idx = (size_t)(h % t->cap);
    for (nodo_t *c = t->secchi[idx]; c != nullptr; c = c->prox) {
        if (c->hash == h && t->uguali(c->chiave, k)) { c->valore = v; return true; }
    }
    nodo_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return false; }
    *n = (nodo_t){.chiave = k, .valore = v, .hash = h, .prox = t->secchi[idx]};
    t->secchi[idx] = n; ++t->len;
    return true;
}

void *ht_cerca(const tab_ht_t *t, const void *k) {
    uint64_t h = t->hash(k); size_t idx = (size_t)(h % t->cap);
    for (const nodo_t *c = t->secchi[idx]; c != nullptr; c = c->prox) {
        if (c->hash == h && t->uguali(c->chiave, k)) { return c->valore; }
    }
    return nullptr;
}

void ht_visita(const tab_ht_t *t, visita_fn fn, void *ctx) {
    for (size_t i = 0; i < t->cap; ++i) {
        for (const nodo_t *c = t->secchi[i]; c != nullptr; c = c->prox) { fn(c->chiave, c->valore, ctx); }
    }
}

void ht_distruggi(tab_ht_t *t) {
    for (size_t i = 0; i < t->cap; ++i) {
        for (nodo_t *c = t->secchi[i]; c != nullptr; ) { nodo_t *p = c->prox; free(c); c = p; }
    }
    free(t->secchi);
}

uint64_t hash_str(const void *p) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *s = p; *s != '\0'; ++s) { h ^= *s; h *= 1099511628211ULL; }
    return h;
}
bool uguali_str(const void *a, const void *b) { return strcmp(a, b) == 0; }
uint64_t hash_coord(const void *p) {
    const coord_t *c = p; uint64_t h = 14695981039346656037ULL;
    h ^= (uint32_t)c->x; h *= 1099511628211ULL; h ^= (uint32_t)c->y; h *= 1099511628211ULL;
    return h;
}
bool uguali_coord(const void *a, const void *b) {
    const coord_t *ca = a, *cb = b; return ca->x == cb->x && ca->y == cb->y;
}
void conta_grandi(const void *k, void *v, void *ctx) {
    (void)k; if (*(const int *)v >= 1000000) { ++(*(size_t *)ctx); }
}

int main(void) {
    tab_ht_t citta = {}, mappa = {};
    if (!ht_init(&citta, 8, hash_str, uguali_str) || !ht_init(&mappa, 8, hash_coord, uguali_coord)) {
        ht_distruggi(&citta); ht_distruggi(&mappa); return 1;
    }
    int pop[] = {2750000, 1350000, 850000}; size_t grandi = 0;
    coord_t p1 = {2, 5}, p2 = {-1, 3}, q = {2, 5};
    if (!ht_imposta(&citta, "RM", &pop[0]) || !ht_imposta(&citta, "MI", &pop[1]) ||
        !ht_imposta(&citta, "TO", &pop[2]) || !ht_imposta(&mappa, &p1, "Porto") ||
        !ht_imposta(&mappa, &p2, "Parco")) {
        ht_distruggi(&citta); ht_distruggi(&mappa); return 1;
    }
    ht_visita(&citta, conta_grandi, &grandi);
    const int *pop_mi = ht_cerca(&citta, "MI");
    if (pop_mi != nullptr) { printf("MI=%d, citta >= 1M: %zu\n", *pop_mi, grandi); }
    const char *zona = ht_cerca(&mappa, &q);
    if (zona != nullptr) { printf("Zona (2,5): %s\n", zona); }
    ht_distruggi(&citta); ht_distruggi(&mappa);
    return 0;
}
```

```output
MI=1350000, citta >= 1M: 2
Zona (2,5): Porto
```

Nota la separazione netta dei ruoli:

- Le funzioni `ht_*` non contengono alcun riferimento a `strcmp`, `int` o `coord_t`: funzionano su qualsiasi tipo purché il chiamante fornisca `hash_fn` e `uguali_fn` coerenti.
- In `hash_coord`, l'hash combina esplicitamente i due campi `c->x` e `c->y` (convertiti a `uint32_t`), senza mai leggere i byte grezzi della `struct`.
- In `conta_grandi`, il parametro `k` non serve e viene silenziato con `(void)k;`, mentre `ctx` punta al contatore locale `grandi` in `main`. Nota che qui `citta` e `mappa` operano in modalità *prestito*: i dati (`pop`, `p1`, `p2`, i letterali stringa) appartengono a `main`, e `ht_distruggi` libera solo i nodi e l'array `secchi`.

> **Approfondimento — La trappola del padding nelle chiavi `struct`**
> Considera una struttura `struct chiave_cella { uint8_t piano; int32_t stanza; };`. Su un'architettura comune con `int32_t` allineato a 4 byte, il compilatore inserisce 3 byte di padding tra `piano` (offset 0) e `stanza` (offset 4), portando `sizeof(struct chiave_cella)` a 8 byte. Se dichiari due variabili locali e assegni solo `.piano` e `.stanza`, quei 3 byte di padding possono contenere bit diversi rimasti sullo stack. Una funzione di hash che scansionasse tutti gli 8 byte grezzi calcolerebbe due hash diversi per due chiavi con lo stesso `piano` e la stessa `stanza`, violando `uguali(a, b) => hash(a) == hash(b)` e facendo fallire la ricerca in modo del tutto imprevedibile.

### Esercizio 18.4 — Tabella hash generica riutilizzata per chiavi stringa case-insensitive e chiavi struct con padding

**Descrizione**

Scrivi un programma C che implementi una tabella hash generica basata su `void *` e puntatori a funzione (`typedef uint64_t (*hash_fn)(const void *chiave);`, `typedef bool (*uguali_fn)(const void *a, const void *b);`, `typedef void (*visita_fn)(const void *chiave, void *valore, void *ctx);`) con ridimensionamento automatico al superamento del fattore di carico `0.75` (`(len + 1) * 4 > cap * 3`). Definisci `nodo_ht_t` (`void *chiave; void *valore; uint64_t hash; struct nodo_ht *prox;`) e `tab_ht_t` (`nodo_ht_t **secchi; size_t cap; size_t len; hash_fn hash; uguali_fn uguali;`) con le funzioni `ht_init`, `ht_ridimensiona`, `ht_inserisci` (`1` inserito, `0` aggiornato, `-1` errore), `ht_cerca`, `ht_rimuovi`, `ht_visita` e `ht_distruggi` (in modalità prestito: la tabella possiede solo i propri nodi, mentre `main` possiede i pool di chiavi e valori).

Riutilizza la STESSA `tab_ht_t` contemporaneamente per due tabelle in `main`:

1. `ht_str` con chiavi stringa `char[24]` confrontate in modo **insensibile alle maiuscole/minuscole** (`hash_str_ci` con FNV-1a su `tolower((unsigned char)*p)` e `uguali_str_ci` coerente, garantendo `uguali(a, b) => hash(a) == hash(b)`) e valori `int32_t`;
2. `ht_celle` con chiavi `typedef struct chiave_cella { uint8_t piano; int32_t stanza; } chiave_cella_t;` (struttura dotata di padding tra `piano` e `stanza`) e valori `double`, usando `hash_cella` calcolato **campo per campo** (FNV-1a sul byte `piano` e sui `4` byte di `(uint32_t)stanza` in ordine di spostamento `0, 8, 16, 24`, mai sui byte grezzi della struct) e `uguali_cella`.

Per dimostrare l'indipendenza dal padding, in `main` pre-riempi con `memset(..., 0x55, ...)` le chiavi memorizzate e con `memset(..., 0xAA, ...)` le chiavi di ricerca/rimozione prima di assegnare `.piano` e `.stanza`. Leggi da `stdin` i comandi `S_PUT <k> <v>`, `S_GET <k>`, `S_DEL <k>`, `C_PUT <piano> <stanza> <temp>`, `C_GET <piano> <stanza>`, `C_DEL <piano> <stanza>` e `REPORT <soglia_temp>` (che usa `ht_visita` con un contesto `ctx` per sommare i valori di `ht_str` e calcolare conteggio e media delle celle con temperatura `>= soglia_temp`), producendo l'output esatto dell'esempio.

**Concetti da tenere a mente**

- tabella hash generica su `void *` parametrizzata dalle callback `hash_fn`, `uguali_fn` e `visita_fn`
- invariante fondamentale `uguali(a, b) => hash(a) == hash(b)` sulle stringhe case-insensitive
- calcolo portabile campo per campo dell'hash di una `struct` per ignorare i byte di padding
- attraversamento della tabella generica tramite `ht_visita` e parametro di contesto `void *ctx`

**Domande guida**

1. Che cosa accadrebbe in `ht_str` se `uguali_str_ci` ignorasse maiuscole e minuscole ma `hash_str_ci` usasse i caratteri senza `tolower`?
2. Perché pre-riempire con `0x55` le chiavi inserite in `ht_celle` e con `0xAA` le chiavi passate a `ht_cerca` smaschera subito un hash calcolato erroneamente su `sizeof(chiave_cella_t)` byte?
3. In che modo `ht_visita` con il parametro `void *ctx` permette di aggregare dati di entrambi i domini senza esporre `nodo_ht_t` né usare variabili globali?
4. Perché il controllo `curr->hash == h && t->uguali(curr->chiave, chiave)` può evitare chiamate superflue a `t->uguali`?

**Esempio di esecuzione**

```input
S_PUT Alfa 10
S_PUT beta 25
S_PUT ALFA 40
S_GET alfa
C_PUT 1 101 21.5
C_PUT 2 204 18.0
C_PUT 1 101 23.0
C_GET 1 101
REPORT 20.0
S_DEL BETA
C_DEL 2 204
REPORT 20.0
```

```output
S_INS Alfa=10
S_INS beta=25
S_UPD ALFA=40
S_GET alfa: 40
C_INS (1,101)=21.5
C_INS (2,204)=18.0
C_UPD (1,101)=23.0
C_GET (1,101): 23.0
REPORT str: len=2 somma=65
REPORT celle: len=2 sopra_soglia=1 media_sopra=23.00
S_DEL BETA: OK
C_DEL (2,204): OK
REPORT str: len=1 somma=40
REPORT celle: len=1 sopra_soglia=1 media_sopra=23.00
```
