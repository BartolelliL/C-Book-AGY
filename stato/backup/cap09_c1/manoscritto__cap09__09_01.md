## 9.1 Array di `char` e terminatore nullo

Nel capitolo 8 hai visto che un array non memorizza al proprio interno la propria lunghezza: quando lo passi a una funzione devi accompagnarlo con un parametro `size_t n`. Per il testo, però, il C adotta una convenzione specifica: invece di conservare un contatore separato, marca la fine dei caratteri utili con un byte di valore zero.

Una **stringa** (*string*) in C è una sequenza di caratteri memorizzata in un array di `char` e chiusa dal carattere **terminatore nullo** (*null terminator*) `'\0'`, cioè il carattere di valore numerico zero che segna la fine della stringa.

Per visualizzare la differenza tra lo spazio riservato in memoria e il testo effettivamente contenuto, guarda come appare in memoria l'array `char codice[12] = "IT-2026";`:

```text
Indice:   0     1     2     3     4     5     6     7     8     9     10    11
       +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
Byte:  | 'I' | 'T' | '-' | '2' | '0' | '2' | '6' |'\0' |'\0' |'\0' |'\0' |'\0' |
       +-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+-----+
       |<----------- 7 caratteri utili --------->| fin |<--- spazio residuo --->|
       |<---------------------- capacità del buffer: 12 byte ------------------>|
```

Osserva bene lo schema:

- La **capacità** del buffer è la dimensione fisica dell'array in byte, ottenibile con `sizeof(codice)` nella stessa visibilità della dichiarazione: qui vale `12`.
- La **lunghezza logica** della stringa è il numero di caratteri che precedono il primo `'\0'`: qui vale `7`.
- Poiché almeno un byte deve sempre essere riservato a `'\0'`, un buffer `char s[N]` può contenere una stringa di lunghezza logica al più `N - 1`.

### Inizializzare una stringa

In C puoi inizializzare un array di `char` con una stringa letterale in diversi modi:

<!-- cod: id=9.1-b tipo=frammento -->
```c
char saluto[] = "ciao";      // 5 byte: 'c', 'i', 'a', 'o', '\0'
char etichetta[16] = "ciao"; // 16 byte: i primi 5 come sopra, gli altri 11 azzerati
char vuota[8] = "";          // 8 byte: vuota[0] == '\0' (lunghezza logica 0)
```

Quando ometti la dimensione tra parentesi quadre (`char saluto[] = "ciao";`), il compilatore conta automaticamente i caratteri della stringa letterale e aggiunge `1` per `'\0'`: `sizeof(saluto)` vale quindi `5`, non `4`. Quando invece indichi una dimensione maggiore (`char etichetta[16] = "ciao";`), il compilatore copia i caratteri e il `'\0'` iniziale, e azzera tutti i byte rimanenti (la stessa regola che hai visto per gli array nel capitolo 8). La stringa vuota `""` non occupa zero byte: contiene comunque un singolo byte pari a `'\0'`, quindi ha lunghezza logica `0` ma richiede almeno `1` byte di memoria.

Esiste però un pericolo serio: un array di `char` privo di `'\0'` **non è una stringa valida**. Per esempio:

<!-- cod: id=9.1-c tipo=frammento -->
```c
// Attenzione: NON è una stringa valida! Manca '\0'.
char non_stringa[4] = {'c', 'i', 'a', 'o'};
```

Anche `char rotta[4] = "ciao";` è un errore subdolo: in C lo standard consente questa inizializzazione troncando il `'\0'` finale, producendo un array di 4 byte senza terminatore nullo. Secondo lo standard C23, una stringa è definita come una sequenza di caratteri terminata dal carattere nullo; passare un array di `char` privo di `'\0'` a `printf("%s", ...)`, `puts` o alle funzioni di `<string.h>` provoca lettura fuori dai limiti e **comportamento indefinito**: la funzione continua a leggere i byte successivi in memoria finché non incontra casualmente uno zero o il programma si arresta.

### Scorrere, pulire e stampare una stringa

Poiché ogni stringa valida termina con `'\0'`, puoi scorrerla carattere per carattere con un ciclo `while` o `for` fermandoti non appena `s[i] == '\0'`:

<!-- cod: id=9.1-d tipo=frammento -->
```c
size_t lunghezza = 0;
while (s[lunghezza] != '\0') {
    ++lunghezza;
}
```

