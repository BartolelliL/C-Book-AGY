# Capitolo 6 — Ripetizioni

> **In questo capitolo imparerai a:**
> - Scegliere il ciclo adatto (`while`, `do-while` o `for`) in base alla condizione di arresto
> - Controllare il flusso dentro un ciclo con `break` e `continue` senza creare codice confuso
> - Scrivere cicli annidati per elaborare tabelle, griglie e sequenze
> - Formulare l'invariante di un ciclo per verificarne correttezza e terminazione

> **Ti servono:** i capitoli 1–5, in particolare operatori relazionali e logici, valutazione a corto circuito, `if`/`else`, `switch`, `fgets`, `sscanf`, `getchar`, `putchar`, `fprintf`, `nullptr`, `EOF`, `EXIT_SUCCESS` ed `EXIT_FAILURE`.

Nel capitolo precedente hai imparato a leggere una riga con `fgets` o un singolo carattere con `getchar`, ma i tuoi programmi riuscivano a elaborare soltanto un numero fisso e minuscolo di dati. Se volessi sommare mille importi, contare le righe di un testo di lunghezza sconosciuta o chiedere di nuovo un valore finché l'utente non inserisce un numero valido, copiare e incollare le stesse istruzioni non sarebbe né pratico né possibile: spesso non sai nemmeno in anticipo quanti dati arriveranno dallo stream di ingresso.

Per risolvere problemi del genere servono le istruzioni di ripetizione. Il C mette a disposizione tre costrutti dedicati — `while`, `do-while` e `for` — insieme alle istruzioni `break` e `continue` per gestire uscite anticipate o casi da saltare. Saper scegliere il costrutto giusto rende il codice più chiaro e riduce drasticamente gli errori sui casi limite, come un input vuoto o un conteggio sfasato di un'unità.

In questo capitolo imparerai prima a costruire cicli singoli per elaborare sequenze di lunghezza arbitraria fino alla fine dell'input, poi a combinare cicli annidati per lavorare su tabelle e griglie. Infine vedrai come ragionare sulla correttezza e sulla terminazione di un ciclo usando gli invarianti di ciclo, uno strumento semplice ma prezioso che ti accompagnerà in tutto il resto del libro.

## 6.1 Il ciclo `while`

Nel capitolo 5 hai visto come leggere una singola riga con `fgets` o un singolo carattere con `getchar`. Quando però un programma deve elaborare tutti i dati presenti in ingresso — un testo di cento righe, un elenco di spese, una serie di misurazioni — non conosci quasi mai in anticipo quanti elementi arriveranno. Serve un modo per dire al computer: "finché questa condizione è vera, ripeti questo blocco di istruzioni".

Nel linguaggio C questo meccanismo prende il nome di **ciclo** (*loop*): un costrutto di controllo che ripete un blocco di istruzioni finché una condizione rimane vera. Ogni singola esecuzione del corpo di un ciclo si chiama **iterazione** (*iteration*).

Il costrutto di ripetizione più semplice ed essenziale è il ciclo `while`:

<!-- cod: id=6.1-c tipo=frammento -->
```c
while (condizione) {
    // corpo del ciclo
}
```

Il ciclo `while` esegue un *controllo in testa*: prima di entrare nel corpo, valuta `condizione`. Se il risultato è diverso da zero (vero), esegue tutte le istruzioni racchiuse tra le parentesi graffe e poi torna in cima a rivalutare `condizione`. Se invece `condizione` vale zero (falso), il ciclo termina immediatamente e il flusso di controllo prosegue con la prima istruzione dopo la graffa di chiusura. Poiché il controllo avviene prima della prima iterazione, se la condizione è già falsa all'inizio, il corpo del ciclo viene eseguito **zero volte**. Questa semantica è pienamente definita dallo standard C23.

```text
          +----------------------------+
          |                            |
          v                            |
   [ condizione ] --(vero / != 0)--> [ corpo del ciclo ]
          |
     (falso / 0)
          |
          v
   [ istruzione successiva ]
```

Affinché un ciclo `while` funzioni correttamente e termini, devono essere sempre presenti tre elementi chiari:

1. **Inizializzazione prima del ciclo**: le variabili che compaiono nella condizione devono avere un valore definito prima di raggiungere `while`.
2. **Condizione di permanenza**: un'espressione che resta vera finché c'è lavoro da svolgere e diventa falsa quando il compito è concluso.
3. **Aggiornamento verso la terminazione**: almeno un'operazione nel corpo (o nella condizione stessa, come una lettura dallo stream) deve modificare lo stato in modo da avvicinare la condizione al valore falso.

Se dimentichi l'aggiornamento, oppure aggiorni la variabile nella direzione sbagliata, la condizione resta vera per sempre e ottieni un *ciclo infinito*: il programma non termina da solo e dovrai interromperlo manualmente dal terminale (di solito con `Ctrl+C`).

### Leggere fino alla fine dell'input

L'uso più frequente di `while` con l'ingresso standard consiste nel leggere dati fino alla **fine dell'input**, senza dover conoscere in anticipo il numero di righe o di caratteri. Esistono due idiomi fondamentali, entrambi basati sulle funzioni introdotte nel capitolo 5:

- **Lettura riga per riga con `fgets`**:
  ```text
  while (fgets(riga, (int)sizeof(riga), stdin) != nullptr) { ... }
  ```
  A ogni controllo di testa, `fgets` tenta di leggere la riga successiva da `stdin` dentro il buffer `riga`. Finché riesce a leggere qualcosa, restituisce `riga` (che è diverso da `nullptr`) ed esegue il corpo del ciclo. Quando lo stream termina o si verifica un errore di lettura, `fgets` restituisce `nullptr` e il ciclo si chiude in modo pulito.

- **Lettura carattere per carattere con `getchar`**:
  ```text
  while ((c = getchar()) != EOF) { ... }
  ```
  Qui `c` **deve** avere tipo `int` (mai `char`), per il motivo visto nel capitolo 5: solo `int` può rappresentare tutti i caratteri possibili e il valore negativo `EOF` senza ambiguità. A ogni iterazione `getchar()` legge il prossimo carattere, lo assegna a `c` e il risultato dell'assegnamento viene confrontato con `EOF`. Quando lo stream finisce, `getchar()` restituisce `EOF` e il ciclo termina. Le regole di precedenza tra `=` e `!=` e la valutazione della condizione sono definite dallo standard C23.

> **C23** — La parola chiave `nullptr` è stata introdotta con il C23. Se compili con uno standard precedente (C17 o C11), sostituisci `nullptr` con la macro `NULL` definita in `<stdio.h>` e `<stdlib.h>`.

### Contatori, accumulatori, minimo e massimo

Molti problemi su sequenze di lunghezza arbitraria si risolvono combinando quattro schemi ricorrenti attorno a un ciclo `while`:

- **Contatore**: una variabile intera inizializzata a `0` prima del ciclo (per esempio `int conteggio = 0;`) e incrementata con `++conteggio;` ogni volta che incontri un elemento o un evento da contare.
- **Accumulatore**: una variabile numerica inizializzata all'elemento neutro dell'operazione (`0` o `0.0` per una somma, `1` per un prodotto) e aggiornata nel corpo (per esempio `somma += valore;`).
- **Minimo e massimo**: a differenza di somma e conteggio, non puoi quasi mai inizializzare `minimo` o `massimo` a `0`: se tutti i numeri letti fossero positivi (per esempio `12`, `18`, `25`), un `minimo` inizializzato a `0` rimarrebbe erroneamente `0`. La soluzione sicura consiste nell'inizializzare `minimo` e `massimo` con il **primo elemento valido** (riconoscibile perché `conteggio == 0`), aggiornandoli poi con `if (valore < minimo)` e `if (valore > massimo)` sugli elementi successivi.
- **Caso di zero elementi letti**: poiché il ciclo `while` può compiere zero iterazioni (input vuoto), dopo il ciclo controlla sempre se `conteggio == 0` prima di stampare minimo, massimo o media. Dividere `somma / conteggio` quando `conteggio` vale `0` provocherebbe una divisione per zero (comportamento indefinito per gli interi, oppure valori speciali come `NaN` in virgola mobile).

