# Seguridad — Autenticación, Autorización y Hardenings (pyllren)

Este documento consolida todo lo relacionado con seguridad en la aplicación: cómo se generan y validan tokens, control de roles/alcance por sucursal, CORS, hashing de contraseñas, manejo de errores 401/403, y cómo el frontend consume y aplica tokens.

Contenido rápido:
- Tipo de autenticación: OAuth2 (password) / JWT (Bearer)
- Hashing: `bcrypt` vía `passlib`
- Token signing: HS256 con `SECRET_KEY` configurable
- Verificación y dependencias FastAPI: `app.api.deps` (ej.: `CurrentUser`, `get_current_admin_user`, `ensure_bodega_in_scope`)
- CORS: configurable desde variables de entorno (`BACKEND_CORS_ORIGINS`, `FRONTEND_HOST`)

---

## 1) Backend — generación y verificación del token

- Creación del token:
  - Módulo: `backend/app/core/security.py`
  - Función: `create_access_token(subject, expires_delta)` que genera un JWT con payload `{ "exp": <expiry>, "sub": <subject> }` firmado con `settings.SECRET_KEY` y algoritmo `HS256`.
  - Expiración: `ACCESS_TOKEN_EXPIRE_MINUTES` (configurable en `backend/app/core/config.py`, por defecto 60*24*8 = 8 días).

- Verificación del token (dependencia):
  - Módulo: `backend/app/api/deps.py`
  - Se usa `OAuth2PasswordBearer` indicando `tokenUrl` en `settings.API_V1_STR + '/login/access-token'`.
  - `get_current_user(session, token)` decodifica con `jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])`, valida payload contra `TokenPayload` (modelo) y recupera `User` desde la DB.
  - Errores: si el token es inválido o el usuario no existe/está inactivo se levantan HTTP errors 403, 404 o 400 según el caso.

## 2) Password hashing

- Implementación: `passlib` con esquema `bcrypt` (archivo `backend/app/core/security.py`).
- Funciones: `get_password_hash(password)` y `verify_password(plain, hashed)`.

## 3) Roles y permisos (backend)

- Roles y superusuario:
  - `User.is_superuser` marca superusuarios.
  - `id_rol` identifica roles en la DB; por convención el rol `Administrador` se detecta como `id_rol == 1`.

- Dependencias útiles (en `app.api.deps`):
  - `get_current_active_superuser(current_user)`: valida `current_user.is_superuser`, levanta 403 si no.
  - `get_current_admin_user(current_user)`: permite superusuarios o usuarios con `id_rol == 1`.

- Helpers:
  - `is_admin_user(current_user)`: True si superuser o `id_rol == 1`.
  - `get_user_scope(current_user)`: devuelve `None` para admin (acceso total) o `{"id_sucursal": N}` para usuarios limitados a una sucursal. Muchos endpoints aplican este scope server-side.
  - `ensure_bodega_in_scope(session, bodega_id, current_user)`: valida que la bodega pertenezca a la sucursal del usuario (si no es admin) — lanza 404 si la bodega no existe o 403 si está fuera de alcance.

## 4) Manejo de errores y redirecciones (frontend/backend)

- Backend: usa HTTP status codes apropiados: 401/403 para autenticación/autorización, 404 para recursos no encontrados, 409 para conflictos (ej. capacidad insuficiente en recepción).
- Frontend: en `frontend/src/main.tsx` hay un manejador global que atrapa `ApiError` con status 401/403, borra `access_token` de `localStorage` y redirige a `/login`.

## 5) CORS y orígenes permitidos

- Configuración central: `backend/app/core/config.py`.
  - `BACKEND_CORS_ORIGINS` (read from env) y `FRONTEND_HOST`.
  - Propiedad derivada `all_cors_origins` que normaliza orígenes y añade `FRONTEND_HOST`.

- En `backend/app/main.py` si `settings.all_cors_origins` tiene valores se instala `CORSMiddleware` con:
  - `allow_origins = settings.all_cors_origins`
  - `allow_credentials = True`
  - `allow_methods = ['*']`
  - `allow_headers = ['*']`

Recomendación: en producción restringir `allow_origins` a orígenes concretos y revisar `allow_credentials` según si se usan cookies seguras.

## 6) Configuración sensible y protección de secretos

- `SECRET_KEY` está en `backend/app/core/config.py` y por defecto se genera, pero la validación `_enforce_non_default_secrets()` obliga a cambiar valores peligrosos (`changethis`) y a no dejar secrets por defecto en entornos no locales.
- Recomendación operativa: almacenar `SECRET_KEY`, credenciales DB, y credenciales Redis/SMTP en variables de entorno seguras / vault.

## 7) Frontend — almacenamiento y envío del token

- Almacenamiento: `frontend/src/hooks/useAuth.ts`
  - En login exitoso se guarda `localStorage.setItem('access_token', response.access_token)`.
  - Logout borra `access_token` y redirige.

