# 📚 Curriculum: Paper Trading con tastytrade API

## 🎯 Objetivo del Curso

Este es el **Curso 2** de la comunidad de trading algorítmico cuantitativo. Los estudiantes aprenderán a implementar un sistema de paper trading en tiempo real utilizando la API de tastytrade, integrando las estrategias desarrolladas en el Curso 1 (Backtesting).

**Audiencia**: Traders sin conocimientos de programación que quieren entender cómo funciona un sistema de paper trading profesional.

**Duración**: 6-8 semanas (18-22 lecciones)

**Prerequisitos**: Haber completado Curso 1 (Backtesting con 100% win rate)

---

## 📋 Estructura del Curso

### **Módulo 1: Fundamentos del SDK de tastytrade** (1 semana)

#### Lección 1.1: Introducción al API de tastytrade
- **Objetivos**:
  - Entender qué es un API y por qué es importante
  - Conocer las capacidades de tastytrade API
  - Diferenciar entre datos históricos (Polygon) y datos en tiempo real (tastytrade)
  
- **Contenido Conceptual**:
  - ¿Qué es un API REST?
  - Autenticación: username, password, tokens de sesión
  - Concepto de "endpoints" (rutas para obtener datos)
  - Diferencia entre HTTP requests y WebSocket connections
  
- **Ejemplos sin código**:
  - Diagrama visual: Cliente → API → Servidor de tastytrade
  - Flujo de autenticación explicado paso a paso
  - Comparación: llamar al API = hacer una llamada telefónica automatizada
  
- **Ejercicio**:
  - Crear cuenta de prueba en tastytrade
  - Explorar la documentación oficial
  - Identificar 5 endpoints que nos interesan (cuentas, opciones, órdenes)

#### Lección 1.2: Autenticación y Gestión de Sesiones
- **Objetivos**:
  - Entender el proceso de login/logout
  - Aprender sobre tokens de sesión y su expiración
  - Conocer las mejores prácticas de seguridad
  
- **Contenido Conceptual**:
  - ¿Qué es un token de sesión?
  - Expiración de sesiones (por qué y cuándo)
  - Almacenamiento seguro de credenciales
  - Variables de entorno vs hardcoded passwords
  
- **Pseudocódigo**:
  ```
  1. Leer username y password de variables de entorno
  2. Crear sesión con tastytrade
  3. Verificar que la sesión está activa
  4. Si falla, mostrar error y terminar
  5. Si éxito, guardar token para usar después
  ```
  
- **Ejercicio**:
  - Dibujar diagrama de flujo de autenticación
  - Identificar qué hacer si la sesión expira durante trading
  - Crear documento de mejores prácticas de seguridad

#### Lección 1.3: Obtención de Cadenas de Opciones (Option Chains)
- **Objetivos**:
  - Entender qué es una option chain
  - Aprender a filtrar opciones por DTE, Delta, Strike
  - Conocer la estructura de datos de una opción
  
- **Contenido Conceptual**:
  - Componentes de una option chain: strikes, expirations, calls, puts
  - Símbolo de opción: formato estándar (OCC)
  - Filtros importantes: DTE (35-45), Delta (0.15-0.30)
  - Bid/Ask spread y liquidez
  
- **Pseudocódigo**:
  ```
  1. Solicitar option chain para SPY
  2. Filtrar solo expirations entre 35-45 DTE
  3. Para cada expiration:
     a. Filtrar puts con delta entre 0.15-0.30
     b. Seleccionar el strike más cercano a delta objetivo
  4. Devolver lista de opciones candidatas
  ```
  
- **Ejercicio**:
  - Crear tabla con estructura de datos de una opción
  - Dibujar árbol de decisión para filtrar opciones
  - Calcular manualmente cuántas opciones hay en una chain (strikes × expirations × call/put)

---

### **Módulo 2: Streaming de Datos en Tiempo Real** (1-2 semanas)

#### Lección 2.1: Introducción a WebSockets y DXLink
- **Objetivos**:
  - Entender la diferencia entre HTTP requests y WebSockets
  - Conocer el protocolo DXLink de tastytrade
  - Aprender sobre eventos en tiempo real
  
- **Contenido Conceptual**:
  - HTTP: pregunta → respuesta (como SMS)
  - WebSocket: conexión permanente bidireccional (como llamada telefónica)
  - DXLink: protocolo específico de tastytrade para streaming
  - Tipos de eventos: Quote, Greeks, Trade, Candle
  
- **Analogía**:
  - HTTP = Enviar carta por correo y esperar respuesta
  - WebSocket = Línea telefónica abierta todo el día
  
- **Pseudocódigo**:
  ```
  1. Abrir conexión WebSocket con tastytrade
  2. Autenticarse (enviar token de sesión)
  3. Suscribirse a eventos de Quote para SPY
  4. Mantener conexión abierta
  5. Escuchar eventos entrantes en un loop infinito
  6. Procesar cada evento cuando llega
  ```
  
- **Ejercicio**:
  - Dibujar diagrama: Cliente ↔ WebSocket ↔ Servidor
  - Identificar ventajas/desventajas de WebSocket vs HTTP
  - Crear lista de eventos que necesitamos para paper trading

#### Lección 2.2: Streaming de Quotes y Greeks
- **Objetivos**:
  - Suscribirse a cotizaciones en tiempo real
  - Obtener Greeks actualizados (Delta, Theta, Vega, Gamma)
  - Manejar múltiples símbolos simultáneamente
  
- **Contenido Conceptual**:
  - Quote: bid, ask, last, volume, timestamp
  - Greeks: Delta, Theta, Vega, Gamma, Rho
  - Frecuencia de actualizaciones (cada segundo vs cada tick)
  - Concepto de "callback": función que se ejecuta cuando llega dato
  
- **Estructura de Datos** (Quote):
  ```
  Quote {
    symbol: "SPY"
    bid: 450.25
    ask: 450.30
    last: 450.28
    volume: 125000
    timestamp: "2025-10-21T10:30:45.123Z"
  }
  ```
  
