# Capitolo 22 — Gestione avanzata della memoria

> **In questo capitolo imparerai a:**
> - Allineare buffer statici e blocchi allocati con `alignas`, `alignof` e `max_align_t`
> - Implementare da zero un allocatore ad arena, un allocatore a pool e un allocatore con lista libera (anche con campo array flessibile) garantendo allineamento corretto
> - Ridurre frammentazione e numero di chiamate a `malloc` scegliendo l'allocatore adatto al ciclo di vita dei dati
> - Spiegare le regole di strict aliasing e di `restrict` e diagnosticare corruzioni della memoria

> **Ti servono:** memoria dinamica (capitolo 11), rappresentazione a basso livello, allineamento e padding (capitolo 13), puntatori avanzati e `restrict` (capitolo 14), `void *` e `memcpy`/`memset` (capitolo 15), moduli su più file e tipi opachi (capitolo 19), aritmetica controllata e diagnostica (capitolo 21).

Nel capitolo 21 hai imparato a rendere il codice robusto propagando gli errori, verificando gli invarianti e prevenendo il comportamento indefinito con strumenti come i sanitizer e il debugger. Ora hai a disposizione tutti gli elementi per scendere ancora più in profondità e prendere il controllo diretto di come il programma acquisisce, organizza e rilascia la memoria.

Le funzioni `malloc`, `calloc`, `realloc` e `free` sono strumenti generici: devono funzionare bene in qualunque scenario, per blocchi grandi o piccoli, liberati in qualsiasi ordine. Questa flessibilità ha però un prezzo. Quando un programma crea migliaia di piccoli oggetti con la stessa durata di vita — come i nodi di un albero di sintassi o i record temporanei di un'elaborazione — oppure alloca e libera di continuo strutture tutte della stessa dimensione, chiamare `malloc` e `free` per ogni singolo elemento introduce sovraccarico amministrativo, frammentazione e maggiori rischi di perdite di memoria.

In questo capitolo imparerai a progettare allocatori specializzati partendo da zero: dall'allineamento rigoroso con `alignas` e `max_align_t`, fino all'allocatore ad arena, all'allocatore a pool e all'allocatore con lista libera abbinato al campo array flessibile. Infine studierai le regole dello standard C23 sul tipo effettivo, sullo strict aliasing e su `restrict`, e costruirai tecniche difensive come canarini di confine e avvelenamento dei byte per diagnosticare le corruzioni della memoria prima che diventino errori silenziosi.

## 22.1 Allineamento in pratica con `alignas` e `max_align_t`

Nel capitolo 13 hai incontrato i concetti di **allineamento** e **padding** e hai usato l'operatore `alignof` per interrogare il requisito di allineamento di un tipo. Fino a questo punto, però, ti sei limitato a *osservare* le scelte del compilatore: potevi riordinare i campi di una `struct` per sprecare meno byte, ma non avevi ancora uno strumento per *imporre* un allineamento specifico a una variabile, a un campo o a un buffer di memoria grezza.

Quando costruisci un allocatore personalizzato, questa possibilità diventa indispensabile. Immagina di riservare un buffer statico di byte da cui distribuire in seguito variabili `int64_t`, `double` o intere `struct`. Se dichiari semplicemente `static unsigned char buffer[1024];`, il tipo `unsigned char` ha allineamento `1`: il compilatore è perfettamente libero di collocare `buffer` a un indirizzo dispari, come `0x1001`. Se il tuo allocatore consegnasse quell'indirizzo iniziale per memorizzarvi un `double` (che su molte piattaforme richiede un indirizzo multiplo di 8), violeresti il vincolo di allineamento.

Per imporre un allineamento esplicito il C23 mette a disposizione lo specificatore `alignas`. Puoi passargli un tipo (`alignas(double)`) oppure un'espressione intera costante positiva che sia una potenza di due (`alignas(16)`, `alignas(64)`). La sua regola è precisa:

- `alignas` rafforza il requisito di allineamento di un oggetto o di un campo di `struct`, ma **non può mai ridurlo** al di sotto dell'allineamento naturale del tipo (per esempio scrivere `alignas(1) double x;` è un errore di compilazione).
- `alignas` può essere applicato a variabili e a campi di `struct` o `union`, ma **non** a `typedef`, parametri di funzione o campi di bit.
- Un allineamento richiesto da `alignas` uguale a `0` viene ignorato.

> **C23** — In C23 `alignas` e `alignof` sono parole chiave native del linguaggio e non richiedono alcun header. Nei compilatori più vecchi (C11/C17) si usavano le parole chiave `_Alignas` e `_Alignof`, oppure le macro `alignas` e `alignof` definite nell'header `<stdalign.h>`, che in C23 è superato e non va incluso.

Ma quale allineamento devi scegliere se il tuo buffer deve poter ospitare *qualsiasi* tipo standard del C, senza sapere in anticipo quale? Qui entra in gioco `max_align_t`, un tipo definito in `<stddef.h>`. Il suo requisito di allineamento, espresso da `alignof(max_align_t)`, rappresenta il **più grande allineamento fondamentale** supportato dalla piattaforma (spesso 8 o 16 byte sulle architetture moderne). È un riferimento analogo alla garanzia offerta da `malloc`, `calloc` e `realloc`: ogni blocco restituito da queste funzioni è opportunamente allineato per qualunque oggetto con allineamento fondamentale la cui dimensione non superi quella richiesta (in particolare, per richieste di almeno `sizeof(max_align_t)` byte è allineato almeno ad `alignof(max_align_t)`).

Dichiarare un buffer statico in questo modo:

<!-- cod: id=22.1-b tipo=frammento -->
```c
static alignas(max_align_t) unsigned char buffer[1024];
```

garantisce che il primo byte di `buffer` si trovi sempre a un indirizzo multiplo di `alignof(max_align_t)`. Secondo lo standard C23, `alignas`, `alignof` e `max_align_t` sono definiti dal linguaggio; tuttavia il valore numerico esatto di `alignof(max_align_t)` e gli eventuali allineamenti estesi superiori ad esso (come `alignas(64)`) costituiscono un **comportamento dipendente dall'implementazione**. Al contrario, dereferenziare un puntatore che non rispetta l'allineamento richiesto dal tipo puntato provoca **comportamento indefinito**.

Una volta allineata la base del buffer, ogni allocatore ha bisogno di un'operazione fondamentale: **arrotondare una dimensione `n` al multiplo superiore** di un allineamento `A` (potenza di due). Nella pratica si vede spesso la formula bit a bit `(n + (A - 1)) & ~(A - 1)`, che funziona perché, quando `A` è una potenza di due, `A - 1` ha tutti i bit bassi a `1` e `~(A - 1)` azzera proprio il resto della divisione per `A`.

Questa formula, però, nasconde due trappole se usata senza difese:

1. Se `A` vale `0` o non è una potenza di due (per esempio `6`), la maschera `~(A - 1)` produce risultati privi di senso. Per verificare che `A` sia una potenza di due non nulla si controlla `A != 0 && (A & (A - 1)) == 0`.
2. Se `n` è molto vicino a `SIZE_MAX`, la somma `n + (A - 1)` va in **wrap-around** (overflow senza segno) e restituisce un numero piccolo vicino a `0`, portando ad allocare un buffer minuscolo al posto di uno enorme.

Per rendere l'arrotondamento davvero sicuro, combiniamo la verifica della potenza di due con la macro C23 `ckd_add` di `<stdckdint.h>` vista nel capitolo 21:

<!-- cod: id=22.1-c tipo=frammento -->
```c
bool arrotonda_allineamento(size_t n, size_t allin, size_t *out) {
    if (allin == 0 || (allin & (allin - 1)) != 0 || out == nullptr) {
        return false;
    }
    size_t somma = 0;
    if (ckd_add(&somma, n, allin - 1)) {
        return false;
    }
    *out = somma & ~(allin - 1);
    return true;
}
```

Per verificare a tempo di esecuzione se un puntatore `p` rispetta un allineamento `allin` (potenza di due), non si può applicare l'operatore `%` o `&` direttamente a `void *`: occorre convertire il puntatore al tipo intero senza segno `uintptr_t` (`<stdint.h>`, capitolo 13) e controllare che `((uintptr_t)p & (uintptr_t)(allin - 1)) == 0`.

Infine, ricorda una conseguenza importante dell'allineamento sugli array di `struct`. In un array contiguo `T arr[N]`, l'elemento `arr[1]` inizia esattamente `sizeof(T)` byte dopo `arr[0]`. Affinché *ogni* elemento dell'array rispetti l'allineamento `alignof(T)`, il compilatore garantisce che `sizeof(T)` sia sempre un **multiplo di `alignof(T)`**, aggiungendo se necessario byte di **padding** in coda alla `struct`. Per esempio, se applichi `alignas(64)` a una `struct` i cui campi occupano solo 8 byte, la sua dimensione sale a 64 byte: una tecnica usata spesso per far sì che due strutture occupino **linee di cache** distinte del processore (approfondiremo il ruolo della cache nel capitolo 25).

