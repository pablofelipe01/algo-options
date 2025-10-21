# 🔧 Utilities / Utilidades

Este directorio contiene scripts de utilidad para tareas específicas del proyecto.

## Scripts Disponibles

### `test_price_lookup.py`
**Propósito**: Búsqueda y verificación de precios de opciones específicas

**Características**:
- Lookup de precios por ticker y fecha
- Búsqueda de opciones OTM específicas
- Validación de datos de Polygon.io
- Verificación de contratos específicos

**Uso**:
```bash
python scripts/utils/test_price_lookup.py
```

**Casos de Uso**:
- Verificar precio de un contrato específico
- Debugging de datos de mercado
- Validación de resultados de backtest
- Investigación de anomalías en precios

---

## Propósito del Directorio

Este directorio contiene herramientas de soporte que **no son parte del flujo principal** de:
- Data pipeline (`scripts/data_pipeline/`)
- Backtesting (`scripts/backtest/`)
- Estrategias (`scripts/strategies/`)

Son scripts auxiliares para tareas puntuales de debugging, validación y análisis ad-hoc.

## Desarrollo Futuro

Scripts candidatos para este directorio:
- Validadores de datos
- Herramientas de debugging
- Scripts de limpieza
- Utilidades de formato/conversión
