## 12.1 Raggruppare dati con `struct`

Immagina di dover scrivere un programma che gestisce le rilevazioni di una stazione meteorologica: per ogni misura devi conservare il codice della stazione (una stringa), la quota in metri (un `int`), la temperatura rilevata (un `double`) e un'indicazione che dice se il sensore è attivo (un `bool`). Con gli strumenti visti finora avresti due strade, entrambe scomode: dichiarare quattro variabili separate per ogni rilevazione (`codice_1`, `quota_1`, `temp_1`, `attiva_1`, poi `codice_2`, `quota_2`, e così via), oppure costruire quattro array paralleli di uguale lunghezza. Nel primo caso il codice diventa presto illeggibile e ogni funzione che elabora una rilevazione dovrebbe ricevere quattro parametri separati; nel secondo caso basta scambiare due elementi in tre array dimenticando il quarto per disallineare in modo irreparabile i dati.

Quando più valori di tipo anche diverso descrivono insieme una stessa entità logica, il C offre un tipo aggregato apposito: la **struttura** (*struct*), cioè un tipo aggregato definito con `struct` che raggruppa più campi, anche di tipi diversi, sotto un unico nome. Ogni singola variabile dichiarata all'interno di una `struct` (o di una `union`, che vedremo nel capitolo 13) si chiama **campo** (*field*).

Per creare un tipo struttura si scrive la parola chiave `struct`, seguita da un'etichetta (*tag*) che ne costituisce il nome, dalle parentesi graffe contenenti le dichiarazioni dei campi e da un punto e virgola finale obbligatorio:

<!-- cod: id=12.1-b tipo=frammento -->
```c
struct rilevazione_meteo {
    char codice[16];
    int quota;
    double temperatura;
    bool attiva;
};
```

Questa definizione non crea ancora alcuna variabile in memoria: descrive al compilatore il modello del nuovo tipo `struct rilevazione_meteo`, elencando nome e tipo di ciascun campo. Dimenticare il punto e virgola dopo la parentesi graffa di chiusura è uno degli errori di sintassi più frequenti e genera segnalazioni fuorvianti sulle righe successive.

In memoria i campi di una struttura sono disposti esattamente nell'ordine in cui compaiono nella definizione:

```text
struct rilevazione_meteo
+------------------+---------+---------------+--------+
| codice[0..15]    | quota   | temperatura   | attiva |
| (16 byte)        | (4 byte)| (8 byte)      | (1 byte|
+------------------+---------+---------------+--------+
^ indirizzo base della struttura
```

Una volta definito il tipo, puoi dichiarare una o più variabili di tipo `struct rilevazione_meteo` esattamente come fai con i tipi fondamentali. Per leggere o modificare un singolo campo si usa l'**operatore punto** (`.`): dato il nome della variabile struttura seguito da `.` e dal nome del campo, ottieni il campo stesso come se fosse una normale variabile del suo tipo.

<!-- cod: id=12.1-c tipo=frammento -->
```c
struct rilevazione_meteo r;
strcpy(r.codice, "STZ-04");
r.quota = 820;
r.temperatura = 14.5;
r.attiva = true;
```

Osserva che per `r.codice`, che è un array di `char`, valgono le regole viste nel capitolo 9: non puoi assegnare una stringa con `=` dopo la dichiarazione, ma usi `strcpy` (oppure `snprintf`). Per gli altri campi usi il normale assegnamento `=`.

Come per gli array, è sempre buona norma inizializzare la struttura nel momento in cui la dichiari. Il C offre tre forme di inizializzazione:

1. **Inizializzazione per posizione**: i valori tra parentesi graffe vengono associati ai campi nell'ordine esatto della definizione:
   `struct rilevazione_meteo r1 = {"STZ-01", 1250, 12.4, true};`
2. **Inizializzatore designato** (già visto sugli array nel capitolo 8): davanti a ciascun valore indichi `.nome_campo = valore`, in qualunque ordine:
   `struct rilevazione_meteo r2 = {.temperatura = 12.4, .codice = "STZ-01", .quota = 1250, .attiva = true};`
3. **Inizializzazione parziale o vuota**: se ometti alcuni campi in un inizializzatore, il compilatore azzera automaticamente tutti i campi mancanti (`0` per gli interi, `0.0` per i numeri in virgola mobile, `false` per i booleani, `'\0'` per i caratteri, `nullptr` per i puntatori). In C23 puoi scrivere l'inizializzatore vuoto `{}` per azzerare l'intera struttura.

