# scripts/strategies/filters.py
"""
Filtros de Selección de Opciones
=================================

Filtros cuantitativos para identificar opciones negociables según:
- Liquidez (volumen, open interest, spreads)
- Volatilidad Implícita (IV rank, IV percentile)
- Delta y moneyness
- DTE (Days to Expiration)
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict


class LiquidityFilter:
    """
    Filtra opciones por criterios de liquidez.
    
    Opciones ilíquidas tienen spreads bid-ask amplios y pueden
    resultar en ejecuciones pobres.
    """
    
    def __init__(self, 
                 min_volume: int = 10,
                 min_open_interest: int = 50,
                 max_bid_ask_spread_pct: float = 10.0):
        """
        Parámetros:
        -----------
        min_volume : int
            Volumen mínimo diario
        min_open_interest : int
            Open Interest mínimo
        max_bid_ask_spread_pct : float
            Spread bid-ask máximo como % del mid price
        """
        self.min_volume = min_volume
        self.min_oi = min_open_interest
        self.max_spread = max_bid_ask_spread_pct
    
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica filtros de liquidez.
        
        Parámetros:
        -----------
        df : pd.DataFrame
            Datos de opciones
        
        Retorna:
        --------
        pd.DataFrame
            Opciones que pasan los filtros de liquidez
        """
        # Calcular spread bid-ask si no existe
        if 'bid_ask_spread_pct' not in df.columns:
            df = df.copy()
            # Si tenemos bid/ask, calcular spread
            if 'bid' in df.columns and 'ask' in df.columns:
                mid = (df['bid'] + df['ask']) / 2
                df['bid_ask_spread_pct'] = ((df['ask'] - df['bid']) / mid * 100)
            else:
                # Si no, asumir que close es razonable
                df['bid_ask_spread_pct'] = 5.0  # Asumir 5% por defecto
        
        # Aplicar filtros
        mask = (
            (df['volume'] >= self.min_volume) &
            (df['oi'] >= self.min_oi) &
            (df['bid_ask_spread_pct'] <= self.max_spread)
        )
        
        filtered = df[mask].copy()
        
        print(f"   📊 Liquidez: {len(filtered):,}/{len(df):,} opciones "
              f"({len(filtered)/len(df)*100:.1f}%)")
        
        return filtered
    
    def adjust_for_dte(self, dte: int) -> 'LiquidityFilter':
        """
        Ajusta filtros de liquidez según DTE.
        
        Vencimientos cortos requieren mayor liquidez.
        
        Parámetros:
        -----------
        dte : int
            Days to expiration
        
        Retorna:
        --------
        LiquidityFilter
            Nueva instancia con parámetros ajustados
        """
        if dte <= 21:
            # DTE corto: requisitos más estrictos
            return LiquidityFilter(
                min_volume=int(self.min_volume * 1.5),
                min_open_interest=int(self.min_oi * 1.5),
                max_bid_ask_spread_pct=self.max_spread * 0.7
            )
        elif dte <= 35:
            # DTE medio: requisitos moderados
            return LiquidityFilter(
                min_volume=int(self.min_volume * 1.2),
                min_open_interest=int(self.min_oi * 1.2),
                max_bid_ask_spread_pct=self.max_spread * 0.85
            )
        else:
            # DTE largo: requisitos estándar
            return self


