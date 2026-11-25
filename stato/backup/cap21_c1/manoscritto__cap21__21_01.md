## 21.1 Gestione degli errori: codici di ritorno, `errno` e `perror`

Quando un programma supera qualche decina di righe, gli errori smettono di essere eccezioni rare e diventano parte integrante del flusso di esecuzione. Una funzione può fallire perché un file non esiste, perché una stringa non rappresenta un intero valido, perché un calcolo va in overflow o perché lo heap non ha memoria sufficiente. In C non esiste un meccanismo automatico che interrompa le chiamate a catena quando qualcosa va storto: ogni funzione deve restituire un segnale chiaro al chiamante, e ogni chiamante deve controllarlo prima di procedere.

### Codici di ritorno espliciti e parametri di uscita

La strategia più limpida e diffusa in C consiste nel separare il **canale del risultato** dal **canale dell'esito**. La funzione riceve un puntatore come parametro di uscita (per esempio `int64_t *out`) in cui scrive il valore calcolato solo in caso di successo, e riserva il proprio valore di ritorno a un codice di stato.

A seconda della ricchezza delle informazioni richieste, il valore di ritorno assume una di queste forme:

- `bool`, quando al chiamante basta sapere se l'operazione è riuscita (`true`) oppure fallita (`false`);
- un puntatore (`nullptr` in caso di fallimento), come fanno `malloc` e `fopen`;
- un valore sentinella intero come `EOF` o `-1`, quando i valori validi sono non negativi;
- una `enum` di stato descrittiva (con il successo fissato a `0`), quando il chiamante deve distinguere con precisione cause diverse di errore, per esempio sintassi errata, divisione per zero o overflow.

Un'enumerazione di stato rende il contratto leggibile e consente di propagare l'errore in modo uniforme a ogni livello di chiamata: una funzione intermedia controlla l'esito della sotto-funzione, e se è diverso dal valore di successo lo restituisce subito al proprio chiamante senza mascherarlo.

### La macro `errno` e le costanti standard

Molte funzioni della libreria standard (come `strtoll`, `strtod`, `fopen` o `sqrt`) comunicano il fallimento tramite il valore di ritorno, ma registrano la causa specifica in una variabile di errore globale al thread esposta dalla macro `errno` di `<errno.h>`, che hai già incontrato brevemente nel capitolo 14 per `ERANGE`.

Lo standard C23 definisce tre costanti intere positive in `<errno.h>`:

- `EDOM` (*domain error*): un argomento è fuori dal dominio matematico della funzione (per esempio `sqrt` di un numero negativo);
- `ERANGE` (*range error*): il risultato è troppo grande o troppo piccolo per essere rappresentato dal tipo di ritorno (per esempio un numero fuori scala in `strtoll` o `strtod`);
- `EILSEQ` (*illegal byte sequence*): una sequenza di byte non è valida nella codifica attesa.

I sistemi operativi aggiungono molte altre costanti (come il codice per file inesistente o permessi insufficienti), ma solo `EDOM`, `ERANGE` ed `EILSEQ` sono garantite dallo standard su qualsiasi piattaforma.

Usare `errno` in modo corretto richiede due regole ferree:

1. **Azzeramento preventivo**: la libreria standard non azzera mai `errno` quando una funzione ha successo. Se `errno` contiene un codice residuo di un errore precedente, leggerlo dopo una chiamata riuscita trae in inganno. Prima di chiamare una funzione che segnala errori tramite `errno`, scrivi sempre `errno = 0;`.
2. **Salvataggio immediato**: in caso di fallimento, copia subito `errno` in una variabile locale (`int err = errno;`) prima di invocare qualsiasi altra funzione di libreria, incluse `fprintf` o `fclose`.

### Diagnostica leggibile con `perror` e `strerror`

Un codice numerico come `2` o `34` dice poco a chi legge un messaggio di errore. La libreria standard offre due funzioni per tradurre `errno` in testo comprensibile:

