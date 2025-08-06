# ui/crafting_views.py
import discord
from discord import ui
from firebase_config import db
from firebase_admin import firestore
import random
from data.crafting_library import CRAFTING_RECIPES, ORDERED_RECIPES
# Importa o gerador de ID de item que já usamos na batalha
from cogs.item_cog import get_and_increment_item_id

class CraftingView(ui.View):
    def __init__(self, author: discord.User, char_data: dict, cidade_data: dict, stackable_inventory: dict, item_templates_cache: dict):
        super().__init__(timeout=300)
        self.author = author
        self.char_data = char_data
        self.cidade_data = cidade_data
        self.stackable_inventory = stackable_inventory
        self.item_templates_cache = item_templates_cache # Guarda o cache de itens
        
        self.current_recipe_index = 0
        self.update_buttons()

    def update_buttons(self):
        # Lógica para desabilitar/habilitar botões de navegação
        self.children[0].disabled = self.current_recipe_index == 0
        self.children[2].disabled = self.current_recipe_index == len(ORDERED_RECIPES) - 1

    def create_embed(self) -> discord.Embed:
        recipe_id = ORDERED_RECIPES[self.current_recipe_index]
        recipe = CRAFTING_RECIPES[recipe_id]
        
        # --- ALTERAÇÃO AQUI: Usa o cache ---
        item_final_template = self.item_templates_cache.get(recipe['item_criado_template_id'], {})
        
        nivel_mesa_cidade = self.cidade_data.get('construcoes', {}).get('MESA_TRABALHO', {}).get('nivel', 0)
        
        desc = f"Use os botões para navegar entre as receitas disponíveis.\n"
        desc += f"**Nível da sua Mesa de Trabalho:** `{nivel_mesa_cidade}`"
        embed = discord.Embed(title="🛠️ Mesa de Trabalho", description=desc, color=discord.Color.dark_theme())

        item_emote = item_final_template.get('emote', '📦')
        item_nome = item_final_template.get('nome', 'Item Desconhecido')
        embed.add_field(
            name=f"Criar: {item_emote} {item_nome}",
            value=f"**Requer Mesa Nível:** `{recipe['nivel_mesa_trabalho']}`",
            inline=False
        )
        
        ingredientes_str = ""
        pode_criar = nivel_mesa_cidade >= recipe['nivel_mesa_trabalho']
        
        for ingrediente in recipe['ingredientes']:
            template_id = ingrediente['template_id']
            qtd_necessaria = ingrediente['quantidade']
            qtd_jogador = self.stackable_inventory.get(template_id, 0)
            
            # --- ALTERAÇÃO AQUI: Usa o cache ---
            emote_ingrediente = self.item_templates_cache.get(template_id, {}).get('emote', '❔')
            nome_ingrediente = self.item_templates_cache.get(template_id, {}).get('nome', template_id)
            
            status_emoji = "✅" if qtd_jogador >= qtd_necessaria else "❌"
            ingredientes_str += f"{emote_ingrediente} {nome_ingrediente}: `{qtd_jogador}/{qtd_necessaria}` {status_emoji}\n"
            
            if qtd_jogador < qtd_necessaria:
                pode_criar = False
        
        embed.add_field(name="Ingredientes Necessários", value=ingredientes_str, inline=False)
        
        craft_button = discord.utils.get(self.children, custom_id="craft_item")
        if craft_button:
            craft_button.disabled = not pode_criar

        embed.set_footer(text=f"Receita {self.current_recipe_index + 1}/{len(ORDERED_RECIPES)}")
        return embed

    @ui.button(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="prev_recipe")
    async def prev_recipe(self, interaction: discord.Interaction, button: ui.Button):
        self.current_recipe_index -= 1
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # --- BOTÃO DE CRAFT TOTALMENTE IMPLEMENTADO ---
    @ui.button(label="Criar Item", style=discord.ButtonStyle.success, emoji="🛠️", custom_id="craft_item")
    async def craft_item(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)

        # 1. PEGA O ESTADO ATUAL
        user_id_str = str(self.author.id)
        char_ref = db.collection('characters').document(user_id_str)
        recipe_id = ORDERED_RECIPES[self.current_recipe_index]
        recipe = CRAFTING_RECIPES[recipe_id]

        # 2. VERIFICAÇÃO DE SEGURANÇA NO SERVIDOR
        # Recarrega os dados para garantir que nada mudou
        cidade_doc = db.collection('cidades').document(str(interaction.guild.id)).get()
        nivel_mesa_cidade = cidade_doc.to_dict().get('construcoes', {}).get('MESA_TRABALHO', {}).get('nivel', 0)
        inventario_atual = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}

        if nivel_mesa_cidade < recipe['nivel_mesa_trabalho']:
            return await interaction.followup.send("❌ Seu nível de Mesa de Trabalho é muito baixo!", ephemeral=True)

        for ingrediente in recipe['ingredientes']:
            if inventario_atual.get(ingrediente['template_id'], 0) < ingrediente['quantidade']:
                return await interaction.followup.send("❌ Você não tem mais os materiais necessários!", ephemeral=True)
        
        # 3. PREPARA O CONSUMO DE MATERIAIS
        batch = db.batch()
        for ingrediente in recipe['ingredientes']:
            material_ref = char_ref.collection('inventario_empilhavel').document(ingrediente['template_id'])
            batch.update(material_ref, {'quantidade': firestore.Increment(-ingrediente['quantidade'])})

        # 4. ROLAGEM DE RESULTADO (FALHA -> OBRA-PRIMA -> SUCESSO)
        feedback_msg = ""
        feedback_color = discord.Color.green()

        if random.random() < recipe.get('chance_falha', 0.0):
            # --- FALHA ---
            feedback_msg = "🔥 **Falha na Criação!**\nVocê perdeu os materiais nesta tentativa."
            feedback_color = discord.Color.dark_red()
        
        elif random.random() < recipe.get('chance_obra_prima', 0.0):
            # --- SUCESSO CRÍTICO (OBRA-PRIMA) ---
            if 'quantidade_obra_prima' in recipe: # Obra-prima de consumível
                qtd = recipe['quantidade_obra_prima']
                item_id = recipe['item_criado_template_id']
                item_ref = char_ref.collection('inventario_empilhavel').document(item_id)
                batch.set(item_ref, {'quantidade': firestore.Increment(qtd)}, merge=True)
                nome_item = self.item_templates_cache[item_id]['nome']
                feedback_msg = f"✨ **Obra-Prima!**\nVocê criou com maestria e produziu **{qtd}x {nome_item}**!"
            else: # Obra-prima de equipamento
                item_id = recipe['item_obra_prima_template_id']
                self._create_unique_item(user_id_str, item_id, batch)
                nome_item = self.item_templates_cache[item_id]['nome']
                feedback_msg = f"✨ **Obra-Prima!**\nVocê forjou um item de qualidade excepcional: **{nome_item}**!"
        
        else:
            # --- SUCESSO NORMAL ---
            item_id = recipe['item_criado_template_id']
            if 'quantidade_criada' in recipe: # Sucesso normal de consumível
                qtd = recipe['quantidade_criada']
                item_ref = char_ref.collection('inventario_empilhavel').document(item_id)
                batch.set(item_ref, {'quantidade': firestore.Increment(qtd)}, merge=True)
                nome_item = self.item_templates_cache[item_id]['nome']
                feedback_msg = f"✅ **Sucesso!**\nVocê criou **{qtd}x {nome_item}**."
            else: # Sucesso normal de equipamento
                self._create_unique_item(user_id_str, item_id, batch)
                nome_item = self.item_templates_cache[item_id]['nome']
                feedback_msg = f"✅ **Sucesso!**\nVocê criou **1x {nome_item}**."

        # 5. EXECUTA AS MUDANÇAS E ATUALIZA A INTERFACE
        batch.commit()
        await interaction.followup.send(embed=discord.Embed(description=feedback_msg, color=feedback_color), ephemeral=True)

        # Recarrega o inventário e atualiza a view
        self.stackable_inventory = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}
        embed = self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @ui.button(label="➡️", style=discord.ButtonStyle.secondary, custom_id="next_recipe")
    async def next_recipe(self, interaction: discord.Interaction, button: ui.Button):
        self.current_recipe_index += 1
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # --- FUNÇÃO AJUDANTE PARA CRIAR ITENS ÚNICOS ---
    def _create_unique_item(self, owner_id: str, template_id: str, batch):
        template_data = self.item_templates_cache[template_id]
        
        transaction = db.transaction()
        item_id = get_and_increment_item_id(transaction)
        
        item_ref = db.collection('items').document(str(item_id))
        item_data = {"template_id": template_id, "owner_id": owner_id, "encantamentos_aplicados": []}
        
        if stats_base := template_data.get('stats_base'):
            item_data['stats_gerados'] = {s: random.randint(v['min'], v['max']) for s, v in stats_base.items()}
            
        if template_data.get("tipo") == "FERRAMENTA":
            atributos = template_data.get("atributos_ferramenta", {})
            item_data["durabilidade_atual"] = atributos.get("durabilidade_max", 100)
        
        batch.set(item_ref, item_data)
        
        inventory_ref = db.collection('characters').document(owner_id).collection('inventario_equipamentos').document(str(item_id))
        batch.set(inventory_ref, {'equipado': False})
        

    # O botão de filtro pode ser adicionado aqui depois