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
- **Salvare il risultato di `getchar()` in una variabile `char` invece che in `int`**: impedisce di distinguere in modo portabile `EOF` dai caratteri validi, causando cicli infiniti o troncamenti prematuri a seconda del segno di `char`.
- **Dimenticare che `fgets` conserva il carattere `'\n'` alla fine della riga letta**: quando il ritorno a capo entra nel buffer, aggiungerlo di nuovo nella `printf` con `%s` produce righe vuote doppie o confronti inattesi.
- **Ignorare eventuali caratteri extra dopo un numero in `sscanf`**: senza il controllo con `" %c"` e una variabile `char` di appoggio, un input malformato come `12abc` viene accettato silenziosamente come `12`.

## Prima di proseguire

- [ ] So leggere una riga di testo da `stdin` con `fgets(buffer, (int)sizeof(buffer), stdin)`, verificare `nullptr` e gestire il `'\n'` conservato nel buffer.
- [ ] So abbinare `fgets` e `sscanf` usando gli specificatori corretti (`%d`, `%ld`, `%u`, `%lf`, `" %c"`), l'idioma `&` e il controllo esatto del valore restituito.
- [ ] So distinguere e gestire fine dell'input, errori di formato, caratteri spuri in coda (con `"%d %c"`) e valori fuori intervallo, stampando gli errori su `stderr` con `fprintf` e restituendo `EXIT_FAILURE` o `EXIT_SUCCESS`.
- [ ] So leggere e scrivere singoli caratteri con `getchar()` (salvato sempre in `int`) e `putchar()`, controllare `EOF` e `'\n'`, e convertire le cifre decimali tramite `'0'`.
