# OpenSearch Local con Docker Compose
## Ingesta de datos y creación de dashboards con búsqueda facetada (guía completa)

> **Objetivo:** Implementar un entorno local de OpenSearch usando Docker Compose, cargar datasets (sample + propio), crear visualizaciones y dashboards interactivos con búsqueda facetada.

---

## 📋 Requisitos técnicos

- **Docker** y **Docker Compose**
- **Python 3.9+**
- **Navegador web**

**Puertos libres:**
- `9200` → OpenSearch API
- `9600` → Performance Analyzer
- `5601` → OpenSearch Dashboards

---

## Configuración inicial

### 1. Clonar/crear proyecto

```bash
mkdir opensearch-local && cd opensearch-local
```

### 2. Configurar variables de entorno

```bash
# Editar credenciales
nano .env
```

**Archivo `.env`:**
```bash
# OpenSearch Configuration
OPENSEARCH_ADMIN_PASSWORD=tu_password_seguro
OPENSEARCH_USERNAME=admin
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
```

### 3. Instalar dependencias Python

```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🐳 Docker Compose

### Levantar servicios

```bash
docker-compose up -d
```

### Verificar estado

```bash
# Ver contenedores
docker ps

# Verificar OpenSearch
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} https://localhost:9200
```

---

## Acceso a OpenSearch Dashboards

- **URL:** http://localhost:5601
- **Usuario:** admin
- **Contraseña:** (la configurada en `.env`)

---

## Dataset 1: Sample Flight Data (Oficial)

### Cargar datos de ejemplo

1. Ir a **Home** en Dashboards
2. Seleccionar **Add sample data**
3. Elegir **Sample flight data**
4. Confirmar instalación

**Esto crea automáticamente:**
- Índice: `opensearch_dashboards_sample_data_flights`
- Visualizaciones predefinidas
- Dashboard: `[Flights] Global Flight Dashboard`

### Explorar datos

1. **Menú → Discover**
2. Index pattern: `opensearch_dashboards_sample_data_flights`
3. Cambiar rango: **Last 7 days**
4. Probar consulta DQL:

```text
FlightDelay:true AND FlightDelayMin >= 60
```

---

## Dataset 2: Events Dataset (Propio)

### Cargar CSV con Python

```bash
# Cargar dataset propio
python upload_csv.py \
  --file events_dataset.csv \
  --index events \
  --time-field @timestamp \
  --recreate
```

**Nota:** Las credenciales se cargan automáticamente desde `.env`

### Crear Index Pattern

1. **Menú → Management**
2. **Dashboards Management**
3. **Index Patterns**
4. **Create index pattern:**
   - Name: `events*`
   - Time field: `@timestamp`

---

##  Visualizaciones (Dataset Events)

### 1. Conteo por tipo de evento
- **Tipo:** Vertical Bar
- **Y-axis:** Count
- **X-axis:** `event_type.keyword`

### 2. Eventos en el tiempo
- **Tipo:** Line
- **X-axis:** Date Histogram (`@timestamp`)
- **Y-axis:** Count

### 3. Eventos por ubicación
- **Tipo:** Vertical Bar
- **X-axis:** `location.keyword`

### 4. Métrica total
- **Tipo:** Metric
- **Métrica:** Count

### 5. Distribución por severidad
- **Tipo:** Pie Chart
- **Slice by:** `severity.keyword`

### 6. Eventos por dispositivo
- **Tipo:** Horizontal Bar
- **Y-axis:** `device.keyword`
- **X-axis:** Count

---

## Dashboards

### Dashboard 1: Events Analytics

1. **Menú → Dashboards**
2. **Create new dashboard**
3. Añadir las 6 visualizaciones creadas
4. **Guardar como:** `Events Analytics - Faceted Search`

### Dashboard 2: Flight Data (Preexistente)

1. **Menú → Dashboards**
2. Abrir: `[Flights] Global Flight Dashboard`
3. Probar filtros interactivos:
   - Carrier
   - FlightDelay
   - Destination country

---

## Búsqueda Facetada (Faceted Search)

### Filtros disponibles en Events Dashboard:

- **Tipo de evento:** `event_type.keyword`
- **Ubicación:** `location.keyword`
- **Severidad:** `severity.keyword`
- **Plan:** `plan.keyword`
- **Dispositivo:** `device.keyword`
- **Sistema operativo:** `os.keyword`
- **Rango de fechas:** `@timestamp`

### Cómo usar:

1. Hacer clic en cualquier valor de las visualizaciones
2. Los filtros se aplican automáticamente a todo el dashboard
3. Usar el panel de filtros para refinar búsquedas
4. Combinar múltiples filtros para análisis específicos

---

## Comandos útiles

### Gestión de contenedores

```bash
# Parar servicios
docker-compose down

# Ver logs
docker-compose logs -f opensearch
docker-compose logs -f dashboards

# Reiniciar servicios
docker-compose restart
```

### Gestión de datos

```bash
# Recargar dataset
python upload_csv.py --file events_dataset.csv --index events --recreate

# Ver índices
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} "https://localhost:9200/_cat/indices?v"

# Eliminar índice
curl -k -u admin:${OPENSEARCH_ADMIN_PASSWORD} -X DELETE "https://localhost:9200/events"
```

---

## Seguridad

### Archivos importantes:

- **`.env`** - Credenciales (NO subir a GitHub)
- **`.gitignore`** - Excluye archivos sensibles

### Buenas prácticas:

1. **Nunca** subir `.env` a repositorios públicos
2. Usar contraseñas seguras en producción
3. Cambiar credenciales por defecto
4. Revisar `.gitignore` antes de commits

---

## Estructura del proyecto

```
opensearch-local/
├── .env                    # Credenciales (NO subir)
├── .gitignore            # Archivos excluidos de Git
├── docker-compose.yml    # Configuración de servicios
├── opensearch_dashboards.yml  # Config de Dashboards
├── requirements.txt      # Dependencias Python
├── upload_csv.py        # Script de carga de datos
├── events_dataset.csv   # Dataset de ejemplo
└── README.md           # Esta documentación
```

---


## Troubleshooting

### Problemas comunes:

**Puerto ocupado:**
```bash
# Verificar qué usa el puerto
sudo lsof -i :9200
sudo lsof -i :5601
```

**Memoria insuficiente:**
```bash
# Ajustar en docker-compose.yml
OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
```

**Credenciales incorrectas:**
```bash
# Verificar .env
cat .env

# Probar conexión
curl -k -u admin:tu_password https://localhost:9200
```
