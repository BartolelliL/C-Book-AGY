# Capitolo 5 — Leggere dalla tastiera

> **In questo capitolo imparerai a:**
> - Leggere una riga di testo dalla tastiera in modo sicuro con `fgets`
> - Convertire righe di testo in valori numerici con `sscanf` verificando il valore restituito
> - Gestire in modo corretto gli errori di formato e la fine dell'input (`nullptr` ed `EOF`), segnalando gli errori su `stderr` con `fprintf`
> - Leggere ed elaborare singoli caratteri con `getchar` e `putchar`

> **Ti servono:** i capitoli 1–4 (`printf`, tipi di dato, specificatori di formato, `sizeof`, cast esplicito, `if`/`else`, `switch`, valutazione a corto circuito e comportamento indefinito).

Nei capitoli precedenti hai imparato a dichiarare variabili, eseguire calcoli e prendere decisioni con `if` e `switch`. Tutti i programmi scritti finora, però, avevano un limite evidente: i dati su cui lavoravano erano fissati nel codice sorgente. Ogni volta che volevi provare un caso diverso, dovevi modificare il sorgente e ricompilare l'eseguibile.

Un programma reale riceve i dati dall'esterno mentre è in esecuzione: un utente che digita alla tastiera, un file di misure, oppure l'uscita di un altro programma collegato dal terminale. In C, leggere dati dall'esterno richiede attenzione perché l'input dell'utente non è mai garantito: qualcuno può premere Invio senza scrivere nulla, digitare lettere dove ti aspetti un numero, inserire caratteri extra o chiudere il canale di ingresso prima del previsto.

In questo capitolo imposterai un approccio solido e portabile per leggere dalla tastiera. Imparerai a leggere intere righe di testo in sicurezza con `fgets`, a estrarne i numeri con `sscanf` controllando ogni possibile errore, a separare i messaggi diagnostici dall'uscita normale usando `stderr` e `fprintf`, e infine a lavorare su singoli caratteri con `getchar` e `putchar`.

## 5.1 Leggere una riga di testo con `fgets`

Finora i tuoi programmi hanno soltanto scritto verso lo schermo tramite `printf`. Per interagire davvero con chi li esegue devono poter fare anche il percorso inverso: ricevere testo dalla tastiera. In C, l'ingresso e l'uscita non sono legati direttamente a uno specifico dispositivo fisico, ma passano attraverso un concetto più generale.

Quando un programma legge caratteri dalla tastiera o stampa testo sul terminale, opera su uno **stream** (*stream*): l'astrazione di un canale sequenziale di caratteri o byte usato per leggere dati in ingresso o scrivere dati in uscita. Trattare tastiera, schermo e file come stream significa poter usare le stesse funzioni della libreria standard indipendentemente da dove arrivino davvero i dati. All'avvio di ogni programma C, `<stdio.h>` mette automaticamente a disposizione lo stream di ingresso predefinito, chiamato `stdin` (*standard input*), collegato di norma alla tastiera.

Per conservare una riga di testo letta da `stdin`, una singola variabile `char` non basta, perché contiene un solo carattere. Serve un **buffer** (*buffer*): un'area temporanea di memoria usata per accumulare dati durante la lettura, la scrittura o la formattazione. In questo capitolo dichiariamo un buffer di testo usando l'idioma:

<!-- cod: id=5.1-b tipo=frammento -->
```c
char riga[100];
```

Questa dichiarazione riserva in memoria 100 byte contigui capaci di ospitare una sequenza di caratteri. Per ora trattala come una formula fissa per preparare spazio sufficiente a una riga di testo: studieremo in dettaglio gli array nel capitolo 8 e le stringhe nel capitolo 9.

Per riempire il buffer leggendo da `stdin` usiamo la funzione `fgets`, dichiarata in `<stdio.h>`:

<!-- cod: id=5.1-c tipo=frammento -->
```c
char riga[100];
fgets(riga, (int)sizeof(riga), stdin);
```

