# Documentation Stucture

Developer Documentation Structure
Consiglio: genera un repo vuoto, e iniserisci questo repo come un sottomodulo git, dopo potrai inizializzare la tua struttura di appunti con il comando `--init` garantendo una struttura stabile. Questo ti permette anche di avere gli script e le tue note separate.

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

5. **./vault/rusco:** É una cartella temporanea in questo modo quando si converte l'intero repo con il comando `-a` queste note vengono escluse dal check di consistenza in modo che si possano fare note temporanee senza preoccuparsi di inserire le `main.md`.

# Dipendenze utili VSCode

1. **Markdown TOC:** Gestisce la possibilità di creare Table of content, ovvero degli indici autogenerati in note molto lunghe, in questo modo sono più facilmente navigabili _es:_

   - apri la nota in cui inserire l'elenco
   - Ctrl + Shift + P (comandi VSCode)
   - usa il comando: `Markdown TOC: Insert TOC`
   - usa il comando: `Markdown TOC: Update TOC`

2. **Markdown Preview Enhanced:** Questa serve ad utilizzare componenti di CSS e HTML direttamente nelle note, in questo modo è possibile vedere in preview parole colorate e indentate direttamente sull'editor e non conflitta con `pandoc` durante eventuali conversioni. Permette di sfruttare lo schema colori presente in "Legenda dei colori"

3. **Markdown Preview Mermaid Support:** Usare il mermaid per creare grafici, i file .md devono chiamarsi con lo stesso nome dell'immagine che andranno a generare e saranno nella cartella vault/assets/macro-argomento/mermaid/.

   > <span style="color: orange;">NOTA:</span> Una volta creata l'immagine del grafico desiderata, tasto destro ed esporta come png e ritagliarla di conseguenza.

   In Questo modo se si vuole modificare una immagine si può avere direttamente il file generatore con estensione del nome -mermaid.md e l'immagine generata per poter fare modifiche rapide se necessarie. Nel caso in cui si trovasse una immagine inserita nel progetto è anche semplice capire se è una immagine scaricata e aggiunta o una generata e quindi modificabile guardando semplicemente il link.

4. **Markdownlint** + **Prettier:** sono una combo di estensioni che permette di segnalare errori di formattazione all'interno di un md file attraverso regole presenti nel file `.markdownlint.json` nella root. Unito a Prettier per correggere direttamente la formattazione.

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

# Dipendenze librerie

1. Pandoc: serve a convertire da .tex a .pdf

2. MikTeX: serve ad avere LateX installato

3. Fonts: GNU FreeFonts (FreeSans e FreeMono)

# Build di un documento

Ovunque ci si trovi é possibile richiamare il `make.py` e questo genererá le note.pdf con le opzioni specificate, usare `-h` o `--help` per avere maggiori informazioni di funzionamento.

## Eseguire il make python

É un eseguibile che indipendentemente da dove ci si trova quando viene lanciato si entra nel progetto, e genera dentro la cartella `vault/build` l'output generato.

```bash
# help
\scripts\make.py -h
# inizializzazione repo
\scripts\make.py -i
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
