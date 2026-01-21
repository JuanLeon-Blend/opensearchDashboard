# 🧪 OpenSearch Local con Docker Compose
## Ingesta de datos y creación de dashboards con búsqueda facetada (guía completa)

> **Objetivo:** Implementar un entorno local de OpenSearch usando Docker Compose, cargar datasets (sample + propio), crear visualizaciones y dashboards interactivos con búsqueda facetada.

---

## 📋 Requisitos técnicos

- **Ubuntu 20.04+** (o cualquier distribución Linux)
- **Docker** y **Docker Compose**
- **Python 3.9+**
- **Navegador web**

**Puertos libres:**
- `9200` → OpenSearch API
- `9600` → Performance Analyzer
- `5601` → OpenSearch Dashboards

---

## 🐧 Instalación de Docker en Ubuntu

### 1. Actualizar sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalar Docker

```bash
# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Agregar clave GPG de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalación
docker --version
```

### 3. Configurar permisos de usuario

```bash
# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Aplicar cambios (cerrar sesión y volver a entrar, o ejecutar)
newgrp docker

# Verificar que funciona sin sudo
docker ps
```

### 4. Configurar vm.max_map_count (REQUERIDO para OpenSearch)

```bash
# Temporal (se pierde al reiniciar)
sudo sysctl -w vm.max_map_count=262144

# Permanente
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 🐳 Creación del Docker Compose

### Arquitectura del docker-compose.yml

El archivo `docker-compose.yml` define dos servicios principales:

#### 1. **Servicio OpenSearch** (Motor de búsqueda)
- **Imagen:** `opensearchproject/opensearch:latest`
- **Puerto 9200:** API REST para consultas y gestión
- **Puerto 9600:** Performance Analyzer
- **Volumen persistente:** Guarda datos, índices y dashboards
- **Variables de entorno:** Configuración del cluster y seguridad

#### 2. **Servicio Dashboards** (Interfaz web)
- **Imagen:** `opensearchproject/opensearch-dashboards:latest`
- **Puerto 5601:** Interfaz web de visualización
- **Conexión:** Se comunica con OpenSearch vía red interna
- **Autenticación:** Usa credenciales desde variables de entorno

### Archivo docker-compose.yml explicado

```yaml
services:
  opensearch:
    image: opensearchproject/opensearch:latest
    container_name: opensearch
    environment:
      # Nombre del cluster
      - cluster.name=opensearch-local
      # Nombre del nodo
      - node.name=opensearch
      # Modo single-node (sin réplicas)
      - discovery.type=single-node
      # Bloqueo de memoria para mejor rendimiento
      - bootstrap.memory_lock=true
      # Contraseña admin desde .env (SEGURIDAD)
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_ADMIN_PASSWORD}
      # Memoria JVM (ajustar según tu RAM)
      - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
    ulimits:
      # Permitir bloqueo de memoria
      memlock:
        soft: -1
        hard: -1
    volumes:
      # PERSISTENCIA: Guarda datos, índices, dashboards
      - opensearch-data:/usr/share/opensearch/data
    ports:
      - "9200:9200"  # API REST
      - "9600:9600"  # Performance Analyzer
    networks:
      - os-net

  dashboards:
    image: opensearchproject/opensearch-dashboards:latest
    container_name: opensearch-dashboards
    depends_on:
      - opensearch
    environment:
      # URL interna de OpenSearch
      - OPENSEARCH_HOSTS=https://opensearch:9200
      # Credenciales desde .env
      - OPENSEARCH_USERNAME=${OPENSEARCH_USERNAME}
      - OPENSEARCH_PASSWORD=${OPENSEARCH_ADMIN_PASSWORD}
      # Desactivar verificación SSL (desarrollo local)
      - OPENSEARCH_SSL_VERIFICATIONMODE=none
    ports:
      - "5601:5601"
    networks:
      - os-net

# Volumen nombrado para persistencia
volumes:
  opensearch-data:

# Red interna para comunicación entre servicios
networks:
  os-net:
```

### ¿Por qué usar volúmenes?

Sin volúmenes, al ejecutar `docker compose down`, pierdes:
- ❌ Todos los dashboards creados
- ❌ Visualizaciones configuradas
- ❌ Datos cargados (índices)
- ❌ Configuraciones de seguridad

Con volúmenes (`opensearch-data`):
- ✅ Los datos persisten entre reinicios
- ✅ Los dashboards se mantienen
- ✅ Solo se pierden con `docker compose down -v`

---

## 🚀 Configuración inicial

### 1. Clonar/crear proyecto

```bash
mkdir opensearch-local && cd opensearch-local
```

### 2. Crear archivo .env (SEGURIDAD)

```bash
# Copiar plantilla
cp .env.example .env

# Editar con tu contraseña
nano .env
```

**Archivo `.env`:**
```bash
# OpenSearch Configuration
# IMPORTANTE: Contraseña debe tener:
# - Mínimo 8 caracteres
# - Al menos 1 mayúscula
# - Al menos 1 minúscula
# - Al menos 1 número
# - Al menos 1 carácter especial
OPENSEARCH_ADMIN_PASSWORD=Admin123!
OPENSEARCH_USERNAME=admin
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
```

### 3. Crear archivo .gitignore

```bash
cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.pyc
.venv/

# IDE
.vscode/
.idea/
EOF
```

### 4. Instalar dependencias Python

```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🐳 Levantar servicios

```bash
# Iniciar en segundo plano
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Ver solo logs de OpenSearch
docker compose logs -f opensearch

# Ver estado de contenedores
docker ps
```

### Verificar que funciona

```bash
# Verificar OpenSearch
curl -k -u admin:Admin123! https://localhost:9200

# Respuesta esperada:
# {
#   "name" : "opensearch",
#   "cluster_name" : "opensearch-local",
#   "version" : { ... }
# }
```

---

## 🌐 Acceso a OpenSearch Dashboards

- **URL:** http://localhost:5601
- **Usuario:** `admin`
- **Contraseña:** (la configurada en `.env`)

---

## 📊 Dataset 1: Sample Flight Data (Oficial)

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

## 📈 Dataset 2: Events Dataset (Propio)

### Cargar CSV con Python

```bash
# Activar entorno virtual
source .venv/bin/activate

# Cargar dataset (credenciales desde .env)
python upload_csv.py \
  --file events_dataset.csv \
  --index events \
  --time-field @timestamp \
  --recreate
```

### Crear Index Pattern

1. **Menú → Management**
2. **Dashboards Management**
3. **Index Patterns**
4. **Create index pattern:**
   - Name: `events*`
   - Time field: `@timestamp`

---


## 📁 Estructura del proyecto

```
opensearch-local/
├── .env                    # Credenciales (NO subir)
├── .env.example           # Plantilla de configuración
├── .gitignore            # Archivos excluidos de Git
├── docker-compose.yml    # Configuración de servicios
├── requirements.txt      # Dependencias Python
├── upload_csv.py        # Script de carga de datos
├── events_dataset.csv   # Dataset de ejemplo
└── README.md           # Esta documentación
```

---

## ✅ Resultado final

- ✅ OpenSearch corriendo en local con Docker
- ✅ Configuración segura con variables de entorno
- ✅ Datos persistentes con volúmenes Docker
- ✅ Dataset oficial (Flight Data) cargado
- ✅ Dataset propio (Events) cargado desde CSV
- ✅ 6+ visualizaciones creadas
- ✅ 2 dashboards funcionales
- ✅ Búsqueda facetada operativa
- ✅ Filtros dinámicos e interactivos

---

## 🆘 Troubleshooting

### Problemas comunes:

**Error: vm.max_map_count too low**
```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

**Puerto ocupado:**
```bash
# Verificar qué usa el puerto
sudo lsof -i :9200
sudo lsof -i :5601

# Matar proceso si es necesario
sudo kill -9 <PID>
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
curl -k -u admin:Admin123! https://localhost:9200
```

**Contenedor no inicia:**
```bash
# Ver logs detallados
docker compose logs opensearch

# Verificar permisos
ls -la

# Recrear contenedores
docker compose down -v
docker compose up -d
```

**Error de permisos en volumen:**
```bash
# Verificar propietario del volumen
docker volume inspect opensearch-local_opensearch-data

# Si es necesario, eliminar y recrear
docker compose down -v
docker compose up -d
```