```text
Array di struct con alignas(64):
offset:  0       8                              64      72
        +-------+------------------------------+-------+------------------------------+
        | dati  |      padding (56 byte)       | dati  |      padding (56 byte)       |
        +-------+------------------------------+-------+------------------------------+
        ^ arr[0] (multiplo di 64)              ^ arr[1] (multiplo di 64)
```

### Esempio guidato

Il programma seguente dichiara un buffer statico allineato con `alignas(max_align_t)` e una struttura `contatore_cache_t` allineata a 64 byte con `alignas(64)`. Verifica con `uintptr_t` che il buffer e ogni elemento di un array di tre `contatore_cache_t` rispettino il proprio allineamento, poi mette alla prova la funzione `arrotonda_su` su casi regolari, su un allineamento non potenza di due e su un valore prossimo a `SIZE_MAX`.

<!-- cod: id=22.1-a tipo=programma -->
```c
#include <stdckdint.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct contatore_cache {
    alignas(64) uint32_t valore;
    uint32_t stato;
} contatore_cache_t;

static alignas(max_align_t) unsigned char deposito[64];
static contatore_cache_t contatori[3];

static bool potenza_di_due(size_t a) {
    return a != 0 && (a & (a - 1)) == 0;
}

static bool arrotonda_su(size_t n, size_t allin, size_t *out) {
    if (!potenza_di_due(allin) || out == nullptr) {
        return false;
    }
    size_t somma = 0;
    if (ckd_add(&somma, n, allin - 1)) {
        return false;
    }
    *out = somma & ~(allin - 1);
    return true;
}

static bool e_allineato(const void *p, size_t allin) {
    if (p == nullptr || !potenza_di_due(allin)) {
        return false;
    }
    return ((uintptr_t)p & (uintptr_t)(allin - 1)) == 0;
}

int main(void) {
    bool dep_ok = e_allineato(deposito, alignof(max_align_t));
    bool arr_ok = true;
    for (size_t i = 0; i < 3; ++i) {
        if (!e_allineato(&contatori[i], 64)) {
            arr_ok = false;
        }
    }
    printf("deposito allineato a max_align_t: %d\n", dep_ok ? 1 : 0);
    printf("contatore_cache_t: alignof=%zu sizeof=%zu array_ok=%d\n",
           alignof(contatore_cache_t), sizeof(contatore_cache_t), arr_ok ? 1 : 0);

    size_t test_n[] = {0, 19, 32, 10, SIZE_MAX - 3};
    size_t test_a[] = {16, 8, 16, 6, 16};
    for (size_t i = 0; i < 5; ++i) {
        size_t ris = 0;
        if (arrotonda_su(test_n[i], test_a[i], &ris)) {
            printf("caso %zu (allin=%zu): %zu\n", i, test_a[i], ris);
        } else {
            printf("caso %zu (allin=%zu): ERRORE\n", i, test_a[i]);
        }
    }
    return 0;
}
```

```output
deposito allineato a max_align_t: 1
contatore_cache_t: alignof=64 sizeof=64 array_ok=1
caso 0 (allin=16): 0
caso 1 (allin=8): 24
caso 2 (allin=16): 32
caso 3 (allin=6): ERRORE
caso 4 (allin=16): ERRORE
```

Osserva i punti chiave del programma:

- `static alignas(max_align_t) unsigned char deposito[64];` garantisce che l'indirizzo di `deposito` sia divisibile per `alignof(max_align_t)`, come confermato da `e_allineato`. Non stampiamo il valore numerico di `alignof(max_align_t)` perché dipende dall'architettura, ma verifichiamo la proprietà in modo portabile.
- In `contatore_cache_t`, `valore` e `stato` occupano complessivamente solo 8 byte, ma lo specificatore `alignas(64)` impone che la struttura abbia allineamento 64 e quindi dimensione 64 (con 56 byte di padding finale), in modo che tutti gli elementi di `contatori[3]` cadano su indirizzi multipli di 64.
- Nei casi di prova di `arrotonda_su`: `0` resta `0`, `19` sale a `24` (multiplo di 8), `32` resta `32`. Il caso 3 viene rifiutato perché `6` non è una potenza di due, mentre il caso 4 (`SIZE_MAX - 3` con allineamento `16`) viene intercettato da `ckd_add` prima che avvenga il wrap-around.

> **Approfondimento — Perché `unsigned char buf[N]` non basta per un allocatore**
> Un buffer statico di byte per un allocatore personalizzato non può essere dichiarato come semplice `unsigned char buf[N]`: `alignof(unsigned char)` è `1`, quindi il compilatore può collocare `buf` a un indirizzo dispari. Aggiungere `alignas(max_align_t)` garantisce che l'inizio del buffer sia adatto a qualsiasi tipo fondamentale senza sprecare byte di riallineamento iniziale.

### Esercizio 22.1 — Pianificatore di allineamento e layout di struct con `alignas`, `max_align_t` e `ckd_add`

**Descrizione**

Scrivi un programma C che implementi utilità rigorose di allineamento e un simulatore di layout di `struct` in memoria. (1) Implementa `bool e_potenza_di_due(size_t a)`, `bool arrotonda_allineamento(size_t n, size_t allin, size_t *out)` (verifica `e_potenza_di_due(allin)`, usa `ckd_add` di `<stdckdint.h>` per evitare overflow nella somma `n + (allin - 1)` e applica `& ~(allin - 1)`) e `bool puntatore_allineato(const void *p, size_t allin)` (usa `uintptr_t`). (2) Definisci `typedef struct blocco_32 { alignas(32) uint8_t dati[20]; } blocco_32_t;`, un buffer statico `static alignas(max_align_t) unsigned char buf_max[128];` e un array `static blocco_32_t arr_32[3];`. (3) Leggi da `stdin` comandi fino a fine input: `ALIGN <dim> <allin>` stampa `ALIGN(<dim>, <allin>) = <ris>` oppure `ERRORE`; `ALIGN_MAX <allin>` verifica `arrotonda_allineamento(SIZE_MAX, allin, &ris)` stampando `ALIGN(SIZE_MAX, <allin>) = OK` o `ERRORE`; `LAYOUT <k>` (`0 <= k <= 16`) seguito da `k` righe `<dim> <allin>` (`dim > 0`, `allin` potenza di due) calcola l'offset allineato e il padding di ciascun campo, l'allineamento massimo della `struct`, la dimensione totale arrotondata e il padding di coda, stampando esattamente come nell'esempio; `CHECK_STATIC` verifica l'allineamento di `buf_max` rispetto a `alignof(max_align_t)`, che `alignof(blocco_32_t) == 32`, `sizeof(blocco_32_t) == 32` e che tutti gli elementi di `arr_32` siano allineati a 32 byte, stampando `CHECK_STATIC: max_align_ok=1 align32=32 sizeof32=32 array_ok=1`.

**Concetti da tenere a mente**

- verifica che un allineamento sia una potenza di due non nulla: `a != 0 && (a & (a - 1)) == 0`
- arrotondamento sicuro al multiplo superiore con `ckd_add` e maschera `~(allin - 1)`
- uso di `alignas(max_align_t)` e `alignas(32)` su buffer statici e `struct` e verifica tramite `uintptr_t`
- calcolo di offset, padding interno, allineamento complessivo e padding finale di una `struct`

**Domande guida**

1. Perché l'espressione `(a & (a - 1)) == 0` da sola non basta a verificare che `a` sia una potenza di due valida?
2. Che cosa succederebbe nella formula `(n + (allin - 1)) & ~(allin - 1)` se `n` valesse `SIZE_MAX` e `allin` valesse `16` senza un controllo preventivo di overflow?
3. Perché `sizeof(blocco_32_t)` vale `32` anche se il campo `dati` occupa solo `20` byte?
4. Quale differenza c'è tra il padding interno inserito prima di un campo e il padding di coda aggiunto in fondo a una `struct`?

**Esempio di esecuzione**

```input
ALIGN 0 16
ALIGN 13 8
ALIGN 16 16
ALIGN 10 6
ALIGN 10 0
ALIGN_MAX 16
ALIGN_MAX 1
LAYOUT 3
1 1
8 8
1 1
LAYOUT 3
8 8
1 1
1 1
CHECK_STATIC
```

```output
ALIGN(0, 16) = 0
ALIGN(13, 8) = 16
ALIGN(16, 16) = 16
ALIGN(10, 6) = ERRORE
ALIGN(10, 0) = ERRORE
ALIGN(SIZE_MAX, 16) = ERRORE
ALIGN(SIZE_MAX, 1) = OK
  campo 0: offset=0 dim=1 allin=1 pad=0
  campo 1: offset=8 dim=8 allin=8 pad=7
  campo 2: offset=16 dim=1 allin=1 pad=0
LAYOUT(3): dim=24 allin=8 pad_interno=7 pad_coda=7
  campo 0: offset=0 dim=8 allin=8 pad=0
  campo 1: offset=8 dim=1 allin=1 pad=0
  campo 2: offset=9 dim=1 allin=1 pad=0
LAYOUT(3): dim=16 allin=8 pad_interno=0 pad_coda=6
CHECK_STATIC: max_align_ok=1 align32=32 sizeof32=32 array_ok=1
```

