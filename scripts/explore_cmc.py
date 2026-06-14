import requests, os, json
from dotenv import load_dotenv
load_dotenv('D:/Dev/zion-smart-dca-skill/.env')
key = os.getenv('CMC_API_KEY')
headers = {'X-CMC_PRO_API_KEY': key}

print('=== FEAR & GREED LATEST via CMC v3 ===')
r = requests.get('https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest', headers=headers)
print(json.dumps(r.json(), indent=2)[:600])

print()
print('=== FEAR & GREED HISTORICAL via CMC v3 (5 dias) ===')
r = requests.get('https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical?limit=5', headers=headers)
print(json.dumps(r.json(), indent=2)[:800])

print()
print('=== BTC INFO — metadata completo ===')
r = requests.get('https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?symbol=BTC', headers=headers)
d = r.json()
if d.get('data') and d['data'].get('BTC'):
    btc = d['data']['BTC'][0]
    print('Tags:', btc.get('tags', [])[:10])
    print('Category:', btc.get('category'))
    print('Description:', str(btc.get('description',''))[:200])

print()
print('=== CATEGORIES (narrativas de mercado) ===')
r = requests.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories?limit=8', headers=headers)
d = r.json()
if d.get('data'):
    for cat in d['data'][:8]:
        name = cat.get('name','?')
        coins = cat.get('num_tokens','?')
        change = cat.get('avg_price_change','N/A')
        vol = cat.get('volume','?')
        print(f'  {name} | {coins} coins | change={change} | vol={vol}')
