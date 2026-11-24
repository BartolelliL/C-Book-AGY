## 20.5 Salvare e caricare strutture: formati binari e versioni

Quando devi salvare su file una struttura C, la tentazione più forte è scrivere una sola riga:

<!-- cod: id=20.5-b tipo=frammento -->
```c
// FRAGILE E NON PORTABILE: non salvare mai una struct grezza così!
fwrite(&record, sizeof(record), 1, fp);
```

Questo approccio sembra comodo, ma fallisce per quattro motivi strutturali che conosci già dal capitolo 13:

1. **Ordine dei byte**: un intero multibyte scritto su una macchina little-endian verrebbe letto con i byte invertiti su una macchina big-endian.
2. **Allineamento e padding**: compilatori diversi (o persino versioni e opzioni diverse dello stesso compilatore) possono inserire quantità diverse di byte di **padding** dentro e in fondo alla `struct`. Inoltre i byte di padding hanno contenuto **non specificato**: scriverli su disco significa riversare nel file dati casuali rimasti sullo stack o sullo heap.
3. **Dimensione dei tipi**: tipi come `int` o `long` non hanno una larghezza garantita identica su tutte le piattaforme.
4. **Puntatori**: se la `struct` contiene un campo puntatore (per esempio `char *nome`), `fwrite` scrive l'indirizzo di memoria corrente, non i caratteri della stringa. Alla successiva esecuzione quell'indirizzo non punta più a nulla e dereferenziarlo provoca comportamento indefinito.

La soluzione professionale è la **serializzazione** (*serialization*): la conversione di strutture dati in memoria in una sequenza portabile di byte o testo da salvare su file e ricostruire in seguito. Nella serializzazione binaria portabile decidi tu, byte per byte, il formato esatto del file:

- Ogni campo numerico usa un tipo a larghezza fissa di `<stdint.h>` (`uint8_t`, `uint16_t`, `uint32_t`, `int32_t`, `int64_t`) ed è codificato e decodificato esplicitamente in **big-endian** o **little-endian** tramite spostamenti bit a bit (`>>`, `<<`) e maschere (`& 0xFFU`). Questa codifica è completamente definita dallo standard C23 e produce gli stessi identici byte su qualsiasi processore e compilatore.
- Le stringhe di lunghezza variabile (allocate sullo heap o in buffer) si salvano con un **prefisso di lunghezza** (per esempio un `uint16_t len` seguito esattamente dai `len` byte della stringa, senza `'\0'`). Al caricamento leggi `len`, verifichi che non superi un limite massimo sensato, allochi `len + 1` byte, leggi `len` byte e aggiungi `'\0'`.
- All'inizio del file anteponi un'**intestazione binaria** fissa progettata per proteggere il lettore da file errati, obsoleti o danneggiati:

```text
+---------------+------------+-------------+---------------+
| Numero magico | Versione   | Conteggio   | Checksum      |
| (4 byte ASCII)| (uint16_t) | (uint32_t)  | (uint32_t)    |
+---------------+------------+-------------+---------------+
| Record 0 ... Record N-1 (payload variabile)              |
+----------------------------------------------------------+
```

Ogni campo dell'intestazione ha uno scopo preciso:

- **Numero magico** (*magic number*, es. `"STAZ"`): quattro byte fissi che identificano subito il formato; se qualcuno passa al tuo programma un'immagine o un file di testo, il caricamento fallisce immediatamente.
- **Versione del formato** (es. `1`, `2`): i programmi evolvono e aggiungono nuovi campi alle strutture. Salvando la versione nell'intestazione, il lettore può mantenere la **retrocompatibilità**: quando apre un file in versione `1`, legge solo i campi previsti dalla v1 e assegna valori predefiniti ai campi introdotti nella v2; se incontra una versione sconosciuta (es. `9`), rifiuta il file in modo pulito.
- **Conteggio dei record**: indica quanti elementi attendersi nel payload.
- **Somma di controllo** (*checksum*): un valore calcolato su tutti i byte del payload (per esempio con FNV-1a a 32 bit o un accumulatore dedicato). Al caricamento ricalcoli la checksum sui byte letti e la confronti con quella salvata nell'intestazione: se anche un solo bit del file è stato alterato, il controllo fallisce e i dati corrotti vengono scartati.

