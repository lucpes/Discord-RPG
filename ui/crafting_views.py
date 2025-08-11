# ui/crafting_views.py
import discord
from discord import ui
from firebase_config import db
from firebase_admin import firestore
import random
from data.crafting_library import CRAFTING_RECIPES, ORDERED_RECIPES
# Importa o gerador de ID de item que já usamos na batalha
from cogs.item_cog import get_and_increment_item_id
from game.professions_helper import grant_profession_xp
from utils.inventory_helpers import check_inventory_space

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
        
        item_final_template = self.item_templates_cache.get(recipe['item_criado_template_id'], {})
        
        nivel_mesa_cidade = self.cidade_data.get('construcoes', {}).get('MESA_TRABALHO', {}).get('nivel', 0)
        profissoes_data = self.char_data.get('profissoes', {})
        nivel_artesao_jogador = profissoes_data.get('artesao', {}).get('nivel', 1)
        
        desc = f"Use os botões para navegar entre as receitas disponíveis.\n"
        desc += f"**Nível da sua Mesa de Trabalho:** `{nivel_mesa_cidade}`"
        embed = discord.Embed(title="🛠️ Mesa de Trabalho", description=desc, color=discord.Color.dark_theme())

        # Monta a string de requerimentos
        nivel_mesa_req = recipe.get('nivel_mesa_trabalho', 1)
        nivel_artesao_req = recipe.get('nivel_artesao', 1)
        req_mesa_str = f"`{nivel_mesa_req}` ({'✅' if nivel_mesa_cidade >= nivel_mesa_req else '❌'})"
        req_artesao_str = f"`{nivel_artesao_req}` ({'✅' if nivel_artesao_jogador >= nivel_artesao_req else '❌'})"
        
        # --- FORMATAÇÃO CORRIGIDA AQUI ---
        # Agora sem abreviações e com quebra de linha
        requisitos_value = (
            f"**Requer Nível da Mesa:** {req_mesa_str}\n"
            f"**Requer Nível de Artesão:** {req_artesao_str}"
        )
        
        embed.add_field(
            name=f"Criar: {item_final_template.get('emote', '📦')} {item_final_template.get('nome')}",
            value=requisitos_value,
            inline=False
        )
        
        # A verificação de 'pode_criar' agora inclui o nível de artesão
        pode_criar = (nivel_mesa_cidade >= nivel_mesa_req) and (nivel_artesao_jogador >= nivel_artesao_req)
        
        ingredientes_str = ""
        for ingrediente in recipe['ingredientes']:
            template_id = ingrediente['template_id']
            qtd_necessaria = ingrediente['quantidade']
            qtd_jogador = self.stackable_inventory.get(template_id, 0)
            
            emote_ingrediente = self.item_templates_cache.get(template_id, {}).get('emote', '❔')
            nome_ingrediente = self.item_templates_cache.get(template_id, {}).get('nome', template_id)
            
            status_emoji = "✅" if qtd_jogador >= qtd_necessaria else "❌"
            ingredientes_str += f"{emote_ingrediente} {nome_ingrediente}: `{qtd_jogador}/{qtd_necessaria}` {status_emoji}\n"
            
            if qtd_jogador < qtd_necessaria:
                pode_criar = False
        
        embed.add_field(name="Ingredientes Necessários", value=ingredientes_str or "Nenhum", inline=False)
        
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

    @ui.button(label="Criar Item", style=discord.ButtonStyle.success, emoji="🛠️", custom_id="craft_item")
    async def craft_item(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)

        # 1. PEGA O ESTADO ATUAL (sem alterações aqui)
        user_id_str = str(self.author.id)
        char_ref = db.collection('characters').document(user_id_str)
        try:
            char_doc = char_ref.get()
            if not char_doc.exists:
                return await interaction.followup.send("❌ Personagem não encontrado.", ephemeral=True)
            self.char_data = char_doc.to_dict()
        except Exception as e:
            print(f"Erro ao buscar dados do personagem: {e}")
            return await interaction.followup.send("❌ Ocorreu um erro ao buscar seus dados. Tente novamente.", ephemeral=True)

        recipe_id = ORDERED_RECIPES[self.current_recipe_index]
        recipe = CRAFTING_RECIPES[recipe_id]

        # 2. VERIFICAÇÃO DE SEGURANÇA (sem alterações aqui)
        cidade_doc = db.collection('cidades').document(str(interaction.guild.id)).get()
        nivel_mesa_cidade = cidade_doc.to_dict().get('construcoes', {}).get('MESA_TRABALHO', {}).get('nivel', 0)
        inventario_atual = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}

        nivel_artesao_jogador = self.char_data.get('profissoes', {}).get('artesao', {}).get('nivel', 1)
        if nivel_artesao_jogador < recipe.get('nivel_artesao', 1):
            return await interaction.followup.send("❌ Seu nível de Artesão é muito baixo!", ephemeral=True)

        if nivel_mesa_cidade < recipe.get('nivel_mesa_trabalho', 1):
            return await interaction.followup.send("❌ O nível da Mesa de Trabalho da cidade é muito baixo!", ephemeral=True)

        for ingrediente in recipe['ingredientes']:
            if inventario_atual.get(ingrediente['template_id'], 0) < ingrediente['quantidade']:
                return await interaction.followup.send("❌ Você não tem mais os materiais necessários!", ephemeral=True)
        
        # 3. PREPARA O CONSUMO DE MATERIAIS (sem alterações aqui)
        batch = db.batch()
        for ingrediente in recipe['ingredientes']:
            material_ref = char_ref.collection('inventario_empilhavel').document(ingrediente['template_id'])
            batch.update(material_ref, {'quantidade': firestore.Increment(-ingrediente['quantidade'])})

        # 4. ROLAGEM DE RESULTADO E PREPARAÇÃO DA CRIAÇÃO (LÓGICA CORRIGIDA)
        feedback_msg = ""
        feedback_color = discord.Color.green()
        item_criado = False

        if random.random() < recipe.get('chance_falha', 0.0):
            feedback_msg = "🔥 **Falha na Criação!**\nVocê perdeu os materiais nesta tentativa."
            feedback_color = discord.Color.dark_red()
        
        elif random.random() < recipe.get('chance_obra_prima', 0.0):
            item_criado = True
            # MODIFICAÇÃO: A lógica da obra-prima agora também se baseia no tipo de item.
            # Verifica se a obra-prima é um item único e especial (ex: uma espada lendária)
            if 'item_obra_prima_template_id' in recipe:
                item_id = recipe['item_obra_prima_template_id']
                item_template = self.item_templates_cache[item_id]

                if not check_inventory_space(char_ref, self.char_data, item_template, item_id):
                    return await interaction.followup.send("❌ Seu inventário de equipamentos está cheio! A criação foi cancelada e os materiais não foram gastos.", ephemeral=True)

                self._create_unique_item(user_id_str, item_id, batch)
                feedback_msg = f"✨ **Obra-Prima!**\nVocê forjou um item de qualidade excepcional: **{item_template['nome']}**!"
            else:
                # Se não for um item especial, a obra-prima é um bônus de quantidade do item padrão (que deve ser empilhável)
                item_id = recipe['item_criado_template_id']
                item_template = self.item_templates_cache[item_id]

                if not check_inventory_space(char_ref, self.char_data, item_template, item_id):
                    return await interaction.followup.send("❌ Seu inventário de itens empilháveis está cheio! A criação foi cancelada e os materiais não foram gastos.", ephemeral=True)
                
                qtd = recipe.get('quantidade_obra_prima', recipe.get('quantidade_criada', 1) * 2) # Bônus de quantidade
                item_ref = char_ref.collection('inventario_empilhavel').document(item_id)
                batch.set(item_ref, {'quantidade': firestore.Increment(qtd)}, merge=True)
                feedback_msg = f"✨ **Obra-Prima!**\nVocê criou com maestria e produziu **{qtd}x {item_template['nome']}**!"
        
        else:
            # Lógica para Sucesso Normal
            item_criado = True
            item_id = recipe['item_criado_template_id']
            item_template = self.item_templates_cache[item_id]

            if not check_inventory_space(char_ref, self.char_data, item_template, item_id):
                tipo_inventario = "equipamentos" if item_template.get('tipo', 'MATERIAL') in ["ARMA", "ARMADURA", "ESCUDO", "FERRAMENTA"] else "itens empilháveis"
                return await interaction.followup.send(f"❌ Seu inventário de {tipo_inventario} está cheio! A criação foi cancelada e os materiais não foram gastos.", ephemeral=True)
            
            # --- MODIFICAÇÃO PRINCIPAL ---
            # A decisão de como criar o item agora é baseada no TIPO do item, e não na receita.
            item_tipo = item_template.get('tipo', 'MATERIAL')
            if item_tipo in ["MATERIAL", "CONSUMIVEL"]:
                # Se for Material ou Consumível, cria no inventário empilhável.
                qtd = recipe.get('quantidade_criada', 1)
                item_ref = char_ref.collection('inventario_empilhavel').document(item_id)
                batch.set(item_ref, {'quantidade': firestore.Increment(qtd)}, merge=True)
                feedback_msg = f"✅ **Sucesso!**\nVocê criou **{qtd}x {item_template['nome']}**."
            else: # ARMA, ARMADURA, ESCUDO, FERRAMENTA
                # Se for qualquer outro tipo, cria como um item único no inventário de equipamentos.
                self._create_unique_item(user_id_str, item_id, batch)
                feedback_msg = f"✅ **Sucesso!**\nVocê criou **1x {item_template['nome']}**."

        # 5. e 6. CONCEDE XP E EXECUTA AS MUDANÇAS (sem alterações aqui)
        if item_criado:
            xp_ganho = recipe.get('xp_concedido', 50)
            grant_profession_xp(user_id_str, "artesao", xp_ganho)

        batch.commit()
        await interaction.followup.send(embed=discord.Embed(description=feedback_msg, color=feedback_color), ephemeral=True)

        self.stackable_inventory = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}
        char_doc_final = char_ref.get()
        if char_doc_final.exists:
            self.char_data = char_doc_final.to_dict()

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