## 18.2 Gestire le collisioni con il concatenamento

Nella sotto-sezione precedente hai visto che le collisioni sono inevitabili: anche una buona funzione di hash può mappare due chiavi diverse sullo stesso indice di secchio. Se la tabella hash fosse un semplice array di valori, il secondo inserimento sovrascriverebbe il primo. Occorre quindi una strategia per ospitare più coppie chiave-valore che ricadono nello stesso secchio.

La strategia più diffusa e lineare da implementare in C è il **concatenamento** (*separate chaining*): ciascun elemento dell'array `secchi` non contiene direttamente una coppia chiave-valore, ma è un puntatore alla testa di una lista semplicemente concatenata (capitolo 17) che raccoglie tutti i nodi finiti in quel secchio. L'array dei secchi è quindi un array dinamico di puntatori a nodo, di tipo `nodo_t **secchi`, allocato sullo heap con tutti gli elementi inizializzati a `nullptr`.

```text
tabella_t:
  cap = 4, len = 3
  secchi -----> [0] ---> ["mela" | 5 | *] ---> nullptr
                [1] ---> ["kiwi" | 2 | *] ---> ["uva" | 4 | *] ---> nullptr
                [2] ---> nullptr
                [3] ---> nullptr
```

In questo schema `"kiwi"` e `"uva"` hanno prodotto entrambe l'indice di secchio `1`, quindi convivono nella catena collegata a `secchi[1]`. I secchi `2` e `3` sono vuoti (`nullptr`). Se la funzione di hash distribuisce bene le chiavi e il numero di secchi è proporzionato al numero di elementi, la maggior parte delle catene contiene zero, uno o due nodi, e ogni operazione esamina pochissimi elementi.

### Le quattro operazioni fondamentali

Ogni operazione su una tabella hash con concatenamento inizia calcolando `size_t idx = (size_t)(hash_fnv1a(chiave) % t->cap);` (con `t->cap > 0`) e lavorando poi **solo** sulla catena `t->secchi[idx]`:

1. **Ricerca**: scorre la catena `t->secchi[idx]` con un puntatore `const nodo_t *curr`. A ogni nodo confronta la chiave con `strcmp(curr->chiave, chiave) == 0`. Se trova corrispondenza restituisce il nodo (o il valore); se raggiunge `nullptr`, la chiave non è presente.
2. **Inserimento con semantica dizionario**: una tabella hash non ammette chiavi duplicate. Prima di allocare qualsiasi cosa, scorre la catena `t->secchi[idx]` per verificare se `chiave` esiste già. Se la trova, aggiorna semplicemente il campo `valore` sul nodo esistente e termina senza modificare `t->len` né allocare memoria. Se la chiave non è presente, alloca un nuovo nodo con `malloc`, duplica la stringa della chiave con `strdup(chiave)` (così la tabella possiede una propria copia indipendente dal buffer del chiamante), collega il nodo in testa alla catena (`n->prox = t->secchi[idx]; t->secchi[idx] = n;`) e incrementa `t->len`. Se `strdup` fallisce dopo che `malloc` per il nodo ha avuto successo, occorre liberare subito il nodo con `free(n)` prima di segnalare errore, evitando perdite di memoria.
3. **Rimozione**: applica esattamente la tecnica del puntatore a puntatore vista nel capitolo 17. Partendo da `nodo_t **cur = &t->secchi[idx];`, si avanza finché `*cur != nullptr && strcmp((*cur)->chiave, chiave) != 0` tramite `cur = &(*cur)->prox;`. Se `*cur` raggiunge `nullptr`, la chiave non esiste. Altrimenti si salva `nodo_t *da_lib = *cur;`, si aggiorna il puntatore con `*cur = da_lib->prox;` (che aggiorna automaticamente `t->secchi[idx]` se il nodo era il primo della catena, oppure `prec->prox` se era un nodo interno), si liberano `da_lib->chiave` e `da_lib`, e si decrementa `t->len`.
4. **Distruzione completa**: scorre tutti i secchi da `0` a `t->cap - 1`. Per ciascuna catena salva sempre `nodo_t *prossimo = curr->prox;` **prima** di chiamare `free(curr->chiave);` e `free(curr);`, altrimenti leggere `curr->prox` dopo `free(curr)` causerebbe un uso dopo la liberazione. Al termine del ciclo sui secchi libera l'array `free(t->secchi);` e azzera i campi della struttura (`t->secchi = nullptr; t->cap = 0; t->len = 0;`).

