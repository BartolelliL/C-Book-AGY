# CONVENZIONI — regole condivise per tutti gli agenti

Questo file va letto per intero all'inizio di OGNI compito. Se un prompt e questo file sembrano
in conflitto, vince questo file e lo segnali nel messaggio finale.

---

## 1. Scheda del libro (parametri modificabili dall'utente)

| Voce | Valore |
|---|---|
| Titolo di lavoro | C - Il linguaggio di programmazione |
| Lingua del libro | Italiano |
| Standard del linguaggio | C23 (ISO/IEC 9899:2024) |
| Lettori | Studenti di 16-18 anni, partono da zero in C. Possono conoscere un altro linguaggio (per esempio Python) ma non e' garantito: ogni concetto va spiegato da zero |
| Traguardo | Autonomia completa in C: il lettore sa scrivere da solo programmi di qualche centinaio di righe su piu' file, con strutture dati dinamiche, senza perdite di memoria e senza comportamento indefinito. Concetto di riferimento: una **tabella hash generica come tipo opaco** (`void *`, puntatori a funzione, regole di possesso della memoria). Vedi `PROGRAMMA.md` |
| Livello | Dal capitolo 13 in poi il libro e' di livello intermedio-avanzato: stesso rigore, meno spiegazioni elementari, esercizi piu' lunghi (40-150 righe), in parte su piu' file |
| Sistema operativo dei lettori | Variabile (macOS, Linux, Windows): niente istruzioni legate a un solo sistema; nessuna dipendenza da un IDE specifico |
| Soluzioni degli esercizi | NON compaiono nel libro. Le soluzioni di riferimento esistono solo nei blueprint (per verificare gli esercizi) e nel file separato `docente/soluzioni_commentate.md` |
| Progetto finale | Un progetto di difficolta' alta nell'ultimo capitolo (un interprete per un piccolo linguaggio), diviso in fasi, con test automatici |
| Sotto-sezioni per capitolo | Da 3 a 6, ognuna con teoria, esempio guidato, esercizio |
| Forma di cortesia | Seconda persona singolare ("tu") |
| Identificatori nel codice | In italiano, senza accenti, `snake_case` (es. `somma_totale`); le parole chiave e la libreria restano quelle del C |
| Fonti | Nessun documento da caricare: il contenuto si basa sul linguaggio C e sulla sua libreria standard (C23) |

---

## 2. Regole generali per ogni compito

1. **Leggi prima di scrivere.** Leggi questo file, il prompt del compito e tutti i file di input elencati. Se un file di
   input manca o non e' valido: FERMATI e dillo all'utente (quale file, che cosa manca). Non inventare sostituti.
2. **Scrivi solo dove ti e' permesso** (tabella sotto). Non modificare mai `scripts/`, `prompts/`, `config.json`,
   `CONVENZIONI.md`, `PROGRAMMA.md`, `stato/stato.json`. Nessun agente esegue comandi di avanzamento (vedi i comandi consentiti qui sotto).
3. **`stato/macro_scaletta.json` e' congelata dopo l'approvazione**: nessun agente la modifica.
4. **Ripresa**: se i file di output del tuo compito esistono gia' (sessione interrotta), non rifarli da capo: individua cosa
   manca o cosa e' segnalato come errato e completa/correggi solo quello.
5. **Non dichiarare mai di aver eseguito un comando se non l'hai eseguito.** Se non puoi eseguire comandi, dillo
   chiaramente nel messaggio finale: l'utente lancera' i controlli.
6. **Non inventare.** Se non sei sicuro di un fatto sul linguaggio C o sul comportamento di una funzione, non scriverlo
   come certo: scegli una formulazione che sai essere corretta, oppure segnala il dubbio nel messaggio finale.
7. **Una sessione, un compito.** Non iniziare compiti diversi da quello richiesto.
8. **Contesto contenuto**: non rileggere l'intero libro se non e' richiesto. Leggi solo i file indicati dal prompt.

### Chi scrive dove

