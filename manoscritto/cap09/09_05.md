## 9.5 Buffer overflow e gestione sicura del testo

Nel capitolo 8 hai visto che il C non controlla automaticamente gli indici degli array. Quando questo problema riguarda un buffer di testo e una funzione scrive dati oltre l'ultimo byte riservato, si verifica un **buffer overflow**: una scrittura di dati oltre la fine della memoria riservata a un buffer, causa di comportamento indefinito e di gravi vulnerabilità di sicurezza.

In C23 un buffer overflow viola i limiti dell'oggetto allocato e provoca **comportamento indefinito**. Nei casi più fortunati il programma si chiude immediatamente; nei casi peggiori sovrascrive silenziosamente altre variabili vicine in memoria o permette a un attaccante di alterare il comportamento del programma fornendo un input costruito ad arte.

> **Attenzione — Errore da non scrivere mai**
> Il frammento seguente mostra un classico buffer overflow causato da `strcpy` senza controllo della capacità: provoca comportamento indefinito e **non va mai scritto** in un programma reale.

<!-- cod: id=9.5-b tipo=frammento -->
```c
// ERRORE GRAVE: comportamento indefinito (buffer overflow)!
char nome[6];
strcpy(nome, "Alessandra");  // Scrive 11 byte (incluso '\0') in un buffer da 6 byte
```

### Errori *off-by-one* sulle stringhe

Anche un solo byte in eccesso è già un buffer overflow. L'errore più frequente sulle stringhe è dimenticare il byte riservato al terminatore nullo `'\0'`:

- Un buffer `char codice[5]` può contenere una stringa di al massimo `4` caratteri utili (`indici 0..3`) più `'\0'` in posizione `4`.
- Se verifichi la capienza con `strlen(orig) <= sizeof(dest)` invece di `strlen(orig) < sizeof(dest)`, quando `strlen(orig)` è esattamente uguale a `sizeof(dest)` il terminatore nullo viene scritto fuori dai limiti del buffer.

### Righe di ingresso più lunghe del buffer di `fgets`

Usare `fgets(buf, (int)sizeof(buf), stdin)` impedisce il buffer overflow perché `fgets` legge al massimo `sizeof(buf) - 1` caratteri e aggiunge sempre `'\0'`. Tuttavia, che cosa accade se l'utente digita una riga più lunga di `sizeof(buf) - 1` caratteri?

`fgets` riempie il buffer con la prima parte della riga e **lascia tutti i caratteri rimanenti nello stream `stdin`**. Se non fai nulla, la chiamata successiva a `fgets` leggerà gli avanzi della riga precedente scambiandoli per una nuova riga!

Per gestire il caso in modo rigoroso procedi così:

1. Dopo `fgets`, cerca `'\n'` con `size_t len = strcspn(buf, "\n");`.
2. Se `buf[len] == '\n'`, l'intera riga è entrata nel buffer: sostituisci `buf[len] = '\0';` e hai finito.
3. Se `buf[len] != '\n'`, non è stato ancora letto `'\n'` (oppure il file è finito subito dopo). Leggi il prossimo carattere con `int c = getchar();`:
   - se `c == '\n' || c == EOF`, la riga era lunga **esattamente** `sizeof(buf) - 1` caratteri e non è stata troncata;
   - altrimenti la riga superava la capacità del buffer: continua a chiamare `getchar()` in un ciclo finché `c != '\n' && c != EOF` per svuotare completamente la parte eccedente prima della lettura successiva.

### Progettare funzioni sicure per il testo

La regola d'oro per prevenire i buffer overflow nel tuo codice è semplice: **ogni funzione che modifica una stringa di destinazione deve ricevere sempre la coppia `(char dest[], size_t capienza)`**, deve riservare almeno un byte per `'\0'` e deve restituire un `bool` (o un codice di stato) per informare il chiamante se l'operazione è riuscita o se è stata rifiutata per mancanza di spazio.

Riassumiamo una lista di controllo pratica da applicare ogni volta che lavori con stringhe in C:

