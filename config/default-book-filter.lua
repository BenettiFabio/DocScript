-- scene-break.lua
--
-- Converte i separatori di capitolo Markdown (una riga con --- circondata
-- da righe vuote, riconosciuta da Pandoc come HorizontalRule) in un
-- "asterismo" centrato (es. ***), sia per l'output LaTeX/PDF che per
-- l'output EPUB/HTML.
--
-- Lo stile del glifo NON e' definito qui: per il PDF lo decide il comando
-- \sceneBreak nel template book.tex, per l'EPUB lo decide la variabile
-- CSS --scene-break-glyph in book.css. Cosi' puoi cambiare l'aspetto del
-- separatore in un solo posto, senza toccare questo filtro.
--
-- Uso:
--   pandoc capitolo.md --lua-filter=scene-break.lua ...

function HorizontalRule(el)
  if FORMAT:match('latex') then
    return pandoc.RawBlock('latex', '\\sceneBreak')
  elseif FORMAT:match('html') or FORMAT:match('epub') then
    -- Contenuto vuoto (zero-width space): il glifo vero lo mette il CSS
    -- tramite .scene-break::before, per restare coerente col tema scelto.
    return pandoc.RawBlock('html', '<p class="scene-break">&#8203;</p>')
  else
    return pandoc.Para({ pandoc.Str('***') })
  end
end


-- function HorizontalRule(el)
--   if FORMAT:match('latex') then

--     return pandoc.RawBlock('latex', [[
-- \begin{center}
--   *\quad *\quad *
-- \end{center}
-- ]])

--   elseif FORMAT:match('html') or FORMAT:match('epub') then

--     -- Il glifo viene gestito dal CSS
--     return pandoc.RawBlock(
--       'html',
--       '<p class="scene-break">&#8203;</p>'
--     )

--   else

--     return pandoc.Para({
--       pandoc.Str('***')
--     })

--   end
-- end