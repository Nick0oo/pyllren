"""
Script para probar la conexión SMTP desde localhost.

Este script ayuda a diagnosticar problemas de conexión SMTP
y verifica qué puertos están disponibles desde tu red.

Uso:
    cd backend
    uv run python scripts/test_smtp_connection.py
    
    O si estás usando el entorno virtual directamente:
    cd backend
    .venv/Scripts/python scripts/test_smtp_connection.py
"""
import smtplib
import sys
import os
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Intentar importar settings, si falla dar instrucciones
try:
    from app.core.config import settings
except ImportError as e:
    print("=" * 60)
    print("❌ Error: No se pudo importar las dependencias.")
    print("=" * 60)
    print(f"Error: {e}")
    print("\n💡 Solución:")
    print("   Ejecuta el script usando uv run:")
    print("   cd backend")
    print("   uv run python scripts/test_smtp_connection.py")
    print("\n   O activa el entorno virtual primero:")
    print("   cd backend")
    print("   .venv\\Scripts\\activate  # Windows")
    print("   python scripts/test_smtp_connection.py")
    sys.exit(1)


def test_smtp_connection(host: str, port: int, use_ssl: bool = False) -> bool:
    """Prueba una conexión SMTP específica."""
    try:
        print(f"\n🔍 Probando conexión a {host}:{port} (SSL: {use_ssl})...")
        
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        
        server.quit()
        print(f"✅ Conexión exitosa a {host}:{port}")
        return True
    except (TimeoutError, ConnectionError, OSError) as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False


def test_all_ports(host: str) -> None:
    """Prueba todos los puertos comunes de SMTP."""
    print(f"\n{'='*60}")
    print(f"🧪 Probando conexiones SMTP a {host}")
    print(f"{'='*60}")
    
    ports_to_test = [
        (465, True, "SSL directo (recomendado para Gmail)"),
        (587, False, "STARTTLS (alternativa)"),
        (2587, False, "Puerto Alternativo para Resend")
    ]
    
    results = []
    for port, use_ssl, description in ports_to_test:
        success = test_smtp_connection(host, port, use_ssl)
        results.append((port, use_ssl, description, success))
    
    print(f"\n{'='*60}")
    print("📊 Resumen de resultados:")
    print(f"{'='*60}")
    
    for port, use_ssl, description, success in results:
        status = "✅ DISPONIBLE" if success else "❌ BLOQUEADO/NO DISPONIBLE"
        print(f"Puerto {port} ({description}): {status}")
    
    # Recomendación
    available = [r for r in results if r[3]]
    if available:
        best = available[0]
        print(f"\n Recomendación: Usar puerto {best[0]} con SSL={best[1]}")
        print(f"   SMTP_PORT={best[0]}")
        print(f"   SMTP_SSL={str(best[1]).lower()}")
        print(f"   SMTP_TLS={str(not best[1]).lower()}")
    else:
        print(f"\n⚠️  Ningún puerto está disponible desde tu red.")
        print(f"   Posibles soluciones:")
        print(f"   1. Usa una VPN")
        print(f"   2. Usa un servicio SMTP relé (SendGrid, Mailgun, etc.)")
        print(f"   3. Prueba desde otra red (móvil, otro ISP)")


def test_with_credentials() -> None:
    """Prueba la conexión completa con credenciales."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("\n⚠️  Credenciales no configuradas. Solo probando conexión...")
        return
    
    print(f"\n{'='*60}")
    print("🔐 Probando autenticación SMTP")
    print(f"{'='*60}")
    
    try:
        host = settings.SMTP_HOST
        port = settings.SMTP_PORT
        use_ssl = settings.SMTP_SSL
        
        print(f"\nConectando a {host}:{port}...")
        
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if settings.SMTP_TLS:
                server.starttls()
        
        print(f"Autenticando con usuario: {settings.SMTP_USER}...")
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.quit()
        
        print(f"✅ Autenticación exitosa!")
        print(f"\n💡 Tu configuración SMTP está funcionando correctamente.")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación: {e}")
        print(f"\n💡 Verifica:")
        print(f"   - SMTP_USER: {settings.SMTP_USER}")
        print(f"   - SMTP_PASSWORD: {'*' * min(len(settings.SMTP_PASSWORD), 8)}")
        print(f"   - Para Gmail, usa un App Password, no tu contraseña regular")
    except (TimeoutError, ConnectionError, OSError) as e:
        print(f"❌ Error de conexión: {e}")
        print(f"\n💡 El puerto {port} puede estar bloqueado. Prueba otros puertos.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🧪 Script de prueba de conexión SMTP")
    print("=" * 60)
    
    # Determinar qué host probar
    if settings.SMTP_HOST and settings.SMTP_HOST != "smtp.gmail.com":
        # Si hay un host configurado diferente a Gmail, probarlo
        test_host = settings.SMTP_HOST
        print(f"📧 Probando host configurado: {test_host}")
    else:
        # Por defecto, probar Gmail
        test_host = "smtp.gmail.com"
        print(f"📧 Probando Gmail (por defecto)")
    
    # Probar todos los puertos comunes
    test_all_ports(test_host)
    
    # Si hay configuración, probar con credenciales
    if settings.SMTP_HOST:
        test_with_credentials()
    
    print(f"\n{'='*60}")
    print("✅ Prueba completada")
    print(f"{'='*60}")