| Compito | Puo' creare/modificare |
|---|---|
| P1 | `stato/macro_scaletta.json` |
| P1R | `stato/revisione_p1.md` |
| P2 (cap. N) | `stato/blueprint/capNN.json` |
| P2B | `stato/coerenza_blueprint.json`; correzioni locali a `stato/blueprint/capNN.json` |
| P3 (cap. N) | `manoscritto/capNN/*.md` |
| P4 (cap. N) | `audit/capNN_cC_audit.json` (e basta: l'auditor NON modifica il testo) |
| P5 (cap. N) | i file di `manoscritto/capNN/` indicati nei residui; `audit/capNN_cC_p5.json` o `audit/globale_p5_capNN.json` |
| P6D (cap. N) | `stato/digest/capNN.md` |
| P6 | `audit/globale_audit.json` (e basta) |
| P7 (cap. N) | `docente/commenti/capNN.json` |
| P7M | `apparati/metadati.json` |

(`NN` = numero del capitolo a due cifre, `C` = numero del ciclo di audit, `N` senza zero iniziale.)

### Comandi di controllo (dalla cartella del progetto)

Questi sono gli UNICI comandi che un agente puo' eseguire (non modificano lo stato della pipeline):

```
python3 scripts/libro.py controlla-macro  # controlla la macro-scaletta
python3 scripts/libro.py controlla-bp N   # controlla il blueprint del capitolo N (compila e prova le soluzioni)
python3 scripts/libro.py controlla N      # controlla il capitolo N scritto (struttura, codice compilato ed eseguito, progressione)
```

I comandi `avanti`, `verifica`, `approva`, `riapri`, `unisci`, `soluzioni`, `indice`, `fine`, `prossimo`, `stato`, `diagnosi`
sono SOLO dell'utente: nessun agente li esegue, nessun agente tocca `stato/stato.json`.

---

## 3. Formato del manoscritto (`manoscritto/capNN/`)

Ogni capitolo e' una cartella con questi file, tutti obbligatori:

- `NN_00.md` — apertura del capitolo
- `NN_01.md`, `NN_02.md`, ... — una per ogni sotto-sezione del blueprint
- `NN_99.md` — riepilogo

### 3.1 `NN_00.md`

```markdown
# Capitolo N — Titolo del capitolo

> **In questo capitolo imparerai a:**
> - obiettivo 1
> - obiettivo 2
> - obiettivo 3

> **Ti servono:** (capitoli o concetti precedenti, in una riga)

Due o tre paragrafi di apertura che spiegano perche' questo argomento serve davvero.
```

### 3.2 `NN_kk.md` (sotto-sezione N.k)

Ordine e intestazioni ESATTI (i controlli automatici li cercano):

````markdown
## N.k Titolo della sotto-sezione

Teoria in prosa. Prima l'idea, poi il termine tecnico, poi la regola.

### Esempio guidato

<!-- cod: id=N.k-a tipo=programma -->
```c
#include <stdio.h>

int main(void) {
    printf("Ciao!\n");
    return 0;
}
```

```output
Ciao!
```

Spiegazione dell'esempio, riga per riga o per blocchi.

> **Approfondimento — Titolo**
> Solo se il blueprint lo prevede. Testo del box.

### Esercizio N.k — Titolo dell'esercizio

**Descrizione**

Testo dell'esercizio.

**Concetti da tenere a mente**

- concetto 1
- concetto 2

**Domande guida**

1. Prima domanda che indirizza il ragionamento?
2. Seconda domanda?
3. Terza domanda?

**Esempio di esecuzione**

```input
input di esempio
```

```output
output di esempio
```
````

Per un progetto l'intestazione e' `### Progetto N.k — Titolo` e dopo la descrizione si aggiunge l'elenco numerato
delle **Fasi**.

### 3.3 `NN_99.md`

```markdown
## Riepilogo

- punto 1
- punto 2

## Errori comuni

- errore 1 e come riconoscerlo

## Prima di proseguire

- [ ] so spiegare ...
- [ ] so scrivere ...
```

### 3.4 Blocchi di codice C: marcatori obbligatori

Ogni blocco ```` ```c ```` deve essere preceduto, sulla riga immediatamente precedente (righe vuote ammesse), da un
marcatore:

```
<!-- cod: id=<id univoco nel capitolo> tipo=<tipo> [exit=N] [gruppo=<nome> file=<nome_file>] -->
```

| `tipo` | Significato | Controllo automatico |
|---|---|---|
| `programma` (predefinito) | programma completo con `main` | compilato ed eseguito; se segue un blocco `output`, l'output reale deve coincidere |
| `frammento` | poche righe illustrative, non un programma | non compilato (usalo con parsimonia) |
| `errore` | codice che DEVE essere rifiutato dal compilatore | deve fallire la compilazione |
| `traccia` | scheletro con `TODO` dentro un esercizio (max 25 righe) | non compilato |

- `id` ha la forma `N.k-a`, `N.k-b`, ... (N = capitolo, k = sotto-sezione).
- **Programmi su piu' file** (dal capitolo 19): ogni blocco ```` ```c ```` del programma ha lo STESSO `gruppo=<nome>` e un
  proprio `file=<nome>.c` oppure `file=<nome>.h` (solo lettere, cifre, `_`). I blocchi del gruppo vengono scritti come
  file nella stessa cartella e compilati INSIEME (`main` in uno dei `.c`). Il blocco ```` ```input ```` e il blocco
  ```` ```output ```` si mettono dopo l'ULTIMO blocco del gruppo. Ogni blocco ha comunque un `id` univoco.
- Se il programma legge dalla tastiera, subito dopo il blocco `c` metti un blocco ```` ```input ```` con l'input
  da fornire, poi il blocco ```` ```output ````.
- Se `main` restituisce un valore diverso da 0 su richiesta dell'esempio, indica `exit=N`.
- Gli output mostrati devono essere ESATTAMENTE quelli prodotti dal programma (gli spazi finali sono ignorati).

---

## 4. Regole sul codice C

1. **Standard C23.** Il codice deve compilare senza nessun warning con `-Wall -Wextra -Wpedantic -Werror`.
2. **Solo libreria standard**, solo gli header ammessi dallo script. Nessuna funzione POSIX o Windows (`unistd.h`,
   `sleep`, `conio.h`, `getch`, `system("clear")`, `M_PI`, ...). Le novita' C23 (`bool`/`true`/`false`, `nullptr`,
   `constexpr`, `typeof`, `auto`, `0b...`, separatori di cifre) si usano SOLO se sono nel registro del capitolo,
   e vanno segnalate con un box `> **C23** ...` che spiega cosa fare con compilatori piu' vecchi.
