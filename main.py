import pandas as pd
import folium
from folium.plugins import HeatMap
import panel as pn
import plotly.express as px

# Ativar extensões do Panel
pn.extension()

# Coordenadas para o centro de São José dos Campos - SP
centro_sjc = [-23.2237, -45.9009]

# Carregar os três arquivos CSV
file_path_2022 = 'data/SJCDadosCriminais_2022.csv'
file_path_2023 = 'data/SJCDadosCriminais_2023.csv'
file_path_2024 = 'data/SJCDadosCriminais_2024.csv'

data_2022 = pd.read_csv(file_path_2022)
data_2023 = pd.read_csv(file_path_2023)
data_2024 = pd.read_csv(file_path_2024)

# Concatenar os três DataFrames
data = pd.concat([data_2022, data_2023, data_2024], ignore_index=True)

# Criar uma nova coluna para o formato MM/YYYY usando MES_ESTATISTICA e ANO_ESTATISTICA
data['MES_ANO'] = data['MES_ESTATISTICA'].astype(str).str.zfill(2) + '/' + data['ANO_ESTATISTICA'].astype(str)

# Obter todos os tipos de crimes únicos na coluna NATUREZA_APURADA
natureza_apurada_unique = sorted(data['NATUREZA_APURADA'].unique())

# Obter todos os anos únicos na coluna ANO_ESTATISTICA
anos_unique = ['TODOS'] + sorted(data['ANO_ESTATISTICA'].unique())

# Criar widgets para selecionar o tipo de crime e o ano
crime_type = pn.widgets.Select(name='Tipo de Crime', options=natureza_apurada_unique)
ano = pn.widgets.Select(name='Ano', options=anos_unique)

# Criar um botão para gerar o mapa
generate_button = pn.widgets.Button(name='Gerar Mapa')

# Espaço onde o mapa será renderizado (com tamanho maior)
map_pane = pn.pane.HTML(sizing_mode='fixed', height=400, width=1200)

# Espaço para exibir as estatísticas
stats_pane = pn.pane.HTML(sizing_mode='stretch_width')

# Espaço para os gráficos de barras
plot_pane = pn.pane.Plotly(sizing_mode='stretch_width', margin=(250, 0, 0, 0))  # Adiciona margem superior

# Criar espaços adicionais para os gráficos dos top 10 bairros
top_bairros_panes = [pn.pane.Plotly(sizing_mode='stretch_width') for _ in range(10)]

