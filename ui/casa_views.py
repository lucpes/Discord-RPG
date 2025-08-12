# ui/casa_views.py
import discord
from discord import ui
from discord.ext import commands # --- IMPORTAÇÃO CORRIGIDA ---
import math
from firebase_config import db
from firebase_admin import firestore

# --- VIEW PRINCIPAL DA CASA ---
class CasaView(ui.View):
    def __init__(self, author: discord.User, bot: commands.Bot, char_data: dict, item_templates_cache: dict):
        super().__init__(timeout=300)
        self.author = author
        self.bot = bot
        self.char_data = char_data
        self.item_templates_cache = item_templates_cache

    @ui.button(label="Acessar Baú", style=discord.ButtonStyle.primary, emoji="📦")
    async def acessar_bau(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        view = BauView(
            user=interaction.user,
            char_data=self.char_data,
            item_templates_cache=self.item_templates_cache
        )
        # A BauView agora carrega os itens por conta própria para se manter atualizada
        await view.reload_and_update(interaction, initial_load=True)

    @ui.button(label="Melhorias da Casa", style=discord.ButtonStyle.secondary, emoji="🛠️", disabled=True)
    async def melhorias(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Em breve, você poderá fazer melhorias em sua casa!", ephemeral=True)

# --- MODAL DE QUANTIDADE ---
class QuantityModal(ui.Modal, title="Mover Quantidade"):
    def __init__(self, item_data: dict, max_qtd: int, direction: str, bau_view: 'BauView'):
        super().__init__()
        self.item_data = item_data
        self.direction = direction
        self.bau_view = bau_view
        
        template_nome = self.item_data['template_data'].get('nome', 'Item')
        self.quantidade_input = ui.TextInput(label=f"Mover: {template_nome}", placeholder=f"Disponível: {max_qtd}", default=str(max_qtd))
        self.add_item(self.quantidade_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantidade = int(self.quantidade_input.value)
            if not (0 < quantidade <= self.item_data['quantidade']):
                raise ValueError
        except ValueError:
            return await interaction.response.send_message("❌ Quantidade inválida!", ephemeral=True)
        await self.bau_view.move_item(interaction, self.item_data, self.direction, quantidade)


# --- VIEW COMPLETA E CORRIGIDA DO BAÚ ---
class BauView(ui.View):
    def __init__(self, user: discord.User, char_data: dict, item_templates_cache: dict):
        super().__init__(timeout=300)
        self.user = user
        self.char_data = char_data
        self.item_templates_cache = item_templates_cache
        self.backpack_items = []
        self.chest_items = []
        self.items_per_page = 5
        self.current_backpack_page = 1
        self.current_chest_page = 1
        self.total_backpack_pages = 1
        self.total_chest_pages = 1
        self.message: discord.Message = None

    def update_view(self):
        self.clear_items()
        
        start_backpack = (self.current_backpack_page - 1) * self.items_per_page
        end_backpack = start_backpack + self.items_per_page
        backpack_page_items = self.backpack_items[start_backpack:end_backpack]

        start_chest = (self.current_chest_page - 1) * self.items_per_page
        end_chest = start_chest + self.items_per_page
        chest_page_items = self.chest_items[start_chest:end_chest]

        if backpack_page_items:
            self.add_item(self.create_select_menu(backpack_page_items, start_backpack, "backpack", "Mover da Mochila para o Baú ➡️"))
        if chest_page_items:
            self.add_item(self.create_select_menu(chest_page_items, start_chest, "chest", "⬅️ Mover do Baú para a Mochila"))
            
        self.add_item(ui.Button(label="⬅️ Mochila", custom_id="prev_backpack", disabled=(self.current_backpack_page == 1), row=2))
        self.add_item(ui.Button(label="Mochila ➡️", custom_id="next_backpack", disabled=(self.current_backpack_page >= self.total_backpack_pages), row=2))
        self.add_item(ui.Button(label="⬅️ Baú", custom_id="prev_chest", disabled=(self.current_chest_page == 1), row=3))
        self.add_item(ui.Button(label="Baú ➡️", custom_id="next_chest", disabled=(self.current_chest_page >= self.total_chest_pages), row=3))
        
        for item in self.children:
            if isinstance(item, ui.Button):
                item.callback = self.on_page_change

    def create_select_menu(self, items: list, start_index: int, origin: str, placeholder: str) -> ui.Select:
        options = []
        for i, item in enumerate(items):
            template = item['template_data']
            label = f"{template.get('emote', '❓')} {template.get('nome')}"
            if 'quantidade' in item:
                label += f" (x{item['quantidade']})"
            else:
                label += f" [ID: {item['id']}]"
            options.append(discord.SelectOption(label=label, value=f"{origin}_{start_index + i}"))
        select = ui.Select(placeholder=placeholder, options=options)
        select.callback = self.on_item_select
        return select

    async def on_page_change(self, interaction: discord.Interaction):
        custom_id = interaction.data['custom_id']
        if custom_id == 'prev_backpack': self.current_backpack_page -= 1
        elif custom_id == 'next_backpack': self.current_backpack_page += 1
        elif custom_id == 'prev_chest': self.current_chest_page -= 1
        elif custom_id == 'next_chest': self.current_chest_page += 1
        self.update_view()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_item_select(self, interaction: discord.Interaction):
        origin, index_str = interaction.data['values'][0].split('_')
        index = int(index_str)
        item_data = self.backpack_items[index] if origin == 'backpack' else self.chest_items[index]
        direction = 'to_chest' if origin == 'backpack' else 'to_backpack'
        
        if 'quantidade' in item_data:
            modal = QuantityModal(item_data, item_data['quantidade'], direction, self)
            await interaction.response.send_modal(modal)
        else:
            await self.move_item(interaction, item_data, direction)

    async def move_item(self, interaction: discord.Interaction, item_data: dict, direction: str, quantidade: int = 1):
        """Função central que move o item, agora com a lógica completa."""
        # Adia a resposta para ter tempo de processar
        if not interaction.response.is_done():
            await interaction.response.defer()

        is_stackable = 'quantidade' in item_data
        
        # --- 1. VERIFICAÇÃO DE LIMITE DE SLOTS ---
        if direction == 'to_chest':
            limites_bau = self.char_data.get('casa', {}).get('limites_bau', {})
            if is_stackable:
                limite = limites_bau.get('empilhavel', 0)
                itens_no_bau = [item for item in self.chest_items if 'quantidade' in item]
                item_ja_existe = any(item['template_id'] == item_data['template_id'] for item in itens_no_bau)
                if not item_ja_existe and len(itens_no_bau) >= limite:
                    return await interaction.followup.send("❌ Seu baú não tem mais espaço para novos tipos de materiais!", ephemeral=True)
            else: # Equipamento
                limite = limites_bau.get('equipamentos', 0)
                itens_no_bau = [item for item in self.chest_items if 'id' in item]
                if len(itens_no_bau) >= limite:
                    return await interaction.followup.send("❌ Seu baú não tem mais espaço para novos equipamentos!", ephemeral=True)
        # (A verificação para a mochila pode ser adicionada aqui da mesma forma se necessário)

        # --- 2. PREPARA A TRANSAÇÃO NO BANCO DE DADOS ---
        user_id_str = str(self.user.id)
        char_ref = db.collection('characters').document(user_id_str)
        
        if direction == 'to_chest':
            origem_equip_ref, origem_stack_ref = char_ref.collection('inventario_equipamentos'), char_ref.collection('inventario_empilhavel')
            destino_equip_ref, destino_stack_ref = char_ref.collection('bau_equipamentos'), char_ref.collection('bau_empilhavel')
        else: # to_backpack
            origem_equip_ref, origem_stack_ref = char_ref.collection('bau_equipamentos'), char_ref.collection('bau_empilhavel')
            destino_equip_ref, destino_stack_ref = char_ref.collection('inventario_equipamentos'), char_ref.collection('inventario_empilhavel')

        batch = db.batch()
        if is_stackable:
            template_id = item_data['template_id']
            batch.update(origem_stack_ref.document(template_id), {'quantidade': firestore.Increment(-quantidade)})
            batch.set(destino_stack_ref.document(template_id), {'quantidade': firestore.Increment(quantidade)}, merge=True)
        else: # Equipamento
            item_id = item_data['id']
            # Para equipamentos, pegamos os dados e os movemos
            dados_item = item_data.get('instance_data', {}) 
            batch.delete(origem_equip_ref.document(item_id))
            batch.set(destino_equip_ref.document(item_id), {}) # Não precisa de 'equipado' no baú

        # --- 3. EXECUTA, DÁ FEEDBACK E ATUALIZA A INTERFACE ---
        batch.commit()
        
        nome_item = item_data['template_data']['nome']
        qtd_str = f"{quantidade}x " if is_stackable else ""
        feedback = f"✅ Você moveu **{qtd_str}{nome_item}**."
        
        # Se a interação veio de um modal, precisamos de uma nova resposta
        if interaction.type == discord.InteractionType.modal_submit:
            await interaction.response.send_message(feedback, ephemeral=True)
        else:
            await interaction.followup.send(feedback, ephemeral=True)

        # Recarrega tudo para mostrar o estado mais recente
        await self.reload_and_update(interaction)

    async def reload_and_update(self, interaction: discord.Interaction, initial_load: bool = False, item_movido: bool = False):
        user_id_str = str(self.user.id)
        char_ref = db.collection('characters').document(user_id_str)
        self.backpack_items = await self._load_inventory(char_ref.collection('inventario_equipamentos'), char_ref.collection('inventario_empilhavel'))
        self.chest_items = await self._load_inventory(char_ref.collection('bau_equipamentos'), char_ref.collection('bau_empilhavel'))
        
        self.total_backpack_pages = max(1, math.ceil(len(self.backpack_items) / self.items_per_page))
        self.total_chest_pages = max(1, math.ceil(len(self.chest_items) / self.items_per_page))
        self.current_backpack_page = min(self.current_backpack_page, self.total_backpack_pages)
        self.current_chest_page = min(self.current_chest_page, self.total_chest_pages)
        
        self.update_view()
        embed = self.create_embed()
        
        if initial_load:
            message = await interaction.followup.send(embed=embed, view=self, ephemeral=True)
            self.message = message
        elif not item_movido: # Se não foi um movimento, a interação é de um modal
            await interaction.response.edit_message(embed=embed, view=self)

    async def _load_inventory(self, equip_ref, stack_ref):
        items_list = []
        for item_doc in equip_ref.stream():
            item_id = item_doc.id
            instance_doc = db.collection('items').document(item_id).get()
            if instance_doc.exists:
                instance_data = instance_doc.to_dict()
                template_data = self.item_templates_cache.get(instance_data['template_id'])
                if template_data:
                    items_list.append({"id": item_id, "instance_data": instance_data, "template_data": template_data})
        for item_doc in stack_ref.stream():
            template_id = item_doc.id
            quantidade = item_doc.to_dict().get('quantidade', 0)
            if quantidade > 0:
                template_data = self.item_templates_cache.get(template_id)
                if template_data:
                    items_list.append({"template_id": template_id, "quantidade": quantidade, "template_data": template_data})
        return items_list

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"📦 Baú Pessoal de {self.user.display_name}", color=discord.Color.dark_gold())
        limites_inv = self.char_data.get('limites_inventario', {})
        limites_bau = self.char_data.get('casa', {}).get('limites_bau', {})
        
        equip_mochila = len([i for i in self.backpack_items if 'id' in i])
        stack_mochila = len([i for i in self.backpack_items if 'quantidade' in i])
        equip_bau = len([i for i in self.chest_items if 'id' in i])
        stack_bau = len([i for i in self.chest_items if 'quantidade' in i])

        start_backpack = (self.current_backpack_page - 1) * self.items_per_page
        backpack_page_items = self.backpack_items[start_backpack : start_backpack + self.items_per_page]
        backpack_str = "\n".join([self._format_item_line(item) for item in backpack_page_items]) or "*Vazio*"
        embed.add_field(name=f"🎒 Mochila ({equip_mochila}/{limites_inv.get('equipamentos', 0)} Equip. | {stack_mochila}/{limites_inv.get('empilhavel', 0)} Mat.)", value=backpack_str, inline=False)
        
        start_chest = (self.current_chest_page - 1) * self.items_per_page
        chest_page_items = self.chest_items[start_chest : start_chest + self.items_per_page]
        chest_str = "\n".join([self._format_item_line(item) for item in chest_page_items]) or "*Vazio*"
        embed.add_field(name=f"🗄️ Baú ({equip_bau}/{limites_bau.get('equipamentos', 0)} Equip. | {stack_bau}/{limites_bau.get('empilhavel', 0)} Mat.)", value=chest_str, inline=False)
        
        embed.set_footer(text=f"Mochila Pág. {self.current_backpack_page}/{self.total_backpack_pages} | Baú Pág. {self.current_chest_page}/{self.total_chest_pages}")
        return embed

    def _format_item_line(self, item_data):
        template = item_data['template_data']
        emote = template.get('emote', '❓')
        nome = template.get('nome', 'Item Desconhecido')
        if 'quantidade' in item_data:
            return f"{emote} **{nome}** `x{item_data['quantidade']}`"
        else:
            return f"{emote} **{nome}** `[ID: {item_data['id']}]`"