## 22.2 L'allocatore ad arena su buffer statico

Quando elabori un testo, costruisci un albero di nodi o analizzi una richiesta di rete, spesso crei decine o migliaia di piccoli oggetti che condividono la stessa **durata di vita**: nascono insieme durante una fase di lavoro e diventano tutti inutili nello stesso istante, appena quella fase termina. Chiamare `malloc` per ogni singolo oggetto e poi scrivere un ciclo di `free` per smontare l'intera struttura ha due svantaggi evidenti: ogni chiamata a `malloc` aggiunge metadati e lavoro di ricerca nell'allocatore di sistema, e basta dimenticare un percorso di errore per introdurre una **perdita di memoria**.

L'idea per eliminare entrambi i problemi è tanto semplice quanto efficace: invece di chiedere mille piccoli blocchi separati, riservi una sola volta una regione di memoria contigua e consegni le fette una dopo l'altra avanzando un semplice indice. Quando tutti gli oggetti non servono più, riporti l'indice a zero in una singola istruzione.

Questo schema si chiama **allocatore ad arena** (*arena allocator*, spesso detto anche *bump allocator*): è un allocatore che assegna memoria avanzando un cursore su un buffer contiguo e libera tutti gli oggetti in un colpo solo.

Per costruire un'arena su un buffer statico, priva di qualunque chiamata a `malloc` e `free`, basta una `struct` con quattro campi:

- `base`: puntatore `unsigned char *` al primo byte del buffer (dichiarato con `alignas(max_align_t)` o un allineamento maggiore);
- `cap`: capacità totale del buffer in byte;
- `usati`: cursore che indica quanti byte sono già stati assegnati dall'inizio del buffer;
- `picco`: valore massimo mai raggiunto da `usati`, utile per dimensionare il buffer in base all'uso reale.

```text
Buffer statico alignas(max_align_t):
+---------+-----+----------------+-----+----------------------+
| obj 1   | pad |     obj 2      | pad |    spazio libero     |
+---------+-----+----------------+-----+----------------------+
^                                      ^                      ^
base                                   base + usati           base + cap
```

Ogni allocazione nell'arena lavora in tempo costante ($O(1)$, notazione che formalizzeremo nel capitolo 23) e segue quattro passaggi precisi:

1. Controlla che `a != nullptr`, `dim > 0` e che l'allineamento richiesto `allin` sia una potenza di due non nulla (nell'allocazione generica `arena_alloca` si usa `alignof(max_align_t)`).
2. Calcola lo spiazzamento di **padding** necessario rispetto all'indirizzo effettivo corrente `curr = (uintptr_t)(a->base + a->usati)`. Il resto rispetto ad `allin` è `resto = (size_t)(curr & (uintptr_t)(allin - 1))`; se `resto != 0`, servono `pad = allin - resto` byte di allineamento, altrimenti `pad = 0`.
3. Verifica l'assenza di overflow e di sforamento della capacità con `ckd_add(&inizio, a->usati, pad)`, `ckd_add(&fine, inizio, dim)` e `fine <= a->cap`. Se uno di questi controlli fallisce, restituisce `nullptr` senza modificare lo stato dell'arena.
4. Aggiorna `a->usati = fine`, aggiorna `a->picco` se `a->usati > a->picco` e restituisce `a->base + inizio`.

Perché calcolare il resto sull'indirizzo reale `a->base + a->usati` anziché solo sull'indice `a->usati`? Se `base` è allineata a `alignof(max_align_t)` (per esempio 16 byte), ma il chiamante chiede un oggetto allineato a 32 byte, `a->usati == 0` non garantisce che `a->base` sia multiplo di 32. Calcolare il resto sull'indirizzo effettivo tramite `uintptr_t` rende la funzione corretta per qualsiasi allineamento.

Il rilascio della memoria nell'arena avviene in blocco:

- **`arena_reset`** imposta semplicemente `a->usati = 0` in tempo costante $O(1)$ (preservando `a->picco`), rendendo immediatamente riutilizzabile l'intero buffer per una nuova fase di lavoro.
- **Marche di salvataggio e ripristino (checkpoint)**: se all'interno di una fase più lunga vuoi creare allocazioni temporanee annidate, salvi la posizione corrente con `size_t marca = a->usati;` e, al termine del lavoro temporaneo, riporti indietro il cursore con `arena_ripristina(a, marca)` (verificando `marca <= a->usati`). In questo modo gli oggetti allocati *prima* della marca restano intatti, mentre quelli allocati *dopo* vengono rilasciati tutti insieme.

Questo modello di gestione della memoria è ideale per strutture costruite per fasi: nel capitolo 26 useremo proprio un allocatore ad arena per allocare tutti i nodi dell'albero di sintassi del nostro interprete e liberarli in un colpo solo al termine dell'esecuzione.

Fai attenzione alla regola di sicurezza dello standard C23: mentre il calcolo degli spiazzamenti allineati e il ripristino del cursore sono completamente definiti, conservare e dereferenziare un puntatore ottenuto dall'arena *dopo* un `arena_reset` o *dopo* un `arena_ripristina` che riporta il cursore prima di quel blocco produce un **puntatore pendente** e l'accesso provoca **comportamento indefinito**.

> **Se vieni da Python** — In Python l'allocazione e la liberazione degli oggetti sono gestite automaticamente dal garbage collector e dal conteggio dei riferimenti, con un costo fisso per ogni singolo oggetto; in C puoi scegliere allocatori su misura (come arena, pool e lista libera) per azzerare il costo di allocazione e controllare esattamente l'allineamento e la durata di vita della memoria.

### Esempio guidato

Il programma seguente, organizzato su tre file (`arena.h`, `arena.c`, `main.c`), utilizza un allocatore ad arena appoggiato su un buffer statico `alignas(max_align_t)` per costruire una lista temporanea di token estratti da una frase. Dopo aver stampato i token, richiama `arena_reset` in tempo costante per analizzare una seconda frase senza chiamare mai `malloc` né `free`, e infine mostra il rientro pulito di `nullptr` quando una richiesta supera la capacità residua.

<!-- cod: id=22.2-a tipo=programma gruppo=arena_token file=arena.h -->
```c
#ifndef ARENA_H
#define ARENA_H

#include <stddef.h>

typedef struct arena {
    unsigned char *base;
    size_t cap;
    size_t usati;
    size_t picco;
} arena_t;

bool arena_inizializza(arena_t *a, void *buffer, size_t cap);
void *arena_alloca(arena_t *a, size_t dim);
void arena_reset(arena_t *a);

#endif
```

<!-- cod: id=22.2-b tipo=programma gruppo=arena_token file=arena.c -->
```c
#include "arena.h"
#include <stdckdint.h>
#include <stdint.h>

bool arena_inizializza(arena_t *a, void *buffer, size_t cap) {
    if (a == nullptr || buffer == nullptr || cap == 0) {
        return false;
    }
    if (((uintptr_t)buffer & (uintptr_t)(alignof(max_align_t) - 1)) != 0) {
        return false;
    }
    a->base = buffer;
    a->cap = cap;
    a->usati = 0;
    a->picco = 0;
    return true;
}

void *arena_alloca(arena_t *a, size_t dim) {
    if (a == nullptr || a->base == nullptr || dim == 0) {
        return nullptr;
    }
    size_t allin = alignof(max_align_t);
    uintptr_t curr = (uintptr_t)(a->base + a->usati);
    size_t resto = (size_t)(curr & (uintptr_t)(allin - 1));
    size_t pad = (resto == 0) ? 0 : (allin - resto);
    size_t inizio = 0;
    size_t fine = 0;
    if (ckd_add(&inizio, a->usati, pad) || ckd_add(&fine, inizio, dim) || fine > a->cap) {
        return nullptr;
    }
    a->usati = fine;
    if (a->usati > a->picco) {
        a->picco = a->usati;
    }
    return a->base + inizio;
}

void arena_reset(arena_t *a) {
    if (a != nullptr) {
        a->usati = 0;
    }
}
```

