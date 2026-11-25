# Capitolo 11 — Memoria dinamica

> **In questo capitolo imparerai a:**
> - Distinguere durata di vita e ruolo di stack e heap
> - Allocare, ridimensionare e liberare memoria dinamica con `malloc`, `calloc`, `realloc` e `free` controllando sempre i fallimenti
> - Costruire array dinamici che crescono in modo sicuro senza perdere il puntatore originale
> - Riconoscere ed eliminare perdite di memoria, uso dopo la liberazione e doppia liberazione con i sanitizer

> **Ti servono:** durata di vita delle variabili (capitolo 7), array (capitolo 8), stringhe e `buffer overflow` (capitolo 9), puntatori, `nullptr`, dereferenziazione e aritmetica dei puntatori (capitolo 10).

Finora ogni volta che hai avuto bisogno di memorizzare una sequenza di dati hai dichiarato un array di dimensione fissa, come `int voti[100];` oppure `char riga[128];`. Questa scelta funziona bene quando conosci in anticipo un limite superiore piccolo e ragionevole, ma mostra subito i propri limiti nei programmi reali: se gli elementi da leggere sono dieci, sprechi gran parte dello spazio; se diventano mille, il programma non riesce a gestirli. Inoltre, un array dichiarato dentro una funzione scompare appena la funzione termina, rendendo impossibile costruire dati che sopravvivano al ritorno al chiamante.

Per superare questi vincoli, il linguaggio C mette a disposizione la memoria dinamica: un'area di memoria separata da quella delle variabili locali, dalla quale il programma può richiedere esattamente il numero di byte necessari mentre è in esecuzione, ridimensionarli se i dati crescono e restituirli al sistema quando non servono più. Tutto questo avviene grazie ai puntatori che hai appena imparato a usare nel capitolo 10.

Questa libertà porta con sé una responsabilità diretta. In C nessuno ripulisce automaticamente i blocchi allocati dinamicamente: dimenticare di liberare la memoria, usarla dopo averla rilasciata o liberarla due volte sono errori gravi che possono rimanere nascosti durante prove brevi e compromettere il programma in seguito. In questo capitolo imparerai sia le funzioni della libreria standard per gestire la memoria dinamica, sia la disciplina e gli strumenti di controllo automatico necessari per scrivere codice sicuro fin dal primo tentativo.

## 11.1 Stack e heap: perché serve la memoria dinamica

Quando avvii un programma compilato in C, il sistema operativo gli assegna uno spazio di memoria organizzato in regioni con compiti distinti. Per capire dove vivono le variabili e come gestire collezioni di dati di dimensione variabile, è fondamentale distinguere le due aree principali in cui vengono conservati i dati durante l'esecuzione: lo **stack** e lo **heap**.

Lo **stack** è un'area di memoria gestita automaticamente in ordine ultimo entrato primo uscito (LIFO, *Last In, First Out*) per le chiamate di funzione e le variabili locali automatiche. Ogni volta che una funzione viene chiamata, il programma riserva sullo stack un blocco ordinato chiamato *frame* (o record di attivazione), che contiene i parametri della funzione, le sue variabili locali automatiche e le informazioni necessarie per tornare al chiamante. Appena la funzione termina con `return`, il suo frame viene rimosso dalla cima dello stack e tutta la memoria che occupava torna immediatamente disponibile.

Lo **heap** è invece un'area di memoria da cui il programma richiede e rilascia blocchi di durata controllata esplicitamente con funzioni come `malloc` e `free`. La richiesta di memoria a tempo di esecuzione sullo heap prende il nome di **allocazione dinamica** (*dynamic allocation*). A differenza dello stack, lo heap non segue l'ordine delle chiamate di funzione: un blocco allocato dentro una funzione resta vivo e valido anche dopo il suo ritorno, finché il programma non decide esplicitamente di rilasciarlo (oppure finché il programma termina).

```text
+------------------------------------------+
|  STACK (gestione automatica, LIFO)       |
|  [ frame di main: variabili locali     ] |
|  [ frame di funzione_a: parametri, ... ] |
|  [ frame di funzione_b: parametri, ... ] |
|        |  cresce a ogni chiamata         |
|        v                                 |
|                                          |
|              spazio libero               |
|                                          |
|        ^                                 |
|        |  cresce a ogni allocazione      |
|  [ blocco dinamico 2 (allocato)        ] |
|  [ blocco dinamico 1 (allocato)        ] |
|  HEAP (gestione esplicita: malloc/free)  |
+------------------------------------------+
```

Lo schema mostra l'organizzazione concettuale della memoria: stack e heap occupano zone separate e rispondono a esigenze diverse. Come hai visto nel capitolo 7, la **durata di vita** di una variabile stabilisce per quanto tempo la sua memoria rimane valida. Possiamo fissare questa prima regola fondamentale:

- Le variabili locali automatiche risiedono sullo **stack**: nascono all'ingresso nel blocco in cui sono dichiarate e scompaiono automaticamente alla sua uscita.
- I blocchi ottenuti tramite **allocazione dinamica** risiedono sullo **heap** e sopravvivono al ritorno dalle funzioni finché il programma non li rilascia esplicitamente con `free` (oppure finché il programma termina).

Secondo lo standard C23, sia la durata di vita automatica sia quella allocata dinamicamente sono completamente definite; al contrario, accedere a un oggetto automatico dopo l'uscita dal suo blocco oppure a un blocco dinamico dopo averlo liberato provoca **comportamento indefinito**.

### I limiti degli array sullo stack

Gli array che hai usato dal capitolo 8, come `double misure[1000];`, sono variabili locali allocate sullo stack. Sono comodi e veloci, ma presentano tre limiti strutturali:

1. **Dimensione fissa a tempo di compilazione.** Devi decidere quanti elementi riservare prima ancora di sapere quanti dati inserirà l'utente. Se ne arrivano 5, hai occupato inutilmente spazio per 995 elementi; se ne arrivano 1001, non puoi contenerli tutti senza rischiare un accesso fuori dai limiti o scartare dati.
2. **Capacità complessiva ridotta dello stack.** Sui sistemi moderni lo stack di un programma ha una dimensione relativamente piccola (spesso pochi megabyte). Dichiarare un array molto grande sullo stack — oppure eseguire una ricorsione troppo profonda — esaurisce lo spazio disponibile e causa uno *stack overflow*, che termina bruscamente il programma senza possibilità di recupero.
3. **Impossibilità di restituire un array locale da una funzione.** Se una funzione dichiara un array locale e restituisce un puntatore al suo primo elemento, il frame della funzione viene distrutto al momento del `return`. Il puntatore restituito indica memoria che non appartiene più a quell'array e dereferenziarlo provoca comportamento indefinito.

Il seguente frammento mostra questo errore tipico.

> **Attenzione — Codice errato (comportamento indefinito)**
> Il frammento qui sotto è **vietato** nei programmi reali: restituisce l'indirizzo di un array locale allocato sullo stack, che cessa di esistere appena la funzione termina. Non scrivere mai codice di questo tipo.

<!-- cod: id=11.1-b tipo=frammento -->
```c
int *crea_array_errato(void) {
    int locali[4] = {10, 20, 30, 40};
    return locali;  // ERRORE: locali scompare al ritorno della funzione!
}
```

Un altro aspetto importante riguarda gli *array a lunghezza variabile* (VLA, *Variable-Length Arrays*), che permettono in C di dichiarare un array locale con dimensione determinata a tempo di esecuzione (come `int a[n];`). In questo libro **non usiamo i VLA**: anch'essi vengono di solito allocati sullo stack, non offrono alcun modo per verificare se l'allocazione sia fallita e, se `n` è grande o mal controllato, possono provocare uno stack overflow silenzioso e impossibile da intercettare.

### Il ruolo dello heap

Lo heap risolve tutti e tre i limiti appena elencati. Quando usi l'allocazione dinamica (che imparerai nel dettaglio nella sotto-sezione 11.2):

- puoi richiedere esattamente la quantità di memoria che serve in base ai dati letti a tempo di esecuzione;
- disponi di uno spazio molto più ampio rispetto allo stack;
- puoi verificare subito se il sistema è riuscito a soddisfare la richiesta (controllando se la funzione restituisce `nullptr`);
- puoi creare un blocco dentro una funzione e restituirne il puntatore al chiamante, perché quel blocco resterà valido finché non verrà liberato esplicitamente.

### Esempio guidato

Il programma seguente legge fino a `100` misure `double` da `stdin` in un array fisso sullo stack e confronta i byte effettivamente usati con quelli riservati a tempo di compilazione, mostrando lo spazio sprecato. Poi chiama una breve funzione ricorsiva `mostra_frame` per osservare concretamente la creazione e la distruzione LIFO dei frame sullo stack.

<!-- cod: id=11.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

void mostra_frame(int livello, int massimo) {
    printf("Ingresso frame %d\n", livello);
    if (livello < massimo) {
        mostra_frame(livello + 1, massimo);
    }
    printf("Uscita frame %d\n", livello);
}

