# INDICADORES DEL DASHBOARD AWS BEDROCK USAGE CONTROL

## Resumen Ejecutivo

Este documento describe los principales indicadores monitorizados en cada pestaña del **AWS Bedrock Usage Dashboard**, un sistema de control y monitorización del uso de servicios AWS Bedrock en tiempo real.

---

## 📊 **PESTAÑA 1: USER CONSUMPTION**

### Indicadores Principales

#### **Métricas de Resumen (Tarjetas Superiores)**
- **Total Requests Today**: Número total de solicitudes realizadas hoy por todos los usuarios
- **Active Users**: Cantidad de usuarios que han realizado al menos una solicitud hoy
- **Avg Requests/User**: Promedio de solicitudes por usuario activo
- **Avg Cost/User**: Costo promedio por usuario (calculado del día anterior)

#### **Gráficos de Análisis**
- **Hourly Usage Today**: Histograma de uso por horas (0:00-23:00) del día actual
- **Usage Distribution by User**: Distribución de solicitudes entre los usuarios más activos (top 10)

#### **Tabla de Detalles de Usuario**
- **User**: Identificador del usuario
- **Person**: Nombre real de la persona (etiqueta)
- **Team**: Equipo al que pertenece
- **Blocking Status**: Estado de bloqueo (ACTIVE, ACTIVE_ADM, BLOCKED, BLOCKED_ADM)
- **Daily Requests**: Solicitudes del día actual vs límite diario
- **Daily Usage**: Porcentaje de uso diario con indicadores visuales
- **Monthly Requests**: Solicitudes del mes vs límite mensual
- **Monthly Usage**: Porcentaje de uso mensual con indicadores visuales

#### **Gráficos Temporales**
- **User Daily Usage**: Tendencia de uso diario por usuario (últimos 10 días)
- **Model Usage Distribution Today**: Distribución del uso por modelo de IA

#### **Alertas de Usuario**
- Alertas automáticas para usuarios que superan el 80% de su límite diario
- Clasificación por criticidad (Info, Warning, Critical)

---

## 🏢 **PESTAÑA 2: TEAM CONSUMPTION**

### Indicadores Principales

#### **Gráficos de Equipo**
- **Team Monthly Usage**: Uso mensual acumulado por equipo
- **Team Daily Usage**: Tendencia diaria por equipo (últimos 10 días)

#### **Tabla de Uso por Equipos**
- **Team**: Nombre del equipo
- **Daily Requests**: Solicitudes del día actual
- **Daily Usage**: Porcentaje de uso diario estimado
- **Monthly Requests**: Solicitudes mensuales acumuladas
- **Monthly Usage**: Porcentaje del límite mensual del equipo

#### **Tabla de Usuarios en Equipos**
- **User**: Usuario individual
- **Person**: Nombre real
- **Team**: Equipo de pertenencia
- **Monthly Requests**: Contribución mensual del usuario
- **% of Team Usage**: Porcentaje que representa del uso total del equipo

#### **Alertas de Equipo**
- Monitorización de equipos que superan el 80% de su límite mensual
- Alertas por criticidad según umbrales configurados

---

## 📋 **PESTAÑA 3: CONSUMPTION DETAILS**

### Indicadores Principales

#### **Gráfico de Tendencia**
- **Daily Usage Trend**: Gráfico de barras del uso total diario (últimos 10 días)

#### **Tabla de Consumo Detallado**
- **User**: Identificador del usuario
- **Person**: Nombre real
- **Team**: Equipo
- **Columnas Diarias**: Una columna por cada uno de los últimos 10 días
  - Valores numéricos de solicitudes por día
  - Identificación visual de fines de semana

#### **Tabla de Uso por Modelos**
- **Team**: Equipo (filas)
- **Modelos**: Columnas por cada modelo de IA disponible
  - Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku, etc.
  - Amazon Titan
- **Total Requests**: Suma total por equipo

#### **Gráficos Adicionales**
- **Model Consumption Evolution**: Evolución del uso por modelo (últimos 10 días)
- **Usage by User Agent**: Distribución por tipo de cliente/aplicación

---

## 💰 **PESTAÑA 4: COST ANALYSIS**

### Indicadores Principales

#### **Métricas de Costo (Tarjetas Superiores)**
- **AWS Bedrock Cost Last 30 Days**: Costo total de Bedrock en los últimos 30 días
- **AWS Bedrock Cost Current Month**: Costo acumulado del mes actual

#### **Tabla de Costos por Servicio**
- **Service**: Servicio de AWS Bedrock
- **Columnas Diarias**: Costo diario por servicio (últimos 10 días)
- **Total**: Suma total por servicio

#### **Análisis Costo vs Solicitudes**
- **Date**: Fecha
- **Total Cost (USD)**: Costo total del día
- **Total Requests**: Número total de solicitudes
- **Cost per Request (USD)**: Costo unitario por solicitud
- **Efficiency Rating**: Calificación de eficiencia
- **Trends**: Tendencias de costo y solicitudes

