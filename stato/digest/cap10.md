# Digest — Capitolo 10: Puntatori

## Termini definiti e glossario
- **Indirizzo di memoria** (*memory address*): posizione numerica che identifica un byte o l'inizio di un oggetto nella memoria del programma.
- **Puntatore** (*pointer*): variabile che memorizza l'indirizzo di memoria di un oggetto o di una funzione, oppure il valore nullo.
- **Operatore indirizzo** (`&`, *address-of operator*): ricava l'indirizzo di un oggetto in memoria (`T *`).
- **Dereferenziazione** (*dereferencing*, `*`): operazione che segue il puntatore per accedere in lettura o scrittura all'oggetto puntato.
- **Puntatore nullo** (*null pointer*): puntatore con valore `nullptr` (C23) o `NULL` che indica esplicitamente di non puntare ad alcun oggetto valido.
- **Decadimento di array** (*array decay*): conversione automatica del nome di un array `T[N]` in puntatore `T *` al primo elemento (`&a[0]`).
- **Aritmetica dei puntatori** (*pointer arithmetic*): somma/sottrazione tra puntatori e interi scalata per `sizeof(*p)`, e sottrazione tra due puntatori allo stesso array (`ptrdiff_t`).
- **Passaggio per puntatore**: tecnica che passa l'indirizzo di un oggetto (copiato per valore) per modificare variabili del chiamante o restituire più risultati tramite **parametri di uscita** (*output parameters*).
- Altri termini del glossario usati: `ptrdiff_t`, comportamento indefinito, comportamento dipendente dall'implementazione, valutazione a corto circuito.

## Concetti spiegati
- Dichiarazione `T *p` (l'asterisco si lega al singolo identificatore: `int* a, b;` dichiara un solo puntatore); `sizeof(p)` uguale tra puntatori a tipi diversi sullo stesso sistema; confronto tra puntatori con `==`/`!=`.
- `nullptr` (C23, tipo `nullptr_t`, non si converte a `int`) vs `NULL`; divieto assoluto di dereferenziare `nullptr`, controllo `p != nullptr && ...` con corto circuito.
- Decadimento di array ed eccezioni (`sizeof(a)`, `&a`, `char buf[] = "ciao"`). Equivalenza `a[i] == *(a + i)`, adattamento dei parametri `T a[]` a `T *a`. Differenza tra array (non riassegnabile) e puntatore (riassegnabile). Letterali stringa sempre in `const char *`.
- Aritmetica dei puntatori su intervallo semiaperto `[inizio, fine)` con `fine = a + n` (lecito formare `a + n`, vietato dereferenziarlo; vietato formare `a - 1` o `a + n + 1`; vietato sottrarre/confrontare con `<` puntatori ad array diversi). `ptrdiff_t` (`<stddef.h>`, `%td`) applicato a `strchr`/`strrchr`/`strstr`.
- Parametri di uscita opzionali (`nullptr`) abbinati a ritorno `bool`; divieto assoluto di restituire `&locale` (indirizzo di variabile automatica).
- Qualificatore `const`: `T *p`, `const T *p`, `T *const p`, `const T *const p` (regola lettura destra->sinistra / sinistra di `const`). Conversione implicita `T * -> const T *` ammessa, inversa no. Preservazione di `const` in C23 per `strchr`/`strrchr`/`strstr`/`strpbrk`.

## Esempi e scenari
- **10.1**: aggiornamento di due contatori `a` e `b` tramite `int *p`.
- **10.2**: `cerca_primo_negativo` su `serie_a`/`serie_b`, verifica `nullptr == NULL`.
- **10.3**: confronto `sizeof(valori)` vs `sizeof(p)`, sotto-sequenza da `&valori[2]`, `const char *messaggio`.
- **10.4**: somma `double misure[]` con `[inizio, fine)` e indici `ptrdiff_t` su `"linguaggio C moderno"`.
- **10.5**: `scambia`, `dividi_sicuro`, `statistiche` (con parametri di uscita opzionali).
- **10.6**: confronto tra `const int *`, `int *const`, `const int *const` ed estrazione estensione con `strrchr` su `const char *percorso`.

## Esercizi
- **10.1 — Controllo di due serbatoi tramite puntatore selettore**: gestire `serbatoio_a` e `serbatoio_b` tramite `double *attivo`. Difficoltà: 2/5.
- **10.2 — Ricerca e correzione sicura con puntatori e `nullptr`**: `trova_massimo` e `trova_primo_oltre_soglia` con modifica tramite `*p_oltre`. Difficoltà: 2/5.
- **10.3 — Finestre scorrevoli su array tramite decadimento e puntatori**: `somma_finestra` e `stampa_sequenza` su `const int *` con finestre di lunghezza `k`. Difficoltà: 3/5.
- **10.4 — Distanze tra delimitatori e inversione di intervalli con aritmetica dei puntatori**: `lunghezza_ptr` e `inverti_intervallo` su `[inizio, fine)` tra prima e ultima occorrenza di `sep`. Difficoltà: 3/5.
- **10.5 — Ordinamento e scomposizione di tempi di gara con passaggio per puntatore**: `scambia_int`, `ordina_tre`, `scomponi_secondi` con parametri opzionali. Difficoltà: 3/5.
- **10.6 — Estrattore di coppie `chiave=valore` con `const`, puntatori e C23**: `trova_valore` (`strchr` con `const`) e `copia_trim` (`char *const dest`, `ptrdiff_t *`). Difficoltà: 4/5.

## Rinvii
- Richiami ai capitoli precedenti: cap. 2, 3, 4, 5, 7, 8, 9.
- Rinvii in avanti: cap. 14 (restituzione puntatori/vita oggetti e `int **` per riassegnare un puntatore del chiamante).

## Affermazioni forti
- Dichiarare sempre un puntatore per riga (`int *a;`) e inizializzare sempre alla dichiarazione (o a `nullptr`).
- Controllare sempre `p != nullptr` prima di dereferenziare.
- Associare sempre i letterali stringa a `const char *`, mai modificarli.
- Non dereferenziare mai `a + n` né formare puntatori fuori da `[a, a + n]`.
- Mai restituire l'indirizzo di una variabile locale automatica.

## Stile del codice
- Standard C23 (`nullptr`, `bool`, preservazione `const` in `<string.h>`, `constexpr` negli esercizi).
- Spazio prima di `*` (`int *p`), `<stddef.h>` incluso per `size_t` e `ptrdiff_t` (`%td`).
