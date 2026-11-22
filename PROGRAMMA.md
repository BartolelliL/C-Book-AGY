# PROGRAMMA — dal primo programma all'autonomia in C

Questo file e' l'input di P1. E' una PROPOSTA: P1 puo' unire o dividere capitoli (da 15 a 28 in tutto) se motiva la
scelta, ma deve rispettare l'ordine di propedeuticita' e raggiungere il traguardo qui sotto.

Lettori: studenti di 16-18 anni, zero C all'inizio. Standard: C23. Sistema operativo: qualunque (solo libreria
standard, niente POSIX/Windows, niente thread). Il libro e' un **libro di esercizi e di progetto**: ogni sotto-sezione
spiega un concetto e poi fa esercitare, senza dare soluzioni.

## Traguardo del libro

**Concetto di riferimento: una tabella hash generica, scritta come tipo opaco su piu' file.**
Il lettore, a fine libro, deve saperla progettare e scrivere da solo: `void *` per chiavi e valori, puntatori a
funzione per hash, confronto e rilascio, gestione delle collisioni, ridimensionamento (rehashing), regole chiare su
"chi possiede e chi libera" la memoria, header pubblico con tipo opaco, controllo degli errori senza perdite di memoria
e senza comportamento indefinito. Tutto il libro prepara questo traguardo; il progetto finale (un interprete) la usa.

**Livello avanzato (Parte IV)**: il lettore sa progettare allocatori propri, strutture dati e algoritmi non banali (heap, alberi
bilanciati, grafi), usare le tecniche avanzate del linguaggio (macro, `_Generic`, `setjmp`) e scrivere test automatici.

**Autonomia**: alla fine il lettore sa scrivere da solo programmi di qualche centinaio di righe su piu' file, con
strutture dati dinamiche; leggere e correggere codice C altrui; usare gli strumenti di diagnostica (avvisi del
compilatore, sanitizer, debugger); consultare la documentazione dello standard; riconoscere e evitare il comportamento
indefinito.

## Capitoli proposti

### Parte I — Fondamenti
1. **Il primo programma** — cos'e' il C, compilare ed eseguire (in modo neutro rispetto al sistema operativo),
   struttura di un programma, `printf`, commenti, errori e avvisi del compilatore.
2. **Variabili e tipi** — `int`, `double`, `char`, `bool` (C23), dichiarazione e inizializzazione, costanti (`const`,
   `constexpr`), `sizeof`, limiti dei tipi (`<limits.h>`), specificatori di formato.
3. **Operatori ed espressioni** — aritmetici, divisione intera e resto, assegnamenti composti, relazionali, logici,
   precedenza, conversioni di tipo, overflow dei tipi interi, imprecisione dei numeri in virgola mobile.
4. **Leggere dalla tastiera** — `fgets`, conversione di testo in numeri (`strtol`, `sscanf`), controllo degli errori,
   fine dell'input.
5. **Decisioni** — `if`/`else`, `switch`, operatore condizionale, valutazione a corto circuito.
6. **Ripetizioni** — `while`, `do`-`while`, `for`, `break`/`continue`, cicli annidati, invarianti di ciclo.
7. **Funzioni** — definizione, prototipi, parametri passati per valore, `return`, visibilita' delle variabili,
   `static` locale, ricorsione, scomposizione di un problema in funzioni.

### Parte II — Dati e memoria
8. **Array** — array mono e bidimensionali, accessi fuori dai limiti, array e funzioni, ricerca e ordinamento
   elementari, complessita' (idea intuitiva di costo).
9. **Stringhe** — array di `char`, terminatore, `<string.h>`, `<ctype.h>`, confronti, buffer overflow, `snprintf`.
10. **Puntatori** — indirizzi, `&` e `*`, `NULL`/`nullptr`, puntatori e array, aritmetica dei puntatori, passaggio per
    puntatore, `const` e puntatori.
11. **Memoria dinamica** — stack e heap, `malloc`/`calloc`/`realloc`/`free`, array dinamici, perdite di memoria,
    uso dopo `free`, doppia liberazione, strumenti di diagnostica (sanitizer).
12. **Strutture, enumerazioni, typedef** — `struct`, `enum`, `typedef`, array di struct, puntatori a struct, struct
    annidate, copia e passaggio di struct.

