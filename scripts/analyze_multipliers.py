import pandas as pd

df = pd.read_csv('D:/Dev/zion-smart-dca-skill/docs/weekly_decisions.csv', index_col=0, parse_dates=True)

print('=== 17 SEMANAS - BREAKDOWN COMPLETO ===')
print(f'{"Sem":<4} {"Data":<12} {"BTC":>10} {"FG":>4} {"RSI":>6} {"Mult":>5} {"USD":>8} {"Decisao":<16}')
print('-'*70)
for idx, r in df.iterrows():
    flag = ' <-- BUILDUP! *' if r['is_buildup'] else ''
    print(f'{int(r["week"]):<4} {str(idx.date()):<12} ${r["btc_price"]:>9,.0f} {int(r["fear_greed"]):>4} {r["rsi"]:>6.1f} {r["multiplier"]:>5.1f}x ${r["dca_amount"]:>7.2f} {r["decision"]:<16}{flag}')

print()
print('=== DISTRIBUICAO DOS MULTIPLICADORES ===')
mult_labels = {
    0.5: 'Extreme Greed (0.5x) - ECONOMIA',
    1.0: 'Neutral       (1.0x) - PADRAO  ',
    1.5: 'Fear          (1.5x) - COMPRA+ ',
    2.0: 'Extreme Fear  (2.0x) - COMPRA++'
}
for m in [0.5, 1.0, 1.5, 2.0]:
    c = len(df[df['multiplier'] == m])
    if c > 0:
        pct = c/len(df)*100
        bar = '#' * c
        label = mult_labels[m]
        print(f'  {label}  {c:>2} semanas ({pct:>4.1f}%)  {bar}')

print()
semanas_medo = len(df[df['multiplier'] >= 1.5])
total_extra = df['dca_amount'].sum() - (70 * len(df))
media_semanal = df['dca_amount'].mean()
print(f'Semanas em regiao de medo (1.5x+):  {semanas_medo} de {len(df)} ({semanas_medo/len(df)*100:.0f}%)')
print(f'Total extra comprado vs base $70:   ${total_extra:.2f}')
print(f'Media de compra semanal real:       ${media_semanal:.2f} vs $70 base')
print(f'BTC total acumulado (Zion):         {df["btc_held"].iloc[-1]:.6f} BTC')
print(f'BTC extra vs DCA padrao:            +{(df["btc_held"].iloc[-1] - 0.023624):.6f} BTC (+{(df["btc_held"].iloc[-1] - 0.023624)/0.023624*100:.1f}%)')
