#!/bin/bash
# deploy-dashboard-to-aws.sh
# Despliegue simplificado del Dashboard a S3 + CloudFront

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
BUCKET_NAME="bedrock-dashboard-prod"
REGION="eu-west-1"
CLOUDFRONT_COMMENT="Bedrock Usage Dashboard"
DASHBOARD_DIR="./02. Source/Dashboard"

echo -e "${GREEN}🚀 Iniciando despliegue del Dashboard a AWS${NC}"
echo "=================================================="

# Paso 1: Crear bucket S3
echo -e "\n${YELLOW}📦 Paso 1: Creando bucket S3...${NC}"
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://${BUCKET_NAME}" --region ${REGION}
    echo -e "${GREEN}✅ Bucket creado: ${BUCKET_NAME}${NC}"
else
    echo -e "${YELLOW}⚠️  Bucket ya existe: ${BUCKET_NAME}${NC}"
fi

# Paso 2: Configurar bucket para hosting estático
echo -e "\n${YELLOW}🌐 Paso 2: Configurando bucket...${NC}"

# Habilitar versionado
aws s3api put-bucket-versioning \
    --bucket ${BUCKET_NAME} \
    --versioning-configuration Status=Enabled

# Habilitar encriptación
aws s3api put-bucket-encryption \
    --bucket ${BUCKET_NAME} \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Bloquear acceso público (usaremos CloudFront OAI)
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo -e "${GREEN}✅ Bucket configurado correctamente${NC}"

# Paso 3: Subir archivos del dashboard
echo -e "\n${YELLOW}📤 Paso 3: Subiendo archivos del dashboard...${NC}"
aws s3 sync "${DASHBOARD_DIR}" "s3://${BUCKET_NAME}/" \
    --exclude "*.md" \
    --exclude ".DS_Store" \
    --cache-control "public, max-age=31536000" \
    --metadata-directive REPLACE

# Configurar cache-control específico para HTML (no cachear)
aws s3 cp "${DASHBOARD_DIR}/bedrock_usage_dashboard_modular.html" \
    "s3://${BUCKET_NAME}/bedrock_usage_dashboard_modular.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

aws s3 cp "${DASHBOARD_DIR}/login.html" \
    "s3://${BUCKET_NAME}/login.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo -e "${GREEN}✅ Archivos subidos correctamente${NC}"

# Paso 4: Crear Origin Access Identity (OAI)
echo -e "\n${YELLOW}🔐 Paso 4: Creando Origin Access Identity...${NC}"
OAI_ID=$(aws cloudfront create-cloud-front-origin-access-identity \
    --cloud-front-origin-access-identity-config \
        CallerReference="bedrock-dashboard-$(date +%s)",Comment="OAI for Bedrock Dashboard" \
    --query 'CloudFrontOriginAccessIdentity.Id' \
    --output text 2>/dev/null || echo "")

if [ -z "$OAI_ID" ]; then
    # Si ya existe, obtener el ID existente
    OAI_ID=$(aws cloudfront list-cloud-front-origin-access-identities \
        --query "CloudFrontOriginAccessIdentityList.Items[?Comment=='OAI for Bedrock Dashboard'].Id | [0]" \
        --output text)
    echo -e "${YELLOW}⚠️  Usando OAI existente: ${OAI_ID}${NC}"
else
    echo -e "${GREEN}✅ OAI creado: ${OAI_ID}${NC}"
fi

# Paso 5: Actualizar bucket policy para permitir acceso desde CloudFront
echo -e "\n${YELLOW}📋 Paso 5: Configurando bucket policy...${NC}"

# Obtener el ARN canónico del OAI
OAI_CANONICAL_USER=$(aws cloudfront get-cloud-front-origin-access-identity \
    --id ${OAI_ID} \
    --query 'CloudFrontOriginAccessIdentity.S3CanonicalUserId' \
    --output text)

cat > /tmp/bucket-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontOAI",
            "Effect": "Allow",
            "Principal": {
                "CanonicalUser": "${OAI_CANONICAL_USER}"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${BUCKET_NAME} \
    --policy file:///tmp/bucket-policy.json

echo -e "${GREEN}✅ Bucket policy configurada${NC}"

# Paso 6: Crear distribución CloudFront
echo -e "\n${YELLOW}☁️  Paso 6: Creando distribución CloudFront...${NC}"
cat > /tmp/cloudfront-config.json <<EOF
{
    "CallerReference": "bedrock-dashboard-$(date +%s)",
    "Comment": "${CLOUDFRONT_COMMENT}",
    "Enabled": true,
    "DefaultRootObject": "login.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": "origin-access-identity/cloudfront/${OAI_ID}"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "Compress": true,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000
    },
    "ViewerCertificate": {
        "CloudFrontDefaultCertificate": true,
        "MinimumProtocolVersion": "TLSv1.2_2021"
    }
}
EOF

DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file:///tmp/cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text 2>/dev/null || echo "")

if [ -z "$DISTRIBUTION_ID" ]; then
    echo -e "${YELLOW}⚠️  Buscando distribución existente...${NC}"
    DISTRIBUTION_ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='${CLOUDFRONT_COMMENT}'].Id | [0]" \
        --output text)
fi

echo -e "${GREEN}✅ Distribución CloudFront: ${DISTRIBUTION_ID}${NC}"

# Obtener URL de CloudFront
CLOUDFRONT_URL=$(aws cloudfront get-distribution \
    --id ${DISTRIBUTION_ID} \
    --query 'Distribution.DomainName' \
    --output text)

# Paso 7: Resumen final
echo -e "\n${GREEN}=================================================="
echo "✅ DESPLIEGUE COMPLETADO EXITOSAMENTE"
echo "==================================================${NC}"
echo ""
echo -e "${YELLOW}📊 Información del Dashboard:${NC}"
echo "  • Bucket S3: s3://${BUCKET_NAME}"
echo "  • CloudFront Distribution ID: ${DISTRIBUTION_ID}"
echo "  • URL del Dashboard: https://${CLOUDFRONT_URL}"
echo ""
echo -e "${YELLOW}🔐 Autenticación:${NC}"
echo "  • Método: AWS Access Key + Secret Key (sin cambios)"
echo "  • Login: https://${CLOUDFRONT_URL}/login.html"
echo ""
echo -e "${YELLOW}⏱️  Nota:${NC}"
echo "  La distribución de CloudFront puede tardar 15-20 minutos en propagarse"
echo "  Puedes verificar el estado con:"
echo "  aws cloudfront get-distribution --id ${DISTRIBUTION_ID}"
echo ""
echo -e "${GREEN}🎉 Dashboard publicado y accesible globalmente!${NC}"

# Limpiar archivos temporales
rm -f /tmp/bucket-policy.json /tmp/cloudfront-config.json
