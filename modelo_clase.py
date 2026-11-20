from pathlib import Path
import pandas as pd

FECHA_CORTE = pd.Timestamp('2026-10-31')
ORDEN_SEGMENTOS = ['Sin compra','Primerizos','En desarrollo','Fieles','En pausa']

def cargar_datos(carpeta=None):
    carpeta = Path(carpeta) if carpeta else Path(__file__).parent
    clientes = pd.read_csv(carpeta/'KORA_clientes.csv', parse_dates=['fecha_registro'])
    pedidos = pd.read_csv(carpeta/'KORA_pedidos.csv', parse_dates=['fecha_pedido'])
    assert clientes['id_cliente'].is_unique, 'ID de cliente duplicado'
    assert pedidos['id_pedido'].is_unique, 'ID de pedido duplicado'
    assert pedidos['id_cliente'].isin(clientes['id_cliente']).all(), 'Pedido sin cliente'
    assert pedidos['ingreso_neto_cop'].ge(0).all(), 'Ingreso negativo'
    return clientes, pedidos

def segmento_de_cliente(fila):
    n = fila['n_pedidos']
    dias = fila['dias_sin_compra']
    if n == 0:
        return 'Sin compra'
    if dias > 90:
        return 'En pausa'
    if n >= 3:
        return 'Fieles'
    if n == 1:
        return 'Primerizos'
    return 'En desarrollo'

def preparar_clientes(clientes, pedidos, fecha_corte=FECHA_CORTE):
    resumen = pedidos.groupby('id_cliente', as_index=False).agg(
        n_pedidos=('id_pedido','nunique'),
        ingreso_total=('ingreso_neto_cop','sum'),
        ultima_compra=('fecha_pedido','max'),
    )
    # Conservamos explícitamente a clientes que nunca compraron.
    perfil = clientes.merge(resumen, on='id_cliente', how='left', validate='one_to_one', indicator=True)
    perfil['n_pedidos'] = perfil['n_pedidos'].fillna(0).astype(int)
    perfil['ingreso_total'] = perfil['ingreso_total'].fillna(0).astype(float)
    perfil['dias_sin_compra'] = (pd.Timestamp(fecha_corte)-perfil['ultima_compra']).dt.days
    perfil['segmento'] = perfil.apply(segmento_de_cliente,axis=1)
    perfil['tiene_compra'] = perfil['n_pedidos'] > 0
    perfil['repite'] = perfil['n_pedidos'] >= 2
    return perfil

def kpis(perfil):
    n = len(perfil)
    compradores = int(perfil['tiene_compra'].sum())
    pedidos = int(perfil['n_pedidos'].sum())
    ingreso = float(perfil['ingreso_total'].sum())
    return {
        'clientes_registrados': n,
        'clientes_compradores': compradores,
        'pedidos': pedidos,
        'ingreso_neto_cop': ingreso,
        'ticket_promedio': ingreso/pedidos if pedidos else 0,
        'tasa_recompra': float(perfil['repite'].sum())/compradores if compradores else 0,
        'cobertura_compra': compradores/n if n else 0, # NO llamar a esto tasa de conversión de visitas
    }