- `void perror(const char *s);` (`<stdio.h>`): stampa su `stderr` il prefisso `s` (se diverso da `nullptr` e non vuoto), seguito da `": "`, dal messaggio descrittivo associato al valore corrente di `errno` e da un carattere di a capo `'\n'`.
- `char *strerror(int errnum);` (`<string.h>`): restituisce un puntatore a una stringa descrittiva associata al codice `errnum` (puoi passarle direttamente la copia salvata `err`).

La stringa restituita da `strerror` appartiene alla libreria standard e va trattata come di sola lettura: secondo lo standard C23, il testo esatto prodotto da `perror` e `strerror` è **comportamento dipendente dall'implementazione** (può variare tra sistemi operativi e dipendere dalla lingua di sistema), mentre modificare i caratteri della stringa restituita da `strerror` provoca **comportamento indefinito**. Inoltre una chiamata successiva a `strerror` può sovrascrivere il buffer interno restituito dalla chiamata precedente: se devi conservarne il testo, copialo subito o stampalo immediatamente.

### Aritmetica intera controllata con `<stdckdint.h>`

Nel capitolo 3 hai visto che l'overflow sugli interi con segno è **comportamento indefinito**, mentre sugli interi senza segno avvolge silenziosamente modulo $2^N$. Scrivere a mano i controlli preventivi prima di ogni somma, sottrazione o moltiplicazione è verboso e facile da sbagliare, soprattutto quando si mescolano tipi con larghezze o segni diversi.

Il C23 risolve questo problema con l'intestazione `<stdckdint.h>`, che fornisce tre macro tipizzate per eseguire operazioni intere controllate:

- `bool ckd_add(type1 *result, type2 a, type3 b);`
- `bool ckd_sub(type1 *result, type2 a, type3 b);`
- `bool ckd_mul(type1 *result, type2 a, type3 b);`

Ciascuna macro calcola il risultato matematico esatto (come se disponesse di precisione infinita), lo converte nel tipo di `*result` memorizzandolo in `*result`, e restituisce:

- `false` se il valore memorizzato in `*result` coincide con il risultato matematico esatto (nessun overflow);
- `true` se si è verificato un overflow: in questo caso `*result` contiene comunque il risultato troncato modulo $2^N$ (dove $N$ è la larghezza in bit del tipo di `*result`), **senza alcun comportamento indefinito**.

Nota bene la convenzione del valore di ritorno: `true` segnala che c'è stato un errore di overflow, così puoi scrivere in modo naturale `if (ckd_mul(&byte_tot, n, sizeof(int64_t))) { ... }`. Un altro vantaggio notevole è che `a`, `b` e `*result` possono avere tipi interi diversi (purché interi standard diversi da `bool` e dai tipi carattere `char`): la macro esegue il calcolo sul valore matematico esatto e verifica se rientra nell'intervallo del tipo di destinazione.

> **C23** — L'intestazione `<stdckdint.h>` e le macro `ckd_add`, `ckd_sub`, `ckd_mul` sono state introdotte dallo standard C23. Con compilatori più vecchi (C11/C17) occorre scrivere funzioni ausiliarie che confrontino gli operandi con i limiti di `<limits.h>` o `<stdint.h>` prima di eseguire l'operazione (per esempio verificando `b > 0 && a > INT64_MAX - b` prima di `a + b`), oppure ricorrere alle estensioni specifiche del compilatore.

### Esempio guidato

