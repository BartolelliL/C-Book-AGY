# Digest — Capitolo 5: Leggere dalla tastiera

## Termini definiti e glossario
- **Stream** (*stream*): astrazione di un canale sequenziale di caratteri o byte usato per leggere dati in ingresso o scrivere dati in uscita.
- **Buffer** (*buffer*): area temporanea di memoria usata per accumulare dati durante la lettura, la scrittura o la formattazione.
- **Fine dell'input** (*end of file*): condizione in cui uno stream non contiene più dati da leggere, segnalata da `EOF` o da `nullptr`.
- Altri termini del glossario usati: `stdin` (*standard input*), `stdout`, `stderr`, specificatore di formato, comportamento indefinito, comportamento dipendente dall'implementazione, valutazione a corto circuito.

## Concetti spiegati
- Astrazione degli stream standard (`stdin`, `stdout`, `stderr` in `<stdio.h>`) e separazione tra dati su `stdout` ed errori su `stderr` tramite `fprintf`.
- Lettura di righe in sicurezza con `fgets(buffer, (int)sizeof(buffer), stdin)`: limite `n - 1` caratteri, conservazione di `'\n'`, aggiunta automatica di `'\0'`, controllo di `nullptr` (C23; `NULL` in C17/C11).
- Separazione tra lettura della riga (`fgets`) ed estrazione/conversione (`sscanf`), uso obbligatorio di `&` davanti alle variabili di destinazione.
- Specificatori di `sscanf`: `%d`, `%ld`, `%u`, `%lf` (obbligatorio per `double`), `%c` vs `" %c"` per saltare spazi bianchi.
- Controllo del valore restituito da `sscanf` confrontato con il numero esatto di valori attesi (non `!= 0`, perché riga vuota restituisce `EOF`).
- Classificazione in ordine dei 4 errori di input: fine input, riga vuota/non numerica, caratteri spuri in coda (rilevati con `" %c"` + variabile `extra`), valore fuori intervallo.
- Codici di uscita portabili `EXIT_SUCCESS` ed `EXIT_FAILURE` in `<stdlib.h>`.
- Lettura e scrittura di singoli caratteri con `getchar()` e `putchar()`: tipo `int` obbligatorio per `getchar()` per distinguere ogni `unsigned char` da `EOF`.
- Contiguità garantita delle cifre `'0'..'9'` (`c - '0'` e `'0' + d`).

## Esempi e scenari
- **5.1**: registrazione a un circolo di lettura (`nome_lettore`, `titolo_libro`).
- **5.2**: calcolo resa chilometrica e consumo pro capite (`riga`, `distanza_km`, `litri_consumati`, `passeggeri`, `km_per_litro`, `litri_per_persona`).
- **5.3**: registrazione voto universitario con eventuale lode (`voto`, `lode`, `extra`, `con_lode`).
- **5.4**: validazione sigla operativa di 3 caratteri (`c1`..`c4`, `priorita`).

## Esercizi
- **5.1 — Scheda di iscrizione al torneo di scacchi**: leggere nome giocatore e circolo in due buffer `char[100]` con `fgets` e stampare il riepilogo. Difficoltà: 1/5.
- **5.2 — Riepilogo di una sessione di ricarica elettrica**: leggere kWh, tariffa, minuti di sosta e codice tessera con `fgets` + `sscanf`, validare con `switch` e calcolare costo, sconto e potenza media. Difficoltà: 2/5.
- **5.3 — Validatore di prenotazione per una sala conferenze**: validare fila e posto con `"%d %c"` e `extra`, segnalare errori su `stderr` con `EXIT_FAILURE` e stampare settore/posizione su `stdout`. Difficoltà: 2/5.
- **5.4 — Verifica di un codice di accesso con `getchar` e `putchar`**: leggere 4 caratteri + terminatore in `int` con `getchar()`, validare formato, calcolare numero e cifra di controllo e stampare con `putchar`. Difficoltà: 3/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 1–4 in apertura; cap. 2 (`sizeof` che produce `size_t`); cap. 4 (valutazione a corto circuito).
- Rinvii in avanti: cap. 6 (cicli `while` per svuotare residui e leggere fino a `EOF`); cap. 8 (array); cap. 9 (stringhe, `'\0'`, `<ctype.h>`); cap. 10 (`nullptr`, `&` e puntatori); cap. 14 (`strtol` e `strtod` per overflow).

## Affermazioni forti
- `gets` è vietata in questo libro e rimossa dallo standard C.
- Usare sempre `fgets` + `sscanf` per leggere righe e numeri; mai `scanf("%s")` o simile (non usato).
- In `sscanf` per `double` usare sempre `%lf`, mai `%f` (comportamento indefinito).
- Controllare sempre `sscanf(...) == numero_atteso` (mai `!= 0`).
- Salvare sempre il risultato di `getchar()` in `int`, mai in `char`, e confrontare sempre con `EOF`, mai con `-1`.
- Rispettare sempre l'ordine: fine input -> formato `sscanf` -> intervallo.

## Stile del codice
- Standard C23: uso di `nullptr` e `bool`, ma `05_01`–`05_02` usano `printf` + `return 1;`/`return 0;` per gli errori, mentre da `05_03` in poi si usano `fprintf(stderr, ...)`, `<stdlib.h>`, `EXIT_SUCCESS` ed `EXIT_FAILURE` (in `05_04` `printf` per output normale e `fprintf(stderr, ...)` per errori).
- Identificatori in `snake_case` italiano senza accenti (`nome_lettore`, `distanza_km`), buffer locali `char riga[100]` o `char riga[128]` con `(int)sizeof(riga)`.
- Graffe sempre presenti, 4 spazi, `int main(void)`.