- **Estructura de Datos** (Greeks):
  ```
  Greeks {
    symbol: ".SPY251017P450"
    delta: -0.25
    theta: -0.05
    vega: 0.12
    gamma: 0.03
    timestamp: "2025-10-21T10:30:45.234Z"
  }
  ```
  
- **Pseudocódigo**:
  ```
  1. Crear lista de símbolos a monitorear: [SPY, QQQ, IWM, ...]
  2. Para cada símbolo:
     a. Suscribirse a eventos Quote
     b. Suscribirse a eventos Greeks
  3. Definir callback para Quote:
     - Actualizar precio actual en memoria
     - Registrar en log con timestamp
  4. Definir callback para Greeks:
     - Actualizar valores de greeks en memoria
     - Registrar en log con timestamp
  5. Ejecutar loop infinito para mantener conexión
  ```
  
- **Ejercicio**:
  - Crear tabla con todos los campos de Quote y Greeks
  - Diseñar formato de log para almacenar datos
  - Calcular cuántos eventos por minuto esperamos (10 tickers × 2 tipos × 60 segundos)

#### Lección 2.3: Monitoreo de Múltiples Posiciones
- **Objetivos**:
  - Rastrear portafolio virtual en tiempo real
  - Calcular PnL actualizado constantemente
  - Detectar condiciones de salida (profit target, stop loss)
  
- **Contenido Conceptual**:
  - Portafolio como diccionario: {símbolo: posición}
  - Posición: entry_price, current_price, quantity, PnL
  - PnL calculation: (current_price - entry_price) × quantity × multiplier
  - Condiciones de salida: profit_target (50%), stop_loss (-200%)
  
- **Estructura de Datos** (Posición):
  ```
  Position {
    symbol: ".SPY251017P450"
    strategy: "covered_call"
    entry_date: "2025-10-15"
    entry_price: 2.50
    current_price: 1.25
    quantity: -1
    multiplier: 100
    days_held: 6
    unrealized_pnl: 125.00
    profit_target: 1.25  # 50% de 2.50
    stop_loss: 7.50      # -200% de 2.50
  }
  ```
  
- **Pseudocódigo**:
  ```
  1. Mantener diccionario de posiciones abiertas
  2. Cuando llega evento Quote para un símbolo en portafolio:
     a. Obtener posición correspondiente
     b. Actualizar current_price con nuevo bid/ask
     c. Recalcular unrealized_pnl
     d. Verificar si se alcanzó profit_target:
        - Si PnL% ≥ 50%, marcar para cierre
     e. Verificar si se alcanzó stop_loss:
        - Si PnL% ≤ -200%, marcar para cierre urgente
  3. Para posiciones marcadas para cierre:
     - Generar señal de salida
     - Registrar en log
     - Remover de portafolio activo
  ```
  
- **Ejercicio**:
  - Crear tabla de ejemplo con 5 posiciones y sus estados
  - Calcular PnL manualmente para diferentes escenarios
  - Diseñar algoritmo de priorización (¿qué revisar primero?)

---

### **Módulo 3: Gestor de Portafolio Virtual** (2 semanas)

#### Lección 3.1: Arquitectura del Sistema de Paper Trading
- **Objetivos**:
  - Entender los componentes del sistema
  - Conocer el flujo de datos de entrada a salida
  - Aprender sobre separación de responsabilidades
  
- **Contenido Conceptual**:
  - Componentes principales:
    1. **Data Manager**: Obtiene datos en tiempo real
    2. **Signal Generator**: Decide cuándo entrar/salir
    3. **Portfolio Manager**: Gestiona posiciones virtuales
    4. **Order Simulator**: Simula ejecución de órdenes
    5. **Logger**: Registra todo para análisis
  
- **Diagrama de Arquitectura**:
  ```
  [tastytrade API] → [Data Manager] → [Signal Generator]
                                            ↓
                                     [Portfolio Manager]
                                            ↓
                                     [Order Simulator]
                                            ↓
                                        [Logger]
                                            ↓
                                      [Dashboard]
  ```
  
- **Flujo de Datos**:
  1. Data Manager recibe Quote/Greeks de tastytrade
  2. Signal Generator analiza datos y genera señales
  3. Portfolio Manager valida señales (capital, riesgo)
  4. Order Simulator ejecuta órdenes virtuales
  5. Logger registra todo en archivos CSV
  6. Dashboard visualiza estado en tiempo real
  
- **Ejercicio**:
  - Dibujar diagrama de arquitectura personalizado
  - Identificar qué pasa si falla cada componente
  - Crear lista de verificación (checklist) para validación

#### Lección 3.2: Implementación del Portfolio Manager
- **Objetivos**:
  - Gestionar capital virtual ($20,000 inicial)
  - Rastrear posiciones abiertas y cerradas
  - Calcular métricas en tiempo real
  
- **Contenido Conceptual**:
  - Capital management: cash disponible vs usado
  - Posiciones: open, closed, pending
  - Métricas: total_pnl, win_rate, sharpe_ratio
  - Límites: max_positions (10), max_per_ticker (1)
  
- **Estructura de Datos** (Portfolio):
  ```
  Portfolio {
    initial_capital: 20000.00
    current_capital: 21250.00
    cash_available: 19000.00
    cash_in_positions: 2250.00
    open_positions: [Position1, Position2, ...]
    closed_positions: [Position3, Position4, ...]
    total_pnl: 1250.00
    win_rate: 0.95
    total_trades: 20
  }
  ```
  
- **Pseudocódigo** (Abrir Posición):
  ```
  function open_position(signal):
    1. Verificar que cash_available > costo de posición
    2. Verificar que open_positions < max_positions (10)
    3. Verificar que no hay posición abierta en este ticker
    4. Calcular costo: premium × quantity × multiplier
    5. Si todas las validaciones pasan:
       a. Crear objeto Position
       b. Agregar a open_positions
       c. Restar costo de cash_available
       d. Registrar en log
       e. Retornar éxito
    6. Si falla alguna validación:
       a. Registrar rechazo en log
       b. Retornar fallo con razón
  ```
  