### L'errore del punto e virgola dopo `while`

Un errore tanto subdolo quanto frequente è scrivere un punto e virgola subito dopo la parentesi chiusa di `while`:

<!-- cod: id=6.1-d tipo=frammento -->
```c
int passi = 0;
while (passi < 5); {  // ERRORE: il punto e virgola chiude un ciclo a corpo vuoto!
    ++passi;
}
```

In C un punto e virgola da solo è un'*istruzione vuota*. Il compilatore interpreta quel codice come "finché `passi < 5`, non fare nulla": poiché `passi` resta `0`, il ciclo diventa infinito e il blocco `{ ++passi; }` tra parentesi graffe non viene mai raggiunto. Controlla sempre che tra `while (condizione)` e `{` non compaia mai un `;`.

### Esempio guidato

Il primo programma legge un testo qualsiasi da `stdin` carattere per carattere con `while ((c = getchar()) != EOF)` e conta i caratteri totali, le righe (contando i `'\n'`) e le cifre decimali (`'0'..'9'`).

<!-- cod: id=6.1-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int c = 0;
    int caratteri = 0;
    int righe = 0;
    int cifre = 0;

    while ((c = getchar()) != EOF) {
        ++caratteri;
        if (c == '\n') {
            ++righe;
        }
        if (c >= '0' && c <= '9') {
            ++cifre;
        }
    }

    printf("Caratteri totali: %d\n", caratteri);
    printf("Righe complete (\\n): %d\n", righe);
    printf("Cifre decimali: %d\n", cifre);
    return EXIT_SUCCESS;
}
```

```input
Riga 1: 42
Riga 2: 108
```

```output
Caratteri totali: 22
Righe complete (\n): 1
Cifre decimali: 7
```

Analizziamo come lavora questo programma:

- Prima del ciclo inizializziamo `c` e i tre contatori (`caratteri`, `righe`, `cifre`) a `0`. Anche se l'input fosse completamente vuoto, il programma non userebbe mai variabili non inizializzate e stamperebbe tre zeri.
- La condizione `(c = getchar()) != EOF` legge il carattere successivo, lo salva in `c` (di tipo `int`) e controlla che non sia la fine dell'input.
- Per ogni carattere letto incrementiamo `caratteri` (compresi gli spazi e i `'\n'`), poi usiamo due `if` indipendenti per contare i ritorni a capo (`'\n'`, che delimitano le righe complete terminate da Invio) e le cifre decimali (sfruttando il fatto che in C i codici di `'0'..'9'` sono contigui).

Il secondo esempio mostra invece la lettura riga per riga con `fgets` e `sscanf`: legge una sequenza di importi in euro fino alla fine dell'input, controllando sia gli errori di formato sia il caso di sequenza vuota.

<!-- cod: id=6.1-b tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char riga[128];
    int conteggio = 0;
    double totale = 0.0;

    while (fgets(riga, (int)sizeof(riga), stdin) != nullptr) {
        double importo = 0.0;
        char extra = '\0';
        if (sscanf(riga, "%lf %c", &importo, &extra) != 1) {
            fprintf(stderr, "Errore: importo non valido.\n");
            return EXIT_FAILURE;
        }
        totale += importo;
        ++conteggio;
    }

    if (conteggio == 0) {
        printf("Nessun importo inserito.\n");
        return EXIT_SUCCESS;
    }

    printf("Importi letti: %d\n", conteggio);
    printf("Totale: %.2f euro\n", totale);
    return EXIT_SUCCESS;
}
```

```input
12.50
7.25
20.25
```

```output
Importi letti: 3
Totale: 40.00 euro
```

Qui `fgets` legge una riga alla volta nel buffer `riga` e termina automaticamente quando `stdin` si chiude. Dentro il ciclo verifichiamo il formato con `"%lf %c"` per rifiutare righe malformate o caratteri extra in coda, esattamente come hai imparato nel capitolo 5. All'uscita dal ciclo, il controllo `if (conteggio == 0)` gestisce in modo pulito il caso limite di input vuoto.

> **Approfondimento — Perché le parentesi attorno a `(c = getchar())` sono obbligatorie**
> Che cosa succederebbe se scrivessi `while (c = getchar() != EOF)` dimenticando le parentesi interne? Per le regole di precedenza degli operatori del C (capitolo 3), l'operatore `!=` ha precedenza maggiore rispetto all'assegnamento `=`. Il compilatore raggrupperebbe quindi l'espressione come `while (c = (getchar() != EOF))`: prima confronta il carattere letto con `EOF`, ottenendo `1` (vero) oppure `0` (falso), e poi assegna `1` o `0` a `c`! Il ciclo continuerebbe a leggere fino alla fine dello stream, ma dentro il corpo `c` varrebbe sempre `1` invece del carattere letto. Le parentesi in `(c = getchar()) != EOF` forzano prima l'assegnamento del carattere a `c` e solo dopo il confronto con `EOF`.

### Esercizio 6.1 — Statistiche delle temperature giornaliere

**Descrizione**

Scrivi un programma C che legga da `stdin` una sequenza di lunghezza arbitraria di temperature in gradi Celsius (`double`, una per riga) usando un ciclo `while (fgets(...) != nullptr)`. Per ogni riga verifica il formato con `sscanf(riga, "%lf %c", &temp, &extra) != 1`: in caso di formato non valido stampa un messaggio di errore su `stderr` e termina con `EXIT_FAILURE`. Durante il ciclo aggiorna il numero di letture, la temperatura minima, la temperatura massima, la somma e il conteggio dei giorni con gelo (`temp <= 0.0`). Al termine dello stream, se non è stata letta alcuna temperatura stampa `Nessuna temperatura inserita.` e restituisci `EXIT_SUCCESS`; altrimenti stampa letture valide, minima, massima, media (tutte con due cifre decimali) e giorni con gelo esattamente come nell'esempio di esecuzione, restituendo `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- ciclo `while` con controllo in testa
- lettura fino alla fine dell'input con `fgets` e `nullptr`
- inizializzazione sicura di minimo e massimo al primo elemento
- gestione del caso limite di input vuoto (0 letture)

**Domande guida**

1. Perché non è corretto inizializzare la temperatura minima a `0.0` prima di iniziare il ciclo `while`?
2. Come puoi riconoscere all'interno del ciclo di star elaborando la prima temperatura valida per inizializzare minima e massima?
3. Che cosa succederebbe se provassi a calcolare la media senza verificare prima che il conteggio sia maggiore di zero?
4. Quando termina naturalmente il ciclo `while` basato su `fgets`?

**Esempio di esecuzione**

```input
12.5
-1.0
0.0
8.5
```

```output
Letture valide: 4
Minima: -1.00 C
Massima: 12.50 C
Media: 5.00 C
Giorni con gelo (<= 0 C): 2
```

## 6.2 Il ciclo `do-while`

Con il ciclo `while` la condizione viene controllata prima di entrare nel corpo: se è falsa all'inizio, il corpo non viene eseguito nemmeno una volta. Ci sono però situazioni in cui sai con certezza che il blocco di istruzioni deve essere eseguito **almeno una volta**, e solo al termine del primo passo ha senso decidere se ripetere.

Pensa a quando chiedi un dato all'utente e vuoi ripetere la richiesta finché non arriva un valore valido, oppure a quando mostri un menu interattivo e ripeti finché l'utente non sceglie l'opzione di uscita, oppure ancora a quando estrai le cifre decimali di un numero intero non negativo: anche il numero `0` ha una cifra (lo zero stesso) e richiede quindi almeno un'iterazione.

Per questi casi il C offre il ciclo `do-while`:

<!-- cod: id=6.2-b tipo=frammento -->
```c
do {
    // corpo del ciclo: eseguito sempre almeno una volta
} while (condizione);
```

Osserva le due differenze fondamentali rispetto a `while`:

1. **Controllo in coda**: il programma entra subito nel corpo racchiuso tra `{` e `}`, esegue tutte le istruzioni e solo alla fine valuta `condizione`. Se è diversa da zero (vero), torna a `do` per una nuova iterazione; se è zero (falso), prosegue con l'istruzione successiva.
2. **Punto e virgola finale obbligatorio**: la riga `while (condizione);` deve terminare con `;`. Dimenticarlo provoca un errore di compilazione.

```text
          +----------------------------+
          |                            |
          v                            |
   [ corpo del ciclo ]                 |
          |                            |
          v                            |
   [ condizione ] --(vero / != 0)------+
          |
     (falso / 0)
          |
          v
   [ istruzione successiva ]
```

### Regola di visibilità delle variabili nella condizione

Nel ciclo `do-while` c'è una regola sintattica molto importante che sorprende spesso chi inizia: **ogni variabile usata dentro `while (condizione);` deve essere dichiarata prima di `do`**, e non all'interno del blocco tra parentesi graffe.

In C le variabili dichiarate dentro un blocco `{ ... }` esistono solo fino alla parentesi graffa di chiusura `}` (lo vedremo nel capitolo 7). Poiché `while (condizione);` si trova *dopo* quella graffa, una variabile dichiarata nel corpo non esiste più quando la condizione viene valutata:

<!-- cod: id=6.2-c tipo=errore -->
```c
#include <stdio.h>

int main(void) {
    do {
        int scelta = 0;
        printf("Scelta: %d\n", scelta);
    } while (scelta != 0);  // ERRORE: scelta non è visibile qui!
    return 0;
}
```

Il compilatore segnala che `scelta` non è dichiarato nella condizione finale. Per correggere il codice basta spostare `int scelta = 0;` subito prima della parola chiave `do`.

Secondo lo standard C23, la valutazione in coda, l'esecuzione garantita della prima iterazione e la visibilità di blocco del corpo di `do-while` hanno comportamento pienamente definito.

### Gestire la fine dell'input in modo sicuro

Quando usi `do-while` per chiedere ripetutamente un dato da `stdin` finché non è valido, c'è un dettaglio critico da non trascurare: **che cosa succede se lo stream si chiude prima che arrivi un dato valido?**

Immagina di eseguire il programma passando un file di testo in ingresso, oppure che l'utente prema la combinazione di fine input (`Ctrl+D` su Linux/macOS, `Ctrl+Z` seguito da Invio su Windows). Se `fgets` restituisce `nullptr` e tu tratti quel caso come un semplice input errato, la variabile `valido` resta `false` e il ciclo ripete `fgets` all'infinito.

La regola difensiva è semplice: controlla sempre `fgets(...) == nullptr` all'interno del corpo e, se accade, segnala l'errore su `stderr` e interrompi il programma con `return EXIT_FAILURE;` (oppure esci dal ciclo in modo esplicito).

> **Se vieni da Python** — Python non possiede un costrutto `do-while` nativo: per ottenere lo stesso effetto si scrive di solito un ciclo `while True:` con un `if ...: break` in fondo. In C `do { ... } while (condizione);` rende esplicita la garanzia di almeno un'esecuzione del corpo prima del controllo finale.

### Esempio guidato

Il programma seguente richiede ripetutamente da `stdin` un codice PIN intero compreso tra `100` e `999` inclusi, usando `do { ... } while (!valido);`. Scarta ogni riga malformata o fuori intervallo, conta i tentativi e termina in modo sicuro se `stdin` si chiude prima di ricevere un PIN valido.

<!-- cod: id=6.2-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char riga[128];
    int pin = 0;
    int tentativi = 0;
    bool valido = false;

    do {
        if (fgets(riga, (int)sizeof(riga), stdin) == nullptr) {
            fprintf(stderr, "Errore: fine dell'input prima di un PIN valido.\n");
            return EXIT_FAILURE;
        }
        ++tentativi;

        char extra = '\0';
        if (sscanf(riga, "%d %c", &pin, &extra) == 1 &&
            pin >= 100 && pin <= 999) {
            valido = true;
        } else {
            printf("PIN non valido, riprova.\n");
        }
    } while (!valido);

    printf("PIN accettato: %d (tentativi: %d)\n", pin, tentativi);
    return EXIT_SUCCESS;
}
```

```input
abc
42
1050
735
```

```output
PIN non valido, riprova.
PIN non valido, riprova.
PIN non valido, riprova.
PIN accettato: 735 (tentativi: 4)
```

Osserva i punti chiave del programma:

- Le variabili `riga`, `pin`, `tentativi` e `valido` sono dichiarate *prima* del blocco `do`: in questo modo `valido` è visibile nella condizione finale `while (!valido);`, e `pin` e `tentativi` restano accessibili anche dopo il ciclo per la stampa conclusiva.
- La variabile `extra`, usata solo per il controllo dei caratteri spuri in `sscanf`, serve unicamente dentro il corpo ed è quindi dichiarata all'interno delle graffe.
- La prima operazione di ogni iterazione verifica `fgets(...) == nullptr`: se l'input termina in anticipo, il programma scrive su `stderr` e restituisce `EXIT_FAILURE`, evitando qualsiasi ciclo infinito.
- Nella condizione dell'`if`, grazie alla valutazione a corto circuito di `&&` (capitolo 4), `pin >= 100 && pin <= 999` viene valutato solo se `sscanf` ha effettivamente convertito un singolo intero valido.

> **C23** — I tipi e i valori `bool`, `true`, `false` e `nullptr` sono parole chiave native in C23. Con standard precedenti (C17 o C11) servono `#include <stdbool.h>` per `bool`/`true`/`false` e `NULL` al posto di `nullptr`.

> **Approfondimento — Perché dimenticare il controllo di `nullptr` blocca il `do-while`**
> Quando uno stream raggiunge la fine dell'input, lo stato di fine file rimane attivo sullo stream stesso. Ogni chiamata successiva a `fgets(..., stdin)` non si ferma più ad aspettare nuovi caratteri: restituisce istantaneamente `nullptr` senza modificare il contenuto del buffer `riga`. Se un ciclo `do { ... } while (!valido);` non intercetta `nullptr`, esegue `sscanf` sullo stesso buffer (o fallisce di nuovo), lascia `valido` a `false` e ripete il ciclo milioni di volte al secondo fino a riempire il terminale di messaggi di errore. Controllare sempre il ritorno di `fgets` elimina questo rischio alla radice.

### Esercizio 6.2 — Analisi delle cifre di un intero non negativo con `do-while`

**Descrizione**

