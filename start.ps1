# AI Agent 启动脚本
# 同时启动前端和后端服务

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = $PSScriptRoot
}

Write-Host "AI Agent 启动脚本" -ForegroundColor Cyan
Write-Host "项目目录: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# 后端启动函数
function Start-Backend {
    Write-Host "[后端] 启动 Python 服务..." -ForegroundColor Yellow
    $VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

    if (-not (Test-Path $VenvPython)) {
        Write-Host "[后端] 错误: venv 未找到，请先运行: python -m venv venv && pip install -e ." -ForegroundColor Red
        return $null
    }

    $BackendJob = Start-Job -ScriptBlock {
        param($PythonPath, $ProjectRoot)
        Set-Location $ProjectRoot
        & $PythonPath -m gateway.server
    } -ArgumentList $VenvPython, $ProjectRoot

    Write-Host "[后端] 服务启动中... (端口 8080)" -ForegroundColor Green
    return $BackendJob
}

# 前端启动函数
function Start-Frontend {
    Write-Host "[前端] 启动 Vite 服务..." -ForegroundColor Yellow
    $FrontendDir = Join-Path $ProjectRoot "frontend"

    if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
        Write-Host "[前端] 错误: frontend 未找到，请先初始化项目" -ForegroundColor Red
        return $null
    }

    $FrontendJob = Start-Job -ScriptBlock {
        param($FrontendDir)
        Set-Location $FrontendDir
        npm run dev
    } -ArgumentList $FrontendDir

    Write-Host "[前端] 服务启动中... (端口 3000)" -ForegroundColor Green
    return $FrontendJob
}

# 启动服务
$Jobs = @()

if ($BackendOnly) {
    $Jobs += Start-Backend
} elseif ($FrontendOnly) {
    $Jobs += Start-Frontend
} else {
    $Jobs += Start-Backend
    $Jobs += Start-Frontend
}

if ($Jobs.Count -eq 0) {
    Write-Host "没有服务启动" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "服务已启动:" -ForegroundColor Cyan
Write-Host "  - 后端 API: http://localhost:8080" -ForegroundColor White
Write-Host "  - 前端界面: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Gray
Write-Host ""

# 等待并显示输出
try {
    while ($Jobs.Count -gt 0) {
        foreach ($Job in $Jobs) {
            $Output = Receive-Job -Job $Job -ErrorAction SilentlyContinue
            if ($Output) {
                $JobName = if ($Job.Location -match "gateway") { "[后端]" } else { "[前端]" }
                Write-Host "$JobName $Output"
            }

            if ($Job.State -eq "Completed" -or $Job.State -eq "Failed") {
                $Jobs = $Jobs | Where-Object { $_.Id -ne $Job.Id }
            }
        }
        Start-Sleep -Milliseconds 100
    }
} finally {
    # 清理 Jobs
    $Jobs | Stop-Job -PassThru | Remove-Job
    Write-Host "所有服务已停止" -ForegroundColor Yellow
}