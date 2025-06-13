#!/bin/bash

# Script de Deploy Completo para Discord AI Tutor Free

# --- Variáveis de Configuração ---
IMAGE_NAME="discord-ai-tutor-free"
CONTAINER_NAME="discord-tutor-bot"
ENV_FILE="./.env" # Caminho para o arquivo .env na raiz do projeto

# --- Funções Auxiliares ---

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

check_docker() {
    if ! command -v docker &> /dev/null
    then
        log_error "Docker não está instalado. Por favor, instale o Docker Desktop ou o Docker Engine."
        exit 1
    fi
    log_info "Docker encontrado."
}

check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Arquivo .env não encontrado em $ENV_FILE. Por favor, crie-o com base no .env.example."
        exit 1
    fi
    log_info "Arquivo .env encontrado."
}

stop_and_remove_container() {
    log_info "Verificando se o container '$CONTAINER_NAME' está em execução..."
    if docker ps -a --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        log_info "Parando e removendo o container existente '$CONTAINER_NAME'..."
        docker stop "$CONTAINER_NAME" && docker rm "$CONTAINER_NAME"
        if [ $? -ne 0 ]; then
            log_error "Falha ao parar/remover o container '$CONTAINER_NAME'."
            exit 1
        fi
    else
        log_info "Nenhum container '$CONTAINER_NAME' em execução ou existente."
    fi
}

build_docker_image() {
    log_info "Construindo a imagem Docker '$IMAGE_NAME'..."
    docker build -t "$IMAGE_NAME" .. # O Dockerfile está na raiz do projeto pai
    if [ $? -ne 0 ]; then
        log_error "Falha ao construir a imagem Docker."
        exit 1
    fi
    log_info "Imagem Docker construída com sucesso."
}

run_docker_container() {
    log_info "Executando o container Docker '$CONTAINER_NAME'..."
    # O arquivo .env está na raiz do projeto pai, então precisamos referenciá-lo corretamente
    docker run -d \
        --name "$CONTAINER_NAME" \
        --env-file "../$ENV_FILE" \
        "$IMAGE_NAME"
    
    if [ $? -ne 0 ]; then
        log_error "Falha ao executar o container Docker."
        exit 1
    fi
    log_info "Container Docker '$CONTAINER_NAME' iniciado com sucesso."
}

# --- Fluxo Principal do Deploy ---

log_info "Iniciando o processo de deploy para Discord AI Tutor Free..."

check_docker
check_env_file

# Navegar para o diretório raiz do projeto (onde está o Dockerfile e .env)
# Este script está em discord_ai_tutor_free/deploy, então precisamos ir um nível acima
CURRENT_DIR=$(pwd)
cd .. # Volta para discord_ai_tutor_free/

stop_and_remove_container
build_docker_image
run_docker_container

# Voltar para o diretório original do script
cd "$CURRENT_DIR"

log_info "Deploy concluído. Verifique os logs do container para confirmar o funcionamento:"
log_info "docker logs $CONTAINER_NAME"
log_info "Para parar o bot: docker stop $CONTAINER_NAME"
log_info "Para remover o bot: docker rm $CONTAINER_NAME"

exit 0