I tre argomenti di `fgets(buffer, n, stream)` hanno un significato preciso:

- `buffer`: il nome del buffer in cui salvare i caratteri letti (qui `riga`);
- `n`: la capienza massima del buffer in byte, passata come `int`. Usare `(int)sizeof(riga)` invece di ripetere `100` evita disallineamenti se in futuro cambi la dimensione del buffer (ricorda dal capitolo 2 che `sizeof` produce un `size_t`, quindi il cast `(int)` rende esplicita la conversione al tipo richiesto da `fgets`);
- `stream`: il canale da cui leggere, cioè `stdin` per la tastiera.

La regola di comportamento di `fgets` è definita con esattezza dallo standard C23 (a patto che `n >= 1` e che `buffer` abbia almeno `n` byte): `fgets(buffer, n, stdin)` legge dallo stream `stdin` al più `n - 1` caratteri, fermandosi non appena incontra il carattere di ritorno a capo `'\n'` oppure la fine dell'input, e aggiunge automaticamente un carattere di chiusura interna (`'\0'`, che approfondiremo nel capitolo 9) subito dopo l'ultimo carattere letto. Proprio per lasciare spazio a questo carattere di chiusura interna, in un buffer di `100` byte possono entrare al massimo `99` caratteri letti dall'utente.

Un dettaglio fondamentale è che `fgets` **conserva `'\n'` nel buffer** se la riga letta è abbastanza corta da farlo entrare. Per esempio, se digiti `Anna` e premi Invio, dentro `riga` vengono memorizzati i caratteri `'A'`, `'n'`, `'n'`, `'a'`, `'\n'` seguiti da `'\0'`:

```text
Indice:      0     1     2     3     4     5    ...  99
Contenuto: [ 'A' | 'n' | 'n' | 'a' | '\n'| '\0'| ... ]
```

Quando poi stampi il contenuto del buffer con `printf` usando lo specificatore di formato `%s`, `printf` scrive tutti i caratteri fino al carattere di chiusura interna, compreso quel `'\n'` finale. Per questo motivo, scrivendo `printf("Nome: %s", riga);`, il cursore andrà già a capo senza bisogno di un secondo `\n` nella stringa di formato.

Che cosa succede se l'utente non fornisce più dati e chiude lo stream di ingresso prima che `fgets` riesca a leggere anche un solo carattere? Si verifica la condizione di **fine dell'input** (*end of file*): la condizione in cui uno stream non contiene più dati da leggere, segnalata da `EOF` o da `nullptr`. Nel caso di `fgets`, se la lettura fallisce per fine dell'input o per un errore di lettura, la funzione restituisce la parola chiave `nullptr` (in caso di successo restituisce invece il buffer stesso). Il controllo va fatto sempre, subito dopo la chiamata:

<!-- cod: id=5.1-d tipo=frammento -->
```c
if (fgets(riga, (int)sizeof(riga), stdin) == nullptr) {
    printf("Errore: nessuna riga letta.\n");
    return 1;
}
```

> **C23** — La parola chiave `nullptr` è stata introdotta dallo standard C23 per rappresentare in modo sicuro e tipizzato il valore nullo (lo approfondiremo nel capitolo 10). Se compili con uno standard precedente (C17 o C11), al posto di `nullptr` devi scrivere la macro `NULL`, definita in `<stdio.h>` e `<stddef.h>`.

Potresti incontrare in vecchi manuali una funzione chiamata `gets` per leggere una riga dalla tastiera. Non usarla mai: `gets` non accetta la dimensione del buffer, quindi se l'utente digita più caratteri di quelli disponibili la funzione scrive oltre la fine della memoria riservata, provocando comportamento indefinito e gravi falle di sicurezza. Per questa ragione `gets` è stata rimossa dallo standard C già da anni e in questo libro è vietata. Adottare `fgets` fin dal primo giorno significa abituarsi a leggere sempre per righe intere e con un limite esplicito di lunghezza.

