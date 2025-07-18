#!/bin/bash

set -e  # para o script parar se der erro

IMAGE_NAME="contratos360-builder"
CONTAINER_NAME="contratos360-temp"
OUTPUT_DIR="./dist-linux"
BIN_PATH_IN_CONTAINER="/app/Contratos360"

echo "🛠️  1. Construindo a imagem Docker..."
docker build -t $IMAGE_NAME .

echo "🚀  2. Criando container temporário..."
CONTAINER_ID=$(docker create $IMAGE_NAME)

echo "📦  3. Extraindo executável para $OUTPUT_DIR..."
mkdir -p $OUTPUT_DIR
docker cp "$CONTAINER_ID:$BIN_PATH_IN_CONTAINER" "$OUTPUT_DIR/Contratos360"

echo "🧼  4. Limpando container temporário..."
docker rm $CONTAINER_ID > /dev/null

echo "✅  Finalizado! O executável está em: $OUTPUT_DIR/Contratos360"
echo "💡 Use: chmod +x $OUTPUT_DIR/Contratos360 && $OUTPUT_DIR/Contratos360"
