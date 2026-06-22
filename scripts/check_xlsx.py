import pandas as pd
df = pd.read_excel('/home/jessegoncalves/problm/planilha_teste.xlsx')
print(df[['CIDADE', 'status_processamento', 'observacoes']])
