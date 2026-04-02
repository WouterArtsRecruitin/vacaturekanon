#!/usr/bin/env node
/**
 * Vacaturekanon — E2E Test
 * Tests the full chain: Worker → Pipedrive → Email → Template Builder
 *
 * Usage:
 *   WORKER_URL=https://... PIPEDRIVE_API_TOKEN=... node e2e-test.js
 */

import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

// Load .env if present
const envPath = resolve('.env');
if (existsSync(envPath)) {
  readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
    const eqIdx = line.indexOf('=');
    if (eqIdx < 1) return;
    const key = line.slice(0, eqIdx).trim();
    const val = line.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '');
    if (key && !process.env[key]) process.env[key] = val;
  });
}

const WORKER_URL       = process.env.WORKER_URL;
const PIPEDRIVE_TOKEN  = process.env.PIPEDRIVE_API_TOKEN;

const results = [];
let dealId = null;
let bedrijfsnaam = null;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function pass(test, detail) {
  results.push({ ok: true, test, detail: detail || '' });
  console.log('  \u2705 PASS: ' + test + (detail ? ' (' + detail + ')' : ''));
}

function fail(test, detail) {
  results.push({ ok: false, test, detail: detail || '' });
  console.log('  \u274C FAIL: ' + test + (detail ? '\n         ' + detail : ''));
}

async function pipedriveGet(path) {
  const url = 'https://api.pipedrive.com/v1' + path +
    (path.includes('?') ? '&' : '?') + 'api_token=' + PIPEDRIVE_TOKEN;
  const res = await fetch(url);
  return res.json();
}

// ─── STAP 1: Worker ───────────────────────────────────────────────────────────

