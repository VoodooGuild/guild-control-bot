# Guild Control Bot 🤖

Bot do Discord para integração com o Guild Control Center.

## Comandos disponíveis

| Comando | Descrição |
|---|---|
| `/add-renter` | Abre um formulário para adicionar um novo renter |
| `/list-renters` | Lista todos os renters ativos |
| `/remove-renter` | Desativa um renter pelo nome in-game |

Todos os comandos exigem permissão de **Administrador**.

## Estrutura do projeto

```
guild-control-bot/
├── bot.py           # Arquivo principal
├── database.py      # Conexão com Supabase
├── cogs/
│   └── renters.py   # Módulo de renters
├── requirements.txt
├── Procfile         # Para Railway
└── .env.example     # Exemplo de variáveis de ambiente
```

## Variáveis de ambiente necessárias

```
DISCORD_TOKEN=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
```
