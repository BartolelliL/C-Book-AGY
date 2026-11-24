# Capitolo 18 — Tabelle hash

> **In questo capitolo imparerai a:**
> - Spiegare il funzionamento di una funzione di hash e il problema delle collisioni
> - Implementare una tabella hash con risoluzione delle collisioni per concatenamento
> - Monitorare il fattore di carico ed eseguire il ridimensionamento (rehashing) senza perdite di memoria
> - Progettare una tabella hash generica con `void *` e puntatori a funzione per hash, confronto e rilascio

> **Ti servono:** allocazione dinamica (capitolo 11), `struct` (capitolo 12), tipi a dimensione fissa e padding (capitolo 13), puntatore generico `void *` (capitolo 15), puntatori a funzione e callback (capitolo 16), liste concatenate e possesso della memoria (capitolo 17).

Nel capitolo 17 hai costruito liste concatenate, pile, code e alberi binari di ricerca, e hai fissato le regole per gestire il possesso della memoria nei contenitori dinamici. Quando però devi associare una chiave a un valore — per esempio un codice prodotto a un prezzo, il nome di una variabile al suo valore o un identificatore a una scheda utente — cercare in una lista richiede di scorrere in media metà degli elementi, mentre un albero binario di ricerca richiede una sequenza di confronti dalla radice alle foglie e può degenerare se le chiavi arrivano in ordine.

Una tabella hash risolve questo problema con un'idea diversa: invece di confrontare la chiave con molte altre chiavi una dopo l'altra, applica una formula matematica alla chiave per calcolare direttamente l'indice dell'array in cui il valore dovrebbe trovarsi. Se la formula distribuisce bene le chiavi e la tabella cresce quando diventa troppo piena, inserimento, ricerca e rimozione richiedono in media un numero costante di operazioni, indipendentemente dal fatto che la tabella contenga dieci elementi o un milione.

In questo capitolo metterai insieme quasi tutti gli strumenti costruiti finora: aritmetica intera senza segno a 64 bit, liste concatenate e puntatori a puntatori per gestire le collisioni, gestione rigorosa dell'overflow nel ridimensionamento, `void *`, callback per hash, confronto e visita, e contratti espliciti di possesso separati per chiavi e valori. Il risultato finale sarà una tabella hash generica completa, pronta per essere trasformata in una libreria modulare su più file nel capitolo 19.

## 18.1 Come funziona una tabella hash e cosa fa una funzione di hash

Immagina di dover cercare il prezzo di un articolo a partire dal suo codice testuale, come `"A104"` o `"mouse_usb"`, dentro un archivio di cinquantamila prodotti. Se conservi i prodotti in un array non ordinato o in una lista concatenata, nel caso medio devi esaminare metà delle voci prima di trovare quella giusta. Se li ordini in un array puoi usare la ricerca binaria, ma ogni nuovo inserimento obbliga a spostare migliaia di elementi. Un albero binario di ricerca bilancia meglio le due esigenze, ma richiede comunque una catena di confronti lungo l'altezza dell'albero e, come hai visto nel capitolo 17, può sbilanciarsi se le chiavi arrivano già ordinate.

Quando invece le chiavi sono piccoli interi consecutivi, come `0, 1, 2, ..., 99`, conosci già la soluzione più veloce possibile: un array indicizzato direttamente dalla chiave. L'accesso `prezzi[codice]` va subito alla cella desiderata in un solo passo. La **tabella hash** (*hash table*) generalizza esattamente questa idea a chiavi qualsiasi — stringhe, interi sparsi, coordinate, strutture — definendo una struttura dati associativa che mappa chiavi a valori usando una funzione di hash per accedere in tempo medio costante.

Il ponte tra una chiave arbitraria e un indice valido di array è la **funzione di hash** (*hash function*): una funzione deterministica che trasforma una chiave di dimensione arbitraria in un intero usato per scegliere il secchio (*bucket*) della tabella. Una volta ottenuto l'intero senza segno `h` (tipicamente di tipo `uint64_t` o `size_t`), lo si riduce a un indice compreso tra `0` e `num_secchi - 1` tramite l'operatore modulo:

```text
chiave "roma"  --->  funzione di hash  --->  h (uint64_t)  --->  h % num_secchi  --->  indice del secchio
```

### Proprietà di una buona funzione di hash per tabelle

Non tutte le funzioni che trasformano una chiave in un intero sono adatte a una tabella hash. Una funzione di hash efficace deve rispettare tre requisiti:

1. **Determinismo**: chiamata più volte su chiavi uguali, deve restituire sempre lo stesso identico valore. Non può dipendere da numeri casuali non fissati, dall'orario di sistema o dall'indirizzo di memoria in cui si trova la stringa.
2. **Distribuzione uniforme**: chiavi simili — per esempio `"chiave1"` e `"chiave2"`, oppure anagrammi come `"roma"` e `"amor"` — devono produrre valori di hash molto diversi, così da distribuirsi in modo equilibrato su tutti i secchi. Una funzione ingenua che somma i codici ASCII dei caratteri fallisce proprio qui: `"roma"`, `"amor"` e `"ramo"` contengono gli stessi byte in ordine diverso e producono la stessa somma.
3. **Efficienza**: poiché l'hash viene calcolato a ogni inserimento, ricerca e rimozione, il calcolo deve richiedere solo poche operazioni elementari per byte (XOR, moltiplicazioni, somme o spostamenti di bit).

È importante distinguere le funzioni di hash per tabelle hash dagli *hash crittografici* (come SHA-256). Un hash crittografico è progettato per resistere ad attacchi malevoli: deve essere computazionalmente impossibile risalire all'input dall'output o fabbricare due input con lo stesso hash, ed è quindi molto più lento. Una funzione di hash per tabelle punta invece a velocità e buona distribuzione statistica su dati ordinari; in caso di input provenienti da utenti non fidati in applicazioni di rete servono tecniche aggiuntive (come un seme casuale per processo), che esulano dalla struttura di base di questo capitolo.

### Implementazioni concrete in C23

Due funzioni classiche, compatte e affidabili per le stringhe sono **FNV-1a** a 64 bit e **djb2**. Entrambe elaborano la stringa un byte alla volta, combinando lo stato corrente `h` con ciascun byte tramite aritmetica intera senza segno:

<!-- cod: id=18.1-b tipo=frammento -->
```c
uint64_t hash_fnv1a_esempio(const char *s) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return h;
}
```

In FNV-1a il valore iniziale (`14695981039346656037ULL`, detto *offset basis*) e il moltiplicatore (`1099511628211ULL`, un numero primo scelto appositamente) fanno sì che la variazione di un singolo bit di ingresso o lo scambio di due caratteri adiacenti modifichi drasticamente tutti i bit di `h`. La variante **djb2** parte invece da `5381ULL` e aggiorna `h = h * 33ULL + (uint64_t)(*p);` per ogni byte `unsigned char`: è ancora più semplice, ma su alcune sequenze brevi o potenze di due tende a distribuire meno bene di FNV-1a.

Quando le chiavi sono già numeri interi (per esempio identificatori `uint64_t`), usare direttamente `x % num_secchi` può sembrare naturale, ma è rischioso se le chiavi hanno uno schema regolare. Se `num_secchi` è `8` e gli identificatori sono tutti multipli di `8` (come `0, 8, 16, 24, 32` — una situazione comunissima con indirizzi allineati), `x % 8` vale sempre `0` e tutte le chiavi finiscono nello stesso secchio. Per evitarlo si applica una funzione di **mescolamento di bit** (*bit mixing*), che combina spostamenti a destra (`>>`), XOR (`^`) e moltiplicazioni per costanti dispari a 64 bit:

<!-- cod: id=18.1-c tipo=frammento -->
```c
uint64_t mescola_u64(uint64_t x) {
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    return x;
}
```

Ogni passaggio diffonde l'influenza dei bit alti verso i bit bassi e viceversa, spezzando le regolarità aritmetiche prima della riduzione `h % num_secchi`.

### Collisioni e regola fondamentale

Anche con la migliore funzione di hash possibile, le chiavi possibili sono praticamente infinite (tutte le stringhe immaginabili), mentre i secchi della tabella sono un numero finito `num_secchi`. Per il **principio dei cassetti** (se metti più oggetti che cassetti, almeno un cassetto conterrà più di un oggetto), è matematicamente inevitabile che due chiavi diverse producano lo stesso indice di secchio. Questo evento si chiama **collisione** (*collision*): il caso in cui due chiavi distinte producono lo stesso indice di secchio in una tabella hash.

La conseguenza diretta è cruciale: una tabella hash **non può** basarsi soltanto sul valore di hash per decidere se ha trovato la chiave cercata. Deve sempre conservare la chiave originale dentro il secchio e confrontarla esplicitamente con quella cercata (per esempio con `strcmp` per le stringhe).

Riassumiamo la regola precisa:

- Una funzione di hash per tabelle hash è deterministica: a chiavi uguali deve produrre sempre lo stesso intero senza segno (`uint64_t` o `size_t`), poi ridotto all'indice del secchio mediante `h % num_secchi` (con `num_secchi > 0`).
- Nel calcolo dell'hash sui byte di una stringa o di un buffer occorre convertire i caratteri a `unsigned char` e usare aritmetica intera senza segno (il cui *wraparound* modulo `2^N` è definito), evitando sia il segno dipendente dall'implementazione di `char` sia l'overflow con segno.
- Per il principio dei cassetti le collisioni sono inevitabili, quindi la tabella deve memorizzare la chiave e verificarne l'uguaglianza.

