# Seleção, layout e revisão

Reutilize fonte/transcrição existentes. Em lives longas, analise trechos com pequena sobreposição e salve candidatos. Serviços pagos ou envio a terceiros exigem autorização correspondente; MuAPI e Gemini não são requisitos.

Pontue abertura, emoção/humor/conflito, clareza e desfecho. Score é heurística editorial, não previsão de views. Exclua ócio, contexto enganoso e frases incompletas. Sobreposição maior que metade do menor trecho: mantenha a melhor opção, salvo cenas distintas. Compare também com conteúdo já publicado.

Primeiros 1–3 segundos: ação, pergunta ou reação real. Corte preparação desnecessária, preserve sentido e cronologia. Não invente fala/título. Prefira 20–75 segundos quando completos, teto de 90; não preencha grade com cenas fracas.

## Layout padrão

720×1280, 30fps, pixels quadrados. Câmera superior 720×560; gameplay inferior 720×720. Preencha cada região com recorte proporcional. Sem câmera, gameplay ocupa canvas inteiro. Nunca distorça, espelhe, duplique ou adicione fundo borrado/bordas.

Coordenadas dependem da gravação: confira rosto, personagem, veículo e ação principal. Ajuste por cena se o assunto sair do foco. Não copie coordenadas de outra fonte sem revisar.

Marca discreta com nome do canal em duas tipografias compatíveis; GTA 6 Sem Limites é exemplo configurável. Sem avatar, rodapé, marca de terceiros ou título permanente. Capa em frame real com gancho curto; faixa inicial de até 3s somente se escolhida. Legendas confiáveis e contrastadas, sem cobrir rosto/ação. Português por padrão; não traduza idiomas desconhecidos sem pedido.

scripts/render_clip.py JOB.json recebe source, output, start, duration, game=[x,y,w,h], camera opcional, watermark_png transparente 720×1280 e captions_ass opcionais, ffmpeg e ffprobe. Prepare os assets conforme o perfil. O script não faz análise editorial, não publica e não aprova o resultado.

## Revisão

Valide MP4 real, H.264/yuv420p, AAC, 720×1280, SAR 1:1, duração até 90s, faststart e decodificação. Renomear WebM não converte formato.

Veja início, momento principal, final e transições; escute abertura e fala principal. Amplie apenas trechos incertos ou sinalizados. Garanta gancho verdadeiro, enquadramento e sincronização. Não reveja material inalterado já revisado com hash idêntico.

Registre SHA-256, source_id, intervalos, layout, caminho, legenda, revisão técnica/visual/áudio e estado por rede. Estado inicial pending/not_submitted. Só marque passed após revisar.
