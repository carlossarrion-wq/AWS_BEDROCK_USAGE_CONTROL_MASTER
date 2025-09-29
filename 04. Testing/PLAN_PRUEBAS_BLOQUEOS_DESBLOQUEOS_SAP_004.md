# Plan de Pruebas Unitarias - Bloqueos y Desbloqueos
## Usuario de Prueba: sap_004

**Fecha:** 23 de Septiembre, 2025  
**Sistema:** AWS Bedrock Usage Control  
**Objetivo:** Validar todos los escenarios de bloqueo y desbloqueo tanto manual como automático

---

## 📋 Resumen Ejecutivo

Este plan de pruebas unitarias está diseñado para validar exhaustivamente todos los escenarios de bloqueo y desbloqueo del sistema AWS Bedrock Usage Control utilizando el usuario de prueba `sap_004`. Se cubrirán tanto los flujos automáticos como los manuales, incluyendo casos edge y escenarios de error.

## 🎯 Objetivos de las Pruebas

1. **Validar bloqueos automáticos** por límites diarios y mensuales
2. **Validar desbloqueos automáticos** por expiración de tiempo
3. **Validar bloqueos manuales** desde dashboard administrativo
4. **Validar desbloqueos manuales** desde dashboard administrativo
5. **Verificar protección administrativa** (`administrative_safe`)
6. **Validar manejo de timezone** (CET/Europe/Madrid)
7. **Verificar integridad de datos** en base de datos
8. **Validar notificaciones por email**
9. **Verificar políticas IAM** de bloqueo/desbloqueo

## 🧪 Escenarios de Prueba

### 1. BLOQUEO AUTOMÁTICO - Límite Diario

#### Escenario 1.1: Bloqueo por Límite Diario Excedido
- **Usuario:** sap_004
- **Límite diario:** 350 requests
- **Requests actuales:** 351 (excede límite)
- **Resultado esperado:** Usuario bloqueado hasta 00:00 CET del día siguiente

#### Escenario 1.2: Bloqueo por Límite Mensual Excedido
- **Usuario:** sap_004
- **Límite mensual:** 5000 requests
- **Requests actuales:** 5001 (excede límite)
- **Resultado esperado:** Usuario bloqueado hasta 00:00 CET del día siguiente

#### Escenario 1.3: Usuario con Protección Administrativa
- **Usuario:** sap_004
- **administrative_safe:** 'Y'
- **Requests actuales:** 400 (excede límite diario)
- **Resultado esperado:** NO se bloquea (protección activa)

### 2. DESBLOQUEO AUTOMÁTICO - Por Expiración

#### Escenario 2.1: Desbloqueo por Expiración de Tiempo
- **Usuario:** sap_004
- **Estado inicial:** Bloqueado
- **blocked_until:** Fecha pasada (ej: ayer 23:59)
- **Resultado esperado:** Usuario desbloqueado automáticamente

#### Escenario 2.2: Usuario Bloqueado Sin Expiración
- **Usuario:** sap_004
- **Estado inicial:** Bloqueado
- **blocked_until:** NULL (bloqueo indefinido)
- **Resultado esperado:** Usuario permanece bloqueado

#### Escenario 2.3: Usuario Bloqueado con Expiración Futura
- **Usuario:** sap_004
- **Estado inicial:** Bloqueado
- **blocked_until:** Fecha futura (ej: mañana 00:00)
- **Resultado esperado:** Usuario permanece bloqueado

### 3. BLOQUEO MANUAL - Dashboard Administrativo

#### Escenario 3.1: Bloqueo Manual por Administrador
- **Usuario:** sap_004
- **Acción:** API event con action='block'
- **Ejecutado por:** admin-user
- **Razón:** "Bloqueo administrativo de prueba"
- **Resultado esperado:** Usuario bloqueado por 24 horas exactas

