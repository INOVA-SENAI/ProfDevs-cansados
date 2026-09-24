# Spec: Geração de Imagem de Slide

---

## Overview

<!-- Descreva em 2-3 frases o que essa feature faz e por que ela existe. -->
Permite que o usuário digite um prompt de texto livre (um tema ou ideia) e receba, em troca, uma imagem única no formato de slide (proporção 16:9, com título e conteúdo visual), gerada por IA generativa de imagem.

**Problema que resolve:**
<!-- Ex: Usuários não conseguem... / O sistema ainda não suporta... -->
Professores e alunos não têm uma forma rápida de gerar uma imagem de slide pronta a partir de uma ideia, sem abrir uma ferramenta de design.

**Solução proposta:**
<!-- Ex: Implementar um componente que... -->
Um app Streamlit onde o usuário digita um prompt/tema; o sistema monta um prompt final padronizado (incluindo instruções fixas de formato slide: proporção 16:9, layout com título e conteúdo) e chama a API de imagem da OpenAI (gpt-image-1 / DALL-E 3), exibindo o resultado e permitindo o download.

---

## Requirements

<!-- Liste os requisitos funcionais e não-funcionais da feature.
Use linguagem clara: "O sistema DEVE...", "O usuário PODE...", "NÃO É necessário..." -->

### Funcionais
- [ ] RF01 - O usuário PODE digitar um prompt/tema livre em um campo de texto
- [ ] RF02 - O usuário DEVE escolher o tipo de slide: Capa, Conteúdo ou Divisória
- [ ] RF03 - O sistema DEVE montar um prompt final padronizado, combinando o prompt do usuário com as regras do tipo escolhido definidas em `.kiro/steering/identidade-visual.md` (paleta, tipografia, layout)
- [ ] RF04 - O prompt DEVE instruir a IA a deixar livre a área do logo e NÃO desenhar logotipo
- [ ] RF05 - O sistema DEVE chamar a API de geração de imagem da OpenAI com o prompt final
- [ ] RF06 - O sistema DEVE sobrepor o logo oficial (`senai/`) na posição correta do tipo de slide: branco no canto superior esquerdo (Capa), azul no canto superior direito (Conteúdo/Divisória)
- [ ] RF07 - O sistema DEVE exibir a imagem final na tela
- [ ] RF08 - O usuário PODE baixar a imagem final em PNG

### Não-funcionais
- [ ] RNF01 - A chave da API da OpenAI DEVE ser lida de uma variável de ambiente, nunca hardcoded no código
- [ ] RNF02 - O sistema DEVE tratar erros da API (timeout, prompt rejeitado, etc.) exibindo uma mensagem simples ao usuário, sem quebrar o app

### Fora de escopo
<!-- O que explicitamente NÃO faz parte desta feature -->
- Gerar um deck completo com múltiplos slides
- Editar a imagem gerada dentro do app
- Slide de Encerramento (é fixo; usar o do modelo original)

---

## Tasks

<!-- Quebre a implementação em tasks atômicas e ordenadas. -->

- [ ] **Task 1:** Criar estrutura base do app Streamlit em `app/main.py`
- [ ] **Task 2:** Criar módulo de montagem de prompt em `prompts/slide_prompt.py`, com um template por tipo de slide (Capa, Conteúdo, Divisória) seguindo `identidade-visual.md`
- [ ] **Task 3:** Integrar chamada à API de imagem da OpenAI em tamanho paisagem (leitura da chave via `.env`)
- [ ] **Task 4:** Criar `app/logo_overlay.py` que sobrepõe o logo oficial com Pillow conforme o tipo de slide
- [ ] **Task 5:** Implementar UI: campo de prompt, seletor de tipo, botão de gerar, exibição e download
- [ ] **Task 6:** Escrever testes (`tests/`) para a montagem de prompt e para a sobreposição do logo
- [ ] **Task 7:** Documentar no README como rodar o app e configurar a chave de API

---

## Notas de Design

<!-- Decisões técnicas, alternativas consideradas, diagramas, etc. -->
- Optou-se por IA generativa de imagem (texto→imagem) em vez de um template renderizado. Risco conhecido e aceito: texto renderizado por modelos de imagem nem sempre sai perfeitamente legível.
- Sem backend separado no MVP: toda a lógica roda dentro do próprio app Streamlit.
- Padrão visual: Modelo de Apresentação SENAI 2026 — regras completas em `.kiro/steering/identidade-visual.md`.
- O logo é aplicado por código (Pillow), não pela IA, porque modelos de imagem distorcem logotipos. A IA gera o slide com a área do logo vazia.

---

## Critérios de Aceite

<!-- Como saberemos que a feature está pronta? -->
- [ ] Usuário consegue digitar um prompt, escolher o tipo e receber uma imagem em formato slide (16:9)
- [ ] A imagem segue a paleta SENAI (azul `#164193`, laranja `#E8490F`) e o layout do tipo escolhido
- [ ] O logo presente na imagem é o arquivo oficial, na posição correta
- [ ] A imagem gerada é exibida na tela e pode ser baixada
- [ ] A chave de API não está hardcoded em nenhum arquivo versionado