Dal punto di vista dello standard C23, l'aritmetica modulare su `uint64_t` e `size_t` e la lettura dei byte come `unsigned char` sono completamente definite. Al contrario, il segno di `char` è **comportamento dipendente dall'implementazione**, mentre l'overflow su interi con segno (come `int` o `int64_t`) e l'operazione `h % 0` provocano **comportamento indefinito**.

> **Se vieni da Python** — In Python il tipo `dict` è integrato nel linguaggio, ridimensiona automaticamente, richiede chiavi immutabili (*hashable*) tramite `__hash__` e `__eq__` e gestisce la memoria con il garbage collector; in C occorre progettare esplicitamente secchi, collisioni, ridimensionamento, callback di hash e confronto e regole di possesso.

### Esempio guidato

Il programma seguente mette a confronto una funzione di hash ingenua (`hash_somma`, che somma i valori dei byte) con `hash_fnv1a` su quattro parole che includono tre anagrammi (`"roma"`, `"amor"`, `"mora"`). Per ciascuna parola stampa gli hash in esadecimale e gli indici di secchio modulo `8`.

<!-- cod: id=18.1-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

constexpr size_t NUM_SECCHI = 8;

uint64_t hash_somma(const char *s) {
    uint64_t h = 0;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h += (uint64_t)(*p);
    }
    return h;
}

uint64_t hash_fnv1a(const char *s) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return h;
}

int main(void) {
    const char *parole[] = {"roma", "amor", "mora", "sole"};
    size_t num_parole = sizeof(parole) / sizeof(parole[0]);

    for (size_t i = 0; i < num_parole; ++i) {
        uint64_t hs = hash_somma(parole[i]);
        uint64_t hf = hash_fnv1a(parole[i]);
        printf("%-4s | somma=0x%04" PRIx64 " (sec %zu) | fnv1a=0x%016" PRIx64 " (sec %zu)\n",
               parole[i],
               hs, (size_t)(hs % NUM_SECCHI),
               hf, (size_t)(hf % NUM_SECCHI));
    }

    return 0;
}
```

```output
roma | somma=0x01af (sec 7) | fnv1a=0xa35c141ff0caad88 (sec 0)
amor | somma=0x01af (sec 7) | fnv1a=0x8c778a83af1454b2 (sec 2)
mora | somma=0x01af (sec 7) | fnv1a=0x0d1beba2c400c74c (sec 4)
sole | somma=0x01b3 (sec 3) | fnv1a=0x6038c818f0bde8ac (sec 4)
```

Osserva il comportamento delle due funzioni:

- Con `hash_somma`, `"roma"`, `"amor"` e `"mora"` producono esattamente lo stesso valore (`0x01af`) e finiscono tutte nel secchio `7`. Poiché l'addizione è commutativa, qualunque permutazione degli stessi caratteri produce una collisione garantita.
- Con `hash_fnv1a`, invece, i tre anagrammi producono valori a 64 bit completamente diversi e si distribuiscono su tre secchi distinti (`0`, `2` e `4`).
- Nota però `"mora"` e `"sole"`: pur avendo hash a 64 bit del tutto diversi, entrambi finiscono nel secchio `4` dopo la riduzione `% 8`. Anche una buona funzione di hash genera collisioni quando l'hash viene ridotto a un numero piccolo di secchi: ecco perché una tabella hash deve sempre conservare la chiave e saper gestire le collisioni.

> **Approfondimento — Perché `unsigned char` e `uint64_t` sono obbligatori negli hash**
> In C lo standard lascia all'implementazione la scelta se il tipo `char` sia con segno o senza segno. Se un carattere non ASCII (come una lettera accentata codificata in UTF-8) ha il bit più significativo a `1`, su una piattaforma con `char` con segno viene letto come numero negativo; promosso a `uint64_t`, i suoi 56 bit superiori verrebbero riempiti di `1` (estensione del segno), producendo un hash diverso rispetto a una piattaforma dove `char` è senza segno. Convertire il puntatore a `const unsigned char *` garantisce valori sempre in `0..255` ovunque. Inoltre, moltiplicare per `1099511628211ULL` supera subito il massimo valore rappresentabile: su `int64_t` sarebbe overflow con segno (comportamento indefinito), mentre su `uint64_t` l'aritmetica è definita esattamente modulo `2^64`, quindi il risultato è identico su ogni compilatore conforme al C23.

### Esercizio 18.1 — Analizzatore di funzioni di hash e distribuzione sui secchi per stringhe e interi

**Descrizione**

Scrivi un programma C che implementi tre funzioni di hash deterministiche basate su aritmetica senza segno a `64` bit (`uint64_t`):

1. `uint64_t hash_fnv1a(const char *s)` (FNV-1a a 64 bit: valore iniziale `14695981039346656037ULL`, per ogni byte convertito a `unsigned char` esegue `h ^= byte; h *= 1099511628211ULL;`);
2. `uint64_t hash_djb2(const char *s)` (valore iniziale `5381ULL`, per ogni byte `unsigned char` esegue `h = h * 33ULL + byte;`);
3. `uint64_t hash_mix64(uint64_t x)` (mescolamento a 64 bit: `x ^= x >> 30; x *= 0xbf58476d1ce4e5b9ULL; x ^= x >> 27; x *= 0x94d049bb133111ebULL; x ^= x >> 31; return x;`).

Implementa inoltre `void stampa_stat(const char *nome, const size_t *cont, size_t m, size_t n)` che, dato l'array `cont` di lunghezza `m` contenente il numero di chiavi mappate in ciascun secchio, calcola `occupati` (secchi con `cont[i] > 0`), `vuoti` (`m - occupati`), `collisioni` (`n - occupati`) e `max_carico` (massimo di `cont[i]`), stampando `STAT <nome>: occupati=<occ> vuoti=<vuoti> collisioni=<coll> max_carico=<max>`.

In `main` leggi dalla prima riga `<modo> <m> <n>` dove `<modo>` è `STR` oppure `INT`, `1 <= m <= 64` e `0 <= n <= 64`. Alloca dinamicamente due array di contatori `size_t` di lunghezza `m` con `calloc`. Se `<modo>` è `STR`, leggi `n` righe contenenti ciascuna una parola (senza spazi, max `63` caratteri), calcola `i1 = (size_t)(hash_fnv1a(k) % m)` e `i2 = (size_t)(hash_djb2(k) % m)`, incrementa i rispettivi contatori, stampa `<parola>: fnv1a=<i1> djb2=<i2>` e al termine chiama `stampa_stat` per `fnv1a` e `djb2`. Se `<modo>` è `INT`, leggi `n` righe contenenti ciascuna un intero senza segno `uint64_t`, confronta `i1 = (size_t)(x % m)` (`identita`) con `i2 = (size_t)(hash_mix64(x) % m)` (`mix64`), stampa `<x>: identita=<i1> mix64=<i2>` e al termine stampa le statistiche per `identita` e `mix64`. Libera tutta la memoria allocata prima di uscire.

**Concetti da tenere a mente**

- determinismo della funzione di hash e riduzione all'indice di secchio con `h % m`
- uso obbligatorio di `uint64_t` e cast a `unsigned char` per evitare overflow con segno e `char` negativi
- confronto tra modulo diretto `x % m` e mescolamento di bit su chiavi intere strutturate (multipli di `m`)
- calcolo delle metriche di distribuzione: secchi occupati, secchi vuoti, collisioni e carico massimo

**Domande guida**

1. Perché nelle funzioni `hash_fnv1a` e `hash_djb2` devi convertire ogni carattere della stringa a `unsigned char` prima di combinarlo con `uint64_t`?
2. Che cosa succede alle collisioni con la funzione `identita` (`x % m`) se inserisci 8 chiavi intere tutte multiple di `m`?
3. Perché il numero totale di collisioni su `n` chiavi distribuite in `m` secchi equivale esattamente a `n - occupati`?
4. Quale vantaggio offre l'aritmetica su `uint64_t` rispetto a `int64_t` quando moltiplichi ripetutamente per una grande costante prima?

**Esempio di esecuzione**

```input
STR 8 5
roma
amor
mora
cane
gatto
```

```output
roma: fnv1a=0 djb2=4
amor: fnv1a=2 djb2=4
mora: fnv1a=4 djb2=4
cane: fnv1a=0 djb2=4
gatto: fnv1a=6 djb2=4
STAT fnv1a: occupati=4 vuoti=4 collisioni=1 max_carico=2
STAT djb2: occupati=1 vuoti=7 collisioni=4 max_carico=5
```

## 18.2 Gestire le collisioni con il concatenamento

Nella sotto-sezione precedente hai visto che le collisioni sono inevitabili: anche una buona funzione di hash può mappare due chiavi diverse sullo stesso indice di secchio. Se la tabella hash fosse un semplice array di valori, il secondo inserimento sovrascriverebbe il primo. Occorre quindi una strategia per ospitare più coppie chiave-valore che ricadono nello stesso secchio.

La strategia più diffusa e lineare da implementare in C è il **concatenamento** (*separate chaining*): ciascun elemento dell'array `secchi` non contiene direttamente una coppia chiave-valore, ma è un puntatore alla testa di una lista semplicemente concatenata (capitolo 17) che raccoglie tutti i nodi finiti in quel secchio. L'array dei secchi è quindi un array dinamico di puntatori a nodo, di tipo `nodo_t **secchi`, allocato sullo heap con tutti gli elementi inizializzati a `nullptr`.

```text
tabella_t:
  cap = 4, len = 3
  secchi -----> [0] ---> ["mela" | 5 | *] ---> nullptr
                [1] ---> ["kiwi" | 2 | *] ---> ["uva" | 4 | *] ---> nullptr
                [2] ---> nullptr
                [3] ---> nullptr