> **Se vieni da Python** — In Python `input()` restituisce una stringa di lunghezza arbitraria eliminando automaticamente il ritorno a capo finale. In C `fgets` legge in un buffer di dimensione fissa, conserva `'\n'` se rientra nella capienza del buffer e segnala la fine dell'input restituendo `nullptr`.

### Esempio guidato

Il programma seguente simula la registrazione a un circolo di lettura. Legge da `stdin` il nome del lettore e il titolo del libro preferito in due buffer da 100 byte usando `fgets`, verifica che nessuna delle due letture incontri `nullptr` e stampa il riepilogo con `%s`.

<!-- cod: id=5.1-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    char nome_lettore[100];
    char titolo_libro[100];

    printf("Inserisci il tuo nome:\n");
    if (fgets(nome_lettore, (int)sizeof(nome_lettore), stdin) == nullptr) {
        printf("Errore: fine dell'input durante la lettura del nome.\n");
        return 1;
    }

    printf("Inserisci il titolo del libro preferito:\n");
    if (fgets(titolo_libro, (int)sizeof(titolo_libro), stdin) == nullptr) {
        printf("Errore: fine dell'input durante la lettura del titolo.\n");
        return 1;
    }

    printf("--- Scheda circolo di lettura ---\n");
    printf("Lettore: %s", nome_lettore);
    printf("Libro preferito: %s", titolo_libro);
    return 0;
}
```

```input
Sara Conti
Il barone rampante
```

```output
Inserisci il tuo nome:
Inserisci il titolo del libro preferito:
--- Scheda circolo di lettura ---
Lettore: Sara Conti
Libro preferito: Il barone rampante
```

Analizziamo il funzionamento del programma blocco per blocco:

- Le righe `char nome_lettore[100];` e `char titolo_libro[100];` riservano due buffer distinti, ciascuno capace di contenere fino a 99 caratteri utili più il carattere di chiusura interna.
- Prima di ogni `fgets`, `printf` stampa un invito terminato da `\n`.
- La condizione `if (fgets(nome_lettore, (int)sizeof(nome_lettore), stdin) == nullptr)` esegue la lettura e controlla immediatamente il risultato. Se lo stream termina prima di leggere qualsiasi carattere, il programma avvisa l'utente e termina con `return 1;`.
- Nelle ultime due `printf` manca `\n` alla fine della stringa di formato (`"Lettore: %s"` e `"Libro preferito: %s"`). Nell'output, però, le due righe compaiono regolarmente una sotto l'altra, perché `fgets` ha conservato in ciascun buffer il `'\n'` digitato con il tasto Invio. Se avessi scritto `"Lettore: %s\n"`, avresti ottenuto una riga vuota indesiderata tra una voce e l'altra.

> **Approfondimento — Quando la riga supera la capienza del buffer**
> Che cosa accade se dichiari `char riga[10];` e l'utente digita una parola di 15 caratteri seguita da Invio? `fgets` non scrive mai fuori dal buffer: legge in sicurezza soltanto i primi 9 caratteri, aggiunge il carattere di chiusura interna e termina. I caratteri rimanenti (insieme al `'\n'`) non vanno perduti, ma restano in attesa nello stream `stdin` e saranno restituiti dalla chiamata a `fgets` successiva. Inoltre, in questo caso il buffer non contiene `'\n'`. Nei capitoli 6 e 9 vedrai come riconoscere una riga troncata e svuotare i caratteri residui con un ciclo.

### Esercizio 5.1 — Scheda di iscrizione al torneo di scacchi

**Descrizione**

Scrivi un programma C che chieda all'utente il nome del giocatore e il nome del circolo di appartenenza, leggendo due righe da `stdin` in due buffer `char` di `100` byte mediante `fgets` e `(int)sizeof(...)`. Prima di ciascuna lettura stampa l'invito terminato da ritorno a capo (`Inserisci il nome del giocatore:` e `Inserisci il circolo di appartenenza:`). Dopo ogni chiamata a `fgets`, controlla se il valore restituito è `nullptr`; in tal caso stampa un messaggio di errore e termina restituendo `1`. Se entrambe le letture riescono, stampa il riepilogo esattamente come nell'esempio di esecuzione usando `%s` (ricordando che `fgets` conserva il ritorno a capo presente nell'input) e restituisci `0`.

**Concetti da tenere a mente**

- stream `stdin`
- buffer `char[]` e `(int)sizeof(...)`
- lettura sicura di righe con `fgets`
- controllo della fine dell'input con `nullptr` (C23)
- stampa del testo del buffer con `%s`

**Domande guida**

1. Quale vantaggio offre passare `(int)sizeof(buffer)` a `fgets` rispetto a scrivere la dimensione numerica in due punti diversi del programma?
2. Che cosa restituisce `fgets` quando incontra la fine dell'input prima di leggere qualsiasi carattere?
3. Perché nelle righe finali di stampa con `%s` non devi aggiungere un altro ritorno a capo se la riga letta da `fgets` termina già con `'\n'`?
4. Quanti caratteri utili al massimo può contenere un buffer dichiarato di 100 byte quando viene passato a `fgets`?

**Esempio di esecuzione**

```input
Marco Bianchi
Cavallo Nero
```

```output
Inserisci il nome del giocatore:
Inserisci il circolo di appartenenza:
=== ISCRIZIONE TORNEO ===
Giocatore: Marco Bianchi
Circolo: Cavallo Nero
```

## 5.2 Estrarre numeri da una riga con `sscanf`

Con `fgets` sei riuscito a leggere una riga di testo dalla tastiera e a conservarla in un buffer `char`. Ma quel buffer contiene caratteri, non numeri: se l'utente digita `42`, in memoria ci sono i due caratteri `'4'` e `'2'`, non l'intero `42` su cui puoi eseguire somme o divisioni. Per fare calcoli devi convertire il testo nei tipi numerici del C (`int`, `long`, `unsigned int`, `double`) oppure estrarre un singolo `char`.

La strategia che adotterai in tutto il libro divide il lavoro in due passi nettamente separati:

1. leggi sempre l'intera riga da `stdin` dentro un buffer con `fgets`;
2. estrai i valori dal buffer in memoria con `sscanf`.

Separare lettura ed estrazione ti dà il pieno controllo su ciò che l'utente digita: la riga viene consumata per intero da `stdin` anche se contiene un errore di formato, evitando che caratteri sbagliati restino bloccati nello stream a rovinare le letture successive.

La funzione `sscanf` (*string scan formatted*, dichiarata in `<stdio.h>`) analizza il testo già presente in un buffer secondo una stringa di formato e scrive i valori convertiti nelle variabili indicate:

<!-- cod: id=5.2-b tipo=frammento -->
```c
char riga[128];
int eta = 0;
double altezza = 0.0;

