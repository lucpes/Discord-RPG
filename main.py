# main.py

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

# 1. CARREGAR VARIÁVEIS DE AMBIENTE
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 2. CONFIGURAR A CLASSE DO BOT E CARREGAR COGS
class RPG_Bot(commands.Bot):
    def __init__(self):
        # O command_prefix é necessário, mas não será usado se você só usar comandos de barra
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        """Carrega todos os cogs da pasta /cogs e sincroniza os comandos."""
        print("Carregando cogs...")
        # Carrega os novos cogs
        await self.load_extension('cogs.registro_cog')
        print("  -> Cog 'registro_cog' carregado.")
        await self.load_extension('cogs.personagem_cog')
        print("  -> Cog 'personagem_cog' carregado.")
        await self.load_extension('cogs.item_cog')
        print("  -> Cog 'item_cog' carregado.")
        
        # Sincroniza a árvore de comandos após carregar tudo
        print("Sincronizando comandos de barra...")
        synced = await self.tree.sync()
        print(f"{len(synced)} comandos sincronizados!")

    async def on_ready(self):
        print("="*50)
        print(f"O Bot {self.user} está online e pronto!")
        print(f"ID do Bot: {self.user.id}")
        print("="*50)

# 3. INICIAR O BOT
if __name__ == "__main__":
    if TOKEN is None:
        print("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env")
    else:
        bot = RPG_Bot()
        bot.run(TOKEN)