#### Escenario 3.2: Bloqueo Manual de Usuario Ya Bloqueado
- **Usuario:** sap_004
- **Estado inicial:** Ya bloqueado automáticamente
- **Acción:** Bloqueo manual adicional
- **Resultado esperado:** Actualización de razón y tiempo de bloqueo

#### Escenario 3.3: Bloqueo Manual con Protección Administrativa
- **Usuario:** sap_004
- **administrative_safe:** 'Y'
- **Acción:** Bloqueo manual
- **Resultado esperado:** Bloqueo exitoso (protección NO aplica a manuales)

### 4. DESBLOQUEO MANUAL - Dashboard Administrativo

#### Escenario 4.1: Desbloqueo Manual por Administrador
- **Usuario:** sap_004
- **Estado inicial:** Bloqueado
- **Acción:** API event con action='unblock'
- **Ejecutado por:** admin-user
- **Resultado esperado:** Usuario desbloqueado + administrative_safe='Y'

#### Escenario 4.2: Desbloqueo Manual de Usuario No Bloqueado
- **Usuario:** sap_004
- **Estado inicial:** No bloqueado
- **Acción:** Desbloqueo manual
- **Resultado esperado:** Operación exitosa, administrative_safe='Y'

#### Escenario 4.3: Desbloqueo Manual con Activación de Protección
- **Usuario:** sap_004
- **Estado inicial:** Bloqueado
- **Acción:** Desbloqueo manual
- **Verificación:** administrative_safe debe cambiar a 'Y'
- **Resultado esperado:** Protección contra futuros bloqueos automáticos

### 5. RESET DIARIO - Función Programada

#### Escenario 5.1: Reset Diario con Usuarios Expirados
- **Usuario:** sap_004
- **Estado inicial:** Bloqueado con blocked_until expirado
- **Acción:** Ejecución de bedrock-daily-reset
- **Resultado esperado:** Usuario desbloqueado automáticamente

#### Escenario 5.2: Remoción de Protección Administrativa
- **Usuario:** sap_004
- **Estado inicial:** administrative_safe='Y'
- **Acción:** Reset diario
- **Resultado esperado:** administrative_safe cambia a 'N'

### 6. CASOS EDGE Y MANEJO DE ERRORES

#### Escenario 6.1: Fallo de Conexión a Base de Datos
- **Usuario:** sap_004
- **Condición:** Error de conexión MySQL
- **Resultado esperado:** Error manejado gracefully, notificación SNS

#### Escenario 6.2: Fallo de Política IAM
- **Usuario:** sap_004
- **Condición:** Error al crear/modificar política IAM
- **Resultado esperado:** Operación registrada como fallida en audit log

#### Escenario 6.3: Fallo de Servicio de Email
- **Usuario:** sap_004
- **Condición:** Error en servicio de notificaciones
- **Resultado esperado:** Fallback a Gmail, operación continúa

## 🔧 Configuración de Datos de Prueba

### Datos Iniciales para sap_004

```sql
-- Configuración inicial del usuario sap_004
INSERT INTO user_limits (user_id, team, person, daily_request_limit, monthly_request_limit, administrative_safe, created_at) 
VALUES ('sap_004', 'sdlc_team', 'SAP Test User 004', 350, 5000, 'N', NOW())
ON DUPLICATE KEY UPDATE
    team = VALUES(team),
    person = VALUES(person),
    daily_request_limit = VALUES(daily_request_limit),
    monthly_request_limit = VALUES(monthly_request_limit),
    administrative_safe = 'N',
    updated_at = NOW();

-- Estado inicial de bloqueo (limpio)
DELETE FROM user_blocking_status WHERE user_id = 'sap_004';

-- Limpiar logs de auditoría previos
DELETE FROM blocking_audit_log WHERE user_id = 'sap_004';
```

### Estados de Prueba Específicos

#### Estado 1: Usuario Normal Activo
```sql
UPDATE user_limits SET administrative_safe = 'N' WHERE user_id = 'sap_004';
DELETE FROM user_blocking_status WHERE user_id = 'sap_004';
```