// Dopo aver letto la riga con fgets:
int letti = sscanf(riga, "%d %lf", &eta, &altezza);
```

Nota il simbolo `&` davanti a `eta` e a `altezza`. Senza `&`, una funzione C riceverebbe soltanto una copia del valore della variabile e non potrebbe modificarla. Il simbolo `&` indica a `sscanf` dove si trova la variabile affinché possa scrivervi il risultato della conversione. Per ora trattalo come un idioma obbligatorio davanti a ogni variabile di destinazione passata a `sscanf` (lo vedremo nel capitolo 10, quando studieremo i puntatori).

Gli specificatori di formato di `sscanf` somigliano a quelli di `printf`, ma presentano differenze cruciali che non puoi ignorare:

| Tipo della variabile | Specificatore in `sscanf` | Note |
|---|---|---|
| `int` | `%d` | Salta eventuali spazi bianchi iniziali |
| `long` | `%ld` | Salta eventuali spazi bianchi iniziali |
| `unsigned int` | `%u` | Salta eventuali spazi bianchi iniziali |
| `double` | `%lf` | **Mai** `%f` (che è solo per `float`) |
| `char` | `%c` oppure `" %c"` | `%c` legge anche spazi e `'\n'`; `" %c"` salta gli spazi bianchi prima del carattere |

Fai particolare attenzione a due punti della tabella:

- Per leggere un `double` in `sscanf` devi scrivere `%lf`, non `%f`. Lo specificatore `%f` in `sscanf` corrisponde a un `float`, mentre per un `double` serve la `l` di *long float*.
- Lo specificatore `%c`, a differenza di `%d` e `%lf`, **non salta** gli spazi bianchi né i ritorni a capo. Se una riga contiene `15 A` e scrivi `sscanf(riga, "%d%c", &n, &codice)`, in `codice` finisce lo spazio `' '` invece di `'A'`. Inserire uno spazio nella stringa di formato — cioè `"%d %c"` oppure `" %c"` — istruisce `sscanf` a saltare zero o più caratteri di spaziatura (spazi, tabulazioni, `'\n'`) prima di leggere il carattere desiderato.

Secondo lo standard C23, fornire uno specificatore di formato che non corrisponde al tipo dell'argomento (per esempio `%f` per un `double`), oppure dimenticare `&` davanti alla variabile di destinazione, provoca **comportamento indefinito**: il compilatore con `-Wall -Wextra` ti avviserà spesso, ma lo standard non garantisce nulla sull'esecuzione del programma.

Una singola chiamata a `sscanf` può estrarre più valori dalla stessa riga, separati da spazi. Per sapere se la conversione è riuscita, devi **sempre** controllare il valore restituito da `sscanf`:

- restituisce il numero di elementi convertiti e assegnati con successo (da `0` fino al numero di specificatori presenti nella stringa di formato);
- restituisce la costante negativa `EOF` se la lettura fallisce prima ancora della prima conversione (per esempio quando la riga è vuota o contiene solo spazi bianchi).

Proprio per questo motivo il controllo corretto confronta il risultato con il numero esatto di valori attesi:

<!-- cod: id=5.2-c tipo=frammento -->
```c
if (sscanf(riga, "%d %lf", &eta, &altezza) != 2) {
    printf("Errore: inserisci un intero e un numero decimale.\n");
    return 1;
}
```

Non scrivere mai `if (sscanf(...) != 0)` pensando che significhi "ha letto almeno un valore": su una riga vuota `sscanf` restituisce `EOF`, che è un intero negativo e quindi è diverso da `0`! Confrontare sempre con il numero atteso (`== 2` per il successo, `!= 2` per l'errore) intercetta in un colpo solo sia gli errori di formato (`0` o `1`) sia la riga vuota (`EOF`).

Infine, `sscanf` ha un limite importante da conoscere fin d'ora: se l'utente digita un numero troppo grande per entrare nel tipo di destinazione (per esempio una sequenza di trenta cifre per un `int`), la conversione in `sscanf` provoca **comportamento indefinito** in C23. Quando servirà gestire in modo completamente sicuro anche l'overflow in ingresso, useremo funzioni dedicate come `strtol` e `strtod` (lo vedremo nel capitolo 14).

> **Se vieni da Python** — In Python converti il testo in numero con `int()` o `float()`, che sollevano un'eccezione `ValueError` se il formato è errato. In C non esistono eccezioni: `sscanf` segnala l'esito tramite il proprio valore di ritorno intero, che devi controllare esplicitamente con un `if`.

### Esempio guidato

Il programma seguente calcola la resa chilometrica e il consumo di carburante per passeggero di un viaggio in auto. Legge due righe da `stdin` con `fgets`: dalla prima estrae la distanza percorsa in chilometri e i litri consumati (`double`), dalla seconda estrae il numero di passeggeri (`int`). Controlla sia `fgets` sia `sscanf` e verifica che i valori siano strettamente positivi prima di dividere.

<!-- cod: id=5.2-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    char riga[128];
    double distanza_km = 0.0;
    double litri_consumati = 0.0;
    int passeggeri = 0;

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr ||
        sscanf(riga, "%lf %lf", &distanza_km, &litri_consumati) != 2) {
        printf("Errore: inserisci distanza e litri sulla prima riga.\n");
        return 1;
    }

    if (fgets(riga, (int)sizeof(riga), stdin) == nullptr ||
        sscanf(riga, "%d", &passeggeri) != 1) {
        printf("Errore: inserisci il numero di passeggeri sulla seconda riga.\n");
        return 1;
    }

    if (distanza_km <= 0.0 || litri_consumati <= 0.0 || passeggeri <= 0) {
        printf("Errore: tutti i valori devono essere positivi.\n");
        return 1;
    }

    double km_per_litro = distanza_km / litri_consumati;
    double litri_per_persona = litri_consumati / passeggeri;

    printf("Distanza: %.2f km\n", distanza_km);
    printf("Resa media: %.2f km/L\n", km_per_litro);
    printf("Consumo pro capite: %.2f L\n", litri_per_persona);
    return 0;
}
```

