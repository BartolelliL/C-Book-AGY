# Capitolo 21 — Robustezza e qualità

> **In questo capitolo imparerai a:**
> - Propagare e diagnosticare errori con codici di ritorno, `errno`, `perror`, `strerror` e operazioni intere controllate di `<stdckdint.h>`
> - Strutturare il rilascio deterministico di più risorse con il modello `goto cleanup`
> - Scrivere asserzioni con `assert` e funzioni variadiche con `<stdarg.h>`
> - Usare macro con argomenti, compilazione condizionale, `__FILE__`, `__LINE__` e attributi C23 (`[[nodiscard]]`, `[[maybe_unused]]`, `[[noreturn]]`) evitando le trappole del preprocessore
> - Spiegare i casi critici di comportamento indefinito e il ruolo di `volatile` e `<signal.h>`

> **Ti servono:** la gestione della memoria dinamica e i sanitizer (capitolo 11), `errno` e le conversioni numeriche sicure (capitolo 14), i programmi su più file con il preprocessore e i tipi opachi (capitolo 19) e la gestione dei file con `<stdio.h>` (capitolo 20).

Un programma che funziona soltanto quando tutti gli input sono ben formati, i file esistono sempre e la memoria non si esaurisce mai è fragile. Nei programmi reali, soprattutto quando crescono fino a diverse centinaia di righe distribuite su più moduli, i guasti fanno parte della normalità: un disco può riempirsi, un numero può superare l'intervallo del tipo, una funzione può acquisire tre risorse in sequenza e fallire alla quarta. Scrivere codice robusto in C significa progettare ogni funzione affinché segnali gli errori in modo esplicito, rilasci in ordine tutte le risorse già acquisite e non scivoli mai nel comportamento indefinito.

In questo capitolo raccogli gli strumenti che lo standard C23 mette a disposizione per trasformare un programma corretto nel caso felice in un software affidabile e diagnosticabile. Vedrai come propagare errori in modo sistematico e come prevenire l'overflow intero con `<stdckdint.h>`, come centralizzare il rilascio delle risorse con il modello `goto cleanup`, come esprimere invarianti interni con `assert` e come costruire interfacce di logging flessibili con le funzioni variadiche di `<stdarg.h>`.

Infine affronterai le macro con argomenti, i simboli di posizione del preprocessore e gli attributi standard del C23, per poi tirare le fila sui casi più pericolosi di comportamento indefinito, sul flusso di lavoro con sanitizer e debugger e sul ruolo di `volatile` e `<signal.h>` nella gestione dei segnali di sistema.

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

## 21.2 Liberare risorse in ordine con `goto cleanup`

Quando una funzione acquisisce una sola risorsa (per esempio un singolo blocco `malloc` o un solo file `fopen`), gestire un errore è immediato: si controlla il puntatore e si esce con `return`. La situazione cambia radicalmente non appena la stessa funzione deve acquisire tre o quattro risorse in sequenza: aprire un file sorgente, allocare due buffer sullo heap, aprire un file di destinazione e, magari, creare un tipo opaco.

Se ogni controllo di errore chiude manualmente tutto ciò che è stato aperto fino a quel momento ed esegue un `return` anticipato, il codice di pulizia viene duplicato in ogni ramo. Al quarto passo devi ricordare di rilasciare le tre risorse precedenti; se in seguito aggiungi una quinta risorsa nel mezzo della funzione, devi aggiornare tutti i rami d'errore successivi. Dimenticarne anche uno solo produce una perdita di memoria o lascia un file aperto.

### Il modello `goto cleanup`

Per risolvere questo problema in modo sistematico, il C idiomatico adotta il modello **goto cleanup**: un modello che usa salti in avanti con `goto` verso un'unica etichetta finale per rilasciare più risorse in ordine inverso senza perdite di memoria.

La struttura segue quattro regole precise:

1. **Inizializza tutte le risorse in testa alla funzione**: prima di qualunque operazione che possa fallire (e quindi prima del primo `goto`), dichiara tutte le variabili di risorsa e inizializzale a `nullptr` (e la variabile di esito al codice di errore predefinito, oppure impostala esplicitamente prima di ogni salto).
2. **Salta sempre in avanti verso una sola etichetta `cleanup:`**: ogni volta che un passo fallisce, imposta il codice di esito appropriato ed esegui `goto cleanup;`.
3. **Sul percorso di successo, imposta l'esito positivo e lascia fluire l'esecuzione dentro `cleanup:`**: in questo modo la pulizia è identica tanto in caso di successo quanto in caso di errore.
4. **Rilascia le risorse in ordine inverso all'acquisizione**: dentro `cleanup:`, libera per prima l'ultima risorsa acquisita e per ultima la prima. Questo rispetta le eventuali dipendenze tra risorse (per esempio un file di uscita chiuso prima dei buffer usati per scriverlo).

Per la memoria dinamica, lo standard garantisce che `free(nullptr)` non fa nulla ed è del tutto sicuro. Per gli stream `FILE *`, invece, chiamare `fclose(nullptr)` provoca **comportamento indefinito**: dentro `cleanup:` occorre sempre proteggerlo con `if (fp != nullptr) { fclose(fp); }`.

### Chiusura controllata dei file di uscita e pulizia dei file parziali

Nel capitolo 20 hai visto che, quando scrivi su un file, un errore di disco pieno può manifestarsi solo al momento di svuotare i buffer dentro `fclose(fout)`. Sul percorso di successo devi quindi controllare il valore restituito da `fclose(fout)` **prima** di dichiarare l'operazione riuscita:

<!-- cod: id=21.2-b tipo=frammento -->
```c
int rc = fclose(fout);
fout = nullptr;  // evita una seconda fclose nel blocco cleanup:
if (rc != 0) {
    esito = ESITO_ERR_IO;
    goto cleanup;
}
esito = ESITO_OK;

cleanup:
if (fout != nullptr) {
    fclose(fout);
}
if (esito != ESITO_OK && fout_creato) {
    remove(percorso_out);
}
```

Osserva due dettagli cruciali in questo frammento:

- **Azzeramento immediato (`fout = nullptr;`)**: subito dopo aver chiamato `fclose(fout)` sul percorso di successo, imposta `fout = nullptr;`. Altrimenti, quando il flusso entra in `cleanup:`, `fout` sarebbe ancora non nullo e verrebbe chiuso una seconda volta (comportamento indefinito).
- **Rimozione di file parziali**: se la funzione ha creato `percorso_out` (`fout_creato == true`) ma l'esito finale non è positivo, `cleanup:` chiude prima `fout` (se è ancora aperto) e poi chiama `remove(percorso_out)` per non lasciare sul disco un file troncato o corrotto.

### Disciplina d'uso di `goto`

L'istruzione `goto` ha cattiva fama quando viene usata per saltare avanti e indietro in modo disordinato (il cosiddetto codice spaghetti), rendendo impossibile capire quali invarianti valgano in un punto del programma. In C, però, `goto` è del tutto legittimo in due situazioni ben delimitate:

1. **Rilascio centralizzato delle risorse (`goto cleanup`)** con salti esclusivamente in avanti verso la fine della funzione.
2. **Uscita immediata da cicli annidati**, quando un semplice `break` uscirebbe solo dal ciclo più interno.

Esistono invece due errori da evitare in modo assoluto:

- **Salti all'indietro**, che vanno sempre sostituiti da `while`, `for` o `do-while`.
- **Salti che scavalcano l'inizializzazione di una variabile locale**: secondo lo standard C23 il salto in avanti con `goto` all'interno della stessa funzione è definito, ma se salti oltre la riga `char *buf = nullptr;` e poi in `cleanup:` esegui `free(buf)`, leggi un valore indeterminato provocando **comportamento indefinito**. Dichiarare e inizializzare tutte le risorse in cima alla funzione prima del primo `goto` elimina il rischio alla radice.

> **Se vieni da Python** — In Python gli errori interrompono automaticamente il flusso con eccezioni (`try`/`except`/`finally`) e le risorse vengono rilasciate dai context manager (`with`); in C gli errori si propagano esplicitamente tramite codici di ritorno ed `errno`, e il rilascio deterministico di più risorse si struttura con il modello `goto cleanup`.

### Esempio guidato

Confronta prima il codice fragile basato su `return` anticipati duplicati:

<!-- cod: id=21.2-c tipo=frammento -->
```c
// STILE FRAGILE: ogni errore deve ricordare tutte le risorse già aperte
FILE *fin = fopen(in_path, "r");
if (fin == nullptr) { return false; }
char *buf1 = malloc(256);
if (buf1 == nullptr) { fclose(fin); return false; }
char *buf2 = malloc(256);
if (buf2 == nullptr) { free(buf1); fclose(fin); return false; }
FILE *fout = fopen(out_path, "w");
if (fout == nullptr) { free(buf2); free(buf1); fclose(fin); return false; }
```

Ecco invece un programma completo che implementa una funzione `filtra_righe_maiuscolo`: apre un file sorgente e un file destinazione, alloca due buffer dinamici per leggere e trasformare in maiuscolo solo le righe non vuote, gestisce ogni errore tramite `goto cleanup` senza perdite di memoria, e infine verifica il file prodotto rimuovendo i file temporanei.

