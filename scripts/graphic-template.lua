-- https://stackoverflow.com/questions/62831191/using-span-for-font-color-in-pandoc-markdown-for-both-html-and-pdf
-- https://bookdown.org/yihui/rmarkdown-cookbook/font-color.html
-- https://ulriklyngs.com/post/2019/02/20/how-to-use-pandoc-filters-for-advanced-customisation-of-your-r-markdown-documents/

function Span(el)
  if el.attributes.style then
    local stylestr = el.attributes.style

    -- Normalizza gli spazi nello stile per evitare problemi
    stylestr = stylestr:gsub("%s+", " ")

    -- Estrazione dei colori
    local fg_color = string.match(stylestr, "color:%s*([^;]+);")           -- Colore del testo
    local bg_color = string.match(stylestr, "background%-color:%s*([^;]+);") -- Colore di sfondo

    -- Mappa dei colori standard verso i colori personalizzati (solo per lo sfondo)
    local color_map = {
      yellow = "hlyellow",      -- Giallo pastello
      red = "hlred",            -- Rosso chiaro/pesca
      green = "hlgreen",        -- Verde menta chiaro
      violet = "hlviolet",      -- Viola chiaro/lilla
      orange = "hlorange",      -- Arancione tenue
      skyblue = "hlskyblue"     -- Azzurro pastello
    }

    -- Se è presente il background-color, usa la mappa per convertirlo
    if bg_color and color_map[bg_color] then
      bg_color = color_map[bg_color]
    end

    if FORMAT:match('latex') then
      local inner = pandoc.utils.stringify(el.content)
      -- Gestione prioritaria del background-color
      if bg_color then
        local colored = "\\colorbox{"..bg_color.."}{"..inner.."}"
        return pandoc.RawInline("latex", colored)
      elseif fg_color then
        local colored = "\\textcolor{"..fg_color.."}{"..inner.."}"
        return pandoc.RawInline("latex", colored)
      else
        -- Nessun colore specificato
        return el
      end
    else
      -- In altri formati (HTML, ecc.), lasciamo invariato l'elemento
      return el
    end
  else
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

-- -- per convertire i blocchi delle immagini con dimensione
function Image(img)
  local width = img.attributes["width"] or "\\linewidth"
  local path = img.src
  local latex = string.format("\\includegraphics[width=%s]{%s}", width, path)

  -- Restituisce sempre RawInline
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