```input
450.5 28.0
4
```

```output
Distanza: 450.50 km
Resa media: 16.09 km/L
Consumo pro capite: 7.00 L
```

Osserva come funzionano i controlli del programma:

- Il buffer `riga` viene riutilizzato per la seconda chiamata a `fgets`: una volta estratti `distanza_km` e `litri_consumati` nella prima lettura, il testo precedente non serve più.
- Nella condizione `fgets(...) == nullptr || sscanf(...) != 2` entra in gioco la valutazione a corto circuito vista nel capitolo 4: se `fgets` restituisce `nullptr`, `sscanf` non viene nemmeno chiamata, evitando di leggere un buffer non inizializzato (alla prima lettura, comportamento indefinito) o rimasto al contenuto precedente.
- Per i due `double` lo specificatore in `sscanf` è `%lf %lf`, mentre nella `printf` finale è `%.2f`.
- Prima delle divisioni `distanza_km / litri_consumati` e `litri_consumati / passeggeri`, il controllo `<= 0` esclude sia lo zero sia eventuali valori negativi privi di senso fisico.

> **Approfondimento — Perché `%f` in `printf` va bene per `double`, ma in `sscanf` no**
> Quando passi un `float` a `printf`, una regola storica del C (le *promozioni predefinite degli argomenti* nelle funzioni a numero variabile di argomenti) converte automaticamente quel `float` in `double` prima della chiamata; per questo `printf` riceve sempre un `double` e accetta `%f` per entrambi i tipi. Con `sscanf`, invece, non passi il valore della variabile ma il suo indirizzo tramite `&var`, e sugli indirizzi non avviene alcuna promozione automatica: `sscanf` ha bisogno di sapere esattamente quanti byte scrivere in memoria (tipicamente 4 byte per un `float` con `%f`, 8 byte per un `double` con `%lf`). Passare `&var` di tipo `double` con `%f` fa scrivere i byte nel formato sbagliato e in una porzione parziale della variabile, producendo comportamento indefinito.

