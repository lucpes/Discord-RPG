# cogs/stats_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db

# Importa as ferramentas do seu stats_library e o novo helper
from data.stats_library import STATS, STAT_CATEGORIES
from utils.character_helpers import load_player_sheet
from game.stat_calculator import calcular_stats_completos

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="status", description="Exibe a ficha completa de status do seu personagem.")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)

        # Usa a função centralizada para carregar todos os dados do jogador
        sheet = load_player_sheet(user_id_str)
        if not sheet:
            await interaction.followup.send("❌ Você precisa ter um personagem para ver seus status. Use `/perfil`.", ephemeral=True)
            return

        char_data = sheet['char_data']
        equipped_items = sheet['equipped_items']

        # Calcula os status finais, já somando tudo
        stats_finais = calcular_stats_completos(char_data, equipped_items)

        embed = discord.Embed(
            title=f"Ficha de Status de {sheet['player_data'].get('nick')}",
            description="Estes são seus atributos totais, incluindo bônus de equipamentos e habilidades.",
            color=interaction.user.color
        )

        # Organiza os status com base nas categorias do seu stats_library.py
        stats_by_category = {category: [] for category in STAT_CATEGORIES}
        
        for stat_id, stat_info in STATS.items():
            # Verifica se o personagem possui aquele status e se ele tem uma categoria para ser exibido
            if stat_id in stats_finais and 'category' in stat_info and stats_finais[stat_id] > 0:
                valor = stats_finais[stat_id]
                
                # Formata como porcentagem se necessário
                if stat_info.get("is_percent"):
                    # Multiplica por 100 para exibir como porcentagem real
                    valor_str = f"{valor * 100:.1f}%" 
                else:
                    valor_str = f"{valor:,}"
                
                line = f"{stat_info['emoji']} **{stat_info['nome']}:** `{valor_str}`"
                stats_by_category[stat_info['category']].append(line)

        # Adiciona os campos ao embed na ordem definida em STAT_CATEGORIES
        for category in STAT_CATEGORIES:
            if stats_by_category[category]:
                embed.add_field(
                    name=f"--- {category.capitalize()} ---",
                    value="\n".join(stats_by_category[category]),
                    inline=True
                )
        
        # Adiciona um campo para status sem categoria, se houver algum
        # (Isso é opcional, mas pode ser útil para depuração)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))