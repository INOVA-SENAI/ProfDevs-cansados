---
inclusion: always
---

# Identidade Visual: Modelo de Apresentação SENAI 2026

Todo slide gerado DEVE seguir este padrão. Referência original: `senai_slides/assets/modelo_apresentacao_senai_2026.pdf`. A implementação fica em `senai_slides/apresentacao.py`.

## Formato
- Proporção 16:9 (paisagem)

## Paleta de Cores (extraída do .pptx oficial)
| Uso | Cor | Hex |
|---|---|---|
| Azul SENAI (principal: fundos de capa, títulos, textos) | Azul | `#164193` |
| Laranja SENAI (destaques, marcadores de lista, frases de impacto) | Laranja | `#E8490F` |
| Verde (detalhe pontual, ex: ponto final de frase de destaque) | Verde | `#52AE32` |
| Azul claro (secundária, uso raro) | Azul claro | `#008AD1` |
| Fundo de slides internos | Branco | `#FFFFFF` |
| Só no diagrama, para completar 6 cores (não é do .pptx oficial) | Âmbar | `#F08A00` |
| Só no diagrama, para completar 6 cores (não é do .pptx oficial) | Turquesa | `#009E96` |

## Tipografia
- Fonte principal: **Century Gothic** (geométrica, traço fino) — títulos e corpo
- Fallback: Arial
- Títulos de capa e divisória em CAIXA ALTA

## Tipos de Slide

### 1. Capa
- Fundo azul `#164193` sólido
- Logo SENAI branco com assinatura "Serviço Nacional de Aprendizagem Industrial" no canto superior esquerdo
- Título em branco, CAIXA ALTA, grande, alinhado à esquerda na metade inferior

### 2. Conteúdo interno
- Fundo branco
- Barra lateral vertical à esquerda: faixa laranja no topo, corte diagonal branco, faixa azul até o fim
- Logo SENAI azul (com o "i" laranja) no canto superior direito
- Título em azul `#164193`, no topo à esquerda (não em caixa alta)
- Lista de tópicos em azul com marcadores laranja
- Opcional: frase de destaque em laranja `#E8490F` na parte inferior
- Pouco texto — não sobrecarregar o slide

### 3. Divisória (seção)
- Mesmo fundo branco, barra lateral e logo azul do slide de conteúdo
- Apenas o título da seção, em azul `#164193`, CAIXA ALTA, alinhado à esquerda na parte inferior

### 4. Diagrama
Modelo para qualquer gráfico ou esquema: `referencias/diagrama.png` (infográfico circular). O layout é o do modelo; as cores são as da paleta SENAI.
- Mesmo fundo branco, barra lateral e logo azul do slide de conteúdo
- Círculo central branco, com sombreado suave e sombra; título em azul `#164193`, negrito, CAIXA ALTA, com uma bolinha na cor de cada item logo abaixo
- De 3 a 6 itens em volta: a primeira metade à esquerda, de cima para baixo, e o resto à direita
- Cada item é um cartão arredondado na cor do item, com título em negrito e CAIXA ALTA e um texto curto, ambos em branco; nos cartões da direita, o texto é alinhado pela direita
- Na ponta de dentro de cada cartão, um círculo branco com o número do item (01, 02...) na cor do item
- Os círculos de cada lado são ligados por um arco em degradê entre as cores dos itens
- Cores dos itens, nesta ordem: laranja, âmbar, verde, turquesa, azul claro e azul SENAI. Com menos de 6 itens, as cores são espalhadas pela sequência: sempre começa no laranja e termina no azul

### 5. Encerramento
- Fundo azul, logo branco à esquerda, linha vertical branca, contatos do SENAI/SC à direita (site em laranja, negrito e sublinhado)
- Conteúdo fixo, sem parâmetros
- Diferença conhecida: os ícones de redes sociais do modelo são vetoriais no .pptx e não foram reproduzidos

## Tamanho de saída
- 1920x1080 px por slide; o PDF usa 144 dpi, o que dá 13,33 x 7,5 polegadas (tamanho padrão de slide 16:9)

## Assets Oficiais (`senai_slides/assets/`)
- `logo_senai_branco.png` — logo com assinatura, para fundo azul (capa e encerramento)
- `logo_senai_azul.png` — logo para fundo branco (conteúdo e divisória); PNG 320x85 com fundo transparente
- `barra_lateral.png` — barra lateral laranja/azul dos slides internos

## Regra sobre o Logo
O logo é sempre o arquivo oficial, colado pela biblioteca. Nunca redesenhar, recolorir ou distorcer.