<!-- cod: id=22.2-c tipo=programma gruppo=arena_token file=main.c -->
```c
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "arena.h"

typedef struct nodo_token {
    char testo[16];
    struct nodo_token *prox;
} nodo_token_t;

static alignas(max_align_t) unsigned char spazio_arena[512];

static nodo_token_t *separa_parole(arena_t *a, const char *frase) {
    nodo_token_t *testa = nullptr;
    nodo_token_t **coda = &testa;
    const char *p = frase;
    while (*p != '\0') {
        while (*p == ' ') {
            ++p;
        }
        if (*p == '\0') {
            break;
        }
        const char *inizio = p;
        while (*p != '\0' && *p != ' ') {
            ++p;
        }
        size_t len = (size_t)(p - inizio);
        if (len >= sizeof(testa->testo)) {
            len = sizeof(testa->testo) - 1;
        }
        nodo_token_t *nodo = arena_alloca(a, sizeof(*nodo));
        if (nodo == nullptr) {
            return nullptr;
        }
        memcpy(nodo->testo, inizio, len);
        nodo->testo[len] = '\0';
        nodo->prox = nullptr;
        *coda = nodo;
        coda = &nodo->prox;
    }
    return testa;
}

static void stampa_lista(const char *etichetta, const nodo_token_t *t) {
    printf("%s:", etichetta);
    for (const nodo_token_t *c = t; c != nullptr; c = c->prox) {
        printf(" [%s]", c->testo);
    }
    printf("\n");
}

int main(void) {
    arena_t arena = {};
    if (!arena_inizializza(&arena, spazio_arena, sizeof(spazio_arena))) {
        return 1;
    }

    nodo_token_t *lista1 = separa_parole(&arena, "memoria veloce senza malloc");
    stampa_lista("Frase 1", lista1);

    arena_reset(&arena);
    nodo_token_t *lista2 = separa_parole(&arena, "reset in tempo costante");
    stampa_lista("Frase 2", lista2);

    void *eccesso = arena_alloca(&arena, 1024);
    printf("Richiesta 1024 byte: %s\n", (eccesso == nullptr) ? "nullptr (esaurita)" : "OK");
    printf("Picco non nullo: %d, usati dopo reset+frase2 > 0: %d\n",
           (arena.picco > 0) ? 1 : 0, (arena.usati > 0) ? 1 : 0);
    return 0;
}
```

```output
Frase 1: [memoria] [veloce] [senza] [malloc]
Frase 2: [reset] [in] [tempo] [costante]
Richiesta 1024 byte: nullptr (esaurita)
Picco non nullo: 1, usati dopo reset+frase2 > 0: 1
```

Nota come `separa_parole` costruisca l'intera lista concatenata di `nodo_token_t` senza alcuna funzione `libera_lista`: appena la prima frase è stata stampata, `arena_reset(&arena)` azzera il cursore e rende l'intero buffer `spazio_arena` pronto per la seconda frase. Quando poi `main` richiede `1024` byte da un'arena di `512` byte, `arena_alloca` rileva `fine > a->cap` e restituisce `nullptr` lasciando intatti i nodi di `lista2`.

> **Approfondimento — Frammentazione e durata di vita**
> Un'arena azzera il costo amministrativo per singolo oggetto (nessuna intestazione per blocco) e rende impossibili le perdite di memoria individuali, ma ha un limite strutturale: non può riciclare un singolo oggetto finché non si ripristina una marca o non si resetta l'intera arena. Funziona al meglio quando gli oggetti nascono e muoiono insieme.

### Esercizio 22.2 — Allocatore ad arena su buffer statico con allineamento esplicito e marche di ripristino

**Descrizione**