- **Pseudocódigo** (Cerrar Posición):
  ```
  function close_position(symbol, exit_price):
    1. Buscar posición en open_positions
    2. Si no existe, retornar error
    3. Calcular PnL: (exit_price - entry_price) × quantity × multiplier
    4. Actualizar posición:
       - exit_price = precio actual
       - exit_date = fecha actual
       - realized_pnl = PnL calculado
       - status = "closed"
    5. Mover posición a closed_positions
    6. Sumar realized_pnl a total_pnl
    7. Liberar cash: sumar exit_price × quantity × multiplier a cash_available
    8. Recalcular win_rate
    9. Registrar en log
    10. Retornar éxito con PnL
  ```
  
- **Ejercicio**:
  - Crear tabla de ejemplo con evolución de capital
  - Simular manualmente 3 trades (2 ganancias, 1 pérdida)
  - Calcular win_rate y total_pnl paso a paso

#### Lección 3.3: Simulación de Ejecución de Órdenes
- **Objetivos**:
  - Simular realísticamente la ejecución de órdenes
  - Considerar slippage y bid/ask spread
  - Manejar órdenes rechazadas
  
- **Contenido Conceptual**:
  - Tipos de órdenes: Market, Limit
  - Slippage: diferencia entre precio esperado y ejecutado
  - Bid/Ask spread: diferencia entre compra y venta
  - Fill assumptions: ¿A qué precio se ejecuta?
  
- **Reglas de Simulación**:
  - **Venta de opción (apertura)**: Ejecutar al **bid** (precio más conservador)
  - **Compra de opción (cierre)**: Ejecutar al **ask** (precio más conservador)
  - **Slippage**: agregar 1-2% de deterioro adicional
  - **Rechazo**: Si spread > 10% del mid-price, rechazar orden
  
- **Pseudocódigo** (Simular Orden):
  ```
  function simulate_order(order):
    1. Obtener cotización actual (bid, ask, mid)
    2. Calcular spread_pct: (ask - bid) / mid
    3. Si spread_pct > 0.10:
       - Rechazar orden (spread muy amplio)
       - Retornar fallo
    4. Si orden es "venta de opción" (apertura):
       a. fill_price = bid
       b. Aplicar slippage: fill_price × 0.98
    5. Si orden es "compra de opción" (cierre):
       a. fill_price = ask
       b. Aplicar slippage: fill_price × 1.02
    6. Calcular costo total: fill_price × quantity × multiplier
    7. Retornar éxito con fill_price y costo
  ```
  
- **Ejercicio**:
  - Crear tabla comparativa: precio teórico vs precio simulado
  - Calcular impacto del slippage en 10 trades
  - Diseñar casos extremos (spreads muy amplios)

---

### **Módulo 4: Generador de Señales en Tiempo Real** (1-2 semanas)

#### Lección 4.1: Adaptación de Estrategias del Backtest
- **Objetivos**:
  - Convertir lógica de backtest a tiempo real
  - Manejar datos incompletos o faltantes
  - Implementar filtros de calidad
  
- **Contenido Conceptual**:
  - Backtest vs Real-time: diferencias clave
  - Backtest: tenemos todos los datos históricos
  - Real-time: solo tenemos datos hasta "ahora"
  - Look-ahead bias: usar datos del futuro (ERROR)
  
- **Diferencias Críticas**:
  | Aspecto | Backtest | Real-Time |
  |---------|----------|-----------|
  | Datos | Históricos completos | Solo hasta ahora |
  | Ejecución | Instantánea | Puede fallar |
  | Precio | Teórico (mid) | Bid/Ask real |
  | Tiempo | Simulado | Real (delays) |
  
- **Pseudocódigo** (Señal de Entrada):
  ```
  function generate_entry_signal(ticker):
    1. Obtener precio actual del underlying (SPY, QQQ, etc.)
    2. Calcular volatilidad reciente (últimos 20 días)
    3. Obtener option chain para este ticker
    4. Filtrar opciones:
       a. DTE entre 35-45 días
       b. Delta entre 0.15-0.30 (para covered call)
       c. Bid/Ask spread < 10%
    5. Si no hay opciones que cumplan criterios:
       - No generar señal
       - Registrar razón en log
       - Retornar None
    6. Seleccionar "mejor" opción:
       - La más cercana a delta objetivo (0.20)
    7. Aplicar parámetros adaptativos según volatilidad:
       - High vol: profit_target=40%, stop_loss=-150%
       - Medium vol: profit_target=50%, stop_loss=-200%
       - Low vol: profit_target=60%, stop_loss=-250%
    8. Crear objeto Signal con todos los parámetros
    9. Retornar Signal
  ```
  
- **Ejercicio**:
  - Identificar 5 diferencias entre backtest y real-time
  - Crear checklist de validación de señales
  - Diseñar manejo de errores (¿qué hacer si falla API?)

#### Lección 4.2: Lógica de Salida Anticipada (Early Exit)
- **Objetivos**:
  - Implementar profit target (50%)
  - Implementar stop loss (-200%)
  - Optimizar turnover de capital
  
- **Contenido Conceptual**:
  - ¿Por qué salir antes de expiración?
  - Ventajas: liberar capital, reducir riesgo
  - Desventajas: comisiones, slippage
  - Nuestro backtest: 75% de trades con early exit
  
- **Reglas de Salida**:
  ```
  Cada 5 minutos (o cada tick):
  1. Para cada posición abierta:
     a. Calcular PnL%: (current_price - entry_price) / entry_price
     b. Si PnL% ≥ 50%:
        - Generar señal de salida (profit_target)
     c. Si PnL% ≤ -200%:
        - Generar señal de salida URGENTE (stop_loss)
     d. Si days_held ≥ DTE - 1:
        - Generar señal de salida (expiration)
  ```
  
