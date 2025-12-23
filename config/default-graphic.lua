-- https://stackoverflow.com/questions/62831191/using-span-for-font-color-in-pandoc-markdown-for-both-html-and-pdf
-- https://bookdown.org/yihui/rmarkdown-cookbook/font-color.html
-- https://ulriklyngs.com/post/2019/02/20/how-to-use-pandoc-filters-for-advanced-customisation-of-your-r-markdown-documents/

function Span(el)
  local stylestr = el.attributes.style or ""
  stylestr = stylestr:gsub("%s+", " ")  -- Normalizza spazi

  -- Estrazione proprietà CSS
  local fg_color = string.match(stylestr, "color:%s*([^;]+);")
  local bg_color = string.match(stylestr, "background%-color:%s*([^;]+);")
  local underline = string.match(stylestr, "text%-decoration:%s*underline") or el.classes:includes("underline")

  -- Mappa colori di sfondo → LaTeX custom colors
  local color_map = {
    yellow = "hlyellow",
    red = "hlred",
    green = "hlgreen",
    violet = "hlviolet",
    orange = "hlorange",
    skyblue = "hlskyblue"
  }

  if bg_color and color_map[bg_color] then
    bg_color = color_map[bg_color]
  end

  -- Generazione LaTeX
  if FORMAT:match('latex') then
    local inner = pandoc.utils.stringify(el.content)

    -- Applica colore del testo solo se non c'è l'evidenziatore
    if fg_color and not bg_color then
      inner = "\\textcolor{" .. fg_color .. "}{" .. inner .. "}"
    end

    -- Applica sfondo (evidenziazione)
    if bg_color then
      inner = "\\colorbox{" .. bg_color .. "}{" .. inner .. "}"
    end

    -- Applica sottolineatura
    if underline then
      inner = "\\underline{" .. inner .. "}"
    end

    return pandoc.RawInline("latex", inner)
  else
    -- In altri formati (HTML, ecc.) non alteriamo l'output
    return el
  end
end

function RawBlock(el)
  if el.format == "markdown" or el.format == "latex" then
    -- Sostituzione dei caratteri box-drawing con ASCII
    local replacements = {
      ["├"] = "|",
      ["└"] = "`",
      ["─"] = "-",
      ["│"] = "|",
      ["┌"] = "+",
      ["┐"] = "+",
      ["┬"] = "+",
      ["┴"] = "+",
      ["┼"] = "+",
      ["╰"] = "`",
      ["╭"] = "+",
    }

    local text = el.text
    for k, v in pairs(replacements) do
      text = text:gsub(k, v)
    end
    return pandoc.RawBlock(el.format, text)
  end
end

function CodeBlock(el)
  -- Stessa cosa per blocchi di codice veri e propri
  local replacements = {
    ["├"] = "|",
    ["└"] = "`",
    ["─"] = "-",
    ["│"] = "|",
    ["┌"] = "+",
    ["┐"] = "+",
    ["┬"] = "+",
    ["┴"] = "+",
    ["┼"] = "+",
    ["╰"] = "`",
    ["╭"] = "+",
  }

  local text = el.text
  for k, v in pairs(replacements) do
    text = text:gsub(k, v)
  end
  return pandoc.CodeBlock(text, el.attr)
end

-- per convertire i blocchi delle immagini con dimensione
-- function Image(img)
--   local width = img.attributes["width"] or "\\linewidth"
--   local path = img.src
--   local latex = string.format("\\includegraphics[width=%s]{%s}", width, path)

--   -- Restituisce sempre RawInline
--   return pandoc.RawInline("latex", latex)
-- end

function Image(img)
  local raw_width = img.attributes["width"]
  local width

  if raw_width then
    -- Se è una percentuale (es. 50%), converti in frazione di \linewidth
    local percent = raw_width:match("^(%d+)%%$")
    if percent then
      local fraction = tonumber(percent) / 100
      width = string.format("%.3f\\linewidth", fraction)
    else
      -- Usa il valore così com'è (es. "5cm" o "\\linewidth")
      width = raw_width
    end
  else
    width = "\\linewidth"
  end

  local path = img.src
  local latex = string.format("\\includegraphics[width=%s]{%s}", width, path)

  return pandoc.RawInline("latex", latex)
end

-- Funzione per gestire i div
function Div(el)
  if el.attributes.style == "text-align:center;" then
    -- Blocchi centrati
    table.insert(el.content, 1, pandoc.RawBlock('latex', '\\begin{center}'))
    table.insert(el.content, pandoc.RawBlock('latex', '\\end{center}'))
    return el.content

  elseif el.attributes.style == "page-break-after: always;" then
    -- Interruzione di pagina
    return pandoc.RawBlock('latex', '\\newpage')

  else
    -- Altri div rimangono invariati
    return el
  end
end

-- include-pdf 
function Para(el)
  -- Se il paragrafo contiene esattamente un Link
  if #el.content == 1 and el.content[1].t == "Link" then
    local link = el.content[1]
    local target = link.target
    if target:match("%.pdf$") then
      if FORMAT == "latex" then
        return pandoc.RawBlock("latex", "\\includepdf[pages=-]{" .. target .. "}")
      else
        return el  -- normale link per HTML/preview
      end
    end
  end
end

