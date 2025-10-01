# Guía de Ejecución - Pruebas Unitarias de Operaciones Manuales
## bedrock-realtime-usage-controller Lambda Function

**Archivo de Pruebas:** `test_manual_operations_comprehensive.py`  
**Grupo:** Grupo 8 - Operaciones Manuales  
**Versión:** 1.0.0  
**Fecha:** 10 de enero de 2025

---

## 📋 ÍNDICE

1. [Descripción General](#descripción-general)
2. [Requisitos Previos](#requisitos-previos)
3. [Instalación de Dependencias](#instalación-de-dependencias)
4. [Estructura de las Pruebas](#estructura-de-las-pruebas)
5. [Ejecución de las Pruebas](#ejecución-de-las-pruebas)
6. [Casos de Prueba Incluidos](#casos-de-prueba-incluidos)
7. [Interpretación de Resultados](#interpretación-de-resultados)
8. [Solución de Problemas](#solución-de-problemas)

---

## 📖 DESCRIPCIÓN GENERAL

Este conjunto de pruebas unitarias valida todas las operaciones manuales realizadas por administradores en la función Lambda `bedrock-realtime-usage-controller`. Las pruebas cubren:

- ✅ **Bloqueos manuales** con diferentes duraciones (1 día, 30 días, 90 días, indefinido, personalizado)
- ✅ **Desbloqueos manuales** con protección administrativa
- ✅ **Consultas de estado** de usuarios
- ✅ **Manejo de errores** y casos edge
- ✅ **Validación de base de datos** y operaciones IAM

**Total de Pruebas:** 35 casos de prueba organizados en 6 clases

---

## 🔧 REQUISITOS PREVIOS

### Software Necesario

```bash
Python 3.9+
pytest 7.0+
pytest-cov (opcional, para cobertura)
```

### Dependencias del Proyecto

```bash
pymysql
pytz
boto3
```

### Estructura de Directorios

```
AWS_BEDROCK_USAGE_CONTROL_MASTER/
├── 02. Source/
│   └── Lambda Functions/
│       └── bedrock-realtime-usage-controller-aws-20250923/
│           └── lambda_function.py
└── 04. Testing/
    ├── test_manual_operations_comprehensive.py
    └── MANUAL_OPERATIONS_TEST_GUIDE.md (este archivo)
```

---

## 📦 INSTALACIÓN DE DEPENDENCIAS

### 1. Crear Entorno Virtual (Recomendado)

```bash
cd /Users/csarrion/Cline/AWS_BEDROCK_USAGE_CONTROL_MASTER
python3 -m venv test_env
source test_env/bin/activate  # En Windows: test_env\Scripts\activate
```

### 2. Instalar Dependencias de Testing

```bash
pip install pytest pytest-cov pytest-mock
```

### 3. Instalar Dependencias del Proyecto

```bash
pip install pymysql pytz boto3
```

### 4. Verificar Instalación

```bash
pytest --version
python -c "import pymysql, pytz, boto3; print('Dependencies OK')"
```

---

## 🏗️ ESTRUCTURA DE LAS PRUEBAS

### Fixtures Principales

| Fixture | Descripción | Uso |
|---------|-------------|-----|
| `mock_mysql_connection` | Mock de conexión MySQL | Simula operaciones de BD |
| `mock_iam_client` | Mock de cliente IAM | Simula operaciones IAM |
| `mock_lambda_client` | Mock de cliente Lambda | Simula invocaciones Lambda |
| `sample_usage_info` | Datos de uso de ejemplo | Información de límites |
| `mock_current_time` | Tiempo CET mockeado | Control de timestamps |

### Clases de Prueba

```
TestManualBlockingOperations (8 tests)
├── Bloqueo 1 día
├── Bloqueo 30 días
├── Bloqueo 90 días
├── Bloqueo indefinido
├── Bloqueo personalizado
├── Fallo de bloqueo
└── Excepción de bloqueo

TestManualUnblockingOperations (4 tests)
├── Desbloqueo exitoso
├── Desbloqueo con razón personalizada
├── Fallo de desbloqueo
└── Excepción de desbloqueo

TestUserStatusChecking (6 tests)
├── Estado bloqueado automático
├── Estado bloqueado manual
├── Estado bloqueado indefinido
├── Estado no bloqueado
├── Sin registro de estado
└── Excepción en consulta

TestExecuteAdminBlocking (5 tests)
├── Bloqueo 1 día
├── Bloqueo 30 días
├── Bloqueo indefinido
├── Expiración personalizada
└── Fallo de base de datos

TestExecuteAdminUnblocking (5 tests)
├── Desbloqueo exitoso
├── Establece protección admin
├── Crea user_limits si falta
├── Fallo de base de datos
└── Fallo de IAM (no crítico)

TestGetUserCurrentUsage (4 tests)
├── Obtención exitosa
├── Sin registro de límites
├── Con protección admin
└── Excepción de BD
```

---

## ▶️ EJECUCIÓN DE LAS PRUEBAS

### Ejecución Completa

```bash
cd 04. Testing
pytest test_manual_operations_comprehensive.py -v
```

### Ejecución por Clase

```bash
# Solo bloqueos manuales
pytest test_manual_operations_comprehensive.py::TestManualBlockingOperations -v

# Solo desbloqueos manuales
pytest test_manual_operations_comprehensive.py::TestManualUnblockingOperations -v

# Solo consultas de estado
pytest test_manual_operations_comprehensive.py::TestUserStatusChecking -v
```

### Ejecución de Prueba Individual

```bash
pytest test_manual_operations_comprehensive.py::TestManualBlockingOperations::test_manual_block_user_success_1day -v
```

### Con Cobertura de Código

```bash
pytest test_manual_operations_comprehensive.py --cov=lambda_function --cov-report=html
```

### Modo Detallado con Salida Completa

```bash
pytest test_manual_operations_comprehensive.py -vv -s
```

### Ejecución Rápida (Detener en Primer Fallo)

```bash
pytest test_manual_operations_comprehensive.py -x
```

---

## 📊 CASOS DE PRUEBA INCLUIDOS

### 1. Bloqueos Manuales (8 tests)

#### ✅ test_manual_block_user_success_1day
**Objetivo:** Validar bloqueo manual con duración de 1 día  
**Entrada:**
```json
{
  "action": "block",
  "user_id": "test_user",
  "reason": "Manual admin block for testing",
  "performed_by": "admin_user",
  "duration": "1day"
}
```
**Validaciones:**
- StatusCode = 200
- Mensaje de éxito
- Parámetros correctos pasados a execute_admin_blocking

#### ✅ test_manual_block_user_success_30days
**Objetivo:** Validar bloqueo manual con duración de 30 días  
**Validaciones:**
- Duración correcta ('30days')
- Respuesta exitosa

#### ✅ test_manual_block_user_success_90days
**Objetivo:** Validar bloqueo manual con duración de 90 días  
**Validaciones:**
- Duración correcta ('90days')
- Respuesta exitosa

#### ✅ test_manual_block_user_success_indefinite
**Objetivo:** Validar bloqueo manual indefinido  
**Validaciones:**
- Duración 'indefinite'
- Sin fecha de expiración

#### ✅ test_manual_block_user_success_custom_duration
**Objetivo:** Validar bloqueo con fecha personalizada  
**Entrada:**
```json
{
  "duration": "custom",
  "expires_at": "2025-02-15T10:00:00Z"
}
```
**Validaciones:**
- Fecha personalizada procesada correctamente

#### ✅ test_manual_block_user_failure
**Objetivo:** Validar manejo de fallo en bloqueo  
**Validaciones:**
- StatusCode = 500
- Mensaje de error apropiado

#### ✅ test_manual_block_user_exception
**Objetivo:** Validar manejo de excepciones  
**Validaciones:**
- StatusCode = 500
- Error capturado y reportado

### 2. Desbloqueos Manuales (4 tests)

#### ✅ test_manual_unblock_user_success
**Objetivo:** Validar desbloqueo manual exitoso  
**Entrada:**
```json
{
  "action": "unblock",
  "user_id": "test_user",
  "reason": "Manual admin unblock",
  "performed_by": "admin_user"
}
```
**Validaciones:**
- StatusCode = 200
- Mensaje de éxito
- Parámetros correctos

#### ✅ test_manual_unblock_user_with_custom_reason
**Objetivo:** Validar desbloqueo con razón personalizada  
**Validaciones:**
- Razón personalizada procesada

#### ✅ test_manual_unblock_user_failure
**Objetivo:** Validar manejo de fallo  
**Validaciones:**
- StatusCode = 500

#### ✅ test_manual_unblock_user_exception
**Objetivo:** Validar manejo de excepciones  
**Validaciones:**
- Error capturado

### 3. Consultas de Estado (6 tests)

#### ✅ test_check_user_status_blocked_automatic
**Objetivo:** Validar consulta de usuario bloqueado automáticamente  
**Validaciones:**
- is_blocked = True
- block_type = 'AUTO'
- performed_by = 'system'
- blocked_until = medianoche (00:00:00)

#### ✅ test_check_user_status_blocked_manual
**Objetivo:** Validar consulta de usuario bloqueado manualmente  
**Validaciones:**
- block_type = 'Manual'
- performed_by = 'dashboard_admin'
- administrative_safe = True

#### ✅ test_check_user_status_blocked_indefinite
**Objetivo:** Validar consulta de usuario bloqueado indefinidamente  
**Validaciones:**
- expires_at = None

#### ✅ test_check_user_status_not_blocked
**Objetivo:** Validar consulta de usuario no bloqueado  
**Validaciones:**
- is_blocked = False
- block_type = 'None'

#### ✅ test_check_user_status_no_record
**Objetivo:** Validar consulta sin registro  
**Validaciones:**
- Manejo correcto de ausencia de datos

#### ✅ test_check_user_status_exception
**Objetivo:** Validar manejo de excepciones  
**Validaciones:**
- StatusCode = 500

### 4. Ejecución de Bloqueo Admin (5 tests)

#### ✅ test_execute_admin_blocking_1day_duration
**Objetivo:** Validar ejecución de bloqueo de 1 día  
**Validaciones:**
- Resultado = True
- Llamadas a BD >= 2
- blocked_until calculado correctamente

#### ✅ test_execute_admin_blocking_30days_duration
**Objetivo:** Validar ejecución de bloqueo de 30 días  
**Validaciones:**
- Resultado = True

#### ✅ test_execute_admin_blocking_indefinite
**Objetivo:** Validar ejecución de bloqueo indefinido  
**Validaciones:**
- blocked_until = None

#### ✅ test_execute_admin_blocking_custom_expiration
**Objetivo:** Validar bloqueo con fecha personalizada  
**Validaciones:**
- Fecha procesada correctamente

#### ✅ test_execute_admin_blocking_database_failure
**Objetivo:** Validar manejo de fallo de BD  
**Validaciones:**
- Resultado = False

### 5. Ejecución de Desbloqueo Admin (5 tests)

#### ✅ test_execute_admin_unblocking_success
**Objetivo:** Validar ejecución exitosa de desbloqueo  
**Validaciones:**
- Resultado = True
- Llamadas a BD >= 3

#### ✅ test_execute_admin_unblocking_sets_admin_protection
**Objetivo:** Validar que se establece protección administrativa  
**Validaciones:**
- administrative_safe = 'Y'
- UPDATE user_limits ejecutado

#### ✅ test_execute_admin_unblocking_creates_user_limits_if_missing
**Objetivo:** Validar creación de user_limits si no existe  
**Validaciones:**
- INSERT user_limits ejecutado

#### ✅ test_execute_admin_unblocking_database_failure
**Objetivo:** Validar manejo de fallo de BD  
**Validaciones:**
- Resultado = False

#### ✅ test_execute_admin_unblocking_iam_failure
**Objetivo:** Validar que fallo de IAM no es crítico  
**Validaciones:**
- Resultado = True (continúa a pesar del fallo)

### 6. Obtención de Uso Actual (4 tests)

#### ✅ test_get_user_current_usage_success
**Objetivo:** Validar obtención exitosa de uso  
**Validaciones:**
- daily_requests_used = 250
- monthly_requests_used = 3500
- Porcentajes calculados correctamente

#### ✅ test_get_user_current_usage_no_limits_record
**Objetivo:** Validar uso de límites por defecto  
**Validaciones:**
- daily_limit = 350 (default)
- monthly_limit = 5000 (default)

#### ✅ test_get_user_current_usage_with_admin_protection
**Objetivo:** Validar detección de protección admin  
**Validaciones:**
- administrative_safe = True

#### ✅ test_get_user_current_usage_exception
**Objetivo:** Validar manejo de excepciones  
**Validaciones:**
- Valores por defecto retornados

---

## 📈 INTERPRETACIÓN DE RESULTADOS

### Salida Exitosa

```
======================== test session starts =========================
collected 35 items

test_manual_operations_comprehensive.py::TestManualBlockingOperations::test_manual_block_user_success_1day PASSED [ 2%]
test_manual_operations_comprehensive.py::TestManualBlockingOperations::test_manual_block_user_success_30days PASSED [ 5%]
...
======================== 35 passed in 2.45s ==========================
```

### Salida con Fallos

```
FAILED test_manual_operations_comprehensive.py::TestManualBlockingOperations::test_manual_block_user_success_1day - AssertionError: assert 500 == 200
```

### Métricas de Cobertura

```
Name                Coverage
----------------------------------
lambda_function.py  85%
----------------------------------
TOTAL              85%
```

**Objetivo de Cobertura:** ≥ 80% para operaciones manuales

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: ModuleNotFoundError: No module named 'lambda_function'

**Causa:** El path al módulo no está configurado correctamente

**Solución:**
```bash
export PYTHONPATH="${PYTHONPATH}:/Users/csarrion/Cline/AWS_BEDROCK_USAGE_CONTROL_MASTER/02. Source/Lambda Functions/bedrock-realtime-usage-controller-aws-20250923"
```

### Error: ImportError: cannot import name 'X' from 'lambda_function'

**Causa:** La función que se está probando no existe en lambda_function.py

**Solución:** Verificar que la función existe y está correctamente nombrada

### Error: AssertionError en test de duración

**Causa:** El cálculo de blocked_until no coincide con lo esperado

**Solución:** Verificar que mock_current_time está activo y la lógica de cálculo de fechas

### Error: MagicMock object has no attribute 'cursor'

**Causa:** El mock de conexión MySQL no está configurado correctamente

**Solución:** Verificar que se está usando el fixture `mock_mysql_connection`

### Tests Lentos

**Causa:** Operaciones de I/O no mockeadas

**Solución:**
```bash
pytest test_manual_operations_comprehensive.py -v --durations=10
```
Identificar y mockear operaciones lentas

---

## 📝 NOTAS ADICIONALES

### Convenciones de Nombres

- **test_X_success:** Prueba de caso exitoso
- **test_X_failure:** Prueba de caso de fallo esperado
- **test_X_exception:** Prueba de manejo de excepciones
- **test_X_edge_case:** Prueba de caso límite

### Mantenimiento

- Actualizar pruebas cuando se modifique lambda_function.py
- Revisar cobertura después de cada cambio
- Documentar nuevos casos de prueba en este archivo

### Integración Continua

Para integrar en CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run Manual Operations Tests
  run: |
    pytest 04. Testing/test_manual_operations_comprehensive.py -v --cov
```

---

## 📞 CONTACTO Y SOPORTE

**Autor:** AWS Bedrock Usage Control System  
**Versión:** 1.0.0  
**Última Actualización:** 10 de enero de 2025

Para reportar problemas o sugerencias, crear un issue en el repositorio del proyecto.

---

**FIN DEL DOCUMENTO**
