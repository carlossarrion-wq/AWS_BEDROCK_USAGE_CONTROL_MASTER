# AWS Lambda Functions - Production Backups

Este directorio contiene los archivos ZIP de las funciones Lambda descargados directamente desde AWS en producción.

## 📋 Archivos de Backup desde AWS

### bedrock-email-service-aws-YYYYMMDD.zip
**Función:** `bedrock-email-service`
**Última modificación:** 2025-09-23T21:05:45.000+0000
**Runtime:** Python 3.9
**Descripción:** Servicio centralizado de notificaciones por email con plantillas HTML profesionales, sistema de colores y diseño responsivo.

### bedrock-realtime-usage-controller-aws-YYYYMMDD.zip
**Función:** `bedrock-realtime-usage-controller`
**Última modificación:** 2025-09-23T20:56:45.000+0000
**Runtime:** Python 3.9
**Descripción:** Función consolidada que combina logging en tiempo real, verificación de cuotas, lógica de bloqueo y notificaciones por email. Incluye dependencias PyMySQL y PyTZ.

### bedrock-daily-reset-aws-YYYYMMDD.zip
**Función:** `bedrock-daily-reset`
**Última modificación:** 2025-09-23T06:42:02.000+0000
**Runtime:** Python 3.9
**Descripción:** Función de reset diario que desbloquea usuarios cuyo período de bloqueo ha expirado y gestiona flags administrativos.

### bedrock-mysql-query-executor-aws-YYYYMMDD.zip
**Función:** `bedrock-mysql-query-executor`
**Última modificación:** 2025-09-19T17:52:13.000+0000
**Runtime:** Python 3.9
**Descripción:** Función legacy para ejecutar consultas MySQL desde el dashboard. Puede estar en proceso de deprecación.

## 🔒 Seguridad y Uso

- **Origen:** Descargados directamente desde AWS Lambda usando AWS CLI
- **Integridad:** Estos son los archivos ZIP exactos que están desplegados en producción
- **Propósito:** Backup de seguridad para restauración en caso de necesidad
- **Fecha de descarga:** $(date +%Y-%m-%d)

## 📝 Comandos de Descarga Utilizados

```bash
# Descargar bedrock-email-service
aws lambda get-function --function-name bedrock-email-service --query 'Code.Location' --output text | xargs curl -o bedrock-email-service-aws-YYYYMMDD.zip

# Descargar bedrock-realtime-usage-controller
aws lambda get-function --function-name bedrock-realtime-usage-controller --query 'Code.Location' --output text | xargs curl -o bedrock-realtime-usage-controller-aws-YYYYMMDD.zip

# Descargar bedrock-daily-reset
aws lambda get-function --function-name bedrock-daily-reset --query 'Code.Location' --output text | xargs curl -o bedrock-daily-reset-aws-YYYYMMDD.zip

# Descargar bedrock-mysql-query-executor
aws lambda get-function --function-name bedrock-mysql-query-executor --query 'Code.Location' --output text | xargs curl -o bedrock-mysql-query-executor-aws-YYYYMMDD.zip
```

## 🔄 Restauración

Para restaurar una función desde estos backups:

```bash
# Ejemplo para bedrock-email-service
aws lambda update-function-code \
    --function-name bedrock-email-service \
    --zip-file fileb://bedrock-email-service-aws-YYYYMMDD.zip
```

## ⚠️ Notas Importantes

1. **Versiones de Producción:** Estos archivos representan las versiones exactas desplegadas en AWS
2. **Dependencias Incluidas:** Los ZIPs contienen todas las dependencias necesarias (PyMySQL, PyTZ, etc.)
3. **Configuración:** Las variables de entorno y configuraciones IAM no están incluidas en los ZIPs
4. **Actualización Regular:** Se recomienda actualizar estos backups regularmente después de despliegues

## 📊 Tamaños de Archivo

- `bedrock-email-service`: ~9 KB
- `bedrock-realtime-usage-controller`: ~560 KB (incluye PyMySQL y PyTZ)
- `bedrock-daily-reset`: ~550 KB (incluye dependencias)
- `bedrock-mysql-query-executor`: ~49 KB

---
**Generado automáticamente el:** $(date)
**Sistema:** AWS Bedrock Usage Control v2.1.0
