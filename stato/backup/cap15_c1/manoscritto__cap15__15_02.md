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
- usa **`memcpy`** solo quando sei certo che i `n` byte di sorgente e gli `n` byte di destinazione **non si sovrappongono** (per esempio quando copi da un buffer temporaneo a un array di destinazione). Invocare `memcpy` su aree sovrapposte viola il contratto di `restrict` e provoca **comportamento indefinito**: una copia ottimizzata potrebbe sovrascrivere byte non ancora letti.
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

Il programma seguente lavora su un buffer binario `uint8_t trama[12]` che contiene deliberatamente byte `0x00`. Inizializza l'intero buffer con `memset`, copia un'intestazione da un array separato con `memcpy`, sposta una porzione sovrapposta con `memmove`, cerca un byte marcatore dopo uno zero con `memchr` e confronta due sotto-blocchi con `memcmp`.

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

In `main` leggi da `stdin` fino a fine input comandi (con valori di byte decimali in `0..255`): `INS <pos> <k> <b0> ... <bk-1>` (`0 <= k <= 16`), `DEL <pos> <n>`, `FILL <pos> <n> <val>`, `FIND <da> <val>`, `CMP <p1> <p2> <n>` e `DUMP`, stampando gli esiti esattamente come nell'esempio di esecuzione.

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