<!-- cod: id=21.2-a tipo=programma -->
```c
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>

static bool filtra_righe_maiuscolo(const char *in_path, const char *out_path) {
    bool ok = false;
    FILE *fin = nullptr;
    char *buf_in = nullptr;
    char *buf_out = nullptr;
    FILE *fout = nullptr;
    bool fout_creato = false;

    fin = fopen(in_path, "r");
    if (fin == nullptr) { goto cleanup; }

    buf_in = malloc(128);
    if (buf_in == nullptr) { goto cleanup; }

    buf_out = malloc(128);
    if (buf_out == nullptr) { goto cleanup; }

    fout = fopen(out_path, "w");
    if (fout == nullptr) { goto cleanup; }
    fout_creato = true;

    while (fgets(buf_in, 128, fin) != nullptr) {
        if (buf_in[0] == '\n' || buf_in[0] == '\0') { continue; }
        size_t i = 0;
        for (; buf_in[i] != '\0'; ++i) {
            buf_out[i] = (char)toupper((unsigned char)buf_in[i]);
        }
        buf_out[i] = '\0';
        if (fputs(buf_out, fout) == EOF) { goto cleanup; }
    }
    if (ferror(fin)) { goto cleanup; }

    int rc = fclose(fout);
    fout = nullptr;
    if (rc != 0) { goto cleanup; }
    ok = true;

cleanup:
    if (fout != nullptr) { fclose(fout); }
    if (!ok && fout_creato) { remove(out_path); }
    free(buf_out);
    free(buf_in);
    if (fin != nullptr) { fclose(fin); }
    return ok;
}

int main(void) {
    const char *f_in = "esempio_21_2_in.txt";
    const char *f_out = "esempio_21_2_out.txt";

    FILE *fp = fopen(f_in, "w");
    if (fp == nullptr) { return EXIT_FAILURE; }
    fputs("prima riga\n\nseconda riga\n", fp);
    if (fclose(fp) != 0) { remove(f_in); return EXIT_FAILURE; }

    if (!filtra_righe_maiuscolo(f_in, f_out)) {
        remove(f_in);
        return EXIT_FAILURE;
    }

    FILE *fr = fopen(f_out, "r");
    if (fr != nullptr) {
        char riga[128];
        while (fgets(riga, (int)sizeof(riga), fr) != nullptr) {
            fputs(riga, stdout);
        }
        fclose(fr);
    }

    remove(f_out);
    remove(f_in);
    return 0;
}
```

```output
PRIMA RIGA
SECONDA RIGA
```

Analizza il blocco `cleanup:` di `filtra_righe_maiuscolo`:

- Tutte e quattro le risorse (`fin`, `buf_in`, `buf_out`, `fout`) sono inizializzate a `nullptr` prima del primo `fopen`.
- Se `fopen(out_path, "w")` fallisce, il salto a `cleanup:` libera `buf_out`, libera `buf_in` e chiude `fin`, saltando sia `fclose(fout)` sia `remove(out_path)`.
- Se invece fallisce `fputs` a metà scrittura, `cleanup:` chiude `fout`, elimina il file parziale `out_path` perché `!ok && fout_creato` è vero, libera i due buffer e chiude `fin`.
- Sul percorso di successo, `fclose(fout)` viene controllato, `fout` viene subito azzerato a `nullptr` e `ok` diventa `true`: in `cleanup:` vengono quindi liberati solo i due buffer e chiuso `fin`, lasciando intatto il file di uscita.

> **Approfondimento — Perché il modello `goto cleanup` è lo standard nei grandi progetti C**
> Nel kernel Linux, in Git e in molte librerie di sistema in C, il modello `goto cleanup` è una convenzione codificata nelle linee guida di stile. Centralizzare il rilascio in un solo punto in fondo alla funzione garantisce che aggiungere una nuova risorsa richieda una sola modifica nel blocco `cleanup:` invece di dover aggiornare decine di rami `if` sparsi nel corpo della funzione, riducendo drasticamente il rischio di perdite di memoria nei percorsi di errore meno testati.

### Esercizio 21.2 — Pipeline multi-risorsa con rilascio deterministico tramite `goto cleanup` e iniezione di guasti

**Descrizione**

Scrivi un programma C che implementi una pipeline di elaborazione su file e memoria dinamica strutturata rigorosamente con il modello **goto cleanup**.

1. Definisci `typedef enum esito_pipe { PIPE_OK = 0, PIPE_ERR_APERTURA_IN, PIPE_ERR_MEM_BUF, PIPE_ERR_MEM_ARRAY, PIPE_ERR_APERTURA_OUT, PIPE_ERR_SCRITTURA } esito_pipe_t;` e `typedef struct stats_risorse { size_t file_aperti; size_t file_chiusi; size_t blocchi_allocati; size_t blocchi_liberati; } stats_risorse_t;`.
2. Scrivi `esito_pipe_t elabora_pipeline(const char *file_in, const char *file_out, size_t n_righe, int guasto_passo, stats_risorse_t *st)` che inizializza tutte e quattro le risorse a `nullptr` (`FILE *fin`, `char *buf`, `int64_t *somme`, `FILE *fout`), le acquisisce in sequenza (`fin = fopen(file_in, "r")`, `buf = malloc(256)`, `somme = malloc(n_righe * sizeof(*somme))` controllando overflow con `ckd_mul`, `fout = fopen(file_out, "w")`), simula il fallimento al passo `guasto_passo` (`1` = apertura input, `2` = buffer, `3` = array somme, `4` = apertura output, `5` = errore di scrittura dopo aver aperto `fout`; `0` = nessun guasto), somma gli interi su ciascuna riga di `file_in` scrivendo `Riga <i>: <somma>` su `file_out`, chiude e verifica `fout` azzerandolo a `nullptr`, e salta sempre a una sola etichetta `cleanup:` in fondo alla funzione che rilascia in ordine inverso tutte le risorse non nulle, rimuove `file_out` se `esito != PIPE_OK` ed aggiorna `st`.
3. In `main` leggi dalla prima riga `n_righe` (`1 <= n_righe <= 16`), scrivi le successive `n_righe` righe di interi nel file temporaneo `"pipe_in_21_2.txt"`, poi leggi i comandi `RUN <guasto_passo>` (`0..5`) eseguendo `elabora_pipeline`, stampando `RUN <g>: <ESITO> (file=<aperti>/<chiusi> mem=<alloc>/<lib>)` e, se `PIPE_OK`, stampando le righe di `"pipe_out_21_2.txt"` indentate di due spazi prima di rimuoverlo. Al termine rimuovi `"pipe_in_21_2.txt"`.

**Concetti da tenere a mente**

- inizializzazione di tutte le risorse a `nullptr` prima di qualsiasi salto `goto`
- salti in avanti verso un'unica etichetta `cleanup:` con rilascio in ordine inverso all'acquisizione
- azzeramento di `fout = nullptr` dopo la chiusura sul percorso di successo per evitare doppie `fclose`
- rimozione del file di uscita parziale quando `esito != PIPE_OK`

**Domande guida**

1. Che cosa accadrebbe nel blocco `cleanup:` se un salto `goto` al passo 2 venisse eseguito prima di inizializzare `somme` e `fout` a `nullptr`?
2. Perché dopo aver chiamato `fclose(fout)` sul percorso di successo devi scrivere subito `fout = nullptr;` prima di proseguire verso `cleanup:`?
3. In quale ordine conviene rilasciare `fin`, `buf`, `somme` e `fout` dentro `cleanup:`?
4. Perché se si verifica un errore al passo 5 (scrittura) il blocco `cleanup:` deve prima chiudere `fout` e poi rimuovere `file_out`?

**Esempio di esecuzione**

```input
2
10 20 30
-5 15
RUN 1
RUN 2
RUN 3
RUN 4
RUN 5
RUN 0
```

```output
RUN 1: ERR_APERTURA_IN (file=0/0 mem=0/0)
RUN 2: ERR_MEM_BUF (file=1/1 mem=0/0)
RUN 3: ERR_MEM_ARRAY (file=1/1 mem=1/1)
RUN 4: ERR_APERTURA_OUT (file=1/1 mem=2/2)
RUN 5: ERR_SCRITTURA (file=2/2 mem=2/2)
RUN 0: OK (file=2/2 mem=2/2)
  Riga 0: 60
  Riga 1: 10
```

## 21.3 Verificare invarianti a tempo di esecuzione con `assert`

Mentre scrivi una struttura dati o un algoritmo non banale, ti basi continuamente su proprietà che *devono* essere sempre vere in determinati punti del codice: in una lista ordinata gli elementi sono in ordine non decrescente; in una coda circolare la lunghezza non supera mai la capacità; un puntatore interno non è mai nullo. Se una di queste ipotesi viene violata, significa che c'è un difetto nella tua logica, e prima scopri la violazione, più facile sarà individuarne la causa.

Per trasformare queste ipotesi in controlli eseguibili, la libreria standard offre in `<assert.h>` la macro `assert`. Un'**asserzione** (*assertion*) è un controllo diagnostico espresso con `assert` che verifica un'ipotesi del programmatore durante lo sviluppo. La sintassi è semplice:

<!-- cod: id=21.3-c tipo=frammento -->
```c
assert(espressione);
```

(Naturalmente, per poterla usare devi includere `#include <assert.h>`.)

### Come funziona `assert` e che cos'è `NDEBUG`

A tempo di esecuzione, `assert(espressione)` valuta `espressione`:

- se il risultato è diverso da zero (vero), non fa nulla e il programma prosegue;
- se il risultato è zero (falso), stampa su `stderr` un messaggio diagnostico contenente l'espressione fallita, il nome del file, il numero di riga e il nome della funzione, e termina immediatamente il programma invocando `abort()` (`<stdlib.h>`).

Lo standard C23 definisce con precisione la semantica di `assert`, l'effetto di `NDEBUG` e la chiamata ad `abort()`; il formato esatto del messaggio diagnostico scritto su `stderr` è invece **comportamento dipendente dall'implementazione**.

Il secondo aspetto fondamentale di `assert` è la sua disabilitazione a tempo di compilazione. Se la macro `NDEBUG` (*no debug*) è definita nel punto in cui il sorgente include `<assert.h>` — tramite `#define NDEBUG` prima dell'`#include <assert.h>`, oppure più comunemente passando l'opzione `-DNDEBUG` al compilatore nelle build di rilascio — allora `assert(espressione)` si espande in `((void)0)`. In quel caso l'espressione **non viene nemmeno valutata** e il controllo ha costo zero nel codice compilato finale.

