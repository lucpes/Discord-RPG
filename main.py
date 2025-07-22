import discord
from discord import app_commands # Importa o necessário para comandos de barra
import os
from dotenv import load_dotenv

# 1. CARREGAR VARIÁVEIS DE AMBIENTE
# Carrega o token do bot do arquivo .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 2. CONFIGURAR INTENTS
# Intents são as permissões que seu bot precisa para funcionar.
# O 'default()' é um bom ponto de partida.
intents = discord.Intents.default()
# Para um bot de RPG, você provavelmente precisará de mais permissões no futuro,
# como ler mensagens e ver membros do servidor. Você pode ativá-las aqui:
# intents.message_content = True
# intents.members = True


# 3. CRIAR A CLASSE DO BOT
# Usar uma classe é uma forma organizada de estruturar seu bot.
class RPG_Bot(discord.Client):
    def __init__(self):
        # Inicializa a classe pai (discord.Client) com as intents que definimos
        super().__init__(intents=intents)
        
        # Cria uma "árvore de comandos" para registrar todos os seus comandos de barra (/)
        self.tree = app_commands.CommandTree(self)

    # O 'setup_hook' é uma função especial que roda antes do bot se conectar completamente.
    # É o lugar perfeito para sincronizar seus comandos de barra com o Discord.
    async def setup_hook(self):
        print("Sincronizando comandos...")
        await self.tree.sync()
        print("Comandos sincronizados!")


# Cria uma instância do nosso bot
bot = RPG_Bot()


# 4. EVENTO "ON_READY"
# Este evento é disparado quando o bot se conecta com sucesso ao Discord.
@bot.event
async def on_ready():
    print("="*50)
    print(f"O Bot {bot.user} está online e pronto!")
    print(f"ID do Bot: {bot.user.id}")
    print("="*50)


# 5. DECORADOR E COMANDO DE BARRA DE EXEMPLO
# Este é o decorador que você pediu para criar um comando de barra (/).

@bot.tree.command(name="ping", description="Verifica a latência do bot.")
async def ping(interaction: discord.Interaction):
    """
    Um comando de exemplo para verificar se o bot está respondendo.
    
    Args:
        interaction (discord.Interaction): A interação do usuário que invocou o comando.
    """
    # Calcula a latência (tempo de resposta) do bot
    latencia = round(bot.latency * 1000) # em milissegundos
    
    # Responde ao usuário. interaction.response.send_message é a forma padrão de responder.
    await interaction.response.send_message(
        f"🏓 Pong! A minha latência é de `{latencia}ms`."
    )





#=====================================================================================================================================#

# 6. LIGAR O BOT
# Esta é a última linha, que de fato executa o bot usando o token.
if __name__ == "__main__":
    if TOKEN is None:
        print("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env")
    else:
        bot.run(TOKEN)