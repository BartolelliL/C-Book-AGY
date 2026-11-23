## Riepilogo

- Una **funzione** racchiude un compito ben definito dietro un nome, una lista di **parametri** con i rispettivi tipi (oppure `void` se non accetta parametri) e un tipo di ritorno (oppure `void` se non restituisce valori). Gli **argomenti** sono le espressioni passate alla chiamata.
- Ogni funzione va dichiarata prima della sua prima chiamata tramite definizione completa o **prototipo**, con firma perfettamente coerente con la definizione. Alla chiamata gli argomenti subiscono conversione implicita verso i tipi dei parametri.
- Il C usa sempre il **passaggio per valore**: la funzione riceve una copia di ciascun argomento e modificare un parametro non altera mai la variabile del chiamante (per modificare variabili del chiamante useremo i puntatori nel capitolo 10). L'ordine di valutazione degli argomenti è comportamento non specificato.
- Le funzioni `abs`, `labs` e `llabs` di `<stdlib.h>` calcolano il valore assoluto di `int`, `long` e `long long`, ma chiamarle su `INT_MIN`, `LONG_MIN` o `LLONG_MIN` provoca comportamento indefinito.
- La **visibilità** stabilisce dove un nome può essere usato (visibilità di blocco per variabili locali e parametri, visibilità di file per prototipi e costanti `constexpr`); la **durata di vita** stabilisce per quanto tempo esiste la memoria dell'oggetto (automatica per le variabili locali normali, statica per l'intera esecuzione nel caso di `static` locale).
- Una funzione che usa la **ricorsione** richiama se stessa su un sottoproblema più piccolo: richiede sempre almeno un **caso base** e un passo ricorsivo strettamente convergente; ogni invocazione attiva dispone di copie indipendenti dei propri parametri e delle variabili automatiche.
- Scomporre un problema dall'alto verso il basso in funzioni brevi, pure e con una sola responsabilità, separando calcolo, validazione e I/O, rende i programmi più leggibili, riutilizzabili e facili da verificare.

## Errori comuni

- **Aspettarsi che modificare un parametro dentro una funzione aggiorni la variabile del chiamante**: in C il passaggio è sempre per valore; per aggiornare una variabile del chiamante restituisci il nuovo valore con `return` e riassegnalo nel chiamante (oppure usa i puntatori, lo vedremo nel capitolo 10).
- **Chiamare una funzione prima di averla definita o averne dichiarato il prototipo, oppure scrivere un prototipo con tipi diversi dalla definizione**: il compilatore segnala un identificatore non dichiarato o un conflitto di tipi; tieni tutti i prototipi allineati alle definizioni in cima al file.
- **Dimenticare un'istruzione `return` in uno dei rami di una funzione non `void`, oppure scrivere un punto e virgola indesiderato nell'intestazione della definizione**: nel primo caso usare il valore restituito provoca comportamento indefinito (e `-Wall -Werror` lo segnala); nel secondo il compilatore rifiuta la definizione per errore di sintassi.
- **Dichiarare una variabile locale senza `static` quando serve conservarne il valore tra chiamate successive, oppure inizializzare una variabile `static` con un'espressione non costante**: una variabile automatica si azzera o si ricrea a ogni chiamata, mentre una `static` accetta solo inizializzatori costanti noti a tempo di compilazione.
- **Scrivere una funzione ricorsiva senza caso base o con un passo ricorsivo che non si avvicina al caso base**: la ricorsione prosegue all'infinito fino a esaurire la memoria della pila delle chiamate, provocando comportamento indefinito.
- **Chiamare `abs`, `labs` o `llabs` rispettivamente su `INT_MIN`, `LONG_MIN` o `LLONG_MIN` senza controllo preventivo**: nella rappresentazione in complemento a due (lo vedremo nel capitolo 13) il valore assoluto del minimo intero con segno non è rappresentabile nel tipo di ritorno e la chiamata provoca comportamento indefinito.

## Prima di proseguire

- [ ] So scrivere definizioni e prototipi coerenti di funzioni con tipi di ritorno numerici, `bool` e `void`, distinguendo con precisione tra parametri e argomenti.
- [ ] So prevedere gli effetti del passaggio per valore, evitare effetti collaterali incrociati tra argomenti di una stessa chiamata e usare in sicurezza `abs`, `labs` e `llabs`.
- [ ] So distinguere visibilità di blocco e durata di vita automatica o statica, spiegando come e quando usare una variabile locale `static`.
- [ ] So scrivere una funzione ricorsiva identificando caso base e passo ricorsivo convergente, e so tracciarne discesa e risalita sulla pila delle chiamate.
- [ ] So scomporre un problema articolato in funzioni piccole, pure e componibili, separando la logica di calcolo dalla lettura dell'input e dalla stampa dell'output.