int main(void) {
    constexpr size_t MAX_MISURE = 100;
    double buffer[MAX_MISURE] = {0.0};
    char riga[64];
    size_t usati = 0;

    while (usati < MAX_MISURE && fgets(riga, (int)sizeof(riga), stdin) != nullptr) {
        double valore = 0.0;
        char extra = '\0';
        if (sscanf(riga, "%lf %c", &valore, &extra) == 1) {
            buffer[usati] = valore;
            ++usati;
        }
    }

    size_t byte_riservati = sizeof(buffer);
    size_t byte_usati = usati * sizeof(buffer[0]);
    printf("Misure lette: %zu su %zu\n", usati, MAX_MISURE);
    printf("Stack riservato: %zu B, usato: %zu B, sprecato: %zu B\n",
           byte_riservati, byte_usati, byte_riservati - byte_usati);

    mostra_frame(1, 3);
    return 0;
}
```

```input
12.5
18.0
15.5
```

```output
Misure lette: 3 su 100
Stack riservato: 800 B, usato: 24 B, sprecato: 776 B
Ingresso frame 1
Ingresso frame 2
Ingresso frame 3
Uscita frame 3
Uscita frame 2
Uscita frame 1
```

Osserva che cosa evidenziano le due parti dell'esecuzione:

- L'array `buffer` occupa `100 * sizeof(double)`, cioè `800` byte sullo stack (dove `sizeof(double)` vale `8`), anche se l'input contiene solo `3` valori (`24` byte effettivi). Se l'input avesse contenuto `150` valori, gli ultimi `50` sarebbero stati ignorati.
- La funzione `mostra_frame` stampa prima gli ingressi `1`, `2`, `3` e poi le uscite in ordine inverso `3`, `2`, `1`: è esattamente la disciplina LIFO dello stack. L'ultimo frame creato è sempre il primo a essere distrutto.

> **Approfondimento — Perché non mettere tutto sullo heap**
> Allocare memoria sullo stack è un'operazione quasi istantanea: al processore basta spostare di pochi byte un singolo registro interno (il puntatore di stack). Al contrario, ogni richiesta sullo heap coinvolge un gestore della memoria che deve cercare un blocco libero adatto, aggiornarne le strutture interne di controllo e, alla fine, restituirlo con `free`. Per questo motivo, quando un oggetto è piccolo, ha dimensione nota e vive solo all'interno di una funzione, lo stack resta sempre la scelta più semplice, sicura e veloce.

### Esercizio 11.1 — Simulatore di stack delle chiamate e soglia heap

**Descrizione**

Scrivi un programma C che simuli la gestione LIFO di uno stack delle chiamate di capacità configurabile e il dirottamento sullo heap di blocchi grandi (senza usare `malloc`, applicando gli array dei capitoli precedenti per osservare il comportamento di stack e heap). Leggi dalla prima riga di `stdin` `limite_stack` (`int` compreso tra `1` e `1'000'000`, in byte). Usa `constexpr size_t MAX_FRAME = 32;` e due array paralleli `char nomi[MAX_FRAME][32]` e `size_t dim_frame[MAX_FRAME]` per rappresentare i frame attivi sullo stack. Leggi poi fino a fine input una sequenza di comandi (uno per riga; ignora le righe vuote):

- `CALL <nome> <byte>` (`nome` fino a `31` caratteri senza spazi, `byte` in `1..1'000'000`) prova a inserire un frame sullo stack; se `profondita == MAX_FRAME` oppure `usati + dim > limite_stack`, NON inserisce il frame e stampa `STACK OVERFLOW: <nome> richiede <byte> B (disponibili <disp> B)`, altrimenti inserisce il frame, aggiorna `usati` e `picco_stack` e stampa `CALL <nome> (+<byte> B) -> stack=<usati>/<limite> B`.
- `RET` rimuove l'ultimo frame inserito (LIFO): se `profondita == 0` stampa `ERRORE: stack vuoto`, altrimenti rimuove il frame, decrementa `usati` e stampa `RET <nome> (-<byte> B) -> stack=<usati>/<limite> B`.
- `HEAP <nome> <byte>` (`byte` in `1..1'000'000`) registra una richiesta sullo heap senza consumare stack, somma `byte` a `totale_heap` e stampa `HEAP <nome> (+<byte> B) -> heap=<totale_heap> B`.

In caso di formato o comando non valido stampa su `stderr` e restituisci `EXIT_FAILURE`. Al termine stampa picco dello stack, numero di frame rimasti sullo stack e totale richiesto sullo heap esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- ordine LIFO (ultimo entrato, primo uscito) dei frame sullo stack
- capacità limitata dello stack e condizione di stack overflow
- differenza tra memoria sullo stack (automatica per chiamata) e memoria sullo heap (indipendente dai frame)
- validazione rigorosa dell'input e gestione sicura dei limiti dell'array

**Domande guida**

1. Quale frame deve essere rimosso per primo quando arriva un comando `RET` e quale indice degli array `nomi` e `dim_frame` lo rappresenta?
2. Perché devi controllare `usati + dim > limite_stack` prima di aggiungere il nuovo frame invece di aggiornare `usati` e poi verificare?
3. In che modo il comando `HEAP` differisce da `CALL` rispetto al contatore `usati` e al picco dello stack?
4. Che cosa rappresenta il numero di frame rimasti sullo stack al termine dell'esecuzione?

**Esempio di esecuzione**

```input
1000
CALL main 256
CALL elabora 512
CALL stampa 400
HEAP buffer_grande 4096
RET
CALL stampa 400
RET
RET
```

```output
CALL main (+256 B) -> stack=256/1000 B
CALL elabora (+512 B) -> stack=768/1000 B
STACK OVERFLOW: stampa richiede 400 B (disponibili 232 B)
HEAP buffer_grande (+4096 B) -> heap=4096 B
RET elabora (-512 B) -> stack=256/1000 B
CALL stampa (+400 B) -> stack=656/1000 B
RET stampa (-400 B) -> stack=256/1000 B
RET main (-256 B) -> stack=0/1000 B
Picco stack: 768 B
Frame rimasti sullo stack: 0
Totale richiesto sullo heap: 4096 B
```

## 11.2 Allocare e liberare memoria: `malloc`, `calloc` e `free`

Per richiedere memoria sullo heap e restituirla al termine dell'uso, la libreria standard del C mette a disposizione un gruppo di funzioni dichiarate nell'header `<stdlib.h>`: `malloc`, `calloc` e `free`, affiancate da `exit` per terminare il programma in caso di errore irreversibile. A queste si aggiungono in C23 `strdup` e `strndup` in `<string.h>`, pensate per duplicare stringhe direttamente sullo heap.

### Allocare un blocco con `malloc`

La funzione `malloc` (*memory allocation*) riceve il numero di byte desiderati (`size_t`) e restituisce l'indirizzo del primo byte del blocco allocato sullo heap, oppure `nullptr` se la memoria non è disponibile:

```text
void *malloc(size_t size);
```

Il tipo restituito è `void *`, un puntatore senza tipo specifico capace di memorizzare l'indirizzo di qualunque oggetto (lo vedremo nel capitolo 15). In C un `void *` si converte **implicitamente** in qualsiasi puntatore a oggetto `T *`, senza bisogno di alcun cast esplicito. Per allocare un array dinamico di `n` elementi, l'idioma consigliato è questo:

<!-- cod: id=11.2-b tipo=frammento -->
```c
int *p = malloc(n * sizeof(*p));
```

Osserva la forma `n * sizeof(*p)`: moltiplica il numero di elementi per la dimensione dell'oggetto puntato da `p`, senza ripetere il tipo `int` a destra dell'uguale. Se un giorno cambierai la dichiarazione da `int *p` a `double *p`, `sizeof(*p)` si adatterà automaticamente.

La memoria restituita da `malloc` ha **contenuto indeterminato**: contiene i bit lasciati lì in precedenza. Leggere un elemento di un blocco allocato con `malloc` prima di avergli scritto un valore provoca **comportamento indefinito**.

### Controllare sempre il fallimento e gestire gli errori fatali con `exit`

Una richiesta di allocazione sullo heap può sempre fallire, per esempio se la memoria del sistema è esaurita o se il numero di byte richiesto è eccessivo. Per questo devi controllare **ogni volta** che il puntatore restituito non sia `nullptr` prima di dereferenziarlo:

<!-- cod: id=11.2-c tipo=frammento -->
```c
int *p = malloc(n * sizeof(*p));
if (p == nullptr) {
    fprintf(stderr, "Errore: memoria insufficiente.\n");
    exit(EXIT_FAILURE);
}
```

La funzione `void exit(int status);` (in `<stdlib.h>`) termina immediatamente l'esecuzione del programma da qualunque funzione ti trovi, svuota gli stream di uscita aperti (come `stdout` e `stderr`) e restituisce all'ambiente il codice `status` (`EXIT_SUCCESS` o `EXIT_FAILURE`). È particolarmente comoda quando racchiudi la stampa dell'errore e la terminazione in una piccola funzione ausiliaria.

### Allocare e azzerare con `calloc`

Quando desideri che il blocco allocato parta interamente azzerato — per esempio per una tabella di contatori o un array di frequenze — la libreria standard offre `calloc` (*contiguous allocation*):

```text
void *calloc(size_t nmemb, size_t size);
```

A differenza di `malloc`, `calloc` prende due argomenti separati: il numero di elementi `nmemb` e la dimensione `size` di ciascun elemento. Esegue due operazioni fondamentali:

1. verifica internamente che il prodotto `nmemb * size` non vada in overflow (restituendo `nullptr` se il calcolo supererebbe il massimo di `size_t`);
2. inizializza tutti i bit del blocco a zero (per gli interi corrisponde al valore `0`, per `double` corrisponde a `0.0` sui sistemi IEEE 754 e per i puntatori a `nullptr` sulle architetture comuni).

L'idioma corrispondente è `double *valori = calloc(n, sizeof(*valori));`. Anche con `calloc` il controllo di `nullptr` è obbligatorio.

Possiamo riassumere la regola per `malloc` e `calloc` così:

- `malloc(size)` alloca `size` byte sullo heap con contenuto indeterminato; `calloc(nmemb, size)` alloca spazio per `nmemb` oggetti da `size` byte inizializzati tutti a zero (tutti i bit a `0`) e verifica l'overflow del prodotto `nmemb * size`.
- Entrambe restituiscono `void *`, che in C si converte implicitamente a qualsiasi puntatore a oggetto `T *` senza cast, oppure `nullptr` in caso di fallimento.
- Il puntatore restituito va sempre controllato prima dell'uso.

Nota sullo standard C23: che cosa accade se chiami `malloc(0)` o `calloc(0, sizeof(int))`? Il comportamento è **dipendente dall'implementazione**: può restituire `nullptr` oppure un puntatore univoco non dereferenziabile (che va comunque passato a `free`). Inoltre, leggere byte non inizializzati restituiti da `malloc` provoca **comportamento indefinito**.

### Restituire la memoria con `free`

Quando un blocco sullo heap non ti serve più, devi rilasciarlo chiamando `free` (`<stdlib.h>`):

```text
void free(void *ptr);
```

Le regole fondamentali di `free` sono chiare e non ammettono eccezioni:

- `free(ptr)` rilascia un blocco precedentemente restituito da `malloc`, `calloc`, `realloc`, `strdup` o `strndup`.
- Chiamare `free(nullptr)` è **sempre definito** dallo standard C23 e non esegue alcuna azione: questa proprietà semplifica molto la pulizia sui rami di errore.
- Subito dopo `free(ptr)` è buona pratica impostare `ptr = nullptr;`, così il puntatore non conserva più l'indirizzo del blocco ormai liberato.
- Chiamare `free` su un indirizzo non proveniente dall'allocatore (come l'indirizzo di una variabile sullo stack o un puntatore spostato con aritmetica), oppure chiamarlo due volte sullo stesso blocco, provoca **comportamento indefinito**.

### Duplicare stringhe dinamicamente in C23: `strdup` e `strndup`

Capita molto spesso di voler conservare sullo heap una copia indipendente di una stringa letta in un buffer locale. In C23 l'header `<string.h>` fornisce due funzioni dedicate:

- `char *strdup(const char *s);` alloca sullo heap una copia completa della stringa `s` (incluso il terminatore nullo `'\0'`) e ne restituisce l'indirizzo, oppure `nullptr` se l'allocazione fallisce.
- `char *strndup(const char *s, size_t size);` alloca sullo heap una copia di al più `size` caratteri di `s`, aggiungendo sempre `'\0'` alla fine, e restituisce l'indirizzo oppure `nullptr`.

Entrambe restituiscono memoria allocata dinamicamente: il chiamante è sempre responsabile di controllare `nullptr` e di liberare la stringa con `free`. Passare a `strdup` o `strndup` un puntatore nullo o una sequenza non valida provoca comportamento indefinito.

> **C23** — Le funzioni `strdup` e `strndup` sono state standardizzate in `<string.h>` solo a partire da C23 (in precedenza esistevano come estensioni POSIX). Se compili con uno standard più vecchio come C11 o C17, puoi ottenere lo stesso risultato allocando con `malloc(strlen(s) + 1)` e copiando con `strcpy` (oppure calcolando il minimo tra `strlen(s)` e `size` per `strndup` e aggiungendo `'\0'`).

> **Se vieni da Python** — In Python la memoria degli oggetti è gestita automaticamente dal garbage collector e dal conteggio dei riferimenti; in C ogni blocco allocato sullo heap con `malloc`, `calloc`, `realloc`, `strdup` o `strndup` deve essere liberato esplicitamente con `free`.

### Esempio guidato

Il programma seguente legge da `stdin` il nome di una stazione meteo, il numero `n` di temperature rilevate e le `n` temperature. Alloca l'array dinamico con `calloc`, duplica il nome completo con `strdup` e la sigla di 3 lettere con `strndup`, verifica tutti i puntatori usando la funzione ausiliaria `termina_errore` con `exit(EXIT_FAILURE)`, calcola media ed escursione termica e libera ogni blocco impostando i puntatori a `nullptr`.

<!-- cod: id=11.2-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void termina_errore(const char *msg) {
    fprintf(stderr, "Errore: %s\n", msg);
    exit(EXIT_FAILURE);
}

int main(void) {
    char buf[64], riga[64];
    int n_in = 0;
    if (fgets(buf, (int)sizeof(buf), stdin) == nullptr ||
        fgets(riga, (int)sizeof(riga), stdin) == nullptr ||
        sscanf(riga, "%d", &n_in) != 1 || n_in < 1) {
        termina_errore("intestazione non valida.");
    }
    buf[strcspn(buf, "\n")] = '\0';
    size_t n = (size_t)n_in;
    double *temp = calloc(n, sizeof(*temp));
    char *stazione = strdup(buf);
    char *sigla = strndup(buf, 3);
    if (temp == nullptr || stazione == nullptr || sigla == nullptr) {
        free(temp); free(stazione); free(sigla);
        termina_errore("allocazione fallita.");
    }
    double somma = 0.0, minimo = 0.0, massimo = 0.0;
    for (size_t i = 0; i < n; ++i) {
        if (fgets(riga, (int)sizeof(riga), stdin) == nullptr || sscanf(riga, "%lf", &temp[i]) != 1) {
            free(temp); free(stazione); free(sigla);
            termina_errore("temperatura non valida.");
        }
        somma += temp[i];
        if (i == 0 || temp[i] < minimo) { minimo = temp[i]; }
        if (i == 0 || temp[i] > massimo) { massimo = temp[i]; }
    }
    printf("Stazione: %s (%s)\nMedia: %.2f, escursione: %.2f\n",
           stazione, sigla, somma / (double)n, massimo - minimo);
    free(temp); temp = nullptr; free(stazione); stazione = nullptr; free(sigla); sigla = nullptr;
    return EXIT_SUCCESS;
}
```

