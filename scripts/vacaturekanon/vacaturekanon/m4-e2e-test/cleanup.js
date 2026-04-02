#!/usr/bin/env node
/**
 * Vacaturekanon — Cleanup Script
 * Verwijdert test deals/persons/orgs uit Pipedrive na E2E test.
 *
 * Usage:
 *   PIPEDRIVE_API_TOKEN=... node cleanup.js --deal-id 12345
 *   PIPEDRIVE_API_TOKEN=... node cleanup.js --bedrijfsnaam "TestBedrijf B.V."
 */

import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import minimist from 'minimist';

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

const TOKEN = process.env.PIPEDRIVE_API_TOKEN;
if (!TOKEN) {
  console.error('Fout: PIPEDRIVE_API_TOKEN niet ingesteld.');
  process.exit(1);
}

const args = minimist(process.argv.slice(2), {
  string: ['deal-id', 'bedrijfsnaam'],
  alias: { d: 'deal-id', b: 'bedrijfsnaam' },
});

const BASE = 'https://api.pipedrive.com/v1';

async function pipedrive(method, path, body) {
  const url = BASE + path + (path.includes('?') ? '&' : '?') + 'api_token=' + TOKEN;
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  return res.json();
}

async function deleteDeal(id) {
  const deal = await pipedrive('GET', '/deals/' + id);
  if (!deal.success || !deal.data) {
    console.log('Deal ' + id + ' niet gevonden — al verwijderd of ongeldig ID');
    return;
  }
  const title = deal.data.title;
  const personId = deal.data.person_id;
  const orgId = deal.data.org_id;

  // Delete deal
  const delDeal = await pipedrive('DELETE', '/deals/' + id);
  if (delDeal.success) {
    console.log('Verwijderd: Deal "' + title + '" (ID: ' + id + ')');
  } else {
    console.log('Fout bij verwijderen deal: ' + JSON.stringify(delDeal));
  }

  // Delete person
  if (personId) {
    const delPerson = await pipedrive('DELETE', '/persons/' + personId);
    delPerson.success
      ? console.log('Verwijderd: Person ID ' + personId)
      : console.log('Fout bij verwijderen person ' + personId + ': ' + JSON.stringify(delPerson));
  }

  // Delete org (only if it has no other deals)
  if (orgId) {
    const orgDeals = await pipedrive('GET', '/organizations/' + orgId + '/deals?status=all_not_deleted');
    const remaining = orgDeals.data || [];
    if (remaining.length === 0) {
      const delOrg = await pipedrive('DELETE', '/organizations/' + orgId);
      delOrg.success
        ? console.log('Verwijderd: Organization ID ' + orgId)
        : console.log('Fout bij verwijderen org ' + orgId + ': ' + JSON.stringify(delOrg));
    } else {
      console.log('Organization ' + orgId + ' heeft nog ' + remaining.length + ' deals — niet verwijderd');
    }
  }
}

async function main() {
  if (args['deal-id']) {
    const id = Number(args['deal-id']);
    if (!id) { console.error('Ongeldig deal-id: ' + args['deal-id']); process.exit(1); }
    console.log('Verwijderen deal ID: ' + id);
    await deleteDeal(id);

  } else if (args['bedrijfsnaam']) {
    const naam = args['bedrijfsnaam'];
    console.log('Zoeken deals voor: ' + naam);
    const search = await pipedrive('GET', '/deals/search?term=' + encodeURIComponent(naam) + '&exact_match=false');
    if (!search.success || !search.data?.items?.length) {
      console.log('Geen deals gevonden voor "' + naam + '"');
      process.exit(0);
    }
    for (const item of search.data.items) {
      if (item.item.title && item.item.title.includes(naam)) {
        await deleteDeal(item.item.id);
      }
    }

  } else {
    // Default: clean up TestBedrijf from test-payload.json
    const payloadPath = resolve('./test-payload.json');
    if (!existsSync(payloadPath)) {
      console.error('Gebruik: node cleanup.js --deal-id <id> of --bedrijfsnaam "<naam>"');
      process.exit(1);
    }
    const payload = JSON.parse(readFileSync(payloadPath, 'utf-8'));
    const naam = payload.bedrijfsnaam;
    console.log('Verwijderen testdata voor: ' + naam);
    const search = await pipedrive('GET', '/deals/search?term=' + encodeURIComponent(naam) + '&exact_match=false');
    if (!search.success || !search.data?.items?.length) {
      console.log('Geen deals gevonden — database al schoon');
      process.exit(0);
    }
    for (const item of search.data.items) {
      if (item.item.title && item.item.title.includes(naam)) {
        await deleteDeal(item.item.id);
      }
    }
  }

  console.log('\nKlaar.');
}

main().catch(err => { console.error('Fout:', err); process.exit(1); });