3. **Mai**: `gets`, `scanf("%s")` senza larghezza, `fflush(stdin)`, `void main`, array a lunghezza variabile (VLA),
   comportamento indefinito negli esempi eseguibili. Per mostrare un comportamento indefinito usa un `frammento`
   con un box che dice chiaramente che e' un errore e non va mai scritto cosi'.
4. **Input**: per leggere testo usa `fgets`. Per i numeri segui l'ordine di introduzione del registro (`scanf` con controllo
   del valore restituito, oppure `fgets` + `strtol`/`sscanf`). Controlla sempre il valore di ritorno di `scanf`,
   `fopen`, `malloc`.
5. **Output deterministico**: niente `rand()` senza `srand` con seme fisso, niente `time()` nell'output, niente
   indirizzi (`%p`) nell'output mostrato. Se un esercizio non puo' essere deterministico: `verificabile: false`.
6. **Programmi corti**: un esempio guidato sta in 40 righe al massimo (80 dal capitolo 13).
7. **Stile**: 4 spazi, graffa di apertura sulla stessa riga, graffe SEMPRE presenti in `if`/`for`/`while`, `int main(void)`,
   `return 0;` esplicito, nomi in `snake_case` italiano senza accenti, costanti in MAIUSCOLO, commenti in italiano e brevi.
8. **Mai riportare messaggi del compilatore in modo letterale** (cambiano da compilatore a compilatore): descrivi il tipo di
   messaggio ("il compilatore segnala che ... non e' dichiarato").
9. **Progressione**: in un capitolo si usano SOLO gli elementi del linguaggio e della libreria introdotti in quel
   capitolo o nei precedenti (vedi `stato/macro_scaletta.json`, campo `registro`, e `stato/stati/capNN.md`). Un
   concetto nuovo si introduce nel capitolo previsto, mai di sfuggita. Rinvii in avanti solo nella forma
   "(lo vedremo nel capitolo X)" con X corretto.

---

## 5. Regole di scrittura (italiano)

1. **Ordine didattico**: motivazione → idea intuitiva → termine tecnico → regola precisa → esempio → errore tipico.
2. **Termini**: usa SEMPRE il termine ufficiale del glossario (`stato/macro_scaletta.json`, campo `glossario`). I
   `sinonimi_vietati` non vanno mai usati. Alla prima occorrenza di un termine: **grassetto** e, se serve, il termine
   inglese tra parentesi.
3. **Registro**: tono diretto, rigoroso, incoraggiante; frasi brevi; niente slang, niente emoji, niente iperboli
   ("semplicissimo", "banale"), niente frasi vuote ("in questo capitolo vedremo...") oltre all'apertura prevista.
