# Digest — Capitolo 25: Qualità e prestazioni

## Termini definiti e glossario
- **Riproducibile** / **indipendente dalla macchina**: confronto tra algoritmi basato sul conteggio esatto delle operazioni elementari anziché sul tempo d'orologio.
- **Adattivo**: comportamento di un algoritmo le cui operazioni variano in base all'ordine iniziale dei dati in ingresso.
- **Cache**: gerarchia di memoria veloce (L1, L2, L3) posta tra registri CPU e RAM.
- **Linea di cache** (*cache line*): blocco contiguo di memoria (tipicamente 64 byte) trasferito insieme dalla RAM alla cache su un *cache miss*.
- **Località dei dati** (*data locality*): proprietà di accedere a indirizzi vicini, distinta in **località spaziale** (indirizzi adiacenti) e **località temporale** (riuso ravvicinato dello stesso dato).
- **Per righe** (*row-major*): memorizzazione contigua per righe degli array multidimensionali in C.
- **Campi freddi**: campi di una `struct` letti raramente rispetto ai campi usati nei cicli caldi.
- **Array di Struct (AoS)** (*Array of Structures*): array in cui ogni elemento è una `struct` completa.
- **Struct di Array (SoA)** (*Structure of Arrays*): `struct` che racchiude un array contiguo separato per ciascun campo.
- **Regola "as-if"**: principio C23 che consente al compilatore di trasformare il codice purché il comportamento osservabile, in assenza di UB, resti identico.
- **Regressioni**: difetti che ricompaiono in codice già collaudato dopo una modifica.
- **Test automatico** (*automated test*): verifica eseguibile ripetibile del comportamento di funzioni e moduli rispetto a risultati attesi e invarianti.
- **Fuzzing**: tecnica di verifica automatica con grandi quantità di input generati casualmente; usa un **seme** fisso (`srand`) e spesso un **test differenziale con oracolo** (confronto passo-passo con un riferimento elementare).
- **Cassetta degli attrezzi professionale**: uso combinato di avvisi severi del compilatore, sanitizer, debugger e profiler.
- **Termini del glossario usati**: *comportamento indefinito* (UB), *dipendente dall'implementazione*, *definito*, `padding`, `strict aliasing`, `restrict`, `nullptr`, `volatile`, *tipo opaco*, `wrap-around`, `overflow`.