- **Pseudocódigo** (Monitor de Salidas):
  ```
  function monitor_exits():
    1. Obtener lista de posiciones abiertas
    2. Para cada posición:
       a. Obtener precio actual (bid/ask)
       b. Calcular unrealized_pnl%
       c. Obtener profit_target y stop_loss de parámetros adaptativos
       d. Si unrealized_pnl% ≥ profit_target:
          - Crear exit_signal con reason="profit_target"
       e. Si unrealized_pnl% ≤ stop_loss:
          - Crear exit_signal con reason="stop_loss", priority=URGENT
       f. Si days_held ≥ (DTE - 1):
          - Crear exit_signal con reason="expiration"
    3. Retornar lista de exit_signals ordenada por prioridad
  ```
  
- **Ejercicio**:
  - Crear tabla de ejemplo con 10 posiciones y sus estados
  - Calcular cuántas deberían cerrarse
  - Diseñar sistema de prioridades (¿qué cerrar primero?)

#### Lección 4.3: Integración con Parámetros Adaptativos
- **Objetivos**:
  - Usar recomendaciones del análisis cuantitativo
  - Ajustar parámetros según volatilidad del ticker
  - Validar que los parámetros funcionan en real-time
  
- **Contenido Conceptual**:
  - Parámetros adaptativos: calculados en Fase 2
  - Clasificación por volatilidad: High, Medium, Low
  - Archivo: `ticker_parameters_recommendations.csv`
  - Cargar una vez al inicio, actualizar semanalmente
  
- **Estructura de Datos** (Parámetros):
  ```
  {
    "SPY": {
      "volatility": "Medium",
      "profit_target": 0.50,
      "stop_loss": -2.00,
      "dte_range": [35, 45]
    },
    "QQQ": {
      "volatility": "High",
      "profit_target": 0.40,
      "stop_loss": -1.50,
      "dte_range": [35, 45]
    },
    ...
  }
  ```
  
- **Pseudocódigo** (Cargar Parámetros):
  ```
  function load_adaptive_parameters():
    1. Leer CSV: ticker_parameters_recommendations.csv
    2. Para cada fila:
       a. Extraer ticker, volatility, profit_target, stop_loss, dte_min, dte_max
       b. Crear diccionario con parámetros
       c. Agregar a parámetros globales
    3. Validar que todos los tickers esperados están presentes
    4. Si falta alguno, usar parámetros default:
       - profit_target: 50%
       - stop_loss: -200%
       - dte_range: [35, 45]
    5. Retornar diccionario de parámetros
  ```
  
- **Pseudocódigo** (Aplicar Parámetros):
  ```
  function apply_parameters(ticker, signal):
    1. Buscar parámetros para este ticker
    2. Si existe en diccionario:
       - signal.profit_target = parámetros[ticker].profit_target
       - signal.stop_loss = parámetros[ticker].stop_loss
       - signal.dte_min = parámetros[ticker].dte_range[0]
       - signal.dte_max = parámetros[ticker].dte_range[1]
    3. Si no existe:
       - Usar parámetros default
       - Registrar warning en log
    4. Retornar signal actualizada
  ```
  
- **Ejercicio**:
  - Crear tabla con parámetros para 10 tickers
  - Calcular impacto de usar parámetros adaptativos vs default
  - Diseñar proceso de actualización semanal

---

### **Módulo 5: Logging y Comparación con Backtest** (1 semana)

#### Lección 5.1: Sistema de Logging Completo
- **Objetivos**:
  - Registrar todas las operaciones del sistema
  - Facilitar debugging y análisis
  - Cumplir con formato esperado por dashboard
  
- **Contenido Conceptual**:
  - ¿Por qué hacer logging?
  - Tipos de logs: trades, signals, errors, performance
  - Formato: CSV para fácil análisis
  - Campos requeridos (compatibles con dashboard existente)
  
- **Estructura de Archivos de Log**:
  ```
  logs/paper_trading/
    ├── trades_YYYYMMDD.csv        # Trades ejecutados
    ├── signals_YYYYMMDD.csv       # Señales generadas
    ├── portfolio_YYYYMMDD.csv     # Estado del portafolio cada hora
    ├── errors_YYYYMMDD.csv        # Errores y excepciones
    └── performance_YYYYMMDD.csv   # Métricas agregadas diarias
  ```
  
- **Campos de trades_YYYYMMDD.csv**:
  ```csv
  ticker,strategy,entry_date,entry_price,exit_date,exit_price,
  premium_collected,days_held,pnl,status,dte,delta,
  profit_target,stop_loss,exit_reason
  ```
  
- **Pseudocódigo** (Log de Trade):
  ```
  function log_trade(position):
    1. Crear registro con todos los campos:
       - ticker: position.symbol
       - strategy: position.strategy
       - entry_date: position.entry_date
       - entry_price: position.entry_price
       - exit_date: datetime.now()
       - exit_price: position.current_price
       - premium_collected: position.entry_price × 100
       - days_held: (exit_date - entry_date).days
       - pnl: position.realized_pnl
       - status: "closed"
       - dte: position.dte
       - delta: position.delta
       - profit_target: position.profit_target
       - stop_loss: position.stop_loss
       - exit_reason: position.exit_reason
    2. Agregar registro a archivo CSV del día actual
    3. Flush para asegurar que se escribió
  ```
  
- **Ejercicio**:
  - Diseñar esquema completo de logging
  - Crear archivo CSV de ejemplo con 5 trades
  - Identificar qué más deberíamos registrar

#### Lección 5.2: Validación vs Backtest
- **Objetivos**:
  - Comparar resultados de paper trading con backtest
  - Identificar discrepancias y sus causas
  - Validar que el sistema funciona correctamente
  
- **Contenido Conceptual**:
  - ¿Por qué comparar con backtest?
  - Diferencias esperadas: slippage, timing, rechazo de órdenes
  - Métricas a comparar: PnL, Win Rate, Sharpe, Trades ejecutados
  - Tolerancia: ±5% es aceptable
  
