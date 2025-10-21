"""
Script para verificar calidad de datos extraídos
"""
import pandas as pd
from pathlib import Path
import sys

def verify_file(filepath: str):
    """
    Verifica la calidad de un archivo de datos
    """
    print(f"\n{'='*60}")
    print(f"VERIFICACIÓN: {filepath}")
    print(f"{'='*60}")
    
    # Cargar datos
    df = pd.read_parquet(filepath)
    
    # 1. Info básica
    print(f"\n📊 INFO BÁSICA:")
    print(f"  Total registros: {len(df):,}")
    print(f"  Fechas únicas: {df['date'].nunique()}")
    print(f"  Tickers únicos: {df['underlying'].nunique()}")
    print(f"  Vencimientos: {df['expiration'].nunique()}")
    print(f"  Rango DTE: {df['dte'].min()}-{df['dte'].max()}")
    
    # 2. Completitud de datos
    print(f"\n✅ COMPLETITUD:")
    critical_fields = {
        'Contratos': 'ticker',
        'Precios': 'close',
        'Volumen': 'volume',
        'Delta': 'delta',
        'IV': 'iv',
        'OI': 'oi'
    }
    
    for name, field in critical_fields.items():
        count = df[field].notna().sum()
        pct = (count / len(df)) * 100
        status = "✅" if pct > 70 else "⚠️"
        print(f"  {status} {name:12s}: {count:6,}/{len(df):6,} ({pct:5.1f}%)")
    
    # 3. Calidad de datos
    print(f"\n📈 CALIDAD:")
    with_data = df[df['close'].notna()]
    
    if len(with_data) > 0:
        print(f"  Volumen total: {with_data['volume'].sum():,.0f}")
        print(f"  Precio promedio: ${with_data['close'].mean():.2f}")
        print(f"  IV promedio: {with_data['iv'].mean():.2%}")
        print(f"  Delta promedio: {with_data['delta'].mean():.4f}")
    
    # 4. Distribución
    print(f"\n📊 DISTRIBUCIÓN:")
    print(f"  Calls: {(df['type'] == 'call').sum():,}")
    print(f"  Puts: {(df['type'] == 'put').sum():,}")
    
    # 5. Strikes
    print(f"\n💰 STRIKES:")
    print(f"  Mínimo: ${df['strike'].min():.0f}")
    print(f"  Máximo: ${df['strike'].max():.0f}")
    print(f"  Rango: ${df['strike'].max() - df['strike'].min():.0f}")
    
    # 6. Top 5 más líquidos
    print(f"\n🔥 TOP 5 MÁS LÍQUIDOS:")
    top5 = with_data.nlargest(5, 'volume')
    for idx, row in top5.iterrows():
        print(f"  {row['ticker']:25s} Strike ${row['strike']:6.0f} "
              f"Vol: {row['volume']:8,.0f}")
    
    # 7. Verificación de integridad
    print(f"\n🔍 INTEGRIDAD:")
    issues = []
    
    if len(df) == 0:
        issues.append("Sin datos")
    if df['close'].notna().sum() < len(df) * 0.7:
        issues.append("Menos de 70% con precios")
    if df['delta'].notna().sum() < len(df) * 0.7:
        issues.append("Menos de 70% con griegas")
    if df['dte'].min() < 0:
        issues.append("DTEs negativos")
    
    if issues:
        print("  ⚠️ PROBLEMAS DETECTADOS:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print("  ✅ TODO OK - Datos válidos")
        return True


if __name__ == "__main__":
    # Verificar archivo de test
    test_files = list(Path("data/historical").glob("test_*.parquet"))
    
    if not test_files:
        print("❌ No se encontraron archivos de test")
        sys.exit(1)
    
    print("\n🔍 VERIFICACIÓN DE DATOS EXTRAÍDOS\n")
    
    all_ok = True
    for file in test_files:
        ok = verify_file(str(file))
        all_ok = all_ok and ok
    
    print(f"\n{'='*60}")
    if all_ok:
        print("✅ VERIFICACIÓN EXITOSA - Listo para extracción completa")
        print(f"{'='*60}\n")
        sys.exit(0)
    else:
        print("⚠️ VERIFICACIÓN CON ADVERTENCIAS - Revisar datos")
        print(f"{'='*60}\n")
        sys.exit(1)