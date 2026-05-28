# DocScript Documentation Structure

> 🇮🇹 [Leggi in italiano](README.it.md) | 🇬🇧 You are reading the English version

It is a structure that allows you to manage notes, documentation and memos directly in markdown. It has the advantage of being organized by topics and allows you to convert files and entire blocks of files using the `pandoc` tool.

Through this architecture it is possible to configure a PDF conversion environment with default templates, yaml and lua filters for cases where the same ones are used frequently, while also being able to change them quickly and temporarily without affecting the architecture.

If initialized as a database in a shared network folder with multiple users, it is also possible to create a knowledge aggregator among people, sharing notes, documentation and being able to borrow other people's notes to create dynamic and more complete documentation.

Tip: generate an empty repo for your notes so that they are versioned separately from the submodule, insert this repo as a git submodule, then you can initialize your notes structure with the `--init` command ensuring a stable structure. This also allows you to keep your scripts and notes separate.

For more information on the operations this submodule can perform, run:

```bash
python DocScript/DocScript.py --help
```

## Initialization Guide

1. <span style="color: brown;">Creating the personal repo</span>

   On GitHub or locally, create a git repo with:

   ```bash
   git init --bare MyDocumentation
   ```

   This will contain your documentation completely separate from everything else, allowing you to back it up and version it independently.

2. <span style="color: brown;">Clone the repo and add the submodule</span>

   ```bash
   git clone /path/to/MyDocumentation MyDocs
   cd MyDocs
   git submodule add https://github.com/BenettiFabio/DocScript
   ```