```

In questo schema `"kiwi"` e `"uva"` hanno prodotto entrambe l'indice di secchio `1`, quindi convivono nella catena collegata a `secchi[1]`. I secchi `2` e `3` sono vuoti (`nullptr`). Se la funzione di hash distribuisce bene le chiavi e il numero di secchi è proporzionato al numero di elementi, la maggior parte delle catene contiene zero, uno o due nodi, e ogni operazione esamina pochissimi elementi.

### Le quattro operazioni fondamentali

Ogni operazione su una tabella hash con concatenamento inizia calcolando `size_t idx = (size_t)(hash_fnv1a(chiave) % t->cap);` (con `t->cap > 0`) e lavorando poi **solo** sulla catena `t->secchi[idx]`:

1. **Ricerca**: scorre la catena `t->secchi[idx]` con un puntatore `const nodo_t *curr`. A ogni nodo confronta la chiave con `strcmp(curr->chiave, chiave) == 0`. Se trova corrispondenza restituisce il nodo (o il valore); se raggiunge `nullptr`, la chiave non è presente.
2. **Inserimento con semantica dizionario**: una tabella hash non ammette chiavi duplicate. Prima di allocare qualsiasi cosa, scorre la catena `t->secchi[idx]` per verificare se `chiave` esiste già. Se la trova, aggiorna semplicemente il campo `valore` sul nodo esistente e termina senza modificare `t->len` né allocare memoria. Se la chiave non è presente, alloca un nuovo nodo con `malloc`, duplica la stringa della chiave con `strdup(chiave)` (così la tabella possiede una propria copia indipendente dal buffer del chiamante), collega il nodo in testa alla catena (`n->prox = t->secchi[idx]; t->secchi[idx] = n;`) e incrementa `t->len`. Se `strdup` fallisce dopo che `malloc` per il nodo ha avuto successo, occorre liberare subito il nodo con `free(n)` prima di segnalare errore, evitando perdite di memoria.
3. **Rimozione**: applica esattamente la tecnica del puntatore a puntatore vista nel capitolo 17. Partendo da `nodo_t **cur = &t->secchi[idx];`, si avanza finché `*cur != nullptr && strcmp((*cur)->chiave, chiave) != 0` tramite `cur = &(*cur)->prox;`. Se `*cur` raggiunge `nullptr`, la chiave non esiste. Altrimenti si salva `nodo_t *da_lib = *cur;`, si aggiorna il puntatore con `*cur = da_lib->prox;` (che aggiorna automaticamente `t->secchi[idx]` se il nodo era il primo della catena, oppure `prec->prox` se era un nodo interno), si liberano `da_lib->chiave` e `da_lib`, e si decrementa `t->len`.
4. **Distruzione completa**: scorre tutti i secchi da `0` a `t->cap - 1`. Per ciascuna catena salva sempre `nodo_t *prossimo = curr->prox;` **prima** di chiamare `free(curr->chiave);` e `free(curr);`, altrimenti leggere `curr->prox` dopo `free(curr)` causerebbe un uso dopo la liberazione. Al termine del ciclo sui secchi libera l'array `free(t->secchi);` e azzera i campi della struttura (`t->secchi = nullptr; t->cap = 0; t->len = 0;`).

Riassumiamo la regola precisa:

- In una tabella hash con concatenamento l'array dei secchi ha tipo `nodo_t **secchi` (allocato sullo heap con tutti gli elementi inizializzati a `nullptr`), e ciascun secchio è la testa di una lista semplicemente concatenata.
- Inserimento, ricerca e rimozione operano sulla sola catena `secchi[idx]`: l'inserimento di una chiave già presente aggiorna il valore senza creare duplicati; la rimozione tramite puntatore a puntatore `nodo_t **cur = &t->secchi[idx]` unifica il caso del primo nodo e dei nodi interni; la distruzione libera ogni catena salvando `curr->prox` prima di liberare chiave e nodo, poi libera l'array `secchi`.

Secondo lo standard C23, l'inizializzazione esplicita di ogni puntatore `secchi[i] = nullptr` e la gestione delle catene sono completamente definite; al contrario, accedere a `secchi` con un indice fuori dai limiti o leggere `curr->prox` dopo `free(curr)` provoca **comportamento indefinito**.

> **Nota sull'indirizzamento aperto** — Il concatenamento non è l'unica strategia per risolvere le collisioni. Nell'*indirizzamento aperto* (*open addressing*), tutte le coppie risiedono direttamente dentro l'array dei secchi senza liste esterne: se il secchio `idx` è occupato, si esplora una sequenza di secchi alternativi (per esempio `idx + 1`, `idx + 2`, ..., modulo `cap`). Questa tecnica riduce le allocazioni e tiene i dati contigui in memoria, ma rende più delicata la rimozione (che richiede marcatori speciali di cella cancellata) e impone che il numero di elementi resti sempre strettamente inferiore alla capacità. In questo capitolo useremo il concatenamento, più chiaro e modulare per costruire una tabella generica.

### Esempio guidato

Il programma seguente realizza una piccola rubrica telefonica aziendale (`nome -> numero interno`) basata su una tabella hash a `8` secchi fissi con concatenamento. Inserisce quattro contatti (tra cui `"anna"` e `"piero"`, oppure altre coppie che collidono nello stesso secchio), aggiorna un interno esistente, cerca contatti presenti e assenti, rimuove nodi da una catena e distrugge la tabella in modo pulito.

<!-- cod: id=18.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct voce { char *nome; int interno; struct voce *prox; } voce_t;
typedef struct rubrica { voce_t **secchi; size_t cap; size_t len; } rubrica_t;

uint64_t hash_fnv1a(const char *s) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return h;
}

bool rubrica_init(rubrica_t *r, size_t cap) {
    r->secchi = malloc(cap * sizeof(*r->secchi));
    if (r->secchi == nullptr) { return false; }
    for (size_t i = 0; i < cap; ++i) { r->secchi[i] = nullptr; }
    r->cap = cap; r->len = 0;
    return true;
}

bool rubrica_imposta(rubrica_t *r, const char *nome, int interno) {
    size_t idx = (size_t)(hash_fnv1a(nome) % r->cap);
    for (voce_t *c = r->secchi[idx]; c != nullptr; c = c->prox) {
        if (strcmp(c->nome, nome) == 0) { c->interno = interno; return true; }
    }
    voce_t *v = malloc(sizeof(*v));
    if (v == nullptr) { return false; }
    v->nome = strdup(nome);
    if (v->nome == nullptr) { free(v); return false; }
    v->interno = interno; v->prox = r->secchi[idx];
    r->secchi[idx] = v; ++r->len;
    return true;
}

const voce_t *rubrica_cerca(const rubrica_t *r, const char *nome) {
    size_t idx = (size_t)(hash_fnv1a(nome) % r->cap);
    for (const voce_t *c = r->secchi[idx]; c != nullptr; c = c->prox) {
        if (strcmp(c->nome, nome) == 0) { return c; }
    }
    return nullptr;
}

bool rubrica_rimuovi(rubrica_t *r, const char *nome) {
    size_t idx = (size_t)(hash_fnv1a(nome) % r->cap);
    voce_t **cur = &r->secchi[idx];
    while (*cur != nullptr && strcmp((*cur)->nome, nome) != 0) { cur = &(*cur)->prox; }
    if (*cur == nullptr) { return false; }
    voce_t *da_lib = *cur; *cur = da_lib->prox;
    free(da_lib->nome); free(da_lib); --r->len;
    return true;
}

void rubrica_distruggi(rubrica_t *r) {
    for (size_t i = 0; i < r->cap; ++i) {
        for (voce_t *c = r->secchi[i]; c != nullptr; ) {
            voce_t *prossimo = c->prox; free(c->nome); free(c); c = prossimo;
        }
    }
    free(r->secchi); r->secchi = nullptr; r->cap = 0; r->len = 0;
}

int main(void) {
    rubrica_t rub = {};
    if (!rubrica_init(&rub, 8)) { return 1; }
    rubrica_imposta(&rub, "roma", 101); rubrica_imposta(&rub, "cane", 102);
    rubrica_imposta(&rub, "amor", 204); rubrica_imposta(&rub, "roma", 199);
    const voce_t *v1 = rubrica_cerca(&rub, "roma"), *v2 = rubrica_cerca(&rub, "luca");
    printf("roma -> %d, luca -> %s, len=%zu\n", v1->interno, v2 ? "trovato" : "assente", rub.len);
    printf("rimuovi cane: %s\n", rubrica_rimuovi(&rub, "cane") ? "ok" : "no");
    printf("rimuovi roma: %s, len=%zu\n", rubrica_rimuovi(&rub, "roma") ? "ok" : "no", rub.len);
    rubrica_distruggi(&rub);
    return 0;
}
```

```output
roma -> 199, luca -> assente, len=3
rimuovi cane: ok
rimuovi roma: ok, len=1
```

Osserva i punti chiave dell'esempio:

- `"roma"` e `"cane"` producono entrambe l'indice di secchio `0` modulo `8` con FNV-1a: `"cane"` viene inserito in testa alla catena di `secchi[0]`, seguito da `"roma"`.
- La seconda chiamata `rubrica_imposta(&rub, "roma", 199);` trova `"roma"` nella catena `secchi[0]` e ne aggiorna il campo `interno` da `101` a `199` senza allocare un nuovo nodo e lasciando `len` uguale a `3`.
- Quando `rubrica_rimuovi` elimina prima `"cane"` (in testa alla catena di `secchi[0]`) e poi `"roma"` (diventato unico elemento della catena), lo stesso ciclo su `voce_t **cur = &r->secchi[idx];` gestisce entrambi i casi senza rami speciali.
- Infine `rubrica_distruggi` rilascia il nodo rimasto (`"amor"`) e l'array `secchi`, azzerando la struttura.