- Envío automático: `frontend/src/client/core/OpenAPI.ts` define la configuración global y `OpenAPI.TOKEN` se establece en `frontend/src/main.tsx` a `async () => localStorage.getItem('access_token') || ''`.
  - `frontend/src/client/core/request.ts` en `getHeaders()` recupera `TOKEN` y, si existe, añade la cabecera `Authorization: Bearer <token>`.
  - Resultado: todas las llamadas generadas por el cliente OpenAPI incluyen el header Authorization si hay token en `localStorage`.

## 8) Protección de endpoints sensibles (ejemplos)

- Crear bodega: `POST /bodegas/` tiene `dependencies=[Depends(get_current_admin_user)]` — solo admins pueden crear bodegas.
- Endpoints que usan `CurrentUser` y `get_user_scope` filtran la data restornada por sucursal cuando el usuario no es admin.
- `ensure_bodega_in_scope` se usa en endpoints que manipulan o consultan bodegas/lotes para validar alcance.

## 9) Recomendaciones y mejoras sugeridas

- Implementar Refresh Tokens y/o revocación de tokens para permitir logout centralizado y rotación segura.
- Considerar tokens de corta duración + refresh token con almacenamiento seguro (HttpOnly cookie) para mitigar XSS.
- Añadir rate-limiting en el proxy (traefik/nginx) o middleware para evitar abusos y brute-force.
- Registrar métricas y alertas de seguridad (intentos 401/403, tasas de fallo en login, uso de tokens expirados).
- Revisar CORS en producción: usar lista blanca explícita y no `'*'` en `allow_headers` si no es necesario.
- Evaluar uso de autenticación basada en claves para integraciones machine-to-machine y scopes finos para APIs externas.

---

