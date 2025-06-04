# Documentation Stucture

Developer Documentation Structure
Consiglio: genera un repo vuoto per le note in modo da versionarle separate dal sottomodulo, inserisci questo repo come un sottomodulo git, dopo potrai inizializzare la tua struttura di appunti con il comando `--init` garantendo una struttura stabile. Questo ti permette anche di avere gli script e le tue note separate.

Per maggiori informazioni sulle operazioni che puó fare questo sottomodulo lanciare:

```bash
python DocScript/make.py --help
```

## Guida all'inizializzazione

1. <span style="color: brown;">Creazione del repo personale</span>

   Su GitHub o in locale creare un repo git con:

   ```bash
   git init --bare MyDocumentation
   ```

2. <span style="color: brown;">Clonare il repo ed inserire il sottomodulo</span>

   ```bash
   git clone /path/to/MyDocumentation MyDocs
   cd MyDocs
   git submodules add https://github.com/BenettiFabio/DocScript
   ```

3. <span style="color: brown;">Inizializzare il vault</span>

   A questo punto grazie agli script si puó inizializzare un vault in cui iniziare a scrivere la propria documentazione. Ricorda di stare dentro la cartella `MyDocs/`.

   ```bash
   python DocScript/make.py --help
   python DocScript/make.py --init
   ```

   Verrá creato un **vault** con una struttura standard basata un un **macro-argomento** con una nota al suo interno, una cartella **assets** per gli allegati e al di fuori i file per le indentazioni di **markdownlint** e **prettier**.

   Per maggiori informazioni sulla struttura base del progetto proseguire con la lettura.

   Se Hai giá un vault e sai giá come usarlo, ma hai dei collaboratori e vuoi iniziare ad usarlo in gruppo allora puoi inizializzare una banca dati con

   ```bash
   python DocScript/make.py --init-bank
   ```

   Questo genererá 3 file dentro la cartella `bank/`:

   - `collaborator.md` : in cui specificare con chi lavori
   - `main.md` : sará un indice complessivo delle note di tutti i collaboratori
   - `custom.md` : che puoi riempire per compilare le tue note personalizzate