> **Approfondimento — Perché inizializzare `secchi` con `malloc` e un ciclo a `nullptr`**
> Molti programmi C allocano array di puntatori con `calloc`, che azzera tutti i byte a `0`. Sulle piattaforme moderne la rappresentazione in memoria di `nullptr` coincide effettivamente con tutti bit a zero, ma lo standard C non lo impone in generale: su architetture storiche il puntatore nullo poteva avere una rappresentazione diversa. Allocare con `malloc(cap * sizeof(*r->secchi))` e scrivere un ciclo esplicito `for (size_t i = 0; i < cap; ++i) { r->secchi[i] = nullptr; }` è completamente portabile secondo lo standard C23 e rende esplicita l'intenzione a chi legge il codice.

### Esercizio 18.2 — Contatore di frequenze su tabella hash con concatenamento e ispezione dei secchi

**Descrizione**

Scrivi un programma C che implementi una tabella hash a capacità fissa con risoluzione delle collisioni per concatenamento per contare le frequenze di parole chiave. Definisci `typedef struct nodo_freq { char *chiave; int64_t conteggio; struct nodo_freq *prox; } nodo_freq_t;` e `typedef struct tab_freq { nodo_freq_t **secchi; size_t cap; size_t len; } tab_freq_t;`. Usa la funzione di hash FNV-1a a `64` bit su `unsigned char` (`offset = 14695981039346656037ULL`, `primo = 1099511628211ULL`) e implementa cinque funzioni:

1. `bool tab_init(tab_freq_t *t, size_t cap)` che alloca `t->secchi` con `malloc` (controllando `cap >= 1 && cap <= 64`) e inizializza esplicitamente ogni `t->secchi[i] = nullptr`;
2. `int tab_aggiungi(tab_freq_t *t, const char *chiave, int64_t delta, size_t *secchio_out, int64_t *val_out)` che cerca `chiave` nel secchio `idx = (size_t)(hash_fnv1a(chiave) % t->cap)`: se presente somma `delta` al `conteggio` e restituisce `0` (aggiornato); se assente alloca nodo e copia della chiave con `strdup`, inserisce in testa a `t->secchi[idx]`, incrementa `t->len` e restituisce `1` (inserito), oppure `-1` se l'allocazione fallisce senza perdere memoria;
3. `const nodo_freq_t *tab_cerca(const tab_freq_t *t, const char *chiave)`;
4. `bool tab_rimuovi(tab_freq_t *t, const char *chiave)` che rimuove il nodo tramite puntatore a puntatore `nodo_freq_t **cur = &t->secchi[idx];` liberando `chiave` e nodo;
5. `void tab_distruggi(tab_freq_t *t)` che libera tutte le catene, `t->secchi` e azzera i campi.

In `main` leggi dalla prima riga `cap` (`1 <= cap <= 64`), poi leggi comandi da `stdin` fino a fine input: `INC <parola> <delta>` (`delta > 0`), `GET <parola>`, `DEL <parola>` e `DUMP` (che stampa i secchi non vuoti in ordine di indice oppure `  (vuota)` se `len == 0`), producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- array dinamico di secchi `nodo_freq_t **secchi` con inizializzazione esplicita a `nullptr`
- gestione delle collisioni tramite liste semplicemente concatenate per secchio
- aggiornamento in-place su chiave duplicata e duplicazione con `strdup` solo su nuovo inserimento
- rimozione uniforme di testa e nodi interni di una catena con `nodo_freq_t **cur`
- distruzione completa salvando `curr->prox` prima di liberare chiave e nodo

**Domande guida**

1. Che cosa succede se in `tab_aggiungi` l'allocazione di `strdup(chiave)` fallisce dopo che `malloc` per il nodo è riuscita?
2. Perché nella rimozione dentro una catena del secchio `idx` conviene usare `nodo_freq_t **cur = &t->secchi[idx];`?
3. Come si comporta la tabella nel caso limite `cap == 1` con più chiavi diverse e perché è un ottimo banco di prova per le collisioni?
4. In che ordine devi liberare `curr->chiave`, `curr` e `t->secchi` in `tab_distruggi` per evitare sia perdite di memoria sia uso dopo la liberazione?

**Esempio di esecuzione**

```input
4
INC mela 2
INC pera 1
INC mela 3
INC uva 4
INC kiwi 2
DUMP
GET mela
GET pesca
DEL mela
DEL pesca
DUMP
```

```output
INS mela=2 (secchio=0)
INS pera=1 (secchio=3)
UPD mela=5 (secchio=0)
INS uva=4 (secchio=1)
INS kiwi=2 (secchio=1)
Tabella (len=4, cap=4):
  [0]: mela=5
  [1]: kiwi=2 -> uva=4
  [3]: pera=1
GET mela: 5
GET pesca: NON TROVATO
DEL mela: OK
DEL pesca: NON TROVATO
Tabella (len=3, cap=4):
  [1]: kiwi=2 -> uva=4
  [3]: pera=1
```

## 18.3 Fattore di carico e ridimensionamento

La tabella hash della sotto-sezione 18.2 ha un limite evidente: il numero di secchi `cap` resta fisso per tutta la durata del programma. Se apri una tabella con `8` secchi e vi inserisci `8000` chiavi, anche con una funzione di hash ideale ogni secchio accumula in media `1000` nodi. La ricerca non è più in tempo medio costante: degenera nella ricerca lineare su una lista di mille elementi.

Per misurare quanto una tabella hash è piena si definisce il **fattore di carico** (*load factor*): il rapporto tra il numero di elementi memorizzati in una tabella hash e il numero totale dei suoi secchi, cioè `alpha = (double)len / (double)cap`. Con il concatenamento, `alpha` coincide esattamente con la lunghezza media delle catene (inclusi i secchi vuoti). Finché `alpha` resta al di sotto di una soglia piccola — tipicamente `0.75` — le catene restano cortissime e le operazioni mantengono tempo medio costante.

### Controllare la soglia senza virgola mobile né overflow

Quando stai per inserire una **nuova** chiave (cioè dopo aver verificato che la chiave non sia già presente, perché un aggiornamento non aumenta `len`), devi chiederti se `(len + 1) / cap > 0.75`, ossia `3 / 4`. Invece di ricorrere a una divisione in virgola mobile, puoi trasformare la disuguaglianza in aritmetica intera esatta:

```text
(len + 1) / cap > 3 / 4    <===>    (len + 1) * 4 > cap * 3
```

L'aritmetica intera è più rapida ed evita qualunque imprecisione di arrotondamento. Bisogna però fare attenzione a un dettaglio: se `len` o `cap` fossero vicini a `SIZE_MAX`, le moltiplicazioni `(len + 1) * 4`, `cap * 3` o il calcolo della nuova capacità `cap * 2` e della sua dimensione in byte `nuova_cap * sizeof(nodo_t *)` potrebbero andare in *wraparound* su `size_t`. Prima di moltiplicare conviene quindi verificare i limiti:

<!-- cod: id=18.3-b tipo=frammento -->
```c
if (nuova_cap == 0 || nuova_cap > SIZE_MAX / sizeof(nodo_t *)) {
    return false;
}
```

### L'algoritmo di ridimensionamento per spostamento dei nodi

Quando la soglia viene superata si esegue il **ridimensionamento** (*rehashing*): l'operazione di riallocazione di una tabella hash con più secchi e ricalcolo delle posizioni di tutte le chiavi.

Attenzione a non confondere questo passaggio con `realloc`: non basta allargare l'array `secchi`, perché l'indice di ciascuna chiave dipende da `h % cap`. Cambiando `cap` (per esempio raddoppiandola da `4` a `8`), quasi tutte le chiavi cambiano secchio. Un nodo che prima stava nel secchio `1` perché `h % 4 == 1` potrebbe ora appartenere al secchio `5` perché `h % 8 == 5`.

Il modo pulito ed efficiente per eseguire il ridimensionamento consiste nello **spostare i nodi esistenti** senza allocarne di nuovi:

1. Si salva il valore di hash a 64 bit (`uint64_t hash`) direttamente dentro ogni nodo al momento dell'inserimento. Così durante il ridimensionamento non serve nemmeno ricalcolare la funzione di hash sulla stringa della chiave.
2. Si alloca un nuovo array `nodo_t **nuovi = malloc(nuova_cap * sizeof(*nuovi));` e si controlla subito se vale `nullptr`. Se `malloc` fallisce, la funzione restituisce `false` **senza aver toccato `t->secchi` né `t->cap`**: la tabella originale rimane integra e senza perdite di memoria.
3. Si inizializzano a `nullptr` tutti i puntatori di `nuovi`.
4. Si scorrono tutti i secchi del vecchio array `t->secchi`. Per ciascun nodo `c` della catena, si salva `nodo_t *prossimo = c->prox;`, si calcola il nuovo indice `size_t idx = (size_t)(c->hash % nuova_cap);` e si inserisce lo stesso nodo `c` in testa a `nuovi[idx]` (`c->prox = nuovi[idx]; nuovi[idx] = c;`).
5. Terminato lo spostamento, si libera il vecchio array `free(t->secchi);` e si aggiornano `t->secchi = nuovi;` e `t->cap = nuova_cap;`.

```text
Prima (cap = 4):
  secchi[1] ---> [n1: hash=13] ---> [n2: hash=9] ---> nullptr

Dopo (cap = 8):
  nuovi[1]  ---> [n2: hash=9 ] ---> nullptr   (9 % 8 == 1)
  nuovi[5]  ---> [n1: hash=13] ---> nullptr   (13 % 8 == 5)
```

