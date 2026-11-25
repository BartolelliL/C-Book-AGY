# Digest — Capitolo 20: File e dati binari

## Termini definiti e glossario
- **File di testo** (*text file*): file aperto in modalità testo contenente righe di caratteri leggibili, con eventuale traduzione automatica dei fine riga (`'\n'` ↔ `"\r\n"`).
- **File binario** (*binary file*): file aperto con il modificatore `"b"` (`"rb"`, `"wb"`, `"r+b"`, ecc.) in cui i byte sono letti e scritti come sequenza grezza senza traduzioni.
- **Accesso casuale** (*random access*): spostamento diretto dell'indicatore di posizione in un file binario mediante `fseek`, `ftell` e `rewind` per leggere o aggiornare record senza scorrere l'intero file.
- **Serializzazione** (*serialization*): conversione di strutture dati in memoria in una sequenza portabile di byte o testo da salvare su file e ricostruire in seguito.
- **Numero magico** (*magic number*): sequenza fissa di byte iniziali (es. `"STAZ"`, `"CATB"`) che identifica il formato di un file binario.
- **Somma di controllo** (*checksum*): valore calcolato sui byte del payload per rilevare corruzioni.
- Altri termini usati: stream, `FILE` (tipo opaco), buffer, `EOF`, `feof`, `ferror`, `clearerr`, elaborazione a blocchi (streaming), `tmpfile`, `SEEK_SET`/`SEEK_CUR`/`SEEK_END`, ordine dei byte (little-endian / big-endian), padding, retrocompatibilità, comportamento dipendente dall'implementazione, valori non specificati, comportamento indefinito.

## Concetti spiegati
- Gestione file di testo con `fopen` (`"r"`, `"w"`, `"a"`, `"r+"`, `"w+"`, `"a+"`, `"wx"`/`"w+x"`), `fprintf`, `fputs` (senza `'\n'` automatico), `fputc`, `fflush`, `fclose` (controllo obbligatorio in scrittura), `rename` e `remove` (aggiornamento sicuro tramite file temporaneo).
- Lettura sicura con `fgets` (gestione righe più lunghe del buffer) e `fgetc` (ritorno obbligatorio in `int`, mai `char`); divieto di `while (!feof(fp))`, distinzione post-ciclo tra `ferror(fp)` e `feof(fp)` e ripristino con `clearerr(fp)`.
- File binari a blocchi con `fread(buf, 1, sizeof(buf), fp)` e `fwrite`; regola di alternanza tra lettura e scrittura su stream di aggiornamento (`fflush`/`fseek`/`rewind`).
- Accesso casuale su record a dimensione fissa con `fseek` (`SEEK_SET`, `SEEK_CUR`, `SEEK_END`), `ftell` (tipo `long int`, controllo `-1L` e limite `LONG_MAX`), `rewind` e `tmpfile()`; limiti di portabilità di `SEEK_END` su binari e `ftell` su testo.
- Divieto di `fwrite(&struct, sizeof(struct), 1, fp)` per endianness, padding non specificato, larghezza tipi e puntatori. Serializzazione portabile con `<stdint.h>`, maschere/spostamenti, prefisso di lunghezza per stringhe, intestazione con magic/versione/conteggio/checksum, limiti difensivi prima di `malloc`/`realloc` e caricamento atomico in `tmp`.

## Esempi e scenari
- `20.1-a`: rapporto meteo (`rapporto_esempio.tmp` -> `rapporto_esempio.txt`) con `rename`, append e `remove`.
- `20.2-a`: lettura file di configurazione con buffer da 24 byte, riga troncata, `sscanf`, `fputc` su sola lettura e `clearerr`.
- `20.3-a`: cifratura/decifratura XOR a blocchi da 8 byte su 21 byte e confronto con `memcmp`.
- `20.4-a`: `tmpfile()` con 4 record fissi da 12 byte (`sensore_t`), aggiornamento in loco e `rewind`.
- `20.5-a/c/d` (`formato_stazioni.h`, `formato_stazioni.c`, `main.c`): serializzazione big-endian v1/v2 di stazioni meteo con `"STAZ"` e checksum.

## Esercizi
- **20.1 — Generatore di ricevute testuali con aggiornamento sicuro tramite rename e remove**: comandi `VOCE`/`NOTA`, file temporaneo, `rename`, append e `remove`. Difficoltà: 3/5.
- **20.2 — Analizzatore di file di log con gestione delle righe lunghe e diagnostica feof/ferror/clearerr**: buffer 32 byte, `strtol` con `errno`/`ERANGE`, test `fputc` su `"r"`. Difficoltà: 4/5.
- **20.3 — Compressore e decompressore binario RLE a blocchi con fread e fwrite**: RLE a blocchi da 16 byte attraverso confini di blocco e `memcmp`. Difficoltà: 4/5.
- **20.4 — Archivio binario a record fissi con accesso casuale e aggiornamento in loco su più file**: `archivio_rec.h`/`.c`/`main.c` su `tmpfile()`, record LE 24 byte. Difficoltà: 4/5.
- **20.5 — Serializzatore binario portabile e versionato (v1/v2) con numero magico e checksum**: `catalogo_bin.h`/`.c`/`main.c` LE con `"CATB"`, FNV-1a 32 bit, `CORROMPI` e `TRONCA`. Difficoltà: 5/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 5 (stream e buffer), cap. 9 (stringhe), cap. 11 (memoria dinamica), cap. 12 (`struct`, `enum`), cap. 13 (tipi fissi, endianness, padding), cap. 14 (`strtol`, `strtod`), cap. 19 (programmi su più file e tipi opachi).
- Rinvii in avanti: cap. 21 (diagnostica errori di sistema e rilascio di più risorse su molti percorsi di errore).

## Affermazioni forti
- Mai copiare `FILE` per valore, invocare `fflush` su stream di ingresso o riusare `FILE *` dopo `fclose` (comportamento indefinito).
- Mai usare `while (!feof(fp))` come condizione del ciclo di lettura; salvare sempre `fgetc` in `int`, mai in `char`.
- Su stream di aggiornamento, alternare lettura e scrittura senza `fseek`/`rewind` (o `fflush` dopo scrittura) è comportamento indefinito.
- Mai serializzare `struct` grezze con `fwrite(&s, sizeof(s), 1, fp)`.
- Validare sempre conteggi e lunghezze letti da file prima di chiamare `malloc`/`realloc`.

## Stile del codice
- Standard C23 (`nullptr`, `bool`, `constexpr`, `{}`), `<stdint.h>`, `<inttypes.h>`, `<stdio.h>`, `<stdlib.h>`, `<string.h>`.
- Funzioni helper `static` nei `.c`, chiusura sicura su tutti i percorsi d'errore, pulizia dei file temporanei con `remove`, `snake_case` italiano, indentazione 4 spazi.
