---
inclusion: always
---

# Produto: ProfDevs-cansados

## Nome do Projeto
ProfDevs-cansados

## Descrição
<!-- Descreva aqui o propósito principal do projeto. O que ele faz? Qual problema resolve? -->
O projeto tem duas partes:

1. **Agente de Slides SENAI**: no Kiro, a skill `gerador-slides`; em qualquer outra IA de chat, o prompt portátil `agente/AGENTE_SLIDES_SENAI.md`. A IA conversa sobre a aula e escreve um deck em YAML com o conteúdo dos slides.
2. **Biblioteca `senai_slides`**: o validador confere o deck (limites de texto, ordem, campos) e, se não houver erro, desenha os slides no padrão do Modelo de Apresentação SENAI 2026 (ver `identidade-visual.md`) e salva PNGs e um PDF.

A IA só escreve o conteúdo; todo o visual é feito pela biblioteca. Assim o resultado é sempre fiel à marca, sem depender de API paga nem de IA de imagem.

## Público-alvo
<!-- Quem são os usuários finais? Ex: desenvolvedores, estudantes, professores de SENAI... -->
Professores do SENAI que precisam montar apresentações de aula rapidamente, sem ferramenta de design.

## Objetivos
<!-- Liste os objetivos principais do projeto -->
- [x] Agente (skill no Kiro e prompt portátil) que escreve o conteúdo da aula em um deck YAML
- [x] Validador que confere o deck antes de gerar, com mensagens em português
- [x] Biblioteca que transforma o script em slides fiéis à identidade visual do SENAI (capa, conteúdo, divisória, diagrama e encerramento)
- [x] Saída pronta para usar: um PNG por slide e um PDF com a apresentação completa

## Status
<!-- Ex: Em desenvolvimento, MVP, Produção -->
MVP pronto