Realizza su tre file (`arena_st.h`, `arena_st.c`, `main.c`) un **allocatore ad arena** privo di chiamate a `malloc`, appoggiato su un buffer statico. (1) In `arena_st.h` (protetto da `ARENA_ST_H`) definisci `typedef struct arena { unsigned char *base; size_t cap; size_t usati; size_t picco; } arena_t;` e dichiara: `bool arena_init(arena_t *a, void *buffer, size_t cap);` (verifica `a != nullptr`, `buffer != nullptr`, `cap > 0` e che `buffer` sia allineato almeno a `alignof(max_align_t)`), `void *arena_alloca_allineato(arena_t *a, size_t dim, size_t allin);` (richiede `dim > 0` e `allin` potenza di due; calcola il padding necessario rispetto all'indirizzo corrente `a->base + a->usati` tramite `uintptr_t`, controlla overflow con `ckd_add` e capacità `fine <= a->cap`, aggiorna `usati` e `picco`), `void *arena_alloca(arena_t *a, size_t dim);` (delega a `arena_alloca_allineato(a, dim, alignof(max_align_t))`), `size_t arena_marca(const arena_t *a);`, `bool arena_ripristina(arena_t *a, size_t marca);` (accetta `marca <= a->usati` preservando `a->picco`) e `void arena_reset(arena_t *a);` (azzera `usati` preservando `picco`). (2) In `main.c` dichiara un buffer statico `static alignas(64) unsigned char mem_arena[256];` (con `static_assert(64 >= alignof(max_align_t))`), inizializza l'arena e gestisci da `stdin` una pila di al più `8` marche e i comandi: `ALLOC <dim> <allin>`, `ALLOC_DEF <dim>`, `MARK`, `RESTORE`, `RESET` e `STATS`. Per ogni allocazione riuscita verifica con `uintptr_t` l'allineamento del puntatore restituito e inizializza i byte con `memset`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- buffer statico allineato con `alignas(64)` / `alignas(max_align_t)` senza alcuna chiamata a `malloc`
- calcolo del padding rispetto all'indirizzo corrente e controllo di overflow con `ckd_add`
- salvataggio e ripristino del cursore (marche/checkpoint) per rilasci parziali annidati
- reset globale $O(1)$ mantenendo il picco storico di utilizzo

**Domande guida**

1. Perché `arena_alloca_allineato` calcola il resto di allineamento sull'indirizzo effettivo `a->base + a->usati` anziché solo su `a->usati`?
2. Che cosa succede ai puntatori allocati dopo una marca una volta che il chiamante invoca `arena_ripristina`?
3. Perché `arena_reset` e `arena_ripristina` non riducono il campo `a->picco`?
4. In quale caso `arena_alloca_allineato` deve restituire `nullptr` anche se `a->usati < a->cap`?

**Esempio di esecuzione**

```input
ALLOC 5 16
ALLOC 10 16
MARK
ALLOC 20 32
ALLOC 64 16
STATS
RESTORE
STATS
ALLOC_DEF 16
ALLOC 200 16
RESET
STATS
```

```output
ALLOC(5, 16): OK usati=5 allin_ok=1
ALLOC(10, 16): OK usati=26 allin_ok=1
MARK #1: pos=26
ALLOC(20, 32): OK usati=52 allin_ok=1
ALLOC(64, 16): OK usati=128 allin_ok=1
STATS: usati=128 picco=128 cap=256
RESTORE: OK usati=26
STATS: usati=26 picco=128 cap=256
ALLOC_DEF(16): OK allin_ok=1
ALLOC(200, 16): OK usati=248 allin_ok=1
RESET: usati=0
STATS: usati=0 picco=248 cap=256
```

## 22.3 L'allocatore a pool per blocchi di dimensione fissa

L'allocatore ad arena funziona benissimo quando gli oggetti muoiono tutti insieme, ma non è adatto quando gli oggetti vengono creati e distrutti in ordine arbitrario: pensa alle particelle di una simulazione fisica, alle connessioni attive di un server o ai nodi di una struttura dati dinamica che crescono e si riducono continuamente. In molti di questi casi, però, tutti gli oggetti hanno esattamente la **stessa dimensione**.

Sfruttando questa uniformità possiamo costruire un **allocatore a pool** (*pool allocator*, spesso chiamato anche *fixed-size pool*): un allocatore specializzato che gestisce blocchi di dimensione fissa garantendo allocazione e rilascio in tempo costante ($O(1)$) e **zero frammentazione esterna**, perché ogni blocco liberato ha sempre la dimensione esatta per accogliere qualsiasi richiesta successiva.

Come fa un pool a sapere in tempo costante qual è il prossimo blocco libero senza scorrere l'intero buffer? Mantiene una **lista libera** (*free list*): una sequenza collegata di blocchi di memoria disponibili mantenuta dall'allocatore per soddisfare nuove richieste e riciclare blocchi liberati. Il trucco fondamentale del pool è che, finché un blocco è libero, i suoi byte non contengono dati dell'utente: possiamo usarne i primi `sizeof(void *)` byte per memorizzare il puntatore al blocco libero successivo! In questo modo la lista libera non richiede nessuna allocazione esterna di nodi.

```text
Pool di 4 blocchi di dimensione uniforme (passo):
testa_libera -> [ Blocco 0: prox -> B2 ] [ Blocco 1: OCCUPATO ] [ Blocco 2: prox -> nullptr ] [ Blocco 3: OCCUPATO ]
```

Quando il chiamante chiede un blocco (`pool_alloca`), il pool estrae il blocco in testa alla lista libera (`testa_libera`), sposta `testa_libera` sul blocco successivo e restituisce l'indirizzo estratto: poche istruzioni, tempo $O(1)$. Quando il chiamante libera un blocco (`pool_libera`), il pool scrive il vecchio valore di `testa_libera` nei primi byte del blocco appena rilasciato e fa puntare `testa_libera` ad esso: ancora tempo $O(1)$.

Per realizzare questo schema in modo portabile e conforme allo standard C23 occorre rispettare tre regole rigorose:

1. **Calcolo del passo (dimensione dello slot)**: ogni blocco deve poter ospitare sia i dati richiesti (`dim_blocco`) sia il puntatore della lista libera (`sizeof(void *)`), ed essere allineato per qualsiasi tipo fondamentale. Si prende quindi `min_dim = max(dim_blocco, sizeof(void *))` e lo si arrotonda al multiplo superiore di `alignof(max_align_t)` controllando gli overflow con `ckd_add` e `ckd_mul` prima di allocare `n_blocchi * passo` byte.
2. **Tipo effettivo e `memcpy` per il puntatore `prox`**: quando un blocco viene riciclato — prima contiene il puntatore `void *` della lista libera, poi una `struct` dell'utente, poi di nuovo `void *` — devi rispettare la regola del **tipo effettivo** e dello **strict aliasing** (che analizzeremo in dettaglio nella sotto-sezione 22.5). Un'area di memoria ottenuta da `malloc` non ha un tipo dichiarato: ogni scrittura di un oggetto utente ne imposta legalmente il nuovo tipo effettivo. Per leggere e scrivere il puntatore `prox` all'interno di un blocco libero senza violare le regole di aliasing, si usa sempre `memcpy(&prox, blocco, sizeof(prox))` e `memcpy(blocco, &prox, sizeof(prox))`, mai cast diretti del tipo `*(void **)blocco`.
3. **Validazione sicura in `pool_libera`**: prima di reinserire un puntatore `ptr` nella lista libera, un pool robusto verifica due cose: che `ptr` appartenga davvero all'intervallo del pool su un confine esatto di slot, e che quel blocco non sia già libero (per bloccare sul nascere una **doppia liberazione**, che creerebbe un ciclo infinito nella lista libera). Attenzione: in C confrontare con `<` o `>=` due puntatori che non appartengono allo stesso oggetto allocato (per esempio `ptr` sullo stack e `p->memoria` sullo heap) provoca **comportamento indefinito**. La soluzione portabile è convertire gli indirizzi a `uintptr_t`, controllare `addr >= base && addr < fine && ((addr - base) % p->passo) == 0`, ricavare l'indice dello slot `idx = (size_t)(addr - base) / p->passo` e verificare una tabella di stato `uint8_t *occupato`.

Secondo lo standard C23, le regole sul tipo effettivo degli oggetti allocati dinamicamente e sulla copia con `memcpy` sono completamente definite; leggere un blocco riciclato prima di scrivervi il nuovo tipo, liberare due volte lo stesso blocco o confrontare con `<` puntatori a oggetti non correlati provoca invece **comportamento indefinito**.

### Esempio guidato

Il programma seguente su tre file (`pool_entita.h`, `pool_entita.c`, `main.c`) implementa un allocatore a pool per gestire le particelle di una piccola simulazione. Alloca quattro particelle fino a riempire il pool, ne libera due in ordine sparso, alloca una nuova particella che ricicla esattamente l'ultimo slot liberato in tempo costante $O(1)$ e stampa ad ogni passo il numero di blocchi occupati e liberi.

<!-- cod: id=22.3-a tipo=programma gruppo=pool_particelle file=pool_entita.h -->
```c
#ifndef POOL_ENTITA_H
#define POOL_ENTITA_H

#include <stddef.h>

typedef struct pool_entita pool_entita_t;

pool_entita_t *pool_entita_crea(size_t dim_blocco, size_t n_blocchi);
void pool_entita_distruggi(pool_entita_t *p);
void *pool_entita_alloca(pool_entita_t *p);
bool pool_entita_libera(pool_entita_t *p, void *ptr);
size_t pool_entita_occupati(const pool_entita_t *p);
size_t pool_entita_liberi(const pool_entita_t *p);

#endif
```

<!-- cod: id=22.3-b tipo=programma gruppo=pool_particelle file=pool_entita.c -->
```c
#include "pool_entita.h"
#include <stdckdint.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct pool_entita {
    unsigned char *memoria;
    uint8_t *stato;
    void *testa_libera;
    size_t passo;
    size_t n_blocchi;
    size_t occupati;
};

pool_entita_t *pool_entita_crea(size_t dim_blocco, size_t n_blocchi) {
    if (dim_blocco == 0 || n_blocchi == 0) {
        return nullptr;
    }
    size_t base_dim = (dim_blocco < sizeof(void *)) ? sizeof(void *) : dim_blocco;
    size_t allin = alignof(max_align_t);
    size_t somma = 0;
    size_t tot = 0;
    if (ckd_add(&somma, base_dim, allin - 1)) {
        return nullptr;
    }
    size_t passo = somma & ~(allin - 1);
    if (ckd_mul(&tot, n_blocchi, passo)) {
        return nullptr;
    }
    pool_entita_t *p = calloc(1, sizeof(*p));
    if (p == nullptr) {
        return nullptr;
    }
    p->memoria = malloc(tot);
    p->stato = calloc(n_blocchi, sizeof(*p->stato));
    if (p->memoria == nullptr || p->stato == nullptr) {
        free(p->memoria);
        free(p->stato);
        free(p);
        return nullptr;
    }
    p->passo = passo;
    p->n_blocchi = n_blocchi;
    for (size_t i = 0; i < n_blocchi; ++i) {
        void *prox = (i + 1 < n_blocchi) ? (void *)(p->memoria + (i + 1) * passo) : nullptr;
        memcpy(p->memoria + i * passo, &prox, sizeof(prox));
    }
    p->testa_libera = p->memoria;
    return p;
}

void pool_entita_distruggi(pool_entita_t *p) {
    if (p == nullptr) {
        return;
    }
    free(p->memoria);
    free(p->stato);
    free(p);
}

void *pool_entita_alloca(pool_entita_t *p) {
    if (p == nullptr || p->testa_libera == nullptr) {
        return nullptr;
    }
    void *blocco = p->testa_libera;
    void *prox = nullptr;
    memcpy(&prox, blocco, sizeof(prox));
    p->testa_libera = prox;
    size_t idx = (size_t)((unsigned char *)blocco - p->memoria) / p->passo;
    p->stato[idx] = 1;
    ++p->occupati;
    return blocco;
}

bool pool_entita_libera(pool_entita_t *p, void *ptr) {
    if (p == nullptr || ptr == nullptr) {
        return false;
    }
    uintptr_t addr = (uintptr_t)ptr;
    uintptr_t base = (uintptr_t)p->memoria;
    uintptr_t fine = base + p->n_blocchi * p->passo;
    if (addr < base || addr >= fine || ((addr - base) % p->passo) != 0) {
        return false;
    }
    size_t idx = (size_t)(addr - base) / p->passo;
    if (p->stato[idx] == 0) {
        return false;
    }
    p->stato[idx] = 0;
    memcpy(ptr, &p->testa_libera, sizeof(p->testa_libera));
    p->testa_libera = ptr;
    --p->occupati;
    return true;
}

size_t pool_entita_occupati(const pool_entita_t *p) {
    return (p != nullptr) ? p->occupati : 0;
}

size_t pool_entita_liberi(const pool_entita_t *p) {
    return (p != nullptr) ? (p->n_blocchi - p->occupati) : 0;
}
```

<!-- cod: id=22.3-c tipo=programma gruppo=pool_particelle file=main.c -->
```c
#include <stdio.h>
#include "pool_entita.h"

typedef struct particella {
    int id;
    double x;
    double y;
} particella_t;

int main(void) {
    pool_entita_t *pool = pool_entita_crea(sizeof(particella_t), 4);
    if (pool == nullptr) {
        return 1;
    }

    particella_t *attive[4] = {};
    for (int i = 0; i < 4; ++i) {
        attive[i] = pool_entita_alloca(pool);
        attive[i]->id = i + 1;
        attive[i]->x = (double)i * 1.5;
        attive[i]->y = (double)i * -0.5;
    }
    printf("Dopo 4 allocazioni: occ=%zu lib=%zu\n",
           pool_entita_occupati(pool), pool_entita_liberi(pool));
    printf("Quinta allocazione: %s\n",
           (pool_entita_alloca(pool) == nullptr) ? "PIENO" : "OK");

    pool_entita_libera(pool, attive[1]);
    pool_entita_libera(pool, attive[3]);
    printf("Dopo 2 rilasci: occ=%zu lib=%zu\n",
           pool_entita_occupati(pool), pool_entita_liberi(pool));

    particella_t *nuova = pool_entita_alloca(pool);
    bool riciclato = (nuova == attive[3]);
    nuova->id = 99;
    nuova->x = 10.0;
    nuova->y = 20.0;
    printf("Nuova particella id=%d (%.1f, %.1f) riciclato_slot3=%d occ=%zu lib=%zu\n",
           nuova->id, nuova->x, nuova->y, riciclato ? 1 : 0,
           pool_entita_occupati(pool), pool_entita_liberi(pool));

    pool_entita_distruggi(pool);
    return 0;
}
```

```output
Dopo 4 allocazioni: occ=4 lib=0
Quinta allocazione: PIENO
Dopo 2 rilasci: occ=2 lib=2
Nuova particella id=99 (10.0, 20.0) riciclato_slot3=1 occ=3 lib=1
```

Osserva come `pool_entita_t` nasconda la propria implementazione dietro un **tipo opaco** (capitolo 19). Quando liberiamo `attive[1]` e poi `attive[3]`, quest'ultimo finisce in cima alla lista libera (politica LIFO): la successiva `pool_entita_alloca` restituisce esattamente l'indirizzo di `attive[3]` in tempo costante, senza mai invocare `malloc`, e la scrittura dei campi di `nuova` imposta legalmente il nuovo valore nello slot riciclato.

> **Approfondimento — Memoria da `malloc`, tipo effettivo e `memcpy`**
> Perché in C23 la memoria di un pool generico dovrebbe provenire da `malloc` e leggere/scrivere il puntatore della lista libera con `memcpy`? Un blocco allocato con `malloc` non ha un tipo dichiarato, quindi ogni scrittura di un nuovo tipo utente ne aggiorna legalmente il tipo effettivo, mentre `memcpy` evita qualsiasi conflitto di strict aliasing quando il blocco torna nella lista libera.

### Esercizio 22.3 — Allocatore a pool generico opaco con rilevamento di doppia liberazione e puntatori estranei

**Descrizione**

Realizza su tre file (`pool_blocchi.h`, `pool_blocchi.c`, `main.c`) un **allocatore a pool** generico come **tipo opaco** `pool_t` per blocchi di dimensione fissa. (1) In `pool_blocchi.h` (protetto da `POOL_BLOCCHI_H`) definisci `typedef struct pool pool_t;` e `typedef enum pool_esito { POOL_OK = 0, POOL_ERR_NULLO, POOL_ERR_FUORI_POOL, POOL_ERR_DOPPIA_FREE } pool_esito_t;`, e dichiara `pool_t *pool_crea(size_t dim_blocco, size_t n_blocchi);`, `void pool_distruggi(pool_t *p);`, `void *pool_alloca(pool_t *p);`, `pool_esito_t pool_libera(pool_t *p, void *ptr);`, `size_t pool_liberi(const pool_t *p);`, `size_t pool_occupati(const pool_t *p);`, `size_t pool_picco(const pool_t *p);` e `size_t pool_capacita(const pool_t *p);`. (2) In `pool_blocchi.c` arrotonda il passo di ciascuno slot al multiplo superiore di `alignof(max_align_t)` di `max(dim_blocco, sizeof(void *))` controllando l'overflow con `ckd_add`/`ckd_mul`, alloca l'area contigua con `malloc` (priva di tipo dichiarato, così da rispettare il tipo effettivo C23 al riciclo dei blocchi) e una tabella di stato `uint8_t *occupato` con `calloc`. Mantieni la lista libera leggendo e scrivendo il puntatore `prox` dentro ogni blocco libero esclusivamente con `memcpy`. In `pool_libera` valida `ptr` tramite `uintptr_t` (rifiutando puntatori estranei o disallineati con `POOL_ERR_FUORI_POOL` e blocchi già liberi con `POOL_ERR_DOPPIA_FREE`). (3) In `main.c` gestisci un array di `16` handle `sessione_t *slots[16]` (`typedef struct sessione { uint32_t id; int64_t punti; char tag[12]; } sessione_t;`) con i comandi da `stdin`: `INIT <n>` (`1 <= n <= 16`), `NEW <slot> <id> <punti> <tag>`, `SHOW <slot>`, `FREE <slot>` (senza azzerare `slots[slot]` così da poter testare una doppia liberazione; prima di uscire libera solo gli slot ancora attivi tramite `pool_distruggi`), `FREE_BAD` (tenta `pool_libera` su `nullptr`, su una variabile sullo stack e su un puntatore interno disallineato a `+1` byte dallo slot 0 se allocato) e `STATS`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- allocazione e rilascio $O(1)$ tramite lista libera memorizzata nei blocchi liberi su slot a passo costante allineato
- rispetto del tipo effettivo C23 sui blocchi riciclati mediante memoria `malloc` e `memcpy` per il collegamento della lista libera
- verifica di appartenenza al pool e confine di slot tramite `uintptr_t` evitando confronti `<` tra puntatori estranei
- rilevamento deterministico della doppia liberazione tramite tabella di stato

**Domande guida**

1. Perché il passo di ogni blocco del pool deve essere almeno `sizeof(void *)` oltre che multiplo di `alignof(max_align_t)`?
2. In che modo usare `memcpy` per salvare e leggere il puntatore al blocco libero successivo previene violazioni di strict aliasing?
3. Perché in `pool_libera` conviene convertire `ptr` e `p->memoria` a `uintptr_t` prima di verificare se `ptr` rientra nell'intervallo del pool?
4. Che cosa succederebbe alla lista libera se un blocco già libero venisse reinserito una seconda volta senza il controllo di doppia liberazione?

**Esempio di esecuzione**

```input
INIT 3
NEW 0 101 500 ALFA
NEW 1 102 750 BETA
NEW 2 103 200 GAMMA
NEW 3 104 100 DELTA
STATS
SHOW 1
FREE 1
FREE 1
FREE_BAD
NEW 3 104 900 DELTA
SHOW 3
STATS
```

```output
INIT: cap=3
NEW[0]: OK allin_ok=1
NEW[1]: OK allin_ok=1
NEW[2]: OK allin_ok=1
NEW[3]: PIENO
STATS: liberi=0 occupati=3 tot=3 picco=3
SHOW[1]: id=102 punti=750 tag=BETA
FREE[1]: OK
FREE[1]: DOPPIA_FREE
FREE_BAD: null=NULLO stack=FUORI_POOL disallin=FUORI_POOL
NEW[3]: OK allin_ok=1
SHOW[3]: id=104 punti=900 tag=DELTA
STATS: liberi=0 occupati=3 tot=3 picco=3
```

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
#include <inttypes.h>
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
    printf("Messaggio #%" PRIu32 " (%zu char): %s\n", m->id, m->len, m->testo);
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

## 22.5 Strict aliasing, `restrict` e diagnosi delle corruzioni

Quando lavori a basso livello con puntatori, buffer grezzi e allocatori personalizzati, una domanda torna spesso: se ho una variabile `float x`, posso leggerne i bit convertendo `&x` a `uint32_t *`? La risposta dello standard C23 è un netto no, e il motivo riguarda il modo in cui il compilatore genera codice veloce.

Per ottimizzare un programma, il compilatore deve sapere se una scrittura tramite un puntatore `p` può modificare l'oggetto letto tramite un altro puntatore `q` (situazione chiamata *aliasing*). Se dovesse supporre che qualunque puntatore possa puntare a qualunque variabile, dovrebbe ricaricare ogni valore dalla memoria dopo ogni scrittura, rinunciando a gran parte delle ottimizzazioni nei registri.

Per questo lo standard definisce il **tipo effettivo** di un oggetto in memoria (il suo tipo dichiarato, oppure, per la memoria priva di tipo restituita da `malloc`, il tipo dell'ultima scrittura eseguita su di essa) e stabilisce la regola di **strict aliasing**: un oggetto in memoria non può essere letto o scritto tramite un puntatore di tipo incompatibile. In particolare, lo standard C23 consente di accedere a un oggetto solo attraverso un'espressione di uno di questi tipi:

- il proprio tipo effettivo (o una versione qualificata con `const` o `volatile`);
- la corrispondente versione con segno o senza segno (per esempio `unsigned int` per un `int`);
- una `struct` o una `union` che contenga tra i suoi campi uno dei tipi sopra elencati;
- un **tipo carattere** (`char`, `signed char` oppure `unsigned char`), che ha il permesso speciale di ispezionare la rappresentazione in byte di qualsiasi oggetto.

Violando questa regola — per esempio facendo il cosiddetto *type punning* tramite cast di puntatore — si provoca **comportamento indefinito**:

<!-- cod: id=22.5-b tipo=frammento -->
```c
// ERRORE: comportamento indefinito (violazione di strict aliasing), NON scrivere mai così!
float f = 1.5f;
uint32_t bit_sbagliati = *(uint32_t *)&f;
```

Come si reinterpretano allora i bit di un `float` o di un `double` in modo 100% portabile e conforme al C23? Con `memcpy`, affiancata da una `static_assert` sulle dimensioni:

<!-- cod: id=22.5-c tipo=frammento -->
```c
static_assert(sizeof(float) == sizeof(uint32_t));
float f = 1.5f;
uint32_t bit = 0;
memcpy(&bit, &f, sizeof(bit));
```

`memcpy` copia la rappresentazione in byte nell'oggetto di destinazione (che mantiene il proprio tipo dichiarato `uint32_t`), rispettando strict aliasing; inoltre tutti i compilatori moderni riconoscono questo idioma e lo traducono in un singolo spostamento di registro senza alcuna chiamata a funzione. Che dire invece del *type punning* tramite `union` (scrivere in un campo `float` e leggere da un campo `uint32_t`)? In C la lettura di un campo non attivo di una `union` reinterpreta la rappresentazione dei byte (dipendendo comunque da dimensione, padding ed endianness della piattaforma), ma può creare problemi di portabilità (per esempio con i bit di padding o in codice condiviso con C++): per questo `memcpy` resta la tecnica più pulita, esplicita e universale.

Strict aliasing permette al compilatore di escludere l'aliasing tra puntatori di **tipi incompatibili** (come `float *` e `uint32_t *`), ma non aiuta quando due puntatori hanno lo **stesso tipo** (come `double *dst` e `const double *a`). Qui interviene il qualificatore `restrict` (introdotto nel capitolo 14): qualificando i parametri come `double *restrict dst, const double *restrict a`, prometti al compilatore che le aree di memoria a cui accedi tramite quei puntatori **non si sovrappongono**. Così il compilatore può ottimizzare il ciclo esattamente come fa per tipi incompatibili. Come per strict aliasing, violare la promessa di `restrict` (passando aree sovrapposte) provoca **comportamento indefinito** (approfondiremo l'interazione tra comportamento indefinito e ottimizzazioni nel capitolo 25).

> **Se vieni da Python** — In Python il modulo `struct` converte numeri in sequenze di byte senza esporre l'aliasing dei puntatori; in C la reinterpretazione portabile dei bit di un oggetto richiede `memcpy` per rispettare la regola di strict aliasing.

Chiudiamo il capitolo con le **tecniche difensive** che puoi integrare nei tuoi allocatori per diagnosticare corruzioni della memoria durante lo sviluppo, in affiancamento ad AddressSanitizer:

- **Canarini di confine (*redzone*)**: prima e dopo il payload restituito al chiamante, l'allocatore riserva due fasce di guardia (la guardia sinistra deve avere dimensione multipla di `alignof(max_align_t)` per preservare l'allineamento del payload) e le riempie con byte noti (per esempio `0xA5` a sinistra e `0x5A` a destra). Alla verifica o al rilascio, se anche un solo byte delle guardie è cambiato, l'allocatore segnala immediatamente un **underflow** (scrittura prima dell'inizio) o un **overflow** (scrittura oltre la fine).
- **Avvelenamento (*poisoning*)**: subito dopo l'allocazione il payload viene riempito con un pattern riconoscibile (come `0xAA`) per far emergere subito eventuali letture di memoria non inizializzata; subito prima della `free`, il payload viene sovrascritto con un altro pattern (come `0xDD`) per rendere evidenti eventuali errori di **uso dopo la liberazione**.
- **Tracciamento delle allocazioni attive**: mantenendo una tabella di record indicizzati tramite `(uintptr_t)payload`, l'allocatore diagnostico può segnalare con precisione i blocchi e i byte non ancora liberati (**perdite di memoria**) e intercettare le **doppie liberazioni**.

