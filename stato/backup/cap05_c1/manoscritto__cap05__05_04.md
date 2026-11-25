## 5.4 Leggere e scrivere singoli caratteri con `getchar` e `putchar`

Leggere intere righe con `fgets` è la scelta migliore per testo e numeri, ma in molti problemi vuoi ispezionare o produrre un singolo carattere alla volta: per esempio analizzare un codice a formato fisso, contare caratteri o trasformare un testo carattere per carattere. Per queste operazioni `<stdio.h>` fornisce due funzioni leggere ed essenziali: `getchar()` e `putchar(c)`.

La funzione `getchar()` legge il prossimo carattere disponibile nello stream `stdin`. La funzione `putchar(c)` fa l'operazione simmetrica: scrive un singolo carattere su `stdout` (convertendolo internamente in `unsigned char`) e restituisce il carattere scritto, oppure `EOF` in caso di errore di scrittura.

C'è una regola obbligatoria che devi rispettare ogni volta che usi `getchar()`: **salva sempre il valore restituito da `getchar()` in una variabile di tipo `int`, mai in un `char`**.

<!-- cod: id=5.4-b tipo=frammento -->
```c
int c = getchar();
if (c == EOF) {
    fprintf(stderr, "Fine dell'input.\n");
    return EXIT_FAILURE;
}
putchar(c);
```

Il motivo è semplice ma fondamentale. `getchar()` deve poter restituire *tutti* i possibili valori di un byte valido (cioè ogni possibile `unsigned char`, da `0` a `255` sui sistemi a 8 bit) *più* un valore distinto per segnalare la fine dell'input o un errore di lettura: la costante negativa `EOF` (definita in `<stdio.h>`). Un `char` non ha abbastanza valori distinti per contenere tutti i possibili byte *e* un segnale separato di fine dell'input; un `int`, invece, li distingue senza alcuna ambiguità. Per questo `getchar()` restituisce il carattere letto come `unsigned char` convertito in `int`, oppure `EOF`.

Lo standard C23 definisce con precisione il tipo di ritorno `int` di `getchar()` e garantisce che `EOF` sia un intero negativo; sono invece **dipendenti dall'implementazione** sia il valore numerico concreto di `EOF` (tipicamente `-1`, ma nel codice devi sempre confrontare con `EOF` e mai con `-1`) sia il fatto che il tipo `char` semplice sia con segno o senza segno.

Quando esegui un programma da terminale, fai attenzione a come arrivano i caratteri su `stdin`: di norma il terminale raccoglie ciò che digiti in un buffer di riga e consegna tutti i caratteri al programma solo quando premi Invio. Inoltre, il tasto Invio inserisce nello stream il carattere `'\n'`, che `getchar()` legge esattamente come qualsiasi altro carattere. Se l'utente digita `AB3` e preme Invio, nello stream ci sono quattro caratteri in sequenza:

```text
Posizione:   1     2     3     4
stdin:     [ 'A' | 'B' | '3' | '\n' ]
```

Di conseguenza, quando un input deve avere una lunghezza esatta (per esempio tre caratteri), non basta leggere i primi tre caratteri: conviene verificare sia che nessuno di essi sia `EOF` o `'\n'` (input troppo corto), sia che il carattere immediatamente successivo sia `'\n'` oppure `EOF` (per escludere caratteri extra sulla stessa riga).

Un'altra operazione frequente con i singoli caratteri è lavorare sulle cifre decimali. Lo standard C23 garantisce che i dieci caratteri `'0'`, `'1'`, `'2'`, ..., `'9'` abbiano codici numerici contigui e crescenti in qualsiasi codifica di caratteri supportata dal compilatore. Questo rende completamente portabili due operazioni:

- dopo aver verificato che `c >= '0' && c <= '9'`, l'espressione `c - '0'` calcola il valore numerico intero compreso tra `0` e `9` (per esempio `'5' - '0'` vale `5`);
- viceversa, dato un intero `d` compreso tra `0` e `9`, l'espressione `'0' + d` produce il carattere stampabile corrispondente, pronto per essere passato a `putchar`.

Al contrario, lo standard C23 non garantisce la contiguità delle lettere dell'alfabeto in tutte le codifiche esistenti, anche se su quasi tutti i sistemi moderni (ASCII/UTF-8) `'A'..'Z'` e `'a'..'z'` sono contigue; nei capitoli successivi vedremo le funzioni di `<ctype.h>` per classificare lettere e cifre in modo ancora più pulito.

In questa sotto-sezione leggiamo un numero fissato di caratteri con chiamate esplicite a `getchar()`, perché non abbiamo ancora introdotto i cicli. Per leggere ed elaborare sequenze di caratteri di lunghezza arbitraria fino a `EOF` userai un ciclo `while` (lo vedremo nel capitolo 6).

### Esempio guidato

Il programma seguente legge una sigla operativa composta esattamente da tre caratteri: due lettere maiuscole (`'A'..'Z'`) seguite da una cifra di priorità (`'1'..'5'`). Usa `getchar()` salvando ogni risultato in una variabile `int`, verifica l'assenza di `EOF`, di `'\n'` prematuri e di caratteri extra dopo il terzo carattere, ricava il livello numerico di priorità con `c3 - '0'` e stampa la sigla formattata carattere per carattere con `putchar`.