### Divieto assoluto di effetti collaterali dentro `assert`

Proprio perché `assert(...)` sparisce del tutto quando è definita `NDEBUG`, esiste una regola inviolabile: **l'espressione dentro `assert` non deve mai avere effetti collaterali**. Non deve modificare variabili (`++i`, `x = 0`), non deve eseguire operazioni di I/O (`fopen`, `fgets`) e non deve allocare o modificare strutture dati.

Osserva questo errore tipico:

<!-- cod: id=21.3-b tipo=frammento -->
```c
// ERRORE GRAVE: effetto collaterale dentro assert
assert(++n <= cap);             // con -DNDEBUG, n NON viene incrementato!
assert(fopen("dati.txt", "r") != nullptr); // con -DNDEBUG il file NON viene aperto!
```

Un programma che funziona in modalità debug e fallisce misteriosamente quando viene compilato con `-DNDEBUG` ha quasi sempre un effetto collaterale nascosto dentro un'asserzione. Scrivi sempre l'operazione fuori dall'`assert` e verifica solo il risultato (o, per errori esterni, usa `if`).

### Errori di programmazione contro errori operativi (e `static_assert`)

La distinzione più importante nell'uso delle asserzioni è capire *quando* usarle e *quando* evitarle:

- **Errori di programmazione (usa `assert`)**: violazioni di precondizioni interne di funzioni `static`, postcondizioni o invarianti di una struttura dati (per esempio verificare che dopo un inserimento la lista sia ancora ordinata e che il conteggio dei nodi coincida con `len`). Se falliscono, c'è un bug nel codice sorgente.
- **Errori operativi a tempo di esecuzione (usa `if` e codici di ritorno)**: input dell'utente malformato, file mancanti o illeggibili, fallimenti di `malloc`, o puntatori nulli passati da un chiamante esterno a un'interfaccia pubblica. Questi casi possono accadere anche in un programma privo di bug e devono rimanere gestiti anche quando si compila con `-DNDEBUG`.

Ricorda inoltre la differenza rispetto all'**asserzione statica** `static_assert` vista nel capitolo 15: `static_assert` verifica un'espressione costante **a tempo di compilazione** (per esempio dimensioni di tipi o costanti di configurazione), blocca la compilazione se è falsa e non è influenzata da `NDEBUG`; `assert` verifica invece condizioni **a tempo di esecuzione** durante sviluppo e test e viene disabilitata da `NDEBUG`.

### Esempio guidato

Il programma seguente implementa una piccola lista ordinata dinamica di interi (`lista_ord_t`). Una funzione `controlla_invariante`, protetta da `#ifndef NDEBUG`, verifica senza effetti collaterali che `len <= cap`, che il puntatore `dati` sia coerente con `cap` e che gli elementi siano ordinati in senso non decrescente. Le funzioni di inserimento e rimozione chiamano `assert(controlla_invariante(l))` sia all'ingresso sia all'uscita.

<!-- cod: id=21.3-a tipo=programma -->
```c
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct lista_ord {
    int *dati;
    size_t len;
    size_t cap;
} lista_ord_t;

#ifndef NDEBUG
static bool controlla_invariante(const lista_ord_t *l) {
    if (l == nullptr || l->len > l->cap) { return false; }
    if (l->cap > 0 && l->dati == nullptr) { return false; }
    for (size_t i = 1; i < l->len; ++i) {
        if (l->dati[i - 1] > l->dati[i]) { return false; }
    }
    return true;
}
#endif

static bool lista_inserisci(lista_ord_t *l, int val) {
    if (l == nullptr) { return false; }
    assert(controlla_invariante(l));

    if (l->len == l->cap) {
        size_t nuova_cap = (l->cap == 0) ? 4 : (l->cap * 2);
        int *tmp = realloc(l->dati, nuova_cap * sizeof(*tmp));
        if (tmp == nullptr) { return false; }
        l->dati = tmp;
        l->cap = nuova_cap;
    }

    size_t pos = l->len;
    while (pos > 0 && l->dati[pos - 1] > val) {
        l->dati[pos] = l->dati[pos - 1];
        --pos;
    }
    l->dati[pos] = val;
    ++l->len;

    assert(controlla_invariante(l));
    return true;
}

static bool lista_rimuovi(lista_ord_t *l, int val) {
    if (l == nullptr) { return false; }
    assert(controlla_invariante(l));

    size_t pos = 0;
    while (pos < l->len && l->dati[pos] != val) {
        ++pos;
    }
    if (pos == l->len) { return false; }

    for (size_t i = pos + 1; i < l->len; ++i) {
        l->dati[i - 1] = l->dati[i];
    }
    --l->len;

    assert(controlla_invariante(l));
    return true;
}

int main(void) {
    lista_ord_t lista = {};
    const int valori[] = {30, 10, 20, 10, 5};
    for (size_t i = 0; i < sizeof(valori) / sizeof(valori[0]); ++i) {
        if (!lista_inserisci(&lista, valori[i])) {
            free(lista.dati);
            return EXIT_FAILURE;
        }
    }
    lista_rimuovi(&lista, 10);

    printf("Elementi (%zu):", lista.len);
    for (size_t i = 0; i < lista.len; ++i) {
        printf(" %d", lista.dati[i]);
    }
    printf("\n");

    free(lista.dati);
    return 0;
}
```

```output
Elementi (4): 5 10 20 30
```

Osserva come convivono i controlli difensivi e le asserzioni:

- `if (l == nullptr)` e `if (tmp == nullptr)` gestiscono errori esterni o di memoria con un normale ritorno `false`: rimangono attivi anche compilando con `-DNDEBUG`.
- `assert(controlla_invariante(l))` verifica invece le proprietà interne della struttura dati all'ingresso e all'uscita di ogni modifica.
- La funzione `controlla_invariante` riceve `const lista_ord_t *` e non modifica alcun campo: è completamente priva di effetti collaterali.

> **Approfondimento — Strutturare le funzioni di verifica dell'invariante**
> Raggruppare tutti i vincoli strutturali di un tipo in una funzione ausiliaria `static bool ..._invariante_ok(const T *x)` mantiene leggibili le funzioni operative e permette di richiamare l'intero insieme di controlli con una sola riga `assert(..._invariante_ok(x))`. Racchiudere la definizione di questa funzione dentro `#ifndef NDEBUG ... #endif` evita inoltre che il compilatore emetta un avviso di funzione `static` inutilizzata quando compili in modalità rilascio con `-DNDEBUG`.

### Esercizio 21.3 — Coda circolare dinamica con verifica di invarianti tramite `assert` su più file

**Descrizione**

Realizza una coda circolare FIFO ridimensionabile di `int32_t` come **tipo opaco** su tre file (`coda_inv.h`, `coda_inv.c`, `main.c`) integrando verifiche sistematiche di invarianti con `assert` (`<assert.h>`).

1. In `coda_inv.h` (protetto da `CODA_INV_H`) dichiara `typedef struct coda_inv coda_inv_t;` e le funzioni: `coda_inv_t *coda_crea(void);` (capacità iniziale `2`), `void coda_distruggi(coda_inv_t *q);`, `bool coda_accoda(coda_inv_t *q, int32_t val);` (raddoppia la capacità quando `len == cap` linearizzando gli elementi nel nuovo buffer), `bool coda_estrai(coda_inv_t *q, int32_t *out);`, `bool coda_testa(const coda_inv_t *q, int32_t *out);`, `size_t coda_len(const coda_inv_t *q);`, `size_t coda_cap(const coda_inv_t *q);` e `bool coda_elemento_i(const coda_inv_t *q, size_t idx, int32_t *out);`.
2. In `coda_inv.c` definisci dentro `#ifndef NDEBUG` la funzione `static bool coda_invariante_ok(const coda_inv_t *q)` che verifica senza effetti collaterali: `q != nullptr && q->dati != nullptr`, `q->cap >= 2 && (q->cap & (q->cap - 1)) == 0`, `q->len <= q->cap`, `q->testa < q->cap && q->coda < q->cap`, e `(q->testa + q->len) % q->cap == q->coda`. Gestisci con `if` e valori di ritorno gli errori esterni (puntatori nulli del chiamante, coda vuota, fallimento di `malloc`), e verifica `assert(coda_invariante_ok(q))` all'ingresso e all'uscita di ogni operazione interna (incluso dopo il ridimensionamento).
3. In `main.c` leggi da `stdin` i comandi `ENQ <val>`, `DEQ`, `PEEK`, `STAT` e `DUMP`, producendo esattamente l'output dell'esempio e compilando senza avvisi sia normalmente sia con `-DNDEBUG`.

**Concetti da tenere a mente**

- separazione netta tra validazione di errori esterni (`if` + `bool`) e invarianti interni (`assert`)
- assenza di effetti collaterali dentro `assert(...)` e protezione di `coda_invariante_ok` con `#ifndef NDEBUG`
- invariante circolare esatto `(testa + len) % cap == coda` con capacità sempre potenza di due
- linearizzazione sicura del buffer circolare durante il raddoppio della capacità

**Domande guida**

1. Perché in `coda_estrai` gestisci `q->len == 0` restituendo `false` anziché scrivere `assert(q->len > 0)`?
2. Perché conviene proteggere la definizione della funzione helper `coda_invariante_ok` con `#ifndef NDEBUG`?
3. Che cosa accadrebbe se scrivessi `assert(coda_accoda(q, val))` in `main.c` e poi compilassi con `-DNDEBUG`?
4. Come verifichi che l'invariante `(testa + len) % cap == coda` valga sia quando la coda è vuota (`len == 0`) sia quando è piena (`len == cap`)?

