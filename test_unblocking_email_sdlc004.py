#!/usr/bin/env python3
"""
Test unitario para verificar el envío de email de desbloqueo automático
para el usuario sdlc_004 usando el servicio de email mejorado.

Este script invoca directamente la Lambda bedrock-email-service para
verificar que el email con formato HTML mejorado se envía correctamente.
"""

import json
import boto3
from datetime import datetime

# Cliente Lambda
lambda_client = boto3.client('lambda', region_name='eu-west-1')

def test_unblocking_email_for_sdlc004():
    """
    Prueba unitaria: Enviar email de desbloqueo automático para sdlc_004
    """
    print("=" * 80)
    print("PRUEBA UNITARIA: Email de Desbloqueo Automático para sdlc_004")
    print("=" * 80)
    print()
    
    # Payload para invocar la Lambda de email service
    # Simula un desbloqueo automático del sistema
    email_payload = {
        'action': 'send_unblocking_email',
        'user_id': 'sdlc_004',
        'reason': 'Automatic unblock'
    }
    
    print("📧 Invocando Lambda bedrock-email-service...")
    print(f"   Payload: {json.dumps(email_payload, indent=2)}")
    print()
    
    try:
        # Invocar la Lambda de email service
        response = lambda_client.invoke(
            FunctionName='bedrock-email-service',
            InvocationType='RequestResponse',
            Payload=json.dumps(email_payload)
        )
        
        # Leer la respuesta
        response_payload = json.loads(response['Payload'].read())
        
        print("✅ Respuesta de la Lambda:")
        print(json.dumps(response_payload, indent=2))
        print()
        
        # Verificar el resultado
        if response_payload.get('statusCode') == 200:
            print("=" * 80)
            print("✅ PRUEBA EXITOSA")
            print("=" * 80)
            print()
            print("El email de desbloqueo automático ha sido enviado correctamente.")
            print("Por favor, verifica el buzón del usuario sdlc_004 para confirmar")
            print("que el email tiene el formato HTML mejorado.")
            print()
            print("Detalles esperados del email:")
            print("  - Asunto: ✅ AWS Bedrock Access Restored - sdlc_004")
            print("  - Formato: HTML con colores y estilos profesionales")
            print("  - Color: Verde (indicando restauración exitosa)")
            print("  - Contenido: Mensaje en español con detalles del desbloqueo")
            print()
            return True
        else:
            print("=" * 80)
            print("❌ PRUEBA FALLIDA")
            print("=" * 80)
            print()
            print(f"Error al enviar el email: {response_payload.get('body', 'Unknown error')}")
            print()
            return False
            
    except Exception as e:
        print("=" * 80)
        print("❌ ERROR EN LA PRUEBA")
        print("=" * 80)
        print()
        print(f"Excepción: {str(e)}")
        print()
        return False

def test_admin_unblocking_email_for_sdlc004():
    """
    Prueba adicional: Email de desbloqueo manual (admin) para comparación
    """
    print("=" * 80)
    print("PRUEBA ADICIONAL: Email de Desbloqueo Manual (Admin) para sdlc_004")
    print("=" * 80)
    print()
    
    # Payload para desbloqueo manual por admin
    email_payload = {
        'action': 'send_admin_unblocking_email',
        'user_id': 'sdlc_004',
        'performed_by': 'dashboard_admin',
        'reason': 'Manual unblock for testing'
    }
    
    print("📧 Invocando Lambda bedrock-email-service...")
    print(f"   Payload: {json.dumps(email_payload, indent=2)}")
    print()
    
    try:
        response = lambda_client.invoke(
            FunctionName='bedrock-email-service',
            InvocationType='RequestResponse',
            Payload=json.dumps(email_payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        print("✅ Respuesta de la Lambda:")
        print(json.dumps(response_payload, indent=2))
        print()
        
        if response_payload.get('statusCode') == 200:
            print("✅ Email de desbloqueo manual enviado correctamente")
            print()
            return True
        else:
            print(f"❌ Error: {response_payload.get('body', 'Unknown error')}")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        print()
        return False

if __name__ == "__main__":
    print()
    print("🧪 INICIANDO PRUEBAS UNITARIAS DE EMAIL")
    print(f"⏰ Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar prueba principal
    test1_result = test_unblocking_email_for_sdlc004()
    
    print()
    print("-" * 80)
    print()
    
    # Ejecutar prueba adicional (opcional)
    print("¿Deseas ejecutar también la prueba de desbloqueo manual? (s/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 's':
            print()
            test2_result = test_admin_unblocking_email_for_sdlc004()
    except:
        pass
    
    print()
    print("=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)
    print()
    print(f"Prueba de desbloqueo automático: {'✅ EXITOSA' if test1_result else '❌ FALLIDA'}")
    print()
    print("NOTA: Verifica el buzón de correo del usuario sdlc_004 para confirmar")
    print("      que el email recibido tiene el formato HTML mejorado.")
    print()
