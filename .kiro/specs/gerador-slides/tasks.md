# Tasks: Gerador de slides SENAI

Tasks em ondas: cada onda depende da anterior; as tasks dentro de uma onda são independentes e podem rodar em paralelo (Run all Tasks).

## Onda 1

- [x] 1. Ler e checar o YAML
  - `validar_arquivo` e `_estrutura` em `senai_slides/validador.py`
  - YAML quebrado com número de linha, arquivo fora de UTF-8, campos e tipos de slide
  - _Requisitos: 1.1–1.6_

## Onda 2

- [x] 2. Limites de texto por tipo de slide
  - Título, tópicos (2 a 5, ou 3 com destaque) e destaque; espaços repetidos não contam
  - Teste de pior caso: deck no limite de tudo precisa desenhar sem `TextoLongoDemais`
  - _Requisitos: 2.1–2.6_
- [x] 3. Ordem do deck
  - Capa primeiro, encerramento por último, um de cada
  - _Requisitos: 3.1–3.2_
- [x] 4. Limite de 20 slides
  - _Requisitos: 4.1_
- [x] 5. Gerador
  - `senai_slides/gerador.py` e opção `--gerar` na CLI, que só gera deck sem erro
  - _Requisitos: 6.1–6.3_

## Onda 3

- [x] 6. Avisos de conteúdo e testes
  - Destaque demais, conteúdo sem seção, seção vazia, caixa alta, destaque sem ponto, título repetido
  - `tests/test_validador.py`
  - _Requisitos: 5.1_
- [x] 7. Skill `gerador-slides`
  - `.kiro/skills/gerador-slides/SKILL.md`; teste do frontmatter em `tests/test_kiro.py`
  - _Requisitos: 7.1–7.3_
- [x] 8. Hooks
  - `validar-slides.json` (FileSave) e `caca-segredos.json` (PostTaskExecution) + `scripts/caca_segredos.py`
  - Testes: JSON válido, gatilhos aceitos pelo Kiro, matcher, caça-segredos com chave falsa
  - _Requisitos: 8.1–8.3_
- [x] 9. Agente portátil em YAML
  - `agente/AGENTE_SLIDES_SENAI.md` passa a devolver YAML; exemplo igual a `slides/exemplo.yaml`
  - _Requisitos: 9.1–9.2_
- [x] 10. Documentação
  - README, steering (`tech`, `structure`, `product`) e README dos hooks

## Onda 4

- [x] 11. Slide de diagrama
  - `Apresentacao.diagrama` em `senai_slides/apresentacao.py`, no layout de `.kiro/steering/referencias/diagrama.png`
  - Validador: campos dos itens, de 3 a 6 itens, limites de texto; diagrama conta como conteúdo da seção nos avisos
  - Agente, `slides/exemplo.yaml` (etapas da desenergização), identidade visual e README
  - Testes: cores e posição dos cartões, margem da logo e da borda, pior caso dos limites
  - _Requisitos: 1.4, 2.1, 2.7, 5.1, 10.1–10.4_

## Pendente

- [ ] Testar a skill no Kiro com um pedido real ("Gere uma aula de 10 slides sobre NR-12")
- [ ] Testar o prompt portátil em duas IAs de chat diferentes
- [ ] Desafio extra: caça-segredos como pre-commit do Git