### Esercizio 5.2 — Riepilogo di una sessione di ricarica elettrica

**Descrizione**

Scrivi un programma C che legga da `stdin` due righe tramite `fgets` (senza stampare inviti) ed estragga i dati con `sscanf`: la prima riga contiene energia erogata in kWh (`double`) e tariffa in euro/kWh (`double`) separati da spazio; la seconda riga contiene i minuti di sosta (`int`) e il codice tessera (`char`: `'A'` o `'a'` per abbonato con sconto del `10%`, `'O'` o `'o'` per occasionale senza sconto). Verifica ogni chiamata a `fgets` rispetto a `nullptr`, controlla che ciascuna chiamata a `sscanf` restituisca esattamente `2`, verifica che i valori numerici siano non negativi e che il codice tessera sia valido (con `switch`); in caso di errore stampa un messaggio e restituisci `1`. Altrimenti calcola costo lordo, sconto, totale da pagare e potenza media in kW (`energia_kwh / (minuti_sosta / 60.0)` solo se `minuti_sosta > 0`, altrimenti stampa `Potenza media: non calcolabile`). Produci l'output con due cifre decimali esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- abbinamento `fgets` + `sscanf`
- specificatore `%lf` per `double` e `" %c"` per `char` in `sscanf`
- idioma `&` davanti alle variabili in `sscanf`
- controllo esatto del valore restituito da `sscanf`
- guardia contro la divisione per zero

