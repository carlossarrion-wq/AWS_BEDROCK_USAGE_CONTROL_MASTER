#!/usr/bin/env python3
"""
Script para ejecutar los cambios de esquema de bloqueo automático en la base de datos MySQL
"""

import pymysql
import sys
import os
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'BedrockUsage2024!',
    'database': 'bedrock_usage',
    'charset': 'utf8mb4',
    'autocommit': False
}

def log_message(message, level="INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def connect_to_database():
    """Conectar a la base de datos MySQL"""
    try:
        log_message("Conectando a la base de datos...")
        connection = pymysql.connect(**DB_CONFIG)
        log_message("✅ Conexión establecida exitosamente")
        return connection
    except Exception as e:
        log_message(f"❌ Error conectando a la base de datos: {str(e)}", "ERROR")
        return None

def execute_sql_file(connection, file_path):
    """Ejecutar archivo SQL línea por línea"""
    try:
        log_message(f"Ejecutando archivo SQL: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Dividir por statements SQL (usando DELIMITER como separador)
        statements = []
        current_statement = ""
        delimiter = ";"
        
        lines = sql_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Cambiar delimiter
            if line.startswith('DELIMITER'):
                delimiter = line.split()[1]
                i += 1
                continue
            
            # Agregar línea al statement actual
            if line and not line.startswith('--'):
                current_statement += line + "\n"
            
            # Si encontramos el delimiter, ejecutar el statement
            if line.endswith(delimiter) and delimiter != ";":
                # Para procedimientos almacenados
                if current_statement.strip():
                    statements.append(current_statement.replace(delimiter, ""))
                current_statement = ""
            elif line.endswith(";") and delimiter == ";":
                # Para statements normales
                if current_statement.strip():
                    statements.append(current_statement)
                current_statement = ""
            
            i += 1
        
        # Agregar último statement si existe
        if current_statement.strip():
            statements.append(current_statement)
        
        # Ejecutar cada statement
        cursor = connection.cursor()
        executed_count = 0
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
                
            try:
                # Log para statements importantes
                if any(keyword in statement.upper() for keyword in ['ALTER TABLE', 'CREATE PROCEDURE', 'CREATE VIEW', 'DROP PROCEDURE']):
                    log_message(f"Ejecutando: {statement[:100]}...")
                
                cursor.execute(statement)
                executed_count += 1
                
                # Commit cada cierto número de statements
                if executed_count % 10 == 0:
                    connection.commit()
                    log_message(f"✅ Ejecutados {executed_count} statements")
                    
            except Exception as e:
                error_msg = str(e)
                # Ignorar errores esperados (campos que ya existen, etc.)
                if any(ignore in error_msg.lower() for ignore in [
                    'duplicate column name',
                    'already exists',
                    'duplicate key name',
                    'campo', 'ya existe'
                ]):
                    log_message(f"⚠️  Advertencia (esperada): {error_msg}")
                    continue
                else:
                    log_message(f"❌ Error ejecutando statement {i+1}: {error_msg}", "ERROR")
                    log_message(f"Statement: {statement[:200]}...", "ERROR")
                    raise
        
        # Commit final
        connection.commit()
        log_message(f"✅ Archivo SQL ejecutado exitosamente. Total statements: {executed_count}")
        
    except Exception as e:
        log_message(f"❌ Error ejecutando archivo SQL: {str(e)}", "ERROR")
        connection.rollback()
        raise

def verify_changes(connection):
    """Verificar que los cambios se aplicaron correctamente"""
    try:
        log_message("Verificando cambios aplicados...")
        cursor = connection.cursor()
        
        # Verificar tabla user_limits
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'bedrock_usage' 
            AND TABLE_NAME = 'user_limits' 
            AND COLUMN_NAME = 'administrative_safe'
        """)
        result = cursor.fetchone()
        if result['count'] > 0:
            log_message("✅ Campo 'administrative_safe' añadido a user_limits")
        else:
            log_message("❌ Campo 'administrative_safe' NO encontrado en user_limits", "ERROR")
        
        # Verificar tabla user_blocking_status
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'bedrock_usage' 
            AND TABLE_NAME = 'user_blocking_status' 
            AND COLUMN_NAME = 'requests_at_blocking'
        """)
        result = cursor.fetchone()
        if result['count'] > 0:
            log_message("✅ Campo 'requests_at_blocking' añadido a user_blocking_status")
        else:
            log_message("❌ Campo 'requests_at_blocking' NO encontrado en user_blocking_status", "ERROR")
        
        # Verificar tabla blocking_audit_log
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'bedrock_usage' 
            AND TABLE_NAME = 'blocking_audit_log' 
            AND COLUMN_NAME = 'operation_type'
        """)
        result = cursor.fetchone()
        if result['count'] > 0:
            log_message("✅ Campo 'operation_type' encontrado en blocking_audit_log")
        else:
            log_message("❌ Campo 'operation_type' NO encontrado en blocking_audit_log", "ERROR")
        
        # Verificar stored procedures
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.ROUTINES 
            WHERE ROUTINE_SCHEMA = 'bedrock_usage' 
            AND ROUTINE_NAME = 'CheckUserBlockingStatus'
        """)
        result = cursor.fetchone()
        if result['count'] > 0:
            log_message("✅ Stored procedure 'CheckUserBlockingStatus' creado")
        else:
            log_message("❌ Stored procedure 'CheckUserBlockingStatus' NO encontrado", "ERROR")
        
        log_message("✅ Verificación completada")
        
    except Exception as e:
        log_message(f"❌ Error verificando cambios: {str(e)}", "ERROR")

def main():
    """Función principal"""
    log_message("🚀 Iniciando aplicación de cambios de esquema de bloqueo automático")
    
    # Conectar a la base de datos
    connection = connect_to_database()
    if not connection:
        sys.exit(1)
    
    try:
        # Ejecutar el DDL
        ddl_file = "migration/15_adapt_existing_blocking_schema.sql"
        if not os.path.exists(ddl_file):
            log_message(f"❌ Archivo DDL no encontrado: {ddl_file}", "ERROR")
            sys.exit(1)
        
        execute_sql_file(connection, ddl_file)
        
        # Verificar cambios
        verify_changes(connection)
        
        log_message("🎉 ¡Cambios de esquema aplicados exitosamente!")
        
    except Exception as e:
        log_message(f"❌ Error durante la ejecución: {str(e)}", "ERROR")
        sys.exit(1)
    
    finally:
        if connection:
            connection.close()
            log_message("Conexión cerrada")

if __name__ == "__main__":
    main()
