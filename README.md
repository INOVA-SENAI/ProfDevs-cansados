# ProfDevs-cansados

Crie apresentações de aula no padrão visual do **SENAI 2026** conversando com uma IA.

A IA escreve o conteúdo da aula em um **deck YAML**. O validador confere o deck (tamanho dos textos, ordem dos slides, campos) e, se estiver tudo certo, a biblioteca `senai_slides` gera os slides em PNG e em PDF, com as cores, a fonte, a logo e o layout oficiais.

> **Status:** MVP pronto e testado. Não precisa de chave de API nem tem custo por slide.

## Como funciona

```
Pedido ──▶ IA (skill no Kiro ou prompt em qualquer chat) ──escreve──▶ slides/<aula>.yaml
                                                                          │
                                        python -m senai_slides.validador  │  (no Kiro: ao salvar)
                                                                          ▼
                                             erro? mensagem clara, nada é gerado
                                             ok?   outputs/<aula>/ slide_01.png ... + <aula>.pdf
```

**A IA escreve, o código desenha.** A IA nunca escreve código de desenho, e o validador não deixa gerar um deck fora do padrão. Por isso o visual sai sempre igual ao modelo oficial, sem logo deformada nem texto cortado.

## Instalação (uma vez só)

Requisito: Python 3.10 ou mais novo.

```bash
git clone <url-do-repositorio>
cd ProfDevs-cansados
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
```

> No Windows, use `python` ou `py`. O comando `python3` pode abrir a Microsoft Store.

## Como usar

### No Kiro

Peça no chat: *"Gere uma aula de 10 slides sobre NR-10 para a turma de Eletrotécnica"*. A skill `gerador-slides` entra sozinha (ou chame com `/gerador-slides`): ela escreve `slides/<aula>.yaml`, roda o validador, corrige os erros e gera os slides. Depois disso, cada vez que você editar e salvar o YAML, o hook gera de novo.

### Em qualquer outra IA (ChatGPT, Claude, Gemini, Copilot)

1. Abra [agente/AGENTE_SLIDES_SENAI.md](agente/AGENTE_SLIDES_SENAI.md), copie **todo** o conteúdo e cole como primeira mensagem na IA.
2. Na mensagem seguinte, peça a aula. Se tiver um trecho de apostila, cole junto.
3. Salve o YAML que a IA devolver em `slides/` (ex.: `slides/aula_nr10.yaml`).
4. Com o `venv` ativo, rode:
   ```bash
   python -m senai_slides.validador slides/aula_nr10.yaml --gerar
   ```
5. Os slides aparecem em `outputs/<nome-da-aula>/`: um PNG por slide e um PDF com a apresentação completa.

Se aparecer algum **erro**, cole a mensagem na mesma conversa. O agente já sabe corrigir. Linhas de **aviso** não impedem a geração.

## O deck

```yaml
nome: NR-10 Introducao
slides:
  - tipo: capa
    titulo: Segurança em Instalações Elétricas
  - tipo: divisoria
    titulo: Riscos elétricos
  - tipo: conteudo
    titulo: Principais riscos da eletricidade
    topicos:
      - "Choque elétrico: corrente passando pelo corpo"
      - Incêndios por sobrecarga ou curto-circuito
    destaque: Todo circuito deve ser tratado como energizado até prova em contrário.
  - tipo: encerramento
```

| Tipo | Slide | Limites |
|---|---|---|
| `capa` | Fundo azul, logo SENAI, título em caixa alta | título até 60 caracteres |
| `divisoria` | Abertura de seção: fundo branco, barra lateral, título grande | título até 40 |
| `conteudo` | Título, tópicos com marcadores laranja e, opcionalmente, uma frase de destaque | título até 50; de 2 a 5 tópicos de até 90 (até 3 com destaque); destaque até 100 |
| `diagrama` | Círculo central com o título e, em volta, cartões coloridos e numerados (modelo em [.kiro/steering/referencias/diagrama.png](.kiro/steering/referencias/diagrama.png)) | título até 30; de 3 a 6 itens, cada um com `titulo` até 20 e `texto` até 70 |
| `encerramento` | Logo e contatos do SENAI/SC | sem campos |

