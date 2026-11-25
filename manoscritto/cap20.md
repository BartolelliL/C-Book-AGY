# Capitolo 20 — File e dati binari

> **In questo capitolo imparerai a:**
> - Aprire, leggere, scrivere e chiudere file di testo con `fopen`, `fgets`, `fprintf` e `fclose` controllando ogni errore
> - Distinguere la fine del file dagli errori di lettura con `feof` e `ferror`
> - Leggere e scrivere dati binari con `fread` e `fwrite` e posizionarsi nel file con `fseek` e `ftell`
> - Progettare formati binari portabili e versionati per salvare e ricaricare strutture

> **Ti servono:** stream e buffer (cap. 5), stringhe (cap. 9), memoria dinamica (cap. 11), strutture ed enumerazioni (cap. 12), tipi a larghezza fissa, ordine dei byte, allineamento e padding (cap. 13), programmi su più file e tipi opachi (cap. 19).

Tutti i programmi che hai scritto finora hanno un limite evidente: appena `main` termina, ogni dato accumulato nello stack o sullo heap scompare. Nel capitolo 19 hai imparato a organizzare una libreria su più file come tipo opaco, pronta per applicazioni complesse; tuttavia una tabella hash, un catalogo o un archivio di misure che si svuota a ogni chiusura del programma serve a poco nel mondo reale. Per conservare i risultati tra un'esecuzione e l'altra, scambiare informazioni con altri programmi o elaborare insiemi di dati che superano la memoria disponibile, occorre leggere e scrivere file su disco.

Dal capitolo 5 conosci già il concetto di stream grazie a `stdin`, `stdout` e `stderr`. La libreria standard del C (`<stdio.h>`) estende esattamente la stessa astrazione ai file sul disco attraverso il tipo opaco `FILE`: aprire un file significa ottenere un puntatore `FILE *` su cui operare con funzioni di lettura, scrittura e posizionamento. Questo approccio unificato ha però esigenze di disciplina rigorose: ogni operazione di ingresso e uscita può fallire per motivi esterni al tuo codice (file inesistente, permessi insufficienti, disco pieno, file troncato o corrotto) e ogni risorsa aperta va sempre chiusa controllando l'esito finale.

In questo capitolo imparerai prima a gestire i file di testo in modo sicuro, evitando le trappole più diffuse come `while (!feof(fp))` o la perdita di errori di chiusura. Passerai poi ai file binari con `fread`, `fwrite`, `fseek` e `ftell`, fino all'accesso casuale su record di dimensione fissa e alla serializzazione binaria portabile e versionata, capace di resistere alle differenze tra architetture e di rilevare file danneggiati.

## 20.1 Aprire, scrivere e chiudere file di testo

Quando scrivi un programma che produce un rapporto, un registro di eventi o un file di configurazione, non puoi più limitarti a stampare sul terminale: hai bisogno di aprire un file sul filesystem, scrivervi caratteri leggibili e assicurarti che tutti i byte raggiungano effettivamente il disco prima di proseguire.

Nel capitolo 5 hai incontrato lo **stream** come astrazione di un canale sequenziale di caratteri o byte e hai usato i tre stream predefiniti `stdin`, `stdout` e `stderr`. Nella libreria standard (`<stdio.h>`) ogni stream è rappresentato da un oggetto di tipo `FILE`, il prototipo storico del **tipo opaco** che hai studiato nel capitolo 19. Il tuo codice non conosce i campi interni di `FILE` (come il puntatore al buffer interno, la posizione corrente o gli indicatori di stato) e non deve mai copiarlo per valore: lavori sempre e soltanto attraverso un puntatore `FILE *`. Un **file di testo** (*text file*) è un file aperto in modalità testo contenente righe di caratteri leggibili, con eventuale traduzione automatica dei fine riga da parte della libreria standard (per esempio tra `'\n'` usato dal programma C e la sequenza `"\r\n"` su Windows).

Per associare un `FILE *` a un file sul disco si chiama `fopen`:

```text
FILE *fopen(const char *restrict filename, const char *restrict mode);
```

Il primo argomento è il percorso del file; il secondo è una stringa che indica la modalità di apertura. Le modalità di testo standard sono:

| Modalità | Significato | Se il file esiste già | Se il file non esiste |
|---|---|---|---|
| `"r"` | Solo lettura | Apre dall'inizio | Fallisce (`nullptr`) |
| `"w"` | Solo scrittura | Tronca a zero byte | Crea un nuovo file |
| `"a"` | Scrittura in coda (append) | Scrive sempre in fondo | Crea un nuovo file |
| `"r+"` | Lettura e scrittura | Apre dall'inizio senza troncare | Fallisce (`nullptr`) |
| `"w+"` | Lettura e scrittura | Tronca a zero byte | Crea un nuovo file |
| `"a+"` | Lettura e scrittura in coda | Legge dall'inizio, scrive in fondo | Crea un nuovo file |
| `"wx"` / `"w+x"` | Scrittura esclusiva (C11/C23) | Fallisce (`nullptr`), evita sovrascritture | Crea un nuovo file |

Se l'apertura fallisce (per esempio perché il file non esiste in modalità `"r"`, manca il permesso di scrittura o il file esiste già con `"wx"`), `fopen` restituisce `nullptr`. Controllare subito `if (fp == nullptr)` è obbligatorio prima di qualunque operazione sullo stream.

Una volta aperto il file in scrittura, hai tre funzioni principali di `<stdio.h>`:

- `fprintf(fp, formato, ...)`: funziona esattamente come `printf`, ma scrive sullo stream `fp`. Restituisce il numero di caratteri scritti oppure un valore negativo in caso di errore.
- `fputs(s, fp)`: scrive la stringa `s` senza il terminatore nullo e **senza aggiungere `'\n'`** (a differenza di `puts`, che scrive su `stdout` aggiungendo sempre un ritorno a capo). Restituisce un valore non negativo oppure `EOF` in caso di errore.
- `fputc(c, fp)`: scrive il singolo carattere `(unsigned char)c` su `fp` e lo restituisce come `int`, oppure restituisce `EOF` in caso di errore.

Le scritture su un `FILE *` non finiscono immediatamente sul disco: per ragioni di efficienza la libreria standard le accumula nel **buffer** interno dello stream e le trasferisce al sistema operativo a blocchi. Quando hai bisogno di forzare subito lo svuotamento del buffer di uno stream di uscita (per esempio prima di controllare che non ci siano errori o prima di una fase critica), chiami `fflush(fp)`, che restituisce `0` in caso di successo oppure `EOF` in caso di errore. Passare `nullptr` a `fflush` svuota tutti gli stream di uscita aperti.