Infine, una regola di sicurezza fondamentale: **valida sempre ogni conteggio e ogni lunghezza letti dal file prima di chiamare `malloc` o `realloc`**, e in caso di errore a metà caricamento libera sempre tutte le allocazioni già effettuate (costruendo i dati in una struttura temporanea e sostituendo quella di destinazione solo se il caricamento riesce fino in fondo).

> **Se vieni da Python** — In Python moduli come `struct` o `json` offrono serializzazione ad alto livello già pronta. In C i formati binari portabili si progettano esplicitamente codificando campo per campo con `<stdint.h>`, spostamenti bit a bit, numero magico, versione e checksum: è un lavoro più esplicito, ma garantisce controllo assoluto su dimensioni, prestazioni e compatibilità tra piattaforme.

### Esempio guidato

Questo esempio su tre file (`formato_stazioni.h`, `formato_stazioni.c`, `main.c`) salva e ricarica un elenco dinamico di stazioni meteorologiche i cui nomi sono allocati sullo heap. Il formato è interamente **big-endian** con intestazione di `14` byte: numero magico `"STAZ"` (4 byte), versione `uint16_t` (`1` o `2`), conteggio `uint32_t` e checksum `uint32_t` sul payload. La versione `2` aggiunge il campo `int16_t quota_m` (predefinito a `0` quando si carica un file `v1`). Il `main` verifica salvataggio/caricamento in v2, retrocompatibilità con v1 e rilevamento di un file corrotto.

<!-- cod: id=20.5-a tipo=programma gruppo=stazioni file=formato_stazioni.h -->
```c
#ifndef FORMATO_STAZIONI_H
#define FORMATO_STAZIONI_H

#include <stddef.h>
#include <stdint.h>

typedef struct stazione {
    uint16_t id;
    int16_t quota_m;
    char *nome;
} stazione_t;

typedef struct elenco_stazioni {
    stazione_t *dati;
    size_t len;
} elenco_stazioni_t;

void staz_libera(elenco_stazioni_t *e);
bool staz_aggiungi(elenco_stazioni_t *e, uint16_t id, int16_t quota_m, const char *nome);
bool staz_salva(const elenco_stazioni_t *e, const char *percorso, uint16_t versione);
bool staz_carica(elenco_stazioni_t *e, const char *percorso, uint16_t *ver_out);

#endif
```

