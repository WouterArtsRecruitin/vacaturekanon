#!/usr/bin/env node
/**
 * Vacaturekanon Template Builder
 * Fills prospect-template.html or kandidaat-template.html with JSON data.
 *
 * Usage:
 *   node template-builder.js --type prospect --input data.json --output filled.html
 *   node template-builder.js --type kandidaat --input vacancy.json --output vacancy.html
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import minimist from 'minimist';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── HTML escape (required for all {{variable}} replacements) ─────────────────

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── Required variables per template type ─────────────────────────────────────

const REQUIRED_PROSPECT = [
  'bedrijfsnaam', 'sector', 'doelgroep_functietitels', 'regio',
  'usps_werkgever', 'JOTFORM_URL', 'CALENDLY_URL',
];

const REQUIRED_KANDIDAAT = [
  'functietitel', 'bedrijfsnaam', 'regio', 'salaris_range',
  'contract_type', 'sector', 'sollicitatie_url',
];

// ─── Defaults for optional variables ──────────────────────────────────────────

const DEFAULTS_PROSPECT = {
  avg_time_to_hire: '67',
  logo_url: '',
  opleidingsniveau: 'MBO/HBO',
  voornaam: '',
  achternaam: '',
  email: '',
  telefoonnummer: '',
  urgentie: '',
  lead_score: '',
  classificatie: '',
  PIXEL_ID: 'REPLACE_WITH_PIXEL_ID',
  GA4_ID: 'REPLACE_WITH_GA4_ID',
  urgency_class: '',
  aantal_medewerkers: '',
  bedrijfswebsite_url: '',
  tone_of_voice: '',
};

const DEFAULTS_KANDIDAAT = {
  logo_url: '',
  opleidingsniveau: 'MBO/HBO',
  bedrijfsbeschrijving: '',
  functieomschrijving: '',
  eisen: '',
  arbeidsvoorwaarden: '',
  usps_werkgever: '',
  hero_bg_image: '',
  date_posted: new Date().toISOString().split('T')[0],
  telefoonnummer_recruiter: '06-12 34 56 78',
  email_recruiter: 'info@recruitin.nl',
  opdrachtgever_kleur_primary: '#1A3F6F',
  opdrachtgever_kleur_primary_dark: '#122D52',
  PIXEL_ID: 'REPLACE_WITH_PIXEL_ID',
  GA4_ID: 'REPLACE_WITH_GA4_ID',
};

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const args = minimist(process.argv.slice(2), {
    string: ['type', 'input', 'output'],
    alias: { t: 'type', i: 'input', o: 'output' },
  });

  const type = args.type;
  const inputPath = args.input;
  const outputPath = args.output;

  if (!type || !['prospect', 'kandidaat'].includes(type)) {
    die('--type moet "prospect" of "kandidaat" zijn');
  }
  if (!inputPath) die('--input <bestand.json> is verplicht');
  if (!outputPath) die('--output <output.html> is verplicht');

  const absInput = resolve(inputPath);
  if (!existsSync(absInput)) die('Input bestand niet gevonden: ' + absInput);

  // Load input JSON
  let inputData;
  try {
    inputData = JSON.parse(readFileSync(absInput, 'utf-8'));
  } catch (err) {
    die('Ongeldig JSON in ' + absInput + ': ' + err.message);
  }

  // Load sector data
  const sectorDataPath = join(__dirname, 'sector-data.json');
  let sectorData = {};
  if (existsSync(sectorDataPath)) {
    try {
      sectorData = JSON.parse(readFileSync(sectorDataPath, 'utf-8'));
    } catch (_) {
      console.warn('Waarschuwing: sector-data.json kon niet geladen worden');
    }
  }

  // Enrich data with sector-specific fields
  const sector = inputData.sector || '';
  const sectorInfo = sectorData[sector] || {};
  if (!inputData.avg_time_to_hire && sectorInfo.avg_time_to_hire) {
    inputData.avg_time_to_hire = sectorInfo.avg_time_to_hire;
  }

  // Merge defaults
  const defaults = type === 'prospect' ? DEFAULTS_PROSPECT : DEFAULTS_KANDIDAAT;
  const data = Object.assign({}, defaults, inputData);

  // Set urgency_class for prospect template
  if (type === 'prospect' && data.urgentie === 'Zeer urgent (< 4 weken)') {
    data.urgency_class = ' red';
  }

  // Load template
  const templateName = type + '-template.html';
  const templatePath = join(__dirname, 'templates', templateName);
  if (!existsSync(templatePath)) {
    die('Template niet gevonden: ' + templatePath + '\nMaak een "templates/" map aan en plaats de HTML templates daarin.');
  }

  let html = readFileSync(templatePath, 'utf-8');

  // Validate required fields
  const required = type === 'prospect' ? REQUIRED_PROSPECT : REQUIRED_KANDIDAAT;
  const missing = required.filter(f => !data[f] || String(data[f]).trim() === '');
  if (missing.length > 0) {
    die('Verplichte velden ontbreken in input JSON:\n  ' + missing.join(', '));
  }

  // Replace all {{variables}}
  let replaced = 0;
  let defaultsUsed = 0;
  const usedKeys = new Set();

  html = html.replace(/\{\{([a-zA-Z0-9_]+)\}\}/g, (match, key) => {
    usedKeys.add(key);
    if (data[key] !== undefined && data[key] !== '') {
      if (defaults[key] !== undefined && data[key] === defaults[key]) {
        defaultsUsed++;
      } else {
        replaced++;
      }
      return escapeHtml(data[key]);
    }
    defaultsUsed++;
    return '';
  });

  // Light minification: collapse 3+ blank lines to 1
  html = html.replace(/\n{3,}/g, '\n\n');

  // Write output
  const absOutput = resolve(outputPath);
  const outputDir = dirname(absOutput);
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  writeFileSync(absOutput, html, 'utf-8');

  const fileSize = Math.round(html.length / 1024);
  console.log('');
  console.log('Template gevuld: ' + absOutput);
  console.log('  Variabelen vervangen:  ' + replaced);
  console.log('  Defaults gebruikt:     ' + defaultsUsed);
  console.log('  Totale bestandsgrootte: ' + fileSize + ' KB');
  if (sectorInfo.avg_time_to_hire) {
    console.log('  Sector data geladen:   ' + sector + ' (' + sectorInfo.avg_time_to_hire + ' dagen avg time-to-hire)');
  }
  console.log('');
}

function die(msg) {
  console.error('Fout: ' + msg);
  process.exit(1);
}

main();