Scrivi un programma C che legga da `stdin` una riga contenente un intero `long long` compreso tra `0` e `1'000'000'000` inclusi (controllando fine dell'input, formato esatto con `"%lld %c"` e intervallo; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Usando un ciclo `do-while` che estrae le cifre decimali dalla meno significativa alla più significativa mediante `% 10` e `/= 10`, calcola: il numero totale di cifre (per `0` deve valere `1`), la somma delle cifre, la cifra massima e il numero ottenuto invertendo l'ordine delle cifre (gli zeri iniziali del numero invertito spariscono naturalmente nel valore numerico). Stampa i risultati esattamente come nell'esempio di esecuzione e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- ciclo `do-while` con controllo in coda
- garanzia di almeno una iterazione (caso limite `n = 0`)
- visibilità delle variabili dichiarate prima del blocco `do`
- estrazione di cifre con `% 10` e `/= 10`

**Domande guida**

1. Perché un ciclo `do-while` gestisce naturalmente il caso limite in cui il numero inserito vale `0` senza richiedere un `if` separato?
2. Dove devi dichiarare la variabile `residuo` affinché possa essere controllata nella condizione finale `while (residuo > 0);`?
3. Come aggiorni la variabile `inverso` a ogni iterazione per aggiungere in fondo la nuova cifra appena estratta?
4. Perché limitare l'ingresso a `1'000'000'000` e usare `long long` per `inverso` impedisce qualsiasi rischio di overflow?

**Esempio di esecuzione**

```input
40825
```

```output
Numero: 40825
Cifre: 5
Somma cifre: 19
Cifra massima: 8
Numero invertito: 52804
```

## 6.3 Il ciclo `for`

Molti cicli seguono sempre lo stesso schema: inizializzi un contatore prima del ciclo, ripeti finché il contatore soddisfa una condizione e aggiorni il contatore alla fine di ogni iterazione. Con `while` questi tre pezzi finiscono sparsi in punti diversi del codice, e in un corpo lungo è facile dimenticare l'aggiornamento o non vedere subito i limiti del conteggio.

Il ciclo `for` raccoglie i tre elementi di controllo in una sola intestazione:

<!-- cod: id=6.3-b tipo=frammento -->
```c
for (inizializzazione; condizione; aggiornamento) {
    // corpo del ciclo
}
```

Il suo funzionamento segue esattamente quest'ordine:

1. Esegue `inizializzazione` **una sola volta**, prima di iniziare.
2. Valuta `condizione` **prima di ogni iterazione**. Se è zero (falso), il ciclo termina immediatamente (può quindi compiere anche zero iterazioni).
3. Se `condizione` è diversa da zero (vero), esegue il corpo tra le parentesi graffe.
4. Al termine del corpo esegue `aggiornamento` e torna al passo 2.

Concettualmente, un ciclo `for` corrisponde quasi del tutto a questo `while` (l'unica sottile differenza riguarda `continue`, che vedrai nella prossima sotto-sezione):

<!-- cod: id=6.3-c tipo=frammento -->
```c
inizializzazione;
while (condizione) {
    // corpo del ciclo
    aggiornamento;
}
```

### Visibilità della variabile di controllo e clausole facoltative

In C puoi dichiarare la variabile di controllo direttamente nella prima clausola del `for`:

<!-- cod: id=6.3-d tipo=frammento -->
```c
for (int i = 0; i < n; ++i) {
    printf("%d\n", i);
}
```

Una variabile dichiarata nell'intestazione del `for` è **visibile esclusivamente all'interno del ciclo**: dopo la parentesi graffa di chiusura `}` non esiste più. Questo è un grande vantaggio: evita conflitti di nomi e ti permette di usare di nuovo `int i` in un secondo ciclo `for` poco sotto, senza sporcare il resto di `main`.

Ciascuna delle tre clausole del `for` può essere omessa (lasciando comunque i due punti e virgola `;`). In particolare, se `condizione` viene omessa — come in `for (;;)` — lo standard C23 la considera sempre vera (`1`), ottenendo un ciclo che prosegue finché non interviene un'uscita esplicita dal corpo. Sia la semantica delle tre clausole, sia la visibilità circoscritta della dichiarazione iniziale, sia il significato della condizione omessa sono pienamente definiti dallo standard C23.

### Conteggi in avanti, a ritroso, a passo arbitrario e valori `double`

Il ciclo `for` si adatta a ogni schema di conteggio regolare:

- **Da `0` a `n - 1`** (`n` iterazioni): `for (int i = 0; i < n; ++i)`. È la convenzione più usata in C, soprattutto quando lavorerai con gli array (lo vedremo nel capitolo 8).
- **Da `1` a `n`** (`n` iterazioni): `for (int i = 1; i <= n; ++i)`. È comoda quando il contatore rappresenta un numero ordinale naturale, come il numero di un mese o di una riga di tabella.
- **A ritroso**: `for (int i = n; i >= 1; --i)` conta all'indietro da `n` fino a `1`.
- **A passo arbitrario**: `for (int i = 0; i <= 20; i += 2)` avanza di due in due (`0, 2, 4, ..., 20`).

Quando invece ti serve una sequenza di valori in virgola mobile — per esempio `20.0`, `20.2`, `20.4`, ... — **non usare mai una variabile `double` come contatore del `for`**. Usa un contatore intero `i` e calcola il valore `double` dentro il corpo (per esempio `double t = 20.0 + i * 0.2;`): in questo modo ogni passo subisce al massimo un singolo arrotondamento e il numero di iterazioni resta esatto.

### Tre errori classici del ciclo `for`

1. **Errori *off-by-one* (sfasamento di un'unità)**: scambiare `<` con `<=` (o partire da `1` invece che da `0`) fa compiere un'iterazione in più o in meno. Verifica sempre con un esempio minuscolo (come `n = 1` o `n = 2`): con `int i = 0; i < n; ++i` esegui `n` iterazioni (`0` .. `n - 1`); con `int i = 1; i <= n; ++i` esegui ancora `n` iterazioni (`1` .. `n`).
2. **Underflow di contatori `unsigned` nei cicli decrescenti**: se scrivi `for (unsigned int i = 5; i >= 0; --i)`, quando `i` vale `0` il decremento `--i` non produce `-1` ma `UINT_MAX` (aritmetica modulare degli interi senza segno, capitolo 3). La condizione `i >= 0` rimane quindi *sempre* vera e il ciclo diventa infinito. Per contare a ritroso fino a `0`, usa un tipo con segno (`int`).
3. **Punto e virgola dopo `for (...);`**: proprio come per `while`, scrivere `for (int i = 0; i < n; ++i); { ... }` esegue `n` iterazioni vuote e poi esegue il blocco tra graffe una sola volta, fuori dal ciclo (e se nel blocco usassi `i`, il compilatore segnalerebbe che `i` non è dichiarato).

### Come scegliere tra `for`, `while` e `do-while`

| Situazione | Ciclo consigliato | Motivo |
|---|---|---|
| Numero di iterazioni noto in anticipo o conteggio regolare | `for` | Inizializzazione, limite e passo sono leggibili a colpo d'occhio |
| Lettura fino alla fine dell'input o condizione che può essere falsa da subito | `while` | Controllo in testa senza contatore artificiale |
| Il corpo deve essere eseguito almeno una volta (validazione input, cifre di `0`) | `do-while` | Controllo in coda garantito |

> **Se vieni da Python** — In Python il ciclo `for` itera direttamente sugli elementi di una sequenza o di `range(n)`. In C il `for` non ha sequenze incorporate: controlli esplicitamente inizializzazione, condizione di permanenza e aggiornamento del contatore, il che richiede qualche carattere in più ma ti dà controllo completo su passo, direzione e tipo della variabile.

### Esempio guidato

Il programma seguente legge da `stdin` un intero `n` compreso tra `1` e `20` e usa due cicli `for` indipendenti: il primo stampa `n` righe di una tabella Celsius–Fahrenheit calcolando il passo decimale `0.2` a partire da un contatore intero `i` (`0..n-1`); il secondo stampa i primi `n` numeri di Fibonacci (`1..n`) memorizzati in variabili `long long`.

<!-- cod: id=6.3-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char riga[128];
    int n = 0;
    char extra = '\0';

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr ||
        sscanf(riga, "%d %c", &n, &extra) != 1 || n < 1 || n > 20) {
        fprintf(stderr, "Errore: inserisci un intero tra 1 e 20.\n");
        return EXIT_FAILURE;
    }

    printf("Tabella Celsius -> Fahrenheit:\n");
    for (int i = 0; i < n; ++i) {
        double celsius = 20.0 + i * 0.2;
        double fahrenheit = celsius * 9.0 / 5.0 + 32.0;
        printf("%5.1f C = %6.2f F\n", celsius, fahrenheit);
    }

    long long prec = 0;
    long long corr = 1;
    printf("Primi %d numeri di Fibonacci:\n", n);
    for (int i = 1; i <= n; ++i) {
        printf("F(%d) = %lld\n", i, prec);
        long long prox = prec + corr;
        prec = corr;
        corr = prox;
    }

    return EXIT_SUCCESS;
}
```