```input
Milano
4
12.5
18.0
15.5
14.0
```

```output
Stazione: Milano (Mil)
Media: 15.00, escursione: 5.50
```

Osserva i punti chiave di questo programma:

- Le tre allocazioni (`temp`, `stazione`, `sigla`) vengono verificate insieme: se anche una sola fallisce, chiamare `free` su tutte e tre è perfettamente sicuro perché `free(nullptr)` non fa nulla.
- `strndup(buf, 3)` copia al più `3` caratteri (`"Mil"`) e inserisce automaticamente il terminatore `'\0'` nel quarto byte.
- Anche se una temperatura fosse mal formattata durante il ciclo `for`, il programma libera tutti e tre i blocchi prima di chiamare `termina_errore`, mantenendo il codice pulito su ogni percorso.
- Alla fine ogni puntatore viene liberato e subito impostato a `nullptr`.

> **Approfondimento — Perché evitare il cast sul risultato di `malloc`**
> In alcuni testi meno recenti capita di incontrare `(int *)malloc(n * sizeof(int))`. In C quel cast è superfluo perché `void *` si converte implicitamente a qualsiasi puntatore a oggetto, ed è persino dannoso per la leggibilità e la manutenzione: costringe a ripetere il tipo due volte (a sinistra e a destra dell'uguale), aumentando il rischio di dimenticare di aggiornare uno dei due punti quando cambia il tipo dell'array. Scrivere `int *p = malloc(n * sizeof(*p));` è più breve, più sicuro e idiomatico in C.

### Esercizio 11.2 — Analisi dinamica di punteggi e targhette con `malloc`, `calloc`, `strdup` e `strndup`

**Descrizione**

Scrivi un programma C che utilizzi `malloc`, `calloc`, `free`, `exit` (`<stdlib.h>`) e le funzioni C23 `strdup` e `strndup` (`<string.h>`). Definisci prima di `main` una funzione ausiliaria `void errore_fatale(const char *messaggio)` che stampi `Errore: <messaggio>` su `stderr` e termini il programma con `exit(EXIT_FAILURE)`. In `main` leggi dalla prima riga di `stdin` un'etichetta non vuota (buffer di `64` byte, rimuovendo `'\n'` con `strcspn`), dalla seconda riga due interi `n` (`1..1000`) e `k` (`1..63`), e dalle successive `n` righe gli `n` punteggi interi (`0..100`). Alloca dinamicamente:

- una copia completa dell'etichetta con `strdup`;
- un codice abbreviato di al più `k` caratteri con `strndup`;
- un array di `n` interi con `malloc(n * sizeof(*punteggi))` per i punteggi;
- una tabella di `101` contatori azzerati con `calloc(101, sizeof(*freq))` per le frequenze dei punteggi `0..100`.

Controlla che nessuna allocazione sia `nullptr` (in caso di errore di allocazione o di input libera i blocchi già allocati e chiama `errore_fatale`). Calcola minimo, massimo, media (`%.2f`), numero di punteggi distinti presenti e punteggio più frequente (a parità di frequenza, il punteggio numericamente più piccolo). Stampa il riepilogo esattamente come nell'esempio di esecuzione, libera tutti i blocchi con `free` impostando ogni puntatore a `nullptr` e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- allocazione con `malloc(n * sizeof(*p))` senza cast esplicito
- allocazione azzerata con `calloc(101, sizeof(*freq))` per contatori di frequenza
- duplicazione dinamica di stringhe in C23 con `strdup` e `strndup`
- controllo di `nullptr`, gestione degli errori con `exit(EXIT_FAILURE)` e rilascio con `free`

**Domande guida**

1. Perché `calloc` è particolarmente adatta per la tabella delle frequenze rispetto a `malloc`?
2. Quale differenza c'è tra il comportamento di `strdup` e quello di `strndup` quando la stringa originale è più lunga di `k` caratteri?
3. Perché il codice abbreviato restituito da `strndup` e la copia restituita da `strdup` vanno liberati esplicitamente con `free`?
4. Perché è sicuro chiamare `free` su tutti e quattro i puntatori in caso di errore se li hai inizializzati prima a `nullptr`?

**Esempio di esecuzione**

```input
Verifica-Informatica
6 8
80
95
80
70
95
80
```

```output
Etichetta: Verifica-Informatica (codice: Verifica)
Campioni: 6, distinti: 3
Min: 70, max: 95, media: 83.33
Punteggio piu frequente: 80 (3 volte)
```

## 11.3 Ridimensionare blocchi con `realloc` e array dinamici

Con `malloc` e `calloc` puoi allocare esattamente la memoria che serve, ma presuppongono che tu conosca già la quantità di dati prima di iniziare a leggerli. Molto spesso, però, leggi valori da uno stream fino alla fine dell'input senza sapere in anticipo se saranno tre, trenta o trentamila. Per far crescere (o restringere) un blocco già allocato sullo heap esiste la funzione `realloc` (`<stdlib.h>`):

```text
void *realloc(void *ptr, size_t size);
```

### Come funziona `realloc`

Quando chiami `realloc(ptr, nuova_dim)`, l'allocatore ridimensiona il blocco puntato da `ptr` portandolo a `nuova_dim` byte e preserva i dati già presenti fino al minimo tra la vecchia e la nuova dimensione:

- se dopo il blocco attuale c'è spazio libero sufficiente sullo heap, `realloc` può estenderlo **sul posto** e restituire lo stesso indirizzo `ptr`;
- se lo spazio contiguo non basta, `realloc` alloca un **nuovo blocco** di `nuova_dim` byte in un'altra posizione dello heap, copia automaticamente il contenuto precedente nel nuovo blocco, libera il vecchio blocco e restituisce il nuovo indirizzo;
- se l'allocazione fallisce, `realloc` restituisce `nullptr` e lascia **intatto e ancora valido** il blocco originale puntato da `ptr`.

Quest'ultimo dettaglio impone una regola ferrea: **salva sempre il risultato di `realloc` in un puntatore temporaneo** prima di aggiornare il puntatore originale.

<!-- cod: id=11.3-b tipo=frammento -->
```c
double *tmp = realloc(p, nuova_cap * sizeof(*p));
if (tmp == nullptr) {
    // p è ancora valido: possiamo liberarlo senza perdite di memoria
    free(p);
    fprintf(stderr, "Errore: riallocazione fallita.\n");
    return EXIT_FAILURE;
}
p = tmp;
```

Se invece scrivessi direttamente `p = realloc(p, nuova_dim);` e la richiesta fallisse, `p` verrebbe sovrascritto con `nullptr`: il vecchio blocco resterebbe allocato sullo heap, ma avresti perso l'unico puntatore che permetteva di liberarlo, creando una perdita di memoria immediata.

### Casi limite di `realloc` in C23

Lo standard C23 definisce con precisione due casi particolari:

- Se `ptr` è `nullptr`, `realloc(nullptr, nuova_dim)` si comporta esattamente come `malloc(nuova_dim)`. Questo permette di iniziare con un puntatore `nullptr` e usare un unico codice di crescita per la prima allocazione e le successive.
- Se `nuova_dim` è `0`, in C23 chiamare `realloc(ptr, 0)` provoca **comportamento indefinito**. Per rilasciare completamente un blocco non si chiama mai `realloc(ptr, 0)`, ma sempre `free(ptr)` seguito da `ptr = nullptr;`.

> **C23** — Negli standard C precedenti al C23 il comportamento di `realloc(ptr, 0)` era dipendente dall'implementazione (alcune librerie liberavano il blocco restituendo `nullptr`, altre restituivano un puntatore non nullo). Il C23 ha rimosso questa ambiguità rendendo `realloc(ptr, 0)` comportamento indefinito: controlla sempre che la nuova dimensione sia maggiore di zero prima di chiamare `realloc`, e usa `free` quando la dimensione scende a zero.

### Costruire un array dinamico con lunghezza e capacità

Per raccogliere un numero ignoto di elementi in un array dinamico, conviene mantenere sempre due contatori `size_t` distinti accanto al puntatore `dati`:

- **lunghezza effettiva (`len`)**: quanti elementi validi sono stati inseriti finora;
- **capacità allocata (`cap`)**: quanti elementi entrano nel blocco attualmente allocato sullo heap (vale sempre `len <= cap`).

```text
cap = 8, len = 5
+------+------+------+------+------+------+------+------+
| 10.5 | 12.0 |  9.5 | 14.0 | 11.0 |  ?   |  ?   |  ?   |
+------+------+------+------+------+------+------+------+
  [0]    [1]    [2]    [3]    [4]    [5]    [6]    [7]
  <--------- elementi usati --------><-- spazio libero -->
```

Quando devi inserire un nuovo elemento, controlli se `len == cap`. Se c'è ancora spazio (`len < cap`), scrivi direttamente in `dati[len]` e incrementi `len` senza toccare `realloc`. Solo quando l'array è pieno (`len == cap`), calcoli una nuova capacità **raddoppiando** quella precedente — per esempio seguendo la progressione `0 -> 4 -> 8 -> 16 -> 32` — e chiami `realloc` tramite un puntatore temporaneo.

Questa strategia si chiama **crescita geometrica**. Rispetto a chiamare `realloc` a ogni singolo elemento aggiunto, riduce drasticamente il numero di riallocazioni e di copie in memoria: per inserire un milione di elementi bastano circa venti raddoppi invece di un milione di chiamate a `realloc`.

Al termine della lettura, se l'array non è vuoto (`len > 0`) e ha molta capacità inutilizzata (`len < cap`), puoi eseguire una **compattazione finale** (*shrink-to-fit*) chiamando `realloc(dati, len * sizeof(*dati))` con il solito puntatore temporaneo. Se invece `len == 0`, liberi direttamente il blocco con `free(dati); dati = nullptr; cap = 0;`.

> **Se vieni da Python** — In Python una lista cresce automaticamente con `append` nascondendo le riallocazioni; in C un array dinamico si costruisce esplicitamente gestendo puntatore, lunghezza, capacità e crescita geometrica con `realloc`.

### Esempio guidato

Il programma seguente legge da `stdin` un numero imprecisato di misure `double`, accumulandole in un array dinamico che parte da capacità `4` e raddoppia con `realloc` e puntatore temporaneo ogni volta che si riempie. Stampa un messaggio a ogni raddoppio, calcola la media finale e libera correttamente il blocco.

<!-- cod: id=11.3-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    size_t cap = 4, len = 0;
    double *misure = malloc(cap * sizeof(*misure));
    if (misure == nullptr) {
        fprintf(stderr, "Errore: allocazione iniziale fallita.\n");
        return EXIT_FAILURE;
    }

    char riga[64];
    double valore = 0.0;
    while (fgets(riga, (int)sizeof(riga), stdin) != nullptr) {
        if (sscanf(riga, "%lf", &valore) != 1) {
            continue;
        }
        if (len == cap) {
            size_t nuova_cap = cap * 2;
            double *tmp = realloc(misure, nuova_cap * sizeof(*misure));
            if (tmp == nullptr) {
                free(misure);
                fprintf(stderr, "Errore: riallocazione fallita.\n");
                return EXIT_FAILURE;
            }
            printf("Capacita raddoppiata: %zu -> %zu\n", cap, nuova_cap);
            misure = tmp;
            cap = nuova_cap;
        }
        misure[len] = valore;
        ++len;
    }

    double somma = 0.0;
    for (size_t i = 0; i < len; ++i) { somma += misure[i]; }
    printf("Misure lette: %zu (capacita finale: %zu)\n", len, cap);
    if (len > 0) { printf("Media: %.2f\n", somma / (double)len); }
    free(misure);
    misure = nullptr;
    return EXIT_SUCCESS;
}
```

```input
10.0
12.0
14.0
16.0
18.0
20.0
```

```output
Capacita raddoppiata: 4 -> 8
Misure lette: 6 (capacita finale: 8)
Media: 15.00
```

Osserva come si comporta l'array dinamico durante la lettura:

- I primi quattro valori occupano gli indici `0..3` senza alcuna riallocazione.
- All'arrivo del quinto valore (`18.0`), `len` vale `4` ed è uguale a `cap`: il programma calcola `nuova_cap = 8` e chiama `realloc` salvando il risultato in `tmp`. Solo dopo aver verificato `tmp != nullptr` aggiorna `misure` e `cap`.
- Se la riallocazione fosse fallita, `misure` avrebbe ancora contenuto l'indirizzo del blocco da 4 elementi, permettendo di chiamare `free(misure)` prima di restituire `EXIT_FAILURE`.

> **Approfondimento — Perché il raddoppio mantiene lineare il costo totale**
> Supponi di inserire `n` elementi in un array dinamico che raddoppia la capacità ogni volta che si riempie. Le copie complessive eseguite durante tutti i ridimensionamenti fino a raggiungere `n` sono al massimo `1 + 2 + 4 + 8 + ... + n`, una somma che resta sempre inferiore a `2n` (quindi proporzionale a `n`, in media meno di due copie per elemento). Se invece aumentassi la capacità di un solo elemento per volta, a ogni inserimento dovresti copiare tutti i dati già presenti, con un numero di copie proporzionale a `n * n` (costo quadratico): per centomila elementi la differenza passa da una frazione di secondo a diversi minuti.

### Esercizio 11.3 — Array dinamico a crescita geometrica e compattazione con `realloc`

**Descrizione**

Scrivi un programma C che legga da `stdin` una soglia intera `soglia` dalla prima riga (`"%d %c"` == `1`) e poi un numero arbitrario (anche nullo) di interi dalle righe successive fino a fine input (`-100'000..100'000`; in caso di formato o intervallo non valido libera la memoria allocata, stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`). Accumula i valori letti in un array dinamico `int *dati = nullptr;` gestendo lunghezza effettiva `len` e capacità `cap` inizialmente entrambe a `0`.