Riassumiamo la regola precisa:

- In una tabella hash con concatenamento l'array dei secchi ha tipo `nodo_t **secchi` (allocato sullo heap con tutti gli elementi inizializzati a `nullptr`), e ciascun secchio è la testa di una lista semplicemente concatenata.
- Inserimento, ricerca e rimozione operano sulla sola catena `secchi[idx]`: l'inserimento di una chiave già presente aggiorna il valore senza creare duplicati; la rimozione tramite puntatore a puntatore `nodo_t **cur = &t->secchi[idx]` unifica il caso del primo nodo e dei nodi interni; la distruzione libera ogni catena salvando `curr->prox` prima di liberare chiave e nodo, poi libera l'array `secchi`.

Secondo lo standard C23, l'inizializzazione esplicita di ogni puntatore `secchi[i] = nullptr` e la gestione delle catene sono completamente definite; al contrario, accedere a `secchi` con un indice fuori dai limiti o leggere `curr->prox` dopo `free(curr)` provoca **comportamento indefinito**.

> **Nota sull'indirizzamento aperto** — Il concatenamento non è l'unica strategia per risolvere le collisioni. Nell'*indirizzamento aperto* (*open addressing*), tutte le coppie risiedono direttamente dentro l'array dei secchi senza liste esterne: se il secchio `idx` è occupato, si esplora una sequenza di secchi alternativi (per esempio `idx + 1`, `idx + 2`, ..., modulo `cap`). Questa tecnica riduce le allocazioni e tiene i dati contigui in memoria, ma rende più delicata la rimozione (che richiede marcatori speciali di cella cancellata) e impone che il numero di elementi resti sempre strettamente inferiore alla capacità. In questo capitolo useremo il concatenamento, più chiaro e modulare per costruire una tabella generica.

### Esempio guidato

Il programma seguente realizza una piccola rubrica telefonica aziendale (`nome -> numero interno`) basata su una tabella hash a `8` secchi fissi con concatenamento. Inserisce quattro contatti (tra cui `"anna"` e `"piero"`, oppure altre coppie che collidono nello stesso secchio), aggiorna un interno esistente, cerca contatti presenti e assenti, rimuove nodi da una catena e distrugge la tabella in modo pulito.

