#!/bin/bash

echo "=== Configuração do Repositório GitHub ==="
echo ""

# Verificar se estamos no diretório correto
if [ ! -d ".git" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do repositório Git"
    exit 1
fi

echo "📁 Diretório atual: $(pwd)"
echo ""

# Solicitar informações do usuário
read -p "Digite seu nome de usuário do GitHub: " GITHUB_USER
read -p "Digite o nome do repositório (padrão: hackatonaws): " REPO_NAME

# Usar nome padrão se não fornecido
if [ -z "$REPO_NAME" ]; then
    REPO_NAME="hackatonaws"
fi

echo ""
echo "🔧 Configurando remote origin..."

# Remover remote existente se houver
git remote remove origin 2>/dev/null || true

# Adicionar novo remote
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git

echo "✅ Remote configurado: https://github.com/$GITHUB_USER/$REPO_NAME.git"
echo ""

# Verificar remotes
echo "📋 Remotes configurados:"
git remote -v
echo ""

echo "🚀 Próximos passos:"
echo "1. Crie o repositório '$REPO_NAME' no GitHub (https://github.com/new)"
echo "2. Execute: git push -u origin master"
echo ""
echo "💡 Comandos úteis:"
echo "   git push                    # Enviar mudanças"
echo "   git pull                    # Baixar mudanças"
echo "   git status                  # Ver status"
echo "   git log --oneline           # Ver histórico"
echo ""
