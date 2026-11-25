# Capitolo 13 — Dati a basso livello

> **In questo capitolo imparerai a:**
> - Spiegare la rappresentazione binaria in complemento a due e usare i tipi a dimensione fissa di `<stdint.h>` e `<inttypes.h>`
> - Manipolare singoli bit con operatori bit a bit, maschere e spostamenti evitando comportamento indefinito
> - Usare `union` e unioni etichettate e definire campi di bit con consapevolezza dei loro limiti
> - Analizzare ordine dei byte, allineamento e padding delle `struct` usando `alignof` e `offsetof`

> **Ti servono:** Capitoli 2, 3, 10 e 12 (tipi interi, `sizeof`, overflow e comportamento indefinito, puntatori, `struct` ed `enum`).

Finora hai trattato le variabili come contenitori di valori matematici: un `int` conserva un intero, una `struct` raggruppa più campi sotto un unico nome e un puntatore conserva l'indirizzo di un oggetto. Nel capitolo precedente, tuttavia, hai già incontrato un primo indizio di ciò che accade sotto la superficie: la dimensione restituita da `sizeof` per una `struct` può superare la somma delle dimensioni dei suoi campi.

Quando scrivi software di sistema, protocolli di rete, formati di file binari, driver o strutture dati compatte ad alte prestazioni, non basta conoscere il valore logico di una variabile: devi controllare con esattezza quanti bit occupa, come quei bit sono codificati, in quale ordine i byte sono disposti in memoria e dove il compilatore inserisce eventuali spazi vuoti tra un campo e l'altro. Il C nasce proprio per darti questo livello di controllo senza rinunciare alla portabilità.

In questo capitolo aprirai il cofano della rappresentazione dei dati in memoria. Imparerai a scegliere tipi interi di larghezza garantita, a manipolare singoli bit e sotto-campi senza cadere nel comportamento indefinito, a sovrapporre dati in memoria in modo sicuro tramite le unioni etichettate, a valutare quando convengono i campi di bit e a leggere e progettare il layout fisico di byte e strutture su qualsiasi architettura.

## 13.1 Interi in binario, complemento a due e `<stdint.h>`

Ogni dato presente nella memoria di un calcolatore è memorizzato come una sequenza finita di **bit** (*binary digit*), ciascuno dei quali può valere `0` oppure `1`. Quando scrivi un programma che dialoga con un dispositivo hardware, decodifica un file binario o gestisce flag di stato, pensare ai numeri solo in base dieci nasconde la struttura reale dei dati. Conoscere la rappresentazione in base due e in base sedici, e saper scegliere tipi interi dalla larghezza esattamente nota, è il primo passo per lavorare in modo affidabile a basso livello.

### Base 2, base 16 e letterali binari ed esadecimali

In un sistema posizionale di base $b$, ciascuna cifra moltiplica una potenza della base. Su $8$ bit senza segno, i bit sono numerati da destra a sinistra da $0$ (il bit meno significativo, **LSB**, *least significant bit*) a $7$ (il bit più significativo, **MSB**, *most significant bit*), con pesi $2^0 = 1, 2^1 = 2, \dots, 2^7 = 128$. La sequenza `10100110` vale quindi $128 + 32 + 4 + 2 = 166$.

Scrivere lunghe sequenze di `0` e `1` è scomodo e soggetto a errori di lettura. Per questo si usa la base sedici (**esadecimale**), le cui cifre sono `0`–`9` e `A`–`F` (o `a`–`f`, che rappresentano i valori da `10` a `15`). Poiché $16 = 2^4$, **ogni singola cifra esadecimale corrisponde esattamente a un gruppo di 4 bit** (un *nibble*):

```text
Binario:      1010   0110
Esadecimale:    A      6     ->  0xA6  (10 * 16 + 6 = 166)
```

In C puoi scrivere un letterale intero in esadecimale con il prefisso `0x` oppure `0X` (per esempio `0xA6`, `0x1234ABCD`) e, a partire dallo standard C23, direttamente in binario con il prefisso `0b` oppure `0B` (per esempio `0b10100110`). Per rendere leggibili le sequenze lunghe puoi abbinare entrambi i prefissi al separatore di cifre `'` introdotto nel capitolo 2: `0b1010'0110` o `0x1234'5678`.

> **C23** — I letterali binari con prefisso `0b`/`0B` e l'obbligo della rappresentazione in complemento a due per gli interi con segno sono stati standardizzati in C23. Con compilatori più vecchi (C11 o C17) i letterali `0b...` non fanno parte dello standard portabile: in quei casi usa sempre la notazione esadecimale `0x...`.

### La codifica in complemento a due