class VolatilityFilter:
    """
    Filtra opciones por criterios de volatilidad implícita.
    
    Preferimos vender opciones cuando IV está elevada (IV rank alto).
    """
    
    def __init__(self,
                 min_iv: Optional[float] = None,
                 min_iv_rank: Optional[float] = None,
                 min_iv_percentile: Optional[float] = None):
        """
        Parámetros:
        -----------
        min_iv : float, optional
            IV mínima absoluta (ej. 0.20 = 20%)
        min_iv_rank : float, optional
            IV Rank mínimo (0-100)
        min_iv_percentile : float, optional
            IV Percentile mínimo (0-100)
        """
        self.min_iv = min_iv
        self.min_iv_rank = min_iv_rank
        self.min_iv_percentile = min_iv_percentile
    
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica filtros de volatilidad.
        """
        mask = pd.Series([True] * len(df), index=df.index)
        
        # Filtrar por IV absoluta
        if self.min_iv is not None and 'iv' in df.columns:
            mask &= (df['iv'] >= self.min_iv)
        
        # Filtrar por IV Rank
        if self.min_iv_rank is not None and 'iv_rank' in df.columns:
            mask &= (df['iv_rank'] >= self.min_iv_rank)
        
        # Filtrar por IV Percentile
        if self.min_iv_percentile is not None and 'iv_percentile' in df.columns:
            mask &= (df['iv_percentile'] >= self.min_iv_percentile)
        
        filtered = df[mask].copy()
        
        print(f"   📈 Volatilidad: {len(filtered):,}/{len(df):,} opciones "
              f"({len(filtered)/len(df)*100:.1f}%)")
        
        return filtered
    
    def adjust_for_dte(self, dte: int) -> 'VolatilityFilter':
        """
        Ajusta requisitos de IV según DTE.
        
        Vencimientos cortos requieren IV más alta para compensar riesgo gamma.
        """
        if dte <= 21:
            # DTE corto: IV más alta
            return VolatilityFilter(
                min_iv=self.min_iv * 1.2 if self.min_iv else None,
                min_iv_rank=max(self.min_iv_rank + 10, 70) if self.min_iv_rank else None,
                min_iv_percentile=max(self.min_iv_percentile + 10, 70) if self.min_iv_percentile else None
            )
        else:
            return self


class DeltaFilter:
    """
    Filtra opciones por delta target.
    
    Delta indica la probabilidad aproximada de que la opción
    expire ITM y controla el riesgo direccional.
    """
    
    def __init__(self,
                 delta_range: Tuple[float, float],
                 option_type: Optional[str] = None):
        """
        Parámetros:
        -----------
        delta_range : tuple
            (min_delta, max_delta) en valor absoluto
        option_type : str, optional
            'call' o 'put' - filtra solo ese tipo
        """
        self.delta_range = delta_range
        self.option_type = option_type
    
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra por delta y tipo de opción.
        """
        filtered = df.copy()
        
        # Filtrar por tipo si se especifica
        if self.option_type:
            filtered = filtered[filtered['type'] == self.option_type]
        
        # Filtrar por delta (usar valor absoluto)
        if 'delta' in filtered.columns:
            abs_delta = filtered['delta'].abs()
            mask = (abs_delta >= self.delta_range[0]) & (abs_delta <= self.delta_range[1])
            filtered = filtered[mask]
        
        print(f"   🎯 Delta {self.delta_range}: {len(filtered):,} opciones")
        
        return filtered


