# Capitolo 15 — Programmazione generica con void *

> **In questo capitolo imparerai a:**
> - Convertire e manipolare puntatori generici `void *` in modo sicuro
> - Copiare, spostare, confrontare e inizializzare blocchi di byte con `memcpy`, `memmove`, `memcmp` e `memset`
> - Progettare e implementare un vettore dinamico generico indipendente dal tipo degli elementi
> - Scrivere codice adattato al tipo e verifiche a tempo di compilazione con `_Generic`, `typeof`, `auto` e `static_assert`

> **Ti servono:** puntatori e aritmetica dei puntatori (cap. 10), memoria dinamica sullo heap (cap. 11), `struct` ed `enum` (cap. 12), tipi interi a larghezza fissa, `alignof`, `offsetof` e padding (cap. 13), puntatori a puntatore, `restrict` e puntatori pendenti (cap. 14).

Nel capitolo precedente hai visto come gestire puntatori a puntatore, matrici dinamiche e argomenti da riga di comando mantenendo il controllo sui tipi e sulla durata di vita della memoria. Ogni struttura dati che hai scritto finora, però, era legata a un solo tipo concreto: un array dinamico di `int`, un elenco di stringhe, una tabella di `double`. Appena il programma ha bisogno dello stesso contenitore per un nuovo tipo di dato — per esempio una `struct` di misure o di eventi — dovresti duplicare tutto il codice cambiando solo il tipo dichiarato.

In C non esistono classi generiche né template automatici, ma il linguaggio mette a disposizione due leve complementari molto potenti. A tempo di esecuzione puoi astrarre dal tipo concreto lavorando su indirizzi generici (`void *`) e su blocchi grezzi di byte tramite le funzioni `memcpy`, `memmove`, `memcmp`, `memset` e `memchr`: è il fondamento su cui poggiano tutti i contenitori generici della libreria standard e dei programmi reali. A tempo di compilazione, invece, il C23 ti offre strumenti come `_Generic`, `typeof`, `typeof_unqual`, `auto` e `static_assert` per adattare il codice al tipo esatto delle espressioni e verificare in anticipo ipotesi su dimensioni, allineamento e layout, senza alcun costo durante l'esecuzione.

In questo capitolo unirai entrambi i livelli: partirai dalle regole precise di `void *` e della manipolazione di byte, costruirai da zero un vettore dinamico generico sicuro contro overflow e problemi di allineamento, e imparerai a sfruttare le selezioni statiche e le verifiche a tempo di compilazione del C23. Questi strumenti preparano direttamente il terreno ai puntatori a funzione e alle strutture dati dinamiche generiche dei capitoli successivi.

## 15.1 Il puntatore generico `void *`

Quando scrivi una funzione in C, ogni parametro puntatore dichiara in modo esplicito il tipo dell'oggetto a cui punta: `int *`, `double *`, `const char *`. Questa informazione è preziosa perché permette al compilatore di verificare la coerenza dei tipi, calcolare gli spostamenti dell'aritmetica dei puntatori e leggere il numero corretto di byte durante la dereferenziazione. In molti scenari, però, vuoi scrivere una funzione o una struttura dati che riceva l'indirizzo di un oggetto *senza sapere in anticipo quale sia il suo tipo*.

Hai già incontrato questo meccanismo nel capitolo 11 con `malloc`, `calloc` e `realloc`: queste funzioni restituiscono un indirizzo di tipo `void *` perché l'allocatore riserva una sequenza di byte sullo heap e non può sapere se tu vi memorizzerai interi, numeri in virgola mobile o strutture. Quell'indirizzo è un **puntatore generico** (*generic pointer*): un puntatore di tipo `void *` capace di contenere l'indirizzo di qualsiasi oggetto, ma non dereferenziabile direttamente.

L'idea intuitiva è semplice: un puntatore tipizzato (`double *`) conserva due informazioni — *dove* inizia l'oggetto in memoria e *come* interpretarne i byte — mentre `void *` conserva soltanto la prima. Per questo puoi pensare a `void *` come a un "indirizzo puro" di un oggetto: puoi passarlo a funzioni generiche, salvarlo in una struttura o confrontarlo con un altro indirizzo, ma non puoi leggere o scrivere il valore puntato finché non restituisci al compilatore l'informazione sul tipo originale.

```text
Variabili in memoria              Puntatore generico
---------------------             ------------------
int n = 42;        [ 4 byte ] <--+
double x = 3.5;    [ 8 byte ]    +-- void *p  (conosce solo l'indirizzo,
                                               non il tipo né la dimensione)
```

### Conversioni implicite e qualificazione `const`

Una caratteristica centrale del C è che la conversione tra qualunque puntatore a oggetto `T *` e `void *` avviene **implicitamente**, in entrambe le direzioni, senza bisogno di alcun cast esplicito:

<!-- cod: id=15.1-b tipo=frammento -->
```c
int valore = 42;
void *generico = &valore;   // int * -> void * (implicita)
int *ripristinato = generico; // void * -> int * (implicita)
```

Questa stessa regola spiega perché dal capitolo 11 scrivi `int *v = malloc(n * sizeof(*v));` senza anteporre `(int *)` davanti a `malloc`. Oltre a essere più pulito, omettere il cast evita di mascherare errori di tipo o di qualificazione.

La conversione implicita rispetta rigorosamente il qualificatore `const`:
- un puntatore `T *` può convertirsi implicitamente in `void *` oppure in `const void *`;
- un puntatore `const T *` può convertirsi implicitamente **solo** in `const void *`, mai in `void *`;
- un `const void *` può riconvertirsi implicitamente in `const T *`, mai in `T *` (perché permetterebbe di modificare un oggetto dichiarato di sola lettura).

Quando progetti funzioni generiche che si limitano a leggere i dati puntati (per esempio una funzione di stampa o di confronto), usa sempre `const void *` come parametro: in questo modo accetti sia oggetti mutabili sia oggetti `const` senza violare le garanzie di sola lettura.

### Divieti dello standard e calcolo di indirizzi a byte

Poiché `void` è un tipo incompleto senza dimensione (`sizeof(void)` non è valido in C standard), il compilatore non sa quanti byte occupi l'oggetto puntato da un `void *`. Da questa assenza di dimensione discendono due divieti tassativi dello standard C23:

