# 🟪 Tenant Service

Multi-tenancy management service for M-PESA SaaS platform.

## 📋 Overview

The Tenant Service handles all multi-tenancy aspects of the platform including:

- Organization (tenant) management
- User management with roles and permissions
- Feature flag management
- Invitation workflows
- Tenant isolation and limits
- Subscription tier enforcement

## 🏗️ Architecture

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ API Layer │────▶│ Service Layer │────▶│ Model Layer │
│ (FastAPI) │ │ (Business │ │ (SQLAlchemy) │
│ │ │ Logic) │ │ │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│ │ │
▼ ▼ ▼
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL │
│ Redis │
│ Kafka │
└─────────────────────────────────────────────────────────────┘

## Start the service

uvicorn src.main:app --reload --port 8004

## Core Endpoints

## Tenants

POST /api/v1/tenants - Create tenant

GET /api/v1/tenants/{id} - Get tenant

PUT /api/v1/tenants/{id} - Update tenant

DELETE /api/v1/tenants/{id} - Delete tenant

POST /api/v1/tenants/{id}/upgrade - Upgrade tier

## Users

GET /api/v1/tenants/{id}/users - List users

POST /api/v1/tenants/{id}/users - Create user

PUT /api/v1/tenants/{id}/users/{uid} - Update user

DELETE /api/v1/tenants/{id}/users/{uid} - Delete user

POST /api/v1/tenants/{id}/users/invite - Invite user

## Organization (Tenant)

json
{
"id": "uuid",
"name": "Acme Corp",
"slug": "acme-corp",
"tier": "professional",
"status": "active",
"email": "admin@acme.com",
"max_users": 10,
"max_transactions": 50000,
"trial_ends_at": "2026-03-31T00:00:00Z"
}

## User

json
{
"id": "uuid",
"tenant_id": "uuid",
"email": "user@acme.com",
"first_name": "John",
"last_name": "Doe",
"role": "admin",
"status": "active",
"mfa_enabled": false
}
🔒 Security
JWT authentication for API access

API key support for service accounts

Role-based access control (RBAC)

MFA support (TOTP)

Rate limiting per tenant

Audit logging for all operations

📈 Monitoring
Prometheus metrics at /metrics

Structured JSON logging

Sentry integration for error tracking

Health check at /health

🧪 Testing
bash

# Run tests

pytest

# With coverage

pytest --cov=src tests/

# Specific test file

pytest tests/test_tenants.py -v
🤝 Integration
Kafka Events Published
tenant.created - New tenant created

tenant.updated - Tenant updated

tenant.deleted - Tenant deleted

tenant.upgraded - Tier upgrade

user.created - New user created

user.updated - User updated

user.deleted - User deleted

Service Dependencies
PostgreSQL - Primary database

Redis - Caching and rate limiting

Kafka - Event publishing (optional)

Auth Service - Authentication (when not standalone)

## 🚀 **Quick Setup Script**

Create this PowerShell script to quickly set up the entire service:

### **setup-tenant-service.ps1**

.\setup-tenant-service.ps1

## This complete Tenant Service implementation includes:

✅ Full multi-tenancy support

✅ User management with roles

✅ Feature flags

✅ Invitation workflow

✅ API endpoints with documentation

✅ Database models and migrations

✅ Security and authentication

✅ Monitoring and logging

✅ Docker support

✅ Comprehensive testing structure

The service is production-ready and follows all best practices for a microservice in a FinTech platform!

```

```
