# 📈 Proyecto Final: ETL y Análisis de Acciones del NYSE

---

## 🚀 Descripción General

Este proyecto implementa un pipeline ETL (Extracción, Transformación y Carga) completo para construir una base de datos actualizada diariamente con información sobre las 500 empresas de mayor capitalización bursátil del NYSE (S&P 500).

Permite analizar precios históricos, fundamentos financieros y calcular indicadores técnicos clave para estrategias de trading y análisis de inversión.

---

## 🎯 Objetivos

### Objetivos Mínimos:
- Extracción de datos históricos y fundamentales usando Yahoo Finance (`yfinance`).
- Transformación, limpieza y cálculo de indicadores técnicos.
- Almacenamiento en base de datos relacional PostgreSQL.
- Análisis Exploratorio de Datos (EDA).
- Desarrollo de dashboards de visualización en Power BI.

### Objetivos Plus:
- Automatización diaria de la actualización de datos.
- Creación de la tabla `resumen_inversion` (señales combinadas de compra/venta).
- Democratizar el acceso a datos financieros de calidad para pequeños inversores.

---

## 🧩 Estructura del Pipeline

| Fase | Scripts | Descripción |
|:----|:--------|:------------|
| **Extracción** | `ext.py`, `ext_diario.py` | Descarga inicial y actualización diaria de datos desde Yahoo Finance y Wikipedia. |
| **Transformación** | `transform.py` | Limpieza de datasets y cálculo de indicadores técnicos: SMA, EMA, RSI, MACD, ATR, OBV, Volatilidad, Bollinger Bands. |
| **Carga** | `load.py` | Inserción incremental en PostgreSQL, controlando duplicados y actualizaciones. |
| **Orquestación** | `main.py` | Automatización completa del proceso ETL. |

---

## 🗃️ Datasets Finales

- **empresas_ready.csv**: Información básica (Ticker, Nombre, Sector, Industria).
- **precios_historicos_ready.csv**: Precios diarios (Open, High, Low, Close, Volume).
- **indicadores_fundamentales_ready.csv**: PER, ROE, Deuda/Patrimonio, Margen Neto, etc.
- **indicadores_tecnicos_ready.csv**: SMA, EMA, RSI, MACD, ATR, OBV, Volatilidad, Bollinger Bands.

---

## 🛠️ Tecnologías Utilizadas

| Herramienta | Propósito |
|:------------|:----------|
| **Python 3.12** | Desarrollo del pipeline ETL. |
| **PostgreSQL** | Base de datos relacional. |
| **DBeaver** | Administración de la base de datos. |
| **Power BI (futuro)** | Visualización de dashboards. |
| **GitHub** | Control de versiones. |
| **Principales librerías Python**: | `pandas`, `numpy`, `yfinance`, `psycopg2`, `tqdm`, `python-dotenv`. |

---

## 🌎 Fuente de Datos

- **Yahoo Finance** (`yfinance`):  
  - Precios de apertura, cierre, máximo, mínimo y volumen.
  - Datos fundamentales básicos (PER, EPS, Market Cap, etc.).
  - Datos ajustados por dividendos y splits.

- **Wikipedia**:  
  - Lista actualizada del S&P 500 (símbolos, nombres, sector, industria).

---

## 🏗️ Estado del Proyecto

✅ Extracción masiva inicial completada.  
✅ Actualización diaria implementada.  
✅ Base de datos PostgreSQL funcional.  
✅ Indicadores técnicos y fundamentales calculados.  
🚀 Próximo paso: desarrollo de Análisis Exploratorio de Datos

---

## 📈 Próximos Desarrollos

- Realización de un Análisis Exploratorio de Datos (EDA) sobre la base de datos creada.
- Generación automática de señales de trading basadas en análisis técnico y fundamental.
- Implementación de modelos predictivos sobre precios históricos.
- Construcción de dashboards interactivos en Power BI para análisis visual.



---

## 🤝 Colaboración

Cualquier sugerencia o colaboración para expandir este proyecto es bienvenida. ¡A construir herramientas financieras accesibles para todos! 🚀