<!-- cod: id=20.5-c tipo=programma gruppo=stazioni file=formato_stazioni.c -->
```c
#include "formato_stazioni.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static constexpr uint32_t MAX_STAZ = 256;
static constexpr uint16_t MAX_NOME = 64;
static const uint8_t MAGIC[4] = {'S', 'T', 'A', 'Z'};

static void scrivi_u16_be(uint8_t b[2], uint16_t v) {
    b[0] = (uint8_t)((v >> 8) & 0xFFU);
    b[1] = (uint8_t)(v & 0xFFU);
}

static void scrivi_u32_be(uint8_t b[4], uint32_t v) {
    b[0] = (uint8_t)((v >> 24) & 0xFFU);
    b[1] = (uint8_t)((v >> 16) & 0xFFU);
    b[2] = (uint8_t)((v >> 8) & 0xFFU);
    b[3] = (uint8_t)(v & 0xFFU);
}

static uint16_t leggi_u16_be(const uint8_t b[2]) {
    return (uint16_t)(((uint16_t)b[0] << 8) | (uint16_t)b[1]);
}

static uint32_t leggi_u32_be(const uint8_t b[4]) {
    return ((uint32_t)b[0] << 24) | ((uint32_t)b[1] << 16) |
           ((uint32_t)b[2] << 8) | (uint32_t)b[3];
}

static uint32_t aggiorna_csum(uint32_t h, const uint8_t *p, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        h = (h * 33U) ^ p[i];
    }
    return h;
}

void staz_libera(elenco_stazioni_t *e) {
    if (e == nullptr) { return; }
    for (size_t i = 0; i < e->len; ++i) {
        free(e->dati[i].nome);
    }
    free(e->dati);
    e->dati = nullptr;
    e->len = 0;
}

bool staz_aggiungi(elenco_stazioni_t *e, uint16_t id, int16_t quota_m, const char *nome) {
    if (e == nullptr || nome == nullptr || e->len >= MAX_STAZ) { return false; }
    size_t nlen = strlen(nome);
    if (nlen > MAX_NOME) { return false; }
    stazione_t *tmp = realloc(e->dati, (e->len + 1) * sizeof(*tmp));
    if (tmp == nullptr) { return false; }
    e->dati = tmp;
    char *copia = malloc(nlen + 1);
    if (copia == nullptr) { return false; }
    memcpy(copia, nome, nlen + 1);
    e->dati[e->len++] = (stazione_t){.id = id, .quota_m = quota_m, .nome = copia};
    return true;
}

bool staz_salva(const elenco_stazioni_t *e, const char *percorso, uint16_t versione) {
    if (e == nullptr || (versione != 1 && versione != 2)) { return false; }
    FILE *fp = fopen(percorso, "wb");
    if (fp == nullptr) { return false; }
    uint8_t hdr[14] = {};
    if (fwrite(hdr, 1, sizeof(hdr), fp) != sizeof(hdr)) { fclose(fp); return false; }
    uint32_t csum = 5381U;
    for (size_t i = 0; i < e->len; ++i) {
        uint16_t nlen = (uint16_t)strlen(e->dati[i].nome);
        uint8_t rec[6];
        size_t rlen = 0;
        scrivi_u16_be(rec, e->dati[i].id);
        rlen = 2;
        if (versione == 2) {
            scrivi_u16_be(rec + rlen, (uint16_t)e->dati[i].quota_m);
            rlen += 2;
        }
        scrivi_u16_be(rec + rlen, nlen);
        rlen += 2;
        csum = aggiorna_csum(csum, rec, rlen);
        csum = aggiorna_csum(csum, (const uint8_t *)e->dati[i].nome, nlen);
        if (fwrite(rec, 1, rlen, fp) != rlen ||
            (nlen > 0 && fwrite(e->dati[i].nome, 1, nlen, fp) != nlen)) {
            fclose(fp);
            return false;
        }
    }
    memcpy(hdr, MAGIC, 4);
    scrivi_u16_be(hdr + 4, versione);
    scrivi_u32_be(hdr + 6, (uint32_t)e->len);
    scrivi_u32_be(hdr + 10, csum);
    return fseek(fp, 0L, SEEK_SET) == 0 && fwrite(hdr, 1, sizeof(hdr), fp) == sizeof(hdr) &&
           fclose(fp) == 0;
}

bool staz_carica(elenco_stazioni_t *e, const char *percorso, uint16_t *ver_out) {
    FILE *fp = fopen(percorso, "rb");
    if (fp == nullptr) { return false; }
    uint8_t hdr[14];
    if (fread(hdr, 1, sizeof(hdr), fp) != sizeof(hdr) || memcmp(hdr, MAGIC, 4) != 0) {
        fclose(fp);
        return false;
    }
    uint16_t ver = leggi_u16_be(hdr + 4);
    uint32_t n = leggi_u32_be(hdr + 6);
    uint32_t attesa = leggi_u32_be(hdr + 10);
    if ((ver != 1 && ver != 2) || n > MAX_STAZ) { fclose(fp); return false; }
    elenco_stazioni_t tmp = {};
    uint32_t csum = 5381U;
    size_t fissa = (ver == 2) ? 6 : 4;
    for (uint32_t i = 0; i < n; ++i) {
        uint8_t rec[6];
        if (fread(rec, 1, fissa, fp) != fissa) { staz_libera(&tmp); fclose(fp); return false; }
        uint16_t id = leggi_u16_be(rec);
        int16_t quota = (ver == 2) ? (int16_t)leggi_u16_be(rec + 2) : 0;
        uint16_t nlen = leggi_u16_be(rec + ((ver == 2) ? 4 : 2));
        if (nlen > MAX_NOME) { staz_libera(&tmp); fclose(fp); return false; }
        char nome[MAX_NOME + 1];
        if (nlen > 0 && fread(nome, 1, nlen, fp) != nlen) { staz_libera(&tmp); fclose(fp); return false; }
        nome[nlen] = '\0';
        csum = aggiorna_csum(csum, rec, fissa);
        csum = aggiorna_csum(csum, (const uint8_t *)nome, nlen);
        if (!staz_aggiungi(&tmp, id, quota, nome)) { staz_libera(&tmp); fclose(fp); return false; }
    }
    bool extra = (fgetc(fp) != EOF);
    fclose(fp);
    if (extra || csum != attesa) { staz_libera(&tmp); return false; }
    staz_libera(e);
    *e = tmp;
    if (ver_out != nullptr) { *ver_out = ver; }
    return true;
}
```

