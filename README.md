# GTA Online → Discord (GitHub Actions)

Bot que consulta a atualização semanal do GTA Online e envia um Embed para um canal do Discord.

## Como usar

1. Crie um repositório no GitHub.
2. Envie estes arquivos para o repositório.
3. No GitHub, abra:
   **Settings → Secrets and variables → Actions**
4. Clique em **New repository secret**.
5. Nome:
   `DISCORD_WEBHOOK_URL`
6. Valor: cole a URL do Webhook do Discord.
7. Salve.

O workflow roda automaticamente **toda quinta-feira às 14:00 UTC**, que corresponde a **11:00 no horário de Brasília (UTC-3)**.

Você também pode executar manualmente em:
**Actions → GTA Online Weekly Update → Run workflow**

## Importante

Não coloque a URL do Webhook diretamente em `bot.py` ou em qualquer arquivo público do GitHub. Use a Secret.

O bot usa o GrindMap como fonte independente para os dados semanais:
https://grindmap.com/gta-online-weekly-update

A fonte pode mudar seu formato no futuro; nesse caso, o código de leitura pode precisar de atualização.
