## 24.6 Formati binari compatti con campi di bit

Nel capitolo 13 hai incontrato i campi di bit, le unioni etichettate e l'ordine dei byte. Quando un programma deve mantenere in RAM milioni di record compatti — come nodi di un interprete, voci di una tabella di pagina o descrittori di pacchetti di telemetria — risparmiare anche pochi byte per oggetto riduce drasticamente il consumo di memoria. Al tempo stesso, molti di questi oggetti vanno poi salvati su file o trasmessi in rete secondo un formato binario preciso.

È qui che si commette uno degli errori più insidiosi del C: confondere la **rappresentazione in memoria** (ottimizzata per la macchina locale) con il **formato binario su cavo o file** (che deve essere identico su ogni architettura).

### Campi di bit avanzati e verifica con `static_assert`

In una `struct`, un campo di bit dichiara il numero esatto di bit occupati all'interno di un'unità di memorizzazione. Per scrivere codice portabile e privo di ambiguità rispetta quattro regole precise:

- **Specifica sempre il segno**: dichiara i campi di bit come `unsigned int`, `signed int` oppure `bool`. Non usare mai `int` semplice, perché lo standard lascia **dipendente dall'implementazione** se un campo di bit `int` sia con segno o senza segno.
- **Campi anonimi di riserva**: scrivere `unsigned int : 3;` inserisce 3 bit di padding non indirizzabili, utili per allineare il campo successivo o riservare bit per estensioni future.
- **Campi a larghezza zero (`unsigned int : 0;`)**: forzano il campo di bit successivo a iniziare in una nuova unità di memorizzazione, evitando che un campo si sovrapponga a un confine che desideri tenere separato.
- **Verifica a tempo di compilazione**: controlla sempre la compattezza attesa con `static_assert`, ad esempio `static_assert(sizeof(data_ora_bf_t) == sizeof(unsigned int));`, per accorgerti subito se un campo aggiunto sfora la parola di 32 bit.

