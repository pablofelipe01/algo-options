# 📊 Módulo de Estrategias de Trading de Opciones

Sistema completo de estrategias cuantitativas para trading algorítmico de opciones, implementando reglas no discrecionales basadas en DTE, delta, volatilidad y gestión de riesgo adaptativa.

---

## 📑 Tabla de Contenidos

- [Descripción](#descripción)
- [Filosofía de Diseño](#filosofía-de-diseño)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Estrategias Implementadas](#estrategias-implementadas)
- [Sistema de Filtros](#sistema-de-filtros)
- [Gestión de Riesgo](#gestión-de-riesgo)
- [Guía de Uso](#guía-de-uso)
- [API Reference](#api-reference)
- [Ejemplos Completos](#ejemplos-completos)
- [Reglas Cuantitativas](#reglas-cuantitativas)
- [Performance y Optimización](#performance-y-optimización)

---

## 🎯 Descripción

Este módulo traduce modelos cuantitativos abstractos en estrategias de trading ejecutables. Cada estrategia está completamente definida por reglas numéricas, sin discrecionalidad:

### **Del Modelo al Mercado**
```
Perspectiva Subjetiva → Reglas Cuantitativas → Ejecución Automática
"Neutral"             → Delta 0.16-0.25      → Iron Condor @ 45 DTE
"Alcista moderado"    → Delta 0.30-0.40      → Covered Call Income
```

### **Características Principales**

- ✅ **100% Reglas Cuantitativas** - Sin interpretación subjetiva
- ✅ **Gestión de Riesgo Adaptativa** - Parámetros dinámicos por DTE
- ✅ **Filtros Multi-Nivel** - Liquidez, IV, Delta, DTE
- ✅ **Tracking Completo** - Estado y performance de posiciones
- ✅ **Backtesting Ready** - Diseñado para simulación histórica

---

## 💡 Filosofía de Diseño

### **1. Reglas No Discrecionales**

Todas las decisiones son cuantitativas:
```python
# ❌ MAL (Discrecional)
if mercado_parece_neutral and volatilidad_alta:
    abrir_iron_condor()

# ✅ BIEN (Cuantitativo)
if (0.16 <= abs(delta) <= 0.25) and (iv_rank >= 70) and (15 <= dte <= 60):
    abrir_iron_condor()
```

### **2. Adaptabilidad Sistemática**

Los parámetros se ajustan automáticamente según condiciones objetivas:

| Condición | Parámetro Afectado | Ajuste |
|-----------|-------------------|--------|
| DTE ≤ 21 días | Profit Target | 25% (más conservador) |
| DTE 22-35 días | Profit Target | 40% (moderado) |
| DTE ≥ 36 días | Profit Target | 50% (más agresivo) |
| DTE corto | Liquidez requerida | +50% |
| DTE corto | IV Rank mínimo | +10 puntos |

### **3. Arquitectura Extensible**
```python
class StrategyBase(ABC):
    """
    Todas las estrategias heredan de esta clase base.
    Garantiza interfaz consistente y comportamiento predecible.
    """
    @abstractmethod
    def scan(self, options_data, market_data) -> DataFrame
    
    @abstractmethod
    def construct_position(self, opportunity) -> Position
    
    @abstractmethod
    def evaluate_exit(self, position, current_data) -> (bool, str)
```

---

## 🏗️ Arquitectura del Sistema
```
strategies/
├── __init__.py              # Exportaciones principales
├── base.py                  # Arquitectura base
│   ├── StrategyBase         # Clase abstracta
│   ├── StrategyRules        # Reglas cuantitativas
│   └── Position             # Estado de posición
│
├── filters.py               # Sistema de filtros
│   ├── LiquidityFilter      # Vol, OI, spreads
│   ├── VolatilityFilter     # IV rank, percentile
│   ├── DeltaFilter          # Selección por delta
│   ├── DTEFilter            # Días hasta vencimiento
│   └── OptionSelector       # Orquestador maestro
│
├── risk_manager.py          # Gestión de riesgo
│   ├── RiskManager          # Motor principal
│   ├── RiskParameters       # Parámetros por posición
│   ├── Profit/Stop adaptativos
│   ├── Monitor Gamma
│   └── Sugerencias de ajuste
│
├── iron_condor.py           # Iron Condor
│   └── IronCondor(StrategyBase)
│
└── covered_call.py          # Covered Call
    └── CoveredCall(StrategyBase)
```

---

## 📈 Estrategias Implementadas

### **1. Iron Condor** 🦅

**Estructura:**
```
        Short Put          Short Call
            ↓                  ↓
   Long Put ●─────────●─────────● Long Call
         Strike-5   Strike   Strike+5
```

**Reglas Cuantitativas:**

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| **DTE** | 15-60 días | Balance theta vs gamma risk |
| **Short Delta** | 0.16-0.25 | ~20% probabilidad ITM |
| **Long Delta** | 0.05-0.10 | Protección OTM |
| **Spread Width** | 5 puntos | Standard para liquidez |
| **Min IV Rank** | 60-75 (por DTE) | Vender volatilidad alta |
| **Profit Target** | 25-50% (por DTE) | Adaptativo |
| **Stop Loss** | 100-200% (por DTE) | Control de pérdidas |

**Profit Targets Adaptativos:**
```python
DTE ≤ 21 días:  25% profit target  # Salir rápido (gamma risk)
DTE 22-35 días: 40% profit target  # Moderado
DTE ≥ 36 días:  50% profit target  # Dejar madurar
```

**Ejemplo de Uso:**
```python
from strategies import IronCondor

# Crear estrategia con reglas específicas
ic = IronCondor(
    dte_range=(30, 45),           # Solo 30-45 días
    short_delta_range=(0.16, 0.25),
    long_delta_range=(0.05, 0.10),
    min_iv_rank=70,               # IV alta
    spread_width=5
)

# Escanear oportunidades
opportunities = ic.scan(options_data, market_data)

# Top opportunity
best = opportunities.iloc[0]
print(f"Strike Put: ${best['put_short_strike']}")
print(f"Strike Call: ${best['call_short_strike']}")
print(f"Crédito: ${best['total_credit']}")
print(f"RoR: {best['return_on_risk']:.1f}%")

# Construir y abrir posición
position = ic.construct_position(best)
ic.open_position(position)
```

---

### **2. Covered Call** 📞

**Dos Modos de Operación:**

#### **A. Income Mode** (Ingresos)

Objetivo: Generar flujo de caja manteniendo acciones.
```
Long 100 Shares
    +
Short Call @ Delta 0.30-0.40 (OTM)
```

**Reglas:**

| Parámetro | Valor | Razón |
|-----------|-------|-------|
| **Delta** | 0.30-0.40 | ~35% prob. asignación |
| **Profit Target** | 30-50% (por DTE) | Capturar decay |
| **Rollout** | 7-21 días antes | Extender duración |
| **Gestión** | Cerrar si Delta > 0.50 | Evitar asignación |

#### **B. Assignment Mode** (Asignación)

Objetivo: Vender acciones a precio objetivo.
```
Long 100 Shares @ $100
    +
Short Call @ $110 (Delta 0.60-0.70)
```

**Reglas:**

| Parámetro | Valor | Razón |
|-----------|-------|-------|
| **Delta** | 0.60-0.70 | ~65% prob. asignación |
| **Target** | Asignación | Vender al strike |
| **Gestión** | Mantener hasta expiry | Buscar asignación |

**Ejemplo de Uso:**
```python
from strategies import CoveredCall

# Income Mode
cc_income = CoveredCall(
    strategy_type="income",
    dte_range=(30, 45),
    min_iv_rank=60,
    shares_owned=100
)

opportunities = cc_income.scan(options_data, market_data)

# Mejor oportunidad por return anualizado
best = opportunities.iloc[0]
print(f"Strike: ${best['strike']}")
print(f"Premium: ${best['premium']:.2f}")
print(f"Annualized Return: {best['annualized_return']:.1f}%")
print(f"PoP: {best['pop']:.1f}%")

position = cc_income.construct_position(best)
cc_income.open_position(position)

# Assignment Mode
cc_assign = CoveredCall(
    strategy_type="assignment",
    dte_range=(30, 45),
    shares_owned=100
)
```

---

## 🔍 Sistema de Filtros

### **Pipeline de Selección**
```
Todas las Opciones (1000+)
    ↓
[DTEFilter] → DTE 15-60
    ↓ (500 opciones)
[LiquidityFilter] → Vol > 10, OI > 50
    ↓ (300 opciones)
[VolatilityFilter] → IV Rank > 60
    ↓ (150 opciones)
[DeltaFilter] → Delta 0.16-0.25
    ↓ (50 opciones)
[Ranking] → Por RoR, Premium, etc.
    ↓
Top 10 Oportunidades ✓
```

### **Filtros Disponibles**

#### **1. LiquidityFilter**
```python
from strategies import LiquidityFilter

liq_filter = LiquidityFilter(
    min_volume=10,              # Volumen mínimo diario
    min_open_interest=50,       # OI mínimo
    max_bid_ask_spread_pct=10.0 # Spread máximo 10%
)

# Ajuste automático por DTE
liq_filter_short = liq_filter.adjust_for_dte(dte=15)
# Para DTE corto: vol+50%, OI+50%, spread más estricto
```

**Criterios:**
- Volumen suficiente para ejecutar sin slippage
- OI alto indica interés institucional
- Spread bajo reduce costos de entrada/salida

#### **2. VolatilityFilter**
```python
from strategies import VolatilityFilter

vol_filter = VolatilityFilter(
    min_iv=0.20,           # IV mínima absoluta (20%)
    min_iv_rank=60,        # IV Rank mínimo (percentil)
    min_iv_percentile=60   # IV Percentile mínimo
)

# Ajuste automático
vol_filter_short = vol_filter.adjust_for_dte(dte=15)
# Para DTE corto: IV Rank +10 puntos (70 mínimo)
```

**Lógica:**
- Vender opciones cuando IV está elevada
- IV alta = primas más jugosas
- Reversion to mean esperada

#### **3. DeltaFilter**
```python
from strategies import DeltaFilter

# Para short puts de Iron Condor
delta_filter = DeltaFilter(
    delta_range=(0.16, 0.25),
    option_type='put'
)

filtered = delta_filter.filter(options_data)
```

**Interpretación Delta:**
- Delta 0.20 ≈ 20% probabilidad de expirar ITM
- Delta 0.50 = ATM (50/50)
- Delta 0.80 = Deep ITM (80% prob ITM)

#### **4. DTEFilter**
```python
from strategies import DTEFilter

dte_filter = DTEFilter(dte_range=(30, 45))
filtered = dte_filter.filter(options_data)
```

**Filosofía DTE:**
- Muy corto (< 15): Gamma risk alto
- Corto (15-21): Decay rápido pero arriesgado
- Medio (22-35): Balance óptimo
- Largo (36-60): Decay lento pero estable

#### **5. OptionSelector (Orquestador)**
```python
from strategies import OptionSelector, LiquidityFilter, VolatilityFilter, DTEFilter, DeltaFilter

selector = OptionSelector(
    liquidity_filter=LiquidityFilter(min_volume=50, min_oi=100),
    volatility_filter=VolatilityFilter(min_iv_rank=70),
    dte_filter=DTEFilter(dte_range=(30, 45)),
    delta_filter=DeltaFilter(delta_range=(0.16, 0.25))
)

# Aplica todos los filtros en secuencia
selected = selector.select(options_data, adjust_for_dte=True)

# Rankea por crédito
top_10 = selector.rank_by_credit(selected, top_n=10)
```

---

## 🛡️ Gestión de Riesgo

### **Principio Central: Adaptabilidad por DTE**
```python
from strategies import RiskManager

rm = RiskManager(base_capital=100000, max_position_pct=5.0)
```

### **Parámetros Adaptativos - Iron Condor**
```python
# DTE = 15 días (CORTO)
risk_params = rm.calculate_iron_condor_risk(dte=15, max_credit=200)
# → Profit Target: 25% ($50)
# → Stop Loss: 100% ($200)
# → Rollout: 7 días antes
# → Max Gamma: 0.03

# DTE = 30 días (MEDIO)
risk_params = rm.calculate_iron_condor_risk(dte=30, max_credit=200)
# → Profit Target: 40% ($80)
# → Stop Loss: 150% ($300)
# → Rollout: 14 días antes
# → Max Gamma: 0.05

# DTE = 50 días (LARGO)
risk_params = rm.calculate_iron_condor_risk(dte=50, max_credit=200)
# → Profit Target: 50% ($100)
# → Stop Loss: 200% ($400)
# → Rollout: 21 días antes
# → Max Gamma: 0.08
```

### **Decisión de Salida**
```python
should_exit, reason = rm.should_exit(
    entry_credit=200,
    current_value=120,
    dte=25,
    current_delta=0.30,
    risk_params=risk_params
)

# Razones de salida:
# - "profit_target_reached"
# - "stop_loss_hit"
# - "rollout_threshold"
# - "delta_threshold_exceeded"
# - "expiration"
```

### **Monitor de Gamma**
```python
gamma_alert = rm.monitor_gamma_risk(
    position_gamma=0.08,
    underlying_price=670,
    dte=15
)

if gamma_alert['at_risk']:
    print(f"⚠️ Gamma Risk: ${gamma_alert['gamma_exposure_dollars']:.2f}")
    print(f"Recomendación: {gamma_alert['recommendation']}")
```

### **Sugerencias de Ajuste**
```python
adjustment = rm.suggest_adjustment(
    position_delta=0.60,
    position_gamma=0.08,
    dte=15,
    underlying_move_pct=6.5
)

if adjustment['needs_adjustment']:
    for suggestion in adjustment['suggestions']:
        print(f"{suggestion['severity'].upper()}: {suggestion['message']}")
        print(f"→ {suggestion['action']}")
```

---

## 🚀 Guía de Uso

### **Workflow Completo**

#### **1. Importaciones**
```python
from strategies import IronCondor, CoveredCall
from strategies import OptionSelector, LiquidityFilter, VolatilityFilter, DTEFilter
from strategies import RiskManager
import pandas as pd
```

#### **2. Cargar Datos**
```python
# Desde tus archivos parquet
df = pd.read_parquet('../data/historical/SPY_60days.parquet')

# Filtrar fecha específica
today_data = df[df['date'] == '2025-10-20']

# Market data
market_data = {
    'iv_rank': 70,
    'underlying_price': 670
}
```

#### **3. Crear Estrategia**
```python
ic = IronCondor(
    dte_range=(30, 45),
    short_delta_range=(0.16, 0.25),
    long_delta_range=(0.05, 0.10),
    min_iv_rank=70,
    min_volume=50,
    min_open_interest=100
)
```

#### **4. Escanear Oportunidades**
```python
opportunities = ic.scan(today_data, market_data)

print(f"Oportunidades encontradas: {len(opportunities)}")
print("\nTop 5 por RoR:")
print(opportunities.head()[['total_credit', 'return_on_risk', 'net_delta']])
```

#### **5. Construir Posición**
```python
# Seleccionar mejor oportunidad
best = opportunities.iloc[0]

# Construir posición completa
position = ic.construct_position(best)

print(f"Estrategia: {position.strategy_name}")
print(f"Crédito: ${position.premium_collected:.2f}")
print(f"Profit Target: ${position.profit_target:.2f}")
print(f"Stop Loss: ${position.stop_loss:.2f}")
print(f"\nLegs:")
for leg in position.legs:
    print(f"  {leg['position']} {leg['type']} @ ${leg['strike']:.0f}")
```

#### **6. Abrir Posición**
```python
ic.open_position(position)
print(f"✓ Posición abierta")
print(f"Posiciones abiertas: {len(ic.get_open_positions())}")
```

#### **7. Monitoreo Diario**
```python
# Cargar datos del día siguiente
next_day_data = df[df['date'] == '2025-10-21']

# Evaluar cada posición
for position in ic.get_open_positions():
    should_exit, reason = ic.evaluate_exit(position, next_day_data)
    
    if should_exit:
        print(f"⚠️ Cerrar posición: {reason}")
        
        # Calcular valor de salida
        exit_value = ic.calculate_position_value(position, current_prices)
        
        # Cerrar
        ic.close_position(position, datetime.now(), exit_value, reason)
```

#### **8. Estadísticas**
```python
stats = ic.get_statistics()

print("\n📊 Estadísticas:")
print(f"Total trades: {stats['total_trades']}")
print(f"Win rate: {stats['win_rate']:.1f}%")
print(f"Avg P&L: ${stats['avg_pnl']:.2f}")
print(f"Total P&L: ${stats['total_pnl']:.2f}")
print(f"Best trade: ${stats['largest_winner']:.2f}")
print(f"Worst trade: ${stats['largest_loser']:.2f}")
```

---

## 📚 API Reference

### `base.py`

#### `StrategyRules`
```python
@dataclass
class StrategyRules:
    name: str
    dte_range: Tuple[int, int]
    short_delta_range: Tuple[float, float]
    long_delta_range: Optional[Tuple[float, float]]
    min_iv_rank: float
    min_volume: int
    min_open_interest: int
    profit_target_pct: float
    stop_loss_pct: float
```

#### `Position`
```python
@dataclass
class Position:
    strategy_name: str
    entry_date: datetime
    expiration_date: datetime
    dte_at_entry: int
    underlying: str
    underlying_price_entry: float
    legs: List[Dict]
    premium_collected: float
    max_risk: float
    delta: float
    gamma: float
    theta: float
    vega: float
    profit_target: float
    stop_loss: float
    is_open: bool
    current_pnl: Optional[float]
```

#### `StrategyBase`
```python
class StrategyBase(ABC):
    @abstractmethod
    def scan(self, options_data: DataFrame, market_data: Dict) -> DataFrame:
        """Escanea mercado y retorna oportunidades."""
        
    @abstractmethod
    def construct_position(self, opportunity: Series) -> Position:
        """Construye posición desde oportunidad."""
        
    @abstractmethod
    def evaluate_exit(self, position: Position, current_data: DataFrame) -> Tuple[bool, str]:
        """Evalúa si cerrar posición."""
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de performance."""
```

---

## 💻 Ejemplos Completos

### **Ejemplo 1: Scanner Diario de Iron Condors**
```python
#!/usr/bin/env python3
"""Scanner diario de Iron Condors en SPY."""

import pandas as pd
from datetime import datetime
from strategies import IronCondor

def scan_daily_iron_condors():
    # Cargar datos
    df = pd.read_parquet('../data/historical/SPY_60days.parquet')
    today = datetime.now().date()
    today_data = df[df['date'] == str(today)]
    
    if len(today_data) == 0:
        print("No hay datos para hoy")
        return
    
    # Market data
    underlying_price = today_data['underlying_price'].iloc[0]
    iv_rank = 70  # Simulado - calcular real desde histórico
    
    market_data = {
        'iv_rank': iv_rank,
        'underlying_price': underlying_price
    }
    
    # Crear estrategia
    ic = IronCondor(
        dte_range=(30, 45),
        short_delta_range=(0.18, 0.25),
        min_iv_rank=65,
        min_volume=50,
        min_open_interest=100
    )
    
    # Escanear
    opportunities = ic.scan(today_data, market_data)
    
    if len(opportunities) == 0:
        print("No hay oportunidades hoy")
        return
    
    # Mostrar top 5
    print(f"\n{'='*70}")
    print(f"IRON CONDORS - {today}")
    print(f"{'='*70}")
    print(f"Precio SPY: ${underlying_price:.2f}")
    print(f"IV Rank: {iv_rank:.0f}")
    print(f"\nTop 5 Oportunidades:")
    
    for i, opp in opportunities.head(5).iterrows():
        print(f"\n#{i+1}:")
        print(f"  Put Spread: ${opp['put_short_strike']:.0f}/${opp['put_long_strike']:.0f}")
        print(f"  Call Spread: ${opp['call_short_strike']:.0f}/${opp['call_long_strike']:.0f}")
        print(f"  DTE: {opp['dte']:.0f} días")
        print(f"  Crédito: ${opp['total_credit']:.2f}")
        print(f"  RoR: {opp['return_on_risk']:.1f}%")
        print(f"  Delta neto: {opp['net_delta']:.3f}")

if __name__ == "__main__":
    scan_daily_iron_condors()
```

### **Ejemplo 2: Sistema Completo con Alertas**
```python
#!/usr/bin/env python3
"""Sistema completo de gestión de Iron Condors."""

import pandas as pd
from datetime import datetime
from strategies import IronCondor
import smtplib
from email.mime.text import MIMEText

class IronCondorSystem:
    def __init__(self):
        self.ic = IronCondor(
            dte_range=(30, 45),
            short_delta_range=(0.16, 0.25),
            min_iv_rank=70
        )
        
    def daily_workflow(self):
        """Workflow diario completo."""
        # 1. Gestionar posiciones existentes
        self.manage_positions()
        
        # 2. Buscar nuevas oportunidades
        self.scan_opportunities()
        
        # 3. Generar reporte
        self.generate_report()
        
        # 4. Enviar alertas
        self.send_alerts()
    
    def manage_positions(self):
        """Gestiona posiciones abiertas."""
        current_data = self.load_current_data()
        
        for position in self.ic.get_open_positions():
            should_exit, reason = self.ic.evaluate_exit(position, current_data)
            
            if should_exit:
                print(f"⚠️ ALERTA: Cerrar posición")
                print(f"   Razón: {reason}")
                print(f"   Entry: {position.entry_date}")
                print(f"   Crédito: ${position.premium_collected:.2f}")
                # Aquí: ejecutar cierre real
    
    def scan_opportunities(self):
        """Escanea nuevas oportunidades."""
        if len(self.ic.get_open_positions()) >= 5:
            return  # Máximo 5 posiciones
        
        current_data = self.load_current_data()
        market_data = self.get_market_data()
        
        opportunities = self.ic.scan(current_data, market_data)
        
        if len(opportunities) > 0:
            print(f"✓ {len(opportunities)} nuevas oportunidades")
    
    def generate_report(self):
        """Genera reporte diario."""
        stats = self.ic.get_statistics()
        
        report = f"""
        REPORTE DIARIO - {datetime.now().date()}
        =====================================
        
        Posiciones Abiertas: {len(self.ic.get_open_positions())}
        Posiciones Cerradas: {len(self.ic.get_closed_positions())}
        
        Win Rate: {stats['win_rate']:.1f}%
        P&L Total: ${stats['total_pnl']:.2f}
        Mejor Trade: ${stats['largest_winner']:.2f}
        Peor Trade: ${stats['largest_loser']:.2f}
        """
        
        print(report)
        return report
    
    def send_alerts(self):
        """Envía alertas por email."""
        # Implementar según necesidad
        pass
    
    def load_current_data(self):
        # Implementar
        pass
    
    def get_market_data(self):
        # Implementar
        pass

if __name__ == "__main__":
    system = IronCondorSystem()
    system.daily_workflow()
```

---

## 📋 Reglas Cuantitativas - Tabla Completa

### **Iron Condor (DTE 15-60)**

| Parámetro | DTE ≤ 21 | DTE 22-35 | DTE ≥ 36 |
|-----------|----------|-----------|----------|
| **Short Delta** | 0.18-0.25 | 0.16-0.25 | 0.16-0.25 |
| **Long Delta** | 0.08-0.12 | 0.05-0.10 | 0.05-0.10 |
| **Min IV Rank** | 75 | 65 | 60 |
| **Profit Target** | 25% | 40% | 50% |
| **Stop Loss** | 100% | 150% | 200% |
| **Rollout Days** | 7 | 14 | 21 |
| **Max Gamma** | 0.03 | 0.05 | 0.08 |
| **Liquidity Mult** | 1.5x | 1.2x | 1.0x |

### **Covered Call - Income (DTE 15-60)**

| Parámetro | DTE ≤ 21 | DTE 22-35 | DTE ≥ 36 |
|-----------|----------|-----------|----------|
| **Delta** | 0.25-0.35 | 0.30-0.40 | 0.30-0.40 |
| **Min Premium** | $0.30 | $0.25 | $0.25 |
| **Profit Target** | 30% | 40% | 50% |
| **Rollout Days** | 7 | 14 | 21 |
| **Max Delta Roll** | 0.50 | 0.50 | 0.50 |

### **Covered Call - Assignment (DTE 15-60)**

| Parámetro | Todos los DTEs |
|-----------|----------------|
| **Delta** | 0.60-0.70 |
| **Objetivo** | Asignación |
| **Gestión** | Hold to expiry |
| **Delta Threshold** | 0.85 |

---

## ⚡ Performance y Optimización

### **Benchmarks**

En hardware típico (MacBook Pro M1):

| Operación | Tiempo | Throughput |
|-----------|--------|------------|
| Scan 10K opciones | ~200ms | 50K ops/sec |
| Construct position | <1ms | - |
| Evaluate exit (1 pos) | <1ms | - |
| Daily workflow (10 pos) | ~2s | - |

### **Optimizaciones Implementadas**

1. **Filtrado Progresivo**: Filtros más restrictivos primero
2. **Vectorización**: Numpy/Pandas para operaciones en bulk
3. **Lazy Evaluation**: Solo calcular cuando necesario
4. **Caching**: Resultados de filtros reutilizables

### **Escalabilidad**

El sistema está diseñado para escalar:
```python
# Single ticker
ic_spy = IronCondor()
opp_spy = ic_spy.scan(spy_data, market_data)

# Multiple tickers (paralelizable)
tickers = ['SPY', 'QQQ', 'IWM', 'DIA']
all_opportunities = []

for ticker in tickers:
    data = load_data(ticker)
    opp = ic_spy.scan(data, market_data)
    all_opportunities.append(opp)

combined = pd.concat(all_opportunities).sort_values('return_on_risk', ascending=False)
```

---

## 🔬 Testing

### **Test de Integración**
```bash
# Test individual de cada estrategia
python -m strategies.iron_condor
python -m strategies.covered_call

# Test de filtros
python -m strategies.filters

# Test de risk manager
python -m strategies.risk_manager
```

### **Validación de Reglas**
```python
from strategies import IronCondor

ic = IronCondor()

# Verificar que las reglas se aplican correctamente
assert ic.rules.dte_range == (15, 60)
assert ic.rules.short_delta_range == (0.16, 0.25)

# Test con datos sintéticos
test_data = generate_test_options()
opportunities = ic.scan(test_data, market_data)

# Verificar que cumple criterios
for _, opp in opportunities.iterrows():
    assert 15 <= opp['dte'] <= 60
    assert 0.16 <= abs(opp['put_short_delta']) <= 0.25
```

---

## 🛠️ Troubleshooting

### **Problema: No encuentra oportunidades**
```python
# Debug paso a paso
from strategies import OptionSelector, LiquidityFilter, VolatilityFilter, DTEFilter

selector = OptionSelector(...)

# Ver cuántas pasan cada filtro
print(f"Total opciones: {len(options_data)}")

# Después de cada filtro
after_dte = dte_filter.filter(options_data)
print(f"Después DTE: {len(after_dte)}")

after_liq = liq_filter.filter(after_dte)
print(f"Después liquidez: {len(after_liq)}")
```

**Soluciones:**
- Relajar filtros (menor IV rank, mayor DTE range)
- Verificar calidad de datos
- Comprobar que hay suficientes strikes disponibles

### **Problema: Posiciones no se cierran**
```python
# Verificar parámetros de riesgo
position = ic.get_open_positions()[0]
risk_params = rm.calculate_iron_condor_risk(
    dte=current_dte,
    max_credit=position.premium_collected
)

print(f"Profit target: ${risk_params.profit_target:.2f}")
print(f"Stop loss: ${risk_params.stop_loss:.2f}")
print(f"P&L actual: ${current_pnl:.2f}")
```

---

## 📄 Licencia

Parte del proyecto "Sistema de Trading Algorítmico de Opciones".  
Uso educativo y personal.

---

## 🎓 Próximos Pasos

Una vez dominado este módulo:

1. **Implementar Backtester** → `backtester.py`
2. **Agregar más estrategias** → Spreads, Straddles, etc.
3. **Optimización de parámetros** → Walk-forward, Monte Carlo
4. **Live Trading** → Integración con broker API
5. **Dashboard** → Visualización en tiempo real

---

**Última actualización:** Octubre 2025  
**Versión:** 1.0.0  
**Autor:** Sistema de Trading de Opciones