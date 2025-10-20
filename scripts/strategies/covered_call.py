# scripts/strategies/covered_call.py
"""
Estrategia Covered Call
========================

Covered Call: Venta de call contra acciones que ya poseemos.

Dos variantes según objetivo:

1. **Income (Ingresos):**
   - Objetivo: Generar ingresos por primas
   - Delta: 0.30-0.40 (OTM, baja probabilidad de asignación)
   - Gestión: Rodar antes de vencimiento si sigue OTM
   
2. **Assignment (Asignación):**
   - Objetivo: Vender las acciones a precio objetivo
   - Delta: 0.60-0.70 (ITM o cerca, alta probabilidad de asignación)
   - Gestión: Mantener hasta vencimiento

Requisitos:
- Poseer 100 acciones del subyacente por contrato
- DTE: 15-60 días
- Preferible alta IV para maximizar prima

Basado en reglas del documento de estrategias modificadas.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .base import StrategyBase, StrategyRules, Position
from .filters import OptionSelector, LiquidityFilter, VolatilityFilter, DTEFilter, DeltaFilter
from .risk_manager import RiskManager


class CoveredCall(StrategyBase):
    """
    Implementación completa de la estrategia Covered Call.
    
    Dos modos de operación:
    
    **INCOME MODE:**
    - Delta strikes: 0.30-0.40 (más OTM)
    - Profit target por DTE:
      - 15-21 DTE: 30%
      - 22-35 DTE: 40%
      - 36-60 DTE: 50%
    - Rodar si quedan pocos días y sigue OTM
    
    **ASSIGNMENT MODE:**
    - Delta strikes: 0.60-0.70 (más ITM)
    - Objetivo: Asignación (mantener hasta vencimiento)
    - No rodar, dejar expirar
    """
    
    def __init__(self,
                 strategy_type: str = "income",
                 dte_range: Tuple[int, int] = (15, 60),
                 min_iv_rank: float = 50.0,
                 min_volume: int = 10,
                 min_open_interest: int = 50,
                 shares_owned: int = 100,
                 base_capital: float = 100000):
        """
        Inicializa la estrategia Covered Call.
        
        Parámetros:
        -----------
        strategy_type : str
            "income" o "assignment"
        dte_range : tuple
            (min_dte, max_dte) en días
        min_iv_rank : float
            IV Rank mínimo (preferible alta IV)
        min_volume : int
            Volumen mínimo
        min_open_interest : int
            Open Interest mínimo
        shares_owned : int
            Número de acciones poseídas (típicamente 100 por contrato)
        base_capital : float
            Capital base para cálculos
        """
        if strategy_type not in ["income", "assignment"]:
            raise ValueError("strategy_type debe ser 'income' o 'assignment'")
        
        # Determinar rango de delta según tipo
        if strategy_type == "income":
            delta_range = (0.30, 0.40)  # Más OTM
        else:  # assignment
            delta_range = (0.60, 0.70)  # Más ITM
        
        rules = StrategyRules(
            name=f"Covered Call ({strategy_type.title()})",
            dte_range=dte_range,
            short_delta_range=delta_range,
            long_delta_range=None,  # No hay long leg
            min_iv_rank=min_iv_rank,
            min_volume=min_volume,
            min_open_interest=min_open_interest
        )
        
        super().__init__(rules)
        
        self.strategy_type = strategy_type
        self.shares_owned = shares_owned
        self.risk_manager = RiskManager(base_capital=base_capital)
        
        # Crear selector de opciones
        self.call_selector = self._create_selector()
    
    def _create_selector(self) -> OptionSelector:
        """
        Crea un selector de calls según el tipo de estrategia.
        
        Retorna:
        --------
        OptionSelector
        """
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
                delta_range=self.rules.short_delta_range,
                option_type='call'
            )
        )
    
    def scan(self, options_data: pd.DataFrame, market_data: Dict) -> pd.DataFrame:
        """
        Escanea el mercado buscando oportunidades de Covered Call.
        
        Proceso:
        1. Filtrar calls que cumplan criterios de delta y liquidez
        2. Calcular premium anualizado
        3. Rankear por premium y/o probabilidad según tipo
        
        Parámetros:
        -----------
        options_data : pd.DataFrame
            Cadena de opciones disponibles
        market_data : dict
            Debe contener: 'iv_rank', 'underlying_price'
        
        Retorna:
        --------
        pd.DataFrame
            Oportunidades de Covered Call rankeadas
        """
        print("\n" + "=" * 70)
        print(f"🔍 ESCANEANDO COVERED CALLS ({self.strategy_type.upper()})")
        print("=" * 70)
        
        # Agregar IV rank si viene en market_data
        if 'iv_rank' in market_data:
            options_data = options_data.copy()
            options_data['iv_rank'] = market_data['iv_rank']
        
        underlying_price = market_data.get('underlying_price',
                                          options_data['underlying_price'].iloc[0] if 'underlying_price' in options_data.columns else None)
        
        # Seleccionar calls
        print(f"\n1️⃣  Seleccionando CALLs (delta {self.rules.short_delta_range})...")
        calls = self.call_selector.select(
            options_data[options_data['type'] == 'call'],
            adjust_for_dte=True
        )
        
        if len(calls) == 0:
            print("   ⚠️  No hay calls disponibles")
            return pd.DataFrame()
        
        # Calcular métricas adicionales
        print("\n2️⃣  Calculando métricas de Covered Call...")
        
        opportunities = []
        
        for _, call in calls.iterrows():
            # Premium recibido
            premium = call['close']
            
            # Return on Stock (premium como % del precio de la acción)
            ros = (premium / underlying_price) * 100 if underlying_price > 0 else 0
            
            # Annualized Return
            days_to_exp = call['dte']
            annualized_return = (ros * 365 / days_to_exp) if days_to_exp > 0 else 0
            
            # Downside protection (cuánto puede caer la acción antes de perder)
            downside_protection = (premium / underlying_price) * 100 if underlying_price > 0 else 0
            
            # Upside potential (ganancia si se asigna)
            if call['strike'] > underlying_price:
                upside = ((call['strike'] - underlying_price + premium) / underlying_price) * 100
            else:
                upside = (premium / underlying_price) * 100
            
            # Probability of profit (aproximada desde delta)
            # Para covered call: ganamos si la acción no sube más allá del strike
            # P(profit) ≈ 1 - abs(delta) para calls vendidos
            pop = (1 - abs(call.get('delta', 0.5))) * 100
            
            opportunities.append({
                'date': call['date'],
                'expiration': call['expiration'],
                'dte': call['dte'],
                'underlying_price': underlying_price,
                'strike': call['strike'],
                'call_price': call['close'],
                'delta': call.get('delta'),
                'gamma': call.get('gamma'),
                'theta': call.get('theta'),
                'vega': call.get('vega'),
                'iv': call.get('iv'),
                'volume': call.get('volume'),
                'oi': call.get('oi'),
                
                # Métricas clave
                'premium': premium,
                'return_on_stock': ros,
                'annualized_return': annualized_return,
                'downside_protection': downside_protection,
                'upside_potential': upside,
                'pop': pop,
                
                # Clasificación
                'moneyness': 'ITM' if call['strike'] < underlying_price else 'ATM' if abs(call['strike'] - underlying_price) < 5 else 'OTM'
            })
        
        df_opportunities = pd.DataFrame(opportunities)
        
        # Filtrar por premium mínimo (al menos 0.25 = $25)
        min_premium = 0.25 if self.strategy_type == "income" else 0.30
        df_opportunities = df_opportunities[df_opportunities['premium'] >= min_premium]
        
        if len(df_opportunities) == 0:
            print(f"   ⚠️  No hay calls con premium mínimo ${min_premium:.2f}")
            return pd.DataFrame()
        
        # Rankear según tipo de estrategia
        if self.strategy_type == "income":
            # Para income: preferir mayor return anualizado
            df_opportunities = df_opportunities.sort_values('annualized_return', ascending=False)
            metric = 'annualized_return'
        else:  # assignment
            # Para assignment: preferir mayor probabilidad de asignación (delta más alto)
            df_opportunities['assignment_prob'] = df_opportunities['delta'].abs()
            df_opportunities = df_opportunities.sort_values('assignment_prob', ascending=False)
            metric = 'assignment_prob'
        
        print(f"\n✅ Covered Calls encontrados: {len(df_opportunities)}")
        print(f"   Premium promedio: ${df_opportunities['premium'].mean():.2f}")
        print(f"   Return anualizado promedio: {df_opportunities['annualized_return'].mean():.1f}%")
        print(f"   PoP promedio: {df_opportunities['pop'].mean():.1f}%")
        
        return df_opportunities
    
    def construct_position(self, opportunity: pd.Series) -> Position:
        """
        Construye una posición de Covered Call desde una oportunidad.
        
        Parámetros:
        -----------
        opportunity : pd.Series
            Fila del DataFrame de oportunidades
        
        Retorna:
        --------
        Position
            Posición completamente definida
        """
        # Verificar que tenemos acciones suficientes
        contracts = self.shares_owned // 100
        if contracts < 1:
            raise ValueError(f"Se necesitan al menos 100 acciones, tienes {self.shares_owned}")
        
        # Construir legs (solo el call vendido, las acciones no son un leg)
        legs = [
            {
                'type': 'call',
                'strike': opportunity['strike'],
                'position': 'short',
                'price': opportunity['call_price'],
                'delta': opportunity['delta'],
                'gamma': opportunity.get('gamma', 0),
                'theta': opportunity.get('theta', 0),
                'vega': opportunity.get('vega', 0),
                'contracts': 1
            }
        ]
        
        # Calcular parámetros de riesgo
        risk_params = self.risk_manager.calculate_covered_call_risk(
            dte=int(opportunity['dte']),
            premium_received=opportunity['premium'] * 100,  # Convertir a $ por contrato
            strategy_type=self.strategy_type
        )
        
        # El "riesgo máximo" de un covered call es ilimitado en teoría
        # (si la acción cae a 0), pero en la práctica es:
        # - Para income: costo de la acción - premium recibido
        # - Para assignment: ninguno (queremos que se asigne)
        underlying_value = opportunity['underlying_price'] * 100  # Por contrato
        max_risk = underlying_value - (opportunity['premium'] * 100)
        
        # Calcular griegas (solo del call vendido, multiplicado por -1 por estar short)
        net_greeks = {
            'delta': -opportunity['delta'] * 100,  # Short call tiene delta negativo
            'gamma': -opportunity.get('gamma', 0) * 100,
            'theta': -opportunity.get('theta', 0) * 100,  # Theta positivo al vender
            'vega': -opportunity.get('vega', 0) * 100,
            'rho': 0  # Menos relevante para covered calls
        }
        
        # Crear posición
        position = Position(
            strategy_name=self.rules.name,
            entry_date=datetime.now(),
            expiration_date=opportunity['expiration'],
            dte_at_entry=int(opportunity['dte']),
            underlying=opportunity.get('ticker', 'UNKNOWN'),
            underlying_price_entry=opportunity['underlying_price'],
            legs=legs,
            premium_collected=opportunity['premium'] * 100,
            max_risk=max_risk,
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
        Evalúa si un Covered Call debe cerrarse o rodarse.
        
        Lógica diferenciada por tipo:
        
        **INCOME:**
        - Profit target alcanzado → Cerrar y tomar beneficio
        - Cerca de vencimiento y OTM → Rodar al próximo mes
        - Delta > 0.50 (amenaza de asignación) → Considerar rodar
        
        **ASSIGNMENT:**
        - Delta > 0.85 (casi segura asignación) → Dejar expirar
        - Mantener hasta vencimiento en casi todos los casos
        
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
        # Buscar el call actual
        call_leg = position.legs[0]
        call_data = current_data[
            (current_data['strike'] == call_leg['strike']) &
            (current_data['type'] == 'call')
        ]
        
        if len(call_data) == 0:
            return (False, "insufficient_data")
        
        current_call = call_data.iloc[0]
        current_price = current_call['close']
        current_delta = current_call.get('delta', 0.5)
        
        # Calcular P&L actual
        pnl = (call_leg['price'] - current_price) * 100
        
        # Calcular DTE actual
        days_held = (datetime.now() - position.entry_date).days
        current_dte = position.dte_at_entry - days_held
        
        # Obtener parámetros de riesgo
        risk_params = self.risk_manager.calculate_covered_call_risk(
            dte=max(current_dte, 1),
            premium_received=position.premium_collected,
            strategy_type=self.strategy_type
        )
        
        # Lógica según tipo de estrategia
        if self.strategy_type == "income":
            # INCOME MODE
            
            # Razón 1: Profit target alcanzado
            if pnl >= risk_params.profit_target:
                return (True, f"profit_target_reached (${pnl:.2f} >= ${risk_params.profit_target:.2f})")
            
            # Razón 2: Cerca de vencimiento y sigue OTM (rodar)
            if current_dte <= risk_params.rollout_threshold_days:
                if current_delta < 0.50:  # Sigue OTM
                    return (True, f"rollout_opportunity (DTE={current_dte}, Delta={current_delta:.2f})")
            
            # Razón 3: Delta muy alto (amenaza de asignación no deseada)
            if current_delta >= risk_params.adjustment_delta_threshold:
                return (True, f"assignment_threat (Delta={current_delta:.2f} >= {risk_params.adjustment_delta_threshold:.2f})")
            
            # Razón 4: Vencimiento
            if current_dte <= 0:
                return (True, "expiration")
            
            # Razón 5: Stop loss (pérdida muy grande - el call subió mucho)
            # Para covered calls, stop loss es cuando la acción subió tanto que el call está muy ITM
            if pnl < 0 and abs(pnl) > position.premium_collected * 2:
                return (True, f"stop_loss_breach (${pnl:.2f})")
        
        else:  # assignment
            # ASSIGNMENT MODE
            
            # Razón 1: Vencimiento (dejar expirar)
            if current_dte <= 0:
                return (True, "expiration_for_assignment")
            
            # Razón 2: Delta muy alto (asignación casi segura - mantener)
            if current_delta >= 0.85:
                # En realidad NO salimos, solo informamos
                return (False, f"assignment_likely (Delta={current_delta:.2f})")
            
            # Razón 3: Solo salir si la acción cayó mucho y ya no queremos vender
            # (esto sería discrecional, aquí no lo implementamos)
            pass
        
        return (False, "holding")
    
    def should_roll(self, position: Position, current_data: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Determina si un Covered Call debe rodarse al próximo vencimiento.
        
        Solo aplica para strategy_type="income".
        
        Retorna:
        --------
        tuple
            (should_roll: bool, roll_details: dict)
        """
        if self.strategy_type != "income":
            return (False, {"reason": "assignment_mode_no_roll"})
        
        should_exit, reason = self.evaluate_exit(position, current_data)
        
        if should_exit and "rollout_opportunity" in reason:
            # Buscar próximo vencimiento
            next_expiration = current_data['expiration'].min()  # Simplificado
            
            return (True, {
                "reason": "near_expiration_otm",
                "current_dte": position.dte_at_entry - (datetime.now() - position.entry_date).days,
                "recommendation": f"Roll to {next_expiration}",
                "action": "close_current_and_sell_next"
            })
        
        return (False, {"reason": "no_roll_needed"})


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Estrategia Covered Call")
    print("=" * 70)
    
    # Crear datos sintéticos de opciones
    np.random.seed(42)
    
    dates = pd.date_range('2025-10-20', periods=1)
    expirations = pd.date_range('2025-12-15', periods=1)
    underlying_price = 670
    
    test_calls = []
    
    # Generar calls con diferentes strikes y deltas
    for strike in range(660, 720, 5):
        for date in dates:
            dte = (expirations[0] - date).days
            
            # Calcular delta aproximado (calls tienen delta positivo)
            moneyness = strike / underlying_price
            if moneyness < 0.98:
                delta = np.random.uniform(0.70, 0.85)  # Deep ITM
            elif moneyness < 1.02:
                delta = np.random.uniform(0.45, 0.55)  # ATM
            else:
                delta = np.random.uniform(0.20, 0.40)  # OTM
            
            # Precio del call (intrínseco + extrínseco)
            intrinsic = max(0, underlying_price - strike)
            extrinsic = (dte / 60) * 5 * np.random.uniform(0.8, 1.2)
            call_price = intrinsic + extrinsic
            
            test_calls.append({
                'date': date,
                'ticker': 'SPY',
                'type': 'call',
                'strike': strike,
                'expiration': expirations[0],
                'dte': dte,
                'close': call_price,
                'volume': np.random.randint(50, 300),
                'oi': np.random.randint(100, 1000),
                'delta': delta,
                'gamma': 0.01,
                'theta': -0.05 * (dte / 60),
                'vega': 0.10,
                'iv': np.random.uniform(0.20, 0.30),
                'iv_rank': np.random.uniform(60, 80),
                'underlying_price': underlying_price
            })
    
    df_calls = pd.DataFrame(test_calls)
    
    print(f"\n📊 Datos de prueba: {len(df_calls)} calls")
    print(f"   Strikes: ${df_calls['strike'].min():.0f} - ${df_calls['strike'].max():.0f}")
    print(f"   Precio subyacente: ${underlying_price:.2f}")
    print(f"   DTE: {df_calls['dte'].iloc[0]} días")
    
    market_data = {
        'iv_rank': 70,
        'underlying_price': underlying_price
    }
    
    # Test 1: Covered Call para Income
    print("\n" + "=" * 70)
    print("Test 1: Covered Call - INCOME MODE")
    print("=" * 70)
    
    cc_income = CoveredCall(
        strategy_type="income",
        dte_range=(40, 60),
        min_iv_rank=60,
        shares_owned=100
    )
    
    opportunities_income = cc_income.scan(df_calls, market_data)
    
    if len(opportunities_income) > 0:
        print(f"\n🎯 Top 5 Covered Calls (Income) por Return Anualizado:")
        print("-" * 70)
        
        for idx, opp in opportunities_income.head(5).iterrows():
            print(f"\n   #{idx + 1}:")
            print(f"   Strike: ${opp['strike']:.0f} ({opp['moneyness']})")
            print(f"   Delta: {opp['delta']:.3f}")
            print(f"   Premium: ${opp['premium']:.2f}")
            print(f"   Return on Stock: {opp['return_on_stock']:.2f}%")
            print(f"   Annualized Return: {opp['annualized_return']:.1f}%")
            print(f"   PoP: {opp['pop']:.1f}%")
        
        # Construir posición de ejemplo
        print("\n" + "-" * 70)
        print("Construyendo posición de ejemplo (Income)...")
        print("-" * 70)
        
        position_income = cc_income.construct_position(opportunities_income.iloc[0])
        
        print(f"\n✅ Posición creada:")
        print(f"   Estrategia: {position_income.strategy_name}")
        print(f"   Strike: ${position_income.legs[0]['strike']:.0f}")
        print(f"   Premium recibido: ${position_income.premium_collected:.2f}")
        print(f"   Profit target: ${position_income.profit_target:.2f}")
        print(f"   Delta neto: {position_income.delta:.2f}")
        print(f"   Theta diario: ${position_income.theta:.2f}")
    
    # Test 2: Covered Call para Assignment
    print("\n" + "=" * 70)
    print("Test 2: Covered Call - ASSIGNMENT MODE")
    print("=" * 70)
    
    cc_assignment = CoveredCall(
        strategy_type="assignment",
        dte_range=(40, 60),
        min_iv_rank=50,
        shares_owned=100
    )
    
    opportunities_assignment = cc_assignment.scan(df_calls, market_data)
    
    if len(opportunities_assignment) > 0:
        print(f"\n🎯 Top 5 Covered Calls (Assignment) por Probabilidad de Asignación:")
        print("-" * 70)
        
        for idx, opp in opportunities_assignment.head(5).iterrows():
            print(f"\n   #{idx + 1}:")
            print(f"   Strike: ${opp['strike']:.0f} ({opp['moneyness']})")
            print(f"   Delta: {opp['delta']:.3f} (Prob. asignación: {opp.get('assignment_prob', 0):.1%})")
            print(f"   Premium: ${opp['premium']:.2f}")
            print(f"   Upside potential: {opp['upside_potential']:.2f}%")
        
        # Construir posición de ejemplo
        print("\n" + "-" * 70)
        print("Construyendo posición de ejemplo (Assignment)...")
        print("-" * 70)
        
        position_assignment = cc_assignment.construct_position(opportunities_assignment.iloc[0])
        
        print(f"\n✅ Posición creada:")
        print(f"   Estrategia: {position_assignment.strategy_name}")
        print(f"   Strike: ${position_assignment.legs[0]['strike']:.0f}")
        print(f"   Premium recibido: ${position_assignment.premium_collected:.2f}")
        print(f"   Objetivo: Asignación a ${position_assignment.legs[0]['strike']:.0f}")
        print(f"   Delta neto: {position_assignment.delta:.2f}")
    
    print("\n" + "=" * 70)
    print("✓ Tests completados")
    print("=" * 70)