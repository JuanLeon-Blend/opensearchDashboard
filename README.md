# OpenSearch Local

## Configuración

1. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```

2. Edita `.env` con tus credenciales reales

3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta OpenSearch:
   ```bash
   docker-compose up -d
   ```

5. Sube datos CSV:
   ```bash
   python upload_csv.py --file events_dataset.csv --index events --time-field @timestamp --recreate
   ```

## Importante
- Nunca subas el archivo `.env` a GitHub
- Usa `.env.example` como plantilla para otros desarrolladores# opensearchDashboard