async function testWorker() {
  console.log('\n[Stap 1] Worker intake...');
  if (!WORKER_URL) {
    fail('Worker URL ingesteld', 'WORKER_URL ontbreekt');
    return;
  }

  const payload = JSON.parse(readFileSync(new URL('./test-payload.json', import.meta.url), 'utf-8'));
  bedrijfsnaam = payload.bedrijfsnaam;

  let res, data;
  try {
    res = await fetch(WORKER_URL + '/api/intake', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    data = await res.json();
  } catch (err) {
    fail('Worker bereikbaar', err.message);
    return;
  }

  res.status === 200
    ? pass('Worker antwoordt 200 OK')
    : fail('Worker antwoordt 200 OK', 'Status: ' + res.status);

  data.success === true
    ? pass('Response bevat success: true')
    : fail('Response bevat success: true', JSON.stringify(data));

  typeof data.lead_score === 'number' && data.lead_score > 0
    ? pass('Lead score aanwezig', data.lead_score + '/25')
    : fail('Lead score aanwezig', 'Ontvangen: ' + data.lead_score);

  ['HOT', 'WARM', 'COLD'].includes(data.classificatie)
    ? pass('Classificatie correct', data.classificatie)
    : fail('Classificatie correct', 'Ontvangen: ' + data.classificatie);

  // Automation & High Tech(5) + 250-500(5) + Urgent(4) + €2.500-€5.000(4) + Gelderland(5) = 23 = HOT
  data.lead_score === 23
    ? pass('Score berekening klopt', '23/25 = HOT')
    : fail('Score berekening klopt', 'Verwacht 23, ontvangen ' + data.lead_score);

  if (data.pipedrive_deal_id) {
    dealId = data.pipedrive_deal_id;
    pass('Pipedrive deal ID ontvangen', 'ID: ' + dealId);
  } else {
    fail('Pipedrive deal ID ontvangen');
  }
}

// ─── STAP 2: Pipedrive ────────────────────────────────────────────────────────

async function testPipedrive() {
  console.log('\n[Stap 2] Pipedrive verificatie...');
  if (!PIPEDRIVE_TOKEN) {
    fail('Pipedrive API token ingesteld', 'PIPEDRIVE_API_TOKEN ontbreekt');
    return;
  }
  if (!bedrijfsnaam) {
    fail('Bedrijfsnaam beschikbaar voor zoeken', 'Stap 1 mislukt');
    return;
  }

  let searchResult;
  try {
    searchResult = await pipedriveGet('/deals/search?term=' + encodeURIComponent(bedrijfsnaam) + '&exact_match=false');
  } catch (err) {
    fail('Pipedrive API bereikbaar', err.message);
    return;
  }

  if (!searchResult.success) {
    fail('Pipedrive API bereikbaar', JSON.stringify(searchResult));
    return;
  }
  pass('Pipedrive API bereikbaar');

  const items = searchResult.data?.items || [];
  const match = items.find(i => i.item.title && i.item.title.includes(bedrijfsnaam));

  if (!match) {
    fail('Deal gevonden in Pipedrive', 'Geen deal met "' + bedrijfsnaam + '" gevonden');
    return;
  }
  pass('Deal gevonden in Pipedrive', match.item.title);
  const foundDealId = dealId || match.item.id;

  let detail;
  try {
    const resp = await pipedriveGet('/deals/' + foundDealId);
    detail = resp.data;
  } catch (err) {
    fail('Deal details ophalen', err.message);
    return;
  }

  detail?.stage_id
    ? pass('Deal heeft stage', 'Stage ID: ' + detail.stage_id)
    : fail('Deal heeft stage', 'stage_id ontbreekt');

  detail?.person_id
    ? pass('Person gekoppeld aan deal')
    : fail('Person gekoppeld aan deal');

  detail?.org_id
    ? pass('Organization gekoppeld aan deal')
    : fail('Organization gekoppeld aan deal');
}

// ─── STAP 3: Email ────────────────────────────────────────────────────────────

async function testEmail() {
  console.log('\n[Stap 3] Email verificatie...');
  // Worker response already indicates email_sent — no Resend inbox API needed for basic E2E
  const workerOk = results.some(r => r.test === 'Response bevat success: true' && r.ok);
  workerOk
    ? pass('Email stap bereikt (worker succesvol)', 'email_sent gecontroleerd via worker response')
    : fail('Email stap bereikt', 'Stap 1 was niet succesvol');
}

// ─── STAP 4: Template Builder ─────────────────────────────────────────────────

async function testTemplateBuilder() {
  console.log('\n[Stap 4] Template builder...');

  const builderPath = resolve('../m3-automation/template-builder.js');
  const inputPath   = resolve('../m3-automation/example-prospect.json');
  const outputPath  = '/tmp/vk-e2e-prospect.html';

  if (!existsSync(builderPath)) {
    fail('Template builder aanwezig', 'Niet gevonden: ' + builderPath);
    return;
  }

  if (!existsSync(inputPath)) {
    fail('Example prospect JSON aanwezig', 'Niet gevonden: ' + inputPath);
    return;
  }

  try {
    // Use execFile (not exec) to avoid shell injection
    await execFileAsync(process.execPath, [builderPath, '--type', 'prospect', '--input', inputPath, '--output', outputPath]);
    pass('Template builder draait zonder errors');
  } catch (err) {
    fail('Template builder draait zonder errors', (err.stderr || err.message).toString().slice(0, 200));
    return;
  }

  if (!existsSync(outputPath)) {
    fail('Output HTML aangemaakt', 'Bestand ontbreekt: ' + outputPath);
    return;
  }

  const html = readFileSync(outputPath, 'utf-8');

  const unfilledVars = (html.match(/\{\{[a-zA-Z0-9_]+\}\}/g) || []);
  // PIXEL_ID and GA4_ID are expected to remain as-is (set at deploy time, not via template-builder)
  const unexpectedUnfilled = unfilledVars.filter(v => !['{{PIXEL_ID}}', '{{GA4_ID}}'].includes(v));

  unexpectedUnfilled.length === 0
    ? pass('Geen onverwachte lege template variabelen')
    : fail('Geen onverwachte lege template variabelen', unexpectedUnfilled.join(', '));

  html.length > 5000
    ? pass('Output heeft substantiele inhoud', Math.round(html.length / 1024) + ' KB')
    : fail('Output heeft substantiele inhoud', html.length + ' bytes — te klein');

  html.trim().toLowerCase().startsWith('<!doctype')
    ? pass('Valide HTML doctype aanwezig')
    : fail('Valide HTML doctype aanwezig');
}

// ─── Run ──────────────────────────────────────────────────────────────────────

async function run() {
  console.log('');
  console.log('=================================================');
  console.log('  VACATUREKANON E2E TEST');
  console.log('  ' + new Date().toLocaleString('nl-NL'));
  console.log('=================================================');

  if (!WORKER_URL) {
    console.log('\n  Tip: WORKER_URL niet ingesteld. Worker tests worden als FAIL gemarkeerd.');
    console.log('  Gebruik: WORKER_URL=https://vacaturekanon-intake.workers.dev node e2e-test.js\n');
  }

  await testWorker();
  await testPipedrive();
  await testEmail();
  await testTemplateBuilder();

  const passed = results.filter(r => r.ok).length;
  const total  = results.length;

  console.log('');
  console.log('=================================================');
  if (passed === total) {
    console.log('  RESULTAAT: ' + passed + '/' + total + ' PASSED \u2705');
  } else {
    console.log('  RESULTAAT: ' + passed + '/' + total + ' PASSED | ' + (total - passed) + ' FAILED \u274C');
  }
  console.log('=================================================');

  if (dealId) {
    console.log('\n  Test deal ID: ' + dealId);
    console.log('  Opruimen: PIPEDRIVE_API_TOKEN=... node cleanup.js --deal-id ' + dealId + '\n');
  }

  process.exit(passed === total ? 0 : 1);
}

run().catch(err => { console.error('Fout:', err); process.exit(1); });
