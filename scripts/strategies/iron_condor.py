# scripts/strategies/iron_condor.py
"""
Estrategia Iron Condor
=======================

Iron Condor: Venta simultánea de call spread OTM y put spread OTM.

Estructura:
- Vender Put @ delta 0.16-0.25
- Comprar Put @ delta 0.05-0.10 (5 puntos más abajo)
- Vender Call @ delta -0.16 a -0.25
- Comprar Call @ delta -0.05 a -0.10 (5 puntos más arriba)

Objetivo: Beneficiarse del decaimiento temporal en mercados neutrales de rango.

Basado en reglas del documento con DTE 15-60 días.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .base import StrategyBase, StrategyRules, Position
from .filters import OptionSelector, LiquidityFilter, VolatilityFilter, DTEFilter, DeltaFilter
from .risk_manager import RiskManager


class IronCondor(StrategyBase):
    """
    Implementación completa de la estrategia Iron Condor.
    
    Reglas cuantitativas del documento:
    - DTE: 15-60 días
    - Short strikes: Delta 0.16-0.25 (call y put)
    - Long strikes: Delta 0.05-0.10 (call y put)
    - Spread width: 5 puntos típicamente
    - Min IV Rank: Variable por DTE (60-75)
    - Profit target: Variable por DTE (25%-50%)
    - Stop loss: Variable por DTE (100%-200%)
    """
    
    def __init__(self, 
                 dte_range: Tuple[int, int] = (15, 60),
                 short_delta_range: Tuple[float, float] = (0.16, 0.25),
                 long_delta_range: Tuple[float, float] = (0.05, 0.10),
                 spread_width: int = 5,
                 min_iv_rank: float = 60.0,
                 min_volume: int = 10,
                 min_open_interest: int = 50,
                 base_capital: float = 100000):
        """
        Inicializa la estrategia Iron Condor.
        
        Parámetros:
        -----------
        dte_range : tuple
            (min_dte, max_dte) en días
        short_delta_range : tuple
            Rango de delta para strikes cortos
        long_delta_range : tuple
            Rango de delta para strikes largos
        spread_width : int
            Ancho del spread en puntos
        min_iv_rank : float
            IV Rank mínimo
        min_volume : int
            Volumen mínimo
        min_open_interest : int
            Open Interest mínimo
        base_capital : float
            Capital base para cálculos de riesgo
        """
        rules = StrategyRules(
            name="Iron Condor",
            dte_range=dte_range,
            short_delta_range=short_delta_range,
            long_delta_range=long_delta_range,
            min_iv_rank=min_iv_rank,
            min_volume=min_volume,
            min_open_interest=min_open_interest
        )
        
        super().__init__(rules)
        
        self.spread_width = spread_width
        self.risk_manager = RiskManager(base_capital=base_capital)
        
        # Crear selectores de opciones
        self.put_short_selector = self._create_selector('put', 'short')
        self.put_long_selector = self._create_selector('put', 'long')
        self.call_short_selector = self._create_selector('call', 'short')
        self.call_long_selector = self._create_selector('call', 'long')
    
    def _create_selector(self, option_type: str, position: str) -> OptionSelector:
        """
        Crea un selector de opciones para un leg específico.
        
        Parámetros:
        -----------
        option_type : str
            'call' o 'put'
        position : str
            'short' o 'long'
        
        Retorna:
        --------
        OptionSelector
        """
        delta_range = (
            self.rules.short_delta_range if position == 'short' 
            else self.rules.long_delta_range
        )
        
        return OptionSelector(
            liquidity_filter=LiquidityFilter(
                min_volume=self.rules.min_volume,
                min_open_interest=self.rules.min_open_interest,
                max_bid_ask_spread_pct=10.0
            ),
            volatility_filter=VolatilityFilter(
                min_iv_rank=self.rules.min_iv_rank
            ),
            dte_filter=DTEFilter(
                dte_range=self.rules.dte_range
            ),
            delta_filter=DeltaFilter(
                delta_range=delta_range,
                option_type=option_type
            )
        )
    
    def scan(self, options_data: pd.DataFrame, market_data: Dict) -> pd.DataFrame:
        """
        Escanea el mercado buscando oportunidades de Iron Condor.
        
        Proceso:
        1. Seleccionar puts cortos (delta 0.16-0.25)
        2. Para cada put corto, buscar put largo 5 strikes abajo
        3. Seleccionar calls cortos (delta -0.16 a -0.25)
        4. Para cada call corto, buscar call largo 5 strikes arriba
        5. Combinar en Iron Condors completos
        6. Rankear por crédito total
        
        Parámetros:
        -----------
        options_data : pd.DataFrame
            Cadena de opciones disponibles
        market_data : dict
            Debe contener: 'iv_rank', 'underlying_price'
        
        Retorna:
        --------
        pd.DataFrame
            Oportunidades de Iron Condor rankeadas
        """
        print("\n" + "=" * 70)
        print("🔍 ESCANEANDO IRON CONDORS")
        print("=" * 70)
        
        # Agregar IV rank si viene en market_data
        if 'iv_rank' in market_data:
            options_data = options_data.copy()
            options_data['iv_rank'] = market_data['iv_rank']
        
        underlying_price = market_data.get('underlying_price', 
                                          options_data['underlying_price'].iloc[0] if 'underlying_price' in options_data.columns else None)
        
        # 1. Seleccionar puts cortos
        print("\n1️⃣  Seleccionando PUT cortos (short)...")
        put_shorts = self.put_short_selector.select(
            options_data[options_data['type'] == 'put'],
            adjust_for_dte=True
        )
        
        if len(put_shorts) == 0:
            print("   ⚠️  No hay puts cortos disponibles")
            return pd.DataFrame()
        
        # 2. Seleccionar calls cortos
        print("\n2️⃣  Seleccionando CALL cortos (short)...")
        call_shorts = self.call_short_selector.select(
            options_data[options_data['type'] == 'call'],
            adjust_for_dte=True
        )
        
        if len(call_shorts) == 0:
            print("   ⚠️  No hay calls cortos disponibles")
            return pd.DataFrame()
        
        # 3. Construir Iron Condors
        print("\n3️⃣  Construyendo Iron Condors completos...")
        iron_condors = []
        
        # Agrupar por fecha/expiration
        for date in put_shorts['date'].unique():
            date_puts = put_shorts[put_shorts['date'] == date]
            date_calls = call_shorts[call_shorts['date'] == date]
            
            if len(date_puts) == 0 or len(date_calls) == 0:
                continue
            
            for _, put_short in date_puts.iterrows():
                # Buscar put largo (5 strikes abajo)
                put_long_strike = put_short['strike'] - self.spread_width
                put_long = options_data[
                    (options_data['strike'] == put_long_strike) &
                    (options_data['type'] == 'put') &
                    (options_data['date'] == date)
                ]
                
                if len(put_long) == 0:
                    continue
                
                put_long = put_long.iloc[0]
                
                for _, call_short in date_calls.iterrows():
                    # Buscar call largo (5 strikes arriba)
                    call_long_strike = call_short['strike'] + self.spread_width
                    call_long = options_data[
                        (options_data['strike'] == call_long_strike) &
                        (options_data['type'] == 'call') &
                        (options_data['date'] == date)
                    ]
                    
                    if len(call_long) == 0:
                        continue
                    
                    call_long = call_long.iloc[0]
                    
                    # Calcular métricas del Iron Condor
                    # Crédito = (Put short - Put long) + (Call short - Call long)
                    put_spread_credit = put_short['close'] - put_long['close']
                    call_spread_credit = call_short['close'] - call_long['close']
                    total_credit = put_spread_credit + call_spread_credit
                    
                    # Riesgo máximo = Ancho del spread - Crédito recibido
                    max_risk = (self.spread_width - total_credit) * 100
                    
                    # Return on Risk
                    ror = (total_credit / self.spread_width) * 100 if self.spread_width > 0 else 0
                    
                    # Calcular griegas netas (aproximadas)
                    net_delta = (put_short.get('delta', 0) - put_long.get('delta', 0) + 
                                call_short.get('delta', 0) - call_long.get('delta', 0))
                    
                    iron_condors.append({
                        'date': date,
                        'expiration': put_short['expiration'],
                        'dte': put_short['dte'],
                        'underlying_price': underlying_price,
                        
                        # Put spread
                        'put_short_strike': put_short['strike'],
                        'put_short_delta': put_short.get('delta'),
                        'put_short_price': put_short['close'],
                        'put_long_strike': put_long['strike'],
                        'put_long_delta': put_long.get('delta'),
                        'put_long_price': put_long['close'],
                        'put_spread_credit': put_spread_credit,
                        
                        # Call spread
                        'call_short_strike': call_short['strike'],
                        'call_short_delta': call_short.get('delta'),
                        'call_short_price': call_short['close'],
                        'call_long_strike': call_long['strike'],
                        'call_long_delta': call_long.get('delta'),
                        'call_long_price': call_long['close'],
                        'call_spread_credit': call_spread_credit,
                        
                        # Totales
                        'total_credit': total_credit,
                        'max_risk': max_risk,
                        'return_on_risk': ror,
                        'net_delta': net_delta,
                        
                        # IV
                        'put_iv': put_short.get('iv'),
                        'call_iv': call_short.get('iv'),
                        'avg_iv': (put_short.get('iv', 0) + call_short.get('iv', 0)) / 2
                    })
        
        if len(iron_condors) == 0:
            print("   ⚠️  No se pudieron construir Iron Condors completos")
            return pd.DataFrame()
        
        df_condors = pd.DataFrame(iron_condors)
        
        # Filtrar por crédito mínimo (al menos 0.30 por spread)
        df_condors = df_condors[df_condors['total_credit'] >= 0.60]
        
        # Rankear por Return on Risk
        df_condors = df_condors.sort_values('return_on_risk', ascending=False)
        
        print(f"\n✅ Iron Condors construidos: {len(df_condors)}")
        print(f"   Crédito promedio: ${df_condors['total_credit'].mean():.2f}")
        print(f"   RoR promedio: {df_condors['return_on_risk'].mean():.1f}%")
        
        return df_condors
    
    def construct_position(self, opportunity: pd.Series) -> Position:
        """
        Construye una posición de Iron Condor desde una oportunidad.
        
        Parámetros:
        -----------
        opportunity : pd.Series
            Fila del DataFrame de oportunidades
        
        Retorna:
        --------
        Position
            Posición completamente definida
        """
        # Construir legs
        legs = [
            {
                'type': 'put',
                'strike': opportunity['put_short_strike'],
                'position': 'short',
                'price': opportunity['put_short_price'],
                'delta': opportunity['put_short_delta'],
                'contracts': 1
            },
            {
                'type': 'put',
                'strike': opportunity['put_long_strike'],
                'position': 'long',
                'price': opportunity['put_long_price'],
                'delta': opportunity['put_long_delta'],
                'contracts': 1
            },
            {
                'type': 'call',
                'strike': opportunity['call_short_strike'],
                'position': 'short',
                'price': opportunity['call_short_price'],
                'delta': opportunity['call_short_delta'],
                'contracts': 1
            },
            {
                'type': 'call',
                'strike': opportunity['call_long_strike'],
                'position': 'long',
                'price': opportunity['call_long_price'],
                'delta': opportunity['call_long_delta'],
                'contracts': 1
            }
        ]
        
        # Calcular parámetros de riesgo
        risk_params = self.risk_manager.calculate_iron_condor_risk(
            dte=int(opportunity['dte']),
            max_credit=opportunity['total_credit'] * 100,  # Convertir a $ por contrato
            width=self.spread_width
        )
        
        # Calcular griegas (simplificado)
        net_greeks = self.calculate_greeks(legs)
        
        # Crear posición
        position = Position(
            strategy_name=self.rules.name,
            entry_date=datetime.now(),
            expiration_date=opportunity['expiration'],
            dte_at_entry=int(opportunity['dte']),
            underlying=opportunity.get('ticker', 'UNKNOWN'),
            underlying_price_entry=opportunity['underlying_price'],
            legs=legs,
            premium_collected=opportunity['total_credit'] * 100,
            max_risk=opportunity['max_risk'],
            delta=net_greeks['delta'],
            gamma=net_greeks['gamma'],
            theta=net_greeks['theta'],
            vega=net_greeks['vega'],
            profit_target=risk_params.profit_target,
            stop_loss=risk_params.stop_loss
        )
        
        return position
    
    def evaluate_exit(self, position: Position, current_data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Evalúa si un Iron Condor debe cerrarse.
        
        Parámetros:
        -----------
        position : Position
            Posición a evaluar
        current_data : pd.DataFrame
            Datos actuales del mercado
        
        Retorna:
        --------
        tuple
            (should_exit: bool, reason: str)
        """
        # Calcular valor actual
        current_prices = {}
        for leg in position.legs:
            leg_data = current_data[
                (current_data['strike'] == leg['strike']) &
                (current_data['type'] == leg['type'])
            ]
            
            if len(leg_data) > 0:
                leg_id = f"{leg['type']}_{leg['strike']}"
                current_prices[leg_id] = leg_data.iloc[0]['close']
        
        if not current_prices:
            return (False, "insufficient_data")
        
        # Calcular valor actual de la posición
        current_value = self.calculate_position_value(position, current_prices)
        
        # Calcular DTE actual
        days_held = (datetime.now() - position.entry_date).days
        current_dte = position.dte_at_entry - days_held
        
        # Obtener parámetros de riesgo
        risk_params = self.risk_manager.calculate_iron_condor_risk(
            dte=current_dte,
            max_credit=position.premium_collected,
            width=self.spread_width
        )
        
        # Evaluar salida
        should_exit, reason = self.risk_manager.should_exit(
            entry_credit=position.premium_collected,
            current_value=current_value,
            dte=current_dte,
            current_delta=position.delta,  # Idealmente actualizar
            risk_params=risk_params
        )
        
        return (should_exit, reason)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Estrategia Iron Condor")
    print("=" * 70)
    
    # Crear datos sintéticos de opciones
    np.random.seed(42)
    n_options = 200
    
    dates = pd.date_range('2025-10-20', periods=1)
    expirations = pd.date_range('2025-12-15', periods=1)
    
    test_options = []
    underlying_price = 670
    
    # Generar puts
    for strike in range(600, 670, 5):
        for date in dates:
            dte = (expirations[0] - date).days
            delta = -0.30 + (strike - 600) / 700  # Delta más negativo para strikes bajos
            
            test_options.append({
                'date': date,
                'ticker': 'SPY',
                'type': 'put',
                'strike': strike,
                'expiration': expirations[0],
                'dte': dte,
                'close': max(0.5, 670 - strike) * (dte / 60) * np.random.uniform(0.8, 1.2),
                'volume': np.random.randint(50, 300),
                'oi': np.random.randint(100, 1000),
                'delta': delta,
                'gamma': 0.01,
                'theta': -0.05,
                'vega': 0.10,
                'iv': np.random.uniform(0.20, 0.30),
                'iv_rank': np.random.uniform(60, 80),
                'underlying_price': underlying_price
            })
    
    # Generar calls
    for strike in range(670, 740, 5):
        for date in dates:
            dte = (expirations[0] - date).days
            delta = 0.30 - (strike - 670) / 700  # Delta más positivo para strikes bajos
            
            test_options.append({
                'date': date,
                'ticker': 'SPY',
                'type': 'call',
                'strike': strike,
                'expiration': expirations[0],
                'dte': dte,
                'close': max(0.5, strike - 670) * (dte / 60) * np.random.uniform(0.8, 1.2),
                'volume': np.random.randint(50, 300),
                'oi': np.random.randint(100, 1000),
                'delta': delta,
                'gamma': 0.01,
                'theta': -0.05,
                'vega': 0.10,
                'iv': np.random.uniform(0.20, 0.30),
                'iv_rank': np.random.uniform(60, 80),
                'underlying_price': underlying_price
            })
    
    df_options = pd.DataFrame(test_options)
    
    print(f"\n📊 Datos de prueba: {len(df_options)} opciones")
    print(f"   Puts: {len(df_options[df_options['type']=='put'])}")
    print(f"   Calls: {len(df_options[df_options['type']=='call'])}")
    print(f"   DTE: {df_options['dte'].iloc[0]} días")
    
    # Crear estrategia
    ic = IronCondor(
        dte_range=(40, 60),
        short_delta_range=(0.15, 0.30),
        long_delta_range=(0.05, 0.15),
        spread_width=5,
        min_iv_rank=60
    )
    
    # Escanear oportunidades
    market_data = {
        'iv_rank': 70,
        'underlying_price': underlying_price
    }
    
    opportunities = ic.scan(df_options, market_data)
    
    if len(opportunities) > 0:
        print(f"\n🎯 Top 3 Iron Condors por RoR:")
        print("-" * 70)
        
        for idx, opp in opportunities.head(3).iterrows():
            print(f"\n   IC #{idx + 1}:")
            print(f"   Put Spread: ${opp['put_short_strike']:.0f}/${opp['put_long_strike']:.0f} = ${opp['put_spread_credit']:.2f}")
            print(f"   Call Spread: ${opp['call_short_strike']:.0f}/${opp['call_long_strike']:.0f} = ${opp['call_spread_credit']:.2f}")
            print(f"   Crédito Total: ${opp['total_credit']:.2f}")
            print(f"   RoR: {opp['return_on_risk']:.1f}%")
            print(f"   Delta Neto: {opp['net_delta']:.3f}")
        
        # Construir posición de ejemplo
        print("\n" + "=" * 70)
        print("Construyendo posición de ejemplo...")
        print("=" * 70)
        
        position = ic.construct_position(opportunities.iloc[0])
        
        print(f"\n✅ Posición creada:")
        print(f"   Estrategia: {position.strategy_name}")
        print(f"   Crédito recibido: ${position.premium_collected:.2f}")
        print(f"   Riesgo máximo: ${position.max_risk:.2f}")
        print(f"   Profit target: ${position.profit_target:.2f}")
        print(f"   Stop loss: ${position.stop_loss:.2f}")
        print(f"   Delta neto: {position.delta:.4f}")
        print(f"   Theta diario: ${position.theta:.2f}")
        
        print(f"\n   Legs ({len(position.legs)}):")
        for leg in position.legs:
            print(f"      {leg['position']:5s} {leg['type']:4s} @ ${leg['strike']:.0f} | ${leg['price']:.2f}")
    
    print("\n" + "=" * 70)
    print("✓ Tests completados")
    print("=" * 70)