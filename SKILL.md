---
name: super-clips-studio
description: Configure canais de cortes, encontre destaques em lives, produza clipes verticais e agende lotes revisados no TikTok, Instagram e Kwai com contexto compacto.
---

# Super Clips Studio

Uma skill única: perfil do Stream Clip Studio, seleção editorial das skills de clips, comunicação breve inspirada no Caveman e publicação verificável. Não exige carregar as skills antigas.

## Primeiro uso

Consulte o perfil salvo. Se não existir, pergunte numa mensagem:
“Qual o nome do canal e @ de cada rede? Pode enviar uma foto opcional e um layout de referência, ou escolher o padrão. Qual a live, pasta de saída e redes desejadas?”

Foto e layout são opcionais e podem chegar depois. Use assets/profile.example.json como estrutura. Configurar perfil não autoriza alterar identidade visual das contas. Pergunte quantidade, horários e fuso apenas se faltarem para a tarefa. Guarde perfil, mídia e sessões fora desta skill e do Git.

## Fluxo

1. Retome pelo checkpoint compacto; preserve arquivos, revisões e aprovações existentes.
2. Para seleção/render, leia somente [edição](references/editing.md). Analise a transcrição uma vez, escolha abertura forte, ação/reação e desfecho completo. Até 90 segundos; não prometa viralização.
3. Primeiro layout ou mudança relevante: mostre um frame real antes do lote, salvo autorização para seguir. Padrão: câmera acima, gameplay quadrada ampliada e centralizada abaixo, sem bordas, espelho ou fundo borrado; somente a marca do canal.
4. Renderize por script e revise imagem/áudio. scripts/render_clip.py oferece render técnico portátil; o motor legado permanece disponível, mas seus presets antigos não definem o padrão desta skill.
5. Publique somente quando solicitado. Leia [publicação](references/publishing.md) nessa fase. Registre confirmações por plataforma.

## Economia de tokens

- Português breve, resultado primeiro, sem narração rotineira. Cumpra atualizações obrigatórias do ambiente.
- Leia cada recurso uma vez por versão; releia apenas o trecho afetado por mudança ou falha. Não carregue todas as referências ou skills.
- Use scripts para download, transcrição, render e validação. Logs ficam em disco; retorne contagens, caminhos e erros relevantes.
- Navegador: conector oficial suficiente primeiro; caso contrário controles autorizados pelo ambiente. DOM direcionado antes de screenshots; imagem para revisão visual ou falha. Evite dumps e polling rápido.
- Um uploader ativo por plataforma. Paralelismo somente onde comprovadamente seguro.
- Após duas falhas iguais, preserve trabalho e mude a abordagem com evidência nova ou reporte bloqueio. Nunca repita submissão ambígua.
- Salve checkpoint pequeno ao mudar de fase: próximo corte, horários, confirmados, pendências e caminhos. Não releia toda a conversa.
- Meta: reduzir 70% contra execução comparável. Não declare atingida sem medição. Leia [métricas](references/metrics.md) apenas ao medir.

Preserve revisão editorial, segurança, verificações críticas e prevenção de duplicatas. Não contorne limites, CAPTCHA ou rejeições de aprovação.