> **C23** — L'inizializzatore vuoto `{}` (per esempio `struct rilevazione_meteo r = {};`) è stato standardizzato in C23 e azzera tutti i campi della struttura, esattamente come `{0}` negli standard precedenti. Se compili con un compilatore più vecchio in modalità C17 o C11, scrivi `{0}` al posto di `{}`.

Riassumiamo le regole fondamentali della definizione e dell'inizializzazione:

- `struct nome_tag { ... };` definisce un nuovo tipo struttura i cui campi sono memorizzati nell'ordine dichiarato.
- L'operatore punto (`s.campo`) accede in lettura o in scrittura al campo della variabile struttura `s`.
- Una struttura può essere inizializzata per posizione (`{v1, v2}`) o con inizializzatori designati (`{.campo1 = v1, .campo2 = v2}`); i campi omessi vengono azzerati automaticamente e in C23 `{}` azzera l'intera struttura.
- Secondo lo standard C23, la sequenza dei campi in memoria, l'operatore punto, gli inizializzatori designati, l'azzeramento dei campi omessi e `{}` hanno comportamento completamente definito. Al contrario, leggere un campo di una struttura automatica (dichiarata dentro una funzione) senza averlo prima inizializzato o assegnato provoca **comportamento indefinito**.

Infine, puoi misurare quanti byte occupa in memoria una struttura applicando `sizeof` al nome del tipo (`sizeof(struct rilevazione_meteo)`) oppure a una variabile (`sizeof(r)`). Potresti aspettarti che il risultato coincida sempre con la somma delle dimensioni dei singoli campi, ma spesso è leggermente maggiore: `sizeof(struct rilevazione_meteo)` è sempre maggiore o uguale alla somma delle dimensioni dei suoi campi. Questo accade perché il compilatore può inserire byte inutilizzati tra un campo e l'altro o in coda alla struttura per rispettare i vincoli di disposizione in memoria del processore (lo vedremo nel capitolo 13). Per questo motivo non devi mai stimare a mano la dimensione di una `struct` sommando le dimensioni dei campi: usa sempre `sizeof`.

> **Se vieni da Python** — In Python una classe raggruppa dati e operazioni associate, e puoi persino aggiungere nuovi campi a un oggetto durante l'esecuzione. In C una `struct` contiene soltanto i campi dati fissati nella sua definizione a tempo di compilazione, mentre le funzioni che lavorano su quei dati sono definite all'esterno della struttura.

### Esempio guidato

Il programma seguente definisce `struct rilevazione_meteo`, inizializza la prima variabile con inizializzatori designati e la seconda con l'inizializzatore vuoto `{}` (C23), ne aggiorna poi i campi con l'operatore punto, stampa entrambe le rilevazioni e confronta `sizeof(struct rilevazione_meteo)` con la somma delle dimensioni dei singoli campi.

<!-- cod: id=12.1-a tipo=programma -->
```c
#include <stdio.h>
#include <string.h>

struct rilevazione_meteo {
    char codice[16];
    int quota;
    double temperatura;
    bool attiva;
};

int main(void) {
    struct rilevazione_meteo monte = {
        .codice = "ALPI-01",
        .quota = 1850,
        .temperatura = 6.5,
        .attiva = true
    };
    struct rilevazione_meteo valle = {};

    strcpy(valle.codice, "VAL-02");
    valle.quota = 240;
    valle.temperatura = 19.2;
    valle.attiva = false;

    printf("%s: quota %d m, %.1f C, attiva=%d\n",
           monte.codice, monte.quota, monte.temperatura, monte.attiva);
    printf("%s: quota %d m, %.1f C, attiva=%d\n",
           valle.codice, valle.quota, valle.temperatura, valle.attiva);

    size_t somma_campi = sizeof(monte.codice) + sizeof(monte.quota)
                       + sizeof(monte.temperatura) + sizeof(monte.attiva);
    printf("Somma dimensioni campi: %zu byte\n", somma_campi);
    printf("sizeof(struct rilevazione_meteo): %zu byte\n",
           sizeof(struct rilevazione_meteo));
    return 0;
}
```

```output
ALPI-01: quota 1850 m, 6.5 C, attiva=1
VAL-02: quota 240 m, 19.2 C, attiva=0
Somma dimensioni campi: 29 byte
sizeof(struct rilevazione_meteo): 40 byte
```

Esaminiamo i passaggi chiave:

