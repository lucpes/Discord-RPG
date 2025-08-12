# cogs/casa_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.views import BauView # Vamos criar esta View a seguir

class CasaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cache de templates para ser usado na View do Baú
        self.item_templates_cache = {}
        try:
            templates_stream = db.collection('item_templates').stream()
            for template in templates_stream:
                self.item_templates_cache[template.id] = template.to_dict()
        except Exception as e:
            print(f"❌ ERRO ao carregar templates de itens no CasaCog: {e}")

    @app_commands.command(name="bau", description="Acesse seu baú pessoal para guardar e retirar itens.")
    async def bau(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user_id_str = str(interaction.user.id)
        
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            return await interaction.followup.send("❌ Você precisa ter um personagem para ter um baú.", ephemeral=True)
            
        char_data = char_doc.to_dict()
        
        # Verifica se o jogador está em casa para usar o baú
        if char_data.get('localizacao_id') != "CASA":
            return await interaction.followup.send("❌ Você precisa estar na sua casa para acessar o baú! Use `/viajar` no meu privado.", ephemeral=True)
            
        # Carrega os inventários (mochila e baú)
        # (A lógica de carregamento será adicionada aqui quando criarmos a View)

        # Por enquanto, uma mensagem de placeholder:
        await interaction.followup.send("🚧 O sistema de baú está em construção! Em breve você poderá gerenciar seus itens aqui.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CasaCog(bot))