**Domande guida**

1. Quale specificatore di formato devi usare in `sscanf` per leggere una variabile di tipo `double` e perché differisce da `printf`?
2. Perché nella seconda chiamata a `sscanf` conviene scrivere uno spazio prima di `%c` nella stringa di formato?
3. Che cosa controlla la condizione `sscanf(...) != 2` e perché non basta controllare `sscanf(...) == 0`?
4. In che modo proteggi il calcolo della potenza media quando i minuti di sosta inseriti valgono `0`?

**Esempio di esecuzione**

```input
24.5 0.60
90 A
```

```output
Energia: 24.50 kWh
Costo lordo: 14.70 euro
Sconto: 1.47 euro
Totale da pagare: 13.23 euro
Potenza media: 16.33 kW
```

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
> Da terminale puoi salvare l'uscita di un programma in un file usando l'operatore `>` (per esempio `./programma > risultato.txt` su Linux e macOS, oppure `programma.exe > risultato.txt` su Windows). Quel comando ridirige soltanto `stdout`: tutto ciò che il programma scrive con `fprintf(stdout, ...)` o `printf(...)` finisce nel file, mentre i messaggi inviati a `stderr` compaiono comunque sul terminale. Se invece stampassi gli errori su `stdout`, un errore di input finirebbe silenziosamente dentro `risultato.txt` al posto dei dati veri, corrompendo il file o mandando in errore il programma successivo che dovesse leggerlo.

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