- **Métricas de Comparación**:
  | Métrica | Backtest | Paper Trading | Diferencia |
  |---------|----------|---------------|------------|
  | Total PnL | $8,594 | ? | ? |
  | Win Rate | 100% | ? | ? |
  | Sharpe | 10.07 | ? | ? |
  | Trades | 37 | ? | ? |
  | Avg Days | 26.4 | ? | ? |
  
- **Pseudocódigo** (Comparar Resultados):
  ```
  function compare_with_backtest():
    1. Cargar métricas del backtest (CSV histórico)
    2. Calcular métricas del paper trading (logs recientes)
    3. Para cada métrica:
       a. Calcular diferencia absoluta
       b. Calcular diferencia porcentual
       c. Si diferencia > 5%:
          - Marcar como "discrepancia"
          - Investigar causa
       d. Si diferencia < 5%:
          - Marcar como "dentro de tolerancia"
    4. Generar reporte de validación
    5. Si hay discrepancias críticas:
       - Alertar al usuario
       - Sugerir revisión manual
  ```
  
- **Ejercicio**:
  - Crear tabla de comparación manualmente
  - Identificar 5 causas posibles de discrepancia
  - Diseñar proceso de investigación de discrepancias

#### Lección 5.3: Integración con Dashboard Existente
- **Objetivos**:
  - Extender dashboard para incluir paper trading
  - Comparar visualmente backtest vs paper trading
  - Monitorear performance en tiempo real
  
- **Contenido Conceptual**:
  - Dashboard actual: 5 tabs (Overview, Performance, Early Closures, ML Dataset, Parameters)
  - Nueva tab: "Paper Trading Live"
  - Componentes: Portafolio actual, PnL en tiempo real, Comparación con backtest
  
- **Diseño de Nueva Tab**:
  ```
  Tab 6: Paper Trading Live
  ┌─────────────────────────────────────────┐
  │ Métricas en Tiempo Real                 │
  │ - Capital actual: $21,250               │
  │ - Posiciones abiertas: 8                │
  │ - PnL del día: +$450                    │
  │ - PnL total: +$1,250                    │
  └─────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────┐
  │ Posiciones Abiertas                     │
  │ Tabla con: ticker, strategy, days_held, │
  │ unrealized_pnl, profit_target, stop_loss│
  └─────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────┐
  │ Comparación: Backtest vs Paper Trading  │
  │ Gráfico de barras lado a lado           │
  └─────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────┐
  │ Últimos Trades Ejecutados               │
  │ Tabla con últimos 10 trades             │
  └─────────────────────────────────────────┘
  ```
  
- **Pseudocódigo** (Actualizar Dashboard):
  ```
  function update_dashboard():
    1. Leer logs de paper trading del día actual
    2. Calcular métricas:
       - capital_actual
       - posiciones_abiertas (count)
       - pnl_del_dia (sum de trades hoy)
       - pnl_total (sum de todos los trades)
    3. Obtener lista de posiciones abiertas del Portfolio Manager
    4. Crear visualizaciones:
       - Gráfico de PnL acumulado (línea temporal)
       - Tabla de posiciones abiertas
       - Gráfico comparativo (barras)
       - Tabla de últimos trades
    5. Renderizar en Streamlit
    6. Configurar auto-refresh cada 30 segundos
  ```
  
- **Ejercicio**:
  - Diseñar mockup de la nueva tab
  - Identificar datos necesarios para cada visualización
  - Crear lista de funcionalidades adicionales deseables

---

### **Módulo 6: Testing y Despliegue** (1 semana)

#### Lección 6.1: Unit Testing y Validación
- **Objetivos**:
  - Validar que cada componente funciona correctamente
  - Crear tests automáticos
  - Detectar bugs antes de ir a producción
  
- **Contenido Conceptual**:
  - ¿Qué es un unit test?
  - ¿Por qué son importantes?
  - Estructura: Arrange, Act, Assert
  - Mocking: simular respuestas de API
  
- **Tests Críticos**:
  ```
  1. Test de autenticación:
     - Verificar login exitoso
     - Verificar manejo de credenciales incorrectas
     - Verificar expiración de sesión
  
  2. Test de option chain:
     - Verificar filtrado por DTE
     - Verificar filtrado por Delta
     - Verificar manejo de chain vacía
  
  3. Test de señales:
     - Verificar generación de señal válida
     - Verificar rechazo de señal inválida
     - Verificar aplicación de parámetros adaptativos
  
  4. Test de portfolio manager:
     - Verificar apertura de posición
     - Verificar cierre de posición
     - Verificar validación de capital
     - Verificar límite de posiciones
  
  5. Test de order simulator:
     - Verificar cálculo de slippage
     - Verificar rechazo por spread amplio
     - Verificar fill price correcto
  ```
  
- **Pseudocódigo** (Test Ejemplo):
  ```
  test_open_position():
    # Arrange
    portfolio = crear_portfolio_con_20k()
    signal = crear_señal_valida()
    
    # Act
    resultado = portfolio.open_position(signal)
    
    # Assert
    assert resultado.success == True
    assert portfolio.open_positions.length == 1
    assert portfolio.cash_available == 20000 - costo_posicion
  ```
  
- **Ejercicio**:
  - Crear lista de 10 tests críticos
  - Diseñar casos de prueba (inputs y outputs esperados)
  - Identificar qué componentes son más riesgosos

#### Lección 6.2: Forward Testing Protocol
- **Objetivos**:
  - Ejecutar sistema en modo observación
  - Recolectar datos durante 1-2 semanas
  - Validar antes de trading real
  
- **Contenido Conceptual**:
  - Forward testing: ejecutar sistema sin dinero real
  - Observación: monitorear sin intervenir
  - Duración recomendada: 2-4 semanas
  - Criterios de éxito para pasar a siguiente fase
  