```input
5
```

```output
Tabella Celsius -> Fahrenheit:
 20.0 C =  68.00 F
 20.2 C =  68.36 F
 20.4 C =  68.72 F
 20.6 C =  69.08 F
 20.8 C =  69.44 F
Primi 5 numeri di Fibonacci:
F(1) = 0
F(2) = 1
F(3) = 1
F(4) = 2
F(5) = 3
```

Analizziamo le scelte fatte nei due cicli:

- Entrambi i cicli dichiarano `int i` nella propria intestazione. Non c'è alcun conflitto perché la visibilità del primo `i` termina alla chiusura del primo `for`.
- Il primo ciclo usa lo schema `0..n-1` (`int i = 0; i < n; ++i`) e ricava `celsius` tramite `20.0 + i * 0.2`: così le iterazioni sono esattamente `n` e gli errori di arrotondamento non si sommano da un passo all'altro.
- Il secondo ciclo usa lo schema `1..n` (`int i = 1; i <= n; ++i`) per numerare in modo naturale i termini `F(1)` .. `F(n)`. Le variabili `prec` e `corr` sono di tipo `long long` per evitare overflow anche su valori di `n` più grandi, e vengono dichiarate prima del ciclo perché devono conservare il proprio valore da un'iterazione alla successiva.

> **Approfondimento — Due insidie del `for`: contatori `double` e contatori `unsigned` decrescenti**
> Se scrivi `for (double x = 0.0; x != 1.0; x += 0.1)`, lo 0.1 non è rappresentabile esattamente in binario (capitolo 3): dopo dieci somme `x` non vale esattamente `1.0`, `x != 1.0` resta vero e il ciclo non si ferma! Perfino con `x <= 1.0` rischi di eseguire 10 oppure 11 iterazioni a seconda dell'arrotondamento. Usa sempre un contatore intero (`for (int i = 0; i <= 10; ++i)`) e calcola `i * 0.1`.
> Analogamente, in `for (unsigned int i = 3; i >= 0; --i)`, dopo `i = 0` il decremento `--i` avvolge `i` al valore `UINT_MAX`: la condizione `i >= 0` è vera per qualunque `unsigned int` e il ciclo è infinito. Con i cicli decrescenti fino a zero, scegli un tipo intero con segno (`int`).

### Esercizio 6.3 — Piano di risparmio mensile con ciclo `for`

**Descrizione**

Scrivi un programma C che legga da `stdin` una sola riga contenente quattro valori separati da spazi: `capitale_iniziale` (`double >= 0.0`), `versamento_mensile` (`double >= 0.0`), `tasso_annuo` in percentuale (`double` tra `0.0` e `50.0` inclusi) e `mesi` (`int` tra `1` e `60` inclusi). Verifica fine dell'input, formato esatto rifiutando caratteri extra (`"%lf %lf %lf %d %c"` con valore restituito `4`) e validità dei domini; in caso di errore scrivi su `stderr` e restituisci `EXIT_FAILURE`. Calcola il tasso mensile come `(tasso_annuo / 100.0) / 12.0` e usa un ciclo `for` con contatore intero `mese` da `1` a `mesi` inclusi: in ogni mese calcola `interessi = saldo * tasso_mensile`, somma `interessi` a `interessi_totali`, aggiungi `interessi + versamento_mensile` a `saldo`, aggiorna `totale_versato` e stampa la riga del mese (`%2d` per il numero del mese, `%.2f` per gli importi). Dopo il ciclo stampa il riepilogo finale esattamente come nell'esempio di esecuzione e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- ciclo `for` con contatore intero dichiarato nell'intestazione
- aggiornamento di più accumulatori a ogni iterazione
- condizione esatta `<=` per evitare errori off-by-one
- formattazione allineata con `%2d` e `%.2f`

**Domande guida**

1. Perché in questo problema il ciclo `for` è più adatto di `while` e `do-while`?
2. Quale condizione devi scrivere nel `for` (con `mese` che parte da `1`) affinché vengano simulati esattamente tutti i mesi richiesti senza saltarne l'ultimo?
3. In quale ordine vanno calcolati interessi e aggiornamento del saldo all'interno di ogni mese?
4. Perché conviene dichiarare `int mese` direttamente nella prima clausola del `for`?

**Esempio di esecuzione**

```input
1000.0 100.0 12.0 3
```

```output
Mese  1: interessi = 10.00, saldo = 1110.00
Mese  2: interessi = 11.10, saldo = 1221.10
Mese  3: interessi = 12.21, saldo = 1333.31
Totale versato: 1300.00
Interessi maturati: 33.31
Saldo finale: 1333.31
```

## 6.4 Modificare il percorso di un ciclo: `break` e `continue`

Di norma un ciclo ripete tutto il proprio corpo fino in fondo e si arresta soltanto quando la condizione di permanenza diventa falsa. A volte però, durante un'iterazione, accade qualcosa che richiede una deviazione immediata: potresti aver già trovato l'elemento che cercavi, aver incontrato un valore speciale che segnala la fine dei dati, oppure voler ignorare una riga vuota senza annidare il resto del corpo dentro un altro `if`.

Per questi due bisogni il C mette a disposizione due istruzioni di salto controllato: `break` e `continue`.

### Uscire subito con `break`

Hai già usato `break` nel capitolo 4 per chiudere i rami di uno `switch`. Dentro un ciclo (`while`, `do-while` o `for`), `break` **interrompe immediatamente il solo ciclo più interno che la racchiude** e trasferisce il flusso di controllo alla prima istruzione successiva al ciclo.

È utile soprattutto in due casi:

- **Ricerca riuscita**: appena trovi il primo numero o il primo carattere che soddisfa un criterio, non ha senso continuare a scorrere il resto della sequenza.
- **Condizione sentinella o di emergenza**: interrompi l'elaborazione quando incontri un codice speciale (come `9999`) o superi una soglia critica.

### Saltare l'iterazione corrente con `continue`

L'istruzione `continue`, invece, non chiude il ciclo: **salta tutte le istruzioni residue dell'iterazione corrente** del solo ciclo più interno e passa subito all'iterazione successiva.

È particolarmente comoda come filtro iniziale nel corpo del ciclo: se una riga è vuota o un campione è fuori intervallo, esegui `continue` e lasci il resto del corpo dedicato al caso normale, senza accumulare livelli superflui di `if`/`else`.

### La differenza decisiva di `continue` tra `for` e `while`

Fai molta attenzione al punto esatto in cui `continue` fa saltare il programma:

- In un ciclo **`for`**, `continue` esegue comunque la **clausola di aggiornamento** prima di rivalutare la condizione.
- In un ciclo **`while`** o **`do-while`**, `continue` salta direttamente alla **valutazione della condizione**, scavalcando qualsiasi istruzione di aggiornamento scritta più in basso nel corpo.

