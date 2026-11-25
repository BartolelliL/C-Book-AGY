# Digest — Capitolo 2: Variabili e tipi

## Termini definiti e glossario
- **variabile** (*variable*): oggetto in memoria dotato di nome e tipo il cui valore può essere letto e modificato durante l'esecuzione.
- **dichiarazione** (*declaration*): costrutto che introduce il nome e il tipo di una variabile, funzione o tipo nel programma.
- **inizializzazione** (*initialization*): assegnazione del valore iniziale a una variabile nel momento stesso in cui viene definita.
- **tipo di dato** (*data type*): insieme di valori rappresentabili e di operazioni lecite su un oggetto o su un'espressione.
- **specificatore di formato** (*format specifier*): segnaposto introdotto da `%` in funzioni come `printf` (e `sscanf`) che indica come interpretare o stampare un valore.
- **costante** (*constant*): valore o oggetto di sola lettura che non può essere modificato dopo la sua definizione.
- Altri termini usati: identificatore, assegnamento, virgola mobile, comportamento indefinito, comportamento dipendente dall'implementazione, promozione predefinita degli argomenti, operatore `sizeof`, `size_t`.

## Concetti spiegati
- Dichiarazione, inizializzazione (`=`) e assegnamento successivo senza ripetere il tipo.
- Regole sugli identificatori C e convenzione del libro (`snake_case` italiano senza accenti per variabili, MAIUSCOLO per costanti).
- Rischio di leggere variabili locali non inizializzate (rappresentazione indeterminata e comportamento indefinito).
- Tipi fondamentali: `int` con modificatori (`short`, `long`, `long long`, `signed`, `unsigned`) e suffissi (`L`, `LL`, `U`); separatore di cifre C23 (`'`); `double` (scelta predefinita) e `float`; `char` (1 byte, letterali `'A'`, distinto da `"A"`); `bool`, `true`, `false` (parole chiave native in C23).
- Specificatori di formato in `printf`: `%d`, `%u`, `%ld`, `%lu`, `%lld`, `%llu`, `%f`, `%c`, `%zu`, `%%`; precisione (`.N`), larghezza minima di campo e allineamento a sinistra (`-`); promozioni predefinite degli argomenti.
- Costanti con `const` (sola lettura, anche a tempo di esecuzione) e `constexpr` (C23, costante nota a tempo di compilazione, controlli severi sull'inizializzatore).
- Operatore `sizeof`, tipo `size_t` (`<stddef.h>`, `%zu`) e costanti di `<limits.h>` (`CHAR_BIT`, `CHAR_MIN`/`MAX`, `SCHAR_*`, `UCHAR_MAX`, `SHRT_*`, `USHRT_MAX`, `INT_*`, `UINT_MAX`, `LONG_*`, `ULONG_MAX`, `LLONG_*`, `ULLONG_MAX`); distinzione tra garanzie dello standard e dettagli dipendenti dall'implementazione (es. `long` a 4 byte su Windows 64-bit e 8 byte su Linux/macOS).

## Esempi e scenari
- Variabili ricorrenti: `punti_vita`, `giorno`, `mese`, `zona`, `temperatura_c`, `pressione_hpa`, `umidita`, `pioggia_mm`, `POSTI_MASSIMI`, `PREZZO_INTERO`, `dim_int`.
- Programmi guidati: punti vita di un personaggio (`2.1-a`), scheda libro di biblioteca (`2.2-a`), bollettino meteo allineato (`2.3-a`), configurazione sala cinematografica (`2.4-a`) + errore modifica costante (`2.4-d`), diagnostica `sizeof` e `<limits.h>` (`2.5-a`).

## Esercizi
- **2.1 — Aggiornare il contatore di un'aula studio**: dichiarare, inizializzare e aggiornare `posti_liberi` stampando tre stati con `%d`. Difficoltà: 1/5.
- **2.2 — Scheda di un satellite meteorologico**: dichiarare cinque variabili (`long` con separatore C23, `int`, `double`, `char`, `bool`) e stamparle. Difficoltà: 2/5.
- **2.3 — Prospetto di un impianto fotovoltaico**: stampare tabella allineata con `%u`, `%lld`, larghezza minima, precisione decimale e `%%`. Difficoltà: 2/5.
- **2.4 — Parametri di configurazione di una stampante 3D**: combinare costanti `constexpr` e `const` e stamparle formattate. Difficoltà: 2/5.
- **2.5 — Tabella di dimensioni e limiti dei tipi**: usare `sizeof` in costanti `size_t` (`%zu`) e stampare `CHAR_BIT` e limiti di `<limits.h>`. Difficoltà: 3/5.

## Rinvii
- Capitolo 3: comportamento indefinito (2.1), virgola mobile e limiti di precisione (2.2), calcoli e confronti tra valori (2.99).
- Capitolo 5: `sscanf` (2.3), lettura da tastiera per `const` (2.4).
- Capitolo 7: protezione di valori ricevuti da funzioni con `const` (2.4).
- Capitolo 8: dimensione di un array con `constexpr` (2.4).
- Capitolo 9: stringhe terminate da carattere speciale (2.2).
- Capitolo 10: aggirare `const` provoca comportamento indefinito (2.4).
- Capitolo 13: tipi interi a larghezza fissa in `<stdint.h>` (2.5).
- Capitolo 21: funzioni variadiche (2.3).

## Affermazioni forti
- Inizializzare sempre ogni variabile locale al momento della dichiarazione; leggerne una non inizializzata provoca comportamento indefinito.
- Usare uno specificatore di formato non coerente con il tipo in `printf` (o meno argomenti) provoca comportamento indefinito.
- `sizeof(char)` è sempre `1`; il segno di `char` semplice dipende dall'implementazione.
- `constexpr int LIMITE = 3.7;` in C23 è un errore di compilazione (nessun troncamento silenzioso).

## Stile del codice
- Header ordinati alfabeticamente (`<limits.h>`, `<stddef.h>`, `<stdio.h>`).
- Variabili in `snake_case` italiano senza accenti, costanti in `MAIUSCOLO`, suffissi `L`/`U` espliciti sui letterali, `const` e `constexpr` usati per valori immutabili.
