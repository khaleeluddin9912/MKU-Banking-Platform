# MKU Banking Platform

A learning project for building and deploying a production-minded banking application on AWS.
It uses simulated money only. It is not connected to real banks or payment networks.

## Stack
- React + Vite frontend
- FastAPI backend
- PostgreSQL database
- Docker Compose for local development

## Run locally

Requirements: Docker Desktop or Docker Engine + Compose plugin.

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```
2. Change `JWT_SECRET` in `.env` to a long random value.
3. Start the stack:
   ```bash
   docker compose up --build
   ```
4. Open:
   - Frontend: http://localhost:5173
   - API docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

Stop:
```bash
docker compose down
```

Remove local database data (destructive):
```bash
docker compose down -v
```

## First use
Register a user. The application creates a simulated INR account with an opening balance of ₹10,000.
Register a second user in another browser/private window to test transfers.

## Important implementation notes
- Passwords are hashed with Argon2.
- API access uses short-lived JWT access tokens.
- Transfer amounts are validated and processed in a database transaction.
- PostgreSQL row locks are used when updating balances.
- Amounts are stored as integer paise to avoid floating-point money errors.
- The frontend stores the access token in memory only. Refreshing the page signs you out; this is intentional for this starter.
- The app is a development foundation, not a certified or audited financial system.

## Useful endpoints
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/me`
- `GET /api/account`
- `GET /api/transactions`
- `POST /api/transfers`
- `GET /health`

## Next deployment stages
We will deploy this in stages: AWS networking, container registry, compute/orchestration, managed PostgreSQL, HTTPS/domain, secrets, CI/CD, monitoring, backups, and recovery testing. Do not deploy with the example secrets.
