 # ui/views.py
import discord
import math
from firebase_config import db
from data.habilidades_library import HABILIDADES
from data.classes_data import CLASSES_DATA, ORDERED_CLASSES
from data.game_constants import EQUIPMENT_SLOTS, RARITY_EMOJIS # Importa os novos dados
from data.stats_library import format_stat

# ---------------------------------------------------------------------------------
# VIEW DO INVENTÁRIO (Totalmente Redesenhada)
# ---------------------------------------------------------------------------------
class InventarioView(discord.ui.View):
    def __init__(self, user: discord.User, equipped_items: dict, backpack_items: list):
        super().__init__(timeout=300)
        self.user = user
        self.equipped_items = equipped_items
        self.backpack_items = backpack_items
        
        self.items_per_page = 4 # Aumentamos um pouco o limite por página
        self.current_page = 1
        self.total_pages = math.ceil(len(self.backpack_items) / self.items_per_page) if self.backpack_items else 1

        self.update_buttons()

    def update_buttons(self):
        # Encontra os botões de paginação pelo custom_id
        prev_button = discord.utils.get(self.children, custom_id="prev_page")
        next_button = discord.utils.get(self.children, custom_id="next_page")
        if prev_button: prev_button.disabled = self.current_page == 1
        if next_button: next_button.disabled = self.current_page >= self.total_pages

    def format_item_line(self, item_data):
        """Formata uma única linha de item para exibição."""
        template = item_data['template_data']
        rarity_id = template.get('raridade', 'COMUM').upper()
        emoji = RARITY_EMOJIS.get(rarity_id, '⚪️')
        return f"{emoji} `[{item_data['id']}]` **{template['nome']}**"

    async def create_inventory_embed(self):
        """Cria o embed do inventário com o novo layout de colunas."""
        embed = discord.Embed(title=f"Inventário de {self.user.display_name}", color=self.user.color)
        embed.set_thumbnail(url=self.user.display_avatar.url)

        # --- Seção de Itens Equipados (Layout de Colunas) ---
        
        # Coluna da Esquerda (Armadura)
        armor_slots = ["CAPACETE", "PEITORAL", "CALCA", "BOTA"]
        armor_str = ""
        for slot_id in armor_slots:
            slot_info = EQUIPMENT_SLOTS[slot_id]
            item = self.equipped_items.get(slot_id)
            armor_str += f"{slot_info['emoji']} **{slot_info['display']}:**\n"
            armor_str += f"↳ {self.format_item_line(item)}\n" if item else "↳ — *Vazio*\n"
        embed.add_field(name="Armadura Principal", value=armor_str, inline=True)

        # Coluna da Direita (Armas e Acessórios)
        accessory_slots = ["MAO_PRINCIPAL", "MAO_SECUNDARIA", "ANEL", "COLAR"]
        accessory_str = ""
        for slot_id in accessory_slots:
            slot_info = EQUIPMENT_SLOTS[slot_id]
            item = self.equipped_items.get(slot_id)
            accessory_str += f"{slot_info['emoji']} **{slot_info['display']}:**\n"
            accessory_str += f"↳ {self.format_item_line(item)}\n" if item else "↳ — *Vazio*\n"
        embed.add_field(name="Combate e Acessórios", value=accessory_str, inline=True)
        
        # Seção de Runas (Centralizada)
        rune_slots = ["RUNA_1", "RUNA_2"]
        rune_str = ""
        for slot_id in rune_slots:
            slot_info = EQUIPMENT_SLOTS[slot_id]
            item = self.equipped_items.get(slot_id)
            rune_str += f"{slot_info['emoji']} {self.format_item_line(item) if item else '— *Vazio*'}\n"
        embed.add_field(name="Runas", value=rune_str, inline=False)
        
        # --- Seção da Mochila Paginada (Layout Compacto) ---
        if not self.backpack_items:
            embed.add_field(name="🎒 Mochila", value="Sua mochila está vazia.", inline=False)
        else:
            start_index = (self.current_page - 1) * self.items_per_page
            end_index = start_index + self.items_per_page
            items_on_page = self.backpack_items[start_index:end_index]
            
            backpack_list = [self.format_item_line(item) for item in items_on_page]
            embed.add_field(name="🎒 Mochila", value="\n".join(backpack_list), inline=False)
            embed.set_footer(text=f"Use /equipar <ID> para equipar um item | Página {self.current_page}/{self.total_pages}")
            
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_page -= 1
        self.update_buttons()
        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_page += 1
        self.update_buttons()
        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Desequipar Tudo", style=discord.ButtonStyle.danger, emoji="♻️", custom_id="unequip_all", row=1)
    async def unequip_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        await interaction.response.defer(thinking=True, ephemeral=True)

        user_id = str(interaction.user.id)
        batch = db.batch()
        
        unequipped_count = 0
        for slot, item_data in self.equipped_items.items():
            item_ref = db.collection('characters').document(user_id).collection('inventario').document(item_data['id'])
            batch.update(item_ref, {'equipado': False})
            unequipped_count += 1
        
        if unequipped_count > 0:
            batch.commit()
            await interaction.followup.send(f"✅ {unequipped_count} item(ns) foram desequipados e movidos para a mochila.", ephemeral=True)
            # Para atualizar a view, o ideal seria o usuário clicar no botão de inventário de novo
        else:
            await interaction.followup.send("Você não tem itens equipados para desequipar.", ephemeral=True)

