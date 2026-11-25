# Capitolo 9 — Stringhe

> **In questo capitolo imparerai a:**
> - Manipolare stringhe C come array di `char` terminati da `'\0'`
> - Usare correttamente le funzioni di `<string.h>` e `<ctype.h>` rispettando il cast a `unsigned char`
> - Costruire stringhe formattate in modo sicuro con `snprintf` verificando eventuali troncamenti
> - Prevenire i buffer overflow nella copia, concatenazione e analisi del testo

> **Ti servono:** i capitoli 2, 5, 6, 7 e 8 (tipo `char`, `size_t` e `sizeof`, lettura sicura con `fgets`, cicli, funzioni e array).

Finora i tuoi programmi hanno lavorato soprattutto con numeri: contatori, misure, coordinate e tabelle memorizzate in array. Nel mondo reale, però, quasi ogni programma elabora anche testo: nomi di persone e di file, codici di spedizione, comandi digitati dall'utente, messaggi di errore e righe formattate da salvare o mostrare a schermo.

A differenza di molti altri linguaggi, il C non offre un tipo dedicato per il testo di lunghezza automatica. Una stringa in C è costruita direttamente sopra lo strumento che hai appena imparato nel capitolo 8: un normale array di `char`, chiuso da uno speciale carattere di valore zero (`'\0'`) che segnala dove termina il testo. Questa scelta rende il C essenziale e molto efficiente, ma affida interamente a te la responsabilità di rispettare i limiti del buffer e di mantenere sempre integro quel carattere finale.

In questo capitolo imparerai prima a gestire le stringhe manualmente, per capire davvero che cosa accade in memoria, e poi a usare in modo rigoroso le funzioni della libreria standard in `<string.h>`, `<ctype.h>` e `<stdio.h>` (`snprintf`). Scoprirai anche come evitare una delle classi di errori più insidiose della programmazione in C: i buffer overflow.

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

Quando ometti la dimensione tra parentesi quadre (`char saluto[] = "ciao";`), il compilatore conta automaticamente i caratteri della stringa letterale e aggiunge `1` per `'\0'`: `sizeof(saluto)` vale quindi `5`, non `4`. Quando invece indichi una dimensione maggiore (`char etichetta[16] = "ciao";`), il compilatore copia i caratteri e il `'\0'` finale, e azzera tutti i byte rimanenti (la stessa regola che hai visto per gli array nel capitolo 8). La stringa vuota `""` non occupa zero byte: contiene comunque un singolo byte pari a `'\0'`, quindi ha lunghezza logica `0` ma richiede almeno `1` byte di memoria.

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
> - `'\0'` è una costante carattere di valore numerico `0`: è il terminatore nullo che chiude una stringa.
> - `'0'` è una costante carattere che rappresenta la cifra zero: in codifica ASCII il suo valore numerico è `48`, non `0`.
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

## 9.2 Elaborare stringhe con `<string.h>`

Scrivere ogni volta un ciclo manuale per misurare, confrontare o cercare dentro una stringa sarebbe lungo e ripetitivo. La libreria standard del C raccoglie queste operazioni nell'header `<string.h>`. Le funzioni di `<string.h>` sono veloci e ben collaudate, ma richiedono attenzione: tutte presumono che le stringhe in ingresso siano terminate da `'\0'` e che tu rispetti la capacità dei buffer di destinazione.

### Misurare la lunghezza: `strlen`

La funzione `strlen(s)` restituisce un `size_t` pari al numero di caratteri di `s` che precedono il terminatore nullo `'\0'`. A differenza di `sizeof`, `strlen` non conosce la capacità del buffer: scorre la stringa byte per byte finché non incontra `'\0'`.

Questa proprietà ha una conseguenza pratica importante: **non chiamare mai `strlen(s)` nella condizione di un ciclo `for`**.

<!-- cod: id=9.2-b tipo=frammento -->
```c
// Inefficiente: ricalcola strlen(s) a ogni iterazione
for (size_t i = 0; i < strlen(s); ++i) { ... }

// Corretto: calcola la lunghezza una sola volta prima del ciclo
size_t lun = strlen(s);
for (size_t i = 0; i < lun; ++i) { ... }
```

Su una stringa di lunghezza $n$, chiamare `strlen(s)` a ogni iterazione trasforma un semplice attraversamento lineare in un lavoro proporzionale a $n \cdot n$. Se invece salvi il valore in una variabile `size_t lun = strlen(s);` (oppure controlli direttamente `s[i] != '\0'`), scorri la stringa una sola volta.

### Confrontare stringhe: `strcmp` e `strncmp`

Come per qualunque altro array (capitolo 8), non puoi confrontare due stringhe con `s1 == s2`: quell'espressione non confronta i caratteri delle due stringhe. Per confrontare il contenuto di due stringhe in ordine lessicografico (cioè carattere per carattere secondo il valore numerico di ciascun byte interpretato come `unsigned char`) si usano:

- `strcmp(s1, s2)` confronta interamente `s1` e `s2`.
- `strncmp(s1, s2, n)` confronta al più i primi `n` caratteri di `s1` e `s2` (utile per verificare un prefisso).

Entrambe restituiscono un `int` il cui **segno** indica il risultato del confronto:

- `< 0` se `s1` precede `s2` in ordine lessicografico;
- `0` se le due stringhe (o i primi `n` caratteri) sono uguali;
- `> 0` se `s1` segue `s2`.

Lo standard C23 definisce solo il segno del valore restituito, non la sua grandezza: non scrivere mai `strcmp(a, b) == 1` o `strcmp(a, b) == -1`, ma confronta sempre con `0` (`< 0`, `== 0`, `> 0`).

### Cercare caratteri, sottostringhe e prefissi

`<string.h>` mette a disposizione due famiglie di funzioni di ricerca:

1. **Funzioni di ricerca che segnalano presenza o assenza tramite `nullptr`**:
   - `strchr(s, c)` cerca la **prima** occorrenza del carattere `(char)c` in `s` (incluso `'\0'`);
   - `strrchr(s, c)` cerca l'**ultima** occorrenza del carattere `(char)c` in `s`;
   - `strstr(s1, s2)` cerca la prima occorrenza della sottostringa `s2` dentro `s1`;
   - `strpbrk(s1, s2)` cerca in `s1` il primo carattere che appartiene all'insieme di caratteri contenuti in `s2`.

   Tutte e quattro restituiscono `nullptr` se la ricerca fallisce, oppure un puntatore alla posizione trovata. Imparerai a usare direttamente quel puntatore nel capitolo 10; in questo capitolo puoi già verificare se un carattere o una sottostringa è presente confrontando il risultato con `!= nullptr` (o `== nullptr`).

2. **Funzioni che misurano un prefisso e restituiscono un `size_t`**:
   - `strcspn(s1, s2)` restituisce la lunghezza del prefisso iniziale di `s1` composto solo da caratteri **assenti** in `s2`;
   - `strspn(s1, s2)` restituisce la lunghezza del prefisso iniziale di `s1` composto **esclusivamente** da caratteri **presenti** in `s2`.

Con `strcspn` si scrive l'idioma standard più pulito per rimuovere il ritorno a capo lasciato da `fgets`:

