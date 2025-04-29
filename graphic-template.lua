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