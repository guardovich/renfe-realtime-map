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

# Instala las dependencias
pip install -r requirements.txt
```

### Ejecución

```bash
python app.py
```

Luego abre en tu navegador: **http://127.0.0.1:5050**

## 📊 Datos

Consume la API de GTFS Realtime de RENFE:
- **Posiciones de vehículos**: `https://gtfsrt.renfe.com/vehicle_positions.json`

Los datos se actualizan automáticamente cada 30 segundos.

## 📝 Uso

1. **Filtrar por línea**: Usa el dropdown para ver solo una línea (C5, R1, etc.)
2. **Buscar**: Escribe parte del label o tripId
3. **Actualizar manualmente**: Click en "Actualizar ahora"
4. **Ver detalles**: Haz click en cualquier marcador del mapa

## 🛠️ Tecnología

| Componente | Tecnología |
|-----------|-----------|
| **Backend** | Flask (Python) |
| **Frontend** | Leaflet.js + MarkerCluster |
| **Mapas** | OpenStreetMap |
| **Datos** | RENFE GTFS Realtime API |

## 📁 Estructura del proyecto

```
renfe-realtime-map/
├── app.py                 # Servidor Flask + HTML/JS
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
└── LICENSE               # MIT License
```

## 🔧 Endpoints de la API

### `GET /api/vehicles`
Retorna lista de vehículos en tiempo real con posiciones.

```json
{
  "fetched_at": 1705687123.456,
  "vehicles": [
    {
      "entity_id": "ABC123",
      "label": "C5-23727-PLATF.(5)",
      "tripId": "23727",
      "stopId": "28065_0",
      "status": "IN_TRANSIT",
      "lat": 40.4168,
      "lon": -3.7038,
      "line": "C5"
    }
  ]
}
```

### `GET /api/alerts`
Retorna alertas y perturbaciones del servicio.

## 💡 Ejemplos de uso

**Ver solo la línea C5:**
1. Abre la app en http://127.0.0.1:5050
2. Selecciona "C5" en el dropdown
3. Solo verás trenes de la línea C5

**Buscar un tren específico:**
1. Escribe el tripId o label en la barra de búsqueda
2. Los marcadores se filtran automáticamente

## 📄 Licencia

MIT – Úsalo, modifícalo y distribúyelo libremente. Ver archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

David Guardo