**Esempio di esecuzione**

```input
ENQ 10
ENQ 20
DEQ
ENQ 30
ENQ 40
STAT
DUMP
PEEK
DEQ
DEQ
DEQ
DEQ
```

```output
ENQ 10 (len=1, cap=2)
ENQ 20 (len=2, cap=2)
DEQ: 10
ENQ 30 (len=2, cap=2)
ENQ 40 (len=3, cap=4)
STAT len=3 cap=4
DUMP: 20 30 40
PEEK: 20
DEQ: 20
DEQ: 30
DEQ: 40
DEQ: VUOTA
```

## 21.4 Funzioni variadiche con `<stdarg.h>`

Fin dal capitolo 1 usi `printf` e `fprintf` passando un numero qualsiasi di argomenti: uno, due, cinque, di tipi diversi. Una funzione con questa capacità è una **funzione variadica** (*variadic function*): una funzione che accetta un numero variabile di argomenti, dichiarata con `...` (ellissi) nell'elenco dei parametri e letta tramite gli strumenti dell'intestazione `<stdarg.h>`.

Costruire funzioni variadiche ti permette di scrivere utility di logging personalizzate, formattatori che allocano automaticamente il buffer esatto sullo heap o funzioni di aggregazione flessibili. Poiché però il C non trasmette a tempo di esecuzione né il conteggio né i tipi degli argomenti passati attraverso `...`, questo meccanismo richiede regole rigorose.

### Il ciclo di vita di `va_list`

In `<stdarg.h>` sono definiti il tipo `va_list` e quattro macro che ne governano l'intero ciclo di vita:

1. `va_list ap;` — dichiara lo stato di scorrimento degli argomenti variadici.
2. `va_start(ap, ultimo_parametro);` — inizializza `ap` affinché punti al primo argomento variabile (quello che segue `ultimo_parametro`).
3. `va_arg(ap, tipo)` — estrae l'argomento corrente assumendo che abbia tipo `tipo` e fa avanzare `ap` all'argomento successivo.
4. `va_copy(dest, src)` — copia lo stato corrente di `src` in un secondo `va_list` chiamato `dest`, utile quando devi percorrere due volte la stessa lista di argomenti.
5. `va_end(ap);` — chiude `ap` prima di uscire dalla funzione.

Ogni `va_start` e ogni `va_copy` **deve** essere bilanciato da un corrispondente `va_end` su **tutti** i percorsi di uscita della funzione, inclusi i rami di errore. Secondo lo standard C23, omettere `va_end`, leggere oltre il numero di argomenti effettivamente forniti dal chiamante oppure passare a `va_arg` un tipo incompatibile provoca **comportamento indefinito**.

> **C23** — A partire dallo standard C23, una funzione variadica può anche non avere alcun parametro fisso (`void f(...);`) e `va_start` accetta un solo argomento (`va_start(ap)`), ignorando eventuali argomenti successivi per compatibilità. Con compilatori più vecchi (C17 e precedenti) è obbligatorio almeno un parametro fisso e va usata la forma a due argomenti `va_start(ap, ultimo_parametro)`, che rimane pienamente valida anche in C23.

### Come sapere quanti argomenti leggere

Dato che `va_arg` non sa dove finiscono gli argomenti né che tipo abbiano, la funzione e il chiamante devono concordare una convenzione esplicita. Le tre convenzioni canoniche sono:

- **Contatore iniziale**: un parametro fisso indica il numero di argomenti dello stesso tipo che seguono (per esempio `int somma(size_t n, ...)`).
- **Valore sentinella**: gli argomenti dello stesso tipo si concludono con un valore speciale concordato, tipicamente `nullptr` per una sequenza di puntatori a stringa (per esempio `unisci("a", "b", nullptr)`).
- **Stringa di formato**: una stringa come in `printf` specifica sia quanti argomenti leggere sia il tipo di ciascuno (per esempio `"%s: %d"`).

### Promozioni predefinite degli argomenti variadici

Quando passi un argomento nella parte `...` di una chiamata di funzione, il C applica automaticamente le **promozioni predefinite degli argomenti** (*default argument promotions*):

- ogni tipo intero più stretto di `int` (`bool`, `char`, `signed char`, `unsigned char`, `short`, `unsigned short`) viene promosso a `int` (oppure `unsigned int` se `int` non può rappresentare tutti i valori del tipo originale);
- `float` viene promosso a `double`.

Di conseguenza, dentro `va_arg(ap, tipo)` **non devi mai** scrivere `bool`, `char`, `short` o `float`: se un chiamante ha passato un `bool` o un `char`, la funzione variadica riceve un `int`, quindi devi estrarlo con `va_arg(ap, int)` (e, se serve, convertirlo poi in `bool` o `char`); se ha passato un `float`, devi estrarlo con `va_arg(ap, double)`. Richiedere a `va_arg` un tipo non promosso provoca **comportamento indefinito**.

### Inoltrare `va_list` a `vprintf`, `vfprintf` e `vsnprintf`

Non puoi passare `...` da una funzione variadica a `printf` o `fprintf`. Per scrivere wrapper di formattazione e logging, `<stdio.h>` mette a disposizione le varianti con prefisso `v` che accettano direttamente un `va_list` già inizializzato:

- `int vprintf(const char *restrict format, va_list arg);`
- `int vfprintf(FILE *restrict stream, const char *restrict format, va_list arg);`
- `int vsnprintf(char *restrict s, size_t n, const char *restrict format, va_list arg);`

Dopo che hai passato `ap` a una funzione come `vsnprintf`, lo stato di `ap` diventa indeterminato: non puoi riutilizzarlo una seconda volta. Per implementare il classico **pattern a due passaggi** che alloca una stringa formattata della dimensione esatta sullo heap, usa `va_copy`:

1. inizializza `ap` con `va_start`;
2. crea `va_copy(copia, ap);`;
3. chiama `int len = vsnprintf(nullptr, 0, fmt, copia);` e chiudi subito `va_end(copia);`;
4. se `len >= 0`, alloca `(size_t)len + 1` byte con `malloc`, chiama `vsnprintf(buf, (size_t)len + 1, fmt, ap)` e chiudi `va_end(ap);`.

> **Se vieni da Python** — In Python gli argomenti variabili (`*args`, `**kwargs`) conservano lunghezza e tipi a tempo di esecuzione; in C una funzione variadica (`...`) non conosce né il numero né il tipo degli argomenti ricevuti e si affida completamente al contratto tra chiamante e `va_arg`.

### Esempio guidato

Il programma seguente mostra tre funzioni variadiche: `somma_pesata` (contatore iniziale con promozione da `bool` e `float`), `unisci_con_spazio` (sequenza terminata da sentinella `nullptr` che percorre due volte gli argomenti usando `va_copy`) e `stampa_log` (wrapper che inoltra `va_list` a `vprintf` e `vfprintf`).

<!-- cod: id=21.4-a tipo=programma -->
```c
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static double somma_variadica(size_t n, ...) {
    va_list ap;
    va_start(ap, n);
    double tot = 0.0;
    for (size_t i = 0; i < n; ++i) {
        tot += va_arg(ap, double);
    }
    va_end(ap);
    return tot;
}

static char *unisci_stringhe(const char *prima, ...) {
    if (prima == nullptr) { return nullptr; }
    va_list ap, copia;
    va_start(ap, prima);
    va_copy(copia, ap);

    size_t len = strlen(prima);
    const char *s = nullptr;
    while ((s = va_arg(copia, const char *)) != nullptr) {
        len += 1 + strlen(s);
    }
    va_end(copia);

    char *res = malloc(len + 1);
    if (res == nullptr) {
        va_end(ap);
        return nullptr;
    }

    size_t pos = strlen(prima);
    memcpy(res, prima, pos);
    while ((s = va_arg(ap, const char *)) != nullptr) {
        res[pos++] = '-';
        size_t slen = strlen(s);
        memcpy(res + pos, s, slen);
        pos += slen;
    }
    res[pos] = '\0';
    va_end(ap);
    return res;
}

static void log_messaggio(FILE *out, const char *livello, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    if (out == stdout) {
        printf("[%s] ", livello);
        vprintf(fmt, ap);
        putchar('\n');
    } else {
        fprintf(out, "[%s] ", livello);
        vfprintf(out, fmt, ap);
        fputc('\n', out);
    }
    va_end(ap);
}

int main(void) {
    float f = 1.5f;
    double tot = somma_variadica(3, (double)2, (double)f, 4.25);
    printf("Somma: %.2f\n", tot);

    char *etichetta = unisci_stringhe("mod", "net", "v2", (const char *)nullptr);
    if (etichetta == nullptr) { return EXIT_FAILURE; }
    printf("Etichetta: %s\n", etichetta);
    free(etichetta);

    log_messaggio(stdout, "OK", "avvio nodo=%d stato=%s", 7, "attivo");
    return 0;
}
```

```output
Somma: 7.75
Etichetta: mod-net-v2
[OK] avvio nodo=7 stato=attivo
```

Nota alcuni dettagli tecnici importanti:

- In `somma_variadica(3, (double)2, (double)f, 4.25)`, il `2` viene convertito esplicitamente in `double` perché un letterale `int` non verrebbe promosso a `double` nella parte `...` (estrarre un `int` come `double` con `va_arg` causerebbe comportamento indefinito). Il `float f` verrebbe già promosso a `double`, e il cast rende esplicito il contratto.
- In `unisci_stringhe`, la sentinella finale è scritta `(const char *)nullptr` per assicurare che il tipo passato coincida esattamente con `const char *` richiesto da `va_arg`. `va_copy(copia, ap)` permette di calcolare la lunghezza esatta nel primo passaggio e copiare i byte nel secondo, chiudendo sia `copia` sia `ap` con `va_end` su ogni percorso.
- In `log_messaggio`, `va_list` viene inoltrato a `vprintf` (su `stdout`) o `vfprintf` (su qualsiasi `FILE *`) evitando di duplicare la logica di formattazione.

