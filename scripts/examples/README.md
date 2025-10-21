# 📚 Examples / Ejemplos

Este directorio contiene scripts de demostración y ejemplos educativos.

## Scripts Disponibles

### `demo_quantitative.py`
**Propósito**: Demostración completa del módulo cuantitativo (Black-Scholes-Merton)

**Características**:
- Cálculo de BSM con datos reales de mercado
- Cálculo de Greeks (Delta, Gamma, Theta, Vega, Rho)
- Análisis de probabilidad (ITM, OTM, Touch, Profit)
- Ejemplos con SPY y TSLA
- Visualización de resultados

**Uso**:
```bash
python scripts/examples/demo_quantitative.py
```

**Salida**: Muestra cálculos detallados con datos reales del mercado de opciones.

---

## Cuándo Usar Estos Scripts

- **Aprendizaje**: Para entender cómo funcionan los módulos cuantitativos
- **Validación**: Para verificar cálculos de BSM y Greeks
- **Desarrollo**: Como referencia al crear nuevas funcionalidades
- **Testing**: Para probar cambios en los módulos base

## Notas

Estos scripts son **educativos** y no están diseñados para producción. Para backtesting real, usar `scripts/backtest/`.