## Concetti spiegati
- Conteggio deterministico di confronti, spostamenti e accessi in memoria rispetto ai limiti di `clock()`, `clock_t` e `CLOCKS_PER_SEC` (`<time.h>`); eliminazione del codice morto (*dead-code elimination*) e uso di un pozzo `volatile`.
- Gerarchia di memoria (registri, L1, L2, L3, RAM), *cache hit*/*cache miss*, scansione *row-major* contro *col-major* nelle matrici e confronto quantitativo AoS contro SoA tramite offset logici (`sizeof`, `offsetof`).
- Livelli di ottimizzazione (`-O0`, `-O2`, `-O3`, `-Os`), regola *as-if* ed eliminazione di controlli post-UB (overflow con segno, dereferenziazione prima di `nullptr`, shift fuori intervallo, `strict aliasing`, `restrict`).
- Idiomi sicuri in C23: `<stdckdint.h>` (`ckd_add`, `ckd_sub`, `ckd_mul`), validazione dell'intervallo degli shift senza segno, reinterpretazione dei bit con `memcpy` + `static_assert`, controllo preventivo di disgiunzione con `uintptr_t` prima di `restrict`.
- Mini framework di test automatici su più file: contesto (`mt_ctx_t`/`test_ctx_t`), macro `do { ... } while (0)` con `#` e `__func__`/`__FILE__`/`__LINE__`, runner con puntatori a funzione, limiti di `assert()` (`abort()` e `-DNDEBUG`), criteri di isolamento e copertura dei casi limite.
- Fuzzing a seme fisso (`srand`/`rand`, `static_assert(RAND_MAX >= 32767)`), verifica continua degli invarianti e integrazione con `-Wall -Wextra -Wpedantic -Werror`, `-fsanitize=address,undefined`, `gdb`/`lldb` e profiler (regola del 90%/10%).

## Esempi e scenari
- `25.1-a`: `ricerca_lineare` contro `ricerca_binaria` su 10 000 `int32_t` con `contatori_t` (`confronti`, `accessi`) e ciclo `clock()` protetto da `volatile uint64_t pozzo`.
- `25.2-a`: `punto_aos_t` (64 byte con `static_assert`) contro `punti_soa_t` su 64 punti 3D (`conta_cambi_linea`) e scansione `16 x 16` di `double` per righe contro per colonne.
- `25.3-b`, `25.3-c` (frammenti con UB) e `25.3-a`: `incrementa_sicuro` (`ckd_add`), `leggi_sicuro` (`nullptr`), `aree_disgiunte` (`uintptr_t`) e `scala_e_somma` (`restrict`).
- `25.4-a`/`25.4-b` (`gruppo=demo_test`: `mini_test.h`, `main.c`): `MT_VERO`, `MT_EQ_I32`, `mt_esegui` applicati a `trova_max`, `cerca_bin` e `test_fallimento_dimostrativo`.
- `25.5-a`: fuzzer differenziale (`seme=12345U`) per `ordina_inserzione` contro `qsort` con `confronta_i32`, `invariante_ordinato` e `memcmp`.

## Esercizi
- `25.1` — *Profilatore deterministico di operazioni per algoritmi di ordinamento adattivi e verifica di clock*: confronta Insertion, Shell e Heap Sort su `int32_t` contando confronti, spostamenti e accessi con verifica `memcmp` e `CLOCK_CHECK` (difficoltà: 3/5).
- `25.2` — *Confronto quantitativo AoS contro SoA e scansione di matrici tramite simulatore deterministico di cache*: simulatore LRU a 16 linee da 64 byte su 3 file per `particella_aos_t`, `particelle_soa_t` e matrici (difficoltà: 4/5).
- `25.3` — *Primitive numeriche e vettoriali sicure contro overflow, shift, strict aliasing e violazioni di restrict*: cinque primitive prive di UB (`ckd_add`, `ckd_mul`, shift `uint32_t`, `memcpy` float/uint32, wrapper `uintptr_t` per `restrict`) (difficoltà: 3/5).
- `25.4` — *Mini framework di test automatici su più file applicato a un buffer circolare opaco*: suite su 4 file (`test_fw.h`, `ring_buf.h`, `ring_buf.c`, `main.c`) con `ring_t` e `demo_fallimento` (difficoltà: 4/5).
- `25.5` — *Fuzzer differenziale a seme fisso (srand/rand) con oracolo e verifica di invarianti per una mappa ordinata*: fuzzer su 3 file per `mappa_ord_t` contro un oracolo su array diretto (difficoltà: 4/5).

## Rinvii
- Richiami a capitoli precedenti: 11 (AddressSanitizer), 13 (allineamento e `padding`), 14 (`restrict`), 19 (compilazione separata e tipi opachi), 21 (`assert`, `<stdckdint.h>`, `volatile`, sanitizer), 22 (`strict aliasing`), 23 (complessità asintotica e notazione O), 24 (macro `do-while(0)` e `#`).
- Rinvii in avanti: capitolo 26 in `25_00.md`, `25_04.md` e `25_99.md` ("lo vedremo nel capitolo 26").

## Affermazioni forti
- Qualsiasi comportamento indefinito annulla ogni garanzia del compilatore sull'intera esecuzione.
- Controllare sempre che né l'istante iniziale né quello finale di `clock()` valgano `(clock_t)-1`; non usare mai un tempo misurato come output atteso deterministico.
- Non scrivere mai controlli di overflow o `nullptr` dopo un potenziale UB; validare sempre gli shift su tipi senza segno prima dell'operazione.
- Non usare `assert()` come unico strumento di test perché termina con `abort()` e scompare con `-DNDEBUG`.
- Nel fuzzing usare sempre un seme fisso, non dipendere dalla sequenza numerica grezza di `rand()` e non usare mai `rand()` per scopi crittografici o di sicurezza.

## Stile del codice
- Standard C23: `constexpr`, `static_assert` a un argomento, `{}`, `bool`/`true`/`false`, `nullptr`, `<stdckdint.h>`.
- Indentazione a 4 spazi, graffe sempre presenti, `static` per funzioni interne, `snake_case` italiano senza accenti, suffisso `_t` per `typedef struct`, costanti e macro in MAIUSCOLO, include guard `NOME_H`, variabili temporanee nelle macro con prefisso `_`, `EXIT_SUCCESS`/`EXIT_FAILURE` nei test.