# ---------------------------------------------------------------------------------
# COMPONENTE SELECT CUSTOMIZADO PARA HABILIDADES
# ---------------------------------------------------------------------------------
class SkillSelect(discord.ui.Select):
    def __init__(self, slot_index: int, known_skills_options: list, equipped_skill_id: str = None):
        super().__init__(
            placeholder=f"Escolha a habilidade para o Slot {slot_index + 1}",
            options=known_skills_options,
            custom_id=f"skill_slot_{slot_index}" # ID customizado para cada slot
        )
        # Define o valor padrão explicitamente no construtor
        if equipped_skill_id:
            for option in self.options:
                if option.value == equipped_skill_id:
                    option.default = True
                    break

    async def callback(self, interaction: discord.Interaction):
        # Apenas responde à interação para o Discord não dar erro de timeout
        await interaction.response.defer()


# ---------------------------------------------------------------------------------
# VIEW DO PERFIL (Sem alterações na lógica)
# ---------------------------------------------------------------------------------
class PerfilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Inventário", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def inventario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(interaction.user.id)
        inventory_snapshot = db.collection('characters').document(user_id).collection('inventario').stream()
        equipped_items, backpack_items = {}, []
        for item_ref in inventory_snapshot:
            item_id, is_equipped = item_ref.id, item_ref.to_dict().get('equipado', False)
            instance_doc = db.collection('items').document(item_id).get()
            if not instance_doc.exists: continue
            instance_data = instance_doc.to_dict()
            template_doc = db.collection('item_templates').document(instance_data['template_id']).get()
            if not template_doc.exists: continue
            template_data = template_doc.to_dict()
            full_item_data = {"id": item_id, "instance_data": instance_data, "template_data": template_data}
            if is_equipped:
                slot = template_data.get('slot')
                if slot: equipped_items[slot] = full_item_data
            else:
                backpack_items.append(full_item_data)
        view = InventarioView(user=interaction.user, equipped_items=equipped_items, backpack_items=backpack_items)
        embed = await view.create_inventory_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Habilidades", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def habilidades(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(interaction.user.id)
        char_ref = db.collection('characters').document(user_id)
        char_doc = char_ref.get()
        if not char_doc.exists:
            await interaction.followup.send("❌ Personagem não encontrado.", ephemeral=True)
            return
        char_data = char_doc.to_dict()
        if not char_data.get('habilidades_conhecidas'):
            await interaction.followup.send("Você ainda não conhece nenhuma habilidade para gerenciar!", ephemeral=True)
            return
        view = HabilidadesView(user=interaction.user, char_data=char_data)
        embed = discord.Embed(
            title="⚔️ Gerenciar Habilidades",
            description="Use os menus abaixo para trocar suas habilidades equipadas.\n"
                        "As habilidades disponíveis são todas que seu personagem já aprendeu.\n"
                        "Clique em 'Salvar Alterações' para confirmar.",
            color=interaction.user.color
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Talentos", style=discord.ButtonStyle.secondary, emoji="🌟")
    async def talentos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Os talentos de classe serão implementados em breve!", ephemeral=True)



# ---------------------------------------------------------------------------------
# VIEW DE HABILIDADES - VERSÃO COM A CORREÇÃO FINAL
# ---------------------------------------------------------------------------------
class HabilidadesView(discord.ui.View):
    def __init__(self, user: discord.User, char_data: dict):
        super().__init__(timeout=300)
        self.user = user
        
        self.selected_skills = char_data.get('habilidades_equipadas', [])
        while len(self.selected_skills) < 3:
            self.selected_skills.append(None)

        known_skill_ids = list(set(char_data.get('habilidades_conhecidas', [])))
        
        base_options = []
        for skill_id in known_skill_ids:
            skill_info = HABILIDADES.get(skill_id)
            if skill_info:
                base_options.append(discord.SelectOption(
                    label=skill_info['nome'], value=skill_id, description=skill_info['descricao'][:100], emoji=skill_info.get('emoji')
                ))

        if not base_options:
            self.add_item(discord.ui.Button(label="Nenhuma habilidade conhecida", disabled=True))
            return

        for i in range(3):
            # ### A CORREÇÃO CRÍTICA ESTÁ AQUI ###
            # Para cada menu, criamos uma CÓPIA PROFUNDA da lista de opções.
            # Isso garante que a marcação de 'default' em um menu não afete os outros.
            current_options = [
                discord.SelectOption(label=opt.label, value=opt.value, description=opt.description, emoji=opt.emoji) 
                for opt in base_options
            ]
            
            select = discord.ui.Select(
                placeholder=f"Slot de Habilidade {i+1}", options=current_options, custom_id=f"skill_slot_{i}", row=i
            )
            select.callback = self.select_callback
            self.add_item(select)
        
        save_button = discord.ui.Button(label="Salvar Alterações", style=discord.ButtonStyle.success, row=4)
        save_button.callback = self.save_changes
        self.add_item(save_button)
        
        self.update_select_visual_state()

    def update_select_visual_state(self):
        """Atualiza o estado visual (placeholder e default) de todos os menus."""
        for i in range(3):
            select_menu = self.children[i]
            if not isinstance(select_menu, discord.ui.Select): continue
            
            default_skill_id = self.selected_skills[i]
            
            new_placeholder = f"Slot de Habilidade {i+1}"
            for option in select_menu.options:
                # Limpa o default anterior e define o novo
                option.default = option.value == default_skill_id
                if option.default:
                    new_placeholder = option.label
            select_menu.placeholder = new_placeholder

    def create_embeds(self, focused_skill_id: str = None) -> list[discord.Embed]:
        """Cria a lista de embeds para serem exibidos."""
        main_embed = discord.Embed(
            title="⚔️ Gerenciar Habilidades",
            description="Use os menus para equipar as habilidades que você conhece.\nAs informações da habilidade selecionada aparecerão abaixo.",
            color=self.user.color
        )
        embeds = [main_embed]

        if focused_skill_id and (skill_info := HABILIDADES.get(focused_skill_id)):
            details_embed = discord.Embed(color=discord.Color.dark_grey())
            details_embed.set_author(name=f"{skill_info.get('emoji', '')} {skill_info['nome']}")
            
            # --- BLOCO DE INFORMAÇÕES ATUALIZADO ---
            
            # Linha 1: Tipo e Custo de Mana
            tipo = skill_info.get('tipo', 'N/A').capitalize()
            custo = skill_info.get('custo_mana')
            info_linha1 = f"**Tipo:** {tipo}"
            if custo is not None:
                info_linha1 += f" | **Custo:** {custo} 💧"
            
            # Linha 2: Usos por Batalha
            usos = skill_info.get('usos_por_batalha')
            if usos is None:
                info_linha2 = "**Usos:** Ilimitados"
            else:
                info_linha2 = f"**Usos por Batalha:** {usos}"

            details_embed.description = f"{info_linha1}\n{info_linha2}\n\n*{skill_info['descricao']}*"
            
            # Bloco de Efeitos (continua o mesmo)
            if efeitos := skill_info.get('efeitos'):
                efeitos_str = "\n".join([format_stat(stat, val) for stat, val in efeitos.items()])
                details_embed.add_field(name="Efeitos da Habilidade", value=efeitos_str)
            
            embeds.append(details_embed)
        
        return embeds

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id: return

        slot_index = int(interaction.data['custom_id'].split('_')[-1])
        selected_skill_id = interaction.data['values'][0]

        self.selected_skills[slot_index] = selected_skill_id
        self.update_select_visual_state()
        
        embeds = self.create_embeds(focused_skill_id=selected_skill_id)
        
        await interaction.response.edit_message(embeds=embeds, view=self)

    async def save_changes(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id: return

        newly_equipped = [skill_id for skill_id in self.selected_skills if skill_id is not None]

        if len(newly_equipped) != len(set(newly_equipped)):
            await interaction.response.send_message("❌ Você não pode equipar a mesma habilidade mais de uma vez!", ephemeral=True)
            return
        
        char_ref = db.collection('characters').document(str(self.user.id))
        char_ref.update({'habilidades_equipadas': newly_equipped})

        for item in self.children: item.disabled = True
        await interaction.response.edit_message(content="✅ Habilidades atualizadas com sucesso!", view=None, embeds=[])

# ---------------------------------------------------------------------------------
# VIEW DE CRIAÇÃO DE CLASSE (Atualizada para nova estrutura de dados)
# ---------------------------------------------------------------------------------
class ClasseSelectionView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=300)
        self.user = user
        self.current_class_index = 0

    def create_embed(self):
        class_name = ORDERED_CLASSES[self.current_class_index]
        class_data = CLASSES_DATA[class_name]
        
        embed = discord.Embed(title=f"Escolha sua Classe: {class_name}", description=f"**Estilo:** {class_data['estilo']}", color=discord.Color.blue())

        # --- CORREÇÃO APLICADA AQUI ---
        # Pega a URL da imagem e verifica se ela existe antes de usá-la
        image_url = class_data.get('image_url')
        if image_url and image_url != "...": # Adicionamos uma checagem extra
            embed.set_image(url=image_url)
        # Se a URL não for válida, o embed será enviado sem a imagem, evitando o erro.

        # Busca os nomes das habilidades a partir dos IDs para exibir
        habilidades_nomes = [HABILIDADES.get(hab_id, {}).get('nome', hab_id) for hab_id in class_data['habilidades_iniciais']]
        embed.add_field(name="⚔️ Habilidades Iniciais", value="- " + "\n- ".join(habilidades_nomes) if habilidades_nomes else "Nenhuma", inline=True)
        
        embed.add_field(name="🌟 Evoluções Possíveis", value="- " + "\n- ".join(class_data['evolucoes']), inline=True)
        embed.set_footer(text=f"Classe {self.current_class_index + 1}/{len(ORDERED_CLASSES)}")
        return embed

    async def select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        for item in self.children: item.disabled = True

        class_name = ORDERED_CLASSES[self.current_class_index]
        selected_class_data = CLASSES_DATA[class_name]
        initial_skills = selected_class_data['habilidades_iniciais']
        
        # Salva o personagem com os dados limpos e corretos
        char_ref = db.collection('characters').document(str(interaction.user.id))
        char_ref.set({
            'classe': class_name, 'nivel': 1, 'xp': 0, 'moedas': 100, 'banco': 0, 'diamantes': 5,
            
            'localizacao_id': str(interaction.guild.id),
            
            'habilidades_equipadas': initial_skills,
            'habilidades_conhecidas': initial_skills
        })

        final_embed = self.create_embed()
        final_embed.title = f"✅ Classe Selecionada: {class_name}"
        final_embed.color = discord.Color.green()
        await interaction.response.edit_message(embed=final_embed, view=self)
        self.stop()
    
    # ... (os outros botões de navegação e update_message permanecem os mesmos) ...
    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_class_index = (self.current_class_index - 1) % len(ORDERED_CLASSES)
        await self.update_message(interaction)

    @discord.ui.button(label="✅ Selecionar", style=discord.ButtonStyle.success)
    async def select_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_button(interaction, button)

    @discord.ui.button(label="Próximo ➡️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_class_index = (self.current_class_index + 1) % len(ORDERED_CLASSES)
        await self.update_message(interaction)
        