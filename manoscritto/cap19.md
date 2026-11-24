# Capitolo 19 — Programmi su più file

> **In questo capitolo imparerai a:**
> - Separare interfaccia e implementazione tra file di intestazione (`.h`) e file sorgenti (`.c`) con compilazione separata
> - Proteggere gli header con protezioni di inclusione e controllare il collegamento con `static`, `extern` e `inline`
> - Nascondere la rappresentazione interna di una struttura dati mediante tipi opachi
> - Organizzare la tabella hash generica come libreria riutilizzabile su più file

> **Ti servono:** funzioni, prototipi, visibilità e durata di vita (capitolo 7), strutture ed enumerazioni (capitolo 12), puntatori a funzione e callback (capitolo 16), tabelle hash generiche e possesso della memoria (capitolo 18).

Fino a questo momento ogni tuo programma C è vissuto in un unico file `.c`. Per esercizi da cinquanta o cento righe questa scelta è comoda, ma già con la tabella hash generica del capitolo 18 hai visto il file crescere rapidamente: strutture interne, funzioni di supporto, logica della tabella e `main` convivono nello stesso testo. In un progetto reale di migliaia di righe — o semplicemente quando vuoi riutilizzare la tua tabella hash in un secondo programma senza fare copia e incolla — tenere tutto in un solo file diventa ingestibile: ogni piccola modifica costringe a ricompilare l'intero programma e qualunque funzione può toccare per errore i dettagli interni di un'altra componente.

Il linguaggio C affronta questo problema separando nettamente ciò che un modulo *promette* di offrire da *come* lo realizza. L'interfaccia pubblica viene scritta in un **file di intestazione** (`.h`), mentre il codice vero e proprio risiede in un file sorgente (`.c`). Ogni file `.c` può essere compilato in modo indipendente e unito agli altri soltanto nella fase finale di collegamento. Con pochi strumenti — protezioni di inclusione, qualificatori `static`, `extern` e `inline`, e strutture incomplete — puoi decidere esattamente quali simboli sono visibili all'esterno e quali restano privati del modulo.

Al termine di questo capitolo raggiungerai il traguardo centrale del libro: trasformare la tabella hash generica del capitolo 18 in una vera libreria modulare opaca (`tabella_hash.h` e `tabella_hash.c`). Chi la usa non potrà né vedere né corrompere i secchi interni, configurerà le politiche di possesso della memoria con una sola struttura di configurazione e potrà riutilizzare lo stesso modulo in più programmi, incluso l'interprete del capitolo finale (lo vedremo nel capitolo 26).

## 19.1 File di intestazione, file sorgenti e compilazione separata

Quando un programma supera qualche centinaio di righe, dividere il codice in moduli distinti non è una questione estetica ma una necessità tecnica. Separare il programma in più file risolve tre problemi concreti: permette di distinguere l'*interfaccia* (quali tipi e funzioni un modulo mette a disposizione) dall'*implementazione* (come quelle funzioni sono scritte), consente di riutilizzare lo stesso modulo in programmi diversi senza duplicarne il codice sorgente e rende possibile ricompilare soltanto i file effettivamente modificati.

In C ogni modulo è formato tipicamente da una coppia di file con lo stesso nome di base:

- un **file di intestazione** (*header file*), con estensione `.h`, che espone dichiarazioni di tipi, costanti e prototipi condivisi tra più file sorgenti;
- un file sorgente con estensione `.c`, che contiene le definizioni vere e proprie delle funzioni dichiarate nell'header.

Per capire come il compilatore trasforma più file sorgenti in un unico eseguibile occorre osservare da vicino le fasi della traduzione introdotte nel capitolo 1. Il compilatore non legge mai tutti i file `.c` contemporaneamente: lavora su un file `.c` alla volta. Prima che inizi l'analisi del codice C, il preprocessore espande ogni direttiva `#include` copiando testualmente il contenuto degli header richiesti dentro il file sorgente. Il risultato di questa espansione è chiamato **unità di traduzione** (*translation unit*): è un singolo file sorgente `.c` dopo l'espansione di tutti gli `#include` e delle direttive del preprocessore.

Ciascuna unità di traduzione viene tradotta dal compilatore in modo del tutto indipendente in un *file oggetto* (con estensione `.o` su sistemi Unix/Linux/macOS o `.obj` su alcuni compilatori Windows), che contiene codice macchina ancora incompleto perché i riferimenti a funzioni definite in altri file non hanno ancora un indirizzo definitivo. Questa prima fase si chiama **compilazione separata** (*separate compilation*): la compilazione indipendente di ciascun file `.c` in un file oggetto, seguita dal collegamento finale in un unico eseguibile. Nell'ultima fase interviene il collegatore, che unisce tutti i file oggetto e le librerie richieste, risolve ogni chiamata tra moduli e produce l'eseguibile finale.

```text
geometria.h ──┐                        ┌── geometria.o ──┐
              ├──> preprocessore ──>   │                 ├──> collegatore ──> programma
geometria.c ──┘    (unità di trad. 1)  │                 │
                                       │                 │
geometria.h ──┐                        │                 │
              ├──> preprocessore ──>   └── main.o ───────┘
main.c ───────┘    (unità di trad. 2)
```

Da riga di comando puoi eseguire la compilazione separata in due passaggi espliciti (usando il flag `-c` per fermarti al file oggetto) oppure affidare i passaggi a un solo comando:

```text
cc -std=c23 -Wall -Wextra -Wpedantic -Werror -c geometria.c
cc -std=c23 -Wall -Wextra -Wpedantic -Werror -c main.c
cc geometria.o main.o -lm -o programma
```

Se in seguito modifichi soltanto `main.c`, ti basta ricompilare `main.c` in `main.o` e ripetere il collegamento, senza dover ricompilare `geometria.c`. Quando invece modifichi `geometria.h`, devi ricompilare tutti i file `.c` che lo includono.

Per includere un file di intestazione il preprocessore offre due forme di `#include`:

- `#include <stdio.h>` (con parentesi angolari) cerca l'header nelle directory di sistema della libreria standard;
- `#include "geometria.h"` (con virgolette doppie) cerca prima nella directory del file sorgente corrente (o nei percorsi del progetto) e, solo se non lo trova, nei percorsi di sistema.

Quando scrivi il file di implementazione `modulo.c`, segui sempre una regola d'oro: inserisci `#include "modulo.h"` come **prima direttiva** del file, prima persino di `<stdio.h>` o `<stdlib.h>`. Questa abitudine garantisce due verifiche automatiche a ogni compilazione:

1. verifica che `modulo.h` sia *autosufficiente*, cioè che includa da sé tutti gli header da cui dipendono i suoi tipi (come `<stddef.h>` o `<stdint.h>`) senza contare su inclusioni precedenti fatte dal chiamante;
2. verifica che i prototipi dichiarati in `modulo.h` coincidano esattamente con le definizioni scritte in `modulo.c`.

Che cosa deve contenere un file di intestazione e che cosa va invece evitato con rigore? Nell'header vanno solo **dichiarazioni**: definizioni di tipi (`struct`, `enum`, `typedef`), prototipi di funzioni e costanti condivise. Non devi mai mettere in un `.h` definizioni di funzioni normali (non `inline` e non `static`) né definizioni di variabili globali con collegamento esterno: poiché ogni `#include` copia il contenuto dell'header in ciascuna unità di traduzione, includere quell'header in due file `.c` genererebbe due definizioni dello stesso simbolo e il collegatore segnalerebbe un errore di definizione multipla.

Riassumiamo le regole fondamentali della compilazione separata secondo lo standard C23:

- L'interfaccia pubblica di un modulo risiede nel file di intestazione (`.h`) con sole dichiarazioni; l'implementazione risiede nel corrispondente file sorgente (`.c`).
- Ogni file `.c`, dopo il preprocessore, forma un'unità di traduzione compilata indipendentemente in un file oggetto; il collegatore unisce i file oggetto nell'eseguibile finale.
- Ogni `modulo.c` include `"modulo.h"` come prima direttiva per verificare l'autosufficienza dell'header e la corrispondenza delle firme.
- Secondo lo standard C23, ogni identificatore con collegamento esterno usato nel programma deve avere esattamente una definizione esterna. Dichiarare nell'header un prototipo incompatibile con la definizione nel `.c` (situazione possibile se il `.c` dimentica di includere il proprio header) provoca **comportamento indefinito**, perché il compilatore non può accorgersi della discrepanza tra le due unità di traduzione.

> **Se vieni da Python** — In Python ogni file `.py` è direttamente un modulo importabile a tempo di esecuzione con `import`. In C la modularità separa esplicitamente l'interfaccia (`.h`) dall'implementazione (`.c`) e avviene in due fasi distinte prima dell'esecuzione: la compilazione separata di ciascuna unità di traduzione e il collegamento finale.

### Esempio guidato

Costruiamo un piccolo programma di geometria 2D suddiviso in tre file: `geometria.h`, `geometria.c` e `main.c`. L'header definisce i tipi `punto_t` e `rettangolo_t` e dichiara tre funzioni; `geometria.c` include `"geometria.h"` come prima riga e le implementa; `main.c` usa il modulo conoscendone solo l'interfaccia.

<!-- cod: id=19.1-a tipo=programma gruppo=geo file=geometria.h -->
```c
typedef struct punto {
    double x;
    double y;
} punto_t;

typedef struct rettangolo {
    punto_t origine;
    double larghezza;
    double altezza;
} rettangolo_t;

double geo_distanza(punto_t a, punto_t b);
double geo_area(rettangolo_t r);
double geo_perimetro(rettangolo_t r);
```

<!-- cod: id=19.1-b tipo=programma gruppo=geo file=geometria.c -->
```c
#include "geometria.h"
#include <math.h>

double geo_distanza(punto_t a, punto_t b) {
    double dx = b.x - a.x;
    double dy = b.y - a.y;
    return sqrt(dx * dx + dy * dy);
}

double geo_area(rettangolo_t r) {
    return r.larghezza * r.altezza;
}

double geo_perimetro(rettangolo_t r) {
    return 2.0 * (r.larghezza + r.altezza);
}
```

