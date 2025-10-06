# 🚀 Dashboard Deployment Information

## ✅ Despliegue Completado Exitosamente

**Fecha de despliegue:** 6 de Octubre de 2025

---

## 📊 Información del Dashboard

### URLs de Acceso
- **URL Principal:** https://dtotgt2ngc4fp.cloudfront.net
- **Login:** https://dtotgt2ngc4fp.cloudfront.net/login.html
- **Dashboard:** https://dtotgt2ngc4fp.cloudfront.net/bedrock_usage_dashboard_modular.html

### Recursos AWS Creados

| Recurso | ID/Nombre | Región |
|---------|-----------|--------|
| **S3 Bucket** | `bedrock-dashboard-prod` | eu-west-1 |
| **CloudFront Distribution** | `E229DT26M9K8BR` | Global |
| **Origin Access Identity (OAI)** | `E38XS3I3OHPKD8` | Global |

---

## 🔐 Autenticación

- **Método:** AWS Access Key + Secret Key (sin cambios)
- **Flujo:** 
  1. Usuario ingresa Access Key + Secret Key en login.html
  2. Dashboard asume el rol `dashboard-role`
  3. Acceso a recursos AWS (RDS, DynamoDB, CloudWatch, Cost Explorer)

---

## 🏗️ Arquitectura Desplegada

```
Internet (HTTPS)
       ↓
CloudFront (CDN Global)
  • URL: dtotgt2ngc4fp.cloudfront.net
  • Certificado SSL: Incluido
  • Caché: Habilitado
       ↓
S3 Bucket (Privado)
  • Nombre: bedrock-dashboard-prod
  • Región: eu-west-1
  • Acceso: Solo vía CloudFront OAI
  • Versionado: Habilitado
  • Encriptación: AES256
       ↓
Backend (Sin cambios)
  • Lambda Functions
  • RDS MySQL
  • DynamoDB
  • CloudWatch
  • Cost Explorer
```

---

## 💰 Costos Estimados

| Servicio | Costo Mensual Estimado |
|----------|------------------------|
| S3 Storage (1 GB) | ~$0.50 |
| CloudFront (10 GB + 100K requests) | ~$1.50 |
| **TOTAL** | **~$2.00/mes** |

*Nota: Costos de backend (RDS, Lambda, etc.) no incluidos ya que existían previamente*

---

## 🔄 Actualización del Dashboard

### Para actualizar el dashboard después de hacer cambios:

```bash
# Ejecutar el script de actualización
./update-dashboard.sh
```

Este script:
1. Sube los archivos modificados a S3
2. Invalida la caché de CloudFront
3. Los cambios estarán disponibles en 5-10 minutos

### Actualización Manual

```bash
# Subir archivos a S3
aws s3 sync "./02. Source/Dashboard" s3://bedrock-dashboard-prod/ \
    --exclude "*.md" --exclude ".DS_Store"

# Invalidar caché de CloudFront
aws cloudfront create-invalidation \
    --distribution-id E229DT26M9K8BR \
    --paths "/*"
```

---

## 📋 Comandos Útiles

### Verificar estado de CloudFront
```bash
aws cloudfront get-distribution --id E229DT26M9K8BR
```

### Ver archivos en S3
```bash
aws s3 ls s3://bedrock-dashboard-prod/ --recursive
```

### Ver logs de CloudFront
```bash
aws cloudfront list-distributions --query "DistributionList.Items[?Id=='E229DT26M9K8BR']"
```

### Descargar backup del dashboard
```bash
aws s3 sync s3://bedrock-dashboard-prod/ ./dashboard-backup/
```

---

## 🔒 Seguridad

### Configuraciones Aplicadas

✅ **S3 Bucket:**
- Acceso público bloqueado
- Solo accesible vía CloudFront OAI
- Versionado habilitado
- Encriptación AES256 en reposo

✅ **CloudFront:**
- HTTPS obligatorio (redirect-to-https)
- TLS 1.2 mínimo
- Compresión habilitada
- Caché optimizado

✅ **Autenticación:**
- AWS Access Key + Secret Key
- AssumeRole para dashboard-role
- Sin cambios en el flujo actual

---

## ⏱️ Tiempos de Propagación

- **Primera vez:** 15-20 minutos para que CloudFront se propague globalmente
- **Actualizaciones:** 5-10 minutos para invalidación de caché
- **Cambios en S3:** Inmediatos (pero caché puede tardar)

---

## 🎯 Próximos Pasos Opcionales

### 1. Dominio Personalizado (Opcional)
Para usar un dominio como `dashboard.tuempresa.com`:

```bash
# 1. Solicitar certificado SSL en ACM (us-east-1)
aws acm request-certificate \
    --domain-name dashboard.tuempresa.com \
    --validation-method DNS \
    --region us-east-1

# 2. Actualizar CloudFront con el certificado
# 3. Crear registro CNAME en Route 53
```

### 2. Logs de Acceso (Opcional)
Para habilitar logs de CloudFront:

```bash
# Crear bucket para logs
aws s3 mb s3://bedrock-dashboard-logs

# Actualizar configuración de CloudFront
```

### 3. Alertas de Costos (Opcional)
Para recibir alertas si los costos superan un umbral:

```bash
# Crear alarma en CloudWatch
aws cloudwatch put-metric-alarm \
    --alarm-name dashboard-cost-alert \
    --alarm-description "Alert when dashboard costs exceed $10" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 86400 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold
```

---

## 🆘 Troubleshooting

### Problema: Dashboard no carga
**Solución:**
```bash
# Verificar estado de CloudFront
aws cloudfront get-distribution --id E229DT26M9K8BR

# Verificar archivos en S3
aws s3 ls s3://bedrock-dashboard-prod/
```

### Problema: Cambios no se reflejan
**Solución:**
```bash
# Invalidar caché de CloudFront
aws cloudfront create-invalidation \
    --distribution-id E229DT26M9K8BR \
    --paths "/*"
```

### Problema: Error de autenticación
**Solución:**
- Verificar que las credenciales AWS sean válidas
- Verificar que el rol `dashboard-role` exista y tenga permisos
- Verificar que el usuario pueda asumir el rol

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs de CloudFront
2. Verificar configuración de S3
3. Comprobar permisos de IAM
4. Revisar logs de navegador (F12 → Console)

---

## 📝 Notas Importantes

1. **Caché de CloudFront:** Los archivos HTML no se cachean (`no-cache`), pero CSS/JS sí (1 año)
2. **Costos:** Monitorear uso mensual en AWS Cost Explorer
3. **Backups:** S3 tiene versionado habilitado, se pueden recuperar versiones anteriores
4. **Seguridad:** El bucket S3 es privado, solo accesible vía CloudFront
5. **Actualizaciones:** Usar `update-dashboard.sh` para desplegar cambios

---

## ✅ Checklist de Verificación

- [x] Bucket S3 creado y configurado
- [x] Archivos del dashboard subidos
- [x] CloudFront distribution creada
- [x] OAI configurado correctamente
- [x] Bucket policy aplicada
- [x] HTTPS habilitado
- [x] Dashboard accesible vía URL de CloudFront
- [x] Script de actualización creado
- [x] Documentación completada

---

**Dashboard desplegado exitosamente y listo para uso! 🎉**