Al contrario, lo standard C23 non garantisce la contiguità delle lettere dell'alfabeto in tutte le codifiche esistenti, anche se su quasi tutti i sistemi moderni (ASCII/UTF-8) `'A'..'Z'` e `'a'..'z'` sono contigue; per classificare lettere e cifre in modo ancora più pulito useremo le funzioni di `<ctype.h>` (lo vedremo nel capitolo 9).

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
> - sulle piattaforme a 8 bit in cui `char` è **senza segno** (per esempio molti sistemi ARM), i valori di `char` vanno da `0` a `255`: il valore negativo `EOF` viene convertito in un valore non negativo (tipicamente `255` quando `EOF` vale `-1`) e il confronto `c == EOF` risulta **sempre falso**, impedendo al programma di rilevare la fine dell'input;
> - sulle piattaforme a 8 bit in cui `char` è **con segno** (da `-128` a `127`), il byte valido di valore `255` viene tipicamente convertito in `-1` (conversione fuori intervallo dipendente dall'implementazione), che coincide con `EOF` quando questo vale `-1`: il programma interrompe la lettura in anticipo scambiando un dato valido per la fine dello stream.
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

## Riepilogo

- Uno **stream** è un canale sequenziale di caratteri o byte; ogni programma C dispone di `stdin` (ingresso), `stdout` (uscita normale) e `stderr` (messaggi di errore).
- Per leggere una riga di testo in sicurezza si usa `fgets(buffer, (int)sizeof(buffer), stdin)` dentro un **buffer** `char riga[100];` (studieremo array e stringhe nei capitoli 8 e 9). `fgets` legge al più `n - 1` caratteri, conserva `'\n'` se entra nel buffer e restituisce `nullptr` (in C23; `NULL` in C17/C11) in caso di **fine dell'input** o errore di lettura. Non usare mai `gets`.
- Per estrarre valori numerici o caratteri da una riga già letta si usa `sscanf(riga, formato, &var, ...)`, passando `&` davanti a ogni variabile di destinazione (lo vedremo nel capitolo 10) e rispettando gli specificatori esatti: `%d` per `int`, `%ld` per `long`, `%u` per `unsigned int`, `%lf` per `double`, `" %c"` per un `char` saltando gli spazi bianchi. Controlla sempre che `sscanf` restituisca esattamente il numero di valori attesi.
- Per rifiutare caratteri extra in coda a un numero, aggiungi `" %c"` con una variabile `char extra` e verifica `sscanf(riga, "%d %c", &valore, &extra) == 1`. Per gestire in modo sicuro anche l'overflow numerico in ingresso useremo `strtol` e `strtod` (lo vedremo nel capitolo 14).
- I messaggi di errore vanno inviati su `stderr` tramite `fprintf(stderr, ...)`; per comunicare l'esito al sistema operativo si includono `<stdlib.h>` e si restituiscono le costanti portabili `EXIT_SUCCESS` ed `EXIT_FAILURE`.
- Per leggere e scrivere singoli caratteri si usano `getchar()` e `putchar(c)`. Il valore restituito da `getchar()` va sempre memorizzato in una variabile `int` (mai `char`) per distinguerlo senza ambiguità da `EOF`. Le cifre `'0'..'9'` hanno codici contigui, quindi `c - '0'` ricava il valore `0..9` e `'0' + d` il carattere cifra. Nel prossimo capitolo userai i cicli per leggere sequenze di lunghezza arbitraria fino a `EOF` (lo vedremo nel capitolo 6).

## Errori comuni

- **Usare `%f` invece di `%lf` in `sscanf` per una variabile `double`**: in `printf` entrambi usano `%f`, ma in `sscanf` scrivere `%f` per un `double` provoca comportamento indefinito; usa sempre `%lf` per `double`.
- **Dimenticare il simbolo `&` davanti al nome della variabile numerica in `sscanf`**: scrivere `sscanf(riga, "%d", valore)` invece di `&valore` causa comportamento indefinito; controlla sempre gli avvisi del compilatore.
- **Controllare il ritorno di `sscanf` con `!= 0` invece che con `== numero_atteso`**: su una riga vuota o di soli spazi `sscanf` restituisce `EOF` (un valore negativo), quindi `!= 0` risulterebbe vero per errore.
- **Salvare il risultato di `getchar()` in una variabile `char` invece che in `int`**: impedisce di distinguere in modo portabile `EOF` dai caratteri validi, causando il mancato riconoscimento della fine dell'input o interruzioni premature della lettura a seconda del segno di `char`.
- **Dimenticare che `fgets` conserva il carattere `'\n'` alla fine della riga letta**: quando il ritorno a capo entra nel buffer, aggiungerlo di nuovo nella `printf` con `%s` produce righe vuote doppie o confronti inattesi.
- **Ignorare eventuali caratteri extra dopo un numero in `sscanf`**: senza il controllo con `" %c"` e una variabile `char` di appoggio, un input malformato come `12abc` viene accettato silenziosamente come `12`.

## Prima di proseguire

- [ ] So leggere una riga di testo da `stdin` con `fgets(buffer, (int)sizeof(buffer), stdin)`, verificare `nullptr` e gestire il `'\n'` conservato nel buffer.
- [ ] So abbinare `fgets` e `sscanf` usando gli specificatori corretti (`%d`, `%ld`, `%u`, `%lf`, `" %c"`), l'idioma `&` e il controllo esatto del valore restituito.
- [ ] So distinguere e gestire fine dell'input, errori di formato, caratteri spuri in coda (con `"%d %c"`) e valori fuori intervallo, stampando gli errori su `stderr` con `fprintf` e restituendo `EXIT_FAILURE` o `EXIT_SUCCESS`.
- [ ] So leggere e scrivere singoli caratteri con `getchar()` (salvato sempre in `int`) e `putchar()`, controllare `EOF` e `'\n'`, e convertire le cifre decimali tramite `'0'`.