<!-- cod: id=19.1-c tipo=programma gruppo=geo file=main.c -->
```c
#include <stdio.h>
#include "geometria.h"

int main(void) {
    punto_t p1 = {.x = 1.0, .y = 2.0};
    punto_t p2 = {.x = 4.0, .y = 6.0};
    rettangolo_t r = {
        .origine = p1,
        .larghezza = 5.0,
        .altezza = 3.5
    };

    printf("Distanza p1-p2: %.2f\n", geo_distanza(p1, p2));
    printf("Area rettangolo: %.2f\n", geo_area(r));
    printf("Perimetro rettangolo: %.2f\n", geo_perimetro(r));
    return 0;
}
```

```output
Distanza p1-p2: 5.00
Area rettangolo: 17.50
Perimetro rettangolo: 17.00
```

Osserva come sono divise le responsabilità tra i tre file:

- `geometria.h` non include `<math.h>` perché la sua interfaccia usa soltanto `double` e i tipi che definisce. La dipendenza da `sqrt` è un dettaglio implementativo confinato dentro `geometria.c`.
- In `geometria.c` la prima riga è `#include "geometria.h"`: se `geo_area` avesse un tipo di ritorno o un parametro diverso dal prototipo nell'header, il compilatore segnalerebbe immediatamente l'incompatibilità di tipo.
- In `main.c` il compilatore conosce `punto_t`, `rettangolo_t` e le firme delle funzioni `geo_*` grazie a `#include "geometria.h"`, ma non vede i corpi delle funzioni: genera chiamate a simboli esterni che il collegatore risolve unendo `geometria.o` e `main.o` (con `-lm` per la libreria matematica).

> **Approfondimento — Perché includere `"modulo.h"` come prima riga di `modulo.c`**
> Supponi che un header `archivio.h` usi `size_t` nei suoi prototipi ma dimentichi `#include <stddef.h>`. Se `archivio.c` includesse `<stdio.h>` prima di `"archivio.h"`, `<stdio.h>` definirebbe già `size_t` e l'errore resterebbe nascosto durante la compilazione di `archivio.c`. Il difetto emergerebbe solo in seguito, in un altro file sorgente che includesse `"archivio.h"` prima di qualsiasi header standard. Mettendo sempre `#include "archivio.h"` alla riga 1 di `archivio.c`, il compilatore controlla l'autosufficienza dell'header fin dalla prima compilazione.

### Esercizio 19.1 — Modulo di aritmetica razionale su più file con separazione tra interfaccia e implementazione

**Descrizione**

Scrivi un programma C organizzato su tre file (`razionale.h`, `razionale.c`, `main.c`) che implementi un modulo per l'aritmetica esatta sui numeri razionali (frazioni `num / den` ridotte ai minimi termini). Nel file di intestazione `razionale.h` definisci `typedef struct razionale { int64_t num; int64_t den; } razionale_t;` e dichiara cinque funzioni:

1. `razionale_t raz_crea(int64_t num, int64_t den, bool *ok)` che rifiuta `den == 0` impostando `*ok = false`, altrimenti porta il segno sul numeratore (`den > 0`), normalizza `0 / den` in `0 / 1`, divide per il massimo comun divisore (algoritmo di Euclide) e imposta `*ok = true`;
2. `razionale_t raz_somma(razionale_t a, razionale_t b)`;
3. `razionale_t raz_moltiplica(razionale_t a, razionale_t b)`;
4. `int raz_confronta(razionale_t a, razionale_t b)` che restituisce `-1`, `0` oppure `1`;
5. `void raz_stampa(razionale_t r)` che stampa `<num>` se `r.den == 1`, altrimenti `<num>/<den>`.

