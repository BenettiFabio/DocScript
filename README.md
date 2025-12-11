# DocScript Docupementation Structure

É una struttura che permette di gestire appunti, documentazione e note direttamente in markdown. Ha il vantaggio di avere una organizzazione per argomenti e permette di Convertire file e interi blocchi di file mediante il tool `pandoc`.

Mediante questa architettura é possibile configurare un ambiente di conversione di pdf con template, yaml e lua filter di default nel caso in cui si utilizzino spesso sempre gli stessi, ma di cambiarli velocemente e temporaneamente senza intaccare l'architettura.

Se inizializzata come banca dati in una cartella di rete condivisa con piú utenti é possibile anche creare un aggregatore di conoscenza tra persone, condividendo appunti, note, e documentazione e potendo prendere in prestito note altrui per farne una documentazione dinamica e piú completa.

Consiglio: genera un repo vuoto per le note in modo da versionarle separate dal sottomodulo, inserisci questo repo come un sottomodulo git, dopo potrai inizializzare la tua struttura di appunti con il comando `--init` garantendo una struttura stabile. Questo ti permette anche di avere gli script e le tue note separate.

Per maggiori informazioni sulle operazioni che puó fare questo sottomodulo lanciare:

```bash
python DocScript/DocScript.py --help
```

## Guida all'inizializzazione

1. <span style="color: brown;">Creazione del repo personale</span>

   Su GitHub o in locale creare un repo git con:

   ```bash
   git init --bare MyDocumentation
   ```

   Questo conterrá la tua documentazione completamente separata dal resto potendo farne backup e versionarla separatamente da tutto.

2. <span style="color: brown;">Clonare il repo ed inserire il sottomodulo</span>

   ```bash
   git clone /path/to/MyDocumentation MyDocs
   cd MyDocs
   git submodule add https://github.com/BenettiFabio/DocScript
   ```

