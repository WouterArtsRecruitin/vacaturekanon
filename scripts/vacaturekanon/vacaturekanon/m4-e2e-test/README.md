# M4 — E2E Test

Test de volledige Vacaturekanon keten: Worker → Pipedrive → Email → Template Builder.

## Vereisten

- Worker is deployed (zie M1 README)
- Pipedrive API token beschikbaar
- Node.js 18+

## Setup

```bash
cp .env.example .env
# Vul WORKER_URL en PIPEDRIVE_API_TOKEN in
```

## Test draaien

```bash
# Met .env bestand
node e2e-test.js

# Of direct met env vars
WORKER_URL=https://vacaturekanon-intake.workers.dev \
PIPEDRIVE_API_TOKEN=abc123 \
node e2e-test.js
```

## Verwacht resultaat

```
=================================================
  VACATUREKANON E2E TEST
=================================================

[Stap 1] Worker intake...
  ✅ PASS: Worker antwoordt 200 OK
  ✅ PASS: Response bevat success: true
  ✅ PASS: Lead score aanwezig (23/25)
  ✅ PASS: Classificatie correct (HOT)
  ✅ PASS: Score berekening klopt (23/25 = HOT)
  ✅ PASS: Pipedrive deal ID ontvangen (ID: 12345)

[Stap 2] Pipedrive verificatie...
  ✅ PASS: Pipedrive API bereikbaar
  ✅ PASS: Deal gevonden in Pipedrive
  ✅ PASS: Deal heeft stage
  ✅ PASS: Person gekoppeld aan deal
  ✅ PASS: Organization gekoppeld aan deal

[Stap 3] Email verificatie...
  ✅ PASS: Email stap bereikt (worker succesvol)

[Stap 4] Template builder...
  ✅ PASS: Template builder draait zonder errors
  ✅ PASS: Geen onverwachte lege template variabelen
  ✅ PASS: Output heeft substantiele inhoud (28 KB)
  ✅ PASS: Valide HTML doctype aanwezig

=================================================
  RESULTAAT: 15/15 PASSED ✅
=================================================
```

## Na de test: opruimen

```bash
# Verwijder test deal (ID staat onderaan test output)
PIPEDRIVE_API_TOKEN=abc123 node cleanup.js --deal-id 12345

# Of op bedrijfsnaam
PIPEDRIVE_API_TOKEN=abc123 node cleanup.js --bedrijfsnaam "TestBedrijf B.V."

# Automatisch op basis van test-payload.json
PIPEDRIVE_API_TOKEN=abc123 node cleanup.js
```
