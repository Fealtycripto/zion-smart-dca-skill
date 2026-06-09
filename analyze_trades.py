import pandas as pd

df = pd.read_csv('D:/Dev/Carteira_2026_with_transaction_history.csv')
date_col = df.columns[0]
df = df.rename(columns={date_col: 'Date'})
df['Date'] = pd.to_datetime(df['Date'])
df['Total_num'] = pd.to_numeric(df['Total value (USD)'].astype(str).str.replace(',',''), errors='coerce')

print('=== RESUMO GERAL ===')
print(f'Total trades: {len(df)}')
print(f'Periodo: {df["Date"].min().date()} a {df["Date"].max().date()}')
print()

print('=== POR ATIVO ===')
for token in df['Token'].unique():
    sub = df[df['Token'] == token]
    buys = sub[sub['Type'] == 'buy']
    sells = sub[sub['Type'] == 'sell']
    total_usd = buys['Total_num'].sum()
    print(f'{token}: {len(sub)} trades | {len(buys)} compras | {len(sells)} vendas | USD {total_usd:.2f} comprado')

print()
buildups = df[df['Notes'].str.contains('BUILDUP', na=False)]
print(f'=== BUILDUP EVENTS: {len(buildups)} trades ===')
print(buildups[['Date', 'Token', 'Total_num', 'Notes']].to_string())

print()
buys_only = df[df['Type'] == 'buy']
print(f'Total investido (buys): USD {buys_only["Total_num"].sum():.2f}')
weeks = df['Date'].dt.to_period('W').nunique()
print(f'Semanas distintas de operacao: {weeks}')
print(f'Sessoes de aporte distintas: {df["Date"].dt.date.nunique()}')
