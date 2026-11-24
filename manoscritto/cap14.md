# Capitolo 14 — Puntatori avanzati

> **In questo capitolo imparerai a:**
> - Usare puntatori a puntatori per modificare un puntatore dentro una funzione e gestire array di puntatori
> - Allocare e liberare matrici dinamiche in modo contiguo o per righe senza perdite di memoria
> - Elaborare argomenti da riga di comando con `argc`/`argv` e convertire stringhe in numeri con `strtol` e `strtod` controllando gli overflow con `errno`, `ERANGE` e `HUGE_VAL`
> - Applicare correttamente `const` e `restrict` e prevenire puntatori pendenti usando valori sentinella

> **Ti servono:** stringhe (capitolo 9), puntatori, decadimento di array, aritmetica dei puntatori e `const` (capitolo 10), allocazione dinamica con `malloc`, `calloc`, `realloc`, `free` e sanitizer (capitolo 11), strutture e `typedef` (capitolo 12).

Nel capitolo 10 hai visto che un puntatore conserva l'indirizzo di un oggetto in memoria e permette a una funzione di modificare una variabile del chiamante. Con i soli puntatori a un livello, però, ti scontri presto con un limite concreto: se una funzione deve allocare, ridimensionare con `realloc` o azzerare a `nullptr` un puntatore che appartiene al chiamante, ricevere `T *` per valore non basta, perché la funzione riceve solo una copia dell'indirizzo. Lo stesso accade quando devi organizzare raccolte di stringhe di lunghezza variabile, matrici le cui dimensioni si conoscono solo a tempo di esecuzione o gli argomenti passati al programma dal terminale.

In questo capitolo impari a padroneggiare l'indirezione multipla e i contratti avanzati sui puntatori. Vedrai come un puntatore a puntatore (`T **`) consenta di modificare un puntatore dall'interno di una funzione, come confrontare matrici dinamiche per righe e in un unico blocco contiguo, e come leggere opzioni da riga di comando con `argc` e `argv` convertendo il testo in numeri con `strtol` e `strtod` senza mai ignorare errori di formato o overflow.

Infine affronterai due strumenti essenziali per scrivere librerie robuste e veloci: le regole di `const` su più livelli di puntatori insieme al qualificatore `restrict` per garantire l'assenza di sovrapposizione in memoria, e l'uso dei valori sentinella abbinato alle tecniche per prevenire i puntatori pendenti. Sono le basi indispensabili per passare, dal capitolo successivo, ai puntatori generici `void *` e alle strutture dati dinamiche complesse.

## 14.1 Puntatori a puntatori

Nel capitolo 10 hai imparato a passare l'indirizzo di una variabile `int` a una funzione tramite `int *` per poterne cambiare il valore. Ma che cosa succede quando la variabile che vuoi modificare dentro una funzione è *essa stessa* un puntatore? Pensa a una funzione che alloca o ridimensiona un array dinamico sullo heap con `realloc`, oppure a una funzione di pulizia che chiama `free` e vuole azzerare a `nullptr` il puntatore del chiamante: in C tutti gli argomenti vengono trasmessi con **passaggio per valore**, quindi passando un semplice `int *p` la funzione riceve una copia dell'indirizzo contenuto in `p`. Qualsiasi assegnamento al parametro dentro la funzione modifica solo quella copia locale, lasciando invariato il puntatore del chiamante.

Per modificare un puntatore dall'interno di una funzione occorre fare esattamente ciò che si fa per qualsiasi altro tipo di dato: passare il suo indirizzo. Poiché un puntatore è una variabile che occupa spazio in memoria, ha a sua volta un indirizzo. Una variabile costruita per contenerlo si chiama **puntatore a puntatore** (*pointer to pointer*): è una variabile che contiene l'indirizzo di un'altra variabile di tipo puntatore.

Se `valore` ha tipo `int` e `p` ha tipo `int *` (inizializzato con `&valore`), allora l'espressione `&p` ha tipo `int **` e può essere memorizzata in `int **pp = &p;`. La catena di indirizzi in memoria ha questo aspetto:

```text
Indirizzo      Contenuto         Nome    Tipo
-----------    --------------    -----   ------
0x1000         [     42     ] <--+  valore  int
                                 |
0x1020         [   0x1000   ] ---+  p       int *
                     ^
                     |
0x1040         [   0x1020   ] ------ pp     int **
```

Ogni asterisco aggiuntivo corrisponde a un passo lungo le frecce della catena:

- `pp` contiene `0x1020`, cioè l'indirizzo della variabile puntatore `p`.
- `*pp` (un livello di dereferenziazione) accede alla variabile `p` stessa (che vale `0x1000`): leggendo `*pp` ottieni l'indirizzo di `valore`; assegnando `*pp = ...` modifichi dove punta `p`.
- `**pp` (due livelli di dereferenziazione) segue anche la seconda freccia e accede all'oggetto `valore` (che vale `42`): scrivere `**pp = 99;` modifica direttamente `valore`.

La regola generale vale per qualsiasi tipo `T`: un puntatore a puntatore `T **pp` memorizza l'indirizzo di una variabile `T *p` ottenuto con `&p`. Con `*pp` leggi o modifichi il puntatore `p` del chiamante; con `**pp` accedi all'oggetto di tipo `T` puntato da `p`. Secondo lo standard C23, la dereferenziazione su livelli validi è completamente definita; al contrario, dereferenziare `pp` quando `pp == nullptr` (o non è inizializzato), oppure dereferenziare `*pp` quando `*pp == nullptr` (o non è inizializzato), provoca **comportamento indefinito**.

Per questo motivo, in ogni funzione che riceve `T **pp`, i controlli difensivi vanno applicati a entrambi i livelli prima di dereferenziare: prima si verifica `pp != nullptr`, e solo dopo (sfruttando la valutazione a corto circuito di `&&`) si controlla `*pp != nullptr` quando si intende accedere all'oggetto puntato.

I puntatori a puntatori compaiono in quattro idiomi fondamentali della programmazione C:

1. **Allocazione o riallocazione tramite parametro di uscita.** Una funzione che ridimensiona un buffer con `realloc` può restituire un `bool` per segnalare successo o fallimento e aggiornare il puntatore del chiamante attraverso `T **dati`. Il blocco viene riallocato prima su un puntatore temporaneo `tmp`: solo se `tmp != nullptr` si aggiorna `*dati = tmp;` (evitando di perdere il vecchio blocco in caso di errore, come visto nel capitolo 11).
2. **Scambio di due puntatori.** Se due variabili `const char *prima` e `const char *seconda` puntano a stringhe diverse, scambiare i due puntatori con `void scambia_str(const char **a, const char **b)` richiede solo tre assegnamenti di indirizzi in tempo costante, senza copiare alcun carattere.
3. **Rilascio sicuro con azzeramento.** Una funzione come `void libera_int(int **p)` controlla `if (p != nullptr)`, chiama `free(*p)` (che è innocua se `*p == nullptr`) e imposta `*p = nullptr;`. In questo modo il puntatore del chiamante non conserva l'indirizzo del blocco appena liberato.
4. **Avanzamento di un cursore di lettura.** Per analizzare una stringa un pezzo alla volta, una funzione può ricevere `const char **cursore`: legge i caratteri a partire da `*cursore`, poi aggiorna `*cursore` alla posizione successiva così che il chiamante sappia da dove riprendere. È lo stesso principio su cui si basa il parametro `endptr` di `strtol` e `strtod`, che vedrai nella sotto-sezione 14.3.

<!-- cod: id=14.1-b tipo=frammento -->
```c
void avanza_spazi(const char **cursore) {
    if (cursore == nullptr || *cursore == nullptr) {
        return;
    }
    const char *p = *cursore;
    while (*p == ' ' || *p == '\t') {
        ++p;
    }
    *cursore = p;
}
```

Nota la chiarezza di copiare `*cursore` nella variabile locale `const char *p`, fare avanzare `p` durante il ciclo e scrivere `*cursore = p;` una sola volta in uscita: si evitano espressioni scomode come `++(*cursore)` e il codice resta lineare e leggibile.

### Esempio guidato

Il programma seguente riunisce tre usi idiomatici di `T **`: `scambia_stringhe` scambia due puntatori `const char *`, `espandi_array` ridimensiona un array dinamico di `int` aggiornando il puntatore del chiamante e `libera_e_azzera` libera la memoria azzerando il puntatore del chiamante a `nullptr`.

<!-- cod: id=14.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

void scambia_stringhe(const char **a, const char **b) {
    if (a == nullptr || b == nullptr) {
        return;
    }
    const char *tmp = *a;
    *a = *b;
    *b = tmp;
}

bool espandi_array(int **dati, size_t *cap, size_t nuova_cap) {
    if (dati == nullptr || cap == nullptr || nuova_cap <= *cap) {
        return false;
    }
    int *tmp = realloc(*dati, nuova_cap * sizeof(*tmp));
    if (tmp == nullptr) {
        return false;
    }
    for (size_t i = *cap; i < nuova_cap; ++i) {
        tmp[i] = 0;
    }
    *dati = tmp;
    *cap = nuova_cap;
    return true;
}

void libera_e_azzera(int **dati) {
    if (dati == nullptr) {
        return;
    }
    free(*dati);
    *dati = nullptr;
}