#### Estado 2: Usuario Bloqueado Automáticamente
```sql
INSERT INTO user_blocking_status (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, created_at)
VALUES ('sap_004', 'Y', 'Daily limit exceeded', NOW(), DATE_ADD(CURDATE(), INTERVAL 1 DAY), NOW())
ON DUPLICATE KEY UPDATE
    is_blocked = 'Y',
    blocked_reason = 'Daily limit exceeded',
    blocked_at = NOW(),
    blocked_until = DATE_ADD(CURDATE(), INTERVAL 1 DAY),
    updated_at = NOW();
```

#### Estado 3: Usuario con Protección Administrativa
```sql
UPDATE user_limits SET administrative_safe = 'Y' WHERE user_id = 'sap_004';
DELETE FROM user_blocking_status WHERE user_id = 'sap_004';
```

#### Estado 4: Usuario Bloqueado Expirado
```sql
INSERT INTO user_blocking_status (user_id, is_blocked, blocked_reason, blocked_at, blocked_until, created_at)
VALUES ('sap_004', 'Y', 'Daily limit exceeded', DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 HOUR), NOW())
ON DUPLICATE KEY UPDATE
    is_blocked = 'Y',
    blocked_reason = 'Daily limit exceeded',
    blocked_at = DATE_SUB(NOW(), INTERVAL 1 DAY),
    blocked_until = DATE_SUB(NOW(), INTERVAL 1 HOUR),
    updated_at = NOW();
```

## 🧪 Casos de Prueba Detallados

### Caso de Prueba 1: Bloqueo Automático por Límite Diario

```python
def test_automatic_blocking_daily_limit_sap_004():
    """
    Prueba bloqueo automático cuando sap_004 excede límite diario
    """
    # Preparar datos
    setup_user_normal_active('sap_004')
    simulate_daily_usage('sap_004', 351)  # Excede límite de 350
    
    # Simular evento CloudTrail
    cloudtrail_event = create_bedrock_event('sap_004', 'InvokeModel')
    
    # Ejecutar función
    result = lambda_handler(cloudtrail_event, {})
    
    # Verificaciones
    assert result['statusCode'] == 200
    assert_user_is_blocked('sap_004')
    assert_blocked_until_tomorrow_midnight('sap_004')
    assert_audit_log_entry('sap_004', 'BLOCK', 'Daily limit exceeded')
    assert_iam_policy_has_deny('sap_004')
    assert_email_notification_sent('sap_004', 'blocking')
```

### Caso de Prueba 2: Desbloqueo Automático por Expiración

```python
def test_automatic_unblocking_expired_sap_004():
    """
    Prueba desbloqueo automático cuando expira el bloqueo de sap_004
    """
    # Preparar datos
    setup_user_blocked_expired('sap_004')
    
    # Simular evento CloudTrail (cualquier petición)
    cloudtrail_event = create_bedrock_event('sap_004', 'InvokeModel')
    
    # Ejecutar función
    result = lambda_handler(cloudtrail_event, {})
    
    # Verificaciones
    assert result['statusCode'] == 200
    assert_user_is_not_blocked('sap_004')
    assert_blocked_until_is_null('sap_004')
    assert_audit_log_entry('sap_004', 'UNBLOCK', 'Automatic unblock')
    assert_iam_policy_no_deny('sap_004')
    assert_email_notification_sent('sap_004', 'unblocking')
```

### Caso de Prueba 3: Bloqueo Manual por Administrador