### Parte III — Livello intermedio e avanzato
13. **Dati a basso livello** — rappresentazione degli interi (con e senza segno, complemento a due), `<stdint.h>`,
    operatori bit a bit e maschere, spostamenti, campi di bit, `union`, ordine dei byte (endianness), `offsetof`,
    allineamento e padding delle struct.
14. **Puntatori avanzati** — puntatori a puntatori, array di puntatori, matrici dinamiche, `argc`/`argv`, `const`
    correttezza, `restrict`, `NULL` come valore sentinella, puntatori "penzolanti".
15. **Puntatori a funzione** — dichiarazione e uso, callback, `qsort` e `bsearch`, tabelle di funzioni (dispatch).
16. **Programmazione generica con `void *`** — `void *` e conversioni, `memcpy`/`memmove`/`memcmp`, contenitori
    generici (vettore dinamico generico), `_Generic`, `typeof`, `static_assert`, `alignof`.
17. **Strutture dati dinamiche** — liste concatenate (semplici e doppie), pile e code, alberi binari di ricerca,
    regole di possesso della memoria e distruzione.
18. **Tabelle hash** — funzioni di hash, collisioni (concatenamento), fattore di carico e rehashing; la tabella hash
    generica con puntatori a funzione (chiave, confronto, rilascio).
19. **Programmi su piu' file** — header e file sorgenti, `static` e `extern` a livello di file, `inline`, include
    guard, tipi opachi, compilazione separata, come si organizza una libreria.
20. **File e dati binari** — `fopen`/`fclose`/`fgets`/`fprintf`, file di testo e binari, `fread`/`fwrite`/`fseek`/
    `ftell`, salvataggio e caricamento di strutture, formati di file e versioni.
21. **Robustezza e qualita'** — gestione degli errori (valori di ritorno, `errno`, `perror`), il modello `goto cleanup`
    per liberare le risorse, `assert`, funzioni variadiche (`<stdarg.h>`), preprocessore avanzato (macro con
    argomenti, compilazione condizionale, `__FILE__`/`__LINE__`), comportamento indefinito e come lo si cerca (sanitizer,
    debugger), cenni a `volatile` e `signal`.
### Parte IV — Avanzato
22. **Gestione avanzata della memoria** — allocatori scritti da te su un buffer statico allineato (`alignas`): allocatore
    ad arena, a pool e con lista libera (free list); allineamento e padding in pratica; ridurre le chiamate a `malloc`;
    scoprire perdite e corruzioni della memoria; strict aliasing e `restrict` (cosa il compilatore e' autorizzato a supporre).
23. **Strutture dati e algoritmi avanzati** — complessita' (notazione O, verificata contando le operazioni e non misurando
    i secondi), heap binario e coda di priorita', albero AVL (rotazioni), trie, grafi con liste di adiacenza, visite in
    ampiezza e in profondita', cammini minimi (algoritmo di Dijkstra con la coda di priorita'); dove ha senso, in forma
    generica (riuso del capitolo 16).
24. **Tecniche avanzate del linguaggio** — macro avanzate (macro variadiche, `do`-`while(0)`, X-macro), `_Generic` per
    funzioni "sovraccaricate", `inline`, `setjmp`/`longjmp` (uscite non locali, gestione degli errori, coroutine semplici),
    liste intrusive con `offsetof`, macchine a stati con tabelle di puntatori a funzione, campi di bit per formati binari.
25. **Qualita' e prestazioni** — misurare senza tempi (contare le operazioni; `clock` solo in esercizi non verificati),
    localita' dei dati e cache (array di struct contro struct di array), ottimizzazioni del compilatore e comportamento
    indefinito, scrivere test automatici in C (un mini framework con macro), prove con input casuali a seme fisso (fuzzing
    semplice), cenni agli strumenti professionali (debugger, profiler, sanitizer).

