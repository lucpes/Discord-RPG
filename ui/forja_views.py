# ui/forja_views.py
import discord
from discord import ui
import math
import random
from firebase_config import db
from firebase_admin import firestore
from data.game_constants import RARITY_EMOJIS
from data.forja_library import FORJA_BLUEPRINTS
from cogs.item_cog import get_and_increment_item_id
from game.professions_helper import grant_profession_xp
from game.forja_helpers import calcular_stats_fusao

# --- MODAL DE QUANTIDADE (ATUALIZADO) ---
class QuantityModal(ui.Modal, title="Especificar Quantidade"):
    def __init__(self, item_data: dict, slot_index: int, forja_view: 'ForjaView'):
        super().__init__()
        self.item_data = item_data
        self.slot_index = slot_index
        self.forja_view = forja_view
        max_qtd = self.item_data.get('quantidade', 1)
        template_nome = self.item_data['template_data'].get('nome', 'Item')
        self.quantidade_input = ui.TextInput(label=f"Usar: {template_nome}", placeholder=f"Você possui: {max_qtd}", default="1")
        self.add_item(self.quantidade_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantidade = int(self.quantidade_input.value)
            max_qtd = self.item_data.get('quantidade', 0)
            if not (0 < quantidade <= max_qtd):
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(f"❌ Quantidade inválida!", ephemeral=True)

        # --- LÓGICA DE ATUALIZAÇÃO DO INVENTÁRIO ---
        # 1. Cria uma cópia do item com a quantidade a ser usada
        item_para_slot = self.item_data.copy()
        item_para_slot['quantidade'] = quantidade
        
        # 2. Subtrai a quantidade do inventário da ForjaView
        self.item_data['quantidade'] -= quantidade
        if self.item_data['quantidade'] <= 0:
            # Se a quantidade zerar, remove o item da lista
            self.forja_view.inventario_empilhavel.remove(self.item_data)
        
        # 3. Coloca o item no slot e atualiza a interface
        self.forja_view.slots[self.slot_index] = item_para_slot
        self.forja_view.update_view()
        embed = self.forja_view.create_embed()
        
        await self.forja_view.message.edit(embed=embed, view=self.forja_view)
        await interaction.response.defer()
        await interaction.delete_original_response()

# --- VIEW DE SELEÇÃO DE ITENS (ATUALIZADA) ---
class ItemSelectionView(ui.View):
    def __init__(self, author: discord.User, forja_view: 'ForjaView', slot_index: int):
        super().__init__(timeout=180)
        self.author = author
        self.forja_view = forja_view
        self.slot_index = slot_index
        
        # --- LÓGICA DE FILTRO ADICIONADA AQUI ---
        # 1. Pega o inventário completo
        inventario_total = self.forja_view.inventario_equipamentos + self.forja_view.inventario_empilhavel
        
        # 2. Pega os IDs dos itens únicos que já estão nos slots da forja
        ids_nos_slots = {item['id'] for item in self.forja_view.slots if item and 'id' in item}
        
        # 3. Filtra o inventário para remover os itens que já estão em uso
        self.inventario_completo = [
            item for item in inventario_total
            if 'id' not in item or item['id'] not in ids_nos_slots
        ]
        # Esta lógica garante que:
        # - Itens empilháveis (sem 'id') são sempre mostrados.
        # - Itens únicos (com 'id') só são mostrados se não estiverem já num slot.
        
        # O resto da inicialização continua a mesma
        self.items_per_page = 5
        self.current_page = 1
        self.total_pages = math.ceil(len(self.inventario_completo) / self.items_per_page) if self.inventario_completo else 1
        
        self.update_view()

    def update_view(self):
        self.clear_items()
        
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = self.current_page * self.items_per_page
        items_on_page = self.inventario_completo[start_index:end_index]

        for i, item in enumerate(items_on_page):
            item_index = start_index + i
            self.add_item(self.SelectItemButton(item, item_index, self))
            
        prev_button = ui.Button(label="⬅️", custom_id="prev_page", disabled=(self.current_page == 1), row=1)
        next_button = ui.Button(label="➡️", custom_id="next_page", disabled=(self.current_page >= self.total_pages), row=1)
        
        prev_button.callback = self.on_page_change
        next_button.callback = self.on_page_change
        
        self.add_item(prev_button)
        self.add_item(next_button)

    async def on_page_change(self, interaction: discord.Interaction):
        if interaction.data['custom_id'] == "prev_page":
            self.current_page -= 1
        else:
            self.current_page += 1
        
        self.update_view()
        await interaction.response.edit_message(view=self)

    # Botão para selecionar um item específico
    class SelectItemButton(ui.Button):
        def __init__(self, item_data: dict, item_index: int, parent_view: 'ItemSelectionView'):
            template = item_data['template_data']
            label = f"{template.get('emote', '❓')} {template.get('nome')}"
            if 'quantidade' in item_data:
                label += f" (x{item_data['quantidade']})"
            else:
                label += f" [ID: {item_data['id']}]"
                
            super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=f"select_{item_index}")
            self.item_data = item_data
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            if 'quantidade' in self.item_data:
                modal = QuantityModal(self.item_data, self.parent_view.slot_index, self.parent_view.forja_view)
                await interaction.response.send_modal(modal)
            else:
                # --- LÓGICA DE ATUALIZAÇÃO DO INVENTÁRIO ---
                # Remove o equipamento da lista de inventário da ForjaView
                self.parent_view.forja_view.inventario_equipamentos.remove(self.item_data)

                # Coloca o item no slot e atualiza a interface
                self.parent_view.forja_view.slots[self.parent_view.slot_index] = self.item_data
                self.parent_view.forja_view.update_view()
                embed = self.parent_view.forja_view.create_embed()
                
                await self.parent_view.forja_view.message.edit(embed=embed, view=self.parent_view.forja_view)
                await interaction.response.defer()
                await interaction.delete_original_response()


