## 17.5 Regole di possesso della memoria e distruzione

Finché i nodi di una lista o di un albero contengono solo valori semplici come `int` o array a dimensione fissa dentro la `struct`, liberare la struttura è lineare: basta chiamare `free` su ogni nodo. Nei programmi reali, però, i contenitori generici basati su `void *` memorizzano puntatori a stringhe allocate con `strdup`, a `struct` con campi dinamici annidati, oppure a oggetti già posseduti da un'altra parte del programma. Se non decidi prima chi deve chiamare `free` su quei dati, finisci in uno di tre difetti: nessuno li libera (perdita di memoria), li liberano in due (doppia liberazione), oppure uno li libera mentre l'altro li sta ancora usando (puntatore pendente e uso dopo la liberazione).

Per eliminare l'ambiguità si definisce il **possesso della memoria** (*ownership*): un contratto chiaro che stabilisce quale modulo o struttura dati è responsabile di liberare un blocco allocato dinamicamente. La regola di fondo è semplice ma inderogabile: **ogni blocco allocato sullo heap deve avere un solo proprietario alla volta**, e solo il proprietario può chiamare `free` su quel blocco.

### I tre contratti di possesso per un contenitore generico

Quando progetti un contenitore generico su `void *` (come una lista generica o, presto, una tabella hash), puoi scegliere tra tre contratti ben distinti:

1. **Trasferimento di possesso**: il chiamante alloca l'oggetto sullo heap e lo consegna al contenitore; da quel momento il contenitore diventa il proprietario e si occupa di liberarlo alla rimozione o alla distruzione. Il chiamante non deve più chiamare `free` su quel puntatore.
2. **Copia (clonazione)**: il contenitore duplica il dato al momento dell'inserimento (per esempio con `strdup` o una callback di copia) e possiede la propria copia; il chiamante resta proprietario dell'originale e può modificarlo o liberarlo liberamente.
3. **Prestito (*borrowing*)**: il contenitore memorizza solo puntatori a oggetti posseduti altrove (sullo stack o dentro un altro contenitore proprietario) e **non libera mai** i dati puntati, ma solo i propri nodi interni.

### La callback distruttore e la convenzione `nullptr`

Un contenitore generico non conosce il tipo concreto nascosto dietro `void *`, quindi non sa se per liberare un dato basti `free(dato)` (come per una stringa di `strdup`) o se occorra prima liberare campi dinamici annidati dentro una `struct`. La soluzione idiomatica in C combina `void *` (capitolo 15) e callback (capitolo 16) definendo un tipo di funzione distruttore:

<!-- cod: id=17.5-b tipo=frammento -->
```c
typedef void (*distruggi_fn)(void *dato);
```

Il descrittore del contenitore memorizza il puntatore `distruggi_fn distruggi;`, ricevuto all'inizializzazione:

- Se il contenitore è **proprietario** di blocchi semplici (per esempio stringhe allocate con `strdup`), passi direttamente `free`, la cui firma `void free(void *)` coincide esattamente con `distruggi_fn`.
- Se il contenitore è **proprietario** di `struct` con risorse annidate sullo heap, passi una funzione dedicata (per esempio `distruggi_documento`) che libera prima i campi interni e solo alla fine la `struct` stessa.
- Se il contenitore opera in modalità **prestito**, passi `nullptr`: alla rimozione e alla distruzione il contenitore controlla `if (l->distruggi != nullptr) { l->distruggi(curr->dato); }` prima di `free(curr)`, liberando così soltanto i propri nodi.

> **C23** — La funzione `strdup` di `<string.h>` è stata standardizzata in C23. Con compilatori che supportano solo C11 o C17 in modalità stretta, puoi duplicare una stringa allocando `strlen(s) + 1` byte con `malloc` e copiando con `memcpy`.

### Ordine di distruzione ed errori di allocazione

Due regole operative completano il contratto:

- **Ordine di distruzione tra proprietario e viste in prestito**: se hai un contenitore proprietario (`lista_prop`) e una seconda struttura in prestito (`lista_vista`) che punta a un sottoinsieme degli stessi oggetti, devi sempre distruggere `lista_vista` **prima** di rimuovere elementi da `lista_prop` o di distruggere `lista_prop`. In caso contrario i nodi di `lista_vista` conserverebbero puntatori pendenti verso memoria già liberata.
- **Fallimento di allocazione durante l'inserimento**: se `inserisci(contenitore, dato)` fallisce perché `malloc` per il nuovo nodo restituisce `nullptr`, il contenitore non ha preso in carico `dato`. Il contratto deve stabilire chiaramente che, in caso di errore, **il chiamante conserva la responsabilità** di liberare `dato` per evitare una perdita di memoria nel ramo di errore.