#### **Atribución de Costos por Equipo**
- **Team**: Equipo
- **Columnas Diarias**: Costo estimado por equipo por día
- **Total**: Costo total atribuido
- **Avg Daily**: Promedio diario

#### **Gráficos de Análisis de Costos**
- **Daily Cost Trend**: Tendencia de costo diario
- **Service Cost Distribution**: Distribución de costos por servicio
- **Cost per Request Trend**: Tendencia del costo por solicitud
- **Cost vs Requests Correlation**: Análisis de correlación

---

## 🔒 **PESTAÑA 5: BLOCKING MANAGEMENT**

### Indicadores Principales

#### **Controles de Bloqueo Manual**
- **Select User**: Selector de usuario para bloquear/desbloquear
- **Block Duration**: Duración del bloqueo (1 día, 30 días, 90 días, personalizado, indefinido)
- **Reason**: Motivo del bloqueo/desbloqueo

#### **Tabla de Estado de Usuarios**
- **User**: Identificador del usuario
- **Person**: Nombre real
- **Team**: Equipo
- **Status**: Estado actual (ACTIVE, BLOCKED, etc.)
- **Daily Usage**: Uso diario actual vs límite
- **Daily Limit**: Límite diario configurado
- **Monthly Usage**: Uso mensual vs límite
- **Blocked Since**: Fecha y hora de bloqueo
- **Expires**: Fecha y hora de expiración del bloqueo

#### **Historial de Operaciones**
- **Timestamp**: Fecha y hora de la operación
- **User**: Usuario afectado
- **Person**: Nombre real
- **Operation**: Tipo de operación (BLOCK, UNBLOCK)
- **Reason**: Motivo de la operación
- **Performed By**: Quien realizó la operación

---

## 💸 **PESTAÑA 6: AWS COSTS CONTROL**

### Indicadores Principales

#### **Métricas Generales de AWS (Tarjetas Superiores)**
- **AWS Cost (All Services) Last 30 Days**: Costo total de AWS (todos los servicios)
- **AWS Cost (All Services) Current Month**: Costo del mes actual (todos los servicios)

#### **Tabla de Servicios Principales**
- **Service**: Servicio de AWS
- **Category**: Categoría del servicio
- **Current Month Cost**: Costo del mes actual
- **Previous Month Cost**: Costo del mes anterior
- **Change (%)**: Cambio porcentual
- **Trend**: Tendencia
- **% of Total**: Porcentaje del costo total
- **Recommendation**: Recomendación de optimización

#### **Desglose Diario de Costos**
- **Date**: Fecha
- **Total Cost**: Costo total del día
- **Categorías**: Costos por categoría de servicio
  - Compute, Storage, Database, Networking, AI/ML, Analytics, Security, Management, Other
- **Daily Change**: Cambio diario

#### **Recomendaciones de Optimización**
- **Service**: Servicio
- **Issue Type**: Tipo de problema identificado
- **Current Cost**: Costo actual
- **Potential Savings**: Ahorro potencial
- **Priority**: Prioridad de la recomendación
- **Implementation**: Pasos de implementación
- **Risk Level**: Nivel de riesgo

#### **Gráficos de Control de Costos**
- **AWS Cost Trend**: Tendencia de costos (últimos 30 días)
- **Service Cost Distribution**: Distribución por servicios
- **Cost per Service Category**: Costos por categoría

---

## 🎯 **INDICADORES TRANSVERSALES**

### Alertas del Sistema
- **Alertas de Conexión**: Estado de conectividad con AWS
- **Alertas de Uso**: Usuarios/equipos cerca de límites
- **Alertas de Costo**: Costos elevados o tendencias preocupantes
- **Alertas de Rendimiento**: Eficiencia del sistema

### Métricas de Rendimiento
- **Tiempo de Respuesta**: Latencia de las consultas
- **Disponibilidad**: Uptime del sistema
- **Precisión de Datos**: Calidad de la información mostrada

### Configuración Dinámica
- **Límites por Usuario**: Configurables desde base de datos
- **Límites por Equipo**: Ajustables según necesidades
- **Umbrales de Alerta**: Personalizables (60% warning, 85% critical)
- **Períodos de Análisis**: Últimos 10 días para tendencias detalladas

---

## 📈 **CARACTERÍSTICAS TÉCNICAS**

### Fuentes de Datos
- **AWS CloudWatch**: Métricas de uso en tiempo real
- **AWS Cost Explorer**: Datos de costos y facturación
- **Base de Datos MySQL**: Almacenamiento de configuraciones y logs
- **AWS IAM**: Información de usuarios y equipos

### Actualización de Datos
- **Tiempo Real**: Métricas de uso y bloqueos
- **Horaria**: Agregaciones y tendencias
- **Diaria**: Análisis de costos y reportes

### Capacidades de Exportación
- **Formato CSV**: Todas las tablas son exportables
- **Filtros**: Paginación y búsqueda en tablas grandes
- **Histórico**: Datos de los últimos 10-30 días según el indicador

---

*Documento generado automáticamente - Última actualización: 20/10/2025*