<!-- cod: id=9.2-c tipo=frammento -->
```c
riga[strcspn(riga, "\n")] = '\0';
```

Se `riga` contiene `'\n'`, `strcspn(riga, "\n")` restituisce esattamente l'indice di `'\n'`, che viene sostituito con `'\0'`. Se `riga` non contiene `'\n'`, `strcspn` restituisce la lunghezza della stringa, cioè l'indice del terminatore nullo già presente, che viene riscritto con `'\0'` senza alcun danno. Con `strspn`, invece, puoi verificare che una stringa contenga solo caratteri permessi controllando `strspn(s, ammessi) == strlen(s)`.

### Copia e concatenazione: `strcpy`, `strncpy`, `strcat` e `strncat`

Come per il confronto, non puoi copiare una stringa con `dest = orig`. In `<string.h>` esistono quattro funzioni per copiare e accodare stringhe:

- `strcpy(dest, orig)` copia `orig` in `dest`, incluso `'\0'`, senza verificare la capacità di `dest`.
- `strcat(dest, orig)` accoda `orig` al termine di `dest`, incluso `'\0'`, senza verificare la capacità di `dest`.
- `strncpy(dest, orig, n)` copia al più `n` caratteri da `orig` in `dest`. Se `orig` è più corta di `n`, riempie i byte rimanenti con `'\0'`. **Attenzione**: se `orig` ha lunghezza maggiore o uguale a `n`, `strncpy` **non scrive alcun `'\0'` finale**, lasciando `dest` privo di terminatore nullo se non lo imposti tu esplicitamente.
- `strncat(dest, orig, n)` accoda al più `n` caratteri di `orig` al termine di `dest` e aggiunge **sempre** `'\0'` finale. **Attenzione**: il terzo argomento `n` non è la dimensione totale del buffer `dest`, ma il numero massimo di caratteri da aggiungere; perciò `dest` deve avere almeno `strlen(dest) + n + 1` byte di capacità totale (spesso si passa `sizeof(dest) - strlen(dest) - 1` dopo aver verificato che resti spazio).

Regola fondamentale dallo standard C23: in tutte e quattro le funzioni (`strcpy`, `strncpy`, `strcat`, `strncat`), sorgente e destinazione **non devono sovrapporsi in memoria** e la scrittura **non deve mai superare la capacità di `dest`**; violare una delle due condizioni provoca **comportamento indefinito**. Controlla sempre in anticipo la capacità disponibile prima di copiare o accodare.

> **Se vieni da Python** — In Python puoi confrontare e concatenare stringhe con `==` e `+`, e `len(s)` impiega tempo costante. In C devi usare funzioni come `strcmp`, `snprintf` o copie e concatenazioni controllate verificando sempre la capienza del buffer, e `strlen(s)` scorre la stringa fino a `'\0'`.

> **C23** — In C23 `strchr`, `strrchr`, `strstr` e `strpbrk` preservano il qualificatore `const` del primo argomento: se passi una stringa `const char[]`, il risultato mantiene `const` evitando modifiche accidentali (lo vedremo nel capitolo 10). Nei compilatori più vecchi (C11/C17) il risultato perdeva il qualificatore `const` anche quando il primo argomento era di sola lettura.

### Esempio guidato

Il programma seguente legge due nomi di file di registro da `stdin`, rimuove `'\n'` con `strcspn`, verifica se il primo inizia con `"log_"` tramite `strncmp`, controlla la presenza del punto con `strrchr` e della sottostringa `"err"` con `strstr`, confronta i due nomi in ordine lessicografico con `strcmp` e infine compone un percorso etichettato controllando la capienza prima di `strcpy` e `strncat`.

<!-- cod: id=9.2-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char nome1[64];
    char nome2[64];
    char percorso[80] = "";

    if (fgets(nome1, (int)sizeof(nome1), stdin) == nullptr ||
        fgets(nome2, (int)sizeof(nome2), stdin) == nullptr) {
        fprintf(stderr, "Errore: servono due nomi di file.\n");
        return EXIT_FAILURE;
    }
    nome1[strcspn(nome1, "\n")] = '\0';
    nome2[strcspn(nome2, "\n")] = '\0';

    bool prefisso_log = (strncmp(nome1, "log_", 4) == 0);
    bool ha_punto = (strrchr(nome1, '.') != nullptr);
    bool contiene_err = (strstr(nome1, "err") != nullptr);

    printf("File 1: %s (lunghezza %zu)\n", nome1, strlen(nome1));
    printf("Prefisso log_: %s, punto: %s, contiene err: %s\n",
           prefisso_log ? "si" : "no", ha_punto ? "si" : "no",
           contiene_err ? "si" : "no");

    int cmp = strcmp(nome1, nome2);
    printf("Ordine: %s\n", cmp < 0 ? "nome1 prima di nome2"
                         : (cmp > 0 ? "nome1 dopo nome2" : "uguali"));

    const char DIR[] = "archivio/";
    if (strlen(DIR) + strlen(nome1) < sizeof(percorso)) {
        strcpy(percorso, DIR);
        size_t spazio = sizeof(percorso) - strlen(percorso) - 1;
        strncat(percorso, nome1, spazio);
        printf("Percorso: %s\n", percorso);
    } else {
        printf("Percorso troppo lungo per il buffer.\n");
    }
    return EXIT_SUCCESS;
}
```

```input
log_errore.txt
log_avvio.txt
```

```output
File 1: log_errore.txt (lunghezza 14)
Prefisso log_: si, punto: si, contiene err: si
Ordine: nome1 dopo nome2
Percorso: archivio/log_errore.txt
```

Osserva come lavorano insieme le funzioni di `<string.h>`:

- `strcspn(nome1, "\n")` individua subito l'eventuale ritorno a capo e lo sostituisce con `'\0'`.
- `strncmp(nome1, "log_", 4) == 0` controlla solo i primi 4 caratteri senza richiedere che l'intera stringa sia uguale a `"log_"`.
- `strrchr(nome1, '.') != nullptr` e `strstr(nome1, "err") != nullptr` rispondono in modo pulito a domande di presenza senza bisogno di manipolare direttamente i puntatori restituiti.
- `strcmp(nome1, nome2)` confronta `"log_errore.txt"` e `"log_avvio.txt"`: poiché `'e'` segue `'a'`, restituisce un intero maggiore di `0`, e controlliamo `cmp > 0` (mai `cmp == 1`).
- Prima di chiamare `strcpy` e `strncat` verifichiamo `strlen(DIR) + strlen(nome1) < sizeof(percorso)` (stretto `<`, per lasciare almeno un byte a `'\0'`), e calcoliamo lo spazio residuo `sizeof(percorso) - strlen(percorso) - 1` come terzo argomento di `strncat`.

> **Approfondimento — Insidie di `strncpy` e conservazione di `const` in C23**
> Molti principianti pensano che `strncpy` sia la versione "sicura" di `strcpy`, ma non lo è affatto: è stata progettata originariamente per campi di lunghezza fissa non necessariamente terminati da `'\0'`. Se scrivi `strncpy(dest, orig, sizeof(dest));` e `orig` ha almeno `sizeof(dest)` caratteri, `dest` rimane privo di `'\0'`; dovresti quindi scrivere comunque `dest[sizeof(dest) - 1] = '\0';`. Inoltre, se `orig` è corta e `dest` è grande, `strncpy` spreca tempo azzerando tutti i byte residui. Per copiare stringhe in modo chiaro e sicuro conviene quasi sempre controllare la lunghezza prima di `strcpy` oppure usare `snprintf` (sotto-sezione 9.4).
>
> Quanto a `strchr`, `strrchr`, `strstr` e `strpbrk`, nel capitolo 10 vedrai come il puntatore che restituiscono permette di estrarre estensioni o suddividere una stringa senza copiarla, e perché la novità C23 che preserva `const` impedisce di modificare per errore una stringa di sola lettura.

### Esercizio 9.2 — Filtro e ordine lessicografico di etichette con `<string.h>`

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stdlib.h>` e `<string.h>` per analizzare un elenco di etichette. Leggi dalla prima riga di `stdin` la parola chiave `chiave` (buffer di `32` byte), rimuovi `'\n'` con `strcspn` e verifica che non sia vuota (`strlen(chiave) > 0`; altrimenti errore su `stderr` e `EXIT_FAILURE`). Leggi poi fino alla fine dell'input una sequenza di etichette (buffer di `48` byte), rimuovendo `'\n'` con `strcspn`. Ignora le righe vuote; un'etichetta è valida solo se tutti i suoi caratteri appartengono a `"abcdefghijklmnopqrstuvwxyz0123456789-_"` (verificato con `strspn(voce, ...) == strlen(voce)`): se non è valida incrementa `scartate` e passa alla successiva. Sulle etichette valide calcola: quante sono uguali a `chiave` (`strcmp == 0`), quante iniziano con `chiave` (`strncmp == 0`), quante contengono `chiave` (`strstr != nullptr`), quante contengono almeno un separatore `'-'` o `'_'` (`strpbrk != nullptr`), e mantieni la prima e l'ultima in ordine lessicografico (`strcmp` + `strcpy` in due buffer da `48` byte). Inoltre raccogli in un buffer `trovate[128] = ""` le etichette che contengono `chiave`, separate da `", "`, usando `strncat` solo quando c'è spazio sufficiente (controllando `strlen(trovate) + sep + strlen(voce) < sizeof(trovate)`). Se non ci sono etichette valide stampa `Nessuna etichetta valida.` e `Valide: 0, scartate: S`; altrimenti stampa il riepilogo esattamente come nell'esempio di esecuzione (usando `(nessuna)` se `trovate` è vuota).

