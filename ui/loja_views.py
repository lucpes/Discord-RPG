# ui/loja_views.py
import discord
from discord import ui
import math
from firebase_config import db
from firebase_admin import firestore
from data.loja_library import LOJA_INVENTARIO
# Importa o gerador de ID de item
from cogs.item_cog import get_and_increment_item_id
import random

# --- Modal de Compra Corrigido ---
class BuyModal(ui.Modal, title="Confirmar Compra"):
    def __init__(self, item_id: str, item_loja_info: dict, item_template: dict, loja_view: 'LojaView'):
        super().__init__()
        self.item_id = item_id
        self.item_loja_info = item_loja_info # Guarda os dados da loja (com preço)
        self.item_template = item_template
        self.loja_view = loja_view
        
        self.quantidade_input = ui.TextInput(label=f"Comprar: {self.item_template.get('nome', self.item_id)}", placeholder="Digite a quantidade desejada", default="1")
        self.add_item(self.quantidade_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # 1. VALIDAÇÃO DA QUANTIDADE
        try:
            quantidade = int(self.quantidade_input.value)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            return await interaction.followup.send("❌ Por favor, insira uma quantidade válida (um número inteiro maior que zero).", ephemeral=True)

        # 2. VERIFICAÇÕES DE SEGURANÇA NO SERVIDOR
        user_id_str = str(self.loja_view.author.id)
        char_ref = db.collection('characters').document(user_id_str)
        char_doc = char_ref.get()
        if not char_doc.exists: return

        char_data = char_doc.to_dict()
        preco_total = self.item_loja_info['preco_compra'] * quantidade
        tipo_moeda = self.item_loja_info['tipo_moeda']

        # Verifica se o jogador tem dinheiro suficiente
        if char_data.get(tipo_moeda.lower(), 0) < preco_total:
            moeda_str = "Moedas" if tipo_moeda == "MOEDAS" else "Diamantes"
            return await interaction.followup.send(f"❌ Você não tem {moeda_str} suficientes! Custo total: {preco_total}.", ephemeral=True)

        # 3. PROCESSA A COMPRA
        batch = db.batch()

        # Debita o dinheiro do jogador
        batch.update(char_ref, {tipo_moeda.lower(): firestore.Increment(-preco_total)})

        item_template = self.loja_view.item_templates_cache.get(self.item_id, {})
        item_tipo = item_template.get('tipo', 'MATERIAL')

        if item_tipo in ["ARMA", "ARMADURA", "ESCUDO", "FERRAMENTA"]:
            # --- LÓGICA PARA ITENS ÚNICOS (EQUIPAMENTOS) ---
            for _ in range(quantidade):
                transaction = db.transaction()
                item_id_novo = get_and_increment_item_id(transaction)
                item_ref_novo = db.collection('items').document(str(item_id_novo))
                
                item_data = {"template_id": self.item_id, "owner_id": user_id_str, "encantamentos_aplicados": []}
                if stats_base := item_template.get('stats_base'):
                    item_data['stats_gerados'] = {s: random.randint(v['min'], v['max']) for s, v in stats_base.items()}
                if item_tipo == "FERRAMENTA":
                    atributos = item_template.get("atributos_ferramenta", {})
                    item_data["durabilidade_atual"] = atributos.get("durabilidade_max", 100)
                
                batch.set(item_ref_novo, item_data)
                
                inventory_ref = char_ref.collection('inventario_equipamentos').document(str(item_id_novo))
                batch.set(inventory_ref, {'equipado': False})
        else:
            # --- LÓGICA PARA ITENS EMPILHÁVEIS ---
            inventory_ref = char_ref.collection('inventario_empilhavel').document(self.item_id)
            batch.set(inventory_ref, {'quantidade': firestore.Increment(quantidade)}, merge=True)

        batch.commit()
        
        # 4. ENVIA MENSAGEM DE SUCESSO
        await interaction.followup.send(f"✅ Compra realizada com sucesso! Você adquiriu **{quantidade}x {item_template.get('nome')}**.", ephemeral=True)

# --- A NOVA E APRIMORADA LojaView ---
class LojaView(ui.View):
    def __init__(self, author: discord.User, char_data: dict, cidade_data: dict, item_templates_cache: dict):
        super().__init__(timeout=300)
        self.author = author
        self.char_data = char_data
        self.cidade_data = cidade_data
        self.item_templates_cache = item_templates_cache
        self.current_category = None
        self.current_page = 1
        self.items_per_page = 6
        self.update_view()

    def update_view(self):
        """Atualiza a view para mostrar as categorias ou os itens paginados."""
        self.clear_items()
        nivel_loja_cidade = self.cidade_data.get('construcoes', {}).get('LOJA', {}).get('nivel', 0)

        if self.current_category is None:
            # --- TELA 1: MOSTRA AS CATEGORIAS ---
            for category_id, items in LOJA_INVENTARIO.items():
                if any(item['nivel_loja_req'] <= nivel_loja_cidade for item in items):
                    button = ui.Button(label=category_id.capitalize(), custom_id=f"category_{category_id}")
                    button.callback = self.on_category_select
                    self.add_item(button)
        else:
            # --- TELA 2: MOSTRA OS ITENS DA CATEGORIA ---
            items_in_category = [item for item in LOJA_INVENTARIO.get(self.current_category, []) if item['nivel_loja_req'] <= nivel_loja_cidade]
            
            # Lógica de Paginação
            start_index = (self.current_page - 1) * self.items_per_page
            end_index = self.current_page * self.items_per_page
            items_on_page = items_in_category[start_index:end_index]
            total_pages = math.ceil(len(items_in_category) / self.items_per_page) if items_in_category else 1

            # Adiciona os botões numerados
            for i, item_loja in enumerate(items_on_page):
                button = ui.Button(label=f"{i+1}", style=discord.ButtonStyle.success, custom_id=f"buy_{i}")
                button.callback = self.on_buy_press
                self.add_item(button)
            
            # Adiciona botões de navegação e de voltar
            prev_button = ui.Button(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="prev_page", disabled=(self.current_page == 1))
            next_button = ui.Button(label="➡️", style=discord.ButtonStyle.secondary, custom_id="next_page", disabled=(self.current_page >= total_pages))
            back_button = ui.Button(label="Voltar", style=discord.ButtonStyle.danger, custom_id="back_to_categories", row=2)
            
            prev_button.callback = self.on_page_change
            next_button.callback = self.on_page_change
            back_button.callback = self.on_back_select
            
            self.add_item(prev_button)
            self.add_item(next_button)
            self.add_item(back_button)

    def create_embed(self) -> discord.Embed:
        nivel_loja = self.cidade_data.get('construcoes', {}).get('LOJA', {}).get('nivel', 0)
        embed = discord.Embed(title=f"🏪 Loja de Utilidades (Nível {nivel_loja})", color=discord.Color.from_rgb(128, 174, 184))

        if self.current_category is None:
            embed.description = "Bem-vindo(a)! Selecione uma categoria para ver os itens disponíveis."
        else:
            embed.description = f"Itens disponíveis na categoria **{self.current_category.capitalize()}**."
            
            nivel_loja_cidade = self.cidade_data.get('construcoes', {}).get('LOJA', {}).get('nivel', 0)
            items_in_category = [item for item in LOJA_INVENTARIO.get(self.current_category, []) if item['nivel_loja_req'] <= nivel_loja_cidade]
            
            start_index = (self.current_page - 1) * self.items_per_page
            end_index = self.current_page * self.items_per_page
            items_on_page = items_in_category[start_index:end_index]
            total_pages = math.ceil(len(items_in_category) / self.items_per_page) if items_in_category else 1

            items_str = ""
            for i, item_loja in enumerate(items_on_page):
                template = self.item_templates_cache.get(item_loja['template_id'], {})
                moeda_emoji = "🪙" if item_loja['tipo_moeda'] == 'MOEDAS' else "💎"
                items_str += f"**{i+1}.** {template.get('emote', '🛒')} **{template.get('nome', item_loja['template_id'])}** - {moeda_emoji} {item_loja['preco_compra']}\n"
            
            embed.add_field(name="Itens à Venda", value=items_str or "Nenhum item disponível nesta categoria.")
            embed.set_footer(text=f"Página {self.current_page}/{total_pages}")

        return embed
        
    async def on_category_select(self, interaction: discord.Interaction):
        self.current_category = interaction.data['custom_id'].split('_')[1]
        self.current_page = 1 # Reseta para a primeira página ao mudar de categoria
        self.update_view()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_back_select(self, interaction: discord.Interaction):
        self.current_category = None
        self.update_view()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def on_page_change(self, interaction: discord.Interaction):
        if interaction.data['custom_id'] == "prev_page":
            self.current_page -= 1
        else:
            self.current_page += 1
        
        self.update_view()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def on_buy_press(self, interaction: discord.Interaction):
        item_index_on_page = int(interaction.data['custom_id'].split('_')[1])
        nivel_loja_cidade = self.cidade_data.get('construcoes', {}).get('LOJA', {}).get('nivel', 0)
        items_in_category = [item for item in LOJA_INVENTARIO.get(self.current_category, []) if item['nivel_loja_req'] <= nivel_loja_cidade]
        
        start_index = (self.current_page - 1) * self.items_per_page
        actual_item_index = start_index + item_index_on_page
        
        # --- CORREÇÃO APLICADA AQUI ---
        # Passa tanto os dados da loja quanto os dados do template para o Modal
        item_loja_info = items_in_category[actual_item_index]
        item_id = item_loja_info['template_id']
        item_template = self.item_templates_cache.get(item_id, {})
        
        modal = BuyModal(item_id, item_loja_info, item_template, self)
        await interaction.response.send_modal(modal)