### Progetto finale
26. **Progetto finale (difficolta' alta): un interprete per un piccolo linguaggio di programmazione.** Il lettore
    costruisce da zero un interprete che legge un programma scritto in un linguaggio inventato da lui (numeri, variabili,
    espressioni, `if`, `while`, funzioni, istruzione di stampa), lo analizza e lo esegue: scrivere un linguaggio e vederlo
    "girare" e' la cosa piu' stimolante che si possa fare in C. Organizzazione su piu' file (almeno: valori, analizzatore
    lessicale, analizzatore sintattico, valutazione, programma principale), senza perdite di memoria. Usa quasi tutto il libro:
    `union` ed `enum` per i valori e i nodi, ricorsione per l'analisi delle espressioni, memoria dinamica per l'albero del
    programma gestita con l'allocatore ad arena del capitolo 22, la TUA tabella hash generica (capitolo 18) per le variabili
    e le funzioni, puntatori a funzione per le
    funzioni predefinite, gestione degli errori con messaggi chiari. Fasi (una per sotto-sezione, le prime con esercizi che
    preparano i pezzi, l'ultima con il progetto completo):
    26.1 progettare il linguaggio e le strutture dati; 26.2 l'analizzatore lessicale (testo -> elementi); 26.3 l'analizzatore
    sintattico (elementi -> albero, espressioni con precedenza); 26.4 la valutazione e le variabili; 26.5 `if`/`while` e
    funzioni definite dall'utente; 26.6 il progetto completo con prova automatica (programmi in ingresso da tastiera,
    risultati attesi in uscita). Estensione FACOLTATIVA (non verificata automaticamente): un raccoglitore di memoria
    automatico (garbage collector a marcatura e scansione) per i valori dell'interprete). P1 puo' proporre un progetto alternativo di pari complessita' (per esempio una macchina
    virtuale a pila con assemblatore), ma deve usare SOLO concetti dei capitoli 1-25, dividerlo in 4-6 fasi con criteri di
    verifica e prevedere test automatici.

## Vincoli didattici

- Ogni sotto-sezione si chiude con un esercizio; la difficolta' cresce nel capitolo e nel libro (capitoli 1-7:
  da 1 a 3 su 5; capitoli 8-12: da 2 a 4; capitoli 13-21: da 3 a 5; capitoli 22-25: da 4 a 5).
- Gli esercizi non contengono soluzioni: aiutano solo "concetti da tenere a mente" e "domande guida".
- Prima di introdurre un concetto non si usa mai (nemmeno negli esempi).
- Dal capitolo 13 gli esercizi tipici sono programmi di 40-150 righe; dal capitolo 19 possono essere su piu' file.
- Il comportamento indefinito va spiegato quando nasce (cap. 3, 8, 10, 11, 13) e ripreso nei capitoli 21 e 25: il lettore
  deve sapere perche' e' pericoloso, non solo che esiste.
- Nessuna dipendenza da funzioni non standard (niente POSIX/Windows, niente thread).

## Note di progetto (emerse dal primo giro di P1; vanno rispettate se si rilancia P1)

- **Ordine**: Decisioni (capitolo 4) PRIMA di Leggere dalla tastiera (capitolo 5): controllare i valori restituiti richiede `if`.
- **Input**: niente `scanf`/`fscanf`/`atoi`/`atof` (vanno in `non_trattati`). Capitolo 5: `fgets` + `sscanf`, con `nullptr` ed `EOF`
  per la fine dell'input (compromesso dichiarato: buffer `char riga[...]` e `&` presentati come idiomi, con rinvio ai capitoli 8 e 10).
  `strtol`/`strtod` nel capitolo 14.
- **Errori**: `fprintf` e `stderr` nel capitolo 5 (messaggi di errore), `exit` nel capitolo 11 (fallimento di `malloc`).
- **Matematica**: `math.h` con `fabs`, `sqrt`, `pow`, `floor`, `ceil`, `round`, `fmod` nel capitolo 3 (il libro deve ricordare `-lm` su Linux).
- **Programmazione generica**: `void *` nel capitolo 15 PRIMA dei puntatori a funzione (capitolo 16); nel capitolo 11 `malloc` restituisce
  un "puntatore generico" citato in una frase con rinvio al capitolo 15.
- Il progetto finale (capitolo 26) ha come prerequisiti anche i capitoli 17 (alberi) e 20 (file).
- Tutti i testi in italiano con le lettere accentate corrette (mai `e'`, `perche'`).
