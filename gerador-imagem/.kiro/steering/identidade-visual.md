---
inclusion: always
---

# Identidade Visual: Modelo de Apresentação SENAI 2026

Todo slide gerado DEVE seguir este padrão. Referência original: `assets/senai/modelo_apresentacao_senai_2026.pdf`.

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

### 4. Encerramento
- Fundo azul, logo branco à esquerda, contatos do SENAI/SC à direita
- É fixo (não gerado por IA) — usar o modelo original

## Assets Oficiais (`assets/senai/`)
- `logo_senai_branco.png` — logo para fundo azul (capa)
- `logo_senai_azul.png` — logo para fundo branco (conteúdo e divisória); PNG 320x85 com fundo transparente, recortado sem margem — é este arquivo que o código sobrepõe na imagem gerada
- `barra_lateral.png` — barra lateral laranja/azul dos slides internos

## Regra sobre o Logo
Modelos de IA de imagem não reproduzem logotipos com fidelidade. O logo oficial NUNCA deve ser desenhado pela IA: a imagem é gerada sem logo e o arquivo oficial de `assets/senai/` é sobreposto por código na posição correta.