```text
Blocco protetto da canarini (allocato in un'unica malloc):
+--------------------+------------------------+--------------------+
| Guardia sinistra   | Payload (avvelenato)   | Guardia destra     |
| 0xA5 0xA5 ... 0xA5 | 0xAA 0xAA ... 0xAA     | 0x5A 0x5A ... 0x5A |
+--------------------+------------------------+--------------------+
^ grezzo             ^ payload (allineato)    ^ payload + dim
```

### Esempio guidato

Il programma seguente riunisce i tre pilastri della sotto-sezione: (1) reinterpreta in modo sicuro i bit di un `double` con `memcpy` e `static_assert` (evitando il cast scorretto mostrato sopra), (2) esegue un ciclo vettoriale con `restrict` su array disgiunti, e (3) costruisce un piccolo blocco protetto da byte canarino capace di rilevare uno sforamento di un singolo byte nella redzone destra senza causare comportamento indefinito (poiché la redzone appartiene comunque al blocco allocato con `malloc`).

<!-- cod: id=22.5-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static_assert(sizeof(double) == sizeof(uint64_t));

static constexpr size_t GUARDIA = (alignof(max_align_t) > 16) ? alignof(max_align_t) : 16;
static constexpr unsigned char CAN_SX = 0xA5U;
static constexpr unsigned char CAN_DX = 0x5AU;
static constexpr unsigned char VELENO_ALLOC = 0xAAU;
static constexpr unsigned char VELENO_FREE = 0xDDU;