Archivos de referencia (implementación):
- `backend/app/core/security.py` — creación/verificación de JWT y hashing de contraseñas.
- `backend/app/api/deps.py` — dependencias para obtener `CurrentUser`, `get_current_admin_user`, `get_current_active_superuser`, `get_user_scope`, `ensure_bodega_in_scope`.
- `backend/app/core/config.py` — `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `BACKEND_CORS_ORIGINS`, `FRONTEND_HOST`.
- `backend/app/main.py` — instalación de `CORSMiddleware` con `settings.all_cors_origins`.
- `frontend/src/hooks/useAuth.ts` — login/logout y almacenamiento en `localStorage`.
- `frontend/src/main.tsx` — configuración `OpenAPI.TOKEN` y manejo global de errores 401/403.
- `frontend/src/client/core/request.ts` — añade `Authorization` header cuando `OpenAPI.TOKEN` retorna valor.

Si quieres, genero además:

- Un checklist operativo para desplegar con buenas prácticas (env vars, TLS, CORS, rate limit).
- Un ejemplo de flujo con `curl` y cómo probar expiración y revocación simulada.

Estado: creado `security.md`.

---

## 10) Manejo de sesiones y estrategias de autenticación

- Tokens vs sesiones:

  - La aplicación usa JWT de acceso (Bearer token) almacenado en `localStorage`. Esto simplifica el cliente SPA pero expone tokens a XSS si no hay mitigaciones estrictas.
  - Alternativa más segura para SPAs: usar `access_token` corto + `refresh_token` en `HttpOnly` cookie (solo el servidor puede leerla). Considera este enfoque para reducir riesgo de robo de tokens desde XSS.

- Sesiones persistentes y multi-dispositivo:

  - Si se requieren sesiones por dispositivo, mantener una tabla `user_sessions` en BD con `user_id`, `device_info`, `issued_at`, `expires_at`, `revoked`.
  - Al hacer logout o revocar sesión, marcar `revoked=true` y filtrar tokens en endpoints (por ejemplo, guardar `jti` en DB al emitir token y verificarlo en cada request o en un cache redis).

- Revocación:

  - Implementar lista de revocación (blacklist) en Redis para tokens revocados o usar short-lived tokens con refresh tokens que pueden revocarse.


## 11) HTTPS / TLS y cifrado en tránsito

- Requisito: todas las conexiones públicas deben usar HTTPS.

  - En producción el TLS debe terminar en el proxy inverso (Traefik / Nginx) o en el LB (ALB, Cloud Load Balancer).
  - En entornos locales puede usarse TLS de desarrollo, pero nunca habilitar comunicaciones no cifradas en producción.

- Certificados:

  - Usar certificados gestionados (Let's Encrypt, ACME) o certificados de CA internos rotados automáticamente.
  - Habilitar renovación automática y monitorizar expiración.

- Protocolos y cifrados recomendados:

  - TLS 1.2 mínimo, preferible TLS 1.3.
  - Preferir suites modernas (ECDHE + AES-GCM o ChaCha20-Poly1305).
  - Evitar RC4, DES, 3DES, and deprecated ciphers and key sizes < 2048 (for RSA).

- HSTS y cabeceras de seguridad:

  - Establecer `Strict-Transport-Security` (HSTS) con `includeSubDomains; preload` cuando sea apropiado.
  - Añadir cabeceras: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, y `Content-Security-Policy` para mitigar XSS.


## 12) Cifrado en reposo (at-rest)

- Base de datos:

  - Habilitar cifrado a nivel de disco (EBS encryption, Azure Disk Encryption) y/o cifrado a nivel de BD si el proveedor lo soporta (TDE en algunos RDBMS).
  - Para campos sensibles (PII, tokens de terceros) considerar cifrado campo-a-campo con claves gestionadas en KMS.

- Backups:

  - Asegurar que los backups están cifrados y accesibles solo por servicios/usuarios autorizados.
  - Mantener políticas de retención y pruebas de restauración periódicas.


## 13) Tipos de cifrado y claves

- Simétrico:

  - AES-256-GCM para cifrado de datos en reposo y para cifrado de secretos en aplicaciones.

- Asimétrico:

  - RSA/ECDSA para intercambio de claves y certificados TLS.

- Firma/HMAC:

  - JWTs actualmente usan `HS256` (HMAC + SHA256) — esto usa una clave simétrica (`SECRET_KEY`). Para mayor seguridad en entornos con múltiples servicios, considerar `RS256` (clave pública/privada) para permitir verificación sin compartir la clave privada.

- Gestión de claves:

  - Usar un KMS (AWS KMS, GCP KMS, Azure KeyVault, HashiCorp Vault) para generar, almacenar y rotar claves.
  - No almacenar claves en código ni en repositorios.


## 14) Auditorías y logs

- Qué loggear (mínimo):

  - Eventos de autenticación: login success/fail, token refresh, token revocado.
  - Operaciones críticas: creación/edición/eliminación de recursos (bodegas, usuarios, roles), cambios de privilegios.
  - Accesos denegados (401/403) y anomalías en tasa de acceso (picos de autenticación fallida).

- Consideraciones de privacidad y seguridad en logs:

  - Nunca loggear contraseñas en texto ni secret tokens completos. Redactar o hashear valores sensibles.
  - Enmascarar PII cuando sea posible.

- Integración y almacenamiento de logs:

  - Enviar logs a un sistema centralizado (ELK, Loki, Datadog, Splunk) con transporte seguro (TLS) y control de acceso.
  - Habilitar alertas para eventos críticos (varios 401s/403s, intentos de fuerza bruta).

- Retención y cumplimiento:

  - Definir políticas de retención y borrado según normativas (ej. GDPR), y asegurar posibilidad de auditoría.


## 15) Protección en la capa de aplicación

- Validación y saneamiento de entradas:

  - Usar modelos/serializers (p.ej. pydantic/SQLModel) para validar datos y evitar inyección.
  - Evitar concatenar SQL; usar ORM/queries parametrizadas.

- Protecciones contra CSRF/XSS:

  - Si se usan cookies de autenticación (HttpOnly), habilitar `SameSite` y CSRF tokens donde aplique.
  - Aplicar `Content-Security-Policy` y sanitizar HTML de entradas de usuario.

- Seguridad en cabeceras y políticas:

  - Implementar `CSP`, `HSTS`, `X-Frame-Options`, `X-Content-Type-Options`.


## 16) Persistencia de datos y backups seguros

- Backups cifrados y acceso restringido.
- Pruebas periódicas de restauración y documentación del procedimiento RTO/RPO.


## 17) Monitorización, detección y respuesta a incidentes

- Monitorizar métricas de seguridad: tasas de login fallido, tokens expirados, 401/403, picos de tráfico.
- Preparar playbooks de respuesta: revocar keys, rotar `SECRET_KEY` si es comprometida, invalidar sesiones desde la DB.


## 18) Ejemplos operativos y `curl`

- Obtener token (ejemplo):

```bash
curl -X POST "https://api.example.com/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=usuario@example.com&password=MiPass"
```

- Llamada autenticada con token:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  https://api.example.com/api/v1/bodegas
```

- Verificar TLS (OpenSSL):

```bash
openssl s_client -connect api.example.com:443 -tls1_2
```


## 19) Checklist operativo (breve)

- **Secrets:** Store `SECRET_KEY`, DB credentials, and API keys in KMS or env vars outside repo.
- **TLS:** Enforce TLS 1.2+/1.3, automatic certificate renewal.
- **Tokens:** Use short-lived access tokens; implement refresh tokens with revocation support.
- **Backups:** Encrypt backups and test restores monthly.
- **Logging:** Centralize logs, redact secrets, alert on anomalies.
- **CORS:** Restrict `allow_origins` in production to known frontends.
- **Rate limit:** Apply rate limiting at proxy for auth endpoints.


---
