# cogs/personagem_cog.py
import discord
from discord import app_commands
from discord.ext import commands

from firebase_config import db
from data.classes_data import CLASSES_DATA # Importa os dados estáticos
from ui.views import ClasseSelectionView, PerfilView # Importa as Views de UI

class PersonagemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="perfil", description="Veja seu perfil ou crie um novo personagem.")
    async def perfil(self, interaction: discord.Interaction):
        # (Cole aqui o código do comando /perfil, sem alterações)
        user_id_str = str(interaction.user.id)
        player_ref = db.collection('players').document(user_id_str)
        player_doc = player_ref.get()
        if not player_doc.exists:
            await interaction.response.send_message("Você ainda não está registrado. Use `/registrar` primeiro!", ephemeral=True)
            return

        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if char_doc.exists:
            player_data = player_doc.to_dict()
            char_data = char_doc.to_dict()
            embed = discord.Embed(
                title=f"Perfil de {player_data.get('nick', 'Aventureiro')}",
                description=f"Um(a) {char_data.get('classe', 'Desconhecido')} de nível {char_data.get('nivel', 0)} explorando o mundo.",
                color=interaction.user.color
            )
            classe_info = CLASSES_DATA.get(char_data.get('classe'))
            if classe_info:
                embed.set_thumbnail(url=classe_info['image_url'])
            embed.add_field(name="Informações Básicas", value=f"**Classe:** {char_data.get('classe', 'N/A')}\n**Nível:** {char_data.get('nivel', 0)}\n**Guilda:** Sem guilda (em breve)", inline=True)
            embed.add_field(name="Riquezas", value=f"🪙 **Moedas:** {char_data.get('moedas', 0)}\n🏦 **Banco:** {char_data.get('banco', 0)}\n💎 **Diamantes:** {char_data.get('diamantes', 0)}", inline=True)
            habilidades_list = char_data.get('habilidades_equipadas', ['Nenhuma habilidade equipada.'])
            embed.add_field(name="Habilidades Equipadas", value=">>> " + "\n".join(f"• {hab}" for hab in habilidades_list), inline=False)
            view = PerfilView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            view = ClasseSelectionView(user=interaction.user)
            initial_embed = view.create_embed()
            await interaction.response.send_message(
                "Você ainda não tem um personagem. Vamos criar um agora! Escolha sua classe abaixo:",
                embed=initial_embed,
                view=view,
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(PersonagemCog(bot))