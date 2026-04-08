# fix-tenant-config.ps1
Write-Host "🔧 Fixing Tenant Service Configuration" -ForegroundColor Cyan

cd C:\Users\Administrator\python_projects\services\tenant-service

# Create complete .env with all required fields
@"
# ============================================
# Tenant Service Environment Variables
# ============================================

# Database
DATABASE_URL=sqlite:///./tenants.db

# Security (REQUIRED)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Redis (Optional - uses default if not set)
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600

# Kafka (Optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# API Configuration
API_PORT=8004
API_VERSION=v1
DEBUG=True
ENVIRONMENT=development

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_ENABLED=False
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
"@ | Out-File -FilePath ".env" -Encoding utf8 -Force

Write-Host "✅ Created complete .env file" -ForegroundColor Green

# Check if the config.py has all these fields
Write-Host "`nChecking Settings class fields..." -ForegroundColor Yellow
python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.core.config import Settings
    print('Settings fields:')
    for field_name, field in Settings.model_fields.items():
        required = 'REQUIRED' if field.is_required() else 'optional'
        print(f'  - {field_name}: {required}')
except Exception as e:
    print(f'Error reading config: {e}')
"

# Now start the service
Write-Host "`nStarting Tenant Service..." -ForegroundColor Green
uvicorn src.main:app --reload --port 8004