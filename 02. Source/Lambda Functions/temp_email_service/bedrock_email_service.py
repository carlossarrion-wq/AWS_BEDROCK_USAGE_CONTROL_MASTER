#!/usr/bin/env python3
"""
AWS Bedrock Individual Blocking System - Enhanced Email Service
==============================================================

This module provides comprehensive email notification services for:
1. Warning emails (80% quota reached) - Amber color
2. Blocking emails (100% quota exceeded) - Light red color
3. Unblocking emails (daily reset) - Green color
4. Admin blocking emails (manual admin block) - Light red color
5. Admin unblocking emails (manual admin unblock) - Green color

All emails follow the Spanish templates with proper color coding and formatting.

Author: AWS Bedrock Usage Control System
Version: 2.0.0
"""

import json
import boto3
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
iam = boto3.client('iam')

class EnhancedEmailNotificationService:
    """Enhanced email service for all Bedrock notification scenarios"""
    
    def __init__(self, credentials_file: str = None):
        """
        Initialize email service with credentials
        
        Args:
            credentials_file: Path to credentials JSON file
        """
        self.iam_client = iam
        self.credentials = self._load_credentials(credentials_file)
        self.smtp_config = self.credentials.get('gmail_smtp', {})
        self.email_settings = self.credentials.get('email_settings', {})
        
        # SMTP configuration
        self.smtp_server = self.smtp_config.get('server', 'smtp.gmail.com')
        self.smtp_port = self.smtp_config.get('port', 587)
        self.gmail_user = self.smtp_config.get('user', '')
        self.gmail_password = self.smtp_config.get('password', '')
        self.use_tls = self.smtp_config.get('use_tls', True)
        
        logger.info(f"Email service initialized with user: {self.gmail_user}")
    
    def _load_credentials(self, credentials_file: str = None) -> Dict[str, Any]:
        """Load email credentials from file"""
        try:
            if not credentials_file:
                # Try multiple possible locations
                possible_paths = [
                    'email_credentials.json',
                    os.path.join(os.path.dirname(__file__), 'email_credentials.json'),
                    '/opt/email_credentials.json'  # Lambda layer location
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        credentials_file = path
                        break
            
            if credentials_file and os.path.exists(credentials_file):
                with open(credentials_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Credentials file not found, using environment variables")
                return {
                    'gmail_smtp': {
                        'server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
                        'port': int(os.environ.get('SMTP_PORT', '587')),
                        'user': os.environ.get('GMAIL_USER', ''),
                        'password': os.environ.get('GMAIL_PASSWORD', ''),
                        'use_tls': True
                    },
                    'email_settings': {
                        'default_language': 'es',
                        'timezone': 'Europe/Madrid',
                        'reply_to': os.environ.get('GMAIL_USER', '')
                    }
                }
        except Exception as e:
            logger.error(f"Error loading credentials: {str(e)}")
            return {}
    
    def get_user_email(self, user_id: str) -> Optional[str]:
        """
        Retrieve user email from IAM tags
        
        Args:
            user_id: The user ID to get email for
            
        Returns:
            User email address or None if not found
        """
        try:
            response = self.iam_client.list_user_tags(UserName=user_id)
            user_tags = {tag['Key']: tag['Value'] for tag in response['Tags']}
            
            email = user_tags.get('Email')
            if email:
                logger.info(f"Retrieved email for user {user_id}: {email}")
                return email
            else:
                logger.warning(f"No Email tag found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving email for user {user_id}: {str(e)}")
            return None
    
    def get_user_display_name(self, user_id: str) -> str:
        """
        Get user display name from IAM tags with fallback logic
        
        Priority:
        1. Person tag (if exists and not "unknown")
        2. Email tag without domain (if exists)
        3. user_id as fallback
        
        Args:
            user_id: The user ID to get display name for
            
        Returns:
            Display name for the user
        """
        try:
            response = self.iam_client.list_user_tags(UserName=user_id)
            user_tags = {tag['Key']: tag['Value'] for tag in response['Tags']}
            
            # Priority 1: Person tag (if exists and not "unknown")
            person_name = user_tags.get('Person')
            if person_name and person_name.lower() != 'unknown':
                logger.info(f"Using Person tag for {user_id}: {person_name}")
                return person_name
            
            # Priority 2: Email tag without domain (if exists)
            email = user_tags.get('Email')
            if email and '@' in email:
                email_username = email.split('@')[0]
                logger.info(f"Using email username for {user_id}: {email_username}")
                return email_username
            
            # Priority 3: user_id as fallback
            logger.info(f"Using user_id as fallback for {user_id}")
            return user_id
                
        except Exception as e:
            logger.error(f"Error retrieving display name for user {user_id}: {str(e)}")
            return user_id
    
    def send_warning_email(self, user_id: str, usage_record: Dict[str, Any]) -> bool:
        """
        Send warning email (80% quota reached) - Amber color
        
        Args:
            user_id: The user ID
            usage_record: Current usage record from DynamoDB
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            user_email = self.get_user_email(user_id)
            if not user_email:
                logger.warning(f"Cannot send warning email to {user_id} - no email address")
                return False
            
            # Get display name for personalization
            display_name = self.get_user_display_name(user_id)
            
            # Prepare email content
            current_usage = int(usage_record['request_count']) if isinstance(usage_record['request_count'], Decimal) else usage_record['request_count']
            daily_limit = int(usage_record['daily_limit']) if isinstance(usage_record['daily_limit'], Decimal) else usage_record['daily_limit']
            
            subject = f"Aviso de Uso de Bedrock - Te estás acercando a tu límite diario"
            
            html_body = self._generate_warning_email_html(display_name, usage_record)
            text_body = self._generate_warning_email_text(display_name, usage_record)
            
            # Send email
            return self._send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Error sending warning email to {user_id}: {str(e)}")
            return False
    
    def send_blocking_email(self, user_id: str, usage_record: Dict[str, Any], reason: str = "daily_limit_exceeded") -> bool:
        """
        Send blocking email (100% quota exceeded) - Light red color
        
        Args:
            user_id: The user ID
            usage_record: Current usage record from DynamoDB
            reason: Reason for blocking
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            user_email = self.get_user_email(user_id)
            if not user_email:
                logger.warning(f"Cannot send blocking email to {user_id} - no email address")
                return False
            
            # Get display name for personalization
            display_name = self.get_user_display_name(user_id)
            
            subject = f"Acceso a Bedrock Bloqueado - Límite diario excedido"
            
            html_body = self._generate_blocking_email_html(display_name, usage_record, reason)
            text_body = self._generate_blocking_email_text(display_name, usage_record, reason)
            
            # Send email
            return self._send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Error sending blocking email to {user_id}: {str(e)}")
            return False
    
    def send_unblocking_email(self, user_id: str, reason: str = "daily_reset") -> bool:
        """
        Send unblocking email (daily reset) - Green color
        
        Args:
            user_id: The user ID
            reason: Reason for unblocking
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            user_email = self.get_user_email(user_id)
            if not user_email:
                logger.warning(f"Cannot send unblocking email to {user_id} - no email address")
                return False
            
            subject = f"Acceso a Bedrock Restaurado - Ya puedes usar Bedrock nuevamente"
            
            html_body = self._generate_unblocking_email_html(user_id, reason)
            text_body = self._generate_unblocking_email_text(user_id, reason)
            
            # Send email
            return self._send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Error sending unblocking email to {user_id}: {str(e)}")
            return False
    
    def send_admin_blocking_email(self, user_id: str, admin_user: str, reason: str = "manual_admin_block", usage_record: Dict[str, Any] = None) -> bool:
        """
        Send admin blocking email (manual admin block) - Light red color
        
        Args:
            user_id: The user ID
            admin_user: Administrator who performed the block
            reason: Reason for blocking
            usage_record: Current usage record from DynamoDB (optional, for expiration date)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            user_email = self.get_user_email(user_id)
            if not user_email:
                logger.warning(f"Cannot send admin blocking email to {user_id} - no email address")
                return False
            
            # Get display name for personalization
            display_name = self.get_user_display_name(user_id)
            
            subject = f"Acceso a Bedrock Bloqueado por Administrador"
            
            html_body = self._generate_admin_blocking_email_html(display_name, admin_user, reason, usage_record)
            text_body = self._generate_admin_blocking_email_text(display_name, admin_user, reason, usage_record)
            
            # Send email
            return self._send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Error sending admin blocking email to {user_id}: {str(e)}")
            return False
    
    def send_admin_unblocking_email(self, user_id: str, admin_user: str, reason: str = "manual_admin_unblock") -> bool:
        """
        Send admin unblocking email (manual admin unblock) - Green color
        
        Args:
            user_id: The user ID
            admin_user: Administrator who performed the unblock
            reason: Reason for unblocking
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            user_email = self.get_user_email(user_id)
            if not user_email:
                logger.warning(f"Cannot send admin unblocking email to {user_id} - no email address")
                return False
            
            # Get display name for personalization
            display_name = self.get_user_display_name(user_id)
            
            subject = f"Acceso a Bedrock Restaurado por Administrador"
            
            html_body = self._generate_admin_unblocking_email_html(display_name, admin_user, reason)
            text_body = self._generate_admin_unblocking_email_text(display_name, admin_user, reason)
            
            # Send email
            return self._send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Error sending admin unblocking email to {user_id}: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Send email using Gmail SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.gmail_user
            message["To"] = to_email
            message["Reply-To"] = self.email_settings.get('reply_to', self.gmail_user)
            
            # Create the plain-text and HTML version of your message
            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            
            # Add HTML/plain-text parts to MIMEMultipart message
            message.attach(part1)
            message.attach(part2)
            
            # Create secure connection with server and send email
            context = ssl.create_default_context()
            # For Gmail SMTP, we need to be less strict about certificate verification
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.gmail_user, self.gmail_password)
                text = message.as_string()
                server.sendmail(self.gmail_user, to_email, text)
            
            logger.info(f"Email sent successfully to {to_email} via Gmail SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email} via Gmail SMTP: {str(e)}")
            return False
    
    def _get_madrid_time(self) -> str:
        """Get current time in Madrid timezone"""
        try:
            # Use proper Madrid timezone handling for DST
            import zoneinfo
            madrid_tz = zoneinfo.ZoneInfo('Europe/Madrid')
            madrid_time = datetime.now(madrid_tz)
            # Determine if we're in DST (CEST) or standard time (CET)
            tz_name = 'CEST' if madrid_time.dst() else 'CET'
            return madrid_time.strftime(f'%Y-%m-%d %H:%M:%S {tz_name}')
        except ImportError:
            # Fallback for older Python versions - manually handle DST
            try:
                # Simple DST check: March last Sunday to October last Sunday
                now_utc = datetime.utcnow()
                year = now_utc.year
                
                # Calculate DST period (rough approximation)
                # DST starts last Sunday in March, ends last Sunday in October
                march_last_sunday = 31 - ((5 * year // 4 + 4) % 7)
                october_last_sunday = 31 - ((5 * year // 4 + 1) % 7)
                
                dst_start = datetime(year, 3, march_last_sunday, 1, 0, 0)  # 1 AM UTC
                dst_end = datetime(year, 10, october_last_sunday, 1, 0, 0)  # 1 AM UTC
                
                is_dst = dst_start <= now_utc < dst_end
                offset_hours = 2 if is_dst else 1
                tz_name = 'CEST' if is_dst else 'CET'
                
                madrid_tz = timezone(timedelta(hours=offset_hours))
                madrid_time = now_utc.replace(tzinfo=timezone.utc).astimezone(madrid_tz)
                return madrid_time.strftime(f'%Y-%m-%d %H:%M:%S {tz_name}')
            except:
                return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def _generate_warning_email_html(self, display_name: str, usage_record: Dict[str, Any]) -> str:
        """Generate HTML content for warning email - Amber color"""
        current_usage = int(usage_record['request_count']) if isinstance(usage_record['request_count'], Decimal) else usage_record['request_count']
        daily_limit = int(usage_record['daily_limit']) if isinstance(usage_record['daily_limit'], Decimal) else usage_record['daily_limit']
        team = usage_record.get('team', 'desconocido')
        percentage = int((current_usage / daily_limit) * 100) if daily_limit > 0 else 0
        remaining = daily_limit - current_usage
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Aviso de Uso de Bedrock</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
                .header {{ background-color: #F4B860; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
                .usage-bar {{ background-color: #EFE6D5; height: 20px; border-radius: 10px; margin: 10px 0; }}
                .usage-fill {{ background-color: #F4B860; height: 100%; border-radius: 10px; transition: width 0.3s ease; }}
                .stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #F4B860; }}
                .stat-label {{ font-size: 12px; color: #666; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Aviso de Uso de Bedrock</h1>
                    <p>Te estás acercando a tu límite diario</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{display_name}</strong>,</p>
                    
                    <p>Este es un aviso de que te estás acercando a tu límite diario de uso de AWS Bedrock.</p>
                    
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: {percentage}%;"></div>
                    </div>
                    
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value">{current_usage}</div>
                            <div class="stat-label">Solicitudes Usadas</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{remaining}</div>
                            <div class="stat-label">Restantes</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{daily_limit}</div>
                            <div class="stat-label">Límite Diario</div>
                        </div>
                    </div>
                    
                    <p><strong>Estado Actual:</strong></p>
                    <ul>
                        <li>Uso: {current_usage} de {daily_limit} solicitudes ({percentage}%)</li>
                        <li>Equipo: {team}</li>
                        <li>Umbral de aviso: 40 solicitudes</li>
                        <li>Solicitudes restantes: {remaining}</li>
                    </ul>
                    
                    <p><strong>¿Qué sucede después?</strong></p>
                    <p>Si excedes tu límite diario de {daily_limit} solicitudes, tu acceso a AWS Bedrock será bloqueado temporalmente. El bloqueo expirará automáticamente y tu acceso será restaurado a las 00h de mañana.</p>
                    
                    <p>Por favor, regula el uso de este servicio para evitar interrupciones en tu trabajo.</p>
                </div>
                <div class="footer">
                    <p>Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.</p>
                    <p>Enviado desde: {self.gmail_user}</p>
                    <p>Fecha y hora: {self._get_madrid_time()}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_warning_email_text(self, display_name: str, usage_record: Dict[str, Any]) -> str:
        """Generate plain text content for warning email"""
        current_usage = int(usage_record['request_count']) if isinstance(usage_record['request_count'], Decimal) else usage_record['request_count']
        daily_limit = int(usage_record['daily_limit']) if isinstance(usage_record['daily_limit'], Decimal) else usage_record['daily_limit']
        team = usage_record.get('team', 'desconocido')
        percentage = int((current_usage / daily_limit) * 100) if daily_limit > 0 else 0
        remaining = daily_limit - current_usage
        
        return f"""
AVISO DE USO DE BEDROCK

Hola {display_name},

Este es un aviso de que te estás acercando a tu límite diario de uso de AWS Bedrock.

ESTADO ACTUAL:
- Uso: {current_usage} de {daily_limit} solicitudes ({percentage}%)
- Equipo: {team}
- Solicitudes restantes: {remaining}

¿QUÉ SUCEDE DESPUÉS?
Si excedes tu límite diario de {daily_limit} solicitudes, tu acceso a AWS Bedrock será bloqueado temporalmente. El bloqueo expirará automáticamente y tu acceso será restaurado a las 00h de mañana.

Por favor, regula el uso de este servicio para evitar interrupciones en tu trabajo.

---
Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.
Enviado desde: {self.gmail_user}
Fecha y hora: {self._get_madrid_time()}
        """
    
    def _generate_blocking_email_html(self, display_name: str, usage_record: Dict[str, Any], reason: str) -> str:
        """Generate HTML content for blocking email - Light red color"""
        current_usage = int(usage_record['request_count']) if isinstance(usage_record['request_count'], Decimal) else usage_record['request_count']
        daily_limit = int(usage_record['daily_limit']) if isinstance(usage_record['daily_limit'], Decimal) else usage_record['daily_limit']
        team = usage_record.get('team', 'desconocido')
        
        # Get expiration date from usage_record
        expiration_text = "mañana a las 00:00:00 CET"
        if usage_record.get('expires_at'):
            expires_at = usage_record.get('expires_at')
            try:
                # Handle different datetime formats
                if expires_at.endswith('Z'):
                    exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    exp_time = datetime.fromisoformat(expires_at)
                
                # Convert to Madrid timezone for display with proper DST handling
                try:
                    import zoneinfo
                    madrid_tz = zoneinfo.ZoneInfo('Europe/Madrid')
                    exp_time_madrid = exp_time.astimezone(madrid_tz)
                    # Determine if we're in DST (CEST) or standard time (CET)
                    tz_name = 'CEST' if exp_time_madrid.dst() else 'CET'
                    expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
                except ImportError:
                    # Fallback for older Python versions - manually handle DST
                    year = exp_time.year
                    
                    # Calculate DST period (rough approximation)
                    march_last_sunday = 31 - ((5 * year // 4 + 4) % 7)
                    october_last_sunday = 31 - ((5 * year // 4 + 1) % 7)
                    
                    dst_start = datetime(year, 3, march_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                    dst_end = datetime(year, 10, october_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                    
                    is_dst = dst_start <= exp_time < dst_end
                    offset_hours = 2 if is_dst else 1
                    tz_name = 'CEST' if is_dst else 'CET'
                    
                    madrid_tz = timezone(timedelta(hours=offset_hours))
                    exp_time_madrid = exp_time.astimezone(madrid_tz)
                    expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
            except Exception as e:
                logger.warning(f"Error parsing expiration date {expires_at}: {str(e)}")
                expiration_text = "mañana a las 00:00:00 CET"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Acceso a Bedrock Bloqueado</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
                .header {{ background-color: #EC7266; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
                .alert-box {{ background-color: #ffebee; border-left: 4px solid #EC7266; padding: 15px; margin: 20px 0; }}
                .stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #EC7266; }}
                .stat-label {{ font-size: 12px; color: #666; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Acceso a Bedrock Bloqueado</h1>
                    <p>Límite diario excedido</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{display_name}</strong>,</p>
                    
                    <div class="alert-box">
                        <strong>Tu acceso a AWS Bedrock ha sido bloqueado temporalmente.</strong><br>
                        Has excedido tu límite diario de uso y no puedes realizar solicitudes adicionales hasta que expire dicho bloqueo.
                    </div>
                    
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value">{current_usage}</div>
                            <div class="stat-label">Solicitudes Usadas</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{daily_limit}</div>
                            <div class="stat-label">Límite Diario</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">0</div>
                            <div class="stat-label">Restantes</div>
                        </div>
                    </div>
                    
                    <p><strong>Detalles del Bloqueo:</strong></p>
                    <ul>
                        <li>Razón: Límite diario excedido ({current_usage}/{daily_limit} solicitudes)</li>
                        <li>Equipo: {team}</li>
                        <li>El bloqueo expira: {expiration_text}</li>
                    </ul>
                    
                    <p><strong>¿Qué sucede después?</strong></p>
                    <p>Tu acceso será restaurado automáticamente cuando expire el bloqueo. No necesitas realizar ninguna acción adicional.</p>
                    
                    <p><strong>¿Necesitas acceso inmediato?</strong></p>
                    <p>Si tienes una necesidad urgente de negocio, por favor contacta a tu administrador de AWS quien podrá restaurar tu acceso manualmente.</p>
                </div>
                <div class="footer">
                    <p>Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.</p>
                    <p>Enviado desde: {self.gmail_user}</p>
                    <p>Fecha y hora: {self._get_madrid_time()}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_blocking_email_text(self, display_name: str, usage_record: Dict[str, Any], reason: str) -> str:
        """Generate plain text content for blocking email"""
        current_usage = int(usage_record['request_count']) if isinstance(usage_record['request_count'], Decimal) else usage_record['request_count']
        daily_limit = int(usage_record['daily_limit']) if isinstance(usage_record['daily_limit'], Decimal) else usage_record['daily_limit']
        team = usage_record.get('team', 'desconocido')
        
        # Get expiration date from usage_record
        expiration_text = "mañana a las 00:00:00 CET"
        if usage_record.get('expires_at'):
            expires_at = usage_record.get('expires_at')
            try:
                # Handle different datetime formats
                if expires_at.endswith('Z'):
                    exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                else:
                    exp_time = datetime.fromisoformat(expires_at)
                
                # Convert to Madrid timezone for display with proper DST handling
                try:
                    import zoneinfo
                    madrid_tz = zoneinfo.ZoneInfo('Europe/Madrid')
                    exp_time_madrid = exp_time.astimezone(madrid_tz)
                    # Determine if we're in DST (CEST) or standard time (CET)
                    tz_name = 'CEST' if exp_time_madrid.dst() else 'CET'
                    expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
                except ImportError:
                    # Fallback for older Python versions - manually handle DST
                    year = exp_time.year
                    
                    # Calculate DST period (rough approximation)
                    march_last_sunday = 31 - ((5 * year // 4 + 4) % 7)
                    october_last_sunday = 31 - ((5 * year // 4 + 1) % 7)
                    
                    dst_start = datetime(year, 3, march_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                    dst_end = datetime(year, 10, october_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                    
                    is_dst = dst_start <= exp_time < dst_end
                    offset_hours = 2 if is_dst else 1
                    tz_name = 'CEST' if is_dst else 'CET'
                    
                    madrid_tz = timezone(timedelta(hours=offset_hours))
                    exp_time_madrid = exp_time.astimezone(madrid_tz)
                    expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
            except Exception as e:
                logger.warning(f"Error parsing expiration date {expires_at}: {str(e)}")
                expiration_text = "mañana a las 00:00:00 CET"
        
        return f"""
ACCESO A BEDROCK BLOQUEADO

Hola {display_name},

Tu acceso a AWS Bedrock ha sido bloqueado temporalmente.
Has excedido tu límite diario de uso y no puedes realizar solicitudes adicionales hasta que expire dicho bloqueo.

DETALLES DEL BLOQUEO:
- Razón: Límite diario excedido ({current_usage}/{daily_limit} solicitudes)
- Equipo: {team}
- El bloqueo expira: {expiration_text}

¿QUÉ SUCEDE DESPUÉS?
Tu acceso será restaurado automáticamente cuando expire el bloqueo. No necesitas realizar ninguna acción adicional.

¿NECESITAS ACCESO INMEDIATO?
Si tienes una necesidad urgente de negocio, por favor contacta a tu administrador de AWS quien podrá restaurar tu acceso manualmente.

---
Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.
Enviado desde: {self.gmail_user}
Fecha y hora: {self._get_madrid_time()}
        """
    
    def _generate_unblocking_email_html(self, user_id: str, reason: str) -> str:
        """Generate HTML content for unblocking email - Green color"""
        reason_text = {
            'daily_reset': 'Tu período de bloqueo ha expirado',
            'manual_admin_unblock': 'Un administrador ha restaurado tu acceso manualmente',
            'automatic_expiration': 'Tu período de bloqueo ha expirado'
        }.get(reason, 'Tu acceso ha sido restaurado')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Acceso a Bedrock Restaurado</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
                .header {{ background-color: #9CD286; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
                .success-box {{ background-color: #E8F5E8; border-left: 4px solid #9CD286; padding: 15px; margin: 20px 0; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Acceso a Bedrock Restaurado</h1>
                    <p>Ya puedes usar Bedrock nuevamente</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{user_id}</strong>,</p>
                    
                    <div class="success-box">
                        <strong>¡Buenas noticias!</strong> Tu acceso a AWS Bedrock ha sido restaurado.<br>
                        {reason_text}.
                    </div>
                    
                    <p><strong>Esto significa que:</strong></p>
                    <ul>
                        <li>Ya puedes realizar llamadas a la API de AWS Bedrock nuevamente</li>
                        <li>Tu contador de uso diario ha sido reiniciado</li>
                        <li>Se aplican los límites de uso normales</li>
                    </ul>
                    
                    <p><strong>De aquí en adelante:</strong></p>
                    <p>Por favor, regula el uso de este servicio para evitar futuros bloqueos. Recibirás un aviso cuando te acerques a tu límite diario.</p>
                    
                    <p>¡Gracias por tu colaboración!</p>
                </div>
                <div class="footer">
                    <p>Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.</p>
                    <p>Enviado desde: {self.gmail_user}</p>
                    <p>Fecha y hora: {self._get_madrid_time()}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_unblocking_email_text(self, user_id: str, reason: str) -> str:
        """Generate plain text content for unblocking email"""
        reason_text = {
            'daily_reset': 'Tu período de bloqueo ha expirado',
            'manual_admin_unblock': 'Un administrador ha restaurado tu acceso manualmente',
            'automatic_expiration': 'Tu período de bloqueo ha expirado'
        }.get(reason, 'Tu acceso ha sido restaurado')
        
        return f"""
ACCESO A BEDROCK RESTAURADO

Hola {user_id},

¡Buenas noticias! Tu acceso a AWS Bedrock ha sido restaurado.
{reason_text}.

ESTO SIGNIFICA QUE:
- Ya puedes realizar llamadas a la API de AWS Bedrock nuevamente
- Tu contador de uso diario ha sido reiniciado
- Se aplican los límites de uso normales

DE AQUÍ EN ADELANTE:
Por favor, regula el uso de este servicio para evitar futuros bloqueos. Recibirás un aviso cuando te acerques a tu límite diario.

¡Gracias por tu colaboración!

---
Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.
Enviado desde: {self.gmail_user}
Fecha y hora: {self._get_madrid_time()}
        """
    
    def _generate_admin_blocking_email_html(self, display_name: str, admin_user: str, reason: str, usage_record: Dict[str, Any] = None) -> str:
        """Generate HTML content for admin blocking email - Light red color"""
        # Get expiration date from usage_record
        expiration_text = "Indefinida (hasta que un administrador lo restaure)"
        if usage_record and usage_record.get('expires_at'):
            expires_at = usage_record.get('expires_at')
            if expires_at and expires_at != 'Indefinite':
                try:
                    # Handle different datetime formats
                    if expires_at.endswith('Z'):
                        exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    else:
                        exp_time = datetime.fromisoformat(expires_at)
                    
                    # Convert to Madrid timezone for display with proper DST handling
                    try:
                        import zoneinfo
                        madrid_tz = zoneinfo.ZoneInfo('Europe/Madrid')
                        exp_time_madrid = exp_time.astimezone(madrid_tz)
                        # Determine if we're in DST (CEST) or standard time (CET)
                        tz_name = 'CEST' if exp_time_madrid.dst() else 'CET'
                        expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
                    except ImportError:
                        # Fallback for older Python versions - manually handle DST
                        year = exp_time.year
                        
                        # Calculate DST period (rough approximation)
                        march_last_sunday = 31 - ((5 * year // 4 + 4) % 7)
                        october_last_sunday = 31 - ((5 * year // 4 + 1) % 7)
                        
                        dst_start = datetime(year, 3, march_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                        dst_end = datetime(year, 10, october_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                        
                        is_dst = dst_start <= exp_time < dst_end
                        offset_hours = 2 if is_dst else 1
                        tz_name = 'CEST' if is_dst else 'CET'
                        
                        madrid_tz = timezone(timedelta(hours=offset_hours))
                        exp_time_madrid = exp_time.astimezone(madrid_tz)
                        expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
                except Exception as e:
                    logger.warning(f"Error parsing expiration date {expires_at}: {str(e)}")
                    expiration_text = "Indefinida (hasta que un administrador lo restaure)"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Acceso a Bedrock Bloqueado por Administrador</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
                .header {{ background-color: #EC7266; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
                .alert-box {{ background-color: #ffebee; border-left: 4px solid #EC7266; padding: 15px; margin: 20px 0; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Acceso a Bedrock Bloqueado</h1>
                    <p>Bloqueado por Administrador</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{display_name}</strong>,</p>
                    
                    <div class="alert-box">
                        <strong>Tu acceso a AWS Bedrock ha sido bloqueado por un administrador.</strong><br>
                        Un administrador de AWS ha bloqueado tu cuenta intencionalmente.
                    </div>
                    
                    <p><strong>Detalles del Bloqueo:</strong></p>
                    <ul>
                        <li>Razón: {reason}</li>
                        <li>Bloqueado por: {admin_user}</li>
                        <li>Fecha del bloqueo: {self._get_madrid_time()}</li>
                        <li>Fecha prevista de desbloqueo: {expiration_text}</li>
                    </ul>
                    
                    <p><strong>¿Qué sucede después?</strong></p>
                    <p>Tu acceso permanecerá bloqueado hasta que un administrador lo restaure manualmente. Este bloqueo no se restaurará automáticamente.</p>
                    
                    <p><strong>¿Necesitas más información?</strong></p>
                    <p>Si tienes preguntas sobre este bloqueo, por favor contacta a tu administrador de AWS.</p>
                </div>
                <div class="footer">
                    <p>Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.</p>
                    <p>Enviado desde: {self.gmail_user}</p>
                    <p>Fecha y hora: {self._get_madrid_time()}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_admin_blocking_email_text(self, display_name: str, admin_user: str, reason: str, usage_record: Dict[str, Any] = None) -> str:
        """Generate plain text content for admin blocking email"""
        # Get expiration date from usage_record
        expiration_text = "Indefinida (hasta que un administrador lo restaure)"
        if usage_record and usage_record.get('expires_at'):
            expires_at = usage_record.get('expires_at')
            if expires_at and expires_at != 'Indefinite':
                try:
                    # Handle different datetime formats
                    if expires_at.endswith('Z'):
                        exp_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    else:
                        exp_time = datetime.fromisoformat(expires_at)
                    
                    # Convert to Madrid timezone for display with proper DST handling
                    try:
                        import zoneinfo
                        madrid_tz = zoneinfo.ZoneInfo('Europe/Madrid')
                        exp_time_madrid = exp_time.astimezone(madrid_tz)
                        # Determine if we're in DST (CEST) or standard time (CET)
                        tz_name = 'CEST' if exp_time_madrid.dst() else 'CET'
                        expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
                    except ImportError:
                        # Fallback for older Python versions - manually handle DST
                        year = exp_time.year
                        
                        # Calculate DST period (rough approximation)
                        march_last_sunday = 31 - ((5 * year // 4 + 4) % 7)
                        october_last_sunday = 31 - ((5 * year // 4 + 1) % 7)
                        
                        dst_start = datetime(year, 3, march_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                        dst_end = datetime(year, 10, october_last_sunday, 1, 0, 0, tzinfo=timezone.utc)
                        
                        is_dst = dst_start <= exp_time < dst_end
                        offset_hours = 2 if is_dst else 1
                        tz_name = 'CEST' if is_dst else 'CET'
                        
                        madrid_tz = timezone(timedelta(hours=offset_hours))
                        exp_time_madrid = exp_time.astimezone(madrid_tz)
                        expiration_text = exp_time_madrid.strftime(f'%Y-%m-%d a las %H:%M:%S {tz_name}')
                except Exception as e:
                    logger.warning(f"Error parsing expiration date {expires_at}: {str(e)}")
                    expiration_text = "Indefinida (hasta que un administrador lo restaure)"
        
        return f"""
ACCESO A BEDROCK BLOQUEADO POR ADMINISTRADOR

Hola {display_name},

Tu acceso a AWS Bedrock ha sido bloqueado por un administrador.
Un administrador de AWS ha bloqueado tu cuenta intencionalmente o manualmente.

DETALLES DEL BLOQUEO:
- Razón: {reason}
- Bloqueado por: {admin_user}
- Fecha del bloqueo: {self._get_madrid_time()}
- Fecha prevista de desbloqueo: {expiration_text}

¿QUÉ SUCEDE DESPUÉS?
Tu acceso permanecerá bloqueado hasta que un administrador lo restaure manualmente. Este bloqueo no se restaurará automáticamente con el reinicio diario.

¿NECESITAS MÁS INFORMACIÓN?
Si tienes preguntas sobre este bloqueo, por favor contacta a tu administrador de AWS o al equipo de soporte técnico.

---
Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.
Enviado desde: {self.gmail_user}
Fecha y hora: {self._get_madrid_time()}
        """
    
    def _generate_admin_unblocking_email_html(self, user_id: str, admin_user: str, reason: str) -> str:
        """Generate HTML content for admin unblocking email - Green color"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Acceso a Bedrock Restaurado por Administrador</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
                .header {{ background-color: #9CD286; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: white; padding: 20px; border-radius: 0 0 5px 5px; }}
                .success-box {{ background-color: #E8F5E8; border-left: 4px solid #9CD286; padding: 15px; margin: 20px 0; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Acceso a Bedrock Restaurado</h1>
                    <p>Restaurado por Administrador</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{user_id}</strong>,</p>
                    
                    <div class="success-box">
                        <strong>¡Buenas noticias!</strong> Tu acceso a AWS Bedrock ha sido restaurado por un administrador.<br>
                        Un administrador ha desbloqueado tu cuenta manualmente, después de alcanzar el límite diario (tienes protección administrativa).
                    </div>
                    
                    <p><strong>Detalles de la Restauración:</strong></p>
                    <ul>
                        <li>Restaurado por: {admin_user}</li>
                        <li>Fecha de restauración: {self._get_madrid_time()}</li>
                        <li>Tipo: Desbloqueo administrativo manual</li>
                        <li>Protección: Tienes protección administrativa hasta mañana</li>
                    </ul>
                    
                    <p><strong>Esto significa que:</strong></p>
                    <ul>
                        <li>Ya puedes realizar llamadas a la API de AWS Bedrock nuevamente</li>
                        <li>Tienes protección administrativa contra bloqueos automáticos hasta mañana</li>
                        <li>Tu contador de uso diario se reiniciará normalmente mañana</li>
                    </ul>
                    
                    <p><strong>De aquí en adelante:</strong></p>
                    <p>Aunque tienes protección administrativa temporal, por favor regula el uso de este servicio responsablemente.</p>
                    
                    <p>¡Gracias por tu colaboración!</p>
                </div>
                <div class="footer">
                    <p>Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.</p>
                    <p>Enviado desde: {self.gmail_user}</p>
                    <p>Fecha y hora: {self._get_madrid_time()}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _generate_admin_unblocking_email_text(self, user_id: str, admin_user: str, reason: str) -> str:
        """Generate plain text content for admin unblocking email"""
        return f"""
ACCESO A BEDROCK RESTAURADO POR ADMINISTRADOR

Hola {user_id},

¡Buenas noticias! Tu acceso a AWS Bedrock ha sido restaurado por un administrador.
Un administrador ha desbloqueado tu cuenta manualmente, después de alcanzar el límite diario.

DETALLES DE LA RESTAURACIÓN:
- Fecha de restauración: {self._get_madrid_time()}
- Tipo: Desbloqueo administrativo manual

ESTO SIGNIFICA QUE:
- Ya puedes realizar llamadas a la API de AWS Bedrock nuevamente
- Tienes protección administrativa contra bloqueos automáticos hasta mañana a las 00h
- Tu contador de uso diario se reiniciará normalmente mañana

DE AQUÍ EN ADELANTE:
Por favor, regula el uso de este servicio para evitar futuros bloqueos. Recibirás un aviso cuando te acerques a tu límite diario.

¡Gracias por tu colaboración!

---
Esta es una notificación automática del Sistema de Control de Uso de AWS Bedrock.
Enviado desde: {self.gmail_user}
Fecha y hora: {self._get_madrid_time()}
        """


# Factory function to create email service instance
def create_email_service(credentials_file: str = None) -> EnhancedEmailNotificationService:
    """
    Factory function to create email service instance
    
    Args:
        credentials_file: Path to credentials file
        
    Returns:
        EnhancedEmailNotificationService instance
    """
    return EnhancedEmailNotificationService(credentials_file)


# For testing purposes
if __name__ == "__main__":
    # Test the email service
    email_service = create_email_service()
    
    # Test usage record
    test_usage_record = {
        'request_count': 42,
        'daily_limit': 50,
        'team': 'team_sap_group'
    }
    
    print("Email service initialized successfully")
    print(f"SMTP Server: {email_service.smtp_server}")
    print(f"SMTP Port: {email_service.smtp_port}")
    print(f"Gmail User: {email_service.gmail_user}")
    
    # Note: Actual email sending would require valid user with Email tag in IAM
    print("\nEmail service ready for integration with Lambda functions")
