# cogs/forja_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from firebase_config import db
from ui.forja_views import ForjaView # Importa nossa nova View

class ForjaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Carrega o cache de itens para a forja
        self.item_templates_cache = {}
        try:
            templates_stream = db.collection('item_templates').stream()
            for template in templates_stream:
                self.item_templates_cache[template.id] = template.to_dict()
            print(f"✅ {len(self.item_templates_cache)} templates de itens carregados no cache da Forja.")
        except Exception as e:
            print(f"❌ ERRO ao carregar templates de itens na Forja: {e}")

    @app_commands.command(name="forja", description="Use a forja para fundir e aprimorar equipamentos.")
    async def forja(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ A Forja só pode ser acedida dentro de uma cidade (servidor).", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        user_id_str = str(interaction.user.id)
        cidade_atual_id = str(interaction.guild.id)

        # --- LÓGICA DE VERIFICAÇÃO COMPLETA ---
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists:
            return await interaction.followup.send("Você precisa ter um personagem para usar a Forja.", ephemeral=True)

        char_data = char_doc.to_dict()
        if char_data.get('localizacao_id') != cidade_atual_id:
            return await interaction.followup.send(f"Você não está em **{interaction.guild.name}** para usar a Forja daqui! Use `/viajar`.", ephemeral=True)
            
        cidade_ref = db.collection('cidades').document(cidade_atual_id)
        cidade_doc = cidade_ref.get()
        if not cidade_doc.exists:
            return await interaction.followup.send(f"A cidade de **{interaction.guild.name}** ainda não foi fundada.", ephemeral=True)

        cidade_data = cidade_doc.to_dict()
        if cidade_data.get('construcoes', {}).get('FORJA', {}).get('nivel', 0) == 0:
            return await interaction.followup.send("🔥 A Forja ainda não foi construída nesta cidade!", ephemeral=True)

        # --- LÓGICA DE CARREGAMENTO DO INVENTÁRIO COMPLETO ---
        inventario_equipamentos = []
        equip_snapshot = char_ref.collection('inventario_equipamentos').stream()
        for item_ref in equip_snapshot:
            item_id = item_ref.id
            instance_doc = db.collection('items').document(item_id).get()
            if not instance_doc.exists: continue
            
            instance_data = instance_doc.to_dict()
            template_id = instance_data.get('template_id')
            template_doc = db.collection('item_templates').document(template_id).get()
            if not template_doc.exists: continue
            
            # Guarda os dados completos do item
            inventario_equipamentos.append({
                "id": item_id,
                "template_id": template_id,
                "instance_data": instance_data,
                "template_data": template_doc.to_dict()
            })

        inventario_empilhavel = []
        stackable_snapshot = char_ref.collection('inventario_empilhavel').stream()
        for item_ref in stackable_snapshot:
            template_id = item_ref.id
            quantidade = item_ref.to_dict().get('quantidade', 0)
            if quantidade <= 0: continue

            template_doc = db.collection('item_templates').document(template_id).get()
            if not template_doc.exists: continue
            
            inventario_empilhavel.append({
                "template_id": template_id,
                "quantidade": quantidade,
                "template_data": template_doc.to_dict()
            })
            
        view = ForjaView(
            author=interaction.user,
            char_data=char_data,
            cidade_data=cidade_data,
            inventario_equipamentos=inventario_equipamentos,
            inventario_empilhavel=inventario_empilhavel,
            item_templates_cache=self.item_templates_cache
        )
        embed = view.create_embed()
        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        view.message = message

async def setup(bot: commands.Bot):
    await bot.add_cog(ForjaCog(bot))