```yaml
  - tipo: diagrama
    titulo: Etapas da desenergização
    itens:
      - titulo: Seccionamento
        texto: Desligar e abrir o circuito com um dispositivo de manobra adequado.
      - titulo: Impedimento
        texto: Bloquear e travar o dispositivo para ninguém religar o circuito.
      - titulo: Ausência de tensão
        texto: Testar com detector de tensão antes de tocar no circuito.
```

Capa sempre no início, encerramento sempre no fim, no máximo 20 slides. O exemplo completo está em [slides/exemplo.yaml](slides/exemplo.yaml), e as regras detalhadas, no [prompt do agente](agente/AGENTE_SLIDES_SENAI.md). Quem preferir Python pode continuar usando a classe `Apresentacao` direto.

## Estrutura do projeto

| Caminho | O que tem |
|---|---|
| [agente/AGENTE_SLIDES_SENAI.md](agente/AGENTE_SLIDES_SENAI.md) | Regras de conteúdo e limites; é também o prompt para colar em outra IA |
| [slides/](slides/) | Decks das aulas em YAML |
| [senai_slides/validador.py](senai_slides/validador.py) | Confere o deck e, com `--gerar`, gera os slides |
| [senai_slides/gerador.py](senai_slides/gerador.py) | Passa o deck validado para a `Apresentacao` |
| [senai_slides/apresentacao.py](senai_slides/apresentacao.py) | Desenha os slides |
| [senai_slides/assets/](senai_slides/assets/) | Logos, barra lateral e modelo PDF oficiais. **Não edite.** |
| [scripts/caca_segredos.py](scripts/caca_segredos.py) | Procura chaves da AWS no repositório |
| [tests/](tests/) | Testes automatizados |
| `outputs/` | Slides gerados (fora do git) |

## Trabalhamos com o Kiro

Antes de mexer no projeto, leia a pasta `.kiro/`:

| Arquivo | O que tem |
|---|---|
| [.kiro/steering/product.md](.kiro/steering/product.md) | Objetivo e público do produto |
| [.kiro/steering/tech.md](.kiro/steering/tech.md) | Stack, comandos e regras técnicas |
| [.kiro/steering/structure.md](.kiro/steering/structure.md) | Pastas e convenções de nomes |
| [.kiro/steering/identidade-visual.md](.kiro/steering/identidade-visual.md) | Cores, fonte e layout de cada tipo de slide |
| [.kiro/specs/gerador-slides/](.kiro/specs/gerador-slides/) | Spec atual: `requirements.md` (EARS), `design.md` e `tasks.md` (em ondas) |
| [.kiro/skills/gerador-slides/SKILL.md](.kiro/skills/gerador-slides/SKILL.md) | Skill do agente: escreve o deck, valida e gera |
| [.kiro/hooks/](.kiro/hooks/) | Validar e gerar ao salvar `slides/*.yaml`; caça-segredos ao fim de cada task |

## Identidade visual

- Azul SENAI `#164193`, laranja `#E8490F` e verde `#52AE32` (só no ponto final do destaque)
- No diagrama, os itens vão do laranja ao azul, passando por âmbar, verde, turquesa e azul claro
- Fonte Century Gothic, que já vem com o Windows/Office. Se não estiver instalada, a biblioteca usa Arial.
- Slides em 1920x1080; o PDF sai no tamanho padrão de slide 16:9

## Para quem vai desenvolver

```bash
pytest            # 118 testes
ruff check .      # lint
ruff format .     # formatação
```

- **Regra de ouro:** se mudar um tipo de slide, um campo do deck ou um limite do validador, atualize também o [prompt do agente](agente/AGENTE_SLIDES_SENAI.md). Um teste valida e gera o exemplo do prompt e falha se os dois divergirem.
- Antes de commitar: `python scripts/caca_segredos.py`.
- Crie branches no formato `feature/nome-da-feature` ou `fix/descricao-do-bug`.
- Arquivos Python em `snake_case`; pastas em minúsculas e sem espaços.

## O que falta

- [ ] Testar a skill no Kiro e o prompt em pelo menos duas IAs diferentes (ex.: ChatGPT e Gemini) com um tema real de aula
- [ ] Desafio extra: rodar o caça-segredos como pre-commit do Git
- [ ] Opcional: ícones de redes sociais no slide de encerramento (no modelo original eles são vetoriais e não foram reproduzidos)
- [ ] Opcional: exportar também em `.pptx` editável
