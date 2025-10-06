#!/bin/bash
# update-dashboard.sh
# Script para actualizar el dashboard después de hacer cambios

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuración
BUCKET_NAME="bedrock-dashboard-prod"
DISTRIBUTION_ID="E229DT26M9K8BR"
DASHBOARD_DIR="./02. Source/Dashboard"

echo -e "${GREEN}🔄 Actualizando Dashboard en AWS${NC}"
echo "=================================================="

# Paso 1: Subir archivos modificados
echo -e "\n${YELLOW}📤 Paso 1: Subiendo archivos actualizados...${NC}"
aws s3 sync "${DASHBOARD_DIR}" "s3://${BUCKET_NAME}/" \
    --exclude "*.md" \
    --exclude ".DS_Store" \
    --delete \
    --cache-control "public, max-age=31536000"

# Configurar cache-control específico para HTML (no cachear)
aws s3 cp "${DASHBOARD_DIR}/bedrock_usage_dashboard_modular.html" \
    "s3://${BUCKET_NAME}/bedrock_usage_dashboard_modular.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

aws s3 cp "${DASHBOARD_DIR}/login.html" \
    "s3://${BUCKET_NAME}/login.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo -e "${GREEN}✅ Archivos actualizados en S3${NC}"

# Paso 2: Invalidar caché de CloudFront
echo -e "\n${YELLOW}🔄 Paso 2: Invalidando caché de CloudFront...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}✅ Invalidación creada: ${INVALIDATION_ID}${NC}"

# Paso 3: Resumen
echo -e "\n${GREEN}=================================================="
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "==================================================${NC}"
echo ""
echo -e "${YELLOW}📊 Información:${NC}"
echo "  • Bucket S3: s3://${BUCKET_NAME}"
echo "  • CloudFront Distribution: ${DISTRIBUTION_ID}"
echo "  • Invalidation ID: ${INVALIDATION_ID}"
echo "  • URL: https://dtotgt2ngc4fp.cloudfront.net/login.html"
echo ""
echo -e "${YELLOW}⏱️  Nota:${NC}"
echo "  La invalidación puede tardar 5-10 minutos en completarse"
echo "  Puedes verificar el estado con:"
echo "  aws cloudfront get-invalidation --distribution-id ${DISTRIBUTION_ID} --id ${INVALIDATION_ID}"
echo ""
echo -e "${GREEN}🎉 Dashboard actualizado!${NC}"