<!-- cod: id=20.5-d tipo=programma gruppo=stazioni file=main.c -->
```c
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include "formato_stazioni.h"

static void stampa(const elenco_stazioni_t *e) {
    for (size_t i = 0; i < e->len; ++i) {
        printf("  id=%" PRIu16 " quota=%" PRId16 "m nome=%s\n",
               e->dati[i].id, e->dati[i].quota_m, e->dati[i].nome);
    }
}

int main(void) {
    const char *percorso = "stazioni_es.bin";
    elenco_stazioni_t el = {};
    if (!staz_aggiungi(&el, 10, 420, "Passo_Nord") ||
        !staz_aggiungi(&el, 20, 12, "Porto_Est")) {
        staz_libera(&el);
        return EXIT_FAILURE;
    }

    uint16_t ver = 0;
    if (staz_salva(&el, percorso, 2) && staz_carica(&el, percorso, &ver)) {
        printf("Caricato v%" PRIu16 ":\n", ver);
        stampa(&el);
    }
    if (staz_salva(&el, percorso, 1) && staz_carica(&el, percorso, &ver)) {
        printf("Caricato v%" PRIu16 " (retrocompatibile):\n", ver);
        stampa(&el);
    }

    // Corrompe 1 byte del payload e verifica il rifiuto tramite checksum
    FILE *fp = fopen(percorso, "r+b");
    if (fp != nullptr) {
        uint8_t guasto = 0xFF;
        (void)fseek(fp, 14L, SEEK_SET);
        (void)fwrite(&guasto, 1, 1, fp);
        fclose(fp);
    }
    printf("Dopo corruzione: %s\n",
           staz_carica(&el, percorso, &ver) ? "ACCETTATO" : "RIFIUTATO");

    staz_libera(&el);
    remove(percorso);
    return 0;
}
```

```output
Caricato v2:
  id=10 quota=420m nome=Passo_Nord
  id=20 quota=12m nome=Porto_Est
Caricato v1 (retrocompatibile):
  id=10 quota=0m nome=Passo_Nord
  id=20 quota=0m nome=Porto_Est
Dopo corruzione: RIFIUTATO
```

Osserva le scelte progettuali che rendono questo modulo robusto:

- In `staz_salva` scriviamo prima `14` byte di zeri come segnaposto per l'intestazione, poi scriviamo i record aggiornando la checksum `csum`, e alla fine torniamo all'inizio con `fseek(fp, 0L, SEEK_SET)` per scrivere l'intestazione definitiva con `MAGIC`, `versione`, `len` e `csum`.
- In `staz_carica` costruiamo tutto nella variabile locale `tmp` e solo dopo che `extra == false` e `csum == attesa` liberiamo `e` e lo sostituiamo con `tmp`: se il file è corrotto, l'elenco precedente in memoria resta intatto e non si verifica alcuna perdita di memoria.
- Caricando un file salvato in `v1`, `quota_m` riceve il valore predefinito `0` senza errori. Alterando un solo byte nel payload (offset `14`), la checksum non coincide più e il file viene rifiutato.

> **Approfondimento — Trattare ogni file come input non fidato**
> Un file binario aperto da disco va sempre trattato come input potenzialmente alterato o malizioso. Se `staz_carica` chiamasse `malloc(n * sizeof(stazione_t))` senza prima controllare `n <= MAX_STAZ` (e `nlen <= MAX_NOME`), basterebbe alterare quattro byte nell'intestazione per scrivere `n = 4000000000` e provocare un overflow nella moltiplicazione o un esaurimento immediato della memoria. Imporre limiti massimi espliciti prima di ogni allocazione è una pratica difensiva essenziale.

### Esercizio 20.5 — Serializzatore binario portabile e versionato (v1/v2) con numero magico e checksum

**Descrizione**

