param(
    [string]$Distro = "Ubuntu-24.04-Codex",
    [string]$SparkRoot = "/opt/spark/spark-skills",
    [string]$SmokeRoot = "/opt/spark/spark-pipeline-smoke",
    [string]$RealSecurityTaskSummary = ""
)

$ErrorActionPreference = "Continue"

$result = [ordered]@{
    wsl_available = $false
    distro = $Distro
    distro_installed = $false
    distro_version = $null
    spark_root = $SparkRoot
    spark_present = $false
    spark_commit = $null
    spark_core_imports = $false
    harbor_available = $false
    docker_available = $false
    docker_compose_available = $false
    docker_local_smoke_image = $false
    pipeline_smoke_present = $false
    pipeline_smoke_passed = $false
    pipeline_smoke_summary = $null
    real_security_task_present = $false
    real_security_task_passed = $false
    real_security_task_summary = $null
    notes = @()
}

if (-not $RealSecurityTaskSummary) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RealSecurityTaskSummary = Join-Path $scriptRoot "..\outputs\wsl_harbor_real_upload_001\summary.json"
}

try {
    $status = & wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        $result.wsl_available = $true
    } else {
        $result.notes += "wsl --status failed: $status"
    }
} catch {
    $result.notes += "wsl command failed: $($_.Exception.Message)"
}

try {
    $list = & wsl -l -v 2>&1
    $cleanList = (($list -join "`n") -replace "`0", "")
    $result.distro_installed = ($cleanList -match [regex]::Escape($Distro))
    if ($result.distro_installed) {
        $line = (($cleanList -split "`n") | Where-Object { $_ -match [regex]::Escape($Distro) } | Select-Object -First 1)
        $result.distro_version = $line
    }
} catch {
    $result.notes += "wsl -l -v failed: $($_.Exception.Message)"
}

if ($result.distro_installed) {
    try {
        & wsl -d $Distro -- bash -lc "test -d '$SparkRoot/.git'" 2>$null
        $result.spark_present = ($LASTEXITCODE -eq 0)

        if ($result.spark_present) {
            $commit = & wsl -d $Distro -- bash -lc "cd '$SparkRoot' && git rev-parse --short HEAD 2>/dev/null || true" 2>$null
            $result.spark_commit = (($commit -join "`n").Trim())

            & wsl -d $Distro -- bash -lc "cd '$SparkRoot' && .venv/bin/python - <<'PY' >/dev/null 2>&1
import spark_skills_gen.pipeline
import spark_skills_gen.executor
import spark_skills_gen.trajectory
import spark_skills_gen.dashboard.app
PY" 2>$null
            $result.spark_core_imports = ($LASTEXITCODE -eq 0)

            & wsl -d $Distro -- bash -lc "cd '$SparkRoot' && .venv/bin/harbor --help >/dev/null 2>&1" 2>$null
            $result.harbor_available = ($LASTEXITCODE -eq 0)
        }

        & wsl -d $Distro -- bash -lc "docker version >/dev/null 2>&1" 2>$null
        $result.docker_available = ($LASTEXITCODE -eq 0)

        & wsl -d $Distro -- bash -lc "docker compose version >/dev/null 2>&1" 2>$null
        $result.docker_compose_available = ($LASTEXITCODE -eq 0)

        & wsl -d $Distro -- bash -lc "docker image inspect spark-wsl-smoke:local >/dev/null 2>&1" 2>$null
        $result.docker_local_smoke_image = ($LASTEXITCODE -eq 0)

        & wsl -d $Distro -- bash -lc "test -f '$SmokeRoot/results/oracle/pipeline_summary.json'" 2>$null
        $result.pipeline_smoke_present = ($LASTEXITCODE -eq 0)

        if ($result.pipeline_smoke_present) {
            $summaryJson = & wsl -d $Distro -- bash -lc "cat '$SmokeRoot/results/oracle/pipeline_summary.json'" 2>$null
            $summaryText = ($summaryJson -join "`n")
            try {
                $summary = $summaryText | ConvertFrom-Json
                $result.pipeline_smoke_summary = $summary
                $result.pipeline_smoke_passed = (($summary.total_tasks -eq 1) -and ($summary.passed -eq 1))
            } catch {
                $result.notes += "could not parse pipeline smoke summary: $($_.Exception.Message)"
            }
        }
    } catch {
        $result.notes += "distro probe failed: $($_.Exception.Message)"
    }
}

try {
    if (Test-Path -LiteralPath $RealSecurityTaskSummary) {
        $result.real_security_task_present = $true
        $realSummary = Get-Content -LiteralPath $RealSecurityTaskSummary -Raw -Encoding UTF8 | ConvertFrom-Json
        $result.real_security_task_summary = $realSummary
        $result.real_security_task_passed = (($realSummary.passed -eq $true) -and ([double]$realSummary.reward -eq 1.0))
    }
} catch {
    $result.notes += "could not parse real security task summary: $($_.Exception.Message)"
}

$result | ConvertTo-Json -Depth 5