I nodi `n1` e `n2` e le loro chiavi restano esattamente negli stessi indirizzi sullo heap: cambiano soltanto i puntatori `prox` e l'array dei secchi.

### Costo ammortizzato del raddoppio

A prima vista, ridimensionare la tabella può sembrare costoso perché richiede di visitare tutti gli `n` nodi presenti. Tuttavia, raddoppiando la capacità a ogni ridimensionamento (`4 -> 8 -> 16 -> 32 -> ...`), gli eventi di ridimensionamento diventano sempre più rari al crescere di `n`. Tra un ridimensionamento e il successivo avvengono tanti inserimenti veloci quanti sono i nodi da spostare: ripartendo il costo del ridimensionamento su tutti gli inserimenti che lo hanno provocato, il costo medio per singolo inserimento (detto *costo ammortizzato*) resta costante.

Riassumiamo la regola precisa:

- Il fattore di carico `alpha = (double)len / (double)cap` misura il riempimento medio dei secchi. Quando l'inserimento di una nuova chiave farebbe superare la soglia scelta (tipicamente `0.75`, verificabile in aritmetica intera come `(len + 1) * 4 > cap * 3` previa verifica di overflow), occorre eseguire il ridimensionamento allocando un nuovo array di secchi di capacità maggiore (controllando `nuova_cap <= SIZE_MAX / sizeof(nodo_t *)`), ricalcolando l'indice di secchio di ogni nodo esistente (preferibilmente riusando l'hash memorizzato nel nodo) e ricollegando i nodi esistenti senza riallocarli.
- Se `malloc` fallisce durante il ridimensionamento, la tabella originale deve restare integra senza perdite di memoria.

Secondo lo standard C23, il controllo di overflow su `nuova_cap * sizeof(nodo_t *)` e lo spostamento dei puntatori ai nodi sono definiti; al contrario, liberare o sovrascrivere `t->secchi` prima di verificare che il nuovo array sia diverso da `nullptr` provoca una perdita di memoria oppure una dereferenziazione nulla (**comportamento indefinito**).

### Esempio guidato

Il programma seguente gestisce un listino prezzi (`codice prodotto -> prezzo` in euro) con capacità iniziale `4`. A ogni inserimento che farebbe superare la soglia `0.75`, la tabella raddoppia la propria capacità spostando i nodi esistenti e stampa lo stato (lunghezza, capacità, fattore di carico e catena più lunga) prima e dopo il ridimensionamento.

<!-- cod: id=18.3-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct voce_prezzo { char *codice; uint64_t hash; double prezzo; struct voce_prezzo *prox; } voce_prezzo_t;
typedef struct listino { voce_prezzo_t **secchi; size_t cap; size_t len; } listino_t;

uint64_t hash_fnv1a(const char *s) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p); h *= 1099511628211ULL;
    }
    return h;
}

size_t max_catena(const listino_t *l) {
    size_t max_c = 0;
    for (size_t i = 0; i < l->cap; ++i) {
        size_t n = 0;
        for (const voce_prezzo_t *c = l->secchi[i]; c != nullptr; c = c->prox) { ++n; }
        if (n > max_c) { max_c = n; }
    }
    return max_c;
}

void stampa_stato(const char *fase, const listino_t *l) {
    printf("%-12s len=%zu cap=%zu carico=%.2f max_catena=%zu\n",
           fase, l->len, l->cap, (double)l->len / (double)l->cap, max_catena(l));
}

bool listino_rehash(listino_t *l, size_t nuova_cap) {
    if (nuova_cap == 0 || nuova_cap > SIZE_MAX / sizeof(*l->secchi)) { return false; }
    voce_prezzo_t **nuovi = malloc(nuova_cap * sizeof(*nuovi));
    if (nuovi == nullptr) { return false; }
    for (size_t i = 0; i < nuova_cap; ++i) { nuovi[i] = nullptr; }
    for (size_t i = 0; i < l->cap; ++i) {
        for (voce_prezzo_t *c = l->secchi[i]; c != nullptr; ) {
            voce_prezzo_t *p = c->prox;
            size_t idx = (size_t)(c->hash % nuova_cap);
            c->prox = nuovi[idx]; nuovi[idx] = c; c = p;
        }
    }
    free(l->secchi); l->secchi = nuovi; l->cap = nuova_cap;
    return true;
}

bool listino_imposta(listino_t *l, const char *codice, double prezzo) {
    uint64_t h = hash_fnv1a(codice);
    size_t idx = (size_t)(h % l->cap);
    for (voce_prezzo_t *c = l->secchi[idx]; c != nullptr; c = c->prox) {
        if (c->hash == h && strcmp(c->codice, codice) == 0) { c->prezzo = prezzo; return true; }
    }
    if ((l->len + 1) * 4 > l->cap * 3) {
        stampa_stato("Prima rehash", l);
        if (l->cap > SIZE_MAX / 2 || !listino_rehash(l, l->cap * 2)) { return false; }
        stampa_stato("Dopo rehash", l);
        idx = (size_t)(h % l->cap);
    }
    voce_prezzo_t *v = malloc(sizeof(*v));
    if (v == nullptr) { return false; }
    v->codice = strdup(codice);
    if (v->codice == nullptr) { free(v); return false; }
    v->hash = h; v->prezzo = prezzo; v->prox = l->secchi[idx];
    l->secchi[idx] = v; ++l->len;
    return true;
}

void listino_distruggi(listino_t *l) {
    for (size_t i = 0; i < l->cap; ++i) {
        for (voce_prezzo_t *c = l->secchi[i]; c != nullptr; ) {
            voce_prezzo_t *p = c->prox; free(c->codice); free(c); c = p;
        }
    }
    free(l->secchi);
}