int main(void) {
    const char *etichetta_a = "sensore_nord";
    const char *etichetta_b = "sensore_sud";
    printf("Prima: a=%s, b=%s\n", etichetta_a, etichetta_b);
    scambia_stringhe(&etichetta_a, &etichetta_b);
    printf("Dopo:  a=%s, b=%s\n", etichetta_a, etichetta_b);

    int *misure = nullptr;
    size_t capacita = 0;

    if (!espandi_array(&misure, &capacita, 3)) {
        fprintf(stderr, "Errore: allocazione iniziale fallita.\n");
        return EXIT_FAILURE;
    }
    misure[0] = 12;
    misure[1] = 18;
    misure[2] = 24;

    if (!espandi_array(&misure, &capacita, 5)) {
        libera_e_azzera(&misure);
        fprintf(stderr, "Errore: espansione fallita.\n");
        return EXIT_FAILURE;
    }
    misure[3] = 30;
    misure[4] = 36;

    printf("Misure (cap=%zu):", capacita);
    for (size_t i = 0; i < capacita; ++i) {
        printf(" %d", misure[i]);
    }
    printf("\n");

    libera_e_azzera(&misure);
    printf("Dopo rilascio: misure nullo = %d\n", misure == nullptr);
    return EXIT_SUCCESS;
}
```

```output
Prima: a=sensore_nord, b=sensore_sud
Dopo:  a=sensore_sud, b=sensore_nord
Misure (cap=5): 12 18 24 30 36
Dopo rilascio: misure nullo = 1
```

Analizziamo i passaggi chiave:

- In `scambia_stringhe(&etichetta_a, &etichetta_b)` passiamo gli indirizzi delle due variabili `const char *`. Dentro la funzione, `*a` e `*b` rappresentano proprio `etichetta_a` ed `etichetta_b`: lo scambio sposta solo i puntatori, non i caratteri dei letterali stringa.
- Nella prima chiamata a `espandi_array(&misure, &capacita, 3)`, `misure` vale `nullptr`: come sai dal capitolo 11, `realloc(nullptr, ...)` si comporta come `malloc`. Se l'allocazione riesce, `*dati = tmp` aggiorna `misure` nel `main` e inizializza a `0` i nuovi elementi.
- Nella seconda chiamata a `espandi_array(&misure, &capacita, 5)`, `realloc` estende il blocco a 5 interi (eventualmente spostandolo in un'altra zona dello heap) e aggiorna `misure` solo in caso di successo. Se fallisse, `misure` punterebbe ancora al vecchio blocco di 3 elementi e verrebbe liberato correttamente da `libera_e_azzera(&misure)`.
- Infine `libera_e_azzera(&misure)` rilascia lo heap tramite `free(*dati)` e imposta `*dati = nullptr`, così la verifica `misure == nullptr` nel `main` restituisce `1` (`true`).

> **Approfondimento — Quando fermarsi a due livelli di indirezione**
> Il C non pone limiti rigidi al numero di asterischi: sintatticamente puoi scrivere `int ***ppp`. Nella pratica, però, un puntatore a tre livelli rende il codice difficile da leggere e facile da sbagliare. Quando ti accorgi che una firma richiede `T ***`, è quasi sempre il segnale che conviene raggruppare il puntatore, la lunghezza e la capacità in una `struct` descrittore e passare un semplice puntatore singolo `descrittore_t *` alla funzione.

### Esercizio 14.1 — Parser di coppie chiave=valore e tabella dinamica gestiti tramite puntatori a puntatori

**Descrizione**

Scrivi un programma C che definisca `typedef struct coppia { char *chiave; char *valore; } coppia_t;` e implementi quattro funzioni basate su puntatori a puntatori:

1. `int estrai_coppia(const char **cursore, char chiave_out[32], char valore_out[32])` che salta eventuali spazi, tabulazioni e `';'` iniziali avanzando `*cursore`; se raggiunge `'\0'` restituisce `0`, altrimenti estrae una coppia `chiave=valore` (dove `chiave` e `valore` sono non vuoti, lunghi al più `31` caratteri e non contengono spazi, `'='` o `';'`), avanza `*cursore` al carattere successivo alla coppia e restituisce `1` (restituisce `-1` in caso di errore di sintassi);
2. `bool aggiungi_coppia(coppia_t **tab, size_t *len, size_t *cap, const char *chiave, const char *valore)` che fa crescere `*tab` con `realloc` (`0 -> 2 -> 4 -> ...`) e duplica `chiave` e `valore` con `strdup`;
3. `void scambia_puntatori(char **a, char **b)` che scambia due puntatori `char *` senza copiare stringhe;
4. `void libera_tabella(coppia_t **tab, size_t *len, size_t *cap)` che libera ogni coppia e `*tab`, azzerando `*tab = nullptr`, `*len = 0` e `*cap = 0`.

In `main` leggi dalla prima riga di `stdin` una sequenza di coppie separate da `';'` o spazi, estraile in un ciclo passando `&cursore` a `estrai_coppia` e inseriscile con `aggiungi_coppia(&tabella, &len, &cap, ...)`. Leggi poi dalle righe successive eventuali comandi `SWAP <i> <j>` (`0 <= i, j < len`), che scambiano i puntatori `tabella[i].valore` e `tabella[j].valore` chiamando `scambia_puntatori`. In caso di errore di sintassi, indice o allocazione libera tutto, scrivi su `stderr` e restituisci `EXIT_FAILURE`. Al termine stampa le coppie, il totale con capacità, chiama `libera_tabella(&tabella, &len, &cap)` e verifica che `tabella == nullptr` esattamente come nell'esempio.

**Concetti da tenere a mente**

- puntatore a puntatore (`T **`) per modificare un puntatore del chiamante dentro una funzione
- avanzamento di un cursore di scansione tramite `const char **cursore`
- riallocazione sicura di un array dinamico tramite `coppia_t **tab` con puntatore temporaneo
- scambio di puntatori `char *` tramite `char **` senza copiare i caratteri
- funzione di rilascio che libera e azzera il puntatore del chiamante (`*tab = nullptr`)

**Domande guida**

1. Perché `aggiungi_coppia` e `libera_tabella` devono ricevere `coppia_t **tab` invece di `coppia_t *tab`?
2. Come fa `estrai_coppia` a comunicare al ciclo in `main` il punto esatto della riga da cui riprendere la lettura alla chiamata successiva?
3. Quale vantaggio offre `scambia_puntatori(&tabella[i].valore, &tabella[j].valore)` rispetto a copiare le stringhe con `strcpy`?
4. Perché dopo `libera_tabella(&tabella, &len, &cap)` la verifica `tabella == nullptr` in `main` risulta vera?

**Esempio di esecuzione**

```input
host=alpha; porta=8080; modo=auto
SWAP 0 2
```

```output
[0] host=auto
[1] porta=8080
[2] modo=alpha
Totale coppie: 3 (capacita: 4)
Dopo rilascio: ptr_nullo=1 len=0 cap=0
```

## 14.2 Array di puntatori e matrici dinamiche

Un secondo contesto in cui i puntatori a puntatori diventano indispensabili riguarda le raccolte di sequenze e le tabelle bidimensionali la cui dimensione si conosce solo a tempo di esecuzione.

Considera prima un elenco di stringhe. Se usi una matrice di caratteri `char nomi[4][32]`, ogni riga occupa sempre 32 byte anche per una parola di 3 lettere, e scambiare due righe richiede di copiare 32 byte con `strcpy`. Un **array di puntatori** (`const char *nomi[4]` sullo stack, oppure `char **nomi` allocato sullo heap) risolve entrambi i problemi: ogni elemento dell'array è solo un indirizzo che punta a una stringa della lunghezza esatta necessaria. Quando devi riordinare l'elenco, sposti esclusivamente i puntatori (8 byte ciascuno su sistemi a 64 bit), lasciando intatti i caratteri in memoria.

Lo stesso schema permette di rappresentare sullo heap una **matrice dinamica** di `R` righe e `C` colonne, di cui esistono due rappresentazioni principali: per righe oppure in un unico blocco contiguo.

### Matrice dinamica per righe (`T **`)

Nella rappresentazione per righe si alloca prima un array di `R` puntatori (`int **m = calloc(R, sizeof(*m))`), e poi per ciascuna riga `i` da `0` a `R - 1` si alloca un blocco di `C` elementi (`m[i] = calloc(C, sizeof(*m[i]))`). In totale si eseguono `R + 1` allocazioni distinte e si accede agli elementi con la notazione familiare `m[i][j]`: `m[i]` legge il puntatore alla riga `i`, e `[j]` si sposta di `j` elementi dentro quella riga.

Questa rappresentazione ha due vantaggi: permette di avere righe di lunghezze diverse (*array frastagliato*) e consente di scambiare due righe in tempo costante scambiando solo `m[r1]` e `m[r2]`. Ha però due responsabilità precise sulla memoria:

- **Gestione del fallimento parziale:** se l'allocazione della riga `i` restituisce `nullptr`, le righe `0..i-1` e l'array di puntatori `m` sono già stati allocati. Prima di restituire `nullptr` devi liberare `m[0]..m[i-1]` e poi `free(m)`, altrimenti provochi una perdita di memoria.
- **Ordine inverso di liberazione:** quando distruggi la matrice devi liberare prima tutte le singole righe `free(m[i])` e solo alla fine `free(m)`. Se liberassi `m` per primo, leggere `m[i]` subito dopo causerebbe uso dopo la liberazione.

### Matrice dinamica in un unico blocco contiguo (`T *`)

La seconda rappresentazione appiattisce tutte le `R` righe una dopo l'altra in un solo blocco sullo heap:

<!-- cod: id=14.2-b tipo=frammento -->
```c
if (righe == 0 || cols == 0 || righe > SIZE_MAX / cols) {
    return nullptr;
}
int *dati = calloc(righe * cols, sizeof(*dati));
```

Prima di moltiplicare `righe * cols` occorre verificare `righe <= SIZE_MAX / cols` (con `SIZE_MAX` di `<stdint.h>`) per evitare l'overflow dell'aritmetica senza segno di `size_t`. L'elemento di riga `i` e colonna `j` si trova alla posizione `dati[i * cols + j]`. Il confronto tra i due layout in memoria chiarisce subito la differenza per una griglia 3×4:

```text
Matrice per righe (int **m): 4 allocazioni separate sullo heap
m ---> [ ptr_0 ] ---> [ a00 | a01 | a02 | a03 ]
       [ ptr_1 ] ---> [ a10 | a11 | a12 | a13 ]
       [ ptr_2 ] ---> [ a20 | a21 | a22 | a23 ]