**Concetti da tenere a mente**

- rimozione di `'\n'` con `strcspn` e validazione dell'alfabeto con `strspn`
- confronto esatto (`strcmp`) e per prefisso (`strncmp`)
- ricerca di sottostringhe (`strstr`) e di caratteri separatori (`strpbrk`)
- copia e concatenazione controllata con `strcpy` e `strncat`

**Domande guida**

1. In che modo il confronto `strspn(voce, caratteri_ammessi) == strlen(voce)` garantisce che l'intera etichetta contenga solo caratteri permessi?
2. Perché non puoi confrontare due etichette con `voce == chiave` ma devi usare `strcmp(voce, chiave) == 0`?
3. Quale controllo devi eseguire prima di chiamare `strncat` sul buffer `trovate` per evitare un buffer overflow e non aggiungere un separatore senza l'etichetta successiva?
4. Come gestisci l'inizializzazione di `prima_less` e `ultima_less` quando incontri la prima etichetta valida?

**Esempio di esecuzione**

```input
net
net-core
alpha
net_io
Bad!Tag
supernet

net
```

```output
Valide: 5, scartate: 1
Uguali a chiave: 1
Con prefisso chiave: 3
Contengono chiave: 4
Con separatore (- o _): 2
Prima lessicografica: alpha
Ultima lessicografica: supernet
Corrispondenze: net-core, net_io, supernet, net
```

## 9.3 Classificare e trasformare caratteri con `<ctype.h>`

Quando analizzi del testo — per esempio per verificare se un codice contiene solo cifre esadecimali, per contare le parole o per convertire una frase in minuscolo — potresti essere tentato di scrivere confronti manuali come `c >= 'a' && c <= 'z'` o sottrazioni come `c - 'a' + 'A'`. Questi trucchi sono poco leggibili, facili da sbagliare e assumono proprietà della codifica dei caratteri che non sono garantite in generale. La libreria standard offre invece l'header `<ctype.h>`, progettato apposta per classificare e trasformare singoli caratteri in modo chiaro e portabile.

### Funzioni di classificazione e di conversione

Le funzioni di classificazione di `<ctype.h>` verificano a quale categoria appartiene un carattere:

- `isalpha(c)`: lettera alfabetica (`'A'`-`'Z'`, `'a'`-`'z'` nel locale `"C"`);
- `isdigit(c)`: cifra decimale (`'0'`-`'9'`);
- `isalnum(c)`: lettera alfabetica oppure cifra decimale;
- `isspace(c)`: carattere di spaziatura (`' '`, `'\t'`, `'\n'`, `'\r'`, `'\v'`, `'\f'`);
- `isupper(c)`: lettera maiuscola;
- `islower(c)`: lettera minuscola;
- `isxdigit(c)`: cifra esadecimale (`'0'`-`'9'`, `'a'`-`'f'`, `'A'`-`'F'`);
- `ispunct(c)`: carattere stampabile di punteggiatura (né spazio né alfanumerico);
- `isprint(c)`: carattere stampabile, spazio incluso.

Per trasformare le lettere tra maiuscolo e minuscolo `<ctype.h>` fornisce due funzioni di conversione:

- `tolower(c)`: se `c` è una lettera maiuscola restituisce la corrispondente minuscola; lascia invariato qualunque altro carattere;
- `toupper(c)`: se `c` è una lettera minuscola restituisce la corrispondente maiuscola; lascia invariato qualunque altro carattere.

### Valore di ritorno delle funzioni `is*`

Tutte le funzioni di classificazione `is*` restituiscono un `int` che vale:

- `0` se il carattere **non** appartiene alla categoria (falso);
- un intero **diverso da zero** (non necessariamente `1`) se il carattere appartiene alla categoria (vero).

Perciò usa sempre il risultato direttamente dentro una condizione (`if (isdigit((unsigned char)c))` oppure `if (isdigit((unsigned char)c) != 0)`), e **non confrontarlo mai con `== 1`**.

### La regola obbligatoria del cast `(unsigned char)`

Tutte le funzioni di `<ctype.h>` hanno un parametro di tipo `int`, per poter accettare anche il valore `EOF` (restituito per esempio da `getchar`). Lo standard C23 stabilisce però un vincolo rigoroso sul valore dell'argomento: **deve valere `EOF` oppure essere rappresentabile come `unsigned char`** (cioè un intero non negativo in `0..UCHAR_MAX`).

Dove nasce il problema? Come hai imparato nel capitolo 2, se `char` sia con segno o senza segno è un comportamento dipendente dall'implementazione. Sulle piattaforme in cui `char` è con segno, un byte con valore superiore a `127` (come i byte di un carattere accentato o di un file non ASCII) ha valore negativo. Passare direttamente un `char` negativo diverso da `EOF` a `isalpha`, `isdigit`, `tolower` o a qualsiasi altra funzione di `<ctype.h>` provoca **comportamento indefinito**.