```python
def test_manual_blocking_by_admin_sap_004():
    """
    Prueba bloqueo manual de sap_004 por administrador
    """
    # Preparar datos
    setup_user_normal_active('sap_004')
    
    # Crear evento API manual
    api_event = {
        'action': 'block',
        'user_id': 'sap_004',
        'reason': 'Manual admin block for testing',
        'performed_by': 'admin-test-user'
    }
    
    # Ejecutar función
    result = lambda_handler(api_event, {})
    
    # Verificaciones
    assert result['statusCode'] == 200
    assert_user_is_blocked('sap_004')
    assert_blocked_until_24_hours_from_now('sap_004')
    assert_audit_log_entry('sap_004', 'BLOCK', 'Manual admin block for testing', 'admin-test-user')
    assert_iam_policy_has_deny('sap_004')
    assert_enhanced_email_notification_sent('sap_004', 'blocking', 'admin-test-user')
```

### Caso de Prueba 4: Desbloqueo Manual con Protección

```python
def test_manual_unblocking_with_protection_sap_004():
    """
    Prueba desbloqueo manual de sap_004 con activación de protección administrativa
    """
    # Preparar datos
    setup_user_blocked('sap_004')
    
    # Crear evento API manual
    api_event = {
        'action': 'unblock',
        'user_id': 'sap_004',
        'reason': 'Manual admin unblock for testing',
        'performed_by': 'admin-test-user'
    }
    
    # Ejecutar función
    result = lambda_handler(api_event, {})
    
    # Verificaciones
    assert result['statusCode'] == 200
    assert_user_is_not_blocked('sap_004')
    assert_administrative_safe_is_active('sap_004')
    assert_audit_log_entry('sap_004', 'UNBLOCK', 'Manual admin unblock for testing', 'admin-test-user')
    assert_iam_policy_no_deny('sap_004')
    assert_enhanced_email_notification_sent('sap_004', 'unblocking', 'admin-test-user')
```

### Caso de Prueba 5: Protección Administrativa Previene Bloqueo

```python
def test_administrative_protection_prevents_blocking_sap_004():
    """
    Prueba que la protección administrativa previene bloqueo automático de sap_004
    """
    # Preparar datos
    setup_user_with_admin_protection('sap_004')
    simulate_daily_usage('sap_004', 400)  # Excede límite pero tiene protección
    
    # Simular evento CloudTrail
    cloudtrail_event = create_bedrock_event('sap_004', 'InvokeModel')
    
    # Ejecutar función
    result = lambda_handler(cloudtrail_event, {})
    
    # Verificaciones
    assert result['statusCode'] == 200
    assert_user_is_not_blocked('sap_004')
    assert_administrative_safe_is_active('sap_004')
    assert_request_logged_normally('sap_004')
    assert_no_blocking_audit_log('sap_004')
    assert_iam_policy_no_deny('sap_004')
```

## 🔍 Funciones de Verificación

### Verificaciones de Estado de Usuario

```python
def assert_user_is_blocked(user_id):
    """Verifica que el usuario esté bloqueado"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT is_blocked FROM user_blocking_status WHERE user_id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            assert result is not None, f"No blocking status found for {user_id}"
            assert result['is_blocked'] == 'Y', f"User {user_id} is not blocked"

def assert_user_is_not_blocked(user_id):
    """Verifica que el usuario NO esté bloqueado"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT is_blocked FROM user_blocking_status WHERE user_id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            if result:
                assert result['is_blocked'] == 'N', f"User {user_id} is still blocked"

def assert_administrative_safe_is_active(user_id):
    """Verifica que la protección administrativa esté activa"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT administrative_safe FROM user_limits WHERE user_id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            assert result is not None, f"No user limits found for {user_id}"
            assert result['administrative_safe'] == 'Y', f"Administrative protection not active for {user_id}"
```

### Verificaciones de Tiempo de Bloqueo