Lo stesso meccanismo serve per pulire una riga letta con `fgets`. Come hai visto nel capitolo 5, `fgets` inserisce nel buffer anche il carattere `'\n'` se l'intera riga entra nello spazio disponibile. Per rimuoverlo manualmente, cerchi il primo carattere che sia `'\n'` oppure `'\0'` e lo sostituisci con `'\0'`: in questo modo la stringa termina esattamente prima del ritorno a capo.

Per stampare una stringa su `stdout` hai due strumenti in `<stdio.h>`:

- `printf("%s", s)` stampa tutti i caratteri di `s` fino al primo `'\0'`, senza andare a capo da sola.
- `puts(s)` stampa la stringa `s` seguita automaticamente da `'\n'` e restituisce un intero non negativo (oppure `EOF` in caso di errore). È comoda e leggibile quando vuoi stampare una singola stringa su una riga intera.

### Passare stringhe alle funzioni

Quando passi una stringa a una funzione valgono le stesse regole degli array del capitolo 8:

- Se la funzione deve solo **leggere** la stringa, dichiara il parametro come `const char s[]`. In questo caso spesso non occorre un parametro `lunghezza`, perché il terminatore nullo `'\0'` indica già dove fermarsi.
- Se la funzione deve **scrivere** o aggiungere caratteri nella stringa, dichiara il parametro come `char s[]` e passa **sempre** anche la capacità del buffer (`size_t capienza`). Il terminatore nullo dice dove finisce il contenuto attuale, non quanto spazio fisico resta prima della fine dell'array.

> **Se vieni da Python** — In Python le stringhe sono oggetti immutabili di lunghezza arbitraria gestiti automaticamente; in C una stringa è un array mutabile di `char` a capacità fissa terminato da `'\0'`. Puoi modificare un singolo carattere direttamente con `s[i] = 'X';`, ma devi sempre rispettare la dimensione del buffer.

### Esempio guidato

Il programma seguente parte da un codice di spedizione memorizzato in `char codice[16]`, confronta la capacità del buffer con la lunghezza logica calcolata manualmente, legge un'etichetta da `stdin` con `fgets`, rimuove manualmente `'\n'`, la stampa con `puts` e infine mostra che cosa accade quando si inserisce `'\0'` a metà dell'array.

<!-- cod: id=9.1-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

size_t lunghezza_manuale(const char s[]) {
    size_t i = 0;
    while (s[i] != '\0') {
        ++i;
    }
    return i;
}

