import streamlit as st
import plotly.express as px

from modelo_clase import ORDEN_SEGMENTOS, cargar_datos, preparar_clientes, kpis

st.set_page_config(layout = 'wide')
st.title('KORA | Conociendo clientes')
st.caption('Corte: 2026/10/31')

def obtener_datos():
    clientes, pedidos = cargar_datos()
    perfil = preparar_clientes(clientes, pedidos)
    return clientes, pedidos, perfil

clientes, pedidos, perfil = obtener_datos()

ciudades = st.sidebar.multiselect('Ciudad',sorted(perfil['ciudad'].unique()), default=sorted(perfil['ciudad'].unique()))
canales = st.sidebar.multiselect('Canal de adquisición',sorted(perfil['canal_adquisicion'].unique()),default = sorted(perfil['canal_adquisicion'].unique()))
filtrado = perfil.loc[
    perfil['ciudad'].isin(ciudades) &
    perfil['canal_adquisicion'].isin(canales)
].copy()

a, b, c, d = st.columns(4)
m = kpis(filtrado)
a.metric('Clientes registrados',f'{m['clientes_registrados']:,}',border = True)
b.metric('Clientes compradores',f'{m['clientes_compradores']:,}',border = True)
c.metric('Ingreso neto (COP)',f'${m['ingreso_neto_cop']/1e6:,.1f} M',border = True)
d.metric('Ticket promedio (COP)',f'${m['ticket_promedio']:,.0f}',border = True)

tabla = filtrado.groupby('segmento').size().reset_index(name = 'clientes')
fig = px.bar(tabla,x = 'segmento',y = 'clientes',text = 'clientes',
             category_orders = {'segmento':ORDEN_SEGMENTOS})
fig.update_layout(xaxis_title = 'Segmento',yaxis_title = 'Clientes')
st.plotly_chart(fig,width = 'stretch')

pedidos_f = pedidos.loc[pedidos['id_cliente'].isin(filtrado['id_cliente'])].copy()
categoria = pedidos_f.groupby('categoria',as_index = False).agg(ingreso = ('ingreso_neto_cop','sum')).sort_values('ingreso')
fig = px.bar(categoria,x = 'ingreso',y = 'categoria',orientation = 'h')
fig.update_layout(xaxis_title = 'Ingreso neto (COP)',yaxis_title = '')
st.plotly_chart(fig,width = 'stretch')

pedidos_f['mes'] = pedidos_f['fecha_pedido'].dt.to_period('M').astype(str)
mensual = pedidos_f.groupby('mes',as_index = False).agg(pedidos=('id_pedido','count'))
fig = px.line(mensual,x = 'mes',y = 'pedidos',markers = True)
fig.update_layout(xaxis_title = 'Mes',yaxis_title = 'Pedidos')
st.plotly_chart(fig,width = 'stretch')
