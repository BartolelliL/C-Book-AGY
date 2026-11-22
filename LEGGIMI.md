# Pipeline per scrivere il libro di C (Google Antigravity, modelli Gemini 4)

Questo pacchetto ti permette di scrivere il libro **mandando un messaggio alla volta ad Antigravity**, con i soli modelli
**Gemini 4 Neon, Argon e Hydrogen**. Non c'e' orchestratore ne' sub-agenti: in ogni sessione lavora un solo agente su un
compito preciso. Non devi decidere tu cosa fare dopo: uno script controlla il lavoro e ti dice **quale modello scegliere e
quale messaggio incollare**.

## 1. Preparazione (una volta sola)

1. Serve **Python 3.8 o superiore** e un **compilatore C** (macOS: `xcode-select --install`; Linux: `gcc` o `clang`;
   Windows: WSL).
2. Nel terminale, nella cartella del progetto:
   ```
   git init
   python3 scripts/libro.py diagnosi
   ```
   `diagnosi` controlla Python, compilatore, supporto a C23 (e quali novita' C23 il tuo compilatore capisce) e i file.
   Deve finire con "TUTTO OK". Se il compilatore non conosce `-std=c23` usa `-std=c2x` da solo.
3. Apri la cartella come workspace in **Antigravity**.
4. (Facoltativo) prima di partire modifica `PROGRAMMA.md` (capitoli), la tabella iniziale di `CONVENZIONI.md` (lettori,
   soluzioni, lingua) e `config.json` (limiti, modelli, dimensione dei lotti).

## 2. Il ciclo (sempre lo stesso)

```
python3 scripts/libro.py avanti
```

1. Il comando controlla cio' che e' stato prodotto e ti mostra la tabella di avanzamento, **il modello da selezionare** e **il
   messaggio esatto da incollare** (con i capitoli, es. `CAPITOLI=3`).
2. In Antigravity apri una **sessione nuova**, seleziona il modello indicato, incolla il messaggio (solo quello).
3. Aspetta che l'agente finisca. Poi torna al punto 1.

Se ci sono stati errori, `avanti` te lo dice e ripropone lo stesso passo: l'agente riconosce da solo il rilancio (legge i file di
esito con gli errori) e corregge solo quelli. Se la sessione si interrompe (quota, chiusura), reincolla lo stesso messaggio: l'agente
completa solo cio' che manca.

## 3. I modelli e perche'

| Ruolo | Modello | Passi |
|---|---|---|
| Scrive e progetta | **Gemini 4 Neon** (il piu' adatto tra i tre al lavoro complesso: sostituisce Argon con qualita' vicina a Carbon) | P1, P2, P3, P5 |
| Controlla | **Gemini 4 Argon**: un modello DIVERSO da chi ha scritto | P1R, P2B, P4, P6 |
| Lavoro meccanico o di riassunto | **Gemini 4 Hydrogen** (veloce ed economico) | P6D, P7, P7M |

Dove il passo lo prevede, se Antigravity lo permette, imposta il **ragionamento alto** (la tabella in `config.json` lo indica).
Tutti e tre sono modelli Google: l'indipendenza tra chi scrive e chi controlla e' quindi minore di quella tra famiglie
diverse. La compensano i controlli automatici dello script (compila ed esegue tutto il codice) e i tuoi tre checkpoint. Se
vuoi un'altra assegnazione modifica la tabella `modelli` in `config.json`.

## 4. I passi

| Passo | Cosa fa | Quante volte |
|---|---|---|
| P1 | Macro-scaletta: capitoli, obiettivi, registro degli elementi del linguaggio, glossario | 1 |
| P1R | Critica indipendente della macro-scaletta (`stato/revisione_p1.md`) | 1 |
| **Checkpoint 1** | **Tu** leggi macro-scaletta e critica, poi `approva 1` | 1 |
| P2 | Scheda tecnica di un capitolo, con esercizi e soluzioni di riferimento (compilate e provate dallo script) | 1 messaggio ogni 2 capitoli |
| P2B | Coerenza tra le schede (lavora su un riepilogo generato dallo script) | 1 |
| P3 | Stesura di un capitolo (testo, codice, esercizi senza soluzioni) | 1 messaggio per capitolo |
| P4 | Audit indipendente del capitolo | 1-2 giri per capitolo, 2 capitoli a messaggio |
| P5 | Correzioni mirate (solo se servono) | se serve |
| **Checkpoint 2** | **Tu** leggi il **capitolo pilota** e approvi (`approva pilota`) | 1 |
| P6D | Riassunti strutturati (digest) dei capitoli | 1 messaggio ogni 4 capitoli |
| P6 | Revisione di coerenza su tutto il libro, a partire dai digest | 1 |
| P7 | Commenti alle soluzioni per il docente | 1 messaggio ogni 4 capitoli |
| P7M | Metadati del libro | 1 |
| **Checkpoint 3** | **Tu** leggi tutto, `approva finale`, poi `fine` crea il file finale | 1 |

**Il capitolo pilota** (`capitolo_pilota` in `config.json`, ora il 10, sui puntatori) e' il primo capitolo scritto e controllato
fino in fondo, da solo, prima di tutti gli altri. Se ti convince, la sua prima sotto-sezione diventa l'esempio di stile per tutto il
libro; se no, correggi prompt o regole e rifai il capitolo.

