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