Come si rappresentano i numeri negativi usando soltanto bit `0` e `1`? Lo standard C23 stabilisce che tutti i tipi interi con segno adottano obbligatoriamente il **complemento a due** (*two's complement*), cioè la codifica binaria degli interi con segno in cui il bit più significativo ha peso negativo.

Su $N$ bit, i bit da $0$ a $N - 2$ conservano il consueto peso positivo $2^i$, mentre il bit $N - 1$ (il bit più significativo) ha peso $-2^{N-1}$. Se il bit più significativo è `0`, il numero è non negativo (da $0$ a $2^{N-1} - 1$); se è `1`, il numero è negativo (da $-2^{N-1}$ a $-1$).

```text
Su 8 bit (int8_t):   bit 7    6    5    4    3    2    1    0
Peso:                 -128  +64  +32  +16   +8   +4   +2   +1

  0111'1111  =  +64 + 32 + 16 + 8 + 4 + 2 + 1           = +127  (INT8_MAX)
  0000'0001  =                                       +1 =   +1
  0000'0000  =                                        0 =    0
  1111'1111  = -128 + 64 + 32 + 16 + 8 + 4 + 2 + 1      =   -1
  1111'1011  = -128 + 64 + 32 + 16 + 8      + 2 + 1     =   -5
  1000'0000  = -128                                     = -128  (INT8_MIN)
```

Questa codifica ha due proprietà fondamentali:

1. **Un solo zero** (`0000'0000`) e **calcolo uniforme dell'opposto**: per ottenere la rappresentazione binaria di `-x` si invertono tutti i bit di `x` (operazione che nella prossima sotto-sezione vedrai indicata con `~x`) e si somma `1`: `-x` coincide con `~x + 1` modulo $2^N$. Per esempio, partendo da `+5` (`0000'0101`), invertire i bit produce `1111'1010` e aggiungere `1` dà `1111'1011`, cioè `-5`.
2. **Asimmetria degli estremi**: l'intervallo su $N$ bit è $[-2^{N-1},\; 2^{N-1} - 1]$. Su $8$ bit il minimo è `-128` e il massimo è `+127`: l'opposto di `INT8_MIN` (`+128`) non è rappresentabile in `int8_t`. Lo stesso vale per `int16_t`, `int32_t` e `int64_t`.

Secondo lo standard C23, la rappresentazione in complemento a due degli interi con segno è **definita**, ma l'overflow aritmetico sui tipi con segno rimane comunque **comportamento indefinito** (come hai visto nel capitolo 3). Anche se conosci i bit sottostanti, non puoi quindi fare affidamento sul riavvolgimento di un intero con segno: per l'aritmetica modulare si usano sempre i tipi senza segno.

### Tipi a larghezza esatta in `<stdint.h>`

Come hai visto nel capitolo 2, i tipi fondamentali `int` e `long` hanno solo larghezze minime garantite: `long` occupa $8$ byte sulla maggior parte dei sistemi Linux e macOS a 64 bit, ma solo $4$ byte su Windows a 64 bit. Se devi leggere un campo intero da $32$ bit da un file o memorizzare un contatore che richiede esattamente $64$ bit, `int` e `long` non bastano.

L'header `<stdint.h>` definisce i tipi interi a **larghezza esatta** (senza bit di riempimento interni):

| Con segno | Senza segno | Larghezza | Limiti in `<stdint.h>` |
|---|---|---|---|
| `int8_t` | `uint8_t` | 8 bit | `INT8_MIN`, `INT8_MAX`, `UINT8_MAX` |
| `int16_t` | `uint16_t` | 16 bit | `INT16_MIN`, `INT16_MAX`, `UINT16_MAX` |
| `int32_t` | `uint32_t` | 32 bit | `INT32_MIN`, `INT32_MAX`, `UINT32_MAX` |
| `int64_t` | `uint64_t` | 64 bit | `INT64_MIN`, `INT64_MAX`, `UINT64_MAX` |

Oltre ai tipi a larghezza fissa, `<stdint.h>` fornisce la costante `SIZE_MAX` (il valore massimo rappresentabile da `size_t`) e due tipi speciali pensati per i puntatori: `intptr_t` e `uintptr_t`. Questi ultimi sono tipi interi (con segno e senza segno) sufficientemente ampi da contenere un indirizzo di memoria convertito da un puntatore a oggetto e riconvertito al tipo di puntatore originale senza perdita di bit, sia su architetture a 32 bit sia su architetture a 64 bit. Li userai raramente nei calcoli quotidiani, ma risultano essenziali quando si ispezionano allineamenti o si implementano allocatori a basso livello (lo vedremo nel capitolo 22).

### Stampare in modo portabile con `<inttypes.h>`

Poiché `int64_t` può essere definito come `long` su un sistema e come `long long` su un altro, usare `%ld` o `%lld` direttamente in `printf` non è portabile e produce avvisi del compilatore. L'header `<inttypes.h>` (che include automaticamente `<stdint.h>`) risolve il problema fornendo macro stringa per ogni larghezza:

- `PRId8`, `PRId16`, `PRId32`, `PRId64` per stampare in decimale con segno (`intN_t`);
- `PRIu8`, `PRIu16`, `PRIu32`, `PRIu64` per stampare in decimale senza segno (`uintN_t`);
- `PRIx8`, `PRIx16`, `PRIx32`, `PRIx64` per stampare in esadecimale minuscolo (`uintN_t`).

In C due letterali stringa adiacenti vengono concatenati automaticamente dal compilatore. Per usare una macro `PRI*` si chiude la stringa di formato subito dopo `%` (o dopo eventuali modificatori di larghezza come `%04`), si inserisce la macro e si riapre la stringa:

<!-- cod: id=13.1-b tipo=frammento -->
```c
uint32_t codice = 0x002A'1F0CU;
int64_t saldo = -42'000'000'000LL;
printf("codice=0x%08" PRIx32 " saldo=%" PRId64 "\n", codice, saldo);
```

> **Se vieni da Python** — In Python gli interi hanno precisione arbitraria e non possiedono una larghezza fissa in bit (quindi negare o invertire un intero non agisce su 8, 16 o 32 bit fissi). In C ogni tipo di `<stdint.h>` ha una larghezza esatta in complemento a due e un intervallo finito di valori.

### Esempio guidato

Il programma seguente dichiara valori mediante letterali binari (`0b...`) ed esadecimali (`0x...`) usando i tipi di `<stdint.h>`, mette a confronto la stessa sequenza di 8 bit vista come `int8_t` (complemento a due) e come `uint8_t`, verifica `SIZE_MAX` e la conversione reversibile di un puntatore tramite `uintptr_t` e stampa ogni risultato con le macro `PRI*` di `<inttypes.h>`.

<!-- cod: id=13.1-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    uint8_t byte_bin = 0b1010'0110U;
    uint32_t parola_hex = 0x1A2B'3C4DU;

    printf("byte_bin: dec=%" PRIu8 " hex=0x%02" PRIx8 "\n", byte_bin, byte_bin);
    printf("parola_hex: dec=%" PRIu32 " hex=0x%08" PRIx32 "\n",
           parola_hex, parola_hex);

    int8_t campioni[4] = {0, INT8_MAX, -1, INT8_MIN};
    for (size_t i = 0; i < 4; ++i) {
        int8_t s = campioni[i];
        uint8_t u = (uint8_t)s;
        printf("int8_t=%4" PRId8 " -> stessi bit come uint8_t=%3" PRIu8
               " (0x%02" PRIx8 ")\n", s, u, u);
    }

    int valore = 99;
    const int *p_orig = &valore;
    uintptr_t addr = (uintptr_t)p_orig;
    const int *p_ricostruito = (const int *)addr;

    printf("SIZE_MAX >= UINT32_MAX: %d\n", SIZE_MAX >= UINT32_MAX);
    printf("sizeof(uintptr_t) == sizeof(void *): %d\n",
           sizeof(uintptr_t) == sizeof(void *));
    printf("Round-trip puntatore riuscito: %d (valore=%d)\n",
           p_ricostruito == p_orig, *p_ricostruito);

    return 0;
}
```

```output
byte_bin: dec=166 hex=0xa6
parola_hex: dec=439041101 hex=0x1a2b3c4d
int8_t=   0 -> stessi bit come uint8_t=  0 (0x00)
int8_t= 127 -> stessi bit come uint8_t=127 (0x7f)
int8_t=  -1 -> stessi bit come uint8_t=255 (0xff)
int8_t=-128 -> stessi bit come uint8_t=128 (0x80)
SIZE_MAX >= UINT32_MAX: 1
sizeof(uintptr_t) == sizeof(void *): 1
Round-trip puntatore riuscito: 1 (valore=99)
```

Osserva i punti chiave dell'esempio:

- `0b1010'0110U` e `0x1A2B'3C4DU` usano i separatori di cifre per raggruppare rispettivamente 4 bit e 4 cifre esadecimali; la stampa con `PRIu8`, `PRIx8`, `PRIu32` e `PRIx32` funziona in modo identico su qualsiasi compilatore C23.
- Nel ciclo, `uint8_t u = (uint8_t)s;` converte il valore con segno in `uint8_t` modulo $256$, mostrando gli esatti 8 bit della rappresentazione in complemento a due: `-1` corrisponde a `0xff` (`255`), mentre `INT8_MIN` (`-128`) corrisponde a `0x80` (`128`, il solo bit 7 a `1`).
- La conversione `p_orig` → `uintptr_t` → `p_ricostruito` conserva tutti i bit dell'indirizzo: il confronto `p_ricostruito == p_orig` vale `1` e la dereferenziazione `*p_ricostruito` legge correttamente `99`, senza stampare indirizzi numerici non deterministici.

> **Approfondimento — Complemento a due obbligatorio ma overflow ancora indefinito**
> Negli standard C precedenti al C23 erano teoricamente ammesse altre due codifiche storiche per i numeri negativi (modulo e segno, complemento a uno), ormai scomparse dall'hardware moderno. Il C23 ha finalmente imposto il complemento a due come unica rappresentazione valida. Perché, allora, l'overflow di un intero con segno (come `INT32_MAX + 1`) resta comportamento indefinito? Perché assumere che l'overflow con segno non avvenga mai permette al compilatore di eseguire ottimizzazioni importanti nei cicli e nell'aritmetica degli indici (per esempio dedurre che `x + 1 > x` è sempre vero per un `int`). Se ti serve il riavvolgimento modulo $2^N$, usa sempre un tipo senza segno come `uint32_t`.

### Esercizio 13.1 — Analizzatore di parole a 16 bit in complemento a due con `<stdint.h>` e `<inttypes.h>`

**Descrizione**

Scrivi un programma C che includa `<inttypes.h>`, `<stddef.h>`, `<stdint.h>`, `<stdio.h>` e `<stdlib.h>` per analizzare parole binarie a 16 bit. Dichiara prima di `main` tre funzioni: `int16_t interpreta_c2_16(uint16_t u)` (restituisce il valore in complemento a due associato ai 16 bit di `u` senza provocare comportamento indefinito: se `(u & 0x8000U) == 0` restituisce `(int16_t)u`, altrimenti calcola `-(int32_t)((uint16_t)(~u) + 1U)` e lo converte in `int16_t`), `int conta_bit_16(uint16_t u)` (conta i bit a `1` in `u`) e `void formatta_bin16(uint16_t u, char out[20])` (scrive i 16 bit dal più significativo al meno significativo in 4 gruppi di 4 bit separati da `'_'`, es. `1000_0000_0000_0000`). In `main` leggi dalla prima riga `n` (`0 <= n <= 64`) e dalle successive `n` righe un intero decimale non negativo `val <= UINT16_MAX` (`65535`, letto con `"%u %c"` == `1`; in caso di errore stampa su `stderr` e restituisci `EXIT_FAILURE`). Se `n == 0` stampa `Nessuna parola da analizzare.` e restituisci `EXIT_SUCCESS`. Altrimenti per ogni parola `u` (`uint16_t`) stampa con `PRIx16`, `PRIu16`, `PRId16`: `#<i>: hex=0x<4hex> bin=<bin16> u=<u16> c2=<s16> bit1=<k>`, accumulando la somma senza segno in `uint64_t` (`PRIu64`), la somma con segno in `int64_t` (`PRId64`), il minimo e il massimo in complemento a due e il conteggio dei valori negativi e dei valori uguali agli estremi `INT16_MIN` o `INT16_MAX`, stampando il riepilogo esattamente come nell'esempio.

**Concetti da tenere a mente**

- rappresentazione in complemento a due su 16 bit e peso negativo `-32768` del bit 15
- tipi a larghezza esatta `uint16_t`, `int16_t`, `uint64_t`, `int64_t` e limiti `UINT16_MAX`, `INT16_MIN`, `INT16_MAX` (`<stdint.h>`)
- stampa portabile con le macro `PRIx16`, `PRIu16`, `PRId16`, `PRIu64` e `PRId64` (`<inttypes.h>`)
- ricostruzione aritmetica di `~u + 1` su `uint16_t` senza overflow con segno

**Domande guida**

1. Perché la parola `0xFFFF` vale `65535` come `uint16_t` ma vale `-1` quando viene interpretata in complemento a due come `int16_t`?
2. Quale bit di un `uint16_t` stabilisce se il corrispondente valore in complemento a due è negativo e qual è il suo peso?
3. Come funziona la concatenazione della macro `PRId16` o `PRIu64` dentro la stringa di formato di `printf`?
4. Perché per accumulare la somma di molti valori `int16_t` o `uint16_t` è opportuno usare `int64_t` e `uint64_t`?

**Esempio di esecuzione**

```input
4
32767
32768
65535
42
```

```output
#0: hex=0x7fff bin=0111_1111_1111_1111 u=32767 c2=32767 bit1=15
#1: hex=0x8000 bin=1000_0000_0000_0000 u=32768 c2=-32768 bit1=1
#2: hex=0xffff bin=1111_1111_1111_1111 u=65535 c2=-1 bit1=16
#3: hex=0x002a bin=0000_0000_0010_1010 u=42 c2=42 bit1=3
Somma unsigned: 131112, somma c2: 40
Min c2: -32768, max c2: 32767
Negativi: 2, estremi (INT16_MIN/MAX): 2
```

## 13.2 Operatori bit a bit, maschere e spostamenti

Immagina di dover memorizzare otto interruttori booleani (acceso/spento) per configurare un sensore, oppure i quattro canali da 8 bit (alfa, rosso, verde, blu) di un pixel dentro un singolo intero a 32 bit. Usare un `bool` separato per ogni flag spreca spazio, e dividere e moltiplicare per potenze di due per estrarre i singoli campi è verboso e poco espressivo. Il C mette a disposizione gli **operatori bit a bit**, che operano direttamente sui singoli bit degli operandi interi.

### Gli operatori logici bit a bit: `&`, `|`, `^`, `~`

Gli operatori bit a bit eseguono un'operazione logica in parallelo su ogni posizione di bit dei loro operandi interi:

| Operatore | Nome | Risultato sul singolo bit | Esempio su 4 bit (`1010` e `1100`) |
|---|---|---|---|
| `&` | AND bit a bit | `1` solo se entrambi i bit sono `1` | `1010 & 1100` → `1000` |
| `\|` | OR bit a bit | `1` se almeno uno dei due bit è `1` | `1010 \| 1100` → `1110` |
| `^` | XOR bit a bit | `1` se i due bit sono diversi | `1010 ^ 1100` → `0110` |
| `~` | NOT bit a bit (unario) | inverte ogni bit (`0` → `1`, `1` → `0`) | `~1010` → `0101` (su tutti i bit del tipo) |

Agli operatori binari `&`, `|` e `^` corrispondono gli assegnamenti composti `&=`, `|=` e `^=`.

Non confondere mai gli operatori bit a bit (`&`, `|`, `~`) con gli operatori logici booleani (`&&`, `||`, `!`) del capitolo 3:

- `&&`, `||` e `!` trattano l'intero operando come vero (diverso da zero) o falso (zero), producono sempre `0` oppure `1` e applicano la valutazione a corto circuito.
- `&`, `|` e `~` elaborano ciascun bit in modo indipendente, producono un intero e valutano sempre entrambi gli operandi. Per esempio, `0b0100 && 0b0010` vale `1` (entrambi diversi da zero), mentre `0b0100 & 0b0010` vale `0` (nessun bit a `1` in comune).

### Gli operatori di spostamento: `<<` e `>>`

Gli operatori di spostamento fanno scorrere i bit di un intero verso sinistra (`<<`, con assegnamento composto `<<=`) o verso destra (`>>`, con `>>=`):

- **Spostamento a sinistra (`x << k`)** su un tipo senza segno: sposta tutti i bit di `k` posizioni verso il bit più significativo, scarta i `k` bit che escono a sinistra e riempie con `0` le `k` posizioni libere a destra. Se non si perdono bit significativi, equivale a moltiplicare per $2^k$.
- **Spostamento a destra (`x >> k`)** su un tipo senza segno: sposta tutti i bit di `k` posizioni verso il bit meno significativo, scarta i `k` bit che escono a destra e riempie con `0` le `k` posizioni libere a sinistra (spostamento logico). Equivale alla divisione intera per $2^k$.

Attenzione alle regole dello standard C23 sugli spostamenti, perché qui è facile introdurre **comportamento indefinito**:

- In `x << k` e `x >> k`, il conteggio `k` deve soddisfare $0 \le k < W$, dove $W$ è la larghezza in bit del tipo promosso di `x`. Se `k < 0` oppure `k >= W` (per esempio spostare un `uint32_t` di `32` bit), il comportamento è **indefinito**.
- Se `x` ha un tipo con segno: `x << k` è **comportamento indefinito** se `x < 0` oppure se il risultato matematico $x \cdot 2^k$ non è rappresentabile nel tipo promosso (overflow).
- Se `x` ha un tipo con segno negativo (`x < 0`), `x >> k` è **comportamento dipendente dall'implementazione** (molti compilatori propagano il bit di segno `1`, ma lo standard non lo impone).

Regola pratica: esegui **sempre** le manipolazioni di bit e gli spostamenti su tipi interi senza segno (`uint16_t`, `uint32_t`, `uint64_t`, `unsigned int`).

### Maschere di bit e i quattro idiomi fondamentali

Una **maschera di bit** (*bitmask*) è un valore intero usato con gli operatori bit a bit per leggere, impostare, azzerare o invertire specifici bit. Per isolare il singolo bit in posizione `k` (contando da `0` per il bit meno significativo) si costruisce la maschera `1U << k` (o `1ULL << k` per tipi a 64 bit):

```text
k = 3  ->  1U << 3  =  0000'1000  (solo il bit 3 vale 1)
         ~(1U << 3) =  1111'0111  (tutti a 1 tranne il bit 3)
```

Con questa maschera si scrivono i quattro idiomi che incontrerai in qualsiasi codice C a basso livello:

1. **Impostare il bit `k` a `1`**: `x |= (1U << k);`
2. **Azzerare il bit `k` a `0`**: `x &= ~(1U << k);`
3. **Invertire (commutare) il bit `k`**: `x ^= (1U << k);`
4. **Controllare se il bit `k` è `1`**: `(x & (1U << k)) != 0U`

### Impacchettare ed estrarre sotto-campi di più bit

Spesso un registro o una parola `uint32_t` contiene più campi di larghezza diversa (per esempio un campo da `4` bit a partire dalla posizione `pos`, seguito da un campo da `8` bit). Una maschera di `len` bit consecutivi tutti a `1` (con $1 \le \text{len} < 32$) si ottiene con `(1U << len) - 1U` (per esempio `(1U << 4) - 1U` vale `0b1111`, cioè `0x0FU`):

- **Estrazione** di un sotto-campo lungo `len` bit che inizia al bit `pos`: `uint32_t campo = (val >> pos) & ((1U << len) - 1U);`
- **Impacchettamento** di più campi in una parola `uint32_t`: si maschera ciascun campo alla sua larghezza, lo si sposta nella posizione di destinazione con `<<` e si combinano i contributi con `|`.

### Promozioni intere e trappole con `uint8_t` e `uint16_t`

Come hai imparato nel capitolo 3, nelle espressioni i tipi interi più piccoli di `int` (come `uint8_t` e `uint16_t`) subiscono le **promozioni intere** e vengono convertiti in `int` (che è con segno!) prima che l'operatore venga applicato. Questo produce due trappole frequenti:

- Se `uint8_t b = 0x0FU;`, l'espressione `~b` promuove prima `b` a `int` (`0x0000000F` su 32 bit) e poi inverte tutti i 32 bit, producendo il valore negativo `0xFFFFFFF0` (`-16`). Se vuoi il complemento su 8 bit, scrivi `(uint8_t)(~b)` oppure `(uint8_t)(b ^ 0xFFU)`.
- Se sposti a sinistra `1 << 31` con `1` di tipo `int` a 32 bit, provochi overflow con segno (**comportamento indefinito**). Usando il suffisso `U` (`1U << 31`) o un cast esplicito a `uint32_t` (`(uint32_t)1U << 31`), l'operando è senza segno e il risultato `0x80000000U` è completamente definito.

### Esempio guidato

Il programma seguente combina quattro canali a 8 bit (`alfa`, `rosso`, `verde`, `blu`) in un singolo colore ARGB `uint32_t`, li riestrae tramite `>>` e `& 0xFFU`, e poi manipola i flag di un registro di controllo a 16 bit (`uint16_t`) usando i quattro idiomi con maschere di bit.

<!-- cod: id=13.2-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

constexpr uint16_t FLAG_ACCESO = (uint16_t)(1U << 0);
constexpr uint16_t FLAG_ALLARME = (uint16_t)(1U << 2);
constexpr uint16_t FLAG_SILENZIOSO = (uint16_t)(1U << 5);

uint32_t impacchetta_argb(uint8_t a, uint8_t r, uint8_t g, uint8_t b) {
    return ((uint32_t)a << 24) |
           ((uint32_t)r << 16) |
           ((uint32_t)g << 8) |
           (uint32_t)b;
}

int main(void) {
    uint32_t colore = impacchetta_argb(0xFFU, 0x3AU, 0x7CU, 0x19U);
    uint8_t a = (uint8_t)((colore >> 24) & 0xFFU);
    uint8_t r = (uint8_t)((colore >> 16) & 0xFFU);
    uint8_t g = (uint8_t)((colore >> 8) & 0xFFU);
    uint8_t b = (uint8_t)(colore & 0xFFU);

    printf("Colore ARGB: 0x%08" PRIx32 "\n", colore);
    printf("Canali estratti -> A=%" PRIu8 " R=%" PRIu8
           " G=%" PRIu8 " B=%" PRIu8 "\n", a, r, g, b);

    uint16_t registro = 0U;
    registro |= FLAG_ACCESO | FLAG_ALLARME;
    printf("Dopo imposta ACCESO|ALLARME: 0x%04" PRIx16 "\n", registro);

    registro ^= FLAG_SILENZIOSO;
    registro &= (uint16_t)(~FLAG_ALLARME);
    printf("Dopo toggle SILENZIOSO e azzera ALLARME: 0x%04" PRIx16 "\n", registro);

    bool acceso = (registro & FLAG_ACCESO) != 0U;
    bool allarme = (registro & FLAG_ALLARME) != 0U;
    bool silenzioso = (registro & FLAG_SILENZIOSO) != 0U;
    printf("Stato flag -> acceso=%d allarme=%d silenzioso=%d\n",
           acceso, allarme, silenzioso);

    return 0;
}
```

```output
Colore ARGB: 0xff3a7c19
Canali estratti -> A=255 R=58 G=124 B=25
Dopo imposta ACCESO|ALLARME: 0x0005
Dopo toggle SILENZIOSO e azzera ALLARME: 0x0021
Stato flag -> acceso=1 allarme=0 silenzioso=1
```

Esaminiamo i dettagli più importanti:

- In `impacchetta_argb`, ogni `uint8_t` viene convertito esplicitamente a `uint32_t` prima dello spostamento `<< 24` o `<< 16`: in questo modo nessuno spostamento avviene su un `int` con segno promosso.
- Per riestrarre i canali, `>>` porta il byte desiderato nelle posizioni `7..0` e `& 0xFFU` azzera tutti i bit più significativi.
- Sul registro `uint16_t`, l'azzeramento `registro &= (uint16_t)(~FLAG_ALLARME);` applica il cast esplicito a `uint16_t` sul risultato di `~` per gestire in modo pulito la promozione intera.
- I test `(registro & FLAG_ACCESO) != 0U` racchiudono sempre `registro & FLAG_ACCESO` tra parentesi tonde.

> **Approfondimento — La trappola di precedenza tra `&` e `!=`**
> In C gli operatori relazionali e di uguaglianza (`==`, `!=`) hanno precedenza **maggiore** degli operatori bit a bit `&`, `^` e `|`. Se scrivi `if (stato & MASCHERA != 0)`, il compilatore interpreta l'espressione come `stato & (MASCHERA != 0)`, cioè `stato & 1`, controllando il bit `0` invece della maschera voluta! Metti quindi **sempre** le parentesi tonde attorno alle operazioni bit a bit dentro i confronti: `(stato & MASCHERA) != 0U`.

### Esercizio 13.2 — Codificatore e decodificatore di istruzioni a 32 bit per una mini-CPU con maschere e spostamenti

**Descrizione**

Una mini-CPU codifica ogni istruzione in una parola `uint32_t` con questo layout: bit `31..28` = `opcode` (`0..15`), bit `27..24` = `rd` (`0..15`), bit `23..20` = `rs` (`0..15`), bit `19..16` = `flags` (`0..15`), bit `15..0` = `imm` (`int16_t` in `-32768..32767`, memorizzato nei 16 bit bassi come `(uint16_t)imm`). Definisci `typedef struct istruzione { uint8_t opcode; uint8_t rd; uint8_t rs; uint8_t flags; int16_t imm; } istruzione_t;` e tre funzioni: `uint32_t codifica_istruzione(const istruzione_t *i)`, `istruzione_t decodifica_istruzione(uint32_t w)` (che ricostruisce `imm` con segno dai 16 bit bassi senza comportamento indefinito) e `uint32_t aggiorna_flags(uint32_t w, uint8_t set_m, uint8_t clr_m, uint8_t tog_m)` (che sui 4 bit di `flags` applica nell'ordine `|= (set_m & 0x0FU)`, `&= ~(clr_m & 0x0FU)` e `^= (tog_m & 0x0FU)` lasciando invariati gli altri 28 bit). In `main` leggi comandi fino a fine input: `ENC <op> <rd> <rs> <flags> <imm>` stampa `ENC -> 0x<8hex>`; `DEC <u32>` (letto con `%u`) decodifica e stampa `DEC 0x<8hex> -> op=<op> rd=<rd> rs=<rs> flags=0x<1hex> imm=<imm>`; `FLG <u32> <set> <clr> <tog>` aggiorna i flag e stampa `FLG 0x<8hex> -> 0x<8hex> (flags=0x<1hex>)`. Valida ogni dominio (in caso di errore scrivi su `stderr` e restituisci `EXIT_FAILURE`) e al termine stampa `Operazioni eseguite: <tot>`.

**Concetti da tenere a mente**

- impacchettamento di campi in un `uint32_t` con spostamenti a sinistra (`<<`) e OR bit a bit (`|`)
- estrazione di campi con spostamenti a destra (`>>`) e maschere di bit (`& 0x0FU`, `& 0xFFFFU`)
- aggiornamento selettivo di bit con `|=` (imposta), `&= ~` (azzera) e `^=` (inverte)
- uso esclusivo di operandi senza segno (`uint32_t`) per evitare comportamento indefinito negli spostamenti

**Domande guida**

1. Perché in `codifica_istruzione` devi convertire ciascun campo a `uint32_t` e mascherare `imm` con `0xFFFFU` prima di applicare `<<` e `|`?
2. Come fai in `aggiorna_flags` a modificare solo i bit `19..16` della parola a 32 bit senza alterare `opcode`, registri e immediato?
3. Perché spostare di 28 posizioni a sinistra un `int` con segno a 32 bit può provocare comportamento indefinito mentre su `uint32_t` è sempre definito?
4. Quale sequenza di spostamento e maschera estrae esattamente i 4 bit del registro `rs` (posizioni `23..20`)?

**Esempio di esecuzione**

```input
ENC 2 1 3 5 -10
DEC 557187062
FLG 557187062 8 1 2
```

```output
ENC -> 0x2135fff6
DEC 0x2135fff6 -> op=2 rd=1 rs=3 flags=0x5 imm=-10
FLG 0x2135fff6 -> 0x213efff6 (flags=0xe)
Operazioni eseguite: 3
```

## 13.3 Unioni e unioni etichettate

Supponi di dover rappresentare un pacchetto di telemetria che, di volta in volta, trasporta **o** una quota intera (`int32_t`), **o** una tensione in virgola mobile (`double`), **o** una breve sigla testuale (`char[8]`), ma mai più di uno di questi tre valori contemporaneamente. Se usassi una `struct` con tutti e tre i campi, ogni pacchetto occuperebbe spazio per tutti e tre anche se due campi restano inutilizzati. In C esiste un tipo aggregato pensato esattamente per i dati mutualmente esclusivi: l'**unione**.

### Cos'è un'unione (`union`)

Un'**unione** (*union*) è un tipo definito con la parola chiave `union` i cui campi condividono la stessa area di memoria e solo uno alla volta è attivo. Mentre in una `struct` i campi sono disposti in sequenza uno dopo l'altro, in una `union` **tutti i campi iniziano esattamente allo stesso indirizzo di memoria (offset 0)** e si sovrappongono fisicamente.

```text
struct equivalente (campi in sequenza):
offset:  0       4       8               16              24
        [ int32 ][ pad  ][    double     ][   char[8]    ]   -> 24 byte

union (campi sovrapposti a offset 0):
offset:  0                               8
        [ int32 ]                        <- 4 byte (offset 0)
        [           double              ]<- 8 byte (offset 0)
        [           char[8]             ]<- 8 byte (offset 0) -> 8 byte totali
```

La dimensione di una `union`, restituita da `sizeof`, è almeno pari alla dimensione del suo campo più ampio, arrotondata per eccesso al multiplo dell'allineamento più stringente tra i suoi campi (vedrai i dettagli dell'allineamento nella sotto-sezione 13.6). Nell'esempio dello schema, la `union` occupa `8` byte invece di `24`: un risparmio di due terzi della memoria quando si memorizzano migliaia di elementi in un array.

### Campo attivo, inizializzazione e regola sullo standard

Poiché i campi condividono gli stessi byte, scrivere in un campo sovrascrive i byte di tutti gli altri. Il campo in cui hai scritto per ultimo si chiama **campo attivo** della `union`.

Puoi inizializzare una `union` in tre modi:

- con un valore posizionale `{42}`, che inizializza sempre il **primo** campo dichiarato;
- con un **inizializzatore designato** `{.tensione = 3.7}`, che sceglie esplicitamente quale campo attivare;
- con `{}` (C23), che azzera l'intera unione.

<!-- cod: id=13.3-b tipo=frammento -->
```c
union dato_sensore {
    int32_t quota;
    double tensione;
    char sigla[8];
};

union dato_sensore d = {.tensione = 12.4};  // campo attivo: tensione
d.quota = 1500;                             // ora il campo attivo è quota
```

Secondo lo standard C23, la sovrapposizione di tutti i campi di una `union` a offset `0` è **definita**. Che cosa succede invece se leggi un campo diverso dal campo attivo (per esempio leggi `d.tensione` dopo aver scritto `d.quota`)? In C la lettura di un campo non attivo reinterpreta i byte sottostanti con il tipo del nuovo campo: il risultato è **non specificato** (o può persino formare una rappresentazione non valida per certi tipi) e dipende dall'architettura e dal formato binario interno dei tipi. Non usare quindi una `union` per convertire numeri tra tipi diversi; l'unica ispezione sicura dei byte grezzi passa per i tipi carattere, come vedrai nella sotto-sezione 13.5.

### Le unioni etichettate

Una `union` da sola ha un limite evidente: non ricorda quale dei suoi campi sia attualmente attivo. Se passi una `union` a una funzione, la funzione non ha modo di sapere se i suoi byte rappresentano una quota, una tensione o una sigla.

La soluzione idiomatica in C è l'**unione etichettata** (*tagged union*): una coppia formata da un'enumerazione (`enum`, detta *etichetta*) e da una `union`, racchiuse insieme dentro una `struct`. L'etichetta registra in ogni momento quale campo della `union` è valido.

<!-- cod: id=13.3-c tipo=frammento -->
```c
typedef enum tipo_misura : int {
    MISURA_QUOTA = 0,
    MISURA_TENSIONE = 1,
    MISURA_SIGLA = 2
} tipo_misura_t;

typedef union valore_misura {
    int32_t quota;
    double tensione;
    char sigla[8];
} valore_misura_t;

typedef struct messaggio_telemetria {
    tipo_misura_t tipo;
    valore_misura_t dato;
} messaggio_telemetria_t;
```

### Elaborare unioni etichettate con `switch`

Ogni funzione che legge o trasforma un'unione etichettata deve rispettare una disciplina rigorosa:

1. **In scrittura**: aggiorna sempre insieme il campo `tipo` e il campo corrispondente dentro `dato` (per esempio costruendo un letterale composto `(messaggio_telemetria_t){.tipo = MISURA_TENSIONE, .dato = {.tensione = 3.7}}`).
2. **In lettura**: controlla sempre `msg->tipo` con uno `switch` e accedi esclusivamente al campo della `union` associato a quel `case`.

In questo modo non leggi mai per errore un campo inattivo e, se aggiungi un nuovo caso all'`enum`, il compilatore con `-Wall -Wextra` ti segnala gli `switch` che non lo gestiscono.

> **Se vieni da Python** — In Python una variabile può cambiare liberamente tipo a tempo di esecuzione (un intero, poi un float, poi una stringa), perché l'interprete conserva il tipo dentro ogni oggetto in memoria. In C le variabili hanno tipo fisso a tempo di compilazione: l'unione etichettata è il modo esplicito, veloce e senza costi nascosti con cui si modella un valore che può appartenere a uno tra più tipi noti.

### Esempio guidato

Il programma seguente definisce l'unione etichettata `messaggio_telemetria_t`, confronta `sizeof` della `union` con quello di una `struct` equivalente che conterrebbe tutti e tre i campi in parallelo, ed elabora un array di messaggi tramite una funzione che ispeziona l'etichetta con `switch`.

<!-- cod: id=13.3-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef enum tipo_msg : int {
    MSG_QUOTA = 0,
    MSG_TENSIONE = 1,
    MSG_SIGLA = 2
} tipo_msg_t;

typedef union carico_msg {
    int32_t quota;
    double tensione;
    char sigla[8];
} carico_msg_t;

typedef struct carico_struct_eq {
    int32_t quota;
    double tensione;
    char sigla[8];
} carico_struct_eq_t;

typedef struct messaggio_telemetria {
    tipo_msg_t tipo;
    carico_msg_t carico;
} messaggio_telemetria_t;

void stampa_messaggio(size_t idx, const messaggio_telemetria_t *m) {
    printf("Msg %zu -> ", idx);
    switch (m->tipo) {
        case MSG_QUOTA:
            printf("quota = %" PRId32 " m\n", m->carico.quota);
            break;
        case MSG_TENSIONE:
            printf("tensione = %.2f V\n", m->carico.tensione);
            break;
        case MSG_SIGLA:
            printf("sigla = %s\n", m->carico.sigla);
            break;
    }
}

int main(void) {
    printf("sizeof(union) = %zu, sizeof(struct eq) = %zu\n",
           sizeof(carico_msg_t), sizeof(carico_struct_eq_t));
    printf("sizeof(messaggio_telemetria_t) = %zu\n",
           sizeof(messaggio_telemetria_t));

    messaggio_telemetria_t log[3] = {
        {.tipo = MSG_QUOTA, .carico = {.quota = 1240}},
        {.tipo = MSG_TENSIONE, .carico = {.tensione = 11.85}},
        {.tipo = MSG_SIGLA, .carico = {.sigla = "SAT-07"}}
    };

    for (size_t i = 0; i < 3; ++i) {
        stampa_messaggio(i, &log[i]);
    }
    return 0;
}
```

```output
sizeof(union) = 8, sizeof(struct eq) = 24
sizeof(messaggio_telemetria_t) = 16
Msg 0 -> quota = 1240 m
Msg 1 -> tensione = 11.85 V
Msg 2 -> sigla = SAT-07
```

Analizziamo l'esecuzione:

- `carico_msg_t` occupa solo `8` byte contro i `24` di `carico_struct_eq_t`, perché `quota`, `tensione` e `sigla` condividono gli stessi 8 byte.
- L'intera `messaggio_telemetria_t` occupa `16` byte (`4` byte per `tipo_msg_t`, `4` byte di padding per allineare `double` a `8` byte e `8` byte per la `union`), rimanendo comunque più compatta della `struct` non sovrapposta.
- Nell'array `log`, ogni elemento usa inizializzatori designati annidati (`.carico = {.tensione = 11.85}`) per attivare con chiarezza il campo corrispondente all'etichetta.
- In `stampa_messaggio`, lo `switch (m->tipo)` garantisce che venga letto sempre e solo il campo attivo.

> **Approfondimento — Tipi somma in C e uso negli interpreti**
> Le unioni etichettate sono il modo con cui il C modella i cosiddetti *tipi somma* (o *variant*), cioè dati che possono assumere forme diverse appartenenti a un insieme chiuso di alternative, senza allocazioni dinamiche extra e senza sprecare memoria. È una delle strutture più usate nei compilatori e negli interpreti: le ritroveremo nel capitolo 26 per rappresentare i token, i valori a tempo di esecuzione e i nodi dell'albero sintattico del nostro interprete.

### Esercizio 13.3 — Valutatore di celle di un foglio di calcolo basato su unioni etichettate

**Descrizione**

Scrivi un programma C che modelli un vettore di `8` celle (`cella_t foglio[8]`) tramite un'unione etichettata. Definisci `typedef enum tipo_cella : int { CELLA_VUOTA = 0, CELLA_INT = 1, CELLA_REAL = 2, CELLA_TESTO = 3, CELLA_ERR = 4 } tipo_cella_t;`, l'unione `typedef union dato_cella { int64_t intero; double reale; char testo[16]; int cod_err; } dato_cella_t;` e la struttura `typedef struct cella { tipo_cella_t tipo; dato_cella_t dato; } cella_t;`. Implementa `cella_t somma_celle(const cella_t *a, const cella_t *b)`: se una cella è `CELLA_ERR` propaga quel codice d'errore (dando precedenza ad `a`); se una è `CELLA_VUOTA` restituisce `CELLA_ERR` con codice `10` (cella vuota); se una è `CELLA_TESTO` restituisce `CELLA_ERR` con codice `20` (tipo incompatibile); se entrambe sono `CELLA_INT` restituisce `CELLA_INT` con `a->dato.intero + b->dato.intero`; altrimenti converte i due operandi numerici a `double` e restituisce `CELLA_REAL`. In `main` leggi comandi fino a fine input (`idx` in `0..7`): `INT <idx> <val>`, `REAL <idx> <val>`, `TXT <idx> <parola>` (`%15s`), `ADD <dest> <i1> <i2>` (assegna `foglio[dest] = somma_celle(&foglio[i1], &foglio[i2])`) e `CLR <idx>` (imposta `CELLA_VUOTA`). Al termine stampa `Verifica sizeof(union) <= sizeof(struct): <1 o 0>`, tutte le celle non vuote nel formato `C<i> [TIPO]: <valore>` e il conteggio di celle numeriche (`INT` + `REAL`), testuali ed errori.

**Concetti da tenere a mente**

- definizione di un'unione (`union`) con campi sovrapposti in memoria
- costruzione di un'unione etichettata (`struct` con `enum tipo` + `union dato`)
- accesso esclusivo al campo attivo della `union` guidato da `switch` sull'etichetta
- promozione controllata tra intero e reale e propagazione degli errori

**Domande guida**

1. Perché `sizeof(dato_cella_t)` è determinata dal campo più grande (`char testo[16]`) anziché dalla somma di `int64_t`, `double`, `char[16]` e `int`?
2. Che cosa accadrebbe se leggessi `c->dato.reale` quando `c->tipo` vale invece `CELLA_INT` o `CELLA_TESTO`?
3. Come fa `somma_celle` a sommare correttamente una cella `CELLA_INT` e una cella `CELLA_REAL` producendo una nuova cella `CELLA_REAL`?
4. Perché se il comando `ADD` usa lo stesso indice come destinazione e come operando (es. `ADD 0 0 1`) passare il risultato per valore evita di corrompere gli operandi durante il calcolo?

**Esempio di esecuzione**

```input
INT 0 25
INT 1 17
ADD 2 0 1
REAL 3 2.50
ADD 4 2 3
TXT 5 Totale
ADD 6 4 5
ADD 7 0 7
```

```output
Verifica sizeof(union) <= sizeof(struct): 1
C0 [INT]: 25
C1 [INT]: 17
C2 [INT]: 42
C3 [REAL]: 2.50
C4 [REAL]: 44.50
C5 [TXT]: Totale
C6 [ERR]: #20
C7 [ERR]: #10
Riepilogo -> numeriche: 5, testo: 1, errori: 2
```

## 13.4 Campi di bit

Nella sotto-sezione 13.2 hai visto come impacchettare più flag e piccoli numeri dentro un intero usando maschere di bit e spostamenti. Quando però una struttura interna di un programma contiene molti flag o contatori da 2, 3 o 4 bit, scrivere manualmente spostamenti e maschere in ogni punto del codice può appesantire la lettura. Il C offre una sintassi dedicata dentro le `struct`: i **campi di bit** (*bit-fields*).

### Dichiarare campi di bit in una `struct`

All'interno di una `struct`, un campo di bit si dichiara indicando il tipo, il nome, i due punti `:` e la larghezza in bit come espressione costante intera non negativa:

<!-- cod: id=13.4-b tipo=frammento -->
```c
typedef struct stato_dispositivo {
    bool abilitato : 1;
    unsigned int modalita : 2;   // valori 0..3
    unsigned int livello : 3;    // valori 0..7
    unsigned int codice : 4;     // valori 0..15
} stato_dispositivo_t;
```

Il compilatore impacchetta questi campi uno accanto all'altro all'interno di un'unità di memorizzazione (tipicamente da 4 byte per `unsigned int`) e genera automaticamente le maschere e gli spostamenti necessari ogni volta che leggi o assegni `s.livello`. In questo esempio, tutti e quattro i campi occupano insieme solo `10` bit, per cui l'intera `struct` può stare in un singolo `unsigned int` (`4` byte) invece di richiedere campi interi separati.

### Tipi consentiti e aritmetica modulare

Lo standard C23 garantisce la portabilità dei campi di bit dichiarati con i tipi `unsigned int`, `signed int` e `bool`. Fai attenzione a una regola insidiosa: **non dichiarare mai un campo di bit come `int` semplice** (senza `signed` o `unsigned`). Diversamente da una normale variabile `int` (che è sempre con segno), per un campo di bit dichiarato `int x : 3;` è **dipendente dall'implementazione** se `x` sia con segno (`-4..3`) oppure senza segno (`0..7`). Specifica sempre `unsigned int` (o `bool` per un singolo flag da `1` bit), oppure esplicitamente `signed int` se ti servono valori negativi.

Un campo di bit `unsigned int` largo $k$ bit rappresenta i valori da $0$ a $2^k - 1$ e segue l'**aritmetica modulare** modulo $2^k$: se un campo `unsigned int livello : 3` vale `7` e gli assegni `livello + 1U`, il valore viene troncato ai 3 bit bassi e si riavvolge a `0` in modo completamente definito.

### Campi anonimi, allineamento `: 0` e divieti dello standard

Puoi dichiarare campi di bit **senza nome** (anonimi) per riservare bit inutilizzati:

- `unsigned int : 6;` lascia `6` bit di riempimento non accessibili dal codice;
- `unsigned int : 0;` (larghezza zero, sempre senza nome) forza il campo di bit successivo a iniziare in una nuova unità di memorizzazione.

Lo standard C23 impone inoltre tre divieti rigidi sui campi di bit: **non puoi applicare l'operatore indirizzo `&`, né `sizeof`, né `offsetof`** a un campo di bit (e non esistono array di campi di bit). Se provi a scrivere `&s.codice` o `sizeof(s.codice)`, il compilatore segnala un errore di compilazione. Di conseguenza non puoi nemmeno passare l'indirizzo di un campo di bit a `sscanf`: devi prima leggere in una normale variabile locale `unsigned int`, validarla e poi assegnarla al campo di bit.

### Limiti di portabilità e quando usarli

I campi di bit sono comodi ma hanno **importanti limiti di portabilità**, perché lo standard lascia diversi aspetti come **comportamento dipendente dall'implementazione**:

- l'ordine con cui i campi sono collocati dentro l'unità di memoria (dal bit meno significativo al più significativo, oppure viceversa);
- come vengono gestiti i campi che supererebbero il confine tra due unità di memorizzazione (possono essere divisi o spostati nell'unità successiva con padding);
- la dimensione e l'allineamento complessivo dell'unità scelta dal compilatore.

Da qui discende una regola d'oro di progettazione:

- **Usa i campi di bit** per compattare strutture dati **interne** al programma che vivono soltanto nella RAM del processo corrente (per esempio nodi di strutture dati ad alta densità o descrittori di stato interni).
- **Non usare i campi di bit** per descrivere il layout binario di file su disco, pacchetti di rete o registri hardware esterni: per quelli usa tipi a larghezza esatta (`uint16_t`, `uint32_t`) manipolati con spostamenti e maschere esplicite (sotto-sezione 13.2) o funzioni di conversione esplicite.

### Esempio guidato

Il programma seguente definisce una struttura con campi di bit per lo stato interno di un dispositivo, ne verifica la compattezza con `sizeof`, mostra il riavvolgimento modulare sul campo `livello` da 3 bit e converte la struttura in un registro `uint16_t` portabile tramite maschere e spostamenti.

<!-- cod: id=13.4-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

typedef struct stato_dispositivo {
    bool abilitato : 1;
    unsigned int modalita : 2;
    unsigned int livello : 3;
    unsigned int codice : 4;
    unsigned int : 6;
} stato_dispositivo_t;

uint16_t impacchetta_stato(const stato_dispositivo_t *s) {
    return (uint16_t)((s->abilitato ? 1U : 0U) |
                      ((s->modalita & 3U) << 1) |
                      ((s->livello & 7U) << 3) |
                      ((s->codice & 15U) << 6));
}

int main(void) {
    stato_dispositivo_t d = {
        .abilitato = true,
        .modalita = 2U,
        .livello = 6U,
        .codice = 11U
    };

    printf("sizeof(stato_dispositivo_t) = %zu\n", sizeof(stato_dispositivo_t));
    printf("Iniziale -> ab=%d mod=%u liv=%u cod=%u reg=0x%04" PRIx16 "\n",
           d.abilitato, d.modalita, d.livello, d.codice, impacchetta_stato(&d));

    d.livello = (unsigned int)(d.livello + 1U);
    printf("Dopo +1 (livello=7): liv=%u\n", d.livello);

    d.livello = (unsigned int)(d.livello + 1U);
    printf("Dopo +1 (riavvolgimento mod 8): liv=%u\n", d.livello);

    printf("Registro finale: 0x%04" PRIx16 "\n", impacchetta_stato(&d));
    return 0;
}
```

```output
sizeof(stato_dispositivo_t) = 4
Iniziale -> ab=1 mod=2 liv=6 cod=11 reg=0x02f5
Dopo +1 (livello=7): liv=7
Dopo +1 (riavvolgimento mod 8): liv=0
Registro finale: 0x02c5
```

Nota come funziona l'esempio:

- `sizeof(stato_dispositivo_t)` vale `4` byte: tutti i campi (10 bit utili più 6 bit anonimi) stanno in una sola unità `unsigned int`.
- Quando `d.livello` passa da `6` a `7` e poi viene incrementato ancora di `1`, l'assegnamento al campo a `3` bit tronca `8` (`0b1000`) a `0` (`0b000`) per aritmetica modulare.
- La funzione `impacchetta_stato` estrae i valori logici dei campi e li dispone a posizioni di bit esattamente fissate dentro un `uint16_t`: il valore `0x02f5` (e poi `0x02c5`) è identico su qualsiasi compilatore e architettura, indipendentemente da come il compilatore ha impacchettato i campi di bit in memoria.

> **Approfondimento — Perché `&` è illegale sui campi di bit**
> In C l'unità minima indirizzabile da un puntatore è il **byte** (un `char`), non il singolo bit. Poiché più campi di bit possono coabitare all'interno dello stesso byte — per esempio `abilitato` al bit 0 e `modalita` ai bit 1–2 — un campo di bit non possiede un proprio indirizzo di byte autonomo. Ecco perché il linguaggio vieta di applicare `&`, `sizeof` e `offsetof` a qualunque campo di bit.

### Esercizio 13.4 — Configurazione di porte di uno switch di rete con campi di bit ed esportazione portabile

**Descrizione**

Scrivi un programma C che gestisca `4` porte di uno switch di rete (`porta_bf_t porte[4]`) usando una struttura con campi di bit `typedef struct porta_bf { unsigned int attiva : 1; unsigned int duplex : 1; unsigned int velocita : 2; unsigned int vlan : 4; unsigned int priorita : 3; unsigned int : 5; } porta_bf_t;`. Per garantire una codifica binaria indipendente dall'ordine dei campi di bit del compilatore, implementa due funzioni di conversione verso un registro `uint16_t` con layout fisso (bit `0` = `attiva`, bit `1` = `duplex`, bit `3..2` = `velocita`, bit `7..4` = `vlan`, bit `10..8` = `priorita`): `uint16_t esporta_porta(const porta_bf_t *p)` e `porta_bf_t importa_porta(uint16_t reg)`. In `main` leggi comandi fino a fine input (`id` in `0..3`): `SET <id> <attiva> <duplex> <vel> <vlan> <prio>` (valida ciascun valore rispetto alla larghezza in bit `0..1`, `0..1`, `0..3`, `0..15`, `0..7`), `IMP <id> <reg_u16>` (importa un `uint16_t <= 0x07FFU` con `importa_porta`), `INC_PRIO <id>` (incrementa `porte[id].priorita` di `1`, mostrando il riavvolgimento automatico modulo `8` da `7` a `0` del campo di bit `unsigned int priorita : 3`). Al termine stampa per tutte le `4` porte `P<id>: attiva=<a> duplex=<d> vel=<v> vlan=<vl> prio=<pr> -> reg=0x<04hex>` e il conteggio delle porte attive.

**Concetti da tenere a mente**

- definizione di campi di bit `unsigned int nome : larghezza` dentro una `struct`
- aritmetica modulare automatica (modulo $2^k$) sui campi di bit `unsigned`
- campi di bit anonimi di riempimento (`unsigned int : 5;`)
- conversione esplicita tra `struct` a campi di bit e `uint16_t` per garantire portabilità binaria

**Domande guida**

1. Perché non puoi trasmettere direttamente in rete i byte grezzi di `porta_bf_t` ma devi usare `esporta_porta` e `importa_porta`?
2. Che valore assume il campo `unsigned int priorita : 3` quando vale `7` e gli sommi `1`?
3. Perché non potresti passare `&porte[id].vlan` direttamente a `sscanf` per leggere il valore della VLAN?
4. Qual è l'intervallo di valori rappresentabili da un campo di bit `unsigned int vlan : 4`?

**Esempio di esecuzione**

```input
SET 0 1 1 2 10 6
INC_PRIO 0
INC_PRIO 0
IMP 2 1451
```

```output
P0: attiva=1 duplex=1 vel=2 vlan=10 prio=0 -> reg=0x00ab
P1: attiva=0 duplex=0 vel=0 vlan=0 prio=0 -> reg=0x0000
P2: attiva=1 duplex=1 vel=2 vlan=10 prio=5 -> reg=0x05ab
P3: attiva=0 duplex=0 vel=0 vlan=0 prio=0 -> reg=0x0000
Porte attive: 2
```

## 13.5 Ordine dei byte in memoria

Un `uint8_t` occupa un solo byte, quindi in memoria non c'è alcuna ambiguità su come sia memorizzato. Ma un intero multibyte come `uint32_t x = 0x12345678U;` occupa **quattro byte consecutivi**: `0x12` (il byte più significativo, MSB), `0x34`, `0x56` e `0x78` (il byte meno significativo, LSB). In quale ordine vengono collocati questi quattro byte a indirizzi di memoria crescenti? La risposta non è unica: dipende dall'architettura del processore.

### Little-endian e big-endian

L'**ordine dei byte** (*endianness*) è la convenzione dell'architettura (**little-endian** o **big-endian**) che stabilisce come i byte di un numero multibyte sono disposti in memoria a indirizzi crescenti:

- In un'architettura **little-endian** (come x86-64 e la configurazione standard di ARM64), il **byte meno significativo (LSB)** è memorizzato all'indirizzo più basso e il byte più significativo all'indirizzo più alto.
- In un'architettura **big-endian** (usata come ordine convenzionale dei protocolli di rete, il *network byte order*, e in molti formati binari), il **byte più significativo (MSB)** è memorizzato all'indirizzo più basso, proprio come scriviamo i numeri da sinistra a destra.

```text
Valore astratto: uint32_t x = 0x12345678U  (MSB = 0x12, LSB = 0x78)

Indirizzo:        base+0   base+1   base+2   base+3
Big-endian:       [ 0x12 ] [ 0x34 ] [ 0x56 ] [ 0x78 ]
Little-endian:    [ 0x78 ] [ 0x56 ] [ 0x34 ] [ 0x12 ]
```

Nota una distinzione cruciale: il **valore numerico** di `x` è identico su entrambe le macchine (`305419896`). Ciò che cambia è soltanto la sequenza fisica dei byte in memoria. Secondo lo standard C23, l'ordine dei byte nativo della macchina è **comportamento dipendente dall'implementazione**.

### Ispezionare i byte in memoria e riconoscere l'ordine nativo

In C lo standard garantisce (comportamento **definito**) che puoi sempre leggere la rappresentazione byte per byte di qualunque oggetto in memoria tramite un puntatore `const unsigned char *` (o `const uint8_t *`, dato che sui sistemi con `uint8_t` esso è un alias di `unsigned char`). Questo ti permette di verificare a tempo di esecuzione l'ordine dei byte della macchina ospite usando un `uint16_t` pari a `0x0001U`:

<!-- cod: id=13.5-b tipo=frammento -->
```c
bool macchina_little_endian(void) {
    uint16_t sonda = 0x0001U;
    const uint8_t *byte = (const uint8_t *)&sonda;
    return byte[0] == 0x01U;
}
```

Se il primo byte (`byte[0]`, l'indirizzo più basso) contiene `0x01`, il byte meno significativo è all'inizio e la macchina è little-endian; se contiene `0x00`, la macchina è big-endian.

### Inversione dell'ordine dei byte (*byte swap*)

Quando ricevi un intero già memorizzato con l'ordine dei byte opposto a quello desiderato, puoi invertirne i byte con spostamenti e maschere su tipi senza segno:

<!-- cod: id=13.5-c tipo=frammento -->
```c
uint16_t inverti_u16(uint16_t v) {
    return (uint16_t)((v >> 8) | (v << 8));
}

uint32_t inverti_u32(uint32_t v) {
    return ((v >> 24) & 0x000000FFU) |
           ((v >> 8)  & 0x0000FF00U) |
           ((v << 8)  & 0x00FF0000U) |
           ((v << 24) & 0xFF000000U);
}
```

In `inverti_u32`, il byte più significativo (`bits 31..24`) viene portato nei bit `7..0`, il secondo byte scende nei bit `15..8`, il terzo sale nei bit `23..16` e il byte meno significativo sale nei bit `31..24`.

### Scrittura e lettura portabile in un buffer `uint8_t[]`

Supponi di dover scrivere un `uint32_t` in un buffer `uint8_t buf[4]` per salvarlo su file o inviarlo in rete in formato big-endian (o little-endian). L'errore classico è copiare direttamente i byte grezzi dell'intero in memoria: così facendo il file prodotto da una CPU little-endian risulterebbe corrotto se letto da una CPU big-endian.

Il modo corretto e totalmente portabile consiste nell'estrarre i singoli byte dal valore numerico tramite `>>` e `& 0xFFU`, e nel ricomporli con `<<` e `|`:

- **Scrittura big-endian**: `buf[0] = (uint8_t)((v >> 24) & 0xFFU); ... buf[3] = (uint8_t)(v & 0xFFU);`
- **Scrittura little-endian**: `buf[0] = (uint8_t)(v & 0xFFU); ... buf[3] = (uint8_t)((v >> 24) & 0xFFU);`
- **Lettura big-endian**: `((uint32_t)buf[0] << 24) | ((uint32_t)buf[1] << 16) | ((uint32_t)buf[2] << 8) | (uint32_t)buf[3]`

Questo codice produce esattamente gli stessi byte su qualunque architettura, senza mai dover interrogare l'ordine dei byte nativo della CPU. Ritroverai questa tecnica nel capitolo 20 quando salverai strutture dati su file binari.

### Esempio guidato

Il programma seguente trasforma il valore `0x12345678U` in due buffer `uint8_t[4]` — uno in ordine big-endian e uno in ordine little-endian — usando solo spostamenti e maschere, stampa i singoli byte in esadecimale e poi ricostruisce il valore originale da entrambi i buffer in modo indipendente dall'architettura ospite.

<!-- cod: id=13.5-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

void codifica_be32(uint8_t out[4], uint32_t val) {
    out[0] = (uint8_t)((val >> 24) & 0xFFU);
    out[1] = (uint8_t)((val >> 16) & 0xFFU);
    out[2] = (uint8_t)((val >> 8) & 0xFFU);
    out[3] = (uint8_t)(val & 0xFFU);
}

void codifica_le32(uint8_t out[4], uint32_t val) {
    out[0] = (uint8_t)(val & 0xFFU);
    out[1] = (uint8_t)((val >> 8) & 0xFFU);
    out[2] = (uint8_t)((val >> 16) & 0xFFU);
    out[3] = (uint8_t)((val >> 24) & 0xFFU);
}

uint32_t decodifica_be32(const uint8_t in[4]) {
    return ((uint32_t)in[0] << 24) | ((uint32_t)in[1] << 16) |
           ((uint32_t)in[2] << 8) | (uint32_t)in[3];
}

uint32_t decodifica_le32(const uint8_t in[4]) {
    return (uint32_t)in[0] | ((uint32_t)in[1] << 8) |
           ((uint32_t)in[2] << 16) | ((uint32_t)in[3] << 24);
}

void stampa_buffer(const char *etichetta, const uint8_t buf[4]) {
    printf("%s:", etichetta);
    for (size_t i = 0; i < 4; ++i) {
        printf(" %02" PRIx8, buf[i]);
    }
    printf("\n");
}

int main(void) {
    uint32_t originale = 0x12345678U;
    uint8_t buf_be[4] = {};
    uint8_t buf_le[4] = {};

    codifica_be32(buf_be, originale);
    codifica_le32(buf_le, originale);

    stampa_buffer("Big-endian   ", buf_be);
    stampa_buffer("Little-endian", buf_le);

    uint32_t ric_be = decodifica_be32(buf_be);
    uint32_t ric_le = decodifica_le32(buf_le);

    printf("Ricostruito da BE: 0x%08" PRIx32 "\n", ric_be);
    printf("Ricostruito da LE: 0x%08" PRIx32 "\n", ric_le);
    return 0;
}
```

```output
Big-endian   : 12 34 56 78
Little-endian: 78 56 34 12
Ricostruito da BE: 0x12345678
Ricostruito da LE: 0x12345678
```

Osserva come funzionano codifica e decodifica:

- `codifica_be32` colloca il byte più significativo (`0x12`) in `buf_be[0]` e quello meno significativo (`0x78`) in `buf_be[3]`; `codifica_le32` fa esattamente l'opposto.
- In `decodifica_be32` e `decodifica_le32` ogni elemento `uint8_t` viene convertito a `uint32_t` prima dello spostamento `<<`, evitando le promozioni a `int` con segno.
- Entrambe le funzioni di decodifica ricostruiscono il valore `0x12345678` esatto, e l'output del programma è del tutto indipendente dal fatto che la macchina ospite sia little-endian o big-endian.

> **Approfondimento — Perché `>>` e `<<` sono indipendenti dall'endianness**
> Gli operatori di spostamento `>>` e `<<` sono definiti dallo standard C sul **valore aritmetico** del numero (divisione o moltiplicazione per potenze di due), non sulla disposizione fisica dei suoi byte in RAM. Per questo `(val >> 24) & 0xFFU` restituisce sempre il byte più significativo `0x12` di `0x12345678U`, sia su una CPU little-endian sia su una CPU big-endian, eliminando la necessità di controlli condizionali sull'architettura.

### Esercizio 13.5 — Serializzatore e decodificatore di trame binarie in formato big-endian e little-endian

**Descrizione**

Scrivi un programma C che serializzi e decodifichi un'intestazione di pacchetto di `8` byte (`uint8_t buf[8]`) composta da tre campi: `uint16_t id` (byte `0..1`), `uint16_t lunghezza` (byte `2..3`) e `uint32_t chiave` (byte `4..7`). Implementa le funzioni portabili basate su spostamenti e maschere: `void scrivi_u16_be(uint8_t b[2], uint16_t v)`, `void scrivi_u32_be(uint8_t b[4], uint32_t v)`, `uint16_t leggi_u16_be(const uint8_t b[2])`, `uint32_t leggi_u32_be(const uint8_t b[4])`, `uint16_t swap_u16(uint16_t v)` e `uint32_t swap_u32(uint32_t v)` (che invertono l'ordine dei byte di `uint16_t` e `uint32_t`). In `main` leggi comandi fino a fine input: `PACK <id> <len> <chiave>` (`id <= 65535`, `len <= 65535`, `chiave <= 4294967295`) serializza i tre campi in `buf_be[8]` (big-endian) e, applicando `swap_u16` e `swap_u32`, in `buf_le[8]` (little-endian), stampando entrambe le sequenze di `8` byte esadecimali; `UNPACK_BE <b0> ... <b7>` (8 interi `0..255`) decodifica gli 8 byte come big-endian e stampa `UNPACK_BE -> id=<id> len=<len> chiave=0x<08hex>`; `UNPACK_LE <b0> ... <b7>` li decodifica come little-endian combinando `leggi_u*_be` e `swap_u*` e stampa `UNPACK_LE -> id=<id> len=<len> chiave=0x<08hex>`. In caso di input errato scrivi su `stderr` e restituisci `EXIT_FAILURE`.

**Concetti da tenere a mente**

- differenza tra ordine dei byte big-endian (MSB al primo byte) e little-endian (LSB al primo byte)
- inversione dell'ordine dei byte (*byte swap*) su `uint16_t` e `uint32_t` con spostamenti e maschere
- scrittura e lettura in array `uint8_t[]` indipendenti dall'architettura ospite
- dualità tra lettura little-endian e lettura big-endian seguita da *byte swap*

**Domande guida**

1. Perché `scrivi_u32_be(b, v)` produce esattamente gli stessi 4 byte in memoria sia quando il programma gira su una CPU little-endian sia su una CPU big-endian?
2. Quale espressione con `>>` e `<<` inverte i 4 byte di un valore `uint32_t` dentro `swap_u32`?
3. Perché decodificare 4 byte in formato little-endian equivale a leggerli con `leggi_u32_be` e passare il risultato a `swap_u32`?
4. In quale posizione del buffer `buf_be[8]` finisce il byte più significativo di `chiave` e in quale posizione finisce invece in `buf_le[8]`?

**Esempio di esecuzione**

```input
PACK 258 1024 305419896
UNPACK_BE 1 2 4 0 18 52 86 120
UNPACK_LE 2 1 0 4 120 86 52 18
```

```output
BE: 01 02 04 00 12 34 56 78
LE: 02 01 00 04 78 56 34 12
UNPACK_BE -> id=258 len=1024 chiave=0x12345678
UNPACK_LE -> id=258 len=1024 chiave=0x12345678
```

## 13.6 Allineamento, padding, `alignof` e `offsetof`

Nel capitolo 12 hai osservato che `sizeof` di una `struct` può essere maggiore della somma delle dimensioni dei suoi campi. Nella sotto-sezione 13.3 hai incontrato un caso concreto: `messaggio_telemetria_t` aveva un `enum` da `4` byte e una `union` da `8` byte, eppure occupava `16` byte. Perché il compilatore lascia dei buchi vuoti dentro le strutture? La risposta sta nel modo in cui i processori leggono la memoria centrale.

### Vincoli di allineamento e operatore `alignof`

I processori moderni non leggono la RAM un singolo byte per volta, ma a parole di 4, 8 o più byte. Leggere un `uint64_t` che inizia a un indirizzo multiplo di `8` richiede una sola operazione di accesso alla memoria; leggerlo a un indirizzo non multiplo di `8` può richiedere due accessi separati, rallentare il programma o, su alcune architetture, provocare un errore hardware immediato.

Per questo motivo ogni tipo completo `T` ha un vincolo di **allineamento** (*alignment*): un vincolo per cui l'indirizzo in memoria di un oggetto di tipo `T` deve essere multiplo di una potenza di due (`1`, `2`, `4`, `8`, ...). Tipicamente, per i tipi scalari a larghezza fissa, l'allineamento coincide con la dimensione: `uint8_t` ha allineamento `1`, `uint16_t` ha allineamento `2`, `uint32_t` ha allineamento `4`, `uint64_t` e `double` hanno allineamento `8` (i valori esatti sono **dipendenti dall'implementazione** e dall'ABI della piattaforma).

Per interrogare il vincolo di allineamento di un tipo si usa l'operatore C23 `alignof(tipo)`, che restituisce un valore costante di tipo `size_t`:

<!-- cod: id=13.6-b tipo=frammento -->
```c
size_t a8 = alignof(uint8_t);    // tipicamente 1
size_t a32 = alignof(uint32_t);  // tipicamente 4
size_t a64 = alignof(uint64_t);  // tipicamente 8
```

> **C23** — In C23 `alignof` è una parola chiave del linguaggio sempre disponibile senza includere header dedicati. Negli standard precedenti (C11 e C17) l'operatore nativo si scriveva `_Alignof` (mentre `alignof` era una macro definita in un header apposito).

### Padding nelle `struct` e macro `offsetof`

Quando definisci una `struct`, lo standard C23 stabilisce regole precise:

- I campi sono disposti in memoria esattamente nell'ordine in cui sono dichiarati, e il **primo campo si trova sempre a offset `0`**.
- Prima di ciascun campo successivo, se la posizione corrente non è multipla dell'allineamento del campo, il compilatore inserisce automaticamente dei byte di **padding** (*padding*): byte di riempimento inseriti dentro o in fondo a una `struct` per soddisfare i vincoli di allineamento.
- L'allineamento dell'intera `struct` è pari al massimo degli allineamenti dei suoi campi, e `sizeof(struct)` è sempre un **multiplo di `alignof(struct)`**. Se la fine dell'ultimo campo non cade su un multiplo di `alignof(struct)`, il compilatore aggiunge **padding di coda** alla fine della struttura.

Perché serve il padding di coda? Pensa a un array `record_t v[10];`: in memoria gli elementi sono contigui e l'elemento `v[1]` inizia esattamente `sizeof(record_t)` byte dopo `v[0]`. Solo se `sizeof(record_t)` è multiplo di `alignof(record_t)` ogni elemento dell'array risulta correttamente allineato.

```text
struct record_sparso { uint8_t a; uint64_t b; uint8_t c; uint32_t d; };

offset:  0   1  2  3  4  5  6  7   8..15         16  17 18 19  20..23
        [a] [   padding (7 B)   ] [   b (8 B)   ][c] [pad 3B] [ d (4 B) ]
                                                               ^-- totale: 24 byte
                                                                   (14 utili + 10 padding)
```

Per conoscere la posizione esatta in byte di un campo rispetto all'inizio della struttura si usa la macro `offsetof(tipo_struct, campo)` definita in `<stddef.h>`, che restituisce un valore costante di tipo `size_t` (per esempio `offsetof(struct record_sparso, b)` vale `8`).

### Ridurre il padding riordinando i campi

Poiché il compilatore non può riordinare i campi di una `struct` di propria iniziativa, spetta a te progettarne l'ordine quando la memoria conta (per esempio in array con milioni di elementi). Una regola semplice e molto efficace consiste nell'elencare i campi **in ordine decrescente di allineamento** (prima i campi da 8 byte, poi quelli da 4, poi da 2, infine quelli da 1):

```text
struct record_compatto { uint64_t b; uint32_t d; uint8_t a; uint8_t c; };

offset:  0..7          8..11     12  13  14 15
        [   b (8 B)   ][ d (4 B) ][a][c][pad 2B]
                                         ^-- totale: 16 byte
                                             (14 utili + 2 padding di coda)
```

Senza cambiare un solo bit di informazione, la stessa struttura è scesa da `24` a `16` byte (un risparmio del 33%).

Nota infine due conseguenze importanti definite dallo standard C23:

- Il contenuto dei byte di padding è **non specificato**: possono contenere bit residui qualsiasi lasciati dalla memoria precedente.
- Quando serve imporre un allineamento più stretto di quello predefinito (per esempio per allineare un buffer a una linea di cache), il C23 offre lo specificatore `alignas` (lo vedremo nel capitolo 22).

> **Se vieni da Python** — In Python la disposizione fisica degli oggetti in memoria è gestita e nascosta dall'interprete. In C puoi misurare con precisione allineamento (`alignof`), posizione esatta di ogni campo (`offsetof`) e dimensione totale (`sizeof`), progettando strutture compatte e veloci da attraversare in cache.

### Esempio guidato

Il programma seguente confronta due `struct` che contengono esattamente gli stessi quattro campi (`uint64_t`, `uint32_t` e due `uint8_t`), disposti in ordine sparso nella prima e in ordine decrescente di allineamento nella seconda, stampando `alignof`, `sizeof`, l'`offsetof` di ogni campo e i byte di padding risparmiati.

<!-- cod: id=13.6-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct record_sparso {
    uint8_t a;
    uint64_t b;
    uint8_t c;
    uint32_t d;
} record_sparso_t;

typedef struct record_compatto {
    uint64_t b;
    uint32_t d;
    uint8_t a;
    uint8_t c;
} record_compatto_t;

int main(void) {
    size_t dati_utili = sizeof(uint64_t) + sizeof(uint32_t) +
                        sizeof(uint8_t) + sizeof(uint8_t);

    printf("record_sparso_t: size=%zu align=%zu padding=%zu\n",
           sizeof(record_sparso_t), alignof(record_sparso_t),
           sizeof(record_sparso_t) - dati_utili);
    printf("  offset -> a=%zu b=%zu c=%zu d=%zu\n",
           offsetof(record_sparso_t, a), offsetof(record_sparso_t, b),
           offsetof(record_sparso_t, c), offsetof(record_sparso_t, d));

    printf("record_compatto_t: size=%zu align=%zu padding=%zu\n",
           sizeof(record_compatto_t), alignof(record_compatto_t),
           sizeof(record_compatto_t) - dati_utili);
    printf("  offset -> b=%zu d=%zu a=%zu c=%zu\n",
           offsetof(record_compatto_t, b), offsetof(record_compatto_t, d),
           offsetof(record_compatto_t, a), offsetof(record_compatto_t, c));

    printf("Risparmio per singolo record: %zu byte\n",
           sizeof(record_sparso_t) - sizeof(record_compatto_t));
    return 0;
}
```

```output
record_sparso_t: size=24 align=8 padding=10
  offset -> a=0 b=8 c=16 d=20
record_compatto_t: size=16 align=8 padding=2
  offset -> b=0 d=8 a=12 c=13
Risparmio per singolo record: 8 byte
```

Osserva i risultati stampati dal programma:

- Entrambe le strutture hanno `alignof` pari a `8` (l'allineamento del campo `uint64_t`) e `dati_utili` pari a `14` byte.
- In `record_sparso_t` il compilatore inserisce `7` byte di padding tra `a` (offset `0`) e `b` (offset `8`), più `3` byte di padding tra `c` (offset `16`) e `d` (offset `20`), per un totale di `10` byte di padding e `24` byte complessivi.
- In `record_compatto_t` non esiste alcun buco interno tra i campi (`0`, `8`, `12`, `13`); rimangono solo `2` byte di padding di coda alle posizioni `14` e `15` per portare `sizeof` a `16`, multiplo di `8`.

> **Approfondimento — Perché il padding vieta il confronto grezzo tra `struct`**
> Nel capitolo 12 hai visto che in C non si può scrivere `s1 == s2` tra due `struct`, ma neppure confrontare byte per byte la memoria delle due strutture è affidabile. Poiché i byte di padding hanno contenuto **non specificato**, due variabili `s1` e `s2` con tutti i campi logicamente identici possono ospitare byte spuri diversi nelle zone di padding, facendo fallire un confronto grezzo dei byte. Il confronto corretto tra strutture va sempre eseguito campo per campo.

### Esercizio 13.6 — Calcolatore e ottimizzatore di layout di `struct` con `alignof`, `offsetof` e riduzione del padding

**Descrizione**

Scrivi un programma C che verifichi prima con `alignof` e `offsetof` (`<stddef.h>`) due strutture reali con gli stessi campi a larghezza fissa: `typedef struct rec_sparso { uint8_t t; uint32_t v; uint8_t f; uint16_t c; } rec_sparso_t;` e `typedef struct rec_compatto { uint32_t v; uint16_t c; uint8_t t; uint8_t f; } rec_compatto_t;`, stampando `Verifica struct C -> sparso: size=<S1> align=<A1> off_v=<O1>, compatto: size=<S2> align=<A2> off_c=<O2>`. Poi leggi da `stdin` la specifica di una struttura composta da `n` campi scalari (`1 <= n <= 20`): la prima riga contiene `n`, le successive `n` righe contengono `nome dimensione count` (`nome` fino a `15` caratteri, `dimensione` in `{1, 2, 4, 8}` byte con allineamento pari a `dimensione`, e `count` in `1..16` per un campo singolo o piccolo array `tipo nome[count]` di occupazione `dimensione * count` e allineamento `dimensione`). Implementa una funzione `size_t calcola_layout(campo_spec_t v[], size_t n, size_t *align_out, size_t *pad_tot_out)` che assegna a ogni campo l'`offset` allineato al minimo multiplo del suo allineamento `>= pos_corrente`, somma il padding interno e aggiunge il padding finale per rendere la dimensione totale multipla dell'allineamento massimo. Stampa la mappa originale (`nome: off=<off> dim=<bytes> align=<a>`), poi riordina una copia dei campi per allineamento decrescente (mantenendo l'ordine originale a parità di allineamento), ricalcola il layout ottimizzato e stampa dimensione, allineamento, padding prima e dopo e byte risparmiati.

**Concetti da tenere a mente**

- operatore `alignof` (C23) e macro `offsetof` (`<stddef.h>`)
- regola di allineamento dei campi: offset multiplo dell'allineamento del campo
- padding interno tra i campi e padding di coda per allineare `sizeof(struct)` ad `alignof(struct)`
- riordinamento stabile dei campi per allineamento decrescente per minimizzare il padding

**Domande guida**

1. Perché in `rec_sparso_t` il compilatore inserisce 3 byte di padding dopo il primo `uint8_t` prima del campo `uint32_t v`?
2. Quale formula aritmetica calcola il più piccolo multiplo di `align` maggiore o uguale alla posizione corrente `pos`?
3. Perché anche alla fine dell'ultimo campo possono essere necessari byte di padding di coda?
4. Perché ordinare i campi per allineamento decrescente (`8`, `4`, `2`, `1`) riduce o elimina i buchi di padding interni?

**Esempio di esecuzione**

```input
4
flag1 1 1
timestamp 8 1
codice 2 1
valore 4 1
```

```output
Verifica struct C -> sparso: size=12 align=4 off_v=4, compatto: size=8 align=4 off_c=4
Layout originale:
  flag1: off=0 dim=1 align=1
  timestamp: off=8 dim=8 align=8
  codice: off=16 dim=2 align=2
  valore: off=20 dim=4 align=4
Originale -> size=24 align=8 padding=9
Ottimizzato -> size=16 align=8 padding=1 (risparmio=8 byte)
```

## Riepilogo

- In C23 gli interi con segno usano obbligatoriamente il **complemento a due**: su $N$ bit il bit più significativo ha peso $-2^{N-1}$ e l'intervallo è $[-2^{N-1},\; 2^{N-1} - 1]$ (l'overflow con segno resta comunque comportamento indefinito). I letterali possono essere scritti in binario (`0b...`, C23) o in esadecimale (`0x...`) con separatori `'`. L'header `<stdint.h>` fornisce i tipi a larghezza esatta (`int8_t`..`uint64_t`), `intptr_t`/`uintptr_t` e i relativi limiti (`INT8_MIN`..`UINT64_MAX`, `SIZE_MAX`); `<inttypes.h>` fornisce le macro `PRI*` (`PRIdN`, `PRIuN`, `PRIxN`) per stampare in modo portabile con `printf`.
- Gli operatori bit a bit (`&`, `|`, `^`, `~`) e gli spostamenti (`<<`, `>>`) manipolano direttamente i bit degli interi. Con una **maschera di bit** (`1U << k`) si impostano (`|=`), azzerano (`&= ~`), invertono (`^=`) e controllano (`(x & maschera) != 0U`) singoli bit o sotto-campi. Lavora sempre su tipi senza segno e assicurati che il conteggio di spostamento sia non negativo e strettamente minore della larghezza in bit del tipo promosso.
- Un'**unione** (`union`) sovrappone tutti i propri campi a partire dall'offset `0`: occupa la dimensione del campo più grande (arrotondata all'allineamento massimo) e ha un solo campo attivo alla volta. Un'**unione etichettata** combina in una `struct` un campo `enum` (etichetta) e una `union`, consentendo di verificare sempre l'etichetta con `switch` prima di leggere il campo corrispondente (le ritroveremo nel capitolo 26).
- I **campi di bit** (`unsigned int nome : larghezza;`, `bool flag : 1;`) compattano flag e piccoli contatori dentro una `struct` con aritmetica modulare automatica per i tipi senza segno. Non supportano `&`, `sizeof` né `offsetof`, e il loro layout fisico è dipendente dall'implementazione: usali solo per strutture dati interne, non per formati esterni.
- L'**ordine dei byte** (*little-endian* o *big-endian*) è dipendente dall'implementazione. È sempre lecito ispezionare i byte di un oggetto tramite `const unsigned char *` (o `const uint8_t *`), mentre per scrivere e leggere interi in un buffer in modo indipendente dall'architettura si usano spostamenti (`>>`, `<<`) e maschere (`& 0xFFU`) (li useremo sui file binari nel capitolo 20).
- Ogni tipo ha un requisito di **allineamento** restituito da `alignof(T)` (C23), e `sizeof(T)` è sempre multiplo di `alignof(T)`. Nelle `struct` il compilatore inserisce byte di **padding** (il cui contenuto è non specificato) per rispettare l'allineamento dei campi e della struttura stessa; `offsetof(tipo_struct, campo)` (`<stddef.h>`) ne mostra la posizione esatta. Ordinare i campi per allineamento decrescente riduce o elimina il padding (lo specificatore `alignas` lo vedremo nel capitolo 22).

## Errori comuni

- **Confondere gli operatori bit a bit (`&`, `|`, `~`) con gli operatori logici booleani (`&&`, `||`, `!`) oppure omettere le parentesi in `(valore & MASCHERA) != 0`**: `&&` e `||` valutano vero/falso con corto circuito, non bit per bit; inoltre `!=` e `==` hanno precedenza più alta di `&`, quindi `valore & MASCHERA != 0` viene interpretato come `valore & (MASCHERA != 0)`.
- **Eseguire spostamenti `<<` o `>>` fuori dai limiti o su interi con segno negativi**: spostare di un numero di bit negativo o maggiore o uguale alla larghezza del tipo promosso, oppure spostare a sinistra un intero con segno negativo o in overflow, provoca comportamento indefinito; spostare a destra un intero con segno negativo è dipendente dall'implementazione.
- **Leggere da una `union` un campo diverso dall'ultimo campo scritto oppure dimenticare di controllare l'etichetta**: accedere a un campo inattivo produce un risultato non specificato; nelle unioni etichettate guida sempre ogni accesso con uno `switch` sul campo `enum`.
- **Applicare `&`, `sizeof` o `offsetof` a un campo di bit oppure trasmettere direttamente i byte di una `struct` a campi di bit**: i campi di bit non hanno un indirizzo di byte proprio e il loro ordinamento fisico dipende dal compilatore; per formati binari esterni convertili esplicitamente in un intero a larghezza fissa con maschere e spostamenti.
- **Assumere che tutte le architetture abbiano lo stesso ordine dei byte**: scrivere o leggere direttamente i byte grezzi di un `uint32_t` in memoria lega i dati a little-endian o big-endian; estrai e ricomponi sempre i byte con `>>`, `<<` e `& 0xFFU`.
- **Supporre che `sizeof(struct)` sia uguale alla somma delle dimensioni dei suoi campi**: ignorare il padding porta a calcoli errati sulla memoria occupata e a bug se si tenta di confrontare o salvare byte per byte una struttura senza gestire i campi singolarmente.

## Prima di proseguire

- [ ] So convertire valori tra base 2, base 16 e complemento a due, scegliere i tipi di `<stdint.h>` e stamparli in modo portabile con le macro `PRI*` di `<inttypes.h>`.
- [ ] So scrivere maschere di bit e spostamenti su tipi senza segno per impostare, azzerare, invertire, verificare, impacchettare ed estrarre singoli bit o sotto-campi senza comportamento indefinito.
- [ ] So progettare e manipolare un'unione etichettata (`struct` con `enum` e `union`) accedendo sempre al solo campo attivo tramite `switch`.
- [ ] So definire campi di bit `unsigned int` e `bool`, ne conosco i divieti (`&`, `sizeof`, `offsetof`) e so decidere quando preferire maschere su `uint16_t`/`uint32_t`.
- [ ] So distinguere little-endian e big-endian, scrivere funzioni di *byte swap* e codificare/decodificare interi in un buffer `uint8_t[]` in modo indipendente dall'architettura.
- [ ] So usare `alignof` e `offsetof` per analizzare allineamento e padding di una `struct` e riordinarne i campi per ridurre lo spazio sprecato.