> **Approfondimento — Perché il C non controlla i tipi oltre `...`**
> A differenza di una funzione con firma fissa, sul lato `...` il compilatore non conosce a priori i tipi attesi dalla funzione chiamata e si limita ad applicare le promozioni predefinite. Un solo disallineamento (per esempio passare un `int` dove la funzione chiama `va_arg(ap, int64_t)` o dimenticare la sentinella `nullptr`) corrompe la lettura dello stack o dei registri provocando comportamento indefinito. Per questo, oltre a documentare contratti chiarissimi, conviene abilitare gli avvisi del compilatore sulle stringhe di formato (`-Wall -Wextra`) e limitare le funzioni variadiche ai casi in cui servono davvero.

### Esercizio 21.4 — Formattatore dinamico e aggregatore variadico con `<stdarg.h>`, `va_copy` e `vsnprintf` su più file

**Descrizione**

Realizza un modulo su tre file (`fmt_variadico.h`, `fmt_variadico.c`, `main.c`) che implementi tre **funzioni variadiche** con `<stdarg.h>` e `<stdio.h>`.

1. `char *formatta_alloc(const char *fmt, ...);`: usa `va_start` e `va_copy` per eseguire una prima chiamata `vsnprintf(nullptr, 0, fmt, copia)` che determina esattamente la lunghezza `len`, chiude `copia` con `va_end`, alloca `(size_t)len + 1` byte con `malloc`, esegue la seconda `vsnprintf` su `ap`, chiude `ap` con `va_end` e restituisce la stringa allocata sullo heap (oppure `nullptr` in caso di errore).
2. `void log_su_stream(FILE *out, const char *tag, const char *fmt, ...);`: scrive `[<tag>] ` sullo stream `out`, inoltra `fmt` e `va_list` a `vfprintf` e chiude la riga con `'\n'`.
3. `bool riepilogo_tipato(const char *spec, double *somma_out, size_t *cont_out, ...);`: scorre ogni carattere di `spec` estraendo il corrispondente argomento con `va_arg`: `'i'` (`int`), `'l'` (`int64_t`), `'d'` (`double`) e `'b'` (`bool`, estratto rigorosamente come `va_arg(ap, int) != 0` nel rispetto delle promozioni predefinite, contribuendo `1.0` o `0.0` alla somma). Se incontra un carattere non riconosciuto chiude comunque `ap` con `va_end` e restituisce `false`.
4. In `main.c` leggi da `stdin` i comandi `FMT <prodotto> <qty> <prezzo>` (chiama `formatta_alloc("Prodotto=%s qty=%d tot=%.2f", ...)`), `LOG <tag> <cod> <msg>` (chiama `log_su_stream(stdout, tag, "cod=%d msg=%s", cod, msg)`), `AGG idb <i> <d> <0|1>`, `AGG ll <a64> <b64>`, `AGG VUOTO` e `AGG ERR` (chiama `riepilogo_tipato("ix", ...)`), producendo l'output esatto dell'esempio senza perdite di memoria.

**Concetti da tenere a mente**

- ciclo di vita completo di `va_list`: `va_start`, `va_copy`, `va_arg` e `va_end` su ogni percorso di uscita
- pattern a due passaggi con `va_copy` e `vsnprintf(nullptr, 0, ...)` per allocare stringhe su misura senza troncamenti
- promozioni predefinite degli argomenti variadici (estrarre `bool` come `int` con `va_arg(ap, int)`)
- inoltro di `va_list` a `vfprintf` per costruire funzioni di logging

**Domande guida**

1. Perché in `formatta_alloc` devi chiamare `va_copy` prima della prima `vsnprintf` anziché passare due volte lo stesso `va_list`?
2. Perché nel caso `'b'` di `riepilogo_tipato` devi scrivere `va_arg(ap, int)` invece di `va_arg(ap, bool)`?
3. Quale errore commetteresti se, incontrando un carattere invalido in `spec`, facessi `return false;` prima di chiamare `va_end(ap)`?
4. Perché `log_su_stream` usa `vfprintf` invece di chiamare direttamente `fprintf`?

**Esempio di esecuzione**

```input
FMT Libro 3 12.50
LOG INFO 200 Avvio
AGG idb 10 2.5 1
AGG ll 100000 250000
AGG VUOTO
AGG ERR
```

```output
FMT (len=30): Prodotto=Libro qty=3 tot=37.50
[INFO] cod=200 msg=Avvio
AGG idb: n=3 somma=13.50
AGG ll: n=2 somma=350000.00
AGG VUOTO: n=0 somma=0.00
AGG: SPECIFICA NON VALIDA
```

## 21.5 Preprocessore: macro con argomenti, `__FILE__` e `__LINE__`

Nel capitolo 19 hai usato `#define` per costanti simboliche e protezioni di inclusione. Il preprocessore permette anche di definire **macro con argomenti** (*function-like macros*), che a prima vista assomigliano a funzioni:

<!-- cod: id=21.5-c tipo=frammento -->
```c
#define QUADRATO(x) ((x) * (x))
```

In realtà una macro non è una funzione: prima ancora che il compilatore veda il codice C, il preprocessore effettua una **sostituzione testuale** pura. Questa differenza è potente, ma nasconde quattro trappole classiche che devi conoscere bene.

### Le trappole delle macro con argomenti

1. **Lo spazio tra nome e parentesi**: in `#define DOPPIO(x) ((x) * 2)` la parentesi `(` deve seguire il nome senza spazi. Se scrivi `#define DOPPIO (x) ((x) * 2)`, definisci una macro *senza argomenti* che si espande letteralmente in `(x) ((x) * 2)` causando errori di compilazione.
2. **Parentesi mancanti attorno ai parametri**: se definisci `#define QUADRATO(x) x * x` e scrivi `QUADRATO(a + 1)`, il preprocessore produce `a + 1 * a + 1`, cioè `a + a + 1` invece di `(a + 1) * (a + 1)`.
3. **Parentesi mancanti attorno al corpo intero**: se definisci `#define SOMMA(a, b) (a) + (b)` e scrivi `SOMMA(2, 3) * 4`, ottieni `(2) + (3) * 4`, cioè `14` invece di `20`. Regola: parentesizza **ogni occorrenza di ogni parametro** e **l'intero corpo** della macro.
4. **Valutazione multipla degli argomenti con effetti collaterali**: anche se parentesizzata in modo perfetto, una macro che usa il proprio parametro due volte espande l'espressione dell'argomento due volte. Osserva il frammento seguente:

<!-- cod: id=21.5-b tipo=frammento -->
```c
// TRAPPOLA: MAX_ERRATO valuta due volte l'argomento più grande
#define MAX_ERRATO(a, b) (((a) > (b)) ? (a) : (b))

int x = 5;
int y = 3;
int m = MAX_ERRATO(++x, y); // si espande in (((++x) > (y)) ? (++x) : (y))
                            // x viene incrementato DUE volte (diventa 7)!
```

Inoltre una macro non effettua alcun controllo sui tipi dei parametri e non compare con un proprio frame nel debugger.

### Quando usare `static inline` e quando usare una macro

Per qualsiasi calcolo riutilizzabile che agisce su valori di tipo noto (come un massimo, un minimo o una saturazione in un intervallo), preferisci sempre una funzione `static inline` nel file di intestazione (capitolo 19): valuta ogni argomento esattamente una volta, controlla i tipi e permette comunque al compilatore di espanderne il corpo in linea senza costi di chiamata.

Riserva le macro con argomenti solo a ciò che una funzione C non può fare:

- **`ARRAY_LEN(arr)`**: calcolare il numero di elementi di un vero array tramite `(sizeof(arr) / sizeof((arr)[0]))`. Una funzione non potrebbe farlo perché un array passato a una funzione decade a puntatore (capitolo 10); per la stessa ragione, non applicare mai `ARRAY_LEN` a un puntatore.
- **Catturare il punto di chiamata** con `__FILE__`, `__LINE__` e `__func__`.
- Costrutti avanzati di metaprogrammazione del preprocessore come blocchi `do { ... } while (0)`, stringificazione `#`, concatenazione di token `##` e macro variadiche (lo vedremo nel capitolo 24).

### Posizione del chiamante: `__FILE__`, `__LINE__` e `__func__`

Il C mette a disposizione tre strumenti standard per registrare automaticamente dove si è verificato un evento nel codice sorgente:

- `__FILE__`: macro predefinita che si espande in un letterale stringa con il nome del file sorgente corrente;
- `__LINE__`: macro predefinita che si espande nella costante intera corrispondente al numero di riga corrente;
- `__func__`: identificatore predefinito (non una macro, bensì un array locale implicito `static const char __func__[]`) contenente il nome della funzione in cui appare.

Combinandoli in una macro che chiama una funzione diagnostica, ogni invocazione registra in automatico il file, la riga e la funzione del chiamante.

### Attributi standard C23: `[[nodiscard]]`, `[[maybe_unused]]`, `[[noreturn]]`

Nel capitolo 4 hai conosciuto il primo **attributo** standard del C23 (`[[fallthrough]]`). Per rendere più robusti i contratti tra moduli, il C23 definisce altri tre attributi fondamentali:

- `[[nodiscard]]` (anche con motivazione `[[nodiscard("controlla l'esito")]]`): applicato a una funzione o a un tipo (`struct`/`enum`), chiede al compilatore di emettere un avviso se il chiamante scarta il valore di ritorno senza usarlo. È ideale per funzioni che restituiscono codici di errore o puntatori appena allocati.
- `[[maybe_unused]]`: applicato a un parametro, una variabile o una funzione `static`, indica al compilatore che quell'entità potrebbe legittimamente non essere usata (per esempio un parametro di debug disabilitato con `NDEBUG`), evitando avvisi spuri con `-Wall -Wextra`.
- `[[noreturn]]`: applicato a una funzione (come `exit` o `abort` nella libreria standard), dichiara che la funzione non restituisce mai il controllo al chiamante. Questo consente al compilatore di segnalare codice morto e di non avvisare se manca un `return` dopo la chiamata. Secondo lo standard C23, se una funzione annotata `[[noreturn]]` ritorna effettivamente al chiamante, il programma incorre in **comportamento indefinito**.

> **C23** — Gli attributi `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]` nella sintassi con doppie parentesi quadre sono stati introdotti dal C23. Con compilatori più vecchi puoi omettere `[[nodiscard]]`, silenziare un parametro inutilizzato con `(void)param;` nel corpo della funzione, e per funzioni che non ritornano affidarti alla documentazione o alle estensioni del compilatore.

### Esempio guidato

Il programma seguente definisce `ARRAY_LEN` e una macro diagnostica `REGISTRA_EVENTO` che cattura `__FILE__`, `__LINE__` e `__func__`; confronta l'helper sicuro `static inline massimo_i32` con il comportamento della macro problematica vista sopra; infine applica `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]`.

<!-- cod: id=21.5-a tipo=programma -->
```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define ARRAY_LEN(a) (sizeof(a) / sizeof((a)[0]))
#define REGISTRA_EVENTO(msg) traccia_punto((msg), __FILE__, __LINE__, __func__)

static inline int32_t massimo_i32(int32_t a, int32_t b) {
    return (a > b) ? a : b;
}

[[nodiscard]] static bool traccia_punto(const char *msg, const char *file,
                                        int riga, const char *func) {
    if (msg == nullptr || file == nullptr || func == nullptr) {
        return false;
    }
    printf("Evento \"%s\" in %s (file valido=%s, riga>0=%s)\n",
           msg, func, (file[0] != '\0') ? "SI" : "NO", (riga > 0) ? "SI" : "NO");
    return true;
}

static void stampa_config(int soglia, [[maybe_unused]] const char *note) {
    printf("Soglia attiva: %d\n", soglia);
}

[[noreturn]] static void interrompi_fatale(const char *motivo) {
    fprintf(stderr, "Errore fatale: %s\n", motivo);
    exit(EXIT_FAILURE);
}

static void verifica_sensori(void) {
    const int32_t letture[] = {12, 45, 31, 18};
    printf("Numero letture: %zu\n", ARRAY_LEN(letture));

    int32_t cont = 10;
    int32_t picco = massimo_i32(++cont, 8);
    printf("massimo_i32(++cont, 8) = %d (cont=%d)\n", picco, cont);

    if (!REGISTRA_EVENTO("controllo completato")) {
        interrompi_fatale("impossibile registrare l'evento");
    }
}

int main(void) {
    stampa_config(40, "versione diagnostica");
    verifica_sensori();
    return 0;
}
```

```output
Soglia attiva: 40
Numero letture: 4
massimo_i32(++cont, 8) = 11 (cont=11)
Evento "controllo completato" in verifica_sensori (file valido=SI, riga>0=SI)
```

Osserva come interagiscono i vari strumenti:

- `ARRAY_LEN(letture)` calcola `4` direttamente a tempo di compilazione sul vero array `letture`.
- `massimo_i32(++cont, 8)` incrementa `cont` una sola volta (`11`), cosa che una macro `MAX(a, b)` non avrebbe garantito.
- `REGISTRA_EVENTO("controllo completato")` si espande dentro `verifica_sensori`, quindi `__func__` vale `"verifica_sensori"`, `__FILE__` contiene il nome del file sorgente e `__LINE__` la riga esatta della chiamata.
- `traccia_punto` è marcata `[[nodiscard]]`, per cui il suo esito viene controllato nell'`if`; il parametro `note` di `stampa_config` è marcato `[[maybe_unused]]` per compilare pulito con `-Wextra`; `interrompi_fatale` è annotata `[[noreturn]]` e termina con `exit(EXIT_FAILURE)`.

> **Approfondimento — Perché `__FILE__` e `__LINE__` richiedono una macro**
> Se inserissi `__FILE__` e `__LINE__` direttamente nel corpo di una funzione di logging (per esempio dentro `traccia_punto`), il preprocessore li espanderebbe nella posizione in cui `traccia_punto` è definita: ogni messaggio riporterebbe sempre lo stesso file e lo stesso numero di riga, rendendo inutile la diagnostica. Facendoli espandere da una macro nel punto di chiamata, invece, ogni invocazione passa alla funzione le coordinate esatte della riga in cui è avvenuto l'errore.

### Esercizio 21.5 — Sistema diagnostico con macro con argomenti (`__FILE__`, `__LINE__`, `__func__`), `static inline` e attributi C23

**Descrizione**

Realizza un modulo diagnostico su tre file (`diagnostica.h`, `diagnostica.c`, `main.c`) che combini macro con argomenti sicure, una funzione `static inline` al posto di una macro soggetta a valutazione multipla, `__FILE__`, `__LINE__`, `__func__` e gli attributi standard C23 `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]`.

