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

-- Gestione della larghezza delle Tabelle
function Table(el)
  local numCols = #el.colspecs
  
  if numCols == 0 then
    return el
  end
  
  local function getCellText(cell)
    local text = ""
    for _, block in ipairs(cell.contents) do
      if block.t == "Plain" or block.t == "Para" then
        for _, inline in ipairs(block.content) do
          if inline.t == "Str" then
            text = text .. inline.text
          elseif inline.t == "Space" then
            text = text .. " "
          elseif inline.t == "Code" then
            text = text .. inline.text
          end
        end
      end
    end
    return text
  end
  
  -- 1. Inizializzazione e tracciamento della lunghezza
  local maxWordLength = {}
  local totalTextLength = {}
  local maxCellLength = {} -- Lunghezza massima di una singola cella (riga)
  
  for i = 1, numCols do
    maxWordLength[i] = 0
    totalTextLength[i] = 0
    maxCellLength[i] = 0
  end
  
  -- Analisi
  local function analyzeContent(rows)
    for _, row in ipairs(rows) do
      for colIdx, cell in ipairs(row.cells) do
        local text = getCellText(cell)
        local textLength = #text

        totalTextLength[colIdx] = totalTextLength[colIdx] + textLength
        
        -- Aggiorna la lunghezza della cella più lunga in questa colonna
        maxCellLength[colIdx] = math.max(maxCellLength[colIdx], textLength) 
        
        for word in text:gmatch("%S+") do
          maxWordLength[colIdx] = math.max(maxWordLength[colIdx], #word)
        end
      end
    end
  end

  if el.head and el.head.rows then analyzeContent(el.head.rows) end
  for _, tbody in ipairs(el.bodies) do analyzeContent(tbody.body) end
  
  -- 2. Verifica della "Semplicità Orrizzontale"
  
  local totalRequiredWidth = 0
  local CHAR_TO_PERCENT = 0.01 -- Stima conservativa: 1% di larghezza per 10 caratteri
  local MARGIN_PER_COL = 0.03  -- Margine di sicurezza per colonna
  
  for i = 1, numCols do
    -- Stima la larghezza necessaria basata sulla cella più lunga
    local required = maxCellLength[i] * CHAR_TO_PERCENT 
    totalRequiredWidth = totalRequiredWidth + required + MARGIN_PER_COL
  end

  -- Soglia di attivazione: Se la larghezza richiesta è inferiore al 95% dello spazio totale
  local MAX_SAFE_WIDTH = 0.95
  local isNarrowEnough = totalRequiredWidth < MAX_SAFE_WIDTH
  
  -- === LOGICA DI USCITA: Se è abbastanza stretta, usa la logica fissa/equa ===
  if isNarrowEnough and numCols > 1 then
    
    -- Applico una logica di distribuzione fissa con % bloccate
    local spaceForContent = 0.6
    local spaceForLast = 0.4
    
    if numCols == 2 then
      spaceForContent = 0.3 
      spaceForLast = 0.7
    elseif numCols == 3 then
      spaceForContent = 0.5
      spaceForLast = 0.5
    end
    
    local contentColWidth = (numCols > 1) and (spaceForContent / (numCols - 1)) or spaceForContent
    
    for i = 1, numCols - 1 do
      el.colspecs[i] = {el.colspecs[i][1], contentColWidth}
    end
    
    el.colspecs[numCols] = {el.colspecs[numCols][1], spaceForLast}
    
    return el -- Uscita immediata: non c'è bisogno del calcolo dinamico
  end
  -- ==========================================================================

  -- 3. Continua con la Logica di Equilibrio (Se è troppo larga o sbilanciata)
  
  local minContent = totalTextLength[1]
  local maxContent = totalTextLength[1]
  
  for i = 2, numCols do
    if totalTextLength[i] < minContent then
      minContent = totalTextLength[i]
    end
    if totalTextLength[i] > maxContent then
      maxContent = totalTextLength[i]
    end
  end
  
  -- Margine di sicurezza
  local marginPerCol = 0.02
  local totalMargin = marginPerCol * (numCols - 1)
  local availableSpace = 1.0 - totalMargin
  
  -- Soglia di bilanciamento (per tabelle dinamiche/complesse)
  -- se la colonna piú larga ha almeno il 30% in piu' di testo delle altre -> considero "sbilanciata"
  local BALANCE_THRESHOLD = 0.30 
  local differenceIsSignificant = (maxContent - minContent) > (maxContent * BALANCE_THRESHOLD)
  
  -- === LOGICA DI EQUILIBRIO: DISTRIBUZIONE EQUA ===
  if not differenceIsSignificant and numCols > 1 then
    local equalWidth = availableSpace / numCols
    for i = 1, numCols do
      el.colspecs[i] = {el.colspecs[i][1], equalWidth}
    end
    return el
  end
  -- ===============================================
  
  -- 4. Logica Colonna Larga (Solo se la tabella è troppo larga E sbilanciata)
  
  local maxContentCol = 1
  for i = 2, numCols do
    if totalTextLength[i] > totalTextLength[maxContentCol] then
      maxContentCol = i
    end
  end
  
  -- Calcola larghezza fissa per colonne piccole
  local fixedWidths = {}
  local totalFixed = 0
  
  local CHAR_WIDTH_COEFF = 0.005  
  local MIN_WIDTH = 0.10
  local MAX_FIXED_WIDTH = 0.35 

  for i = 1, numCols do
    if i ~= maxContentCol then
      -- 1. Stima basata sulla quantità totale di testo nella colonna
      local estimated_width = totalTextLength[i] * CHAR_WIDTH_COEFF
      
      -- 2. Assicurati che rispetti i limiti generosi
      local width = math.max(MIN_WIDTH, math.min(MAX_FIXED_WIDTH, estimated_width))
      
      -- 3. Garanzia per la parola più lunga
      width = math.max(width, maxWordLength[i] * 0.008 + 0.06)
      
      fixedWidths[i] = width
      totalFixed = totalFixed + width
    end
  end
  
  local wideWidth = availableSpace - totalFixed
  
  -- 5. Applicazione delle Larghezze
  if wideWidth < 0.25 then
    local equalWidth = availableSpace / numCols
    for i = 1, numCols do
      el.colspecs[i] = {el.colspecs[i][1], equalWidth}
    end
  else
    for i = 1, numCols do
      if i == maxContentCol then
        el.colspecs[i] = {el.colspecs[i][1], wideWidth}
      else
        el.colspecs[i] = {el.colspecs[i][1], fixedWidths[i]}
      end
    end
  end
  
  return el
end