int main(void) {
    listino_t l = {.secchi = malloc(4 * sizeof(*l.secchi)), .cap = 4, .len = 0};
    if (l.secchi == nullptr) { return 1; }
    for (size_t i = 0; i < l.cap; ++i) { l.secchi[i] = nullptr; }
    const char *codici[] = {"penna", "libro", "zaino", "gomma", "riga", "diario", "album"};
    for (size_t i = 0; i < 7; ++i) {
        if (!listino_imposta(&l, codici[i], 2.5 + (double)i)) { listino_distruggi(&l); return 1; }
    }
    listino_distruggi(&l);
    return 0;
}
```

```output
Prima rehash len=3 cap=4 carico=0.75 max_catena=1
Dopo rehash  len=3 cap=8 carico=0.38 max_catena=1
Prima rehash len=6 cap=8 carico=0.75 max_catena=2
Dopo rehash  len=6 cap=16 carico=0.38 max_catena=1
```

Nota come lavora `listino_imposta`:

- I primi tre prodotti portano `len` a `3` su `cap = 4` (`carico = 0.75`). Quando arriva il quarto prodotto (`"gomma"`), `(3 + 1) * 4 > 4 * 3` (`16 > 12`) è vero: scatta `listino_rehash` da `4` a `8` e il carico si dimezza da `0.75` a `0.38`.
- Al settimo prodotto (`"album"`), la tabella raddoppia di nuovo da `8` a `16` secchi e la catena più lunga scende da `2` a `1`.
- Dopo `listino_rehash`, `idx` viene ricalcolato (`idx = (size_t)(h % l->cap);`) usando la nuova capacità prima di inserire il nuovo nodo. Dimenticare di aggiornare `idx` dopo il ridimensionamento è un bug classico che finirebbe per inserire il nodo nel secchio sbagliato!
- Anche `listino_imposta` confronta prima `c->hash == h` e solo in caso di corrispondenza chiama `strcmp`: questo accelera la ricerca lungo la catena, perché confrontare due interi `uint64_t` costa una sola istruzione.

> **Approfondimento — Perché spostare i nodi è meglio che reinserirli**
> Un'implementazione ingenua del ridimensionamento alloca una nuova tabella e richiama `listino_imposta` per ogni elemento, duplicando chiavi e nodi e poi distruggendo la vecchia tabella. Spostare i nodi esistenti è nettamente superiore per tre motivi: esegue **una sola** chiamata a `malloc` (l'array `nuovi`), non duplica alcuna stringa né ricalcola gli hash, e soprattutto è **atomico rispetto agli errori di memoria**: se quella singola `malloc` fallisce, non è stato modificato nulla e la tabella precedente resta intatta senza alcuna pulizia parziale.

### Esercizio 18.3 — Tabella hash auto-ridimensionante con soglia intera, hash memorizzato nel nodo e spostamento a zero allocazioni

**Descrizione**

Scrivi un programma C che implementi una tabella hash di configurazione (`char *chiave -> int32_t valore`) capace di eseguire il ridimensionamento automatico (rehashing) spostando i nodi esistenti senza allocarne di nuovi. Definisci `typedef struct nodo_cfg { char *chiave; uint64_t hash; int32_t valore; struct nodo_cfg *prox; } nodo_cfg_t;` e `typedef struct tab_cfg { nodo_cfg_t **secchi; size_t cap; size_t len; size_t num_rehash; size_t nodi_allocati; } tab_cfg_t;`. Implementa:

1. `bool tab_init(tab_cfg_t *t, size_t cap)` (`1 <= cap <= 16`);
2. `bool tab_ridimensiona(tab_cfg_t *t, size_t nuova_cap, size_t *spostati_out)` che verifica `nuova_cap >= 1 && nuova_cap <= 1024 && nuova_cap <= SIZE_MAX / sizeof(*t->secchi)`, alloca il nuovo array di secchi inizializzato a `nullptr`, sposta tutti i nodi esistenti ricalcolando solo `nodo->hash % nuova_cap` (senza chiamare `hash_fnv1a` né `malloc` per nodo), libera il vecchio `t->secchi`, aggiorna `t->secchi`, `t->cap` e incrementa `t->num_rehash` (se fallisce lascia la tabella intatta);
3. `int tab_put(tab_cfg_t *t, const char *chiave, int32_t val, bool *rehash_fatto, size_t *vecchia_cap, size_t *spostati)` che prima controlla se `chiave` è già presente (se sì aggiorna il valore e restituisce `0` SENZA attivare il ridimensionamento), altrimenti se `(t->len + 1) * 4 > t->cap * 3` chiama `tab_ridimensiona(t, t->cap * 2, spostati)`, poi alloca il nuovo nodo (incrementando `t->nodi_allocati`) e inserisce in testa restituendo `1` (`-1` in caso di errore);
4. `const nodo_cfg_t *tab_cerca(const tab_cfg_t *t, const char *chiave)` (confrontando `c->hash == h && strcmp(c->chiave, chiave) == 0`), `bool tab_rimuovi(tab_cfg_t *t, const char *chiave)`, `size_t tab_max_catena(const tab_cfg_t *t)` e `void tab_distruggi(tab_cfg_t *t)`.

In `main` leggi dalla prima riga `cap_iniziale` (`1 <= cap_iniziale <= 16`), poi leggi comandi fino a fine input: `PUT <chiave> <val>`, `GET <chiave>`, `DEL <chiave>`, `RESERVE <target_cap>` (rifiuta con `RESERVE RIFIUTATO` se `target_cap == 0 || target_cap > 1024`, stampa `RESERVE NOOP (cap=<cap>)` se `target_cap <= cap`, altrimenti ridimensiona a `target_cap`) e `STAT`, producendo l'output esatto dell'esempio.

**Concetti da tenere a mente**

- verifica della soglia di fattore di carico `0.75` in aritmetica intera (`(len + 1) * 4 > cap * 3`)
- ridimensionamento spostando i nodi esistenti tramite l'hash memorizzato nel nodo senza nuove allocazioni
- aggiornamento di una chiave esistente senza attivare un ridimensionamento inutile
- integrità della tabella quando una richiesta di ridimensionamento è rifiutata o fallisce

**Domande guida**

1. Perché in `tab_put` devi verificare se `chiave` è già presente prima di controllare la soglia `(t->len + 1) * 4 > t->cap * 3`?
2. Come dimostra il contatore `nodi_allocati` che `tab_ridimensiona` sposta i nodi esistenti senza riallocarli?
3. Quale vantaggio pratico offre salvare `uint64_t hash` dentro ogni `nodo_cfg_t` sia in `tab_ridimensiona` sia in `tab_cerca`?
4. Che cosa accade alla tabella quando il comando `RESERVE` riceve un valore fuori limite come `0` oppure `5000`?

**Esempio di esecuzione**

```input
2
PUT host 80
PUT port 443
PUT port 8443
PUT mode 1
PUT debug 0
STAT
GET port
DEL mode
RESERVE 2000
RESERVE 16
STAT
```

```output
INS host=80
REHASH 2 -> 4 (spostati=1)
INS port=443
UPD port=8443
INS mode=1
REHASH 4 -> 8 (spostati=3)
INS debug=0
STAT len=4 cap=8 carico=0.50 max_catena=1 rehash=2 alloc_nodi=4
GET port: 8443
DEL mode: OK
RESERVE RIFIUTATO
REHASH 8 -> 16 (spostati=3)
STAT len=3 cap=16 carico=0.19 max_catena=1 rehash=3 alloc_nodi=4
```

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
    ht_imposta(&citta, "RM", &pop[0]); ht_imposta(&citta, "MI", &pop[1]); ht_imposta(&citta, "TO", &pop[2]);
    ht_visita(&citta, conta_grandi, &grandi);
    printf("MI=%d, citta >= 1M: %zu\n", *(int *)ht_cerca(&citta, "MI"), grandi);
    coord_t p1 = {2, 5}, p2 = {-1, 3}, q = {2, 5};
    ht_imposta(&mappa, &p1, "Porto"); ht_imposta(&mappa, &p2, "Parco");
    printf("Zona (2,5): %s\n", (const char *)ht_cerca(&mappa, &q));
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

## 18.5 Regole di possesso della memoria nella tabella hash

Nella sotto-sezione 18.4 la tabella hash generica non liberava né le chiavi né i valori, perché vivevano tutti nello stack di `main`. Nei programmi reali, però, chiavi e valori sono quasi sempre allocati dinamicamente sullo heap — spesso strutture con stringhe o buffer annidati — e possono avere cicli di vita diversi. Riprendendo il concetto di **possesso della memoria** introdotto nel capitolo 17, una tabella hash generica matura deve esprimere con precisione chirurgica chi è responsabile di liberare ciascun blocco.

### Due distruttori indipendenti: possesso separato di chiavi e valori

In una tabella hash le chiavi e i valori non condividono necessariamente lo stesso proprietario. Pensa a questi quattro casi reali:

| `distruggi_chiave` | `distruggi_valore` | Significato |
|---|---|---|
| non nullo | non nullo | La tabella possiede sia le chiavi sia i valori (archivio proprietario) |
| non nullo | `nullptr` | Possesso misto: la tabella possiede le chiavi, ma prende in prestito i valori (es. un indice secondario di alias) |
| `nullptr` | non nullo | Chiavi statiche o condivise (es. letterali stringa), valori posseduti dalla tabella |
| `nullptr` | `nullptr` | Vista completamente in prestito: la tabella possiede solo i propri nodi e l'array `secchi` |

Per supportare tutte e quattro le combinazioni con un'unica struttura, si passa al costruttore `ht_crea` una coppia di callback indipendenti di tipo `typedef void (*distruggi_fn)(void *ptr);`: `distruggi_chiave` e `distruggi_valore`. Quando una callback vale `nullptr`, la tabella opera in modalità prestito su quella componente e non la libera mai.

### Contratti di ciclo di vita per ogni operazione

Una volta introdotti i due distruttori, ogni funzione della tabella deve rispettare un contratto senza ambiguità:

1. **Fallimento di inserimento**: se `ht_inserisci` fallisce per memoria esaurita (nel ridimensionamento o nell'allocazione del nodo) e restituisce `-1`, la tabella **non** acquisisce il possesso né di `chiave` né di `valore` e non chiama alcun distruttore. Il chiamante sa con certezza di doverli liberare lui stesso, evitando sia perdite di memoria sia doppie liberazioni.
2. **Aggiornamento di una chiave già presente**: se `chiave` è già in tabella, il nodo esistente viene aggiornato con il nuovo `valore`. Qui ci sono due risorse da gestire:
   - il vecchio `curr->valore` va liberato se `t->distruggi_valore != nullptr` **e** `curr->valore != valore` (la seconda guardia protegge l'auto-aggiornamento: se il chiamante reinserisce lo stesso puntatore a valore, liberarlo prima di riassegnarlo produrrebbe uso dopo la liberazione);
   - la `chiave` appena passata è ridondante perché il nodo conserva già `curr->chiave`, quindi va liberata se `t->distruggi_chiave != nullptr` **e** `curr->chiave != chiave`.
3. **Rimozione distruttiva ed estrazione (`ht_estrai`)**: a volte vuoi togliere una voce dalla tabella *senza* distruggere il valore, per prenderne nuovamente il possesso nel chiamante. La funzione `ht_estrai(tab_ht_t *t, const void *chiave, void **val_out)` scollega il nodo, libera la chiave se `distruggi_chiave != nullptr`, e poi: se `val_out != nullptr`, scrive il puntatore del valore in `*val_out` trasferendone il possesso al chiamante; altrimenti, se `val_out == nullptr`, chiama `distruggi_valore` (se non nullo). In questo modo `ht_rimuovi(t, chiave)` si riduce a una sola riga: `return ht_estrai(t, chiave, nullptr);`.
4. **Distruzione della tabella (`ht_distruggi`)**: per ogni nodo di ogni secchio salva `prossimo = curr->prox`, chiama `distruggi_chiave(curr->chiave)` se non nullo, chiama `distruggi_valore(curr->valore)` se non nullo, libera `curr`, e infine libera `t->secchi` e `t`.

### Tabelle con possesso misto e ordine di distruzione

Un caso particolarmente istruttivo è l'accoppiamento di una tabella principale proprietaria (`tab_prop`, con `distruggi_chiave` e `distruggi_valore` entrambi non nulli) con una tabella secondaria di alias (`tab_alias`, proprietaria delle proprie chiavi alias ma con `distruggi_valore = nullptr`, quindi in prestito sui valori di `tab_prop`).

Questa architettura richiede due discipline ferree:

- Ogni volta che `tab_prop` sostituisce, rimuove o estrae una risorsa, gli eventuali alias in `tab_alias` che puntavano a quel vecchio puntatore vanno rimossi **prima** (o comunque prima di qualunque accesso a `tab_alias`), altrimenti `tab_alias` conserverebbe puntatori pendenti verso memoria già liberata.
- Alla chiusura del programma, `tab_alias` (la tabella in prestito) deve essere distrutta **prima** di `tab_prop` (la tabella proprietaria).

### Immutabilità delle chiavi e ponte verso il capitolo 19

Esiste un'ultima regola aurea: **non modificare mai una chiave mentre è inserita in una tabella hash**. Se alteri il contenuto di una chiave (per esempio un carattere della stringa o un campo della `struct`), il suo valore di `hash_fn` cambia, ma il nodo resta fisicamente fermo nel vecchio secchio. Le ricerche e le rimozioni successive cercheranno nel nuovo secchio, non troveranno il nodo e lo lasceranno irraggiungibile fino alla distruzione della tabella. Se devi cambiare una chiave, estrai prima il valore con `ht_estrai`, modifica la chiave e reinserisci la coppia.

Fin qui hai dichiarato `struct nodo_ht` e `struct tab_ht` nello stesso file di `main`, quindi il chiamante potrebbe ancora leggere o alterare direttamente `t->secchi` o `t->len`. Nel prossimo capitolo vedrai come spostare l'implementazione in un file `.c` separato e nascondere i campi interni in una libreria su più file (lo vedremo nel capitolo 19).

Riassumiamo la regola precisa:

- Il possesso di chiavi e valori in una tabella hash generica si esprime con due callback distruttore indipendenti `distruggi_chiave` e `distruggi_valore` (ciascuna `nullptr` per la modalità prestito).
- Se un inserimento fallisce per memoria esaurita, la tabella non acquisisce il possesso e lascia al chiamante la responsabilità di liberare chiave e valore. Su aggiornamento di una chiave esistente occorre liberare il vecchio valore (solo se `distruggi_valore != nullptr` e `vecchio != nuovo`) e la chiave ridondante (solo se `distruggi_chiave != nullptr` e `nuova_chiave != nodo->chiave`).
- Non si deve mai modificare una chiave mentre è inserita nella tabella, perché cambiarne l'hash la rende irraggiungibile.

Secondo lo standard C23, il rilascio controllato tramite `distruggi_chiave` e `distruggi_valore` è definito; al contrario, liberare lo stesso oggetto sia nel chiamante sia nella tabella (o su auto-aggiornamento) provoca **doppia liberazione** (**comportamento indefinito**), mentre distruggere una tabella proprietaria prima di una tabella in prestito lascia **puntatori pendenti**.

### Esempio guidato

Il programma seguente mostra una tabella hash generica con distruttori configurabili. `archivio` possiede sia le chiavi stringa (`free`) sia i record dinamici (`distruggi_item`), mentre `indice` è una tabella secondaria in prestito (`distruggi_valore = nullptr`). I contatori `creati` e `distrutti` confermano che aggiornamento, estrazione, rimozione e distruzione ordinata liberano ogni record esattamente una volta.

<!-- cod: id=18.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint64_t (*hash_fn)(const void *);
typedef bool (*uguali_fn)(const void *, const void *);
typedef void (*distruggi_fn)(void *);
typedef struct nodo { void *k; void *v; uint64_t h; struct nodo *prox; } nodo_t;
typedef struct { nodo_t **sec; size_t cap, len; hash_fn hf; uguali_fn eq; distruggi_fn dk, dv; } tab_ht_t;
typedef struct { char *nome; int peso; size_t *cont_dis; } item_t;

tab_ht_t *ht_crea(size_t cap, hash_fn hf, uguali_fn eq, distruggi_fn dk, distruggi_fn dv) {
    tab_ht_t *t = malloc(sizeof(*t));
    if (t == nullptr) { return nullptr; }
    t->sec = malloc(cap * sizeof(*t->sec));
    if (t->sec == nullptr) { free(t); return nullptr; }
    for (size_t i = 0; i < cap; ++i) { t->sec[i] = nullptr; }
    t->cap = cap; t->len = 0; t->hf = hf; t->eq = eq; t->dk = dk; t->dv = dv;
    return t;
}

int ht_inserisci(tab_ht_t *t, void *k, void *v) {
    uint64_t h = t->hf(k); size_t idx = (size_t)(h % t->cap);
    for (nodo_t *c = t->sec[idx]; c != nullptr; c = c->prox) {
        if (c->h == h && t->eq(c->k, k)) {
            if (t->dv != nullptr && c->v != v) { t->dv(c->v); }
            c->v = v;
            if (t->dk != nullptr && c->k != k) { t->dk(k); }
            return 0;
        }
    }
    nodo_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return -1; }
    *n = (nodo_t){.k = k, .v = v, .h = h, .prox = t->sec[idx]};
    t->sec[idx] = n; ++t->len; return 1;
}

bool ht_estrai(tab_ht_t *t, const void *k, void **val_out) {
    uint64_t h = t->hf(k); size_t idx = (size_t)(h % t->cap);
    nodo_t **cur = &t->sec[idx];
    while (*cur != nullptr && ((*cur)->h != h || !t->eq((*cur)->k, k))) { cur = &(*cur)->prox; }
    if (*cur == nullptr) { return false; }
    nodo_t *d = *cur; *cur = d->prox;
    if (t->dk != nullptr) { t->dk(d->k); }
    if (val_out != nullptr) { *val_out = d->v; }
    else if (t->dv != nullptr) { t->dv(d->v); }
    free(d); --t->len; return true;
}

void ht_distruggi(tab_ht_t *t) {
    if (t == nullptr) { return; }
    for (size_t i = 0; i < t->cap; ++i) {
        for (nodo_t *c = t->sec[i]; c != nullptr; ) {
            nodo_t *p = c->prox;
            if (t->dk != nullptr) { t->dk(c->k); }
            if (t->dv != nullptr) { t->dv(c->v); }
            free(c); c = p;
        }
    }
    free(t->sec); free(t);
}

uint64_t h_str(const void *p) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *s = p; *s != '\0'; ++s) { h ^= *s; h *= 1099511628211ULL; }
    return h;
}
bool eq_str(const void *a, const void *b) { return strcmp(a, b) == 0; }
void dis_item(void *p) { item_t *it = p; ++(*it->cont_dis); free(it->nome); free(it); }
item_t *crea_item(const char *s, int w, size_t *cre, size_t *dis) {
    item_t *it = malloc(sizeof(*it)); it->nome = strdup(s); it->peso = w; it->cont_dis = dis; ++(*cre); return it;
}

int main(void) {
    size_t cre = 0, dis = 0;
    tab_ht_t *arch = ht_crea(8, h_str, eq_str, free, dis_item), *ind = ht_crea(8, h_str, eq_str, free, nullptr);
    item_t *a = crea_item("SensoreA", 12, &cre, &dis), *b = crea_item("MotoreB", 40, &cre, &dis);
    ht_inserisci(arch, strdup("k1"), a); ht_inserisci(arch, strdup("k2"), b); ht_inserisci(ind, strdup("alias_b"), b);
    ht_inserisci(arch, strdup("k1"), crea_item("SensoreA2", 15, &cre, &dis));
    void *estr = nullptr;
    if (ht_estrai(arch, "k2", &estr)) {
        ht_estrai(ind, "alias_b", nullptr);
        printf("Estratto: %s (%d)\n", ((item_t *)estr)->nome, ((item_t *)estr)->peso);
        dis_item(estr);
    }
    ht_distruggi(ind); ht_distruggi(arch);
    printf("Bilancio item: creati=%zu distrutti=%zu\n", cre, dis);
    return 0;
}
```