# --- A VIEW PRINCIPAL DA FORJA (TOTALMENTE REFEITA E CORRIGIDA) ---
class ForjaView(ui.View):
    def __init__(self, author: discord.User, char_data: dict, cidade_data: dict, inventario_equipamentos: list, inventario_empilhavel: list, item_templates_cache: dict):
        super().__init__(timeout=300)
        self.author = author
        self.char_data = char_data
        self.cidade_data = cidade_data
        self.inventario_equipamentos = inventario_equipamentos
        self.inventario_empilhavel = inventario_empilhavel
        self.item_templates_cache = item_templates_cache
        self.message: discord.Message = None
        
        self.slots = [None, None, None]
        self.update_view()

    def find_matching_blueprint(self):
        """Procura na biblioteca uma planta que corresponda aos itens nos slots."""
        items_in_slots = [item for item in self.slots if item]
        if not items_in_slots:
            return None

        # Cria uma "impressão digital" dos itens nos slots para comparar com as receitas
        slot_signature = {}
        for item in items_in_slots:
            template_id = item.get('template_id')
            if 'instance_data' in item: # Se for equipamento
                template_id = item['instance_data'].get('template_id')
            
            tipo = "EQUIPAMENTO" if 'instance_data' in item else "MATERIAL"
            key = (template_id, tipo)
            slot_signature[key] = slot_signature.get(key, 0) + item.get('quantidade', 1)

        # Procura uma planta compatível
        for blueprint_id, blueprint_data in FORJA_BLUEPRINTS.items():
            if len(blueprint_data['ingredientes']) != len(slot_signature):
                continue # Pula se o número de ingredientes for diferente

            blueprint_signature = {}
            for ingrediente in blueprint_data['ingredientes']:
                key = (ingrediente['template_id'], ingrediente['tipo'])
                blueprint_signature[key] = blueprint_signature.get(key, 0) + ingrediente.get('quantidade', 1)

            if slot_signature == blueprint_signature:
                return blueprint_data # Encontrou!

        return None # Nenhuma planta encontrada

    def update_view(self):
        self.clear_items()
        for i in range(3):
            item_no_slot = self.slots[i]
            if item_no_slot:
                template_id = item_no_slot.get('template_id')
                if 'instance_data' in item_no_slot:
                    template_id = item_no_slot['instance_data'].get('template_id')
                
                template = self.item_templates_cache.get(template_id, {})
                label = template.get('nome', "Item Desconhecido")

                # Adiciona a quantidade ao label se for um item empilhável
                if 'quantidade' in item_no_slot:
                    label += f" (x{item_no_slot['quantidade']})"
                
                self.add_item(ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=True, row=i))
                # O botão de remover agora chama on_remove_slot
                remove_button = ui.Button(label="Remover", style=discord.ButtonStyle.danger, custom_id=f"remove_slot_{i}", row=i)
                remove_button.callback = self.on_remove_slot
                self.add_item(remove_button)
            else:
                # O botão de adicionar agora chama on_add_slot
                add_button = ui.Button(label=f"Adicionar Item ao Slot {i+1}", style=discord.ButtonStyle.primary, custom_id=f"add_slot_{i}", row=i)
                add_button.callback = self.on_add_slot
                self.add_item(add_button)
        
        # Habilita o botão de fundir apenas se uma receita válida for encontrada
        matching_blueprint = self.find_matching_blueprint()
        fuse_button = ui.Button(label="Fundir Itens", style=discord.ButtonStyle.success, emoji="🔥", custom_id="fuse_items", row=3, disabled=(not matching_blueprint))
        fuse_button.callback = self.on_fuse
        self.add_item(fuse_button)

    def create_embed(self) -> discord.Embed:
        """Cria o embed da forja."""
        nivel_forja = self.cidade_data.get('construcoes', {}).get('FORJA', {}).get('nivel', 0)
        embed = discord.Embed(
            title=f"🔥 Forja (Nível {nivel_forja})",
            description="Coloque até 3 itens nos slots abaixo para descobrir novas combinações.",
            color=discord.Color.red()
        )
        
        for i in range(3):
            item = self.slots[i]
            if item:
                template_id = item.get('template_id')
                if 'instance_data' in item: # Se for equipamento
                    template_id = item['instance_data'].get('template_id')
                
                template = self.item_templates_cache.get(template_id, {})
                nome = template.get('nome', 'Desconhecido')
                emote = template.get('emote', '❓')

                # Adiciona a quantidade se for um item empilhável
                if 'quantidade' in item:
                    nome += f" (x{item['quantidade']})"

                embed.add_field(name=f"Slot {i+1}", value=f"{emote} {nome}", inline=True)
            else:
                embed.add_field(name=f"Slot {i+1}", value="*Vazio*", inline=True)
                
        return embed

    # --- NOVOS CALLBACKS DEDICADOS PARA CADA AÇÃO ---

    async def on_add_slot(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id: return
        
        slot_index = int(interaction.data['custom_id'].split('_')[-1])
        selection_view = ItemSelectionView(self.author, self, slot_index)
        await interaction.response.send_message(
            "Selecione um item do seu inventário:", 
            view=selection_view, 
            ephemeral=True
        )

    async def on_remove_slot(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id: return
        
        slot_index = int(interaction.data['custom_id'].split('_')[-1])
        item_removido = self.slots[slot_index]

        if item_removido:
            # --- LÓGICA DE ATUALIZAÇÃO DO INVENTÁRIO ---
            # Devolve o item removido para a lista de inventário correta
            if 'quantidade' in item_removido: # Se for um item empilhável
                # Procura se o item já existe no inventário para somar a quantidade
                found = False
                for item_inv in self.inventario_empilhavel:
                    if item_inv['template_id'] == item_removido['template_id']:
                        item_inv['quantidade'] += item_removido['quantidade']
                        found = True
                        break
                if not found: # Se não encontrou, adiciona de volta à lista
                    self.inventario_empilhavel.append(item_removido)
            else: # Se for um equipamento
                self.inventario_equipamentos.append(item_removido)
        
        self.slots[slot_index] = None
        self.update_view()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def on_fuse(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id: return
        await interaction.response.defer(ephemeral=True)
        
        # 1. PEGA A PLANTA E VERIFICA REQUISITOS NOVAMENTE
        blueprint = self.find_matching_blueprint()
        if not blueprint:
            return await interaction.followup.send("❌ Estes itens não podem ser fundidos.", ephemeral=True)
        
        # --- VERIFICAÇÃO FINAL DE REQUISITOS ADICIONADA ---
        user_id_str = str(self.author.id)
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        cidade_doc = db.collection('cidades').document(str(interaction.guild.id)).get()

        char_data = char_doc.to_dict()
        cidade_data = cidade_doc.to_dict()

        nivel_forja_cidade = cidade_data.get('construcoes', {}).get('FORJA', {}).get('nivel', 0)
        nivel_ferreiro_jogador = char_data.get('profissoes', {}).get('ferreiro', {}).get('nivel', 1)

        if nivel_forja_cidade < blueprint.get('nivel_forja', 1):
            return await interaction.followup.send("❌ O nível da Forja da cidade é muito baixo para esta fusão!", ephemeral=True)
        
        if nivel_ferreiro_jogador < blueprint.get('nivel_ferreiro', 1):
            return await interaction.followup.send(f"❌ Você não tem o nível de Ferreiro necessário! (Requer: {blueprint.get('nivel_ferreiro', 1)})", ephemeral=True)
        # --- FIM DA VERIFICAÇÃO ---

        user_id_str = str(interaction.user.id)
        char_ref = db.collection('characters').document(user_id_str)
        # (Adicione aqui a verificação final de nível de forja e ferreiro, como fizemos no craft)
        # ...

        # 2. PREPARA O BATCH E CONSOME OS ITENS
        batch = db.batch()
        items_nos_slots = [item for item in self.slots if item]

        for item_usado in items_nos_slots:
            if 'quantidade' in item_usado: # Item empilhável
                item_ref = char_ref.collection('inventario_empilhavel').document(item_usado['template_id'])
                batch.update(item_ref, {'quantidade': firestore.Increment(-item_usado['quantidade'])})
            else: # Equipamento
                # Apaga da coleção de itens e do inventário do jogador
                batch.delete(db.collection('items').document(item_usado['id']))
                batch.delete(char_ref.collection('inventario_equipamentos').document(item_usado['id']))

        # --- LÓGICA DE CRIAÇÃO DE ITEM ATUALIZADA ---
        resultado_info = blueprint['resultado']
        resultado_template_id = resultado_info['template_id']
        resultado_template_data = self.item_templates_cache[resultado_template_id]
        
        # 1. CHAMA O MOTOR DE FUSÃO, PASSANDO O CACHE
        stats_finais_combinados = calcular_stats_fusao(
            items_nos_slots, 
            resultado_info, 
            self.item_templates_cache # Passa o cache para a função
        )
        
        # 2. CRIA O NOVO ITEM COM OS STATS CALCULADOS
        transaction = db.transaction()
        novo_item_id = get_and_increment_item_id(transaction)
        novo_item_ref = db.collection('items').document(str(novo_item_id))
        
        novo_item_data = {
            "template_id": resultado_template_id,
            "owner_id": user_id_str,
            "stats_gerados": stats_finais_combinados, # Usa os stats corretamente calculados
            "encantamentos_aplicados": []
        }
        batch.set(novo_item_ref, novo_item_data)
        
        novo_inv_ref = char_ref.collection('inventario_equipamentos').document(str(novo_item_id))
        batch.set(novo_inv_ref, {'equipado': False})

        # 4. CONCEDE XP DE PROFISSÃO
        if xp_ganho := blueprint.get('xp_concedido'):
            grant_profession_xp(user_id_str, "ferreiro", xp_ganho)
            
        # 5. EXECUTA E DÁ FEEDBACK
        batch.commit()
        self.slots = [None, None, None] # Limpa os slots
        self.update_view()
        embed = self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

        await interaction.followup.send(f"🔥 Você forjou **{resultado_template_data['nome']}** com sucesso!", ephemeral=True)