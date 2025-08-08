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
        # --- CORREÇÃO APLICADA AQUI ---
        
        # Primeiro, definimos as permissões que o bot precisa.
        intents = discord.Intents.default()
        intents.message_content = True # Essencial para comandos de prefixo (!)

        # Agora, inicializamos o bot passando o prefixo E as intents que acabamos de definir.
        super().__init__(command_prefix="!", intents=intents)
        
        # A linha extra 'intents=intents' foi removida pois não era necessária.

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
        await self.load_extension('cogs.admin_cog')
        print("  -> Cog 'admin_cog' carregado.")
        await self.load_extension('cogs.mundo_cog')
        print("  -> Cog 'mundo_cog' carregado.")
        await self.load_extension('cogs.tasks_cog')
        print("  -> Cog 'tasks_cog' carregado.")
        await self.load_extension('cogs.craft_cog')
        print("  -> Cog 'craft_cog' carregado.")
        await self.load_extension('cogs.stats_cog')
        print("  -> Cog 'stats_cog' carregado.")
        await self.load_extension('cogs.profissoes_cog')
        print("  -> Cog 'profissoes_cog' carregado.")
        await self.load_extension('cogs.fornalha_cog')
        print("  -> Cog 'fornalha_cog' carregado.")
        await self.load_extension('cogs.loja_cog')
        print("  -> Cog 'loja_cog' carregado.")
        await self.load_extension('cogs.forja_cog')
        print("  -> Cog 'forja_cog' carregado.")
        
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