static uint64_t double_a_bit(double x) {
    uint64_t bit = 0;
    memcpy(&bit, &x, sizeof(bit));
    return bit;
}

static void scala_e_somma(size_t n, double *restrict dst,
                          const double *restrict a, const double *restrict b, double k) {
    for (size_t i = 0; i < n; ++i) {
        dst[i] = a[i] + k * b[i];
    }
}

static unsigned char *alloca_protetto(size_t dim) {
    unsigned char *grezzo = malloc(GUARDIA + dim + GUARDIA);
    if (grezzo == nullptr) {
        return nullptr;
    }
    memset(grezzo, CAN_SX, GUARDIA);
    memset(grezzo + GUARDIA, VELENO_ALLOC, dim);
    memset(grezzo + GUARDIA + dim, CAN_DX, GUARDIA);
    return grezzo + GUARDIA;
}

static bool guardie_integre(const unsigned char *payload, size_t dim) {
    const unsigned char *grezzo = payload - GUARDIA;
    for (size_t i = 0; i < GUARDIA; ++i) {
        if (grezzo[i] != CAN_SX || grezzo[GUARDIA + dim + i] != CAN_DX) {
            return false;
        }
    }
    return true;
}

static void libera_protetto(unsigned char *payload, size_t dim) {
    memset(payload, VELENO_FREE, dim);
    free(payload - GUARDIA);
}