3. <span style="color: brown;">Initialize the vault</span>

   At this point, thanks to DocScript, you can initialize a vault in which to start writing your documentation. Remember to be inside the `MyDocs/` folder.

   ```bash
   python DocScript/DocScript.py --help
   python DocScript/DocScript.py --init
   ```

   The following will be created:
   - a **vault** with a standard structure based on **macro-topics** with a note.
   - Inside the vault, an **assets** folder for attachments where it is also possible to add icons and logos to be included in the final files.
   - Inside the vault, a **config** folder to organize all custom templates, lua and yaml files in case you want to obtain different results. If you plan to use some of them frequently, you can specify them in the **.conf** file.
   - Outside the vault, the configuration files for **markdownlint** and **prettier** indentation, also customizable — this is just a starting point!

   For more information on the base structure of the project, continue reading.

   If you already have a vault and know how to use it, but have collaborators and want to start using it as a group, you can initialize a database with:

   ```bash
   python DocScript/DocScript.py --init-bank
   ```

   This will generate 3 files inside the `bank/` folder:
   - `collaborator.md` : where you specify who you work with.
   - `main.md` : it will be an overall index of all collaborators' notes.
   - `custom.md` : which you can fill in to compile your personalized notes.
   - **conf/** : as with the classic vault, this allows you to customize the conversion even among notes from other users who use the bank.

4. <span style="color: brown;">Compile the notes to create .pdf and .tex</span>

   At this point you either have a _vault_ or a _database_; if you already know how to use them, great! **Enjoy!**, otherwise go to the conversion procedures for a personal vault [Here](#building-a-document) and for a note with collaborators in a database [Here](#building-a-document-with-collaborators).

   Remember though that document conversions must respect specific constraints, so if this is your first time here, continue reading with the [project structure](#project-structure)!

# Project Structure

0.  **FUNDAMENTAL RULE FOR NOTES:** Note names must all be in <span style="color: red;">_lowercase_</span>, words separated by `-`. Note names are **ALL** descriptive of their position tree:

    _e.g.:_

    ```bash
    vault/
    ├── main.md
    ├── proj1/
    │   ├── main.proj1.sub-proj1.main.md
    │   ├── sub-proj1/
    │   │   └── main.proj1.sub-proj1.sub-arg3.md
    │   ├── main.proj1.sub-arg1.md
    │   └── main.proj1.sub-arg2.md
    ├── proj2/
    │   └── main.proj2.sub-arg1.md
    └── proj3/
        └── main.proj3.sub-arg1.md
    ```

    This way, searching for files and their contents is simplified, and it also simplifies the use of any scripts that can leverage the name for possible automations.

    > <span style="color: red;">ATT!:</span> Every new page added must be inserted directly
    > into the overall index (`main.md`)

1.  `main.md`: This file is the index of the entire structure.
    - It will link all the project pages so they can be easily found over time.
    - The `main.md` will be used as the conversion order so that, if the entire vault is converted into a single pdf, the order in which topics should be included is known.
    - The `main.md` can in turn contain other main files recursively. If there are subfolders, they **must** have their own main files describing the contents of the folder.

2.  **vault:** The Vault is the folder containing all the notes.
    - Note names are divided into _macro-topics_ in the Vault's subfolders.
    - If you want to convert them all at once, the main's order will be used as the order of notes in the final pdf.

    > <span style="color: orange;">NOTE:</span> if you want to convert only a certain limited group of unrelated notes into a single pdf file, you can create a `custom.md` file and insert an index there as if it were a main, with only the notes you want, and then use the `-c` option.

3.  **Assets:** The assets folder contains all documents and images useful to the project that are linked within the various notes.
    - Inside the `assets/macro-topic/` folder there are the related docs, imgs, ...
    - The structure of the `assets/` folder must be identical to the one outside so as to keep it simple to find saved files and documents.
      > _P.S. you don't have to... at your own risk ;) keeping order pays off in the future!_
    - It is also possible to add a logo which must then be specified in the yaml in the main. This way it is possible to generate a more complete document.

    Organization tip:

    > <span style="color: orange;">NOTE:</span> inside the assets there can be images built using `Python`, `Mermaid` and others depending on the needs.
    > <span style="color: orange;">NOTE:</span> the typical structure of the assets folder is as follows
    >
    > ```bash
    > vault/assets/
    >        ├── docfiles/
    >        │   └── logo-image.png
    >        ├── proj1/
    >        │   ├── imgs/
    >        │   │   ├── mermaid-imgs/
    >        │   │   │   └── img1-mermaid.md
    >        │   │   ├── python-imgs/
    >        │   │   │   └── img2-python.py
    >        │   │   ├── img1.png
    >        │   │   └── img2.png
    >        │   └── pdfs/
    >        └── proj2/
    > ```
    >
    > This way I always know that the source files have the same name as the image or pdf and are separated from the rest.

4.  **DocScripts:** This submodule contains all the default scripts and automations that can be run in the project.

    Inside the submodule there is the `requirements/user/` folder which already contains fonts and other components to speed up the vault's initial setup.

5.  **./vault/config:** It is a folder containing all the custom files that can be modified for conversion, including _yaml_, _template_, _lua filter_, and which template to use for _new notes_. Inside the `vault/config/.conf` file, which ones should be used during conversion are specified. For more information see the [Config files priority chapter](#priority-and-usage-of-configuration-files)

    The use of `.conf` is not strictly necessary as a hierarchical order is followed to perform conversions:
    - if nothing is present, the defaults are used.
    - if only some are present, those are used and for all others the defaults are applied.
    - if all are present but the terminal options `-t --template`, `-y --yaml` and `-l --lua` are specified, the latter have <span style="color: red;">highest priority</span>.

6.  **./vault/rusco:** It is a folder for less important notes, for all those things you don't want to persist in the repo. This way, when converting the entire repo with the `-a` command, these notes are excluded from consistency checks so that you can take temporary notes without worrying about inserting them in `main.md`.

# Library Dependencies

1. Pandoc: used to convert from .tex to .pdf (must be added to the Path env)
2. MikTeX: used to have LateX installed
3. Fonts: GNU FreeFonts (FreeSans and FreeMono)

# Useful VSCode Dependencies

1. **Markdown TOC:** (Editor: _Joffrey Kern_) Manages the ability to create a Table of Contents, i.e. auto-generated indexes in very long notes, making them easier to navigate _e.g.:_
   - open the note where you want to insert the list
   - Ctrl + Shift + P (VSCode commands)
   - use the command: `Markdown TOC: Insert TOC`
   - use the command: `Markdown TOC: Update TOC`

2. **Markdown Preview Enhanced:** (Editor: _Yiyi Wang_) This is used to utilize CSS and HTML components directly in the notes, allowing you to see colored and indented words in preview directly in the editor and it does not conflict with `pandoc` during any conversions (_as long as you stay within the limits of the lua filter inserted_). It allows you to use the color scheme present in "Consistency Aid Legend".

3. **Markdown Preview Mermaid Support:** (Editor _Matt Bierner_) To view Mermaid code in real time directly in the VSCode preview during graph generation.

   > <span style="color: orange;">NOTE:</span> Once the desired graph image is created, right-click and export as png and crop it accordingly to insert it in the document.

   This way, if you want to modify an image, you can directly have the generator file with the extension -mermaid.md and the generated image to make quick changes if needed. In case an image inserted in the project is found, it is also easy to understand whether it is a downloaded and added image or a generated and therefore modifiable one by simply looking at the link.

4. **vscode-pdf:** (Editor: _tomoki1207_) Displays PDFs directly in the Editor without having to go through the file discovery.

5. **Markdownlint** (Editor: _David Anson_) + **Prettier:** (Editor: _Prettier_) are a combo of extensions that allows you to flag formatting errors inside an md file through rules present in the `.markdownlint.json` file in the vault root. Combined with Prettier to directly fix the formatting when saving the file.

   > <span style="color: darkviolet;">OSS:</span> to implement them, after installing the
   > extensions follow these steps in `VSCode`:
   >
   > 1. `Ctrl+,` to open settings
   > 2. search: `default formatter`
   > 3. set `esbenp.prettier-vscode`
   > 4. search `format on save` and enable the setting. From this point on, every time you save a note it will be automatically formatted according to the rules contained in the `.prettierrc` file.

# Consistency Aid Legend

The pandoc command for converting from markdown to pdf respects certain rules (inserted in the `.lua`) and to keep the system as long-lived as possible, no overly complex packages have been used. To work around the problem, rules and templates have been added that correctly convert this type of CSS blocks and highlights without issues; if respected, these blocks will not cause errors in the finished pdf.

- `<span style="color: darkviolet;">OSS:</span>` `->` <span style="color: darkviolet;">OSS:</span> This is an observation
- `<span style="color: red;">ATT!:</span>` `->` <span style="color: red;">ATT!:</span> This is a warning
- `<span style="color: orange;">NOTE:</span>` `->` <span style="color: orange;">NOTE:</span> This is a note
- `<span style="color: skyblue;">REMEMBER:</span>` `->` <span style="color: skyblue;">REMEMBER:</span> This is a reminder block
- `<span style="background-color: yellow;">...</span>` `->` <span style="background-color: yellow;">This is a highlighted line</span>
- `<span style="text-decoration: underline;">...</span>` `->` <span style="text-decoration: underline;">This is underlined text</span>

- `1. <span style="color: brown;">...</span>` `->` Numbered lists of a guide to follow go in <span style="color: brown;"> brown </span>.

> <span style="color: orange;">NOTE:</span> Highlights are **always** replaced with custom colors `hl*` (so `yellow` = `hlyellow`) which are present in the conversion-template.tex that makes the highlighter colors in the pdf more pleasant while maintaining real-time Preview visibility. If others are added, add them to `.lua` as well.

> <span style="color: orange;">NOTE:</span> Underlined text is not included in markdown with a symbol like `*` for bold and `_` for italic, so it is necessary to use the `<span>` block converted with the lua filter.

_E.g.:_ image insertion

```markdown
As seen in image Fig.\ref{img: image-title} _Image title_
![Image title.\label{img: image-title}](../assets/macro-arg/imgs/image-name.png){width=\linewidth}

![Image title](../assets/macro-arg/imgs/image-name.png){width=\linewidth}
![Image title](../assets/macro-arg/imgs/image-name.png){width=50%}
```

> <span style="color: orange;">NOTE:</span> In some cases when adding an image it may be moved to the beginning and therefore to the wrong position. To prevent this from happening, it is better to add a page break before the image or before the topic.
>
> ```markdown
> <div style="page-break-after: always;"></div>
> ```

E.g.: inserting titles with symbols in the name such as `=`, `+`, `.`, `()` or `'`

```markdown
### usage in `main.cpp` {#usage-in-maincpp}
```

E.g.: inserting a centered element

```markdown
<div style="text-align:center;">
<!-- something -->
</div>
```

E.g.: inserting an "unrolled" pdf directly inside the notes

```markdown
[Pdf Name](../assets/macro-arg/pdfs/file-name.pdf)
```

E.g.: allowed Emoji insertion

> <span style="color: orange;">NOTE:</span> if some emoticons are missing, modify the lua filter so that they are supported.

Emojis can be inserted using the GitHub format

| Emoji                  | LaTeX Command         | Description                           |
| :--------------------- | :-------------------- | :------------------------------------ |
| `:warning:`            | `\tiWarningOutline`   | :warning: Warning triangle            |
| `:information_source:` | `\tiInfoLargeOutline` | :information_source: Info             |
| `:white_check_mark:`   | `\tiInputChecked`     | :white_check_mark: Confirmation check |
| `:bookmark:`           | `\tiBookmark`         | :bookmark: Bookmark                   |
| `:no_entry_sign:`      | `\tiCancel`           | :no_entry_sign: No entry sign         |
| `:x:`                  | `\tiDelete`           | :x: Closing cross                     |
| `:computer:`           | `\tiDeviceDesktop`    | :computer: Computer screen            |
| `:heavy_minus_sign:`   | `\tiMinusOutline`     | :heavy_minus_sign: Minus sign         |
| `:wrench:`             | `\tiSpanner`          | :wrench: Wrench (maintenance)         |
| `:bulb:`               | `\tiLightbulb`        | :bulb: Light bulb (idea/suggestion)   |
| `:key:`                | `\tiKeyOutline`       | :key: Key                             |
| `:star:`               | `\tiStar`             | :star: Star                           |

E.g.: inserting one or more mathematical equations one below the other, enclose them inside a verbosity block (\`\`\`) specifying the language `{=latex}`, the content will therefore be pure latex, or the simply math block composed by `$$`:

```markdown
$$
\begin{aligned}
equation_1\\
equation_2\\
equation_3
\end{aligned}
$$
```

> <span style="color: orange;">NOTE:</span> it will not be visible in VSCode preview but will render well in pdf.

E.g.: pre-build yaml programming with default template

```yaml
---
# Basic Configurations (Flags to include/exclude sections)
titlepage: true # allows having the initial page with logo and info specified below
headerfooter: true # inserts footer and header on every page
draft: true # watermark with the text chosen below
toc: true # enables or disables the initial index
listtables: true # enables the list of tables at the end of the document
listfigures: true # enables the list of figures at the end of the document

# Company and Document Data
CompanyProject: Personal Documentation
CompanyDepartment:
CompanyOffice:
CompanyDesigner: Benetti Fabio
CompanyDesignerCode:
CompanyTechnicalManager:
CompanyTechnicalSupervisor:
CompanyStudyTitle:
CompanyDocumentCode:

# Layout and Assets Settings
LogoFileName: '../assets/docfiles/logo-docscript'
footerText: 'Confidential - Property of Company S.p.A.'

# Watermark Configuration (if draft: true)
watermark_text: 'Draft'

# TOC Configurations
tocDepth: 5
---
```

# Building a Document

From wherever you are, you can invoke `DocScript.py` and it will generate the notes.pdf with the specified options; use `-h` or `--help` for more information on how it works.

- Start by generating a vault with `-i`. Files and folders to work in will be generated.

- Insert new notes and new topics inside the vault using `-s`.

- Before converting the official document, take a look at `/vault/config/.conf` to set the files to use during conversion. Especially regarding the `yaml/` file which contains the conversion parameters that will be used in the chosen `template/` in order to obtain more or less complex results based on the needs. In the `.conf` it is also possible to choose a base note to insert as a starting point for all new notes, so as to have a standard.

- Convert notes, groups of notes (a macro-topic) or the entire vault with `-n` `-g` and `-a` respectively.

For further information on the command format see the [final chapter](#running-the-python-make).

# Building a Document with Collaborators

- If you initialize a database with `-ib` (see help for more info), a `collaborator.md` file will be created. In this file you can specify the names of the collaborators and the links to their `main.md` of their respective vaults initialized normally with `-i`.

- Subsequently, by running `-u`, the individual `main.md` files will be read creating an overall main.

- Once completed, all notes from all collaborators are known and it is possible to create a `custom.md` note by writing the note or notes of specific collaborators in the order you want them, for example, also repeating them in case you want them in a specific order:

  ```md
  ## Mickey Mouse

  - [note 1](link/to/note/1.md)
  - [note 2](link/to/note/2.md)

  ## Donald Duck

  - [note 3](link/to/note/3.md)
  - [note 4](link/to/note/4.md)

  ## Mickey Mouse

  - [note 5](link/to/note/5.md)
  ```

- then by running `-c` it will be converted as usual. Default _template_, _yaml_, _lua_ will be used unless specified in the `.conf`

<span style="color: orange;">NOTE:</span> when converting a note this way, the source note and all assets (of the collaborators specified in `custom.md`) are copied to the `C:\Users\<User>\Documents\DocScript` folder and immediately deleted after conversion to free up space. This implies having available space when performing a conversion.

For further information on the command format see the [final chapter](#running-the-python-make).

## Running the Python Make

It is an executable that, regardless of where you are when it is launched, enters the project and generates the output inside the `vault/build` folder.

```bash
# help
\scripts\DocScript.py -h
# repo initialization
\scripts\DocScript.py -i
\scripts\DocScript.py -ib
# adding a md note
\scripts\DocScript.py -s macro-topic-name/new-note-name.md
# pdf generation
\scripts\DocScript.py -n source-note-name.md output.pdf
\scripts\DocScript.py -g macro-topic-name output.pdf
\scripts\DocScript.py -a output.pdf
\scripts\DocScript.py -c output.pdf
# these last four options -n -g -a -c accept temporary modifications
# by adding -y -l -t -p -T to change yaml, lua, template and pandoc options and NoteTitle
# even simultaneously
\scripts\DocScript.py -n source-note-name.md output.pdf -y path/to/yaml/file.yaml -t path/to/template/file.tex -T "Custom Note Title"
```

## Priority and usage of configuration files

During document generation, DocScript follows a strict configuration hierarchy.

### 1. Vault configuration files (`/vault/config/`)

- YAML, templates, and plugins are loaded from this directory.
- These files are automatically created during project initialization.
- They are fully editable by the user.
- If deleted, the system falls back to internal default configuration.
- If you don't like using them, you can comment on their content and they will not be considered.

### 2. Default system configuration (fallback)

- If vault configuration files are missing or invalid,
  built-in defaults are used instead.

### 3. Command-line interface (CLI overrides)

- CLI options always override local configuration files.
- Examples: `--yaml`, `--template`, `--lua`, `--pandoc`.

### 4. Document title (`-T / --title`)

- The title follows an explicit override rule:
  - If `--title` is provided, it is always used.
  - It overrides any title defined inside the YAML file.
  - If not provided, the YAML title is used.
  - If neither exists, a fallback title is generated from the group or file name.