3. <span style="color: brown;">Inizializzare il vault</span>

   A questo punto grazie a DocScript si puó inizializzare un vault in cui iniziare a scrivere la propria documentazione. Ricorda di stare dentro la cartella `MyDocs/`.

   ```bash
   python DocScript/DocScript.py --help
   python DocScript/DocScript.py --init
   ```

   Verrá creato:

   - un **vault** con una struttura standard basata **macro-argomenti** con una note.
   - All'interno del vault, una cartella **assets** per gli allegati dove é anche possibile inserire eventuali icone e loghi da inserire nei file finali.
   - All'interno del vault, una cartella **config** in modo da organizzare tutti i template, lua e yaml personlizzati nel caso si vogliano ottenere risultati differenti. Se si punta ad usarne alcuni spesso é possibile specigicarli nel file **.conf**.
   - Al di fuori del vault invece, i file per le indentazioni di **markdownlint** e **prettier** anch'essi personalizzabili, questo é solo un punto di partenza!.

   Per maggiori informazioni sulla struttura base del progetto proseguire con la lettura.

   Se Hai giá un vault e sai giá come usarlo, ma hai dei collaboratori e vuoi iniziare ad usarlo in gruppo allora puoi inizializzare una banca dati con:

   ```bash
   python DocScript/DocScript.py --init-bank
   ```

   Questo genererá 3 file dentro la cartella `bank/`:

   - `collaborator.md` : in cui specificare con chi lavori.
   - `main.md` : sará un indice complessivo delle note di tutti i collaboratori.
   - `custom.md` : che puoi riempire per compilare le tue note personalizzate.
   - **conf/** : come per il vault classico questo permette di personalizzare la conversione anche tra note di altri utenti che usano la banca.

4. <span style="color: brown;">Compilare le note per creare .pdf e .tex</span>

   A questo punto o hai un _vault_ o hai una _banca_ dati, se sai giá usarli benissimo! **Enjoy!**, in caso contrario vai pure alle procedure di conversione per un vault personale [Qui](#build-di-un-documento) e per una nota con collaboratori in una banca dati [Qui](#build-di-un-documento-con-collaboratori).

   Ricorda peró che le conversioni dei documenti devono rispettare dei constraint specifici quindi se é la tua prima volta qui prosegui pure la lettura con la [struttura del progetto](#struttura-del-progetto)!

# Struttura del progetto

0.  **REGOLA FONDAMENTALE DELLE NOTE:** I nomi delle note devono essere tutti in <span style="color: red;">_minuscolo_</span>, le parole separate da `-`. I nomi delle note sono **TUTTI** descrittivi del loro albero di posizione:

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

1.  `main.md`: Questo file è l'indice di tutta la struttura.

    - Andrà a linkare tutte le pagine del progetto in modo da poterle trovare facilmente nel tempo.
    - Il `main.md` verrá utilizzato come ordine di conversione in modo che, se convertito l'intero vault in un unico pdf si conosce in che ordine devono essere inseriti gli argomenti.

2.  **vault:** Il Vault è la cartella contenente tutte le note.

    - I nomi delle note sono divisi in _macro-argomenti_ nelle sottocartelle del Vault.
    - Se vuoi convertirle tutte in una volte verrá usato l'ordine del main come ordine delle note nel pdf finale.

    > <span style="color: orange;">NOTA:</span> se vuoi convertire solo un certo gruppo ristretto di note sconnesse tra loro in un unico file pdf, puoi creare un file `custom.md` e inserire lí un indice come se fosse un main, con solo le note che desideri e poi usare l'opzione `-c`.

3.  **Assets:** La cartella assets contiene tutti i documenti e le immagini utili al progetto che sono linkate all'interno delle varie note.

    - Dentro la cartella `assets/macro-argomento/` ci sono i relativi docs, imgs, ...
    - La struttura della cartella `assets/` deve essere identica a quella fuori in modo da mantenere semplice il ritrovamento dei file e documenti salvati.
      > _P.S. puoi anche non farlo... a tuo rischio ;) mantenere l'ordine premia in futuro!_
    - É possibile anche andare ad inserire un logo che va poi specificato nello yaml nel main. In questo modo é possibile generare un documento piú completo.

    Consiglio di organizzazione:

    > <span style="color: orange;">NOTA:</span> dentro gli assets ci possono essere le immagini costruite mediante `Python`, `Mermaid` e altro in base alle esigenze.
    > <span style="color: orange;">NOTA:</span> la struttura tipica della cartella di assets é la seguente
    >
    > ```bash
    > vault/assets/
    >        ├── docfiles/
    >        │   └── logo-image.png
    >        ├── macro-arg1/
    >        │   ├── imgs/
    >        │   │   ├── mermaid-imgs/
    >        │   │   │   └── img1-mermaid.md
    >        │   │   ├── python-imgs/
    >        │   │   │   └── img2-python.py
    >        │   │   ├── img1.png
    >        │   │   └── img2.png
    >        │   └── pdfs/
    >        └── macro-arg2/
    > ```
    >
    > In questo modo so sempre che i sorgenti si chiamano con lo stesso nome dell'immagine o del pdf e sono separati dal resto.

4.  **DocScripts:** Questo sottomodulo contiene tutti gli script e le automazioni di default che possono essere eseguiti nel progetto.

    Dentro il sottomodulo é presente la cartella `requirements/` dove sono presenti giá i fonts e altri componenti per velocizzare la messa in servizio del vault.

5.  **./vault/config:** É una cartella in cui sono presenti tutti i file custom che possono essere modificati per la conversione tra cui _yaml_, _template_, _lua filter_, e quale template usare per le _nuove note_. Dentro il file `vault/config/.conf` sono specificati quali devono essere usati nella conversione.

    L'ultilizzo del `.conf` non é strettamente necessario in quanto viene seguito un ordine gerarchico per effettuare le conversioni:

    - se non presente nulla vengono usati quelli di default.
    - se presenti solo alcuni vengono usati quelli e per tutti gli altri i default.
    - se presenti tutti ma vengon specificate le opzioni a terminale `-t --template`, `-y --yaml`, `-l --lua` e `-p --pandoc` questi ultimi hanno <span style="color: red;">massima prioritá</span>.

6.  **./vault/rusco:** É una cartella di note non molto importanti per tutte quelle cose che non si vuole che permangano nel repo, in questo modo quando si converte l'intero repo con il comando `-a` queste note vengono escluse dai check consistenza in modo che si possano fare note temporanee senza preoccuparsi di inserirle nel `main.md`.

# Dipendenze librerie

1. Pandoc: serve a convertire da .tex a .pdf (da inserire negli env Path)
2. MikTeX: serve ad avere LateX installato
3. Fonts: GNU FreeFonts (FreeSans e FreeMono)

# Dipendenze utili VSCode

1. **Markdown TOC:** Gestisce la possibilità di creare Table of content, ovvero degli indici autogenerati in note molto lunghe, in questo modo sono più facilmente navigabili _es:_

   - apri la nota in cui inserire l'elenco
   - Ctrl + Shift + P (comandi VSCode)
   - usa il comando: `Markdown TOC: Insert TOC`
   - usa il comando: `Markdown TOC: Update TOC`

2. **Markdown Preview Enhanced:** Questa serve ad utilizzare componenti di CSS e HTML direttamente nelle note, in questo modo è possibile vedere in preview parole colorate e indentate direttamente sull'editor e non conflitta con `pandoc` durante eventuali conversioni (_a patto di rimanere nei limiti del filtro lua inserito_). Permette di sfruttare lo schema colori presente in "Legenda di aiuto alla coerenza"

3. **Markdown Preview Mermaid Support:** Per visualizzare in tempo reale il codice Mermaid direttamente nella preview di VSCode dirante la generazione di grafici.

   > <span style="color: orange;">NOTA:</span> Una volta creata l'immagine del grafico desiderata, tasto destro ed esporta come png e ritagliarla di conseguenza per inserirla nel documento.

   In Questo modo se si vuole modificare una immagine si può avere direttamente il file generatore con estensione del nome -mermaid.md e l'immagine generata per poter fare modifiche rapide se necessarie. Nel caso in cui si trovasse una immagine inserita nel progetto è anche semplice capire se è una immagine scaricata e aggiunta o una generata e quindi modificabile guardando semplicemente il link.

4. **vscode-pdf:** Visualizza direttamente i pdf sull'Editor senza dover passare per la discovery dei file.

5. **Markdownlint** + **Prettier:** sono una combo di estensioni che permette di segnalare errori di formattazione all'interno di un md file attraverso regole presenti nel file `.markdownlint.json` nella root del vault. Unito a Prettier per correggere direttamente la formattazione al salvataggio del file.

   > <span style="color: darkviolet;">OSS:</span> per implementarli, dopo aver installato le
   > estensioni seguire i seguenti passaggisu `VSCode`:
   >
   > 1. `Ctrl+,` per aprire le impostazioni
   > 2. cerca: `default formatter`
   > 3. imposta `esbenp.prettier-vscode`
   > 4. cerca `format on save` e attiva l'impostazione A questo punto ogni salvataggio della nota verrá automaticamente formattata secondo le regole contenute nel file `.prettierrc`.

# Legenda ed aiuto alla coerenza

Il comando di pandoc per la conversione da markdown a pdf rispetta delle regole (inserite nel `.lua`) e per mantenere il sistema piú longevo possibile non sono stati usati pacchetti troppo complessi. Per ovviare al problema sono state aggiunte regole e template che convertono in modo corretto questo tipo di blocchi css e evidenziature senza problemi, se rispettati questi blocchi non causeranno errori nel pdf finito.

- `<span style="color: darkviolet;">OSS:</span>` `->` <span style="color: darkviolet;">OSS:</span> Questa è una osservazione
- `<span style="color: red;">ATT!:</span>` `->` <span style="color: red;">ATT!:</span> Questo è un attenzione
- `<span style="color: orange;">NOTA:</span>` `->` <span style="color: orange;">NOTA:</span> Questa è una nota
- `<span style="color: skyblue;">RICORDA:</span>` `->` <span style="color: skyblue;">RICORDA:</span> Questo è un blocco ricordo
- `<span style="background-color: yellow;">...</span>` `->` <span style="background-color: yellow;">Questa è una riga evidenziata</span>
- `<span style="text-decoration: underline;">...</span>` `->` <span style="text-decoration: underline;">Questo é un testo sottolineato</span>

- `1. <span style="color: brown;">...</span>` `->` Gli elenchi numerati di una guida da seguire vanno in <span style="color: brown;"> marrone </span>.

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

Es: inserimento di una o piú equazioni matematiche una sotto l'altra racchiudere dentro un blocco verbosity (\`\`\`) specificando il linguaggio `{=latex}`, il contenuto sará quindi latex puro:

```markdown
\begin{align*}
equazione_1\\
equazione_2\\
equazione_3
\end{align*}
```

> <span style="color: orange;">NOTA:</span> non si vedrá in anteprima di VSCode ma in pdf renderá bene.

Es: programmazione yaml pre-build con template di default

```yaml
---
# Configurazioni di Base (Flags per includere/escludere sezioni)
titlepage: true # permette di avere la pagina iniziale con logo e info sotto specificate
headerfooter: true # inserisce footer e header in ogni pagina
draft: true # watermark con la scritta scelta successivamente
toc: true # abilita o disabilita l'indice iniziale
listtables: true # abilita la lista delle tabelle in fondo al documento
listfigures: true # abilita la lista delle figure in fondo al documento

# Dati Aziendali e Documento
CompanyProject: Personal Documentation
CompanyDepartment:
CompanyOffice:
CompanyDesigner: Benetti Fabio
CompanyDesignerCode:
CompanyTechnicalManager:
CompanyTechnicalSupervisor:
CompanyStudyTitle:
CompanyDocumentCode:

# Impostazioni di Layout e Assets
LogoFileName: '../assets/docfiles/logo-docscript'
footerText: 'RISERVATO - PROPRIETÀ DI Company S.p.A.'

# Configurazione Watermark (se draft: true)
watermark_text: 'Draft'

# Configurazioni TOC
tocDepth: 5
---
```

# Build di un documento

Ovunque ci si trovi é possibile richiamare il `DocScript.py` e questo genererá le note.pdf con le opzioni specificate, usare `-h` o `--help` per avere maggiori informazioni di funzionamento.

- Iniziare generando un vault con `-i` Verranno generati file e cartelle in cui lavorare.

- Inserire nuove note e nuovi argomenti dentro il vault mediante `-s`.

- Prima di convertire il documento ufficiale dare uno sguardo al `/vault/config/.conf` per impostare i file da usare durante la conversione. Sopratutto per quanto riguarda il file `yaml` il quale contiene i parametri di conversione che verranno usati nel `template` scelto in modo da ottenere risultati piú o meno complessi in base alle esigenze. Nel `.conf` é possibile anche scegliere una nota di base da inserire come punto di partenza per tutte le nuove note, cosí da avere uno standard.

- Convertire note, gruppi di note (un macro-argomento) o l'intero vault con rispettivamente `-n` `-g` e `-a`.

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

- lanciando poi `-c` verrá convertita come di consueto. Verranno usati _template_, _yaml_, _lua_ di default a meno di specifiche nel `.conf`

<span style="color: orange;">NOTA:</span> convertendo una nota in questo modo vengono copiate la nota di partenza e tutti gli asset (dei collaboratori specificati nel `custom.md`) nella cartella `C:\Users\<User>\Documents\DocScript` e vengono immediatamente cancellati dopo la conversione per liberare spazio. Questo implica di avere spazio a disposizione quando si effettua una conversione.

Per ulteriori informazioni sul formato dei comandi vedi il [capitolo finale](#eseguire-il-make-python).

## Eseguire il make python

É un eseguibile che indipendentemente da dove ci si trova quando viene lanciato si entra nel progetto, e genera dentro la cartella `vault/build` l'output generato.

```bash
# help
\scripts\DocScript.py -h
# inizializzazione repo
\scripts\DocScript.py -i
\scripts\DocScript.py -ib
# aggiunta di una nota md
\scripts\DocScript.py -s nome-macro-argomento/nome-nuova-nota.md
# generazione di pdf
\scripts\DocScript.py -n nome-nota-src.md output.pdf
\scripts\DocScript.py -g nome-macro-argomento output.pdf
\scripts\DocScript.py -a output.pdf
\scripts\DocScript.py -c output.pdf
# queste ultime quattro opzioni -n -g -a -c accettano modifiche temporanee
# aggiungendo -y -l -t -p per cambiare yaml, lua, template e pandoc options
# anche contemporaneamente
\scripts\DocScript.py -n nome-nota-src.md output.pdf -y path/to/yaml/file.yaml -t path/to/template/file.tex
```
