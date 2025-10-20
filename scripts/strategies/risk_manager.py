# scripts/strategies/risk_manager.py
"""
Gestión de Riesgo Adaptativa
=============================

Gestión de riesgo diferenciada por DTE:
- Objetivos de beneficio adaptativos
- Stop losses dinámicos
- Monitoreo de exposición Gamma
- Ajustes según volatilidad del mercado

Basado en las reglas del documento de estrategias modificadas.
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class RiskParameters:
    """
    Parámetros de riesgo para una posición.
    """
    profit_target: float           # Objetivo de beneficio ($ absolutos)
    profit_target_pct: float       # Objetivo como % del crédito
    stop_loss: float               # Stop loss ($ absolutos)
    stop_loss_pct: float           # Stop loss como % del crédito
    max_position_size: float       # Tamaño máximo de posición (% del capital)
    max_gamma_exposure: float      # Exposición gamma máxima
    rollout_threshold_days: int    # Días antes de vencimiento para rodar
    adjustment_delta_threshold: float  # Delta para considerar ajustes


class RiskManager:
    """
    Gestor de riesgo que adapta parámetros según DTE y condiciones de mercado.
    
    Filosofía:
    - Vencimientos cortos (≤21 DTE): Más conservador, salir antes
    - Vencimientos medios (22-35 DTE): Moderado
    - Vencimientos largos (36-60 DTE): Más agresivo, dejar correr
    """
    
    # Umbrales de categorización DTE
    SHORT_DTE_THRESHOLD = 21
    MEDIUM_DTE_THRESHOLD = 35
    
    def __init__(self, 
                 base_capital: float = 100000,
                 max_position_pct: float = 5.0):
        """
        Parámetros:
        -----------
        base_capital : float
            Capital base de la cuenta
        max_position_pct : float
            % máximo del capital por posición
        """
        self.base_capital = base_capital
        self.max_position_pct = max_position_pct
    
    def calculate_iron_condor_risk(self,
                                   dte: int,
                                   max_credit: float,
                                   width: int = 5) -> RiskParameters:
        """
        Calcula parámetros de riesgo para Iron Condor según DTE.
        
        Reglas del documento:
        - DTE ≤ 21: Profit target 25%, Stop loss 100%
        - DTE 22-35: Profit target 40%, Stop loss 150%
        - DTE 36-60: Profit target 50%, Stop loss 200%
        
        Parámetros:
        -----------
        dte : int
            Days to expiration
        max_credit : float
            Crédito máximo recibido
        width : int
            Ancho del spread (diferencia entre strikes)
        
        Retorna:
        --------
        RiskParameters
            Parámetros de riesgo calculados
        """
        # Determinar categoría DTE
        if dte <= self.SHORT_DTE_THRESHOLD:
            # Vencimiento corto: muy conservador
            profit_target_pct = 25.0
            stop_loss_pct = 100.0
            max_gamma = 0.03
            rollout_days = 7
            adjustment_delta = 0.40
            
        elif dte <= self.MEDIUM_DTE_THRESHOLD:
            # Vencimiento medio: moderado
            profit_target_pct = 40.0
            stop_loss_pct = 150.0
            max_gamma = 0.05
            rollout_days = 14
            adjustment_delta = 0.50
            
        else:
            # Vencimiento largo: más agresivo
            profit_target_pct = 50.0
            stop_loss_pct = 200.0
            max_gamma = 0.08
            rollout_days = 21
            adjustment_delta = 0.60
        
        # Calcular valores absolutos
        profit_target = max_credit * (profit_target_pct / 100)
        stop_loss = max_credit * (stop_loss_pct / 100)
        
        # Tamaño de posición basado en riesgo máximo
        max_risk = (width * 100) - max_credit
        max_position_size = min(
            (self.base_capital * self.max_position_pct / 100) / max_risk,
            self.max_position_pct
        )
        
        return RiskParameters(
            profit_target=profit_target,
            profit_target_pct=profit_target_pct,
            stop_loss=stop_loss,
            stop_loss_pct=stop_loss_pct,
            max_position_size=max_position_size,
            max_gamma_exposure=max_gamma,
            rollout_threshold_days=rollout_days,
            adjustment_delta_threshold=adjustment_delta
        )
    
    def calculate_covered_call_risk(self,
                                    dte: int,
                                    premium_received: float,
                                    strategy_type: str = "income") -> RiskParameters:
        """
        Calcula parámetros de riesgo para Covered Call según DTE.
        
        Parámetros:
        -----------
        dte : int
            Days to expiration
        premium_received : float
            Prima recibida por vender el call
        strategy_type : str
            "income" o "assignment"
        
        Retorna:
        --------
        RiskParameters
            Parámetros de riesgo calculados
        """
        if strategy_type == "income":
            # Covered Call para ingresos
            if dte <= self.SHORT_DTE_THRESHOLD:
                profit_target_pct = 30.0
                rollout_days = 7
                adjustment_delta = 0.50
                
            elif dte <= self.MEDIUM_DTE_THRESHOLD:
                profit_target_pct = 40.0
                rollout_days = 14
                adjustment_delta = 0.50
                
            else:
                profit_target_pct = 50.0
                rollout_days = 21
                adjustment_delta = 0.50
            
            profit_target = premium_received * (profit_target_pct / 100)
            stop_loss = 0  # N/A para covered calls (gestión de acción)
            
        else:  # assignment
            # Covered Call para asignación
            profit_target_pct = 100.0  # Mantener hasta vencimiento
            profit_target = premium_received
            stop_loss = 0
            rollout_days = 0  # No rodar
            adjustment_delta = 0.85  # Solo ajustar si muy ITM
        
        return RiskParameters(
            profit_target=profit_target,
            profit_target_pct=profit_target_pct,
            stop_loss=stop_loss,
            stop_loss_pct=0,
            max_position_size=100.0,  # Limitado por acciones disponibles
            max_gamma_exposure=0.10,  # Menos crítico para covered calls
            rollout_threshold_days=rollout_days,
            adjustment_delta_threshold=adjustment_delta
        )
    
    def should_exit(self,
                   entry_credit: float,
                   current_value: float,
                   dte: int,
                   current_delta: float,
                   risk_params: RiskParameters) -> Tuple[bool, str]:
        """
        Determina si una posición debe cerrarse.
        
        Parámetros:
        -----------
        entry_credit : float
            Crédito recibido al entrar
        current_value : float
            Valor actual de la posición
        dte : int
            Días hasta vencimiento actuales
        current_delta : float
            Delta actual de la posición
        risk_params : RiskParameters
            Parámetros de riesgo de la posición
        
        Retorna:
        --------
        tuple
            (should_exit: bool, reason: str)
        """
        # Calcular P&L actual (para posiciones de crédito)
        current_pnl = entry_credit - current_value
        
        # Razón 1: Profit target alcanzado
        if current_pnl >= risk_params.profit_target:
            return (True, f"profit_target_reached ({current_pnl:.2f} >= {risk_params.profit_target:.2f})")
        
        # Razón 2: Stop loss activado
        if current_pnl <= -risk_params.stop_loss:
            return (True, f"stop_loss_hit ({current_pnl:.2f} <= -{risk_params.stop_loss:.2f})")
        
        # Razón 3: Cerca de vencimiento (rollout threshold)
        if dte <= risk_params.rollout_threshold_days:
            return (True, f"rollout_threshold ({dte} <= {risk_params.rollout_threshold_days} days)")
        
        # Razón 4: Delta excede umbral (posición amenazada)
        if abs(current_delta) >= risk_params.adjustment_delta_threshold:
            return (True, f"delta_threshold_exceeded ({abs(current_delta):.3f} >= {risk_params.adjustment_delta_threshold:.3f})")
        
        # Razón 5: Vencimiento (DTE = 0)
        if dte <= 0:
            return (True, "expiration")
        
        return (False, "holding")
    
    def calculate_position_size(self,
                               max_risk: float,
                               account_size: float,
                               risk_params: RiskParameters) -> int:
        """
        Calcula el número de contratos a operar.
        
        Parámetros:
        -----------
        max_risk : float
            Riesgo máximo por contrato
        account_size : float
            Tamaño de la cuenta
        risk_params : RiskParameters
            Parámetros de riesgo
        
        Retorna:
        --------
        int
            Número de contratos
        """
        # Máximo basado en % de capital
        max_by_capital = int((account_size * self.max_position_pct / 100) / max_risk)
        
        # Mínimo 1 contrato
        return max(1, max_by_capital)
    
    def monitor_gamma_risk(self,
                          position_gamma: float,
                          underlying_price: float,
                          dte: int) -> Dict[str, any]:
        """
        Monitorea riesgo Gamma de una posición.
        
        Gamma es especialmente peligroso en vencimientos cortos.
        
        Parámetros:
        -----------
        position_gamma : float
            Gamma neto de la posición
        underlying_price : float
            Precio del subyacente
        dte : int
            Days to expiration
        
        Retorna:
        --------
        dict
            Alertas y recomendaciones
        """
        # Calcular exposición gamma en $
        # Gamma exposure = Gamma × (Precio)² × 0.01
        gamma_exposure = abs(position_gamma) * (underlying_price ** 2) * 0.01
        
        # Umbrales según DTE
        if dte <= self.SHORT_DTE_THRESHOLD:
            gamma_threshold = 1000  # Más estricto
            alert_level = "high"
        elif dte <= self.MEDIUM_DTE_THRESHOLD:
            gamma_threshold = 2000  # Moderado
            alert_level = "medium"
        else:
            gamma_threshold = 3000  # Relajado
            alert_level = "low"
        
        # Determinar si hay riesgo
        at_risk = gamma_exposure > gamma_threshold
        
        return {
            'gamma': position_gamma,
            'gamma_exposure_dollars': gamma_exposure,
            'gamma_threshold': gamma_threshold,
            'alert_level': alert_level,
            'at_risk': at_risk,
            'recommendation': "Consider closing early" if at_risk else "Monitor",
            'dte': dte
        }
    
    def suggest_adjustment(self,
                          position_delta: float,
                          position_gamma: float,
                          dte: int,
                          underlying_move_pct: float) -> Dict[str, any]:
        """
        Sugiere ajustes a una posición basado en exposición actual.
        
        Parámetros:
        -----------
        position_delta : float
            Delta neto de la posición
        position_gamma : float
            Gamma neto
        dte : int
            Days to expiration
        underlying_move_pct : float
            % de movimiento del subyacente desde entrada
        
        Retorna:
        --------
        dict
            Sugerencias de ajuste
        """
        suggestions = []
        
        # Sugerencia 1: Delta muy alto
        if abs(position_delta) > 0.50:
            suggestions.append({
                'type': 'delta_adjustment',
                'severity': 'high',
                'message': f"Delta alto ({position_delta:.3f}). Considerar roll de strikes amenazados.",
                'action': 'Roll threatened strikes further OTM'
            })
        
        # Sugerencia 2: Gamma riesgo con DTE corto
        if dte <= self.SHORT_DTE_THRESHOLD and abs(position_gamma) > 0.05:
            suggestions.append({
                'type': 'gamma_risk',
                'severity': 'high',
                'message': f"Alto riesgo Gamma con DTE corto ({dte} días)",
                'action': 'Consider closing entire position'
            })
        
        # Sugerencia 3: Movimiento significativo del subyacente
        if abs(underlying_move_pct) > 5.0:
            suggestions.append({
                'type': 'underlying_move',
                'severity': 'medium',
                'message': f"Movimiento significativo del subyacente ({underlying_move_pct:+.1f}%)",
                'action': 'Re-evaluate position risk'
            })
        
        # Sugerencia 4: Cerca de vencimiento con P&L negativo
        if dte <= 7:
            suggestions.append({
                'type': 'expiration_near',
                'severity': 'high',
                'message': f"Muy cerca de vencimiento ({dte} días)",
                'action': 'Close or roll to next expiration'
            })
        
        return {
            'needs_adjustment': len(suggestions) > 0,
            'suggestions': suggestions,
            'priority': 'high' if any(s['severity'] == 'high' for s in suggestions) else 'medium'
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing: Gestión de Riesgo Adaptativa")
    print("=" * 70)
    
    rm = RiskManager(base_capital=100000, max_position_pct=5.0)
    
    # Test 1: Iron Condor con diferentes DTEs
    print("\n" + "=" * 70)
    print("Test 1: Iron Condor - Parámetros por DTE")
    print("=" * 70)
    
    max_credit = 200  # $2.00 por contrato
    
    for dte in [15, 25, 40]:
        risk_params = rm.calculate_iron_condor_risk(dte, max_credit)
        
        print(f"\n📅 DTE = {dte} días:")
        print(f"   Profit Target: ${risk_params.profit_target:.2f} ({risk_params.profit_target_pct:.0f}%)")
        print(f"   Stop Loss: ${risk_params.stop_loss:.2f} ({risk_params.stop_loss_pct:.0f}%)")
        print(f"   Rollout Threshold: {risk_params.rollout_threshold_days} días")
        print(f"   Max Gamma: {risk_params.max_gamma_exposure:.3f}")
        print(f"   Adjustment Delta: {risk_params.adjustment_delta_threshold:.2f}")
    
    # Test 2: Decisión de salida
    print("\n" + "=" * 70)
    print("Test 2: Decisión de Salida")
    print("=" * 70)
    
    risk_params = rm.calculate_iron_condor_risk(dte=30, max_credit=200)
    
    scenarios = [
        ("Profit target alcanzado", 200, 120, 30, 0.10),
        ("Stop loss activado", 200, 500, 30, 0.10),
        ("Delta amenazante", 200, 180, 30, 0.55),
        ("Cerca de vencimiento", 200, 180, 5, 0.10),
        ("Mantener posición", 200, 180, 30, 0.10)
    ]
    
    for scenario_name, entry_credit, current_value, dte, delta in scenarios:
        should_exit, reason = rm.should_exit(
            entry_credit, current_value, dte, delta, risk_params
        )
        pnl = entry_credit - current_value
        
        print(f"\n📊 {scenario_name}:")
        print(f"   P&L: ${pnl:+.2f}")
        print(f"   DTE: {dte} días")
        print(f"   Delta: {delta:.2f}")
        print(f"   Decisión: {'❌ SALIR' if should_exit else '✅ MANTENER'}")
        if should_exit:
            print(f"   Razón: {reason}")
    
    # Test 3: Monitor Gamma
    print("\n" + "=" * 70)
    print("Test 3: Monitor de Riesgo Gamma")
    print("=" * 70)
    
    for dte in [15, 30, 45]:
        gamma_alert = rm.monitor_gamma_risk(
            position_gamma=0.08,
            underlying_price=670,
            dte=dte
        )
        
        print(f"\n📊 DTE = {dte} días:")
        print(f"   Gamma: {gamma_alert['gamma']:.4f}")
        print(f"   Exposición $: ${gamma_alert['gamma_exposure_dollars']:.2f}")
        print(f"   Umbral: ${gamma_alert['gamma_threshold']:.2f}")
        print(f"   Nivel alerta: {gamma_alert['alert_level']}")
        print(f"   ⚠️  En riesgo: {'SÍ' if gamma_alert['at_risk'] else 'NO'}")
        print(f"   Recomendación: {gamma_alert['recommendation']}")
    
    # Test 4: Sugerencias de ajuste
    print("\n" + "=" * 70)
    print("Test 4: Sugerencias de Ajuste")
    print("=" * 70)
    
    adjustment = rm.suggest_adjustment(
        position_delta=0.60,
        position_gamma=0.08,
        dte=15,
        underlying_move_pct=6.5
    )
    
    print(f"\n🔧 Necesita ajuste: {'SÍ' if adjustment['needs_adjustment'] else 'NO'}")
    print(f"   Prioridad: {adjustment['priority']}")
    
    if adjustment['suggestions']:
        print(f"\n   Sugerencias ({len(adjustment['suggestions'])}):")
        for i, sug in enumerate(adjustment['suggestions'], 1):
            print(f"\n   {i}. {sug['type']} [{sug['severity'].upper()}]")
            print(f"      {sug['message']}")
            print(f"      → Acción: {sug['action']}")
    
    print("\n" + "=" * 70)
    print("✓ Tests completados")
    print("=" * 70)