1. Conta sempre il `+ 1` per `'\0'` nel dimensionare i buffer e nei controlli di capienza (`lunghezza < capienza`).
2. Leggi sempre le righe con `fgets`, mai con funzioni prive di limite, e svuota i residui di `stdin` se la riga eccede il buffer.
3. Specifica sempre la larghezza massima con `%Ns` in `sscanf` (dove `N = sizeof(buf) - 1`).
4. Preferisci `snprintf` e funzioni ausiliarie con capacità esplicita rispetto a `strcpy` e `strcat` non controllate.
5. Verifica sempre i valori di ritorno (`nullptr`, `bool`, `< 0`, `>= capienza`).

Esistono inoltre strumenti del compilatore, chiamati sanitizer, che rilevano automaticamente durante i test eventuali letture o scritture fuori dai limiti di un buffer (lo vedremo nel capitolo 11).

### Esempio guidato

Il programma seguente definisce tre funzioni sicure — `svuota_riga`, `copia_sicura` e `accoda_sicura` — che ricevono sempre la capacità esplicita del buffer di destinazione e restituiscono un esito booleano. Legge un nome utente in un piccolo buffer `char utente[12]`, svuota eventuali caratteri eccedenti e compone un'etichetta in `char tag[18]`.

<!-- cod: id=9.5-a tipo=programma -->
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool svuota_se_troncata(char buf[]) {
    size_t len = strcspn(buf, "\n");
    if (buf[len] == '\n') {
        buf[len] = '\0';
        return false;
    }
    int c = getchar();
    if (c == '\n' || c == EOF) {
        return false;
    }
    while (c != '\n' && c != EOF) {
        c = getchar();
    }
    return true;
}

bool copia_sicura(char dest[], size_t cap, const char orig[]) {
    if (cap == 0 || strlen(orig) >= cap) { return false; }
    strcpy(dest, orig);
    return true;
}

bool accoda_sicura(char dest[], size_t cap, const char orig[]) {
    if (cap == 0 || strlen(dest) + strlen(orig) >= cap) { return false; }
    strcat(dest, orig);
    return true;
}