Nel file `razionale.c` includi `"razionale.h"` come prima direttiva e implementa il modulo (nessuna funzione definita nell'header). In `main.c` leggi comandi da `stdin` fino a fine input: `NORM <n> <d>`, `ADD <n1> <d1> <n2> <d2>`, `MUL <n1> <d1> <n2> <d2>` e `CMP <n1> <d1> <n2> <d2>` (se un denominatore è `0` stampa `ERRORE DENOMINATORE ZERO` e prosegui), producendo l'output esatto dell'esempio.

**Concetti da tenere a mente**

- separazione tra file di intestazione (`.h` con tipi e prototipi) e file sorgente (`.c` con definizioni)
- inclusione di `"razionale.h"` come prima direttiva in `razionale.c` per verificare coerenza e autosufficienza
- compilazione separata di `razionale.c` e `main.c` seguita dal collegamento nell'eseguibile finale
- normalizzazione canonica di frazioni (segno sul numeratore, riduzione tramite MCD, gestione di `den == 0`)

**Domande guida**

1. Perché `razionale.h` deve includere `<stdint.h>` direttamente invece di sperare che lo faccia `main.c` prima di `#include "razionale.h"`?
2. Che cosa accadrebbe al momento del collegamento se definissi il corpo di `raz_somma` dentro `razionale.h` e lo includessi sia in `razionale.c` sia in `main.c`?
3. Perché in `razionale.c` conviene scrivere `#include "razionale.h"` come prima riga del file?
4. Come garantisce `raz_crea` una rappresentazione unica anche per frazioni come `0/-5` o `-6/-8`?

**Esempio di esecuzione**

```input
NORM -6 -8
NORM 0 -5
NORM 4 0
ADD 1 6 1 3
MUL -2 3 9 4
CMP 2 3 3 5
CMP 2 4 1 2
CMP -1 2 1 3
```

```output
3/4
0
ERRORE DENOMINATORE ZERO
1/2
-3/2
1
0
-1
```

## 19.2 Protezioni di inclusione e direttive del preprocessore

Non appena un progetto cresce oltre due o tre file sorgenti, gli header iniziano a includersi a vicenda. Immagina una situazione molto comune: `tipi.h` definisce una `struct`, `filtro.h` include `"tipi.h"` perché i suoi prototipi usano quella `struct`, e `main.c` include sia `"tipi.h"` sia `"filtro.h"`. Questa forma di dipendenza si chiama *inclusione a diamante*:

```text
          tipi.h
         /      \
        v        v
    filtro.h    main.c
         \      /
          v    v
     unità di traduzione di main.c
     (riceve tipi.h DUE volte)
```

Poiché il preprocessore esegue una sostituzione puramente testuale, nell'unità di traduzione di `main.c` il contenuto di `tipi.h` viene copiato due volte: una volta direttamente e una seconda volta attraverso `filtro.h`. Se `tipi.h` contiene una definizione di `struct`, il compilatore vede due definizioni dello stesso tipo nello stesso ambito e arresta la compilazione segnalando una ridefinizione del tipo.

Per impedire che lo stesso file di intestazione venga elaborato più di una volta dentro la medesima unità di traduzione, si usa una **protezione di inclusione** (*include guard*): è una coppia di direttive `#ifndef`/`#define`/`#endif` che impedisce l'inclusione multipla dello stesso file di intestazione.

<!-- cod: id=19.2-b tipo=frammento -->
```c
#ifndef TIPI_H
#define TIPI_H

/* dichiarazioni di tipi, costanti e prototipi */

#endif
```

Il meccanismo è immediato. La prima volta che il preprocessore legge `tipi.h` dentro un'unità di traduzione, il simbolo `TIPI_H` non è ancora definito: la condizione `#ifndef TIPI_H` ("se non è definito `TIPI_H`") è vera, il preprocessore definisce subito `TIPI_H` con `#define TIPI_H` e include il resto del file fino a `#endif`. Se `tipi.h` viene incluso una seconda volta nella stessa unità di traduzione (direttamente o tramite un altro header), `TIPI_H` risulta già definito: `#ifndef TIPI_H` è falsa e il preprocessore salta tutto fino a `#endif`.

Nella scelta del nome della protezione di inclusione rispetta due regole fondamentali:

1. Scegli un nome **univoco** nel progetto, di solito derivato dal nome del file in maiuscolo (per esempio `TIPI_H` oppure `PROGETTO_TIPI_H` in progetti grandi). Se due header diversi usassero per errore la stessa macro, includere il primo impedirebbe l'inclusione del secondo.
2. Non iniziare mai il nome con un doppio underscore (`__TIPI_H__`) né con un underscore seguito da lettera maiuscola (`_TIPI_H`). Lo standard C23 riserva questi identificatori all'implementazione (compilatore e libreria standard): usarli nel proprio codice provoca **comportamento indefinito**.

Oltre alle protezioni di inclusione, la direttiva `#define` permette di definire costanti simboliche o flag del preprocessore che vengono sostituiti testualmente prima della compilazione vera e propria. Una macro definita con `#define` può essere rimossa in qualsiasi punto del file con `#undef NOME`, limitandone la validità alla sola porzione di codice in cui serve.

Quando dovresti usare `#define` al posto di `const` o `constexpr` (capitolo 2)? La regola pratica è netta:

- Per valori numerici tipizzati e dimensioni di array usa sempre `constexpr` (o `const`), perché rispettano il controllo dei tipi e le regole di visibilità del C.
- Usa `#define` solo per ciò che il preprocessore deve vedere prima del compilatore: protezioni di inclusione, flag di configurazione per la compilazione condizionale, e letterali stringa che devono concatenarsi con altri letterali (come formati di `printf`). In questo capitolo usiamo solo macro semplici senza parametri; per le macro con argomenti rimandiamo al seguito (lo vedremo nel capitolo 21).

Le direttive di **compilazione condizionale** consentono di includere o escludere blocchi di codice prima che il compilatore C li analizzi:

- `#ifdef NOME` verifica se `NOME` è definito (equivale a `#if defined(NOME)`);
- `#ifndef NOME` verifica se `NOME` non è definito (equivale a `#if !defined(NOME)`);
- `#if`, `#elif`, `#else`, `#endif` valutano espressioni intere costanti del preprocessore e supportano l'operatore `defined(NOME)` combinato con `&&`, `||` e `!`.

Un uso molto diffuso di `#ifndef` è fornire un valore predefinito sovrascrivibile al momento della compilazione tramite il flag `-DNOME=VALORE` del compilatore: se l'utente compila con `-DLIVELLO_LOG=2`, il `#ifndef LIVELLO_LOG` nell'header risulta falso e prevale il valore passato da riga di comando; altrimenti viene applicato il valore predefinito.

Secondo lo standard C23, il funzionamento delle direttive del preprocessore e della compilazione condizionale è completamente definito; fa eccezione la definizione di nomi riservati (`__...` o `_Maiuscola`), che costituisce **comportamento indefinito**.

### Esempio guidato

Questo programma su quattro file (`tipi.h`, `filtro.h`, `filtro.c`, `main.c`) costruisce una dipendenza a diamante su `tipi.h`, la protegge con protezioni di inclusione e configura il livello di diagnostica a tempo di compilazione con `#ifndef`, `#define`, `#if`, `#elif`, `#else`, `#endif` e `defined(...)`.

<!-- cod: id=19.2-a tipo=programma gruppo=diamante file=tipi.h -->
```c
#ifndef TIPI_H
#define TIPI_H

#include <stddef.h>
#include <stdint.h>

#ifndef LIVELLO_LOG
#define LIVELLO_LOG 1
#endif

#if LIVELLO_LOG == 0
#define ETICHETTA_LOG "SILENZIOSO"
#elif LIVELLO_LOG == 1
#define ETICHETTA_LOG "NORMALE"
#else
#define ETICHETTA_LOG "DETTAGLIATO"
#endif

typedef struct campione {
    int32_t id;
    int32_t valore;
} campione_t;

#endif
```

<!-- cod: id=19.2-c tipo=programma gruppo=diamante file=filtro.h -->
```c
#ifndef FILTRO_H
#define FILTRO_H

#include <stddef.h>
#include "tipi.h"

size_t conta_oltre_soglia(const campione_t *dati, size_t n, int32_t soglia);

#endif
```

<!-- cod: id=19.2-d tipo=programma gruppo=diamante file=filtro.c -->
```c
#include "filtro.h"

size_t conta_oltre_soglia(const campione_t *dati, size_t n, int32_t soglia) {
    if (dati == nullptr) {
        return 0;
    }
    size_t conteggio = 0;
    for (size_t i = 0; i < n; ++i) {
        if (dati[i].valore > soglia) {
            ++conteggio;
        }
    }
    return conteggio;
}
```

<!-- cod: id=19.2-e tipo=programma gruppo=diamante file=main.c -->
```c
#include <stdio.h>
#include "tipi.h"
#include "filtro.h"
#include "tipi.h"

int main(void) {
#if defined(TIPI_H) && defined(FILTRO_H)
    printf("Modalità log: %s (livello %d)\n", ETICHETTA_LOG, LIVELLO_LOG);
#endif
    campione_t serie[] = {
        {.id = 1, .valore = 18},
        {.id = 2, .valore = 27},
        {.id = 3, .valore = 31},
        {.id = 4, .valore = 22}
    };
    size_t n = sizeof(serie) / sizeof(serie[0]);
    size_t alti = conta_oltre_soglia(serie, n, 25);
    printf("Campioni oltre 25: %zu su %zu\n", alti, n);
    return 0;
}
```

```output
Modalità log: NORMALE (livello 1)
Campioni oltre 25: 2 su 4
```

Analizziamo i punti chiave dell'esempio:

- `main.c` include `"tipi.h"`, poi `"filtro.h"` (che a sua volta include `"tipi.h"`) e infine di nuovo `"tipi.h"`. Grazie alla protezione `TIPI_H`, la definizione di `campione_t` viene elaborata una sola volta.
- In `tipi.h` il blocco `#ifndef LIVELLO_LOG` imposta il livello predefinito a `1`. Se compilassi con `-DLIVELLO_LOG=2`, `ETICHETTA_LOG` diventerebbe `"DETTAGLIATO"` senza modificare alcuna riga del sorgente.
- La condizione `#if defined(TIPI_H) && defined(FILTRO_H)` mostra come l'operatore `defined(...)` permetta di combinare più controlli in un'unica direttiva `#if`.

> **Approfondimento — Protezioni di inclusione standard contro `#pragma once`**
> In molti progetti reali incontrerai la direttiva `#pragma once` all'inizio degli header, che chiede al compilatore di includere il file una sola volta. Sebbene quasi tutti i compilatori moderni la supportino come estensione, `#pragma once` non fa parte dello standard ISO C23 e può fallire in casi particolari, per esempio quando lo stesso header è raggiungibile attraverso collegamenti simbolici diversi o copie duplicate nel progetto. La tripla `#ifndef` / `#define` / `#endif` è invece garantita dallo standard ed è sempre portabile.

### Esercizio 19.2 — Architettura a diamante con protezioni di inclusione e configurazione tramite direttive del preprocessore

**Descrizione**

Scrivi un programma C su quattro file (`misura.h`, `statistica.h`, `statistica.c`, `main.c`) che dimostri l'uso delle protezioni di inclusione su una dipendenza a diamante e delle direttive del preprocessore `#define`, `#undef`, `#ifndef`, `#if`, `#elif`, `#else`, `#endif` e `defined`.

1. In `misura.h` (protetto da `MISURA_H`) imposta `#ifndef LIVELLO_PRECISIONE` / `#define LIVELLO_PRECISIONE 2` / `#endif`, seleziona il formato `FMT_VAL` con `#if LIVELLO_PRECISIONE == 1` (`"%.1f"`), `#elif LIVELLO_PRECISIONE == 2` (`"%.2f"`), `#else` (`"%.3f"`), `#endif` e definisci `typedef struct misura { int32_t id; double valore; } misura_t;`.
2. In `statistica.h` (protetto da `STATISTICA_H`) includi `"misura.h"`, definisci `typedef struct riepilogo { size_t n; double min; double max; double media; } riepilogo_t;` e dichiara `bool calcola_riepilogo(const misura_t *arr, size_t n, riepilogo_t *out);` e `size_t conta_anomalie(const misura_t *arr, size_t n, double soglia);`.
3. In `statistica.c` includi `"statistica.h"`, definisci localmente `#define TOLLERANZA_ANOMALIA 1e-9` per il confronto `arr[i].valore > soglia + TOLLERANZA_ANOMALIA` dentro `conta_anomalie` e rimuovi la costante subito dopo con `#undef TOLLERANZA_ANOMALIA`.
4. In `main.c` includi `"misura.h"`, `"statistica.h"` e nuovamente `"misura.h"` (verificando che la protezione di inclusione impedisca errori di ridefinizione), controlla con `#if defined(MISURA_H) && defined(STATISTICA_H)` la corretta inclusione stampando `Config: precisione=<LIVELLO_PRECISIONE>`, poi leggi da `stdin` la prima riga `<n> <soglia>` (`0 <= n <= 64`) e `n` righe `<id> <valore>`, stampando riepilogo e numero di anomalie esattamente come nell'esempio.

**Concetti da tenere a mente**

- protezione di inclusione standard (`#ifndef`/`#define`/`#endif`) con nomi univoci non riservati
- risoluzione delle inclusioni multiple e a diamante tra più file di intestazione
- compilazione condizionale tramite `#ifndef`, `#if`, `#elif`, `#else`, `#endif` e `defined(...)`
- limitazione dell'ambito di una costante del preprocessore tramite `#define` e `#undef`

**Domande guida**

1. Quale errore di compilazione si verificherebbe in `main.c` se rimuovessi la protezione di inclusione da `misura.h`?
2. Perché `#ifndef LIVELLO_PRECISIONE` / `#define LIVELLO_PRECISIONE 2` / `#endif` permette di cambiare precisione dalla riga di comando del compilatore senza modificare `misura.h`?
3. Quale utilità ha `#undef TOLLERANZA_ANOMALIA` subito dopo `conta_anomalie` in `statistica.c`?
4. Perché non bisogna chiamare una protezione di inclusione `_MISURA_H` oppure `__MISURA_H__`?

**Esempio di esecuzione**

```input
4 25.0
101 21.5
102 25.0
103 28.4
104 26.1
```

```output
Config: precisione=2
Riepilogo (n=4): min=21.50 max=28.40 media=25.25
Anomalie (> 25.00): 2
```

## 19.3 Visibilità tra file: `static`, `extern` e `inline`

Quando un programma è formato da più unità di traduzione, non basta sapere *dove* un identificatore è visibile dentro un singolo file (la visibilità vista nel capitolo 7): occorre anche stabilire se lo stesso nome, dichiarato in file `.c` diversi, indica la stessa funzione o lo stesso oggetto oppure entità distinte. Questa proprietà si chiama **collegamento** (*linkage*): è la proprietà che stabilisce se un identificatore dichiarato in più unità di traduzione indica lo stesso oggetto o funzione (esterno, interno o assente).

In C esistono esattamente tre tipi di collegamento:

- **Collegamento esterno** (*external linkage*): è il comportamento predefinito per funzioni e variabili dichiarate a livello di file (fuori da qualsiasi funzione). Il simbolo viene esportato nel file oggetto e può essere collegato da altre unità di traduzione. Proprio per questo due file `.c` non possono definire entrambi una funzione non-`static` con lo stesso nome: il collegatore rifiuterebbe il duplicato.
- **Collegamento interno** (*internal linkage*): si ottiene qualificando con `static` una funzione o una variabile a livello di file. Il simbolo resta privato alla sola unità di traduzione in cui è definito e non è visibile al collegatore dall'esterno. Due file `.c` diversi possono quindi avere ciascuno una propria funzione `static int32_t helper(...)` senza alcun conflitto.
- **Nessun collegamento** (*no linkage*): riguarda parametri di funzione e variabili locali dichiarate dentro un blocco. Ogni dichiarazione indica un'entità distinta, visibile solo nel blocco.

Fai attenzione a non confondere i due significati di `static`:

- **Dentro una funzione** (capitolo 7): `static` cambia la *durata di vita* della variabile locale (da automatica a statica, cioè persistente per tutta l'esecuzione), ma la variabile continua a non avere collegamento ed è visibile solo in quella funzione.
- **A livello di file** (fuori da tutte le funzioni): `static` cambia il *collegamento* da esterno a interno, rendendo la funzione o la variabile privata al file `.c`.

In un modulo ben progettato, ogni funzione ausiliaria e ogni variabile di supporto che non fa parte dell'interfaccia pubblica dichiarata nel `.h` va marcata `static`. Questo riduce i simboli esposti al minimo indispensabile e impedisce collisioni accidentali quando il progetto cresce.

Come si condivide invece una costante o un dato definito in un file `.c` con altri file `.c`? Con la parola chiave `extern`. Scrivere `extern const int32_t LIMITE;` in un file di intestazione è una pura *dichiarazione*: informa il compilatore che esiste un oggetto `LIMITE` di tipo `const int32_t` con collegamento esterno, ma non riserva memoria. L'unica *definizione* (con l'inizializzatore) viene collocata in un solo file `.c`:

<!-- cod: id=19.3-b tipo=frammento -->
```c
/* in modulo.h: sola dichiarazione */
extern const int32_t LIMITE;

/* in modulo.c: unica definizione */
const int32_t LIMITE = 100;
```

In generale, usa `extern` quasi esclusivamente per costanti o tabelle `const` di sola lettura: condividere stato globale mutabile tra file rende il programma difficile da ragionare e da verificare. Ricorda inoltre che, a differenza delle variabili, i prototipi di funzione a livello di file hanno già collegamento esterno per default, quindi scrivere `extern` davanti a un prototipo è lecito ma superfluo.

Resta un caso frequente: piccole funzioni molto semplici (due o tre righe) che vuoi mettere direttamente nell'header affinché il compilatore possa sostituirle nel punto di chiamata eliminando il costo della chiamata di funzione. Se mettessi una normale funzione nell'header, violeresti la regola di definizione unica appena due file `.c` lo includessero. Il C offre la parola chiave `inline` con due modelli ben precisi:

1. **`static inline` nell'header**: è il modello più semplice e più usato. Ogni unità di traduzione riceve una propria definizione con collegamento interno; nessun simbolo esterno viene esportato e quindi non esistono mai conflitti al collegamento.
2. **`inline` nell'header + `extern inline` in esattamente un file `.c`**: la definizione `inline` (senza `static`) nell'header fornisce al compilatore il corpo da espandere, ma *non* emette una definizione esterna nel file oggetto. Se il compilatore sceglie di non espandere la funzione (per esempio con ottimizzazioni spente `-O0`) oppure se il programma prende l'indirizzo della funzione tramite un puntatore a funzione, il collegatore ha bisogno di un simbolo esterno reale. Per emetterlo una sola volta si scrive una dichiarazione `extern inline` (o una definizione non-`inline`) con la stessa firma in esattamente un file `.c`.

Secondo lo standard C23, le regole di collegamento e il modello `inline`/`extern inline` sono definiti con precisione: usare una funzione `inline` non-`static` senza fornire alcuna definizione esterna nel programma può provocare un errore del collegatore, mentre fornire definizioni `inline` diverse tra unità di traduzione causa **comportamento indefinito**.

### Esempio guidato

Questo esempio su tre file (`contatore.h`, `contatore.c`, `main.c`) combina tutti gli strumenti di collegamento: una costante condivisa `extern const`, una funzione ausiliaria `static` privata a `contatore.c`, un helper `static inline` nell'header e una funzione `inline` con definizione esterna `extern inline` di cui `main.c` prende esplicitamente l'indirizzo.

<!-- cod: id=19.3-a tipo=programma gruppo=cont file=contatore.h -->
```c
#ifndef CONTATORE_H
#define CONTATORE_H

#include <stdint.h>

extern const int32_t SOGLIA_MASSIMA;

static inline int32_t raddoppia(int32_t x) {
    return x * 2;
}

inline int32_t limita_valore(int32_t x, int32_t max_val) {
    return (x > max_val) ? max_val : x;
}

int32_t normalizza_punteggio(int32_t grezzo);

#endif
```

<!-- cod: id=19.3-c tipo=programma gruppo=cont file=contatore.c -->
```c
#include "contatore.h"

const int32_t SOGLIA_MASSIMA = 100;

extern inline int32_t limita_valore(int32_t x, int32_t max_val);

static int32_t aggiusta_negativo(int32_t x) {
    return (x < 0) ? 0 : x;
}

int32_t normalizza_punteggio(int32_t grezzo) {
    int32_t non_neg = aggiusta_negativo(grezzo);
    return limita_valore(non_neg, SOGLIA_MASSIMA);
}
```

<!-- cod: id=19.3-d tipo=programma gruppo=cont file=main.c -->
```c
#include <inttypes.h>
#include <stdio.h>
#include "contatore.h"

typedef int32_t (*limita_fn)(int32_t, int32_t);

int main(void) {
    limita_fn fn = limita_valore;
    int32_t a = normalizza_punteggio(-15);
    int32_t b = normalizza_punteggio(65);
    int32_t c = raddoppia(b);

    printf("Soglia condivisa: %" PRId32 "\n", SOGLIA_MASSIMA);
    printf("Normalizzati: %" PRId32 ", %" PRId32 "\n", a, b);
    printf("Raddoppiato e limitato: %" PRId32 "\n", fn(c, SOGLIA_MASSIMA));
    return 0;
}
```

```output
Soglia condivisa: 100
Normalizzati: 0, 65
Raddoppiato e limitato: 100
```

Osserva il ruolo di ogni qualificatore:

- `SOGLIA_MASSIMA` è dichiarata `extern const` in `contatore.h` e definita una sola volta in `contatore.c`: sia `contatore.c` sia `main.c` leggono lo stesso oggetto.
- `aggiusta_negativo` è `static` in `contatore.c`: non compare in `contatore.h` e un altro file `.c` potrebbe definire una propria funzione `static` con lo stesso nome senza collisioni.
- `raddoppia` è `static inline`: ogni unità di traduzione che include `contatore.h` può chiamarla senza esportare simboli al collegatore.
- `limita_valore` è `inline` in `contatore.h` e ha `extern inline` in `contatore.c`: quando `main.c` ne assegna l'indirizzo al puntatore a funzione `fn`, il collegatore trova la definizione esterna emessa da `contatore.o`.

> **Approfondimento — Il modello `inline` del C23 rispetto al C++**
> Chi conosce il C++ spesso si aspetta che scrivere `inline` in un header generi automaticamente un simbolo esterno unificato dal collegatore. In C non funziona così: una definizione `inline` priva di `static` nell'header è un'alternativa a disposizione del compilatore, non una definizione esterna. Se compili senza ottimizzazioni (`-O0`) o prendi l'indirizzo della funzione e dimentichi `extern inline` in un file `.c`, il collegatore segnala un simbolo non risolto. Per piccoli helper di modulo, `static inline` nell'header è quasi sempre la scelta più semplice e sicura.

### Esercizio 19.3 — Moduli con helper `static` omonimi, tabelle `extern const` e funzioni `static inline` / `extern inline`

**Descrizione**

Scrivi un programma C organizzato su cinque file (`valuta.h`, `valuta.c`, `imposta.h`, `imposta.c`, `main.c`) che eserciti in modo completo il collegamento esterno, il collegamento interno con `static`, le dichiarazioni `extern` e le funzioni `inline` del C23.

1. In `valuta.h` (protetto da `VALUTA_H`) dichiara `extern const int32_t TASSI_MILLI[];` ed `extern const size_t NUM_VALUTE;`, definisci `static inline int64_t cent_da_euro(int64_t euro)` (`euro * 100`), definisci `inline int64_t satura_cent(int64_t v, int64_t lo, int64_t hi)` (limita `v` a `[lo, hi]`) e dichiara `bool converti_cent(int64_t cent, size_t cod_valuta, int64_t *out);`.
2. In `valuta.c` definisci `const int32_t TASSI_MILLI[] = {1000, 1080, 860};`, `const size_t NUM_VALUTE = 3;`, la dichiarazione esterna `extern inline int64_t satura_cent(int64_t v, int64_t lo, int64_t hi);`, una funzione privata `static int64_t applica_fattore(int64_t base, int32_t milli)` che calcola il prodotto scalato per `1000` con arrotondamento al centesimo più vicino (`(base >= 0) ? (base * (int64_t)milli + 500) / 1000 : (base * (int64_t)milli - 500) / 1000`), e `converti_cent` (che verifica `cod_valuta < NUM_VALUTE`).
3. In `imposta.h` (protetto da `IMPOSTA_H`) dichiara `extern const int32_t ALIQUOTA_PREDEFINITA_MILLI;` e `int64_t calcola_lordo_cent(int64_t netto_cent, int32_t aliquota_milli);`.
4. In `imposta.c` definisci `const int32_t ALIQUOTA_PREDEFINITA_MILLI = 220;`, una propria funzione privata `static int64_t applica_fattore(int64_t base, int32_t milli)` con lo STESSO nome di quella in `valuta.c` (dimostrando che `static` evita collisioni al collegamento) che calcola `base + (base * (int64_t)milli + 500) / 1000` (o `- 500` se negativo), e `calcola_lordo_cent` (usa `ALIQUOTA_PREDEFINITA_MILLI` quando `aliquota_milli < 0`).
5. In `main.c` assegna l'indirizzo di `satura_cent` a un puntatore a funzione `clamp_fn fn_satura = satura_cent;` (verificando al collegamento l'emissione del simbolo `extern inline`) e leggi da `stdin` i comandi `EURO <e>`, `CONV <cent> <cod>`, `IVA <cent> <aliquota_milli>` e `CLAMP <v> <lo> <hi>`, stampando l'output esatto dell'esempio.

