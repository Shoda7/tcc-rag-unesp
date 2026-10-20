<#
.SYNOPSIS
  Abre o .docx no Word, atualiza o sumario (e demais campos), salva e exporta o PDF.

.DESCRIPTION
  O gerar_tcc.mjs cria o sumario como um campo do Word, que so e preenchido quando o
  Word atualiza o campo. Este script faz isso sem intervencao manual e deixa o .docx
  com o sumario ja preenchido. Rode depois de `node scripts/gerar_tcc.mjs`.

  Requer Microsoft Word instalado. Feche o Word antes: o script aborta se ele estiver
  aberto, para nao esconder nem fechar os documentos de quem esta usando.

.EXAMPLE
  node scripts/gerar_tcc.mjs
  powershell -File scripts/finalizar_docx.ps1 -Pdf DOCUMENTO-ENVIO\TCC_RAG_UNESP_Bauru_rascunho_2026-10-19.pdf
#>
param(
    [string]$Docx = "DOCUMENTO-ENVIO\TCC_RAG_UNESP_Bauru.docx",
    [string]$Pdf
)

$ErrorActionPreference = "Stop"
$docxPath = (Resolve-Path $Docx).Path
if (-not $Pdf) { $Pdf = [IO.Path]::ChangeExtension($docxPath, ".pdf") }
$pdfPath = if ([IO.Path]::IsPathRooted($Pdf)) { $Pdf } else { [IO.Path]::GetFullPath((Join-Path (Get-Location) $Pdf)) }

if (Get-Process WINWORD -ErrorAction SilentlyContinue) {
    throw "O Word esta aberto. Feche-o e rode de novo (o script nao mexe em janelas abertas)."
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($docxPath)
    # as listas de figuras, quadros e tabelas filtram por estilo (TOC com o filtro de estilos); o Word le o separador
    # de lista da configuracao regional (";" no pt-BR), entao ajusto o codigo do campo ao da maquina
    $sep = (Get-Culture).TextInfo.ListSeparator
    foreach ($f in $doc.Fields) {
        if ($f.Type -eq 13 -and $f.Code.Text.Contains('Leg') -and $f.Code.Text.Contains(',1"')) {
            $f.Code.Text = $f.Code.Text.Replace(',1"', $sep + '1"')
        }
    }
    # duas passadas: a segunda corrige os numeros de pagina depois que o sumario ocupa seu espaco
    foreach ($i in 1..2) {
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
        $null = $doc.Fields.Update()
    }
    "Campos de indice (sumario e listas): " + (($doc.TablesOfContents | ForEach-Object { $_.Range.Paragraphs.Count }) -join ", ") + " entradas"
    "Paginas: {0}" -f $doc.ComputeStatistics(2)
    $doc.Save()
    $doc.ExportAsFixedFormat($pdfPath, 17)   # 17 = wdExportFormatPDF
    $doc.Close(0)
    "OK: $docxPath"
    "OK: $pdfPath"
} finally {
    $word.Quit()
}
