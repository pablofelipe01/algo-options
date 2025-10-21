"""
Generador de Workbook PDF - Guía de Trading Algorítmico
Crea un PDF profesional con estilos financieros
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# Colores corporativos financieros
NAVY_BLUE = colors.HexColor('#1E3A5F')
LIGHT_BLUE = colors.HexColor('#4A90E2')
ACCENT_BLUE = colors.HexColor('#2ECC71')
DARK_GRAY = colors.HexColor('#2C3E50')
LIGHT_GRAY = colors.HexColor('#ECF0F1')
GOLD = colors.HexColor('#F39C12')

class WorkbookGenerator:
    def __init__(self, output_filename="Workbook_Trading_Algoritmico.pdf", logo_path=None):
        self.output_filename = output_filename
        self.logo_path = logo_path
        self.doc = SimpleDocTemplate(
            output_filename,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        self.story = []
        self.styles = self._create_styles()
        
    def _create_styles(self):
        """Crea estilos personalizados profesionales"""
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=NAVY_BLUE,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=LIGHT_BLUE,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Encabezado de sección
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=NAVY_BLUE,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=LIGHT_BLUE,
            borderPadding=5,
            backColor=LIGHT_GRAY
        ))
        
        # Encabezado de subsección
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=DARK_GRAY,
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=DARK_GRAY,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Código
        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            backColor=LIGHT_GRAY,
            borderWidth=1,
            borderColor=LIGHT_BLUE,
            borderPadding=12,
            fontName='Courier',
            leftIndent=10,
            rightIndent=10,
            spaceAfter=10,
            spaceBefore=5
        ))
        
        # Checkbox item
        styles.add(ParagraphStyle(
            name='CheckboxItem',
            parent=styles['Normal'],
            fontSize=11,
            textColor=DARK_GRAY,
            spaceAfter=8,
            leftIndent=30,
            fontName='Helvetica'
        ))
        
        # Nota/Tip
        styles.add(ParagraphStyle(
            name='CustomTip',
            parent=styles['Normal'],
            fontSize=10,
            textColor=DARK_GRAY,
            backColor=colors.HexColor('#FFF9E6'),
            borderWidth=1,
            borderColor=GOLD,
            borderPadding=10,
            spaceAfter=15
        ))
        
        return styles
    
    def add_cover_page(self):
        """Crea la portada del workbook"""
        # Logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=2*inch, height=2*inch)
                logo.hAlign = 'CENTER'
                self.story.append(logo)
                self.story.append(Spacer(1, 0.5*inch))
            except Exception as e:
                print(f"No se pudo cargar el logo: {e}")
        
        # Título
        title = Paragraph("WORKBOOK DE TRADING ALGORÍTMICO", self.styles['CustomTitle'])
        self.story.append(title)
        self.story.append(Spacer(1, 0.3*inch))
        
        # Subtítulo
        subtitle = Paragraph("Guía de Configuración desde Cero", self.styles['CustomSubtitle'])
        self.story.append(subtitle)
        self.story.append(Spacer(1, 0.5*inch))
        
        # Línea decorativa
        line_data = [['', '', '']]
        line_table = Table(line_data, colWidths=[2*inch, 2*inch, 2*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 3, LIGHT_BLUE),
        ]))
        self.story.append(line_table)
        self.story.append(Spacer(1, 0.5*inch))
        
        # Información del workbook
        info_data = [
            ['Proyecto:', 'algo-options'],
            ['Fecha:', datetime.now().strftime('%d de %B, %Y')],
            ['Versión:', '1.0'],
            ['Nivel:', 'Principiante a Intermedio'],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), NAVY_BLUE),
            ('TEXTCOLOR', (1, 0), (1, -1), DARK_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        self.story.append(info_table)
        self.story.append(Spacer(1, 1*inch))
        
        # Mensaje motivacional
        motivation = Paragraph(
            "<i>Este workbook te guiará paso a paso desde tener una computadora limpia "
            "hasta estar completamente listo para trading algorítmico. "
            "¡No necesitas conocimientos previos de programación!</i>",
            self.styles['CustomBody']
        )
        self.story.append(motivation)
        
        self.story.append(PageBreak())
    
    def add_table_of_contents(self):
        """Agrega tabla de contenidos"""
        self.story.append(Paragraph("📋 Tabla de Contenidos", self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.3*inch))
        
        toc_data = [
            ['Sección', 'Página'],
            ['1. Instalar Visual Studio Code', '3'],
            ['2. Verificar Python', '5'],
            ['3. Crear tu Proyecto', '8'],
            ['4. Configurar Entorno Virtual', '10'],
            ['5. Crear Estructura de Carpetas', '13'],
            ['6. Instalar Dependencias', '15'],
            ['7. Verificar Instalación', '18'],
            ['8. Próximos Pasos', '20'],
            ['Recursos Adicionales', '22'],
            ['Solución de Problemas', '25'],
        ]
        
        toc_table = Table(toc_data, colWidths=[5*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        self.story.append(toc_table)
        self.story.append(PageBreak())
    
    def add_section(self, number, title, icon="🚀"):
        """Agrega un encabezado de sección principal"""
        section_text = f"{icon} Sección {number}: {title}"
        self.story.append(Paragraph(section_text, self.styles['SectionHeader']))
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_subsection(self, title):
        """Agrega un encabezado de subsección"""
        self.story.append(Paragraph(title, self.styles['SubsectionHeader']))
    
    def add_body(self, text):
        """Agrega texto de cuerpo"""
        self.story.append(Paragraph(text, self.styles['CustomBody']))
        self.story.append(Spacer(1, 0.1*inch))
    
    def add_checkbox_item(self, text):
        """Agrega un item con checkbox"""
        checkbox_text = f"☐ {text}"
        self.story.append(Paragraph(checkbox_text, self.styles['CheckboxItem']))
    
    def add_code_block(self, code):
        """Agrega un bloque de código"""
        # Reemplazar saltos de línea por <br/> para HTML en Paragraph
        code_formatted = code.replace('\n', '<br/>')
        code_para = Paragraph(f"<font name='Courier' size='9'>{code_formatted}</font>", self.styles['CodeBlock'])
        self.story.append(code_para)
        self.story.append(Spacer(1, 0.15*inch))
    
    def add_tip(self, text):
        """Agrega un tip o nota importante"""
        tip_text = f"💡 <b>TIP:</b> {text}"
        self.story.append(Paragraph(tip_text, self.styles['CustomTip']))
    
    def add_notes_section(self):
        """Agrega una sección para notas personales (solo 3 líneas compactas)"""
        self.story.append(Spacer(1, 0.15*inch))
        self.story.append(Paragraph("📝 Notas:", self.styles['SubsectionHeader']))
        
        # Solo 3 líneas compactas para notas
        for _ in range(3):
            self.story.append(Spacer(1, 0.1*inch))
            line_data = [['_' * 85]]
            line_table = Table(line_data, colWidths=[6.5*inch])
            line_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0, 0), (-1, -1), LIGHT_GRAY),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            self.story.append(line_table)
    
    def build_workbook(self):
        """Construye el workbook completo"""
        # Portada
        self.add_cover_page()
        
        # Tabla de contenidos
        self.add_table_of_contents()
        
        # Sección 1: Visual Studio Code
        self.add_section(1, "Instalar Visual Studio Code", "💻")
        self.add_body(
            "Visual Studio Code (VS Code) es un editor de código gratuito creado por Microsoft. "
            "Es donde escribirás y ejecutarás tus programas de trading. Piénsalo como Microsoft Word, "
            "pero diseñado específicamente para escribir código."
        )
        
        self.add_subsection("Pasos para Mac")
        self.add_checkbox_item("Ir a https://code.visualstudio.com/")
        self.add_checkbox_item("Hacer clic en 'Download for Mac'")
        self.add_checkbox_item("Abrir el archivo .zip descargado")
        self.add_checkbox_item("Arrastrar Visual Studio Code.app a Aplicaciones")
        self.add_checkbox_item("Abrir VS Code desde Aplicaciones")
        
        self.add_subsection("Pasos para Windows")
        self.add_checkbox_item("Ir a https://code.visualstudio.com/")
        self.add_checkbox_item("Hacer clic en 'Download for Windows'")
        self.add_checkbox_item("Ejecutar el instalador .exe")
        self.add_checkbox_item("Seguir instrucciones (dejar opciones predeterminadas)")
        self.add_checkbox_item("Abrir VS Code desde el Menú Inicio")
        
        
        self.add_tip(
            "Una vez instalado, VS Code debería mostrar una pantalla de bienvenida con opciones "
            "para abrir carpetas y crear nuevos archivos."
        )
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 2: Verificar Python
        self.add_section(2, "Verificar Python", "🐍")
        self.add_body(
            "Python es el lenguaje de programación que usaremos. Es como el idioma en el que "
            "le hablarás a la computadora para hacer trading algorítmico."
        )
        
        self.add_subsection("Verificar si Python está instalado")
        self.add_checkbox_item("Abrir VS Code")
        self.add_checkbox_item("Abrir Terminal: Menú Terminal → New Terminal")
        self.add_checkbox_item("Ejecutar el siguiente comando:")
        
        self.add_code_block("python3 --version")
        
        self.add_body(
            "<b>Resultado esperado:</b> Deberías ver algo como 'Python 3.9.7' o 'Python 3.10.5'"
        )
        
        self.add_subsection("Si Python no está instalado")
        self.add_body("Para Mac (usando Homebrew):")
        self.add_code_block(
            "/bin/bash -c \"$(curl -fsSL <br/>"
            "https://raw.githubusercontent.com/Homebrew/<br/>"
            "install/HEAD/install.sh)\"<br/>"
            "<br/>"
            "brew install python@3.11"
        )
        
        self.add_body("Para Windows:")
        self.add_checkbox_item("Ir a https://www.python.org/downloads/")
        self.add_checkbox_item("Descargar Python 3.11 para Windows")
        self.add_checkbox_item("IMPORTANTE: Marcar 'Add Python to PATH'")
        self.add_checkbox_item("Hacer clic en 'Install Now'")
        
        self.add_tip(
            "Si ves 'command not found: python', en Mac/Linux usa 'python3' en lugar de 'python'. "
            "En Windows, asegúrate de haber marcado 'Add Python to PATH' durante la instalación."
        )
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 3: Crear Proyecto
        self.add_section(3, "Crear tu Proyecto", "📁")
        self.add_body(
            "Ahora vamos a crear la carpeta principal donde vivirá todo tu proyecto de trading algorítmico."
        )
        
        self.add_subsection("Crear carpeta del proyecto")
        self.add_checkbox_item("Ir al Escritorio")
        self.add_checkbox_item("Crear nueva carpeta llamada 'algo-options'")
        self.add_checkbox_item("Abrir VS Code")
        self.add_checkbox_item("Arrastrar carpeta 'algo-options' a VS Code")
        
        self.add_body(
            "O también puedes usar: File → Open Folder... y seleccionar 'algo-options'"
        )
        
        self.add_tip(
            "En el lado izquierdo de VS Code deberías ver el nombre de tu proyecto: 📁 ALGO-OPTIONS"
        )
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 4: Entorno Virtual
        self.add_section(4, "Configurar el Entorno Virtual", "🔒")
        self.add_body(
            "Un entorno virtual es como una caja aislada donde instalamos todas las herramientas "
            "(librerías) que necesitamos para nuestro proyecto. Esto evita conflictos con otros proyectos."
        )
        
        self.add_subsection("Crear el entorno virtual")
        self.add_checkbox_item("Abrir Terminal en VS Code")
        self.add_checkbox_item("Verificar que estás en la carpeta 'algo-options'")
        self.add_checkbox_item("Ejecutar el comando de creación:")
        
        self.add_body("Para Mac/Linux:")
        self.add_code_block("python3 -m venv venv")
        
        self.add_body("Para Windows:")
        self.add_code_block("python -m venv venv")
        
        self.add_subsection("Activar el entorno virtual")
        self.add_body("Para Mac/Linux:")
        self.add_code_block("source venv/bin/activate")
        
        self.add_body("Para Windows (PowerShell):")
        self.add_code_block("venv\\Scripts\\Activate.ps1")
        
        self.add_body(
            "<b>Verificación:</b> Tu Terminal debería mostrar (venv) al inicio de la línea"
        )
        self.add_code_block("(venv) ~/Desktop/algo-options %")
        
        self.add_tip(
            "Cada vez que cierres VS Code, tendrás que activar nuevamente el entorno virtual. "
            "Es como encender una máquina antes de trabajar con ella."
        )
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 5: Estructura de Carpetas
        self.add_section(5, "Crear la Estructura de Carpetas", "🗂️")
        self.add_body(
            "Organizar el código en carpetas es como organizar documentos en un archivador. "
            "Cada cosa tiene su lugar y es más fácil encontrar lo que necesitas."
        )
        
        self.add_subsection("Estructura del proyecto")
        self.add_code_block(
            "algo-options/<br/>"
            "├── venv/                    (entorno virtual)<br/>"
            "├── data/<br/>"
            "│   ├── historical/          (datos crudos)<br/>"
            "│   └── analysis/            (resultados)<br/>"
            "├── scripts/<br/>"
            "│   ├── data_pipeline/       (obtener datos)<br/>"
            "│   ├── strategies/          (estrategias)<br/>"
            "│   ├── quantitative/        (análisis)<br/>"
            "│   ├── backtest/            (backtesting)<br/>"
            "│   └── dashboard/           (dashboard)<br/>"
            "├── logs/                    (registros)<br/>"
            "└── documents/               (documentación)"
        )
        
        self.add_subsection("Crear toda la estructura")
        self.add_checkbox_item("Copiar y pegar el comando en la Terminal")
        
        self.add_body("Para Mac/Linux:")
        self.add_code_block(
            "mkdir -p data/historical data/analysis<br/>"
            "scripts/data_pipeline scripts/strategies<br/>"
            "scripts/quantitative scripts/backtest<br/>"
            "scripts/dashboard/components scripts/utils<br/>"
            "logs documents"
        )
        
        self.add_checkbox_item("Verificar que las carpetas se crearon en el explorador de VS Code")
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 6: Instalar Dependencias
        self.add_section(6, "Instalar Dependencias", "📦")
        self.add_body(
            "Las dependencias son librerías (paquetes de código) creadas por otros programadores "
            "que nos facilitan la vida. Es como tener herramientas profesionales en vez de "
            "fabricar cada herramienta desde cero."
        )
        
        self.add_subsection("Paso 1: Actualizar pip")
        self.add_checkbox_item("Ejecutar el comando de actualización:")
        self.add_code_block("pip install --upgrade pip")
        
        self.add_subsection("Paso 2: Instalar paquetes básicos")
        self.add_checkbox_item("Copiar y ejecutar (puede tardar 2-5 minutos):")
        self.add_code_block(
            "pip install pandas numpy scipy matplotlib<br/>"
            "seaborn yfinance requests python-dotenv"
        )
        
        self.add_body("Explicación de cada paquete:")
        table_data = [
            ['Paquete', 'Propósito'],
            ['pandas', 'Manejo de datos (como Excel en código)'],
            ['numpy', 'Cálculos matemáticos y arrays'],
            ['scipy', 'Funciones científicas (estadística)'],
            ['matplotlib', 'Gráficos básicos'],
            ['seaborn', 'Gráficos profesionales'],
            ['yfinance', 'Obtener datos de Yahoo Finance'],
            ['streamlit', 'Crear dashboards interactivos'],
        ]
        
        dep_table = Table(table_data, colWidths=[1.5*inch, 4.5*inch])
        dep_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        self.story.append(dep_table)
        self.story.append(Spacer(1, 0.2*inch))
        
        self.add_subsection("Paso 3: Instalar paquetes para dashboard")
        self.add_checkbox_item("Ejecutar:")
        self.add_code_block("pip install streamlit plotly")
        
        self.add_subsection("Paso 4: Guardar las dependencias")
        self.add_checkbox_item("Ejecutar para crear archivo requirements.txt:")
        self.add_code_block("pip freeze > requirements.txt")
        
        self.add_tip(
            "El archivo requirements.txt es como una lista de compras. Si otra persona "
            "o tú mismo necesitan reinstalar el proyecto, solo ejecutan: "
            "pip install -r requirements.txt"
        )
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 7: Verificar Instalación
        self.add_section(7, "Verificar Instalación", "✅")
        self.add_body(
            "Vamos a crear un programa simple para verificar que todo funciona correctamente."
        )
        
        self.add_subsection("Crear archivo de prueba")
        self.add_checkbox_item("En VS Code: File → New File")
        self.add_checkbox_item("Copiar y pegar este código:")
        
        self.add_code_block(
            "# test_installation.py<br/>"
            "import pandas as pd<br/>"
            "import numpy as np<br/>"
            "import matplotlib.pyplot as plt<br/>"
            "<br/>"
            "print('✅ Python funciona correctamente!')<br/>"
            "print(f'✅ Pandas: {pd.__version__}')<br/>"
            "print(f'✅ NumPy: {np.__version__}')<br/>"
            "<br/>"
            "data = {<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;'ticker': ['SPY', 'QQQ', 'IWM'],<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;'precio': [450, 380, 195]<br/>"
            "}<br/>"
            "df = pd.DataFrame(data)<br/>"
            "print(df)<br/>"
            "print('🎉 ¡Todo instalado!')"
        )
        
        self.add_checkbox_item("Guardar como: test_installation.py")
        self.add_checkbox_item("En la Terminal, ejecutar:")
        self.add_code_block("python test_installation.py")
        
        self.add_body(
            "<b>Resultado esperado:</b> Deberías ver las versiones de los paquetes y una tabla con datos de prueba."
        )
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Sección 8: Próximos Pasos
        self.add_section(8, "Próximos Pasos", "🚀")
        self.add_body(
            "¡Felicidades! Has completado la configuración básica. Ahora estás listo para empezar "
            "con trading algorítmico."
        )
        
        self.add_subsection("Checklist de completitud")
        self.add_checkbox_item("VS Code instalado y funcionando")
        self.add_checkbox_item("Python 3.9+ instalado")
        self.add_checkbox_item("Proyecto 'algo-options' creado")
        self.add_checkbox_item("Entorno virtual 'venv' creado y activado")
        self.add_checkbox_item("Estructura de carpetas completa")
        self.add_checkbox_item("Dependencias instaladas")
        self.add_checkbox_item("Test de instalación ejecutado exitosamente")
        
        self.add_subsection("Opciones para continuar")
        self.add_body(
            "<b>Opción 1: Empezar con Datos</b>"
        )
        self.add_body("Ir a: documents/DATA_PIPELINE.md - Aprender a obtener datos históricos de opciones")
        
        self.add_body(
            "<b>Opción 2: Empezar con Estrategias</b>"
        )
        self.add_body("Ir a: documents/strategies_README.md - Aprender sobre Covered Calls e Iron Condors")
        
        self.add_body(
            "<b>Opción 3: Ver el Dashboard</b>"
        )
        self.add_body("Ejecutar: streamlit run scripts/dashboard/app.py")
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Recursos Adicionales
        self.add_section(9, "Recursos Adicionales", "📚")
        
        self.add_subsection("Atajos de teclado útiles en VS Code")
        shortcuts_data = [
            ['Acción', 'Mac', 'Windows'],
            ['Paleta de comandos', 'Cmd + Shift + P', 'Ctrl + Shift + P'],
            ['Abrir/cerrar Terminal', 'Cmd + ñ', 'Ctrl + ñ'],
            ['Guardar archivo', 'Cmd + S', 'Ctrl + S'],
            ['Deshacer', 'Cmd + Z', 'Ctrl + Z'],
            ['Buscar en archivos', 'Cmd + Shift + F', 'Ctrl + Shift + F'],
        ]
        
        shortcuts_table = Table(shortcuts_data, colWidths=[2.5*inch, 1.75*inch, 1.75*inch])
        shortcuts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        self.story.append(shortcuts_table)
        self.story.append(Spacer(1, 0.2*inch))
        
        self.add_subsection("Comandos de Terminal importantes")
        terminal_data = [
            ['Comando', 'Función'],
            ['cd nombre_carpeta', 'Entrar a una carpeta'],
            ['cd ..', 'Subir un nivel'],
            ['pwd', 'Ver ruta actual'],
            ['ls (Mac) / dir (Win)', 'Listar archivos'],
            ['clear', 'Limpiar terminal'],
            ['Ctrl + C', 'Detener programa'],
        ]
        
        terminal_table = Table(terminal_data, colWidths=[2*inch, 4*inch])
        terminal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        self.story.append(terminal_table)
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Solución de Problemas
        self.add_section(10, "Solución de Problemas Comunes", "🔧")
        
        problems = [
            ("'python: command not found'", 
             "Mac/Linux: Usa 'python3' en lugar de 'python'. "
             "Windows: Reinstala Python y marca 'Add to PATH'"),
            
            ("'Permission denied' al crear entorno virtual",
             "Mac/Linux: Ejecutar en Terminal: sudo chown -R $USER:$USER ~/Desktop/algo-options"),
            
            ("PowerShell no ejecuta scripts",
             "Windows: Ejecutar: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"),
            
            ("Entorno virtual no se activa",
             "1. Elimina carpeta venv. "
             "2. Vuelve a crear: python -m venv venv. "
             "3. Activa de nuevo"),
            
            ("'Module not found' al ejecutar",
             "1. Verifica (venv) esté activo. "
             "2. Si no: activa el entorno. "
             "3. Reinstala: pip install nombre_paquete"),
        ]
        
        for problem, solution in problems:
            self.add_subsection(f"Problema: {problem}")
            self.add_body(f"<b>Solución:</b> {solution}")
            self.story.append(Spacer(1, 0.15*inch))
        
        self.add_notes_section()
        self.story.append(PageBreak())
        
        # Página final
        self.story.append(Spacer(1, 2*inch))
        congrats = Paragraph(
            "🎉 ¡FELICIDADES!",
            self.styles['CustomTitle']
        )
        self.story.append(congrats)
        self.story.append(Spacer(1, 0.5*inch))
        
        final_message = Paragraph(
            "Has completado exitosamente la configuración de tu entorno de trading algorítmico. "
            "Estás listo para comenzar a desarrollar estrategias, analizar datos históricos "
            "y crear sistemas de trading automatizados.",
            self.styles['CustomBody']
        )
        self.story.append(final_message)
        self.story.append(Spacer(1, 0.2*inch))
        
        final_message2 = Paragraph(
            "Recuerda: El trading algorítmico es un viaje de aprendizaje continuo. "
            "No te desanimes si encuentras obstáculos, son parte del proceso.",
            self.styles['CustomBody']
        )
        self.story.append(final_message2)
        self.story.append(Spacer(1, 0.2*inch))
        
        final_message3 = Paragraph(
            "<b>¡Mucho éxito en tu camino como trader algorítmico!</b>",
            self.styles['CustomBody']
        )
        self.story.append(final_message3)
        
        # Construir el PDF
        print("Generando workbook PDF...")
        self.doc.build(self.story)
        print(f"✅ Workbook generado exitosamente: {self.output_filename}")


if __name__ == "__main__":
    # Configuración
    LOGO_PATH = "/Users/pablofelipe/Desktop/otions-data/public/logo2.png"
    OUTPUT_FILE = "Workbook_Trading_Algoritmico.pdf"
    
    # Crear generador
    generator = WorkbookGenerator(
        output_filename=OUTPUT_FILE,
        logo_path=LOGO_PATH
    )
    
    # Generar workbook
    generator.build_workbook()
    
    print("\n" + "="*50)
    print("🎉 WORKBOOK COMPLETADO")
    print("="*50)
    print(f"📄 Archivo: {OUTPUT_FILE}")
    print(f"📍 Ubicación: {os.path.abspath(OUTPUT_FILE)}")
    print("\nAbre el PDF y comienza tu viaje en trading algorítmico! 🚀")