**Concetti da tenere a mente**

- collegamento interno con `static` a livello di file per evitare collisioni tra funzioni omonime in file `.c` diversi
- dichiarazione `extern` nell'header associata a un'unica definizione `const` nel file `.c`
- differenza tra `static inline` (collegamento interno) e `inline` nell'header + `extern inline` in un solo `.c`
- verifica della definizione esterna di una funzione `inline` prendendone l'indirizzo tramite puntatore a funzione

**Domande guida**

1. Perché il programma si collega senza errori nonostante sia `valuta.c` sia `imposta.c` definiscano una funzione chiamata `applica_fattore`?
2. Che cosa accadrebbe al collegamento se rimuovessi `extern inline int64_t satura_cent(...);` da `valuta.c` mantenendo `fn_satura = satura_cent;` in `main.c`?
3. Perché nell'header `valuta.h` scrivi `extern const size_t NUM_VALUTE;` senza inizializzatore, riservando `= 3` al solo `valuta.c`?
4. Qual è la differenza di collegamento tra `cent_da_euro` (`static inline`) e `satura_cent` (`inline` + `extern inline`)?

**Esempio di esecuzione**

```input
EURO 15
CONV 1000 1
CONV 1000 9
IVA 1000 -1
IVA 500 100
CLAMP 2500 0 2000
```

