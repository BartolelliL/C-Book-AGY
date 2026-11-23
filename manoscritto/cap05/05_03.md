## 5.3 Controllare gli errori di input e la fine dello stream

Negli esempi delle prime due sotto-sezioni abbiamo stampato sia i risultati sia i messaggi di errore con `printf`, e abbiamo restituito `0` oppure `1` da `main`. Questa scelta funziona per i primi esperimenti, ma ha due limiti seri nei programmi reali: mescola i messaggi diagnostici con i dati prodotti dal programma e usa codici numerici grezzi per comunicare l'esito al sistema operativo. Inoltre, c'è un caso sottile che `sscanf(riga, "%d", &valore) == 1` lascia passare senza protestare: se l'utente digita `28abc`, `sscanf` legge `28`, si ferma davanti alla `'a'` e restituisce `1` come se l'input fosse valido.

### I tre stream standard e `fprintf`

Quando un programma C si avvia, la libreria standard apre automaticamente tre stream distinti, dichiarati in `<stdio.h>`:

- `stdin`: lo stream di ingresso standard (di norma la tastiera);
- `stdout`: lo stream di uscita normale, destinato ai risultati del programma;
- `stderr`: lo stream dedicato ai messaggi di errore e diagnostici.

La funzione `printf` scrive sempre su `stdout`. Per scegliere esplicitamente su quale stream scrivere si usa `fprintf(stream, formato, ...)`, che funziona in modo identico a `printf` ma accetta come primo argomento lo stream di destinazione:

<!-- cod: id=5.3-b tipo=frammento -->
```c
fprintf(stdout, "Risultato: %d\n", risultato);
fprintf(stderr, "Errore: formato non valido.\n");
```

Separare `stdout` da `stderr` è una convenzione fondamentale su tutti i sistemi operativi (Linux, macOS e Windows): sul terminale entrambi appaiono sullo schermo, ma quando ridirigi l'uscita del programma verso un file o un altro programma, i dati puliti restano su `stdout` mentre eventuali errori rimangono visibili su `stderr`.

### Codici di uscita portabili: `EXIT_SUCCESS` ed `EXIT_FAILURE`

Per segnalare al sistema operativo se il programma è terminato correttamente oppure no, l'header `<stdlib.h>` definisce due costanti portabili: `EXIT_SUCCESS` ed `EXIT_FAILURE`. Usarle nel `return` di `main` rende immediato il significato dell'uscita e garantisce la portabilità su ogni piattaforma:

<!-- cod: id=5.3-c tipo=frammento -->
```c
#include <stdio.h>
#include <stdlib.h>

// ...
return EXIT_FAILURE;  // in caso di errore
// ...
return EXIT_SUCCESS;  // in caso di esito corretto
```