Questa differenza spiega perché un `continue` scritto con leggerezza dentro un `while` con contatore può causare un ciclo infinito (vedi l'approfondimento a fine sotto-sezione). Quando invece il `while` avanza grazie a una lettura nella condizione stessa — come `while (fgets(...) != nullptr)` — `continue` è sicuro perché la chiamata successiva a `fgets` avviene comunque nel controllo di testa.

### Interazione con `switch` dentro un ciclo

Quando uno `switch` si trova all'interno di un ciclo, `break` e `continue` si comportano su livelli diversi:

- `break` interrompe **lo `switch`** (il costrutto più interno tra cicli e `switch`), *non* il ciclo esterno.
- `continue` invece ignora lo `switch` e agisce sul **ciclo più interno** che racchiude lo `switch`.

Sia l'effetto di `break` e `continue` sul solo costrutto più interno sia l'esecuzione della clausola di aggiornamento del `for` dopo `continue` sono pienamente definiti dallo standard C23.

### Usare `break` e `continue` con misura

`break` e `continue` semplificano il codice quando rendono evidenti le eccezioni e le uscite anticipate, ma abusarne produce l'effetto opposto. Un ciclo lungo con molti `break` e `continue` sparsi in rami annidati diventa difficile da leggere perché devi controllare l'intero corpo per capire quando e come il ciclo può terminare. Come regola pratica:

- metti eventuali `continue` di filtro nella parte alta del ciclo, come controlli rapidi di esclusione;
- limita i `break` a poche condizioni di arresto ben riconoscibili, registrando in una variabile di stato il motivo dell'uscita se ti serve dopo il ciclo;
- se la condizione di arresto è semplice e naturale, preferisci esprimerla direttamente nell'intestazione del ciclo.

> **Se vieni da Python** — In Python i cicli `while` e `for` ammettono una clausola `else` eseguita soltanto se il ciclo si conclude senza incontrare `break`. In C non esiste alcun `else` collegato ai cicli: per distinguere un'uscita normale da un arresto con `break` si imposta una variabile booleana o una variabile intera di stato prima di eseguire `break`.

### Esempio guidato

Il programma seguente legge da `stdin` una sequenza di campioni interi prodotti da un sensore: usa `continue` per ignorare le righe vuote e i valori negativi di disturbo, e usa `break` per arrestarsi al codice sentinella `9999` oppure al superamento della soglia critica `500`. Prima di ogni `break` aggiorna `stato` per stampare alla fine la causa esatta dell'arresto.

<!-- cod: id=6.4-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    constexpr int SENTINELLA = 9999;
    constexpr int SOGLIA_CRITICA = 500;
    char riga[128];
    int validi = 0, disturbi = 0, picco = 0, stato = 0;

    while (fgets(riga, (int)sizeof(riga), stdin) != nullptr) {
        int valore = 0;
        char extra = '\0';
        int esito = sscanf(riga, "%d %c", &valore, &extra);
        if (esito == EOF) {
            continue;
        }
        if (esito != 1) {
            fprintf(stderr, "Errore: lettura non valida.\n");
            return EXIT_FAILURE;
        }
        if (valore == SENTINELLA) {
            stato = 1;
            break;
        }
        if (valore < 0) {
            ++disturbi;
            continue;
        }
        if (valore > SOGLIA_CRITICA) {
            stato = 2;
            break;
        }
        if (validi == 0 || valore > picco) {
            picco = valore;
        }
        ++validi;
    }
    printf("Validi: %d, picco: %d, disturbi: %d\n", validi, picco, disturbi);
    printf("Arresto: %s\n", stato == 1 ? "sentinella" :
           (stato == 2 ? "soglia critica" : "fine input"));
    return EXIT_SUCCESS;
}
```

```input
120

-15
340
610
200
```

```output
Validi: 2, picco: 340, disturbi: 1
Arresto: soglia critica
```

Seguiamo l'esecuzione sulle sei righe dell'input:

- La prima riga (`120`) è valida: aggiorna `picco` a `120` e porta `validi` a `1`.
- La seconda riga è vuota: `sscanf` restituisce `EOF` e `continue` fa ripartire subito il `while` con la riga successiva.
- La terza riga (`-15`) è negativa: incrementa `disturbi` e usa `continue` per non includerla nel picco né nei campioni validi.
- La quarta riga (`340`) è valida: aggiorna `picco` a `340` e porta `validi` a `2`.
- La quinta riga (`610`) supera `SOGLIA_CRITICA`: registra `stato = 2` ed esegue `break`. La sesta riga (`200`) non viene nemmeno letta.
- Dopo il ciclo, `stato` permette di stampare con certezza quale evento ha chiuso il ciclo.

> **C23** — Le costanti `constexpr` e `nullptr` sono novità del C23; in C17/C11 puoi sostituire `constexpr` con `const` (o `#define`) e `nullptr` con `NULL`.

> **Approfondimento — `continue` in `while` contro `continue` in `for`**
> Confronta questi due frammenti che vorrebbero stampare i numeri da `0` a `4` saltando il `2`:
>
> ```text
> // VERSIONE SBAGLIATA CON while: ciclo infinito!
> int i = 0;
> while (i < 5) {
>     if (i == 2) {
>         continue;  // salta ++i e torna a while (i < 5) con i ancora uguale a 2!
>     }
>     printf("%d\n", i);
>     ++i;
> }
>
> // VERSIONE CORRETTA CON for: termina regolarmente
> for (int i = 0; i < 5; ++i) {
>     if (i == 2) {
>         continue;  // esegue comunque ++i prima di ricontrollare i < 5
>     }
>     printf("%d\n", i);
> }
> ```
>
> Nella versione `while`, quando `i` raggiunge `2`, `continue` salta l'istruzione `++i;` in fondo al corpo: `i` resta `2` per sempre. Nella versione `for`, invece, `continue` esegue sempre la clausola `++i` prima di tornare al test `i < 5`, evitando il blocco.

### Esercizio 6.4 — Carico di un furgone con `break` e `continue`

**Descrizione**

Un furgone ha una capacità massima di `50.0` kg (`constexpr double CAPACITA_MAX = 50.0;`). Scrivi un programma C che legga da `stdin` una sequenza di righe con `while (fgets(...) != nullptr)`, dove ciascuna riga contiene il peso di un pacco in chilogrammi (`double`). Segui queste regole dentro il ciclo usando `continue` e `break`: se la riga è vuota o contiene solo spazi (`sscanf(riga, " %c", &primo) == EOF`), incrementa `righe_vuote` e passa subito alla riga successiva con `continue`; altrimenti estrai un solo `double` con `"%lf %c"` (se il formato non è valido stampa su `stderr` e restituisci `EXIT_FAILURE`); se `peso == 0.0` (valore sentinella di fine lista) registra il motivo di arresto ed esci dal ciclo con `break`; se `peso < 0.0` incrementa `scartati` e passa alla riga successiva con `continue`; se `carico_attuale + peso > CAPACITA_MAX` non caricare il pacco, registra che il furgone è pieno ed esci dal ciclo con `break`; altrimenti carica il pacco aggiornando `carico_attuale` e `caricati`. Al termine del ciclo stampa pacchi caricati, peso totale (`%.2f kg`), pacchi scartati, righe vuote ignorate e causa di arresto (`furgone pieno`, `codice sentinella` oppure `fine dell'input`), restituendo `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- istruzione `continue` per saltare righe vuote o valori scartati
- istruzione `break` per arrestare il ciclo su sentinella o capacità esaurita
- ordine dei controlli dentro il corpo del ciclo
- registrazione dello stato di uscita prima del `break`

**Domande guida**

1. Perché conviene controllare se la riga contiene solo spazi bianchi prima di tentare la conversione numerica con `sscanf`?
2. Che differenza pratica c'è tra usare `continue` quando un peso è negativo e usare `break` quando il peso vale `0.0` o supera la capacità residua?
3. In che modo il programma può sapere dopo la fine del ciclo quale delle tre cause (`furgone pieno`, `codice sentinella` o `fine dell'input`) ha provocato l'uscita?
4. Perché in questo ciclo `while` l'istruzione `continue` non provoca un ciclo infinito?

**Esempio di esecuzione**

```input
12.5

-3.0
20.0
15.0
8.0
10.0
```

```output
Pacchi caricati: 3
Peso totale: 47.50 kg
Pacchi scartati: 1
Righe vuote ignorate: 1
Arresto: furgone pieno
```

## 6.5 Cicli annidati e invarianti di ciclo

Finora ogni ciclo ha percorso una singola sequenza lineare di valori o di righe. Molti problemi reali, però, hanno due dimensioni: stampare una tabella di righe e colonne, esplorare una griglia, oppure confrontare tutte le coppie possibili di elementi. In questi casi si inserisce un ciclo *dentro* il corpo di un altro ciclo, ottenendo una coppia di **cicli annidati**.

### Come funzionano i cicli annidati

