import urllib.request
import urllib.parse
import json
import os

api_key = "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"
base = "https://api.stripe.com/v1"

def req(endpoint, data_str):
    request = urllib.request.Request(f"{base}/{endpoint}", data=data_str.encode('utf-8'), method='POST')
    request.add_header('Authorization', f'Bearer {api_key}')
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        res = urllib.request.urlopen(request)
        return json.loads(res.read())
    except urllib.error.HTTPError as e:
        print(f"HTTPError on {endpoint}: {e.read().decode()}")
        raise

try:
    print("Maken van Product...")
    p = req('products', 'name=Vacaturekanon All-in Project&description=AI-gestuurde Werving %26 Selectie Campagne')
    
    print("Maken van Prijs...")
    pr = req('prices', f'product={p["id"]}&unit_amount=249500&currency=eur')
    
    print("Maken van Payment Link...")
    pl_body = f'line_items[0][price]={pr["id"]}&line_items[0][quantity]=1&after_completion[type]=redirect&after_completion[redirect][url]=https://form.jotform.com/260757174181359'
    pl = req('payment_links', pl_body)
    
    print("Maken van Webhook...")
    # Op basis van CLAUDE.md en eerdere file paden, Netlify domein name is waarschijnlijk gerelateerd aan de ID, 
    # maar een webhook lokaal wijst naar the custom domein. We bouwen het nu voor 
    # de test deploy the function URL met de aanname the "functions = 'api'".
    # Vercel of Netlify kan the path routeren naar /api/stripe-webhook of /.netlify/functions/stripe-webhook
    wh_body = 'url=https://vacaturekanon-2026-demo.netlify.app/.netlify/functions/stripe-webhook&enabled_events[]=checkout.session.completed'
    wh = req('webhook_endpoints', wh_body)
    
    print("\n--- SUCCES ---")
    print(f"PAYMENT LINK: {pl['url']}")
    print(f"WEBHOOK SECRET: {wh['secret']}")

except Exception as e:
    print("\nFOUT OPGETREDEN:")
    print(e)