Ogni volta che `len == cap`, calcola `nuova_cap = (cap == 0) ? 2 : cap * 2;` e ridimensiona con `realloc` salvando il risultato in un puntatore temporaneo `int *tmp` (senza mai sovrascrivere `dati` prima del controllo `tmp == nullptr`), contando il numero di ridimensionamenti di crescita eseguiti e conservando la capacità di picco raggiunta. Terminata la lettura, filtra l'array sul posto mantenendo in ordine relativo solo i valori `>= soglia` (lunghezza `len_filt`).

Se `len_filt == 0`, libera `dati` con `free(dati); dati = nullptr; cap = 0;` senza mai chiamare `realloc(dati, 0)` (comportamento indefinito in C23); se invece `len_filt > 0 && len_filt < cap`, compatta il blocco alla dimensione esatta `len_filt` con `realloc` e puntatore temporaneo. Stampa il riepilogo (elementi letti, capacità di picco, numero di ridimensionamenti di crescita, capacità finale, elementi filtrati, valori e loro somma; se `len_filt == 0` stampa `Valori: (nessuno)` e ometti la riga della somma) esattamente come nell'esempio di esecuzione e libera la memoria prima di uscire.

**Concetti da tenere a mente**

- crescita geometrica (raddoppio della capacità) con coppia (`len`, `cap`)
- uso obbligatorio di un puntatore temporaneo con `realloc` per non perdere il blocco originale
- equivalenza tra `realloc(nullptr, dim)` e `malloc(dim)` alla prima crescita
- divieto di `realloc(ptr, 0)` in C23 e uso di `free` quando la lunghezza scende a zero

