# cogs/casa_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.casa_views import BauView # Importa a nossa nova View
from ui.casa_views import CasaView

class CasaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # O cache de itens agora é carregado, mas será passado para a BauView pelo botão
        self.item_templates_cache = {}
        try:
            templates_stream = db.collection('item_templates').stream()
            for template in templates_stream:
                self.item_templates_cache[template.id] = template.to_dict()
        except Exception as e:
            print(f"❌ ERRO ao carregar templates de itens no CasaCog: {e}")

    @app_commands.command(name="casa", description="Acesse sua casa para guardar itens e ver melhorias.")
    async def casa(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            return await interaction.followup.send("❌ Você precisa ter um personagem para ter uma casa.", ephemeral=True)
            
        char_data = char_doc.to_dict()
        
        # Garante que o jogador esteja em casa
        if char_data.get('localizacao_id') != "CASA":
            return await interaction.followup.send("❌ Você precisa estar na sua casa para acessá-la! Use `/viajar` no meu privado.", ephemeral=True)
        
        # Cria o embed principal da casa
        embed = discord.Embed(
            title=f"🏡 Lar Doce Lar de {interaction.user.display_name}",
            description="Você está em sua casa, um refúgio seguro para descansar e organizar seus pertences.",
            color=discord.Color.dark_green()
        )
        embed.set_footer(text="Use os botões abaixo para interagir.")
        
        # Cria a view principal da casa
        view = CasaView(
            author=interaction.user, 
            bot=self.bot, 
            char_data=char_data,
            item_templates_cache=self.item_templates_cache
        )

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CasaCog(bot))