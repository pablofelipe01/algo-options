# scripts/strategies/base.py
"""
Clase Base para Estrategias de Opciones
========================================

Define la interfaz común para todas las estrategias de trading.
Cada estrategia específica hereda de StrategyBase.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class StrategyRules:
    """
    Reglas cuantitativas para una estrategia.
    
    Todos los parámetros son numéricos y no discrecionales.
    """
    name: str
    dte_range: Tuple[int, int]  # (min_dte, max_dte)
    short_delta_range: Tuple[float, float]
    long_delta_range: Optional[Tuple[float, float]] = None
    min_iv_rank: float = 50.0
    min_iv_percentile: float = 50.0
    min_premium: float = 0.0
    min_volume: int = 10
    min_open_interest: int = 50
    max_bid_ask_spread: float = 0.10
    profit_target_pct: float = 50.0
    stop_loss_pct: float = 200.0
    
    def is_valid_dte(self, dte: int) -> bool:
        """Verifica si DTE está en rango válido."""
        return self.dte_range[0] <= dte <= self.dte_range[1]
    
    def is_valid_delta(self, delta: float, position: str = 'short') -> bool:
        """Verifica si delta está en rango válido."""
        if position == 'short':
            return self.short_delta_range[0] <= abs(delta) <= self.short_delta_range[1]
        elif position == 'long' and self.long_delta_range:
            return self.long_delta_range[0] <= abs(delta) <= self.long_delta_range[1]
        return False


@dataclass
class Position:
    """
    Representa una posición abierta en el mercado.
    """
    strategy_name: str
    entry_date: datetime
    expiration_date: datetime
    dte_at_entry: int
    underlying: str
    underlying_price_entry: float
    
    # Legs de la estrategia
    legs: List[Dict]  # [{'type': 'call', 'strike': 100, 'position': 'short', ...}]
    
    # Financiero
    premium_collected: float
    max_risk: float
    
    # Griegas al entry
    delta: float
    gamma: float
    theta: float
    vega: float
    
    # Gestión
    profit_target: float
    stop_loss: float
    
    # Estado actual
    is_open: bool = True
    current_value: Optional[float] = None
    current_pnl: Optional[float] = None
    exit_date: Optional[datetime] = None
    exit_reason: Optional[str] = None


class StrategyBase(ABC):
    """
    Clase base abstracta para todas las estrategias de opciones.
    
    Define la interfaz que deben implementar todas las estrategias.
    """
    
    def __init__(self, rules: StrategyRules):
        """
        Inicializa la estrategia con reglas específicas.
        
        Parámetros:
        -----------
        rules : StrategyRules
            Reglas cuantitativas de la estrategia
        """
        self.rules = rules
        self.positions: List[Position] = []
    
    @abstractmethod
    def scan(self, options_data: pd.DataFrame, market_data: Dict) -> pd.DataFrame:
        """
        Escanea el mercado y encuentra oportunidades según las reglas.
        
        Parámetros:
        -----------
        options_data : pd.DataFrame
            Cadena de opciones disponibles
        market_data : dict
            Datos del mercado (IV rank, precio subyacente, etc.)
        
        Retorna:
        --------
        pd.DataFrame
            Oportunidades que cumplen todos los criterios
        """
        pass
    
    @abstractmethod
    def construct_position(self, opportunity: pd.Series) -> Position:
        """
        Construye una posición específica desde una oportunidad.
        
        Parámetros:
        -----------
        opportunity : pd.Series
            Fila del DataFrame de oportunidades
        
        Retorna:
        --------
        Position
            Posición completamente definida
        """
        pass
    
    @abstractmethod
    def evaluate_exit(self, position: Position, current_data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Evalúa si una posición debe cerrarse.
        
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
        pass
    
    def calculate_greeks(self, legs: List[Dict]) -> Dict[str, float]:
        """
        Calcula las griegas netas de la posición.
        
        Parámetros:
        -----------
        legs : list
            Lista de legs con sus griegas individuales
        
        Retorna:
        --------
        dict
            Griegas netas: {'delta': float, 'gamma': float, ...}
        """
        net_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
        
        for leg in legs:
            multiplier = 1 if leg['position'] == 'long' else -1
            contracts = leg.get('contracts', 1)
            
            for greek in net_greeks.keys():
                if greek in leg:
                    net_greeks[greek] += leg[greek] * multiplier * contracts * 100
        
        return net_greeks
    
    def calculate_position_value(self, position: Position, current_prices: Dict) -> float:
        """
        Calcula el valor actual de una posición.
        
        Parámetros:
        -----------
        position : Position
            Posición a valorar
        current_prices : dict
            Precios actuales de cada leg
        
        Retorna:
        --------
        float
            Valor actual de la posición
        """
        total_value = 0.0
        
        for leg in position.legs:
            leg_id = f"{leg['type']}_{leg['strike']}"
            if leg_id in current_prices:
                multiplier = 1 if leg['position'] == 'long' else -1
                contracts = leg.get('contracts', 1)
                total_value += current_prices[leg_id] * multiplier * contracts * 100
        
        return total_value
    
    def calculate_pnl(self, position: Position, current_value: float) -> float:
        """
        Calcula el P&L actual de una posición.
        
        Para posiciones de crédito (vendidas):
        P&L = premium_collected - current_value
        
        Para posiciones de débito (compradas):
        P&L = current_value - premium_paid
        """
        if position.premium_collected > 0:  # Posición de crédito
            return position.premium_collected - current_value
        else:  # Posición de débito
            return current_value + position.premium_collected
    
    def open_position(self, position: Position) -> bool:
        """
        Abre una nueva posición.
        
        Retorna:
        --------
        bool
            True si se abrió exitosamente
        """
        self.positions.append(position)
        return True
    
    def close_position(self, position: Position, exit_date: datetime, 
                      exit_value: float, exit_reason: str) -> None:
        """
        Cierra una posición existente.
        """
        position.is_open = False
        position.exit_date = exit_date
        position.current_value = exit_value
        position.current_pnl = self.calculate_pnl(position, exit_value)
        position.exit_reason = exit_reason
    
    def get_open_positions(self) -> List[Position]:
        """Retorna todas las posiciones abiertas."""
        return [p for p in self.positions if p.is_open]
    
    def get_closed_positions(self) -> List[Position]:
        """Retorna todas las posiciones cerradas."""
        return [p for p in self.positions if not p.is_open]
    
    def get_statistics(self) -> Dict:
        """
        Calcula estadísticas de la estrategia.
        
        Retorna:
        --------
        dict
            Estadísticas completas de performance
        """
        closed = self.get_closed_positions()
        
        if not closed:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0
            }
        
        pnls = [p.current_pnl for p in closed if p.current_pnl is not None]
        winners = [pnl for pnl in pnls if pnl > 0]
        
        return {
            'total_trades': len(closed),
            'win_rate': len(winners) / len(closed) * 100 if closed else 0,
            'avg_pnl': np.mean(pnls) if pnls else 0,
            'total_pnl': sum(pnls) if pnls else 0,
            'avg_winner': np.mean(winners) if winners else 0,
            'avg_loser': np.mean([pnl for pnl in pnls if pnl < 0]) if any(pnl < 0 for pnl in pnls) else 0,
            'largest_winner': max(pnls) if pnls else 0,
            'largest_loser': min(pnls) if pnls else 0,
            'win_loss_ratio': abs(np.mean(winners) / np.mean([pnl for pnl in pnls if pnl < 0])) if any(pnl < 0 for pnl in pnls) and winners else 0
        }
    
    def __repr__(self):
        open_pos = len(self.get_open_positions())
        closed_pos = len(self.get_closed_positions())
        return f"{self.rules.name}(open={open_pos}, closed={closed_pos})"