4. <span style="color: brown;">Compilare le note per creare .pdf e .tex</span>

   A questo punto o hai un Vault o hai una banca dati, se sai giá usarli benissimo! **Enjoy!** in caso contrario vai pure alle procedure di conversione per un vault personale [Qui](#build-di-un-documento) e per una nota con collaboratori in una banca dati [Qui](#build-di-un-documento-con-collaboratori).

   Ricorda peró che le conversioni dei documenti devono rispettare dei constraint specifici quindi se é la tua prima volta qui prosegui pure la lettura con la [struttura del progetto](#struttura-del-progetto)!

# Struttura del progetto

0. **REGOLA FONDAMENTALE DELLE NOTE:** I nomi delle note devono essere tutti in <span style="color: red;">_minuscolo_</span>, le parole separate da `-`. I nomi delle note sono **TUTTI** descrittivi del loro albero di posizione:

   _es:_

   ```bash
   vault/
   ├── main.md
   ├── macro-arg1/
   │   ├── main.macro-arg1.sub-arg1.md
   │   └── main.macro-arg1.sub-arg2.md
   ├── macro-arg2/
   │   └── main.macro-arg2.sub-arg1.md
   └── macro-arg3/
       └── main.macro-arg3.sub-arg1.md
   ```

   In Questo modo la ricerca dei file e dei loro contenuti si semplifica e semplifica l'utilizzo anche di eventuali script che possono sfruttare il nome per eventuali automazioni.

   > <span style="color: red;">ATT!:</span> Ogni nuova pagina aggiunta va inserita direttamente
   > nell'indice totale (`main.md`)

1. `main.md`: Questo file è l'indice di tutta la struttura, andrà a linkare tutte le pagine del progetto in modo da poterle trovare facilmente nel tempo.

2. **vault:** Il Vault è la cartella contenente tutte le note, i nomi delle note sono divisi in macro-argomenti nelle sottocartelle del Vault. Dentro il file `main.md` puoi creare un indice che contiene tutte le note per navigare piú facilmente. Se vuoi convertirle tutte in una volte verrá usato l'ordine del main come ordine delle note nel pdf finale.

   > <span style="color: orange;">NOTA:</span> se vuoi convertire solo un certo gruppo ristretto di note sconnesse tra loro in un unico file pdf, puoi creare un file `custom.md` e inserire lí un indice come se fosse un main, con solo le note che desideri e poi usare l'opzione `-c`

3. **Assets:** La cartella assets contiene tutti i documenti e le immagini utili al progetto che sono linkate all'interno delle varie note, dentro la cartella `assets/macro-argomento/` ci sono i relativi docs, imgs, ... la struttura della cartella `assets/` deve essere identica a quella fuori in modo da mantenere semplice il ritrovamento dei file e documenti salvati.

   > <span style="color: orange;">NOTA:</span> dentro gli assets ci possono essere le immagini costruite mediante `Python`, `Mermaid` e `TiKz` in base alle esigenze. Nello specifico per `Tikz` c'é un comando di conversione apposito in quanto é gestito come una nota `.md` ma la nota é negli asset e viene generato un output sempre negli assets, vedi `-nt --note-tikz`.

   > <span style="color: orange;">NOTA:</span> la struttura tipica della cartella di assets é la seguente
   >
   > ```bash
   > vault/assets/
   >        ├── macro-arg1/
   >        │   ├── imgs/
   >        │   │   ├── mermaid-imgs/
   >        │   │   │   └── img1-mermaid.md
   >        │   │   ├── python-imgs/
   >        │   │   │   └── img2-python.py
   >        │   │   ├── img1.png
   >        │   │   └── img2.png
   >        │   └── pdfs/
   >        │         ├── tikz-pdfs/
   >        │         │   └── tikz1-tikz.md
   >        │         └── tikz1.pdf
   >        └── macro-arg2/
   > ```
   >
   > In questo modo so sempre che i sorgenti si chiamano con lo stesso nome dell'immagine o del pdf e sono separati dal resto.
   > _Es:_ `tikz1.pdf` é generato da `tikz1-tikz.md`

4. **DocScripts:** Questo sottomodulo contiene tutti gli script e le automazioni che possono essere eseguiti nel progetto. in modo da aggiungere pagine standardizzate, comandi di conversione da `.md` a `.pdf` o `tex` con `pandoc` in modo semplice mediante il `make.py`.

   Dentro il sottomodulo é presente la cartella `requirements/` dove sono presenti giá i fonts e altri componenti per velocizzare la messa in servizio del vault.

5. **./vault/rusco:** É una cartella temporanea in questo modo quando si converte l'intero repo con il comando `-a` queste note vengono escluse dal check di consistenza in modo che si possano fare note temporanee senza preoccuparsi di inserirle nel `main.md`.

# Dipendenze librerie

1. Pandoc: serve a convertire da .tex a .pdf (da inserire negli env Path)
2. MikTeX: serve ad avere LateX installato
3. Strowberry Perl (da inserire negli env Path)
4. Fonts: GNU FreeFonts (FreeSans e FreeMono)

# Dipendenze utili VSCode

1. **Markdown TOC:** Gestisce la possibilità di creare Table of content, ovvero degli indici autogenerati in note molto lunghe, in questo modo sono più facilmente navigabili _es:_

   - apri la nota in cui inserire l'elenco
   - Ctrl + Shift + P (comandi VSCode)
   - usa il comando: `Markdown TOC: Insert TOC`
   - usa il comando: `Markdown TOC: Update TOC`

2. **Markdown Preview Enhanced:** Questa serve ad utilizzare componenti di CSS e HTML direttamente nelle note, in questo modo è possibile vedere in preview parole colorate e indentate direttamente sull'editor e non conflitta con `pandoc` durante eventuali conversioni. Permette di sfruttare lo schema colori presente in "Legenda di aiuto alla coerenza"

3. **Markdown Preview Mermaid Support:** Usare il mermaid per creare grafici, i file .md devono chiamarsi con lo stesso nome dell'immagine che andranno a generare e saranno nella cartella vault/assets/macro-argomento/mermaid/.

   > <span style="color: orange;">NOTA:</span> Una volta creata l'immagine del grafico desiderata, tasto destro ed esporta come png e ritagliarla di conseguenza.

   In Questo modo se si vuole modificare una immagine si può avere direttamente il file generatore con estensione del nome -mermaid.md e l'immagine generata per poter fare modifiche rapide se necessarie. Nel caso in cui si trovasse una immagine inserita nel progetto è anche semplice capire se è una immagine scaricata e aggiunta o una generata e quindi modificabile guardando semplicemente il link.

4. **vscode-pdf:** Visualizza direttamente i pdf sull'Editor senza dover passare per la discovery dei file.

5. **Markdownlint** + **Prettier:** sono una combo di estensioni che permette di segnalare errori di formattazione all'interno di un md file attraverso regole presenti nel file `.markdownlint.json` nella root. Unito a Prettier per correggere direttamente la formattazione.

   > <span style="color: darkviolet;">OSS:</span> per implementarli, dopo aver installato le
   > estensioni seguire i seguenti passaggisu `VSCode`:
   >
   > 1. `Ctrl+,` per aprire le impostazioni
   > 2. cerca: `default formatter`
   > 3. imposta `esbenp.prettier-vscode`
   > 4. cerca `format on save` e attiva l'impostazione A questo punto ogni salvataggio della nota verrá automaticamente formattata secondo le regole contenute nel file `.prettierrc`.

# Legenda ed aiuto alla coerenza

Il comando di pandoc per la conversione da markdown a pdf rispetta delle regole e per mantenere il sistema piú longevo possibile non sono stati usati pacchetti troppo complessi. Per ovviare al problema sono state aggiunte regole e template che convertono in modo corretto questo tipo di blocchi css e evidenziature senza problemi, se rispettati questi blocchi non causeranno errori nel pdf finito.

- > <span style="color: darkviolet;">OSS:</span> Questa è una osservazione
- > <span style="color: red;">ATT!:</span> Questo è un attenzione
- > <span style="color: orange;">NOTA:</span> Questa è una nota
- > <span style="color: skyblue;">RICORDA:</span> Questo è un blocco ricordo
- <span style="background-color: yellow;">Questa è una riga evidenziata</span>
- <span style="text-decoration: underline;">Questo é un testo sottolineato</span>

1. <span style="color: brown;">Gli elenchi numerati di una guida da seguire vanno in marrone </span>

> <span style="color: orange;">NOTA:</span> Le evidenziazioni vengono **sempre** sostituite con i colori personalizzati `hl*` (quindi `yellow` = `hlyellow`) che sono presenti nel conversion-template.tex che rende i colori dell'evidenziatore nel pdf più gradevoli ma mantenendo la visualizzabilità in Preview real time. Se ne vengono aggiunti altri, aggiungerli anche a `.lua`

> <span style="color: orange;">NOTA:</span> Il testo sottolineato non é compreso in markdown con un simbolo come `*` per il grassetto e `_` per il corsivo quindi occorre usare il blocco `<span>` convertito con il filtro lua.

_Es:_ inserimento immagine

```markdown
Come si vede nella immagine Fig.\ref{img: titolo-image} _Titolo immagine_
![Titolo immagine.\label{img: titolo-image}](../assets/macro-arg/imgs/nome-immagine.png){width=\linewidth}

![Titolo immagine](../assets/macro-arg/imgs/nome-immagine.png){width=\linewidth}
![Titolo immagine](../assets/macro-arg/imgs/nome-immagine.png){width=50%}
```

> <span style="color: orange;">NOTA:</span> In certi casi andando ad aggiungere una immagine puó venire spostata all'inizio e quindi in una posizione errata. Per evitare che accada prima dell'immagine o prima dell'argomento meglio cambiare pagine
>
> ```markdown
> <div style="page-break-after: always;"></div>
> ```

Es: inserimento titoli con simboli nel nome come `=`, `+`, `.`, `()` o `'`

```markdown
### utilizzo nel `main.cpp` {#utilizzo-nel-maincpp}
```

Es: inserimento di un elemento centrato

```markdown
<div style="text-align:center;">
<!-- something -->
</div>
```

Es: inserimento di un pdf "srotolato" direttamente all'interno delle note

```markdown
[Nome Del Pdf](../assets/macro-arg/pdfs/nome-file.pdf)
```

# Build di un documento

Ovunque ci si trovi é possibile richiamare il `make.py` e questo genererá le note.pdf con le opzioni specificate, usare `-h` o `--help` per avere maggiori informazioni di funzionamento.

- Iniziare generando un vault con `-i` Verranno generati file e cartelle in cui lavorare

- inserire nuove note e nuovi argomenti dentro il vault mediante `-s`

- convertire note, gruppi di note o l'intero vault con rispettivamente `-n` `-g` e `-a`

Per ulteriori informazioni sul formato dei comandi vedi il [capitolo finale](#eseguire-il-make-python).

# Build di un documento con collaboratori

- Nel caso si inizializzi una banca dati con `-ib` (vedi help per altre info), verrá creato un file `collaborator.md` in questo file é possibile andare a specificare i nomi dei collaboratori e i link ai loro `main.md` dei rispettivi vault inizializzati normalmente con `-i`.

- Successivamente lanciando un `-u` verranno letti i singoli `main.md` creando un main complessivo.

- Una volta completato si conoscono tutte le note di tutti i collaboratori ed é possibile effettuare una nota `custom.md` andando a scrivere la o le note degli specifici collaboratori nell'ordine in cui si vogliono ad esempio, anche ripetendoli nel caso si vogliano in un ordine specifico:

  ```md
  ## Pippo

  - [nota 1](link/alla/nota/1.md)
  - [nota 2](link/alla/nota/2.md)

  ## Paperino

  - [nota 3](link/alla/nota/3.md)
  - [nota 4](link/alla/nota/4.md)

  ## Pippo

  - [nota 5](link/alla/nota/5.md)
  ```

- lanciando poi `-c` verrá convertita come di consueto.

<span style="color: orange;">NOTA:</span> convertendo una nota in questo modo vengono copiate la nota di partenza e tutti gli asset (dei collaboratori specificati nel `custom.md`) nella cartella `C:\Users\<User>\Documents\DocuBank` e vengono immediatamente cancellati dopo la conversione per liberare spazio. Questo implica di avere spazio a disposizione quando si effettua una conversione.

Per ulteriori informazioni sul formato dei comandi vedi il [capitolo finale](#eseguire-il-make-python).

## Eseguire il make python

É un eseguibile che indipendentemente da dove ci si trova quando viene lanciato si entra nel progetto, e genera dentro la cartella `vault/build` l'output generato.

```bash
# help
\scripts\make.py -h
# inizializzazione repo
\scripts\make.py -i
\scripts\make.py -ib
# aggiunta di una nota md
\scripts\make.py -s nome-macro-argomento/nome-nuova-nota.md
# generazione di pdf
\scripts\make.py -n nome-nota-src.md output.pdf
\scripts\make.py -g nome-macro-argomento output.pdf
\scripts\make.py -a output.pdf
\scripts\make.py -c output.pdf
# conversione immagine tikz
\scripts\make.py -nt nome-nota-src.md output.pdf
```
