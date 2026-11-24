# Capitolo 25 — Qualità e prestazioni

> **In questo capitolo imparerai a:**
> - Confrontare algoritmi contando le operazioni elementari e conoscere i limiti delle misure temporali con `clock`
> - Progettare disposizioni di dati favorevoli alla cache scegliendo tra array di struct e struct di array
> - Spiegare come le ottimizzazioni del compilatore interagiscono con il comportamento indefinito
> - Costruire un mini framework di test automatici con macro ed eseguire prove con input casuali a seme fisso

> **Ti servono:** i capitoli 13 (allineamento e `padding`), 19 (compilazione separata e tipi opachi), 21 (`assert`, `<stdckdint.h>`, `volatile` e sanitizer), 22 (`strict aliasing`), 23 (complessità asintotica e notazione O) e 24 (macro `do-while(0)` e operatore `#`).

Scrivere un programma C che compila senza errori e supera un paio di prove a mano è solo metà del lavoro. Quando il programma cresce su più file — come accadrà nel progetto finale (lo vedremo nel capitolo 26) — servono due qualità che vanno di pari passo: la **correttezza verificabile** nel tempo e **prestazioni** all'altezza del linguaggio che stai usando. Un codice veloce ma pieno di comportamento indefinito si rompe non appena cambi livello di ottimizzazione; un codice corretto ma lento o privo di verifiche automatiche diventa fragile a ogni modifica.

In questo capitolo imparerai a ragionare sulle prestazioni con rigore scientifico. Partirai dal conteggio deterministico delle operazioni elementari e dall'uso consapevole di `clock()`, per poi scendere al livello dell'hardware e capire come la disposizione dei dati in memoria influenzi la cache del processore. Vedrai inoltre in che modo il compilatore trasforma il tuo codice quando attivi `-O2` o `-O3`, e perché qualunque comportamento indefinito annulla ogni garanzia sulle sue ottimizzazioni.

Nella seconda parte del capitolo costruirai gli strumenti di verifica che userai ogni giorno in C: un piccolo framework di test automatici basato su macro riutilizzabili e una tecnica di verifica con input casuali riproducibili, da affiancare a sanitizer, debugger e profiler per individuare i difetti prima ancora che raggiungano l'utente.

## 25.1 Misurare il costo: contare le operazioni e usare `clock`

Nel capitolo 23 hai imparato a classificare gli algoritmi con la complessità asintotica e la notazione O. Sapere che un algoritmo è `O(n log n)` e un altro è `O(n^2)` ti dice come si comportano al crescere di `n`, ma non racconta tutta la storia: due algoritmi con la stessa complessità asintotica possono differire per un fattore costante importante, e un algoritmo `O(n^2)` nel caso peggiore può risultare molto più rapido di uno `O(n log n)` quando i dati in ingresso sono quasi ordinati. Per scegliere con cognizione di causa, devi misurare.

La tentazione immediata è cronometrare il programma con un orologio. Prima di farlo, però, conviene fermarsi a riflettere: il tempo in secondi dipende dal processore, dalla frequenza variabile (turbo o risparmio energetico), dai programmi aperti in background e dalla risoluzione del timer del sistema operativo. Se vuoi confrontare due algoritmi in modo **riproducibile** e **indipendente dalla macchina**, il primo strumento non è il cronometro, ma il **conteggio delle operazioni elementari**: quanti confronti tra elementi esegue l'algoritmo, quanti spostamenti o copie effettua, quanti accessi in memoria o quante allocazioni richiede.

Questi contatori sono numeri interi esatti: sulla tua macchina, su quella di un compagno o su un server remoto, lo stesso algoritmo sullo stesso input eseguirà esattamente lo stesso numero di confronti e di spostamenti. Inoltre, osservare più metriche insieme — per esempio confronti e spostamenti separatamente — permette di capire il comportamento **adattivo** di un algoritmo: su un array già ordinato o quasi ordinato, un algoritmo di ordinamento per inserzione compie pochissimi confronti e quasi nessuno spostamento, mentre su un array in ordine inverso il numero di operazioni cresce quadraticamente.

Quando invece vuoi stimare il tempo reale di elaborazione speso dal processore, la libreria standard mette a disposizione l'intestazione `<time.h>`, che definisce:

- il tipo aritmetico `clock_t`, che rappresenta un istante di tempo di CPU;
- la funzione `clock_t clock(void);`, che restituisce il tempo di processore approssimato utilizzato dal programma dall'avvio (oppure `(clock_t)-1` se la misura non è disponibile o non rappresentabile);
- la costante `CLOCKS_PER_SEC`, che indica quante unità di `clock_t` corrispondono a un secondo.

La regola per misurare un intervallo è precisa:

1. Leggi `clock_t inizio = clock();` prima del blocco da misurare e `clock_t fine = clock();` subito dopo.
2. Verifica sempre che né `inizio` né `fine` valgano `(clock_t)-1`.
3. Calcola i secondi di CPU trascorsi con `(double)(fine - inizio) / (double)CLOCKS_PER_SEC`.

Secondo lo standard C23, i nomi `clock`, `clock_t`, `CLOCKS_PER_SEC` e il valore di errore `(clock_t)-1` sono definiti dallo standard, mentre il tipo aritmetico sottostante a `clock_t`, la risoluzione effettiva del timer e il valore numerico di `CLOCKS_PER_SEC` sono **dipendenti dall'implementazione**. Su alcuni sistemi `clock()` avanza a scatti di millisecondi, su altri di microsecondi; inoltre misura il tempo di CPU del processo (non necessariamente il tempo d'orologio reale se il programma rimane in attesa di input).

Ancora più insidiose sono le trappole del micro-benchmarking:

- **Eliminazione del codice morto (*dead-code elimination*)**: se esegui un calcolo in un ciclo ma non usi mai il risultato, il compilatore con `-O2` può dimostrare che il ciclo non produce effetti osservabili e cancellarlo del tutto.
- **Livello di ottimizzazione**: misurare codice compilato con `-O0` non riflette le prestazioni reali. Le ottimizzazioni (`-O2`) trasformano radicalmente i cicli e possono persino invertire il vincitore tra due soluzioni.
- **Durata troppo breve e rumore del sistema**: una singola ricerca su poche migliaia di elementi dura frazioni di microsecondo, al di sotto della risoluzione del timer. Per ottenere una misura sensata con `clock()` occorre ripetere l'operazione molte volte, e comunque non bisogna mai usare un tempo misurato come output atteso di una verifica deterministica.

### Esempio guidato

