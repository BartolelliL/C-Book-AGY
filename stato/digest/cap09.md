# Digest — Capitolo 9: Stringhe

## Termini definiti e glossario
- **Stringa** (*string*): sequenza di caratteri memorizzata in un array di `char` e chiusa dal terminatore nullo `'\0'`.
- **Terminatore nullo** (*null terminator*): carattere `'\0'` (valore numerico `0`, distinto da `'0'` e `"0"`) che segna la fine della stringa.
- **Buffer overflow**: scrittura di dati oltre la fine della memoria riservata a un buffer, causa di comportamento indefinito e vulnerabilità di sicurezza.
- Altri termini del glossario usati: capacità del buffer, lunghezza logica, *off-by-one*, locale `"C"`, comportamento indefinito, comportamento dipendente dall'implementazione.

## Concetti spiegati
- Differenza tra capacità (`sizeof`) e lunghezza logica (al più `N - 1` caratteri utili); array senza `'\0'` (es. `char rotta[4] = "ciao";`) provoca lettura fuori dai limiti.
- Inizializzazione, scorrimento fino a `'\0'`, rimozione di `'\n'` di `fgets`, stampa con `printf("%s", s)` e `puts(s)` (che aggiunge `'\n'`).
- Passaggio a funzioni: `const char s[]` per lettura, `(char s[], size_t capienza)` per scrittura; nota su UTF-8 (caratteri multi-byte) vs ASCII.
- `<string.h>`: `strlen` (mai nella condizione del `for`), `strcmp`/`strncmp` (confrontare sempre con `< 0`, `== 0`, `> 0`), ricerca (`strchr`, `strrchr`, `strstr`, `strpbrk` -> `nullptr`, C23 preserva `const`), prefissi (`strcspn` per `riga[strcspn(riga, "\n")] = '\0'`, `strspn`), copia/concatenazione (`strcpy`, `strcat`, `strncpy` che non garantisce `'\0'`, `strncat` che vuole lo spazio residuo). Divieto di sovrapposizione sorgente/destinazione.
- `<ctype.h>`: `isalpha`, `isdigit`, `isalnum`, `isspace`, `isupper`, `islower`, `isxdigit`, `ispunct`, `isprint`, `tolower`, `toupper`. Ritorno `0` o `!= 0` (mai `== 1`). Cast obbligatorio `(unsigned char)` per evitare comportamento indefinito su `char` negativi.
- `snprintf(dest, capienza, ...)`: garantisce `'\0'` se `capienza > 0`, controllo `scritti < 0 || (size_t)scritti >= capienza`, `snprintf(nullptr, 0, ...)` per misurare prima; `sprintf` bandita.
- Gestione righe lunghe dopo `fgets`: controllo di `'\n'` e svuotamento di `stdin` con `getchar()` fino a `'\n'`/`EOF` (distinguendo il caso esatto `cap - 1`).

## Esempi e scenari
- **9.1**: codice spedizione `"IT-2026"` ed `etichetta` (`lunghezza_manuale`).
- **9.2**: nomi di file di registro (`nome1`, `nome2`, `percorso`, prefisso `"log_"`).
- **9.3**: conteggio categorie di caratteri e conversione *Title Case* (`frase`, `inizio_parola`).
- **9.4**: etichetta di spedizione (`codice`, `tratta`, `etichetta[64]`, `corta[20]`).
- **9.5**: gestione nome utente e tag (`svuota_se_troncata`, `copia_sicura`, `accoda_sicura`).

## Esercizi
- **9.1 — Analisi e inversione manuale di una stringa senza `<string.h>`**: `rimuovi_newline`, `conta_carattere`, `e_palindroma`, `inverti_stringa`. Difficoltà: 2/5.
- **9.2 — Filtro e ordine lessicografico di etichette con `<string.h>`**: validare con `strspn`, contare prefissi/occorrenze/separatori, min/max lessicografico e raccolta con `strncat`. Difficoltà: 3/5.
- **9.3 — Normalizzatore di testo e validatore di colore esadecimale con `<ctype.h>`**: `normalizza_testo` (spazi e minuscolo), `normalizza_colore_hex` (`#RRGGBB`), conteggi `isalnum`/`ispunct`/`isprint`. Difficoltà: 3/5.
- **9.4 — Generatore di record CSV con verifica di troncamento tramite `snprintf`**: `formatta_record` su `completo[128]` e `anteprima[24]`, calcolo caratteri omessi. Difficoltà: 3/5.
- **9.5 — Raccolta sicura di nomi in buffer limitati contro il buffer overflow**: `leggi_riga_limitata` su `char riga[16]` e `accoda_voce` atomica in `elenco[40]`. Difficoltà: 4/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 2, 5, 6, 7, 8 in apertura; cap. 2 (`char` con/senza segno); cap. 5 (`fgets`); cap. 8 (array e confronto `==`).
- Rinvii in avanti: cap. 10 (uso dei puntatori restituiti da `strchr`/`strstr` e `const` C23); cap. 11 (`snprintf(nullptr, 0, ...)` con `malloc`, sanitizer); cap. 19 (`#define`).

## Affermazioni forti
- `sprintf` è bandita da questo libro.
- Non chiamare mai `strlen(s)` nella condizione di un ciclo `for`.
- Con `strcmp` confrontare sempre con `0`, mai con `== 1` o `== -1`.
- Cast `(unsigned char)` sempre obbligatorio prima di ogni funzione di `<ctype.h>`, senza eccezioni; mai confrontare `is*` con `== 1`.
- Ogni funzione che modifica una stringa di destinazione deve ricevere sempre `(char dest[], size_t capienza)`.
- In `sscanf` specificare sempre `%Ns`.

## Stile del codice
- Standard C23 (`nullptr`, `bool`, `const` preservato in C23), `<stddef.h>` quando serve `size_t` prima di `<stdio.h>` (`09_01`).
- Gestione errori uniforme su `stderr` con `EXIT_FAILURE`/`EXIT_SUCCESS`.
