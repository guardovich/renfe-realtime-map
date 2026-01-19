# 🚂 RENFE Cercanías – Mapa en Tiempo Real

Visualiza todos los trenes de RENFE Cercanías en España en tiempo real sobre un mapa interactivo.

## ✨ Características

- 🗺️ Mapa interactivo con Leaflet
- 🔄 Actualización automática cada 30 segundos
- 🔍 Búsqueda y filtro por línea
- 📍 Información detallada de cada tren (tripId, stopId, coordenadas)
- 🎯 Clustering automático de marcadores

## 🚀 Cómo ejecutar

### Requisitos
- Python 3.8+
- pip

### Instalación

```bash
# Clona el repositorio
git clone https://github.com/TU_USUARIO/renfe-realtime-map.git
cd renfe-realtime-map

# Crea un entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate  # En Mac/Linux
# o: venv\Scripts\activate  # En Windows

# Instala las dependencias
pip install -r requirements.txt
