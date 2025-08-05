# ui/views.py
import discord
from discord import ui
from discord.ext import commands
import math
import asyncio
from firebase_config import db
from firebase_admin import firestore
import random

from data.habilidades_library import HABILIDADES
from data.classes_data import CLASSES_DATA, ORDERED_CLASSES
from data.game_constants import EQUIPMENT_SLOTS, RARITY_EMOJIS
from data.stats_library import format_stat
from utils.storage_helper import get_signed_url
from data.construcoes_library import CONSTRUCOES
from datetime import datetime, timedelta, timezone
from utils.converters import find_player_by_game_id
from data.dungeon_monsters import TIER_MONSTERS # NOVO IMPORT
from data.monstros_library import MONSTROS
from game.stat_calculator import calcular_stats_completos
from data.minas_library import MINAS

# ---------------------------------------------------------------------------------
# VIEW DO PERFIL
# ---------------------------------------------------------------------------------
class PerfilView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Inventário", style=discord.ButtonStyle.secondary, emoji="🎒")
    async def inventario(self, interaction: discord.Interaction, button: ui.Button):
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

    @ui.button(label="Habilidades", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def habilidades(self, interaction: discord.Interaction, button: ui.Button):
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
        view = HabilidadesView(user=interaction.user, bot=interaction.client, char_data=char_data)
        embeds = view.create_embeds()
        await interaction.followup.send(embeds=embeds, view=view, ephemeral=True)

    @ui.button(label="Talentos", style=discord.ButtonStyle.secondary, emoji="🌟")
    async def talentos(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Os talentos de classe serão implementados em breve!", ephemeral=True)

# ---------------------------------------------------------------------------------
# VIEW DE INVENTÁRIO
# ---------------------------------------------------------------------------------
class InventarioView(ui.View):
    def __init__(self, user: discord.User, equipped_items: dict, backpack_items: list):
        super().__init__(timeout=300)
        self.user = user
        self.equipped_items = equipped_items
        self.backpack_items = backpack_items
        self.items_per_page = 4
        self.current_page = 1
        self.total_pages = math.ceil(len(self.backpack_items) / self.items_per_page) if self.backpack_items else 1
        self.update_buttons()

    def update_buttons(self):
        prev_button = discord.utils.get(self.children, custom_id="prev_page")
        next_button = discord.utils.get(self.children, custom_id="next_page")
        if prev_button: prev_button.disabled = self.current_page == 1
        if next_button: next_button.disabled = self.current_page >= self.total_pages

    def format_item_line(self, item_data):
        template = item_data['template_data']
        rarity_id = template.get('raridade', 'COMUM').upper()
        emoji = RARITY_EMOJIS.get(rarity_id, '⚪️')
        return f"{emoji} `[{item_data['id']}]` **{template['nome']}**"

    async def create_inventory_embed(self):
        embed = discord.Embed(title=f"Inventário de {self.user.display_name}", color=self.user.color)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        armor_slots, accessory_slots, rune_slots = ["CAPACETE", "PEITORAL", "CALCA", "BOTA"], ["MAO_PRINCIPAL", "MAO_SECUNDARIA", "ANEL", "COLAR"], ["RUNA_1", "RUNA_2"]
        armor_str, accessory_str, rune_str = "", "", ""
        tool_slots = ["PICARETA", "MACHADO"]
        for slot_id in armor_slots:
            slot_info = EQUIPMENT_SLOTS[slot_id]
            item = self.equipped_items.get(slot_id)
            armor_str += f"{slot_info['emoji']} **{slot_info['display']}:**\n" + (f"↳ {self.format_item_line(item)}\n" if item else "↳ — *Vazio*\n")
        embed.add_field(name="Armadura Principal", value=armor_str, inline=True)
        for slot_id in accessory_slots:
            slot_info = EQUIPMENT_SLOTS[slot_id]
            item = self.equipped_items.get(slot_id)
            accessory_str += f"{slot_info['emoji']} **{slot_info['display']}:**\n" + (f"↳ {self.format_item_line(item)}\n" if item else "↳ — *Vazio*\n")
        embed.add_field(name="Combate e Acessórios", value=accessory_str, inline=True)
        for slot_id in rune_slots:
            slot_info = EQUIPMENT_SLOTS[slot_id]
            item = self.equipped_items.get(slot_id)
            rune_str += f"{slot_info['emoji']} {self.format_item_line(item) if item else '— *Vazio*'}\n"
        embed.add_field(name="Runas", value=rune_str, inline=False)
        tool_str = ""
        for slot_id in tool_slots:
            slot_info = EQUIPMENT_SLOTS.get(slot_id)
            if not slot_info: continue # Ignora se o slot não estiver em game_constants
            item = self.equipped_items.get(slot_id)
            tool_str += f"{slot_info['emoji']} **{slot_info['display']}:** " + (f"{self.format_item_line(item)}\n" if item else "*Vazio*\n")
        
        if tool_str:
             embed.add_field(name="Ferramentas", value=tool_str, inline=False)
        if not self.backpack_items:
            embed.add_field(name="🎒 Mochila", value="Sua mochila está vazia.", inline=False)
        else:
            start_index, end_index = (self.current_page - 1) * self.items_per_page, self.current_page * self.items_per_page
            items_on_page = self.backpack_items[start_index:end_index]
            backpack_list = [self.format_item_line(item) for item in items_on_page]
            embed.add_field(name="🎒 Mochila", value="\n".join(backpack_list), inline=False)
            embed.set_footer(text=f"Use /equipar <ID> para equipar um item | Página {self.current_page}/{self.total_pages}")
        return embed

    @ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_page -= 1
        self.update_buttons()
        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_page += 1
        self.update_buttons()
        embed = await self.create_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Desequipar Tudo", style=discord.ButtonStyle.danger, emoji="♻️", custom_id="unequip_all", row=1)
    async def unequip_all(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user.id: return
        await interaction.response.defer(thinking=True, ephemeral=True)
        user_id = str(interaction.user.id)
        batch = db.batch()
        unequipped_count = 0
        for item_data in self.equipped_items.values():
            item_ref = db.collection('characters').document(user_id).collection('inventario').document(item_data['id'])
            batch.update(item_ref, {'equipado': False})
            unequipped_count += 1
        if unequipped_count > 0:
            batch.commit()
            await interaction.followup.send(f"✅ {unequipped_count} item(ns) foram desequipados.", ephemeral=True)
        else:
            await interaction.followup.send("Você não tem itens equipados.", ephemeral=True)

# ---------------------------------------------------------------------------------
# VIEW DE HABILIDADES
# ---------------------------------------------------------------------------------
class HabilidadesView(ui.View):
    def __init__(self, user: discord.User, bot: commands.Bot, char_data: dict):
        super().__init__(timeout=300)
        self.user = user
        self.bot = bot
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
            self.add_item(ui.Button(label="Nenhuma habilidade conhecida", disabled=True))
            return
        for i in range(3):
            current_options = [discord.SelectOption(label=opt.label, value=opt.value, description=opt.description, emoji=opt.emoji) for opt in base_options]
            select = ui.Select(placeholder=f"Slot de Habilidade {i+1}", options=current_options, custom_id=f"skill_slot_{i}", row=i)
            select.callback = self.select_callback
            self.add_item(select)
        save_button = ui.Button(label="Salvar Alterações", style=discord.ButtonStyle.success, row=4)
        save_button.callback = self.save_changes
        self.add_item(save_button)
        self.update_select_visual_state()

    def update_select_visual_state(self):
        for i in range(3):
            select_menu = self.children[i]
            if not isinstance(select_menu, ui.Select): continue
            default_skill_id = self.selected_skills[i]
            new_placeholder = f"Slot de Habilidade {i+1}"
            for option in select_menu.options:
                option.default = option.value == default_skill_id
                if option.default:
                    new_placeholder = option.label
            select_menu.placeholder = new_placeholder

    def create_embeds(self, focused_skill_id: str = None) -> list[discord.Embed]:
        main_embed = discord.Embed(title="⚔️ Gerenciar Habilidades", description="Use os menus para equipar as habilidades que você conhece.\nAs informações da habilidade selecionada aparecerão abaixo.", color=self.user.color)
        embeds = [main_embed]
        if focused_skill_id and (skill_info := HABILIDADES.get(focused_skill_id)):
            details_embed = discord.Embed(color=discord.Color.dark_grey())
            details_embed.set_author(name=f"{skill_info.get('emoji', '')} {skill_info['nome']}")
            tipo = skill_info.get('tipo', 'N/A').capitalize()
            custo = skill_info.get('custo_mana')
            info_linha1 = f"**Tipo:** {tipo}"
            if custo is not None: info_linha1 += f" | **Custo:** {custo} 💧"
            details_embed.description = f"{info_linha1}\n\n*{skill_info['descricao']}*"
            if efeitos := skill_info.get('efeitos'):
                efeitos_str = "\n".join([format_stat(stat, val) for stat, val in efeitos.items() if stat != 'DURACAO'])
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
# VIEW DE CRIAÇÃO DE CLASSE (CORRIGIDA)
# ---------------------------------------------------------------------------------
class ClasseSelectionView(ui.View):
    def __init__(self, user: discord.User, bot: commands.Bot):
        super().__init__(timeout=300)
        self.user = user
        self.bot = bot
        self.current_class_index = 0

    def create_embed(self):
        class_name = ORDERED_CLASSES[self.current_class_index]
        class_data = CLASSES_DATA[class_name]
        embed = discord.Embed(title=f"Escolha sua Classe: {class_name}", description=f"**Estilo:** {class_data['estilo']}", color=discord.Color.blue())
        image_path = class_data.get('profile_image_path')
        if image_path:
            public_url = get_signed_url(image_path)
            embed.set_image(url=public_url)
        habilidades_nomes = [HABILIDADES.get(hab_id, {}).get('nome', hab_id) for hab_id in class_data['habilidades_iniciais']]
        embed.add_field(name="⚔️ Habilidades Iniciais", value="- " + "\n- ".join(habilidades_nomes) if habilidades_nomes else "Nenhuma", inline=True)
        embed.add_field(name="🌟 Evoluções Possíveis", value="- " + "\n- ".join(class_data['evolucoes']), inline=True)
        embed.set_footer(text=f"Classe {self.current_class_index + 1}/{len(ORDERED_CLASSES)}")
        return embed

    async def select_button(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id: return
        for item in self.children: item.disabled = True
        class_name = ORDERED_CLASSES[self.current_class_index]
        selected_class_data = CLASSES_DATA[class_name]
        initial_skills = selected_class_data['habilidades_iniciais']
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

    async def update_message(self, interaction: discord.Interaction):
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_class_index = (self.current_class_index - 1) % len(ORDERED_CLASSES)
        # CORRIGIDO: Removido o argumento 'button'
        await self.update_message(interaction)

    @ui.button(label="✅ Selecionar", style=discord.ButtonStyle.success)
    async def select_button_callback(self, interaction: discord.Interaction, button: ui.Button):
        # CORRIGIDO: Removido o argumento 'button'
        await self.select_button(interaction)

    @ui.button(label="Próximo ➡️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user.id: return
        self.current_class_index = (self.current_class_index + 1) % len(ORDERED_CLASSES)
        # CORRIGIDO: Removido o argumento 'button'
        await self.update_message(interaction)

# ---------------------------------------------------------------------------------
# VIEWS DE GOVERNO
# ---------------------------------------------------------------------------------
class UpgradeView(ui.View):
    def __init__(self, author: discord.User, cidade_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.cidade_data = cidade_data
        self.selected_building_id = None
        options = []
        construcoes_atuais = self.cidade_data.get('construcoes', {})
        for building_id, building_info in CONSTRUCOES.items():
            nivel_atual = construcoes_atuais.get(building_id, {}).get('nivel', 0)
            options.append(discord.SelectOption(label=f"{building_info['nome']} (Nível {nivel_atual})", value=building_id, emoji=building_info['emoji']))
        self.select_menu = ui.Select(placeholder="Selecione uma construção para ver os detalhes...", options=options)
        self.select_menu.callback = self.on_select
        self.add_item(self.select_menu)
        self.upgrade_button = ui.Button(label="Iniciar Melhoria", style=discord.ButtonStyle.success, disabled=True)
        self.upgrade_button.callback = self.on_upgrade
        self.add_item(self.upgrade_button)

    async def on_select(self, interaction: discord.Interaction):
        self.selected_building_id = self.select_menu.values[0]
        embed = self.create_embed()
        self.upgrade_button.disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_upgrade(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if self.cidade_data.get('construcao_em_andamento'):
            await interaction.followup.send("❌ Já existe uma melhoria em andamento nesta cidade!", ephemeral=True)
            return
        building_info = CONSTRUCOES[self.selected_building_id]
        nivel_atual = self.cidade_data['construcoes'][self.selected_building_id]['nivel']
        if nivel_atual >= len(building_info.get('niveis', [])):
            await interaction.followup.send("✅ Esta construção já está no nível máximo!", ephemeral=True)
            return
        upgrade_data = building_info['niveis'][nivel_atual]
        custo = upgrade_data['custo']
        if self.selected_building_id != "CENTRO_VILA":
            nivel_centro_vila = self.cidade_data['construcoes']['CENTRO_VILA']['nivel']
            if nivel_atual >= nivel_centro_vila:
                await interaction.followup.send(f"❌ A {building_info['nome']} não pode ter um nível maior que o Centro da Vila (Nível {nivel_centro_vila})!", ephemeral=True)
                return
        tesouro_cidade = self.cidade_data.get('tesouro', {})
        for recurso, valor in custo.items():
            if tesouro_cidade.get(recurso, 0) < valor:
                await interaction.followup.send(f"❌ A cidade não tem recursos suficientes! Precisa de {valor} {recurso}, mas só tem {tesouro_cidade.get(recurso, 0)}.", ephemeral=True)
                return
        for recurso, valor in custo.items():
            tesouro_cidade[recurso] -= valor
        tempo_s = upgrade_data['tempo_s']
        termina_em = datetime.now(timezone.utc) + timedelta(seconds=tempo_s)
        construcao_em_andamento = {"id_construcao": self.selected_building_id, "nivel_alvo": nivel_atual + 1, "termina_em": termina_em}
        cidade_ref = db.collection('cidades').document(str(interaction.guild.id))
        cidade_ref.update({'tesouro': tesouro_cidade, 'construcao_em_andamento': construcao_em_andamento})
        await interaction.followup.send(f"✅ Melhoria da **{building_info['nome']}** para o **Nível {nivel_atual + 1}** iniciada! Estará pronta em <t:{int(termina_em.timestamp())}:R>.", ephemeral=True)
        self.stop()

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🏗️ Painel de Melhoria da Cidade", description="Selecione uma construção para ver os custos e tempo de melhoria.", color=discord.Color.orange())
        tesouro = self.cidade_data.get('tesouro', {})
        tesouro_str = f"🪙 Moedas: {tesouro.get('MOEDAS', 0):,}"
        embed.add_field(name="Tesouro da Cidade", value=tesouro_str, inline=False)
        if self.selected_building_id:
            building_info = CONSTRUCOES[self.selected_building_id]
            nivel_atual = self.cidade_data['construcoes'][self.selected_building_id]['nivel']
            info_str = f"Nível Atual: **{nivel_atual}**\n"
            if nivel_atual < len(building_info.get('niveis', [])):
                upgrade_data = building_info['niveis'][nivel_atual]
                custo = upgrade_data['custo']
                tempo_s = upgrade_data['tempo_s']
                custo_str = ", ".join([f"{valor:,} {recurso.capitalize()}" for recurso, valor in custo.items()])
                info_str += f"Próximo Nível: **{nivel_atual + 1}**\n"
                info_str += f"Custo: **{custo_str}**\n"
                info_str += f"Tempo de Construção: **{timedelta(seconds=tempo_s)}**"
            else:
                info_str += "**NÍVEL MÁXIMO ALCANÇADO**"
            embed.add_field(name=f"{building_info['emoji']} {building_info['nome']}", value=info_str, inline=False)
        return embed

class AddViceModal(ui.Modal, title="Adicionar Vice-Governador"):
    game_id_input = ui.TextInput(label="ID de Jogo do Usuário", placeholder="Digite o ID de Jogo (ex: 1001)")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            game_id = int(self.game_id_input.value)
        except ValueError:
            await interaction.followup.send("❌ O ID de Jogo deve ser um número.", ephemeral=True)
            return
        user, _ = await find_player_by_game_id(interaction, game_id)
        if not user:
            await interaction.followup.send(f"❌ Nenhum jogador encontrado com o ID de Jogo `{game_id}`.", ephemeral=True)
            return
        cidade_ref = db.collection('cidades').document(str(interaction.guild.id))
        cidade_ref.update({'vice_governadores_ids': firestore.ArrayUnion([game_id])})
        await interaction.followup.send(f"✅ {user.mention} foi promovido a Vice-Governador!", ephemeral=True)

class GerenciarVicesView(ui.View):
    def __init__(self, author: discord.User, bot: commands.Bot, cidade_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.bot = bot
        self.cidade_data = cidade_data
        self.vice_game_ids = self.cidade_data.get('vice_governadores_ids', [])
        add_button = ui.Button(label="Adicionar Vice", style=discord.ButtonStyle.success, emoji="➕")
        add_button.callback = self.add_vice
        self.add_item(add_button)
        if self.vice_game_ids:
            options = [discord.SelectOption(label=f"ID de Jogo: {gid}", value=str(gid)) for gid in self.vice_game_ids]
            remove_select = ui.Select(placeholder="Selecione um vice para remover...", options=options)
            remove_select.callback = self.remove_vice
            self.add_item(remove_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Apenas o governador pode gerenciar os vices.", ephemeral=True)
            return False
        return True

    async def add_vice(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddViceModal())

    async def remove_vice(self, interaction: discord.Interaction):
        game_id_to_remove = int(interaction.data['values'][0])
        cidade_ref = db.collection('cidades').document(str(interaction.guild.id))
        cidade_ref.update({'vice_governadores_ids': firestore.ArrayRemove([game_id_to_remove])})
        user_removed, _ = await find_player_by_game_id(interaction, game_id_to_remove)
        nome = user_removed.mention if user_removed else f"O jogador com ID `{game_id_to_remove}`"
        await interaction.response.send_message(f"✅ {nome} não é mais um Vice-Governador.", ephemeral=True)
        self.stop()

class GovernarPanelView(ui.View):
    def __init__(self, author: discord.User, bot: commands.Bot, cidade_data: dict, is_governor: bool):
        super().__init__(timeout=300)
        self.author = author
        self.bot = bot
        self.cidade_data = cidade_data
        self.is_governor = is_governor
        melhorias_button = ui.Button(label="Melhorar Construções", style=discord.ButtonStyle.primary, emoji="🏗️")
        melhorias_button.callback = self.open_upgrades
        self.add_item(melhorias_button)
        manage_vices_button = ui.Button(label="Gerenciar Vice-Governadores", style=discord.ButtonStyle.secondary, emoji="👥", disabled=not self.is_governor)
        manage_vices_button.callback = self.manage_vices
        self.add_item(manage_vices_button)
        
        # --- ADICIONE ESTE NOVO BOTÃO ---
        config_portal_button = ui.Button(
            label="Configurar Portal", 
            style=discord.ButtonStyle.secondary, 
            emoji="🌀", 
            disabled=not self.is_governor
        )
        config_portal_button.callback = self.open_portal_config
        self.add_item(config_portal_button)
        # --- FIM DA ADIÇÃO ---

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Você não pode interagir com o painel de outra pessoa.", ephemeral=True)
            return False
        return True

    async def open_upgrades(self, interaction: discord.Interaction):
        view = UpgradeView(author=self.author, cidade_data=self.cidade_data)
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def manage_vices(self, interaction: discord.Interaction):
        cidade_ref = db.collection('cidades').document(str(interaction.guild.id))
        cidade_data = cidade_ref.get().to_dict()
        view = GerenciarVicesView(author=self.author, bot=self.bot, cidade_data=cidade_data)
        vice_ids = cidade_data.get('vice_governadores_ids', [])
        vice_users_str = ""
        if vice_ids:
            query = db.collection('players').where('game_id', 'in', vice_ids).stream()
            vices_data = {p.to_dict()['game_id']: p.to_dict()['nick'] for p in query}
            for gid in vice_ids:
                nick = vices_data.get(gid, '*desconhecido*')
                vice_users_str += f"- **{nick}** (ID: `{gid}`)\n"
        else:
            vice_users_str = "Nenhum vice-governador nomeado."
        embed = discord.Embed(title="👥 Gerenciamento de Vice-Governadores", description=vice_users_str, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    # --- MÉTODO ATUALIZADO PARA A NOVA LÓGICA ---
    async def open_portal_config(self, interaction: discord.Interaction):
        # Responde pedindo para o usuário mencionar o canal
        await interaction.response.send_message(
            f"{interaction.user.mention}, por favor, mencione o canal de texto onde o Portal Abissal deve aparecer.\nVocê tem 60 segundos.",
            ephemeral=True
        )

        def check(m: discord.Message):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            # Espera por uma nova mensagem que passe no 'check'
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)

            if msg.channel_mentions:
                target_channel = msg.channel_mentions[0]
                channel_id = target_channel.id

                cidade_ref = db.collection('cidades').document(str(interaction.guild.id))
                cidade_ref.set({"configuracoes": {"portal_channel_id": channel_id}}, merge=True)
                
                await interaction.edit_original_response(content=f"✅ Canal do Portal configurado para {target_channel.mention}!")
                await msg.delete() # Deleta a mensagem do usuário com a menção
            else:
                await interaction.edit_original_response(content="❌ Nenhuma menção de canal válida encontrada. A configuração foi cancelada.")
                await msg.delete()

        except asyncio.TimeoutError:
            await interaction.edit_original_response(content="⏰ Tempo esgotado! A configuração do portal foi cancelada.")
        

# ---------------------------------------------------------------------------------
# VIEW DA FENDA ABISSAL ABERTA
# ---------------------------------------------------------------------------------
class PortalAbertoView(discord.ui.View):
    def __init__(self, tier_maximo: int):
        # Timeout=None faz com que a view persista mesmo após o bot reiniciar
        super().__init__(timeout=None) 
        
        # Cria um botão para cada tier disponível
        for i in range(1, tier_maximo + 1):
            botao = discord.ui.Button(
                label=f"Entrar - Tier {i}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"portal_entrar_tier_{i}",
                emoji="⚔️"
            )
            # No futuro, este callback terá a lógica de criar/entrar no lobby
            botao.callback = self.entrar_na_fenda 
            self.add_item(botao)

    async def entrar_na_fenda(self, interaction: discord.Interaction):
        # Por enquanto, este é um placeholder.
        # A lógica completa do lobby virá no próximo passo.
        custom_id = interaction.data['custom_id']
        tier_selecionado = int(custom_id.split('_')[-1])
        
        await interaction.response.send_message(
            f"Você se prepara para entrar na fenda de **Tier {tier_selecionado}**!\n"
            f"*(A funcionalidade de lobby cooperativo será implementada a seguir...)*",
            ephemeral=True
        )
        
# --- VIEW DO LOBBY COOPERATIVO (CORRIGIDA) ---
class LobbyView(ui.View):
    def __init__(self, cidade_id: str, tier: int, lider_id: int):
        super().__init__(timeout=None)
        self.cidade_id = cidade_id
        self.tier = tier
        self.lider_id = lider_id
        
        # --- ALTERADO ---
        # Armazenamos a referência do documento principal da cidade
        self.cidade_ref = db.collection('cidades').document(self.cidade_id)
        # E o caminho para o lobby que será usado nos 'updates'
        self.lobby_update_path = f"portal_abissal_ativo.lobbies.tier_{self.tier}"

    @ui.button(label="Entrar no Grupo", style=discord.ButtonStyle.success, custom_id="lobby_join")
    async def join_lobby(self, interaction: discord.Interaction, button: ui.Button):
        # --- CORRIGIDO ---
        cidade_doc = self.cidade_ref.get()
        if not cidade_doc.exists:
            # Se a cidade foi deletada por algum motivo
            await interaction.response.send_message("Erro: A cidade deste lobby não foi encontrada.", ephemeral=True)
            return

        lobby_info = cidade_doc.to_dict().get('portal_abissal_ativo', {}).get('lobbies', {}).get(f'tier_{self.tier}')
        if not lobby_info:
            await interaction.response.send_message("Este lobby não existe mais.", ephemeral=True, delete_after=10)
            await interaction.message.delete()
            return
        
        membros = lobby_info.get('membros', [])
        if len(membros) >= 4:
            return await interaction.response.send_message("❌ O grupo já está cheio!", ephemeral=True)
        if interaction.user.id in membros:
            return await interaction.response.send_message("Você já está neste grupo.", ephemeral=True)

        # Atualiza o array de membros usando o caminho corrigido
        update_path = f"{self.lobby_update_path}.membros"
        self.cidade_ref.update({update_path: firestore.ArrayUnion([interaction.user.id])})
        
        # Atualiza a mensagem do lobby para o novo jogador ver
        membros.append(interaction.user.id)
        membros_mentions = [f"• <@{mid}>" for mid in membros]
        
        embed = interaction.message.embeds[0]
        embed.description = f"**Líder:** <@{self.lider_id}>\n\n**Membros ({len(membros)}/4):**\n" + "\n".join(membros_mentions)
        
        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @ui.button(label="Sair do Grupo", style=discord.ButtonStyle.danger, custom_id="lobby_leave")
    async def leave_lobby(self, interaction: discord.Interaction, button: ui.Button):
        # Lógica para sair do lobby (pode ser implementada depois)
        await interaction.response.send_message("Você saiu do grupo.", ephemeral=True)

    @ui.button(label="Iniciar Batalha", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="lobby_start")
    async def start_battle(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.lider_id:
            return await interaction.response.send_message("Apenas o líder do grupo pode iniciar a batalha.", ephemeral=True)
        
        await interaction.response.defer()

        from cogs.mundo_cog import BattleView

        cidade_doc = self.cidade_ref.get()
        if not cidade_doc.exists:
            return await interaction.message.edit(content="Erro: A cidade deste lobby não foi encontrada.", view=None, embed=None)

        lobby_info = cidade_doc.to_dict().get('portal_abissal_ativo', {}).get('lobbies', {}).get(f'tier_{self.tier}')
        if not lobby_info:
            return await interaction.message.edit(content="Este lobby expirou.", view=None, embed=None)

        membros_ids = lobby_info.get('membros', [])
        
        # --- Preparação de Jogadores e Monstros (sem alterações) ---
        jogadores_para_batalha = []
        for user_id in membros_ids:
            user_id_str = str(user_id)
            player_doc = db.collection('players').document(user_id_str).get()
            char_doc = db.collection('characters').document(user_id_str).get()
            if not player_doc.exists or not char_doc.exists: continue
            player_data = player_doc.to_dict()
            char_data = char_doc.to_dict()
            equipped_items = [] 
            stats_finais = calcular_stats_completos(char_data, equipped_items)
            classe_info = CLASSES_DATA.get(char_data.get('classe'), {})
            combat_path = classe_info.get('combat_image_path')
            jogador_data = {
                "id": user_id, "nick": player_data.get('nick'),
                "stats": stats_finais, "classe": char_data.get('classe'),
                "vida_atual": stats_finais.get('VIDA_MAXIMA', 100),
                "mana_atual": stats_finais.get('MANA_MAXIMA', 100),
                "habilidades_equipadas": char_data.get('habilidades_equipadas', []),
                "imagem_url": get_signed_url(combat_path) if combat_path else None,
                "efeitos_ativos": []
            }
            jogadores_para_batalha.append(jogador_data)

        monstros_para_batalha = []
        grupo_de_monstros = random.choice(TIER_MONSTERS[self.tier])
        for monstro_id in grupo_de_monstros['monstros']:
            template = MONSTROS[monstro_id].copy()
            monstro_data = {**template, "id": monstro_id, "vida_atual": template['stats']['VIDA_MAXIMA'], "efeitos_ativos": []}
            monstros_para_batalha.append(monstro_data)
        
        # --- LÓGICA DE INICIALIZAÇÃO CORRIGIDA ---
        
        # 1. Cria a View da batalha
        battle_view = BattleView(
            bot=interaction.client,
            jogadores_data=jogadores_para_batalha,
            monstros_data=monstros_para_batalha,
            tier=self.tier
        )
        
        # 2. Edita a mensagem do lobby para um placeholder enquanto a batalha carrega
        await interaction.message.edit(content="Iniciando batalha...", embed=None, view=None)
        
        # 3. Associa a mensagem à View para que ela possa se auto-atualizar
        battle_view.message = await interaction.original_response()

        # 4. Inicia o ciclo de turnos, que vai definir o primeiro combatente e desenhar o painel
        await battle_view.iniciar_batalha()

        # 5. Deleta o lobby do Firebase, pois a batalha já começou
        self.cidade_ref.update({self.lobby_update_path: firestore.DELETE_FIELD})


# --- VIEW DA FENDA ABISSAL ABERTA (ATUALIZADA) ---
class PortalAbertoView(ui.View):
    def __init__(self, tier_maximo: int):
        super().__init__(timeout=None)
        for i in range(1, tier_maximo + 1):
            botao = ui.Button(label=f"Entrar - Tier {i}", style=discord.ButtonStyle.secondary, custom_id=f"portal_entrar_tier_{i}", emoji="🌀")
            botao.callback = self.criar_ou_mostrar_lobby
            self.add_item(botao)

    async def criar_ou_mostrar_lobby(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        tier = int(interaction.data['custom_id'].split('_')[-1])
        cidade_id = str(interaction.guild.id)
        portal_ref = db.collection('cidades').document(cidade_id)
        portal_doc = portal_ref.get()
        
        if not portal_doc.exists or 'portal_abissal_ativo' not in portal_doc.to_dict():
            return await interaction.followup.send("O portal para esta fenda já se fechou!", ephemeral=True)
        
        # Caminho para o lobby específico deste tier no Firebase
        lobby_path = f"portal_abissal_ativo.lobbies.tier_{tier}"
        lobby_info = portal_doc.to_dict().get('portal_abissal_ativo', {}).get('lobbies', {}).get(f'tier_{tier}')

        if lobby_info:
            await interaction.followup.send("Já existe um lobby para este Tier. Procure a mensagem do lobby para entrar!", ephemeral=True)
        else:
            # CRIA UM NOVO LOBBY
            lider_id = interaction.user.id
            membros = [lider_id]
            
            view = LobbyView(cidade_id=cidade_id, tier=tier, lider_id=lider_id)
            
            embed_lobby = discord.Embed(
                title=f"Lobby para a Fenda - Tier {tier}",
                description=f"**Líder:** {interaction.user.mention}\n\n**Membros (1/4):**\n• {interaction.user.mention}",
                color=discord.Color.blue()
            )
            embed_lobby.set_footer(text="A batalha começará quando o líder clicar em 'Iniciar Batalha'.")
            
            lobby_message = await interaction.channel.send(embed=embed_lobby, view=view)
            
            # Salva as informações do novo lobby no Firebase
            novo_lobby_data = {
                "lider_id": lider_id,
                "membros": membros,
                "message_id": lobby_message.id,
                "criado_em": firestore.SERVER_TIMESTAMP
            }
            portal_ref.update({lobby_path: novo_lobby_data})
            
            await interaction.followup.send(f"Você criou um lobby para a Fenda de Tier {tier}!", ephemeral=True)
            
# --- VIEW DE MINERAÇÃO COMPLETA E FUNCIONAL ---
class MiningView(ui.View):
    def __init__(self, author: discord.User, char_data: dict, cidade_data: dict, equipped_items: dict):
        super().__init__(timeout=300)
        self.author = author
        self.char_data = char_data
        self.cidade_data = cidade_data
        self.equipped_items = equipped_items # Guarda os itens equipados
        
        self.update_view()

    def update_view(self):
        """Atualiza a view com base no estado de mineração do jogador."""
        self.clear_items()
        mining_status = self.char_data.get('mineração_ativa', {})

        if not mining_status:
            self.add_item(self.create_mine_select())
        else:
            termina_em = mining_status.get('termina_em')
            if datetime.now(timezone.utc) >= termina_em:
                collect_button = ui.Button(label="Coletar Recompensas", style=discord.ButtonStyle.success, emoji="🎉")
                collect_button.callback = self.collect_rewards
                self.add_item(collect_button)

    def create_mine_select(self) -> ui.Select:
        """Cria o menu de seleção com as minas disponíveis."""
        nivel_mina_cidade = self.cidade_data.get('construcoes', {}).get('MINA', {}).get('nivel', 0)
        
        options = []
        for mine_id, mine_info in MINAS.items():
            if mine_info['nivel_minimo_edificio'] <= nivel_mina_cidade:
                options.append(discord.SelectOption(
                    label=mine_info['nome'], value=mine_id,
                    description=f"Tempo: {timedelta(seconds=mine_info['tempo_s'])}"
                ))

        if not options:
            return ui.Select(placeholder="Nenhuma mina disponível para o nível da cidade.", disabled=True)
        
        select = ui.Select(placeholder="Selecione uma mina para começar...", options=options)
        select.callback = self.start_mining
        return select

    async def start_mining(self, interaction: discord.Interaction):
        await interaction.response.defer()
        mine_id = interaction.data['values'][0]
        mine_info = MINAS[mine_id]

        picareta_equipada = self.equipped_items.get("PICARETA")
        if not picareta_equipada:
            await interaction.followup.send("❌ Você precisa ter uma picareta equipada para minerar!", ephemeral=True)
            return

        # --- VERIFICAÇÃO DE DURABILIDADE ADICIONADA ---
        instance_data = picareta_equipada.get('instance_data', {})
        durabilidade_atual = instance_data.get('durabilidade_atual', 0)
        
        if durabilidade_atual <= 0:
            await interaction.followup.send("❌ Sua picareta está quebrada e precisa de reparos!", ephemeral=True)
            return

        atributos_picareta = picareta_equipada['template_data'].get('atributos_ferramenta', {})
        nivel_requerido = mine_info.get('nivel_picareta', 1)
        nivel_picareta_jogador = atributos_picareta.get('nivel_mineração', 0)

        if nivel_picareta_jogador < nivel_requerido:
            await interaction.followup.send(f"❌ Sua picareta não tem o nível necessário! Esta mina requer nível `{nivel_requerido}`, mas sua ferramenta é nível `{nivel_picareta_jogador}`.", ephemeral=True)
            return
            
        # Se todas as verificações passaram, inicia a mineração
        eficiencia = atributos_picareta.get('eficiencia', 0)
        tempo_base_s = mine_info['tempo_s']
        tempo_final_s = tempo_base_s * (1 - eficiencia)
        termina_em = datetime.now(timezone.utc) + timedelta(seconds=tempo_final_s)

        char_ref = db.collection('characters').document(str(self.author.id))
        char_ref.update({
            'mineração_ativa': {
                'mina_id': mine_id,
                'inicia_em': firestore.SERVER_TIMESTAMP,
                'termina_em': termina_em
            }
        })
        
        self.char_data['mineração_ativa'] = {'termina_em': termina_em}
        self.update_view()
        embed = self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    async def collect_rewards(self, interaction: discord.Interaction):
        """Coleta as recompensas da mineração, calcula o loot e a durabilidade."""
        await interaction.response.defer()
        user_id_str = str(self.author.id)
        char_ref = db.collection('characters').document(user_id_str)
        
        mining_status = self.char_data.get('mineração_ativa', {})
        mine_id = mining_status.get('mina_id')
        if not mine_id: return

        mine_info = MINAS[mine_id]
        
        # --- CORREÇÃO APLICADA AQUI ---
        # Pega os bônus da picareta a partir do 'template_data'
        picareta_equipada = self.equipped_items.get("PICARETA")
        atributos_picareta = picareta_equipada['template_data'].get('atributos_ferramenta', {}) if picareta_equipada else {}
        
        poder_coleta = atributos_picareta.get('poder_coleta', 0)
        fortuna = atributos_picareta.get('fortuna', 0)

        # Calcula o loot final
        recompensas_coletadas = {}
        for item_info in mine_info['loot_table']:
            chance_final = item_info['chance_base'] * (1 + poder_coleta)
            if random.random() < chance_final:
                quantidade_range = item_info['quantidade']
                quantidade_base = random.randint(quantidade_range[0], quantidade_range[1])
                quantidade_final = quantidade_base + fortuna
                
                template_id = item_info['template_id']
                if quantidade_final > 0:
                    recompensas_coletadas[template_id] = recompensas_coletadas.get(template_id, 0) + quantidade_final

        # Atualiza o inventário empilhável no Firebase
        if recompensas_coletadas:
            batch = db.batch()
            for template_id, quantidade in recompensas_coletadas.items():
                item_ref = char_ref.collection('inventario_empilhavel').document(template_id)
                batch.set(item_ref, {'quantidade': firestore.Increment(quantidade)}, merge=True)
            batch.commit()

        # Lida com a durabilidade da picareta
        if picareta_equipada:
            item_id = picareta_equipada['id']
            item_ref = db.collection('items').document(item_id)
            item_ref.update({'durabilidade_atual': firestore.Increment(-1)})

        # Limpa o estado de mineração
        char_ref.update({'mineração_ativa': firestore.DELETE_FIELD})
        
        # Atualiza a interface
        self.char_data['mineração_ativa'] = {}
        self.update_view()
        embed = self.create_embed()
        
        # Monta a mensagem de sucesso
        recompensas_str = "\n".join([f" > `{qtd}x` {db.collection('item_templates').document(tid).get().to_dict()['nome']}" for tid, qtd in recompensas_coletadas.items()])
        await interaction.followup.send(
            embed=discord.Embed(
                title="✨ Recompensas Coletadas!",
                description=recompensas_str or "Você não encontrou nada de especial desta vez.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )
        await interaction.edit_original_response(embed=embed, view=self)

    def create_embed(self) -> discord.Embed:
        """Cria o embed com base no estado de mineração do jogador."""
        mining_status = self.char_data.get('mineração_ativa', {})
        
        if not mining_status:
            # Embed para o estado "Livre"
            embed = discord.Embed(
                title="⛏️ Central de Mineração",
                description="Selecione uma mina disponível para começar a extrair recursos.",
                color=discord.Color.dark_gray()
            )
            embed.set_footer(text="O nível da Mina da sua cidade libera novos locais.")
        else:
            termina_em = mining_status.get('termina_em')
            if datetime.now(timezone.utc) >= termina_em:
                # Embed para o estado "Pronto para Coletar"
                embed = discord.Embed(
                    title="🎉 Mineração Concluída! 🎉",
                    description="Seus recursos estão prontos para serem coletados! Clique no botão abaixo.",
                    color=discord.Color.gold()
                )
            else:
                # Embed para o estado "Minerando"
                embed = discord.Embed(
                    title="⛏️ Minerando...",
                    description=f"Você está trabalhando duro na extração de recursos. Volte mais tarde para coletar.\n\n**Conclusão em:** <t:{int(termina_em.timestamp())}:R>",
                    color=discord.Color.orange()
                )
        
        # --- EXIBIÇÃO DA DURABILIDADE CORRIGIDA ---
        picareta_equipada = self.equipped_items.get("PICARETA")
        if picareta_equipada:
            template_data = picareta_equipada['template_data']
            instance_data = picareta_equipada['instance_data']
            
            # Busca a durabilidade atual da instância do item
            atributos_template = template_data.get('atributos_ferramenta', {})
            dur_max = atributos_template.get('durabilidade_max', 1)
            # Se 'durabilidade_atual' não existir na instância, usa a máxima do template
            dur_atual = instance_data.get('durabilidade_atual', dur_max)

            embed.add_field(
                name="Ferramenta Equipada",
                value=f"{template_data.get('emote', '⛏️')} **{template_data.get('nome')}**\n`Durabilidade: {dur_atual}/{dur_max}`",
                inline=False
            )
        else:
            embed.add_field(
                name="Ferramenta Equipada",
                value="Você não tem uma picareta equipada!",
                inline=False
            )
            
        return embed