```output
EURO 15 -> 1500 cent
CONV 1000 [1] -> 1080 cent
CONV ERRORE VALUTA 9
IVA 1000 -> 1220 cent
IVA 500 -> 550 cent
CLAMP -> 2000 cent
```

## 19.4 Incapsulamento con i tipi opachi

Nelle prime tre sotto-sezioni hai visto come separare dichiarazioni e definizioni e come nascondere le funzioni ausiliarie con `static`. Tuttavia, se definisci l'intera `struct` dentro il file di intestazione — come abbiamo fatto per `punto_t` o `campione_t` — qualunque file che include l'header conosce tutti i campi della struttura. Per piccoli tipi puramente geometrici questo è comodo, ma per una struttura dati dinamica (come una pila, un buffer circolare o una tabella hash) espone due rischi seri:

1. qualsiasi chiamante può modificare direttamente i campi interni (`p->len = 999;` o `p->dati = nullptr;`), rompendo gli invarianti e provocando perdite di memoria o accessi fuori dai limiti;
2. ogni cambiamento alla rappresentazione interna (per esempio sostituire un array dinamico con una lista concatenata, o aggiungere un campo di supporto) obbliga a ricompilare tutti i file che includono l'header e rischia di rompere il codice che accedeva direttamente ai vecchi campi.

Il C risolve il problema a tempo di compilazione con il **tipo opaco** (*opaque type*): una struttura dichiarata nell'header in modo incompleto e definita solo nel file `.c`, accessibile dall'esterno tramite puntatore e funzioni.

Il trucco si basa su una caratteristica precisa dello standard C: puoi dichiarare una `struct` senza scriverne il corpo (dichiarazione incompleta) e creare un `typedef` per quel tipo nel file di intestazione:

<!-- cod: id=19.4-b tipo=frammento -->
```c
/* in pila.h: il chiamante sa che esiste struct pila, ma non ne conosce i campi */
typedef struct pila pila_t;
```

La definizione completa `struct pila { ... };` viene scritta esclusivamente dentro `pila.c`. Fuori da `pila.c`, il compilatore sa che `pila_t` è un tipo struttura, ma non ne conosce né i campi né la dimensione in byte: `pila_t` è un *tipo incompleto*.

Su un tipo incompleto il C permette soltanto le operazioni che non richiedono di conoscerne la dimensione o i campi:

- dichiarare puntatori `pila_t *` e `const pila_t *` (perché ogni puntatore a struttura ha una dimensione fissa nota al compilatore);
- passare e ricevere tali puntatori attraverso le funzioni dell'interfaccia pubblica (`pila_crea`, `pila_inserisci`, `pila_len`, `pila_distruggi`).

Al contrario, fuori da `pila.c`, il compilatore rifiuta con un errore di compilazione qualsiasi operazione che richieda la definizione completa della `struct`:

- allocare un'istanza sullo stack (`pila_t p;`);
- applicare l'operatore `sizeof(pila_t)` o `sizeof(*p)`;
- dereferenziare il puntatore o accedere ai campi (`p->len`, `(*p).dati`).

Secondo lo standard C23, i tipi struttura incompleti e i puntatori a tipi incompleti sono completamente definiti; tentare di dereferenziare un tipo incompleto, calcolarne `sizeof` o accedere ai suoi campi fuori dall'unità di traduzione che lo completa è una violazione di vincolo rifiutata dal compilatore.

Poiché il chiamante non può allocare un tipo opaco sullo stack, la progettazione dell'interfaccia segue sempre uno schema coerente:

- un **costruttore** (`pila_crea`) che alloca la struttura sullo heap, inizializza gli invarianti e restituisce `pila_t *` (oppure `nullptr` in caso di errore);
- un **distruttore** (`pila_distruggi`) che libera prima le risorse interne e poi la struttura stessa, ed è tollerante a `nullptr` (se riceve `nullptr` ritorna subito senza fare nulla, esattamente come `free`);
- **operazioni e interrogazioni** che ricevono `pila_t *` quando modificano lo stato e `const pila_t *` quando leggono soltanto (come `pila_len`).

Con questa separazione puoi cambiare completamente l'implementazione dentro `pila.c` — per esempio passare da un array dinamico a una lista concatenata — mantenendo invariato `pila.h`: nessun file chiamante va modificato.