4. **Precisione**: affermazioni sul linguaggio sempre corrette rispetto allo standard C. Distingui con cura
   comportamento *definito*, *dipendente dall'implementazione* e *indefinito*.
5. **Analogie**: ammesse se concrete e brevi; dopo l'analogia scrivi sempre la regola precisa.
6. **Confronti con Python**: opzionali, al massimo uno per sotto-sezione, nel box `> **Se vieni da Python** — ...`.
7. **Schemi di memoria**: disegnali in blocchi ```` ```text ```` (monospazio), senza marcatore.
8. **Lunghezza** di una sotto-sezione: indicativamente 700-2200 parole di prosa (codice escluso).
9. **Esercizi senza soluzione**: l'esercizio contiene descrizione, concetti da tenere a mente, domande guida (che
   indirizzano il ragionamento, mai il codice) ed esempio di esecuzione. Niente codice risolutivo, nemmeno parziale,
   salvo una `traccia` con `TODO`. L'esempio guidato NON deve essere la soluzione dell'esercizio della stessa
   sotto-sezione (i controlli lo verificano).

---

## 6. Formato dei file JSON (riferimento rapido)

I formati completi sono nei prompt P1, P2, P4. Regole comuni: JSON valido (niente commenti, niente virgole finali), testo
in UTF-8, nessun testo fuori dal JSON nei file `.json`.

**Audit / patch** (P4 e P6):

```json
{
  "capitolo": 3,
  "ciclo": 1,
  "verdetto": "da_correggere",
  "patch": [
    {
      "id": "p1",
      "file": "manoscritto/cap03/03_02.md",
      "gravita": "alta",
      "tipo": "fattuale",
      "certezza": "alta",
      "problema": "Spiegazione chiara del problema.",
      "old_text": "testo ESATTO copiato dal file (deve comparire una sola volta)",
      "new_text": "testo corretto"
    }
  ]
}
```

- `gravita`: `bloccante` (testo falso, codice sbagliato, soluzione svelata), `alta` (fuorviante o contro la
  progressione), `media`, `bassa`.
- `tipo`: `fattuale`, `codice`, `grammatica`, `didattica`, `progressione`, `soluzione_esposta`, `glossario`, `coerenza`.
- `certezza`: `alta` solo se sei sicuro della correzione; altrimenti `media` (non verra' applicata in automatico).
- Se la correzione richiede una riscrittura ampia: `old_text` e `new_text` a `null` (se ne occupera' P5).

---

## 7. Messaggio finale (sempre, breve)

Chiudi ogni compito con queste righe e basta:

```
FATTO: <file creati o modificati>
CONTROLLI: <comandi eseguiti e loro esito, oppure "non eseguiti: motivo">
DUBBI: <cose di cui non sei sicuro, o "nessuno">
```

---

## 8. Lavoro a capitoli (un agente per volta)

Il lavoro gira in Google Antigravity con i modelli Gemini 4 (Neon, Argon, Hydrogen): un solo agente per sessione, senza
orchestratore e senza sub-agenti. Il messaggio dell'utente indica il compito (il file in `prompts/`) e, quando serve, i
capitoli (`CAPITOLI=...`: un numero, un elenco `3,7` o un intervallo `3-5`) ed eventuali parametri (`CICLO`, `SORGENTE`).

1. **Un capitolo alla volta.** Se i capitoli sono piu' d'uno, lavorali in ordine: finisci e controlla un capitolo prima di
   passare al successivo. Non rileggere i capitoli gia' chiusi.
2. **Leggi solo cio' che serve.** Il prompt elenca i file di input: non leggere altro (il libro intero non sta nel contesto).
3. **Rilancio dopo errori o interruzioni.** Se i file di esito (`stato/verifica_bp_capNN.json`, `stato/verifica_capNN.json`,
   `stato/verifica_p1.json`) contengono `errori`, lavora in modalita' correzione: correggi SOLO quegli errori e non riscrivere il
   resto. Se i file di output esistono gia' (sessione interrotta), completa solo cio' che manca.
4. **Esegui i controlli indicati e non dichiarare mai di averli eseguiti se non l'hai fatto.** Se non puoi eseguire comandi,
   dillo nel messaggio finale: l'utente li lancera'.
5. **Mai due compiti diversi nella stessa sessione.** Quando hai finito, rispondi con il messaggio finale del paragrafo 7.