class DTEFilter:
    """
    Filtra opciones por días hasta vencimiento (DTE).
    """
    
    def __init__(self, dte_range: Tuple[int, int]):
        """
        Parámetros:
        -----------
        dte_range : tuple
            (min_dte, max_dte) en días
        """
        self.dte_range = dte_range
    
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra por DTE.
        """
        if 'dte' not in df.columns:
            print("   ⚠️  Columna 'dte' no encontrada")
            return df
        
        mask = (df['dte'] >= self.dte_range[0]) & (df['dte'] <= self.dte_range[1])
        filtered = df[mask].copy()
        
        print(f"   📅 DTE {self.dte_range}: {len(filtered):,} opciones")
        
        return filtered


class OptionSelector:
    """
    Selector principal que combina todos los filtros.
    
    Workflow:
    1. Aplicar filtros de liquidez
    2. Aplicar filtros de volatilidad
    3. Aplicar filtros de DTE
    4. Aplicar filtros de delta
    5. Seleccionar mejores candidatos
    """
    
    def __init__(self,
                 liquidity_filter: LiquidityFilter,
                 volatility_filter: VolatilityFilter,
                 dte_filter: DTEFilter,
                 delta_filter: Optional[DeltaFilter] = None):
        """
        Parámetros:
        -----------
        liquidity_filter : LiquidityFilter
        volatility_filter : VolatilityFilter
        dte_filter : DTEFilter
        delta_filter : DeltaFilter, optional
        """
        self.liquidity = liquidity_filter
        self.volatility = volatility_filter
        self.dte = dte_filter
        self.delta = delta_filter
    
    def select(self, df: pd.DataFrame, adjust_for_dte: bool = True) -> pd.DataFrame:
        """
        Aplica todos los filtros en secuencia.
        
        Parámetros:
        -----------
        df : pd.DataFrame
            Datos de opciones
        adjust_for_dte : bool
            Si True, ajusta filtros según DTE promedio
        
        Retorna:
        --------
        pd.DataFrame
            Opciones seleccionadas
        """
        print(f"\n🔍 Selección de Opciones - Total inicial: {len(df):,}")
        print("-" * 70)
        
        # Si está vacío, retornar
        if len(df) == 0:
            return df
        
        # Ajustar filtros para DTE si es necesario
        if adjust_for_dte and 'dte' in df.columns:
            avg_dte = df['dte'].median()
            liquidity = self.liquidity.adjust_for_dte(int(avg_dte))
            volatility = self.volatility.adjust_for_dte(int(avg_dte))
        else:
            liquidity = self.liquidity
            volatility = self.volatility
        
        # Aplicar filtros en secuencia
        result = df.copy()
        
        # 1. DTE
        result = self.dte.filter(result)
        if len(result) == 0:
            print("   ⚠️  Sin opciones después del filtro DTE")
            return result
        
        # 2. Liquidez
        result = liquidity.filter(result)
        if len(result) == 0:
            print("   ⚠️  Sin opciones después del filtro de liquidez")
            return result
        
        # 3. Volatilidad
        result = volatility.filter(result)
        if len(result) == 0:
            print("   ⚠️  Sin opciones después del filtro de volatilidad")
            return result
        
        # 4. Delta (si se especificó)
        if self.delta:
            result = self.delta.filter(result)
            if len(result) == 0:
                print("   ⚠️  Sin opciones después del filtro de delta")
                return result
        
        print("-" * 70)
        print(f"✅ Opciones seleccionadas: {len(result):,} "
              f"({len(result)/len(df)*100:.1f}% del total)")
        
        return result
    
    def rank_by_credit(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        Rankea opciones por crédito (premium) recibido.
        
        Útil para estrategias de venta de opciones.
        """
        if 'close' not in df.columns:
            return df
        
        ranked = df.sort_values('close', ascending=False).head(top_n)
        
        print(f"\n🏆 Top {top_n} por crédito:")
        for idx, row in ranked.iterrows():
            print(f"   Strike ${row['strike']:.0f} | "
                  f"Delta {row['delta']:.3f} | "
                  f"Premium ${row['close']:.2f} | "
                  f"DTE {row['dte']:.0f}")
        
        return ranked


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Filtros de Selección de Opciones")
    print("=" * 70)
    
    # Crear datos sintéticos para testing
    np.random.seed(42)
    n_options = 100
    
    test_data = pd.DataFrame({
        'ticker': ['SPY'] * n_options,
        'type': np.random.choice(['call', 'put'], n_options),
        'strike': np.random.uniform(600, 700, n_options),
        'dte': np.random.randint(15, 60, n_options),
        'close': np.random.uniform(1, 20, n_options),
        'volume': np.random.randint(0, 200, n_options),
        'oi': np.random.randint(0, 500, n_options),
        'delta': np.random.uniform(-0.5, 0.5, n_options),
        'iv': np.random.uniform(0.15, 0.35, n_options),
        'iv_rank': np.random.uniform(30, 90, n_options),
    })
    
    print(f"\n📊 Datos de prueba: {len(test_data)} opciones")
    
    # Test 1: Liquidez
    print("\n" + "=" * 70)
    print("Test 1: Filtro de Liquidez")
    print("=" * 70)
    
    liq_filter = LiquidityFilter(min_volume=50, min_open_interest=100)
    liquid_options = liq_filter.filter(test_data)
    
    # Test 2: Volatilidad
    print("\n" + "=" * 70)
    print("Test 2: Filtro de Volatilidad")
    print("=" * 70)
    
    vol_filter = VolatilityFilter(min_iv_rank=60)
    high_iv = vol_filter.filter(liquid_options)
    
    # Test 3: Delta
    print("\n" + "=" * 70)
    print("Test 3: Filtro de Delta")
    print("=" * 70)
    
    delta_filter = DeltaFilter(delta_range=(0.15, 0.25), option_type='put')
    target_delta = delta_filter.filter(high_iv)
    
    # Test 4: Selector completo
    print("\n" + "=" * 70)
    print("Test 4: Selector Completo")
    print("=" * 70)
    
    selector = OptionSelector(
        liquidity_filter=LiquidityFilter(min_volume=50, min_open_interest=100),
        volatility_filter=VolatilityFilter(min_iv_rank=60),
        dte_filter=DTEFilter(dte_range=(30, 45)),
        delta_filter=DeltaFilter(delta_range=(0.15, 0.25))
    )
    
    selected = selector.select(test_data)
    
    if len(selected) > 0:
        ranked = selector.rank_by_credit(selected, top_n=5)
    
    print("\n" + "=" * 70)
    print("✓ Tests completados")
    print("=" * 70)