"""
Test: Buscar precio real de una opción específica
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def get_option_price(df: pd.DataFrame, 
                     date: datetime,
                     strike: float,
                     option_type: str,
                     expiration: datetime) -> float:
    """
    Busca el precio real de una opción específica en los datos.
    
    Args:
        df: DataFrame con datos históricos
        date: Fecha de consulta
        strike: Strike price
        option_type: 'call' o 'put'
        expiration: Fecha de vencimiento
        
    Returns:
        Precio de la opción (close o vwap)
        None si no se encuentra
    """
    # Filtrar por todos los criterios
    mask = (
        (df['date'] == date) &
        (df['strike'] == strike) &
        (df['type'] == option_type) &
        (df['expiration'] == expiration)
    )
    
    result = df[mask]
    
    if len(result) == 0:
        return None
    
    # Usar close, si es NaN usar vwap, si ambos NaN retornar None
    option_data = result.iloc[0]
    
    price = option_data['close']
    if pd.isna(price):
        price = option_data['vwap']
    
    if pd.isna(price):
        return None
    
    return price


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("🧪 Test: Buscar Precio Real de Opciones\n")
    
    # Cargar datos
    data_path = Path.cwd().parent / "data" / "historical" / "SPY_60days.parquet"
    print(f"Cargando: {data_path}")
    df = pd.read_parquet(data_path)
    print(f"✅ {len(df):,} registros cargados\n")
    
    # Convertir fechas
    df['date'] = pd.to_datetime(df['date'])
    df['expiration'] = pd.to_datetime(df['expiration'])
    
    # TEST 1: Buscar una opción específica
    print("="*60)
    print("TEST 1: Buscar opción PUT específica")
    print("="*60)
    
    test_date = df['date'].iloc[1000]  # Una fecha del medio
    test_expiration = df['expiration'].iloc[1000]
    test_strike = df['strike'].iloc[1000]
    
    print(f"\nBuscando:")
    print(f"  Fecha: {test_date.date()}")
    print(f"  Strike: ${test_strike:.0f}")
    print(f"  Tipo: put")
    print(f"  Vencimiento: {test_expiration.date()}")
    
    price = get_option_price(df, test_date, test_strike, 'put', test_expiration)
    
    if price:
        print(f"\n✅ ENCONTRADO: ${price:.2f}")
    else:
        print(f"\n❌ NO ENCONTRADO")
    
    # TEST 2: Explorar strikes disponibles
    print("\n" + "="*60)
    print("TEST 2: Explorar strikes disponibles")
    print("="*60)
    
    # Usar una fecha específica
    test_date = pd.to_datetime('2025-09-26')
    
    # Ver qué vencimientos hay disponibles en esa fecha
    available_expirations = df[df['date'] == test_date]['expiration'].unique()
    print(f"\nFecha: {test_date.date()}")
    print(f"Vencimientos disponibles: {len(available_expirations)}")
    
    if len(available_expirations) > 0:
        # Tomar el primer vencimiento (o uno específico)
        test_expiration = sorted(available_expirations)[2]  # El 3er vencimiento
        dte = (test_expiration - test_date).days
        
        print(f"Usando vencimiento: {pd.to_datetime(test_expiration).date()} (DTE: {dte})")
        
        # Ver qué strikes hay para ese vencimiento
        mask = (df['date'] == test_date) & (df['expiration'] == test_expiration)
        available_options = df[mask]
        
        puts = available_options[available_options['type'] == 'put'].sort_values('strike')
        calls = available_options[available_options['type'] == 'call'].sort_values('strike')
        
        print(f"\n📊 Opciones disponibles:")
        print(f"  Puts: {len(puts)} strikes")
        print(f"  Calls: {len(calls)} strikes")
        
        if len(puts) > 0:
            print(f"\n  Puts - Strikes disponibles:")
            print(f"    Min: ${puts['strike'].min():.0f}")
            print(f"    Max: ${puts['strike'].max():.0f}")
            print(f"    Ejemplo: {list(puts['strike'].head(10).values)}")
        
        if len(calls) > 0:
            print(f"\n  Calls - Strikes disponibles:")
            print(f"    Min: ${calls['strike'].min():.0f}")
            print(f"    Max: ${calls['strike'].max():.0f}")
            print(f"    Ejemplo: {list(calls['strike'].head(10).values)}")
        
        # TEST 3: Buscar IC con strikes reales
        print("\n" + "="*60)
        print("TEST 3: Buscar IC con strikes REALES")
        print("="*60)
        
        # Construir IC con strikes que SÍ existen
        if len(puts) >= 2 and len(calls) >= 2:
            # Tomar strikes del medio
            mid_put_idx = len(puts) // 2
            mid_call_idx = len(calls) // 2
            
            # Verificar que tengamos suficientes strikes
            if mid_put_idx > 5 and mid_call_idx > 5 and mid_put_idx < len(puts) - 5 and mid_call_idx < len(calls) - 5:
                ic_legs = [
                    {'strike': puts.iloc[mid_put_idx]['strike'], 'type': 'put', 'position': 'short'},
                    {'strike': puts.iloc[mid_put_idx - 5]['strike'], 'type': 'put', 'position': 'long'},
                    {'strike': calls.iloc[mid_call_idx]['strike'], 'type': 'call', 'position': 'short'},
                    {'strike': calls.iloc[mid_call_idx + 5]['strike'], 'type': 'call', 'position': 'long'},
                ]
                
                print(f"\nIntentando con strikes reales:")
                
                total_value = 0
                found_count = 0
                leg_details = []
                
                for i, leg in enumerate(ic_legs, 1):
                    price = get_option_price(df, test_date, leg['strike'], leg['type'], test_expiration)
                    
                    if price:
                        found_count += 1
                        print(f"  {i}. {leg['position']:5s} {leg['type']:4s} @ ${leg['strike']:.0f} → ${price:.2f} ✅")
                        
                        # Calcular valor según posición
                        if leg['position'] == 'short':
                            total_value += price
                            leg_details.append(f"+${price:.2f}")
                        else:
                            total_value -= price
                            leg_details.append(f"-${price:.2f}")
                    else:
                        print(f"  {i}. {leg['position']:5s} {leg['type']:4s} @ ${leg['strike']:.0f} → NO ENCONTRADO ❌")
                
                print(f"\n📊 Resultado:")
                print(f"  Legs encontrados: {found_count}/4")
                
                if found_count == 4:
                    print(f"  Cálculo: {' '.join(leg_details)} = ${total_value:.2f}")
                    print(f"  Valor total del IC: ${total_value:.2f}")
                    print(f"\n  ✅ ¡ÉXITO! Podemos valorar posiciones con datos reales!")
                else:
                    print(f"  ⚠️  Faltan datos para valoración completa")
            else:
                print("  ⚠️  No hay suficientes strikes para construir un IC")
        else:
            print("  ⚠️  No hay suficientes opciones disponibles")
    
    print("\n" + "="*60)
    print("✅ Test completado")
    print("="*60)