Il programma seguente confronta la ricerca lineare e la ricerca binaria su un array ordinato di 10 000 interi. Prima raccoglie i contatori esatti di confronti e accessi all'array su quattro chiavi rappresentative (inizio, centro, fine, assente), poi esegue un ciclo di 2 000 iterazioni misurato con `clock()` accumulando i risultati in un checksum e in un pozzo `volatile` per impedire al compilatore di eliminare il ciclo. Per mantenere l'output deterministico su ogni computer, il programma verifica la validità della misura di `clock()` senza stampare i secondi variabili (durante un'analisi locale sulla tua macchina potresti stampare anche `secondi` con `%.6f`).

<!-- cod: id=25.1-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>

typedef struct contatori {
    uint64_t confronti;
    uint64_t accessi;
} contatori_t;

static ptrdiff_t ricerca_lineare(const int32_t *a, size_t n, int32_t chiave,
                                 contatori_t *c) {
    for (size_t i = 0; i < n; ++i) {
        ++c->confronti;
        ++c->accessi;
        if (a[i] == chiave) {
            return (ptrdiff_t)i;
        }
    }
    return -1;
}

static ptrdiff_t ricerca_binaria(const int32_t *a, size_t n, int32_t chiave,
                                 contatori_t *c) {
    size_t sx = 0;
    size_t dx = n;
    while (sx < dx) {
        size_t mid = sx + (dx - sx) / 2;
        ++c->accessi;
        int32_t val = a[mid];
        ++c->confronti;
        if (val == chiave) {
            return (ptrdiff_t)mid;
        }
        ++c->confronti;
        if (val < chiave) {
            sx = mid + 1;
        } else {
            dx = mid;
        }
    }
    return -1;
}

int main(void) {
    constexpr size_t N = 10000;
    static int32_t dati[N];
    for (size_t i = 0; i < N; ++i) {
        dati[i] = (int32_t)(i * 2);
    }

    const int32_t chiavi[4] = {0, 9998, 19998, 19999};
    contatori_t c_lin = {};
    contatori_t c_bin = {};
    ptrdiff_t somma_pos = 0;

    for (size_t k = 0; k < 4; ++k) {
        somma_pos += ricerca_lineare(dati, N, chiavi[k], &c_lin);
        somma_pos += ricerca_binaria(dati, N, chiavi[k], &c_bin);
    }

    printf("Lineare (4 ricerche): confronti=%" PRIu64 " accessi=%" PRIu64 "\n",
           c_lin.confronti, c_lin.accessi);
    printf("Binaria (4 ricerche): confronti=%" PRIu64 " accessi=%" PRIu64 "\n",
           c_bin.confronti, c_bin.accessi);

    clock_t t0 = clock();
    uint64_t checksum = 0;
    contatori_t scarto = {};
    for (size_t rep = 0; rep < 2000; ++rep) {
        ptrdiff_t p = ricerca_binaria(dati, N, chiavi[rep % 4], &scarto);
        checksum += (uint64_t)(p + 2);
    }
    volatile uint64_t pozzo = checksum;
    clock_t t1 = clock();

    bool valida = (CLOCKS_PER_SEC > 0 && t0 != (clock_t)-1 && t1 != (clock_t)-1
                   && (double)(t1 - t0) / (double)CLOCKS_PER_SEC >= 0.0);
    printf("somma_pos=%td checksum=%" PRIu64 " clock_valida=%d\n",
           somma_pos, pozzo, valida ? 1 : 0);
    return 0;
}
```

```output
Lineare (4 ricerche): confronti=25001 accessi=25001
Binaria (4 ricerche): confronti=103 accessi=53
somma_pos=29994 checksum=7502500 clock_valida=1
```

Osserva i numeri prodotti dal programma:

- Su quattro ricerche in un array di 10 000 elementi, la ricerca lineare esegue 25 001 confronti e 25 001 accessi in memoria, mentre la ricerca binaria si ferma a 103 confronti e 53 accessi. Questa differenza è interamente deterministica e non cambia cambiando computer o compilatore.
- Nel ciclo cronometrato con `clock()`, ogni iterazione aggiorna `checksum`, che viene poi copiato nel pozzo `volatile uint64_t pozzo` e stampato. Così il compilatore è obbligato a eseguire davvero tutte le 2 000 ricerche.
- Prima di calcolare `(double)(t1 - t0) / (double)CLOCKS_PER_SEC`, il codice controlla sia `t0 != (clock_t)-1` sia `t1 != (clock_t)-1`, come richiesto dallo standard.

> **C23** — L'esempio usa `constexpr` per la dimensione `N`, l'inizializzatore vuoto `{}` per azzerare le strutture e `bool` senza includere intestazioni aggiuntive. Con compilatori C17 o precedenti si usano `enum { N = 10000 };`, `{0}` e l'intestazione standard dedicata al tipo booleano di C99/C17.

> **Approfondimento — Perché un benchmark può impiegare 0.000 secondi con `-O2`**
> Se scrivi un ciclo che chiama `ricerca_binaria(...)` un milione di volte ignorando il valore restituito, un compilatore con `-O2` osserva che la funzione legge solo memoria costante e non modifica alcun dato osservabile all'esterno. In base alle regole di ottimizzazione, il compilatore può rimuovere l'intero ciclo: il cronometro misurerà `0.000` secondi anche per milioni di iterazioni. Accumulare il risultato in una variabile che viene poi stampata (o assegnata a un pozzo `volatile`) crea un effetto osservabile e impedisce l'eliminazione del ciclo.

### Esercizio 25.1 — Profilatore deterministico di operazioni per algoritmi di ordinamento adattivi e verifica di clock

**Descrizione**

Scrivi un programma C che confronti in modo deterministico tre algoritmi di ordinamento su `int32_t` contando tre metriche esatte dentro `typedef struct metriche_op { uint64_t confronti; uint64_t spostamenti; uint64_t accessi; } metriche_op_t;`: (1) `ordina_inserzione(int32_t *a, size_t n, metriche_op_t *m)` (incrementa `confronti` a ogni verifica `a[j] > chiave`, `spostamenti` a ogni spostamento `a[j + 1] = a[j]`, e `accessi` per ogni lettura/scrittura di un elemento dell'array); (2) `ordina_shell(int32_t *a, size_t n, metriche_op_t *m)` con passi `gap = n / 2; gap > 0; gap /= 2` contando le stesse metriche; (3) `ordina_heap(int32_t *a, size_t n, metriche_op_t *m)` (max-heap sul posto con costruzione bottom-up ed estrazioni successive) contando confronti, scambi (contati come 3 spostamenti / 4 accessi per scambio) e letture di confronto. In `main` gestisci da `stdin` i comandi: `BENCH <modo> <n>` (`1 <= n <= 256`, `<modo>` tra `ORD` crescente `0..n-1`, `REV` decrescente `n-1..0`, `QUASI` crescente con scambio di ogni coppia `(8*k, 8*k+1)` valida) che esegue tutti e tre gli algoritmi su copie identiche, verifica con `memcmp` che i risultati ordinati coincidano esattamente e stampa i contatori di ciascun algoritmo; `CUSTOM <n> <v0> ... <v{n-1}>` (`0 <= n <= 64`) con la stessa verifica; `CLOCK_CHECK` che invoca `clock()` prima e dopo un breve ciclo accumulato in un pozzo `volatile uint64_t` verificando `CLOCKS_PER_SEC > 0`, `t0 != (clock_t)-1`, `t1 != (clock_t)-1` e `(double)(t1 - t0) / (double)CLOCKS_PER_SEC >= 0.0` (senza stampare i secondi fluttuanti), riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- conteggio deterministico di confronti, spostamenti e accessi in memoria come base portabile di profilazione
- comportamento adattivo di Insertion Sort su input ordinati e quasi ordinati rispetto a Shell Sort e Heap Sort
- verifica di correttezza e coincidenza dei tre ordinamenti tramite `memcmp`
- uso corretto di `clock()`, `clock_t` e `CLOCKS_PER_SEC` (`<time.h>`) con pozzo `volatile` contro l'eliminazione del codice morto

**Domande guida**

1. Perché Insertion Sort esegue molti meno confronti di Heap Sort su una sequenza già ordinata o quasi ordinata, ma esplode sulla sequenza inversa?
2. Come mai nel comando `CLOCK_CHECK` si verifica la validità di `clock()` e `CLOCKS_PER_SEC` senza stampare il numero esatto di millisecondi trascorsi?
3. A che cosa serve accumulare il risultato del ciclo di prova in una variabile qualificata `volatile` prima della seconda chiamata a `clock()`?
4. Quale vantaggio offre misurare sia i confronti sia gli spostamenti invece di osservare un solo contatore?

**Esempio di esecuzione**

```input
BENCH ORD 32
BENCH QUASI 8
BENCH REV 8
CUSTOM 5 9 1 4 1 7
CLOCK_CHECK
```

```output
BENCH ORD(32) ok=1:
  INS:   cmp=31 mov=0 acc=62
  SHELL: cmp=129 mov=0 acc=258
  HEAP:  cmp=231 mov=438 acc=1046
BENCH QUASI(8) ok=1:
  INS:   cmp=7 mov=1 acc=17
  SHELL: cmp=17 mov=1 acc=37
  HEAP:  cmp=27 mov=63 acc=138
BENCH REV(8) ok=1:
  INS:   cmp=28 mov=28 acc=98
  SHELL: cmp=22 mov=12 acc=75
  HEAP:  cmp=24 mov=48 acc=112
CUSTOM(5) ok=1:
  INS:   cmp=8 mov=5 acc=26
  SHELL: cmp=10 mov=5 acc=31
  HEAP:  cmp=10 mov=21 acc=48
CLOCK_CHECK: valido=1
```

## 25.2 Località dei dati e cache: array di struct contro struct di array

Due programmi che eseguono esattamente lo stesso numero di addizioni e di confronti possono avere tempi di esecuzione molto diversi, anche di cinque o dieci volte. La causa quasi sempre non è la velocità del processore nel fare i conti, ma il tempo che il processore passa fermo ad aspettare che i dati arrivino dalla memoria centrale (RAM).

Nei computer moderni, leggere un dato da un registro della CPU richiede meno di un nanosecondo; leggerlo dalla RAM può richiedere circa cento nanosecondi. Per colmare questo divario, tra il processore e la RAM esistono diversi livelli di memoria molto veloce e di dimensioni crescenti, chiamati **cache** (tipicamente L1, L2 e L3):

```text
+-------------------+   ~1 ciclo      (poche decine di byte)
|   Registri CPU    |
+-------------------+
          |
+-------------------+   ~4 cicli      (32-64 KiB per core)
|     Cache L1      |
+-------------------+
          |
+-------------------+   ~12 cicli     (256 KiB - 1 MiB)
|     Cache L2      |
+-------------------+
          |
+-------------------+   ~40 cicli     (diversi MiB condivisi)
|     Cache L3      |
+-------------------+
          |
+-------------------+   ~200+ cicli   (diversi GiB)
|        RAM        |
+-------------------+
```

Quando il programma legge anche un solo byte che non si trova in cache (un *cache miss*), il processore non carica dalla RAM solo quel byte: trasferisce un intero blocco contiguo di memoria chiamato **linea di cache** (*cache line*), tipicamente di 64 byte. Se il dato successivo richiesto dal programma si trova nella stessa linea già caricata, l'accesso avviene in cache (un *cache hit*), decine di volte più velocemente.

Si chiama **località dei dati** (*data locality*) la proprietà di un programma che accede a indirizzi di memoria vicini tra loro, sfruttando efficacemente la cache del processore. Si distinguono due aspetti complementari:

- **Località spaziale**: se accedi a un indirizzo, è probabile che a breve accederai agli indirizzi immediatamente vicini (per esempio scorrendo un array in sequenza).
- **Località temporale**: se accedi a un dato ora, è probabile che lo rileggerai di nuovo a breve (per esempio un accumulatore o una piccola tabella di ricerca).

Questa meccanica ha due conseguenze dirette sul modo in cui scrivi codice C.

La prima riguarda gli array bidimensionali. In C gli array multidimensionali sono memorizzati **per righe** (*row-major*): tutti gli elementi della riga 0 occupano byte consecutivi, seguiti immediatamente dagli elementi della riga 1, e così via. Se scorri una matrice con l'indice di colonna nel ciclo più interno (`m[i][j]` con `j` che varia più rapidamente), ogni linea di cache da 64 byte contiene otto `double` consecutivi che usi tutti prima di passare alla linea successiva. Se invece scorri per colonne (`i` nel ciclo interno), ogni iterazione salta avanti di un'intera riga: su una matrice grande, quasi ogni singolo elemento provoca un *cache miss*, caricando 64 byte dalla RAM per usarne solo 8.

La seconda conseguenza riguarda la disposizione delle collezioni di strutture. Immagina di gestire migliaia di entità geometriche o fisiche, ciascuna con coordinate `x`, `y`, `z` (usate a ogni iterazione di un ciclo caldo) e metadati come un identificativo, uno stato o un nome testuale (letti raramente, quindi **campi freddi**). Hai due modi principali per organizzare questi dati in memoria:

1. **Array di Struct (AoS, *Array of Structures*)**: un singolo array in cui ogni elemento è una `struct` completa. Tutti i campi di uno stesso oggetto sono vicini tra loro, ma in un ciclo che aggiorna solo `x` il processore deve saltare oltre `y`, `z`, i campi freddi e il `padding` per raggiungere la `x` dell'oggetto successivo, trascinando in cache molti byte inutilizzati.
2. **Struct di Array (SoA, *Structure of Arrays*)**: una `struct` che contiene un array contiguo separato per ogni campo (`double *x`, `double *y`, ...). Quando il ciclo aggiorna solo `x`, legge un array compatto di soli `double`: ogni linea di cache da 64 byte porta otto valori utili senza alcuno spreco.

```text
AoS (1 struct = 64 byte -> 1 campo x ogni 64 byte):
[ x0 | y0 | z0 | metadati0 ... ] [ x1 | y1 | z1 | metadati1 ... ]

SoA (array contiguo di x -> 8 campi x in una sola linea da 64 byte):
[ x0 | x1 | x2 | x3 | x4 | x5 | x6 | x7 ]
```

Secondo lo standard C23, la disposizione contigua per righe degli array e l'ordine sequenziale dei campi di una `struct` (salvo il `padding` di allineamento visto nel capitolo 13) sono **definiti**; la dimensione esatta delle linee e la gerarchia delle cache dipendono invece dall'architettura hardware. Per confrontare quantitativamente due layout senza dipendere dal computer o dagli indirizzi fisici, si può simulare in modo deterministico una cache a linee da 64 byte sugli offset logici dei dati (calcolati con `sizeof` e `offsetof`), contando esattamente *hit*, *miss* e byte trasferiti.

> **Se vieni da Python** — In Python ogni numero e ogni oggetto vive sullo heap dietro un riferimento con informazioni di tipo, rendendo l'accesso sparso in memoria; in C scegliere tra AoS e SoA controlla direttamente la disposizione dei byte nelle linee di cache del processore.

### Esempio guidato

Il programma seguente confronta la disposizione AoS e quella SoA per una raccolta di 64 punti 3D dotati di metadati freddi (`id` e una stringa `nome`), verificando con `static_assert` che la `struct` AoS occupi esattamente 64 byte. Stampa le dimensioni, il passo in byte tra due letture consecutive della coordinata `x` e conta quante linee da 64 byte distinte vengono toccate durante un aggiornamento della sola `x`, oltre a confrontare le linee toccate in una scansione per righe contro una per colonne di una matrice contigua `16 x 16` di `double`.

<!-- cod: id=25.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct punto_aos {
    double x;
    double y;
    double z;
    uint64_t id;
    char nome[32];
} punto_aos_t;

static_assert(sizeof(punto_aos_t) == 64);

typedef struct punti_soa {
    double x[64];
    double y[64];
    double z[64];
    uint64_t id[64];
} punti_soa_t;

static size_t conta_cambi_linea(size_t passi, size_t stride_byte, size_t linea) {
    size_t cambi = 0;
    size_t ultima_linea = SIZE_MAX;
    for (size_t i = 0; i < passi; ++i) {
        size_t linea_corr = (i * stride_byte) / linea;
        if (linea_corr != ultima_linea) {
            ++cambi;
            ultima_linea = linea_corr;
        }
    }
    return cambi;
}

int main(void) {
    constexpr size_t N = 64;
    constexpr size_t LINEA = 64;
    static punto_aos_t aos[N];
    static punti_soa_t soa;

    for (size_t i = 0; i < N; ++i) {
        aos[i].x = (double)i;
        soa.x[i] = (double)i;
    }

    double somma_aos = 0.0;
    double somma_soa = 0.0;
    for (size_t i = 0; i < N; ++i) {
        aos[i].x += 1.0;
        soa.x[i] += 1.0;
        somma_aos += aos[i].x;
        somma_soa += soa.x[i];
    }

    size_t passo_aos = sizeof(punto_aos_t);
    size_t passo_soa = sizeof(double);
    size_t linee_aos = conta_cambi_linea(N, passo_aos, LINEA);
    size_t linee_soa = conta_cambi_linea(N, passo_soa, LINEA);

    printf("sizeof(punto_aos_t)=%zu, passo_x AoS=%zu byte, SoA=%zu byte\n",
           sizeof(punto_aos_t), passo_aos, passo_soa);
    printf("Aggiornamento x (64 punti): linee toccate AoS=%zu SoA=%zu (somme %.1f == %.1f)\n",
           linee_aos, linee_soa, somma_aos, somma_soa);

    constexpr size_t R = 16;
    constexpr size_t C = 16;
    size_t cambi_righe = 0;
    size_t cambi_col = 0;
    size_t prev = SIZE_MAX;
    for (size_t i = 0; i < R; ++i) {
        for (size_t j = 0; j < C; ++j) {
            size_t ln = ((i * C + j) * sizeof(double)) / LINEA;
            if (ln != prev) {
                ++cambi_righe;
                prev = ln;
            }
        }
    }
    prev = SIZE_MAX;
    for (size_t j = 0; j < C; ++j) {
        for (size_t i = 0; i < R; ++i) {
            size_t ln = ((i * C + j) * sizeof(double)) / LINEA;
            if (ln != prev) {
                ++cambi_col;
                prev = ln;
            }
        }
    }
    printf("Matrice 16x16 double: cambi linea RIGHE=%zu COLONNE=%zu\n",
           cambi_righe, cambi_col);
    return 0;
}
```

```output
sizeof(punto_aos_t)=64, passo_x AoS=64 byte, SoA=8 byte
Aggiornamento x (64 punti): linee toccate AoS=64 SoA=8 (somme 2080.0 == 2080.0)
Matrice 16x16 double: cambi linea RIGHE=32 COLONNE=256
```

Analizza il risultato:

- Per aggiornare soltanto `x` su 64 punti, il layout AoS avanza di 64 byte a ogni passo e tocca 64 linee di cache diverse (4 096 byte caricati per usare 512 byte di `double`), mentre il layout SoA avanza di 8 byte e tocca appena 8 linee (512 byte, cioè otto volte meno traffico di memoria).
- Nella matrice `16 x 16` di `double` (256 elementi, 2 048 byte totali = 32 linee da 64 byte), la scansione per righe cambia linea solo 32 volte (una ogni 8 elementi), mentre la scansione per colonne cambia linea a ogni singolo accesso (256 volte).

> **C23** — L'esempio usa `static_assert` con un solo argomento (senza messaggio obbligatorio), introdotto in C23; in C11/C17 occorre fornire anche la stringa di messaggio, per esempio `static_assert(sizeof(punto_aos_t) == 64, "attesi 64 byte");`.

> **Approfondimento — Quando AoS è meglio di SoA**
> AoS non è sempre inferiore a SoA. Quando il tuo programma accede a un singolo record scelto in modo casuale — per esempio cercando un utente per chiave in una tabella hash — e legge quasi tutti i suoi campi insieme (`x`, `y`, `z`, `id`, `nome`), il layout AoS tiene tutti i campi di quel record nella stessa linea di cache (un solo miss). Con SoA, invece, leggere cinque campi dello stesso oggetto richiederebbe di toccare cinque array diversi e quindi fino a cinque linee di cache separate. La scelta dipende sempre dal profilo di accesso prevalente.

### Esercizio 25.2 — Confronto quantitativo AoS contro SoA e scansione di matrici tramite simulatore deterministico di cache

**Descrizione**

Realizza su tre file (`cache_sim.h`, `cache_sim.c`, `main.c`) un simulatore deterministico di **cache** LRU a `16` linee da `64` byte (per operare su offset logici indipendenti dagli indirizzi fisici) e usalo per misurare la **località dei dati** tra **Array di Struct (AoS)**, **Struct di Array (SoA)** e scansione di matrici per righe contro per colonne. (1) In `cache_sim.h` (protetto da `CACHE_SIM_H`) definisci `constexpr size_t CACHE_LINEA = 64;` e `constexpr size_t CACHE_LINEE = 16;`, la struttura `cache_sim_t` con `hits`, `misses` e `byte_trasferiti` (`misses * 64`), e dichiara `void cache_reset(cache_sim_t *c);` e `void cache_accedi(cache_sim_t *c, uint64_t offset_byte);` (aggiorna la linea LRU per il blocco `offset_byte / 64`). (2) In `main.c` definisci `typedef struct particella_aos { double x, y, vx, vy; uint64_t id; uint32_t stato, gruppo; char etichetta[16]; } particella_aos_t;` verificando con `static_assert(sizeof(particella_aos_t) == 64)` che ogni particella occupi esattamente una linea di cache, e `particelle_soa_t` con array separati allocati dinamicamente (`x, y, vx, vy, id, stato, gruppo`). Gestisci da `stdin` i comandi: `STEP <n> <dt>` (`1 <= n <= 512`, inizializza le particelle deterministicamente `x=i, y=2*i, vx=1.5, vy=-0.5, stato=i%4`, esegue `x += vx*dt; y += vy*dt;` sia in AoS sia in SoA registrando gli offset logici in `cache_sim_t`, verifica che le somme finali coincidano e stampa hits, misses e byte trasferiti per AoS e SoA); `FILTRA <n> <stato_req>` (conta le particelle con `stato == stato_req` confrontando AoS e SoA nella cache); `MATRICE <r> <c>` (`1 <= r, c <= 64`, confronta la somma di una matrice `r x c` di `double` per righe contro per colonne tramite `cache_sim_t`). Riproduci esattamente l'output dell'esempio senza perdite di memoria.

**Concetti da tenere a mente**

- linee di cache da 64 byte e trasferimento di interi blocchi contigui dalla RAM
- differenza di località spaziale tra AoS (campi caldi mescolati a campi freddi) e SoA (array contigui omogenei)
- scansione row-major (per righe) contro col-major (per colonne) sulle matrici in C
- uso di `offsetof` e offset logici per simulare la cache in modo deterministico e indipendente dagli indirizzi fisici

**Domande guida**

1. Perché nel comando `FILTRA` su 64 particelle la versione AoS causa 64 cache miss mentre la versione SoA ne causa soltanto 4?
2. Quale differenza osservi nel rapporto tra i byte trasferiti di AoS e SoA passando da `STEP` (che legge 32 byte utili per particella) a `FILTRA` (che legge solo 4 byte utili)?
3. Perché nella scansione di una matrice 32x32 di `double` il percorso per colonne provoca un cache miss a ogni elemento quando la cache contiene solo 16 linee da 64 byte?
4. In quale caso d'uso reale il layout AoS risulterebbe invece più conveniente del layout SoA?

**Esempio di esecuzione**

```input
STEP 64 0.5
FILTRA 64 2
MATRICE 32 32
```

```output
STEP(64) ok=1:
  AoS: hits=192 misses=64 byte=4096
  SoA: hits=224 misses=32 byte=2048
FILTRA(64, 2) cnt=16 ok=1:
  AoS: hits=0 misses=64 byte=4096
  SoA: hits=60 misses=4 byte=256
MATRICE(32x32) ok=1:
  RIGHE:   hits=896 misses=128 byte=8192
  COLONNE: hits=0 misses=1024 byte=65536
```

## 25.3 Ottimizzazioni del compilatore e comportamento indefinito

Quando compili un programma C puoi scegliere il livello di ottimizzazione: `-O0` (nessuna ottimizzazione, utile per il debug passo-passo), `-O2` (ottimizzazioni standard per la produzione), `-O3` (ottimizzazioni più aggressive, inclusa la vettorizzazione dei cicli) e `-Os` (ottimizzazione per ridurre la dimensione dell'eseguibile). Con `-O2` e `-O3`, il compilatore non si limita a tradurre riga per riga il tuo sorgente: applica decine di trasformazioni sofisticate, tra cui:

- **Propagazione di costanti**: sostituisce a tempo di compilazione le espressioni i cui operandi sono noti.
- **Inlining**: inserisce il corpo di una piccola funzione direttamente nel punto di chiamata, eliminando il costo della chiamata e aprendo ulteriori semplificazioni.
- **Spostamento di invarianti di ciclo**: porta fuori da un ciclo i calcoli che producono lo stesso risultato a ogni iterazione.
- **Eliminazione di codice morto**: rimuove variabili, rami o interi cicli i cui effetti non sono osservabili.
- **Vettorizzazione**: trasforma un ciclo scalare in istruzioni hardware che elaborano più elementi contemporaneamente.

Tutte queste trasformazioni si basano su un principio dello standard C23 chiamato **regola "as-if"**: il compilatore può riordinare, trasformare o eliminare codice liberamente, purché il comportamento osservabile (output, accessi `volatile`, interazioni con il sistema) di un programma *privo di comportamento indefinito* resti identico a quello descritto dallo standard.

Qui nasce l'interazione più insidiosa del C moderno. Poiché lo standard autorizza il compilatore ad **assumere che nessun comportamento indefinito si verifichi mai** in un'esecuzione valida, il compilatore usa questa ipotesi per dimostrare proprietà sul tuo codice. Se scrivi un controllo *dopo* un'operazione che può già provocare comportamento indefinito, il compilatore può eliminarlo silenziosamente:

- **Controllo post-overflow su interi con segno**: se `x` è `int`, l'espressione `x + 1` non può andare in overflow in un programma valido. Il compilatore dimostra quindi che `x + 1 < x` è *sempre falso* ed elimina il ramo `if (x + 1 < x)`!
- **Controllo `nullptr` dopo la dereferenziazione**: se prima scrivi `int v = *p;` e solo dopo controlli `if (p == nullptr)`, il compilatore deduce che, poiché `*p` è stato dereferenziato senza UB, `p` non può essere `nullptr`, quindi elimina interamente il controllo `if (p == nullptr)`.

Lo stesso vale per gli spostamenti di bit fuori intervallo (per esempio spostare un `uint32_t` di 32 posizioni o di un numero negativo è comportamento indefinito anche sui tipi senza segno), per le violazioni di **strict aliasing** (capitolo 22) e per la violazione del contratto di `restrict` (capitolo 14). Secondo lo standard C23, la regola *as-if*, `<stdckdint.h>`, `memcpy` e il contratto di `restrict` sono definiti, ma la presenza di **qualsiasi comportamento indefinito** annulla ogni garanzia del compilatore sull'intera esecuzione.

Per scrivere codice che sia al tempo stesso veloce e sicuro sotto `-O2` e `-O3`, segui quattro regole pratiche in C23:

1. **Overflow controllato con `<stdckdint.h>`**: invece di fare la somma e controllare dopo, usa `ckd_add(&ris, a, b)`, `ckd_sub(&ris, a, b)` e `ckd_mul(&ris, a, b)` (introdotti nel capitolo 21). Restituiscono `false` se il risultato è esatto e `true` in caso di overflow, senza mai causare UB e compilando in pochissime istruzioni macchina.
2. **Shift sicuri su tipi senza segno**: controlla sempre `k >= 0 && k < 32` (per `uint32_t`, o `< 64` per `uint64_t`) prima di applicare `<<` o `>>`.
3. **Reinterpretazione dei bit con `memcpy` + `static_assert`**: per leggere i bit di un `float` come `uint32_t`, non scrivere `*(const uint32_t *)&f` (viola strict aliasing); usa `memcpy(&u, &f, sizeof(u))` con `static_assert(sizeof(float) == sizeof(uint32_t))`. Con `-O2` il compilatore trasforma quella `memcpy` di 4 byte in una singola istruzione di registro, zero chiamate a funzione e zero UB.
4. **`restrict` protetto**: qualificare i puntatori di un kernel numerico con `restrict` informa il compilatore che le aree di memoria non si sovrappongono, permettendogli di vettorizzare il ciclo e tenere i valori nei registri. Se il chiamante non può garantire la disgiunzione, proteggi la chiamata con un wrapper che controlla l'eventuale sovrapposizione degli intervalli tramite `uintptr_t`, invocando la versione `restrict` solo quando le aree sono davvero disgiunte e ricorrendo altrimenti a un buffer temporaneo.

> **C23** — L'intestazione `<stdckdint.h>` (`ckd_add`, `ckd_sub`, `ckd_mul`) è una novità di C23. Con compilatori più vecchi si devono scrivere controlli preventivi con `INT32_MAX`/`INT32_MIN` prima di eseguire l'operazione aritmetica.

> **Se vieni da Python** — In Python l'aritmetica intera ha precisione arbitraria e non va in overflow, mentre un accesso fuori dai limiti solleva sempre `IndexError`; in C l'overflow con segno e i puntatori invalidi sono comportamento indefinito che il compilatore può sfruttare in modo aggressivo durante l'ottimizzazione.

### Esempio guidato

Osserva prima due brevi frammenti **errati**: contengono comportamento indefinito e non vanno mai scritti in un programma reale.

> **Attenzione — Frammenti con comportamento indefinito (da non scrivere mai)**
> Nei due frammenti seguenti il compilatore con `-O2` può eliminare entrambi gli `if`, perché i controlli avvengono *dopo* un potenziale comportamento indefinito (overflow con segno nel primo caso, dereferenziazione di puntatore nullo nel secondo).

<!-- cod: id=25.3-b tipo=frammento -->
```c
// ERRORE: overflow con segno (UB); con -O2 il controllo può sparire
int controlla_dopo_ub(int x) {
    if (x + 1 < x) {
        return -1;
    }
    return x + 1;
}
```

<!-- cod: id=25.3-c tipo=frammento -->
```c
// ERRORE: dereferenziazione prima del controllo nullptr (UB)
int leggi_dopo_ub(const int *p) {
    int valore = *p;
    if (p == nullptr) {
        return 0;
    }
    return valore;
}
```

Il programma eseguibile seguente mostra invece le versioni corrette e completamente definite in C23: somma sicura con `ckd_add`, controllo preventivo di `nullptr` prima della dereferenziazione e un kernel vettoriale `scala_e_somma` con `restrict` invocato su array disgiunti (verificati con `uintptr_t`).

<!-- cod: id=25.3-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdckdint.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

static bool incrementa_sicuro(int32_t x, int32_t *out) {
    return !ckd_add(out, x, 1);
}

static int32_t leggi_sicuro(const int32_t *p) {
    if (p == nullptr) {
        return 0;
    }
    return *p;
}

static bool aree_disgiunte(const void *a, const void *b, size_t n_byte) {
    uintptr_t ia = (uintptr_t)a;
    uintptr_t ib = (uintptr_t)b;
    return (ia + n_byte <= ib) || (ib + n_byte <= ia);
}

static void scala_e_somma(size_t n, double *restrict dst,
                          const double *restrict src, double fattore) {
    for (size_t i = 0; i < n; ++i) {
        dst[i] = dst[i] + fattore * src[i];
    }
}

int main(void) {
    int32_t ris = 0;
    bool ok1 = incrementa_sicuro(41, &ris);
    printf("41 + 1 -> ok=%d val=%" PRId32 "\n", ok1 ? 1 : 0, ris);

    bool ok2 = incrementa_sicuro(INT32_MAX, &ris);
    printf("INT32_MAX + 1 -> ok=%d\n", ok2 ? 1 : 0);

    int32_t dato = 99;
    printf("leggi(&dato)=%" PRId32 " leggi(nullptr)=%" PRId32 "\n",
           leggi_sicuro(&dato), leggi_sicuro(nullptr));

    double dst[4] = {1.0, 2.0, 3.0, 4.0};
    const double src[4] = {10.0, 20.0, 30.0, 40.0};
    if (aree_disgiunte(dst, src, sizeof(dst))) {
        scala_e_somma(4, dst, src, 0.5);
    }
    printf("dst=[%.1f, %.1f, %.1f, %.1f]\n", dst[0], dst[1], dst[2], dst[3]);
    return 0;
}
```

```output
41 + 1 -> ok=1 val=42
INT32_MAX + 1 -> ok=0
leggi(&dato)=99 leggi(nullptr)=0
dst=[6.0, 12.0, 18.0, 24.0]
```

Nota come ogni controllo avvenga in modo privo di UB: `incrementa_sicuro` delega a `ckd_add`, `leggi_sicuro` controlla `p == nullptr` *prima* di `*p`, e `scala_e_somma` viene chiamata solo dopo aver verificato che `dst` e `src` siano disgiunti, rispettando il contratto di `restrict`.

> **Approfondimento — Perché un bug di UB può emergere solo con `-O2`**
> Un difetto di comportamento indefinito può restare invisibile per mesi durante lo sviluppo con `-O0` e manifestarsi all'improvviso quando compili con `-O2` per il rilascio. A `-O0` il compilatore traduce quasi letteralmente ogni istruzione e spesso esegue il wrap-around hardware dei registri; a `-O2` sfrutta l'ipotesi di assenza di UB per semplificare condizioni, rimuovere controlli e riordinare letture e scritture. Compilare e testare fin da subito sia con `-O2` sia con i sanitizer (`-fsanitize=address,undefined`) evita queste sorprese.

### Esercizio 25.3 — Primitive numeriche e vettoriali sicure contro overflow, shift, strict aliasing e violazioni di restrict

**Descrizione**

Scrivi un programma C che implementi cinque primitive completamente prive di **comportamento indefinito** (sicure anche con `-O3` e `-fsanitize=address,undefined`) per sostituire i classici idiomi vulnerabili alle ottimizzazioni del compilatore: (1) `bool somma_sicura_i32(int32_t a, int32_t b, int32_t *out)` con `ckd_add` (rifiuta overflow invece di eseguire `a + b < a`); (2) `bool prod_sicuro_i64(int64_t a, int64_t b, int64_t *out)` con `ckd_mul`; (3) `bool shift_sicuro_u32(uint32_t x, int k, bool sinistra, uint32_t *out)` che valida `0 <= k && k < 32` prima di applicare `<<` o `>>`; (4) `uint32_t float_a_bit(float f)` e `float bit_a_float(uint32_t u)` che reinterpretano i bit tramite `memcpy` con `static_assert(sizeof(float) == sizeof(uint32_t))` (senza violare **strict aliasing**); (5) `void combina_restrict(size_t n, double *restrict dst, const double *restrict a, const double *restrict b, double alpha)` (`dst[i] = alpha * a[i] + b[i]`) protetta dal wrapper `bool combina_sicura(size_t n, double *dst, const double *a, const double *b, double alpha, bool *usato_restrict)` che verifica tramite `uintptr_t` se l'intervallo di `dst` si sovrappone ad `a` o `b`: se disgiunti chiama `combina_restrict` (`*usato_restrict = true`), se sovrapposti usa un buffer temporaneo dinamico evitando la violazione di `restrict` (`*usato_restrict = false`). In `main` leggi da `stdin` i comandi `ADD32 <a> <b>`, `MUL64 <a> <b>`, `SHL32 <u32> <k>`, `SHR32 <u32> <k>`, `FBITS <val_f>` (stampa esadecimale IEEE-754 e round-trip `bit_a_float`), `VEC_DISJ <alpha>` e `VEC_OVERLAP <alpha>` (entrambi su un vettore base `{1.0, 2.0, 3.0, 4.0}` con `b = {10.0, 20.0, 30.0, 40.0}`, nel secondo caso scrivendo `dst = a` con sovrapposizione totale), riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- uso di `ckd_add` e `ckd_mul` (`<stdckdint.h>`) al posto di controlli post-overflow eliminabili dal compilatore
- validazione dell'intervallo `0 <= k < 32` prima di spostare un `uint32_t`
- reinterpretazione dei bit di `float` tramite `memcpy` e `static_assert` nel rispetto di `strict aliasing`
- verifica preventiva della sovrapposizione tramite `uintptr_t` prima di invocare un kernel con parametri `restrict`

**Domande guida**

1. Perché un compilatore ottimizzante può eliminare interamente il ramo `if (a > 0 && b > 0 && a + b < 0)` su variabili `int32_t`?
2. Come mai `float_a_bit` usa `memcpy` invece di `*(const uint32_t *)&f` e che cosa genera di solito il compilatore con `-O2` per quella `memcpy` di 4 byte?
3. Che cosa succederebbe se invocassi direttamente `combina_restrict` passando `dst == a` sullo stesso array?
4. Perché `shift_sicuro_u32` deve rifiutare `k == 32` anche se `x` è di tipo `uint32_t` senza segno?

**Esempio di esecuzione**

```input
ADD32 2147483640 7
ADD32 2147483640 10
MUL64 -9223372036854775808 -1
SHL32 1 31
SHL32 1 32
SHR32 16 -1
FBITS -2.5
VEC_DISJ 2.0
VEC_OVERLAP 2.0
```

```output
ADD32: OK 2147483647
ADD32: OVERFLOW
MUL64: OVERFLOW
SHL32: OK 0x80000000
SHL32: ERR_SHIFT
SHR32: ERR_SHIFT
FBITS: hex=0xc0200000 rt=-2.50
VEC_DISJ: restrict=1 [12.00 24.00 36.00 48.00]
VEC_OVERLAP: restrict=0 [12.00 24.00 36.00 48.00]
```

## 25.4 Scrivere un mini framework di test automatici in C

Quando modifichi una funzione o ottimizzi una struttura dati, come fai a essere certo di non aver rotto qualcosa che prima funzionava? Provare a mano due o tre input dalla tastiera è lento, noioso e facile da dimenticare: è il modo più rapido per introdurre **regressioni**, cioè difetti che ricompaiono in codice già collaudato. La soluzione usata in ogni progetto serio — e indispensabile per il progetto finale (lo vedremo nel capitolo 26) — è affiancare a ogni modulo una suite di test eseguibili.

Un **test automatico** (*automated test*) è una verifica eseguibile in codice che controlla in modo ripetibile il comportamento di funzioni e moduli rispetto a risultati attesi e invarianti.

Nel capitolo 21 hai incontrato la macro `assert()` di `<assert.h>`. Perché non basta usare `assert()` per scrivere una suite di test? Per due motivi pratici:

1. Quando `assert()` fallisce, invoca `abort()` e **termina immediatamente l'intero programma**. Se hai venti test e il secondo fallisce, non saprai mai se gli altri diciotto passano o falliscono, né avrai un riepilogo complessivo.
2. Se compili con `-DNDEBUG`, tutte le `assert()` scompaiono: una suite di test invece deve restare attiva anche quando verifichi una compilazione ottimizzata con `-O2`.

Costruire un mini framework di test automatici in C richiede poche decine di righe in un file di intestazione riutilizzabile (per esempio `test_fw.h`). Gli ingredienti sono tutti strumenti che conosci già dal capitolo 21 e dal capitolo 24:

- **Una struttura di contesto (`test_ctx_t`)** che accumula i contatori della suite: numero di test eseguiti, superati, falliti, asserzioni superate, asserzioni fallite e un flag booleano (`corrente_ko`) per sapere se il test in corso ha registrato almeno un fallimento.
- **Macro di asserzione protette da `do { ... } while (0)`** (come `T_VERO`, `T_EQ_I32`, `T_EQ_ZU`): valutano ciascun argomento una sola volta in variabili locali, aggiornano i contatori del contesto senza interrompere il programma e, in caso di fallimento, stampano il testo della condizione (grazie all'operatore di stringificazione `#`), la funzione corrente (`__func__`) ed eventualmente file e riga (`__FILE__`, `__LINE__`), oltre ai valori atteso e ottenuto.
- **Un runner (`test_esegui`)** che riceve un puntatore a funzione di test (tramite una tabella di `caso_test_t`), azzera `corrente_ko`, esegue la funzione, aggiorna i totali e stampa `[PASS]` o `[FAIL]`.

Secondo lo standard C23, il costrutto `do { ... } while (0)`, l'operatore `#` del preprocessore e gli identificatori predefiniti `__FILE__`, `__LINE__` e `__func__` sono completamente **definiti**.

Per essere efficace su un modulo a tipo opaco, una suite di test deve rispettare quattro criteri:

1. **Isolamento**: ogni test crea la propria istanza del tipo opaco, esegue le verifiche e la distrugge prima di terminare, così nessun test influenza il successivo e i sanitizer possono rilevare subito eventuali perdite di memoria.
2. **Determinismo**: stessi input e stessi controlli producono sempre lo stesso risultato.
3. **Copertura dei casi limite**: oltre ai casi nominali, testa sempre capacità zero o uno, contenitore vuoto, contenitore pieno, avvolgimento circolare (*wrap-around*), puntatori nulli (`nullptr`) e percorsi di errore.
4. **Codice di uscita coerente**: il programma di test restituisce `EXIT_SUCCESS` (`0`) solo se `ctx.falliti == 0`, e `EXIT_FAILURE` altrimenti, in modo che uno script automatico possa accorgersi immediatamente di un fallimento.

> **Se vieni da Python** — In Python strumenti come `unittest` o `pytest` sono inclusi o installabili con scoperta automatica dei test; in C un mini framework di test si costruisce in poche decine di righe usando macro `do-while(0)`, puntatori a funzione e `__FILE__`/`__LINE__`.

### Esempio guidato

Il programma seguente è organizzato su due file (`mini_test.h` e `main.c`). Il file di intestazione definisce la struttura di contesto, le macro `MT_VERO` e `MT_EQ_I32` protette da `do { ... } while (0)` e il runner `mt_esegui`. Il file `main.c` testa due piccole funzioni (calcolo del massimo in un array e ricerca binaria) e include infine un test volutamente fallito per mostrare la segnalazione pulita dell'errore senza interrompere il programma.

<!-- cod: id=25.4-a tipo=programma gruppo=demo_test file=mini_test.h -->
```c
#ifndef MINI_TEST_H
#define MINI_TEST_H

#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct mt_ctx {
    size_t eseguiti;
    size_t superati;
    size_t falliti;
    size_t ass_ok;
    size_t ass_ko;
    bool corrente_ko;
} mt_ctx_t;

typedef void (*mt_fn)(mt_ctx_t *ctx);

#define MT_VERO(ctx, cond) do { \
    if (cond) { \
        ++(ctx)->ass_ok; \
    } else { \
        ++(ctx)->ass_ko; \
        (ctx)->corrente_ko = true; \
        printf("  [FAIL_ASS] %s: %s\n", __func__, #cond); \
    } \
} while (0)

#define MT_EQ_I32(ctx, att, ott) do { \
    int32_t _att = (att); \
    int32_t _ott = (ott); \
    if (_att == _ott) { \
        ++(ctx)->ass_ok; \
    } else { \
        ++(ctx)->ass_ko; \
        (ctx)->corrente_ko = true; \
        printf("  [FAIL_ASS] %s: %s == %s (att=%" PRId32 " ott=%" PRId32 ")\n", \
               __func__, #att, #ott, _att, _ott); \
    } \
} while (0)

static inline void mt_esegui(mt_ctx_t *ctx, const char *nome, mt_fn fn) {
    ctx->corrente_ko = false;
    fn(ctx);
    ++ctx->eseguiti;
    if (ctx->corrente_ko) {
        ++ctx->falliti;
        printf("[FAIL] %s\n", nome);
    } else {
        ++ctx->superati;
        printf("[PASS] %s\n", nome);
    }
}

#endif
```

<!-- cod: id=25.4-b tipo=programma gruppo=demo_test file=main.c -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "mini_test.h"

static bool trova_max(const int32_t *a, size_t n, int32_t *out) {
    if (a == nullptr || n == 0 || out == nullptr) {
        return false;
    }
    int32_t m = a[0];
    for (size_t i = 1; i < n; ++i) {
        if (a[i] > m) {
            m = a[i];
        }
    }
    *out = m;
    return true;
}

static ptrdiff_t cerca_bin(const int32_t *a, size_t n, int32_t k) {
    size_t sx = 0;
    size_t dx = n;
    while (sx < dx) {
        size_t mid = sx + (dx - sx) / 2;
        if (a[mid] == k) {
            return (ptrdiff_t)mid;
        }
        if (a[mid] < k) {
            sx = mid + 1;
        } else {
            dx = mid;
        }
    }
    return -1;
}

static void test_max_casi(mt_ctx_t *c) {
    int32_t out = 0;
    const int32_t v[4] = {-10, 7, 3, 7};
    MT_VERO(c, !trova_max(nullptr, 4, &out));
    MT_VERO(c, !trova_max(v, 0, &out));
    MT_VERO(c, trova_max(v, 4, &out));
    MT_EQ_I32(c, 7, out);
}

static void test_ricerca_binaria(mt_ctx_t *c) {
    const int32_t v[5] = {2, 5, 8, 12, 20};
    MT_EQ_I32(c, 0, (int32_t)cerca_bin(v, 5, 2));
    MT_EQ_I32(c, 4, (int32_t)cerca_bin(v, 5, 20));
    MT_EQ_I32(c, -1, (int32_t)cerca_bin(v, 5, 9));
}

static void test_fallimento_dimostrativo(mt_ctx_t *c) {
    const int32_t v[2] = {4, 9};
    int32_t out = 0;
    MT_VERO(c, trova_max(v, 2, &out));
    MT_EQ_I32(c, 10, out);
}

int main(void) {
    mt_ctx_t ctx = {};
    mt_esegui(&ctx, "max_casi", test_max_casi);
    mt_esegui(&ctx, "ricerca_binaria", test_ricerca_binaria);
    mt_esegui(&ctx, "fallimento_dimostrativo", test_fallimento_dimostrativo);
    printf("Totale: %zu/%zu superati, %zu falliti (ass ok=%zu ko=%zu)\n",
           ctx.superati, ctx.eseguiti, ctx.falliti, ctx.ass_ok, ctx.ass_ko);
    return 0;
}
```

```output
[PASS] max_casi
[PASS] ricerca_binaria
  [FAIL_ASS] test_fallimento_dimostrativo: 10 == out (att=10 ott=9)
[FAIL] fallimento_dimostrativo
Totale: 2/3 superati, 1 falliti (ass ok=8 ko=1)
```

Osserva due dettagli chiave nell'implementazione di `mini_test.h`:

- In `MT_EQ_I32(ctx, att, ott)`, gli argomenti `att` e `ott` sono salvati una sola volta nelle variabili locali `_att` e `_ott` prima del confronto e della `printf`: se passassi una chiamata di funzione come `cerca_bin(...)`, verrebbe eseguita una sola volta, non due.
- Anche quando `test_fallimento_dimostrativo` fallisce, il programma non si interrompe con `abort()`: registra il fallimento, stampa il nome della funzione (`__func__`) e i valori atteso e ottenuto, poi produce il riepilogo finale. In un eseguibile di test reale, `main` restituirebbe `(ctx.falliti == 0) ? EXIT_SUCCESS : EXIT_FAILURE;`.

> **Approfondimento — Testare il proprio framework di test**
> Un errore sorprendentemente frequente quando si scrivono macro di test personalizzate è commettere un piccolo sbaglio di sintassi o di logica che fa passare *sempre* un'asserzione. Includere un caso diagnostico con un'asserzione volutamente falsa (come `test_fallimento_dimostrativo`) ti conferma che il framework registra davvero il fallimento, incrementa i contatori e stampa il messaggio diagnostico atteso.

### Esercizio 25.4 — Mini framework di test automatici su più file applicato a un buffer circolare opaco

**Descrizione**

Realizza su quattro file (`test_fw.h`, `ring_buf.h`, `ring_buf.c`, `main.c`) un mini framework di **test automatici** con macro `do-while(0)` e usalo per verificare una libreria opaca di buffer circolare. (1) In `test_fw.h` (protetto da `TEST_FW_H`) definisci `typedef struct test_ctx { size_t eseguiti, superati, falliti, ass_ok, ass_ko; bool corrente_ko; } test_ctx_t;`, `typedef void (*test_fn)(test_ctx_t *ctx);`, `typedef struct caso_test { const char *nome; test_fn fn; } caso_test_t;`, le macro protette da `do { ... } while (0)`: `T_VERO(ctx, cond)`, `T_EQ_I32(ctx, att, ott, expr_txt)` e `T_EQ_ZU(ctx, att, ott)` (che incrementano `ass_ok` se vere oppure impostano `corrente_ko = true`, incrementano `ass_ko` e stampano `  [ASS_FAIL] <__func__>: ...` usando `#cond` o `expr_txt` e i valori), e la funzione `static inline void test_esegui(test_ctx_t *ctx, const caso_test_t *c)` che resetta `corrente_ko`, esegue `c->fn(ctx)`, aggiorna `eseguiti`/`superati`/`falliti` e stampa `[PASS] <nome>` oppure `[FAIL] <nome>`. (2) In `ring_buf.h` e `ring_buf.c` implementa il **tipo opaco** `ring_t` (`ring_crea(size_t cap)`, `ring_distruggi`, `ring_push`, `ring_pop`, `ring_len`, `ring_cap`, `ring_vuoto`, `ring_pieno`) con allocazione dinamica sicura e avanzamento circolare `(idx + 1) % cap`. (3) In `main.c` definisci cinque test unitari nella tabella `SUITE[]`: `crea_invalida`, `vuoto_e_pop`, `fifo_base`, `wrap_around` e `pieno_e_svuota`, più un test diagnostico `demo_fallimento` che fallisce intenzionalmente un'asserzione per dimostrare il rilevamento dei guasti. Leggi da `stdin` i comandi `RUN ALL`, `RUN <nome>` e `RUN_DEMO_FAIL` stampando i singoli esiti e il riepilogo `RIEPILOGO: test=<ok>/<tot> falliti=<ko> ass_ok=<aok> ass_ko=<ako>` esattamente come nell'esempio.

**Concetti da tenere a mente**

- macro di asserzione di test protette da `do-while(0)` con stringificazione `#` e `__func__`
- esecuzione continuativa della suite di test con contabilizzazione di test e asserzioni superate/fallite
- progettazione di test unitari su casi nominali, limiti (`cap=0`, vuoto, pieno) e avvolgimento circolare (*wrap-around*)
- verifica che il framework rilevi e segnali correttamente i fallimenti senza interrompere il runner

**Domande guida**

1. Perché un framework di test automatici usa macro come `T_EQ_I32` invece della macro standard `assert()` di `<assert.h>`?
2. Come mai `T_EQ_I32` valuta `att` e `ott` una sola volta in variabili locali dentro `do { ... } while (0)` prima di confrontarle e stamparle?
3. Quali casi limite del buffer circolare verifica il test `wrap_around` rispetto al semplice test `fifo_base`?
4. Perché conviene mantenere un test diagnostico come `demo_fallimento` per verificare il comportamento del framework stesso?

**Esempio di esecuzione**

```input
RUN ALL
RUN wrap_around
RUN_DEMO_FAIL
```

```output
[PASS] crea_invalida
[PASS] vuoto_e_pop
[PASS] fifo_base
[PASS] wrap_around
[PASS] pieno_e_svuota
RIEPILOGO: test=5/5 falliti=0 ass_ok=22 ass_ko=0
[PASS] wrap_around
RIEPILOGO: test=1/1 falliti=0 ass_ok=6 ass_ko=0
  [ASS_FAIL] test_demo_fail: 1 + 1 == 3 (att=3 ott=2)
[FAIL] demo_fallimento
RIEPILOGO: test=0/1 falliti=1 ass_ok=1 ass_ko=1
```

## 25.5 Fuzzing a seme fisso e strumenti professionali di analisi

I test automatici scritti a mano controllano i casi a cui hai pensato tu. I difetti più subdoli, però, si nascondono spesso in combinazioni di operazioni a cui nessuno pensa: un inserimento seguito da tre rimozioni, un ridimensionamento esattamente sul bordo della capacità, un carattere inatteso dentro un parser. Per scoprire questi errori esiste una tecnica complementare chiamata **fuzzing** (*fuzzing*): una tecnica di verifica automatica che sottopone un programma a grandi quantità di input generati casualmente per scoprirne difetti.

In C la libreria standard `<stdlib.h>` fornisce un generatore di numeri pseudocasuali semplice e sempre disponibile:

- `void srand(unsigned int seed);` imposta il **seme** iniziale del generatore;
- `int rand(void);` restituisce l'intero pseudocasuale successivo nell'intervallo `[0, RAND_MAX]`, dove `RAND_MAX` è una costante garantita dallo standard pari ad almeno `32767` (puoi verificarlo con `static_assert(RAND_MAX >= 32767)`).

Due regole sono fondamentali quando usi `srand` e `rand` nel fuzzing:

1. **Usa sempre un seme fisso** (per esempio `srand(12345U)` oppure un seme passato da input). Se il fuzzer scopre un guasto al passo 1 842, rilanciare il programma con lo stesso seme sulla stessa piattaforma riproduce esattamente la stessa sequenza di operazioni, permettendoti di indagare il bug nel debugger.
2. **Non dipendere dalla sequenza numerica grezza di `rand()`**. Secondo lo standard C23, le funzioni `srand`, `rand` e il limite `RAND_MAX >= 32767` sono definiti, ma l'algoritmo interno del generatore e la sequenza prodotta per un dato seme sono **dipendenti dall'implementazione**: lo stesso seme produce numeri diversi su Linux, macOS e Windows. Inoltre `rand()` non va mai usato per scopi crittografici o di sicurezza.

Come fai a sapere se il tuo programma si è comportato bene su 5 000 operazioni casuali, se non conosci in anticipo il risultato di ogni passo? Si usano due strategie potentissime, che funzionano qualunque sia la sequenza prodotta da `rand()`:

- **Test differenziale con oracolo**: affianchi alla tua struttura dati veloce (per esempio una mappa ordinata o una tabella hash) un **oracolo** di riferimento elementare e ovvio — magari lento, basato su un piccolo array lineare — ma quasi impossibile da sbagliare. A ogni passo esegui la stessa operazione casuale su entrambi e controlli che i risultati coincidano esattamente.
- **Verifica continua degli invarianti**: scrivi una funzione dedicata (come `invariante_ok(struttura)`) che controlla a ogni singolo passo le proprietà strutturali (chiavi strettamente ordinate, `len <= cap`, assenza di cicli o puntatori incoerenti). Così intercetti l'errore esattamente nel passo in cui nasce, non migliaia di operazioni dopo.

Il fuzzing a seme fisso diventa ancora più efficace quando lo combini con la **cassetta degli attrezzi professionale** del programmatore C:

- **Avvisi severi del compilatore**: compila sempre con `-Wall -Wextra -Wpedantic` (e preferibilmente `-Werror`) per intercettare conversioni sospette, variabili non usate e violazioni dello standard.
- **Sanitizer durante il fuzzing**: eseguire il fuzzer con `-fsanitize=address,undefined` (AddressSanitizer e UndefinedBehaviorSanitizer, introdotti nei capitoli 11 e 21) trasforma ogni accesso fuori dai limiti, uso dopo la liberazione, perdita di memoria o overflow con segno in un arresto immediato con diagnosi precisa.
- **Debugger (`gdb` o `lldb`)**: una volta trovato un seme che fallisce, il debugger ti permette di fermarti esattamente sul passo incriminato e ispezionare variabili, puntatori e stack delle chiamate.
- **Profiler**: prima di ottimizzare a intuito un programma funzionante, usa un profiler del tuo sistema operativo per misurare dove il programma spende davvero il tempo di CPU.

### Esempio guidato

Il programma seguente applica il fuzzing differenziale a una funzione `ordina_inserzione` su `int32_t`. Fissa il seme `12345U`, genera 200 array di lunghezza casuale tra `0` e `64` con valori positivi e negativi, li ordina sia con `ordina_inserzione` sia con l'oracolo `qsort` della libreria standard, verifica che l'array risultante sia ordinato e che i due risultati coincidano byte per byte tramite `memcmp`. L'output stampa solo il seme, il numero di prove e il numero di errori (`0`), restando identico su qualsiasi implementazione di `rand()`.

<!-- cod: id=25.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static_assert(RAND_MAX >= 32767);

static void ordina_inserzione(int32_t *a, size_t n) {
    for (size_t i = 1; i < n; ++i) {
        int32_t chiave = a[i];
        size_t j = i;
        while (j > 0 && a[j - 1] > chiave) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = chiave;
    }
}

static int confronta_i32(const void *p1, const void *p2) {
    int32_t a = *(const int32_t *)p1;
    int32_t b = *(const int32_t *)p2;
    return (a > b) - (a < b);
}

static bool invariante_ordinato(const int32_t *a, size_t n) {
    for (size_t i = 1; i < n; ++i) {
        if (a[i - 1] > a[i]) {
            return false;
        }
    }
    return true;
}

int main(void) {
    constexpr unsigned int SEME = 12345U;
    constexpr size_t PROVE = 200;
    constexpr size_t MAX_N = 64;

    srand(SEME);
    size_t errori = 0;

    for (size_t t = 0; t < PROVE; ++t) {
        size_t n = (size_t)(rand() % (int)(MAX_N + 1));
        int32_t a[MAX_N] = {};
        int32_t oracolo[MAX_N] = {};

        for (size_t i = 0; i < n; ++i) {
            int32_t val = (int32_t)(rand() % 1001) - 500;
            a[i] = val;
            oracolo[i] = val;
        }

        ordina_inserzione(a, n);
        qsort(oracolo, n, sizeof(int32_t), confronta_i32);

        bool inv_ok = invariante_ordinato(a, n);
        bool uguali = (n == 0) || (memcmp(a, oracolo, n * sizeof(int32_t)) == 0);
        if (!inv_ok || !uguali) {
            ++errori;
        }
    }

    printf("Fuzzing ordinamento (seme=%u): prove=%zu errori=%zu\n",
           SEME, PROVE, errori);
    return (errori == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
```

```output
Fuzzing ordinamento (seme=12345): prove=200 errori=0
```

Osserva come l'esempio mette insieme tutte le buone pratiche viste nel capitolo:

- `confronta_i32` usa `(a > b) - (a < b)` invece di `a - b` per evitare qualsiasi rischio di overflow con segno.
- Ogni prova controlla sia l'invariante (`invariante_ordinato`) sia la coincidenza esatta con l'oracolo (`memcmp` dopo `qsort`), gestendo in modo sicuro anche il caso limite `n == 0`.
- Anche se `rand()` genera numeri diversi su piattaforme diverse, la proprietà verificata (`ordina_inserzione` coincide con `qsort`) è universale e l'esito finale è sempre `errori=0`.

> **Approfondimento — La regola d'oro delle prestazioni in C**
> Prima scrivi codice chiaro, modulare e privo di comportamento indefinito, protetto da test automatici, fuzzing e sanitizer. Solo quando tutto funziona correttamente usa un profiler per individuare i veri colli di bottiglia: nella maggior parte dei programmi reali circa il 90% del tempo viene speso nel 10% del codice. Ottimizzare a caso il restante 90% complica il sorgente senza benefici apprezzabili; concentrare miglioramenti algoritmici e di località dei dati sul 10% caldo produce invece guadagni concreti e misurabili.

### Esercizio 25.5 — Fuzzer differenziale a seme fisso (srand/rand) con oracolo e verifica di invarianti per una mappa ordinata

**Descrizione**

Realizza su tre file (`mappa_ord.h`, `mappa_ord.c`, `main.c`) un motore di **fuzzing** differenziale a seme fisso (`srand`/`rand` di `<stdlib.h>`) che mette alla prova una mappa ordinata dinamica contro un oracolo di riferimento elementare. (1) In `mappa_ord.h` (protetto da `MAPPA_ORD_H`) dichiara il **tipo opaco** `mappa_ord_t` con `mappa_ord_t *mappa_crea(void);`, `void mappa_distruggi(mappa_ord_t *m);`, `bool mappa_put(mappa_ord_t *m, int32_t chiave, int32_t valore, bool *aggiornato);` (usa ricerca binaria `O(log n)`, sposta con `memmove` e cresce raddoppiando con `ckd_mul` e `realloc`), `bool mappa_get(const mappa_ord_t *m, int32_t chiave, int32_t *val_out);`, `bool mappa_del(mappa_ord_t *m, int32_t chiave);`, `size_t mappa_len(const mappa_ord_t *m);` e `bool mappa_invariante_ok(const mappa_ord_t *m);` (verifica `len <= cap` e ordine strettamente crescente delle chiavi). (2) In `main.c` verifica `static_assert(RAND_MAX >= 32767)` e implementa un oracolo diretto su array di `64` posizioni (`bool pres[64]`, `int32_t val[64]`). Leggi da `stdin` i comandi `FUZZ <seme> <passi> <max_k>` (`1 <= passi <= 5000`, `1 <= max_k <= 64`): fissa `srand((unsigned int)seme)`, genera `<passi>` operazioni pseudocasuali con `rand()` (`PUT`, `DEL`, `GET` su chiavi in `[0, max_k)` e valori con segno), confronta a ogni passo il risultato e la lunghezza di `mappa_ord` con l'oracolo e controlla `mappa_invariante_ok(m)`. Al termine esegue una scansione completa di tutte le `max_k` chiavi verificando la coincidenza finale con l'oracolo, libera la mappa e stampa `FUZZ(seme=<seme>, passi=<passi>, k=<max_k>): ok=<passi>/<passi> errori=0 inv_ok=1` esattamente come nell'esempio.

**Concetti da tenere a mente**

- inizializzazione del generatore pseudocasuale con `srand(seme)` e uso di `rand()` con `static_assert(RAND_MAX >= 32767)`
- test differenziale contro un oracolo elementare per individuare discrepanze su migliaia di sequenze casuali
- verifica continua degli invarianti strutturali (ordine stretto delle chiavi e coerenza della lunghezza) a ogni passo
- portabilità dell'esito del fuzzing indipendente dall'implementazione specifica di `rand()`

**Domande guida**

1. Perché l'esito del fuzzer differenziale (`errori=0` e `inv_ok=1`) resta identico su sistemi operativi diversi anche se l'algoritmo interno di `rand()` dipende dall'implementazione?
2. Qual è il vantaggio di confrontare `mappa_ord` con un oracolo banale indicizzato direttamente per chiave rispetto a scrivere a mano dieci test statici?
3. Perché conviene chiamare `mappa_invariante_ok(m)` a ogni singolo passo del fuzzing invece che soltanto alla fine dei 5000 passi?
4. Come mai nel fuzzing professionale si combina l'esecuzione con AddressSanitizer e UndefinedBehaviorSanitizer?

**Esempio di esecuzione**

```input
FUZZ 42 500 16
FUZZ 1337 2000 64
FUZZ 7 300 1
```

```output
FUZZ(seme=42, passi=500, k=16): ok=500/500 errori=0 inv_ok=1
FUZZ(seme=1337, passi=2000, k=64): ok=2000/2000 errori=0 inv_ok=1
FUZZ(seme=7, passi=300, k=1): ok=300/300 errori=0 inv_ok=1
```

## Riepilogo

- Per confrontare algoritmi in modo riproducibile si contano le operazioni elementari (confronti, spostamenti, accessi in memoria). Per stimare il tempo di CPU si usa `<time.h>` (`clock_t`, `clock()`, `CLOCKS_PER_SEC`), verificando sempre che gli istanti siano diversi da `(clock_t)-1` e impedendo l'eliminazione del codice morto tramite un risultato osservabile (stampa o pozzo `volatile`).
- La **località dei dati** sfrutta le linee di cache del processore (tipicamente 64 byte): in C le matrici sono memorizzate per righe (*row-major*), quindi conviene scorrere prima l'indice più a destra. Nei cicli che toccano solo pochi campi caldi di molti record, una disposizione **Struct di Array (SoA)** riduce i *cache miss* e i byte trasferiti rispetto a un **Array di Struct (AoS)**, che resta invece favorevole quando si leggono quasi tutti i campi di un singolo record casuale.
- In base alla regola *as-if* dello standard C23, un compilatore con `-O2` o `-O3` può assumere che non si verifichi mai comportamento indefinito ed eliminare controlli scritti dopo un potenziale UB (come `if (x + 1 < x)` o `if (p == nullptr)` dopo `*p`). Le alternative sicure e veloci in C23 sono `<stdckdint.h>` (`ckd_add`, `ckd_sub`, `ckd_mul`), controlli d'intervallo sugli shift, `memcpy` con `static_assert` per reinterpretare i bit e verifiche di disgiunzione con `uintptr_t` prima di invocare funzioni `restrict`.
- Un mini framework di **test automatici** in C si realizza con una `struct` di contesto, macro protette da `do { ... } while (0)` che usano `#` e `__func__`/`__FILE__`/`__LINE__` e un runner basato su puntatori a funzione: a differenza di `assert()`, registra tutti i fallimenti e produce un riepilogo completo senza interrompere la suite al primo errore.
- Il **fuzzing** a seme fisso (`srand`/`rand` di `<stdlib.h>`, con `RAND_MAX >= 32767`) sottopone moduli e strutture dati a migliaia di sequenze casuali riproducibili, verificando invarianti a ogni passo e confrontando i risultati con un oracolo di riferimento. Abbinato ad avvisi rigorosi, sanitizer, debugger e profiler, costituisce la base della qualità del software in C (che applicherai nel progetto finale, lo vedremo nel capitolo 26).

## Errori comuni

- **Misurare con `clock()` un ciclo il cui risultato non viene mai usato né stampato**: con `-O2` il compilatore elimina l'intero ciclo per eliminazione del codice morto, producendo un tempo prossimo a zero e del tutto fuorviante.
- **Scorrere una matrice bidimensionale per colonne (`m[i][j]` con `i` nel ciclo interno) invece che per righe**: ogni accesso salta di un'intera riga e su matrici grandi provoca continui *cache miss*.
- **Scrivere controlli di overflow dopo aver già provocato un overflow con segno (`if (a + b < a)`) o testare `p == nullptr` dopo aver già dereferenziato `*p`**: il compilatore ottimizzante è autorizzato a rimuovere silenziosamente il controllo.
- **Usare `assert()` di `<assert.h>` come unico strumento di test**: al primo fallimento il programma termina con `abort()` nascondendo tutti i casi successivi, non stampa un riepilogo e scompare compilando con `-DNDEBUG`.
- **Chiamare `rand()` senza `srand` con seme fisso durante il fuzzing oppure dipendere dalla sequenza esatta prodotta da `rand()`**: senza seme fisso i guasti non sono riproducibili, mentre la sequenza numerica grezza cambia da una libreria standard all'altra.

## Prima di proseguire

- [ ] So confrontare algoritmi contando le operazioni elementari e usare correttamente `clock()`, `clock_t` e `CLOCKS_PER_SEC` evitando l'eliminazione del codice morto.
- [ ] So spiegare cos'è una linea di cache e scegliere tra scansione per righe e per colonne e tra layout AoS e SoA in base agli accessi in memoria.
- [ ] So spiegare perché le ottimizzazioni `-O2`/`-O3` possono eliminare controlli scritti dopo un comportamento indefinito e so riscriverli in sicurezza con `<stdckdint.h>`, `memcpy` e controlli preventivi per `restrict`.
- [ ] So costruire un mini framework di test automatici con macro `do-while(0)`, `#` e puntatori a funzione per verificare casi nominali, limiti e d'errore di un modulo opaco.
- [ ] So scrivere un fuzzer differenziale a seme fisso con `srand`/`rand`, oracolo e verifica continua degli invarianti, e so quando usare sanitizer, debugger e profiler.
