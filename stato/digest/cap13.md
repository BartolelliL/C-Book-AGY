# Digest Capitolo 13 — Dati a basso livello

## Termini definiti e glossario
- **Bit** (*binary digit*): unità minima di informazione in memoria, vale `0` oppure `1`.
- **LSB / MSB**: bit meno significativo (posizione `0`) e bit più significativo (posizione $N-1$).
- **Esadecimale**: sistema posizionale in base `16` (`0`–`9`, `A`–`F`), in cui ogni cifra corrisponde a `4` bit (*nibble*).
- **Complemento a due**: codifica obbligatoria in C23 per gli interi con segno in cui il bit più significativo ha peso negativo $-2^{N-1}$.
- **Larghezza esatta**: tipi interi di `<stdint.h>` (`int8_t`..`uint64_t`) di dimensione garantita senza bit di riempimento.
- **Maschera di bit** (*bitmask*): valore intero usato con operatori bit a bit per leggere, impostare, azzerare o invertire bit specifici.
- **Unione** (`union`): tipo aggregato i cui campi si sovrappongono tutti a offset `0`, con un solo **campo attivo** alla volta.
- **Unione etichettata** (*tagged union*): `struct` che abbina un `enum` (etichetta) e una `union` per tracciare il campo attivo.
- **Campi di bit** (*bit-fields*): campi di `struct` con larghezza esplicita in bit (`tipo nome : N;`).
- **Ordine dei byte** (*endianness*): disposizione in memoria dei byte di un intero multibyte (**little-endian**: LSB all'indirizzo più basso; **big-endian**: MSB all'indirizzo più basso).
- **Allineamento** (*alignment*): vincolo che impone all'indirizzo di un oggetto di essere multiplo di una potenza di due (`alignof`).
- **Padding**: byte di riempimento inseriti dal compilatore dentro o in coda a una `struct` per soddisfare i vincoli di allineamento.
- Termini del glossario usati: *comportamento definito*, *comportamento dipendente dall'implementazione*, *comportamento indefinito*, *comportamento non specificato*, *promozioni intere*, *inizializzatore designato*, *letterale composto*.

## Concetti spiegati
- Numerazione binaria ed esadecimale, letterali C23 `0b...` e `0x...` con separatori `'`, complemento a due su $N$ bit.
- Tipi a larghezza fissa (`intN_t`, `uintN_t`, `intptr_t`, `uintptr_t`, `SIZE_MAX`) in `<stdint.h>` e macro `PRI*` in `<inttypes.h>`.
- Operatori bit a bit (`&`, `|`, `^`, `~`) e spostamenti (`<<`, `>>`), quattro idiomi su maschere, estrazione/impacchettamento di sotto-campi, trappole delle promozioni intere e precedenza di `!=` su `&`.
- `union`, inizializzazione posizionale/designata/`{}`, campo attivo e unioni etichettate gestite tramite `switch`.
- Campi di bit (`unsigned int`, `signed int`, `bool`), aritmetica modulare, campi anonimi e `: 0`, divieti su `&`/`sizeof`/`offsetof`, limiti di portabilità.
- Endianness, ispezione via `const unsigned char *`/`const uint8_t *`, *byte swap* e serializzazione portabile in `uint8_t[]`.
- `alignof` (C23), `offsetof` (`<stddef.h>`), calcolo del padding interno e di coda, riordino dei campi per allineamento decrescente.

## Esempi e scenari
- `13.1-a`: conversione `int8_t`/`uint8_t`, `SIZE_MAX`, round-trip puntatore con `uintptr_t` (`campioni`, `p_orig`, `addr`).
- `13.2-a`: impacchettamento/estrazione colore ARGB `uint32_t` e registro `uint16_t` con flag `constexpr`.
- `13.3-a`: telemetria `messaggio_telemetria_t` (quota, tensione, sigla) e confronto `sizeof` con `struct` equivalente.
- `13.4-a`: `stato_dispositivo_t` con campi di bit, overflow modulare su `livello`, esportazione in `uint16_t`.
- `13.5-a`: codifica/decodifica big-endian e little-endian di `0x12345678U` in `uint8_t[4]`.
- `13.6-a`: confronto `record_sparso_t` (24 B) vs `record_compatto_t` (16 B) con `alignof` e `offsetof`.