Abbinando un'intestazione a campi di bit con un'**unione etichettata** (il cui tag risiede proprio in uno dei campi di bit dell'intestazione), puoi rappresentare in pochissimi byte pacchetti binari con payload di tipo variabile: la `struct` occupa soltanto lo spazio dell'intestazione più il ramo più grande della `union`, invece della somma di tutti i possibili payload.

### Perché non si serializzano mai i byte grezzi di una struct a campi di bit

Una volta compattata un'intestazione in 32 bit con `sizeof(intestazione_bf_t) == 4`, la tentazione di copiarla direttamente in un buffer di rete con `memcpy` o di rileggerla come `uint32_t` tramite una `union` è fortissima:

<!-- cod: id=24.6-b tipo=frammento -->
```c
// ERRORE DI PORTABILITÀ: NON SCRIVERE COSÌ!
// L'ordine dei bit, il padding tra unità e l'ordine dei byte dipendono dall'implementazione.
uint8_t buffer[4];
memcpy(buffer, &hdr, sizeof(buffer)); // NON portabile su file o rete!
```

Questo codice è gravemente non portabile per tre ragioni sancite dallo standard C23:

1. **Ordine dei bit dipendente dall'implementazione**: il compilatore può impacchettare i campi di bit dal bit meno significativo verso il più significativo (comune su x86/ARM little-endian) oppure dal più significativo verso il meno significativo.
2. **Padding e confini di unità dipendenti dall'implementazione**: lo standard non garantisce in che modo un campo che supera l'unità corrente venga spezzato o spostato all'unità successiva.
3. **Ordine dei byte (endianness) e *strict aliasing***: i byte di un `unsigned int` in memoria possono essere disposti in little-endian o big-endian, e aggirare il sistema dei tipi con puntatori incompatibili viola le regole di *strict aliasing* (capitolo 22).

### Separare il modello in memoria dal codec portabile

La soluzione pulita separa nettamente due responsabilità:

- **Modello in memoria**: una `struct` a campi di bit (eventualmente affiancata da una `union` etichettata) per lavorare in modo espressivo e compatto dentro il programma (`hdr.versione`, `hdr.tipo`, `hdr.seq`).
- **Codec di serializzazione e deserializzazione**: due funzioni esplicite che convertono la `struct` verso e da un buffer `uint8_t[]` in un ordine dei byte fissato dal protocollo (tipicamente **big-endian**), usando esclusivamente spostamenti e maschere di bit su tipi senza segno (`uint32_t`, `uint16_t`, `uint8_t`).

Nei protocolli reali, al buffer serializzato si aggiunge un controllo di integrità come un **CRC-8** (un codice ridondante ciclico su 8 bit calcolato con spostamenti e XOR rispetto a un polinomio generatore fissato, ad esempio `0x07`), che in fase di decodifica va sempre verificato **prima** di interpretare i campi estratti.

Secondo lo standard C23, la semantica dei campi di bit senza segno, delle unioni etichettate e degli spostamenti su tipi senza segno è completamente definita; l'ordine di impacchettamento dei bit, il padding tra unità e il segno di `int` semplice nei campi di bit sono invece **dipendenti dall'implementazione**.

### Esempio guidato

Il programma seguente rappresenta una data e ora compatta in 32 bit (`data_ora_bf_t`: anno relativo al 2000 su 7 bit, mese su 4, giorno su 5, ora su 5, minuto su 6, doppio-secondo su 5, totale 32 bit), verifica con `static_assert` che la struct occupi una sola parola `unsigned int`, e implementa un codec portabile big-endian in un buffer `uint8_t[4]` verificando che codifica e decodifica restituiscano esattamente i campi originali.

<!-- cod: id=24.6-a tipo=programma -->
```c
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct data_ora_bf {
    unsigned int anno_off : 7;  // 0..127 -> 2000..2127
    unsigned int mese : 4;      // 1..12
    unsigned int giorno : 5;    // 1..31
    unsigned int ora : 5;       // 0..23
    unsigned int minuto : 6;    // 0..59
    unsigned int sec_div2 : 5;  // 0..29 -> secondi pari 0..58
} data_ora_bf_t;

static_assert(sizeof(data_ora_bf_t) == sizeof(unsigned int));

static void codifica_be(const data_ora_bf_t *d, uint8_t out[4]) {
    uint32_t parola = ((uint32_t)d->anno_off << 25) |
                      ((uint32_t)d->mese << 21) |
                      ((uint32_t)d->giorno << 16) |
                      ((uint32_t)d->ora << 11) |
                      ((uint32_t)d->minuto << 5) |
                      (uint32_t)d->sec_div2;
    out[0] = (uint8_t)(parola >> 24);
    out[1] = (uint8_t)(parola >> 16);
    out[2] = (uint8_t)(parola >> 8);
    out[3] = (uint8_t)parola;
}

static data_ora_bf_t decodifica_be(const uint8_t in[4]) {
    uint32_t parola = ((uint32_t)in[0] << 24) |
                      ((uint32_t)in[1] << 16) |
                      ((uint32_t)in[2] << 8) |
                      (uint32_t)in[3];
    data_ora_bf_t d = {
        .anno_off = (parola >> 25) & 0x7FU,
        .mese = (parola >> 21) & 0x0FU,
        .giorno = (parola >> 16) & 0x1FU,
        .ora = (parola >> 11) & 0x1FU,
        .minuto = (parola >> 5) & 0x3FU,
        .sec_div2 = parola & 0x1FU
    };
    return d;
}

int main(void) {
    data_ora_bf_t orig = {
        .anno_off = 26, .mese = 11, .giorno = 24,
        .ora = 17, .minuto = 35, .sec_div2 = 15
    };
    uint8_t filo[4] = {};
    codifica_be(&orig, filo);

    printf("Buffer big-endian: %02" PRIx8 " %02" PRIx8 " %02" PRIx8 " %02" PRIx8 "\n",
           filo[0], filo[1], filo[2], filo[3]);

    data_ora_bf_t dec = decodifica_be(filo);
    printf("Decodificato: %04u-%02u-%02u %02u:%02u:%02u\n",
           2000U + dec.anno_off, dec.mese, dec.giorno,
           dec.ora, dec.minuto, dec.sec_div2 * 2U);

    bool ok = (dec.anno_off == orig.anno_off) && (dec.mese == orig.mese) &&
              (dec.giorno == orig.giorno) && (dec.ora == orig.ora) &&
              (dec.minuto == orig.minuto) && (dec.sec_div2 == orig.sec_div2);
    printf("Consistenza round-trip: %s\n", ok ? "OK" : "ERRORE");
    return 0;
}
```

```output
Buffer big-endian: 35 78 8c 6f
Decodificato: 2026-11-24 17:35:30
Consistenza round-trip: OK
```

Osserva come `codifica_be` e `decodifica_be` non dipendono in alcun modo dal layout fisico dei campi di bit nella memoria della CPU: impacchettano e disimpacchettano esplicitamente la parola a 32 bit con spostamenti e maschere senza segno, producendo sempre gli stessi quattro byte `35 78 8c 6f` su qualsiasi architettura.

> **Approfondimento — Dove i campi di bit brillano davvero**
> I campi di bit danno il massimo nelle strutture puramente interne al processo: nodi di interpreti e compilatori, stati di simulatori, tabelle di pagina e cache dove milioni di oggetti piccoli convivono in RAM. Ogni volta che i dati devono uscire dalla memoria del processo (su disco o in rete), affiancare un codec esplicito a spostamenti e maschere ti permette di mantenere entrambi i vantaggi: compattezza in memoria e portabilità assoluta del formato binario.

### Esercizio 24.6 — Codec binario portabile per frame di telemetria con intestazione a campi di bit, unione etichettata e CRC-8

**Descrizione**

Realizza su tre file (`frame_bin.h`, `frame_bin.c`, `main.c`) un codec binario compatto che separa rigorosamente la rappresentazione in memoria (campi di bit + unione etichettata) dalla serializzazione portabile big-endian su buffer di byte con verifica CRC-8. (1) In `frame_bin.h` (protetto da `FRAME_BIN_H`) definisci `tipo_frame_t` (`FRM_PING = 0`, `FRM_SENSORE = 1`, `FRM_COMANDO = 2`, `FRM_ERRORE = 3`), `esito_frame_t` (`FRM_OK`, `FRM_ERR_LEN`, `FRM_ERR_CRC`, `FRM_ERR_VER`, `FRM_ERR_PAYLOAD`), la struct a campi di bit `intestazione_bf_t` con esattamente 32 bit (`unsigned int versione : 2; tipo : 2; priorita : 2; cifrato : 1; ack : 1; src : 6; dst : 6; len : 4; seq : 8;`, verificata con `static_assert(sizeof(intestazione_bf_t) == sizeof(unsigned int))`), l'unione `payload_frame_t` (`sensore { int16_t temp_d; uint16_t umid_d; }`, `comando { uint8_t op; uint8_t arg; }`, `errore { uint16_t cod; }`) e `frame_t { intestazione_bf_t hdr; payload_frame_t dati; }`. Dichiara `uint8_t frame_crc8(const uint8_t *buf, size_t n);` (polinomio `0x07`, stato iniziale `0x00`), `size_t frame_codifica(const frame_t *f, uint8_t *out, size_t cap);` e `esito_frame_t frame_decodifica(const uint8_t *buf, size_t n, frame_t *out);`. (2) In `frame_bin.c` serializza i 32 bit dell'intestazione in big-endian (`bit 31..30 = versione`, `29..28 = tipo`, `27..26 = priorita`, `25 = cifrato`, `24 = ack`, `23..18 = src`, `17..12 = dst`, `11..8 = len`, `7..0 = seq`), seguiti dal payload big-endian (`PING`: 0 byte, `SENSORE`: 4 byte, `COMANDO`: 2 byte, `ERRORE`: 2 byte) e dal byte finale `CRC-8` calcolato su tutti i byte precedenti. `frame_decodifica` rifiuta lunghezze `< 5` o `> 9` (`FRM_ERR_LEN`), CRC errato (`FRM_ERR_CRC`), `versione != 1` (`FRM_ERR_VER`), lunghezza dichiarata incoerente col tipo (`FRM_ERR_PAYLOAD`) o buffer di dimensione diversa da `5 + hdr.len` (`FRM_ERR_LEN`), ricostruendo `temp_d` in complemento a due senza UB. (3) In `main.c` gestisci da `stdin` i comandi `ENC_PING`, `ENC_SENS`, `ENC_CMD`, `ENC_ERR` (con `versione = 1`) e `DEC <n> <hex0> ... <hex{n-1}>`, riproducendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- rappresentazione in memoria compatta tramite campi di bit `unsigned int` e unione etichettata
- verifica a tempo di compilazione della compattezza della struct con `static_assert`
- serializzazione e deserializzazione big-endian portabile con spostamenti e maschere senza copiare byte grezzi della struct
- calcolo e verifica del codice di integrità CRC-8 e controllo di versione e lunghezza del payload

**Domande guida**

1. Perché non puoi serializzare `frame_t` con una semplice `memcpy(out, &f->hdr, 4)` anche se `sizeof(intestazione_bf_t)` vale 4 sulla tua macchina?
2. Come ricostruisci in modo portabile il valore con segno `int16_t temp_d` dai due byte big-endian del payload senza incorrere in comportamento indefinito?
3. Perché nella decodifica conviene verificare il byte CRC-8 prima di fidarsi dei campi `versione`, `tipo` e `len` estratti dall'intestazione?
4. Quale vantaggio offre combinare `intestazione_bf_t` con l'unione etichettata `payload_frame_t` rispetto a una struct che contenga separatamente tutti i possibili campi di tutti i tipi di frame?

**Esempio di esecuzione**

```input
ENC_PING 2 0 1 5 12 7
ENC_SENS 3 1 0 10 20 42 -125 645
ENC_CMD 1 0 1 1 2 9 16 250
DEC 5 49 14 c0 07 cc
DEC 9 5e 29 44 2a ff 83 02 85 39
DEC 5 49 14 c0 07 00
DEC 5 89 14 c0 07 66
```

```output
ENC(5): 49 14 c0 07 cc
ENC(9): 5e 29 44 2a ff 83 02 85 39
ENC(7): 65 04 22 09 10 fa 28
DEC OK: v=1 PING prio=2 cif=0 ack=1 5->12 seq=7
DEC OK: v=1 SENS prio=3 cif=1 ack=0 10->20 seq=42 temp=-125 umid=645
DEC ERR: CRC
DEC ERR: VER
```