-- -- Gestione della larghezza delle Tabelle
-- function Table(el)
--   local numCols = #el.colspecs
  
--   if numCols == 0 then
--     return el
--   end
  
--   -- Strategia: distribuisci lo spazio in base al numero di colonne
--   -- Le prime n-1 colonne ottengono una frazione equa dello spazio disponibile
--   -- L'ultima colonna prende il resto (tipicamente più grande)
  
--   local spaceForContent = 0.6  -- 60% per le colonne di contenuto
--   local spaceForLast = 0.4     -- 40% per l'ultima colonna (minimo garantito)
  
--   -- Se ci sono poche colonne, possiamo dare più spazio alle prime
--   if numCols == 2 then
--     spaceForContent = 0.3
--     spaceForLast = 0.7
--   elseif numCols == 3 then
--     spaceForContent = 0.5
--     spaceForLast = 0.5
--   end
  
--   -- Calcola larghezza per ogni colonna di contenuto
--   local contentColWidth = spaceForContent / (numCols - 1)
  
--   -- Applica le larghezze
--   for i = 1, numCols - 1 do
--     el.colspecs[i] = {el.colspecs[i][1], contentColWidth}
--   end
  
--   el.colspecs[numCols] = {el.colspecs[numCols][1], spaceForLast}
  
--   return el
-- end





-- Mappa emoji shortcode in formato github --> comando LaTeX Typicons
local emoji_map = {
  warning = "\\tiWarningOutline",
  -- aggiungi qui altre mappature se ti servono
  -- esempio:
  -- info    = "\\tiInfoOutline",
  -- error   = "\\tiErrorOutline",
  information_source = "\\tiInfoLargeOutline",
  white_check_mark = "\\tiInputChecked",
  bookmark = "\\tiBookmark",
  no_entry_sign = "\\tiCancel",
  x = "\\tiDelete",
  computer = "\\tiDeviceDesktop",
  heavy_minus_sign = "\\tiMinusOutline",
  wrench = "\\tiSpanner",
  bulb = "\\tiLightbulb",
  key = "\\tiKeyOutline",
  -- ... 
}

-- Funzione di utilità: verifica se il blocco è un RawInline LaTeX
local function is_latex_raw(inline)
  return inline.t == "RawInline" and inline.format == "latex"
end

-- Converte un testo del tipo ":warning:" in un Inline Raw LaTeX
local function emoji_to_latex(shortcode)
  local cmd = emoji_map[shortcode]
  if not cmd then return nil end
  -- Aggiunge uno spazio alla fine del comando LaTeX
  local cmd_with_space = cmd .. "\\ "
  -- Ritorna un RawInline LaTeX contenente il comando (con spazio LaTeX)
  return pandoc.RawInline("latex", cmd_with_space)
end

-- --------------------------------------------------------------------
-- 1. Trasforma le emoji presenti nei paragrafi (e in altri blocchi
--    di tipo Inlines) quando il target è LaTeX.
-- --------------------------------------------------------------------
-- 3️⃣  Funzione principale: opera su ogni Inline di tipo Str
function Inline(el)
  -- Operiamo solo se il formato di destinazione è LaTeX
  if not FORMAT:match("^latex") then return nil end

  if el.t ~= "Str" then return nil end   -- gestiamo solo stringhe

  -- Pattern che accetta lettere, cifre e underscore:
  --   :nome:          → %w+
  --   :nome_con_ _:   → %w[_%w]*
  local pattern = ":(%w[_%w]*)%:"

  local new_inlines = {}
  local start = 1

  while true do
    local s, e, name = el.text:find(pattern, start)
    if not s then
      -- Nessun altro match: aggiungi il resto della stringa
      table.insert(new_inlines,
        pandoc.Str(el.text:sub(start)))
      break
    end

    -- Parte precedente all'emoji (se presente)
    if s > start then
      table.insert(new_inlines,
        pandoc.Str(el.text:sub(start, s - 1)))
    end

    -- Conversione emoji → LaTeX (se conosciuta)
    local latex = emoji_to_latex(name)
    if latex then
      table.insert(new_inlines, latex)
    else
      -- Emoji sconosciuta: mantieni il testo originale
      table.insert(new_inlines,
        pandoc.Str(":" .. name .. ":"))
    end

    start = e + 1
  end

  -- Restituiamo una lista di inlines (o l’unico elemento)
  if #new_inlines > 1 then
    return pandoc.Inlines(new_inlines)
  else
    return new_inlines[1]
  end
end

-- --------------------------------------------------------------------
-- 2. (Facoltativo) Rimuove le emoji dai formati non‑LaTeX.
--    Se preferisci mantenere il testo “:warning:” anche in HTML, commenta
--    questa funzione.
-- --------------------------------------------------------------------
-- function Str(el)
--   if not FORMAT:match("^latex") then
--     -- Sostituisci gli shortcode con una stringa vuota oppure con
--     -- un fallback testuale a tua scelta.
--     -- local cleaned = el.text:gsub(":(%w+):", "")
--     -- pattern: tra i due due punti sono accettati solo caratteri alfanumerici e l’underscore (_).
--     local cleaned = el.text:gsub(":(%w[_%w]*)%:", "")
--     if cleaned ~= el.text then
--       return pandoc.Str(cleaned)
--     end
--   end
--   return nil
-- end