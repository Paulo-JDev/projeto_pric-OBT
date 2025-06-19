# Use uma imagem base estável do Ubuntu.
FROM ubuntu:22.04

# Define variáveis de ambiente para evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV QT_X11_NO_MITSHM=1

# Atualiza os pacotes e instala as dependências de sistema
# - python3 e python3-pip são essenciais
# - build-essential e qt6-base-dev fornecem as ferramentas e bibliotecas Qt
#   que o pip usará para instalar o PyQt6 corretamente.
# - libgl1-mesa-glx é para a renderização gráfica.
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential \
    qt6-base-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências do Python primeiro para otimizar o cache do Docker
COPY requirements.txt .

# Instala as dependências Python, incluindo o PyQt6
RUN pip3 install --no-cache-dir -r requirements.txt

# Copia todo o resto do código da sua aplicação
COPY . .

# Define o comando que será executado quando o container iniciar
CMD ["python3", "main.py"]