- La definizione di `struct rilevazione_meteo` è posta fuori da `main` (con il punto e virgola finale) così che sia visibile in tutto il file sorgente.
- `monte` viene inizializzata con inizializzatori designati: ogni campo è esplicitamente nominato e l'array `codice` riceve direttamente la stringa letterale `"ALPI-01"` (incluso il terminatore nullo `'\0'` e i byte residui azzerati).
- `valle` viene inizializzata con `{}` (C23), azzerando tutti i suoi campi; subito dopo l'operatore punto permette di popolare ciascun campo in modo sicuro (`strcpy` per la stringa, `=` per i campi scalari).
- Le ultime righe calcolano `somma_campi` (`16 + 4 + 8 + 1 = 29` byte su un'architettura tipica a 64 bit) e la confrontano con `sizeof(struct rilevazione_meteo)` (`40` byte): la differenza è dovuta ai byte inutilizzati aggiunti dal compilatore tra i campi o in coda, un dettaglio dipendente dall'implementazione che approfondiremo nel capitolo 13.

> **Approfondimento — Perché preferire gli inizializzatori designati**
> Gli inizializzatori designati (`.campo = valore`) offrono due vantaggi decisivi rispetto all'inizializzazione posizionale. Primo, chi legge il codice capisce immediatamente che cosa rappresenta ogni numero senza dover tornare alla definizione della `struct`. Secondo, il codice resta corretto anche se in futuro riordini i campi o ne aggiungi di nuovi nella definizione della struttura: un'inizializzazione posizionale associerebbe i valori ai campi sbagliati o smetterebbe di compilare, mentre gli inizializzatori designati continuano a legare ogni valore al campo corretto e azzerano automaticamente eventuali nuovi campi aggiunti.

### Esercizio 12.1 — Gestione di un lotto di magazzino con struct e inizializzatori designati

**Descrizione**

Scrivi un programma C che definisca `struct lotto_merce` con quattro campi: `char codice[16];`, `int quantita;`, `double prezzo_unitario;` e `bool deperibile;`. In `main` dichiara un lotto costante di confronto `const struct lotto_merce riferimento = {.codice = "BASE-00", .quantita = 10, .prezzo_unitario = 5.00, .deperibile = false};` e un lotto `struct lotto_merce attivo = {};` (inizializzatore vuoto C23). Leggi dalla prima riga di `stdin` i dati iniziali di `attivo` (`codice`, `quantita >= 0`, `prezzo_unitario >= 0.0` e un intero `dep` pari a `0` o `1` da assegnare a `attivo.deperibile`, validati con `sscanf(riga, "%15s %d %lf %d %c", attivo.codice, &attivo.quantita, &attivo.prezzo_unitario, &dep, &extra) == 4`). Leggi poi fino a fine input una sequenza di movimenti (uno per riga): `CARICO <q>` (`q > 0`) somma `q` ad `attivo.quantita`; `SCARICO <q>` (`q > 0`) se `q > attivo.quantita` non modifica la quantità, incrementa `rifiutati` e stampa `Scarico rifiutato: disponibili <quantita>`, altrimenti sottrae `q` da `attivo.quantita`. In caso di input o comando non valido stampa su `stderr` e restituisci `EXIT_FAILURE`. Al termine stampa i campi di `attivo`, il numero di scarichi rifiutati, il valore totale (`quantita * prezzo_unitario`) e la differenza di valore rispetto a `riferimento`, esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- definizione di un tipo struttura con `struct` e dichiarazione dei campi
- inizializzatore designato `{.campo = valore}` e inizializzatore vuoto `{}` (C23)
- accesso in lettura e scrittura ai campi tramite l'operatore punto (`.`)
- coesione di campi di tipi diversi (`char[]`, `int`, `double`, `bool`) in un unico oggetto

**Domande guida**

1. Quali valori assumono inizialmente tutti i campi di `attivo` quando lo dichiari con l'inizializzatore vuoto `{}` in C23?
2. Perché per leggere `codice` con `sscanf` non serve l'operatore `&` davanti ad `attivo.codice` mentre è necessario davanti ad `attivo.quantita` e `attivo.prezzo_unitario`?
3. Come accedi ai singoli campi di `attivo` e di `riferimento` per calcolare la differenza tra i due valori economici?
4. Quale vantaggio offre raggruppare i quattro dati in `struct lotto_merce` rispetto a gestire quattro variabili separate per ciascun lotto?

**Esempio di esecuzione**

```input
LATTE-01 20 1.50 1
CARICO 10
SCARICO 35
SCARICO 12
```

```output
Scarico rifiutato: disponibili 30
Lotto: LATTE-01 (deperibile: si)
Quantita finale: 18, prezzo: 1.50 euro
Scarichi rifiutati: 1
Valore attivo: 27.00 euro (diff da BASE-00: -23.00 euro)
```