1. **Non puoi dereferenziare un `void *`**: scrivere `*p` quando `p` ha tipo `void *` o `const void *` è un errore di compilazione.
2. **Non puoi eseguire aritmetica dei puntatori su `void *`**: scrivere `p + 1` o `p += dim` viola lo standard C23 ed è rifiutato dal compilatore con `-Wpedantic` (anche se alcuni compilatori offrono come estensione non standard l'aritmetica a passo 1 byte, non devi mai affidarti a tale estensione).

Ecco due piccoli programmi che illustrano entrambi i divieti e vengono rifiutati dal compilatore:

<!-- cod: id=15.1-c tipo=errore -->
```c
#include <stdio.h>

int main(void) {
    int x = 10;
    void *p = &x;
    printf("%d\n", *p); // Errore: impossibile dereferenziare void *
    return 0;
}
```

<!-- cod: id=15.1-d tipo=errore -->
```c
#include <stdio.h>

int main(void) {
    int dati[3] = {1, 2, 3};
    void *p = dati;
    void *q = p + 1; // Errore con -Wpedantic: aritmetica su void * non ammessa
    (void)q;
    return 0;
}
```

In entrambi i casi il compilatore segnala una violazione delle regole sul tipo `void *` (dereferenziazione non valida nel primo caso, aritmetica su puntatore a `void` nel secondo).

Come si calcola allora in modo portabile l'indirizzo dell'elemento `i`-esimo di una sequenza generica in cui ogni elemento occupa `dim_elem` byte? Si converte il `void *` (o `const void *`) in `unsigned char *` (o `const unsigned char *`) e si esegue l'aritmetica su quello:

<!-- cod: id=15.1-e tipo=frammento -->
```c
const unsigned char *byte_base = base;
const void *elem_i = byte_base + i * dim_elem;
```

Poiché `sizeof(unsigned char)` è garantito uguale a `1` su qualunque architettura, `byte_base + i * dim_elem` avanza esattamente di `i * dim_elem` byte e il risultato si riconverte implicitamente a `const void *`.

### Riconversione sicura e limiti di `void *`

Riassumiamo la regola completa dello standard C23 su `void *`:
- Un puntatore generico `void *` (o `const void *`) può memorizzare l'indirizzo di qualsiasi oggetto in memoria; qualsiasi puntatore a oggetto `T *` si converte implicitamente in `void *` e viceversa senza cast, purché non si rimuovano qualificatori `const`.
- Non è consentito dereferenziare un `void *` né applicarvi l'aritmetica dei puntatori: per accedere ai dati occorre riconvertirlo al tipo originale esatto, mentre per calcolare spiazzamenti in byte occorre convertirlo a `unsigned char *` (o `const unsigned char *`).
- Il tipo `void *` riguarda **solo puntatori a oggetti**, non puntatori a funzione (lo vedremo nel capitolo 16): su alcune architetture gli indirizzi di codice e gli indirizzi di dati possono persino avere rappresentazioni diverse, perciò convertire indirizzi di funzioni in `void *` non è portabile secondo lo standard C23.

Secondo lo standard C23, le conversioni implicite tra `T *` e `void *` e la riconversione al tipo esatto originale sono completamente definite. Al contrario, dereferenziare un `void *` o applicarvi l'aritmetica è una violazione di vincolo (errore di compilazione), mentre **riconvertire un `void *` a un tipo incompatibile rispetto all'oggetto originale e dereferenziarlo provoca comportamento indefinito**: il compilatore assume che puntatori a tipi diversi non si riferiscano allo stesso oggetto (approfondiremo questa regola, nota come *strict aliasing*, nel capitolo 22), e la lettura potrebbe sia interpretare bit sbagliati sia leggere oltre i limiti dell'oggetto.

Per evitare errori di riconversione, un programma C usa sempre uno di due meccanismi:
1. un'**etichetta esplicita** (di solito un `enum`) conservata accanto al `void *`, che dice alla funzione a quale tipo riconvertire il puntatore;
2. un **contratto documentato** tra chiamante e funzione (per esempio un contenitore omogeneo che conserva solo oggetti di un unico tipo stabilito alla creazione, come vedrai nella sotto-sezione 15.3).

### Esempio guidato

Il programma seguente mostra tutte le operazioni corrette su `void *`: conserva in sequenza nello stesso `void *` l'indirizzo di un `int`, di un `double` e di una `struct punto_2d`, li passa a una funzione generica `stampa_oggetto(const void *p, tipo_dato_t t)` guidata da un `enum`, e calcola l'indirizzo dell'elemento `i`-esimo di un array generico tramite `(const unsigned char *)base + i * dim_elem`.

<!-- cod: id=15.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>

typedef enum tipo_dato : int {
    TIPO_INTERO = 0,
    TIPO_REALE = 1,
    TIPO_PUNTO = 2
} tipo_dato_t;

typedef struct punto_2d {
    int x;
    int y;
} punto_2d_t;

const void *calcola_indirizzo(const void *base, size_t indice, size_t dim_elem) {
    const unsigned char *bytes = base;
    return bytes + indice * dim_elem;
}

void stampa_oggetto(const void *p, tipo_dato_t tipo) {
    if (p == nullptr) {
        printf("(nullo)\n");
        return;
    }
    switch (tipo) {
        case TIPO_INTERO: {
            const int *pi = p;
            printf("int: %d\n", *pi);
            break;
        }
        case TIPO_REALE: {
            const double *pd = p;
            printf("double: %.2f\n", *pd);
            break;
        }
        case TIPO_PUNTO: {
            const punto_2d_t *pp = p;
            printf("punto: (%d, %d)\n", pp->x, pp->y);
            break;
        }
    }
}

int main(void) {
    int quota = 120;
    double temperatura = 21.75;
    punto_2d_t vertici[3] = {{0, 0}, {4, 3}, {8, 6}};

    void *generico = &quota;
    stampa_oggetto(generico, TIPO_INTERO);

    generico = &temperatura;
    stampa_oggetto(generico, TIPO_REALE);

    generico = &vertici[1];
    stampa_oggetto(generico, TIPO_PUNTO);

    for (size_t i = 0; i < 3; ++i) {
        const void *elem = calcola_indirizzo(vertici, i, sizeof(punto_2d_t));
        stampa_oggetto(elem, TIPO_PUNTO);
    }

    return 0;
}
```

```output
int: 120
double: 21.75
punto: (4, 3)
punto: (0, 0)
punto: (4, 3)
punto: (8, 6)
```

Analizziamo i punti chiave del programma:
- In `main`, la stessa variabile `void *generico` memorizza prima `&quota` (`int *`), poi `&temperatura` (`double *`) e infine `&vertici[1]` (`punto_2d_t *`), sempre con conversione implicita e senza alcun cast.
- `stampa_oggetto` accetta `const void *p` perché non deve modificare l'oggetto puntato. Dentro ciascun ramo dello `switch`, il parametro `p` viene assegnato implicitamente al puntatore tipizzato corrispondente (`const int *`, `const double *`, `const punto_2d_t *`) prima di dereferenziarlo con `*` o `->`.
- La funzione `calcola_indirizzo` riceve `const void *base`, l'indice `indice` e la dimensione in byte `dim_elem`. Non potendo scrivere `base + indice * dim_elem`, assegna `base` a `const unsigned char *bytes` e restituisce `bytes + indice * dim_elem`, che si riconverte implicitamente a `const void *`.
- Nel ciclo finale, `vertici` decade a `punto_2d_t *`, poi si converte implicitamente a `const void *`; `calcola_indirizzo` individua esattamente ciascuna delle tre strutture `punto_2d_t` in memoria senza conoscere affatto la definizione di `punto_2d_t`.

> **Approfondimento — Perché la conversione tra `void *` e `unsigned char *` è sempre portabile**
> In C non tutti i tipi di puntatore sono tenuti dallo standard ad avere la stessa rappresentazione interna (anche se sulle architetture moderne di uso comune coincidono). Lo standard C23 stabilisce però una garanzia esplicita: `void *` e `char *` (con le loro varianti `signed`/`unsigned` e qualificate `const`) hanno sempre la stessa rappresentazione in memoria e gli stessi requisiti di allineamento. Inoltre, qualsiasi oggetto in memoria può essere esaminato come sequenza di `sizeof(oggetto)` byte di tipo `unsigned char`. Per questo motivo convertire un `void *` a `unsigned char *` per calcolare un offset in byte è garantito portabile su ogni compilatore conforme allo standard.

### Esercizio 15.1 — Registro eterogeneo di parametri con puntatori generici `void *` e indirizzamento a byte

**Descrizione**

Scrivi un programma C che modelli un registro di `6` parametri di tipi eterogenei usando un puntatore generico `void *`. Definisci `typedef enum tipo_param : int { TIPO_INT = 0, TIPO_DOUBLE = 1, TIPO_BOOL = 2 } tipo_param_t;` e `typedef struct voce_reg { char nome[16]; tipo_param_t tipo; void *ptr; } voce_reg_t;`. Implementa tre funzioni:

1. `const void *elemento_generico(const void *base, size_t idx, size_t dim_elem)` che calcola l'indirizzo dell'elemento `idx` convertendo `base` a `const unsigned char *` e aggiungendo `idx * dim_elem` (senza aritmetica su `void *`);
2. `void stampa_parametro(const voce_reg_t *v)` che riconverte `(const void *)v->ptr` al puntatore tipizzato esatto (`const int *`, `const double *`, `const bool *`) e stampa `<nome> (<tipo>) = <valore>` (`%.2f` per `double`, `true`/`false` per `bool`);
3. `bool aggiorna_parametro(voce_reg_t *v, const char *val_str)` che valida e converte `val_str` con `strtol` (controllando `endptr`, `errno == ERANGE` e `INT_MIN..INT_MAX` per `TIPO_INT`; accettando solo `"0"` o `"1"` per `TIPO_BOOL`) o `strtod` (escludendo NaN, `HUGE_VAL` ed `ERANGE` per `TIPO_DOUBLE`) e scrive il valore dereferenziando il puntatore riconvertito.

In `main` dichiara `int contatori[3] = {10, 20, 30};`, `double soglie[2] = {1.5, 9.25};` e `bool attivo = false;`, costruisci `voce_reg_t reg[6]` con nomi `c0`, `c1`, `c2`, `s0`, `s1`, `attivo`, e verifica che `elemento_generico(contatori, i, sizeof(int)) == &contatori[i]` e `elemento_generico(soglie, i, sizeof(double)) == &soglie[i]`. Leggi da `stdin` fino a fine input i comandi `GET <nome>` e `SET <nome> <val>` (stampando `Parametro sconosciuto: <nome>` o `Valore non valido per <nome>` sui casi errati senza terminare). Al termine stampa `Stato finale:`, tutti i `6` parametri e `Verifica indirizzi a byte: OK` esattamente come nell'esempio.

**Concetti da tenere a mente**

- puntatore generico `void *` e `const void *` con conversioni implicite da/verso `T *`
- calcolo portabile di indirizzi in byte tramite `const unsigned char *` (evitando aritmetica su `void *`)
- riconversione sicura del puntatore generico guidata dall'etichetta `tipo_param_t`
- validazione rigorosa dei valori di ingresso con `strtol`, `strtod`, `errno` ed `ERANGE`

**Domande guida**

1. Perché dentro `elemento_generico` devi convertire `base` in `const unsigned char *` prima di scrivere `+ idx * dim_elem` anziché sommare direttamente a `base`?
2. Che cosa accadrebbe se `stampa_parametro` riconvertisse `v->ptr` a `const double *` quando `v->tipo` vale `TIPO_INT`?
3. Perché nella `struct voce_reg` il campo `ptr` ha tipo `void *` mentre nella funzione `elemento_generico` il parametro `base` ha tipo `const void *`?
4. In che modo il confronto `elemento_generico(contatori, i, sizeof(int)) == &contatori[i]` verifica l'aritmetica a byte senza dipendere dagli indirizzi fisici?

**Esempio di esecuzione**

```input
GET c1
SET c1 -42
SET s0 3.75
SET attivo 1
SET attivo 2
GET ignoto
```

```output
c1 (int) = 20
Valore non valido per attivo
Parametro sconosciuto: ignoto
Stato finale:
c0 (int) = 10
c1 (int) = -42
c2 (int) = 30
s0 (double) = 3.75
s1 (double) = 9.25
attivo (bool) = true
Verifica indirizzi a byte: OK
```

## 15.2 Operazioni su byte: `memcpy`, `memmove`, `memcmp` e `memset`

Nel capitolo 9 hai usato le funzioni della famiglia `str*` di `<string.h>` (`strcpy`, `strcmp`, `strchr`) per copiare, confrontare e cercare dentro stringhe di testo. Tutte quelle funzioni condividono una caratteristica vincolante: si fermano appena incontrano il terminatore nullo `'\0'` (il byte `0x00`). Quando lavori con dati generici — array di interi, strutture, pacchetti binari o blocchi gestiti tramite `void *` — il byte `0x00` è un valore del tutto ordinario (per esempio l'intero `0` o i byte superiori di `10`) e non segna affatto la fine dei dati.

Per manipolare blocchi grezzi di memoria di qualunque tipo, lo stesso header `<string.h>` mette a disposizione cinque funzioni della famiglia `mem*`, che accettano puntatori generici `void *` o `const void *` e un conteggio esplicito `size_t n` di byte:

- `void *memcpy(void *restrict s1, const void *restrict s2, size_t n);`
- `void *memmove(void *s1, const void *s2, size_t n);`
- `void *memset(void *s, int c, size_t n);`
- `int memcmp(const void *s1, const void *s2, size_t n);`
- `void *memchr(const void *s, int c, size_t n);` (preserva `const` in C23)

Nessuna di queste funzioni guarda il tipo originale degli oggetti né si arresta su `0x00`: operano sempre su esattamente `n` byte consecutivi.

### `memcpy` contro `memmove`: aree disgiunte e aree sovrapposte

Sia `memcpy(dst, src, n)` sia `memmove(dst, src, n)` copiano `n` byte dall'indirizzo `src` all'indirizzo `dst` e restituiscono `dst`. La differenza decisiva è scritta nella loro firma: `memcpy` dichiara entrambi i parametri con il qualificatore `restrict` (introdotto nel capitolo 14), mentre `memmove` no.

```text
Aree disgiunte (usa memcpy):
  src: [ A ][ B ][ C ]     dst: [   ][   ][   ]

Aree sovrapposte nello stesso buffer (usa memmove):
  buf: [ A ][ B ][ C ][ D ][ E ]
         ^--------^  src (3 byte)
              ^--------^  dst (3 byte)
```

Questa differenza stabilisce una regola netta:
- usa **`memcpy`** solo quando sei certo che gli `n` byte di sorgente e gli `n` byte di destinazione **non si sovrappongono** (per esempio quando copi da un buffer temporaneo a un array di destinazione). Invocare `memcpy` su aree sovrapposte viola il contratto di `restrict` e provoca **comportamento indefinito**: una copia ottimizzata potrebbe sovrascrivere byte non ancora letti.
- usa **`memmove`** ogni volta che sorgente e destinazione appartengono allo stesso array o potrebbero sovrapporsi (per esempio quando sposti a destra gli elementi per fare spazio a un inserimento, oppure a sinistra dopo una rimozione). Lo standard garantisce che `memmove` produca sempre lo stesso risultato di una copia che passa attraverso un buffer temporaneo separato.

### Riempire byte con `memset` e la trappola sugli interi

La funzione `memset(dst, c, n)` converte `c` in `unsigned char` e scrive quel singolo byte in ciascuno degli `n` byte a partire da `dst`. È perfetta per azzerare un buffer di byte o un array di interi (`memset(buf, 0, sizeof(buf))`, perché tutti i bit a `0` rappresentano lo zero per i tipi interi) oppure per riempire un buffer binario con un byte marcatore come `0xFF` o `0xAA`.

Un errore molto frequente è pensare che `memset` imposti ogni *elemento* di un array di `int` al valore `c`. Non è così: `memset` scrive **byte per byte**, non elemento per elemento.

<!-- cod: id=15.2-b tipo=frammento -->
```c
// ATTENZIONE: errore tipico! NON imposta gli elementi a 1.
int valori[4];
memset(valori, 1, sizeof(valori));
// Ogni int (4 byte) diventa 0x01010101 = 16843009, non 1!
```

Se vuoi inizializzare gli elementi di un array di `int` o `double` a un valore diverso da zero (come `1` o `-1`), scrivi un normale ciclo `for`: il compilatore lo ottimizza comunque in modo eccellente e il codice resta chiaro e corretto.

### Confrontare e cercare byte: `memcmp` e `memchr`

La funzione `memcmp(a, b, n)` confronta i primi `n` byte di `a` e `b` interpretandoli come `unsigned char`. Restituisce:
- un valore negativo se il primo byte diverso in `a` è minore del corrispondente byte in `b`;
- `0` se tutti gli `n` byte coincidono (o se `n == 0` con puntatori validi);
- un valore positivo se il primo byte diverso in `a` è maggiore del corrispondente byte in `b`.

Nota che lo standard garantisce solo il **segno** del valore restituito (`< 0`, `0`, `> 0`), non che valga esattamente `-1`, `0` o `1`.

C'è però una cautela fondamentale su `memcmp` che si collega direttamente al capitolo 13: **non usare `memcmp` per verificare l'uguaglianza di due `struct` che possono contenere byte di padding**. I byte di padding dentro una struttura hanno valori indeterminati; due strutture con tutti i campi logicamente uguali possono avere byte di padding diversi, facendo restituire a `memcmp` un valore diverso da `0`. Per confrontare strutture confronta sempre i singoli campi, oppure verifica con `static_assert` (lo vedrai nella sotto-sezione 15.5) che non esista padding solo se stai confrontando formati binari esplicitamente impacchettati.

La funzione `memchr(s, c, n)` cerca la prima occorrenza del byte `(unsigned char)c` nei primi `n` byte di `s` e restituisce il puntatore a quel byte, oppure `nullptr` se il byte non compare. A differenza di `strchr`, continua la ricerca anche dopo eventuali byte `0x00`.

> **C23** — In C23 `memchr` (così come `strchr`, `strrchr`, `strstr` e `strpbrk`) preserva la qualificazione `const`: se le passi un `const void *`, il risultato ha tipo `const void *`; se le passi un `void *` non costante, il risultato ha tipo `void *`. Nei compilatori precedenti (C11/C17) `memchr` restituiva sempre `void *` anche su argomenti `const`, costringendo il programmatore a prestare attenzione a non modificare per errore un oggetto `const`.

### La regola di sicurezza sui puntatori nulli (anche per `n == 0`)

Ricorda una regola severa dello standard C23 che spesso sorprende chi proviene da altri linguaggi: **è vietato passare un puntatore nullo (`nullptr`) a `memcpy`, `memmove`, `memset`, `memcmp` o `memchr` anche quando `n == 0`**. Secondo lo standard C23, il comportamento di queste cinque funzioni è definito solo su puntatori validi che puntano a buffer di almeno `n` byte; passare `nullptr` anche con `n == 0`, superare i limiti di un buffer o invocare `memcpy` su aree sovrapposte provoca **comportamento indefinito**.

In un contenitore dinamico appena inizializzato è del tutto normale avere `dati == nullptr` e `len == 0`. Perciò, prima di chiamare una funzione `mem*` con un conteggio `n` potenzialmente zero, proteggi sempre la chiamata con `if (n > 0)`.

### Esempio guidato

Il programma seguente lavora su un buffer binario `uint8_t trama[10]` che contiene deliberatamente byte `0x00`. Inizializza l'intero buffer con `memset`, copia un'intestazione da un array separato con `memcpy`, sposta una porzione sovrapposta con `memmove`, cerca un byte marcatore dopo uno zero con `memchr` e confronta due sotto-blocchi con `memcmp`.

<!-- cod: id=15.2-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

void stampa_hex(const char *etichetta, const uint8_t *buf, size_t n) {
    printf("%s:", etichetta);
    for (size_t i = 0; i < n; ++i) {
        printf(" %02" PRIx8, buf[i]);
    }
    printf("\n");
}

int main(void) {
    uint8_t trama[10];
    memset(trama, 0x00, sizeof(trama));

    const uint8_t intestazione[4] = {0xAA, 0x00, 0x10, 0xFE};
    memcpy(trama, intestazione, sizeof(intestazione));
    stampa_hex("Dopo memcpy", trama, sizeof(trama));

    // Sposta i primi 4 byte in avanti di 2 posizioni (aree sovrapposte)
    memmove(trama + 2, trama, 4);
    memset(trama, 0xFF, 2);
    stampa_hex("Dopo memmove+memset", trama, sizeof(trama));

    // Cerca 0xFE oltre il byte 0x00 (strchr si fermerebbe prima)
    const void *pos = memchr(trama, 0xFE, sizeof(trama));
    if (pos != nullptr) {
        ptrdiff_t indice = (const uint8_t *)pos - trama;
        printf("Byte 0xFE trovato all'indice %td\n", indice);
    }

    int cmp = memcmp(trama + 2, intestazione, sizeof(intestazione));
    printf("Confronto trama[2..5] vs intestazione: %s\n",
           cmp == 0 ? "uguali" : "diversi");

    return 0;
}
```

```output
Dopo memcpy: aa 00 10 fe 00 00 00 00 00 00
Dopo memmove+memset: ff ff aa 00 10 fe 00 00 00 00
Byte 0xFE trovato all'indice 5
Confronto trama[2..5] vs intestazione: uguali
```

Osserva come ciascuna funzione viene impiegata nel suo ruolo corretto:
- `memset(trama, 0x00, sizeof(trama))` azzera tutti i 10 byte del buffer.
- `memcpy(trama, intestazione, sizeof(intestazione))` è lecita perché `trama` e `intestazione` sono due array distinti e non sovrapposti.
- `memmove(trama + 2, trama, 4)` sposta i byte `[0..3]` nell'intervallo `[2..5]`, che si sovrappone parzialmente all'intervallo di partenza sugli indici `2` e `3`. Usare `memcpy` qui sarebbe stato comportamento indefinito.
- `memchr(trama, 0xFE, sizeof(trama))` attraversa il byte `0x00` all'indice `3` senza fermarsi e individua `0xFE` all'indice `5`. Poiché `trama` qui viene passato come `uint8_t *` ma lo salviamo in `const void *pos`, la conversione a `const uint8_t *` consente di calcolare l'indice con la differenza tra puntatori (`ptrdiff_t`, stampato con `%td`).
- `memcmp(trama + 2, intestazione, sizeof(intestazione))` restituisce `0`, confermando che la sequenza spostata da `memmove` è identica a `intestazione` byte per byte.

> **Approfondimento — Come fa `memmove` a evitare un buffer temporaneo**
> Lo standard descrive `memmove` "come se" copiasse prima in un array temporaneo e poi nella destinazione, ma un'implementazione reale non ha bisogno di allocare memoria aggiuntiva. Quando `dst` e `src` puntano allo stesso blocco di memoria, se `dst < src` la copia procede in avanti dall'indice `0` fino a `n - 1` (i byte che vengono sovrascritti sono già stati letti); se invece `dst > src` la copia procede all'indietro dall'indice `n - 1` fino a `0`. In entrambi i casi nessun byte sorgente viene mai sovrascritto prima di essere copiato, mantenendo prestazioni elevate e memoria ausiliaria costante.

### Esercizio 15.2 — Editor di buffer binario con `memcpy`, `memmove`, `memset`, `memcmp` e `memchr`

**Descrizione**

Scrivi un programma C che gestisca un buffer binario `typedef struct buf_bin { uint8_t dati[64]; size_t len; } buf_bin_t;` (capace di contenere liberamente byte `0x00`) implementando cinque funzioni basate su `memcpy`, `memmove`, `memset`, `memcmp` e `memchr` (`<string.h>`):

1. `bool buf_inserisci(buf_bin_t *b, size_t pos, const uint8_t *src, size_t n)` verifica `pos <= b->len && n <= 64 - b->len`, sposta con `memmove` gli eventuali `b->len - pos` byte di coda se `n > 0 && pos < b->len`, copia `n` byte da `src` con `memcpy` se `n > 0` e aggiorna `b->len`;
2. `bool buf_rimuovi(buf_bin_t *b, size_t pos, size_t n)` verifica `pos <= b->len && n <= b->len - pos`, sposta a sinistra i byte residui con `memmove` se `n > 0 && pos + n < b->len` e riduce `b->len`;
3. `bool buf_riempi(buf_bin_t *b, size_t pos, size_t n, uint8_t val)` verifica i limiti e applica `memset` quando `n > 0`;
4. `ptrdiff_t buf_trova_byte(const buf_bin_t *b, size_t da, uint8_t val)` usa `memchr` (preservando `const` in C23) sull'intervallo `[da, b->len)` restituendo l'indice assoluto oppure `-1`;
5. `int buf_confronta(const buf_bin_t *b, size_t p1, size_t p2, size_t n, bool *ok)` verifica i limiti per entrambe le fette e usa `memcmp` normalizzando il risultato in `-1`, `0` o `1` (`0` se `n == 0`).

In `main` leggi da `stdin` fino a fine input comandi (con valori di byte decimali in `0..255`): `INS <pos> <k> <b0> ... <bk-1>` (`0 <= k <= 16`), `DEL <pos> <n>`, `FILL <pos> <n> <val>`, `FIND <da> <val>`, `CMP <p1> <p2> <n>` e `DUMP` (che stampa `DUMP (0): (vuoto)` se il buffer è vuoto; se un'operazione `INS`, `DEL`, `FILL` o `CMP` viene rifiutata per limiti non validi stampa `<CMD> rifiutato`), stampando gli esiti esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- uso di `memmove` (e non `memcpy`) per spostare porzioni sovrapposte dello stesso buffer
- uso di `memcpy` su aree disgiunte e `memset` per riempire intervalli di byte
- ricerca di un byte anche oltre eventuali byte `0x00` con `memchr` (C23 const-preserving)
- confronto di fette di byte senza segno con `memcmp` e protezione dei casi `n == 0`

**Domande guida**

1. Perché in `buf_inserisci` e `buf_rimuovi` devi usare `memmove` per spostare i byte di coda dentro `b->dati` mentre puoi usare `memcpy` per copiare da `src` a `b->dati + pos`?
2. Perché `strchr` non funzionerebbe al posto di `memchr` sul buffer binario dell'esempio di esecuzione?
3. Che cosa restituisce `memcmp(a, b, n)` in generale e come normalizzi il suo valore in `-1`, `0` o `1`?
4. Perché conviene controllare `if (n > 0)` prima di chiamare `memcpy`, `memmove`, `memset` o `memcmp`?

**Esempio di esecuzione**

```input
INS 0 4 10 0 255 42
INS 2 2 170 187
DUMP
FIND 0 255
FILL 1 2 7
DUMP
CMP 1 2 1
DEL 0 2
DUMP
```

```output
INS ok (len=4)
INS ok (len=6)
DUMP (6): 0a 00 aa bb ff 2a
FIND -> 4
FILL ok
DUMP (6): 0a 07 07 bb ff 2a
CMP -> 0
DEL ok (len=4)
DUMP (4): 07 bb ff 2a
```

## 15.3 Progettare un vettore dinamico generico

Nel capitolo 11 hai costruito un array dinamico di `int` con crescita geometrica tramite `realloc`. Quella struttura funzionava bene, ma era inchiodata a un solo tipo: se ti serviva anche un array dinamico di `double` o di `struct misura`, dovevi riscrivere tutte le funzioni di inizializzazione, inserimento, rimozione e liberazione cambiando soltanto il tipo dell'array.

Ora hai tutti gli ingredienti — `void *`, conversione a `unsigned char *`, `memcpy` e `memmove` — per costruire un **contenitore generico** (*generic container*): una struttura dati che memorizza elementi di tipo qualsiasi, noto al programma solo a tempo di esecuzione.

### Architettura di `vettore_gen`

Per gestire un blocco contiguo sullo heap senza conoscere il tipo `T` a tempo di compilazione, basta un'unica informazione aggiuntiva rispetto a un array dinamico tipizzato: quanti byte occupa ciascun elemento (`dim_elem`, di tipo `size_t`, passato dal chiamante come `sizeof(T)` al momento dell'inizializzazione).

<!-- cod: id=15.3-b tipo=frammento -->
```c
typedef struct vettore_gen {
    void *dati;       // blocco contiguo sullo heap (nullptr se cap == 0)
    size_t dim_elem;  // dimensione in byte di un singolo elemento (sizeof(T))
    size_t len;       // numero di elementi attualmente memorizzati
    size_t cap;       // numero di elementi allocati nel blocco dati
} vettore_gen_t;
```

Osserva come lo stesso identico tipo `vettore_gen_t` gestisca in memoria un vettore di `int` (4 byte per elemento) e un vettore di `struct coppia_xy` (16 byte per elemento):

```text
Vettore di int (dim_elem = 4, len = 3, cap = 4):
  dati -> [  10  ][  20  ][  30  ][ libero ]
          +0      +4      +8      +12      (byte)

Vettore di struct coppia_xy (dim_elem = 16, len = 2, cap = 4):
  dati -> [ x=1.0, y=2.0 ][ x=3.5, y=4.0 ][ libero ][ libero ]
          +0              +16             +32       +48      (byte)
```

Il contenitore non sa se i byte dentro `dati` rappresentino interi, numeri reali o strutture: sa soltanto che ogni slot è largo `dim_elem` byte e che lo slot di indice `idx` inizia esattamente a `idx * dim_elem` byte dall'inizio del blocco.

### Indirizzamento, copia e scorrimento degli elementi

Poiché `v->dati` ha tipo `void *`, non possiamo scrivere `v->dati[idx]` né `v->dati + idx`. Ogni operazione del contenitore segue sempre questo schema:

1. **Calcolo dell'indirizzo**: converte `v->dati` in `unsigned char *base = v->dati;` (oppure `const unsigned char *base = v->dati;` in lettura) e calcola l'indirizzo dell'elemento `idx` come `base + idx * v->dim_elem`.
2. **Inserimento e copia**: riceve il nuovo elemento tramite `const void *elem` e ne copia i `v->dim_elem` byte nello slot di destinazione con `memcpy(base + pos * v->dim_elem, elem, v->dim_elem)`.
3. **Inserimento o rimozione in posizione intermedia**: sposta gli elementi di coda dentro lo stesso blocco usando `memmove` (perché l'area di origine e l'area di destinazione si sovrappongono). Per esempio, per rimuovere l'elemento in posizione `pos < v->len`, se `pos + 1 < v->len` sposta `(v->len - pos - 1) * v->dim_elem` byte da `pos + 1` a `pos` e poi decrementa `v->len`.

Nota che quando `v->len == 0` il puntatore `v->dati` può essere `nullptr`: proteggendo sempre `memmove` con condizioni come `if (pos < v->len)` o `if (pos + 1 < v->len)` rispetti anche la regola C23 vista nella sotto-sezione 15.2.

### Crescita geometrica e prevenzione dell'overflow

Quando `v->len == v->cap` occorre espandere il blocco sullo heap, tipicamente raddoppiando la capacità (`0 -> 2 -> 4 -> 8 -> ...`). Prima di calcolare `nuova_cap * v->dim_elem` e passarlo a `realloc`, devi applicare due difese essenziali:

1. **Controllo di overflow sul prodotto**: verifica `if (nuova_cap > SIZE_MAX / v->dim_elem) { return false; }` (dopo esserti assicurato che `v->dim_elem > 0`). Senza questo controllo, una capacità enorme potrebbe andare in overflow e far allocare a `realloc` un blocco piccolissimo, aprendo un grave buffer overflow.
2. **Puntatore temporaneo per `realloc`**: assegna il risultato a `void *tmp = realloc(v->dati, nuova_cap * v->dim_elem);` e aggiorna `v->dati = tmp;` e `v->cap = nuova_cap;` solo se `tmp != nullptr`, preservando così il blocco precedente in caso di esaurimento della memoria.

### Perché l'allineamento è garantito automaticamente

A questo punto potresti porti una domanda legittima: nel capitolo 13 hai imparato che ogni tipo `T` ha un requisito di allineamento `alignof(T)` (per esempio 8 byte per `double` o per una `struct` che contiene `double`). Se il vettore generico calcola gli indirizzi con `unsigned char *` senza conoscere `T`, come fa a garantire che ogni elemento `base + idx * dim_elem` sia correttamente allineato?

La risposta combina due garanzie dello standard C23:
1. `malloc`, `calloc` e `realloc` restituiscono sempre un indirizzo allineato per **qualsiasi tipo con allineamento fondamentale** (quindi divisibile per `alignof(T)`).
2. Per qualunque tipo `T` (scalare o `struct`), lo standard garantisce che `sizeof(T)` sia sempre un **multiplo intero** di `alignof(T)` (proprio a questo serve il padding finale delle strutture visto nel capitolo 13).

Poiché `base` è multiplo di `alignof(T)` e `dim_elem == sizeof(T)` è multiplo di `alignof(T)`, anche `base + idx * dim_elem` è necessariamente multiplo di `alignof(T)` per ogni `idx`. L'allineamento è dunque garantito automaticamente per qualsiasi tipo omogeneo `T`.

### Limiti della genericità basata solo su `void *`

Un contenitore basato solo su `void *` e `dim_elem` è compatto e veloce, ma ha due limiti che devi conoscere bene:
- **Responsabilità del chiamante sui tipi**: il compilatore non può verificare che tu stia passando un `double *` a un vettore inizializzato con `sizeof(double)`. Passare un puntatore a un tipo o a una dimensione diversa da `dim_elem` provoca **comportamento indefinito** (lettura oltre i limiti dell'oggetto passato o errata interpretazione dei bit).
- **Copia superficiale (*shallow copy*)**: `memcpy` copia i byte dell'elemento così come sono. Se l'elemento è una `struct` che contiene al suo interno un puntatore a memoria allocata sullo heap (per esempio `char *nome`), `vg_free` libererà solo l'array `v->dati`, non le stringhe puntate dai singoli elementi; inoltre il contenitore non sa ancora confrontare due elementi per cercarli o ordinarli. Nei capitoli 16 e 17 supereremo questi limiti affiancando ai contenitori generici i **puntatori a funzione** per confronto e distruzione personalizzati.

> **Se vieni da Python** — In Python una lista può contenere oggetti di tipi diversi senza sforzo perché ogni elemento è un riferimento a un oggetto con informazioni di tipo a tempo di esecuzione; in C un contenitore generico manipola byte grezzi tramite `void *` e `dim_elem`, ottenendo compattezza e velocità al prezzo di richiedere rigore sui tipi.

### Esempio guidato

Il programma seguente implementa un vettore dinamico generico completo (`vg_init`, `vg_push`, `vg_get`, `vg_remove`, `vg_free`) e lo utilizza contemporaneamente per due tipi diversi: `double` e una struttura `coppia_xy_t`.

<!-- cod: id=15.3-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct vettore_gen {
    void *dati;
    size_t dim_elem;
    size_t len;
    size_t cap;
} vettore_gen_t;

typedef struct coppia_xy {
    int id;
    double x;
    double y;
} coppia_xy_t;

void vg_init(vettore_gen_t *v, size_t dim_elem) {
    *v = (vettore_gen_t){.dati = nullptr, .dim_elem = dim_elem, .len = 0, .cap = 0};
}

void vg_free(vettore_gen_t *v) {
    free(v->dati);
    *v = (vettore_gen_t){.dati = nullptr, .dim_elem = v->dim_elem, .len = 0, .cap = 0};
}

bool vg_push(vettore_gen_t *v, const void *elem) {
    if (v->dim_elem == 0 || elem == nullptr) { return false; }
    if (v->len == v->cap) {
        size_t nuova_cap = (v->cap == 0) ? 2 : (v->cap * 2);
        if (nuova_cap < v->cap || nuova_cap > SIZE_MAX / v->dim_elem) { return false; }
        void *tmp = realloc(v->dati, nuova_cap * v->dim_elem);
        if (tmp == nullptr) { return false; }
        v->dati = tmp;
        v->cap = nuova_cap;
    }
    unsigned char *base = v->dati;
    memcpy(base + v->len * v->dim_elem, elem, v->dim_elem);
    ++v->len;
    return true;
}

const void *vg_get(const vettore_gen_t *v, size_t idx) {
    if (idx >= v->len) { return nullptr; }
    return (const unsigned char *)v->dati + idx * v->dim_elem;
}

bool vg_remove(vettore_gen_t *v, size_t idx) {
    if (idx >= v->len) { return false; }
    unsigned char *base = v->dati;
    if (idx + 1 < v->len) {
        memmove(base + idx * v->dim_elem, base + (idx + 1) * v->dim_elem,
                (v->len - idx - 1) * v->dim_elem);
    }
    --v->len;
    return true;
}

int main(void) {
    vettore_gen_t reali, coppie;
    vg_init(&reali, sizeof(double));
    vg_init(&coppie, sizeof(coppia_xy_t));
    double campioni[3] = {1.5, 4.25, 9.0};
    for (size_t i = 0; i < 3; ++i) { vg_push(&reali, &campioni[i]); }
    vg_remove(&reali, 1);
    coppia_xy_t p1 = {1, 2.0, 3.5}, p2 = {2, -1.0, 0.5};
    vg_push(&coppie, &p1);
    vg_push(&coppie, &p2);
    printf("Reali (len=%zu, cap=%zu):", reali.len, reali.cap);
    for (size_t i = 0; i < reali.len; ++i) {
        const double *val = vg_get(&reali, i);
        printf(" %.2f", *val);
    }
    printf("\nCoppie (len=%zu, cap=%zu):", coppie.len, coppie.cap);
    for (size_t i = 0; i < coppie.len; ++i) {
        const coppia_xy_t *c = vg_get(&coppie, i);
        printf(" #%d(%.1f,%.1f)", c->id, c->x, c->y);
    }
    printf("\n");
    vg_free(&reali);
    vg_free(&coppie);
    return 0;
}
```

```output
Reali (len=2, cap=4): 1.50 9.00
Coppie (len=2, cap=2): #1(2.0,3.5) #2(-1.0,0.5)
```

Nota come lo stesso codice gestisce entrambi i tipi senza alcuna duplicazione:
- `vg_push` controlla sia il possibile overflow del raddoppio (`nuova_cap < v->cap`) sia l'overflow della moltiplicazione (`nuova_cap > SIZE_MAX / v->dim_elem`) prima di invocare `realloc`.
- In `reali`, inserire 3 elementi fa crescere la capacità da `0` a `2` e poi da `2` a `4`; la chiamata `vg_remove(&reali, 1)` sposta `9.0` sull'indice `1` tramite `memmove`, riducendo `len` a `2` mentre `cap` resta `4`.
- In lettura, `vg_get` restituisce `const void *`, che viene assegnato implicitamente a `const double *` per `reali` e a `const coppia_xy_t *` per `coppie`.
- Al termine `vg_free` libera entrambi i blocchi sullo heap e azzera i campi, lasciando i due vettori in uno stato pulito e privo di puntatori pendenti.

> **Approfondimento — Valori in blocco contiguo contro array di puntatori `void **`**
> Esistono due modelli principali per realizzare un contenitore generico in C. Il modello che hai appena costruito memorizza i valori direttamente uno accanto all'altro in un unico blocco `void *dati` con passo `dim_elem`: richiede una sola allocazione di memoria (e una sola `free`), garantisce migliore località di cache ed è ideale per tipi piccoli e omogenei. Il modello alternativo memorizza invece un array di puntatori `void **` a oggetti allocati separatamente sullo heap: introduce un'indirezione in più, ma permette di conservare oggetti grandi senza copiarli durante `realloc`, oppure oggetti di dimensioni diverse (lo ritroveremo nelle tabelle hash nel capitolo 18).

### Esercizio 15.3 — Vettore dinamico generico `vettore_gen_t` riutilizzato per `int64_t` e `struct misura_t`

**Descrizione**

Scrivi un programma C che implementi un contenitore generico `typedef struct vettore_gen { void *dati; size_t dim_elem; size_t len; size_t cap; } vettore_gen_t;` completamente indipendente dal tipo degli elementi. Implementa sette funzioni:
- `void vg_init(vettore_gen_t *v, size_t dim_elem)`
- `void vg_free(vettore_gen_t *v)`
- `bool vg_riserva(vettore_gen_t *v, size_t nuova_cap)` (controlla `nuova_cap <= SIZE_MAX / v->dim_elem` e usa `realloc` con puntatore temporaneo)
- `bool vg_inserisci(vettore_gen_t *v, size_t pos, const void *elem)` (`pos <= v->len`, raddoppia la capacità `0 -> 2 -> 4 -> ...` se necessario, sposta con `memmove` e copia con `memcpy`)
- `bool vg_rimuovi(vettore_gen_t *v, size_t pos, void *out)` (`pos < v->len`, copia in `out` se non nullo, sposta con `memmove` e decrementa `len`)
- `const void *vg_leggi(const vettore_gen_t *v, size_t pos)` (`nullptr` se fuori limiti)
- `bool vg_scambia(vettore_gen_t *v, size_t i, size_t j)` (scambia due elementi usando un buffer temporaneo dinamico di `v->dim_elem` byte e `memcpy`)

In `main` crea due `vettore_gen_t`: `v_num` per `int64_t` e `v_mis` per `typedef struct misura { int id; double valore; } misura_t;`. Leggi da `stdin` fino a fine input i comandi `NUM_INS <pos> <val64>`, `NUM_DEL <pos>` (stampa `DEL_NUM: <val>`), `NUM_SWAP <i> <j>`, `MIS_INS <pos> <id> <valore>`, `MIS_DEL <pos>` (stampa `DEL_MIS: #<id>=<valore:.2f>`) e `MIS_SWAP <i> <j>`; se un'operazione fallisce per posizione/indice non valido stampa `ERR` e prosegui. Al termine stampa contenuto, lunghezza e capacità di entrambi i vettori leggendo con `vg_leggi` e libera tutto con `vg_free`.

**Concetti da tenere a mente**

- progettazione di un contenitore generico con `void *dati`, `dim_elem`, `len` e `cap`
- calcolo dell'indirizzo dell'elemento `i`-esimo tramite `(unsigned char *)v->dati + i * v->dim_elem`
- inserimento, rimozione e scambio generici con `memcpy` e `memmove`
- controllo di overflow su `nuova_cap * dim_elem` con `SIZE_MAX / dim_elem`
- riutilizzo dello stesso codice su tipi scalari (`int64_t`) e strutture (`misura_t`)

**Domande guida**

1. Perché `vg_init` ha bisogno di ricevere `dim_elem = sizeof(tipo)` dal chiamante?
2. Come fa `vg_scambia` a scambiare due elementi di dimensione arbitraria senza conoscere a tempo di compilazione se siano `int64_t` o `misura_t`?
3. Quale condizione impedisce l'overflow del prodotto `nuova_cap * v->dim_elem` prima di chiamare `realloc`?
4. Perché dopo aver chiamato `vg_leggi(&v_mis, i)` devi assegnare il puntatore `const void *` restituito a `const misura_t *` prima di accedere a `->id` e `->valore`?

**Esempio di esecuzione**

```input
NUM_INS 0 100
NUM_INS 1 300
NUM_INS 1 200
NUM_SWAP 0 2
NUM_DEL 1
MIS_INS 0 10 12.5
MIS_INS 1 20 8.25
MIS_INS 0 30 4.0
MIS_SWAP 0 2
MIS_DEL 1
```

```output
DEL_NUM: 200
DEL_MIS: #10=12.50
NUM (len=2, cap=4): 300 100
MIS (len=2, cap=4): #20=8.25 #30=4.00
```

## 15.4 Selezione sul tipo con `_Generic`

Nelle prime tre sotto-sezioni hai affrontato la programmazione generica *a tempo di esecuzione*, usando `void *` e `dim_elem` per manipolare dati il cui tipo concreto è nascosto. Spesso, però, il compilatore **conosce già** il tipo esatto di un'espressione `x` (sa se `x` è `int32_t`, `double`, `char *` o `const char *`), e vorresti semplicemente scegliere automaticamente l'etichetta, il formato o la funzione specializzata più adatta per quel tipo, senza dover scrivere manualmente `switch` su un `enum` né pagare alcun costo durante l'esecuzione.

Per questo scopo il linguaggio C offre la selezione generica **`_Generic`**, un'espressione che si comporta come uno `switch` sui *tipi* interamente risolto a tempo di compilazione.

### Sintassi e semantica di `_Generic`

La forma generale è:

<!-- cod: id=15.4-b tipo=frammento -->
```c
_Generic(expr,
    tipo1: risultato1,
    tipo2: risultato2,
    default: risultato_predefinito
)
```

Il compilatore esamina il tipo di `expr` (chiamata *espressione di controllo*), cerca l'associazione il cui tipo è compatibile con quello di `expr` e sostituisce l'intera espressione `_Generic` con il risultato corrispondente. A tempo di esecuzione non rimane alcun confronto né alcuna ramificazione: il codice macchina contiene soltanto il ramo selezionato.

Le regole precise stabilite dallo standard C23 sono:
- **Nessuna valutazione dell'espressione di controllo**: `expr` non viene mai eseguita a tempo di esecuzione (proprio come accade per `sizeof`). Se scrivi `_Generic(++cont, int: 1, default: 0)`, il compilatore guarda solo il tipo di `++cont` (`int`) e **non** incrementa `cont`.
- **Conversione *lvalue* su `expr`**: prima del confronto, `expr` subisce le stesse trasformazioni che avvengono quando si legge un valore: i qualificatori di primo livello (come `const` su una variabile scalare `const int`) vengono rimossi e gli array decadono al puntatore al primo elemento (`char[16]` diventa `char *`).
- **Vincoli sui tipi delle associazioni**: tutti i tipi elencati nei rami devono essere tipi di oggetto completi e **mutuamente incompatibili** (non puoi inserire due rami entrambi per `int`, né per `int` e un `typedef` sinonimo di `int`). Inoltre può comparire al più un ramo `default:`.

### Puntatori mutabili, puntatori `const` e `nullptr_t`

Attenzione a un dettaglio molto importante della conversione *lvalue*: la rimozione di `const` riguarda solo il qualificatore **di primo livello**, non ciò a cui punta un puntatore.
- Se `const int x = 5;`, il tipo controllato da `_Generic(x, ...)` è `int` (il `const` esterno viene rimosso).
- Se `const char *s = "ciao";`, il qualificatore `const` riguarda i caratteri puntati, non la variabile puntatore `s`: perciò `_Generic` distingue nettamente **`char *`** (puntatore a caratteri modificabili) da **`const char *`** (puntatore a caratteri di sola lettura).

In C23 questa distinzione si arricchisce con il tipo di `nullptr`: **`nullptr_t`**, definito in `<stddef.h>`.

> **C23** — In C23 la costante `nullptr` ha un tipo proprio, `nullptr_t` (definito in `<stddef.h>`), distinto da qualsiasi intero e da qualsiasi puntatore `void *`. Questo consente di riconoscerla con un ramo dedicato `nullptr_t:` dentro `_Generic`. Nei compilatori precedenti (C11/C17) esisteva solo la macro `NULL`, che poteva espandersi in `0` (`int`) o `(void *)0` (`void *`) a seconda dell'implementazione, rendendo non portabile l'uso di `NULL` dentro `_Generic`.

### Selezionare funzioni specializzate e controllo di esaustività

Uno degli impieghi più efficaci di `_Generic` consiste nel selezionare una funzione specializzata per il tipo di un argomento e invocarla subito dopo:

<!-- cod: id=15.4-c tipo=frammento -->
```c
double valore = _Generic((x),
    int32_t: elabora_i32,
    double: elabora_dbl
)(x);
```

Osserva dove si trova `(x)`: **fuori** dalle parentesi di `_Generic`. L'espressione `_Generic` restituisce la funzione scelta (`elabora_i32` oppure `elabora_dbl`), e poi la chiamata `(x)` viene applicata soltanto alla funzione selezionata.

Nota anche l'assenza del ramo `default:` in questo frammento. Secondo lo standard C23, se nessuna associazione corrisponde al tipo di `expr` e manca `default:`, il programma viene **rifiutato con errore di compilazione**. Omettere `default:` è quindi una tecnica eccellente per imporre il *controllo di esaustività*: se qualcuno passa un tipo non previsto (per esempio `float` o `int64_t`), il compilatore blocca subito la compilazione anziché ricadere silenziosamente su un comportamento generico.

In questo capitolo usiamo `_Generic` direttamente nelle espressioni del codice; nei capitoli 19, 21 e 24 vedremo come combinarlo con le macro con argomenti del preprocessore per costruire interfacce generiche ancora più compatte.

> **Se vieni da Python** — In Python il controllo del tipo (`isinstance`) avviene a tempo di esecuzione; in C `_Generic`, `typeof` e `static_assert` risolvono completamente selezione e verifiche a tempo di compilazione senza alcun costo a tempo di esecuzione.

### Esempio guidato

Il programma seguente applica `_Generic` a variabili di tipo `int`, `double`, `char *`, `const char *` e `nullptr_t` per selezionare sia una stringa descrittiva del tipo sia la funzione di elaborazione corrispondente, e dimostra con un contatore che l'espressione di controllo non viene mai valutata.

<!-- cod: id=15.4-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <string.h>

void stampa_int(int x) { printf("valore intero = %d\n", x); }
void stampa_dbl(double x) { printf("valore reale = %.2f\n", x); }
void stampa_str_mut(char *s) { printf("stringa mutabile = \"%s\" (len=%zu)\n", s, strlen(s)); }
void stampa_str_const(const char *s) { printf("stringa const = \"%s\" (len=%zu)\n", s, strlen(s)); }
void stampa_null(nullptr_t p) { (void)p; printf("valore nullo (nullptr)\n"); }

int tocca_contatore(int *cont, int x) {
    ++(*cont);
    return x;
}

int main(void) {
    int n = 42;
    double r = 3.25;
    char buf[] = "testo";
    char *p_mut = buf;
    const char *p_const = "fisso";
    nullptr_t np = nullptr;

    printf("n -> %s: ", _Generic(n, int: "int", double: "double", default: "altro"));
    _Generic(n, int: stampa_int, double: stampa_dbl)(n);

    printf("r -> %s: ", _Generic(r, int: "int", double: "double", default: "altro"));
    _Generic(r, int: stampa_int, double: stampa_dbl)(r);

    printf("p_mut -> %s: ",
           _Generic(p_mut, char *: "char *", const char *: "const char *",
                    nullptr_t: "nullptr_t", default: "altro"));
    _Generic(p_mut, char *: stampa_str_mut, const char *: stampa_str_const,
             nullptr_t: stampa_null)(p_mut);

    printf("p_const -> %s: ",
           _Generic(p_const, char *: "char *", const char *: "const char *",
                    nullptr_t: "nullptr_t", default: "altro"));
    _Generic(p_const, char *: stampa_str_mut, const char *: stampa_str_const,
             nullptr_t: stampa_null)(p_const);

    printf("np -> %s: ",
           _Generic(np, char *: "char *", const char *: "const char *",
                    nullptr_t: "nullptr_t", default: "altro"));
    _Generic(np, char *: stampa_str_mut, const char *: stampa_str_const,
             nullptr_t: stampa_null)(np);

    int chiamate = 0;
    const char *t = _Generic(tocca_contatore(&chiamate, n),
                             int: "int", default: "altro");
    printf("Dopo _Generic su tocca_contatore: tipo=%s, chiamate=%d\n", t, chiamate);

    return 0;
}
```

```output
n -> int: valore intero = 42
r -> double: valore reale = 3.25
p_mut -> char *: stringa mutabile = "testo" (len=5)
p_const -> const char *: stringa const = "fisso" (len=5)
np -> nullptr_t: valore nullo (nullptr)
Dopo _Generic su tocca_contatore: tipo=int, chiamate=0
```

Osserva i risultati dell'esecuzione:
- Le variabili `p_mut` (`char *`), `p_const` (`const char *`) e `np` (`nullptr_t`) attivano tre rami distinti, selezionando sia l'etichetta sia la funzione specializzata (`stampa_str_mut`, `stampa_str_const`, `stampa_null`).
- Nelle selezioni delle funzioni manca `default:`: se per distrazione passassimo un `float` al primo `_Generic`, il compilatore rifiuterebbe il codice segnalando l'assenza di un'associazione compatibile.
- Nell'ultima parte del programma, `tocca_contatore(&chiamate, n)` compare come espressione di controllo di `_Generic`: il compilatore determina che il suo tipo di ritorno è `int` senza mai generare una chiamata alla funzione, e infatti `chiamate` rimane `0`.

> **Approfondimento — Perché tutti i rami di `_Generic` devono essere ben tipizzati**
> Anche se a tempo di compilazione `_Generic` seleziona un solo ramo, il compilatore controlla la correttezza sintattica e di tipo di **tutti** i rami presenti. Se scrivessi `_Generic(x, int: stampa_int(x), char *: stampa_str_mut(x))` quando `x` è un `int`, il ramo `char *: stampa_str_mut(x)` fallirebbe la compilazione perché tenta di passare un `int` a una funzione che attende `char *`. Mettendo dentro `_Generic` soltanto i *nomi delle funzioni* e spostando `(x)` all'esterno (`_Generic(x, int: stampa_int, char *: stampa_str_mut)(x)`), ogni ramo è semplicemente il nome di una funzione valida e la chiamata `(x)` viene verificata solo sul ramo scelto.

### Esercizio 15.4 — Dispatch a tempo di compilazione e riconoscimento dei tipi con `_Generic` e `nullptr_t`

**Descrizione**

Scrivi un programma C che dimostri la selezione sul tipo con `_Generic` (senza usare `#define`) e il tipo C23 `nullptr_t` (`<stddef.h>`). Definisci cinque funzioni di calcolo della norma:
- `double norma_i32(int32_t x)` (`fabs((double)x)`),
- `double norma_u32(uint32_t x)` (`(double)x`),
- `double norma_dbl(double x)` (`fabs(x)`),
- `double norma_str(const char *s)` (`s == nullptr ? 0.0 : (double)strlen(s)`),
- `double norma_null(nullptr_t p)` (restituisce sempre `0.0`),

più una funzione di tracciamento `int32_t incrementa_cont(int *c, int32_t x)` che incrementa `*c` e restituisce `x` (per verificare che l'espressione di controllo dentro `_Generic` non viene mai valutata!). In `main` leggi da `stdin` una riga con `a b c testo flag_null` (`int32_t a`, `uint32_t b`, `double c`, una parola `testo` fino a `31` caratteri senza spazi e `flag_null` in `{0, 1}`). Imposta `char *p_mut = (flag_null == 1) ? nullptr : testo;`, `const char *p_const = "costante";` e `nullptr_t np = nullptr;`. Usando espressioni `_Generic` (con rami `int32_t`, `uint32_t`, `double`, `char *`, `const char *`, `nullptr_t` e `default`), seleziona a tempo di compilazione sia il nome del tipo sia la funzione di norma per ciascuno dei sei oggetti (`a`, `b`, `c`, `p_mut`, `p_const`, `np`), verifica con `_Generic(incrementa_cont(&chiamate, a), ...)` che `chiamate` resti `0`, e stampa ogni riga e la somma delle norme esattamente come nell'esempio.

**Concetti da tenere a mente**

- selezione statica del tipo con `_Generic(expr, tipo: valore, ..., default: valore)`
- dispatch di funzioni selezionando il nome della funzione dentro `_Generic` e passando l'argomento fuori
- distinzione in `_Generic` tra `char *`, `const char *` e il tipo C23 `nullptr_t` (`<stddef.h>`)
- mancata valutazione dell'espressione di controllo di `_Generic` a tempo di esecuzione

**Domande guida**

1. Perché conviene scrivere `_Generic(x, int32_t: norma_i32, double: norma_dbl)(x)` invece di scrivere la chiamata dentro ogni ramo di `_Generic`?
2. Come mai `_Generic` distingue `char *` da `const char *` pur rimuovendo un eventuale `const` esterno da `const int32_t`?
3. Perché chiamare `incrementa_cont(&chiamate, a)` come espressione di controllo di `_Generic` lascia `chiamate` uguale a `0`?
4. Quale vantaggio offre avere `nullptr_t` come tipo distinto in `_Generic` rispetto alla vecchia macro `NULL`?

**Esempio di esecuzione**

```input
-15 40 -2.5 ciao 0
```

```output
a: tipo=int32_t norma=15.00
b: tipo=uint32_t norma=40.00
c: tipo=double norma=2.50
p_mut: tipo=char * norma=4.00
p_const: tipo=const char * norma=8.00
np: tipo=nullptr_t norma=0.00
Effetti collaterali in _Generic: chiamate=0 (tipo=int32_t)
Somma norme: 69.50
```

## 15.5 `typeof`, `auto` e `static_assert`

Quando scrivi codice generico o strutture binarie con vincoli precisi di dimensione e allineamento, emergono due bisogni ricorrenti: dichiarare variabili temporanee che abbiano esattamente il tipo di un'altra espressione (senza ripeterlo a mano) e trasformare le assunzioni sul programma in controlli verificati dal compilatore prima ancora di produrre l'eseguibile. Lo standard C23 risponde a entrambi i bisogni con quattro strumenti nativi: `typeof`, `typeof_unqual`, `auto` e `static_assert`.

### Ricavare un tipo con `typeof` e `typeof_unqual`

L'operatore C23 **`typeof(expr)`** (applicabile sia a un'espressione sia a un nome di tipo) restituisce il tipo esatto di `expr` a tempo di compilazione, **senza valutare `expr`** a tempo di esecuzione. Puoi usarlo ovunque serva uno specificatore di tipo, per esempio per dichiarare una variabile di appoggio nello scambio di due elementi puntati da `a` e `b`:

<!-- cod: id=15.5-b tipo=frammento -->
```c
typeof(*a) tmp = *a;
*a = *b;
*b = tmp;
```

Se cambi il tipo di `a` e `b`, la dichiarazione di `tmp` si adatta automaticamente.

C'è però un caso in cui `typeof` conserva *troppo*: `typeof(expr)` mantiene tutti i qualificatori di primo livello dell'espressione, in particolare `const`. Se hai un parametro `const uint64_t limite` e scrivi `typeof(limite) copia = limite;`, anche `copia` risulta `const uint64_t` e il compilatore ti impedirà di modificarla (`++copia` genera un errore di compilazione).

Per risolvere questo problema, C23 affianca a `typeof` l'operatore **`typeof_unqual(expr)`**, che rimuove i qualificatori di primo livello (come `const`) e produce un tipo modificabile:

<!-- cod: id=15.5-c tipo=frammento -->
```c
const uint64_t limite = 100;
typeof_unqual(limite) copia = limite;  // tipo: uint64_t (modificabile)
++copia;                               // valido!
```

> **C23** — Gli operatori `typeof` e `typeof_unqual` sono stati standardizzati in C23. Nei compilatori più vecchi (C11/C17) non fanno parte dello standard (esisteva solo l'estensione non portabile `__typeof__` di GCC/Clang, priva di `typeof_unqual`): con compilatori anteriori a C23 occorre scrivere esplicitamente il nome del tipo desiderato.

### Inferenza statica del tipo con `auto`

In C23 la parola chiave **`auto`** permette al compilatore di dedurre automaticamente il tipo di una singola variabile dal suo inizializzatore, interamente a tempo di compilazione:

<!-- cod: id=15.5-d tipo=frammento -->
```c
auto somma = (uint64_t)0;       // tipo dedotto: uint64_t
auto media = somma / 4.0;       // tipo dedotto: double
```

Le regole di `auto` in C23 sono rigorose:
- ogni dichiarazione con `auto` deve avere un **inizializzatore** (scrivere `auto x;` senza valore iniziale è un errore di compilazione);
- in C23 `auto` dichiara una **singola variabile** (non elenchi di più variabili con tipi misti);
- il tipo dedotto viene fissato definitivamente a tempo di compilazione (rimuovendo i qualificatori di primo livello dell'inizializzatore e applicando il decadimento degli array).

Usa `auto` con giudizio: è utile quando il tipo è già evidente dall'inizializzatore (per esempio `auto somma = (uint64_t)0;` o il valore di ritorno di una funzione dal nome chiaro) o per evitare di ripetere tipi lunghi. Quando invece l'inizializzatore è un letterale semplice come `0` (che ha tipo `int`, non `size_t` né `uint64_t`), scrivere il tipo esplicito o un cast chiaro evita sorprese silenziose sui tipi interi.

> **C23** — Prima del C23, `auto` era una vecchia parola chiave ereditata dalle origini del C che indicava la durata di vita automatica delle variabili locali (già predefinita e quasi mai scritta). C23 ha ridefinito `auto` come deduzione di tipo: su compilatori C11/C17 questa sintassi non è supportata e devi sempre scrivere il tipo esplicito.

> **Se vieni da Python** — In Python una variabile non ha tipo fisso e può cambiare tipo a ogni assegnamento; in C23 la parola chiave `auto` deduce un tipo statico definitivo dall'inizializzatore al momento della compilazione.

### Verifiche a tempo di compilazione: `static_assert`

Quando progetti strutture binarie o tabelle indicizzate da un `enum`, molte ipotesi devono essere vere *prima* ancora di eseguire il programma: per esempio che un byte sia di 8 bit (`CHAR_BIT == 8`), che una `struct` non abbia padding imprevisto (`sizeof(record_t) == 16`), che l'offset di un campo sia quello atteso (`offsetof(...)`), oppure che un array di etichette contenga esattamente tante voci quanti sono i valori dell'`enum`.

Per trasformare queste ipotesi in controlli automatici esiste l'**asserzione statica** (*static assertion*): un controllo verificato dal compilatore con `static_assert` che interrompe la compilazione se una condizione costante è falsa.

In C23 `static_assert` è una parola chiave nativa (non richiede di includere alcun header) e accetta due forme:
- **due argomenti**: `static_assert(condizione, "messaggio");`
- **un solo argomento** (novità C23): `static_assert(condizione);`

La condizione deve essere un'**espressione costante intera** valutabile a tempo di compilazione (non una variabile ordinaria letta da input). Se la condizione è vera, `static_assert` non produce alcun codice macchina e ha costo zero a tempo di esecuzione; se è falsa, la compilazione si arresta subito con un errore di compilazione.

> **C23** — In C11 e C17 la parola chiave nativa era `_Static_assert` e richiedeva obbligatoriamente due argomenti (condizione e messaggio); per scrivere `static_assert` occorreva includere l'header delle asserzioni. In C23 `static_assert` è diventata una parola chiave nativa del linguaggio e il messaggio diagnostico è diventato opzionale.

### Asserzione statica contro controlli a tempo di esecuzione

Distingui bene i due livelli di verifica:
- **`static_assert`** controlla proprietà note **a tempo di compilazione** (dimensioni `sizeof`, allineamenti `alignof`, spiazzamenti `offsetof`, limiti come `CHAR_BIT`, coerenza tra `enum` e array statici). Se fallisce, l'eseguibile non viene nemmeno creato.
- I **controlli a tempo di esecuzione** (`if`, validazione dell'input, controllo di `nullptr`) verificano valori che dipendono dai dati forniti mentre il programma gira (nel capitolo 21 introdurremo anche le asserzioni a tempo di esecuzione con `assert`).

### Esempio guidato

Il programma C23 seguente definisce un'enumerazione di stati, un array parallelo di nomi e una struttura compatta `voce_log_t`. Verifica il layout e la sincronizzazione con `static_assert` (sia a due argomenti sia a un argomento), usa `typeof` per scambiare due strutture, `typeof_unqual` per creare una copia modificabile di un parametro `const` e `auto` per le variabili locali verificandone il tipo dedotto con `_Generic`.

<!-- cod: id=15.5-a tipo=programma -->
```c
#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef enum livello : uint8_t {
    LIV_INFO = 0,
    LIV_AVVISO = 1,
    LIV_ERRORE = 2,
    LIV_CONTEGGIO = 3
} livello_t;

static const char *const NOMI_LIVELLO[] = {"INFO", "AVVISO", "ERRORE"};

typedef struct voce_log {
    uint64_t istante;
    uint32_t codice;
    uint16_t durata_ms;
    uint8_t livello;
    uint8_t priorita;
} voce_log_t;

static_assert(CHAR_BIT == 8, "Sono richiesti byte da 8 bit");
static_assert(sizeof(voce_log_t) == 16, "voce_log_t deve occupare 16 byte");
static_assert(alignof(voce_log_t) >= alignof(uint64_t));
static_assert(offsetof(voce_log_t, codice) == 8 && offsetof(voce_log_t, priorita) == 15);
static_assert(sizeof(NOMI_LIVELLO) / sizeof(NOMI_LIVELLO[0]) == LIV_CONTEGGIO,
              "NOMI_LIVELLO non sincronizzato con livello_t");

void scambia_voci(voce_log_t *a, voce_log_t *b) {
    typeof(*a) tmp = *a;
    *a = *b;
    *b = tmp;
}

uint32_t calcola_punteggio(const voce_log_t *v, const uint32_t base) {
    typeof_unqual(base) fattore = base;
    if (v->priorita > 0U) {
        ++fattore;
    }
    auto risultato = (uint32_t)v->durata_ms * fattore;
    return risultato;
}

int main(void) {
    voce_log_t a = {.istante = 200, .codice = 12, .durata_ms = 30,
                    .livello = LIV_AVVISO, .priorita = 1};
    voce_log_t b = {.istante = 100, .codice = 5, .durata_ms = 20,
                    .livello = LIV_INFO, .priorita = 0};

    if (b.istante < a.istante) {
        scambia_voci(&a, &b);
    }

    auto punti_a = calcola_punteggio(&a, 2U);
    auto punti_b = calcola_punteggio(&b, 2U);
    const char *tipo_punti = _Generic(punti_a, uint32_t: "uint32_t", default: "altro");

    printf("Layout verificato: sizeof(voce_log_t)=%zu, tipo punti=%s\n",
           sizeof(voce_log_t), tipo_punti);
    printf("Prima voce: ts=%" PRIu64 " #%" PRIu32 " [%s] punti=%" PRIu32 "\n",
           a.istante, a.codice, NOMI_LIVELLO[a.livello], punti_a);
    printf("Seconda voce: ts=%" PRIu64 " #%" PRIu32 " [%s] punti=%" PRIu32 "\n",
           b.istante, b.codice, NOMI_LIVELLO[b.livello], punti_b);
    return 0;
}
```

```output
Layout verificato: sizeof(voce_log_t)=16, tipo punti=uint32_t
Prima voce: ts=100 #5 [INFO] punti=40
Seconda voce: ts=200 #12 [AVVISO] punti=90
```

Esaminiamo come lavorano insieme i quattro strumenti C23:
- Le cinque `static_assert` controllano ipotesi critiche sul programma già in fase di compilazione: se in futuro aggiungessi un quarto valore a `livello_t` dimenticando di aggiornare `NOMI_LIVELLO`, il compilatore ti avviserebbe immediatamente bloccando la compilazione.
- In `scambia_voci`, `typeof(*a) tmp = *a;` dichiara `tmp` con il tipo esatto di `*a` (`voce_log_t`).
- In `calcola_punteggio`, il parametro `base` è `const uint32_t`: usando `typeof_unqual(base) fattore = base;`, otteniamo una copia locale di tipo `uint32_t` priva del qualificatore `const`, così `++fattore;` compila senza errori.
- Le variabili `risultato`, `punti_a` e `punti_b` usano `auto`: il compilatore deduce `uint32_t` come confermato dall'espressione `_Generic` stampata in uscita.

> **Approfondimento — `auto` in C23 non introduce tipizzazione dinamica**
> Chi proviene da linguaggi come Python o JavaScript talvolta interpreta `auto` come una variabile capace di contenere valori di qualsiasi tipo. In C23 non è affatto così: `auto` è soltanto un'abbreviazione sintattica risolta interamente dal compilatore. Una volta dedotto `uint32_t` per `punti_a`, quella variabile resta `uint32_t` per tutta la sua durata di vita e il codice macchina generato è identico a quello prodotto scrivendo `uint32_t punti_a = ...;`.

### Esercizio 15.5 — Verificatore di pacchetti C23 con `static_assert`, `typeof`, `typeof_unqual` e `auto`

**Descrizione**

Scrivi un programma C23 che definisca `typedef enum stato_pkt : uint8_t { PKT_OK = 0, PKT_ATTESA = 1, PKT_ERRORE = 2, PKT_CONTEGGIO = 3 } stato_pkt_t;`, l'array costante `static const char *const NOMI_STATO[] = {"OK", "ATTESA", "ERRORE"};` e la struttura compatta `typedef struct pacchetto { uint64_t timestamp; uint32_t id; uint16_t lunghezza; uint8_t stato; uint8_t flag; } pacchetto_t;`. Inserisci cinque `static_assert` (usando sia la forma a due argomenti sia la forma C23 a un solo argomento) per verificare a tempo di compilazione: `CHAR_BIT == 8`, `sizeof(pacchetto_t) == 16`, `alignof(pacchetto_t) >= alignof(uint64_t)`, `offsetof(pacchetto_t, id) == 8 && offsetof(pacchetto_t, flag) == 15` e `sizeof(NOMI_STATO) / sizeof(NOMI_STATO[0]) == PKT_CONTEGGIO`. Implementa:

1. `void scambia_pacchetti(pacchetto_t *a, pacchetto_t *b)` usando `typeof(*a) tmp = *a;`;
2. `uint64_t peso_pacchetto(const pacchetto_t *p, const uint64_t fattore)` che usa `typeof_unqual(fattore) molt = fattore;` (rimuovendo `const` per poter incrementare `molt` di `1` quando `p->flag != 0`) e `auto ris = (uint64_t)p->lunghezza * molt;`.

In `main` leggi dalla prima riga `n` (`1 <= n <= 32`) e dalle successive `n` righe `timestamp id lunghezza stato flag` (`stato` in `0..2`, `lunghezza <= UINT16_MAX`, `flag <= UINT8_MAX`). Alloca `pacchetto_t *elenco` con `calloc`, ordina i pacchetti in ordine crescente di `timestamp` (e a parità per `id` crescente) tramite `scambia_pacchetti`, accumula `auto somma_len = (uint64_t)0;` e `auto somma_pond = (uint64_t)0;` (con `fattore = 2`) verificando il tipo dedotto da `auto` con `_Generic(somma_len, uint64_t: "uint64_t", default: "altro")`, stampa l'esito delle verifiche, i pacchetti ordinati e i totali esattamente come nell'esempio e libera la memoria.

**Concetti da tenere a mente**

- asserzione statica con `static_assert` (a uno e a due argomenti in C23) su `sizeof`, `alignof`, `offsetof` e `CHAR_BIT`
- `typeof(*a)` per dichiarare variabili temporanee coerenti con il tipo puntato
- `typeof_unqual(fattore)` per rimuovere `const` di primo livello e creare una copia modificabile
- inferenza statica del tipo con `auto` in C23 verificata a tempo di compilazione con `_Generic`

**Domande guida**

1. Che cosa succederebbe in `peso_pacchetto` se scrivessi `typeof(fattore) molt = fattore;` invece di `typeof_unqual(fattore) molt = fattore;` e poi tentassi `++molt`?
2. Quale errore protegge in modo automatico la `static_assert` su `sizeof(NOMI_STATO) / sizeof(NOMI_STATO[0]) == PKT_CONTEGGIO`?
3. Perché le cinque `static_assert` non aggiungono alcun costo di esecuzione al programma compilato?
4. Come mai in `auto somma_len = (uint64_t)0;` serve il cast esplicito `(uint64_t)0` se vuoi garantire che il tipo inferito sia `uint64_t`?

**Esempio di esecuzione**

```input
3
200 102 50 1 0
100 105 80 0 3
100 101 20 2 1
```

```output
Verifiche static_assert: superate (sizeof=16)
Tipo somma_len (auto): uint64_t
#101 ts=100 len=20 stato=ERRORE flag=1 pond=60
#105 ts=100 len=80 stato=OK flag=3 pond=240
#102 ts=200 len=50 stato=ATTESA flag=0 pond=100
Totale lunghezza: 150, totale ponderato: 400
```

## Riepilogo

- Un **puntatore generico** `void *` (o `const void *`) memorizza l'indirizzo di qualsiasi oggetto in memoria. In C qualsiasi puntatore a oggetto `T *` si converte implicitamente in `void *` e viceversa senza cast, rispettando la qualificazione `const`. Non si può dereferenziare un `void *` né applicarvi l'aritmetica dei puntatori: per leggere o scrivere i dati occorre riconvertirlo al tipo originale esatto (pena comportamento indefinito), mentre per calcolare uno spiazzamento in byte occorre convertirlo a `unsigned char *` (o `const unsigned char *`). `void *` riguarda solo puntatori a oggetti, non puntatori a funzione (lo vedremo nel capitolo 16).
- Le funzioni `mem*` di `<string.h>` operano su blocchi grezzi di esattamente `n` byte senza fermarsi ai byte `0x00`: `memcpy` copia tra aree disgiunte (parametri `restrict`), `memmove` gestisce in modo sicuro anche aree sovrapposte, `memset` imposta ciascun byte a `(unsigned char)c`, `memcmp` confronta byte come `unsigned char` (ma non va usata su `struct` con byte di padding) e `memchr` cerca un byte preservando `const` in C23. In C23 è vietato passare `nullptr` a queste funzioni anche quando `n == 0`.
- Un **contenitore generico** come un vettore dinamico generico conserva `void *dati`, `size_t dim_elem`, `size_t len` e `size_t cap`. Indirizza gli elementi come `(unsigned char *)v->dati + idx * v->dim_elem`, usa `memcpy`/`memmove` per copia e scorrimento, previene l'overflow con `nuova_cap <= SIZE_MAX / v->dim_elem` prima di `realloc` e garantisce automaticamente l'allineamento per tipi omogenei grazie all'allineamento di `malloc`/`realloc` e alla divisibilità di `sizeof(T)` per `alignof(T)`. Nei capitoli 16 e 17 integreremo questi contenitori con i puntatori a funzione per confronto e distruzione personalizzati.
- La selezione generica `_Generic(expr, tipo1: ris1, ..., default: ris_def)` sceglie un'espressione a tempo di compilazione senza valutare `expr`, rimuovendo i qualificatori di primo livello e distinguendo `char *`, `const char *` e il tipo C23 `nullptr_t` (`<stddef.h>`). Omettendo `default:` si ottiene un controllo di esaustività a compilazione.
- In C23 `typeof(expr)` ricava il tipo esatto di `expr` (mantenendo `const`), `typeof_unqual(expr)` rimuove i qualificatori di primo livello per dichiarare copie modificabili, `auto` deduce il tipo statico di una singola variabile dal suo inizializzatore e l'**asserzione statica** `static_assert` (a uno o due argomenti, senza header aggiuntivi) arresta la compilazione se una condizione costante è falsa, a costo zero durante l'esecuzione.

## Errori comuni

- **Tentare di dereferenziare direttamente un puntatore generico (`*p`) o di eseguirvi aritmetica dei puntatori (`p + 1`)**: il compilatore rifiuta entrambe le operazioni perché `void` non ha dimensione. Riconverti `p` al puntatore tipizzato originale per accedere al valore, oppure a `unsigned char *` (o `const unsigned char *`) per sommare spiazzamenti in byte.
- **Usare `memcpy` al posto di `memmove` quando sorgente e destinazione si sovrappongono dentro lo stesso buffer, oppure passare `nullptr` con `n == 0`**: entrambi i casi provocano comportamento indefinito in C23. Usa `memmove` ogni volta che i due intervalli possono sovrapporsi e proteggi le chiamate con `if (n > 0)` quando un puntatore può essere nullo.
- **Usare `memset(array_int, 1, sizeof(array_int))` per impostare ogni `int` a `1`, oppure confrontare due `struct` con padding tramite `memcmp`**: `memset` scrive il byte `0x01` in ogni singolo byte (ottenendo `0x01010101`, non `1`), mentre i byte di padding nelle strutture possono contenere bit arbitrari che falsano `memcmp`.
- **Scrivere chiamate di funzione con argomenti incompatibili dentro i rami di `_Generic`, oppure aspettarsi che l'espressione di controllo venga eseguita**: il compilatore verifica i tipi di tutti i rami di `_Generic`, quindi seleziona i nomi delle funzioni dentro `_Generic` e passa gli argomenti fuori dalle parentesi; ricorda inoltre che l'espressione di controllo non viene mai valutata.
- **Usare `typeof` su una variabile `const` e tentare di modificare la copia, oppure passare a `static_assert` una variabile ordinaria**: per ottenere una copia modificabile da un oggetto `const` usa `typeof_unqual`, e passa a `static_assert` esclusivamente espressioni costanti valutabili a tempo di compilazione.

## Prima di proseguire

- [ ] So spiegare le regole di conversione implicita tra `T *` e `void *`, il rispetto di `const`, perché `void *` non è dereferenziabile e come calcolare indirizzi in byte con `unsigned char *`.
- [ ] So scegliere correttamente tra `memcpy`, `memmove`, `memset`, `memcmp` e `memchr`, evitando sia le trappole su sovrapposizione, `memset` su interi e padding, sia il passaggio di `nullptr` con `n == 0`.
- [ ] So progettare e implementare un vettore dinamico generico con `void *dati`, `dim_elem`, controllo di overflow `SIZE_MAX / dim_elem` e spiegare perché l'allineamento degli elementi è garantito.
- [ ] So usare `_Generic` per selezionare etichette e funzioni specializzate (distinguendo `char *`, `const char *` e `nullptr_t`) senza incorrere in errori di tipo nei rami non selezionati.
- [ ] So usare `typeof`, `typeof_unqual`, `auto` e `static_assert` (a uno e a due argomenti) per scrivere codice C23 più sicuro e verificare a tempo di compilazione dimensioni, allineamento, offset e coerenza con gli `enum`.