La regola da applicare sempre, senza eccezioni, è convertire esplicitamente ogni `char` a `unsigned char` prima di passarlo a una funzione di `<ctype.h>`:

<!-- cod: id=9.3-b tipo=frammento -->
```c
unsigned char uc = (unsigned char)s[i];
if (isdigit(uc)) { ... }
s[i] = (char)tolower(uc);
```

Nota anche il cast finale `(char)` sul valore restituito da `tolower` e `toupper` (che restituiscono un `int`) quando riassegni il risultato dentro un array di `char`: rende esplicita la conversione ed evita avvisi di conversione ristretta.

Infine, tieni presente che il comportamento esatto di queste funzioni dipende dal **locale** attivo nel programma: all'avvio di ogni programma C è attivo il locale predefinito `"C"`, nel quale le categorie corrispondono esattamente all'insieme di caratteri ASCII.

### Normalizzazione e validazione del testo

Combinando `<ctype.h>` con i cicli sulle stringhe puoi risolvere in modo pulito due compiti ricorrenti:

- **Normalizzare il testo**: ripulire spazi bianchi multipli usando `isspace`, uniformare maiuscole e minuscole con `tolower` o `toupper` e individuare l'inizio di ogni parola tenendo traccia con una variabile `bool` se il carattere precedente era uno spazio.
- **Validare token e codici**: controllare che un identificatore contenga solo caratteri `isalnum` o che un codice esadecimale abbia la lunghezza attesa e sia composto esclusivamente da cifre `isxdigit`.

### Esempio guidato

Il programma seguente legge una riga da `stdin`, rimuove `'\n'` con `strcspn`, conta maiuscole, minuscole, cifre decimali, spazi bianchi e segni di punteggiatura usando `<ctype.h>` con il cast `(unsigned char)`, e trasforma la frase mettendo in maiuscolo la prima lettera di ogni parola e in minuscolo le altre.

<!-- cod: id=9.3-a tipo=programma -->
```c
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char frase[128];
    if (fgets(frase, (int)sizeof(frase), stdin) == nullptr) {
        fprintf(stderr, "Errore: nessuna riga in ingresso.\n");
        return EXIT_FAILURE;
    }
    frase[strcspn(frase, "\n")] = '\0';

    int maiuscole = 0, minuscole = 0, cifre = 0, spazi = 0, punt = 0;
    bool inizio_parola = true;

    for (size_t i = 0; frase[i] != '\0'; ++i) {
        unsigned char uc = (unsigned char)frase[i];
        if (isupper(uc)) { ++maiuscole; }
        else if (islower(uc)) { ++minuscole; }
        else if (isdigit(uc)) { ++cifre; }
        else if (isspace(uc)) { ++spazi; }
        else if (ispunct(uc)) { ++punt; }

        if (isspace(uc)) {
            inizio_parola = true;
        } else if (inizio_parola) {
            frase[i] = (char)toupper(uc);
            inizio_parola = false;
        } else {
            frase[i] = (char)tolower(uc);
        }
    }

    printf("Maiuscole: %d, minuscole: %d, cifre: %d\n", maiuscole, minuscole, cifre);
    printf("Spazi: %d, punteggiatura: %d\n", spazi, punt);
    printf("Titolo: %s\n", frase);
    return EXIT_SUCCESS;
}
```

```input
c23: il LINGUAGGIO di programmazione, 2026!
```

```output
Maiuscole: 10, minuscole: 19, cifre: 6
Spazi: 5, punteggiatura: 3
Titolo: C23: Il Linguaggio Di Programmazione, 2026!
```

Osserva come è strutturato il ciclo:

- All'inizio di ogni iterazione salviamo `unsigned char uc = (unsigned char)frase[i];` una volta sola e passiamo `uc` a tutte le funzioni di `<ctype.h>`: il codice è più leggibile e rispetta sempre la regola del cast.
- I conteggi vengono eseguiti **prima** della trasformazione, così riflettono la frase originale (`10` maiuscole di `LINGUAGGIO`, `19` minuscole, `6` cifre tra `23` e `2026`).
- La variabile booleana `inizio_parola` parte da `true`, torna `true` ogni volta che incontra un carattere `isspace(uc)` e diventa `false` dopo il primo carattere non spazio di ciascuna parola. Poiché `toupper` e `tolower` lasciano invariati cifre e punteggiatura, applicarli a `frase[i]` non altera né `'2'` né `':'` né `'!'`.

