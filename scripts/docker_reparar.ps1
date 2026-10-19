<#
.SYNOPSIS
  Destrava o Docker Desktop quando ele falha ao iniciar com
  "initializing Inference manager / Secrets Engine: listening on unix://...: remove ...:
  The file cannot be accessed by the system".

.DESCRIPTION
  Causa: o Docker Desktop 4.50 deixa para tras sockets AF_UNIX (arquivos "ReparsePoint")
  quando fecha sem desligar direito, e na proxima partida nao consegue remove-los.
  O Windows nao apaga esses arquivos (erro 1920), mas o WSL apaga.

  O script: (1) encerra o Docker Desktop, (2) apaga os sockets orfaos pelo WSL e (3) abre
  o Docker de novo. Nao toca em containers, imagens nem volumes (o banco do projeto fica
  intacto). NUNCA use "Reset to factory defaults" na janela de erro: isso apaga os volumes.

.EXAMPLE
  powershell -File scripts\docker_reparar.ps1            # repara e reinicia
  powershell -File scripts\docker_reparar.ps1 -SoListar  # so mostra os sockets orfaos
#>
param([switch]$SoListar)

$ErrorActionPreference = "Stop"
$pastas = @("$env:LOCALAPPDATA\Docker\run", "$env:LOCALAPPDATA\docker-secrets-engine")
$orfaos = @(foreach ($p in $pastas) {
    if (Test-Path $p) { Get-ChildItem $p -Force | Where-Object { $_.Attributes -match 'ReparsePoint' } }
})

if ($orfaos.Count -eq 0) { "Nenhum socket orfao encontrado." } else { $orfaos | ForEach-Object { "orfao: " + $_.FullName } }
if ($SoListar) { return }

Get-Process | Where-Object { $_.ProcessName -match '^(Docker Desktop|com\.docker\..*)$' } |
    Stop-Process -Force -Confirm:$false
Start-Sleep -Seconds 3

foreach ($f in $orfaos) {
    # C:\Users\x\...  ->  /mnt/c/Users/x/...
    $drive = $f.FullName.Substring(0, 1).ToLower()
    $rest = $f.FullName.Substring(2).Replace('\', '/')
    wsl.exe -d Ubuntu -- rm -f "/mnt/$drive$rest"
    "removido: $($f.Name) (exit $LASTEXITCODE)"
}
wsl.exe --terminate Ubuntu | Out-Null

Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe"
"Docker Desktop iniciado. Aguarde ~1 min ate `docker ps` responder."
