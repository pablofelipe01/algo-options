#!/bin/bash

echo ""
echo "════════════════════════════════════════════════════════════"
echo "    ACTUALIZACIÓN SEMANAL DE DATOS DE OPCIONES"
echo "════════════════════════════════════════════════════════════"
echo ""

# Ir al directorio del proyecto
cd ~/Desktop/otions-data

# Activar entorno virtual
source venv/bin/activate

# Mostrar fecha
echo "📅 Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Ejecutar actualización
echo "🔄 Extrayendo datos de hoy..."
echo ""
python scripts/daily_update.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "📊 VERIFICACIÓN DE DATOS"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    python scripts/verify_all.py
    echo ""
    echo "✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE"
else
    echo ""
    echo "❌ Error durante la actualización"
    echo "📄 Revisa el log en: logs/daily_update_$(date +%Y%m%d).log"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""