1. In `diagnostica.h` (protetto da `DIAGNOSTICA_H`) definisci: le macro `#define ARRAY_LEN(arr) (sizeof(arr) / sizeof((arr)[0]))` e `#define VERIFICA_PASSO(reg, cond, codice) diag_registra((reg), (cond), (codice), __FILE__, __LINE__, __func__)`; la funzione `static inline int32_t satura_i32(int32_t x, int32_t lo, int32_t hi)` (limita `x` a `[lo, hi]` valutando ogni argomento una sola volta); `typedef struct registro_diag { size_t ok; size_t falliti; int primo_codice_err; int prima_riga_err; char primo_file[32]; char prima_func[32]; } registro_diag_t;`; e i prototipi con attributi C23: `[[nodiscard]] bool diag_registra(registro_diag_t *reg, bool cond, int codice, const char *file, int riga, const char *func);`, `[[nodiscard]] bool diag_stampa_riepilogo(const registro_diag_t *reg, [[maybe_unused]] const char *etichetta_debug);` e `[[noreturn]] void diag_errore_fatale(const char *motivo, const char *file, int riga);`.
2. In `diagnostica.c` implementa le tre funzioni: `diag_registra` aggiorna `ok`/`falliti` e al primo fallimento salva `codice`, `riga`, il solo nome base di `file` (dopo l'ultimo `'/'` o `'\\'`) e `func`; `diag_errore_fatale` scrive su `stderr` e chiama `exit(EXIT_FAILURE)`.
3. In `main.c` definisci una funzione helper `esegui_verifica(registro_diag_t *reg, int32_t val, int32_t lo, int32_t hi)` che invoca `VERIFICA_PASSO(reg, val >= lo && val <= hi, 101)` (usando il valore `[[nodiscard]]`) e leggi da `stdin` i comandi `ARRAY` (usa `ARRAY_LEN` su un array locale di 5 `int32_t`), `CHECK <val> <lo> <hi>`, `CLAMP <val> <lo> <hi>` (invoca `satura_i32(++c, lo, hi)` dimostrando che `c` viene incrementato una sola volta) e `REPORT` (chiama `diag_stampa_riepilogo` controllandone il ritorno `[[nodiscard]]`), chiamando `diag_errore_fatale` in caso di comando non riconosciuto.

**Concetti da tenere a mente**

- parentesizzazione completa delle macro con argomenti e uso di `ARRAY_LEN` su veri array
- cattura automatica di `__FILE__`, `__LINE__` e `__func__` nel punto di chiamata tramite macro
- scelta di `static inline` al posto di una macro quando un argomento può avere effetti collaterali (`++c`)
- uso degli attributi C23 `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]`

**Domande guida**

1. Perché `VERIFICA_PASSO` deve essere una macro con argomenti e non una funzione normale affinché `__LINE__` e `__func__` indichino il punto di chiamata?
2. Che cosa succederebbe a `satura_i32(++c, 0, 50)` se fosse scritta come macro `#define SATURA(x, lo, hi) (((x) < (lo)) ? (lo) : (((x) > (hi)) ? (hi) : (x)))`?
3. Perché `ARRAY_LEN(arr)` funziona su un array locale `int32_t soglie[5]` ma produce un risultato errato se applicata a un parametro puntatore `int32_t *p`?
4. Quale contratto comunica al compilatore l'attributo `[[noreturn]]` su `diag_errore_fatale` e quale comportamento si verifica se una funzione `[[noreturn]]` ritorna?

**Esempio di esecuzione**

```input
ARRAY
CHECK 15 0 20
CHECK 25 0 20
CHECK -3 0 20
CLAMP 99 0 50
REPORT
```

```output
ARRAY_LEN: 5
CHECK 15 [0..20]: OK
CHECK 25 [0..20]: FALLITO
CHECK -3 [0..20]: FALLITO
CLAMP(++99, 0, 50) -> 50 (c=100)
REPORT: ok=1 falliti=2 primo_err=101 file=main.c func=esegui_verifica riga_valida=SI
```

## 21.6 Comportamento indefinito, diagnostica e cenni a `volatile` e `signal`

Nel corso del libro hai incontrato più volte il **comportamento indefinito** (*undefined behavior*, UB). In C non significa semplicemente "quella riga produce un valore strano": secondo lo standard, un programma che esegue un'operazione con comportamento indefinito perde qualsiasi garanzia di correttezza sull'intera esecuzione. I compilatori moderni sfruttano l'assenza di UB per ottimizzare il codice: se un'operazione come `x + 1 > x` su un `int` con segno può essere falsa solo in caso di overflow (che è UB), l'ottimizzatore è autorizzato ad assumere che l'overflow non accada mai e a semplificare la condizione in `true` (lo vedremo nel capitolo 25).

### I casi critici di comportamento indefinito

Prima di passare alla Parte IV del libro, è utile avere in mente una mappa sintetica delle sei fonti più frequenti di comportamento indefinito:

- **Dereferenziazione di un puntatore nullo**: leggere o scrivere `*p` quando `p == nullptr` (capitolo 10).
- **Accesso fuori dai limiti**: indicizzare un array o un blocco sullo heap oltre `[0, len - 1]` (capitoli 8 e 11).
- **Uso dopo la liberazione e doppia liberazione**: accedere a memoria già passata a `free` o chiamare `free` due volte sullo stesso indirizzo (capitolo 11).
- **Overflow di interi con segno**: superare `INT_MAX` / `INT64_MAX` o scendere sotto `INT_MIN` / `INT64_MIN`, incluso `INT64_MIN / -1` (capitolo 3 e sotto-sezione 21.1).
- **Lettura di variabili locali non inizializzate**: usare un oggetto con durata di vita automatica prima di avergli assegnato un valore (capitolo 2).
- **Violazione di `restrict`**: passare aree di memoria sovrapposte a parametri dichiarati `restrict`, come in `memcpy` su zone sovrapposte (capitoli 14 e 15).

### Flusso di lavoro diagnostico: avvisi, sanitizer e debugger

Per individuare questi difetti prima che diventino guasti intermittenti, adotta sempre un flusso di lavoro in tre passi:

1. **Compilazione severa con simboli di debug**: compila con `-Wall -Wextra -Wpedantic -g` (aggiungendo `-Werror` nei test automatici). Il flag `-g` inserisce nell'eseguibile le corrispondenze tra istruzioni macchina, file sorgente e numeri di riga.
2. **Analisi dinamica con i sanitizer**: compila ed esegui i test con `-fsanitize=address,undefined` (capitolo 11). AddressSanitizer intercetta accessi fuori dai limiti, uso dopo la liberazione e perdite di memoria; UndefinedBehaviorSanitizer intercetta overflow con segno, spostamenti illegali e dereferenziazioni nulle nel momento esatto in cui avvengono.
3. **Analisi interattiva con un debugger**: un **debugger** è uno strumento che permette di eseguire un programma passo passo, ispezionare variabili e memoria e analizzare gli arresti anomali (come `gdb` o `lldb`, disponibili su Linux, macOS e Windows). Le operazioni essenziali in qualunque debugger sono sempre le stesse: impostare un punto di arresto (*breakpoint*) su una funzione o su una riga, avanzare un'istruzione alla volta (*step* / *next*), stampare il valore di variabili e puntatori e ispezionare lo stack di chiamate (*backtrace*) quando il programma si arresta per un'asserzione fallita o un accesso invalido alla memoria.

### Il qualificatore `volatile`

Un compilatore ottimizzante può mantenere il valore di una variabile in un registro del processore oppure eliminare letture ripetute se vede che il codice C della funzione non modifica quella variabile. Esistono però due situazioni in cui una cella di memoria può cambiare **all'insaputa del normale flusso di controllo**:

- un registro di un dispositivo hardware mappato in memoria (tipico dei sistemi integrati);
- una variabile globale o `static` modificata da un gestore di segnale.

Il qualificatore di tipo `volatile` (per esempio `volatile int flag;`) dice al compilatore che **ogni lettura e ogni scrittura** su quell'oggetto è un effetto osservabile e **non può essere eliminata, riordinata rispetto ad altri accessi `volatile` o tenuta in cache in un registro**.

Fai attenzione a un equivoco molto diffuso: **`volatile` non rende un accesso atomico e non fornisce alcuna sincronizzazione tra thread**. Serve solo a impedire ottimizzazioni del compilatore su singoli accessi in memoria per hardware o gestori di segnale.

### Cenni ai segnali con `<signal.h>`

Un **segnale** è una notifica asincrona o sincrona inviata al programma dal sistema operativo o dal programma stesso (per esempio quando l'utente preme `Ctrl+C` da terminale). L'intestazione standard `<signal.h>` definisce sei segnali portabili:

- `SIGINT`: richiesta di interruzione interattiva (tipicamente `Ctrl+C`);
- `SIGTERM`: richiesta di terminazione ordinata inviata al programma;
- `SIGABRT`: terminazione anomala generata da `abort()` (anche al fallimento di `assert`);
- `SIGFPE`: eccezione aritmetica (per esempio divisione intera per zero);
- `SIGILL`: istruzione macchina illegale;
- `SIGSEGV`: accesso non valido alla memoria (*segmentation fault*).

Le funzioni principali di `<signal.h>` sono due:

- `void (*signal(int sig, void (*func)(int)))(int);` — associa al segnale `sig` la funzione gestore `func`, oppure una delle due costanti speciali `SIG_DFL` (comportamento predefinito del sistema) e `SIG_IGN` (ignora il segnale). Restituisce il gestore precedente, oppure `SIG_ERR` in caso di errore.
- `int raise(int sig);` — invia in modo sincrono il segnale `sig` al programma stesso, restituendo `0` in caso di successo.

Scrivere un gestore di segnale corretto richiede una disciplina severissima. Un segnale può interrompere il programma in qualunque istante, perfino nel mezzo di una chiamata a `malloc` o `printf`. Secondo lo standard C23:

- dentro un gestore di segnale è sicuro leggere e scrivere **solo** oggetti con durata di vita statica di tipo `volatile sig_atomic_t` (un tipo intero definito in `<signal.h>` garantito accessibile come singola entità indivisibile anche in presenza di segnali);
- **non devi mai chiamare funzioni della libreria standard non sicure** come `printf`, `fprintf`, `malloc`, `free` o `exit`: farlo provoca **comportamento indefinito**;
- all'ingresso di un gestore di segnale, se il sistema ripristini automaticamente il segnale a `SIG_DFL` oppure mantenga il gestore registrato è **comportamento dipendente dall'implementazione**. Per portabilità, se il gestore può essere invocato più volte, si richiama `signal(sig, gestore)` al suo interno, mentre la logica vera e propria (stampa di messaggi, chiusura dei file, `free`) va sempre eseguita nel ciclo principale del programma controllando il flag `volatile sig_atomic_t`.

### Esempio guidato

Il programma seguente registra un gestore minimale per `SIGINT` che aggiorna solo una variabile `static volatile sig_atomic_t`, controlla `SIG_ERR`, ignora temporaneamente `SIGTERM` con `SIG_IGN`, invia `SIGTERM` e poi `SIGINT` con `raise`, esce ordinatamente dal ciclo principale al primo controllo del flag e ripristina `SIG_DFL`.

<!-- cod: id=21.6-a tipo=programma -->
```c
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

static volatile sig_atomic_t arresto_richiesto = 0;

static void gestore_sigint(int sig) {
    arresto_richiesto = 1;
    (void)signal(sig, gestore_sigint);
}

int main(void) {
    if (signal(SIGINT, gestore_sigint) == SIG_ERR) {
        fprintf(stderr, "Errore nella registrazione di SIGINT.\n");
        return EXIT_FAILURE;
    }
    if (signal(SIGTERM, SIG_IGN) == SIG_ERR) {
        fprintf(stderr, "Errore nell'impostazione di SIGTERM.\n");
        return EXIT_FAILURE;
    }

    int passi_eseguiti = 0;
    for (int passo = 1; passo <= 5 && !arresto_richiesto; ++passo) {
        printf("Passo %d avviato\n", passo);
        ++passi_eseguiti;

        if (passo == 2) {
            if (raise(SIGTERM) != 0) { return EXIT_FAILURE; }
            printf("SIGTERM inviato ma ignorato: continuo\n");
        }
        if (passo == 3) {
            if (raise(SIGINT) != 0) { return EXIT_FAILURE; }
        }
    }

    (void)signal(SIGINT, SIG_DFL);
    (void)signal(SIGTERM, SIG_DFL);

    printf("Arresto ordinato dopo %d passi (segnale=%d)\n",
           passi_eseguiti, (int)arresto_richiesto);
    return 0;
}
```

```output
Passo 1 avviato
Passo 2 avviato
SIGTERM inviato ma ignorato: continuo
Passo 3 avviato
Arresto ordinato dopo 3 passi (segnale=1)
```

Osserva la separazione dei ruoli:

- `gestore_sigint` esegue soltanto due operazioni consentite dallo standard: assegna `1` alla variabile `static volatile sig_atomic_t arresto_richiesto` e reinstalla se stesso con `signal`. Non esegue alcuna stampa né liberazione di memoria.
- Al passo 2, `raise(SIGTERM)` non interrompe il programma perché `SIGTERM` è impostato a `SIG_IGN`.
- Al passo 3, `raise(SIGINT)` invoca `gestore_sigint`, che imposta `arresto_richiesto = 1`. Al controllo della condizione del ciclo `for`, `!arresto_richiesto` è falso: il programma esce in modo ordinato, ripristina `SIG_DFL` per entrambi i segnali e stampa il riepilogo su `stdout` in piena sicurezza.

> **Approfondimento — Perché dentro un gestore di segnale non puoi chiamare `printf` né `malloc`**
> Le funzioni come `printf` e `malloc` mantengono strutture dati interne condivise (buffer degli stream, liste di blocchi liberi sullo heap). Se un segnale asincrono interrompe il programma proprio mentre `malloc` sta aggiornando i puntatori interni dello heap e il gestore di segnale chiama a sua volta `malloc` o `free`, le strutture interne vengono corrotte in modo imprevedibile (oppure un blocco interno resta bloccato per sempre). Impostare un semplice flag `volatile sig_atomic_t` e reagire fuori dal gestore elimina completamente il problema.

### Esercizio 21.6 — Elaboratore batch con arresto controllato via `<signal.h>` (`volatile sig_atomic_t`, `signal`, `raise`) e difesa da UB

**Descrizione**

Scrivi un programma C che simuli un elaboratore batch con gestione sicura dei segnali di `<signal.h>` e prevenzione dell'overflow con segno tramite `<stdckdint.h>`.

1. Dichiara un flag statico `static volatile sig_atomic_t stato_segnale = 0;` (`0` = attivo, `1` = ricevuto `SIGINT`, `2` = ricevuto `SIGTERM`) e un gestore minimale `static void gestore_arresto(int sig)` che esegua esclusivamente operazioni sicure per i gestori di segnale: imposta `stato_segnale = (sig == SIGINT) ? 1 : 2;` e reinstalla `signal(sig, gestore_arresto);` (senza chiamare `printf`, `malloc` o `free`).
2. In `main` registra `gestore_arresto` per `SIGINT` e `SIGTERM` verificando che `signal` non restituisca `SIG_ERR`, mantieni un array dinamico di `int32_t` sullo heap per i risultati dei lavori completati e leggi comandi da `stdin` finché `stato_segnale == 0`: `WORK <id> <a> <b>` (esegue `ckd_add` su `int32_t`; in caso di overflow stampa `WORK <id>: OVERFLOW EVITATO`, altrimenti salva il risultato nell'array dinamico e stampa `WORK <id>: <somma>`), `IGNORA_TERM` (imposta `signal(SIGTERM, SIG_IGN)` e stampa `SIGTERM: IGNORATO`), `RIATTIVA_TERM` (reinstalla `signal(SIGTERM, gestore_arresto)` e stampa `SIGTERM: GESTITO`), `RAISE_INT` (chiama `raise(SIGINT)`) e `RAISE_TERM` (chiama `raise(SIGTERM)`; se `stato_segnale == 0` stampa `Dopo RAISE_TERM: ancora attivo`).
3. Al termine del ciclo (sia per `EOF` sia per arresto da segnale), ripristina `SIG_DFL` per `SIGINT` e `SIGTERM`, calcola la somma in `int64_t` dei risultati nell'array dinamico, stampa `Arresto: <EOF|SIGINT|SIGTERM> (completati=<n>, somma=<tot>)`, libera la memoria dinamica e restituisci `EXIT_SUCCESS`.

**Concetti da tenere a mente**

- uso esclusivo di `volatile sig_atomic_t` dentro il gestore di segnale senza chiamare `printf`, `malloc` o `free`
- registrazione di gestori, `SIG_IGN` e ripristino di `SIG_DFL` con controllo di `SIG_ERR`
- invio sincrono di segnali con `raise` e arresto ordinato controllato dal ciclo principale
- prevenzione del comportamento indefinito (overflow con segno tramite `ckd_add` e rilascio memoria all'arresto)

**Domande guida**

1. Perché `stato_segnale` deve essere qualificato sia `volatile` sia `sig_atomic_t`?
2. Perché `gestore_arresto` non deve stampare il messaggio `"Arresto: SIGINT"` direttamente con `printf` né chiamare `free`?
3. Che cosa accade quando viene eseguito `RAISE_TERM` dopo `IGNORA_TERM` rispetto a dopo `RIATTIVA_TERM`?
4. Perché `gestore_arresto` richiama `signal(sig, gestore_arresto)` al proprio interno?

**Esempio di esecuzione**

```input
WORK 1 100 250
WORK 2 2147483640 20
IGNORA_TERM
RAISE_TERM
WORK 3 -40 15
RIATTIVA_TERM
RAISE_INT
WORK 4 1 1
```

```output
WORK 1: 350
WORK 2: OVERFLOW EVITATO
SIGTERM: IGNORATO
Dopo RAISE_TERM: ancora attivo
WORK 3: -25
SIGTERM: GESTITO
Arresto: SIGINT (completati=2, somma=325)
```

## Riepilogo

- In C gli errori si propagano esplicitamente tramite codici di ritorno (`enum` di stato, `bool`, `nullptr`, `EOF`) separando il risultato nei parametri di uscita. Per le funzioni che usano `errno` (`<errno.h>`, con le costanti standard `EDOM`, `ERANGE` ed `EILSEQ`), occorre azzerare `errno = 0` prima della chiamata e salvarlo subito in una variabile locale in caso di fallimento; `perror` (`<stdio.h>`) e `strerror` (`<string.h>`, stringa non modificabile) producono messaggi diagnostici leggibili. Le macro C23 `ckd_add`, `ckd_sub` e `ckd_mul` (`<stdckdint.h>`) rilevano gli overflow sugli interi senza comportamento indefinito.
- Il modello **goto cleanup** centralizza il rilascio di più risorse in un'unica etichetta finale `cleanup:`: tutte le risorse vanno inizializzate a `nullptr` prima del primo salto, i salti vanno sempre in avanti e il rilascio avviene in ordine inverso all'acquisizione (ricordando di azzerare `fp = nullptr` dopo una `fclose` anticipata e di rimuovere eventuali file parziali in caso di errore).
- Un'**asserzione** con `assert` (`<assert.h>`) verifica a tempo di esecuzione precondizioni e invarianti interni durante lo sviluppo, terminando con `abort()` se la condizione è falsa. Con `NDEBUG` definito, `assert` viene disabilitata e l'espressione non è valutata: non inserire mai effetti collaterali dentro `assert` e usa sempre `if` e codici di ritorno per gli errori esterni.
- Una **funzione variadica** (`...`) accede agli argomenti tramite `va_list`, `va_start`, `va_arg`, `va_copy` e `va_end` (`<stdarg.h>`), rispettando le promozioni predefinite (`bool`, `char`, `short` -> `int`; `float` -> `double`) e chiudendo ogni `va_list` su tutti i percorsi di uscita. `vprintf`, `vfprintf` e `vsnprintf` permettono di inoltrare `va_list` per logging e formattazione dinamica a due passaggi.
- Le macro con argomenti effettuano sostituzione testuale: richiedono parentesi su ogni parametro e sull'intero corpo, nessun spazio prima di `(` e nessuna valutazione multipla di argomenti con effetti collaterali; quando possibile vanno sostituite da funzioni `static inline`. `__FILE__`, `__LINE__` e `__func__` registrano la posizione del chiamante (tecniche avanzate del preprocessore saranno approfondite più avanti, lo vedremo nel capitolo 24), mentre gli attributi C23 `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]` rafforzano i contratti verificati dal compilatore.
- Prevenire il comportamento indefinito richiede avvisi severi (`-Wall -Wextra -Wpedantic -g`), sanitizer (`-fsanitize=address,undefined`) e un **debugger** (l'interazione tra UB e ottimizzazioni del compilatore sarà ripresa in dettaglio, lo vedremo nel capitolo 25). `volatile` impedisce l'eliminazione o la messa in cache degli accessi a memoria esterna o a flag di segnale, ma non sincronizza thread; in `<signal.h>`, un gestore registrato con `signal` può accedere in sicurezza solo a oggetti statici `volatile sig_atomic_t`, mai a `printf`, `malloc` o `free`.

## Errori comuni

- **Dimenticare di azzerare `errno = 0` prima della chiamata o leggerlo troppo tardi**: leggere `errno` dopo aver già invocato `fprintf` o `fclose` può restituire un codice sovrascritto da quelle chiamate invece dell'errore originario.
- **Inserire effetti collaterali dentro `assert(...)` o usare `assert` per validare input esterni**: espressioni come `assert(fopen(...) != nullptr)` o `assert(++i < n)` spariscono completamente compilando con `-DNDEBUG`, introducendo bug silenziosi nelle build di rilascio.
- **Saltare con `goto cleanup` oltre l'inizializzazione di un puntatore o dimenticare `fp = nullptr` dopo `fclose`**: liberare un puntatore non inizializzato o chiudere due volte lo stesso `FILE *` provoca comportamento indefinito.
- **Passare tipi non promossi (`char`, `short`, `bool`, `float`) a `va_arg`, riutilizzare `va_list` senza `va_copy` o omettere `va_end`**: sono tutte violazioni che provocano comportamento indefinito nelle funzioni variadiche.
- **Scrivere macro con argomenti senza parentesi o passandovi espressioni come `x++`, oppure chiamare `printf`/`malloc` in un gestore di segnale**: nel primo caso si ottengono risultati errati o effetti collaterali duplicati; nel secondo caso si corrompono gli stati interni della libreria standard.

## Prima di proseguire

- [ ] So progettare funzioni che propagano errori con `enum` di stato, `errno`, `perror`, `strerror` e aritmetica controllata con `<stdckdint.h>`.
- [ ] So strutturare il rilascio di più file e blocchi dinamici con il modello `goto cleanup` senza perdite di memoria né doppie chiusure.
- [ ] So distinguere invarianti interni verificati con `assert` (privi di effetti collaterali e compatibili con `-DNDEBUG`) da errori operativi gestiti con `if`.
- [ ] So scrivere funzioni variadiche sicure con `<stdarg.h>`, `va_copy`, `vfprintf` e `vsnprintf` rispettando le promozioni predefinite.
- [ ] So scrivere macro con argomenti sicure (`ARRAY_LEN`, `__FILE__`, `__LINE__`, `__func__`), scegliere `static inline` quando appropriato e applicare `[[nodiscard]]`, `[[maybe_unused]]` e `[[noreturn]]`.
- [ ] So usare avvisi severi, sanitizer e debugger contro il comportamento indefinito, e conosco il ruolo di `volatile` e i limiti dei gestori di segnale in `<signal.h>`.
