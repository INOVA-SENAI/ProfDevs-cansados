---
inclusion: always
---

# Identidade Visual: Modelo SENAI 2026 (Identidade Nova)

Toda apresentação gerada DEVE seguir este padrão. O tema foi extraído do modelo SENAI 2026 "Identidade Nova" pelo gerador do repositório icrcode/teste-kiro (licença MIT) e fica em `senai_slides/tema.py`; os layouts, em `senai_slides/layouts.py`. O arquivo do modelo não fica no projeto: a cópia do teste-kiro tinha uma colagem com fotos de alunos e de um professor, que não pode ser distribuída (LGPD).

## Formato
- 16:9, 13,33 x 7,5 polegadas (a mesma proporção do modelo)
- Saída: `.pptx` editável; prévia PNG de 1920x1080 por slide e um PDF

## Paleta
| Uso | Hex |
|---|---|
| Azul SENAI: títulos, painéis, fundos de divisória e encerramento | `#164194` |
| Laranja SENAI: acentos, números, faixas | `#E84910` |
| Texto de dados | `#1E2A44` |
| Texto secundário | `#5B6475` |
| Fundo de cartões | `#F3F5FA` |
| Fundo de ícones (azul / laranja) | `#E6ECF7` / `#FDE9E1` |
| Séries de gráfico, nesta ordem (validada para daltonismo) | `#7FA3E3`, `#2458B8`, `#E84910` |
| Só no `diagrama`, do primeiro ao último item | `#E84910`, `#F08A00`, `#52AE32`, `#009E96`, `#008AD1`, `#164194` |

## Tipografia e ícones
- **Open Sans** (a fonte do modelo), em `senai_slides/assets/fonts/`. No Windows, é instalada para o usuário na primeira geração, para o PowerPoint mostrar a fonte certa
- Textos longos têm a fonte reduzida até caberem na caixa (`tema.tamanho_que_cabe`)
- Ícones **Material Symbols Rounded** (Google), só da lista de `senai_slides/icones.py`; nunca emojis

## Slides
- **Capa:** fundo branco; logo SENAI (e, com `logo_curso: true`, o logo "Técnico DESI"); traço laranja, título grande em azul, linha "UC: ..." em itálico, tags em pílulas; faixa azul e laranja no rodapé. Com `imagem`, a ilustração fica à direita
- **Agenda:** lista numerada dos títulos dos slides (ou das seções, em apresentações longas), a partir de 4 slides de conteúdo
- **Divisória:** fundo azul com um degradê diagonal suave (`#1A4AA3` a `#0F3279`), sem fotos de pessoas, "SEÇÃO", número grande, nome e descrição da seção, logo branco
- **Conteúdo:** fundo branco, faixa vertical à esquerda (laranja no topo, corte cinza, azul), logo SENAI no alto à direita, título em azul, subtítulo em cinza e "Página X de Y". O conteúdo segue um dos 11 layouts de `layouts.py`
- **`ilustracao`:** itens em cartões à esquerda e a imagem à direita, em quadrado com cantos arredondados (recortada no centro), com o crédito em letra pequena embaixo: "Foto: autor, licença, via Wikimedia Commons" ou "Imagem gerada por IA"
- **`diagrama`:** modelo em `referencias/diagrama.png`. Título no círculo central, com uma bolinha na cor de cada item; de 3 a 6 itens em cartões coloridos em volta (a primeira metade à esquerda, de cima para baixo), título em caixa alta e texto em branco, e o ícone do item no círculo branco. Os círculos de cada lado são ligados por um arco em degradê. O desenho de fundo é uma imagem; textos e ícones continuam editáveis
- **Encerramento:** o mesmo fundo azul da divisória, logo branco, "Obrigado!" e os contatos do SENAI/SC com ícones

## Apresentação
- Transição suave (fade) entre slides e entrada animada dos gráficos
- Notas do apresentador em cada slide

## Imagens
- Sempre realistas: fotos reais (Wikimedia Commons) ou imagens fotográficas criadas por IA. Nada de pixel art, desenho animado ou ilustração
- Toda imagem leva o crédito ou o aviso de IA embaixo
- Nenhuma foto de aluno ou de pessoa identificável sem autorização

## Regra sobre o logo
O logo é sempre o arquivo oficial, colado pela biblioteca. Nunca redesenhar, recolorir (fora a versão branca para fundo azul) ou distorcer. A IA de imagem nunca desenha logo nem texto.