> **Approfondimento — Perché un `char` negativo manda fuori strada `<ctype.h>`**
> Per essere estremamente veloci, molte implementazioni della libreria standard realizzano `isalpha`, `isdigit` e le altre funzioni di `<ctype.h>` come una lettura in una tabella statica in memoria, indicizzata direttamente dal parametro `int c` (spostato di `1` per includere `EOF == -1` all'indice `0`). Se passi un `char` negativo diverso da `EOF`, per esempio `-61`, l'indice calcolato risulta negativo e la funzione esegue un accesso fuori dai limiti della tabella: ecco perché lo standard C classifica questo errore come comportamento indefinito. Il cast `(unsigned char)` trasforma invece quel byte in un valore tra `0` e `255`, sempre dentro la tabella.

### Esercizio 9.3 — Normalizzatore di testo e validatore di colore esadecimale con `<ctype.h>`

**Descrizione**

Scrivi un programma C che includa `<ctype.h>`, `<stdio.h>`, `<stdlib.h>` e `<string.h>` e legga due righe da `stdin` (buffer da `128` e `32` byte), rimuovendo `'\n'` con `strcspn` (se manca una delle due righe stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`). Dichiara prima di `main` i prototipi di due funzioni che usano sempre il cast `(unsigned char)` in ogni chiamata a `<ctype.h>`: `void normalizza_testo(const char orig[], char dest[], size_t cap)` (elimina tutti gli spazi bianchi iniziali e finali tramite `isspace`, comprime ogni sequenza interna di caratteri `isspace` in un singolo spazio `' '` e converte tutte le lettere in minuscolo con `tolower`, terminando `dest` con `'\0'`) e `bool normalizza_colore_hex(const char orig[], char dest[], size_t cap)` (verifica che `orig` abbia lunghezza `7`, inizi con `'#'` e abbia esattamente `6` cifre `isxdigit`; se valida e `cap >= 8`, copia in `dest` il codice convertito in maiuscolo con `toupper` e restituisce `true`, altrimenti restituisce `false`). In `main`, sulla prima riga normalizzata conta parole (sequenze massimali di caratteri non `isspace`), caratteri alfanumerici (`isalnum`), segni di punteggiatura (`ispunct`) e caratteri stampabili (`isprint`), quindi stampa testo normalizzato (tra parentesi quadre `[...]`), conteggi e risultato della validazione del colore esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- cast obbligatorio a `(unsigned char)` per tutte le funzioni di `<ctype.h>`
- classificazione con `isspace`, `isalnum`, `ispunct`, `isprint` e `isxdigit`
- conversione con `tolower` e `toupper`
- compressione di spazi multipli e rimozione di spazi iniziali e finali

**Domande guida**

1. Perché ogni chiamata a `isspace`, `isxdigit`, `tolower` o `toupper` su un elemento di un array `char` deve applicare prima il cast `(unsigned char)`?
2. Come eviti di lasciare uno spazio finale in `dest` quando la stringa di ingresso termina con più spazi o tabulazioni?
3. Quali condizioni deve verificare `normalizza_colore_hex` prima di dichiarare valido un codice colore e convertirlo con `toupper`?
4. Perché il risultato di `isalnum` o `ispunct` va usato direttamente in un `if` anziché confrontato con `== 1`?

**Esempio di esecuzione**

```input
   Ciao,	Mondo   2026!  
#1a2B3c
```

```output
Testo normalizzato: [ciao, mondo 2026!]
Parole: 3
Alfanumerici: 13, punteggiatura: 2, stampabili: 17
Colore valido: #1A2B3C
```

## 9.4 Formattazione sicura con `snprintf`

Spesso non vuoi stampare subito un testo sullo schermo con `printf`, ma costruirlo in memoria dentro una stringa: per esempio un'etichetta di spedizione, una riga CSV, un nome di file o un messaggio di stato che combina testi e numeri.

Nella storia del C esisteva una funzione chiamata `sprintf` che scriveva in un buffer senza ricevere la sua capacità. Se il testo formattato risultava più lungo del buffer, `sprintf` continuava a scrivere oltre la fine dell'array provocando un buffer overflow. Per questo motivo `sprintf` è pericolosa ed è bandita da questo libro. Lo strumento moderno e sicuro di `<stdio.h>` è **`snprintf`**.

### Come funziona `snprintf`

La chiamata ha la forma:

```text
int risultato = snprintf(dest, capienza, formato, ...);
```

Secondo lo standard C23, `snprintf` rispetta regole molto precise:

- Scrive in `dest` **al massimo `capienza - 1` caratteri** e aggiunge **sempre** il terminatore nullo `'\0'` (purché `capienza > 0`). Non supera mai il limite indicato.
- Restituisce un `int`:
  - un valore **negativo** (`< 0`) in caso di errore di codifica o di formattazione;
  - altrimenti, il **numero di caratteri che sarebbero stati scritti** se il buffer fosse stato abbastanza grande, **escludendo `'\0'`**.
- Se `dest` e uno degli argomenti stringa passati in `...` si sovrappongono in memoria, il comportamento è **indefinito** (non passare mai `buf` contemporaneamente come destinazione e come argomento `%s`).

### Rilevare errori e troncamenti

Poiché `snprintf` restituisce la lunghezza che il testo *avrebbe* avuto (non i byte effettivamente scritti), puoi accorgerti sempre se il testo è stato troncato:

<!-- cod: id=9.4-b tipo=frammento -->
```c
int scritti = snprintf(buf, sizeof(buf), "ID=%d, peso=%.1f", id, peso);
if (scritti < 0) {
    // Errore di formattazione
} else if ((size_t)scritti >= sizeof(buf)) {
    // Troncamento: buf è comunque terminato da '\0', ma mancano dei caratteri
}
```

Fai molta attenzione al segno di confronto: è **`(size_t)scritti >= sizeof(buf)`**, non `>`. Se `sizeof(buf)` vale `20` e `scritti` vale `20`, i caratteri utili sarebbero `20` ma nel buffer servirebbero `21` byte per includere `'\0'`: quindi `snprintf` ha scritto solo `19` caratteri più `'\0'`, troncando l'ultimo carattere. Il test combinato `scritti < 0 || (size_t)scritti >= capienza` intercetta sia gli errori sia qualsiasi troncamento.

### Calcolare prima la lunghezza necessaria

Un uso molto utile di `snprintf` consiste nel passare `nullptr` come buffer e `0` come capacità:

<!-- cod: id=9.4-c tipo=frammento -->
```c
int richiesti = snprintf(nullptr, 0, "Codice %s (%d kg)", codice, kg);
```

Quando `capienza` è `0`, `snprintf` non scrive alcun byte in memoria e restituisce esattamente il numero di caratteri utili necessari (a cui dovrai aggiungere `1` per `'\0'` se vuoi conoscere la capacità minima del buffer).

### Assemblare messaggi composti in modo sicuro

Quando devi costruire una stringa in più passaggi (per esempio aggiungendo un segmento alla volta), puoi tenere una variabile `size_t usati = 0;` e verificare sempre quanto spazio resta prima di ogni passo, oppure formattare ciascun segmento in un buffer temporaneo e accodarlo solo se entra interamente nello spazio residuo `sizeof(dest) - usati`. In entrambi i casi, controllare il valore di ritorno di ogni chiamata ti garantisce che nessuna parte del messaggio venga tagliata di nascosto.

### Esempio guidato

Il programma seguente formatta un'etichetta di spedizione composta da codice, tratta e peso. Prima calcola la lunghezza esatta richiesta con `snprintf(nullptr, 0, ...)`, poi formatta la stessa etichetta in due buffer di dimensioni diverse (`etichetta[64]` e `corta[20]`), controllando su entrambi eventuali errori o troncamenti.

<!-- cod: id=9.4-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const char codice[] = "SP-409";
    const char tratta[] = "Torino-Bari";
    double peso_kg = 12.75;

    char etichetta[64];
    char corta[20];

    int richiesti = snprintf(nullptr, 0, "[%s] %s (%.2f kg)",
                             codice, tratta, peso_kg);
    int r_lunga = snprintf(etichetta, sizeof(etichetta), "[%s] %s (%.2f kg)",
                           codice, tratta, peso_kg);
    int r_corta = snprintf(corta, sizeof(corta), "[%s] %s (%.2f kg)",
                           codice, tratta, peso_kg);

    if (richiesti < 0 || r_lunga < 0 || r_corta < 0) {
        fprintf(stderr, "Errore: formattazione fallita.\n");
        return EXIT_FAILURE;
    }

    printf("Lunghezza richiesta: %d caratteri (+ 1 per '\\0')\n", richiesti);

    if ((size_t)r_lunga >= sizeof(etichetta)) {
        printf("Buffer 64 (troncato): %s\n", etichetta);
    } else {
        printf("Buffer 64 (ok): %s\n", etichetta);
    }

    if ((size_t)r_corta >= sizeof(corta)) {
        printf("Buffer 20 (troncato): %s\n", corta);
    } else {
        printf("Buffer 20 (ok): %s\n", corta);
    }
    return EXIT_SUCCESS;
}
```

```output
Lunghezza richiesta: 31 caratteri (+ 1 per '\0')
Buffer 64 (ok): [SP-409] Torino-Bari (12.75 kg)
Buffer 20 (troncato): [SP-409] Torino-Bar
```

Osserva i numeri prodotti dal programma:

- `snprintf(nullptr, 0, ...)` calcola che la stringa completa richiede `31` caratteri utili (quindi almeno `32` byte di buffer per includere `'\0'`).
- Nel buffer `etichetta` (64 byte), `(size_t)r_lunga < sizeof(etichetta)` (`31 < 64`), quindi il testo entra per intero.
- Nel buffer `corta` (20 byte), `r_corta` vale comunque `31`, cioè la lunghezza che *sarebbe* stata scritta. Poiché `31 >= 20`, rileviamo il troncamento: in `corta` sono stati scritti esattamente `19` caratteri (`[SP-409] Torino-Bar`) seguiti dal terminatore nullo `'\0'` in posizione `19`, senza alcun accesso fuori dai limiti.

> **Approfondimento — Misurare prima di scrivere con `snprintf(nullptr, 0, ...)`**
> Finché usi array a dimensione fissa, sapere in anticipo quanti byte servono ti aiuta a decidere se il buffer è sufficiente o se segnalare un errore. Quando imparerai ad allocare memoria dinamica (lo vedremo nel capitolo 11), il trucco di `snprintf(nullptr, 0, ...)` diventerà ancora più prezioso: chiamerai `snprintf(nullptr, 0, formato, ...)` per ottenere la lunghezza esatta `n`, allocherai esattamente `n + 1` byte con `malloc` e poi scriverai la stringa senza mai sprecare spazio né rischiare troncamenti.

### Esercizio 9.4 — Generatore di record CSV con verifica di troncamento tramite `snprintf`

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stdlib.h>` e `<string.h>` per formattare un record di catalogo libri in due buffer di diversa capienza usando `snprintf`. Leggi tre righe da `stdin`: la prima contiene il codice (stringa non vuota senza spazi, buffer `24` byte, estratta con `sscanf(riga, "%23s %c", codice, &extra) == 1`); la seconda contiene il titolo (stringa non vuota, buffer `80` byte, rimuovendo `'\n'` con `strcspn`); la terza contiene anno (`int` in `1900..2100`) e prezzo (`double >= 0.0`) validati con `sscanf(riga, "%d %lf %c", &anno, &prezzo, &extra) == 2`. In caso di errore di input stampa su `stderr` e restituisci `EXIT_FAILURE`. Definisci una funzione `int formatta_record(char dest[], size_t cap, const char codice[], const char titolo[], int anno, double prezzo)` che usa `snprintf` per produrre il formato `"%s;%s;%d;%.2f"` e restituisce il risultato di `snprintf`. In `main` calcola prima la lunghezza esatta richiesta con `snprintf(nullptr, 0, ...)`, poi formatta il record in `char completo[128]` e in `char anteprima[24]`. Verifica su ciascun buffer se `ris < 0` (errore) oppure `(size_t)ris >= sizeof(buffer)` (troncamento) e stampa lunghezza richiesta, stato e contenuto di `completo`, stato e contenuto di `anteprima` e, se l'anteprima è troncata, il numero di caratteri omessi (`req - (int)(sizeof(anteprima) - 1)`), esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- formattazione sicura in memoria con `snprintf`
- calcolo preventivo della lunghezza con `snprintf(nullptr, 0, ...)`
- verifica rigorosa di errore (`< 0`) e troncamento (`(size_t)ris >= capienza`)
- garanzia del terminatore nullo anche in caso di troncamento

**Domande guida**

1. Perché la condizione di troncamento dopo `snprintf` è `(size_t)scritti >= sizeof(buf)` e non `(size_t)scritti > sizeof(buf)`?
2. Che cosa restituisce `snprintf(nullptr, 0, ...)` e quale vantaggio offre rispetto a stimare la lunghezza a occhio?
3. Quando `anteprima` ha dimensione `24` byte ed è troncata, quanti caratteri utili contiene effettivamente al massimo e dove si trova il terminatore nullo?
4. Perché nell'estrazione del codice con `sscanf` scriviamo `%23s` invece di `%s` senza larghezza?

**Esempio di esecuzione**

```input
BK-104
Introduzione al linguaggio C
2026 29.5
```

```output
Lunghezza richiesta: 46
Completo (ok): BK-104;Introduzione al linguaggio C;2026;29.50
Anteprima (troncato): BK-104;Introduzione al 
Caratteri omessi in anteprima: 23
```

## 9.5 Buffer overflow e gestione sicura del testo

Nel capitolo 8 hai visto che il C non controlla automaticamente gli indici degli array. Quando questo problema riguarda un buffer di testo e una funzione scrive dati oltre l'ultimo byte riservato, si verifica un **buffer overflow**: una scrittura di dati oltre la fine della memoria riservata a un buffer, causa di comportamento indefinito e di gravi vulnerabilità di sicurezza.

In C23 un buffer overflow viola i limiti dell'oggetto allocato e provoca **comportamento indefinito**. Nei casi più fortunati il programma si chiude immediatamente; nei casi peggiori sovrascrive silenziosamente altre variabili vicine in memoria o permette a un attaccante di alterare il comportamento del programma fornendo un input costruito ad arte.

> **Attenzione — Errore da non scrivere mai**
> Il frammento seguente mostra un classico buffer overflow causato da `strcpy` senza controllo della capacità: provoca comportamento indefinito e **non va mai scritto** in un programma reale.

<!-- cod: id=9.5-b tipo=frammento -->
```c
// ERRORE GRAVE: comportamento indefinito (buffer overflow)!
char nome[6];
strcpy(nome, "Alessandra");  // Scrive 11 byte (incluso '\0') in un buffer da 6 byte
```

### Errori *off-by-one* sulle stringhe

Anche un solo byte in eccesso è già un buffer overflow. L'errore più frequente sulle stringhe è dimenticare il byte riservato al terminatore nullo `'\0'`:

- Un buffer `char codice[5]` può contenere una stringa di al massimo `4` caratteri utili (`indici 0..3`) più `'\0'` in posizione `4`.
- Se verifichi la capienza con `strlen(orig) <= sizeof(dest)` invece di `strlen(orig) < sizeof(dest)`, quando `strlen(orig)` è esattamente uguale a `sizeof(dest)` il terminatore nullo viene scritto fuori dai limiti del buffer.

### Righe di ingresso più lunghe del buffer di `fgets`

Usare `fgets(buf, (int)sizeof(buf), stdin)` impedisce il buffer overflow perché `fgets` legge al massimo `sizeof(buf) - 1` caratteri e aggiunge sempre `'\0'`. Tuttavia, che cosa accade se l'utente digita una riga più lunga di `sizeof(buf) - 1` caratteri?

`fgets` riempie il buffer con la prima parte della riga e **lascia tutti i caratteri rimanenti nello stream `stdin`**. Se non fai nulla, la chiamata successiva a `fgets` leggerà gli avanzi della riga precedente scambiandoli per una nuova riga!

Per gestire il caso in modo rigoroso procedi così:

1. Dopo `fgets`, cerca `'\n'` con `size_t len = strcspn(buf, "\n");`.
2. Se `buf[len] == '\n'`, l'intera riga è entrata nel buffer: sostituisci `buf[len] = '\0';` e hai finito.
3. Se `buf[len] != '\n'`, non è stato ancora letto `'\n'` (oppure il file è finito subito dopo). Leggi il prossimo carattere con `int c = getchar();`:
   - se `c == '\n' || c == EOF`, la riga era lunga **esattamente** `sizeof(buf) - 1` caratteri e non è stata troncata;
   - altrimenti la riga superava la capacità del buffer: continua a chiamare `getchar()` in un ciclo finché `c != '\n' && c != EOF` per svuotare completamente la parte eccedente prima della lettura successiva.

### Progettare funzioni sicure per il testo

La regola d'oro per prevenire i buffer overflow nel tuo codice è semplice: **ogni funzione che modifica una stringa di destinazione deve ricevere sempre la coppia `(char dest[], size_t capienza)`**, deve riservare almeno un byte per `'\0'` e deve restituire un `bool` (o un codice di stato) per informare il chiamante se l'operazione è riuscita o se è stata rifiutata per mancanza di spazio.

Riassumiamo una lista di controllo pratica da applicare ogni volta che lavori con stringhe in C:

1. Conta sempre il `+ 1` per `'\0'` nel dimensionare i buffer e nei controlli di capienza (`lunghezza < capienza`).
2. Leggi sempre le righe con `fgets`, mai con funzioni prive di limite, e svuota i residui di `stdin` se la riga eccede il buffer.
3. Specifica sempre la larghezza massima con `%Ns` in `sscanf` (dove `N = sizeof(buf) - 1`).
4. Preferisci `snprintf` e funzioni ausiliarie con capacità esplicita rispetto a `strcpy` e `strcat` non controllate.
5. Verifica sempre i valori di ritorno (`nullptr`, `bool`, `< 0`, `>= capienza`).

Esistono inoltre strumenti del compilatore, chiamati sanitizer, che rilevano automaticamente durante i test eventuali letture o scritture fuori dai limiti di un buffer (lo vedremo nel capitolo 11).

### Esempio guidato

Il programma seguente definisce tre funzioni ausiliarie — `svuota_se_troncata`, `copia_sicura` e `accoda_sicura` — che restituiscono un esito booleano (le due funzioni di modifica ricevono sempre la capacità esplicita del buffer di destinazione). Legge un nome utente in un piccolo buffer `char utente[12]`, svuota eventuali caratteri eccedenti e compone un'etichetta in `char tag[18]`.

<!-- cod: id=9.5-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool svuota_se_troncata(char buf[]) {
    size_t len = strcspn(buf, "\n");
    if (buf[len] == '\n') {
        buf[len] = '\0';
        return false;
    }
    int c = getchar();
    if (c == '\n' || c == EOF) {
        return false;
    }
    while (c != '\n' && c != EOF) {
        c = getchar();
    }
    return true;
}

bool copia_sicura(char dest[], size_t cap, const char orig[]) {
    if (cap == 0 || strlen(orig) >= cap) { return false; }
    strcpy(dest, orig);
    return true;
}

bool accoda_sicura(char dest[], size_t cap, const char orig[]) {
    if (cap == 0 || strlen(dest) + strlen(orig) >= cap) { return false; }
    strcat(dest, orig);
    return true;
}

int main(void) {
    char utente[12];
    char tag[18] = "";

    if (fgets(utente, (int)sizeof(utente), stdin) == nullptr) {
        fprintf(stderr, "Errore: input mancante.\n");
        return EXIT_FAILURE;
    }
    bool troncata = svuota_se_troncata(utente);
    printf("Utente letto: %s (troncato: %s)\n", utente, troncata ? "si" : "no");

    if (copia_sicura(tag, sizeof(tag), "USR:") &&
        accoda_sicura(tag, sizeof(tag), utente)) {
        printf("Tag pronto: %s\n", tag);
    } else {
        printf("Spazio insufficiente per comporre il tag.\n");
    }
    return EXIT_SUCCESS;
}
```

```input
massimiliano_rossi
```

```output
Utente letto: massimilian (troncato: si)
Tag pronto: USR:massimilian
```

Osserva come ogni operazione resta dentro i limiti garantiti:

- `utente` ha capacità `12` byte, quindi `fgets` legge al massimo `11` caratteri (`"massimilian"`) più `'\0'`.
- `svuota_se_troncata` scopre che `'\n'` non è presente in `utente`, legge il carattere successivo (`'o'`, diverso da `'\n'` e da `EOF`), consuma il resto della riga fino a `'\n'` e restituisce `true` per segnalare il troncamento. Una seconda `fgets` ripartirebbe ora in modo pulito dalla riga successiva.
- `copia_sicura` e `accoda_sicura` controllano sempre `cap == 0` e che la lunghezza totale resti strettamente minore di `cap` (lasciando spazio per `'\0'`) prima di chiamare `strcpy` e `strcat`. Qui `"USR:"` (4 byte) + `"massimilian"` (11 byte) = `15 < 18`, quindi il tag entra in `tag` con piena sicurezza.

> **Approfondimento — Che cosa succede in memoria durante un buffer overflow**
> Immagina due variabili locali collocate una accanto all'altra in memoria: un buffer `char buf[8]` e un flag `int amministratore = 0;`.
>
> ```text
> Indirizzi crescenti --->
> +-----+-----+-----+-----+-----+-----+-----+-----+-----------------+
> |  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  | amministratore  |
> +-----+-----+-----+-----+-----+-----+-----+-----+-----------------+
> | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' |'\0'| ...  |
> +-----+-----+-----+-----+-----+-----+-----+-----+-----------------+
> |<------------ char buf[8] (8 byte) ----------->|<-- SOVRASCRITTO |
> ```
>
> Scrivere `"ABCDEFGHI"` in `buf` senza controllare la capacità supera gli `8` byte riservati e può invadere i byte della variabile adiacente `amministratore`, trasformando il suo valore da `0` in un numero diverso da zero (vero in un `if`!). La disposizione esatta delle variabili dipende dal compilatore e dalle ottimizzazioni, quindi non puoi mai prevedere quale dato verrà corrotto: l'unica difesa affidabile è prevenire sempre il buffer overflow nel codice.

### Esercizio 9.5 — Raccolta sicura di nomi in buffer limitati contro il buffer overflow

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stdlib.h>` e `<string.h>` per leggere una sequenza di nomi di città da `stdin` (uno per riga, fino alla fine dell'input) usando un piccolo buffer di ingresso `char riga[16];` (al massimo `15` caratteri utili per nome) e comporre un elenco in un buffer di uscita di capacità fissa `char elenco[40] = "";` con voci separate da `" | "`. Dichiara prima di `main` i prototipi di due funzioni sicure: `int leggi_riga_limitata(char buf[], size_t cap)` (usa `fgets`: restituisce `0` alla fine dell'input; se la riga entra interamente nel buffer — incluso il caso limite di esattamente `cap - 1` caratteri seguiti da `'\n'` o `EOF` — rimuove `'\n'` e restituisce `1`; se la riga supera `cap - 1` caratteri, svuota tutti i caratteri residui fino a `'\n'` o `EOF` con `getchar()` e restituisce `2`) e `bool accoda_voce(char dest[], size_t cap, const char voce[], const char sep[])` (verifica in anticipo che `strlen(dest) + (dest[0] != '\0' ? strlen(sep) : 0) + strlen(voce) < cap`; solo se c'è spazio per entrambi accoda prima l'eventuale separatore e poi `voce` e restituisce `true`, altrimenti lascia `dest` intatto e restituisce `false`). In `main` ignora le righe vuote, conta voci inserite, voci omesse per capienza e righe troncate in ingresso (anche se poi omesse per capienza), quindi stampa il riepilogo finale esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- prevenzione del buffer overflow con controllo preventivo della capacità
- svuotamento dello stream residuo con `getchar()` dopo una riga troncata da `fgets`
- caso limite della riga lunga esattamente `cap - 1` caratteri
- accodamento atomico di separatore e voce senza lasciare separatori orfani

**Domande guida**

1. Che cosa succederebbe alla lettura della riga successiva se `leggi_riga_limitata` non svuotasse i caratteri eccedenti lasciati in `stdin` da `fgets`?
2. Come distingue `leggi_riga_limitata` una riga lunga esattamente `15` caratteri seguiti da `'\n'` da una riga lunga `16` o più caratteri?
3. Perché `accoda_voce` deve verificare la capienza complessiva di separatore più voce prima di modificare `dest`?
4. Qual è la lunghezza massima possibile di `elenco` quando la sua capacità è `40` byte?

**Esempio di esecuzione**

```input
Torino
Milano
Reggio Emilia Centro
Rho
Napoli
Bologna
```

```output
Voci inserite: 4
Voci omesse per capienza: 2
Righe troncate in ingresso: 1
Elenco (39/39): Torino | Milano | Reggio Emilia C | Rho
```

## Riepilogo

- Una **stringa** in C è un array di `char` chiuso dal **terminatore nullo** `'\0'` (di valore `0`, distinto dalla cifra `'0'` e dalla stringa `"0"`). La capacità del buffer è `sizeof(s)` byte, mentre la lunghezza logica è il numero di caratteri prima del primo `'\0'` (al più `sizeof(s) - 1`). Un array di `char` privo di `'\0'` non è una stringa valida.
- Le funzioni di `<string.h>` richiedono stringhe terminate da `'\0'`: `strlen` calcola la lunghezza (non va richiamata nella condizione di un `for`); `strcmp` e `strncmp` confrontano lessicograficamente su `unsigned char` restituendo `< 0`, `0` o `> 0`; `strchr`, `strrchr`, `strstr` e `strpbrk` cercano caratteri o sottostringhe restituendo `nullptr` se non li trovano (l'uso diretto del puntatore restituito lo vedremo nel capitolo 10); `strcspn` e `strspn` misurano prefissi (con `s[strcspn(s, "\n")] = '\0'` si rimuove il ritorno a capo di `fgets`).
- Le funzioni `strcpy`, `strncpy`, `strcat` e `strncat` non ammettono sovrapposizioni in memoria e richiedono sempre un controllo preventivo della capacità. Ricorda che `strncpy` non garantisce `'\0'` finale se la sorgente ha lunghezza almeno `n`, mentre `strncat` riceve come terzo argomento il numero massimo di caratteri da aggiungere e richiede `strlen(dest) + n + 1` byte totali.
- Le funzioni di `<ctype.h>` (`isalpha`, `isdigit`, `isalnum`, `isspace`, `isupper`, `islower`, `isxdigit`, `ispunct`, `isprint`, `tolower`, `toupper`) richiedono sempre il cast `(unsigned char)` quando ricevono un `char`, altrimenti un `char` negativo diverso da `EOF` provoca comportamento indefinito. Le funzioni `is*` restituiscono `0` o un intero diverso da zero (non necessariamente `1`).
- `snprintf(dest, capienza, formato, ...)` scrive al massimo `capienza - 1` caratteri garantendo `'\0'` (per `capienza > 0`). Si rilevano errori o troncamenti con `ris < 0 || (size_t)ris >= capienza`, e `snprintf(nullptr, 0, ...)` calcola la lunghezza richiesta senza scrivere nulla (lo combineremo con `malloc` nel capitolo 11).
- Un **buffer overflow** è una scrittura oltre la fine del buffer e provoca comportamento indefinito. Per evitarlo, passa sempre `(char dest[], size_t capienza)` alle funzioni che modificano stringhe, riserva sempre un byte per `'\0'` e svuota i residui di `stdin` con `getchar()` quando una riga supera il buffer di `fgets` (nel capitolo 11 vedrai i sanitizer per rilevare automaticamente gli sforamenti).

## Errori comuni

- **Dimenticare il byte per il terminatore nullo `'\0'`**: dichiarare `char s[4] = "ciao";` o controllare `strlen(orig) <= sizeof(dest)` invece di `<` lascia la stringa priva di `'\0'` o causa un buffer overflow di un byte (*off-by-one*).
- **Confrontare o copiare stringhe con `==` o `=`**: scrivere `s1 == s2` non confronta il contenuto delle due stringhe e `s1 = s2` è rifiutato dal compilatore; usa `strcmp` per confrontare e copie controllate (`snprintf` o controllo di capienza + `strcpy`) per copiare.
- **Passare un `char` direttamente a `<ctype.h>` senza cast `(unsigned char)`**: scrivere `isalpha(s[i])` o `tolower(s[i])` provoca comportamento indefinito sulle piattaforme in cui `char` è con segno se il byte è negativo; scrivi sempre `(unsigned char)s[i]`.
- **Chiamare `strlen(s)` nella condizione di un ciclo `for`**: scrivere `for (size_t i = 0; i < strlen(s); ++i)` ricalcola inutilmente la lunghezza a ogni iterazione; salvala prima del ciclo in una variabile `size_t` oppure controlla `s[i] != '\0'`.
- **Dimenticare il `'\n'` conservato da `fgets`**: una riga letta da tastiera termina quasi sempre con `'\n'`, facendo fallire confronti con `strcmp(riga, "ok")`; rimuovilo subito con `riga[strcspn(riga, "\n")] = '\0';`.
- **Usare male `strncat` o fidarsi di `strncpy`**: passare `sizeof(dest)` come terzo argomento a `strncat` (invece dello spazio residuo `sizeof(dest) - strlen(dest) - 1`) causa buffer overflow, e `strncpy` non aggiunge `'\0'` quando la sorgente raggiunge o supera il limite `n`.
- **Controllare il troncamento di `snprintf` con `scritti > sizeof(buf)`**: se `scritti` è esattamente uguale a `sizeof(buf)`, manca comunque il byte per `'\0'` e il testo è stato troncato; usa sempre `scritti < 0 || (size_t)scritti >= sizeof(buf)`.

## Prima di proseguire

- [ ] So spiegare che cos'è una stringa in C, distinguendo capacità del buffer (`sizeof`) e lunghezza logica fino a `'\0'`, e so scorrere e modificare una stringa manualmente.
- [ ] So usare `strlen`, `strcmp`, `strncmp`, `strchr`, `strrchr`, `strstr`, `strpbrk`, `strcspn`, `strspn`, `strcpy`, `strncpy`, `strcat` e `strncat` evitando errori di confronto, di capacità e di terminazione.
- [ ] So classificare e convertire caratteri con `<ctype.h>` applicando sempre il cast `(unsigned char)` e controllando correttamente il valore di ritorno delle funzioni `is*`.
- [ ] So formattare stringhe in modo sicuro con `snprintf`, verificare errori e troncamenti e calcolare preventivamente la lunghezza richiesta con `snprintf(nullptr, 0, ...)`.
- [ ] So prevenire i buffer overflow gestendo le righe troppo lunghe dopo `fgets` e progettando funzioni che ricevono sempre la capacità esplicita del buffer di destinazione.