**Domande guida**

1. Perché devi assegnare il valore restituito da `realloc` a una variabile temporanea `tmp` invece di scrivere direttamente `dati = realloc(dati, ...)`?
2. Che cosa succede alla prima chiamata di `realloc` quando `dati` vale ancora `nullptr`?
3. Perché quando `len_filt` risulta `0` devi chiamare `free(dati)` anziché `realloc(dati, 0)`?
4. Quanti ridimensionamenti di crescita avvengono leggendo `5` elementi se la capacità parte da `0` e passa a `2`, `4`, `8`?

**Esempio di esecuzione**

```input
10
5
12
-3
25
10
```

```output
Letti: 5, capacita picco: 8, ridimensionamenti: 3
Capacita finale: 3, filtrati (>= 10): 3
Valori: 12 25 10
Somma filtrati: 47
```

## 11.4 Perdite di memoria, uso dopo `free` e doppia liberazione

Gestire direttamente lo heap ti offre controllo completo sulla memoria, ma introduce una classe di difetti che non esistono con le sole variabili sullo stack. Conoscerli in anticipo — e sapere esattamente quali schemi di codice li provocano — è il modo migliore per non introdurli nei tuoi programmi.

### Perdita di memoria (*memory leak*)

Una **perdita di memoria** (*memory leak*) è un errore in cui un blocco allocato dinamicamente non è più raggiungibile ma non viene mai liberato con `free`. Se un programma breve perde pochi byte, alla sua chiusura il sistema operativo recupera comunque tutta la memoria del processo; ma in un programma che lavora a lungo o ripete un'operazione in un ciclo, le perdite si accumulano fino a esaurire la memoria disponibile.

Le perdite di memoria nascono quasi sempre in tre situazioni:

1. **Sovrascrittura di un puntatore senza `free`**: assegni a `p` il risultato di una nuova `malloc` (o `strdup`) mentre `p` puntava ancora a un blocco precedente non liberato.
2. **Uscite anticipate su rami di errore**: una funzione alloca un blocco, incontra un errore di input e fa `return` dimenticando di liberare quel blocco.
3. **Fallimento di una seconda allocazione**: allochi `a` con successo, poi `b` fallisce restituendo `nullptr` ed esci senza liberare `a`.

> **Attenzione — Codice errato (perdita di memoria)**
> Il frammento seguente è **vietato**: riassegna `p` senza aver liberato il primo blocco, rendendo impossibile chiamare `free` su quei 10 interi.

<!-- cod: id=11.4-b tipo=frammento -->
```c
int *p = malloc(10 * sizeof(*p));
p = malloc(20 * sizeof(*p));  // ERRORE: il primo blocco non è più raggiungibile!
free(p);                      // libera solo il secondo blocco
```

### Uso dopo la liberazione (*use-after-free*)

Un **uso dopo la liberazione** (*use-after-free*) è l'accesso in lettura o in scrittura a memoria dinamica già rilasciata con `free`. Secondo lo standard C23 provoca **comportamento indefinito**: dopo `free(p)`, quel blocco appartiene di nuovo all'allocatore e può essere riassegnato a un'altra parte del programma. Leggerlo può restituire dati corrotti; scriverci può danneggiare silenziosamente altre variabili sullo heap.

> **Attenzione — Codice errato (comportamento indefinito)**
> Il frammento seguente è **vietato**: accede a `p[0]` dopo aver liberato il blocco con `free(p)`.

<!-- cod: id=11.4-c tipo=frammento -->
```c
int *p = malloc(4 * sizeof(*p));
if (p != nullptr) {
    p[0] = 42;
    free(p);
    printf("%d\n", p[0]);  // ERRORE: uso dopo la liberazione!
}
```

Impostare subito `p = nullptr;` dopo `free(p)` non elimina il problema se esistono altre copie di quell'indirizzo, ma trasforma `p` in un puntatore nullo facilmente controllabile anziché lasciarlo con un indirizzo ormai non valido (approfondiremo questo caso nel capitolo 14).

### Doppia liberazione (*double free*)

Una **doppia liberazione** (*double free*) è la chiamata ripetuta di `free` sullo stesso blocco di memoria senza una nuova allocazione intermedia. Anche questo è **comportamento indefinito** e corrompe le strutture interne dell'allocatore, portando spesso a chiusure improvvise o vulnerabilità di sicurezza.

