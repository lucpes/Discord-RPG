# ui/views.py
import discord
from discord.ext import commands
import math

from data.classes_data import CLASSES_DATA, ORDERED_CLASSES
from data.game_constants import EQUIPMENT_SLOTS # Importa nossos slots
from data.stats_library import format_stat
from firebase_config import db

# --- NOVA VIEW PARA O INVENTÁRIO COM PAGINAÇÃO ---
class InventarioView(discord.ui.View):
    def __init__(self, user: discord.User, equipped_items: dict, backpack_items: list):
        super().__init__(timeout=300)
        self.user = user
        self.equipped_items = equipped_items
        self.backpack_items = backpack_items
        
        # Lógica de Paginação
        self.items_per_page = 3
        self.current_page = 1
        self.total_pages = math.ceil(len(self.backpack_items) / self.items_per_page)

        self.update_buttons()

    def update_buttons(self):
        """Ativa/desativa os botões de paginação conforme a página atual."""
        self.children[0].disabled = self.current_page == 1
        self.children[1].disabled = self.current_page >= self.total_pages

    async def create_inventory_embed(self):
        """Cria o embed do inventário com os itens equipados e a mochila paginada."""
        embed = discord.Embed(
            title=f"Inventário de {self.user.display_name}",
            color=self.user.color
        ).set_thumbnail(url=self.user.display_avatar.url)

        # Seção de Itens Equipados
        equipped_str = ""
        for slot_id, slot_name in EQUIPMENT_SLOTS.items():
            item = self.equipped_items.get(slot_id)
            if item:
                rarity = item['template_data'].get('raridade', 'COMUM').capitalize()
                equipped_str += f"**{slot_name}:** `[{item['id']}]` {item['template_data']['nome']} ({rarity})\n"
            else:
                equipped_str += f"**{slot_name}:** [Vazio]\n"
        embed.add_field(name="🛡️ Equipamento", value=equipped_str, inline=False)

        # Seção da Mochila Paginada
        if not self.backpack_items:
            embed.add_field(name="🎒 Mochila", value="Sua mochila está vazia.", inline=False)
        else:
            start_index = (self.current_page - 1) * self.items_per_page
            end_index = start_index + self.items_per_page
            items_on_page = self.backpack_items[start_index:end_index]
            
            backpack_str = ""
            for item in items_on_page:
                template = item['template_data']
                stats = "\n".join([format_stat(stat, val) for stat, val in item['instance_data'].get('stats_gerados', {}).items()])
                classes = template.get('classe', 'Qualquer uma')
                if isinstance(classes, list): classes = ", ".join(classes)

                backpack_str += (
                    f"**`{item['id']}` - {template['nome']} - Slot: {template.get('slot', 'N/A')}**\n"
                    f"Classe: `{classes}`\n"
                    f"*{stats or 'Nenhum atributo'}*\n---\n"
                )
            
            embed.add_field(name="🎒 Mochila", value=backpack_str, inline=False)
            embed.set_footer(text=f"Página {self.current_page} de {self.total_pages}")
            
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        
        self.current_page -= 1
        self.update_buttons()
        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return

        self.current_page += 1
        self.update_buttons()
        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# --- VIEW DO PERFIL ATUALIZADA ---
class PerfilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Inventário", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        user_id = str(interaction.user.id)
        inventory_snapshot = db.collection('characters').document(user_id).collection('inventario').stream()
        
        equipped_items = {}
        backpack_items = []

        # Coleta todos os dados de forma assíncrona (mais eficiente no futuro com libs async)
        for item_ref in inventory_snapshot:
            item_id = item_ref.id
            is_equipped = item_ref.to_dict().get('equipado', False)

            instance_doc = db.collection('items').document(item_id).get()
            if not instance_doc.exists: continue
            instance_data = instance_doc.to_dict()

            template_doc = db.collection('item_templates').document(instance_data['template_id']).get()
            if not template_doc.exists: continue
            template_data = template_doc.to_dict()

            full_item_data = {
                "id": item_id,
                "instance_data": instance_data,
                "template_data": template_data
            }

            if is_equipped:
                slot = template_data.get('slot')
                if slot: equipped_items[slot] = full_item_data
            else:
                backpack_items.append(full_item_data)
        
        # Cria e envia a nova View de Inventário
        view = InventarioView(user=interaction.user, equipped_items=equipped_items, backpack_items=backpack_items)
        embed = await view.create_inventory_embed()
        
        # Usa followup.send pois a interação já foi "deferida"
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


    @discord.ui.button(label="Habilidades", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def habilidades(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("A árvore de habilidades será implementada em breve!", ephemeral=True)

    @discord.ui.button(label="Talentos", style=discord.ButtonStyle.secondary, emoji="🌟")
    async def talentos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Os talentos de classe serão implementados em breve!", ephemeral=True)

# A ClasseSelectionView continua aqui, sem alterações...
# (O código da ClasseSelectionView que já tínhamos)
class ClasseSelectionView(discord.ui.View):
    # ... código existente da ClasseSelectionView
    def __init__(self, user: discord.User):
        super().__init__(timeout=300)
        self.user = user
        self.current_class_index = 0

    def create_embed(self):
        class_name = ORDERED_CLASSES[self.current_class_index]
        classe_atual = CLASSES_DATA[class_name]
        embed = discord.Embed(
            title=f"Escolha sua Classe: {class_name}",
            description=f"**Estilo:** {classe_atual['estilo']}",
            color=discord.Color.blue()
        )
        embed.set_image(url=classe_atual['image_url'])
        embed.add_field(name="⚔️ Habilidades Iniciais", value="- " + "\n- ".join(classe_atual['habilidades']), inline=True)
        embed.add_field(name="🌟 Evoluções Possíveis", value="- " + "\n- ".join(classe_atual['evolucoes']), inline=True)
        embed.set_footer(text=f"Classe {self.current_class_index + 1}/{len(ORDERED_CLASSES)}")
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return
        self.current_class_index = (self.current_class_index - 1) % len(ORDERED_CLASSES)
        await self.update_message(interaction)

    @discord.ui.button(label="✅ Selecionar", style=discord.ButtonStyle.success)
    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        class_name = ORDERED_CLASSES[self.current_class_index]
        selected_class = CLASSES_DATA[class_name]
        
        char_ref = db.collection('characters').document(str(interaction.user.id))
        char_ref.set({
            'classe': class_name,
            'nivel': 1,
            'xp': 0,
            'moedas': 100,
            'banco': 0,
            'diamantes': 5,
            'habilidades_equipadas': selected_class['habilidades']
        })

        final_embed = self.create_embed()
        final_embed.title = f"✅ Classe Selecionada: {class_name}"
        final_embed.color = discord.Color.green()
        final_embed.description = f"Parabéns, {interaction.user.mention}! Você iniciou sua jornada como um(a) **{class_name}**."
        
        await interaction.response.edit_message(embed=final_embed, view=self)
        self.stop()

    @discord.ui.button(label="Próximo ➡️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Você não pode interagir com o menu de outra pessoa!", ephemeral=True)
            return
        self.current_class_index = (self.current_class_index + 1) % len(ORDERED_CLASSES)
        await self.update_message(interaction)