int main(void) {
    char codice[16] = "IT-2026";
    char etichetta[32];

    printf("Dimensione buffer codice: %zu byte\n", sizeof(codice));
    printf("Lunghezza logica codice: %zu\n", lunghezza_manuale(codice));

    if (fgets(etichetta, (int)sizeof(etichetta), stdin) == nullptr) {
        fprintf(stderr, "Errore: etichetta mancante.\n");
        return EXIT_FAILURE;
    }
    size_t i = 0;
    while (etichetta[i] != '\0' && etichetta[i] != '\n') {
        ++i;
    }
    etichetta[i] = '\0';

    printf("Etichetta (%zu caratteri):\n", lunghezza_manuale(etichetta));
    puts(etichetta);

    codice[2] = '\0';  // Accorcia logicamente la stringa dopo "IT"
    printf("Prefisso estratto: %s (lunghezza %zu, sizeof %zu)\n",
           codice, lunghezza_manuale(codice), sizeof(codice));
    return EXIT_SUCCESS;
}
```

```input
Fragile - Magazzino Nord
```

```output
Dimensione buffer codice: 16 byte
Lunghezza logica codice: 7
Etichetta (24 caratteri):
Fragile - Magazzino Nord
Prefisso estratto: IT (lunghezza 2, sizeof 16)
```

Analizziamo i passaggi principali del programma:

- `lunghezza_manuale` riceve `const char s[]`: il qualificatore `const` garantisce che la funzione non modifichi la stringa, e il ciclo `while (s[i] != '\0')` si arresta esattamente al terminatore nullo.
- Per `codice`, `sizeof(codice)` restituisce `16` (la capacità fisica dell'array), mentre `lunghezza_manuale(codice)` restituisce `7` (i caratteri di `"IT-2026"`).
- Dopo `fgets`, il ciclo cerca il primo `'\n'` o `'\0'` e scrive `'\0'` in quella posizione: se la riga conteneva `'\n'`, quel carattere viene rimosso; se non lo conteneva, il terminatore nullo resta invariato.
- `puts(etichetta)` stampa l'etichetta andando automaticamente a capo.
- L'istruzione `codice[2] = '\0';` sovrascrive il trattino `'-'` con il terminatore nullo. I caratteri `'2'`, `'0'`, `'2'`, `'6'` restano ancora nei byte successivi dell'array, ma per qualsiasi funzione di stringa `codice` ora contiene `"IT"` (lunghezza `2`), mentre `sizeof(codice)` rimane invariato a `16`.

> **Approfondimento — Differenza tra `'0'`, `'\0'` e `"0"` (e una nota su UTF-8)**
> È facile confondere tre espressioni molto simili ma del tutto diverse:
> - `'\0'` è un singolo `char` di valore numerico `0`: è il terminatore nullo che chiude una stringa.
> - `'0'` è un singolo `char` che rappresenta la cifra zero: in codifica ASCII il suo valore numerico è `48`, non `0`.
> - `"0"` è una stringa letterale composta da **due** `char`: la cifra `'0'` seguita automaticamente da `'\0'`.
>
> Un'altra precisazione riguarda i caratteri accentati: nei sistemi moderni il testo è codificato quasi sempre in UTF-8, dove una lettera come `à` o `è` occupa **due o più byte** (cioè più di un `char`), non uno solo. Di conseguenza il numero di byte di una stringa UTF-8 può essere maggiore del numero di lettere visibili. Per mantenere semplici e prevedibili gli indici carattere per carattere, negli esercizi di questo capitolo lavoreremo su testo ASCII.

### Esercizio 9.1 — Analisi e inversione manuale di una stringa senza `<string.h>`

**Descrizione**

Scrivi un programma C che includa solo `<stddef.h>`, `<stdio.h>` e `<stdlib.h>` (senza usare `<string.h>` né `<ctype.h>`) e dichiari prima di `main` i prototipi di quattro funzioni che lavorano su stringhe terminate da `'\0'`: `size_t rimuovi_newline(char s[])` (trova `'\n'`, se presente lo sostituisce con `'\0'`, e restituisce la lunghezza finale della stringa), `size_t conta_carattere(const char s[], char bersaglio)` (conta le occorrenze di `bersaglio` in `s`), `bool e_palindroma(const char s[], size_t lunghezza)` (verifica se `s` si legge allo stesso modo da sinistra e da destra; una stringa vuota è palindroma) e `void inverti_stringa(char s[], size_t lunghezza)` (inverte i caratteri sul posto lasciando invariato `'\0'`). In `main` leggi da `stdin` due righe con `fgets` (buffer di `128` byte): la prima è la stringa da analizzare (può essere vuota); la seconda contiene un solo carattere `bersaglio` validato con `sscanf(riga_c, " %c %c", &bersaglio, &extra) == 1`. Se manca una riga o il formato della seconda riga non è valido, stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`. Altrimenti stampa lunghezza, numero di occorrenze di `bersaglio`, esito palindromo (`si` o `no`), l'intestazione `Invertita:` e la stringa invertita stampata con `puts`, esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- stringa come array di `char` terminato da `'\0'`
- scorrimento manuale fino a `s[i] != '\0'`
- rimozione del ritorno a capo lasciato da `fgets`
- stampa di una stringa con `puts`
- conservazione del terminatore nullo durante l'inversione sul posto

**Domande guida**

1. Come fai a conoscere la fine della stringa dentro `rimuovi_newline` e `conta_carattere` senza ricevere un parametro `lunghezza` né chiamare `strlen`?
2. Che cosa accadrebbe se in `inverti_stringa` scambiassi anche il carattere in posizione `lunghezza` (cioè il terminatore nullo)?
3. Perché nella funzione `e_palindroma` il caso limite della stringa vuota (`lunghezza == 0`) non deve accedere a `s[lunghezza - 1]`?
4. Quale differenza c'è tra stampare la stringa invertita con `puts(testo)` rispetto a `printf("%s", testo)`?

**Esempio di esecuzione**

```input
radar
r
```

```output
Lunghezza: 5
Occorrenze di 'r': 2
Palindroma: si
Invertita:
radar
```
