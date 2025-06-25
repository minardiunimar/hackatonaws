#!/bin/bash

echo "=== Setup GitHub para Hackaton AWS ==="
echo ""

# Solicitar nome de usuário do GitHub
read -p "Digite seu nome de usuário do GitHub: " GITHUB_USER

# Solicitar nome do repositório (com sugestão)
read -p "Digite o nome do repositório [processador-documentos-hackaton-aws]: " REPO_NAME
REPO_NAME=${REPO_NAME:-processador-documentos-hackaton-aws}

echo ""
echo "Configurando repositório remoto..."

# Remover remote existente se houver
git remote remove origin 2>/dev/null || true

# Adicionar novo remote
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git

echo "Remote configurado: https://github.com/$GITHUB_USER/$REPO_NAME.git"
echo ""

# Verificar se há commits
if git log --oneline -n 1 >/dev/null 2>&1; then
    echo "Enviando código para o GitHub..."
    
    # Tentar push
    if git push -u origin master; then
        echo ""
        echo "✅ Sucesso! Seu projeto foi enviado para:"
        echo "   https://github.com/$GITHUB_USER/$REPO_NAME"
        echo ""
        echo "🎉 Parabéns! Seu projeto do Hackaton AWS está no GitHub!"
    else
        echo ""
        echo "❌ Erro ao enviar. Verifique se:"
        echo "   1. O repositório existe no GitHub"
        echo "   2. Você tem permissão de escrita"
        echo "   3. Suas credenciais estão configuradas"
        echo ""
        echo "Para configurar credenciais:"
        echo "   git config --global user.name 'Seu Nome'"
        echo "   git config --global user.email 'seu@email.com'"
    fi
else
    echo "❌ Nenhum commit encontrado. Execute primeiro:"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
fi