- **Protocolo de Forward Testing**:
  ```
  Semana 1-2: Observación Pasiva
  - Ejecutar sistema en modo simulación
  - No modificar código ni parámetros
  - Registrar todas las operaciones
  - Monitorear errores y excepciones
  - Generar reporte diario
  
  Semana 3-4: Observación Activa
  - Continuar simulación
  - Comparar con backtest semanalmente
  - Ajustar parámetros si es necesario
  - Validar métricas vs expectativas
  - Decidir si está listo para siguiente fase
  ```
  
- **Criterios de Aprobación**:
  ```
  Para pasar a siguiente fase:
  ✅ Win Rate ≥ 90% (backtest: 100%)
  ✅ PnL ≥ 90% del backtest (tolerancia 10%)
  ✅ Sharpe ≥ 8.0 (backtest: 10.07)
  ✅ Sin errores críticos en 2 semanas
  ✅ Discrepancias explicadas y documentadas
  ✅ Dashboard funcionando sin fallos
  ```
  
- **Pseudocódigo** (Validación Semanal):
  ```
  function weekly_validation():
    1. Recolectar métricas de la semana:
       - Total trades ejecutados
       - Win rate actual
       - PnL acumulado
       - Sharpe ratio
       - Errores registrados
    2. Comparar con backtest:
       - Calcular diferencias porcentuales
       - Identificar discrepancias > 10%
    3. Analizar errores:
       - Agrupar por tipo
       - Identificar patrones
       - Priorizar por severidad
    4. Generar reporte:
       - Métricas de la semana
       - Comparación con backtest
       - Lista de errores
       - Recomendaciones
    5. Decidir: ¿Continuar, Ajustar, o Detener?
  ```
  
- **Ejercicio**:
  - Crear plantilla de reporte semanal
  - Diseñar checklist de validación
  - Identificar red flags (señales de alerta)

#### Lección 6.3: Monitoreo y Mantenimiento
- **Objetivos**:
  - Configurar alertas automáticas
  - Establecer rutinas de revisión
  - Planear actualizaciones futuras
  
- **Contenido Conceptual**:
  - Monitoreo continuo: revisar diariamente
  - Alertas: notificaciones automáticas cuando hay problema
  - Mantenimiento: actualizar parámetros semanalmente
  - Escalamiento: preparar para más tickers
  
- **Sistema de Alertas**:
  ```
  Alertas Críticas (Detener sistema):
  ⚠️ Error de autenticación
  ⚠️ Conexión WebSocket caída > 5 min
  ⚠️ PnL diario < -$1000
  ⚠️ Win rate < 80% en última semana
  
  Alertas de Advertencia (Revisar):
  ⚡ Señal rechazada por spread amplio
  ⚡ Capital disponible < 20%
  ⚡ Posición con PnL < -150%
  ⚡ Trade ejecutado con slippage > 3%
  
  Alertas Informativas (Monitorear):
  💡 Nueva posición abierta
  💡 Posición cerrada con profit
  💡 Actualización de parámetros adaptativos
  💡 Reporte semanal generado
  ```
  
- **Rutina Diaria**:
  ```
  Cada día al abrir mercado (9:30 AM ET):
  1. Verificar que sistema está corriendo
  2. Revisar alertas de la noche
  3. Validar conexión a tastytrade API
  4. Confirmar que posiciones están sincronizadas
  
  Cada día al cerrar mercado (4:00 PM ET):
  1. Revisar trades del día
  2. Validar PnL vs esperado
  3. Generar reporte diario
  4. Backup de logs
  ```
  
- **Rutina Semanal**:
  ```
  Cada viernes después del cierre:
  1. Ejecutar análisis cuantitativo actualizado
  2. Recalcular parámetros adaptativos
  3. Actualizar ticker_parameters_recommendations.csv
  4. Generar reporte semanal
  5. Comparar con backtest
  6. Planear ajustes para próxima semana
  ```
  
- **Pseudocódigo** (Sistema de Alertas):
  ```
  function check_and_alert():
    # Alertas Críticas
    if not api_connected():
      send_alert("CRÍTICO: API desconectada", urgency=HIGH)
      stop_system()
    
    if daily_pnl < -1000:
      send_alert("CRÍTICO: Pérdida diaria > $1000", urgency=HIGH)
      stop_new_positions()
    
    # Alertas de Advertencia
    if cash_available < total_capital * 0.20:
      send_alert("ADVERTENCIA: Capital < 20%", urgency=MEDIUM)
    
    for position in open_positions:
      if position.unrealized_pnl_pct < -1.50:
        send_alert(f"ADVERTENCIA: {position.symbol} PnL < -150%", urgency=MEDIUM)
    
    # Alertas Informativas
    if new_trade_executed:
      send_alert(f"INFO: Nueva posición {trade.symbol}", urgency=LOW)
  ```
  
- **Ejercicio**:
  - Diseñar sistema de notificaciones (email, SMS, Slack)
  - Crear checklist de revisión diaria y semanal
  - Planear roadmap de mejoras futuras

---

## 🎯 Objetivos de Aprendizaje por Módulo

### Módulo 1: SDK Fundamentals
**Dominio Conceptual**:
- ✅ Entender arquitectura cliente-servidor
- ✅ Conocer flujo de autenticación
- ✅ Manejar option chains y filtros

**Habilidades Prácticas**:
- ✅ Navegar documentación de API
- ✅ Identificar endpoints relevantes
- ✅ Diseñar flujos de datos

### Módulo 2: Streaming Data
**Dominio Conceptual**:
- ✅ Diferencia HTTP vs WebSocket
- ✅ Eventos en tiempo real
- ✅ Callbacks y async programming (conceptualmente)

**Habilidades Prácticas**:
- ✅ Diseñar sistema de subscripciones
- ✅ Calcular PnL en tiempo real
- ✅ Detectar condiciones de salida

### Módulo 3: Portfolio Manager
**Dominio Conceptual**:
- ✅ Gestión de capital virtual
- ✅ Validación de riesgos
- ✅ Simulación realista de órdenes

**Habilidades Prácticas**:
- ✅ Diseñar arquitectura de componentes
- ✅ Calcular métricas de performance
- ✅ Manejar slippage y spreads