Verifica sistematicamente ogni programma che usa strutture dinamiche compilando con i sanitizer (AddressSanitizer e UndefinedBehaviorSanitizer, capitolo 11): sono la rete di sicurezza che conferma l'assenza di perdite, doppie liberazioni e usi dopo la liberazione. Queste stesse regole di possesso saranno il fondamento della tabella hash generica (lo vedremo nel capitolo 18).

Secondo lo standard C23, l'uso di callback `distruggi_fn` per regolare il possesso della memoria è pienamente definito; liberare lo stesso oggetto sia nel chiamante sia nel contenitore provoca doppia liberazione (**comportamento indefinito**), usarlo dopo la distruzione del proprietario provoca uso dopo la liberazione (**comportamento indefinito**), e non liberarlo da nessuna parte genera una perdita di memoria.

> **Se vieni da Python** — In Python è normale che più strutture condividano riferimenti allo stesso oggetto senza preoccuparsi dell'ordine di distruzione; in C condividere puntatori tra una struttura proprietaria e una vista in prestito richiede di distruggere sempre la vista prima del proprietario per evitare puntatori pendenti e doppie liberazioni.

### Esempio guidato

Il programma seguente definisce una lista generica `lista_gen_t` con nodi `void *` e callback `distruggi_fn`. La usa prima come contenitore proprietario di stringhe duplicate con `strdup` (passando `free` come distruttore) e poi come vista in prestito su `struct` allocate sullo stack (passando `nullptr` come distruttore).

<!-- cod: id=17.5-a tipo=programma -->
```c
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void (*distruggi_fn)(void *dato);

typedef struct nodo_gen { void *dato; struct nodo_gen *prox; } nodo_gen_t;
typedef struct lista_gen { nodo_gen_t *testa; size_t len; distruggi_fn distruggi; } lista_gen_t;
typedef struct sensore { const char *nome; int valore; } sensore_t;

void lg_init(lista_gen_t *l, distruggi_fn distruggi) {
    *l = (lista_gen_t){.testa = nullptr, .len = 0, .distruggi = distruggi};
}

// In caso di fallimento (false), il chiamante resta proprietario di dato.
bool lg_inserisci_testa(lista_gen_t *l, void *dato) {
    nodo_gen_t *n = malloc(sizeof(*n));
    if (n == nullptr) { return false; }
    n->dato = dato;
    n->prox = l->testa;
    l->testa = n;
    ++l->len;
    return true;
}

void lg_distruggi(lista_gen_t *l) {
    nodo_gen_t *curr = l->testa;
    while (curr != nullptr) {
        nodo_gen_t *prossimo = curr->prox;
        if (l->distruggi != nullptr) { l->distruggi(curr->dato); }
        free(curr);
        curr = prossimo;
    }
    l->testa = nullptr;
    l->len = 0;
}

int main(void) {
    lista_gen_t etichette;
    lg_init(&etichette, free);
    const char *parole[] = {"alfa", "beta", "gamma"};
    for (size_t i = 0; i < 3; ++i) {
        char *copia = strdup(parole[i]);
        if (copia == nullptr || !lg_inserisci_testa(&etichette, copia)) {
            free(copia);
            lg_distruggi(&etichette);
            return EXIT_FAILURE;
        }
    }
    printf("Proprietaria (%zu):", etichette.len);
    for (const nodo_gen_t *n = etichette.testa; n != nullptr; n = n->prox) {
        printf(" %s", (const char *)n->dato);
    }
    printf("\n");
    lg_distruggi(&etichette);

    sensore_t sensori[] = {{"T1", 22}, {"T2", 31}, {"T3", 19}};
    lista_gen_t vista;
    lg_init(&vista, nullptr);
    for (size_t i = 0; i < 3; ++i) {
        if (sensori[i].valore >= 20 && !lg_inserisci_testa(&vista, &sensori[i])) {
            lg_distruggi(&vista);
            return EXIT_FAILURE;
        }
    }
    printf("Vista prestito (%zu):", vista.len);
    for (const nodo_gen_t *n = vista.testa; n != nullptr; n = n->prox) {
        const sensore_t *s = n->dato;
        printf(" %s=%d", s->nome, s->valore);
    }
    printf("\n");
    lg_distruggi(&vista);
    return 0;
}
```

```output
Proprietaria (3): gamma beta alfa
Vista prestito (2): T2=31 T1=22
```

Osserva come la stessa implementazione di `lista_gen_t` rispetta entrambi i contratti:

- In `etichette`, passando `free` a `lg_init`, la lista assume il possesso delle copie create con `strdup`: `lg_distruggi(&etichette)` chiama `free(curr->dato)` e poi `free(curr)` per ogni nodo. Se `lg_inserisci_testa` fallisse, `main` chiamerebbe `free(copia)` perché il trasferimento di possesso non è avvenuto.
- In `vista`, passando `nullptr` a `lg_init`, la lista contiene indirizzi di elementi sullo stack (`&sensori[i]`): `lg_distruggi(&vista)` libera soltanto i nodi `nodo_gen_t` e non tenta mai di chiamare `free` su memoria dello stack.