Il programma seguente verifica tre operazioni su `int64_t` con `ckd_add`, `ckd_sub` e `ckd_mul` (mostrando sia il caso esatto sia l'overflow rilevato senza comportamento indefinito), tenta di aprire un file inesistente diagnosticando il fallimento con `errno`, `perror` e `strerror`, e controlla un argomento negativo passato a `sqrt` verificando `EDOM`.

<!-- cod: id=21.1-a tipo=programma -->
```c
#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdckdint.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void prova_aritmetica(void) {
    int64_t ris = 0;

    if (!ckd_add(&ris, INT64_MAX - 10, 5)) {
        printf("Somma esatta: %" PRId64 "\n", ris);
    }
    if (ckd_add(&ris, INT64_MAX - 10, 20)) {
        printf("Somma in overflow rilevata senza UB\n");
    }
    if (ckd_sub(&ris, INT64_MIN, 1)) {
        printf("Sottrazione in overflow rilevata senza UB\n");
    }
    if (ckd_mul(&ris, (int64_t)3'037'000'500, (int64_t)3'037'000'500)) {
        printf("Moltiplicazione in overflow rilevata senza UB\n");
    }
}

static bool radice_sicura(double x, double *out) {
    if (x < 0.0) {
        errno = EDOM;
        return false;
    }
    errno = 0;
    *out = sqrt(x);
    return true;
}

int main(void) {
    prova_aritmetica();

    errno = 0;
    FILE *fp = fopen("file_che_non_esiste_21_1.txt", "r");
    if (fp == nullptr) {
        int err = errno;
        perror("fopen fallita");
        const char *desc = strerror(err);
        printf("Apertura fallita: errno != 0 (%s), strerror valido (%s)\n",
               (err != 0) ? "SI" : "NO",
               (desc != nullptr && desc[0] != '\0') ? "SI" : "NO");
    } else {
        fclose(fp);
    }

    double rad = 0.0;
    if (!radice_sicura(-4.0, &rad)) {
        int err_math = errno;
        printf("sqrt(-4.0): errore di dominio rilevato (EDOM=%s)\n",
               (err_math == EDOM) ? "SI" : "NO");
    }
    return 0;
}
```

```output
Somma esatta: 9223372036854775802
Somma in overflow rilevata senza UB
Sottrazione in overflow rilevata senza UB
Moltiplicazione in overflow rilevata senza UB
Apertura fallita: errno != 0 (SI), strerror valido (SI)
sqrt(-4.0): errore di dominio rilevato (EDOM=SI)
```

Osserva i punti chiave dell'esempio:

- In `prova_aritmetica`, `ckd_add`, `ckd_sub` e `ckd_mul` valutano espressioni che con `+`, `-` e `*` avrebbero provocato comportamento indefinito su `int64_t`. Le macro restituiscono `true` e permettono di gestire il problema in modo pulito.
- Prima di `fopen` si azzera esplicitamente `errno = 0;`. Subito dopo il fallimento si salva `int err = errno;`, poi si chiama `perror("fopen fallita")` (che scrive il messaggio dettagliato su `stderr`) e si interroga `strerror(err)` usando la copia locale.
- Per la radice quadrata di `-4.0`, la funzione `radice_sicura` controlla esplicitamente il dominio (`x < 0.0`), imposta `errno = EDOM` e restituisce `false`: in questo modo la segnalazione tramite `EDOM` è garantita in modo portabile anche sulle piattaforme dove `sqrt` segnala gli errori di dominio solo tramite `NaN` ed eccezioni in virgola mobile. L'output mostrato sopra è quello su `stdout`; su `stderr` comparirà inoltre la riga prodotta da `perror`, il cui testo esatto dipende dal sistema operativo.

> **Approfondimento — Perché salvare subito `int err = errno;`**
> Dopo il fallimento di una funzione come `fopen` o `strtoll`, qualunque chiamata successiva alla libreria standard può sovrascrivere `errno`, perfino se ha successo (lo standard C consente alle funzioni di libreria di modificare `errno` a un valore non nullo anche quando non falliscono, purché non lo azzerino). Se chiamassi `fclose` su un altro stream o `fprintf` prima di leggere `errno`, rischieresti di stampare un codice estraneo o azzerato. Copiare immediatamente `int err = errno;` in una variabile locale elimina questa fonte di errori sottili.

### Esercizio 21.1 — Calcolatrice controllata a 64 bit con `<stdckdint.h>`, `errno` e propagazione di codici di errore

**Descrizione**

Scrivi un programma C che implementi una calcolatrice sicura su interi a 64 bit (`int64_t`) e radici quadrate in virgola mobile, propagando ogni guasto mediante un'enumerazione `esito_calc_t` (`CALC_OK`, `CALC_ERR_SINTASSI`, `CALC_ERR_OVERFLOW`, `CALC_ERR_DIV_ZERO`, `CALC_ERR_DOMINIO`, `CALC_ERR_RANGE`).

1. Implementa `esito_calc_t parsa_i64(const char *s, int64_t *out)` usando `strtoll` dopo `errno = 0`, controllando `errno == ERANGE` (`CALC_ERR_RANGE`) e caratteri residui (`CALC_ERR_SINTASSI`).
2. Implementa `esito_calc_t esegui_op(const char *op, int64_t a, int64_t b, int64_t *out)` che gestisce: `ADD` con `ckd_add`, `SUB` con `ckd_sub`, `MUL` con `ckd_mul` (di `<stdckdint.h>`, restituendo `CALC_ERR_OVERFLOW` quando la macro restituisce `true`), `DIV` (controllando `b == 0` -> `CALC_ERR_DIV_ZERO` e `a == INT64_MIN && b == -1` -> `CALC_ERR_OVERFLOW`) e `AREA` (se `a < 0 || b < 0` imposta `errno = EDOM`, verifica che `strerror(EDOM)` non sia nullo né vuoto e restituisce `CALC_ERR_DOMINIO`, altrimenti usa `ckd_mul`).
3. Implementa `esito_calc_t calcola_radice(const char *s, double *out)` usando `strtod` con `errno = 0` (`ERANGE`/`HUGE_VAL` -> `CALC_ERR_RANGE`), rifiutando `x < 0.0` con `errno = EDOM` (`CALC_ERR_DOMINIO`), e calcolando `sqrt(x)`.
4. In `main` leggi righe da `stdin` (`ADD <a> <b>`, `SUB <a> <b>`, `MUL <a> <b>`, `DIV <a> <b>`, `AREA <a> <b>`, `SQRT <x>`) salvando `int err_salvato = errno;` subito dopo il fallimento e stampando `OK: <ris>` (con `%.2f` per `SQRT`) oppure `ERRORE: <TIPO> (errno=<EDOM|ERANGE|0>)` esattamente come nell'esempio.

**Concetti da tenere a mente**

- operazioni intere controllate `ckd_add`, `ckd_sub` e `ckd_mul` (`<stdckdint.h>`) per rilevare overflow senza comportamento indefinito
- propagazione esplicita degli errori tramite `enum` e parametri di uscita
- azzeramento preventivo di `errno = 0`, salvataggio immediato e distinzione tra `EDOM` ed `ERANGE`
- caso particolare di overflow nella divisione con segno (`INT64_MIN / -1`) e controllo di `strerror`

**Domande guida**

1. Perché `ckd_add(&ris, a, b)` evita il comportamento indefinito anche quando `a + b` supera `INT64_MAX`?
2. Che cosa restituisce `ckd_mul` quando il prodotto è rappresentabile senza overflow: `true` oppure `false`?
3. Oltre alla divisione per zero, quale coppia di operandi provoca overflow nella divisione intera `a / b` su `int64_t`?
4. Perché conviene salvare subito `errno` in una variabile locale `int err = errno;` prima di stampare o invocare altre funzioni?

**Esempio di esecuzione**

```input
ADD 9223372036854775800 7
ADD 9223372036854775800 10
SUB -9223372036854775808 1
MUL 3037000500 3037000500
DIV -9223372036854775808 -1
DIV 10 0
AREA -5 4
SQRT 2.25
SQRT -9
ADD 99999999999999999999999 1
```

```output
OK: 9223372036854775807
ERRORE: OVERFLOW (errno=0)
ERRORE: OVERFLOW (errno=0)
ERRORE: OVERFLOW (errno=0)
ERRORE: OVERFLOW (errno=0)
ERRORE: DIV_ZERO (errno=0)
ERRORE: DOMINIO (errno=EDOM)
OK: 1.50
ERRORE: DOMINIO (errno=EDOM)
ERRORE: RANGE (errno=ERANGE)
```