Realizza una libreria su tre file (`catalogo_bin.h`, `catalogo_bin.c`, `main.c`) per la **serializzazione** e deserializzazione binaria portabile di un catalogo dinamico di articoli (`typedef struct articolo { uint32_t codice; char *titolo; int32_t prezzo_cent; uint16_t giacenza; uint8_t priorita; } articolo_t;`). (1) Il formato binario è interamente in **little-endian** (nessuna `fwrite` diretta di `struct`) e inizia con un'intestazione fissa di `16` byte: byte `0..3` numero magico `"CATB"`, byte `4..5` `uint16_t versione` (`1` oppure `2`), byte `6..7` `uint16_t riservato` (`0`), byte `8..11` `uint32_t num_articoli` (limite difensivo `<= 1024`), byte `12..15` `uint32_t checksum` (FNV-1a a 32 bit calcolata su tutti i byte del payload: valore iniziale `2166136261U`, per ogni byte `h ^= b; h *= 16777619U;`). (2) Ogni articolo nel payload è serializzato come: `codice` (4 byte LE), `prezzo_cent` (4 byte LE come `uint32_t`), `giacenza` (2 byte LE), solo se `versione == 2` il campo `priorita` (1 byte), `len_titolo` (2 byte LE, limite difensivo `<= 128`) seguito dai `len_titolo` byte grezzi del titolo (senza `'\0'`). Al caricamento di un file `v1`, `priorita` assume il valore predefinito `1`. (3) In `catalogo_bin.h` definisci `cat_esito_t` (`CAT_OK`, `CAT_ERR_IO`, `CAT_ERR_MAGIC`, `CAT_ERR_VERSIONE`, `CAT_ERR_CHECKSUM`, `CAT_ERR_TRONCATO`, `CAT_ERR_LIMITE`, `CAT_ERR_MEM`), `catalogo_t` e le funzioni `cat_libera`, `cat_aggiungi`, `cat_salva(const catalogo_t *c, const char *path, uint16_t versione, size_t *byte_scritti)`, `cat_carica(catalogo_t *c, const char *path, uint16_t *ver_letta)` e `cat_esito_nome(cat_esito_t e)`. (4) In `main.c` usa il file `"catalogo_20_5.bin"` (rimuovendolo al termine) e gestisci da `stdin` i comandi `ADD <codice> <prezzo_cent> <giacenza> <priorita> <titolo>`, `SAVE <1|2>`, `LOAD`, `LIST`, `CORROMPI <offset> <hex>` (sovrascrive 1 byte del file con `fopen(..., "r+b")` + `fseek` + `fwrite`) e `TRONCA <nuova_len>` (ricopia solo i primi `nuova_len` byte tramite file temporaneo e `rename`), producendo l'output esatto dell'esempio senza perdite di memoria.

**Concetti da tenere a mente**

- codifica esplicita in little-endian dei campi interi e prefisso di lunghezza per le stringhe allocate sullo heap
- intestazione binaria con numero magico, versione del formato, conteggio e checksum FNV-1a a 32 bit
- retrocompatibilità tra versione 1 (`priorita` predefinita a `1`) e versione 2
- validazione difensiva dei limiti e rilascio pulito della memoria parziale in caso di file corrotto o troncato

**Domande guida**

1. Perché non puoi salvare un `articolo_t` con una singola `fwrite(&a, sizeof(a), 1, fp)` nemmeno se lo ricarichi sulla stessa macchina?
2. In quale ordine conviene controllare numero magico, versione, limiti di `num_articoli`/`len_titolo`, troncamento e checksum durante `cat_carica`?
3. Come gestisce `cat_carica` il campo `priorita` quando legge un file salvato in versione 1 rispetto alla versione 2?
4. Perché in caso di errore a metà del caricamento `cat_carica` deve liberare tutti i titoli già allocati prima di restituire il codice di errore?

**Esempio di esecuzione**

```input
ADD 10 2500 4 3 Tastiera
ADD 20 1200 10 2 Mouse
SAVE 2
LOAD
LIST
SAVE 1
LOAD
LIST
CORROMPI 16 FF
LOAD
CORROMPI 0 00
LOAD
SAVE 2
CORROMPI 4 09
LOAD
SAVE 2
TRONCA 20
LOAD
```

```output
ADD 10: OK
ADD 20: OK
SAVE v2: OK (2 articoli, 55 byte)
LOAD v2: OK (2 articoli)
#0 cod=10 prezzo=2500 giac=4 prio=3 titolo=Tastiera
#1 cod=20 prezzo=1200 giac=10 prio=2 titolo=Mouse
SAVE v1: OK (2 articoli, 53 byte)
LOAD v1: OK (2 articoli)
#0 cod=10 prezzo=2500 giac=4 prio=1 titolo=Tastiera
#1 cod=20 prezzo=1200 giac=10 prio=1 titolo=Mouse
CORROMPI[16]: OK
LOAD ERRORE: CHECKSUM
CORROMPI[0]: OK
LOAD ERRORE: MAGIC
SAVE v2: OK (2 articoli, 55 byte)
CORROMPI[4]: OK
LOAD ERRORE: VERSIONE
SAVE v2: OK (2 articoli, 55 byte)
TRONCA 20: OK
LOAD ERRORE: TRONCATO
```
