# InmoCore V3 Enterprise
### Sistema SaaS PropTech con Arquitectura Multi-tenant, Object Storage, IA Semántica y Búsqueda Geoespacial

Proyecto Integrador — Bases de Datos II · 2026

---

## Ecosistema de Bases de Datos
Siguiendo los mejores estándares, InmoCore no se limita a una sola tecnología. Integra un ecosistema completo:
1. **MongoDB**: Para datos estructurados y operacionales con búsquedas Geoespaciales `2dsphere` (Agencias, Propiedades, Clientes, Contratos, Alertas).
2. **MinIO (S3 Compatible)**: Como Object Storage para almacenar de forma eficiente las fotos en alta resolución de las propiedades.
3. **ChromaDB**: Como base de datos Vectorial de Inteligencia Artificial para buscar descripciones de las propiedades por similitud semántica.

## Características Avanzadas
- **Multi-tenancy (Aislamiento por Agencia)**: El `InmoCoreDAO` requiere inyectar un `agencia_id` en su inicialización. Todas las consultas y escrituras se filtran automáticamente en MongoDB para garantizar que una Agencia no pueda ver los datos de otra.
- **Alertas Basadas en Reglas**: El DAO implementa reglas de negocio. Por ejemplo, si se registra una venta con un monto muy sospechoso (<$10k USD), se dispara un evento automático hacia la colección de `Alertas`.
- **Integración S3**: El `StorageDAO` maneja la conexión con MinIO para las fotos de las casas.
- **Búsqueda IA Vectorial**: `VectorDAO` utiliza ChromaDB para comprender los textos de las casas y que los clientes busquen con lenguaje natural.
- **Geo-Radar**: Consultas `$nearSphere` para rastrear propiedades a la redonda de la agencia.
- **Interfaz Gráfica Empresarial**: Aplicación de escritorio creada en `customtkinter`.

---

## Instalación y Ejecución

### Requisitos previos
- Python 3.12 o superior
- Docker Desktop
- Git

### 1. Entorno
```bash
python -m venv venv
# Activar según tu SO (venv\Scripts\activate o source venv/bin/activate)
pip install -r requirements.txt
```

### 2. Variables
Copia `.env.example` a `.env`.

### 3. Levantar Infraestructura
Esto levantará MongoDB y MinIO.
```bash
docker compose up -d
```
Puedes acceder a la consola de MinIO en http://localhost:9001 (user: admin, pass: password).

### 4. Setup y Seed
```bash
python setup_db.py
python seed.py
```
El seed genera múltiples agencias, puebla MinIO con fotos simuladas, indexa en ChromaDB y llena MongoDB.

### 5. Lanzar Interfaz de Usuario
```bash
python main_ui.py
```
La aplicación gráfica te guiará por todas estas características avanzadas en acción.
