## 20.4 Accesso casuale con `fseek`, `ftell` e `rewind`

Finora hai letto e scritto i file dall'inizio alla fine, un byte o una riga dopo l'altra. Immagina però un archivio con diecimila record su disco in cui devi leggere o modificare soltanto il record numero `4200`: rileggere ogni volta tutto il file dall'inizio e riscriverlo per intero sprecherebbe tempo e risorse. Quando i record hanno una dimensione fissa in byte, puoi calcolare esattamente dove si trova il record desiderato e saltare subito a quella posizione.

Questo meccanismo si chiama **accesso casuale** (*random access*): è lo spostamento diretto dell'indicatore di posizione all'interno di un file binario mediante `fseek`, `ftell` e `rewind` per leggere o aggiornare record senza scorrere l'intero file.

La funzione centrale è `fseek`, dichiarata in `<stdio.h>`:

```text
int fseek(FILE *stream, long int offset, int whence);
```

Sposta l'indicatore di posizione di `stream` di `offset` byte (positivo, nullo o negativo) a partire dal punto di riferimento `whence`, che può assumere uno di tre valori costanti:

- `SEEK_SET`: dall'inizio del file (`offset >= 0`);
- `SEEK_CUR`: dalla posizione corrente dell'indicatore;
- `SEEK_END`: dalla fine del file.

Se lo spostamento riesce, `fseek` restituisce `0` e azzera l'indicatore di fine file (`feof`); altrimenti restituisce un valore diverso da zero. Controlla sempre `fseek(...) == 0` prima di leggere o scrivere.

Per conoscere la posizione corrente dello stream si chiama `ftell(fp)`:

```text
long int ftell(FILE *stream);
```

Su un file binario `ftell` restituisce la distanza in byte dall'inizio del file come `long int`, oppure `-1L` in caso di errore. Per tornare rapidamente all'inizio del file esiste `rewind(fp)`, che sposta l'indicatore al byte `0` e azzera sia l'indicatore di fine file (`feof`) sia quello di errore (`ferror`), senza però restituire un codice di errore.

In un archivio binario con record di dimensione costante `DIM_REC` byte, l'accesso casuale è diretto:

```text
Byte:   0       12      24      36      48
        +-------+-------+-------+-------+
        | rec 0 | rec 1 | rec 2 | rec 3 |
        +-------+-------+-------+-------+
                ^
                +-- offset = 1 * DIM_REC = 12 (SEEK_SET)
```

Per leggere il record di indice `idx` ti posizioni a `(long)idx * (long)DIM_REC` con `SEEK_SET` ed esegui `fread`. Se poi vuoi **aggiornare quel record in loco** su uno stream aperto in aggiornamento (`"r+b"` o `"w+b"`), ricorda che `fread` ha appena fatto avanzare l'indicatore di `DIM_REC` byte verso il record successivo. Devi quindi chiamare `fseek(fp, -(long)DIM_REC, SEEK_CUR)` prima di `fwrite`: questa singola chiamata svolge due compiti indispensabili allo stesso tempo — riporta l'indicatore all'inizio del record appena letto e soddisfa la regola di alternanza tra lettura e scrittura vista nella sotto-sezione 20.3. Dopo la scrittura, se intendi leggere di nuovo, chiama `fflush(fp)` oppure un'altra `fseek`.

Quando hai bisogno di un file binario temporaneo di appoggio che non debba sopravvivere al programma, la libreria standard mette a disposizione `tmpfile()`:

```text
FILE *tmpfile(void);
```

`tmpfile()` crea e apre automaticamente un file binario temporaneo in modalità `"wb+"` (lettura e scrittura binaria) e garantisce che venga eliminato dal sistema operativo alla chiamata di `fclose` o al termine normale del programma, senza dover inventare nomi di file temporanei. Come `fopen`, restituisce `nullptr` in caso di errore.

Fai attenzione a due importanti limiti di portabilità definiti dallo standard C23:

- Sugli stream binari, il supporto a `SEEK_END` è **dipendente dall'implementazione** (su alcuni sistemi un file binario può avere byte nulli di riempimento in fondo). Per determinare la posizione di accodamento o la dimensione di un archivio a record fissi, è più portabile tenere traccia del numero di record `num_record` e posizionarsi con `SEEK_SET` a `(long)(num_record * DIM_REC)`.
- Sui file di testo, a causa della traduzione dei fine riga, il valore restituito da `ftell` non rappresenta necessariamente un conteggio in byte (il suo significato numerico è **dipendente dall'implementazione**): su uno stream di testo `fseek` è portabile soltanto con offset `0` oppure con un offset ottenuto in precedenza da `ftell` sullo stesso stream con `SEEK_SET`. Inoltre, se la posizione supera l'intervallo rappresentabile da `long int`, `ftell` fallisce restituendo `-1L`.

### Esempio guidato

Il programma seguente apre uno stream binario temporaneo con `tmpfile()`, vi scrive quattro record di dimensione fissa (`12` byte ciascuno, codificati esplicitamente in little-endian: `uint32_t id`, `int32_t temperatura_dec`, `char sigla[4]`), ispeziona la dimensione raggiunta con `ftell`, si sposta direttamente sul secondo record (indice `1`) con `SEEK_SET`, lo aggiorna in loco tornando indietro con `SEEK_CUR` e `fflush`, e infine chiama `rewind` per stampare l'intera tabella aggiornata.

<!-- cod: id=20.4-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static constexpr size_t DIM_REC = 12;

typedef struct sensore {
    uint32_t id;
    int32_t temp_dec;
    char sigla[4];
} sensore_t;

static void codifica(const sensore_t *s, uint8_t b[DIM_REC]) {
    memset(b, 0, DIM_REC);
    for (size_t i = 0; i < 4; ++i) {
        b[i] = (uint8_t)((s->id >> (8 * i)) & 0xFFU);
    }
    uint32_t t = (uint32_t)s->temp_dec;
    for (size_t i = 0; i < 4; ++i) {
        b[4 + i] = (uint8_t)((t >> (8 * i)) & 0xFFU);
    }
    memcpy(b + 8, s->sigla, 3);
}

static void decodifica(const uint8_t b[DIM_REC], sensore_t *s) {
    uint32_t id = 0, t = 0;
    for (size_t i = 0; i < 4; ++i) {
        id |= ((uint32_t)b[i]) << (8 * i);
        t |= ((uint32_t)b[4 + i]) << (8 * i);
    }
    s->id = id;
    s->temp_dec = (int32_t)t;
    memcpy(s->sigla, b + 8, 3);
    s->sigla[3] = '\0';
}

int main(void) {
    FILE *fp = tmpfile();
    if (fp == nullptr) {
        return EXIT_FAILURE;
    }

    const sensore_t iniziali[4] = {
        {101, 215, "NOR"},
        {102, 180, "SUD"},
        {103, 240, "EST"},
        {104, 195, "OVE"}
    };
    uint8_t raw[DIM_REC];
    for (size_t i = 0; i < 4; ++i) {
        codifica(&iniziali[i], raw);
        if (fwrite(raw, 1, DIM_REC, fp) != DIM_REC) {
            fclose(fp);
            return EXIT_FAILURE;
        }
    }
    long dim = ftell(fp);
    if (dim < 0) {
        fclose(fp);
        return EXIT_FAILURE;
    }
    printf("Dimensione archivio: %ld byte\n", dim);

    // Lettura e aggiornamento in loco del record 1 (SUD)
    if (fseek(fp, (long)(1 * DIM_REC), SEEK_SET) != 0 ||
        fread(raw, 1, DIM_REC, fp) != DIM_REC) {
        fclose(fp);
        return EXIT_FAILURE;
    }
    sensore_t s = {};
    decodifica(raw, &s);
    printf("Prima: id=%" PRIu32 " sigla=%s temp=%d\n", s.id, s.sigla, s.temp_dec);

    s.temp_dec += 25;
    codifica(&s, raw);
    if (fseek(fp, -(long)DIM_REC, SEEK_CUR) != 0 ||
        fwrite(raw, 1, DIM_REC, fp) != DIM_REC || fflush(fp) != 0) {
        fclose(fp);
        return EXIT_FAILURE;
    }

    rewind(fp);
    for (size_t i = 0; i < 4; ++i) {
        if (fread(raw, 1, DIM_REC, fp) != DIM_REC) {
            fclose(fp);
            return EXIT_FAILURE;
        }
        decodifica(raw, &s);
        printf("[%zu] id=%" PRIu32 " sigla=%s temp=%" PRId32 "\n",
               i, s.id, s.sigla, s.temp_dec);
    }
    fclose(fp);
    return 0;
}
```

```output
Dimensione archivio: 48 byte
Prima: id=102 sigla=SUD temp=180
[0] id=101 sigla=NOR temp=215
[1] id=102 sigla=SUD temp=205
[2] id=103 sigla=EST temp=240
[3] id=104 sigla=OVE temp=195
```

Nota i punti chiave di questo programma:

- `tmpfile()` apre un file binario in modalità `"wb+"`: non occorre scegliere un nome su disco né chiamare `remove`, perché `fclose(fp)` elimina automaticamente il file temporaneo.
- Dopo aver scritto quattro record da `12` byte ciascuno, `ftell(fp)` restituisce `48L`.
- Per aggiornare il record di indice `1`, ci posizioniamo esattamente al byte `12` con `fseek(fp, (long)(1 * DIM_REC), SEEK_SET)`, leggiamo il record, incrementiamo `temp_dec` da `180` a `205`, torniamo indietro di `12` byte con `fseek(fp, -(long)DIM_REC, SEEK_CUR)` e riscriviamo i `12` byte seguiti da `fflush(fp)`.
- Infine `rewind(fp)` riporta lo stream al byte `0` e azzera eventuali indicatori, permettendo la scansione sequenziale di tutti i quattro record.

> **Approfondimento — Perché `ftell` restituisce `long int`**
> Lo standard C definisce `ftell` e l'offset di `fseek` sul tipo `long int`. Su Linux e macOS a 64 bit `long` occupa 64 bit, ma su piattaforme come Windows a 64 bit `long` occupa 32 bit: in quel caso `fseek` e `ftell` gestiscono offset al massimo fino a circa 2 GiB (`LONG_MAX`). Controlla sempre `ftell(fp) < 0` e verifica che il prodotto `idx * DIM_REC` non superi `LONG_MAX` prima del cast a `long`.

### Esercizio 20.4 — Archivio binario a record fissi con accesso casuale e aggiornamento in loco su più file

**Descrizione**

Scrivi un programma C organizzato su tre file (`archivio_rec.h`, `archivio_rec.c`, `main.c`) che incapsuli un archivio binario a record di dimensione fissa (`24` byte per record) come **tipo opaco** `archivio_rec_t` appoggiato su un file temporaneo aperto con `tmpfile()`. (1) Ogni record su file è codificato esplicitamente in `24` byte little-endian senza scrivere la `struct` direttamente: byte `0..3` `uint32_t id`, byte `4` `uint8_t attivo` (`1` o `0`), byte `5..7` zeri riservati, byte `8..15` `int64_t saldo_cent` (come `uint64_t` LE), byte `16..23` `char codice[8]` (fino a 7 caratteri utili + `'\0'`). (2) In `archivio_rec.h` (protetto da `ARCHIVIO_REC_H`) dichiara `typedef struct archivio_rec archivio_rec_t;`, `typedef struct record_conto { uint32_t id; bool attivo; int64_t saldo_cent; char codice[8]; } record_conto_t;` e le funzioni: `archivio_rec_t *arch_crea(void);`, `void arch_distruggi(archivio_rec_t *a);`, `bool arch_aggiungi(archivio_rec_t *a, const record_conto_t *r, size_t *idx_out);` (usa `fseek` con `SEEK_SET` alla posizione `num_record * 24` e `fwrite`), `bool arch_leggi(archivio_rec_t *a, size_t idx, record_conto_t *out);` (`fseek` + `fread`), `bool arch_aggiorna_saldo(archivio_rec_t *a, size_t idx, int64_t delta_cent, int64_t *nuovo_saldo);` (legge il record, verifica `attivo`, torna indietro di `-24` byte con `fseek(..., -(long)24, SEEK_CUR)` rispettando la regola di alternanza lettura-scrittura e riscrive con `fwrite` + `fflush`), `bool arch_disattiva(archivio_rec_t *a, size_t idx);`, `size_t arch_scansiona_attivi(archivio_rec_t *a, int64_t *somma_saldi);` (usa `rewind` e legge sequenzialmente tutti i record) e `long arch_dimensione_byte(archivio_rec_t *a);` (usa `fseek` e `ftell`). (3) In `main.c` leggi da `stdin` i comandi `ADD <id> <codice> <saldo_cent>`, `GET <idx>`, `DELTA <idx> <variazione>`, `DEL <idx>`, `SUM` e `SIZE`, producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- file binario temporaneo aperto in aggiornamento con `tmpfile()` e chiuso da `arch_distruggi`
- calcolo dello spiazzamento di un record fisso con `fseek(..., SEEK_SET)` e riposizionamento relativo con `fseek(..., -24, SEEK_CUR)`
- rispetto della regola di alternanza tra lettura e scrittura su stream di aggiornamento tramite `fseek` e `fflush`
- interrogazione della dimensione con `ftell` e scansione dall'inizio con `rewind`

**Domande guida**

1. Perché in `arch_aggiorna_saldo` occorre chiamare `fseek(fp, -(long)DIM_REC, SEEK_CUR)` tra `fread` e `fwrite` invece di scrivere subito dopo aver letto?
2. Quale vantaggio offre posizionarsi a `(long)(a->num_record * DIM_REC)` con `SEEK_SET` rispetto all'uso di `SEEK_END` su un file binario?
3. Che cosa fa `rewind(fp)` in `arch_scansiona_attivi` oltre a riportare l'indicatore di posizione all'inizio del file?
4. Perché `tmpfile()` garantisce che non restino file residui sul disco al termine del programma?

**Esempio di esecuzione**

```input
ADD 1001 ALFA 5000
ADD 1002 BETA 1200
ADD 1003 GAMMA -300
SIZE
GET 1
DELTA 1 800
GET 1
DEL 2
DELTA 2 100
SUM
GET 5
```

```output
ADD idx=0 id=1001
ADD idx=1 id=1002
ADD idx=2 id=1003
SIZE: 72 byte
GET[1]: id=1002 cod=BETA saldo=1200 stato=ATTIVO
DELTA[1]: saldo=2000
GET[1]: id=1002 cod=BETA saldo=2000 stato=ATTIVO
DEL[2]: OK
DELTA[2]: NON VALIDO
SUM: attivi=2/3 totale=7000
GET[5]: FUORI LIMITI
```