Lo standard C23 definisce l'esistenza di `stdin`, `stdout`, `stderr` e il significato portabile di `EXIT_SUCCESS` ed `EXIT_FAILURE`. Sono invece **dipendenti dall'implementazione** sia il valore numerico concreto di `EXIT_FAILURE` (spesso `1`, ma non obbligatoriamente) sia le modalità di buffering predefinite degli stream (per esempio, `stderr` di norma non trattiene il testo in attesa del ritorno a capo, così i messaggi d'errore compaiono subito).

### Classificare tutti gli errori di input

Quando leggi un numero da una riga, gli errori possibili appartengono a quattro categorie distinte, che conviene verificare sempre nello stesso ordine:

1. **Fine dell'input**: `fgets(riga, (int)sizeof(riga), stdin) == nullptr`. L'utente ha segnalato la fine dello stream prima che il programma potesse leggere la riga. Da tastiera, questa condizione si genera premendo `Ctrl+D` (all'inizio di una riga vuota) su Linux e macOS, oppure `Ctrl+Z` seguito da Invio su Windows.
2. **Riga vuota o testo non numerico**: `sscanf` restituisce `EOF` (riga vuota o di soli spazi) oppure un conteggio minore del numero di valori attesi (per esempio l'utente ha digitato `ciao` al posto di un numero).
3. **Caratteri spuri in coda**: l'utente ha digitato un numero valido seguito da testo non ammesso, come `28abc` oppure `28 30` quando ci si aspettava un solo intero.
4. **Valore fuori intervallo**: il numero è stato estratto correttamente, ma viola le regole del problema (per esempio un voto universitario pari a `35` o `-2`).

Per intercettare sia la categoria 2 sia la categoria 3 con un unico controllo, esiste un idioma semplice ed efficace: aggiungere `" %c"` in fondo alla stringa di formato di `sscanf` insieme a una variabile `char` di appoggio (spesso chiamata `extra`), e verificare che `sscanf` restituisca **esattamente** il numero di valori validi attesi:

<!-- cod: id=5.3-d tipo=frammento -->
```c
int voto = 0;
char extra = '\0';

if (sscanf(riga, "%d %c", &voto, &extra) != 1) {
    fprintf(stderr, "Errore: inserisci un solo numero intero.\n");
    return EXIT_FAILURE;
}
```

Vediamo che cosa accade nei diversi casi, secondo le regole definite dallo standard C23:

- se `riga` è `"  28  \n"`, `%d` legge `28`, lo spazio nella stringa di formato consuma gli spazi e `'\n'` fino alla fine della riga, `%c` non trova nessun altro carattere e `sscanf` restituisce `1` (input accettato);
- se `riga` è `"28abc\n"`, `%d` legge `28`, `%c` legge `'a'` e `sscanf` restituisce `2 != 1` (input rifiutato);
- se `riga` è `"28 99\n"`, `%d` legge `28`, lo spazio salta lo spazio, `%c` legge `'9'` e `sscanf` restituisce `2 != 1` (input rifiutato);
- se `riga` è `"abc\n"` oppure `"\n"`, `sscanf` restituisce `0` oppure `EOF`, entrambi diversi da `1` (input rifiutato).

Solo dopo aver verificato che `fgets` non ha restituito `nullptr` e che `sscanf` ha restituito esattamente il conteggio atteso, controlli l'intervallo del valore estratto. Rispettare quest'ordine impedisce di valutare condizioni su variabili che non sono state aggiornate.

> **Se vieni da Python** — In Python per scrivere un messaggio di errore su `stderr` passi l'argomento `file=sys.stderr` alla funzione `print()`. In C usi `fprintf(stderr, ...)` e restituisci `EXIT_FAILURE` o `EXIT_SUCCESS` da `main`.

### Esempio guidato

Il programma seguente registra un voto universitario: legge sulla prima riga un intero tra `18` e `30` e sulla seconda riga l'indicazione di lode (`S`/`s` per sì, `N`/`n` per no). Rifiuta la fine dell'input, i caratteri spuri in coda (come `28abc`) e le combinazioni non valide (per esempio la lode con un voto inferiore a `30`), inviando ogni errore su `stderr` con `EXIT_FAILURE` e stampando la conferma su `stdout` con `EXIT_SUCCESS`.

<!-- cod: id=5.3-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char riga[128];
    int voto = 0;
    char lode = '\0';
    char extra = '\0';

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr) {
        fprintf(stderr, "Errore: fine dell'input durante la lettura del voto.\n");
        return EXIT_FAILURE;
    }
    if (sscanf(riga, "%d %c", &voto, &extra) != 1) {
        fprintf(stderr, "Errore: formato del voto non valido.\n");
        return EXIT_FAILURE;
    }
    if (voto < 18 || voto > 30) {
        fprintf(stderr, "Errore: il voto deve essere compreso tra 18 e 30.\n");
        return EXIT_FAILURE;
    }

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr) {
        fprintf(stderr, "Errore: fine dell'input durante la lettura della lode.\n");
        return EXIT_FAILURE;
    }
    if (sscanf(riga, " %c %c", &lode, &extra) != 1) {
        fprintf(stderr, "Errore: indica la lode con un solo carattere (S o N).\n");
        return EXIT_FAILURE;
    }
    if (lode != 'S' && lode != 's' && lode != 'N' && lode != 'n') {
        fprintf(stderr, "Errore: codice lode non riconosciuto.\n");
        return EXIT_FAILURE;
    }
    if ((lode == 'S' || lode == 's') && voto != 30) {
        fprintf(stderr, "Errore: la lode è ammessa solo con voto 30.\n");
        return EXIT_FAILURE;
    }

    bool con_lode = (lode == 'S' || lode == 's');
    fprintf(stdout, "Esame registrato: %d%s\n", voto, con_lode ? " e lode" : "");
    return EXIT_SUCCESS;
}
```

```input
30
S
```

```output
Esame registrato: 30 e lode
```

Esamina la sequenza dei controlli:

- Ogni lettura verifica nell'ordine: fine dell'input (`fgets == nullptr`), formato senza caratteri extra (`sscanf(...) != 1`) e validità del dominio (`voto < 18 || voto > 30`, carattere `lode` ammesso, coerenza tra lode e voto `30`).
- Anche per il carattere `lode` è usato lo stesso trucco: `" %c %c"` salta eventuali spazi iniziali, legge il carattere in `lode` e verifica che dopo eventuali altri spazi non ci sia un secondo carattere da leggere in `extra`. Così `"S"` e `"  s  "` vengono accettati, mentre `"SI"` viene scartato perché `sscanf` restituisce `2`.
- Tutti i rami di errore scrivono su `stderr` e interrompono subito il programma con `return EXIT_FAILURE;`. Solo se ogni controllo ha successo il programma scrive su `stdout` e restituisce `EXIT_SUCCESS`.

> **Approfondimento — Ridirezione da riga di comando e separazione di `stdout` e `stderr`**
> Da terminale puoi salvare l'uscita di un programma in un file usando l'operatore `>` (per esempio `./programma > risultato.txt`). Quel comando ridirige soltanto `stdout`: tutto ciò che il programma scrive con `fprintf(stdout, ...)` o `printf(...)` finisce nel file, mentre i messaggi inviati a `stderr` compaiono comunque sul terminale. Se invece stampassi gli errori su `stdout`, un errore di input finirebbe silenziosamente dentro `risultato.txt` al posto dei dati veri, corrompendo il file o mandando in errore il programma successivo che dovesse leggerlo.

### Esercizio 5.3 — Validatore di prenotazione per una sala conferenze

**Descrizione**

Scrivi un programma C che includa `<stdio.h>` e `<stdlib.h>` e legga da `stdin` due righe con `fgets`: la prima contiene il numero di fila (`int` compreso tra `1` e `20` inclusi), la seconda il numero di posto (`int` compreso tra `1` e `15` inclusi). Per ciascuna riga controlla nell'ordine: la fine dell'input (`fgets == nullptr`), la validità del formato rifiutando eventuali caratteri extra dopo il numero tramite l'idioma `"%d %c"` con una variabile `char` di appoggio, e l'appartenenza all'intervallo consentito. In qualsiasi caso di errore scrivi un messaggio descrittivo su `stderr` tramite `fprintf` e termina restituendo `EXIT_FAILURE`. Se entrambi i dati sono validi, stampa su `stdout` con `fprintf` la conferma della prenotazione, il settore (`Platea anteriore` per file `1..5`, `Platea centrale` per `6..12`, `Platea posteriore` per `13..20`) e la posizione (`Corridoio` per i posti `1` e `15`, `Interno` per gli altri), quindi restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- stream `stdin`, `stdout` e `stderr`
- scrittura di errori su `stderr` con `fprintf`
- codici di uscita `EXIT_SUCCESS` ed `EXIT_FAILURE` (`<stdlib.h>`)
- rilevamento di caratteri extra in coda con `"%d %c"`
- distinzione tra fine dell'input, errore di formato e valore fuori intervallo

**Domande guida**

1. Perché conviene inviare i messaggi di errore su `stderr` con `fprintf` invece di stamparli su `stdout` con `printf`?
2. Come riesce la stringa di formato `"%d %c"` in `sscanf` ad accettare `"  12  "` ma a rifiutare `"12abc"` o `"12 3"`?
3. In quale ordine conviene controllare fine dell'input, formato con `sscanf` e intervallo numerico per evitare di leggere variabili non aggiornate?
4. Quale header standard definisce le costanti `EXIT_SUCCESS` ed `EXIT_FAILURE` e perché è preferibile usarle al posto di numeri arbitrari?

**Esempio di esecuzione**

```input
4
1
```

```output
Prenotazione confermata: fila 4, posto 1
Settore: Platea anteriore
Posizione: Corridoio
```
