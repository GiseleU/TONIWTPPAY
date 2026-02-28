# Gwiza WTP Pay Backend

## Project Overview

**Gwiza WTP Pay** is a Meta-compliant, event-driven backend platform that enables small sellers to handle inquiries and process orders via WhatsApp.  

The system emphasizes:

- **Immutable Event Tracking:** Every action is recorded as an event.  
- **Idempotent Webhooks:** Duplicate messages from WhatsApp are safely ignored.  
- **Policy-Governed Outbound Messaging:** All outgoing messages pass compliance checks.  
- **Decoupled Integrations:** Services never talk directly to external systems like WhatsApp or MoMo.

---

## Current Phase: Phase 1 — Coexistence Onboarding + Inquiry Capture

**Objectives:**

- Build seller onboarding flow with coexistence status tracking.  
- Capture inbound WhatsApp messages via webhook.  
- Persist inquiries and raw events.  
- Ensure inquiries are traceable to tenant, seller, and contact without duplication.

**Testing Focus:**

- Webhook contract tests  
- Duplicate event handling  
- Onboarding state transition tests  

**Done Criteria:**  
Every inquiry is traceable and no duplicates are created.

---



---

## Key Models

- **Tenant** – seller account owner  
- **WhatsAppAccount** – phone associated with tenant  
- **Contact** – customer interacting via WhatsApp  
- **Inquiry** – incoming message from contact; can become an order  
- **Order** – confirmed order record  
- **Payment** – payments for orders  
- **Event** – immutable log of actions and transitions  
- **Consent / OptOut** – contact compliance tracking

---

## Services

- `webhook_service.py` – handles incoming WhatsApp messages  
- `message_parser_service.py` – parses seller commands  
- `order_state_service.py` – deterministic order state transitions  
- `payment_service.py` – manages manual payment records  
- `summary_service.py` – daily seller and operational summaries  
- `notification_service.py` – sends outbound messages via adapters  

---

## Tech Stack

- **Backend Framework:** FastAPI  
- **Database:** PostgreSQL via SQLAlchemy  
- **Migrations:** Alembic  
- **Testing:** pytest  
- **Messaging Integrations:** WhatsApp Business API (future), MoMo API (manual MVP)

---

## Setup

1. Create a Python 3.14 virtual environment and activate it.  
2. Install dependencies:

```bash
poetry install





## APP DESCRITPION

## Application Architecture

This is a FastAPI-based backend application designed to enable small sellers to manage customer inquiries and process orders via WhatsApp, integrated with MoMo (Mobile Money) payments. The system is built with event-driven architecture, focusing on compliance with WhatsApp Business API policies.

## Core Architecture

**Framework & Language**: FastAPI (Python) with SQLAlchemy ORM and PostgreSQL database.

**Key Components**:
- **Models**: SQLAlchemy models for tenants, contacts, inquiries, orders, payments, events, and compliance tracking
- **Services**: Business logic layer for command execution, summaries, compliance, and integrations
- **API Routes**: RESTful endpoints for webhooks, commands, reports, and CRUD operations
- **Integrations**: WhatsApp Business API client and MoMo payment webhooks
- **Background Jobs**: Async runners for daily summary generation

## Main Features

### 1. WhatsApp Integration
- Receives inbound customer messages via webhooks
- Creates inquiries from customer messages
- Supports coexistence status for tenant activation
- Outbound messaging capability (client implemented but notification service not fully built)

### 2. Seller Command System
- Sellers can execute commands like:
  - `CONFIRM T#### amount` - Confirm inquiry with amount
  - `DROP T####` - Drop inquiry
  - `SUMMARY` - Get daily sales/revenue summary
- Commands are processed via API with deterministic state transitions
- Audit logging for all command executions

### 3. Order & Payment Management
- Orders created from confirmed inquiries
- Manual payment recording
- MoMo webhook integration for payment notifications
- Order state transitions (new → confirmed → completed/dropped)

### 4. Reporting & Summaries
- Daily summary generation aggregating:
  - Orders (total, paid)
  - Revenue (total, paid)
  - Inquiries (total, confirmed, dropped)
  - Compliance metrics (opt-outs, failed sends, etc.)
- Reports API for retrieving historical summaries
- On-demand summary via SUMMARY command

### 5. Compliance & Security
- WhatsApp coexistence status management
- Compliance signal tracking (opt-outs, blocks, failures)
- Idempotency keys for webhook deduplication
- Policy guards and authorization checks

## Database Schema

**Key Tables**:
- `tenants`: Seller accounts with coexistence status
- `whatsapp_accounts`: Phone numbers associated with tenants
- `contacts`: Customer phone numbers
- `inquiries`: Customer messages/inquiries
- `orders`: Confirmed orders with amounts
- `payments`: Payment records
- `events`: Audit log for all system actions
- `daily_summaries`: Aggregated daily metrics
- `compliance_signals`: WhatsApp compliance tracking

## API Endpoints

- `POST /webhooks/whatsapp` - Handle inbound WhatsApp messages
- `POST /webhooks/momo` - Handle MoMo payment notifications
- `POST /seller-commands/execute` - Execute seller commands
- `GET /reports/daily-summary` - Retrieve daily summaries
- `GET/POST /orders` - Order management
- `GET/POST /payments` - Payment management

## Current Implementation Status

- ✅ WhatsApp webhook handling and inquiry creation
- ✅ Seller command parsing and execution
- ✅ Daily summary generation and reporting
- ✅ Basic order and payment management
- ✅ Compliance tracking and coexistence logic
- ✅ Database migrations and models
- ✅ Comprehensive test suite

- ⚠️ Notification service for outbound WhatsApp messages (client exists, service stubbed)
- ⚠️ Message parser for detecting commands in WhatsApp messages (service stubbed)
- ⚠️ Automatic summary delivery (currently on-demand only)

## Deployment & Configuration

- Uses Poetry for dependency management
- Alembic for database migrations
- Environment-based configuration
- Async support with httpx for external API calls
- Logging and error handling throughout

The application is designed for scalability with event-driven processing, proper separation of concerns, and comprehensive testing, making it suitable for production use by small businesses requiring WhatsApp-based customer interaction and order management.
