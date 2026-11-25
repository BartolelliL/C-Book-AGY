# Digest — Capitolo 19: Programmi su più file

## Termini definiti e glossario
- **File di intestazione** (*header file*, `.h`): file che espone l'interfaccia pubblica di un modulo tramite sole dichiarazioni di tipi, costanti e prototipi.
- **Unità di traduzione** (*translation unit*): singolo file sorgente `.c` dopo l'espansione di tutti gli `#include` e delle direttive del preprocessore.
- **Compilazione separata** (*separate compilation*): compilazione indipendente di ciascun file `.c` in un file oggetto (`.o`/`.obj`), seguita dal collegamento finale.
- **Protezione di inclusione** (*include guard*): coppia di direttive `#ifndef NOME_H` / `#define NOME_H` / `#endif` che impedisce l'inclusione multipla dello stesso header in una unità di traduzione.
- **Compilazione condizionale**: inclusione o esclusione di blocchi di codice tramite `#ifdef`, `#ifndef`, `#if`, `#elif`, `#else`, `#endif` e `defined(...)`.
- **Collegamento** (*linkage*): proprietà che stabilisce se un identificatore dichiarato in più unità di traduzione indica la stessa entità (esterno, interno o assente).
- **Tipo opaco** (*opaque type*): struttura dichiarata nell'header in modo incompleto (`typedef struct nome nome_t;`) e definita solo nel file `.c`, accessibile solo tramite puntatore e funzioni.
- Altri termini usati: collegatore, file oggetto, inclusione a diamante, `static`, `extern`, `inline`, `extern inline`, `static inline`, durata di vita, tipo incompleto, violazione di vincolo, comportamento indefinito, lettera composta, inizializzatore designato.

## Concetti spiegati
- Separazione interfaccia (`.h`) / implementazione (`.c`); `#include <...>` vs `#include "..."`; regola d'oro di includere `"modulo.h"` come prima direttiva di `modulo.c` per verificare autosufficienza e firme.
- Protezioni di inclusione standard rispetto a `#pragma once` (non standard ISO C23), divieto di prefissi riservati `__...` o `_Maiuscola`; uso di `constexpr`/`const` vs `#define`/`#undef` e flag `-DNOME=VALORE`.
- Tre tipi di collegamento: esterno (predefinito a livello di file), interno (`static` a livello di file, distinto da `static` locale), assente (variabili locali/parametri); costanti condivise con `extern const`; funzioni `inline` negli header (`static inline` oppure `inline` + `extern inline` in esattamente un `.c`).
- Incapsulamento tramite tipi opachi: operazioni lecite (`nome_t *`, `const nome_t *`) e illecite fuori dal `.c` (allocazione sullo stack, `sizeof`, accesso con `->`), costruttore sullo heap, distruttore tollerante a `nullptr`, prefissi uniformi.
- Organizzazione della tabella hash generica come libreria opaca (`tabella_hash.h` / `tabella_hash.c`) con `ht_esito_t`, `ht_config_t`, `static bool ht_ridimensiona` e callback per stringhe.

## Esempi e scenari
- `19.1-a/b/c` (`geometria.h`, `geometria.c`, `main.c`): modulo geometria 2D (`punto_t`, `rettangolo_t`, `-lm`).
- `19.2-a/c/d/e` (`tipi.h`, `filtro.h`, `filtro.c`, `main.c`): inclusione a diamante e `LIVELLO_LOG`.
- `19.3-a/c/d` (`contatore.h`, `contatore.c`, `main.c`): `extern const SOGLIA_MASSIMA`, `static`, `static inline`, `inline` + `extern inline` con puntatore a funzione.
- `19.4-a/c/d` (`pila.h`, `pila.c`, `main.c`) + `19.4-e` (`tipo=errore`): pila opaca di `int32_t` e violazione con `sizeof`/`->`.
- `19.5-a/b/c` (`tabella_hash.h`, `tabella_hash.c`, `main.c`): libreria tabella hash opaca usata per parametri di sistema (`int32_t *`) con `ht_config_t` e `ht_estrai`.

## Esercizi
- **19.1 — Modulo di aritmetica razionale su più file con separazione tra interfaccia e implementazione**: `razionale.h`/`razionale.c`/`main.c` con `NORM`/`ADD`/`MUL`/`CMP` e riduzione MCD. Difficoltà: 3/5.
- **19.2 — Architettura a diamante con protezioni di inclusione e configurazione tramite direttive del preprocessore**: `misura.h`/`statistica.h`/`statistica.c`/`main.c` con `LIVELLO_PRECISIONE` e `#undef`. Difficoltà: 3/5.
- **19.3 — Moduli con helper `static` omonimi, tabelle `extern const` e funzioni `static inline` / `extern inline`**: 5 file (`valuta`, `imposta`, `main`) con helper `static applica_fattore` omonimi. Difficoltà: 4/5.
- **19.4 — Buffer circolare a sovrascrittura incapsulato come tipo opaco**: `anello.h`/`anello.c`/`main.c` con `PUSH`/`POP`/`PEEK`/`CLEAR`/`STAT`/`DUMP`. Difficoltà: 4/5.
- **19.5 — Libreria opaca `tabella_hash` su più file con doppio indice (proprietario e in prestito)**: `tabella_hash.h`/`tabella_hash.c`/`main.c` con `per_matricola` (proprietaria) e `per_nome` (prestito). Difficoltà: 5/5.

## Rinvii
- Richiami a capitoli precedenti: cap. 1 (fasi della traduzione), cap. 2 (`const`, `constexpr`), cap. 7 (prototipi, visibilità, durata di vita), cap. 12 (`struct`, `enum`), cap. 16 (puntatori a funzione, callback), cap. 18 (tabella hash generica e possesso della memoria).
- Rinvii in avanti: cap. 21 (macro con argomenti), cap. 26 (progetto finale: interprete).

## Affermazioni forti
- Non inserire definizioni di funzioni normali (non `inline`, non `static`) o variabili globali non-`static` negli header `.h`.
- Includere sempre `"modulo.h"` come prima riga di `modulo.c`.
- Nomi di protezioni di inclusione con `__` o `_Maiuscola` sono riservati e causano comportamento indefinito.
- Dichiarare nell'header un prototipo incompatibile con la definizione nel `.c`, o fornire definizioni `inline` diverse tra unità di traduzione, provoca comportamento indefinito.
- Applicare `sizeof` o `->` a un tipo incompleto fuori dal `.c` che lo definisce è rifiutato dal compilatore (violazione di vincolo).

## Stile del codice
- Standard C23 (`nullptr`, `bool`, `strdup`, `{}`, `<stdint.h>`, `<inttypes.h>`), box `> **C23**` in 19.5.
- Prefissi di modulo uniformi (`geo_`, `raz_`, `pila_`, `anello_`, `ht_`), protezioni `NOME_H` in maiuscolo, `snake_case` italiano, indentazione 4 spazi, `EXIT_SUCCESS`/`EXIT_FAILURE` o `0`.
- Distruttori tolleranti a `nullptr` (`if (t == nullptr) { return; }`), validazione di puntatori e parametri `nullptr` in tutte le API pubbliche.