Blocco contiguo (int *dati): 1 sola allocazione sullo heap
dati -> [ a00 | a01 | a02 | a03 | a10 | a11 | a12 | a13 | a20 | a21 | a22 | a23 ]
         |<----- riga 0 ------>| |<----- riga 1 ------>| |<----- riga 2 ------>|
```

Con il blocco contiguo basta una sola chiamata a `calloc` e una sola `free(dati)`, senza alcun rischio di fallimento parziale, e gli elementi adiacenti risiedono fisicamente vicini in memoria.

### Approccio ibrido e decadimento degli array 2D statici

Se vuoi sia un unico blocco contiguo sia la sintassi `m[i][j]`, puoi usare un **approccio ibrido**: allochi il blocco contiguo `int *dati` di `R * C` elementi e un array di `R` puntatori `int **righe`, impostando `righe[i] = dati + i * C`. La memoria si libera con sole due chiamate: `free(dati)` e `free(righe)`. In generale, scegli il blocco contiguo per il calcolo numerico e le matrici rettangolari regolari; scegli l'array di puntatori per righe quando le righe hanno lunghezze diverse o vanno riordinate spesso senza copiare i dati.

Attenzione a un errore molto frequente: un array bidimensionale statico come `int a[3][4]` **non** è un `int **` e **non** decade a `int **`. Per le regole di decadimento di array viste nel capitolo 10, il nome `a` decade a puntatore al suo primo elemento, e il primo elemento di `int [3][4]` è un array di 4 interi: quindi `a` decade a `int (*)[4]` (puntatore ad array di 4 `int`). In `a[3][4]` non esiste in memoria alcun array di puntatori alle righe; i 12 interi sono già contigui. Passare `a` a una funzione che aspetta `int **` è un errore di tipo rifiutato dal compilatore.

Secondo lo standard C23, entrambe le rappresentazioni dinamiche e la regola di decadimento `T[R][C]` → `T (*)[C]` sono completamente definite; superare i limiti di una riga o di un blocco contiguo provoca comportamento indefinito.

> **Se vieni da Python** — In Python una lista di liste è gestita automaticamente e non espone la differenza tra righe frammentate e un unico blocco contiguo in memoria; in C scegliere tra matrice per righe (`T **`) e blocco contiguo (`T *`) incide direttamente su allocazioni, rilascio e località di cache.

### Esempio guidato

Il programma seguente costruisce la stessa griglia 3×4 sia come matrice per righe (`int **per_righe`) sia come blocco contiguo (`int *contigua`), scambia due righe su `per_righe` spostando solo i puntatori, calcola la somma di una colonna su `contigua` tramite l'indice lineare `i * cols + j` e libera entrambe le strutture senza perdite di memoria.

<!-- cod: id=14.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void libera_righe(int **m, size_t righe) {
    if (m == nullptr) {
        return;
    }
    for (size_t i = 0; i < righe; ++i) {
        free(m[i]);
    }
    free(m);
}

int **alloca_righe(size_t righe, size_t cols) {
    if (righe == 0 || cols == 0) {
        return nullptr;
    }
    int **m = calloc(righe, sizeof(*m));
    if (m == nullptr) {
        return nullptr;
    }
    for (size_t i = 0; i < righe; ++i) {
        m[i] = calloc(cols, sizeof(*m[i]));
        if (m[i] == nullptr) {
            libera_righe(m, i);
            return nullptr;
        }
    }
    return m;
}

int *alloca_contigua(size_t righe, size_t cols) {
    if (righe == 0 || cols == 0 || righe > SIZE_MAX / cols) {
        return nullptr;
    }
    return calloc(righe * cols, sizeof(int));
}

int main(void) {
    constexpr size_t RIGHE = 3;
    constexpr size_t COLS = 4;

    int **per_righe = alloca_righe(RIGHE, COLS);
    int *contigua = alloca_contigua(RIGHE, COLS);
    if (per_righe == nullptr || contigua == nullptr) {
        libera_righe(per_righe, RIGHE);
        free(contigua);
        fprintf(stderr, "Errore: allocazione matrice fallita.\n");
        return EXIT_FAILURE;
    }

    for (size_t i = 0; i < RIGHE; ++i) {
        for (size_t j = 0; j < COLS; ++j) {
            int valore = (int)(i * 10 + j + 1);
            per_righe[i][j] = valore;
            contigua[i * COLS + j] = valore;
        }
    }

    int *tmp = per_righe[0];
    per_righe[0] = per_righe[2];
    per_righe[2] = tmp;

    printf("Matrice per righe dopo scambio riga 0 <-> riga 2:\n");
    for (size_t i = 0; i < RIGHE; ++i) {
        for (size_t j = 0; j < COLS; ++j) {
            printf("%3d", per_righe[i][j]);
        }
        printf("\n");
    }

    size_t col_scelta = 2;
    int somma_col = 0;
    for (size_t i = 0; i < RIGHE; ++i) {
        somma_col += contigua[i * COLS + col_scelta];
    }
    printf("Somma colonna %zu sulla matrice contigua: %d\n", col_scelta, somma_col);

    libera_righe(per_righe, RIGHE);
    free(contigua);
    return EXIT_SUCCESS;
}
```

```output
Matrice per righe dopo scambio riga 0 <-> riga 2:
 21 22 23 24
 11 12 13 14
  1  2  3  4
Somma colonna 2 sulla matrice contigua: 39
```

Osserva alcuni dettagli tecnici di questo programma:

- In `alloca_righe`, se `calloc` fallisce alla riga `i`, chiamiamo `libera_righe(m, i)` passando proprio `i`: in questo modo vengono liberate solo le righe `0..i-1` già allocate e poi l'array `m`.
- In `alloca_contigua`, il controllo `righe > SIZE_MAX / cols` garantisce che il prodotto `righe * cols` non vada in overflow prima di essere passato a `calloc`.
- Lo scambio delle righe `0` e `2` su `per_righe` richiede solo tre assegnamenti di puntatore `int *`, indipendentemente dal numero di colonne `COLS`.
- Sulla matrice `contigua`, la colonna `2` corrisponde agli elementi di indice `0 * 4 + 2` (`3`), `1 * 4 + 2` (`13`) e `2 * 4 + 2` (`23`), la cui somma è `39`.

> **Approfondimento — Prestazioni e cache nelle matrici contigue**
> Una matrice allocata in un singolo blocco contiguo è di norma più veloce di una matrice per righe `T **` per due ragioni: riduce il numero di chiamate all'allocatore da `R + 1` a `1` ed elimina un livello di indirezione a ogni accesso (non serve leggere prima `m[i]` per poi saltare all'indirizzo della riga). Tenere tutti i dati adiacenti favorisce la cache del processore, un aspetto legato alla località in memoria che approfondiremo nel capitolo 25.

### Esercizio 14.2 — Trasposizione di matrice contigua e ordinamento di righe tramite array di puntatori

**Descrizione**

Scrivi un programma C che metta a confronto le due rappresentazioni dinamiche di una matrice di interi `R x C`: un blocco contiguo `typedef struct matrice_contigua { size_t righe; size_t cols; int *dati; } matrice_contigua_t;` (con accesso `dati[r * cols + c]`) e un array di puntatori alle righe `int **per_righe` (con accesso `per_righe[r][c]`). Implementa sei funzioni:

- `bool crea_contigua(matrice_contigua_t *m, size_t r, size_t c)` (verifica `r > 0 && c > 0 && r <= SIZE_MAX / c` e alloca con `calloc`);
- `void libera_contigua(matrice_contigua_t *m)` (libera e azzera i campi);
- `bool trasponi_contigua(const matrice_contigua_t *src, matrice_contigua_t *dst)` (alloca `dst` di dimensione `src->cols x src->righe` e copia `src[r][c]` in `dst[c][r]`);
- `int **crea_per_righe(size_t r, size_t c)` (alloca l'array di `r` puntatori e ciascuna riga di `c` interi, liberando correttamente le righe già allocate in caso di fallimento intermedio);
- `void libera_per_righe(int **m, size_t r)`;
- `void ordina_righe_per_somma(int **m, size_t r, size_t c)` (ordina in modo stabile le righe per somma crescente degli elementi scambiando esclusivamente i puntatori `int *` delle righe, senza copiare gli elementi delle righe).

In `main` leggi dalla prima riga `r c` (`1 <= r <= 32`, `1 <= c <= 32`) e dalle successive `r` righe i `c` interi di ciascuna riga. Carica i valori in entrambe le strutture, calcola e stampa la trasposta (`c x r`) dalla matrice contigua, poi ordina le righe di `per_righe` e stampa ciascuna riga con la propria somma nel formato dell'esempio. Libera tutta la memoria prima di uscire.

**Concetti da tenere a mente**

- matrice dinamica in un unico blocco contiguo con calcolo dell'indice `r * cols + c`
- controllo preventivo di overflow del prodotto `r * c` con `SIZE_MAX / c`
- matrice dinamica per righe (`int **`) con pulizia parziale in caso di errore di allocazione
- ordinamento stabile delle righe scambiando solo i puntatori `int *` senza copiare gli elementi

**Domande guida**

1. Quale espressione mappa le coordinate `(r, c)` nella posizione lineare dell'array `dati` di una matrice contigua di `cols` colonne?
2. Se in `crea_per_righe` l'allocazione della riga `k` fallisce, quali blocchi di memoria devono essere liberati prima di restituire `nullptr`?
3. Perché `ordina_righe_per_somma` riesce a spostare intere righe di `per_righe` con un solo assegnamento di puntatore mentre su una matrice contigua dovrebbe copiare `c` interi per ogni spostamento?
4. In che ordine devi chiamare `free` dentro `libera_per_righe` per evitare una perdita di memoria o un uso dopo la liberazione?

**Esempio di esecuzione**

```input
3 2
10 5
1 2
3 0
```

```output
Trasposta (2x3):
10 1 3
5 2 0
Righe ordinate per somma:
1 2 (somma=3)
3 0 (somma=3)
10 5 (somma=15)
```

## 14.3 Argomenti da riga di comando (`argc`/`argv`), `strtol` e `strtod`

Finora i tuoi programmi hanno letto i dati da `stdin` con `fgets`. Gli strumenti reali da terminale, però, ricevono spesso opzioni e valori direttamente sulla riga di comando al momento dell'avvio, come `./programma --base 16 1a ff`. In C il sistema operativo consegna questi argomenti al programma attraverso una seconda firma standard di `main`:

<!-- cod: id=14.3-b tipo=frammento -->
```c
int main(int argc, char *argv[])
```

Poiché nei parametri di funzione un array `T a[]` decade a puntatore `T *a`, `char *argv[]` è del tutto equivalente a `char **argv`: un puntatore al primo elemento di un array di puntatori a stringa. Lo standard C23 garantisce tre proprietà fondamentali:

- `argc` (*argument count*) è un `int` non negativo che indica quanti argomenti sono stati passati.
- Se `argc > 0`, `argv[0]` punta a una stringa che rappresenta il nome con cui il programma è stato avviato (o una stringa vuota se il sistema non lo fornisce). Gli argomenti veri e propri forniti dall'utente sono `argv[1]`, `argv[2]`, ..., `argv[argc - 1]`.
- `argv[argc]` è garantito essere un puntatore nullo (`nullptr`), che funge da valore sentinella al termine dell'elenco (approfondiremo i valori sentinella nella sotto-sezione 14.5).

```text
argc = 4
argv ---> [ argv[0] ] ---> "./calc\0"
          [ argv[1] ] ---> "--base\0"
          [ argv[2] ] ---> "16\0"
          [ argv[3] ] ---> "ff\0"
          [ argv[4] ] ---> nullptr
```

Per analizzare opzioni come `--base` o `--scala` e argomenti posizionali si scorre `argv` dall'indice `1` fino ad `argc - 1` confrontando le stringhe con `strcmp`. Se un'opzione richiede un parametro successivo (per esempio `--base 16`), occorre sempre verificare `i + 1 < argc` prima di accedere ad `argv[i + 1]`, e poi incrementare `i` per saltare il parametro già consumato. Quando l'utente fornisce un'opzione sconosciuta o malformata, è buona norma segnalare il problema su `stderr` con `fprintf` e restituire `EXIT_FAILURE`.

### Conversione rigorosa in interi: `strtol`, `strtoul`, `strtoll`, `strtoull`

Ogni elemento di `argv` è una stringa `char *`. Come convertirlo in un numero in modo affidabile? Le vecchie funzioni come `atoi`, `atol` e `atof` non segnalano in alcun modo gli errori di formato (restituiscono semplicemente `0` per `"abc"`) e provocano comportamento indefinito in caso di overflow: vanno quindi sempre evitate. Al loro posto, `<stdlib.h>` fornisce una famiglia di funzioni rigorose che sfruttano proprio un puntatore a puntatore `char **endptr`:

- `long int strtol(const char *restrict nptr, char **restrict endptr, int base);`
- `unsigned long int strtoul(const char *restrict nptr, char **restrict endptr, int base);`
- `long long int strtoll(const char *restrict nptr, char **restrict endptr, int base);`
- `unsigned long long int strtoull(const char *restrict nptr, char **restrict endptr, int base);`

Il parametro `base` può valere un numero tra `2` e `36` (per esempio `10` per decimale, `16` per esadecimale, `2` per binario) oppure `0`: con `base == 0` la funzione riconosce automaticamente il prefisso della stringa (`0x`/`0X` per esadecimale, `0` iniziale per ottale, altrimenti decimale).

Passando l'indirizzo di un puntatore locale `char *end = nullptr;` come secondo argomento (`&end`), la funzione scrive in `end` l'indirizzo del primo carattere che non ha potuto convertire. Con due soli controlli su `end` distingui ogni errore di formato:

- Se `end == s`, non è stata letta alcuna cifra valida (per esempio stringa vuota `""` o `"ciao"`).
- Se `*end != '\0'`, dopo il numero restano caratteri residui non validi (per esempio `"12abc"`, dove `end` punta ad `'a'`).

### Conversione in virgola mobile con `strtod` e controllo di `errno`

Per i numeri in virgola mobile `<stdlib.h>` offre `double strtod(const char *restrict nptr, char **restrict endptr);`, che usa lo stesso meccanismo di `endptr` per segnalare la fine della conversione.

Come si rileva invece un **overflow** (numero troppo grande per il tipo) o un **underflow** (numero non nullo troppo vicino a zero per `double`)? Qui entra in gioco l'header `<errno.h>`, che definisce `errno` e la costante `ERANGE`:

1. **Prima** di chiamare `strtol`, `strtoul`, `strtoll`, `strtoull` o `strtod`, scrivi sempre `errno = 0;`.
2. **Dopo** la chiamata, controlla `errno == ERANGE`: in caso di overflow `strtol` restituisce `LONG_MAX` o `LONG_MIN` (e analogamente le altre varianti intere restituiscono il limite del proprio tipo), mentre `strtod` restituisce `+HUGE_VAL` o `-HUGE_VAL` (definita in `<math.h>`).
3. Se il tuo programma deve memorizzare il risultato di `strtol` in un tipo più stretto come `int`, dopo aver verificato `errno != ERANGE` controlla anche `val >= INT_MIN && val <= INT_MAX` prima del cast.

Secondo lo standard C23, il comportamento di `argc`, `argv[argc] == nullptr`, delle funzioni `strto*` e della segnalazione tramite `errno`, `ERANGE` e `HUGE_VAL` è definito. Nessuna funzione della libreria standard azzera `errno` in caso di successo; inoltre, passare un puntatore nullo come primo argomento (`nptr`) a una funzione `strto*` provoca comportamento indefinito.

> **Se vieni da Python** — In Python gli argomenti da riga di comando si leggono da `sys.argv` (una lista di stringhe) e `int()`/`float()` sollevano eccezioni; in C `argc`/`argv` sono un contatore e un array terminato da `nullptr` e la conversione sicura richiede `strtol`/`strtod` con controllo esplicito di `endptr`, `errno` ed `ERANGE`.

### Esempio guidato

Il programma seguente accetta argomenti da riga di comando con firma `int main(int argc, char *argv[])` (e, quando viene eseguito senza argomenti, usa un elenco dimostrativo predefinito). Riconosce l'opzione `--base <B>` e converte i valori restanti con `strtol`, distinguendo tra formato errato ed overflow (`ERANGE`), poi mostra anche la conversione di tre stringhe con `strtod` e il controllo di `HUGE_VAL`.

<!-- cod: id=14.3-a tipo=programma -->
```c
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void analizza_interi(int n, char *const *args) {
    int base = 10;
    for (int i = 1; i < n && args[i] != nullptr; ++i) {
        if (strcmp(args[i], "--base") == 0 && i + 1 < n) {
            char *end = nullptr;
            errno = 0;
            long b = strtol(args[++i], &end, 10);
            if (end != args[i] && *end == '\0' && errno != ERANGE &&
                (b == 0 || (b >= 2 && b <= 36))) {
                base = (int)b;
                printf("Base impostata a %d\n", base);
            } else {
                fprintf(stderr, "Base non valida: %s\n", args[i]);
            }
            continue;
        }
        char *end = nullptr;
        errno = 0;
        long val = strtol(args[i], &end, base);
        if (end == args[i] || *end != '\0') {
            printf("'%s' -> errore di formato\n", args[i]);
        } else if (errno == ERANGE) {
            printf("'%s' -> overflow/underflow (ERANGE)\n", args[i]);
        } else {
            printf("'%s' (base %d) -> %ld\n", args[i], base, val);
        }
    }
}

void prova_strtod(const char *s) {
    char *end = nullptr;
    errno = 0;
    double val = strtod(s, &end);
    if (end == s || *end != '\0') {
        printf("strtod('%s') -> formato non valido\n", s);
    } else if (errno == ERANGE && fabs(val) == HUGE_VAL) {
        printf("strtod('%s') -> overflow (ERANGE, HUGE_VAL)\n", s);
    } else if (errno == ERANGE) {
        printf("strtod('%s') -> underflow (ERANGE)\n", s);
    } else {
        printf("strtod('%s') -> %.2f\n", s, val);
    }
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        analizza_interi(argc, argv);
    } else {
        char a0[] = "demo";
        char a1[] = "--base";
        char a2[] = "16";
        char a3[] = "2a";
        char a4[] = "99999999999999999999999999999";
        char a5[] = "1g";
        char *demo[] = {a0, a1, a2, a3, a4, a5, nullptr};
        analizza_interi(6, demo);
    }

    prova_strtod("3.25");
    prova_strtod("1e500");
    prova_strtod("12.4x");
    return EXIT_SUCCESS;
}
```

```output
Base impostata a 16
'2a' (base 16) -> 42
'99999999999999999999999999999' -> overflow/underflow (ERANGE)
'1g' -> errore di formato
strtod('3.25') -> 3.25
strtod('1e500') -> overflow (ERANGE, HUGE_VAL)
strtod('12.4x') -> formato non valido
```

Osserva come lavorano insieme `endptr`, `errno` e la sentinella `nullptr`:

- Il ciclo in `analizza_interi` controlla `i < n && args[i] != nullptr`, sfruttando sia il contatore sia la sentinella finale.
- Prima di ogni chiamata a `strtol` o `strtod` azzeriamo esplicitamente `errno = 0;`. Senza questo azzeramento, l'errore `ERANGE` impostato su `"99999999999999999999999999999"` resterebbe attivo anche sulle chiamate successive.
- Per `"1g"` in base 16, `strtol` converte la cifra `'1'` e ferma `end` su `'g'`: il controllo `*end != '\0'` cattura subito il carattere residuo non valido.
- In `prova_strtod`, `"1e500"` supera `DBL_MAX`: `strtod` imposta `errno = ERANGE` e restituisce `HUGE_VAL`, così possiamo distinguere l'overflow dall'underflow.

> **Approfondimento — Due insidie frequenti con `strto*`**
> Prima insidia: nessuna funzione della libreria standard azzera `errno` quando ha successo; dimenticare `errno = 0;` prima di `strtol` o `strtod` può produrre falsi positivi ereditati da una chiamata precedente. Seconda insidia: `strtoul` e `strtoull` accettano comunque un segno `'-'` iniziale e applicano la negazione modulare senza segno (convertendo `"-1"` in `ULONG_MAX` senza errore!). Se vuoi accettare solo numeri non negativi, verifica prima che la stringa (dopo eventuali spazi) non inizi con `'-'`.

### Esercizio 14.3 — Elaboratore di argomenti da riga di comando con `strtol`, `strtod` ed `errno`

**Descrizione**

Scrivi un programma C con firma `int main(int argc, char *argv[])` che includa `<ctype.h>`, `<errno.h>`, `<math.h>`, `<stdio.h>`, `<stdlib.h>` e `<string.h>` per analizzare opzioni da riga di comando e convertire stringhe in numeri controllando formato e overflow. Implementa tre funzioni:

1. `int parsa_long(const char *s, int base, long *out)` che rifiuta stringhe vuote o con spazi iniziali (`isspace`), imposta `errno = 0`, chiama `strtol(s, &end, base)` e restituisce `0` in caso di successo (`end != s && *end == '\0' && errno != ERANGE`), `2` se `errno == ERANGE` (overflow/underflow) e `1` per errore di formato;
2. `bool parsa_double(const char *s, double *out)` che imposta `errno = 0`, chiama `strtod(s, &end)` e restituisce `true` solo se la stringa non è vuota né inizia con spazi, `end != s`, `*end == '\0'`, `errno != ERANGE`, `val == val` (esclude NaN) e `fabs(val) != HUGE_VAL`;
3. `int esegui_comando(int argc, char *argv[])` che scorre `argv[1..argc-1]` (terminato dalla sentinella `argv[argc] == nullptr`) riconoscendo `--base <B>` (`B` in `{0, 2, 8, 10, 16}`, predefinita `10`) e `--scala <S>` (`double` finito, predefinito `1.0`). Se un'opzione che inizia con `--` è sconosciuta o ha un parametro mancante o non valido, stampa `ERRORE OPZIONE: <opt>` e restituisce `1`. Ogni altro argomento viene convertito con `parsa_long(arg, base, &v)`: se valido viene sommato in `long long`, altrimenti incrementa `scartati` e stampa `SCARTATO: <arg> (overflow)` oppure `SCARTATO: <arg> (formato)`. Al termine di un comando valido stampa `RISULTATO -> base=<B> scala=<S:.2f> validi=<V> scartati=<SC> somma=<SOMMA> scalata=<SOMMA*S:.2f>` e restituisce `0`.

In `main`: se `argc > 1` esegue direttamente `esegui_comando(argc, argv)` e restituisce `EXIT_SUCCESS` o `EXIT_FAILURE`; se `argc == 1` legge da `stdin` righe di argomenti separati da spazi, costruisce per ciascuna riga un array `char *args[33]` con `args[0] = "cli"` e sentinella `args[n] = nullptr` e richiama `esegui_comando(n, args)`.

**Concetti da tenere a mente**

- firma `int main(int argc, char *argv[])` e sentinella `argv[argc] == nullptr`
- conversione di interi con `strtol` in basi diverse (`0`, `2`, `8`, `10`, `16`) e controllo di `endptr`
- conversione in virgola mobile con `strtod` e controllo di `HUGE_VAL` (`<math.h>`)
- azzeramento obbligatorio di `errno = 0` prima della chiamata e verifica di `errno == ERANGE` (`<errno.h>`)

**Domande guida**

1. Perché devi scrivere `errno = 0` immediatamente prima di ogni chiamata a `strtol` o `strtod`?
2. Quali due controlli su `endptr` servono dopo `strtol(s, &end, base)` per distinguere una stringa senza cifre, una stringa con caratteri residui come `12abc` e una conversione completamente valida?
3. Che differenza c'è nel comportamento di `strtol` quando `base` vale `0` rispetto a quando `base` vale `10` o `16`?
4. Come ti permette la doppia modalità in `main` (`argc > 1` da terminale e `argc == 1` da `stdin`) di riutilizzare identicamente la stessa funzione `esegui_comando`?

**Esempio di esecuzione**

```input
--base 16 --scala 0.5 10 ff 99999999999999999999999999999 1g
--base 0 10 0x10 010
--scala 1e500 5
```

```output
SCARTATO: 99999999999999999999999999999 (overflow)
SCARTATO: 1g (formato)
RISULTATO -> base=16 scala=0.50 validi=2 scartati=2 somma=271 scalata=135.50
RISULTATO -> base=0 scala=1.00 validi=3 scartati=0 somma=34 scalata=34.00
ERRORE OPZIONE: --scala
```

## 14.4 Correttezza di `const` e qualificatore `restrict`

Quando i puntatori diventano multipli o attraversano funzioni di libreria ad alte prestazioni, due qualificatori di tipo diventano centrali per scrivere interfacce chiare e veloci: `const` (introdotto nel capitolo 10 per i puntatori singoli) e `restrict`.

### `const` su più livelli di puntatori

Per leggere senza ambiguità una dichiarazione con più asterischi e uno o più `const`, si applica la regola della lettura da destra a sinistra a partire dal nome della variabile:

- `const char **p`: `p` è un puntatore a un puntatore a `const char`. Puoi cambiare `*p` (dove punta il puntatore intermedio), ma non `**p` (i caratteri puntati).
- `char *const *p`: `p` è un puntatore a un puntatore **costante** a `char`. Non puoi cambiare `*p`, ma puoi modificare i caratteri `**p`.
- `const char *const *p`: `p` è un puntatore a un puntatore **costante** a `const char`. Non puoi modificare né `*p` né i caratteri `**p`.

In C la conversione implicita che aggiunge `const` a un puntatore è permessa **solo sul primo livello puntato**:

- `T *` si converte implicitamente in `const T *`.
- `T **` si converte implicitamente in `T *const *` (aggiunge `const` al primo livello puntato).
- `T **` **non** si converte implicitamente in `const T **` né in `const T *const *`.

A prima vista questo divieto sembra un fastidio: se ho un `char **v` (per esempio `argv`), perché non posso passarlo a una funzione che promette di non modificare i caratteri con `const char **p`? La risposta è che permettere `T ** -> const T **` aprirebbe un buco di sicurezza dei tipi che consentirebbe di modificare un oggetto `const` senza alcun cast esplicito. Guarda che cosa accadrebbe se la conversione fosse legale:

<!-- cod: id=14.4-c tipo=frammento -->
```c
// Esempio dimostrativo (NON compila in C): perché char ** -> const char ** è vietata
const char c = 'X';
char *p = nullptr;
const char **pp = &p; // Se questa riga fosse lecita...
*pp = &c;             // ...ora p (che è char *, non const!) punterebbe al const char c!
*p = 'Y';             // Modifica di un oggetto const senza alcun cast: comportamento indefinito!
```

Il compilatore blocca alla radice questo scenario vietando la conversione implicita da `char **` a `const char **`. Per progettare API *const-correct* per array di stringhe hai due scelte pulite:

- Se l'array contiene stringhe che non vanno modificate, dichiaralo fin dall'origine come `const char *v[]`: il suo nome decade a `const char **` e si converte implicitamente in `const char *const *` (aggiungendo `const` sul primo livello puntato).
- Se invece la funzione deve accettare un `char **` (come `argv` o un array dinamico di stringhe sullo heap) senza modificare i puntatori dell'array, usa il parametro `char *const *`.

### Il qualificatore `restrict`

Osserva le firme della libreria standard che usi ogni giorno:

- `char *strcpy(char *restrict s1, const char *restrict s2);`
- `int snprintf(char *restrict s, size_t n, const char *restrict format, ...);`
- `long int strtol(const char *restrict nptr, char **restrict endptr, int base);`

Quel qualificatore `restrict` (introdotto in C99 e confermato in C23) si applica solo a puntatori a oggetti (`T *restrict p`) e rappresenta una **promessa al compilatore**: durante l'esecuzione del blocco (o della funzione) in cui `p` è dichiarato, ogni oggetto in memoria che viene modificato tramite `p` non sarà letto né scritto attraverso nessun altro puntatore che non derivi da `p`.

In pratica, scrivere `void somma_vettori(double *restrict dst, const double *restrict a, const double *restrict b, size_t n)` dichiara che il buffer di destinazione `dst` non si sovrappone in memoria ad `a` né a `b`. Grazie a questa garanzia il compilatore può ottimizzare i cicli con molta più libertà, mantenendo i valori nei registri della CPU o eseguendo più operazioni in parallelo senza dover rileggere `a[i]` e `b[i]` dalla memoria dopo ogni scrittura su `dst[i]`.

La promessa però è vincolante: secondo lo standard C23, violare `restrict` — per esempio passando due puntatori che raggiungono aree sovrapposte mentre almeno uno dei due modifica i dati — provoca **comportamento indefinito**. Per questo devi usare `restrict` solo quando il contratto della funzione richiede buffer disgiunti; devi invece evitarlo nelle trasformazioni *in-place* o quando sorgente e destinazione possono coincidere o sovrapporsi.

### Esempio guidato

Prima verifichiamo che il compilatore rifiuti la conversione illegale da `char **` a `const char **`: questo programma di tipo `errore` dimostra il vincolo di `const` sul secondo livello.

<!-- cod: id=14.4-b tipo=errore -->
```c
#include <stdio.h>

void stampa_errata(const char **v, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        printf("%s\n", v[i]);
    }
}

int main(void) {
    char s1[] = "alfa";
    char *elenco[1] = {s1};
    stampa_errata(elenco, 1); // Errore di compilazione: char ** non si converte in const char **
    return 0;
}
```

Il compilatore segnala l'incompatibilità tra il tipo dell'argomento (`char **`) e quello del parametro (`const char **`). Il programma eseguibile seguente mostra invece la progettazione corretta: una funzione `stampa_etichette` che accetta `const char *const *` (chiamata su un array `const char *`), una funzione vettoriale `scala_disgiunto` con `restrict` che opera su buffer separati e una trasformazione *in-place* `scala_sul_posto` senza `restrict`.

<!-- cod: id=14.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

void stampa_etichette(const char *const *v, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        printf("[%zu] %s\n", i, v[i]);
    }
}

