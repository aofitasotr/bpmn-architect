$ErrorActionPreference = "Stop"
$need = if ($env:DOCKER_MEMORY_GB) { [int]$env:DOCKER_MEMORY_GB } else { 10 }
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "docker is not installed: https://docs.docker.com/get-docker/"
    exit 1
}

function Test-Daemon {
    docker info *> $null
    return $LASTEXITCODE -eq 0
}

if (-not (Test-Daemon)) {
    $desktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (Test-Path $desktop) {
        Start-Process $desktop
    }
    for ($i = 0; $i -lt 60 -and -not (Test-Daemon); $i++) {
        Start-Sleep -Seconds 2
    }
    if (-not (Test-Daemon)) {
        Write-Host "docker daemon did not start"
        exit 1
    }
}

$bytes = [int64](docker info --format '{{.MemTotal}}')
$have = [math]::Floor($bytes / 1GB)
if ($have -lt $need) {
    Write-Host "warning: docker has $have GB of memory, $need GB is recommended, the model may be killed (OOM)"
    Write-Host "Docker Desktop: Settings > Resources > Memory"
    Write-Host "WSL2: set memory=${need}GB in %UserProfile%\.wslconfig and run: wsl --shutdown"
}

docker compose version *> $null
if ($LASTEXITCODE -eq 0) {
    docker compose up --build @args
} else {
    docker-compose up --build @args
}
