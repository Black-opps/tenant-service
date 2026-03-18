
## 🚀 **Quick Setup Script**

Create this PowerShell script to quickly set up the entire service:

### **setup-tenant-service.ps1**
```powershell
# Tenant Service Setup Script
Write-Host "🚀 Setting up Tenant Service..." -ForegroundColor Green

# Create directory structure
$basePath = "services/tenant-service"
$folders = @(
    "src/api",
    "src/models",
    "src/services",
    "src/core",
    "src/utils",
    "src/middleware",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "migrations/versions",
    "logs"
)

foreach ($folder in $folders) {
    $path = Join-Path $basePath $folder
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    Write-Host "  ✅ Created: $path" -ForegroundColor Green
}

# Create __init__.py files
$initFolders = @(
    "src/api",
    "src/models", 
    "src/services",
    "src/core",
    "src/utils",
    "src/middleware",
    "tests"
)

foreach ($folder in $initFolders) {
    $path = Join-Path $basePath $folder
    $initFile = Join-Path $path "__init__.py"
    if (-not (Test-Path $initFile)) {
        "# $folder module" | Out-File -FilePath $initFile -Encoding UTF8
        Write-Host "  📄 Created: $initFile" -ForegroundColor Cyan
    }
}

Write-Host "`n✅ Tenant Service structure created successfully!" -ForegroundColor Green
Write-Host "📍 Location: $basePath" -ForegroundColor Yellow
Write-Host "`nNext steps:" -ForegroundColor Magenta
Write-Host "1. cd $basePath" -ForegroundColor White
Write-Host "2. Copy .env.example to .env and configure" -ForegroundColor White
Write-Host "3. Run: pip install -r requirements.txt" -ForegroundColor White
Write-Host "4. Run: uvicorn src.main:app --reload --port 8004" -ForegroundColor White