void scala_disgiunto(double *restrict dst, const double *restrict src, size_t n, double fattore) {
    for (size_t i = 0; i < n; ++i) {
        dst[i] = src[i] * fattore;
    }
}

void scala_sul_posto(double *dati, size_t n, double fattore) {
    for (size_t i = 0; i < n; ++i) {
        dati[i] *= fattore;
    }
}

int main(void) {
    const char *nomi[3] = {"temperatura", "pressione", "umidita"};
    stampa_etichette(nomi, 3);

    double ingresso[4] = {2.0, 4.0, 6.0, 8.0};
    double uscita[4] = {0.0, 0.0, 0.0, 0.0};

    scala_disgiunto(uscita, ingresso, 4, 1.5);
    printf("Dopo scala_disgiunto:");
    for (size_t i = 0; i < 4; ++i) {
        printf(" %.1f", uscita[i]);
    }
    printf("\n");

    scala_sul_posto(ingresso, 4, 0.5);
    printf("Dopo scala_sul_posto:");
    for (size_t i = 0; i < 4; ++i) {
        printf(" %.1f", ingresso[i]);
    }
    printf("\n");

    return 0;
}
```

```output
[0] temperatura
[1] pressione
[2] umidita
Dopo scala_disgiunto: 3.0 6.0 9.0 12.0
Dopo scala_sul_posto: 1.0 2.0 3.0 4.0
```

Nota perché ogni chiamata qui è completamente legale e chiara:

- `nomi` ha tipo `const char *[3]`, che decade a `const char **` e si converte implicitamente in `const char *const *` (aggiungendo `const` solo sul primo livello puntato).
- `scala_disgiunto` riceve `uscita` e `ingresso`, due array completamente separati: la promessa di `restrict` è rispettata. Chiamare `scala_disgiunto(ingresso, ingresso, 4, 1.5)` violerebbe invece il contratto di `restrict` provocando comportamento indefinito.
- Per modificare un buffer direttamente sul posto usiamo `scala_sul_posto`, che riceve un singolo puntatore senza `restrict`.

> **Approfondimento — Che cos'è l'aliasing dei puntatori**
> Si parla di *aliasing* quando due puntatori diversi raggiungono la stessa area di memoria. Senza `restrict`, il compilatore deve assumere in modo prudente che una scrittura attraverso `dst[i]` possa alterare il valore che verrà letto subito dopo da `src[i]`, rinunciando a tenere `src[i]` nei registri della CPU. Con `restrict` elimini questo dubbio a tempo di compilazione, lasciando al compilatore il via libera per generare codice macchina più efficiente.

### Esercizio 14.4 — Filtro di segnale con `restrict`, gestione sicura della sovrapposizione e `const` a due livelli

**Descrizione**

Scrivi un programma C che elabori un buffer dinamico di `cap` campioni `double` (`1 <= cap <= 100`) rispettando rigorosamente i contratti di `restrict` e `const`. Implementa quattro funzioni prima di `main`:

1. `bool fette_sovrapposte(size_t off_a, size_t off_b, size_t len)` che restituisce `true` se gli intervalli `[off_a, off_a + len)` e `[off_b, off_b + len)` condividono almeno un indice;
2. `void media_mobile_restrict(double *restrict dst, const double *restrict src, size_t n)` che richiede buffer disgiunti e calcola per `n == 1` `dst[0] = src[0]`, mentre per `n >= 2` calcola `dst[0] = (src[0] + src[1]) / 2.0`, `dst[i] = (src[i - 1] + src[i] + src[i + 1]) / 3.0` per `0 < i < n - 1` e `dst[n - 1] = (src[n - 2] + src[n - 1]) / 2.0`;
3. `bool applica_filtro(double *buf, size_t cap, size_t off_dst, size_t off_src, size_t len, bool *usato_tmp)` che controlla i limiti (`len >= 1`, `off_dst <= cap - len`, `off_src <= cap - len`), chiama direttamente `media_mobile_restrict` con `*usato_tmp = false` se le fette sono disgiunte, oppure alloca un buffer temporaneo `tmp`, calcola `media_mobile_restrict(tmp, buf + off_src, len)`, copia `tmp` in `buf + off_dst`, libera `tmp` e imposta `*usato_tmp = true` se le fette si sovrappongono;
4. `double energia_fette(const double *const *fette, const size_t *lunghezze, size_t k)` che riceve un array di puntatori a dati costanti (`const double *const *`) e somma i quadrati di tutti i campioni delle `k` fette.

In `main` leggi dalla prima riga `cap`, dalla seconda riga i `cap` campioni `double`, e poi fino a fine input comandi `FILTRA <off_dst> <off_src> <len>` stampando `FILTRA [<src>..+<len>] -> [<dst>..+<len>] (tmp=<si|no>)`. Al termine stampa il buffer finale (`%.2f`) e l'energia totale calcolata chiamando `energia_fette` sulle due metà `{buf, buf + cap / 2}` esattamente come nell'esempio.

**Concetti da tenere a mente**

- contratto del qualificatore `restrict`: assenza di sovrapposizione tra `dst` e `src`
- prevenzione del comportamento indefinito tramite rilevazione della sovrapposizione e buffer temporaneo
- `const`-correctness a due livelli con `const double *const *`
- gestione sicura dei limiti con aritmetica priva di overflow (`off <= cap - len`)

**Domande guida**

1. Perché chiamare `media_mobile_restrict(buf + 1, buf, 4)` direttamente senza buffer temporaneo violerebbe il contratto di `restrict` e produrrebbe comportamento indefinito?
2. Come stabilisce `fette_sovrapposte` se due sotto-intervalli di lunghezza `len` dentro lo stesso buffer si intersecano?
3. Che cosa impedisce di modificare ciascuno dei due `const` presenti nella firma `const double *const *fette`?
4. Perché conviene controllare `off_dst <= cap - len` (dopo aver verificato `len <= cap`) invece di scrivere `off_dst + len <= cap`?

**Esempio di esecuzione**

```input
6
0 6 0 6 0 6
FILTRA 3 0 3
FILTRA 1 0 4
```

```output
FILTRA [0..+3] -> [3..+3] (tmp=no)
FILTRA [0..+4] -> [1..+4] (tmp=si)
Buffer: 0.00 3.00 2.00 3.00 1.50 3.00
Energia totale: 33.25
```

## 14.5 Valori sentinella e puntatori pendenti

In questa ultima sotto-sezione uniamo due temi che ricorrono continuamente nella gestione di strutture dinamiche: come segnalare la fine di una sequenza di puntatori senza un contatore separato, e come evitare che un puntatore resti agganciato a memoria non più valida.

### Valori sentinella

Un **valore sentinella** (*sentinel value*) è un valore speciale, come `nullptr` o `'\0'`, posto al termine di una sequenza per segnalarne la fine senza un contatore separato. Ne conosci già due esempi fondamentali:

- il terminatore nullo `'\0'` alla fine di ogni stringa C;
- il puntatore nullo `argv[argc] == nullptr` al termine degli argomenti da riga di comando.

Puoi applicare lo stesso schema a qualsiasi tabella dinamica di stringhe `char **voci`: se garantisci che dopo l'ultima stringa valida ci sia sempre un elemento uguale a `nullptr`, qualunque funzione che riceve `voci` può scandire, contare o liberare tutti gli elementi con un semplice ciclo `for (size_t i = 0; voci[i] != nullptr; ++i)` senza dover passare la lunghezza come parametro separato.

Questa comodità ha due costi precisi che vanno sempre considerati:

1. **Calcolo della lunghezza in tempo lineare ($O(n)$):** per sapere quanti elementi contiene la sequenza occorre scorrerla fino alla sentinella (proprio come fa `strlen`).
2. **Obbligo dello slot extra (`+ 1`):** ogni volta che allochi o riallochi la sequenza per `n` elementi validi devi riservare spazio per `n + 1` puntatori (e quando aggiungi un elemento a `n` già presenti, `realloc` deve richiedere `n + 2` puntatori: gli `n` vecchi, il nuovo e la sentinella `nullptr`). Dimenticare lo slot della sentinella provoca un accesso fuori dai limiti.

### Puntatori pendenti

Un **puntatore pendente** (*dangling pointer*) è un puntatore che conserva l'indirizzo di un oggetto la cui durata di vita è terminata o che è stato liberato. Secondo lo standard C23, dereferenziare, confrontare in modo ordinato o anche solo leggere il valore ormai indeterminato di un puntatore pendente dopo `free` o `realloc` provoca **comportamento indefinito**.

Esistono quattro cause principali di puntatori pendenti. I frammenti seguenti mostrano ciascun errore — **non vanno mai scritti così** — insieme alla relativa correzione.

**1. Restituire l'indirizzo di una variabile locale sullo stack.** Quando la funzione termina, il suo record sullo stack viene distrutto e l'indirizzo restituito punta a memoria non più valida:

<!-- cod: id=14.5-b tipo=frammento -->
```c
// ERRORE (comportamento indefinito): restituisce l'indirizzo di una variabile locale
int *crea_sbagliato(int v) {
    int locale = v;
    return &locale; // locale termina la durata di vita all'uscita dalla funzione!
}
// CORREZIONE: alloca sullo heap con malloc/calloc (chi chiama poi esegue free),
// oppure scrivi il risultato in un parametro passato dal chiamante.
```

**2. Conservare fuori da un blocco l'indirizzo di una variabile dichiarata nel blocco.** La durata di vita di `temporanea` termina alla graffa chiusa:

<!-- cod: id=14.5-c tipo=frammento -->
```c
// ERRORE (comportamento indefinito): puntatore a variabile di blocco interno
int *p = nullptr;
{
    int temporanea = 10;
    p = &temporanea;
}
// Qui p è un puntatore pendente: leggere *p è comportamento indefinito!
// CORREZIONE: dichiara la variabile nello stesso ambito in cui vive p (o più esterno).
```

**3. Non azzerare un puntatore (o un suo alias) dopo `free`.** Dopo `free(a)`, sia `a` sia qualsiasi altra copia `b = a` diventano puntatori pendenti:

<!-- cod: id=14.5-d tipo=frammento -->
```c
// ERRORE (comportamento indefinito): uso dopo la liberazione tramite puntatore o alias
int *a = malloc(sizeof(*a));
int *b = a;
free(a);
// Qui sia a sia b sono puntatori pendenti: accedere a *a o *b è comportamento indefinito!
// CORREZIONE: azzera il puntatore subito dopo free (meglio tramite funzione int **),
// ed evita di mantenere alias non necessari oltre la durata di vita del blocco.
```

**4. Conservare un puntatore diretto a un elemento dentro un array ridimensionato con `realloc`.** Se `realloc` sposta il blocco in una nuova posizione dello heap, il vecchio blocco viene liberato e ogni puntatore a suoi elementi diventa pendente:

<!-- cod: id=14.5-e tipo=frammento -->
```c
// ERRORE (comportamento indefinito): puntatore invalidato da realloc
int *dati = malloc(2 * sizeof(*dati));
int *primo = &dati[0];
int *tmp = realloc(dati, 100 * sizeof(*dati));
if (tmp != nullptr) {
    dati = tmp;
    // Se realloc ha spostato il blocco, primo è ora un puntatore pendente!
}
// CORREZIONE: salva l'indice (size_t idx_primo = 0;) e accedi come dati[idx_primo].
```

### Strategie di prevenzione

Per tenere lontani i puntatori pendenti dal tuo codice, adotta tre abitudini sistematiche:

- Usa funzioni di rilascio con `T **` che chiamano `free(*p); *p = nullptr;`, azzerando il puntatore del chiamante nello stesso punto in cui liberi la memoria.
- Dentro array dinamici che possono crescere con `realloc`, identifica gli elementi tramite **indici `size_t`** anziché tramite puntatori diretti agli elementi.
- Compila e prova regolarmente i tuoi programmi con **AddressSanitizer** (`-fsanitize=address,undefined`, visto nel capitolo 11), che intercetta subito uso dopo la liberazione, accessi fuori dai limiti e uso di variabili di stack fuori ambito.

> **Se vieni da Python** — In Python il *garbage collector* impedisce i puntatori pendenti mantenendo vivi gli oggetti finché esistono riferimenti; in C la durata di vita è gestita esplicitamente e un puntatore a memoria liberata o spostata da `realloc` diventa subito un puntatore pendente.

### Esempio guidato

Il programma seguente gestisce una lista dinamica di comandi `char **comandi` terminata dal valore sentinella `nullptr`. Per ricordare quale comando è attualmente attivo memorizza un indice `size_t attivo_idx` (e non un `char **` o un `char *` diretto dentro l'array), così il riferimento resta valido anche dopo ripetute chiamate a `realloc`. Al termine `libera_comandi` distrugge tutto e azzera `comandi` a `nullptr`.

<!-- cod: id=14.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

size_t conta_comandi(char *const *lista) {
    if (lista == nullptr) {
        return 0;
    }
    size_t n = 0;
    while (lista[n] != nullptr) {
        ++n;
    }
    return n;
}

bool aggiungi_comando(char ***lista, const char *testo) {
    if (lista == nullptr || testo == nullptr) {
        return false;
    }
    size_t n = conta_comandi(*lista);
    char *copia = strdup(testo);
    if (copia == nullptr) {
        return false;
    }
    char **tmp = realloc(*lista, (n + 2) * sizeof(*tmp));
    if (tmp == nullptr) {
        free(copia);
        return false;
    }
    *lista = tmp;
    (*lista)[n] = copia;
    (*lista)[n + 1] = nullptr;
    return true;
}

void libera_comandi(char ***lista) {
    if (lista == nullptr || *lista == nullptr) {
        return;
    }
    for (size_t i = 0; (*lista)[i] != nullptr; ++i) {
        free((*lista)[i]);
    }
    free(*lista);
    *lista = nullptr;
}

int main(void) {
    char **comandi = nullptr;

    if (!aggiungi_comando(&comandi, "avvia") ||
        !aggiungi_comando(&comandi, "controlla")) {
        libera_comandi(&comandi);
        return EXIT_FAILURE;
    }

    size_t attivo_idx = 1; // Indice sicuro invece di char **attivo = &comandi[1]
    printf("Comando attivo prima di realloc: %s\n", comandi[attivo_idx]);

    if (!aggiungi_comando(&comandi, "salva") ||
        !aggiungi_comando(&comandi, "chiudi")) {
        libera_comandi(&comandi);
        return EXIT_FAILURE;
    }

    printf("Totale comandi: %zu\n", conta_comandi(comandi));
    for (size_t i = 0; comandi[i] != nullptr; ++i) {
        printf("[%zu] %s%s\n", i, comandi[i], (i == attivo_idx) ? " <- attivo" : "");
    }

    libera_comandi(&comandi);
    printf("Dopo rilascio: comandi nullo = %d\n", comandi == nullptr);
    return EXIT_SUCCESS;
}
```

