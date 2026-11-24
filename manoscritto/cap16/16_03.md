## 16.3 Ordinare e cercare qualsiasi tipo con `qsort` e `bsearch`

Nel capitolo 8 hai implementato a mano un algoritmo di ordinamento elementare e una ricerca binaria su un array di interi. Quando però il programma cresce e devi ordinare strutture di clienti, elenchi di parole o array di misure in virgola mobile, riscrivere ogni volta l'ordinamento e la ricerca binaria sarebbe lento e rischioso. La libreria standard C mette a disposizione in `<stdlib.h>` due funzioni generiche basate esattamente sul modello appena visto (`void *`, dimensione dell'elemento e callback): `qsort` per ordinare sul posto e `bsearch` per eseguire la ricerca binaria.

### Ordinare sul posto con `qsort`

La firma di `qsort` in `<stdlib.h>` è:

<!-- cod: id=16.3-b tipo=frammento -->
```c
void qsort(void *base, size_t nmemb, size_t size,
           int (*compar)(const void *, const void *));
```

I quattro parametri hanno un significato diretto:

- `base`: puntatore al primo elemento dell'array da ordinare;
- `nmemb`: numero di elementi dell'array;
- `size`: dimensione in byte di un singolo elemento (tipicamente `sizeof(array[0])` o `sizeof(*base)`);
- `compar`: puntatore a funzione del **comparatore**, una callback che decide l'ordine tra due elementi.

`qsort` non conosce il tipo degli elementi: sposta blocchi di `size` byte direttamente dentro l'array `base` (ordinamento sul posto) e, ogni volta che ha bisogno di sapere se un elemento viene prima o dopo un altro, chiama `compar(a, b)` passando gli indirizzi dei due elementi come `const void *`.

### Scrivere comparatori sicuri: il contratto e la trappola della sottrazione

Il comparatore deve rispettare un contratto preciso: restituire un `int` **minore di zero** se `*a` precede `*b`, **zero** se i due elementi sono equivalenti secondo il criterio scelto, oppure **maggiore di zero** se `*a` segue `*b`. Inoltre l'ordinamento definito dal comparatore deve essere coerente (un ordinamento totale stretto debole: se `a < b` allora `b > a`, e se `a < b` e `b < c` allora `a < c`). Un comparatore incoerente provoca **comportamento indefinito** in `qsort` e `bsearch`.

Molti esempi datati che circolano in rete scrivono il comparatore per due interi `int` usando una sottrazione:

<!-- cod: id=16.3-c tipo=frammento -->
```c
// ERRORE: MAI scrivere un comparatore cosi'!
int cmp_int_sbagliato(const void *a, const void *b) {
    const int *pa = a;
    const int *pb = b;
    return *pa - *pb;  // overflow con segno -> comportamento indefinito!
}
```