L'ordine lo decide lo script: prima il pilota, poi tutte le stesure, poi tutti gli audit.
**Quanti messaggi?** Con 26 capitoli circa 85-110 in tutto (una sessione per capitolo nella stesura, lotti piu' grandi nei passi
leggeri). I lotti sono in `config.json` (`lotto_capitoli`): alzali se hai margine di quota, abbassali se l'agente perde il filo.

## 5. Cosa controlla lo script in automatico (e cosa no)

**Controllato da script (affidabile):** il codice di ogni esempio e di ogni soluzione (anche su piu' file) compila senza
warning (`-Wall -Wextra -Wpedantic -Werror`), viene eseguito (con sanitizer se disponibili) e l'output mostrato nel libro e'
identico a quello reale; nessun elemento del linguaggio o della libreria usato prima del capitolo in cui lo introduci; header e
funzioni non portabili vietati; termini del glossario e sinonimi vietati; struttura dei file; **nessuna soluzione negli
esercizi** (nemmeno un esempio guidato che la somigli); gli esempi di esecuzione coincidono con il blueprint.

**Non garantito da script:** la correttezza delle spiegazioni, la bonta' didattica, la qualita' dell'italiano. Qui lavorano
l'audit di un secondo modello (P4, P6) e **tu** nei tre checkpoint. Leggi con attenzione soprattutto il capitolo pilota e i
capitoli su puntatori, memoria dinamica, puntatori a funzione, tabelle hash e il progetto finale.

## 6. Regole d'oro

- **Una sessione = un messaggio**, con il modello indicato da `avanti`.
- **Non modificare i file mentre un agente lavora**, e un solo agente alla volta sulla cartella.
- Incolla **solo** il messaggio che ti mostra `avanti`: tutte le istruzioni sono nei file in `prompts/` e in `CONVENZIONI.md`.
- Non modificare `stato/macro_scaletta.json` dopo averla approvata (lo script se ne accorge). Se serve cambiarla,
  modifica e rilancia `approva 1`.
- Lo script fa un commit Git a ogni passo: puoi sempre tornare indietro.
- Solo tu lanci `avanti`, `approva`, `riapri`, `fine`: gli agenti possono lanciare soltanto `controlla-macro`,
  `controlla-bp N` e `controlla N`, che non toccano lo stato.

## 7. Se qualcosa va storto

| Situazione | Cosa fare |
|---|---|
| Quota esaurita o sessione interrotta | Aspetta, o riduci `lotto_capitoli`, poi **reincolla lo stesso messaggio** |
| L'agente perde il filo o ignora le regole in un lotto di piu' capitoli | Metti `lotto_capitoli` a 1 per quel passo in `config.json` |
| Un agente dice di aver eseguito i controlli ma non e' vero | Nessun problema: `avanti` li rifa sempre lui |
| Un capitolo non ti convince | `python3 scripts/libro.py riapri N stesura` (oppure `blueprint`, `audit`) e poi `avanti` |
| Vuoi controllare a mano un capitolo | `python3 scripts/libro.py controlla N` |
| Vuoi vedere dove sei | `python3 scripts/libro.py stato` |
| Hai modificato un file a mano | `avanti` lo ricontrolla (i capitoli chiusi vengono ricontrollati alla fine) |
| Lo script segnala `P5 dichiara problemi non risolti` | Sono dubbi che spettano a te: apri il file `audit/..._p5.json` e decidi |

## 8. Cartelle

```
CONVENZIONI.md   regole condivise (§8: lavoro a capitoli)       PROGRAMMA.md   capitoli proposti (input di P1)
prompts/         i prompt                                        config.json    limiti, modelli, lotti
scripts/libro.py controlli e avanzamento                         stato/         macro-scaletta, blueprint, esiti dei controlli, digest
manoscritto/     il libro, un file per sotto-sezione             audit/         rapporti di audit e correzioni
docente/         commenti e soluzioni per il docente (NON nel libro)    apparati/  indice analitico e metadati
consegna/        libro_completo.md (file finale)
```

## 9. Comandi

Dell'utente: `avanti` · `stato` · `prossimo` · `diagnosi` · `approva 1 | pilota | finale` · `riapri N fase` · `unisci` ·
`soluzioni` · `indice` · `fine`. Anche degli agenti: `controlla-macro` · `controlla-bp N` · `controlla N`.
(Tutti con `python3 scripts/libro.py <comando>`.)

## 10. Nota sull'affidabilita' del pacchetto

La versione con un solo agente per sessione e i soli modelli Gemini **non e' stata provata**: lo script e' stato solo controllato
nella sintassi dopo le ultime modifiche. Le versioni precedenti della macchina a stati, della sandbox (anche a piu' file), dei
controlli, delle patch e del file finale erano state provate con agenti simulati su Linux con GCC 13 e Python 3.12, ma non con
Antigravity vero ne' su macOS. Il primo giro vero (`diagnosi`, P1, P1R) serve anche a scoprire eventuali problemi: se
qualcosa non torna, incolla l'output di `python3 scripts/libro.py diagnosi` e di `avanti`.