```output
Comando attivo prima di realloc: controlla
Totale comandi: 4
[0] avvia
[1] controlla <- attivo
[2] salva
[3] chiudi
Dopo rilascio: comandi nullo = 1
```

Osserva come l'esempio mette in pratica tutti i concetti della sotto-sezione:

- `conta_comandi` riceve `char *const *` (nel pieno rispetto delle regole di `const` della sotto-sezione 14.4) e conta gli elementi fermandosi alla sentinella `nullptr`.
- In `aggiungi_comando`, `realloc` chiede sempre `(n + 2) * sizeof(*tmp)`: gli `n` puntatori esistenti, il nuovo puntatore in posizione `n` e la sentinella `nullptr` in posizione `n + 1`. Nota che qui compare `char ***lista` solo perché `comandi` non è ancora racchiuso in una `struct`: nell'esercizio 14.5 vedrai come incapsulare `char **voci` in una `struct elenco` elimini il terzo asterisco!
- Dopo le due nuove chiamate a `aggiungi_comando` (ciascuna con `realloc`), `comandi[attivo_idx]` continua a individuare esattamente `"controlla"`, senza alcun rischio di puntatore pendente.
- `libera_comandi(&comandi)` libera prima ogni stringa fino alla sentinella, poi libera l'array e imposta `*lista = nullptr`, così `comandi` nel `main` non resta mai pendente.

