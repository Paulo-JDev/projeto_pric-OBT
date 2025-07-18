# Etapa 1 - Build
FROM ubuntu:22.04 AS build

ENV DEBIAN_FRONTEND=noninteractive
ENV QT_X11_NO_MITSHM=1

# Instala pacotes do sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    qt6-base-dev \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os arquivos
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Instala o PyInstaller
RUN pip3 install pyinstaller

# Copia o restante da aplicação
COPY . .

# Gera o executável
RUN pyinstaller --name "Contratos360" \
    --console \
    --icon="utils/icons/mn.ico" \
    --add-data="utils/icons:utils/icons" \
    --add-data="style.qss:." \
    main.py

# Etapa 2 - Runtime enxuto (opcional)
FROM ubuntu:22.04

# Instala só as libs mínimas pro binário funcionar
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia o executável da build anterior
COPY --from=build /app/dist/Contratos360/Contratos360 .

# Permissão de execução
RUN chmod +x /app/Contratos360

# Comando padrão
CMD ["./Contratos360"]
