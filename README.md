# Super Clips Studio

Skill unificada para perfil, cortes, layout e agendamento no TikTok, Instagram e Kwai, com comunicação breve e carregamento seletivo de contexto. Autor das novas configurações: NicollasDev7. Histórico e créditos anteriores preservados.

Instale este repositório como uma única pasta de skill chamada `super-clips-studio` e invoque **“Use $super-clips-studio para configurar meu canal”**. O ponto de entrada é [SKILL.md](SKILL.md). A configuração inicial aceita nome, @ por rede, foto opcional e layout enviado pelo usuário ou padrão. Não é necessário ativar as skills antigas.

Python 3.11+, FFmpeg e ffprobe são necessários para o novo renderer portátil. `python scripts/render_clip.py JOB.json` gera um MP4 e registro técnico; a revisão editorial e a publicação são conduzidas pelo agente com ferramentas autorizadas. Referências de edição, publicação e métricas são carregadas somente quando necessárias. Origem das decisões: [references/origins.md](references/origins.md).

A meta de reduzir tokens em 70% exige comparação medida; não é garantia. O pacote não inclui contas, vídeos, credenciais ou infraestrutura em nuvem. Os agendamentos só são declarados concluídos com confirmação das plataformas.

## Motor legado

As instruções abaixo documentam os comandos anteriores do Stream Clip Studio. O onboarding dedicado e os presets desse motor são opcionais; o fluxo e layout atuais estão no SKILL.md. Não execute login em navegador separado quando a sessão do usuário já estiver disponível nas ferramentas do ambiente.

Uma skill para Codex no Windows que conecta Gaming Clip, edição vertical e agendamento nativo no TikTok Studio.

## Primeiro uso

Instale Python 3.11+, Git para Windows e o GitHub CLI. Com acesso ao repositório, abra o PowerShell no projeto onde usa o Codex:

```powershell
gh auth login
New-Item -ItemType Directory -Force .agents/skills | Out-Null
gh repo clone NicollasDev7/stream-clip-studio .agents/skills/stream-clip-studio
```

Abra um chat nesse workspace e peça **“Use stream-clip-studio para configurar meu perfil”**.

Também dá para executar, dentro desta pasta:

```powershell
.\setup.ps1
```

O instalador coloca as dependências em uma venv, usa Chromium do Playwright e baixa Bun, Gaming Clip, FFmpeg, yt-dlp e o modelo do Whisper conforme necessário. A configuração pede **nome de exibição, foto, @ e pasta de mídia**. Em seguida abre o TikTok Studio para o login manual em um perfil dedicado. O Chromium fecha quando a tela de upload estiver pronta. A configuração não publica nada.

Se você já tem o Gaming Clip instalado, use `.\setup.ps1 onboard --existing-engine 'C:\caminho\gaming-clip'`. Use `.\run.ps1 login` para renovar a sessão. `onboard --no-login` prepara as configurações sem abrir o navegador.

As configurações pessoais e a sessão ficam em `%LOCALAPPDATA%\stream-clip-studio`. O perfil do Chromium, o SQLite, os logs e as capturas ficam na subpasta `tiktok`. Os originais e os MP4s ficam na pasta escolhida. Esses dados não fazem parte do repositório.

## Do original ao MP4

```powershell
.\run.ps1 import 'https://www.youtube.com/watch?v=ID_DO_VIDEO'
.\run.ps1 import 'C:\Videos\LIVE DIA 3.mp4'
.\run.ps1 analyze 'D:\Clips\LIVE DIA 3.mp4' --lang pt --min 90 --max 120
.\run.ps1 gaming show ID_DO_PROJETO
.\run.ps1 gaming transcript ID_DO_PROJETO --from 1:30:00 --to 1:31:00
.\run.ps1 render 'D:\Clips\LIVE DIA 3.mp4' --start 5400 --duration 60 --streamer '@streamer' --webcam '20,30,650,354' --title 'Era só um carinho' --cover-title 'ERA SÓ UM CARINHO' --cover-at 18
```

`--webcam` é o recorte em pixels da gravação. Quando a webcam estiver ausente, omita a opção. `--focus-x` ajusta o centro horizontal do jogo. `--cover-at` é relativo ao começo do corte. Para legendas dinâmicas, use `--words palavras.json` com uma lista cronológica de palavras, por exemplo:

```json
[{"text":"Olha","start":0.12,"end":0.42,"language":"pt"}]
```

A skill seleciona e revisa os intervalos e marca o idioma das falas para alimentar o renderer. O Whisper global não classifica sozinho cada fala do corte. O MP4 final usa cabeçalho compacto com foto/nome/@ e título, gameplay de ponta a ponta, webcam pequena sobreposta no canto superior esquerdo e crédito do streamer sobre o jogo. A capa aparece somente no primeiro frame. O renderer testa NVENC e cai para libx264 quando a GPU não está disponível. A transcrição usa o Whisper do Gaming Clip instalado.

No quadro de 1080 × 1920, a gameplay vai de y=300 até a base, ocupando 84% da altura, sem bordas laterais nem rodapé branco. A webcam mede 270 × 220 px, em x=36/y=332; o recorte deve privilegiar rosto, fones e ombros. A presença da webcam não diminui a área do jogo. Textos e créditos respeitam margens de 104 px à esquerda e 144 px à direita. A marca discreta usa até 46 px e 15% de opacidade. O selo opcional `--badge 'GTA 6'` aparece no cabeçalho; sem a opção, ele é omitido.

Antes de produzir um lote, gere uma prévia estática do enquadramento real:

```powershell
.\run.ps1 render 'D:\Clips\LIVE DIA 3.mp4' --start 5400 --duration 60 --streamer '@streamer' --webcam '20,30,650,354' --title 'Era só um carinho' --cover-title 'ERA SÓ UM CARINHO' --cover-at 18 --badge 'GTA 6' --preview
```

`--preview` salva apenas um arquivo `.preview.png`, sem MP4, upload ou agendamento. A imagem usa o frame de `--cover-at`, sem a chamada de capa, para avaliar o layout normal. Ajuste `--focus-x` se o recorte vertical tirar o assunto principal da tela. A prévia pode coexistir com o MP4 de mesmo título; arquivos existentes não são sobrescritos. Vídeos já agendados não são substituídos automaticamente.

As atualizações deste layout são de **NicollasDev7**. Esta versão continua o projeto anterior em [Jeffvff/stream-clip-studio](https://github.com/Jeffvff/stream-clip-studio), preservando seu histórico e os demais fluxos.

## TikTok Studio

Edite o YAML local em `%LOCALAPPDATA%\stream-clip-studio\schedule.yaml`, ou copie-o como configuração de lote. Em `folder`, coloque **a subpasta de MP4s do original**, não a pasta que guarda as lives completas. Configure data, horários, fuso, privacidade, ordem, legendas e hashtags no YAML. Depois use:

```powershell
.\run.ps1 schedule plan --config 'C:\caminho\lote.yaml' --limit 3
.\run.ps1 schedule run --approve HASH_DA_PREVIA
.\run.ps1 schedule pending
.\run.ps1 schedule report
.\run.ps1 schedule reconcile --config 'C:\caminho\lote.yaml'
```

A aprovação é do lote exato. A confirmação exige evidência na lista do Studio. Se uma confirmação ficar incerta, a reconciliação consulta a lista sem reenviar.

O fluxo usa a interface visível do TikTok Studio. Se a conta ou a versão do site mostrar controles diferentes, revise os seletores no YAML. A janela, o calendário e as permissões da conta são definidos pelo TikTok.

## Dependências e publicação

O Gaming Clip é baixado separadamente e tem licença AGPL-3.0 ([projeto de origem](https://github.com/iyansr/gaming-clip)). O pacote não inclui a sessão do TikTok, fontes do sistema, modelos baixados nem mídia. Publique somente o código e a documentação desta pasta. Escolha a licença do seu repositório antes de distribuí-lo.

## Avisos de atualização

A skill consulta a revisão mais recente da branch `main` no GitHub ao rodar a configuração ou um comando. Quando houver uma revisão nova, aparece um aviso com o link do commit. Cada publicação na `main` é detectada na próxima execução conectada. A checagem usa a sessão do GitHub CLI para acessar o repositório privado.

```powershell
.\run.ps1 check-update
git pull --ff-only
```

A skill apenas avisa. Para atualizar uma cópia baixada como ZIP, substitua o código pela cópia mais recente. O perfil local, a sessão do TikTok e os vídeos ficam nas mesmas pastas.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s scheduler/tests -v
```