> **Approfondimento — Perché un indice `size_t` è immune allo spostamento di `realloc`**
> Quando `realloc` ingrandisce un blocco sullo heap e non trova spazio adiacente libero, alloca un nuovo blocco altrove, copia i byte e libera il vecchio. L'indirizzo assoluto del blocco cambia, rendendo immediatamente pendente qualsiasi puntatore che vi puntava dentro; la posizione relativa `idx` dell'elemento rispetto all'inizio del blocco, invece, rimane identica e `comandi[idx]` calcola sempre l'indirizzo corretto sulla nuova base.

### Esercizio 14.5 — Elenco dinamico terminato da sentinella `nullptr` con segnalibro per indice immune a `realloc`

**Descrizione**

Scrivi un programma C che definisca `typedef struct elenco { char **voci; bool ha_evid; size_t idx_evid; } elenco_t;` dove `voci` è un array dinamico di `char *` **sempre terminato dal valore sentinella `nullptr`** (senza campo lunghezza separato) e la voce evidenziata è tracciata tramite l'indice `idx_evid` anziché tramite un puntatore diretto che diventerebbe un puntatore pendente dopo `realloc` o dopo una rimozione. Implementa quattro funzioni:

1. `size_t conta_voci(char *const *voci)` che conta le stringhe scorrendo fino alla sentinella `nullptr` (`0` se `voci == nullptr`);
2. `bool aggiungi_voce(elenco_t *e, const char *testo)` che calcola `n = conta_voci(e->voci)`, duplica `testo` con `strdup`, rialloca `e->voci` per `n + 2` puntatori (`n + 1` stringhe + la sentinella `nullptr`), inserisce la copia in `e->voci[n]` e scrive `e->voci[n + 1] = nullptr`;
3. `bool rimuovi_voce(elenco_t *e, size_t pos)` che controlla `pos < conta_voci(e->voci)`, libera `e->voci[pos]`, sposta a sinistra i puntatori successivi fino a includere la sentinella `nullptr` e aggiorna il segnalibro (`ha_evid = false` se `idx_evid == pos`, `--idx_evid` se `idx_evid > pos`);
4. `void libera_elenco(elenco_t *e)` che scorre fino alla sentinella liberando ogni stringa, libera `e->voci` e azzera `e->voci = nullptr`, `e->ha_evid = false`, `e->idx_evid = 0`.

