# Medição

Use contadores reais antes/depois do corte ou lote comparável, incluindo seleção, render, revisão e publicação. Marque tempo, quantidade concluída e fases incluídas. Sem contador disponível: “não mensurado”.

Nos logs Codex, eventos token_count podem conter info.total_token_usage. Extraia apenas números pelo script/localmente; não carregue sessão inteira no contexto e nunca exporte logs pessoais ao GitHub.

Delta = final − inicial. cached_input_tokens já pertence a input_tokens; reasoning_output_tokens já pertence a output_tokens. Não some duas vezes. Total do lote dividido por cortes é média rateada, não medição individual. Tokens não revelam sozinhos cobrança ou limites do plano.

Economia = 100 × (1 − total_atual / total_base). Compare condições/fases iguais e qualidade constante. Incluir erros/retomadas. Só afirme redução de 70% após medir. Não altere modelo, segurança ou configuração global silenciosamente.