In una coppia di cicli annidati, per **ogni singola iterazione** del ciclo esterno, il ciclo interno viene eseguito completamente dall'inizio alla fine. Se il ciclo esterno compie `R` iterazioni e quello interno compie `C` iterazioni, il corpo del ciclo interno viene eseguito complessivamente `R * C` volte.

```text
Ciclo esterno (riga = 1..3)
  riga = 1  -->  colonna = 1, 2, 3, 4   (4 iterazioni interne)
  riga = 2  -->  colonna = 1, 2, 3, 4   (4 iterazioni interne)
  riga = 3  -->  colonna = 1, 2, 3, 4   (4 iterazioni interne)
                                         Totale: 3 * 4 = 12 passi
```

Due accortezze pratiche rendono i cicli annidati subito chiari e privi di errori:

1. **Scegli nomi distinti e significativi per i contatori**: usa `riga` e `colonna` (oppure `r` e `c`), evitando di riutilizzare lo stesso nome nel ciclo interno (che nasconderebbe la variabile del ciclo esterno creando grande confusione).
2. **Azzera i contatori locali al punto giusto**: se devi calcolare una statistica separata per ciascuna riga (per esempio la somma o il numero di elementi di quella riga), la variabile va inizializzata a `0` *dentro* il ciclo esterno, subito prima del ciclo interno, così da ripartire da zero a ogni nuova riga.

### Uscire in modo pulito da cicli annidati

Come hai visto nella sotto-sezione 6.4, `break` interrompe **soltanto il ciclo più interno** che la racchiude. Se stai cercando un elemento in una griglia e vuoi fermare *entrambi* i cicli appena lo trovi, un solo `break` non basta: il ciclo esterno proseguirebbe con la riga successiva.

Il modo più pulito e leggibile consiste nell'usare una variabile `bool` (per esempio `bool trovato = false;`) e controllarla nella condizione del ciclo esterno:

<!-- cod: id=6.5-b tipo=frammento -->
```c
bool trovato = false;
for (int riga = 1; riga <= n && !trovato; ++riga) {
    for (int col = 1; col <= n; ++col) {
        if (riga * col == obiettivo) {
            trovato = true;
            break;  // esce dal ciclo interno; !trovato ferma poi quello esterno
        }
    }
}
```

Appena il valore viene trovato, `trovato` diventa `true`, `break` chiude il ciclo interno e la condizione `riga <= n && !trovato` termina subito anche il ciclo esterno.

### Invarianti di ciclo: verificare correttezza e terminazione

Quando un ciclo diventa un po' più articolato, testarlo su uno o due esempi non basta a essere certi che sia corretto per *tutti* gli ingressi. Esiste uno strumento di ragionamento semplice e potentissimo: l'**invariante di ciclo** (*loop invariant*), cioè una proprietà logica che vale prima del ciclo e resta vera al termine di ogni iterazione.

Per usare un invariante di ciclo allo scopo di verificare la correttezza di un ciclo, controlli tre punti:

1. **Inizializzazione**: la proprietà è vera *prima* della prima iterazione (anche nel caso in cui il ciclo compia zero iterazioni).
2. **Mantenimento**: se la proprietà è vera all'inizio di un'iterazione ed esegui il corpo del ciclo, essa resta vera al termine dell'iterazione stessa.
3. **Conclusione**: quando la condizione di permanenza diventa falsa e il ciclo termina, combinare l'invariante con la negazione della condizione dimostra che il risultato finale è esattamente quello atteso.

Vediamo un esempio concreto. Supponi di sommare i numeri da `1` a `n` con:

<!-- cod: id=6.5-c tipo=frammento -->
```c
int somma = 0;
for (int i = 1; i <= n; ++i) {
    somma += i;
}
```

L'invariante prima di ogni controllo della condizione `i <= n` è: "`somma` contiene la somma degli interi da `1` a `i - 1`, e `1 <= i <= n + 1`".
- **Inizializzazione**: prima del ciclo `i = 1` e `somma = 0`, che è la somma dell'intervallo vuoto `1..0`. Vero.
- **Mantenimento**: se `somma` vale `1 + ... + (i - 1)` e nel corpo aggiungiamo `i` per poi incrementare `i` a `i + 1`, ora `somma` contiene esattamente la somma fino al nuovo `i - 1`. Vero.
- **Conclusione**: il ciclo si ferma quando `i <= n` è falsa, quindi `i == n + 1`. Sostituendo `i = n + 1` nell'invariante otteniamo che `somma` è la somma degli interi da `1` a `n`.

Oltre alla correttezza, occorre verificare la **terminazione**: basta individuare una quantità (per esempio `n + 1 - i`, oppure il numero di caratteri rimasti nello stream) che a ogni iterazione si avvicina strettamente al limite inferiore (o alla fine dello stream). Poiché un intero non può diminuire all'infinito restando maggiore o uguale a zero, il ciclo terminerà certamente in un numero finito di passi.

Secondo lo standard C23, la semantica esatta di tutti i cicli che terminano o che eseguono operazioni osservabili (come l'I/O su `stdin` e `stdout`) è pienamente definita; invece un ciclo infinito privo di qualsiasi effetto osservabile può avere conseguenze particolari durante le ottimizzazioni del compilatore, un motivo in più per garantire sempre la terminazione.

### Esempio guidato

Il programma seguente legge da `stdin` una dimensione `n` (tra `1` e `10`) e due interi positivi `x` e `y`, poi svolge due compiti:
1. stampa la tavola pitagorica `n x n` con due cicli `for` annidati, documentando l'invariante del ciclo esterno;
2. calcola il massimo comun divisore (MCD) di `x` e `y` tramite l'algoritmo di Euclide in un ciclo `while`, commentando invariante e terminazione.

<!-- cod: id=6.5-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char riga[128];
    int n = 0, x = 0, y = 0;
    char extra = '\0';

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr ||
        sscanf(riga, "%d %d %d %c", &n, &x, &y, &extra) != 3 ||
        n < 1 || n > 10 || x <= 0 || y <= 0) {
        fprintf(stderr, "Errore: inserisci n (1..10) e due interi positivi.\n");
        return EXIT_FAILURE;
    }

    printf("Tavola pitagorica %dx%d:\n", n, n);
    // Invariante: sono state stampate le righe 1..(r - 1) complete
    for (int r = 1; r <= n; ++r) {
        for (int c = 1; c <= n; ++c) {
            printf("%4d", r * c);
        }
        putchar('\n');
    }

    int a = x;
    int b = y;
    // Invariante: MCD(a, b) == MCD(x, y) e a > 0, b >= 0
    // Terminazione: b diminuisce strettamente (0 <= a % b < b) fino a 0
    while (b != 0) {
        int resto = a % b;
        a = b;
        b = resto;
    }
    printf("MCD(%d, %d) = %d\n", x, y, a);
    return EXIT_SUCCESS;
}
```

```input
4 84 36
```

```output
Tavola pitagorica 4x4:
   1   2   3   4
   2   4   6   8
   3   6   9  12
   4   8  12  16