int main(void) {
    double valore = -3.5;
    uint64_t bit = double_a_bit(valore);
    printf("double %.1f -> bit = 0x%016" PRIx64 "\n", valore, bit);

    double a[3] = {1.0, 2.0, 3.0};
    double b[3] = {0.5, 1.0, -1.5};
    double dst[3] = {};
    scala_e_somma(3, dst, a, b, 2.0);
    printf("restrict: %.1f %.1f %.1f\n", dst[0], dst[1], dst[2]);

    size_t dim = 8;
    unsigned char *buf = alloca_protetto(dim);
    if (buf == nullptr) {
        return 1;
    }
    printf("Prima della corruzione: guardie=%s\n", guardie_integre(buf, dim) ? "OK" : "CORROTTE");
    buf[dim] = 0xFFU;  // scrive 1 byte dentro la guardia destra (ancora nel blocco malloc)
    printf("Dopo sforamento di 1 byte: guardie=%s\n", guardie_integre(buf, dim) ? "OK" : "CORROTTE");
    libera_protetto(buf, dim);
    return 0;
}
```

```output
double -3.5 -> bit = 0xc00c000000000000
restrict: 2.0 4.0 0.0
Prima della corruzione: guardie=OK
Dopo sforamento di 1 byte: guardie=CORROTTE
```

Osserva come `buf[dim] = 0xFFU;` simuli uno sforamento di un singolo byte oltre il payload senza provocare comportamento indefinito durante il test: il byte all'indice `dim` appartiene infatti alla fascia `GUARDIA` allocata dalla stessa `malloc`, e `guardie_integre` intercetta subito l'alterazione del byte canarino `0x5A`.

> **Approfondimento — Perché violare strict aliasing si rompe con `-O2`**
> Un programma che viola strict aliasing può sembrare funzionare quando lo compili con `-O0` e rompersi improvvisamente con `-O2`: con le ottimizzazioni attive il compilatore assume per contratto che un `float *` e un `uint32_t *` non puntino allo stesso indirizzo e può mantenere il valore di uno dei due in un registro senza ricaricarlo dopo la scrittura sull'altro.

### Esercizio 22.5 — Allocatore diagnostico con canarini di confine, poisoning, ispezione bit via `memcpy` e kernel `restrict`

**Descrizione**

Realizza su tre file (`mem_diag.h`, `mem_diag.c`, `main.c`) un modulo di diagnostica e manipolazione sicura della memoria che integri canarini di confine (redzone), avvelenamento dei byte (poisoning), reinterpretazione di bit conforme a **strict aliasing** e operazioni con `restrict`. (1) In `mem_diag.h` (protetto da `MEM_DIAG_H`) definisci il tipo opaco `diag_ctx_t`, l'enumerazione `diag_esito_t` (`DIAG_OK`, `DIAG_ERR_SCONOSCIUTO`, `DIAG_ERR_GIA_LIBERATO`, `DIAG_ERR_UNDERFLOW`, `DIAG_ERR_OVERFLOW`, `DIAG_ERR_ENTRAMBI`) e dichiara: `diag_ctx_t *diag_crea(void);`, `void diag_distruggi(diag_ctx_t *ctx);`, `void *diag_alloca(diag_ctx_t *ctx, size_t dim);`, `diag_esito_t diag_verifica(const diag_ctx_t *ctx, const void *ptr);`, `diag_esito_t diag_libera(diag_ctx_t *ctx, void *ptr);`, `void diag_report_leak(const diag_ctx_t *ctx, size_t *blocchi_attivi, size_t *byte_attivi);`, `const char *diag_esito_nome(diag_esito_t e);`, `uint32_t float_a_bit(float x);`, `float bit_a_float(uint32_t b);` e `void combina_disgiunti(size_t n, float *restrict dst, const float *restrict a, const float *restrict b, float k);`. (2) In `mem_diag.c` ogni blocco allocato da `diag_alloca` riserva una guardia sinistra di `ALLIN_GUARD` byte (`>= alignof(max_align_t)`) riempita con `0xA5`, il payload di `dim` byte riempito con `0xAA` e una guardia destra di `ALLIN_GUARD` byte riempita con `0x5A`; al rilascio `diag_libera` controlla le guardie, avvelena il payload con `0xDD` prima di `free` e conserva la chiave `uintptr_t` per segnalare eventuali doppie liberazioni. Implementa `float_a_bit` e `bit_a_float` esclusivamente con `memcpy` e `static_assert(sizeof(float) == sizeof(uint32_t))`, e `combina_disgiunti` come `dst[i] = a[i] + k * b[i]`. (3) In `main.c` gestisci fino a `16` blocchi tramite i comandi da `stdin`: `ALLOC <id> <dim>`, `CORROMPI_SX <id>` (altera il byte `-1` dentro la guardia sinistra), `CORROMPI_DX <id>` (altera il byte `dim` dentro la guardia destra), `CHECK <id>`, `FREE <id>`, `FBITS <val>` (estrae segno, esponente e mantissa con `float_a_bit` e verifica il round-trip con `bit_a_float`), `AXPY <k> <n> <a0..> <b0..>` (alloca `a`, `b`, `dst` disgiunti con `diag_alloca`, invoca `combina_disgiunti`, stampa i risultati e verifica che le tre `diag_libera` restituiscano `DIAG_OK`) e `LEAKS`.

**Concetti da tenere a mente**

- guardie di confine (redzone/canarini) allineate per rilevare underflow e overflow senza comportamento indefinito
- avvelenamento (poisoning) con `memset` su allocazione e rilascio e tracciamento delle perdite di memoria
- reinterpretazione portabile dei bit di un `float` tramite `memcpy` e `static_assert` nel rispetto di strict aliasing
- contratto di non sovrapposizione del qualificatore `restrict` su buffer distinti

**Domande guida**

1. Perché la guardia sinistra posta prima del payload deve avere dimensione multipla di `alignof(max_align_t)`?
2. In che modo scrivere un byte nella guardia sinistra a `payload[-1]` durante il test evita il comportamento indefinito pur simulando un underflow?
3. Perché `float_a_bit` usa `memcpy` anziché `*(uint32_t *)&x`, e perché questa scelta non penalizza le prestazioni con il compilatore ottimizzante?
4. Quale contratto violeresti se invocassi `combina_disgiunti` passando lo stesso buffer sia come `dst` sia come `a`?

**Esempio di esecuzione**

```input
ALLOC 0 16
ALLOC 1 12
CHECK 0
CORROMPI_DX 0
CHECK 0
FREE 0
FREE 0
CORROMPI_SX 1
CORROMPI_DX 1
CHECK 1
LEAKS
FREE 1
LEAKS
FBITS 1.0
FBITS -6.5
AXPY 2.0 3 1.0 2.0 3.0 0.5 1.5 -1.0
LEAKS
```

```output
ALLOC[0]: OK dim=16
ALLOC[1]: OK dim=12
CHECK[0]: OK
CORROMPI_DX[0]: OK
CHECK[0]: OVERFLOW
FREE[0]: OVERFLOW
FREE[0]: GIA_LIBERATO
CORROMPI_SX[1]: OK
CORROMPI_DX[1]: OK
CHECK[1]: ENTRAMBI
LEAKS: blocchi=1 byte=12
FREE[1]: ENTRAMBI
LEAKS: blocchi=0 byte=0
FBITS 1.00: hex=0x3f800000 segno=0 esp=127 mant=0x000000 roundtrip=OK
FBITS -6.50: hex=0xc0d00000 segno=1 esp=129 mant=0x500000 roundtrip=OK
AXPY: 2.00 5.00 1.00 (guardie=OK)
LEAKS: blocchi=0 byte=0
```

## Riepilogo

- Lo specificatore C23 `alignas` rafforza il requisito di allineamento di oggetti e campi di `struct` (a un tipo o a una potenza di due), senza mai poterlo ridurre; `max_align_t` (`<stddef.h>`) fornisce tramite `alignof(max_align_t)` il più grande allineamento fondamentale supportato dalla piattaforma. Per arrotondare in modo sicuro una dimensione `n` al multiplo superiore di `A` si verifica `A != 0 && (A & (A - 1)) == 0`, si usa `ckd_add(&s, n, A - 1)` e si applica `s & ~(A - 1)`.
- Un **allocatore ad arena** assegna memoria in tempo costante avanzando un cursore su un buffer contiguo (per esempio statico con `alignas(max_align_t)`) e libera tutti gli oggetti in un colpo solo con `arena_reset` oppure per fasi annidate con marche di salvataggio e ripristino (lo useremo per i nodi dell'albero di sintassi nel capitolo 26).
- Un **allocatore a pool** gestisce blocchi di dimensione fissa (arrotondata al massimo tra `dim_blocco` e `sizeof(void *)`, multiplo di `alignof(max_align_t)`) collegati in una **lista libera** memorizzata dentro i blocchi liberi stessi: garantisce allocazione e rilascio in tempo costante con zero frammentazione esterna, usa memoria `malloc` e `memcpy` per rispettare il tipo effettivo C23 e valida i puntatori in rilascio tramite `uintptr_t` e una tabella di stato.
- Un **campo array flessibile** (`tipo nome[]` come ultimo campo di una `struct`) consente di allocare intestazione e dati variabili in un solo blocco con `offsetof(struct s, nome) + N * sizeof(tipo)`. Un allocatore generico con lista libera antepone a ogni blocco un'intestazione allineata ad `alignof(max_align_t)`, applica first-fit e splitting all'allocazione ed esegue il coalescing dei blocchi liberi adiacenti al rilascio per contrastare la frammentazione esterna.
- La regola di **strict aliasing** vieta di leggere o scrivere un oggetto tramite un puntatore di tipo incompatibile (salvo i tipi carattere e le eccezioni previste dallo standard): per reinterpretare i bit di un oggetto si usa sempre `memcpy` con `static_assert`. `restrict` estende la garanzia di non sovrapposizione a puntatori dello stesso tipo (approfondiremo l'interazione con le ottimizzazioni nel capitolo 25). Canarini di confine (redzone), avvelenamento dei byte (poisoning) e tracciamento dei blocchi completano la diagnosi delle corruzioni di memoria.

## Errori comuni

- **Dichiarare il buffer di un allocatore ad arena come semplice `unsigned char buf[N]` senza `alignas(max_align_t)`**: poiché `alignof(unsigned char)` è `1`, il buffer può iniziare a un indirizzo non allineato per `int64_t` o `double`, portando a comportamento indefinito.
- **Arrotondare una dimensione con `(n + allin - 1) & ~(allin - 1)` senza controlli**: se `allin` è `0` o non è una potenza di due il risultato è errato; se `n` è vicino a `SIZE_MAX` la somma va in wrap-around senza segno e produce un numero piccolo.
- **Usare il cast di puntatore `*(uint32_t *)&f` al posto di `memcpy` per leggere i bit di un `float`**: viola la regola di strict aliasing e introduce comportamento indefinito, spesso invisibile con `-O0` ma distruttivo con `-O2`.
- **Inserire una `struct` con campo array flessibile in un array o copiarla con `*dst = *src`**: il primo caso è vietato dal linguaggio, mentre l'assegnazione copia solo i campi fissi ignorando gli elementi dell'array finale.
- **Dimenticare il coalescing nella lista libera o non rilevare la doppia liberazione in un pool**: nel primo caso la frammentazione esterna rende presto inutilizzabile lo spazio libero; nel secondo caso si crea un ciclo infinito nella lista libera.

## Prima di proseguire

- [ ] So allineare buffer statici e `struct` con `alignas` e `max_align_t`, verificare l'allineamento con `uintptr_t` e arrotondare dimensioni al multiplo superiore senza overflow con `ckd_add`.
- [ ] So implementare un allocatore ad arena su buffer statico con allineamento, reset in tempo costante e marche di salvataggio e ripristino.
- [ ] So implementare un allocatore a pool generico con lista libera gestita tramite `memcpy`, controllo di appartenenza via `uintptr_t` e rilevamento della doppia liberazione.
- [ ] So progettare `struct` con campo array flessibile calcolandone la dimensione con `offsetof` e implementare un allocatore con lista libera dotato di first-fit, splitting e coalescing.
- [ ] So spiegare strict aliasing e `restrict`, reinterpretare bit in modo portabile con `memcpy` e usare canarini di confine e poisoning per diagnosticare corruzioni della memoria.