> **Se vieni da Python** — In Python l'incapsulamento degli attributi si basa su convenzioni come il prefisso `_nome`, ma rimane aggirabile a tempo di esecuzione perché qualunque codice può comunque leggere o scrivere quell'attributo. In C un tipo opaco (struttura incompleta nell'header) impedisce l'accesso diretto ai campi già a tempo di compilazione.

### Esempio guidato

Incapsuliamo una pila dinamica di interi `int32_t` come tipo opaco su tre file (`pila.h`, `pila.c`, `main.c`). Nota che `pila.h` non rivela nulla sulla rappresentazione interna (array dinamico con raddoppio).

<!-- cod: id=19.4-a tipo=programma gruppo=pila file=pila.h -->
```c
#ifndef PILA_H
#define PILA_H

#include <stddef.h>
#include <stdint.h>

typedef struct pila pila_t;

pila_t *pila_crea(size_t cap_iniziale);
void pila_distruggi(pila_t *p);
bool pila_inserisci(pila_t *p, int32_t valore);
bool pila_estrai(pila_t *p, int32_t *out);
size_t pila_len(const pila_t *p);

#endif
```

<!-- cod: id=19.4-c tipo=programma gruppo=pila file=pila.c -->
```c
#include "pila.h"
#include <stdlib.h>

struct pila {
    int32_t *dati;
    size_t len;
    size_t cap;
};

pila_t *pila_crea(size_t cap_iniziale) {
    size_t cap = (cap_iniziale > 0) ? cap_iniziale : 4;
    pila_t *p = malloc(sizeof(*p));
    if (p == nullptr) {
        return nullptr;
    }
    p->dati = malloc(cap * sizeof(*p->dati));
    if (p->dati == nullptr) {
        free(p);
        return nullptr;
    }
    p->len = 0;
    p->cap = cap;
    return p;
}

void pila_distruggi(pila_t *p) {
    if (p == nullptr) {
        return;
    }
    free(p->dati);
    free(p);
}

bool pila_inserisci(pila_t *p, int32_t valore) {
    if (p == nullptr) {
        return false;
    }
    if (p->len == p->cap) {
        if (p->cap > SIZE_MAX / 2 / sizeof(*p->dati)) {
            return false;
        }
        size_t nuova_cap = p->cap * 2;
        int32_t *nuovi = realloc(p->dati, nuova_cap * sizeof(*nuovi));
        if (nuovi == nullptr) {
            return false;
        }
        p->dati = nuovi;
        p->cap = nuova_cap;
    }
    p->dati[p->len] = valore;
    ++p->len;
    return true;
}

bool pila_estrai(pila_t *p, int32_t *out) {
    if (p == nullptr || p->len == 0) {
        return false;
    }
    --p->len;
    if (out != nullptr) {
        *out = p->dati[p->len];
    }
    return true;
}

size_t pila_len(const pila_t *p) {
    return (p != nullptr) ? p->len : 0;
}
```

<!-- cod: id=19.4-d tipo=programma gruppo=pila file=main.c -->
```c
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include "pila.h"

int main(void) {
    pila_t *p = pila_crea(2);
    if (p == nullptr) {
        return EXIT_FAILURE;
    }
    pila_inserisci(p, 10);
    pila_inserisci(p, 20);
    pila_inserisci(p, 30);
    printf("Elementi nella pila: %zu\n", pila_len(p));

    int32_t v = 0;
    while (pila_estrai(p, &v)) {
        printf("Estratto: %" PRId32 "\n", v);
    }
    pila_distruggi(p);
    pila_distruggi(nullptr);
    return EXIT_SUCCESS;
}
```

```output
Elementi nella pila: 3
Estratto: 30
Estratto: 20
Estratto: 10
```

Che cosa succede se un file esterno prova a violare l'incapsulamento applicando `sizeof` al tipo opaco o leggendo un campo con `->`? Il blocco seguente non compila: il compilatore segnala che `pila_t` è un tipo incompleto e non può determinarne la dimensione né dereferenziare il campo `len`.

<!-- cod: id=19.4-e tipo=errore -->
```c
#include <stddef.h>

typedef struct pila pila_t;

size_t violazione(const pila_t *p) {
    size_t dim = sizeof(pila_t);
    return dim + p->len;
}
```

Osserva come `main.c` nell'esempio guidato lavora senza mai conoscere l'esistenza di `dati`, `len` o `cap`: crea la pila con `pila_crea`, la interroga con `pila_len`, la svuota con `pila_estrai` e la libera con `pila_distruggi` (verificando anche che `pila_distruggi(nullptr)` sia innocuo).

> **Approfondimento — Come disegnare un'API opaca pulita in C**
> Un modulo opaco ben progettato segue quattro regole semplici: adotta un prefisso comune per tutti i simboli pubblici (`pila_crea`, `pila_distruggi`, `pila_len`) per evitare collisioni di nomi; qualifica con `const` il puntatore in tutte le funzioni che non modificano la struttura (`const pila_t *`); rende sicuro il distruttore su `nullptr`; documenta nell'header le precondizioni (per esempio i limiti sui parametri) e le regole di possesso della memoria.

### Esercizio 19.4 — Buffer circolare a sovrascrittura incapsulato come tipo opaco

**Descrizione**

Scrivi un programma C organizzato su tre file (`anello.h`, `anello.c`, `main.c`) che incapsuli un buffer circolare a capacità fissa per campioni `int32_t` come **tipo opaco**.

1. In `anello.h` (protetto da `ANELLO_H`) dichiara SOLO il tipo incompleto `typedef struct anello anello_t;` (nessun campo esposto!) e i prototipi: `anello_t *anello_crea(size_t cap);` (accetta `1 <= cap <= 64`, altrimenti `nullptr`), `void anello_distruggi(anello_t *a);` (sicura su `nullptr`), `bool anello_inserisci(anello_t *a, int32_t val, bool *sovrascritto);` (se il buffer è pieno sovrascrive l'elemento più vecchio avanzando l'indice di inizio, incrementa il contatore interno `scartati` e imposta `*sovrascritto = true`), `bool anello_estrai(anello_t *a, int32_t *out);`, `bool anello_leggi_i(const anello_t *a, size_t idx, int32_t *out);` (legge il `idx`-esimo elemento dal più vecchio al più recente), `void anello_svuota(anello_t *a);` (svuota gli elementi preservando `cap` e `scartati`), `size_t anello_len(const anello_t *a);`, `size_t anello_cap(const anello_t *a);` e `size_t anello_scartati(const anello_t *a);`.
2. In `anello.c` definisci privatamente `struct anello` e implementa tutte le funzioni preservando tutti gli invarianti.
3. In `main.c` usa esclusivamente `anello_t *` e le funzioni pubbliche di `anello.h`: leggi dalla prima riga `cap` (`1 <= cap <= 64`), verifica `anello_crea(0) == nullptr` e `anello_distruggi(nullptr)`, poi leggi da `stdin` i comandi `PUSH <val>`, `POP`, `PEEK <idx>`, `CLEAR`, `STAT` e `DUMP`, producendo esattamente l'output dell'esempio e distruggendo il buffer al termine.

**Concetti da tenere a mente**

- dichiarazione incompleta `typedef struct anello anello_t;` nell'header e definizione completa nel solo file `.c`
- impossibilità per `main.c` di leggere o corrompere i campi interni (`inizio`, `len`, `scartati`, `dati`)
- ciclo di vita completo sullo heap: `anello_crea` con validazione e `anello_distruggi` sicuro su `nullptr`
- lettura indicizzata dell'anello tramite `anello_leggi_i` senza esporre la geometria circolare interna

**Domande guida**

1. Perché `main.c` non può dichiarare `anello_t buf;` sullo stack né scrivere `a->scartati = 0;`?
2. Come fa `anello_inserisci` ad aggiornare correttamente `inizio`, `len` e `scartati` quando il buffer è già pieno (`len == cap`)?
3. Perché `anello_distruggi` deve gestire esplicitamente il caso `a == nullptr` senza dereferenziare `a`?
4. Quale vantaggio offre esporre `anello_leggi_i` invece di restituire un puntatore diretto all'array interno `dati`?

**Esempio di esecuzione**

```input
3
PUSH 10
PUSH 20
PUSH 30
PUSH 40
DUMP
PEEK 1
POP
STAT
CLEAR
POP
DUMP
```

```output
PUSH 10 (len=1)
PUSH 20 (len=2)
PUSH 30 (len=3)
PUSH 40 (sovrascritto, len=3)
DUMP (3/3): 20 30 40
PEEK[1]: 30
POP: 20
STAT len=2 cap=3 scartati=1
CLEAR
POP: VUOTO
DUMP (0/3): (vuoto)
```

## 19.5 Organizzare una libreria: la tabella hash come tipo opaco

Siamo arrivati al traguardo centrale del percorso iniziato nei capitoli precedenti. Nel capitolo 18 hai costruito una tabella hash generica con `void *`, callback per hash e uguaglianza, ridimensionamento automatico e regole esplicite di possesso della memoria, ma l'intera implementazione viveva nello stesso file del programma principale e la `struct` interna era visibile a chiunque. Ora hai tutti gli strumenti per trasformarla in una vera **libreria modulare riutilizzabile** su più file (`tabella_hash.h` e `tabella_hash.c`), pronta per essere collegata a qualunque programma — compreso l'interprete del capitolo finale (lo vedremo nel capitolo 26).

Progettiamo con cura il file di intestazione `tabella_hash.h`. Un header ben disegnato deve essere autosufficiente, protetto da una protezione di inclusione (`TABELLA_HASH_H`), dotato di un prefisso uniforme (`ht_`) e capace di esporre *esattamente* ciò che serve al chiamante, nulla di più:

- **Tipo opaco**: `typedef struct tabella_hash tabella_hash_t;`. La `struct nodo_ht` e i campi di `struct tabella_hash` (`secchi`, `cap`, `len`, callback) non compaiono nell'header.
- **Tipi callback**: `ht_hash_fn`, `ht_uguali_fn`, `ht_distruggi_fn` e `ht_visita_fn` (con contesto `void *ctx`).
- **Enumerazione di esito**: `ht_esito_t` (`HT_ERRORE = -1`, `HT_AGGIORNATO = 0`, `HT_INSERITO = 1`) per distinguere in modo inequivocabile un fallimento di allocazione da un aggiornamento o da un nuovo inserimento.
- **Struttura di configurazione**: `ht_config_t`, contenente `cap_iniziale`, `hash`, `uguali`, `distruggi_chiave` e `distruggi_valore`. Passare `const ht_config_t *cfg` a `ht_crea` evita lunghe liste di parametri posizionali e si abbina perfettamente agli inizializzatori designati.
- **Operazioni pubbliche ed helper per stringhe**: `ht_crea`, `ht_distruggi` (sicuro su `nullptr`), `ht_inserisci`, `ht_cerca`, `ht_rimuovi`, `ht_estrai`, `ht_visita`, `ht_len`, `ht_cap`, più le callback pronte all'uso `ht_hash_stringa` (FNV-1a su `unsigned char`) e `ht_uguali_stringa`.

Nel file di implementazione `tabella_hash.c`, aperto da `#include "tabella_hash.h"`, restano confinati tutti i dettagli privati:

- la definizione di `struct nodo_ht` (che conserva `chiave`, `valore`, `hash` precalcolato e puntatore `prox`);
- la definizione completa di `struct tabella_hash`;
- la funzione `static bool ht_ridimensiona(tabella_hash_t *t, size_t nuova_cap)`, con collegamento interno, invisibile al collegatore e impossibile da chiamare dall'esterno.

Secondo lo standard C23, questo schema di incapsulamento (tipi opachi, struttura di configurazione e funzioni `static` interne) è completamente definito e separa nettamente l'interfaccia pubblica dai dettagli implementativi. Un programma chiamante come `main.c` può creare più istanze indipendenti di `tabella_hash_t`, ciascuna con il proprio tipo di chiave e il proprio contratto di possesso (proprietario o in prestito), senza mai poter toccare i secchi o corrompere `len` e `cap`.

### Esempio guidato

Ecco la libreria opaca completa (`tabella_hash.h` e `tabella_hash.c`) collegata a un `main.c` che gestisce un archivio di parametri di sistema: le chiavi sono stringhe `char *` possedute dalla tabella (`strdup` + `free`) e i valori sono `int32_t *` posseduti (`malloc` + `free`). Il programma crea la tabella con `ht_config_t`, inserisce e aggiorna parametri, esegue una visita con contesto `ctx` per sommare i valori, estrae una voce trasferendone il possesso con `ht_estrai` e distrugge la tabella in sicurezza.

<!-- cod: id=19.5-a tipo=programma gruppo=htlib file=tabella_hash.h -->
```c
#ifndef TABELLA_HASH_H
#define TABELLA_HASH_H

#include <stddef.h>
#include <stdint.h>

typedef struct tabella_hash tabella_hash_t;
typedef uint64_t (*ht_hash_fn)(const void *chiave);
typedef bool (*ht_uguali_fn)(const void *a, const void *b);
typedef void (*ht_distruggi_fn)(void *ptr);
typedef void (*ht_visita_fn)(const void *chiave, void *valore, void *ctx);

typedef enum ht_esito {
    HT_ERRORE = -1,
    HT_AGGIORNATO = 0,
    HT_INSERITO = 1
} ht_esito_t;

typedef struct ht_config {
    size_t cap_iniziale;
    ht_hash_fn hash;
    ht_uguali_fn uguali;
    ht_distruggi_fn distruggi_chiave;
    ht_distruggi_fn distruggi_valore;
} ht_config_t;

tabella_hash_t *ht_crea(const ht_config_t *cfg);
void ht_distruggi(tabella_hash_t *t);
ht_esito_t ht_inserisci(tabella_hash_t *t, void *chiave, void *valore);
void *ht_cerca(const tabella_hash_t *t, const void *chiave);
bool ht_rimuovi(tabella_hash_t *t, const void *chiave);
bool ht_estrai(tabella_hash_t *t, const void *chiave, void **val_out);
void ht_visita(const tabella_hash_t *t, ht_visita_fn fn, void *ctx);
size_t ht_len(const tabella_hash_t *t);
size_t ht_cap(const tabella_hash_t *t);
uint64_t ht_hash_stringa(const void *chiave);
bool ht_uguali_stringa(const void *a, const void *b);

#endif
```

<!-- cod: id=19.5-b tipo=programma gruppo=htlib file=tabella_hash.c -->
```c
#include "tabella_hash.h"
#include <stdlib.h>
#include <string.h>

typedef struct nodo_ht {
    void *chiave;
    void *valore;
    uint64_t hash;
    struct nodo_ht *prox;
} nodo_ht_t;

struct tabella_hash {
    nodo_ht_t **secchi;
    size_t cap;
    size_t len;
    ht_hash_fn hash;
    ht_uguali_fn uguali;
    ht_distruggi_fn d_chiave;
    ht_distruggi_fn d_valore;
};

static bool ht_ridimensiona(tabella_hash_t *t, size_t nuova_cap) {
    if (nuova_cap == 0 || nuova_cap > SIZE_MAX / sizeof(*t->secchi)) { return false; }
    nodo_ht_t **nuovi = malloc(nuova_cap * sizeof(*nuovi));
    if (nuovi == nullptr) { return false; }
    for (size_t i = 0; i < nuova_cap; ++i) { nuovi[i] = nullptr; }
    for (size_t i = 0; i < t->cap; ++i) {
        nodo_ht_t *c = t->secchi[i];
        while (c != nullptr) {
            nodo_ht_t *p = c->prox;
            size_t idx = (size_t)(c->hash % nuova_cap);
            c->prox = nuovi[idx];
            nuovi[idx] = c;
            c = p;
        }
    }
    free(t->secchi);
    t->secchi = nuovi;
    t->cap = nuova_cap;
    return true;
}

tabella_hash_t *ht_crea(const ht_config_t *cfg) {
    if (cfg == nullptr || cfg->hash == nullptr || cfg->uguali == nullptr) { return nullptr; }
    size_t cap = (cfg->cap_iniziale > 0) ? cfg->cap_iniziale : 8;
    tabella_hash_t *t = malloc(sizeof(*t));
    if (t == nullptr) { return nullptr; }
    t->secchi = malloc(cap * sizeof(*t->secchi));
    if (t->secchi == nullptr) { free(t); return nullptr; }
    for (size_t i = 0; i < cap; ++i) { t->secchi[i] = nullptr; }
    t->cap = cap; t->len = 0;
    t->hash = cfg->hash; t->uguali = cfg->uguali;
    t->d_chiave = cfg->distruggi_chiave; t->d_valore = cfg->distruggi_valore;
    return t;
}

void ht_distruggi(tabella_hash_t *t) {
    if (t == nullptr) { return; }
    for (size_t i = 0; i < t->cap; ++i) {
        nodo_ht_t *c = t->secchi[i];
        while (c != nullptr) {
            nodo_ht_t *p = c->prox;
            if (t->d_chiave != nullptr) { t->d_chiave(c->chiave); }
            if (t->d_valore != nullptr) { t->d_valore(c->valore); }
            free(c);
            c = p;
        }
    }
    free(t->secchi);
    free(t);
}

ht_esito_t ht_inserisci(tabella_hash_t *t, void *chiave, void *valore) {
    if (t == nullptr || chiave == nullptr) { return HT_ERRORE; }
    uint64_t h = t->hash(chiave);
    size_t idx = (size_t)(h % t->cap);
    for (nodo_ht_t *c = t->secchi[idx]; c != nullptr; c = c->prox) {
        if (c->hash == h && t->uguali(c->chiave, chiave)) {
            if (t->d_valore != nullptr && c->valore != valore) { t->d_valore(c->valore); }
            c->valore = valore;
            if (t->d_chiave != nullptr && c->chiave != chiave) { t->d_chiave(chiave); }
            return HT_AGGIORNATO;
        }
    }
    if ((t->len + 1) * 4 > t->cap * 3) {
        if (!ht_ridimensiona(t, t->cap * 2)) { return HT_ERRORE; }
        idx = (size_t)(h % t->cap);
    }
    nodo_ht_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return HT_ERRORE; }
    *n = (nodo_ht_t){.chiave = chiave, .valore = valore, .hash = h, .prox = t->secchi[idx]};
    t->secchi[idx] = n;
    ++t->len;
    return HT_INSERITO;
}

void *ht_cerca(const tabella_hash_t *t, const void *chiave) {
    if (t == nullptr || chiave == nullptr) { return nullptr; }
    uint64_t h = t->hash(chiave);
    size_t idx = (size_t)(h % t->cap);
    for (const nodo_ht_t *c = t->secchi[idx]; c != nullptr; c = c->prox) {
        if (c->hash == h && t->uguali(c->chiave, chiave)) { return c->valore; }
    }
    return nullptr;
}

bool ht_estrai(tabella_hash_t *t, const void *chiave, void **val_out) {
    if (t == nullptr || chiave == nullptr) { return false; }
    uint64_t h = t->hash(chiave);
    size_t idx = (size_t)(h % t->cap);
    nodo_ht_t **cur = &t->secchi[idx];
    while (*cur != nullptr && ((*cur)->hash != h || !t->uguali((*cur)->chiave, chiave))) {
        cur = &(*cur)->prox;
    }
    if (*cur == nullptr) { return false; }
    nodo_ht_t *d = *cur;
    *cur = d->prox;
    if (t->d_chiave != nullptr) { t->d_chiave(d->chiave); }
    if (val_out != nullptr) { *val_out = d->valore; }
    else if (t->d_valore != nullptr) { t->d_valore(d->valore); }
    free(d);
    --t->len;
    return true;
}

bool ht_rimuovi(tabella_hash_t *t, const void *chiave) { return ht_estrai(t, chiave, nullptr); }

void ht_visita(const tabella_hash_t *t, ht_visita_fn fn, void *ctx) {
    if (t == nullptr || fn == nullptr) { return; }
    for (size_t i = 0; i < t->cap; ++i) {
        for (const nodo_ht_t *c = t->secchi[i]; c != nullptr; c = c->prox) {
            fn(c->chiave, c->valore, ctx);
        }
    }
}

size_t ht_len(const tabella_hash_t *t) { return (t != nullptr) ? t->len : 0; }
size_t ht_cap(const tabella_hash_t *t) { return (t != nullptr) ? t->cap : 0; }

uint64_t ht_hash_stringa(const void *chiave) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = chiave; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return h;
}

bool ht_uguali_stringa(const void *a, const void *b) { return strcmp(a, b) == 0; }
```

<!-- cod: id=19.5-c tipo=programma gruppo=htlib file=main.c -->
```c
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "tabella_hash.h"

typedef struct somma_ctx {
    int64_t totale;
    size_t conteggio;
} somma_ctx_t;

static void accumula_valori(const void *chiave, void *valore, void *ctx) {
    (void)chiave;
    somma_ctx_t *s = ctx;
    s->totale += *(const int32_t *)valore;
    ++s->conteggio;
}

static bool imposta_parametro(tabella_hash_t *t, const char *nome, int32_t val) {
    char *k = strdup(nome);
    int32_t *v = malloc(sizeof(*v));
    if (k == nullptr || v == nullptr) {
        free(k);
        free(v);
        return false;
    }
    *v = val;
    ht_esito_t es = ht_inserisci(t, k, v);
    if (es == HT_ERRORE) {
        free(k);
        free(v);
        return false;
    }
    return true;
}

int main(void) {
    tabella_hash_t *cfg = ht_crea(&(ht_config_t){
        .cap_iniziale = 4,
        .hash = ht_hash_stringa,
        .uguali = ht_uguali_stringa,
        .distruggi_chiave = free,
        .distruggi_valore = free
    });
    if (cfg == nullptr) { return EXIT_FAILURE; }

    imposta_parametro(cfg, "porta", 8080);
    imposta_parametro(cfg, "timeout", 30);
    imposta_parametro(cfg, "connessioni", 64);
    imposta_parametro(cfg, "timeout", 45);

    const int32_t *t_val = ht_cerca(cfg, "timeout");
    if (t_val != nullptr) {
        printf("timeout = %" PRId32 "\n", *t_val);
    }

    somma_ctx_t ctx = {};
    ht_visita(cfg, accumula_valori, &ctx);
    printf("Voci=%zu (cap=%zu), somma=%" PRId64 "\n",
           ctx.conteggio, ht_cap(cfg), ctx.totale);

    void *estratto = nullptr;
    if (ht_estrai(cfg, "porta", &estratto)) {
        int32_t *p = estratto;
        printf("Estratta porta = %" PRId32 " (rimaste %zu)\n", *p, ht_len(cfg));
        free(p);
    }

    ht_distruggi(cfg);
    return EXIT_SUCCESS;
}
```

```output
timeout = 45
Voci=3 (cap=4), somma=8189
Estratta porta = 8080 (rimaste 2)
```

Osserva come `main.c` dialoga con la libreria:

- In `ht_crea` passiamo un letterale composto `&(ht_config_t){...}` con inizializzatori designati: la chiamata è leggibile e il tipo `tabella_hash_t` resta completamente opaco.
- `imposta_parametro` alloca sia la chiave (`strdup`) sia il valore (`malloc`) e ne cede il possesso alla tabella; se `ht_inserisci` aggiorna `"timeout"`, la libreria libera automaticamente il vecchio valore `30` e la chiave duplicata.
- `ht_estrai` rimuove `"porta"`, libera la chiave interna e restituisce il possesso del valore `int32_t *` a `main.c`, che lo stampa e lo libera con `free(p)`.
- Infine `ht_distruggi(cfg)` libera tutti i nodi, le chiavi e i valori rimasti senza lasciare perdite di memoria.

> **C23** — L'esempio usa `strdup` (standardizzata in `<string.h>` dal C23), `bool`/`true`/`false` come parole chiave native, `nullptr` e l'inizializzatore vuoto `{}` (`somma_ctx_t ctx = {};`). Con compilatori precedenti al C23 occorre includere `<stdbool.h>`, usare `NULL` al posto di `nullptr`, scrivere `{0}` invece di `{}` e implementare manualmente una piccola funzione di duplicazione stringa se `strdup` non è disponibile.

> **Approfondimento — Il pattern della `struct` di configurazione (`ht_config_t`) in C23**
> Passare `&(ht_config_t){.cap_iniziale = 8, .hash = ..., .uguali = ...}` a `ht_crea` offre tre vantaggi concreti. Primo, ogni chiamata si documenta da sola senza dover ricordare l'ordine di cinque argomenti. Secondo, tutti i campi omessi nell'inizializzatore designato vengono azzerati automaticamente: omettere `.distruggi_valore` imposta `nullptr`, attivando senza sforzo la modalità prestito. Terzo, se in futuro aggiungi un nuovo campo opzionale a `ht_config_t`, il codice esistente continua a compilare senza modifiche.

### Esercizio 19.5 — Libreria opaca `tabella_hash` su più file con doppio indice (proprietario e in prestito)

**Descrizione**

Realizza la libreria riutilizzabile della **tabella hash generica come tipo opaco** organizzata su tre file (`tabella_hash.h`, `tabella_hash.c`, `main.c`).

1. In `tabella_hash.h` (protetto da `TABELLA_HASH_H`) dichiara il tipo opaco `typedef struct tabella_hash tabella_hash_t;`, i tipi callback (`ht_hash_fn`, `ht_uguali_fn`, `ht_distruggi_fn`, `ht_visita_fn`), `typedef enum ht_esito { HT_ERRORE = -1, HT_AGGIORNATO = 0, HT_INSERITO = 1 } ht_esito_t;`, la struct di configurazione `typedef struct ht_config { size_t cap_iniziale; ht_hash_fn hash; ht_uguali_fn uguali; ht_distruggi_fn distruggi_chiave; ht_distruggi_fn distruggi_valore; } ht_config_t;`, gli helper per stringhe `ht_hash_stringa` e `ht_uguali_stringa` e le operazioni `ht_crea(const ht_config_t *cfg)`, `ht_distruggi`, `ht_inserisci`, `ht_cerca`, `ht_rimuovi`, `ht_estrai`, `ht_visita`, `ht_len` e `ht_cap`.
2. In `tabella_hash.c` definisci privatamente `struct nodo_ht`, `struct tabella_hash` e la funzione `static bool ht_ridimensiona` (raddoppio automatico al superamento del fattore di carico `0.75`: `(len + 1) * 4 > cap * 3`), implementando l'intera libreria con gestione sicura del possesso (su aggiornamento libera vecchio valore e chiave ridondante se posseduti; `ht_distruggi(nullptr)` non fa nulla).
3. In `main.c` modella `typedef struct studente { int32_t matricola; char *nome; int32_t voto; size_t *cont_dist; } studente_t;` e istanzia DUE tabelle opache con `ht_config_t`: `per_matricola` (chiavi `int32_t *` possedute con `free`, valori `studente_t *` posseduti con `distruggi_studente`) e `per_nome` (chiavi `char *` possedute con `free` usando `ht_hash_stringa`/`ht_uguali_stringa`, valori `studente_t *` **in prestito** lasciando `.distruggi_valore = nullptr`). Leggi da `stdin` i comandi `ADD <matricola> <nome> <voto>` (nomi distinti tra studenti diversi; su aggiornamento di una matricola esistente rimuove prima il vecchio nome da `per_nome`), `BY_ID <matricola>`, `BY_NAME <nome>`, `DEL <matricola>` (estrae da `per_matricola` con `ht_estrai`, rimuove da `per_nome` e libera lo studente) e `MEDIA` (usa `ht_visita` su `per_matricola` con un contesto `ctx`). Distruggi `per_nome` PRIMA di `per_matricola` e stampa il bilancio finale `FINE creati=<cre> distrutti=<dis>` esattamente come nell'esempio.

**Concetti da tenere a mente**

- tabella hash generica incapsulata come tipo opaco (`struct nodo_ht` e `struct tabella_hash` private in `tabella_hash.c`)
- configurazione tramite `ht_config_t` e inizializzatori designati con distruttori indipendenti
- riutilizzo della stessa libreria opaca su due domini distinti (chiavi `int32_t *` e chiavi stringa)
- coerenza tra tabella proprietaria (`per_matricola`) e indice secondario in prestito (`per_nome`) e ordine di distruzione

**Domande guida**

1. Perché in `tabella_hash.h` la `struct nodo_ht` non compare affatto mentre `tabella_hash_t` è solo una dichiarazione incompleta?
2. In che modo passare `&(ht_config_t){.cap_iniziale = 4, .hash = ht_hash_stringa, .uguali = ht_uguali_stringa, .distruggi_chiave = free}` imposta automaticamente `per_nome` in modalità prestito per i valori?
3. Perché nel comando `DEL` conviene usare `ht_estrai` su `per_matricola` prima di rimuovere il nome da `per_nome`?
4. Perché `main.c` deve chiamare `ht_distruggi(per_nome)` prima di `ht_distruggi(per_matricola)`?

**Esempio di esecuzione**

```input
ADD 101 Lucia 28
ADD 102 Marco 24
ADD 103 Elena 30
ADD 104 Davide 26
BY_ID 103
BY_NAME Marco
ADD 102 MarcoB 27
BY_NAME Marco
BY_NAME MarcoB
MEDIA
DEL 101
BY_NAME Lucia
MEDIA
```

```output
ADD 101: INSERITO
ADD 102: INSERITO
ADD 103: INSERITO
ADD 104: INSERITO
ID 103: Elena (30)
NAME Marco: #102 (24)
ADD 102: AGGIORNATO
NAME Marco: NON TROVATO
NAME MarcoB: #102 (27)
MEDIA (len=4, cap=8): 27.75
DEL 101: OK
NAME Lucia: NON TROVATO
MEDIA (len=3, cap=8): 27.67
FINE creati=5 distrutti=5
```

## Riepilogo

- In un programma su più file l'interfaccia pubblica di un modulo risiede nel **file di intestazione** (`.h`, con sole dichiarazioni di tipi, costanti e prototipi) e l'implementazione risiede nel corrispondente file sorgente (`.c`). Ogni `.c`, dopo l'espansione del preprocessore, forma un'**unità di traduzione** compilata indipendentemente in un file oggetto mediante **compilazione separata**; il collegatore unisce i file oggetto nell'eseguibile finale.
- Ogni file `modulo.c` deve includere `"modulo.h"` come prima direttiva per verificare che l'header sia autosufficiente e che i prototipi coincidano con le definizioni.
- Ogni header va racchiuso in una **protezione di inclusione** standard (`#ifndef NOME_H` / `#define NOME_H` / ... / `#endif`) con nome univoco e non riservato (mai prefissi `__` o `_Maiuscola`) per gestire inclusioni multiple e dipendenze a diamante. Le direttive `#define`, `#undef`, `#ifdef`, `#ifndef`, `#if`, `#elif`, `#else`, `#endif` e `defined(...)` controllano la compilazione condizionale.
- Il **collegamento** determina la condivisione dei simboli tra unità di traduzione: esterno (predefinito a livello di file), interno (`static` a livello di file, per nascondere helper e stato privato) e assente (variabili locali). Le costanti condivise si dichiarano `extern const` nell'header e si definiscono una sola volta in un `.c`. Per le funzioni `inline` negli header si usa `static inline` (collegamento interno) oppure la coppia `inline` nell'header + `extern inline` in esattamente un `.c`.
- Un **tipo opaco** (`typedef struct nome nome_t;` nell'header, definizione completa `struct nome { ... };` nel solo `.c`) impedisce al codice chiamante di usare `sizeof(nome_t)`, allocare sullo stack o accedere ai campi con `->`, proteggendo gli invarianti del modulo.
- La tabella hash generica del capitolo 18, incapsulata come libreria opaca (`tabella_hash.h` e `tabella_hash.c`) con `ht_config_t` e distruttori indipendenti, è ora un componente riutilizzabile pronto per progetti complessi (lo vedremo nel capitolo 26).

## Errori comuni

- **Definire funzioni non-`inline` o variabili globali non-`static` dentro un file di intestazione (`.h`)**: quando l'header viene incluso da più file `.c`, ogni unità di traduzione riceve una copia della definizione e il collegatore segnala un errore di definizione multipla. Lascia nell'header solo dichiarazioni, `static inline` o `inline` accompagnate da `extern inline` in un `.c`.
- **Dimenticare la protezione di inclusione in un header, riusare lo stesso nome di macro in due header diversi o usare nomi riservati (`_NOME_H`, `__NOME_H__`)**: nel primo caso le inclusioni a diamante causano errori di ridefinizione di tipi; nel secondo un header nasconde silenziosamente l'altro; nel terzo si viola lo standard C23 provocando comportamento indefinito.
- **Scrivere una funzione `inline` senza `static` nell'header dimenticando `extern inline` in un file `.c`**: a ottimizzazioni spente (`-O0`) o quando si prende l'indirizzo della funzione con un puntatore a funzione, il collegatore fallisce con un errore di simbolo non risolto.
- **Dimenticare di includere `"modulo.h"` come prima direttiva in `modulo.c`**: eventuali header mancanti dentro `modulo.h` o divergenze tra prototipi e definizioni possono restare nascosti fino a quando un altro file non include l'header (causando comportamento indefinito se le firme divergono).
- **Esporre la definizione completa della `struct` nell'header di una libreria invece di usare un tipo opaco, oppure tentare `sizeof(tipo_opaco_t)` o `p->campo` fuori dal `.c`**: nel primo caso si perde l'incapsulamento degli invarianti; nel secondo il compilatore rifiuta il codice perché il tipo è incompleto.

## Prima di proseguire

- [ ] So dividere un programma in file di intestazione (`.h`) e file sorgenti (`.c`), compilarli separatamente in file oggetto e collegarli in un unico eseguibile.
- [ ] So scrivere protezioni di inclusione standard con nomi validi e usare `#define`, `#undef`, `#if`, `#elif`, `#else`, `#endif` e `defined(...)` per la compilazione condizionale.
- [ ] So distinguere collegamento esterno, interno (`static` a livello di file) e assente, usare `extern const` per dati condivisi e applicare correttamente sia `static inline` sia `inline` + `extern inline`.
- [ ] So progettare e implementare un tipo opaco con dichiarazione incompleta nell'header, costruttore sullo heap, getter `const` e distruttore tollerante a `nullptr`.
- [ ] So organizzare la tabella hash generica come libreria opaca su più file (`tabella_hash.h` e `tabella_hash.c`) e usarla con più istanze e politiche di possesso diverse.