> **Attenzione — Comportamento indefinito**: non usare MAI la sottrazione `*pa - *pb` dentro un comparatore. Il motivo vale per tre famiglie di tipi diverse:
> 1. **Interi con segno** (`int`, `int32_t`): se `*pa` vale `INT_MIN` (`-2147483648`) e `*pb` vale `1`, la sottrazione va in overflow con segno, che in C è **comportamento indefinito** (e in pratica ribalta il segno del risultato, rovinando l'ordinamento).
> 2. **Interi senza segno** (`unsigned int`, `size_t`): la sottrazione avvolge modulo $2^N$ e non può mai produrre un risultato negativo se non convertita con cura, causando wraparound errati.
> 3. **Virgola mobile** (`double`, `float`): `return (int)(*pa - *pb);` tronca differenze piccole come `0.3 - 0.1 = 0.2` a `0`, facendo credere a `qsort` che due numeri diversi siano uguali!

Il modo corretto, sicuro per qualsiasi tipo numerico (`int`, `int32_t`, `size_t`, `double`) e privo di overflow, consiste nel confrontare direttamente con `>` e `<`:

<!-- cod: id=16.3-d tipo=frammento -->
```c
int cmp_int_sicuro(const void *a, const void *b) {
    const int *pa = a;
    const int *pb = b;
    return (*pa > *pb) - (*pa < *pb);
}
```

Osserva l'espressione `(*pa > *pb) - (*pa < *pb)`: poiché i confronti relazionali in C valgono `1` oppure `0`, l'espressione restituisce sempre esattamente `1` se `*pa > *pb`, `-1` se `*pa < *pb` e `0` se `*pa == *pb`, senza alcun rischio di overflow né di troncamento. Per ordinare in senso decrescente basta invertire gli operandi: `(*pb > *pa) - (*pb < *pa)`.

### Criteri multipli e chiave secondaria di spareggio

Quando ordini un array di `struct` (per esempio record di studenti o articoli di un catalogo), capita spesso che due elementi abbiano lo stesso valore sul criterio principale (per esempio lo stesso anno o lo stesso punteggio). Lo standard C23 stabilisce che l'ordine relativo degli elementi equivalenti dopo `qsort` è **comportamento non specificato**: `qsort` non è garantito stabile. Per ottenere un ordine completamente deterministico su qualsiasi compilatore e sistema operativo, conviene strutturare il comparatore in cascata aggiungendo una chiave secondaria univoca di spareggio (*tie-breaker*): confronti prima il criterio principale; se il risultato è diverso da `0` lo restituisci subito, altrimenti passi al criterio successivo fino a una chiave univoca (come un codice identificativo).

### L'insidia degli array di stringhe (`const char *nomi[]`)

Una trappola molto frequente riguarda gli array di stringhe dichiarati come `const char *nomi[]`. Ogni elemento dell'array **non** è un `char`, bensì un puntatore `const char *` alla prima lettera della stringa. Poiché `qsort` passa al comparatore gli *indirizzi degli elementi dell'array*, i parametri `a` e `b` puntano a puntatori: il loro tipo reale è `const char *const *` (un puntatore a puntatore, capitolo 14), non `const char *`.

```text
nomi[0] (const char *) ──▶ "mela\0"
  ▲
  │
  a (const void * ──▶ const char *const *)
```

Se convertissi erroneamente `a` in `const char *` e lo passassi direttamente a `strcmp`, staresti confrontando i byte dell'indirizzo del puntatore invece dei caratteri della stringa (comportamento indefinito). Devi invece convertire a `const char *const *` e dereferenziare una volta:

<!-- cod: id=16.3-e tipo=frammento -->
```c
int cmp_stringhe(const void *a, const void *b) {
    const char *const *sa = a;
    const char *const *sb = b;
    return strcmp(*sa, *sb);
}
```

### Ricerca binaria generica con `bsearch`

Una volta ordinato l'array, puoi cercare un elemento in tempo logaritmico con `bsearch` (`<stdlib.h>`):

<!-- cod: id=16.3-f tipo=frammento -->
```c
void *bsearch(const void *key, const void *base, size_t nmemb, size_t size,
              int (*compar)(const void *, const void *));
```

`bsearch` riceve l'indirizzo della chiave cercata (`key`), l'array ordinato (`base`, `nmemb`, `size`) e il comparatore `compar`. Restituisce l'indirizzo dell'elemento trovato, oppure `nullptr` se la chiave non è presente.

Perché la chiamata sia corretta devi rispettare quattro regole:

1. **Precondizione di ordinamento**: l'array `base` deve essere già ordinato secondo lo **stesso** comparatore (o uno strettamente compatibile) passato a `bsearch`. Chiamare `bsearch` su un array non ordinato provoca **comportamento indefinito**.
2. **Chiave con il tipo dell'elemento**: `bsearch` passa `key` come primo argomento al comparatore; se cerchi una `struct` per codice, prepara una `struct` chiave con quel campo valorizzato; se cerchi in `const char *nomi[]`, passa l'indirizzo di una variabile `const char *chiave = "...";` (`&chiave`), così che il comparatore riceva `const char *const *`.
3. **Protezione del caso `nmemb == 0` e puntatore `base` nullo**: proprio come per le funzioni `mem*` del capitolo 15, evita di passare `nullptr` come `base` a `qsort` o `bsearch` anche quando `nmemb == 0` (può provocare comportamento indefinito). Proteggi sempre le chiamate con `if (nmemb > 0)` quando il puntatore dinamico potrebbe essere `nullptr`.
4. **Elementi equivalenti**: se nell'array compaiono più elementi equivalenti alla chiave, quale di essi restituisca `bsearch` è **comportamento non specificato**.

> **C23 — Preservazione di `const` in `bsearch`**
> Prima del C23, `bsearch` restituiva sempre un `void *` non qualificato anche quando `base` era `const void *`, costringendo a fare attenzione a non modificare per errore un array costante. In C23 `bsearch` è una funzione generica sul tipo (come `memchr` vista nel capitolo 15): se passi un puntatore a dati `const` (per esempio `const char *const *` o `const libro_t *`), il puntatore restituito preserva la qualificazione `const`, impedendo modifiche accidentali. Con compilatori C17 o precedenti, `bsearch` restituisce comunque `void *`, che si assegna senza problemi a un puntatore `const T *` (ma il compilatore non ti impedirebbe di assegnarlo a un `T *` non `const`).

> **Se vieni da Python** — In Python `list.sort(key=...)` è garantito stabile e accetta una funzione che estrae la chiave di confronto; in C `qsort` ordina sul posto usando un comparatore che confronta coppie di `const void *` e la stabilità non è garantita dallo standard, per cui conviene inserire uno spareggio univoco nel comparatore.

### Esempio guidato

Il programma seguente ordina con `qsort` prima un array di `int` che include gli estremi `INT_MIN` e `INT_MAX` (dove la sottrazione fallirebbe con overflow), poi un array di stringhe `const char *` mostrando il doppio livello di indirezione `const char *const *`. Infine cerca alcune parole nell'array ordinato con `bsearch`, assegnando il risultato a `const char *const *` per sfruttare la preservazione di `const` in C23.

<!-- cod: id=16.3-a tipo=programma -->
```c
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int cmp_int(const void *a, const void *b) {
    const int *pa = a;
    const int *pb = b;
    return (*pa > *pb) - (*pa < *pb);
}

int cmp_stringhe(const void *a, const void *b) {
    const char *const *sa = a;
    const char *const *sb = b;
    return strcmp(*sa, *sb);
}

int main(void) {
    int numeri[] = {42, INT_MAX, -7, INT_MIN, 0};
    constexpr size_t n_num = sizeof(numeri) / sizeof(numeri[0]);
    qsort(numeri, n_num, sizeof(numeri[0]), cmp_int);

    printf("Interi ordinati:");
    for (size_t i = 0; i < n_num; ++i) {
        printf(" %d", numeri[i]);
    }
    printf("\n");

    const char *parole[] = {"rete", "albero", "grafo", "codice", "pila"};
    constexpr size_t n_par = sizeof(parole) / sizeof(parole[0]);
    qsort(parole, n_par, sizeof(parole[0]), cmp_stringhe);

    printf("Parole ordinate:");
    for (size_t i = 0; i < n_par; ++i) {
        printf(" %s", parole[i]);
    }
    printf("\n");

    // Vista const: in C23 bsearch restituisce un puntatore const
    const char *const *vista = parole;
    const char *query[] = {"grafo", "coda", "albero"};
    constexpr size_t n_query = sizeof(query) / sizeof(query[0]);

    for (size_t i = 0; i < n_query; ++i) {
        const char *chiave = query[i];
        const char *const *trovato = bsearch(&chiave, vista, n_par,
                                             sizeof(vista[0]), cmp_stringhe);
        if (trovato != nullptr) {
            ptrdiff_t pos = trovato - vista;
            printf("Cerca '%s': trovato in posizione %td\n", chiave, pos);
        } else {
            printf("Cerca '%s': non trovato\n", chiave);
        }
    }

    return 0;
}
```

```output
Interi ordinati: -2147483648 -7 0 42 2147483647
Parole ordinate: albero codice grafo pila rete
Cerca 'grafo': trovato in posizione 2
Cerca 'coda': non trovato
Cerca 'albero': trovato in posizione 0
```

Osserva i dettagli più istruttivi dell'esempio:

- `cmp_int` usa `(*pa > *pb) - (*pa < *pb)`, gestendo senza alcun overflow il confronto tra `INT_MIN` e `INT_MAX`.
- In `cmp_stringhe`, i parametri `a` e `b` sono convertiti in `const char *const *` e dereferenziati come `*sa` e `*sb` prima di essere passati a `strcmp`.
- Nella chiamata a `bsearch`, passiamo `&chiave` (indirizzo di una variabile `const char *`), non `chiave` direttamente, in modo che il primo argomento ricevuto da `cmp_stringhe` abbia esattamente lo stesso livello di indirezione degli elementi di `vista`.
- Poiché `vista` ha tipo `const char *const *`, in C23 `bsearch` restituisce un puntatore qualificato `const`, e `trovato - vista` (aritmetica dei puntatori con `ptrdiff_t`, capitolo 10) fornisce l'indice esatto dell'elemento trovato.

> **Approfondimento — Stabilità di `qsort` e comportamento non specificato**
> Nonostante il nome richiami *quicksort*, lo standard C non impone quale algoritmo interno debba usare `qsort`: un'implementazione può usare quicksort, mergesort, introsort o un ibrido scelto in base alla dimensione dell'array. Poiché quicksort e introsort non sono algoritmi stabili, due elementi che il comparatore considera equivalenti (valore di ritorno `0`) possono scambiarsi di posto in modo diverso a seconda del sistema operativo o della versione della libreria standard. Quando desideri che l'ordine finale sia identico su tutte le piattaforme, aggiungi sempre nel comparatore un criterio di spareggio univoco.

### Esercizio 16.3 — Catalogo di libri con ordinamento multi-criterio (`qsort`) e ricerca binaria (`bsearch`)

**Descrizione**

Scrivi un programma C che definisca `typedef struct libro { int32_t codice; char titolo[32]; int32_t anno; int32_t pagine; } libro_t;` e implementi tre comparatori conformi a `qsort` e `bsearch` (`<stdlib.h>`), senza mai usare sottrazioni tra interi che possano causare overflow (usando sempre confronti sicuri come `(x > y) - (x < y)`): (1) `int cmp_per_anno_pagine(const void *a, const void *b)` che ordina per `anno` crescente, a parità per `pagine` decrescente e a parità per `codice` crescente; (2) `int cmp_per_titolo(const void *a, const void *b)` che ordina lessicograficamente per `titolo` (`strcmp`) e a parità per `codice` crescente; (3) `int cmp_per_codice(const void *a, const void *b)` che ordina per `codice` crescente. In `main` leggi dalla prima riga `n` (`0 <= n <= 64`) e dalle successive `n` righe `<codice> <titolo_senza_spazi> <anno> <pagine>` (con codici distinti che possono raggiungere anche `INT32_MIN` e `INT32_MAX`), allocando l'array con `calloc` quando `n > 0`. Leggi poi `q` (`0 <= q <= 16`) e `q` codici `int32_t` da cercare. Ordina l'array con `qsort` usando `cmp_per_anno_pagine` e stampalo; ordinalo poi con `cmp_per_titolo` e stampalo; infine ordinalo con `cmp_per_codice` e risolvi ogni query chiamando `bsearch` su un puntatore `const libro_t *vista = catalogo;` (sfruttando la preservazione di `const` in C23 per assegnare il risultato a `const libro_t *`, e proteggendo il caso `n == 0` senza chiamare `qsort` o `bsearch` su `nullptr`). Libera tutta la memoria allocata prima di uscire.

**Concetti da tenere a mente**

- comparatori sicuri per `qsort` e `bsearch` senza sottrazioni a rischio overflow
- ordinamento multi-criterio con chiave univoca di spareggio (*tie-breaker*)
- precondizione di ordinamento di `bsearch` coerente con lo stesso comparatore usato in `qsort`
- preservazione della qualificazione `const` nel valore restituito da `bsearch` in C23
- protezione del caso `n == 0` per non passare `nullptr` a `qsort` o `bsearch`

**Domande guida**

1. Perché scrivere `return la->codice - lb->codice;` in `cmp_per_codice` fallirebbe con comportamento indefinito quando un libro ha codice `INT32_MIN` e un altro `INT32_MAX`?
2. Perché è utile aggiungere il confronto sul campo univoco `codice` come ultimo spareggio in `cmp_per_anno_pagine` e `cmp_per_titolo`?
3. Che cosa succederebbe se chiamassi `bsearch` con `cmp_per_codice` subito dopo aver ordinato il catalogo con `cmp_per_titolo`?
4. In che modo il caso `n == 0` va gestito prima di invocare `qsort` e `bsearch`?

**Esempio di esecuzione**

```input
4
103 Algoritmi 2020 450
101 Reti 2018 320
104 Sistemi 2020 600
102 Compilatori 2020 450
3
104
999
101
```

```output
Ordinati per anno/pagine:
  [#101] Reti (2018, 320 pag)
  [#104] Sistemi (2020, 600 pag)
  [#102] Compilatori (2020, 450 pag)
  [#103] Algoritmi (2020, 450 pag)
Ordinati per titolo:
  [#103] Algoritmi (2020, 450 pag)
  [#102] Compilatori (2020, 450 pag)
  [#101] Reti (2018, 320 pag)
  [#104] Sistemi (2020, 600 pag)
Cerca 104: TROVATO Sistemi (2020, 600 pag)
Cerca 999: NON TROVATO
Cerca 101: TROVATO Reti (2018, 320 pag)
```