L'errore può avvenire in modo diretto (due chiamate a `free(p)` di fila) oppure in modo subdolo attraverso due puntatori *alias* `p` e `q` che contengono lo stesso indirizzo:

> **Attenzione — Codice errato (comportamento indefinito)**
> Il frammento seguente è **vietato**: `p` e `q` puntano allo stesso blocco; la seconda `free` tenta di liberare memoria già rilasciata.

<!-- cod: id=11.4-d tipo=frammento -->
```c
int *p = malloc(4 * sizeof(*p));
int *q = p;   // q e p condividono lo stesso indirizzo
free(p);
free(q);      // ERRORE: doppia liberazione dello stesso blocco!
```

### Altri errori fatali sullo heap

Oltre ai tre errori appena visti, ricorda altre due violazioni che provocano sempre comportamento indefinito:

- **Passare a `free` un indirizzo non proveniente dall'allocatore**: non puoi mai passare a `free` l'indirizzo di una variabile locale sullo stack (`free(&x)`) né un puntatore che hai spostato con l'aritmetica dei puntatori (`++p; free(p);`). A `free` va passato esattamente l'indirizzo restituito da `malloc`, `calloc`, `realloc`, `strdup` o `strndup`.
- **Scrivere oltre la fine del blocco (*heap buffer overflow*)**: come per gli array sullo stack (capitolo 8 e capitolo 9), accedere oltre `n - 1` su un blocco dinamico di `n` elementi — oppure dimenticare il byte `+ 1` per `'\0'` in una stringa dinamica — sovrascrive memoria adiacente o i metadati dell'allocatore.

### Una disciplina semplice per scrivere codice sicuro

Per prevenire quasi tutti questi errori, applica costantemente quattro abitudini:

1. **Un solo proprietario chiaro per ogni blocco**: decidi quale variabile (o funzione) ha il compito di chiamare `free` su un blocco.
2. **Copie indipendenti invece di condivisione accidentale**: se due variabili devono possedere ciascuna la propria stringa, usa `strdup` per creare una copia separata anziché scrivere `q = p;`.
3. **Azzera il puntatore dopo `free`**: scrivi sempre `free(p); p = nullptr;` (così un'eventuale `free(p)` successiva sarà innocua).
4. **Pulizia ordinata su tutti i percorsi di uscita**: prima di ogni `return` o `exit`, assicurati che ogni blocco allocato fino a quel punto sia stato liberato.

### Esempio guidato

Il programma seguente definisce una funzione `elabora_lotto` che alloca due blocchi sullo heap (`etichetta` con `strdup` e `valori` con `calloc`). Mostra la pulizia corretta sia nel caso in cui una delle allocazioni fallisca, sia su un percorso di errore intermedio (`fattore <= 0`), sia al termine normale, azzerando ogni puntatore subito dopo `free`.

<!-- cod: id=11.4-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool elabora_lotto(const char *nome, size_t n, int fattore) {
    char *etichetta = strdup(nome);
    int *valori = calloc(n, sizeof(*valori));
    if (etichetta == nullptr || valori == nullptr) {
        free(etichetta);
        free(valori);
        return false;
    }

    if (fattore <= 0) {
        printf("Lotto %s annullato: fattore non valido (%d)\n", etichetta, fattore);
        free(valori); valori = nullptr;
        free(etichetta); etichetta = nullptr;
        return false;
    }

    int somma = 0;
    for (size_t i = 0; i < n; ++i) {
        valori[i] = (int)(i + 1) * fattore;
        somma += valori[i];
    }
    printf("Lotto %s: somma = %d\n", etichetta, somma);
    free(valori); valori = nullptr;
    free(etichetta); etichetta = nullptr;
    return true;
}

int main(void) {
    elabora_lotto("Alfa", 4, 3);
    elabora_lotto("Beta", 4, -1);
    return EXIT_SUCCESS;
}
```

```output
Lotto Alfa: somma = 30
Lotto Beta annullato: fattore non valido (-1)
```

Osserva come sono gestiti i percorsi di uscita di `elabora_lotto`:

- Se `strdup` riesce e `calloc` fallisce (o viceversa), il primo `if` libera entrambi i puntatori senza rischi, sfruttando il fatto che `free(nullptr)` non fa nulla.
- Nella seconda chiamata (`"Beta"`, fattore `-1`), la funzione entra nel ramo di errore intermedio: prima di restituire `false` libera sia `valori` sia `etichetta` e li imposta a `nullptr`. Senza quelle due `free`, ogni chiamata con fattore non valido avrebbe prodotto una perdita di memoria.
- Nella prima chiamata (`"Alfa"`), dopo aver calcolato e stampato la somma (`3 + 6 + 9 + 12 = 30`), la funzione rilascia entrambi i blocchi in modo ordinato.

> **Approfondimento — Aliasing e responsabilità di liberazione**
> Quando due puntatori `p` e `q` puntano allo stesso blocco allocato, chiamare `free(p)` rende invalido anche `q`, anche se hai scritto `p = nullptr;`: `q` continua a contenere il vecchio indirizzo ormai liberato. Finché lavori con variabili singole, evita di creare alias non necessari usando copie indipendenti; quando costruirai strutture dati complesse come liste e alberi (lo vedremo nel capitolo 17), formalizzeremo regole precise per stabilire senza ambiguità quale parte del programma possiede e libera ciascun blocco.

### Esercizio 11.4 — Gestione sicura di buffer attivo e backup senza perdite né doppie liberazioni

**Descrizione**

Scrivi un programma C che gestisca due stringhe allocate dinamicamente con possesso indipendente, `char *attivo = nullptr;` e `char *backup = nullptr;`, evitando qualsiasi perdita di memoria, uso dopo la liberazione o doppia liberazione su ogni percorso di esecuzione. Leggi da `stdin` una sequenza di comandi (una riga per comando, buffer di `128` byte, rimuovendo `'\n'` con `strcspn`; ignora le righe vuote):

- `IMPOSTA <testo>` (dove `<testo>` è non vuoto dopo il singolo spazio) crea una copia dinamica con `strdup`, la verifica prima di sostituire `attivo`, libera il vecchio `attivo` per evitare perdite di memoria e stampa `Attivo impostato: [<attivo>]`;
- `BACKUP` se `attivo == nullptr` stampa `Backup impossibile: attivo vuoto`, altrimenti crea in `backup` una copia indipendente di `attivo` con `strdup` (mai assegnando `backup = attivo`), liberando l'eventuale vecchio `backup`, e stampa `Backup salvato: [<backup>]`;
- `RIPRISTINA` se `backup == nullptr` stampa `Ripristino impossibile: backup vuoto`, altrimenti sostituisce `attivo` con una copia indipendente di `backup` tramite `strdup` e stampa `Attivo ripristinato: [<attivo>]`;
- `SVUOTA A` (oppure `SVUOTA B`) libera `attivo` (oppure `backup`) se non nullo impostandolo subito a `nullptr` e stampa `Attivo svuotato` (o `Backup svuotato`), mentre se è già `nullptr` stampa `Attivo gia vuoto` (o `Backup gia vuoto`) evitando doppie liberazioni;
- `STATO` stampa `Stato -> attivo=[<attivo o vuoto>], backup=[<backup o vuoto>]`.

Su comando sconosciuto o fallimento di allocazione libera entrambi i buffer prima di restituire `EXIT_FAILURE` con messaggio su `stderr`. A fine input conta quanti dei due buffer erano ancora allocati (`0`, `1` o `2`), liberali entrambi impostandoli a `nullptr` e stampa `Buffer rilasciati alla chiusura: <count>`.

**Concetti da tenere a mente**

- liberazione del vecchio blocco prima di riassegnare un puntatore per prevenire perdite di memoria
- copie indipendenti con `strdup` anziché condivisione dello stesso puntatore (aliasing)
- azzeramento del puntatore (`p = nullptr`) subito dopo `free` per prevenire uso dopo la liberazione e doppia liberazione
- pulizia di tutte le risorse allocate anche sui rami di errore

**Domande guida**

1. Quale errore di memoria provocheresti se in `BACKUP` scrivessi `backup = attivo` invece di allocare una copia indipendente con `strdup`?
2. Perché conviene chiamare `strdup(sorgente)` in un puntatore temporaneo prima di eseguire `free(attivo)`?
3. Come fa il programma a evitare una doppia liberazione se l'utente invia due volte consecutive il comando `SVUOTA A`?
4. Perché è necessario liberare sia `attivo` sia `backup` anche prima di uscire con `EXIT_FAILURE` in caso di comando non valido?

**Esempio di esecuzione**

```input
IMPOSTA versione 1
BACKUP
IMPOSTA versione 2
STATO
SVUOTA A
SVUOTA A
RIPRISTINA
STATO
```

```output
Attivo impostato: [versione 1]
Backup salvato: [versione 1]
Attivo impostato: [versione 2]
Stato -> attivo=[versione 2], backup=[versione 1]
Attivo svuotato
Attivo gia vuoto
Attivo ripristinato: [versione 1]
Stato -> attivo=[versione 1], backup=[versione 1]
Buffer rilasciati alla chiusura: 2
```

## 11.5 Individuare gli errori di memoria con i sanitizer

Anche se compili sempre con `-Wall -Wextra -Wpedantic -Werror`, gli avvisi del compilatore non possono individuare tutti gli errori di memoria. Il compilatore analizza il codice sorgente *prima* dell'esecuzione, ma molti difetti — come un accesso oltre la fine di un blocco allocato dinamicamente, una perdita di memoria su un ramo raro o un uso dopo la liberazione — dipendono dai valori letti mentre il programma è in esecuzione. Ancora peggio: poiché il comportamento indefinito non è obbligato a far chiudere il programma, un codice sbagliato può sembrare funzionare perfettamente sui piccoli casi di prova e guastarsi solo in seguito.

### Che cos'è un sanitizer

Per smascherare questi errori in modo sistematico esistono i **sanitizer**: strumenti integrati nel compilatore che inseriscono automaticamente controlli a tempo di esecuzione nel programma compilato per rilevare errori di memoria o comportamento indefinito.

I due sanitizer più importanti da usare insieme durante lo sviluppo in C sono:

- **AddressSanitizer** (`-fsanitize=address`): rileva accessi fuori dai limiti sullo heap e sullo stack, usi dopo la liberazione, doppie liberazioni, `free` su indirizzi non validi e, sulle piattaforme che supportano il rilevatore integrato, anche le perdite di memoria al termine dell'esecuzione.
- **UndefinedBehaviorSanitizer** (`-fsanitize=undefined`): rileva molti casi di comportamento indefinito, come overflow degli interi con segno, dereferenziazione di puntatori nulli, spostamenti illeciti e divisioni per zero.

A queste opzioni conviene aggiungere sempre `-g`, che inserisce nell'eseguibile le informazioni di debug necessarie affinché il sanitizer possa indicare con precisione i nomi dei file e i numeri di riga.

### Compilare con i sanitizer su più sistemi

Con GCC e Clang (disponibili su Linux, macOS e Windows) puoi attivare entrambi i sanitizer aggiungendo semplicemente le opzioni alla solita riga di compilazione:

```text
gcc -std=c23 -Wall -Wextra -Wpedantic -Werror -g -fsanitize=address,undefined programma.c -o programma
clang -std=c23 -Wall -Wextra -Wpedantic -Werror -g -fsanitize=address,undefined programma.c -o programma
```

Su compilatori diversi (per esempio MSVC su Windows) esistono opzioni analoghe per attivare AddressSanitizer (come `/fsanitize=address` insieme alle informazioni di debug). Tieni presente un dettaglio portabile sulla rilevazione delle perdite di memoria: su Linux AddressSanitizer attiva normalmente il controllo delle perdite in modo automatico, mentre su alcuni altri sistemi il rilevamento delle perdite può richiedere una configurazione separata o strumenti dedicati del sistema operativo.

### Come leggere una segnalazione

Il formato esatto dell'output di un sanitizer varia leggermente tra compilatori e piattaforme, ma ogni segnalazione contiene sempre le stesse informazioni essenziali per risalire alla causa del difetto:

1. **La classe dell'errore**: indica subito di che cosa si tratta (per esempio uno sforamento di scrittura sullo heap, un uso dopo la liberazione, una doppia liberazione o una perdita di memoria di un certo numero di byte).
2. **La riga dell'accesso illecito**: mostra la funzione e il numero di riga esatto in cui il programma ha compiuto l'operazione vietata.
3. **La riga dell'allocazione o della liberazione**: per gli errori sullo heap, il sanitizer indica anche dove quel blocco era stato allocato con `malloc`/`calloc`/`realloc`/`strdup` e, nel caso di uso dopo la liberazione o doppia liberazione, la riga esatta in cui era stato già liberato con `free`.

Grazie a queste tre informazioni non devi più andare a tentativi: il programma si arresta nel punto esatto dell'errore e ti indica sia dove hai sbagliato l'accesso sia dove il blocco è nato o è stato rilasciato.

### Un ciclo di verifica sistematico

Ogni volta che scrivi un programma che usa memoria dinamica, adotta questa abitudine:

1. Compila con tutti gli avvisi attivi e con `-g -fsanitize=address,undefined`.
2. Esegui il programma non solo su un caso normale, ma anche su **casi vuoti** (nessun dato in ingresso), **casi al limite** (un solo elemento, indici sul bordo, stringhe vuote) e **casi di errore** (input mal formattato, per verificare che la pulizia sui rami di uscita non lasci perdite).
3. Considera il programma pronto solo quando supera tutti i casi di prova con **zero segnalazioni** del sanitizer.

Ricorda che i sanitizer rallentano l'esecuzione e aumentano il consumo di memoria perché controllano ogni accesso: li usi durante lo sviluppo e i test, e li disattivi quando compili la versione finale ottimizzata (vedrai gli strumenti di diagnostica avanzati nel capitolo 21).

> **Se vieni da Python** — In Python gli accessi oltre i limiti di una lista sollevano `IndexError`; in C uno sforamento sullo heap o un uso dopo la liberazione sono comportamento indefinito silenzioso, che va intercettato compilando con i sanitizer.

### Esempio guidato

Considera uno degli errori più classici in C con le stringhe sullo heap: dimenticare il byte `+ 1` per il terminatore nullo `'\0'`.

> **Attenzione — Codice errato (comportamento indefinito)**
> Il frammento seguente è **vietato**: `strlen(s)` non conta `'\0'`, quindi `strcpy` scrive un byte oltre la fine del blocco allocato. Senza sanitizer il programma potrebbe sembrare funzionante; con AddressSanitizer viene bloccato immediatamente come sforamento di un byte sullo heap.

<!-- cod: id=11.5-b tipo=frammento -->
```c
const char *s = "ciao";
char *copia = malloc(strlen(s));  // ERRORE: manca + 1 per '\0'!
if (copia != nullptr) {
    strcpy(copia, s);             // scrive '\0' fuori dal blocco allocato!
    free(copia);
}
```

Il programma seguente mostra invece l'implementazione corretta, pronta per essere compilata e verificata con `-fsanitize=address,undefined -g`. Legge parole da `stdin` (una per riga), duplica ciascuna parola in un blocco temporaneo con `strdup`, ridimensiona il buffer dinamico `frase` con `realloc` riservando esattamente `nuova_len + 1` byte per il terminatore nullo, accoda la parola separata da uno spazio e libera subito ogni blocco temporaneo.

<!-- cod: id=11.5-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char riga[64];
    char *frase = nullptr;
    size_t len_frase = 0;

    while (fgets(riga, (int)sizeof(riga), stdin) != nullptr) {
        riga[strcspn(riga, "\n")] = '\0';
        if (riga[0] == '\0') { continue; }
        char *parola = strdup(riga);
        if (parola == nullptr) {
            free(frase);
            fprintf(stderr, "Errore: allocazione parola fallita.\n");
            return EXIT_FAILURE;
        }
        size_t len_p = strlen(parola);
        size_t agg_spazio = (len_frase > 0) ? 1 : 0;
        size_t nuova_len = len_frase + agg_spazio + len_p;
        char *tmp = realloc(frase, nuova_len + 1);
        if (tmp == nullptr) {
            free(parola);
            free(frase);
            fprintf(stderr, "Errore: riallocazione fallita.\n");
            return EXIT_FAILURE;
        }
        frase = tmp;
        if (agg_spazio > 0) { frase[len_frase] = ' '; }
        strcpy(frase + len_frase + agg_spazio, parola);
        len_frase = nuova_len;
        free(parola); parola = nullptr;
    }

    printf("Frase (%zu caratteri): [%s]\n", len_frase, frase != nullptr ? frase : "");
    free(frase); frase = nullptr;
    return EXIT_SUCCESS;
}
```

```input
memoria
dinamica
sicura
```

```output
Frase (23 caratteri): [memoria dinamica sicura]
```

Verifica i punti che rendono questo programma pulito sotto sanitizer:

- La richiesta `realloc(frase, nuova_len + 1)` riserva sempre il byte esatto per il terminatore `'\0'` scritto da `strcpy`.
- Ogni `parola` allocata con `strdup` viene liberata alla fine della stessa iterazione (e anche nel ramo di errore di `realloc`), evitando qualunque perdita di memoria.
- Se l'input fosse vuoto, `frase` rimarrebbe `nullptr`: la `printf` finale controlla `frase != nullptr` evitando di passare un puntatore nullo a `%s`, e `free(nullptr)` termina senza problemi.

> **Approfondimento — Come fa AddressSanitizer a cogliere un solo byte fuori posto**
> Quando compili con `-fsanitize=address`, il programma usa un allocatore speciale che circonda ogni blocco allocato con zone di guardia chiamate *redzone* e mantiene una memoria parallela di stato (*shadow memory*) per tenere traccia di quali byte sono accessibili. Se il tuo codice tenta di leggere o scrivere anche un solo byte dentro una *redzone* — come il `'\0'` mancante in `malloc(strlen(s))` — il controllo inserito dal compilatore blocca subito l'esecuzione. In modo analogo, quando chiami `free`, AddressSanitizer marca quel blocco come "avvelenato" e ne ritarda il riutilizzo, così da intercettare immediatamente qualsiasi uso dopo la liberazione.

### Esercizio 11.5 — Estrattore e concatenatore dinamico di sottostringhe verificato con sanitizer

**Descrizione**

Scrivi un programma C progettato per superare senza alcuna segnalazione la compilazione e l'esecuzione con AddressSanitizer e UndefinedBehaviorSanitizer (`-fsanitize=address,undefined -g`). Leggi da `stdin` la prima riga `testo` (buffer `256` byte, rimuovendo `'\n'` con `strcspn`; deve essere non vuota) e la seconda riga `sep` (separatore, buffer `16` byte, rimuovendo `'\n'` con `strcspn`; può essere vuota). Leggi poi fino a fine input una sequenza di coppie intere `inizio lunghezza` (`"%d %d %c"` == `2`; in caso di formato errato libera la memoria allocata, scrivi su `stderr` e restituisci `EXIT_FAILURE`).

Per ogni coppia verifica i limiti prima di accedere a `testo` evitando overflow: una richiesta è valida solo se `inizio >= 0 && lunghezza > 0 && (size_t)inizio < len_testo && (size_t)lunghezza <= len_testo - (size_t)inizio`. Se non è valida incrementa `scartate` e stampa `Richiesta (<inizio>, <lunghezza>): fuori dai limiti`. Se è valida: estrai la sottostringa sullo heap con `strndup(testo + inizio, (size_t)lunghezza)`, ridimensiona il buffer dinamico `char *risultato` con `realloc` usando un puntatore temporaneo e riservando esattamente `nuova_len + 1` byte per il terminatore nullo `'\0'`, accoda `sep` (solo dalla seconda fetta valida in poi) e la fetta estratta, stampa `Fetta <validi>: [<fetta>]` e libera subito `fetta` impostandola a `nullptr`.

A fine input stampa il conteggio di fette valide e scartate e la stringa concatenata con la sua lunghezza (`Risultato (len=<L>): [<risultato>]`), libera `risultato` e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- riserva esatta del byte extra (`+ 1`) per il terminatore nullo sullo heap per evitare heap-buffer-overflow
- controllo preventivo dei limiti con sottrazione (`len_testo - inizio`) per evitare overflow di indici
- liberazione immediata dei blocchi temporanei (`fetta`) a ogni iterazione per evitare perdite di memoria
- verifica sistematica con `-fsanitize=address,undefined -g` su casi normali, vuoti e al limite

**Domande guida**

1. Quale errore rileverebbe AddressSanitizer se quando ridimensioni `risultato` allocassi `nuova_len` byte invece di `nuova_len + 1`?
2. Perché nella condizione di validità conviene scrivere `(size_t)lunghezza <= len_testo - (size_t)inizio` anziché `(size_t)inizio + (size_t)lunghezza <= len_testo`?
3. Che cosa succederebbe dal punto di vista della memoria se dimenticassi di chiamare `free(fetta)` al termine di ogni iterazione del ciclo?
4. Come gestisci il caso limite in cui nessuna richiesta sia valida (`risultato` resta `nullptr`) al momento della stampa finale?

**Esempio di esecuzione**

```input
programmazione_in_C23
 | 
0 4
18 3
15 50
-1 2
15 2
```

```output
Fetta 1: [prog]
Fetta 2: [C23]
Richiesta (15, 50): fuori dai limiti
Richiesta (-1, 2): fuori dai limiti
Fetta 3: [in]
Fette valide: 3, scartate: 2
Risultato (len=15): [prog | C23 | in]
```

## Riepilogo

- Lo **stack** gestisce in modo automatico e in ordine LIFO i frame delle chiamate di funzione e le variabili locali automatiche; ha capacità ridotta e distrugge gli oggetti all'uscita dal blocco. Lo **heap** permette l'**allocazione dinamica** di blocchi la cui dimensione è decisa a tempo di esecuzione e la cui durata di vita termina solo con `free` (o alla fine del programma).
- `malloc(n * sizeof(*p))` (`<stdlib.h>`) alloca memoria sullo heap con contenuto indeterminato; `calloc(n, sizeof(*p))` alloca memoria azzerata bit per bit controllando l'overflow del prodotto. Entrambe restituiscono `void *` (convertito implicitamente a `T *` senza cast; lo vedremo nel capitolo 15) oppure `nullptr` in caso di fallimento, che va sempre controllato prima dell'uso (anche usando `fprintf(stderr, ...)` ed `exit(EXIT_FAILURE)`).
- `free(ptr)` rilascia un blocco allocato dinamicamente; `free(nullptr)` è definito e innocuo. Dopo `free(ptr)` imposta sempre `ptr = nullptr;`. In C23 `strdup` e `strndup` (`<string.h>`) duplicano stringhe sullo heap e richiedono una `free` da parte del chiamante.
- `realloc(ptr, nuova_dim)` ridimensiona un blocco preservando i dati esistenti e, in caso di fallimento, lascia intatto il blocco originale: usa sempre un puntatore temporaneo `tmp` prima di aggiornare `ptr`. `realloc(nullptr, dim)` equivale a `malloc(dim)`, mentre in C23 `realloc(ptr, 0)` provoca comportamento indefinito. Per array dinamici di lunghezza ignota gestisci insieme lunghezza (`len`) e capacità (`cap`) con crescita geometrica per raddoppio.
- I tre grandi errori della memoria dinamica sono la **perdita di memoria** (blocco non liberato e non più raggiungibile), l'**uso dopo la liberazione** (accesso dopo `free`) e la **doppia liberazione** (chiamare `free` due volte sullo stesso blocco). Un accesso fuori dai limiti sullo heap o `free` su un puntatore spostato o dello stack provocano anch'essi comportamento indefinito.
- I **sanitizer** (`-fsanitize=address,undefined -g`) inseriscono controlli automatici a tempo di esecuzione che rilevano sforamenti, usi dopo la liberazione, doppie liberazioni, comportamenti indefiniti e perdite di memoria, indicando riga dell'accesso e riga dell'allocazione o liberazione.

## Errori comuni

- **Dimenticare di controllare `nullptr` dopo `malloc`, `calloc`, `realloc`, `strdup` o `strndup`**: dereferenziare il puntatore senza verificare che l'allocazione sia riuscita provoca comportamento indefinito in caso di fallimento.
- **Scrivere `p = realloc(p, nuova_dim)` senza puntatore temporaneo**: se `realloc` fallisce restituisce `nullptr` e sovrascrive `p`, facendo perdere l'unico indirizzo del blocco originale e causando una perdita di memoria.
- **Allocare `n` byte invece di `n * sizeof(*p)` o dimenticare `+ 1` per `'\0'`**: scrivere `malloc(n)` per un array di `int` o `double`, oppure `malloc(strlen(s))` per una stringa, riserva troppo poca memoria e provoca un buffer overflow sullo heap.
- **Dimenticare `free` sui rami di errore o prima di riassegnare un puntatore**: uscire anticipatamente da una funzione o sovrascrivere un puntatore senza liberare il blocco precedente lascia memoria allocata e irraggiungibile (perdita di memoria).
- **Accedere a un blocco dopo `free`, liberarlo due volte o passare a `free` un indirizzo errato**: uso dopo la liberazione, doppia liberazione, `free` su un puntatore spostato (`++p`) o su una variabile dello stack provocano comportamento indefinito.
- **Chiamare `realloc(p, 0)` per svuotare un array**: in C23 è comportamento indefinito; quando la dimensione scende a zero bisogna sempre usare `free(p)` seguito da `p = nullptr;`.

## Prima di proseguire

- [ ] So spiegare la differenza tra stack e heap rispetto a gestione, capacità e durata di vita degli oggetti, e perché non si può restituire un array locale da una funzione.
- [ ] So allocare e liberare memoria con `malloc`, `calloc`, `free`, `strdup` e `strndup` controllando sempre `nullptr` e gestendo gli errori con `exit(EXIT_FAILURE)`.
- [ ] So ridimensionare un blocco con `realloc` usando un puntatore temporaneo, gestire un array dinamico con `len`, `cap` e crescita per raddoppio ed evitare `realloc(p, 0)` in C23.
- [ ] So riconoscere e prevenire perdite di memoria, uso dopo la liberazione, doppia liberazione e aliasing involontario su tutti i percorsi di uscita.
- [ ] So compilare ed eseguire i miei programmi con `-fsanitize=address,undefined -g` su casi normali, vuoti, al limite e di errore fino a ottenere zero segnalazioni.
