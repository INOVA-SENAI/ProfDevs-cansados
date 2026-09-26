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
2. **Biblioteca `senai_slides`**: o validador confere o deck (campos, layouts, limites de texto, ícones, seções) e, se não houver erro, monta um `.pptx` editável no padrão SENAI 2026 (ver `identidade-visual.md`), com capa, agenda, divisórias, 11 layouts de conteúdo e encerramento, além de uma prévia PNG por slide e um PDF. A montagem veio do gerador do repositório icrcode/teste-kiro.

A IA só escreve o conteúdo; todo o visual é feito pela biblioteca. Assim o resultado é sempre fiel à marca. As imagens da capa e dos slides `ilustracao` são fotos reais do Wikimedia Commons ou imagens fotográficas criadas pela Amazon Bedrock (gerador de imagens do João), conforme o contexto do slide; entram numa moldura fixa, com crédito, e a logo e os textos nunca passam pela IA de imagem.

## Público-alvo
<!-- Quem são os usuários finais? Ex: desenvolvedores, estudantes, professores de SENAI... -->
Professores do SENAI que precisam montar apresentações de aula rapidamente, sem ferramenta de design.

## Objetivos
<!-- Liste os objetivos principais do projeto -->
- [x] Agente (skill no Kiro e prompt portátil) que escreve o conteúdo da aula em um deck YAML
- [x] Validador que confere o deck antes de gerar, com mensagens em português
- [x] Biblioteca que monta apresentações fiéis à identidade visual do SENAI: capa, agenda, divisórias, 11 layouts de conteúdo (tópicos, cartões, números, processo, linha do tempo, comparação, gráfico, destaque, tabela, ilustração e diagrama) e encerramento
- [x] Imagens realistas: fotos reais com crédito ou imagens criadas por IA, com cache para não buscar nem pagar duas vezes
- [x] O professor escolhe se quer imagens (nenhuma, só fotos ou também IA) e vê a estimativa de custo antes; imagem por IA só é cobrada com `--aceitar-custo`
- [x] Saída pronta para usar: `.pptx` editável com notas do apresentador, prévia PNG de cada slide e PDF

## Status
<!-- Ex: Em desenvolvimento, MVP, Produção -->
MVP pronto
