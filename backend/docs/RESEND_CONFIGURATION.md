# Configuración de Resend

Resend es un servicio SMTP moderno y confiable que no tiene problemas de firewall y es perfecto para desarrollo y producción.

## Documentación Oficial

Consulta la documentación oficial de Resend SMTP: [https://resend.com/docs/send-with-smtp](https://resend.com/docs/send-with-smtp)

## Credenciales de Resend

Según la documentación oficial de Resend:
- **Servidor SMTP:** `smtp.resend.com`
- **Usuario:** `resend` (literal, siempre es este valor)
- **Contraseña:** Tu API Key de Resend
- **Puertos disponibles:**
  - **SMTPS (SSL implícito):** `465`, `2465`
  - **STARTTLS (TLS explícito):** `25`, `587`, `2587`

## Configuración Recomendada

### Opción 1: Puerto 587 con STARTTLS (Recomendado)

```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=tu_api_key_de_resend
SMTP_TLS=True
SMTP_SSL=False
EMAILS_FROM_EMAIL=noreply@tudominio.com
EMAILS_FROM_NAME=Tu Proyecto
```

### Opción 2: Puerto 465 con SMTPS (Alternativa)

Si el puerto 587 está bloqueado, usa SSL:

```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=tu_api_key_de_resend
SMTP_TLS=False
SMTP_SSL=True
EMAILS_FROM_EMAIL=noreply@tudominio.com
EMAILS_FROM_NAME=Tu Proyecto
```

### Opción 3: Puerto 2587 con STARTTLS

Si los puertos anteriores fallan:

```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=2587
SMTP_USER=resend
SMTP_PASSWORD=tu_api_key_de_resend
SMTP_TLS=True
SMTP_SSL=False
EMAILS_FROM_EMAIL=noreply@tudominio.com
EMAILS_FROM_NAME=Tu Proyecto
```

## Pasos para Configurar

### 1. Obtén tu API Key de Resend

1. Regístrate o inicia sesión en [Resend](https://resend.com/)
2. Ve a **API Keys** en el dashboard
3. Crea un nuevo API Key
4. Copia el API Key (solo se muestra una vez)

### 2. Verifica tu dominio

**IMPORTANTE:** Debes verificar tu dominio antes de poder enviar emails.

1. Ve a **Domains** en el dashboard de Resend
2. Agrega tu dominio (ej: `tudominio.com`)
3. Configura los registros DNS que Resend te proporcione:
   - Registro SPF
   - Registro DKIM
   - Registro DMARC (opcional pero recomendado)
4. Espera a que la verificación se complete

### 3. Actualiza tu archivo `.env`

```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_xxxxxxxxxxxxx  # Tu API Key aquí
SMTP_TLS=True
SMTP_SSL=False
EMAILS_FROM_EMAIL=noreply@tudominio.com  # Debe ser de un dominio verificado
EMAILS_FROM_NAME=Tu Proyecto
```

### 4. Reinicia el servidor

```bash
# Detén el servidor (Ctrl+C) y vuelve a iniciarlo
```

### 5. Verifica la configuración

Al iniciar, deberías ver en los logs:
```
EmailService inicializado: smtp.resend.com:587 (SSL: False, TLS: True)
```

## Puertos Disponibles

Resend soporta múltiples puertos según el tipo de seguridad:

| Tipo     | Puerto | Configuración                    |
|----------|--------|----------------------------------|
| STARTTLS | 587    | `SMTP_TLS=True`, `SMTP_SSL=False` |
| STARTTLS | 2587   | `SMTP_TLS=True`, `SMTP_SSL=False` |
| STARTTLS | 25     | `SMTP_TLS=True`, `SMTP_SSL=False` |
| SMTPS    | 465    | `SMTP_SSL=True`, `SMTP_TLS=False` |
| SMTPS    | 2465   | `SMTP_SSL=True`, `SMTP_SSL=False` |

El servicio intentará automáticamente puertos alternativos si el principal falla.

## Ventajas de Resend

- ✅ **Sin problemas de firewall** - Usa puertos estándar
- ✅ **Múltiples puertos disponibles** - Si uno falla, prueba otro automáticamente
- ✅ **Moderno y confiable** - Diseñado para aplicaciones modernas
- ✅ **Excelente deliverability** - Menos probabilidad de spam
- ✅ **Dashboard completo** - Analytics y tracking de emails
- ✅ **API y SMTP** - Puedes usar ambos métodos

## Solución de Problemas

### Error: "your envelope sender domain must exist"

**Problema:** El dominio del remitente no está verificado en Resend.

**Solución:**
1. Accede al dashboard de Resend
2. Ve a **Domains**
3. Verifica que tu dominio esté agregado y verificado
4. Asegúrate de que `EMAILS_FROM_EMAIL` use un email de un dominio verificado

### Error de autenticación

- Verifica que `SMTP_USER` sea exactamente `resend` (sin comillas, literal)
- Verifica que `SMTP_PASSWORD` sea tu API Key completo de Resend
- Asegúrate de que no haya espacios antes/después de las credenciales

### Si el puerto 587 falla

El servicio intentará automáticamente los puertos 465, 2587, 2465 y 25. También puedes configurarlo directamente:

```env
SMTP_PORT=465
SMTP_SSL=True
SMTP_TLS=False
```

### Verificar conexión

Puedes probar la conexión con el script de diagnóstico:

```bash
cd backend
uv run python scripts/test_smtp_connection.py
```

El script detectará automáticamente si estás usando Resend y probará todos sus puertos.

## Recursos

- [Documentación oficial de Resend SMTP](https://resend.com/docs/send-with-smtp)
- [Dashboard de Resend](https://resend.com/)
- [API Reference](https://resend.com/docs/api-reference)