Al termine dell'uso devi chiudere lo stream con `fclose(fp)`. Questa funzione svuota eventuali dati ancora nel buffer, rilascia il descrittore del sistema operativo e restituisce `0` in caso di successo oppure `EOF` in caso di errore. Controllare il valore restituito da `fclose` quando hai scritto su un file è essenziale quanto controllare `fopen`.

Infine, `<stdio.h>` fornisce due funzioni portabili per operare sui nomi dei file sul disco:

- `rename(vecchio, nuovo)`: rinomina il file `vecchio` in `nuovo` e restituisce `0` in caso di successo o un valore diverso da zero in caso di errore (se `nuovo` esiste già, il comportamento è dipendente dall'implementazione: su Linux e macOS lo sostituisce, su Windows può fallire se non viene prima rimosso).
- `remove(percorso)`: elimina il file `percorso` dal filesystem e restituisce `0` in caso di successo o diverso da zero in caso di errore.

Combinare `rename` e `remove` permette uno schema molto solido di aggiornamento sicuro: invece di sovrascrivere direttamente un file importante con `"w"` (che lo troncherebbe subito a zero byte, lasciandolo vuoto o troncato se il programma fallisse a metà scrittura), scrivi prima l'intero contenuto su un file temporaneo, verifichi `fflush` e `fclose(fp) == 0`, e solo se tutto è riuscito promuovi il file temporaneo al nome definitivo con `rename`. Se qualcosa fallisce prima della rinomina, elimini il file temporaneo con `remove` e l'eventuale versione precedente resta intatta.

Riassumiamo le regole chiave dello standard C23:

- `FILE` è un oggetto opaco gestito solo tramite `FILE *`: non copiarlo mai per valore.
- Controlla sempre `fp != nullptr` dopo `fopen`, l'esito di `fprintf`/`fputs`/`fputc`, `fflush(fp) == 0` quando svuoti esplicitamente il buffer e `fclose(fp) == 0` alla chiusura in scrittura.
- Copiare un oggetto `FILE` per valore, invocare `fflush` su uno stream di ingresso oppure riutilizzare un `FILE *` dopo `fclose` provoca **comportamento indefinito** (anche se le modalità di `fopen`, incluse `"wx"`, e le funzioni `fprintf`, `fputs`, `fputc`, `fflush`, `fclose`, `rename` e `remove` sono completamente definite dallo standard C23).

> **Se vieni da Python** — In Python il costrutto `with open(...) as f:` chiude automaticamente il file all'uscita dal blocco e lancia un'eccezione in caso di errore. In C non esistono gestori di contesto né eccezioni: devi controllare manualmente `fopen != nullptr`, verificare l'esito di scrittura e chiusura con `fclose(fp) == 0` e assicurarti che ogni percorso di uscita chiuda tutti gli stream aperti.

### Esempio guidato

Il programma seguente genera un breve rapporto meteorologico giornaliero su un file temporaneo usando `"w"`, `fputs`, `fprintf`, `fputc`, `fflush` e il controllo di `fclose`. Se la scrittura riesce, promuove il file al nome definitivo con `rename`, vi accoda un'osservazione finale aprendolo in modalità `"a"`, lo rilegge su `stdout` per verificarne il contenuto e infine lo elimina con `remove` per non lasciare tracce sul disco.

<!-- cod: id=20.1-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>

static bool scrivi_rapporto(const char *percorso) {
    FILE *fp = fopen(percorso, "w");
    if (fp == nullptr) {
        return false;
    }
    bool ok = (fputs("RAPPORTO METEO\n", fp) != EOF);
    ok = ok && (fprintf(fp, "Temperatura: %.1f C\n", 18.5) >= 0);
    ok = ok && (fprintf(fp, "Umidita: %d%%\n", 62) >= 0);
    for (int i = 0; i < 14 && ok; ++i) {
        ok = (fputc('-', fp) != EOF);
    }
    ok = ok && (fputc('\n', fp) != EOF);
    ok = ok && (fflush(fp) == 0);
    if (fclose(fp) != 0) {
        ok = false;
    }
    return ok;
}

static bool aggiungi_nota(const char *percorso, const char *nota) {
    FILE *fp = fopen(percorso, "a");
    if (fp == nullptr) {
        return false;
    }
    bool ok = (fprintf(fp, "Nota: %s\n", nota) >= 0);
    if (fclose(fp) != 0) {
        ok = false;
    }
    return ok;
}

static bool stampa_file(const char *percorso) {
    FILE *fp = fopen(percorso, "r");
    if (fp == nullptr) {
        return false;
    }
    char riga[128];
    while (fgets(riga, (int)sizeof(riga), fp) != nullptr) {
        fputs(riga, stdout);
    }
    bool ok = (ferror(fp) == 0);
    if (fclose(fp) != 0) {
        ok = false;
    }
    return ok;
}

int main(void) {
    const char *tmp = "rapporto_esempio.tmp";
    const char *fin = "rapporto_esempio.txt";

    if (!scrivi_rapporto(tmp) || rename(tmp, fin) != 0) {
        remove(tmp);
        fprintf(stderr, "Errore nella creazione del rapporto.\n");
        return EXIT_FAILURE;
    }
    if (!aggiungi_nota(fin, "Vento debole da nord.")) {
        remove(fin);
        fprintf(stderr, "Errore nell'aggiornamento del rapporto.\n");
        return EXIT_FAILURE;
    }
    if (!stampa_file(fin) || remove(fin) != 0) {
        remove(fin);
        fprintf(stderr, "Errore nella lettura o rimozione.\n");
        return EXIT_FAILURE;
    }
    printf("Pulizia completata.\n");
    return 0;
}
```

```output
RAPPORTO METEO
Temperatura: 18.5 C
Umidita: 62%
--------------
Nota: Vento debole da nord.
Pulizia completata.
```

Analizziamo i passaggi fondamentali dell'esempio:

- In `scrivi_rapporto`, ogni chiamata di scrittura aggiorna il flag `ok` tramite valutazione a corto circuito (`ok && ...`), così al primo errore le scritture successive vengono saltate ma `fclose(fp)` viene comunque eseguito prima di uscire.
- Il separatore di 14 trattini usa `fputc('-', fp)` seguito da `fputc('\n', fp)`, mentre l'intestazione usa `fputs` con `'\n'` esplicito perché `fputs` non aggiunge ritorni a capo automatici.
- Dopo `fflush(fp) == 0`, controlliamo anche `fclose(fp) != 0` e non usiamo più `fp` dopo la chiusura.
- In `main`, solo dopo che `scrivi_rapporto(tmp)` ha restituito `true`, il file temporaneo viene promosso a `fin` con `rename(tmp, fin) == 0`. Se la creazione o la rinomina fallisce, `remove(tmp)` ripulisce l'eventuale file parziale.
- La funzione `aggiungi_nota` riapre `fin` in modalità `"a"`, accodando la riga finale senza toccare quelle esistenti. Infine `stampa_file` lo rilegge controllando con `ferror(fp) == 0` che non ci siano stati errori di lettura (approfondiremo `ferror` nella sotto-sezione 20.2) e `remove(fin)` lo cancella dal disco.

> **Approfondimento — Perché controllare il valore restituito da `fclose`**
> Quando scrivi su un file con `fprintf` o `fputs`, nella maggior parte dei casi i byte non raggiungono subito il disco: vengono copiati nel buffer in RAM dello stream. Di conseguenza tutte le chiamate a `fprintf` possono restituire successo anche se il disco è pieno o la connessione di rete del filesystem è caduta. Lo svuotamento effettivo verso il sistema operativo avviene spesso soltanto al momento di `fclose(fp)`. Ignorare il valore restituito da `fclose` su uno stream di scrittura significa rischiare di perdere silenziosamente gli ultimi dati scritti.

### Esercizio 20.1 — Generatore di ricevute testuali con aggiornamento sicuro tramite rename e remove

**Descrizione**

Scrivi un programma C che legga da `stdin` una sequenza di righe di comando fino a fine input per costruire una ricevuta su file di testo: `VOCE <articolo> <quantita> <prezzo_cent>` (`1 <= quantita <= 1000`, `0 <= prezzo_cent <= 1000000`, `<articolo>` senza spazi, max 31 caratteri, fino a 64 voci) e `NOTA <testo>` (fino a 16 note, max 127 caratteri ciascuna, rimuovendo il `'\n'` finale). Il programma deve: (1) aprire il file temporaneo `"ricevuta_20_1.tmp"` in modalità `"w"`, scrivere `"=== RICEVUTA ===\n"` con `fputs`, scrivere per ciascuna voce `<articolo> x<quantita> = <euro>.<cent>` con `fprintf` (oppure `"Nessuna voce.\n"` se non ci sono voci), disegnare una riga separatrice di esattamente 16 caratteri `'-'` seguita da `'\n'` usando `fputc`, scrivere `"Totale: <euro>.<cent>\n"` con `fprintf`, chiamare `fflush`, verificare `ferror` e controllare che `fclose` restituisca `0`; (2) rinominare `"ricevuta_20_1.tmp"` in `"ricevuta_20_1.txt"` con `rename`; (3) se è presente almeno una nota, riaprire `"ricevuta_20_1.txt"` in modalità `"a"`, scrivere `"Note:\n"` e ciascuna riga `"- <testo>\n"`, controllando `fclose`; (4) riaprire `"ricevuta_20_1.txt"` in modalità `"r"`, copiare integralmente il contenuto su `stdout` usando `fgets` e `fputs`, chiudere il file e rimuoverlo con `remove`, stampando infine `"Archivio rimosso: OK\n"`. In caso di errore di input o di I/O ripulisci eventuali file temporanei, stampa un messaggio su `stderr` e restituisci `EXIT_FAILURE`.

**Concetti da tenere a mente**

- apertura di file di testo in modalità `"w"`, `"a"` e `"r"` con controllo obbligatorio di `fopen != nullptr`
- uso combinato di `fputs`, `fputc`, `fprintf`, `fflush` e controllo del valore restituito da `fclose`
- aggiornamento sicuro tramite scrittura su file temporaneo seguita da `rename`
- rimozione controllata dei file temporanei e finali con `remove`

**Domande guida**

1. Perché conviene scrivere la ricevuta su un file temporaneo e spostarlo poi con `rename` invece di sovrascrivere direttamente il file definitivo?
2. Quale errore potresti perdere se ignorassi il valore restituito da `fclose` dopo aver chiamato `fprintf` e `fputs`?
3. Qual è la differenza di comportamento tra `fputs` e `puts` riguardo al carattere di fine riga `'\n'`?
4. Che cosa succederebbe alle voci già salvate se nella fase delle note riaprissi `ricevuta_20_1.txt` con `"w"` anziché con `"a"`?

**Esempio di esecuzione**

```input
VOCE Quaderno 2 150
VOCE Penna 3 85
NOTA Pagamento contanti
NOTA Scontrino richiesto
```

```output
=== RICEVUTA ===
Quaderno x2 = 3.00
Penna x3 = 2.55
----------------
Totale: 5.55
Note:
- Pagamento contanti
- Scontrino richiesto
Archivio rimosso: OK
```

## 20.2 Leggere file di testo e distinguere `feof` da `ferror`

Leggere un file di testo sembra a prima vista l'operazione inversa della scrittura, ma presenta insidie molto più sottili: le righe possono avere lunghezze impreviste, un file può terminare senza `'\n'` finale, un disco può restituire un errore di lettura a metà del lavoro e la fine del file può essere rilevata solo *dopo* aver tentato di leggere oltre l'ultimo byte.

Come hai già imparato dal capitolo 5 per `stdin`, il modo più sicuro per leggere testo in C consiste nel separare la lettura fisica dall'analisi del contenuto. Per leggere una riga alla volta si usa `fgets(buf, (int)sizeof(buf), fp)`, che legge al più `sizeof(buf) - 1` caratteri fermandosi al primo `'\n'` (che include nel buffer) oppure alla fine del file, aggiunge sempre `'\0'` e restituisce `buf` in caso di successo o `nullptr` se non riesce a leggere alcun carattere. Una volta ottenuta la riga in memoria, la analizzi con `sscanf`, `strtol` o `strtod` (capitolo 14), così da controllare con precisione gli errori di formato e l'overflow senza mai perdere il controllo della posizione sullo stream.

Quando devi invece ispezionare il file un carattere alla volta, usi `fgetc(fp)`:

```text
int fgetc(FILE *stream);
```

Fai molta attenzione al tipo di ritorno: `fgetc` restituisce un `int`, mai un `char`. Se la lettura riesce, il byte letto viene convertito prima a `unsigned char` (valore compreso tra `0` e `255`) e poi promosso a `int`; se raggiunge la fine del file o si verifica un errore di I/O, restituisce la costante negativa `EOF`. Salvare il risultato di `fgetc` in una variabile `int` è indispensabile per distinguere `EOF` da tutti i 256 valori di byte possibili.

Una situazione che devi gestire esplicitamente con `fgets` sono le **righe più lunghe del buffer**. Se `buf` ha dimensione `N` byte, `fgets` può inserire al massimo `N - 1` caratteri utili prima di `'\0'`. Se una riga nel file supera `N - 1` caratteri, la prima chiamata a `fgets` riempie `buf` senza incontrare `'\n'`, e la chiamata successiva leggerebbe i caratteri rimasti della stessa riga scambiandoli per una nuova riga. Come riconosci il troncamento? Controlli due condizioni: l'ultimo carattere letto in `buf` non è `'\n'` e la lunghezza `strlen(buf)` è uguale a `sizeof(buf) - 1`. Per distinguere una riga lunga esattamente `N - 1` caratteri seguita da `'\n'` (o dalla fine del file) da una riga davvero troncata, puoi leggere un singolo carattere successivo con `fgetc(fp)`: se non è né `'\n'` né `EOF`, la riga è davvero troppo lunga e puoi scartare tutti i caratteri residui con un ciclo `fgetc` fino a `'\n'` o `EOF` (oppure riallocare dinamicamente il buffer se vuoi conservarla per intero).

Veniamo ora all'errore più diffuso nei programmi C che leggono file: scrivere il ciclo controllando `feof(fp)` *prima* della lettura.

<!-- cod: id=20.2-b tipo=frammento -->
```c
// ERRORE: NON scrivere mai questo ciclo!
char riga[64];
while (!feof(fp)) {
    fgets(riga, (int)sizeof(riga), fp);
    printf("%s", riga);
}
```

Perché questo frammento è sbagliato? Perché in C ogni stream mantiene due indicatori interni, interrogabili con `feof(fp)` (fine del file) e `ferror(fp)` (errore di I/O), ed entrambi partono a zero. La funzione `feof(fp)` **non prevede il futuro**: restituisce un valore diverso da zero solo *dopo* che un'operazione di lettura ha già tentato di andare oltre l'ultimo byte del file e ha fallito. Quando il programma ha letto l'ultima riga valida del file, `feof(fp)` è ancora `0`: il ciclo entra in un'iterazione di troppo, `fgets` fallisce restituendo `nullptr` senza modificare `riga` e il programma elabora una seconda volta l'ultima riga (oppure legge memoria non inizializzata se il file era vuoto). Inoltre, se si verifica un errore di lettura sul disco, `feof(fp)` rimane `0` e il ciclo non termina mai.

Lo schema corretto è sempre lo stesso: **la condizione del ciclo controlla direttamente il valore restituito dalla funzione di lettura** (`fgets(...) != nullptr` oppure `(ch = fgetc(fp)) != EOF`). Soltanto *dopo* che il ciclo è terminato interroghi `ferror(fp)` e `feof(fp)` per capire il motivo dell'arresto:

<!-- cod: id=20.2-c tipo=frammento -->
```c
while (fgets(riga, (int)sizeof(riga), fp) != nullptr) {
    // elabora riga
}
if (ferror(fp) != 0) {
    // si è verificato un errore di lettura
} else if (feof(fp) != 0) {
    // fine del file raggiunta regolarmente
}
```

Se sullo stesso stream vuoi azzerare entrambi gli indicatori (per esempio dopo aver rilevato un errore gestibile o prima di riprendere a operare sullo stream), chiami `clearerr(fp)`.

Secondo lo standard C23, il comportamento post-lettura di `feof`, la segnalazione degli errori tramite `ferror` e il ripristino tramite `clearerr` sono completamente definiti. Al contrario, memorizzare il valore restituito da `fgetc` in un `char` introduce un difetto **dipendente dall'implementazione**, legato al fatto che `char` può essere con segno o senza segno a seconda della piattaforma.

### Esempio guidato

Il programma seguente crea un breve file di configurazione con commenti, coppie `chiave=valore` e una riga intenzionalmente più lunga di un buffer di `24` byte. Rilegge poi il file con `fgets`, scarta in modo pulito il residuo delle righe troncate tramite `fgetc`, verifica `feof` e `ferror` alla fine del ciclo e infine provoca deliberatamente un errore provando a scrivere con `fputc` sullo stream aperto in sola lettura, per mostrare l'effetto di `ferror` e il successivo azzeramento con `clearerr`.

<!-- cod: id=20.2-a tipo=programma -->
```c
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static bool crea_config(const char *percorso) {
    FILE *fp = fopen(percorso, "w");
    if (fp == nullptr) {
        return false;
    }
    bool ok = (fputs("# Config sensori\n", fp) != EOF);
    ok = ok && (fputs("porta=8080\n", fp) != EOF);
    ok = ok && (fputs("descrizione=valore_molto_piu_lungo_del_buffer\n", fp) != EOF);
    ok = ok && (fputs("soglia=42\n", fp) != EOF);
    if (fclose(fp) != 0) {
        ok = false;
    }
    return ok;
}

int main(void) {
    const char *percorso = "config_esempio.txt";
    if (!crea_config(percorso)) {
        remove(percorso);
        return EXIT_FAILURE;
    }

    FILE *fp = fopen(percorso, "r");
    if (fp == nullptr) {
        remove(percorso);
        return EXIT_FAILURE;
    }

    char buf[24];
    size_t valide = 0;
    size_t commenti = 0;
    size_t troncate = 0;

    while (fgets(buf, (int)sizeof(buf), fp) != nullptr) {
        size_t len = strlen(buf);
        bool ha_nl = (len > 0 && buf[len - 1] == '\n');
        if (!ha_nl && len == sizeof(buf) - 1) {
            int extra = fgetc(fp);
            if (extra != EOF && extra != '\n') {
                while (extra != EOF && extra != '\n') {
                    extra = fgetc(fp);
                }
                ++troncate;
                continue;
            }
        }
        if (ha_nl) {
            buf[len - 1] = '\0';
        }
        if (buf[0] == '\0' || buf[0] == '#') {
            ++commenti;
            continue;
        }
        char chiave[16];
        long valore = 0;
        char residuo = '\0';
        if (sscanf(buf, "%15[^=]=%ld%c", chiave, &valore, &residuo) == 2) {
            printf("Parametro: %s -> %ld\n", chiave, valore);
            ++valide;
        }
    }

    printf("Fine ciclo: feof=%d ferror=%d\n", feof(fp) != 0, ferror(fp) != 0);
    (void)fputc('!', fp);
    printf("Dopo fputc su sola lettura: ferror=%d\n", ferror(fp) != 0);
    clearerr(fp);
    printf("Dopo clearerr: feof=%d ferror=%d\n", feof(fp) != 0, ferror(fp) != 0);
    printf("Riepilogo: valide=%zu commenti=%zu troncate=%zu\n",
           valide, commenti, troncate);

    fclose(fp);
    remove(percorso);
    return 0;
}
```

```output
Parametro: porta -> 8080
Parametro: soglia -> 42
Fine ciclo: feof=1 ferror=0
Dopo fputc su sola lettura: ferror=1
Dopo clearerr: feof=0 ferror=0
Riepilogo: valide=2 commenti=1 troncate=1
```

Osserva come si comporta il programma sulle diverse righe del file:

- Il ciclo `while (fgets(buf, (int)sizeof(buf), fp) != nullptr)` si arresta non appena `fgets` tenta di leggere oltre l'ultima riga. In quel momento `feof(fp)` vale diverso da zero (`1` nella stampa booleana) e `ferror(fp)` vale `0`.
- Quando `fgets` legge la riga `descrizione=valore_molto_piu_lungo_del_buffer\n` in un buffer di `24` byte, `buf` contiene i primi `23` caratteri senza `'\n'`. La variabile `int extra = fgetc(fp)` legge il 24° carattere (`'o'`), che non è né `'\n'` né `EOF`: il ciclo interno consuma il resto della riga fino a `'\n'`, incrementa `troncate` e passa alla riga successiva (`soglia=42`) senza spezzarla.
- La chiamata `(void)fputc('!', fp)` tenta una scrittura su uno stream aperto con `"r"`: fallisce e imposta l'indicatore di errore (`ferror(fp) != 0`).
- La chiamata `clearerr(fp)` azzera entrambi gli indicatori (`feof` e `ferror` tornano entrambi a `0`). Infine lo stream viene chiuso e il file temporaneo rimosso.

> **Approfondimento — La trappola di `char c = fgetc(fp);`**
> Salvare il risultato di `fgetc` in un `char` invece che in un `int` produce due difetti diversi a seconda della piattaforma:
> - Sui sistemi in cui `char` è senza segno (`0..255`), `EOF` (di solito `-1`) viene convertito a `255`, quindi il confronto `c != EOF` è sempre vero e il programma entra in un ciclo infinito.
> - Sui sistemi in cui `char` è con segno (`-128..127`), un byte legittimo di valore `0xFF` (`255`) viene convertito a `-1`, diventando indistinguibile da `EOF` e interrompendo prematuramente la lettura del file.
>
> Dichiara quindi **sempre** `int c = fgetc(fp);`.

### Esercizio 20.2 — Analizzatore di file di log con gestione delle righe lunghe e diagnostica feof/ferror/clearerr

**Descrizione**

Scrivi un programma C che simuli la lettura rigorosa di un file di log testuale. (1) Copia integralmente `stdin` in un file di testo temporaneo `"log_20_2.txt"` usando `fgetc`/`fputc` (memorizzando ogni carattere in `int`), verifica l'assenza di errori e chiudi il file. (2) Riapri `"log_20_2.txt"` in modalità `"r"` e leggilo con `fgets` in un buffer di esattamente `32` byte (`char buf[32]`). Se una riga supera i 31 caratteri utili (cioè `buf` contiene 31 caratteri senza `'\n'` e il carattere successivo letto con `fgetc` non è né `'\n'` né `EOF`), scarta i caratteri residui della riga fino a `'\n'` o `EOF` con `fgetc` e incrementa il contatore `troncate`. Altrimenti rimuovi eventuale `'\n'`/`'\r'` finale: se la riga è vuota o inizia (dopo eventuali spazi) con `'#'`, incrementa `ignorate`; altrimenti verifica il formato esatto `<livello>;<codice>;<durata_ms>` dove `<livello>` è `INFO`, `WARN` o `ERR`, `<codice>` è un intero nell'intervallo `int32_t` e `<durata_ms>` è un intero non negativo nell'intervallo `int64_t` (entrambi convertiti con `strtol` azzerando `errno = 0` e controllando `ERANGE` e assenza di caratteri residui). Se valida, aggiorna il contatore del livello e la somma delle durate; altrimenti incrementa `malformate`. (3) Al termine del ciclo `fgets`, stampa lo stato `Stato fine lettura: EOF=<0|1> ERR=<0|1>` interrogando `feof` e `ferror`, provoca un errore di scrittura chiamando `fputc('X', fp)` sullo stream aperto in sola lettura e stampa `Dopo scrittura su sola lettura: ERR=<0|1>`, chiama `clearerr(fp)` e stampa `Dopo clearerr: EOF=<0|1> ERR=<0|1>`. (4) Chiudi il file, rimuovilo con `remove` e stampa il riepilogo esatto dell'esempio.

**Concetti da tenere a mente**

- ciclo di lettura basato sul ritorno di `fgets`/`fgetc` anziché su `while (!feof(fp))`
- memorizzazione del ritorno di `fgetc` in `int` per distinguere `EOF` da ogni byte valido
- rilevamento e smaltimento delle righe più lunghe del buffer di `fgets` senza corrompere le righe successive
- distinzione tra `feof` e `ferror` e azzeramento degli indicatori con `clearerr`

**Domande guida**

1. Perché controllare `while (!feof(fp))` prima di chiamare `fgets` produrrebbe un conteggio errato sull'ultima riga del file?
2. Come fai a distinguere una riga lunga esattamente 31 caratteri (seguita da `'\n'`) da una riga realmente troncata lunga 32 o più caratteri quando il buffer è di 32 byte?
3. Perché il valore restituito da `fgetc` va sempre salvato in una variabile `int` e non in un `char`?
4. Quale effetto produce `clearerr(fp)` sugli indicatori interni dello stream dopo un errore di scrittura su uno stream aperto in sola lettura?

**Esempio di esecuzione**

```input
# Log di sistema
INFO;100;15

WARN;205;40
ERR;500;120
INFO;abc;10
WARN;99;-5
INFO;101;999;questa_riga_supera_i_trentuno_caratteri
```

```output
Stato fine lettura: EOF=1 ERR=0
Dopo scrittura su sola lettura: ERR=1
Dopo clearerr: EOF=0 ERR=0
Valide: 3 (INFO=1 WARN=1 ERR=1) Durata=175 ms
Ignorate: 2 Malformate: 2 Troncate: 1
```

## 20.3 File binari con `fread` e `fwrite`

I file di testo sono comodi da leggere con un editor, ma non sono adatti a tutto: immagini, audio, archivi compressi, campioni di sensori o database su disco sono sequenze di byte arbitrari, in cui un byte `0x0A` non significa "a capo" e un byte `0x00` non segna la fine di una stringa. Se aprissi un file simile in modalità testo, su alcuni sistemi operativi la libreria standard tradurrebbe ogni byte `0x0A` in `0x0D 0x0A` in scrittura (o viceversa in lettura), corrompendo irreparabilmente i dati.

Un **file binario** (*binary file*) è un file aperto con il modificatore `"b"` nel secondo argomento di `fopen` (`"rb"`, `"wb"`, `"ab"`, `"r+b"`, `"w+b"`, `"a+b"`, oppure `"wbx"`): i byte vengono letti e scritti esattamente come sequenza grezza, senza alcuna traduzione dei caratteri di fine riga. Anche se su sistemi Unix e macOS la modalità binaria e quella testuale si comportano in modo identico, specificare sempre `"b"` sui file binari è obbligatorio per la portabilità del codice su Windows e per rendere esplicita l'intenzione a chi legge il programma.

Per trasferire blocchi di byte da e verso un file binario si usano `fwrite` e `fread`, dichiarate in `<stdio.h>`:

```text
size_t fwrite(const void *restrict ptr, size_t size, size_t nmemb, FILE *restrict stream);
size_t fread(void *restrict ptr, size_t size, size_t nmemb, FILE *restrict stream);
```

Entrambe ricevono un puntatore al buffer in memoria (`ptr`), la dimensione in byte di un singolo elemento (`size`), il numero di elementi da trasferire (`nmemb`) e lo stream (`stream`). Entrambe restituiscono il numero di **elementi completi** effettivamente trasferiti:

- Per `fwrite`: se il valore restituito è minore di `nmemb`, si è verificato un errore di scrittura.
- Per `fread`: se il valore restituito è minore di `nmemb`, può essere stata raggiunta la fine del file oppure può essersi verificato un errore di lettura. Come per i file di testo, interroghi `ferror(fp)` e `feof(fp)` per distinguere i due casi.

Quando elabori un file binario a blocchi — ad esempio per copiarlo, calcolarne una somma di controllo, comprimerlo o confrontarlo con un altro file — conviene usare un buffer fisso di byte, come `uint8_t buf[4096];` (o una dimensione più piccola nei test), e leggere ripetutamente con `fread(buf, 1, sizeof(buf), fp)`. Passando `size = 1` e `nmemb = sizeof(buf)`, il valore restituito da `fread` è il numero esatto di byte validi letti, anche sull'ultimo blocco parziale del file. Questo schema, chiamato elaborazione a blocchi (streaming), permette di trattare file di dimensioni arbitrarie usando una quantità costante e ridotta di RAM.

```text
File su disco (50 byte)      Buffer uint8_t buf[16]
+----------------+           Iterazione 1: fread(..., 1, 16, fp) -> 16 byte
| blocco 0 (16B) | --------> elabora buf[0..15]
| blocco 1 (16B) | --------> Iterazione 2: fread(..., 1, 16, fp) -> 16 byte
| blocco 2 (16B) | --------> Iterazione 3: fread(..., 1, 16, fp) -> 16 byte
| resto     (2B) | --------> Iterazione 4: fread(..., 1, 16, fp) ->  2 byte
+----------------+           Iterazione 5: fread(..., 1, 16, fp) ->  0 (feof)
```

Un'altra regola cruciale riguarda gli stream aperti in **aggiornamento** (`"r+b"`, `"w+b"`, `"a+b"` e le corrispondenti modalità di testo `"r+"`, `"w+"`, `"a+"`), sui quali lo stesso `FILE *` viene usato sia per leggere sia per scrivere:

- Non puoi passare direttamente da una scrittura a una lettura senza chiamare prima `fflush(fp)`, `fseek` o `rewind`.
- Non puoi passare direttamente da una lettura a una scrittura senza chiamare prima `fseek` o `rewind`, a meno che la lettura precedente non abbia già incontrato la fine del file (`EOF`).

Secondo lo standard C23, `fread`, `fwrite` e le modalità binarie sono completamente definiti; violare la regola di alternanza tra lettura e scrittura su uno stream di aggiornamento provoca invece **comportamento indefinito**, perché i buffer interni di ingresso e uscita potrebbero risultare disallineati.

### Esempio guidato

Il programma seguente scrive una sequenza di `21` byte grezzi (che include anche `0x00`, `0x0A` e `0x0D`) su un file binario con `fwrite`. Poi legge il file a blocchi di `8` byte con `fread(buf, 1, sizeof(buf), fin)`, calcola una checksum XOR su tutti i byte e produce una copia trasformata applicando un XOR con una chiave costante `0x5A`. Infine applica la stessa trasformazione inversa su un terzo file e confronta l'originale e il file ripristinato a blocchi con `memcmp` per verificarne l'identità bit a bit, rimuovendo i file al termine.

<!-- cod: id=20.3-a tipo=programma -->
```c
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static bool trasforma_xor(const char *src, const char *dst, uint8_t chiave,
                          size_t *tot_byte, uint8_t *checksum_in) {
    FILE *fin = fopen(src, "rb");
    FILE *fout = fopen(dst, "wb");
    if (fin == nullptr || fout == nullptr) {
        if (fin != nullptr) { fclose(fin); }
        if (fout != nullptr) { fclose(fout); }
        return false;
    }
    uint8_t buf[8];
    size_t letti = 0;
    size_t totale = 0;
    uint8_t xsum = 0;
    bool ok = true;

    while (ok && (letti = fread(buf, 1, sizeof(buf), fin)) > 0) {
        totale += letti;
        for (size_t i = 0; i < letti; ++i) {
            xsum ^= buf[i];
            buf[i] ^= chiave;
        }
        if (fwrite(buf, 1, letti, fout) != letti) {
            ok = false;
        }
    }
    if (ok && ferror(fin) != 0) { ok = false; }
    if (fclose(fin) != 0) { ok = false; }
    if (fclose(fout) != 0) { ok = false; }
    if (ok) {
        *tot_byte = totale;
        *checksum_in = xsum;
    }
    return ok;
}

static bool file_uguali(const char *a, const char *b) {
    FILE *fa = fopen(a, "rb");
    FILE *fb = fopen(b, "rb");
    if (fa == nullptr || fb == nullptr) {
        if (fa != nullptr) { fclose(fa); }
        if (fb != nullptr) { fclose(fb); }
        return false;
    }
    uint8_t ba[8], bb[8];
    bool uguali = true;
    while (true) {
        size_t na = fread(ba, 1, sizeof(ba), fa);
        size_t nb = fread(bb, 1, sizeof(bb), fb);
        if (na != nb || (na > 0 && memcmp(ba, bb, na) != 0)) {
            uguali = false;
            break;
        }
        if (na == 0) {
            if (ferror(fa) != 0 || ferror(fb) != 0) { uguali = false; }
            break;
        }
    }
    fclose(fa);
    fclose(fb);
    return uguali;
}

int main(void) {
    const char *f_orig = "campioni_es.bin";
    const char *f_xor = "campioni_es.xor";
    const char *f_ric = "campioni_es.ric";
    const uint8_t dati[21] = {
        0x00, 0x0A, 0x0D, 0x10, 0x22, 0x33, 0x44, 0x55,
        0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD,
        0xEE, 0xFF, 0x01, 0x02, 0x03
    };
    FILE *fp = fopen(f_orig, "wb");
    if (fp == nullptr) { return EXIT_FAILURE; }
    bool ok = (fwrite(dati, 1, sizeof(dati), fp) == sizeof(dati));
    if (fclose(fp) != 0) { ok = false; }

    size_t n1 = 0, n2 = 0;
    uint8_t cs_orig = 0, cs_xor = 0;
    ok = ok && trasforma_xor(f_orig, f_xor, 0x5AU, &n1, &cs_orig);
    ok = ok && trasforma_xor(f_xor, f_ric, 0x5AU, &n2, &cs_xor);
    bool identici = ok && file_uguali(f_orig, f_ric);

    remove(f_orig);
    remove(f_xor);
    remove(f_ric);
    if (!ok) { return EXIT_FAILURE; }

    printf("Byte elaborati: %zu -> %zu\n", n1, n2);
    printf("Checksum XOR originale: 0x%02" PRIX8 "\n", cs_orig);
    printf("Ripristino identico: %s\n", identici ? "SI" : "NO");
    return 0;
}
```

```output
Byte elaborati: 21 -> 21
Checksum XOR originale: 0x06
Ripristino identico: SI
```

Esaminiamo i dettagli più importanti:

- I `21` byte di `dati` non sono un multiplo del buffer da `8` byte: `trasforma_xor` esegue due letture da `8` byte, una terza lettura parziale da `5` byte e infine una quarta chiamata a `fread` che restituisce `0`.
- Poiché passiamo `size = 1` e `nmemb = sizeof(buf)`, `letti` vale esattamente `8`, `8`, `5` e `0`, permettendoci di scrivere esattamente `letti` byte su `fout` con `fwrite(buf, 1, letti, fout)`.
- Al termine del ciclo `while`, il controllo `ferror(fin) != 0` garantisce che `fread` abbia restituito `0` per fine del file e non per un errore di lettura.
- In `file_uguali`, confrontiamo sia il numero di byte letti (`na != nb`) sia il contenuto (`memcmp(ba, bb, na) != 0`), così due file in cui uno è prefisso dell'altro vengono distinti correttamente.

> **Approfondimento — `fread(buf, 1, N, fp)` contro `fread(buf, N, 1, fp)`**
> Invertire `size` e `nmemb` è un errore frequente. Con `fread(buf, N, 1, fp)` chiedi alla libreria standard un solo elemento di `N` byte: se il file contiene `21` byte e `N = 8`, dopo i primi due blocchi restano `5` byte, che non bastano a formare un elemento completo. `fread` restituisce quindi `0` anziché `5`, e non hai modo portabile di sapere quanti byte validi siano stati copiati in `buf`. Con `fread(buf, 1, N, fp)` chiedi invece `N` elementi da `1` byte e ricevi sempre il numero esatto di byte letti.

### Esercizio 20.3 — Compressore e decompressore binario RLE a blocchi con fread e fwrite

**Descrizione**

Scrivi un programma C che implementi la compressione e decompressione binaria Run-Length Encoding (RLE) su file reali usando `fread` e `fwrite` a blocchi di `16` byte. Nel formato RLE ogni sequenza di byte uguali consecutivi è codificata come coppia di 2 byte `[conteggio (1..255), valore]`; sequenze più lunghe di `255` byte vanno spezzate in più coppie consecutive (es. 260 byte `0x00` diventano `[255, 0x00]` seguito da `[5, 0x00]`). (1) Leggi da `stdin` zero o più righe nel formato `RUN <conteggio> <hex>` (`1 <= conteggio <= 600`, `<hex>` valore esadecimale `00..FF`) e scrivi i byte grezzi corrispondenti nel file binario `"orig_20_3.bin"` (`"wb"`). (2) Implementa `bool comprimi_rle(const char *src, const char *dst, size_t *byte_orig, size_t *byte_comp)` che legge `src` (`"rb"`) a blocchi di `16` byte con `fread(buf, 1, sizeof(buf), fin)`, fonde correttamente le sequenze di byte uguali anche attraverso i confini dei blocchi e scrive le coppie su `dst` (`"wb"`) con `fwrite`. (3) Implementa `bool decomprimi_rle(const char *src, const char *dst)` che legge `src` a blocchi di `16` byte (8 coppie), rifiuta file con lunghezza dispari o conteggio `0`, e ricostruisce i byte originali su `dst`. (4) Implementa `bool file_identici(const char *a, const char *b)` che confronta `orig_20_3.bin` e `ric_20_3.bin` a blocchi di `16` byte usando `fread` e `memcmp`, verificando che entrambi terminino esattamente insieme. (5) Stampa la dimensione originale, quella compressa con il numero di coppie, l'elenco delle coppie RLE lette dal file compresso (`<cnt>x<HEX2>`, oppure `(vuoto)` se 0 coppie) e `Integrita: OK`, poi elimina tutti e tre i file con `remove`.

**Concetti da tenere a mente**

- apertura in modalità binaria `"rb"` e `"wb"` per preservare esattamente ogni byte
- uso di `fread(buf, 1, sizeof(buf), fp)` per conoscere il numero esatto di byte letti nei blocchi parziali
- mantenimento dello stato della sequenza corrente tra blocchi consecutivi e controllo di `ferror`/`feof`
- verifica dell'integrità binaria con confronti a blocchi tramite `memcmp` e pulizia con `remove`

**Domande guida**

1. Perché nell'elaborazione a blocchi conviene chiamare `fread(buf, 1, sizeof(buf), fp)` invece di `fread(buf, sizeof(buf), 1, fp)`?
2. Che cosa succederebbe a una sequenza di 20 byte uguali letta con un buffer di 16 byte se azzerassi lo stato RLE a ogni iterazione del ciclo `fread`?
3. Come verifichi in `decomprimi_rle` che il file compresso non sia stato troncato a metà di una coppia di 2 byte?
4. Perché in `file_identici` non basta controllare che i blocchi letti coincidano con `memcmp`, ma occorre anche verificare che entrambi i file raggiungano la fine nello stesso momento?

**Esempio di esecuzione**

```input
RUN 10 41
RUN 10 41
RUN 1 42
RUN 260 00
```

```output
Originale: 281 byte
Compresso: 8 byte (4 coppie)
RLE: 20x41 1x42 255x00 5x00
Integrita: OK
```

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
    printf("Prima: id=%" PRIu32 " sigla=%s temp=%" PRId32 "\n", s.id, s.sigla, s.temp_dec);

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
    bool ok = (fseek(fp, 0L, SEEK_SET) == 0 &&
               fwrite(hdr, 1, sizeof(hdr), fp) == sizeof(hdr));
    if (fclose(fp) != 0) { ok = false; }
    return ok;
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

## Riepilogo

- Un file su disco si gestisce tramite un puntatore `FILE *` (tipo opaco in `<stdio.h>`, mai copiato per valore) restituito da `fopen`. Nei **file di testo** (`"r"`, `"w"`, `"a"`, `"r+"`, `"w+"`, `"a+"`, `"wx"`) si scrive con `fprintf`, `fputs` (che non aggiunge `'\n'`) e `fputc`, svuotando il buffer quando necessario con `fflush(fp)` e controllando sempre sia `fopen != nullptr` sia `fclose(fp) == 0`. `rename` e `remove` consentono aggiornamenti sicuri tramite file temporaneo e pulizia finale.
- Per leggere file di testo si usa `fgets` (gestendo eventuali righe più lunghe del buffer) oppure `fgetc` (salvando sempre il risultato in `int` per distinguere `EOF` da ogni byte `0..255`), controllando nel ciclo il valore restituito dalla lettura e mai `while (!feof(fp))`. Solo al termine del ciclo si interrogano `ferror(fp)` e `feof(fp)` per distinguere un errore di I/O dalla fine regolare del file; `clearerr(fp)` azzera entrambi gli indicatori.
- I **file binari** si aprono aggiungendo `"b"` alla modalità (`"rb"`, `"wb"`, `"r+b"`, `"w+b"`...) per evitare traduzioni dei fine riga. `fread(buf, 1, sizeof(buf), fp)` e `fwrite` permettono di elaborare file di qualunque dimensione a blocchi conoscendo il numero esatto di byte trasferiti anche sull'ultimo blocco parziale. Sugli stream di aggiornamento, prima di passare da scrittura a lettura occorre chiamare `fflush`, `fseek` o `rewind`, mentre per passare da lettura (non a `EOF`) a scrittura occorre chiamare `fseek` o `rewind`.
- L'**accesso casuale** nei file binari si realizza con `fseek` (`SEEK_SET`, `SEEK_CUR`, `SEEK_END`), `ftell` (controllando `-1L`) e `rewind`, consentendo di leggere e aggiornare in loco record di dimensione fissa. `tmpfile()` crea file binari temporanei in `"wb+"` eliminati automaticamente alla chiusura.
- La **serializzazione** binaria portabile evita di scrivere `struct` grezze con `fwrite`: codifica ogni campo esplicitamente con tipi a larghezza fissa (`<stdint.h>`), ordine dei byte fissato tramite spostamenti e maschere, prefissi di lunghezza per le stringhe e un'intestazione con numero magico, versione del formato, conteggio e checksum, validando ogni lunghezza prima di allocare memoria. Tecniche più complete per diagnosticare gli errori di sistema e gestire il rilascio di più risorse su molti percorsi di errore saranno approfondite nei prossimi capitoli (lo vedremo nel capitolo 21).

## Errori comuni

- **Scrivere il ciclo di lettura come `while (!feof(fp))` invece di controllare il valore restituito da `fgets` o `fgetc`**: `feof(fp)` diventa vero solo dopo che una lettura ha già fallito oltre la fine del file, facendo elaborare due volte l'ultima riga o leggere dati non inizializzati (e bloccando il ciclo in caso di errore di lettura).
- **Salvare il valore restituito da `fgetc` in una variabile `char` anziché in `int`**: su piattaforme con `char` senza segno `c != EOF` è sempre vero (ciclo infinito), mentre con `char` con segno il byte `0xFF` viene confuso con `EOF` interrompendo la lettura.
- **Dimenticare di controllare `fopen != nullptr` o `fclose(fp) == 0` in scrittura, oppure omettere `"b"` aprendo un file binario**: un errore di disco pieno può manifestarsi solo dentro `fclose`, e l'assenza di `"b"` corrompe i file binari sui sistemi che traducono i fine riga.
- **Alternare lettura e scrittura su uno stream aperto in aggiornamento (`"r+b"`, `"w+b"`) senza interporre `fseek`, `rewind` o `fflush`**: provoca comportamento indefinito per disallineamento dei buffer interni dello stream.
- **Serializzare una `struct` direttamente con `fwrite(&s, sizeof(s), 1, fp)`**: genera file non portabili dipendenti da ordine dei byte, allineamento e padding non specificato, e salva indirizzi di puntatori non validi a un successivo caricamento.

## Prima di proseguire

- [ ] So aprire, scrivere, svuotare e chiudere un file di testo controllando `fopen`, `fflush`, `fclose`, e aggiornare file in modo sicuro con `rename` e `remove`.
- [ ] So leggere file di testo con `fgets` e `fgetc` (in `int`), gestire righe più lunghe del buffer, evitare `while (!feof(fp))` e diagnosticare errori con `ferror`, `feof` e `clearerr`.
- [ ] So elaborare file binari a blocchi con `"rb"`/`"wb"`, `fread(buf, 1, sizeof(buf), fp)` e `fwrite`, rispettando la regola di alternanza su stream di aggiornamento.
- [ ] So implementare l'accesso casuale e l'aggiornamento in loco su archivi binari a record fissi usando `fseek`, `ftell`, `rewind` e `tmpfile`.
- [ ] So progettare un formato binario portabile e versionato con codifica esplicita dei byte, prefisso di lunghezza per le stringhe, numero magico, checksum e controlli difensivi sui limiti prima di allocare memoria.
