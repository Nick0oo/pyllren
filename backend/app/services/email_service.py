"""
Servicio de envío de correos electrónicos usando SMTP.

Este servicio está desacoplado del resto de la aplicación y maneja
exclusivamente el envío de correos usando smtplib y EmailMessage.

Características:
- Soporte para SMTP_SSL (puerto 465) y SMTP con STARTTLS (puerto 587)
- Validación robusta de configuración
- Manejo de errores específico por tipo
- Listo para producción
"""
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Excepción base para errores del servicio de email."""
    pass


class EmailConfigurationError(EmailServiceError):
    """Error de configuración del servicio de email."""
    pass


class EmailSendingError(EmailServiceError):
    """Error al enviar el correo electrónico."""
    pass


class EmailService:
    """
    Servicio para envío de correos electrónicos vía SMTP.
    
    Este servicio maneja la conexión SMTP, autenticación y envío de correos
    de forma desacoplada del resto de la aplicación.
    """

    def __init__(self):
        """Inicializa el servicio de email con configuración de settings."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.smtp_ssl = settings.SMTP_SSL
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME or settings.PROJECT_NAME
        
        # Validar configuración al inicializar
        self._validate_config()
        
        logger.info(
            f"EmailService inicializado: {self.smtp_host}:{self.smtp_port} "
            f"(SSL: {self.smtp_ssl}, TLS: {self.smtp_tls})"
        )

    def _validate_config(self) -> None:
        """
        Valida que la configuración de email esté completa y sea válida.
        
        Raises:
            EmailConfigurationError: Si la configuración es inválida o incompleta
        """
        errors = []
        
        if not self.smtp_host or not self.smtp_host.strip():
            errors.append("SMTP_HOST no está configurado o está vacío")
        
        if not self.smtp_port or self.smtp_port <= 0:
            errors.append(f"SMTP_PORT debe ser un número positivo (actual: {self.smtp_port})")
        
        if not self.smtp_user or not self.smtp_user.strip():
            errors.append("SMTP_USER no está configurado o está vacío")
        
        if not self.smtp_password or not self.smtp_password.strip():
            errors.append("SMTP_PASSWORD no está configurado o está vacío")
        
        if not self.from_email:
            errors.append("EMAILS_FROM_EMAIL no está configurado")
        
        # Validar que SSL y TLS no estén ambos activos simultáneamente
        if self.smtp_ssl and self.smtp_tls:
            errors.append("SMTP_SSL y SMTP_TLS no pueden estar ambos en True simultáneamente")
        
        # Validar puerto según tipo de conexión
        if self.smtp_ssl and self.smtp_port != 465:
            logger.warning(
                f"SMTP_SSL está activo pero el puerto es {self.smtp_port} "
                f"(típicamente se usa 465 para SSL)"
            )
        
        if errors:
            error_msg = "Errores de configuración de email:\n" + "\n".join(f"  - {e}" for e in errors)
            raise EmailConfigurationError(error_msg)

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Envía un correo electrónico usando SMTP.
        
        Intenta múltiples puertos automáticamente si el puerto configurado falla,
        lo cual es útil desde localhost donde algunos ISPs bloquean ciertos puertos.

        Args:
            to_email: Dirección de correo del destinatario
            subject: Asunto del correo
            html_content: Contenido HTML del correo
            text_content: Contenido de texto plano (opcional, se genera automáticamente si no se proporciona)

        Returns:
            True si el correo se envió exitosamente

        Raises:
            EmailConfigurationError: Si la configuración es inválida
            EmailSendingError: Si hay un error al enviar el correo
        """
        # Validar email del destinatario
        if not to_email or "@" not in to_email:
            raise EmailSendingError(f"Email del destinatario inválido: {to_email}")

        # Crear mensaje usando EmailMessage
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        
        # Establecer contenido: texto plano y HTML
        if text_content:
            msg.set_content(text_content, subtype="plain")
        else:
            # Generar texto plano básico desde HTML si no se proporciona
            import re
            text_plain = re.sub(r'<[^>]+>', '', html_content)
            text_plain = re.sub(r'\s+', ' ', text_plain).strip()
            msg.set_content(text_plain or "Email HTML", subtype="plain")
        
        msg.add_alternative(html_content, subtype="html")

        # Intentar enviar con la configuración principal
        try:
            logger.info(
                f"Enviando correo a {to_email} vía {self.smtp_host}:{self.smtp_port}"
            )

            # Conectar y enviar según tipo de conexión
            if self.smtp_ssl or self.smtp_port == 465:
                # Puerto 465 usa SSL directamente (método recomendado para Gmail)
                self._send_via_ssl(msg, to_email)
            else:
                # Puertos 587, 2525 usan STARTTLS
                self._send_via_tls(msg, to_email)

            logger.info(f"✅ Correo enviado exitosamente a {to_email}")
            return True

        except (TimeoutError, ConnectionError, OSError) as e:
            # Si falla la conexión, intentar puertos alternativos automáticamente
            error_msg = str(e)
            logger.warning(
                f"⚠️  Falló conexión en puerto {self.smtp_port}: {error_msg}. "
                f"Intentando puertos alternativos..."
            )
            
            # Intentar puertos alternativos para Gmail, TurboSMTP o Resend
            if "gmail.com" in self.smtp_host.lower() or "turbo-smtp.com" in self.smtp_host.lower() or "resend.com" in self.smtp_host.lower():
                return self._try_alternative_ports(msg, to_email, error_msg)
            else:
                # Para otros proveedores, re-raise el error original
                raise

        except EmailSendingError:
            # Re-raise errores específicos del servicio
            raise
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación SMTP: {e}")
            raise EmailSendingError(
                f"Error de autenticación SMTP. Verifica tus credenciales:\n"
                f"  - SMTP_USER: {self.smtp_user}\n"
                f"  - SMTP_PASSWORD: {'*' * min(len(self.smtp_password), 8) if self.smtp_password else 'no configurado'}\n"
                f"  - Para Gmail, asegúrate de usar un App Password, no tu contraseña regular"
            ) from e
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"❌ Destinatario rechazado: {e}")
            raise EmailSendingError(
                f"El servidor SMTP rechazó el destinatario: {to_email}"
            ) from e
        except smtplib.SMTPSenderRefused as e:
            logger.error(f"❌ Remitente rechazado: {e}")
            error_msg = (
                f"El servidor SMTP rechazó el remitente: {self.from_email}\n\n"
            )
            if "turbo-smtp.com" in self.smtp_host.lower():
                error_msg += (
                    f"💡 Para TurboSMTP:\n"
                    f"   1. Verifica el dominio '{self.from_email.split('@')[1]}' en tu cuenta de TurboSMTP\n"
                    f"   2. O usa un email verificado como remitente\n"
                    f"   3. Ver: backend/docs/TURBOSMTP_CONFIGURATION.md"
                )
            raise EmailSendingError(error_msg) from e
        except smtplib.SMTPDataError as e:
            # Error 552: dominio no verificado, etc.
            error_code = getattr(e, 'smtp_code', None)
            error_msg_str = str(e)
            logger.error(f"❌ Error de datos SMTP (código {error_code}): {e}")
            
            if error_code == 552 or "domain must exist" in error_msg_str.lower() or "envelope sender" in error_msg_str.lower():
                domain = self.from_email.split('@')[1] if '@' in self.from_email else "desconocido"
                error_msg = (
                    f"❌ Dominio del remitente no verificado\n\n"
                    f"El dominio '{domain}' no está verificado en TurboSMTP.\n"
                    f"Email remitente: {self.from_email}\n\n"
                    f"💡 Soluciones:\n"
                    f"   1. Verifica el dominio '{domain}' en tu cuenta de TurboSMTP:\n"
                    f"      - Accede al panel de TurboSMTP\n"
                    f"      - Ve a la sección de dominios\n"
                    f"      - Agrega y verifica el dominio '{domain}'\n"
                    f"      - Configura los registros DNS requeridos\n\n"
                    f"   2. O usa un email de un dominio ya verificado:\n"
                    f"      - Cambia EMAILS_FROM_EMAIL en tu .env\n"
                    f"      - Usa un email que ya esté verificado en TurboSMTP\n\n"
                    f"   3. Para desarrollo, puedes usar el dominio de prueba de TurboSMTP\n\n"
                    f"   Ver: backend/docs/TURBOSMTP_CONFIGURATION.md"
                )
            else:
                error_msg = f"Error SMTP (código {error_code}): {e}"
            
            raise EmailSendingError(error_msg) from e
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP: {e}")
            raise EmailSendingError(f"Error SMTP: {e}") from e
        except (TimeoutError, ConnectionError, OSError) as e:
            error_msg = str(e)
            logger.error(f"❌ Error de conexión SMTP: {error_msg}")
            raise EmailSendingError(
                f"Error de conexión SMTP: {error_msg}\n\n"
                f"Verifica que:\n"
                f"  - SMTP_HOST: {self.smtp_host}\n"
                f"  - SMTP_PORT: {self.smtp_port}\n"
                f"  - El puerto no esté bloqueado por firewall\n"
                f"  - La red permita conexiones SMTP\n"
                f"  - El servidor SMTP esté disponible"
            ) from e
        except Exception as e:
            logger.error(f"❌ Error inesperado al enviar correo: {e}", exc_info=True)
            raise EmailSendingError(f"Error inesperado al enviar correo: {e}") from e

    def _send_via_ssl(self, msg: EmailMessage, to_email: str) -> None:
        """Envía correo usando SMTP_SSL (puerto 465)."""
        logger.debug(f"Usando conexión SSL directa (puerto {self.smtp_port})")
        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            smtp.login(self.smtp_user, self.smtp_password)
            logger.debug("✅ Autenticación exitosa")
            smtp.send_message(msg)

    def _send_via_tls(self, msg: EmailMessage, to_email: str) -> None:
        """Envía correo usando SMTP con STARTTLS (puerto 587)."""
        logger.debug(f"Conectando a {self.smtp_host}:{self.smtp_port}")
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
            if self.smtp_tls:
                logger.debug("Iniciando STARTTLS...")
                smtp.starttls()
            
            logger.debug(f"Autenticando con usuario: {self.smtp_user}")
            smtp.login(self.smtp_user, self.smtp_password)
            logger.debug("✅ Autenticación exitosa")
            smtp.send_message(msg)

    def _try_alternative_ports(
        self, msg: EmailMessage, to_email: str, original_error: str
    ) -> bool:
        """
        Intenta enviar el correo usando puertos alternativos.
        
        Útil cuando el puerto principal está bloqueado por el ISP/firewall.
        """
        # Determinar puertos alternativos según el proveedor
        if "resend.com" in self.smtp_host.lower():
            # Puertos de Resend: 587 (STARTTLS), 465 (SMTPS), 2587 (STARTTLS), 2465 (SMTPS), 25 (STARTTLS)
            # Según: https://resend.com/docs/send-with-smtp
            alternative_configs = [
                (587, False, True),   # STARTTLS (recomendado)
                (465, True, False),   # SMTPS (SSL directo)
                (2587, False, True),  # STARTTLS alternativo
                (2465, True, False), # SMTPS alternativo
                (25, False, True),    # STARTTLS estándar
            ]
        elif "turbo-smtp.com" in self.smtp_host.lower():
            # Puertos de TurboSMTP: 587 (TLS), 465 (SSL), 2525 (TLS), 25 (TLS), 25025 (SSL)
            alternative_configs = [
                (587, False, True),   # TLS (recomendado)
                (465, True, False),   # SSL directo
                (2525, False, True),  # TLS alternativo
                (25, False, True),    # TLS estándar
                (25025, True, False), # SSL alternativo
            ]
        else:
            # Puertos alternativos para Gmail
            alternative_configs = [
                (465, True, False),   # SSL directo (más confiable)
                (587, False, True),  # STARTTLS
            ]
        
        # Filtrar la configuración actual
        alternative_configs = [
            (port, ssl, tls) for port, ssl, tls in alternative_configs
            if not (port == self.smtp_port and ssl == self.smtp_ssl and tls == self.smtp_tls)
        ]
        
        last_error = None
        for port, use_ssl, use_tls in alternative_configs:
            try:
                logger.info(
                    f"🔄 Intentando puerto alternativo {port} "
                    f"(SSL: {use_ssl}, TLS: {use_tls})..."
                )
                
                if use_ssl:
                    with smtplib.SMTP_SSL(self.smtp_host, port, timeout=30) as smtp:
                        smtp.login(self.smtp_user, self.smtp_password)
                        smtp.send_message(msg)
                else:
                    with smtplib.SMTP(self.smtp_host, port, timeout=30) as smtp:
                        if use_tls:
                            smtp.starttls()
                        smtp.login(self.smtp_user, self.smtp_password)
                        smtp.send_message(msg)
                
                logger.info(
                    f"✅ Correo enviado exitosamente usando puerto alternativo {port}"
                )
                logger.warning(
                    f"💡 Considera actualizar tu .env para usar el puerto {port} "
                    f"directamente para mejor rendimiento:\n"
                    f"   SMTP_PORT={port}\n"
                    f"   SMTP_SSL={str(use_ssl).lower()}\n"
                    f"   SMTP_TLS={str(use_tls).lower()}"
                )
                return True
                
            except (TimeoutError, ConnectionError, OSError) as e:
                last_error = e
                logger.debug(f"Puerto {port} también falló: {e}")
                continue
            except Exception as e:
                last_error = e
                logger.debug(f"Error en puerto {port}: {e}")
                continue
        
        # Si todos los puertos fallaron
        if "resend.com" in self.smtp_host.lower():
            error_message = (
                f"Error de conexión SMTP: No se pudo conectar a ningún puerto de Resend.\n\n"
                f"Error original: {original_error}\n\n"
                f"Puertos intentados: 587, 465, 2587, 2465, 25\n\n"
                f"💡 Posibles soluciones:\n"
                f"   1. Verifica que tu red/firewall permita conexiones SMTP salientes\n"
                f"   2. Verifica tus credenciales:\n"
                f"      - SMTP_USER debe ser 'resend' (literal)\n"
                f"      - SMTP_PASSWORD debe ser tu API Key de Resend\n"
                f"   3. Verifica que tu dominio esté verificado en Resend\n"
                f"   4. Prueba desde otra red (móvil, VPN)\n\n"
                f"   Ver: backend/docs/RESEND_CONFIGURATION.md para más detalles"
            )
        elif "turbo-smtp.com" in self.smtp_host.lower():
            error_message = (
                f"Error de conexión SMTP: No se pudo conectar a ningún puerto de TurboSMTP.\n\n"
                f"Error original: {original_error}\n\n"
                f"Puertos intentados: 587, 465, 2525, 25, 25025\n\n"
                f"💡 Posibles soluciones:\n"
                f"   1. Verifica que tu red/firewall permita conexiones SMTP salientes\n"
                f"   2. Verifica tus credenciales (Consumer Key y Consumer Secret)\n"
                f"   3. Prueba desde otra red (móvil, VPN)\n"
                f"   4. Contacta con TurboSMTP para verificar tu cuenta\n\n"
                f"   Ver: backend/docs/TURBOSMTP_CONFIGURATION.md para más detalles"
            )
        else:
            error_message = (
                f"Error de conexión SMTP: No se pudo conectar a ningún puerto.\n\n"
                f"Error original: {original_error}\n\n"
                f"💡 SOLUCIÓN RECOMENDADA: Usa un servicio SMTP relé\n"
                f"   Todos los puertos SMTP están bloqueados desde tu red.\n"
                f"   Los servicios SMTP relé no tienen este problema:\n\n"
                f"   TurboSMTP:\n"
                f"     SMTP_HOST=pro.turbo-smtp.com\n"
                f"     SMTP_PORT=587\n"
                f"     SMTP_USER=tu_consumer_key\n"
                f"     SMTP_PASSWORD=tu_consumer_secret\n"
                f"     SMTP_TLS=True\n\n"
                f"   SendGrid (100 emails/día gratis):\n"
                f"     SMTP_HOST=smtp.sendgrid.net\n"
                f"     SMTP_PORT=587\n"
                f"     SMTP_USER=apikey\n"
                f"     SMTP_PASSWORD=tu_sendgrid_api_key\n"
                f"     SMTP_TLS=True\n\n"
                f"   Ver: backend/docs/SMTP_RELAY_SERVICES.md para más detalles"
            )
        
        raise EmailSendingError(error_message) from last_error


# Instancia singleton del servicio
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Obtiene la instancia singleton del servicio de email.

    Returns:
        Instancia de EmailService

    Raises:
        EmailConfigurationError: Si la configuración es inválida
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_email_safely(
    to_email: str,
    subject: str,
    html_content: str,
) -> None:
    """
    Wrapper seguro para enviar emails en BackgroundTask.
    
    Esta función captura y loguea errores sin propagarlos para que
    los BackgroundTasks no rompan la aplicación si falla el envío.
    
    Args:
        to_email: Dirección de correo del destinatario
        subject: Asunto del correo
        html_content: Contenido HTML del correo
    """
    try:
        email_service = get_email_service()
        email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )
        logger.info(f"✅ Email enviado exitosamente a {to_email} (BackgroundTask)")
    except EmailConfigurationError as e:
        logger.error(
            f"❌ Error de configuración al enviar email a {to_email}: {e}. "
            f"Verifica las variables de entorno SMTP_*"
        )
    except EmailSendingError as e:
        logger.error(
            f"❌ Error al enviar email a {to_email}: {e}. "
            f"El email no se pudo enviar, pero la operación principal se completó."
        )
    except Exception as e:
        logger.error(
            f"❌ Error inesperado al enviar email a {to_email}: {e}",
            exc_info=True
        )