```python
def assert_blocked_until_tomorrow_midnight(user_id):
    """Verifica que el bloqueo expire a medianoche del día siguiente"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT blocked_until FROM user_blocking_status WHERE user_id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            assert result is not None, f"No blocking status found for {user_id}"
            
            blocked_until = result['blocked_until']
            tomorrow_midnight = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            assert blocked_until.date() == tomorrow_midnight.date(), f"Blocked until date incorrect for {user_id}"
            assert blocked_until.hour == 0 and blocked_until.minute == 0, f"Blocked until time not midnight for {user_id}"

def assert_blocked_until_24_hours_from_now(user_id):
    """Verifica que el bloqueo expire en exactamente 24 horas"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT blocked_until, blocked_at FROM user_blocking_status WHERE user_id = %s",
                [user_id]
            )
            result = cursor.fetchone()
            assert result is not None, f"No blocking status found for {user_id}"
            
            blocked_at = result['blocked_at']
            blocked_until = result['blocked_until']
            expected_until = blocked_at + timedelta(hours=24)
            
            time_diff = abs((blocked_until - expected_until).total_seconds())
            assert time_diff < 60, f"Blocked until time not 24 hours from blocked_at for {user_id}"
```

### Verificaciones de Auditoría

```python
def assert_audit_log_entry(user_id, operation_type, reason, performed_by='system'):
    """Verifica que existe una entrada en el log de auditoría"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT operation_type, operation_reason, performed_by 
                FROM blocking_audit_log 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, [user_id])
            result = cursor.fetchone()
            
            assert result is not None, f"No audit log entry found for {user_id}"
            assert result['operation_type'] == operation_type, f"Wrong operation type in audit log for {user_id}"
            assert result['operation_reason'] == reason, f"Wrong reason in audit log for {user_id}"
            assert result['performed_by'] == performed_by, f"Wrong performer in audit log for {user_id}"
```

### Verificaciones de Políticas IAM

```python
def assert_iam_policy_has_deny(user_id):
    """Verifica que la política IAM del usuario tiene statement de DENY"""
    try:
        response = iam.get_user_policy(UserName=user_id, PolicyName=f'{user_id}_BedrockPolicy')
        policy_doc = response['PolicyDocument']
        
        deny_statements = [stmt for stmt in policy_doc['Statement'] if stmt['Effect'] == 'Deny']
        assert len(deny_statements) > 0, f"No DENY statement found in IAM policy for {user_id}"
        
        deny_statement = deny_statements[0]
        assert 'bedrock:InvokeModel' in deny_statement['Action'], f"DENY statement doesn't block Bedrock for {user_id}"
        
    except iam.exceptions.NoSuchEntityException:
        assert False, f"No IAM policy found for {user_id}"

def assert_iam_policy_no_deny(user_id):
    """Verifica que la política IAM del usuario NO tiene statement de DENY"""
    try:
        response = iam.get_user_policy(UserName=user_id, PolicyName=f'{user_id}_BedrockPolicy')
        policy_doc = response['PolicyDocument']
        
        deny_statements = [stmt for stmt in policy_doc['Statement'] if stmt['Effect'] == 'Deny']
        assert len(deny_statements) == 0, f"DENY statement still exists in IAM policy for {user_id}"
        
    except iam.exceptions.NoSuchEntityException:
        # No policy exists, which is acceptable for unblocked users
        pass
```

## 📊 Matriz de Ejecución de Pruebas

