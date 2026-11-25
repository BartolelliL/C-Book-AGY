## 22.1 Allineamento in pratica con `alignas` e `max_align_t`

Nel capitolo 13 hai incontrato i concetti di **allineamento** e **padding** e hai usato l'operatore `alignof` per interrogare il requisito di allineamento di un tipo. Fino a questo punto, però, ti sei limitato a *osservare* le scelte del compilatore: potevi riordinare i campi di una `struct` per sprecare meno byte, ma non avevi ancora uno strumento per *imporre* un allineamento specifico a una variabile, a un campo o a un buffer di memoria grezza.

Quando costruisci un allocatore personalizzato, questa possibilità diventa indispensabile. Immagina di riservare un buffer statico di byte da cui distribuire in seguito variabili `int64_t`, `double` o intere `struct`. Se dichiari semplicemente `static unsigned char buffer[1024];`, il tipo `unsigned char` ha allineamento `1`: il compilatore è perfettamente libero di collocare `buffer` a un indirizzo dispari, come `0x1001`. Se il tuo allocatore consegnasse quell'indirizzo iniziale per memorizzarvi un `double` (che su molte piattaforme richiede un indirizzo multiplo di 8), violeresti il vincolo di allineamento.

Per imporre un allineamento esplicito il C23 mette a disposizione lo specificatore `alignas`. Puoi passargli un tipo (`alignas(double)`) oppure un'espressione intera costante positiva che sia una potenza di due (`alignas(16)`, `alignas(64)`). La sua regola è precisa:

- `alignas` rafforza il requisito di allineamento di un oggetto o di un campo di `struct`, ma **non può mai ridurlo** al di sotto dell'allineamento naturale del tipo (per esempio scrivere `alignas(1) double x;` è un errore di compilazione).
- `alignas` può essere applicato a variabili e a campi di `struct` o `union`, ma **non** a `typedef`, parametri di funzione o campi di bit.
- Un allineamento richiesto da `alignas` uguale a `0` viene ignorato.

> **C23** — In C23 `alignas` e `alignof` sono parole chiave native del linguaggio e non richiedono alcun header. Nei compilatori più vecchi (C11/C17) si usavano le parole chiave `_Alignas` e `_Alignof`, oppure le macro `alignas` e `alignof` definite nell'header `<stdalign.h>`, che in C23 è superato e non va incluso.

Ma quale allineamento devi scegliere se il tuo buffer deve poter ospitare *qualsiasi* tipo standard del C, senza sapere in anticipo quale? Qui entra in gioco `max_align_t`, un tipo definito in `<stddef.h>`. Il suo requisito di allineamento, espresso da `alignof(max_align_t)`, rappresenta il **più grande allineamento fondamentale** supportato dalla piattaforma (spesso 8 o 16 byte sulle architetture moderne). È esattamente la stessa garanzia offerta da `malloc`, `calloc` e `realloc`: ogni blocco restituito da queste funzioni è allineato almeno a `alignof(max_align_t)`, risultando quindi adatto a qualunque oggetto con allineamento fondamentale.

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