<!-- cod: id=18.2-a tipo=programma -->
```c
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct voce { char *nome; int interno; struct voce *prox; } voce_t;
typedef struct rubrica { voce_t **secchi; size_t cap; size_t len; } rubrica_t;

uint64_t hash_fnv1a(const char *s) {
    uint64_t h = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char *)s; *p != '\0'; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return h;
}

bool rubrica_init(rubrica_t *r, size_t cap) {
    r->secchi = malloc(cap * sizeof(*r->secchi));
    if (r->secchi == nullptr) { return false; }
    for (size_t i = 0; i < cap; ++i) { r->secchi[i] = nullptr; }
    r->cap = cap; r->len = 0;
    return true;
}

bool rubrica_imposta(rubrica_t *r, const char *nome, int interno) {
    size_t idx = (size_t)(hash_fnv1a(nome) % r->cap);
    for (voce_t *c = r->secchi[idx]; c != nullptr; c = c->prox) {
        if (strcmp(c->nome, nome) == 0) { c->interno = interno; return true; }
    }
    voce_t *v = malloc(sizeof(*v));
    if (v == nullptr) { return false; }
    v->nome = strdup(nome);
    if (v->nome == nullptr) { free(v); return false; }
    v->interno = interno; v->prox = r->secchi[idx];
    r->secchi[idx] = v; ++r->len;
    return true;
}

const voce_t *rubrica_cerca(const rubrica_t *r, const char *nome) {
    size_t idx = (size_t)(hash_fnv1a(nome) % r->cap);
    for (const voce_t *c = r->secchi[idx]; c != nullptr; c = c->prox) {
        if (strcmp(c->nome, nome) == 0) { return c; }
    }
    return nullptr;
}

bool rubrica_rimuovi(rubrica_t *r, const char *nome) {
    size_t idx = (size_t)(hash_fnv1a(nome) % r->cap);
    voce_t **cur = &r->secchi[idx];
    while (*cur != nullptr && strcmp((*cur)->nome, nome) != 0) { cur = &(*cur)->prox; }
    if (*cur == nullptr) { return false; }
    voce_t *da_lib = *cur; *cur = da_lib->prox;
    free(da_lib->nome); free(da_lib); --r->len;
    return true;
}

void rubrica_distruggi(rubrica_t *r) {
    for (size_t i = 0; i < r->cap; ++i) {
        for (voce_t *c = r->secchi[i]; c != nullptr; ) {
            voce_t *prossimo = c->prox; free(c->nome); free(c); c = prossimo;
        }
    }
    free(r->secchi); r->secchi = nullptr; r->cap = 0; r->len = 0;
}

int main(void) {
    rubrica_t rub = {};
    if (!rubrica_init(&rub, 8)) { return 1; }
    rubrica_imposta(&rub, "roma", 101); rubrica_imposta(&rub, "cane", 102);
    rubrica_imposta(&rub, "amor", 204); rubrica_imposta(&rub, "roma", 199);
    const voce_t *v1 = rubrica_cerca(&rub, "roma"), *v2 = rubrica_cerca(&rub, "luca");
    printf("roma -> %d, luca -> %s, len=%zu\n", v1->interno, v2 ? "trovato" : "assente", rub.len);
    printf("rimuovi cane: %s\n", rubrica_rimuovi(&rub, "cane") ? "ok" : "no");
    printf("rimuovi roma: %s, len=%zu\n", rubrica_rimuovi(&rub, "roma") ? "ok" : "no", rub.len);
    rubrica_distruggi(&rub);
    return 0;
}
```

```output
roma -> 199, luca -> assente, len=3
rimuovi cane: ok
rimuovi roma: ok, len=1
```

Osserva i punti chiave dell'esempio:

- `"roma"` e `"cane"` producono entrambe l'indice di secchio `0` modulo `8` con FNV-1a: `"cane"` viene inserito in testa alla catena di `secchi[0]`, seguito da `"roma"`.
- La seconda chiamata `rubrica_imposta(&rub, "roma", 199);` trova `"roma"` nella catena `secchi[0]` e ne aggiorna il campo `interno` da `101` a `199` senza allocare un nuovo nodo e lasciando `len` uguale a `3`.
- Quando `rubrica_rimuovi` elimina prima `"cane"` (in testa alla catena di `secchi[0]`) e poi `"roma"` (diventato unico elemento della catena), lo stesso ciclo su `voce_t **cur = &r->secchi[idx];` gestisce entrambi i casi senza rami speciali.
- Infine `rubrica_distruggi` rilascia il nodo rimasto (`"amor"`) e l'array `secchi`, azzerando la struttura.

> **Approfondimento — Perché inizializzare `secchi` con `malloc` e un ciclo a `nullptr`**
> Molti programmi C allocano array di puntatori con `calloc`, che azzera tutti i byte a `0`. Sulle piattaforme moderne la rappresentazione in memoria di `nullptr` coincide effettivamente con tutti bit a zero, ma lo standard C non lo impone in generale: su architetture storiche il puntatore nullo poteva avere una rappresentazione diversa. Allocare con `malloc(cap * sizeof(*r->secchi))` e scrivere un ciclo esplicito `for (size_t i = 0; i < cap; ++i) { r->secchi[i] = nullptr; }` è completamente portabile secondo lo standard C23 e rende esplicita l'intenzione a chi legge il codice.

### Esercizio 18.2 — Contatore di frequenze su tabella hash con concatenamento e ispezione dei secchi

**Descrizione**