| Escenario | Usuario | Estado Inicial | Acción | Resultado Esperado | Verificaciones |
|-----------|---------|----------------|--------|-------------------|----------------|
| 1.1 | sap_004 | Activo, 351 requests | CloudTrail event | Bloqueado hasta medianoche | Estado, IAM, Email, Audit |
| 1.2 | sap_004 | Activo, 5001 requests | CloudTrail event | Bloqueado hasta medianoche | Estado, IAM, Email, Audit |
| 1.3 | sap_004 | Protegido, 400 requests | CloudTrail event | NO bloqueado | Estado, Protección |
| 2.1 | sap_004 | Bloqueado expirado | CloudTrail event | Desbloqueado | Estado, IAM, Email, Audit |
| 2.2 | sap_004 | Bloqueado indefinido | CloudTrail event | Permanece bloqueado | Estado |
| 2.3 | sap_004 | Bloqueado futuro | CloudTrail event | Permanece bloqueado | Estado |
| 3.1 | sap_004 | Activo | API block manual | Bloqueado 24h | Estado, IAM, Email, Audit |
| 3.2 | sap_004 | Ya bloqueado | API block manual | Actualizado | Estado, Audit |
| 3.3 | sap_004 | Protegido | API block manual | Bloqueado (ignora protección) | Estado, IAM |
| 4.1 | sap_004 | Bloqueado | API unblock manual | Desbloqueado + protegido | Estado, IAM, Protección |
| 4.2 | sap_004 | Activo | API unblock manual | Protegido | Protección |
| 4.3 | sap_004 | Bloqueado | API unblock manual | administrative_safe='Y' | Protección |
| 5.1 | sap_004 | Bloqueado expirado | Daily reset | Desbloqueado | Estado, Email |
| 5.2 | sap_004 | Protegido | Daily reset | Protección removida | administrative_safe='N' |

## 🚀 Ejecución del Plan de Pruebas

### Preparación del Entorno

```bash
# 1. Configurar variables de entorno
export RDS_ENDPOINT="your-rds-endpoint"
export RDS_USERNAME="your-username"
export RDS_PASSWORD="your-password"
export RDS_DATABASE="bedrock_usage"
export AWS_REGION="eu-west-1"

# 2. Instalar dependencias
pip install pytest pytest-mock boto3 pymysql pytz

# 3. Preparar datos de prueba
python setup_test_data_sap_004.py
```

### Ejecución de Pruebas

```bash
# Ejecutar todas las pruebas para sap_004
python -m pytest test_blocking_unblocking_sap_004.py -v

# Ejecutar pruebas específicas
python -m pytest test_blocking_unblocking_sap_004.py::test_automatic_blocking_daily_limit_sap_004 -v

# Ejecutar con cobertura
python -m pytest test_blocking_unblocking_sap_004.py --cov=lambda_function --cov-report=html
```

### Limpieza Post-Pruebas

```sql
-- Limpiar datos de prueba de sap_004
DELETE FROM blocking_audit_log WHERE user_id = 'sap_004';
DELETE FROM user_blocking_status WHERE user_id = 'sap_004';
UPDATE user_limits SET administrative_safe = 'N' WHERE user_id = 'sap_004';
```

## 📈 Criterios de Éxito

### Métricas de Éxito
- **100% de pruebas pasando** para todos los escenarios
- **Cobertura de código ≥ 95%** para funciones de bloqueo/desbloqueo
- **Tiempo de ejecución < 30 segundos** para toda la suite
- **0 errores de integridad** en base de datos
- **100% de notificaciones enviadas** correctamente

### Validaciones Críticas
- ✅ Bloqueos automáticos funcionan correctamente
- ✅ Desbloqueos automáticos por expiración funcionan
- ✅ Bloqueos manuales funcionan independiente de protección
- ✅ Desbloqueos manuales activan protección administrativa
- ✅ Protección administrativa previene bloqueos automáticos
- ✅ Reset diario remueve protecciones administrativas
- ✅ Políticas IAM se crean/modifican correctamente
- ✅ Auditoría completa de todas las operaciones
- ✅ Notificaciones por email funcionan
- ✅ Manejo de errores es robusto

## 📝 Reporte de Resultados

Al finalizar las pruebas, se generará un reporte detallado que incluirá:

1. **Resumen ejecutivo** con métricas de éxito/fallo
2. **Resultados por escenario** con detalles de cada prueba
3. **Análisis de cobertura** de código y funcionalidad
4. **Identificación de defectos** encontrados
5. **Recomendaciones** para mejoras
6. **Estado de preparación** para producción

---

*Plan de pruebas preparado para validación exhaustiva del sistema de bloqueos y desbloqueos usando el usuario sap_004*