MCD(84, 36) = 12
```

Osserva come funzionano gli invarianti nelle due parti:

- **Tavola pitagorica**: il ciclo esterno scorre le righe `r` da `1` a `n`; per ogni riga il ciclo interno scorre le colonne `c` da `1` a `n` stampando `r * c` su 4 caratteri (`%4d`), e subito dopo il ciclo interno `putchar('\n')` va a capo. Quando `r` raggiunge `n + 1`, l'invariante garantisce che sono state stampate tutte le righe da `1` a `n`.
- **Algoritmo di Euclide**: per una proprietà aritmetica fondamentale, `MCD(a, b)` è uguale a `MCD(b, a % b)`. Prima del ciclo `a = x` e `b = y`, quindi l'invariante `MCD(a, b) == MCD(x, y)` è vero. A ogni iterazione `a` e `b` vengono sostituiti con `b` e `a % b`, preservando l'invariante. Inoltre il resto `a % b` è sempre non negativo e strettamente minore di `b`: dunque `b` diminuisce strettamente a ogni passo e deve raggiungere `0`. All'uscita (`b == 0`), l'invariante afferma `MCD(a, 0) == MCD(x, y)`, e poiché `MCD(a, 0) = a`, la variabile `a` contiene certamente il massimo comun divisore cercato.

> **Approfondimento — Usare l'invariante prima di scrivere il codice**
> L'errore più comune nei cicli (sbagliare tra `<` e `<=`, inizializzare un contatore a `0` invece che a `1`, oppure dimenticare l'ultimo elemento) nasce quasi sempre dal fatto di scrivere prima il codice e solo dopo chiedersi che cosa rappresenti ciascuna variabile. Se invece scrivi in un commento di una riga l'invariante *prima* di scrivere il ciclo — per esempio "a questo punto `divisori` conta i divisori trovati nell'intervallo `1..(col - 1)`" — la scelta iniziale (`col = 1`, `divisori = 0`) e la condizione finale (`col <= n`) diventano obbligate e non lasciano spazio a dubbi off-by-one.

### Esercizio 6.5 — Tabella di divisibilità con cicli annidati e invarianti

**Descrizione**

Scrivi un programma C che legga da `stdin` un intero `n` compreso tra `2` e `12` inclusi (controllando fine dell'input, formato esatto con `"%d %c"` e intervallo; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Usando due cicli `for` annidati (`riga_val` da `1` a `n` e `col` da `1` a `n`), stampa una griglia `n x n` di divisibilità preceduta dall'intestazione `Tabella di divisibilita (1..n):`: ogni riga inizia con `%2d:` seguito, per ciascuna colonna `col`, da uno spazio e dal carattere `'X'` se `riga_val % col == 0` oppure `'.'` altrimenti (scritti con `putchar`). Durante il ciclo interno conta i divisori della riga; al termine del ciclo interno stampa ` | divisori: K` aggiungendo ` (primo)` se `K == 2` e aggiorna `conteggio_primi`, `max_divisori` e `miglior_numero` (in caso di parità sul numero massimo di divisori conserva il numero più piccolo). Documenta nei commenti l'invariante di ciclo sia del ciclo esterno sia del ciclo interno. Al termine stampa il conteggio dei numeri primi trovati e il numero con più divisori esattamente come nell'esempio di esecuzione, restituendo `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- cicli `for` annidati con variabili di controllo distinte
- invariante di ciclo esterno e interno
- ripristino del contatore locale a ogni iterazione del ciclo esterno
- gestione della parità nel calcolo del massimo (`>` contro `>=`)

**Domande guida**

1. Dove deve essere azzerata la variabile `divisori` affinché il conteggio di una riga non si sommi a quello delle righe precedenti?
2. Qual è l'invariante del ciclo interno al termine dell'iterazione `col`, e quale proprietà garantisce alla sua uscita quando `col` supera `n`?
3. Quale differenza produce scrivere `divisori > max_divisori` rispetto a `divisori >= max_divisori` quando due numeri hanno lo stesso numero massimo di divisori?
4. Quante volte in totale viene eseguito il corpo del ciclo interno in funzione di `n`?

**Esempio di esecuzione**

```input
6
```

```output
Tabella di divisibilita (1..6):
 1: X . . . . . | divisori: 1
 2: X X . . . . | divisori: 2 (primo)
 3: X . X . . . | divisori: 2 (primo)
 4: X X . X . . | divisori: 3
 5: X . . . X . | divisori: 2 (primo)
 6: X X X . . X | divisori: 4
Numeri primi trovati: 3
Numero con piu divisori: 6 (4 divisori)
```

## Riepilogo

- Un **ciclo** ripete un blocco di istruzioni finché una condizione rimane vera; ogni esecuzione del corpo è un'**iterazione**.
- Il ciclo `while (condizione) { ... }` valuta la condizione in testa e può compiere anche zero iterazioni. I due idiomi standard per leggere fino alla fine dell'input sono `while (fgets(riga, (int)sizeof(riga), stdin) != nullptr)` e `while ((c = getchar()) != EOF)` con `c` di tipo `int`.
- Il ciclo `do { ... } while (condizione);` esegue il corpo almeno una volta, valuta la condizione in coda e termina obbligatoriamente con `;`. Le variabili usate nella condizione finale vanno dichiarate prima del blocco `do` (lo vedremo nel capitolo 7).
- Il ciclo `for (inizializzazione; condizione; aggiornamento) { ... }` raccoglie le tre parti di un conteggio in un'unica intestazione; una variabile dichiarata in `inizializzazione` è visibile solo dentro il ciclo. Per generare sequenze `double` usa sempre un contatore intero invece di un contatore in virgola mobile.
- L'istruzione `break` interrompe solo il ciclo (o lo `switch`) più interno che la racchiude; `continue` salta il resto dell'iterazione corrente del solo ciclo più interno, eseguendo prima la clausola di aggiornamento nel `for` e tornando subito al test in `while` e `do-while`.
- I cicli annidati permettono di elaborare tabelle e griglie usando nomi distinti per i contatori e, quando serve uscire da più livelli insieme, una variabile `bool` di controllo.
- Un **invariante di ciclo** (verificato su inizializzazione, mantenimento e conclusione) abbinato a una grandezza strettamente decrescente verso la condizione di arresto permette di dimostrare correttezza e terminazione di un ciclo.

## Errori comuni

- **Scrivere un punto e virgola subito dopo `while (condizione);` oppure `for (...);`**: trasforma il ciclo in un ciclo a corpo vuoto e fa eseguire il blocco tra graffe una sola volta fuori dal ciclo (o causa un ciclo infinito).
- **Dimenticare il punto e virgola finale dopo `do { ... } while (condizione);` oppure dichiarare dentro il blocco `do` una variabile usata nella condizione**: entrambi producono errori di compilazione perché il `do-while` richiede `;` in coda e le variabili del blocco terminano la loro visibilità alla graffa di chiusura.
- **Dimenticare le parentesi in `while ((c = getchar()) != EOF)`**: poiché `!=` ha precedenza su `=`, scrivere `c = getchar() != EOF` assegna a `c` soltanto `0` o `1` invece del carattere letto.
- **Commettere errori *off-by-one* o usare un contatore `unsigned int` in un ciclo decrescente con `i >= 0`**: scambiare `<` e `<=` sposta di uno il numero di iterazioni, mentre decrementare `0u` provoca un underflow a `UINT_MAX`, rendendo `i >= 0` sempre vero.
- **Usare una variabile `double` come contatore di un ciclo `for` (per esempio con passo `0.1`)**: accumula errori di arrotondamento binari e può alterare il numero di iterazioni; deriva sempre il valore `double` da un contatore intero.
- **Inserire `continue` in un ciclo `while` prima dell'aggiornamento del contatore**: `continue` salta direttamente al controllo di testa senza eseguire l'incremento posto più in basso, creando un ciclo infinito.
- **Dimenticare di azzerare un contatore o un accumulatore locale a ogni iterazione del ciclo esterno**: in una coppia di cicli annidati, i totali di una riga si sommerebbero erroneamente a quelli delle righe precedenti.

## Prima di proseguire

- [ ] So scrivere cicli `while` per leggere da `stdin` fino alla fine dell'input con `fgets` (`nullptr`) e `getchar` (`EOF`), gestendo anche il caso di zero elementi letti.
- [ ] So usare `do-while` quando serve almeno una iterazione, dichiarando prima di `do` le variabili usate nella condizione e gestendo la chiusura inattesa dello stream.
- [ ] So scrivere cicli `for` crescenti, decrescenti e a passo arbitrario senza errori off-by-one, senza underflow di contatori `unsigned` e senza contatori `double`.
- [ ] So usare `break` e `continue` con misura, distinguendo il comportamento di `continue` tra `for` e `while` e l'interazione con `switch`.
- [ ] So scrivere cicli annidati con contatori distinti e formulare l'invariante di ciclo e la prova di terminazione per un ciclo.