<!-- cod: id=5.4-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int c1 = getchar();
    int c2 = getchar();
    int c3 = getchar();
    int c4 = getchar();

    if (c1 == EOF || c2 == EOF || c3 == EOF ||
        c1 == '\n' || c2 == '\n' || c3 == '\n') {
        fprintf(stderr, "Errore: la sigla deve avere 3 caratteri.\n");
        return EXIT_FAILURE;
    }
    if (c4 != '\n' && c4 != EOF) {
        fprintf(stderr, "Errore: caratteri extra dopo la sigla.\n");
        return EXIT_FAILURE;
    }
    if (c1 < 'A' || c1 > 'Z' || c2 < 'A' || c2 > 'Z' ||
        c3 < '1' || c3 > '5') {
        fprintf(stderr, "Errore: attese due lettere A-Z e una cifra 1-5.\n");
        return EXIT_FAILURE;
    }

    int priorita = c3 - '0';
    printf("Sigla formattata: ");
    putchar('[');
    putchar(c1);
    putchar(c2);
    putchar(']');
    putchar('-');
    putchar('P');
    putchar('0' + priorita);
    putchar('\n');
    printf("Livello di priorità: %d su 5\n", priorita);
    return EXIT_SUCCESS;
}
```

```input
KR4
```

```output
Sigla formattata: [KR]-P4
Livello di priorità: 4 su 5
```

Segui passo dopo passo che cosa fa il programma:

- Le quattro variabili `c1`, `c2`, `c3` e `c4` hanno tutte tipo `int`, così ciascuna può distinguere qualsiasi carattere valido dalla costante negativa `EOF`.
- Il primo `if` intercetta sia una fine dell'input anticipata (`EOF`) sia un ritorno a capo prematuro (`'\n'`, se l'utente ha digitato solo uno o due caratteri prima di premere Invio).
- Il secondo `if` controlla `c4`: se l'input termina correttamente dopo tre caratteri, `c4` sarà `'\n'` (se l'utente ha premuto Invio) oppure `EOF` (se lo stream si è chiuso subito dopo il terzo carattere). Qualunque altro valore indica caratteri in eccesso.
- Il terzo `if` verifica che i primi due caratteri siano lettere maiuscole e che il terzo sia una cifra compresa tra `'1'` e `'5'`.
- L'espressione `c3 - '0'` trasforma il carattere `'4'` nell'intero `4`; nella serie di `putchar` finali, `'0' + priorita` esegue la trasformazione inversa per scrivere il carattere `'4'` su `stdout`, seguito da `'\n'`.

> **Approfondimento — Perché `char c = getchar();` è un bug di portabilità**
> Scrivere `char c = getchar();` sembra innocuo, ma fallisce in modo diverso a seconda che il compilatore tratti `char` come senza segno o con segno (comportamento dipendente dall'implementazione):
> - sulle piattaforme in cui `char` è **senza segno** (per esempio molti sistemi ARM), i valori di `char` vanno da `0` a `255`: il valore negativo `EOF` viene convertito in `255` e il confronto `c == EOF` risulta **sempre falso**, impedendo al programma di rilevare la fine dell'input;
> - sulle piattaforme in cui `char` è **con segno** (da `-128` a `127`), il byte valido di valore `255` (`0xFF`) viene troncato in `-1`, che coincide con `EOF`: il programma interrompe la lettura in anticipo scambiando un dato valido per la fine dello stream.
> Dichiarare sempre `int c = getchar();` elimina entrambi i bug su ogni architettura.

### Esercizio 5.4 — Verifica di un codice di accesso con `getchar` e `putchar`

**Descrizione**

Un laboratorio usa codici di accesso composti esattamente da quattro caratteri: una lettera maiuscola di settore (`'A'` = `Archivio`, `'B'` = `Biblioteca`, `'C'` = `Centro calcolo`) seguita da tre cifre decimali (`'0'..'9'`). Scrivi un programma C che legga i caratteri uno alla volta con cinque chiamate a `getchar()` salvate in variabili `int` (`c1..c4` per il codice e `c5` per verificare che la riga termini con `'\n'` oppure `EOF`). Se uno dei primi quattro caratteri è `EOF`, se `c5` è diverso sia da `'\n'` sia da `EOF`, se `c1` non è tra `'A'`, `'B'`, `'C'` oppure se una delle tre posizioni numeriche non è compresa tra `'0'` e `'9'`, stampa un messaggio di errore su `stderr` con `fprintf` e restituisci `EXIT_FAILURE`. Altrimenti converti le tre cifre in valori numerici con `c - '0'`, calcola il numero intero a tre cifre (`d1 * 100 + d2 * 10 + d3`), la somma delle cifre e la cifra di controllo (`somma_cifre % 10`). Stampa la riga `Codice verificato: ` seguita dal codice nel formato `X-DDD-C` scrivendo ogni singolo carattere con `putchar` (incluso `'0' + controllo` e `'\n'`), quindi stampa settore, numero e somma delle cifre come nell'esempio di esecuzione e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- lettura carattere per carattere con `getchar()` in variabili `int`
- costante `EOF` e controllo della fine della riga
- scrittura di singoli caratteri con `putchar`
- conversione tra carattere cifra e valore numerico tramite `'0'`
- gestione degli errori su `stderr` con `EXIT_FAILURE`

**Domande guida**

1. Perché le variabili che ricevono il risultato di `getchar()` devono essere dichiarate `int` e non `char`?
2. A che cosa serve leggere anche un quinto carattere dopo i quattro caratteri del codice e confrontarlo sia con `'\n'` sia con `EOF`?
3. Perché l'espressione `c2 - '0'` calcola in modo portabile il valore intero di una cifra decimale dopo aver verificato che `c2` sia tra `'0'` e `'9'`?
4. Come puoi ottenere il carattere stampabile corrispondente alla cifra di controllo intera compresa tra `0` e `9` prima di passarlo a `putchar`?

**Esempio di esecuzione**

```input
B407
```

```output
Codice verificato: B-407-1
Settore: Biblioteca
Numero: 407
Somma cifre: 11
```