## Esercizi
- `13.1` — *Analizzatore di parole a 16 bit in complemento a due con `<stdint.h>` e `<inttypes.h>`*: converte `uint16_t` in `int16_t` senza UB, formatta in binario, conta bit a `1` e calcola statistiche. Difficoltà: 3/5.
- `13.2` — *Codificatore e decodificatore di istruzioni a 32 bit per una mini-CPU con maschere e spostamenti*: gestisce comandi `ENC`, `DEC`, `FLG` su `uint32_t`. Difficoltà: 3/5.
- `13.3` — *Valutatore di celle di un foglio di calcolo basato su unioni etichettate*: implementa `foglio[8]` con `INT`, `REAL`, `TXT`, `ADD`, `CLR` e propagazione errori. Difficoltà: 3/5.
- `13.4` — *Configurazione di porte di uno switch di rete con campi di bit ed esportazione portabile*: gestisce `porta_bf_t[4]` con `SET`, `IMP`, `INC_PRIO` ed export `uint16_t`. Difficoltà: 3/5.
- `13.5` — *Serializzatore e decodificatore di trame binarie in formato big-endian e little-endian*: `PACK`, `UNPACK_BE`, `UNPACK_LE` su `uint8_t[8]` con `swap_u16`/`swap_u32`. Difficoltà: 4/5.
- `13.6` — *Calcolatore e ottimizzatore di layout di `struct` con `alignof`, `offsetof` e riduzione del padding*: verifica `struct` reali e calcola layout/riordino di campi letti da `stdin`. Difficoltà: 4/5.

## Rinvii
- Richiami indietro: cap. 2 (tipi interi, separatore `'`), cap. 3 (overflow, UB, operatori logici, promozioni intere), cap. 10 (puntatori), cap. 12 (`sizeof`, `struct`, `enum`, divieto di `s1 == s2`).
- Rinvii in avanti: cap. 20 (salvataggio strutture su file binari), cap. 22 (`uintptr_t` per allocatori e `alignas`), cap. 26 (unioni etichettate per token, valori e nodi AST dell'interprete).

## Affermazioni forti
- In C23 tutti gli interi con segno usano obbligatoriamente il complemento a due, ma l'overflow con segno resta sempre comportamento indefinito.
- Spostamenti `<<` e `>>` vanno sempre eseguiti su tipi senza segno con $0 \le k < W$ (altrimenti UB o dipendente dall'implementazione).
- Leggere un campo inattivo di una `union` è risultato non specificato; l'ispezione dei byte grezzi è definita solo tramite `const unsigned char *` / `const uint8_t *`.
- Mai dichiarare un campo di bit come `int` semplice; vietato applicare `&`, `sizeof`, `offsetof` ai campi di bit; non usarli per formati esterni.
- I byte di padding hanno contenuto non specificato: mai confrontare `struct` byte per byte.

## Stile del codice
- Standard C23 (`bool`, `true`, `false`, `constexpr`, `alignof`, `{}` per zero-inizializzazione, `enum nome : int`, letterali `0b` e `'`).
- Tipi `<stdint.h>` e macro `PRI*` di `<inttypes.h>`; `typedef struct`/`union`/`enum` con suffisso `_t` e nomi in `snake_case` italiano.
- Parentesi esplicite nei confronti bit a bit e cast espliciti prima di `<<` o dopo `~` su tipi piccoli.
- Validazione dell'input con errori su `stderr` e `EXIT_FAILURE`.