Scrivi un programma C che implementi una tabella hash a capacità fissa con risoluzione delle collisioni per concatenamento per contare le frequenze di parole chiave. Definisci `typedef struct nodo_freq { char *chiave; int64_t conteggio; struct nodo_freq *prox; } nodo_freq_t;` e `typedef struct tab_freq { nodo_freq_t **secchi; size_t cap; size_t len; } tab_freq_t;`. Usa la funzione di hash FNV-1a a `64` bit su `unsigned char` (`offset = 14695981039346656037ULL`, `primo = 1099511628211ULL`) e implementa cinque funzioni:

1. `bool tab_init(tab_freq_t *t, size_t cap)` che alloca `t->secchi` con `malloc` (controllando `cap >= 1 && cap <= 64`) e inizializza esplicitamente ogni `t->secchi[i] = nullptr`;
2. `int tab_aggiungi(tab_freq_t *t, const char *chiave, int64_t delta, size_t *secchio_out, int64_t *val_out)` che cerca `chiave` nel secchio `idx = (size_t)(hash_fnv1a(chiave) % t->cap)`: se presente somma `delta` al `conteggio` e restituisce `0` (aggiornato); se assente alloca nodo e copia della chiave con `strdup`, inserisce in testa a `t->secchi[idx]`, incrementa `t->len` e restituisce `1` (inserito), oppure `-1` se l'allocazione fallisce senza perdere memoria;
3. `const nodo_freq_t *tab_cerca(const tab_freq_t *t, const char *chiave)`;
4. `bool tab_rimuovi(tab_freq_t *t, const char *chiave)` che rimuove il nodo tramite puntatore a puntatore `nodo_freq_t **cur = &t->secchi[idx];` liberando `chiave` e nodo;
5. `void tab_distruggi(tab_freq_t *t)` che libera tutte le catene, `t->secchi` e azzera i campi.

In `main` leggi dalla prima riga `cap` (`1 <= cap <= 64`), poi leggi comandi da `stdin` fino a fine input: `INC <parola> <delta>` (`delta > 0`), `GET <parola>`, `DEL <parola>` e `DUMP` (che stampa i secchi non vuoti in ordine di indice oppure `  (vuota)` se `len == 0`), producendo esattamente l'output dell'esempio.

**Concetti da tenere a mente**

- array dinamico di secchi `nodo_freq_t **secchi` con inizializzazione esplicita a `nullptr`
- gestione delle collisioni tramite liste semplicemente concatenate per secchio
- aggiornamento in-place su chiave duplicata e duplicazione con `strdup` solo su nuovo inserimento
- rimozione uniforme di testa e nodi interni di una catena con `nodo_freq_t **cur`
- distruzione completa salvando `curr->prox` prima di liberare chiave e nodo

**Domande guida**

1. Che cosa succede se in `tab_aggiungi` l'allocazione di `strdup(chiave)` fallisce dopo che `malloc` per il nodo è riuscita?
2. Perché nella rimozione dentro una catena del secchio `idx` conviene usare `nodo_freq_t **cur = &t->secchi[idx];`?
3. Come si comporta la tabella nel caso limite `cap == 1` con più chiavi diverse e perché è un ottimo banco di prova per le collisioni?
4. In che ordine devi liberare `curr->chiave`, `curr` e `t->secchi` in `tab_distruggi` per evitare sia perdite di memoria sia uso dopo la liberazione?

**Esempio di esecuzione**

```input
4
INC mela 2
INC pera 1
INC mela 3
INC uva 4
INC kiwi 2
DUMP
GET mela
GET pesca
DEL mela
DEL pesca
DUMP
```

```output
INS mela=2 (secchio=0)
INS pera=1 (secchio=3)
UPD mela=5 (secchio=0)
INS uva=4 (secchio=1)
INS kiwi=2 (secchio=1)
Tabella (len=4, cap=4):
  [0]: mela=5
  [1]: kiwi=2 -> uva=4
  [3]: pera=1
GET mela: 5
GET pesca: NON TROVATO
DEL mela: OK
DEL pesca: NON TROVATO
Tabella (len=3, cap=4):
  [1]: kiwi=2 -> uva=4
  [3]: pera=1
```
