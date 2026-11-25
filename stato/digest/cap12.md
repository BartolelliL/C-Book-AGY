# Digest — Capitolo 12: Strutture, enumerazioni, typedef

## Termini definiti e glossario
- **Struttura** (*struct*): tipo aggregato definito con `struct` che raggruppa più campi, anche di tipi diversi, sotto un unico nome.
- **Campo** (*field*): ogni singola variabile dichiarata all'interno di una `struct` (o `union`).
- **Operatore punto** (`.`): seleziona un campo di una variabile struttura (`s.campo`).
- **Enumerazione** (*enumeration*, `enum`): tipo intero che associa nomi simbolici a un insieme finito di costanti intere.
- **Operatore freccia** (`->`): combina dereferenziazione e accesso al campo per un puntatore a struttura (`p->campo` equivale a `(*p).campo`).
- **Letterale composto** (*compound literal*): espressione `(tipo_t){.campo = valore}` che crea al volo un oggetto struttura senza nome (durata automatica nel blocco).
- **Copia superficiale** (*shallow copy*) vs **copia profonda** (*deep copy*): assegnamento `=` copia il valore del puntatore (condividendo il blocco sullo heap) vs clonazione indipendente dei blocchi puntati.
- Altri termini del glossario usati: `typedef`, struttura annidata, inizializzatore designato, comportamento indefinito, comportamento dipendente dall'implementazione.

## Concetti spiegati
- `struct tag { ... };`: `;` finale obbligatorio, campi disposti nell'ordine dichiarato, `sizeof(struct tag)` >= somma dimensioni campi. Inizializzazione posizionale, designata (`.campo = v`), parziale e vuota `{}` (C23; `{0}` in C17/C11). Leggere campi di `struct` automatica non inizializzata è comportamento indefinito.
- `enum`: costanti in MAIUSCOLO con prefisso comune (visibili nello spazio dei nomi esterno), valori da `0` o espliciti, abbinamento con `switch`. C23: tipo sottostante fisso `enum tag : int { ... };` (senza, è dipendente dall'implementazione).
- `typedef`: crea un sinonimo, non un tipo distinto; suffisso `_t` evitando nomi riservati dallo standard; mantenere sempre il tag della `struct` e non nascondere `*` dentro `typedef` (eccetto tipi opachi).
- Puntatori a `struct`: `->` (precedenza maggiore di `*` e `&`, quindi `&p->campo` vale `&(p->campo)` e `*p.x` è errore); controllo `p != nullptr` prima di `->`; `malloc(sizeof(*p))` per allocare una singola `struct` sullo heap.
- Array di `struct` (sullo stack o dinamici con `realloc(arr, ncap * sizeof(*arr))`), strutture annidate (`p->data.anno`, non può contenere sé stessa per valore), rilascio dall'interno verso l'esterno (prima `free(arr[i].campo_ptr)` poi `free(arr)`).
- Copia/passaggio/restituzione: `=` copia anche array interni; `==` e `!=` vietati tra `struct` (scrivere funzione campo per campo); passaggio per valore per piccole `struct` (1–3 scalari), `const tipo_t *` per grandi/array; mai restituire l'indirizzo di un letterale composto.

## Esempi e scenari
- **12.1**: `struct rilevazione_meteo` (`monte`, `valle`, confronto `somma_campi` vs `sizeof`).
- **12.2**: `priorita_t` (C23 `: int`) e `ticket_t` (`nome_priorita`, `ore_risposta`).
- **12.3**: `conto_t` (`deposita`, `preleva`, `stampa_conto`, conto su stack e conto su heap).
- **12.4**: array dinamico `articolo_t *cat` con `dimensioni_t dim` annidata e `char *titolo` (`libera_catalogo`).
- **12.5**: `vettore2d_t` (`somma_vettori`, `vettore_uguale`) e `nota_t` (`clona_nota`).

## Esercizi
- **12.1 — Gestione di un lotto di magazzino con struct e inizializzatori designati**: `struct lotto_merce` con movimenti `CARICO`/`SCARICO` e confronto con `riferimento`. Difficoltà: 2/5.
- **12.2 — Smistamento di pacchi postali con enum e typedef**: `zona_t` (`: int` C23) e `pacco_t`, tariffe con `switch` e conteggi per zona. Difficoltà: 2/5.
- **12.3 — Controllo di un'unità batteria tramite puntatori a struct e operatore ->**: `batteria_t`, `ricarica_batteria`, `scarica_batteria`, `stampa_batteria` con `->` e `nullptr`. Difficoltà: 3/5.
- **12.4 — Registro dinamico di eventi con struct annidate e stringhe sullo heap**: `orario_t` in `evento_t` con `char *titolo` in array dinamico `realloc` + `strdup`. Difficoltà: 4/5.
- **12.5 — Operazioni su intervalli per valore, letterali composti e copia profonda di fasce**: `intervallo_t` per valore con letterali composti e `fascia_t` con `clona_fascia`. Difficoltà: 3/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 3–4, 8–11.
- Rinvii in avanti: cap. 13 (`union` e padding/allineamento in memoria); cap. 17 (`struct` autoreferenziali con puntatori per liste e alberi); cap. 19 (tipi opachi con `typedef`).

## Affermazioni forti
- Mantenere sempre l'etichetta della `struct` nei `typedef` e non nascondere puntatori dentro `typedef`.
- Non stimare mai a mano `sizeof(struct ...)`: usare sempre `sizeof`.
- Controllare sempre `p != nullptr` prima di usare `->`.
- Liberare sempre i campi puntatore interni prima di liberare la `struct` o l'array che li contiene.
- Mai restituire l'indirizzo di un letterale composto al chiamante.

## Stile del codice
- Standard C23 (`{}`, `enum tag : int`, `nullptr`, `bool`, `strdup`).
- Suffisso `_t` per i tipi utente (`punto_t`, `conto_t`); costanti `enum` in MAIUSCOLO con prefisso comune.