int main(void) {
    char utente[12];
    char tag[18] = "";

    if (fgets(utente, (int)sizeof(utente), stdin) == nullptr) {
        fprintf(stderr, "Errore: input mancante.\n");
        return EXIT_FAILURE;
    }
    bool troncata = svuota_se_troncata(utente);
    printf("Utente letto: %s (troncato: %s)\n", utente, troncata ? "si" : "no");

    if (copia_sicura(tag, sizeof(tag), "USR:") &&
        accoda_sicura(tag, sizeof(tag), utente)) {
        printf("Tag pronto: %s\n", tag);
    } else {
        printf("Spazio insufficiente per comporre il tag.\n");
    }
    return EXIT_SUCCESS;
}
```

```input
massimiliano_rossi
```

```output
Utente letto: massimilian (troncato: si)
Tag pronto: USR:massimilian
```

Osserva come ogni operazione resta dentro i limiti garantiti:

- `utente` ha capacità `12` byte, quindi `fgets` legge al massimo `11` caratteri (`"massimilian"`) più `'\0'`.
- `svuota_se_troncata` scopre che `'\n'` non è presente in `utente`, legge il carattere successivo (`'o'`, diverso da `'\n'` e da `EOF`), consuma il resto della riga fino a `'\n'` e restituisce `true` per segnalare il troncamento. Una seconda `fgets` ripartirebbe ora in modo pulito dalla riga successiva.
- `copia_sicura` e `accoda_sicura` controllano sempre `cap == 0` e che la lunghezza totale resti strettamente minore di `cap` (lasciando spazio per `'\0'`) prima di chiamare `strcpy` e `strcat`. Qui `"USR:"` (4 byte) + `"massimilian"` (11 byte) = `15 < 18`, quindi il tag entra in `tag` con piena sicurezza.

> **Approfondimento — Che cosa succede in memoria durante un buffer overflow**
> Immagina due variabili locali collocate una accanto all'altra in memoria: un buffer `char buf[8]` e un flag `int amministratore = 0;`.
>
> ```text
> Indirizzi crescenti --->
> +-----+-----+-----+-----+-----+-----+-----+-----+-----------------+
> |  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  | amministratore  |
> +-----+-----+-----+-----+-----+-----+-----+-----+-----------------+
> | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' |'\0'| ...  |
> +-----+-----+-----+-----+-----+-----+-----+-----+-----------------+
> |<------------ char buf[8] (8 byte) ----------->|<-- SOVRASCRITTO |
> ```
>
> Scrivere `"ABCDEFGHI"` in `buf` senza controllare la capacità supera gli `8` byte riservati e può invadere i byte della variabile adiacente `amministratore`, trasformando il suo valore da `0` in un numero diverso da zero (vero in un `if`!). La disposizione esatta delle variabili dipende dal compilatore e dalle ottimizzazioni, quindi non puoi mai prevedere quale dato verrà corrotto: l'unica difesa affidabile è prevenire sempre il buffer overflow nel codice.

### Esercizio 9.5 — Raccolta sicura di nomi in buffer limitati contro il buffer overflow

**Descrizione**

Scrivi un programma C che includa `<stdio.h>`, `<stdlib.h>` e `<string.h>` per leggere una sequenza di nomi di città da `stdin` (uno per riga, fino alla fine dell'input) usando un piccolo buffer di ingresso `char riga[16];` (al massimo `15` caratteri utili per nome) e comporre un elenco in un buffer di uscita di capacità fissa `char elenco[40] = "";` con voci separate da `" | "`. Dichiara prima di `main` i prototipi di due funzioni sicure: `int leggi_riga_limitata(char buf[], size_t cap)` (usa `fgets`: restituisce `0` alla fine dell'input; se la riga entra interamente nel buffer — incluso il caso limite di esattamente `cap - 1` caratteri seguiti da `'\n'` o `EOF` — rimuove `'\n'` e restituisce `1`; se la riga supera `cap - 1` caratteri, svuota tutti i caratteri residui fino a `'\n'` o `EOF` con `getchar()` e restituisce `2`) e `bool accoda_voce(char dest[], size_t cap, const char voce[], const char sep[])` (verifica in anticipo che `strlen(dest) + (dest[0] != '\0' ? strlen(sep) : 0) + strlen(voce) < cap`; solo se c'è spazio per entrambi accoda prima l'eventuale separatore e poi `voce` e restituisce `true`, altrimenti lascia `dest` intatto e restituisce `false`). In `main` ignora le righe vuote, conta voci inserite, voci omesse per capienza e righe troncate in ingresso (anche se poi omesse per capienza), quindi stampa il riepilogo finale esattamente come nell'esempio di esecuzione.

**Concetti da tenere a mente**

- prevenzione del buffer overflow con controllo preventivo della capacità
- svuotamento dello stream residuo con `getchar()` dopo una riga troncata da `fgets`
- caso limite della riga lunga esattamente `cap - 1` caratteri
- accodamento atomico di separatore e voce senza lasciare separatori orfani

**Domande guida**

1. Che cosa succederebbe alla lettura della riga successiva se `leggi_riga_limitata` non svuotasse i caratteri eccedenti lasciati in `stdin` da `fgets`?
2. Come distingue `leggi_riga_limitata` una riga lunga esattamente `15` caratteri seguiti da `'\n'` da una riga lunga `16` o più caratteri?
3. Perché `accoda_voce` deve verificare la capienza complessiva di separatore più voce prima di modificare `dest`?
4. Qual è la lunghezza massima possibile di `elenco` quando la sua capacità è `40` byte?

**Esempio di esecuzione**

```input
Torino
Milano
Reggio Emilia Centro
Rho
Napoli
Bologna
```

```output
Voci inserite: 4
Voci omesse per capienza: 2
Righe troncate in ingresso: 1
Elenco (39/39): Torino | Milano | Reggio Emilia C | Rho
```
