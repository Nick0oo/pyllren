# Redis Cache Integration - Documentación

## Resumen

Se ha integrado Redis como sistema de caché para mejorar el rendimiento de las consultas GET más frecuentes del sistema de inventario farmacéutico. La implementación incluye invalidación automática (Write-Through pattern) y fallback gracioso cuando Redis no está disponible.

## Configuración

### Variables de Entorno

El sistema detecta automáticamente el entorno y configura Redis apropiadamente:

- **Local (WSL)**: `REDIS_HOST=localhost` (por defecto)
- **Docker**: `REDIS_HOST=redis` (automático)
- **Puerto**: `REDIS_PORT=6379` (por defecto)
- **Base de datos**: `REDIS_DB=0` (por defecto)
- **Contraseña**: `REDIS_PASSWORD` (opcional)

### Docker Compose

Redis se ejecuta como servicio independiente con:
- Healthcheck automático
- Persistencia de datos (`redis-data` volume)
- Configuración de contraseña opcional
- Dependencias configuradas para backend

## Endpoints con Caché

### TTL Configurado
- **Listas y registros individuales**: 5 minutos (300 segundos)
- **Estadísticas**: 1 minuto (60 segundos)

### Entidades Cacheadas

#### Proveedores (`/api/v1/proveedores/`)
- `GET /` - Lista con búsqueda y filtros
- `GET /stats` - Estadísticas (TTL: 1 min)
- `GET /{id}` - Registro individual
- **Invalidación**: POST, PUT, DELETE → `proveedores:*`

#### Productos (`/api/v1/productos/`)
- `GET /` - Lista paginada
- `GET /{id}` - Registro individual
- **Invalidación**: POST, PUT, DELETE → `productos:*`

#### Sucursales (`/api/v1/sucursales/`)
- `GET /` - Lista completa
- `GET /{id}` - Registro individual
- **Invalidación**: POST, PUT, DELETE → `sucursales:*`

#### Bodegas (`/api/v1/bodegas/`)
- `GET /` - Lista completa
- `GET /{id}` - Registro individual
- **Invalidación**: POST, PUT, DELETE → `bodegas:*`

#### Lotes (`/api/v1/lotes/`)
- `GET /` - Lista paginada
- `GET /{id}` - Registro individual
- **Invalidación**: POST, PUT → `lotes:*` + `proveedores:*` (afecta stats)

#### Roles (`/api/v1/roles/`)
- `GET /` - Lista completa
- `GET /{id}` - Registro individual
- **Invalidación**: POST, PUT → `roles:*`

#### Usuarios (`/api/v1/users/`)
- `GET /` - Lista paginada
- `GET /{user_id}` - Registro individual
- `GET /me` - Usuario actual
- **Invalidación**: POST, PATCH, DELETE → `users:*`

## Estructura de Claves

### Formato Consistente
```
{entidad}:list:{hash_params}     # Listas con parámetros
{entidad}:{id}                    # Registros individuales
{entidad}:stats                   # Estadísticas
```

### Ejemplos
```
proveedores:list:a1b2c3d4         # Lista con filtros específicos
proveedores:123                   # Proveedor ID 123
proveedores:stats                 # Estadísticas de proveedores
users:list:e5f6g7h8              # Lista de usuarios paginada
users:me                         # Usuario actual
```

## Funcionalidades del Módulo Cache

### Funciones Principales

#### `get_cache(key: str) -> Optional[Any]`
- Obtiene valor del caché
- Retorna `None` si no existe o Redis no está disponible
- Logs automáticos de HIT/MISS

#### `set_cache(key: str, value: Any, ttl: int = 300) -> bool`
- Almacena valor en caché con TTL
- Serialización JSON automática
- Retorna `True` si exitoso

#### `delete_cache(key: str) -> bool`
- Elimina clave específica
- Retorna `True` si exitoso

#### `invalidate_pattern(pattern: str) -> int`
- Invalida todas las claves que coincidan con el patrón
- Retorna número de claves eliminadas
- Ejemplo: `invalidate_pattern("proveedores:*")`

### Funciones Helper

#### `list_cache_key(prefix: str, **params) -> str`
- Genera clave para listas con parámetros
- Hash automático de parámetros para consistencia

#### `item_cache_key(prefix: str, item_id: Any) -> str`
- Genera clave para registros individuales

#### `stats_cache_key(prefix: str) -> str`
- Genera clave para estadísticas

### Invalidación por Entidad

#### `invalidate_entity_cache(entity_name: str) -> int`
- Invalida todo el caché de una entidad
- Ejemplo: `invalidate_entity_cache("proveedores")`

## Manejo de Errores

### Fallback Gracioso
- Si Redis no está disponible, los endpoints funcionan normalmente
- No se generan errores por fallos de caché
- Logs de advertencia para debugging

### Logging
- Cache HIT/MISS automático
- Errores de conexión Redis
- Operaciones de invalidación

## Monitoreo y Debugging

### Logs Disponibles
```
Cache HIT for key: proveedores:list:a1b2c3d4
Cache MISS for key: proveedores:123
Cache SET for key: productos:456 (TTL: 300s)
Cache INVALIDATE pattern: proveedores:* (5 keys)
```

### Verificación de Estado
- Redis se inicializa en startup de la aplicación
- Healthcheck automático en Docker
- Conexión se cierra apropiadamente en shutdown

## Uso en Desarrollo Local (WSL)

### Configuración Automática
1. Redis debe estar ejecutándose en WSL (`redis-server`)
2. Backend detecta automáticamente `localhost:6379`
3. No se requiere configuración adicional

### Testing
```bash
# Verificar Redis en WSL
redis-cli ping

# Verificar logs del backend
docker-compose logs backend | grep -i redis
```

## Consideraciones de Rendimiento

### Beneficios
- **Reducción de carga en BD**: Consultas frecuentes servidas desde memoria
- **Respuesta más rápida**: Latencia reducida para datos cacheados
- **Escalabilidad**: Menos conexiones a PostgreSQL

### Optimizaciones Implementadas
- **Connection Pooling**: Pool de conexiones Redis reutilizable
- **Serialización eficiente**: JSON con `hiredis` parser C
- **TTL inteligente**: Diferentes tiempos según tipo de dato
- **Invalidación selectiva**: Solo se invalida lo necesario

## Troubleshooting

### Problemas Comunes

#### Redis no conecta
```
Failed to connect to Redis: [Errno 111] Connection refused
```
**Solución**: Verificar que Redis esté ejecutándose en WSL o Docker

#### Cache no funciona
- Verificar logs de aplicación
- Confirmar que Redis esté disponible
- Revisar configuración de variables de entorno

#### Datos inconsistentes
- Verificar que la invalidación se ejecute correctamente
- Revisar logs de invalidación
- Considerar reducir TTL si es necesario

### Comandos Útiles

```bash
# Verificar estado Redis
redis-cli info

# Limpiar caché completo
redis-cli flushall

# Ver claves existentes
redis-cli keys "*"

# Ver TTL de una clave
redis-cli ttl "proveedores:stats"
```

## Próximos Pasos

### Mejoras Futuras
1. **Métricas**: Integrar métricas de cache hit ratio
2. **Compresión**: Comprimir datos grandes antes de almacenar
3. **Clustering**: Soporte para Redis Cluster en producción
4. **Cache Warming**: Precargar datos críticos al startup

### Monitoreo Avanzado
- Dashboard de métricas de caché
- Alertas por cache miss ratio alto
- Análisis de patrones de uso