### Módulo 4: Signal Generator
**Dominio Conceptual**:
- ✅ Backtest vs Real-time
- ✅ Parámetros adaptativos
- ✅ Early exit optimization

**Habilidades Prácticas**:
- ✅ Adaptar estrategias a tiempo real
- ✅ Aplicar filtros de calidad
- ✅ Integrar análisis cuantitativo

### Módulo 5: Logging & Comparison
**Dominio Conceptual**:
- ✅ Importancia del logging
- ✅ Validación vs backtest
- ✅ Visualización de datos

**Habilidades Prácticas**:
- ✅ Diseñar esquema de logs
- ✅ Comparar métricas
- ✅ Extender dashboard

### Módulo 6: Testing & Deployment
**Dominio Conceptual**:
- ✅ Unit testing
- ✅ Forward testing protocol
- ✅ Monitoreo continuo

**Habilidades Prácticas**:
- ✅ Validar componentes
- ✅ Ejecutar forward testing
- ✅ Configurar alertas

---

## 📊 Métricas de Éxito

### Durante el Curso
- [ ] 100% de módulos completados
- [ ] Todos los ejercicios entregados
- [ ] Comprensión conceptual validada en quizzes
- [ ] Participación activa en sesiones

### Post-Curso (Forward Testing)
- [ ] Win Rate ≥ 90%
- [ ] PnL ≥ 90% del backtest
- [ ] Sharpe Ratio ≥ 8.0
- [ ] Sistema corriendo sin errores críticos
- [ ] Dashboard actualizado y funcional

---

## 🗓️ Timeline Estimado

**Total: 6-8 semanas**

```
Semana 1: Módulo 1 (SDK Fundamentals)
├─ Lección 1.1: Introducción al API
├─ Lección 1.2: Autenticación
└─ Lección 1.3: Option Chains

Semana 2-3: Módulo 2 (Streaming Data)
├─ Lección 2.1: WebSockets y DXLink
├─ Lección 2.2: Quotes y Greeks
└─ Lección 2.3: Monitoreo Multi-Posición

Semana 3-5: Módulo 3 (Portfolio Manager)
├─ Lección 3.1: Arquitectura del Sistema
├─ Lección 3.2: Implementación Portfolio Manager
└─ Lección 3.3: Simulación de Órdenes

Semana 5-6: Módulo 4 (Signal Generator)
├─ Lección 4.1: Adaptación de Estrategias
├─ Lección 4.2: Lógica de Salida Anticipada
└─ Lección 4.3: Parámetros Adaptativos

Semana 7: Módulo 5 (Logging & Comparison)
├─ Lección 5.1: Sistema de Logging
├─ Lección 5.2: Validación vs Backtest
└─ Lección 5.3: Dashboard Integration

Semana 8: Módulo 6 (Testing & Deployment)
├─ Lección 6.1: Unit Testing
├─ Lección 6.2: Forward Testing Protocol
└─ Lección 6.3: Monitoreo y Mantenimiento

Semana 9-10: Forward Testing (2 semanas mínimo)
Semana 11+: Transición a Curso 3 (ML Integration)
```

---

## 📦 Entregables del Curso

### Documentos
1. **Diagramas de Arquitectura**
   - Flujo completo del sistema
   - Componentes y sus interacciones
   - Flujo de datos entrada → salida

2. **Diagramas de Flujo**
   - Generación de señales
   - Ejecución de órdenes
   - Monitoreo de salidas

3. **Tablas de Parámetros**
   - Parámetros adaptativos por ticker
   - Reglas de validación
   - Límites y thresholds

4. **Checklists**
   - Validación pre-ejecución
   - Revisión diaria
   - Revisión semanal

### Código (Conceptual)
1. **Pseudocódigo de Componentes Clave**
   - Portfolio Manager
   - Signal Generator
   - Order Simulator
   - Logger

2. **Plantillas de Tests**
   - Unit tests críticos
   - Casos de prueba

3. **Scripts de Utilidad** (conceptuales)
   - Validación semanal
   - Generación de reportes
   - Sistema de alertas

### Reportes
1. **Reporte de Forward Testing** (semanal)
   - Métricas de performance
   - Comparación con backtest
   - Lista de errores y ajustes

2. **Reporte Final**
   - Resumen de 2 semanas de forward testing
   - Validación de criterios de aprobación
   - Recomendaciones para siguiente fase

---

## 🔗 Integración con Roadmap General

### Curso 1: Backtesting (COMPLETADO ✅)
- Estrategias: Covered Call, Iron Condor
- Análisis cuantitativo
- Parámetros adaptativos
- Dashboard de visualización
- **Resultado**: 100% win rate, $8,594 PnL en 37 trades

### Curso 2: Paper Trading (ESTE CURSO)
- Integración con tastytrade API
- Streaming en tiempo real
- Portfolio management virtual
- Forward testing 2-4 semanas
- **Objetivo**: Validar estrategias en condiciones reales

### Curso 3: ML Integration (FUTURO)
- Predicción de volatilidad
- Optimización de parámetros dinámicos
- Detección de regímenes de mercado
- Backtesting con ML
- **Objetivo**: Mejorar win rate y Sharpe ratio

### Curso 4: Live Trading (FUTURO)
- Ejecución con dinero real
- Risk management avanzado
- Monitoring 24/7
- Escalamiento a más tickers
- **Objetivo**: Trading algorítmico productivo

---

## 🛠️ Herramientas y Recursos

### Software Requerido
- Python 3.9+
- tastytrade account (gratuita)
- VS Code o IDE similar
- Git para control de versiones

### Librerías Python (conceptual)
```
tastytrade         # SDK oficial
pandas             # Análisis de datos
numpy              # Cálculos numéricos
streamlit          # Dashboard
plotly             # Visualizaciones
asyncio            # Async programming
```

### Recursos de Aprendizaje
- Documentación oficial de tastytrade
- tastyware/tastytrade GitHub repo
- Documentación de pandas/numpy
- Tutoriales de async/await en Python

