--[[
  epub-frontmatter.lua

  Inserisce automaticamente:
   - una pagina di copertina (logo, progetto, titolo, autore, data)
   - un colophon a fine documento (dipartimento, codice documento,
     footer text)
  usando gli STESSI metadata del template LaTeX
  (CompanyProject, CompanyStudyTitle, CompanyDesigner, LogoFileName,
   CompanyDepartment, CompanyDocumentCode, footerText).

  Da usare SOLO per il target .epub, in aggiunta (o al posto) del
  lua-filter "normale":

    pandoc ... --lua-filter=filtro_generico.lua \
               --lua-filter=epub-frontmatter.lua \
               -o out.epub

  Le classi CSS generate (.cover-page, .cover-logo, .cover-project,
  .cover-title, .cover-author, .cover-date, .colophon) sono quelle
  gia' definite in epub-style.css.
--]]

-- Escaping minimo per evitare che caratteri speciali nei metadata
-- rompano l'HTML iniettato.
local function esc(s)
  if s == nil then return "" end
  s = s:gsub("&", "&amp;")
  s = s:gsub("<", "&lt;")
  s = s:gsub(">", "&gt;")
  s = s:gsub('"', "&quot;")
  return s
end

local function meta_to_str(m)
  if m == nil then return "" end
  return esc(pandoc.utils.stringify(m))
end

function Pandoc(doc)
  local meta = doc.meta

  local project      = meta_to_str(meta.CompanyProject)
  local study_title  = meta_to_str(meta.CompanyStudyTitle)
  local author       = meta_to_str(meta.CompanyDesigner)
  local logo         = meta_to_str(meta.LogoFileName)
  local department   = meta_to_str(meta.CompanyDepartment)
  local doc_code     = meta_to_str(meta.CompanyDocumentCode)
  local footer_text  = meta_to_str(meta.footerText)
  local date_str     = meta_to_str(meta.date)

  if date_str == "" then
    date_str = os.date("%Y-%m-%d")
  end

  -- ---------------- Cover page ----------------
  local cover = {}
  table.insert(cover, '<div class="cover-page">')
  if logo ~= "" then
    table.insert(cover, string.format(
      '<img src="%s" alt="logo" class="cover-logo"/>', logo))
  end
  if project ~= "" then
    table.insert(cover, string.format(
      '<p class="cover-project">%s</p>', project))
  end
  if study_title ~= "" then
    table.insert(cover, string.format(
      '<p class="cover-title">%s</p>', study_title))
  end
  if author ~= "" then
    table.insert(cover, string.format(
      '<p class="cover-author">%s</p>', author))
  end
  table.insert(cover, string.format(
    '<p class="cover-date">%s</p>', date_str))
  table.insert(cover, '</div>')

  local cover_block = pandoc.RawBlock('html', table.concat(cover, "\n"))

  -- ---------------- Colophon ----------------
  local colophon = {}
  table.insert(colophon, '<div class="colophon">')
  if department ~= "" then
    table.insert(colophon, string.format(
      '<p>Dipartimento: %s</p>', department))
  end
  if doc_code ~= "" then
    table.insert(colophon, string.format(
      '<p>Codice documento: %s</p>', doc_code))
  end
  if footer_text ~= "" then
    table.insert(colophon, string.format('<p>%s</p>', footer_text))
  end
  table.insert(colophon, '</div>')

  local colophon_block = pandoc.RawBlock('html', table.concat(colophon, "\n"))

  -- Copertina in testa, colophon in coda al documento
  table.insert(doc.blocks, 1, cover_block)
  table.insert(doc.blocks, colophon_block)

  return doc
end