> **Approfondimento — Documentare il contratto di possesso nell'interfaccia**
> Quando il codice cresce su più file, chi usa una libreria non deve essere costretto a leggerne l'implementazione per capire chi libera la memoria. Specificare nei commenti dell'interfaccia chi alloca il dato, chi ne resta proprietario in caso di errore di inserimento e quale distruttore verrà invocato alla chiusura previene perdite di memoria, puntatori pendenti e doppie liberazioni nei progetti modulari su più file (lo vedremo nel capitolo 19).

### Esercizio 17.5 — Lista generica con contratti di possesso espliciti: proprietà profonda tramite distruttore e vista in prestito

**Descrizione**

Scrivi un programma C che implementi una lista generica `typedef struct lista_gen { nodo_gen_t *testa; nodo_gen_t *coda; size_t len; distruggi_fn distruggi; } lista_gen_t;` con nodi `typedef struct nodo_gen { void *dato; struct nodo_gen *prox; } nodo_gen_t;` e callback `typedef void (*distruggi_fn)(void *dato);` e `typedef bool (*pred_dato_fn)(const void *dato, const void *ctx);`. Implementa: `void lg_init(lista_gen_t *l, distruggi_fn distruggi)`, `bool lg_inserisci_coda(lista_gen_t *l, void *dato)` (in caso di errore di allocazione del nodo NON libera `dato`), `size_t lg_rimuovi_se(lista_gen_t *l, pred_dato_fn pred, const void *ctx)` (rimuove tutti i nodi per cui `pred` è vero, chiamando `l->distruggi(nodo->dato)` se non nullo prima di `free(nodo)` e mantenendo coerente `l->coda`) e `void lg_distruggi(lista_gen_t *l)` (libera ogni nodo invocando `l->distruggi` se non nullo e azzera la lista). Definisci una risorsa con campi dinamici annidati `typedef struct documento { char *titolo; int *voti; size_t num_voti; size_t *cont_distrutti; } documento_t;`, una funzione `documento_t *crea_documento(const char *titolo, const int *voti, size_t k, size_t *cont_distrutti)` che duplica `titolo` con `strdup` e copia `voti` in un array `calloc`, `double media_documento(const documento_t *d)` e il distruttore profondo `void distruggi_documento(void *p)` che incrementa `*(d->cont_distrutti)` e libera `d->titolo`, `d->voti` e `d`. In `main` leggi dalla prima riga `n soglia_vista soglia_elim` (`0 <= n <= 16`) e dalle successive `n` righe `<titolo> <k> <v1> ... <vk>` (`1 <= k <= 8`). Inserisci tutti gli `n` documenti creati in `lista_prop` (inizializzata con `distruggi_documento`: proprietaria), poi costruisci `lista_vista` (inizializzata con `nullptr`: prestito!) inserendovi i puntatori ai documenti con `media >= soglia_vista`. Stampa `lista_vista`, distruggila PRIMA di `lista_prop` e verifica che `distrutti == 0`; quindi chiama `lg_rimuovi_se` su `lista_prop` per rimuovere i documenti con `media < soglia_elim`, stampa la lista proprietaria residua, distruggi `lista_prop` e stampa il bilancio `creati`/`distrutti` esattamente come nell'esempio.

**Concetti da tenere a mente**

- contratto di possesso della memoria tramite callback `distruggi_fn` (proprietà) e `nullptr` (prestito)
- distruzione profonda di una `struct` contenente puntatori annidati (`titolo`, `voti` e `struct` stessa)
- ordine di distruzione obbligatorio: distruggere la vista in prestito prima del contenitore proprietario
- mantenimento dell'invariante di `testa` e `coda` durante la rimozione selettiva in una lista generica

**Domande guida**

1. Perché `lista_vista` deve essere distrutta prima che `lista_prop` rimuova elementi o venga distrutta?
2. Che cosa accadrebbe se passassi `distruggi_documento` sia a `lista_prop` sia a `lista_vista`?
3. Perché `lg_inserisci_coda` non libera `dato` se `malloc` per il nodo fallisce, e come si comporta `main` in quel caso?
4. In che ordine deve liberare la memoria `distruggi_documento` per evitare sia perdite di memoria sia uso dopo la liberazione?

**Esempio di esecuzione**

```input
3 25.0 20.0
RelazioneA 3 28 30 26
BozzaB 2 18 16
TesinaC 2 22 24
```

```output
Vista prestito (>= 25.00, len=1): RelazioneA(28.00)
Dopo distruzione vista: distrutti=0
Rimossi (< 20.00): 1 (distrutti=1)
Proprietaria residua (len=2): RelazioneA(28.00) TesinaC(23.00)
Fine programma: creati=3 distrutti=3
```