```output
Estratto: MotoreB (40)
Bilancio item: creati=3 distrutti=3
```

Osserva come ogni passaggio mantiene il bilancio esatto:

- `arch` riceve `free` come `dk` (perché le chiavi sono stringhe allocate con `strdup`) e `dis_item` come `dv`. `ind` riceve `free` per le proprie chiavi alias ma `nullptr` per i valori, che prende in prestito da `arch`.
- Quando `k1` viene aggiornata con `SensoreA2`, `ht_inserisci` chiama `dis_item` sul vecchio `SensoreA` e `free` sulla nuova chiave `"k1"` ridondante.
- Con `ht_estrai(arch, "k2", &estr)`, la tabella libera la chiave `"k2"` e il nodo, ma **non** distrugge `MotoreB`: ne restituisce il puntatore in `estr`. Prima di liberare `estr` con `dis_item(estr)`, rimuoviamo `"alias_b"` da `ind` per non lasciare puntatori pendenti.
- Alla fine `ht_distruggi(ind)` viene chiamata prima di `ht_distruggi(arch)` e il bilancio finale conferma `creati=3 distrutti=3`.

> **Approfondimento — Perché una chiave in tabella deve restare immutabile**
> Supponi di inserire una chiave stringa `"alfa"` in una tabella hash: l'hash la colloca nel secchio `3`. Se poi il chiamante conserva un puntatore a quella stessa stringa e ne modifica il contenuto in `"beta"`, l'hash di `"beta"` corrisponderà a un secchio diverso (per esempio `6`), mentre il nodo resterà intrappolato nel secchio `3` con il vecchio valore `nodo->hash`. Da quel momento `ht_cerca(t, "beta")` cercherà nel secchio `6` senza trovarla, e `ht_cerca(t, "alfa")` cercherà nel secchio `3` ma fallirà il confronto `uguali`. Per evitare questo errore difficile da diagnosticare, una chiave non va mai modificata finché risiede nella tabella.

### Esercizio 18.5 — Tabella hash generica con possesso configurabile, indice di alias in prestito ed estrazione del possesso

**Descrizione**

Scrivi un programma C che estenda la tabella hash generica con regole di possesso configurabili tramite due callback distruttore indipendenti: `distruggi_chiave` e `distruggi_valore` (`typedef void (*distruggi_fn)(void *ptr);`, ciascuna `nullptr` in modalità prestito). Implementa:

- `tab_ht_t *ht_crea(size_t cap, hash_fn h, uguali_fn u, distruggi_fn d_chiave, distruggi_fn d_valore)`
- `int ht_inserisci(tab_ht_t *t, void *chiave, void *valore)` (su chiave esistente libera `curr->valore` se `d_valore != nullptr && curr->valore != valore`, aggiorna il valore, libera `chiave` se `d_chiave != nullptr && curr->chiave != chiave` e restituisce `0`; su chiave nuova ridimensiona se `(len + 1) * 4 > cap * 3`, inserisce e restituisce `1`; su fallimento di allocazione NON libera né `chiave` né `valore` e restituisce `-1`)
- `void *ht_cerca(const tab_ht_t *t, const void *chiave)`
- `bool ht_estrai(tab_ht_t *t, const void *chiave, void **val_out)` (scollega il nodo, libera la chiave se `d_chiave != nullptr`, e se `val_out != nullptr` trasferisce il valore in `*val_out` senza distruggerlo, altrimenti chiama `d_valore`)
- `bool ht_rimuovi(tab_ht_t *t, const void *chiave)` (chiama `ht_estrai(t, chiave, nullptr)`)
- `size_t ht_rimuovi_per_valore(tab_ht_t *t, const void *valore)` (rimuove tutte le voci che puntano a `valore`)
- `void ht_distruggi(tab_ht_t *t)`

Modella chiavi tracciate `typedef struct chiave_str { char *testo; size_t *cont_dist; } chiave_str_t;` e risorse annidate `typedef struct risorsa { char *etichetta; int32_t punteggio; size_t *cont_dist; } risorsa_t;` (senza variabili globali: i distruttori incrementano `*cont_dist` prima di liberare `testo`/`etichetta` e la struct).

In `main` crea due tabelle: `tab_prop` proprietaria di chiavi e valori (`distruggi_kstr`, `distruggi_risorsa`) e `tab_alias` con possesso misto (proprietaria delle chiavi `distruggi_kstr`, valori in prestito `nullptr`). Leggi da `stdin` i comandi `PUT <chiave> <etichetta> <punteggio>` (su aggiornamento rimuove prima da `tab_alias` eventuali alias del vecchio valore per non lasciare puntatori pendenti), `ALIAS <alias> <chiave>`, `GET <chiave>`, `GET_ALIAS <alias>`, `DEL <chiave>`, `EXTRACT <chiave>` (estrae la risorsa da `tab_prop`, pulisce eventuali alias, la stampa e la libera esplicitamente nel chiamante) e `BILANCIO`. Prima di uscire distruggi `tab_alias` PRIMA di `tab_prop` e stampa il bilancio finale di chiavi e valori creati/distrutti.

**Concetti da tenere a mente**

- callback distruttore indipendenti `distruggi_chiave` e `distruggi_valore` (possesso vs prestito)
- gestione sicura dell'aggiornamento su chiave duplicata senza perdite di memoria né doppie liberazioni
- estrazione con trasferimento di possesso al chiamante (`ht_estrai`) rispetto alla rimozione distruttiva
- coerenza tra tabella proprietaria e tabella di alias in prestito (pulizia degli alias e ordine di distruzione)

**Domande guida**

1. Perché `tab_alias` usa `distruggi_kstr` come `distruggi_chiave` ma `nullptr` come `distruggi_valore`?
2. Che cosa succederebbe se durante `PUT` su una chiave già presente in `tab_prop` non rimuovessi prima da `tab_alias` gli alias che puntavano alla vecchia risorsa?
3. In che modo `ht_estrai` differisce da `ht_rimuovi` rispetto al possesso della chiave e del valore?
4. Perché nel controllo di aggiornamento dentro `ht_inserisci` conviene verificare `curr->valore != valore` e `curr->chiave != chiave` prima di chiamare i distruttori?

**Esempio di esecuzione**

```input
PUT srv1 WebApp 90
PUT srv2 Database 80
ALIAS main srv1
ALIAS prod srv1
GET_ALIAS main
PUT srv1 WebAppV2 95
GET_ALIAS main
ALIAS prod srv2
EXTRACT srv2
GET_ALIAS prod
BILANCIO
DEL srv1
```

```output
PUT srv1: INSERITO
PUT srv2: INSERITO
ALIAS main -> srv1: INSERITO
ALIAS prod -> srv1: INSERITO
GET_ALIAS main: WebApp (90)
PUT srv1: AGGIORNATO (alias_invalidati=2)
GET_ALIAS main: NON TROVATO
ALIAS prod -> srv2: INSERITO
EXTRACT srv2: Database (80) (alias_invalidati=1)
GET_ALIAS prod: NON TROVATO
BILANCIO chiavi=6/5 valori=3/2
DEL srv1: OK (alias_invalidati=0)
FINE chiavi=6/6 valori=3/3
```

## Riepilogo

- Una **tabella hash** mappa chiavi a valori in tempo medio costante applicando una **funzione di hash** deterministica che produce un intero senza segno (`uint64_t` o `size_t`), ridotto poi all'indice del secchio con `h % num_secchi`. Nel calcolo sui byte di una stringa o di un buffer si converte sempre a `unsigned char` e si usa aritmetica senza segno (FNV-1a, djb2, mescolamento di bit per interi).
- Le **collisioni** sono inevitabili per il principio dei cassetti: la tabella deve conservare la chiave originale e verificarne l'uguaglianza. Nel concatenamento l'array dei secchi ha tipo `nodo_t **secchi` (allocato e inizializzato esplicitamente a `nullptr`), ciascun secchio è la testa di una lista semplicemente concatenata, la rimozione usa un puntatore a puntatore `nodo_t **cur = &t->secchi[idx]` e la distruzione salva `curr->prox` prima di liberare chiave e nodo.
- Il **fattore di carico** `alpha = (double)len / (double)cap` misura la lunghezza media delle catene. Al superamento della soglia (es. `0.75`, verificata in aritmetica intera con `(len + 1) * 4 > cap * 3`), il **ridimensionamento** alloca un nuovo array di secchi (previo controllo `nuova_cap <= SIZE_MAX / sizeof(nodo_t *)`), sposta i nodi esistenti riusando `nodo->hash % nuova_cap` senza riallocarli e lascia la tabella originale intatta se `malloc` fallisce.
- Una tabella hash generica su `void *` è parametrizzata dalle callback `hash_fn`, `uguali_fn` e `visita_fn` (con contesto `void *ctx`). Le prime due devono soddisfare l'invariante `uguali(a, b) => hash(a) == hash(b)`: per le chiavi `struct` l'hash va sempre calcolato combinando i singoli campi, mai sui byte grezzi della `struct` a causa del padding.
- Il possesso di chiavi e valori si controlla con due callback distruttore indipendenti `distruggi_chiave` e `distruggi_valore` (`nullptr` per la modalità prestito). Le operazioni proteggono l'auto-aggiornamento, lasciano il possesso al chiamante se l'inserimento fallisce, offrono `ht_estrai` per trasferire il possesso del valore e vietano di modificare una chiave già inserita. Nel prossimo capitolo incapsuleremo questa tabella hash nascondendone la struttura interna in una libreria su più file (lo vedremo nel capitolo 19).

## Errori comuni

- **Usare `char` direttamente o interi con segno nel calcolo di una funzione di hash**: il segno di `char` è dipendente dall'implementazione e produce hash diversi tra piattaforme sui byte con bit alto a `1`, mentre l'overflow su interi con segno causa comportamento indefinito. Usa sempre `const unsigned char *` e `uint64_t`.
- **Calcolare l'hash di una `struct` sui suoi `sizeof(*s)` byte grezzi**: i byte di padding non inizializzati possono differire tra due chiavi logicamente uguali, violando l'invariante `uguali(a, b) => hash(a) == hash(b)` e rendendo irreperibili chiavi già presenti. Combina esplicitamente i singoli campi.
- **Sovrascrivere o liberare `t->secchi` durante il ridimensionamento prima di verificare che il nuovo array sia diverso da `nullptr`**, oppure dimenticare di ricalcolare `idx = (size_t)(h % t->cap)` dopo il ridimensionamento: nel primo caso si perde memoria o si dereferenzia un puntatore nullo in caso di fallimento di `malloc`; nel secondo si inserisce il nuovo nodo nel secchio sbagliato.
- **Dimenticare di liberare il vecchio valore o la chiave ridondante su aggiornamento**, oppure non proteggere l'auto-aggiornamento (`curr->valore != valore` e `curr->chiave != chiave`): nel primo caso si genera una perdita di memoria, nel secondo una doppia liberazione o un uso dopo la liberazione.
- **Modificare una chiave dopo averla inserita nella tabella hash**: cambiarne il contenuto ne altera l'hash lasciando il nodo nel vecchio secchio, rendendolo irraggiungibile nelle ricerche e nelle rimozioni successive.

## Prima di proseguire

- [ ] So scrivere una funzione di hash deterministica in C23 (come FNV-1a o mescolamento a 64 bit) usando `unsigned char` e `uint64_t`, e spiegare perché le collisioni sono inevitabili.
- [ ] So implementare una tabella hash con concatenamento (`nodo_t **secchi`), aggiornamento su chiave duplicata, rimozione con puntatore a puntatore e distruzione senza perdite di memoria.
- [ ] So verificare il fattore di carico in aritmetica intera ed eseguire il ridimensionamento spostando i nodi esistenti tramite l'hash memorizzato senza riallocarli.
- [ ] So progettare una tabella hash generica su `void *` con callback `hash_fn`, `uguali_fn` e `visita_fn`, scrivendo hash campo per campo per chiavi `struct` con padding.
- [ ] So configurare il possesso separato di chiavi e valori tramite `distruggi_chiave` e `distruggi_valore`, gestire estrazioni (`ht_estrai`) e mantenere coerenti tabelle proprietarie e viste in prestito.
