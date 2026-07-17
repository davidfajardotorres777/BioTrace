# BioTrace V2 Enterprise
### Sistema de Trazabilidad Genómica con Arquitectura Multi-tenant y Object Storage

Proyecto Integrador — Bases de Datos II · 2026

---

## Ecosistema de Bases de Datos
Siguiendo los mejores estándares, BioTrace no se limita a una sola tecnología. Integra un ecosistema:
1. **MongoDB**: Para datos estructurados y operacionales (Pacientes, Muestras, Análisis, Alertas).
2. **MinIO (S3 Compatible)**: Como Object Storage para almacenar de forma eficiente los enormes archivos de secuenciación genómica (`.fastq`, `.bam`) generados por los análisis.

## Características Avanzadas
- **Multi-tenancy (Aislamiento por Clínica)**: El `BioTraceDAO` requiere inyectar un `clinica_id` en su inicialización. Todas las consultas y escrituras se filtran automáticamente en MongoDB para garantizar que una Clínica no pueda ver los datos de otra.
- **Alertas Basadas en Reglas**: El DAO implementa reglas de negocio. Por ejemplo, si se registra una muestra con una temperatura de almacenamiento superior a 4°C, se dispara un evento automático hacia la colección de `Alertas`.
- **Integración S3**: El `StorageDAO` maneja la conexión con MinIO para asegurar la trazabilidad del archivo físico atado al metadato de MongoDB.

---

## Arquitectura

```
Notebook/App → BioTraceDAO (MongoDB)
             → StorageDAO (MinIO)
```

**Colecciones Operacionales:** `pacientes`, `muestras`, `analisis`, `alertas` (Aisladas por `clinica_id`).
**Colecciones Globales:** `clinicas`.

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
El seed ahora genera múltiples clínicas, puebla MinIO con archivos simulados y genera alertas de temperatura controladas.

### 5. Jupyter Notebook
```bash
jupyter notebook demo.ipynb
```
El notebook te guiará por todas estas características avanzadas en acción.