In `main` elabora fino a fine input i comandi `ADD <parola>` (`%31s`), `MARK <idx>`, `DEL <idx>` e `LIST` (stampa `[<i>] <parola>` con ` *` se evidenziata, oppure `(vuoto)`). Al termine stampa il conteggio finale, l'eventuale voce evidenziata, chiama `libera_elenco(&e)` e stampa `Puntatore azzerato: 1` verificando `e.voci == nullptr`.

**Concetti da tenere a mente**

- array dinamico di puntatori `char **` terminato dal valore sentinella `nullptr`
- riserva dello slot aggiuntivo (`n + 2`) per mantenere sempre la sentinella finale dopo `realloc`
- uso di un indice `size_t` al posto di un puntatore diretto per evitare puntatori pendenti dopo `realloc`
- azzeramento sistematico di `e->voci = nullptr` dopo `free` per prevenire uso dopo la liberazione

**Domande guida**

1. Perché in `aggiungi_voce` devi richiedere spazio per `n + 2` puntatori a `realloc` invece di `n + 1`?
2. Che cosa accadrebbe se la voce evidenziata fosse salvata come `char **ptr_evid = &e.voci[1]` e subito dopo arrivasse un comando `ADD` che fa spostare `e.voci` a `realloc`?
3. Come deve essere aggiornato `idx_evid` quando viene rimossa una voce con posizione minore di `idx_evid` rispetto a quando viene rimossa esattamente la voce evidenziata?
4. Perché `libera_elenco` deve liberare tutte le stringhe fino alla sentinella prima di chiamare `free(e->voci)` e impostare `e->voci = nullptr`?

**Esempio di esecuzione**

```input
ADD alfa
ADD beta
ADD gamma
MARK 1
ADD delta
DEL 0
LIST
DEL 0
LIST
```

```output
[0] beta *
[1] gamma
[2] delta
[0] gamma
[1] delta
Totale finale: 2
Evidenziata: nessuna
Puntatore azzerato: 1
```

## Riepilogo

- Un **puntatore a puntatore** (`T **pp = &p;`) memorizza l'indirizzo di una variabile puntatore `T *p`: con `*pp` si legge o si modifica `p` nel chiamante, mentre con `**pp` si accede all'oggetto di tipo `T` puntato da `p`. È lo strumento standard per riallocare un array tramite parametro di uscita, scambiare puntatori in tempo costante, avanzare un cursore di lettura (`const char **`) e liberare memoria azzerando il puntatore del chiamante (`free(*p); *p = nullptr;`). Verifica sempre `pp != nullptr` e, quando serve, `*pp != nullptr` prima di dereferenziare.
- Le **matrici dinamiche** di `R` righe e `C` colonne si rappresentano sullo heap in due modi principali: per righe (`T **m`, con `R + 1` allocazioni, accesso `m[i][j]`, scambio di righe in tempo costante e pulizia parziale obbligatoria in caso di fallimento) oppure in un unico blocco contiguo (`T *dati = calloc(R * C, sizeof(*dati))`, previo controllo `R <= SIZE_MAX / C`, con accesso `dati[i * C + j]`, una sola `free` e migliore località in memoria, tema che riprenderemo nel capitolo 25). Un array bidimensionale statico `T a[R][C]` decade a `T (*)[C]`, non a `T **`.
- Con la firma `int main(int argc, char *argv[])` il programma riceve `argc` argomenti da riga di comando e la garanzia che `argv[argc] == nullptr`. Per convertire stringhe in numeri in modo rigoroso si usano `strtol`, `strtoul`, `strtoll`, `strtoull` e `strtod` (`<stdlib.h>`), azzerando sempre `errno = 0` (`<errno.h>`) prima della chiamata e verificando `endptr != s`, `*endptr == '\0'` e `errno != ERANGE` (oltre a `±HUGE_VAL` di `<math.h>` per `strtod`).
- In C la conversione implicita che aggiunge `const` è consentita solo sul primo livello puntato: `T *` → `const T *` e `T **` → `T *const *` sono valide, mentre `T **` → `const T **` è vietata per prevenire modifiche non sicure a oggetti `const`. Il qualificatore `restrict` (`T *restrict p`) promette al compilatore l'assenza di sovrapposizione per gli oggetti modificati tramite `p`; violare questa promessa provoca comportamento indefinito.
- Un **valore sentinella** (`'\0'` nelle stringhe, `nullptr` negli array di puntatori) chiude una sequenza senza contatore separato, al costo di una scansione lineare per la lunghezza e di uno slot aggiuntivo (`+ 1`). Un **puntatore pendente** nasce quando l'oggetto puntato termina la durata di vita (uscita da funzione o blocco, `free`, spostamento da parte di `realloc`): usarne il valore è comportamento indefinito. Si previene azzerando i puntatori dopo `free`, usando indici `size_t` dentro array ridimensionabili e verificando con AddressSanitizer.

## Errori comuni

- **Passare un puntatore singolo `T *` a una funzione credendo che assegnare `parametro = nuovo_blocco` aggiorni anche il puntatore del chiamante**: in C gli argomenti sono passati per valore; per modificare il puntatore del chiamante (allocazione, `realloc`, azzeramento dopo `free`) occorre passare `&ptr` a un parametro `T **`.
- **Confondere un array bidimensionale statico `int m[3][4]` con una matrice dinamica `int **`, oppure dimenticare la pulizia parziale in `T **`**: `int m[3][4]` decade a `int (*)[4]` perché in memoria contiene solo i 12 interi contigui, senza puntatori di riga. Nell'allocazione per righe, se fallisce la riga `i`, devi liberare le righe `0..i-1` e poi l'array di puntatori per evitare perdite di memoria.
- **Dimenticare `errno = 0;` prima di chiamare `strtol` o `strtod`, oppure non controllare `endptr`**: nessuna funzione della libreria standard azzera `errno` in caso di successo; inoltre, controllare solo il valore restituito non distingue `"0"` da `"abc"` né individua caratteri residui come `"12xy"` (`endptr != s` e `*endptr == '\0'`).
- **Tentare di convertire implicitamente `char **` in `const char **` o violare il contratto di `restrict`**: il compilatore rifiuta `char ** -> const char **`; per API di sola lettura su stringhe usa `const char *const *` (partendo da `const char *[]`) oppure `char *const *`. Non passare mai aree di memoria sovrapposte a una funzione con parametri `restrict` quando almeno uno dei puntatori scrive.
- **Conservare un puntatore diretto a un elemento attraverso una chiamata a `realloc`, oppure dimenticare lo slot per la sentinella `nullptr`**: se `realloc` sposta il blocco sullo heap, ogni puntatore a suoi elementi diventa un puntatore pendente; usa invece un indice `size_t`. Negli array terminati da `nullptr`, riserva sempre spazio per `n + 1` puntatori (`n + 2` quando inserisci un nuovo elemento).

## Prima di proseguire

- [ ] So spiegare la differenza tra `pp`, `*pp` e `**pp` e scrivere funzioni con parametri `T **` per allocare, riallocare, scambiare e azzerare puntatori del chiamante.
- [ ] So allocare, usare e liberare senza perdite di memoria sia una matrice dinamica per righe (`T **`) sia una matrice in blocco contiguo (`T *` con controllo `R <= SIZE_MAX / C`), e so spiegare perché `int a[3][4]` non è un `int **`.
- [ ] So analizzare opzioni e argomenti da riga di comando con `argc`/`argv` e convertire stringhe con `strtol` e `strtod` verificando `endptr`, `errno`, `ERANGE` e `HUGE_VAL`.
- [ ] So leggere da destra a sinistra `const` su puntatori multipli, spiegare perché `char **` non si converte in `const char **` e applicare `restrict` solo quando i buffer sono garantiti disgiunti.
- [ ] So gestire array dinamici terminati dal valore sentinella `nullptr` e prevenire i quattro casi tipici di puntatore pendente usando indici `size_t` e azzeramento dopo `free`.