### Datos Necesarios
- `ticker_parameters_recommendations.csv` (del Curso 1)
- `ml_dataset_10_tickers.csv` (del Curso 1)
- Logs de backtest (para comparación)

---

## 💡 Consejos Pedagógicos

### Para el Instructor
1. **Usar analogías del mundo real**: API = llamada telefónica, WebSocket = línea abierta
2. **Dibujar diagramas abundantemente**: La visualización ayuda a conceptos abstractos
3. **Ejercicios incrementales**: Empezar simple, agregar complejidad gradualmente
4. **Pseudocódigo primero**: Lógica antes que sintaxis
5. **Debugging en vivo**: Mostrar errores reales y cómo resolverlos

### Para el Estudiante
1. **Tomar notas visuales**: Diagramas > texto
2. **Practicar sin código**: Pseudocódigo en papel primero
3. **Hacer todos los ejercicios**: No saltear, cada uno construye sobre el anterior
4. **Preguntar sin miedo**: No hay preguntas tontas
5. **Revisar material previo**: Curso 1 es la base, mantenerlo fresco

---

## 🚨 Puntos Críticos de Atención

### Errores Comunes a Evitar
1. **Look-ahead bias**: Usar datos del futuro en decisiones presentes
2. **Overfitting en parámetros**: Ajustar demasiado a backtest específico
3. **Ignorar slippage**: Asumir ejecución perfecta
4. **No manejar errores**: API puede fallar, siempre tener plan B
5. **Complejidad prematura**: Empezar simple, agregar features gradualmente

### Validaciones Críticas
1. **Capital nunca negativo**: Validar antes de cada trade
2. **Posiciones sincronizadas**: API vs local siempre igual
3. **Timestamps correctos**: Timezone-aware siempre (ET para US markets)
4. **Logs completos**: Nunca perder datos, cada operación registrada
5. **Backups diarios**: Logs y estado del portfolio

---

## 📈 KPIs para Monitorear

### Diarios
- Total trades ejecutados
- PnL del día
- Posiciones abiertas (count)
- Cash disponible
- Errores registrados

### Semanales
- Win rate acumulado
- PnL total
- Sharpe ratio
- Comparación con backtest (%)
- Trades promedio por día

### Mensuales
- ROI (%)
- Sharpe ratio mensual
- Drawdown máximo
- Ratio de early closures
- Uptime del sistema (%)

---

## 🎓 Evaluación del Estudiante

### Quizzes por Módulo
- Módulo 1: 10 preguntas sobre API y autenticación
- Módulo 2: 10 preguntas sobre WebSockets y streaming
- Módulo 3: 10 preguntas sobre portfolio management
- Módulo 4: 10 preguntas sobre signal generation
- Módulo 5: 10 preguntas sobre logging y validación
- Módulo 6: 10 preguntas sobre testing y deployment

### Proyecto Final
**Forward Testing de 2 Semanas**
- Ejecutar sistema en modo simulación
- Generar reportes semanales
- Presentar resultados finales
- Defender decisiones de diseño
- Proponer mejoras futuras

### Criterios de Aprobación
- [ ] 80% mínimo en todos los quizzes
- [ ] Todos los ejercicios completados
- [ ] Forward testing ejecutado sin errores críticos
- [ ] Métricas ≥ 90% del backtest
- [ ] Proyecto final aprobado

---

## 🔮 Próximos Pasos (Post-Curso)

### Inmediato (1-2 semanas)
1. Ejecutar forward testing completo
2. Validar métricas vs backtest
3. Documentar aprendizajes
4. Decidir si pasar a ML Integration

### Corto Plazo (1-2 meses)
1. Extender a 20-30 tickers
2. Agregar más estrategias (Bull Put Spread, etc.)
3. Optimizar performance (latency, throughput)
4. Mejorar dashboard con más features

### Mediano Plazo (3-6 meses)
1. Integrar ML para predicción de volatilidad
2. Implementar regime detection
3. A/B testing de diferentes configuraciones
4. Preparar para live trading

### Largo Plazo (6-12 meses)
1. Transición a live trading con capital pequeño
2. Escalamiento progresivo
3. Automatización completa
4. Desarrollo de comunidad y recursos educativos

---

## 📞 Soporte y Recursos

### Durante el Curso
- Sesiones en vivo: 2 por semana
- Q&A sessions: Viernes al final de cada módulo
- Foro privado: Preguntas asíncronas
- Materiales: Videos, diagramas, pseudocódigo

### Post-Curso
- Comunidad Skool.com: Networking y colaboración
- Updates mensuales: Nuevas features y mejores prácticas
- Office hours: Consultas 1-on-1 para troubleshooting
- Roadmap compartido: Colaboración en futuras fases

---

## 📝 Notas Finales

Este curriculum está diseñado para traders sin background de programación que quieren entender **conceptualmente** cómo funciona un sistema de paper trading profesional.

**No se espera que los estudiantes escriban código** durante el curso, pero sí que entiendan:
- ¿Qué hace cada componente?
- ¿Por qué está diseñado así?
- ¿Cómo fluyen los datos?
- ¿Qué decisiones se toman y cuándo?
- ¿Cómo validar que funciona correctamente?

El objetivo es que al finalizar el curso, los estudiantes puedan:
1. **Supervisar** un sistema de paper trading con confianza
2. **Identificar** problemas cuando surgen
3. **Proponer** mejoras y ajustes
4. **Colaborar** con desarrolladores técnicos
5. **Tomar decisiones** informadas sobre el sistema

Este conocimiento conceptual es la base para eventualmente:
- Implementar el sistema (con apoyo técnico)
- Transicionar a live trading (con gestión de riesgo)
- Escalar a portfolios más grandes
- Desarrollar sistemas más sofisticados (ML, multi-estrategia)

---

**Versión**: 1.0  
**Fecha**: Octubre 21, 2025  
**Autor**: Pablo Felipe  
**Proyecto**: algo-options  
**Contexto**: Comunidad Skool.com - Trading Algorítmico Cuantitativo
