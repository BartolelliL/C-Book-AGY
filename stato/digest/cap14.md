# Digest Capitolo 14 — Puntatori avanzati

## Termini definiti e glossario
- **Puntatore a puntatore** (*pointer to pointer*, `T **pp`): variabile che contiene l'indirizzo di un'altra variabile puntatore `T *p`.
- **Array di puntatori**: array i cui elementi sono indirizzi (es. `const char *nomi[]` o `char **`) anziché blocchi di dati copiati.
- **Matrice dinamica**: struttura bidimensionale sullo heap rappresentabile per righe (`T **m`, incluso *array frastagliato*) o in un unico blocco contiguo (`T *dati` con indice `i * cols + j`).
- **Aliasing**: condizione in cui due puntatori diversi raggiungono la stessa area di memoria.
- **`restrict`**: qualificatore per puntatori a oggetti che promette al compilatore l'assenza di aliasing con altri puntatori non derivati da esso quando il dato viene modificato.
- **Valore sentinella** (*sentinel value*): valore speciale (`'\0'`, `nullptr`) che chiude una sequenza segnalandone la fine senza contatore separato.
- **Puntatore pendente** (*dangling pointer*): puntatore che conserva l'indirizzo di un oggetto la cui durata di vita è terminata o che è stato liberato.
- Termini del glossario usati: *passaggio per valore*, *decadimento di array*, *comportamento definito*, *comportamento indefinito*, *comportamento dipendente dall'implementazione*, *perdita di memoria*, *uso dopo la liberazione*, *AddressSanitizer*.

## Concetti spiegati
- Indirezione multipla (`pp`, `*pp`, `**pp`), controlli difensivi a entrambi i livelli (`pp != nullptr && *pp != nullptr`) e quattro idiomi (`realloc` su parametro d'uscita, scambio puntatori, `free` con azzeramento, cursore `const char **`).
- Matrici dinamiche per righe (`R + 1` allocazioni, pulizia parziale su fallimento, ordine inverso di `free`), blocco contiguo (controllo `righe > SIZE_MAX / cols`), approccio ibrido e decadimento `T[R][C]` → `T (*)[C]` (non `T **`).
- Argomenti `int main(int argc, char *argv[])` con `argv[argc] == nullptr`, conversioni sicure `strtol`/`strtoul`/`strtoll`/`strtoull`/`strtod`, controllo `endptr`, `errno = 0`, `ERANGE` (`<errno.h>`) e `HUGE_VAL` (`<math.h>`), insidie di `atoi` e `strtoul` con `'-'`.
- `const` su più livelli letto da destra a sinistra, divieto di conversione implicita `T **` → `const T **` (API corrette: `const char *const *` o `char *const *`), uso di `restrict`.
- Valori sentinella (costo lineare, slot extra `+1`/`+2`) e quattro cause di puntatori pendenti (stack locale, blocco interno, mancato azzeramento dopo `free`, spostamento da `realloc`) con prevenzione tramite indici `size_t`.

## Esempi e scenari
- `14.1-a`: `scambia_stringhe`, `espandi_array`, `libera_e_azzera` su array dinamico `misure` e `etichetta_a`/`b`.
- `14.2-a`: griglia `3x4` `per_righe` vs `contigua`, scambio di righe e somma colonna.
- `14.3-a`: parser `--base` con `analizza_interi` e `prova_strtod` su input da `argv` o `demo[]`.
- `14.4-b` (errore) e `14.4-a`: blocco di `char **` → `const char **`; `stampa_etichette`, `scala_disgiunto` (`restrict`), `scala_sul_posto`.
- `14.5-a`: lista dinamica `comandi` terminata da `nullptr` con `attivo_idx` immune a `realloc`.

## Esercizi
- `14.1` — *Parser di coppie chiave=valore e tabella dinamica gestiti tramite puntatori a puntatori*: `estrai_coppia`, `aggiungi_coppia`, `scambia_puntatori`, `libera_tabella` con `SWAP`. Difficoltà: 3/5.
- `14.2` — *Trasposizione di matrice contigua e ordinamento di righe tramite array di puntatori*: confronta `matrice_contigua_t` (trasposta) e `int **per_righe` (ordinamento stabile per somma). Difficoltà: 4/5.
- `14.3` — *Elaboratore di argomenti da riga di comando con `strtol`, `strtod` ed `errno`*: gestisce `--base`, `--scala`, overflow e doppia modalità `argv`/`stdin`. Difficoltà: 4/5.
- `14.4` — *Filtro di segnale con `restrict`, gestione sicura della sovrapposizione e `const` a due livelli*: `media_mobile_restrict` con buffer temporaneo su fette sovrapposte ed `energia_fette`. Difficoltà: 4/5.
- `14.5` — *Elenco dinamico terminato da sentinella `nullptr` con segnalibro per indice immune a `realloc`*: `elenco_t` con `ADD`, `MARK`, `DEL`, `LIST`. Difficoltà: 3/5.

## Rinvii
- Richiami indietro: cap. 9 (stringhe), cap. 10 (puntatori, decadimento, `const`), cap. 11 (`malloc`/`calloc`/`realloc`/`free`, AddressSanitizer), cap. 12 (`struct`, `typedef`).
- Rinvii in avanti: cap. 25 (località in memoria e cache nelle matrici contigue).

## Affermazioni forti
- Dereferenziare `pp == nullptr` o `*pp == nullptr` è comportamento indefinito; passare `nullptr` come `nptr` a `strto*` è comportamento indefinito.
- `atoi`, `atol`, `atof` vanno sempre evitate; `errno = 0;` va scritto sempre prima di `strtol`/`strtod`.
- Un array 2D statico `int a[3][4]` non decade mai a `int **`, ma a `int (*)[4]`.
- La conversione implicita `T **` → `const T **` è vietata in C; violare `restrict` provoca comportamento indefinito.
- Leggere o confrontare in modo ordinato un puntatore pendente dopo `free`/`realloc` provoca comportamento indefinito.

## Stile del codice
- Standard C23 (`nullptr`, `bool`, `true`, `false`, `constexpr`).
- Uso sistematico di `sizeof(*ptr)` nelle allocazioni, controllo overflow `r > SIZE_MAX / c`, copia locale del cursore prima di avanzarlo.
- Pulizia completa su errori di allocazione, azzeramento puntatori dopo `free`, messaggi d'errore su `stderr` con `EXIT_FAILURE`/`EXIT_SUCCESS`.