# Função para gerar o mapa de mancha criminal e os gráficos com base no tipo de crime e ano selecionado
def generate_crime_map(event):
    if ano.value == 'TODOS':
        data_filtered = data[data['NATUREZA_APURADA'] == crime_type.value]
    else:
        data_filtered = data[(data['NATUREZA_APURADA'] == crime_type.value) & (data['ANO_ESTATISTICA'] == ano.value)]
    
    # Filtrar apenas os dados com coordenadas válidas
    data_filtered_map = data_filtered[data_filtered['LATITUDE'].notnull() & data_filtered['LONGITUDE'].notnull()]
    
    # Criar o mapa centrado em São José dos Campos - SP
    crime_map = folium.Map(location=centro_sjc, zoom_start=12)
    
    # Adicionar a mancha criminal usando HeatMap
    heat_data = [[row['LATITUDE'], row['LONGITUDE']] for index, row in data_filtered_map.iterrows()]
    HeatMap(heat_data).add_to(crime_map)
    
    # Adicionar a legenda ao mapa
    legend_html = """
    <div style="position: fixed; 
         bottom: 50px; left: 50px; width: 200px; height: 150px; 
         border:2px solid grey; z-index:9999; font-size:14px;
         background-color:white;
         ">
         &nbsp;<b>Legenda</b> <br>
         &nbsp;<i style="color: blue;">●</i> Baixa Densidade <br>
         &nbsp;<i style="color: green;">●</i> Média-Baixa Densidade <br>
         &nbsp;<i style="color: yellow;">●</i> Média Densidade <br>
         &nbsp;<i style="color: orange;">●</i> Média-Alta Densidade <br>
         &nbsp;<i style="color: red;">●</i> Alta Densidade <br>
    </div>
    """
    crime_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Renderizar o mapa no espaço de saída
    map_pane.object = crime_map._repr_html_()

    # Gerar estatísticas
    num_eventos = data_filtered.shape[0]
    
    # Contagem de incidências por bairro
    top_bairros = data_filtered['BAIRRO'].value_counts().head(10)
    top_bairros_html = "<ul>" + "".join([f"<li><b>{bairro}</b>: {count} ocorrências</li>" for bairro, count in top_bairros.items()]) + "</ul>"
    
    # Atualizar o painel de estatísticas
    stats_pane.object = f"""
    <h3>Estatísticas para {crime_type.value} em {ano.value}:</h3>
    <p><b>Total de Eventos:</b> {num_eventos}</p>
    <h4>Top 10 Bairros com Mais Incidências:</h4>
    {top_bairros_html}
    <p>FONTE: Departamento de Polícia Civil, Polícia Militar e Superintendência da Polícia Técnico-Científica<br>
    (1) Soma de Roubo - Outros, Roubo de Carga e Roubo a Banco.<br>
    (2) Homicídio Doloso inclui Homicídio Doloso por Acidente de Trânsito.<br>
    (3) Nº de Vítimas de Homicídio Doloso inclui Nº de Vítimas de Homicídio Doloso por Acidente de Trânsito.<br>
    (4) Soma de Estupro e Estupro de Vulnerável.<br>
    Os dados estatísticos do Estado de São Paulo são divulgados nesta página em data anterior à publicação oficial em <br>
    Diário Oficial do Estado (Lei Estadual nº 9.155/95 e Resolução SSP nº 161/01). No período compreendido entre a divulgação <br>
    inicial e a publicação oficial em Diário Oficial, há possibilidade de retificações que são atualizadas automaticamente nesta página.</p>
    """

    # Gerar gráfico de barras para MM/YYYY usando MES_ESTATISTICA e ANO_ESTATISTICA (Total)
    mes_ano_counts = data_filtered['MES_ANO'].value_counts().sort_index()

    fig_total = px.bar(
        mes_ano_counts, 
        x=mes_ano_counts.index, 
        y=mes_ano_counts.values, 
        labels={'x': 'Mês/Ano', 'y': 'Quantidade'},
        title=f'Quantidade de {crime_type.value} por Mês/Ano em {ano.value}'
    )

    # Adicionar rótulos de valor nas barras
    fig_total.update_traces(texttemplate='%{y}', textposition='outside')

    # Renderizar o gráfico no espaço de saída
    plot_pane.object = fig_total

    # Gerar gráficos de barras para os top 10 bairros
    for i, bairro in enumerate(top_bairros.index):
        bairro_data = data_filtered[data_filtered['BAIRRO'] == bairro]
        mes_ano_bairro_counts = bairro_data['MES_ANO'].value_counts().sort_index()
        
        fig_bairro = px.bar(
            mes_ano_bairro_counts, 
            x=mes_ano_bairro_counts.index, 
            y=mes_ano_bairro_counts.values, 
            labels={'x': 'Mês/Ano', 'y': 'Quantidade'},
            title=f'Quantidade de {crime_type.value} por Mês/Ano em {bairro} ({ano.value})'
        )
        
        fig_bairro.update_traces(texttemplate='%{y}', textposition='outside')
        
        top_bairros_panes[i].object = fig_bairro

# Conectar o botão à função
generate_button.on_click(generate_crime_map)

# Adicionar um espaço entre o mapa e os gráficos
spacer = pn.Spacer(height=50)  # Aumenta o espaçamento entre o mapa e os gráficos

# Layout
app = pn.Column(
    crime_type, 
    ano, 
    generate_button, 
    stats_pane, 
    pn.Row(map_pane),  # Coloca o mapa dentro de uma linha para melhor layout
    spacer,  # Adiciona o espaço entre o mapa e os gráficos
    plot_pane,  # Gráfico total
    *top_bairros_panes  # Gráficos por bairro
)

# Servir a aplicação
app.servable()
