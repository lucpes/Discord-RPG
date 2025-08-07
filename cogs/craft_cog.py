# cogs/craft_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.crafting_views import CraftingView

class CraftCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # --- LÓGICA DE CACHE ADICIONADA AQUI ---
        # Carrega todos os templates de itens do Firebase para a memória
        self.item_templates_cache = {}
        try:
            templates_stream = db.collection('item_templates').stream()
            for template in templates_stream:
                self.item_templates_cache[template.id] = template.to_dict()
            print(f"✅ {len(self.item_templates_cache)} templates de itens carregados no cache.")
        except Exception as e:
            print(f"❌ ERRO ao carregar templates de itens: {e}")

    @app_commands.command(name="craft", description="Abre a interface de criação de itens.")
    async def craft(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Este comando só pode ser usado dentro de um servidor (cidade).", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        cidade_atual_id = str(interaction.guild.id)

        # 1. Verifica se o personagem existe
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            await interaction.followup.send("Você precisa ter um personagem para usar a Mesa de Trabalho.", ephemeral=True)
            return
        
        char_data = char_doc.to_dict()

        # 2. VERIFICA A LOCALIZAÇÃO DO JOGADOR
        if char_data.get('localizacao_id') != cidade_atual_id:
            await interaction.followup.send(
                f"Você não está em **{interaction.guild.name}** para usar a Mesa de Trabalho daqui!\n"
                f"Use o comando `/viajar` para vir para esta cidade.",
                ephemeral=True
            )
            return

        # 3. Verifica se a cidade existe
        cidade_ref = db.collection('cidades').document(cidade_atual_id)
        cidade_doc = cidade_ref.get()
        if not cidade_doc.exists:
            await interaction.followup.send(f"A cidade de **{interaction.guild.name}** ainda não foi fundada.", ephemeral=True)
            return

        # Se tudo estiver certo, continua...
        stackable_inventory = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}
        view = CraftingView(
            author=interaction.user,
            char_data=char_data,
            cidade_data=cidade_doc.to_dict(),
            stackable_inventory=stackable_inventory,
            item_templates_cache=self.item_templates_cache
        )
        embed = view.create_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CraftCog(bot))