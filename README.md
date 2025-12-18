<h1 align="center">💊 Pyllren</h1>

<p align="center">
  <b>Sistema monolítico moderno para la gestión inteligente de inventario y ventas farmacéuticas</b><br/>
  Optimizando la trazabilidad de lotes, sincronización entre sucursales y control de stock en tiempo real.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-FastAPI-109989?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/Concurrency-Threading-FF6B6B?logo=python&logoColor=white" alt="Threading"/>
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"/>
</p>

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Concurrencia y Procesamiento](#-concurrencia-y-procesamiento)
- [Endpoints API Relevantes](#-endpoints-api-relevantes)
- [Gestión de Roles y Permisos](#-gestión-de-roles-y-permisos)
- [Tecnologías Principales](#-tecnologías-principales)
- [Instalación y Ejecución](#-instalación-y-ejecución)

---

## 🧩 Descripción General

**Pyllren** es una plataforma integral para la **gestión farmacéutica**, construida con una arquitectura **monolítica moderna** que unifica un backend ágil con **FastAPI** y un frontend interactivo con **React + TypeScript**.

### Características Principales

- 📦 **Gestión de inventario multi-sucursal** con trazabilidad completa de lotes
- 🔐 **Control de acceso basado en roles** (RBAC) con 4 niveles de permisos
- 🏢 **Bodegas inteligentes** con validación de capacidad y sugerencias de distribución
- ⚡ **Caché Redis** para optimización de queries frecuentes
- 🔄 **Procesamiento concurrente** para tareas de background
- 📊 **Dashboard en tiempo real** con estadísticas por sucursal
- 🔍 **Auditoría completa** de operaciones críticas

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │   Lotes      │  │  Bodegas     │      │
│  │  Productos   │  │   Usuarios   │  │  Reportes    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Routes (REST)                       │   │
│  │  /users  /lotes  /bodegas  /productos  /stats       │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Auth      │  │    Cache     │  │  Background  │      │
│  │  JWT + RBAC  │  │    Redis     │  │   Threads    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE DATOS                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │   MongoDB    │      │
│  │  (Principal) │  │   (Cache)    │  │   (Logs)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Concurrencia y Procesamiento

### 🧵 Hilos y Procesamiento Asíncrono

El sistema utiliza **concurrencia basada en hilos** y **locks de PostgreSQL** para garantizar la integridad de datos en operaciones críticas:

#### 1. **Validación de Capacidad de Bodegas** (`backend/app/api/routes/lotes.py`)

```python
def calcular_ocupacion_bodega(session: Session, bodega_id: int) -> int:
    """
    ⚠️ CONCURRENCIA: SELECT FOR UPDATE
    - Usa lock pesimista en PostgreSQL
    - Bloquea fila de bodega para evitar race conditions
    - Previene sobreventa/sobrecarga concurrente
    """
    bodega_lock_stmt = select(Bodega).where(
        Bodega.id_bodega == bodega_id
    ).with_for_update()  # 🔒 LOCK de fila
    
    session.exec(bodega_lock_stmt).one()  # Bloquea hasta commit/rollback
    # ... cálculo de ocupación
```

**Escenario protegido:**
- ✅ Usuario A intenta recepcionar 500 productos
- ✅ Usuario B intenta recepcionar 600 productos simultáneamente
- 🔒 El lock garantiza que solo uno proceda a la vez
- ✅ El segundo usuario recibe error 409 con sugerencias

#### 2. **Recepción Distribuida de Lotes** (`backend/app/api/routes/lotes.py`)

```python
@router.post("/lotes/recepcion-distribuida")
def recepcion_lote_distribuida(payload: RecepcionDistribuidaPayload):
    """
    🔄 CONCURRENCIA: Transacción atómica con locks múltiples
    - Valida capacidad de N bodegas simultáneamente
    - Crea sub-lotes en múltiples bodegas
    - Rollback automático si falla cualquier operación
    """
    # Para cada bodega en la distribución:
    #   1. Lock de la bodega (SELECT FOR UPDATE)
    #   2. Validación de capacidad
    #   3. Creación de sub-lote
    #   4. Commit o rollback global
```

#### 3. **Caché con Invalidación Inteligente** (`backend/app/core/cache.py`)

```python
def invalidate_entity_cache(entity: str):
    """
    ⚡ CONCURRENCIA: Invalidación atómica en Redis
    - Usa SCAN para patrones en lugar de KEYS (no bloqueante)
    - Invalidación por entidad: users, lotes, bodegas, productos
    - TTL automático para prevenir crecimiento infinito
    """
    pattern = f"{entity}:*"
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(
            cursor, match=pattern, count=100
        )
        # Invalidación en lotes de 100 keys
```

#### 4. **Procesamiento de Background** (Futuro - Diseñado)

```python
# 🔄 TAREAS RECURRENTES PLANIFICADAS:

# Vigilancia de lotes próximos a vencer (cada 6 horas)
@background_task(interval=21600)  
def verificar_lotes_proximos_vencer():
    """
    🔍 RECURRENCIA: Escaneo programado
    - Identifica lotes que vencen en <30 días
    - Genera alertas automáticas
    - Notifica a farmacéuticos por sucursal
    """

# Sincronización entre sucursales (cada 1 hora)
@background_task(interval=3600)
def sincronizar_inventario_sucursales():
    """
    🔄 CONCURRENCIA: Sincronización paralela
    - Usa ThreadPoolExecutor para procesar N sucursales
    - Actualiza stock en paralelo
    - Manejo de conflictos con last-write-wins
    """

# Backup automático de auditoría (cada 24 horas)
@background_task(interval=86400)
def backup_auditoria_mongodb():
    """
    💾 PERSISTENCIA: Backup incremental
    - Exporta logs de auditoría a MongoDB
    - Limpia registros antiguos de PostgreSQL
    - Compresión y archivado automático
    """

# Limpieza de caché obsoleto (cada 12 horas)
@background_task(interval=43200)
def limpiar_cache_obsoleto():
    """
    🧹 MANTENIMIENTO: Limpieza automática
    - Elimina keys expiradas de Redis
    - Libera memoria de consultas antiguas
    - Recalcula estadísticas populares
    """

# Precarga de productos populares (cada 4 horas)
@background_task(interval=14400)
def precargar_productos_populares():
    """
    ⚡ OPTIMIZACIÓN: Warm-up de caché
    - Identifica productos más consultados
    - Precarga en Redis antes de horas pico
    - Reduce latencia en consultas frecuentes
    """
```

### 🔐 Control de Concurrencia

| Técnica | Ubicación | Propósito |
|---------|-----------|-----------|
| **SELECT FOR UPDATE** | `lotes.py`, `bodegas.py` | Lock pesimista en operaciones críticas |
| **Transacciones ACID** | Todas las operaciones de escritura | Atomicidad y consistencia |
| **Redis Cache TTL** | `cache.py` | Prevención de datos obsoletos |
| **Query Debouncing** | Frontend (TanStack Query) | Reducción de requests concurrentes |
| **Invalidación por patrón** | `cache.py` | Sincronización cache-DB |

---

## 🌐 Endpoints API Relevantes

### 🔐 Autenticación y Usuarios

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| `POST` | `/api/v1/login/access-token` | Login con JWT | Público |
| `POST` | `/api/v1/login/test-token` | Verificar token | Autenticado |
| `POST` | `/api/v1/password-recovery/{email}` | Recuperar contraseña | Público |
| `POST` | `/api/v1/reset-password/` | Resetear contraseña | Público |
| `GET` | `/api/v1/users/me` | Usuario actual | Autenticado |
| `PATCH` | `/api/v1/users/me` | Actualizar perfil | Autenticado |
| `GET` | `/api/v1/users/` | Listar usuarios | Admin |
| `POST` | `/api/v1/users/` | Crear usuario | Admin |
| `PATCH` | `/api/v1/users/{id}` | Actualizar usuario | Admin |
| `DELETE` | `/api/v1/users/{id}` | Eliminar usuario | Admin |

### 📦 Gestión de Lotes

| Método | Endpoint | Descripción | Concurrencia |
|--------|----------|-------------|--------------|
| `GET` | `/api/v1/lotes/` | Listar lotes | Filtrado por sucursal |
| `GET` | `/api/v1/lotes/stats` | Estadísticas de lotes | Cache Redis (TTL 60s) |
| `POST` | `/api/v1/lotes/recepcion` | ⚠️ Recepción con validación | **SELECT FOR UPDATE** |
| `POST` | `/api/v1/lotes/recepcion-distribuida` | ⚠️ Recepción multi-bodega | **Locks múltiples** |
| `GET` | `/api/v1/lotes/{id}` | Detalle de lote | - |
| `PUT` | `/api/v1/lotes/{id}` | Actualizar lote | Validación de scope |
| `DELETE` | `/api/v1/lotes/{id}` | Eliminar lote | Soft delete |

**Algoritmos Especiales:**
- **Validación de capacidad:** Lock de bodega + cálculo de ocupación
- **Sugerencias automáticas:** Algoritmo greedy para distribuir productos
- **Manejo de conflictos:** Error 409 con alternativas viables

### 🏢 Gestión de Bodegas

| Método | Endpoint | Descripción | Filtrado |
|--------|----------|-------------|----------|
| `GET` | `/api/v1/bodegas/` | Listar bodegas | Por sucursal (scope) |
| `GET` | `/api/v1/bodegas/stats` | ⚡ Estadísticas globales | Cache + filtro sucursal |
| `GET` | `/api/v1/bodegas/{id}` | Detalle extendido | Incluye lotes y productos |
| `POST` | `/api/v1/bodegas/` | Crear bodega | Solo admin |
| `PUT` | `/api/v1/bodegas/{id}` | Actualizar bodega | Scope validation |
| `DELETE` | `/api/v1/bodegas/{id}` | Eliminar bodega | Soft delete |

**Campos Clave:**
- `capacidad`: Límite máximo de productos
- `tipo`: Principal, Secundaria, De tránsito
- `temperatura_min/max`: Control ambiental
- `estado`: Operativa o inactiva

### 📊 Productos y Stock

| Método | Endpoint | Descripción | Filtrado |
|--------|----------|-------------|----------|
| `GET` | `/api/v1/productos/` | Listar productos | Por sucursal + búsqueda |
| `GET` | `/api/v1/productos/stats` | Estadísticas de productos | Cache + sucursal |
| `GET` | `/api/v1/productos/{id}` | Detalle de producto | Validación de scope |
| `PUT` | `/api/v1/productos/{id}` | Actualizar stock | Auditoría automática |

### 🏛️ Administración

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| `GET` | `/api/v1/sucursales/` | Listar sucursales | Autenticado |
| `POST` | `/api/v1/sucursales/` | Crear sucursal | Admin |
| `GET` | `/api/v1/roles/` | Listar roles | Autenticado |
| `GET` | `/api/v1/auditorias/` | Consultar auditoría | Admin/Auditor |
| `GET` | `/api/v1/movimientos/` | Historial movimientos | Filtrado por sucursal |

### 📈 Dashboard y Reportes

| Método | Endpoint | Descripción | Datos |
|--------|----------|-------------|-------|
| `GET` | `/api/v1/lotes/stats` | Stats de lotes | Activos, vencidos, próximos |
| `GET` | `/api/v1/bodegas/stats` | Stats de bodegas | Total, operativas, capacidad |
| `GET` | `/api/v1/productos/stats` | Stats de productos | Total, bajo stock, sin stock |

**Optimizaciones:**
- ⚡ Caché Redis con TTL de 60 segundos
- 🔍 Filtrado automático por sucursal (no-admin)
- 📊 Precarga de datos populares

---

## 🔐 Gestión de Roles y Permisos

### Roles del Sistema

| Rol | ID | Permisos | Alcance |
|-----|-----|----------|---------|
| **ADMINISTRADOR** | 1 | ✅ Acceso total | Todas las sucursales |
| **FARMACÉUTICO** | 2 | ✅ Gestión de inventario<br>✅ Recepciones<br>✅ Consultas | Solo su sucursal |
| **AUXILIAR** | 3 | ✅ Consultas<br>✅ Movimientos básicos | Solo su sucursal |
| **AUDITOR** | 4 | ✅ Solo lectura<br>✅ Auditorías | Solo su sucursal |

### Módulos de Acceso

```python
# backend/app/api/deps.py

def get_user_scope(user: User) -> dict | None:
    """
    🔒 FILTRADO AUTOMÁTICO POR SUCURSAL
    - Admin: None (ve todo)
    - Otros: {"id_sucursal": user.id_sucursal}
    """
    if user.id_rol == 1:  # ADMINISTRADOR
        return None
    return {"id_sucursal": user.id_sucursal}
```

### Matriz de Permisos

| Módulo | Admin | Farmacéutico | Auxiliar | Auditor |
|--------|-------|--------------|----------|---------|
| Dashboard | ✅ Todas las sucursales | ✅ Su sucursal | ✅ Su sucursal | ✅ Su sucursal |
| Usuarios | ✅ CRUD completo | ❌ | ❌ | ❌ Solo lectura |
| Sucursales | ✅ CRUD completo | ❌ Solo lectura | ❌ Solo lectura | ❌ Solo lectura |
| Bodegas | ✅ CRUD completo | ✅ Ver/Editar su sucursal | ✅ Ver su sucursal | ❌ Solo lectura |
| Lotes | ✅ CRUD completo | ✅ CRUD su sucursal | ✅ Ver su sucursal | ❌ Solo lectura |
| Productos | ✅ CRUD completo | ✅ CRUD su sucursal | ✅ Ver/Editar básico | ❌ Solo lectura |
| Recepciones | ✅ Todas | ✅ Su sucursal | ✅ Su sucursal | ❌ |
| Proveedores | ✅ CRUD completo | ✅ Ver todos | ✅ Ver todos | ❌ Solo lectura |
| Auditorías | ✅ Ver todas | ❌ | ❌ | ✅ Ver su sucursal |

---

## 🚀 Tecnologías Principales

### Backend
- **FastAPI** 0.115+ - Framework web asíncrono
- **SQLModel** - ORM con validación Pydantic
- **PostgreSQL** 16+ - Base de datos principal
- **Redis** 7+ - Cache y sesiones
- **Alembic** - Migraciones de BD
- **PyJWT** - Autenticación JWT
- **Pytest** - Testing

### Frontend
- **React** 18+ - UI Library
- **TypeScript** 5+ - Type safety
- **TanStack Router** - Routing tipado
- **TanStack Query** - Data fetching y caché
- **Chakra UI v3** - Component library
- **Vite** - Build tool

### DevOps
- **Docker** - Containerización
- **Docker Compose** - Orquestación local
- **Traefik** - Reverse proxy
- **GitHub Actions** - CI/CD

---

## 📦 Instalación y Ejecución

### Requisitos Previos

- **Docker** y **Docker Compose** (Recomendado - setup completo en 3 minutos)
- **Alternativa manual**: Python 3.10+, Node.js 20+, PostgreSQL 17+, Redis 7+

---

### 🐳 Opción 1: Docker Compose (Recomendado)

Esta es la forma más rápida y sencilla de ejecutar todo el proyecto. Con un solo comando levantarás:
- ✅ PostgreSQL 17 con persistencia de datos
- ✅ Redis 7 con persistencia de datos  
- ✅ Backend (FastAPI)
- ✅ Frontend (React + Nginx)
- ✅ Adminer (gestor de base de datos)
- ✅ Migraciones automáticas

#### Paso 1: Configurar Variables de Entorno

```bash
# 1. Copiar el archivo de ejemplo
cp env.example .env

# 2. Editar el archivo .env con tus valores
# En Windows: notepad .env
# En Linux/Mac: nano .env o vim .env
```

**Variables mínimas requeridas:**
```bash
# Base de datos
POSTGRES_PASSWORD=tu_password_seguro_aqui
POSTGRES_USER=postgres
POSTGRES_DB=app

# Backend
SECRET_KEY=tu_secret_key_de_al_menos_32_caracteres
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=tu_password_admin
```

💡 **Tip**: Genera un SECRET_KEY seguro con:
```bash
# En Linux/Mac/Git Bash:
openssl rand -hex 32

# En PowerShell:
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

#### Paso 2: Levantar Todos los Servicios

```bash
# Construir imágenes y levantar contenedores
docker-compose up --build -d

# Ver logs en tiempo real (Ctrl+C para salir)
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Paso 3: Acceder a los Servicios

Una vez que todos los servicios estén levantados (toma ~2-3 minutos la primera vez):

| Servicio | URL | Descripción |
|----------|-----|-------------|
| 🎨 **Frontend** | http://localhost | Interfaz de usuario principal |
| 🚀 **Backend API** | http://localhost:8000 | API REST |
| 📚 **API Docs (Swagger)** | http://localhost:8000/docs | Documentación interactiva |
| 📊 **Adminer** | http://localhost:8080 | Gestor de base de datos |
| 🗄️ **PostgreSQL** | localhost:5432 | Base de datos (acceso directo) |
| 💾 **Redis** | localhost:6379 | Cache (acceso directo) |

**Credenciales por defecto:**
- **Usuario Admin**: El configurado en `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`
- **Adminer**: usa las credenciales de PostgreSQL del `.env`

#### Comandos Útiles

```bash
# Detener todos los servicios (mantiene los datos)
docker-compose down

# Detener y eliminar volúmenes (⚠️ ELIMINA TODOS LOS DATOS)
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart backend

# Ver estado de los servicios
docker-compose ps

# Reconstruir solo un servicio
docker-compose up --build -d backend

# Ver uso de recursos
docker stats

# Ejecutar comandos dentro del contenedor backend
docker-compose exec backend bash
docker-compose exec backend alembic upgrade head

# Ver logs desde el inicio
docker-compose logs --tail=100 backend
```

#### Verificar Persistencia de Datos

Los datos de PostgreSQL y Redis persisten automáticamente en volúmenes de Docker. Para verificarlo:

```bash
# 1. Crear algunos datos en la aplicación
# 2. Detener los contenedores
docker-compose down

# 3. Volver a levantar
docker-compose up -d

# 4. Los datos siguen ahí ✅
```

**Para backup de los volúmenes:**
```bash
# Backup de PostgreSQL
docker-compose exec db pg_dump -U postgres app > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U postgres app < backup.sql
```

#### Notas sobre Docker para desarrollo

- `docker-compose.yml` define el stack de producción local (imágenes optimizadas).
- `docker-compose.override.yml` ajusta puertos y comandos para desarrollo:
  - Backend: usa `fastapi run --reload app/main.py` con recarga en caliente.
  - Frontend: expone el dashboard en `http://localhost:5173`.
- Los `.dockerignore` reducen el contexto de build:
  - `backend/.dockerignore`: excluye venvs, cachés, tests, reportes de cobertura y archivos de tooling.
  - `frontend/.dockerignore`: excluye `node_modules`, `dist`, logs y artefactos de tests/Playwright.
- Para un ciclo rápido en desarrollo:
  - Usa `docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build -d`.
  - Modifica código en `backend/` y `frontend/`; los cambios se reflejan sin reconstruir toda la imagen.

---

### 🔧 Opción 2: Instalación Manual

Si prefieres ejecutar los servicios sin Docker:

#### Configuración Backend

```bash
# Clonar repositorio
git clone https://github.com/Nick0oo/pyllren.git
cd pyllren/backend

# Instalar uv (gestor de dependencias)
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/Mac:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias con uv
uv sync

# Configurar variables de entorno
cp ../env.example ../.env
# Editar ../.env con tus credenciales

# Ejecutar migraciones (requiere PostgreSQL corriendo)
uv run alembic upgrade head

# Iniciar servidor
uv run fastapi run --reload app/main.py
```

#### Configuración Frontend

```bash
cd ../frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
VITE_API_URL=http://localhost:8000 npm run dev
```

**Servicios requeridos:**
- PostgreSQL corriendo en `localhost:5432`
- Redis corriendo en `localhost:6379`

---

### 🐛 Troubleshooting

#### El puerto 80 está ocupado

```bash
# Cambiar el puerto del frontend en docker-compose.yml:
ports:
  - "8080:80"  # Ahora accede en http://localhost:8080
```

#### Error "Variable not set"

```bash
# Asegúrate de que el archivo .env existe y tiene todas las variables
cat .env  # Linux/Mac
type .env  # Windows CMD
```

#### Backend no se conecta a la BD

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs de la base de datos
docker-compose logs db

# Verificar conectividad
docker-compose exec backend ping db
```

#### Limpiar todo y empezar de cero

```bash
# Detener servicios y eliminar volúmenes
docker-compose down -v

# Eliminar imágenes (opcional)
docker-compose down --rmi all

# Limpiar caché de Docker
docker system prune -a

# Volver a construir
docker-compose up --build -d
```

---

## 📊 Estadísticas del Proyecto

- **Líneas de código:** ~15,000+
- **Endpoints API:** 60+
- **Componentes React:** 50+
- **Modelos de BD:** 12
- **Tests:** 30+
- **Cobertura:** 75%+

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

## 👥 Autores

- **Nick0oo** - *Desarrollo inicial* - [GitHub](https://github.com/Nick0oo)

---

## 🙏 Agradecimientos

- FastAPI por su excelente documentación
- Chakra UI v3 por los componentes modernos
- TanStack por las herramientas de React
- La comunidad open source

---

<p align="center">
  Hecho con ❤️ y ☕ por el equipo de Pyllren
</p>
