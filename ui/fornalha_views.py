# ui/fornalha_views.py
import discord
from discord import ui
from datetime import datetime, timezone, timedelta
from data.fornalha_library import FORNALHA_RECIPES, ORDERED_FORNALHA_RECIPES
from firebase_config import db
from firebase_admin import firestore
from game.professions_helper import grant_profession_xp

class FornalhaView(ui.View):
    def __init__(self, author: discord.User, char_data: dict, cidade_data: dict, stackable_inventory: dict, item_templates_cache: dict):
        super().__init__(timeout=300)
        self.author = author
        self.char_data = char_data
        self.cidade_data = cidade_data
        self.stackable_inventory = stackable_inventory
        self.item_templates_cache = item_templates_cache
        self.current_recipe_index = 0
        self.update_view()

    def update_view(self):
        self.clear_items()
        refino_status = self.char_data.get('fornalha_ativa', {})

        if not refino_status:
            self.add_item(self.PrevRecipeButton(self))
            self.add_item(self.RefineItemButton(self))
            self.add_item(self.NextRecipeButton(self))
            self.update_nav_buttons()
        else:
            termina_em = refino_status.get('termina_em').astimezone(timezone.utc)
            if datetime.now(timezone.utc) >= termina_em:
                self.add_item(self.CollectItemsButton(self))

    def update_nav_buttons(self):
        prev_button = discord.utils.get(self.children, custom_id="prev_recipe")
        next_button = discord.utils.get(self.children, custom_id="next_recipe")
        refine_button = discord.utils.get(self.children, custom_id="refine_item")

        if prev_button: prev_button.disabled = self.current_recipe_index == 0
        if next_button: next_button.disabled = self.current_recipe_index >= len(ORDERED_FORNALHA_RECIPES) - 1
        
        # Desabilita o botão de refinar se os requisitos não forem cumpridos
        if refine_button:
            if not ORDERED_FORNALHA_RECIPES:
                refine_button.disabled = True
                return
            
            recipe_id = ORDERED_FORNALHA_RECIPES[self.current_recipe_index]
            recipe = FORNALHA_RECIPES[recipe_id]
            nivel_fornalha_cidade = self.cidade_data.get('construcoes', {}).get('FORNALHA', {}).get('nivel', 0)
            nivel_ferreiro_jogador = self.char_data.get('profissoes', {}).get('ferreiro', {}).get('nivel', 1)
            
            pode_refinar = (nivel_fornalha_cidade >= recipe['nivel_fornalha']) and (nivel_ferreiro_jogador >= recipe['nivel_ferreiro'])
            for ingrediente in recipe['ingredientes']:
                if self.stackable_inventory.get(ingrediente['template_id'], 0) < ingrediente['quantidade']:
                    pode_refinar = False
                    break
            refine_button.disabled = not pode_refinar


    def create_embed(self) -> discord.Embed:
        refino_status = self.char_data.get('fornalha_ativa', {})
        
        if not refino_status:
            if not ORDERED_FORNALHA_RECIPES:
                return discord.Embed(title="🔥 Fornalha", description="Nenhuma receita de refino disponível no momento.", color=discord.Color.dark_gray())
                
            recipe_id = ORDERED_FORNALHA_RECIPES[self.current_recipe_index]
            recipe = FORNALHA_RECIPES[recipe_id]
            item_final_template = self.item_templates_cache.get(recipe['item_criado_template_id'], {})
            
            nivel_fornalha_cidade = self.cidade_data.get('construcoes', {}).get('FORNALHA', {}).get('nivel', 0)
            nivel_ferreiro_jogador = self.char_data.get('profissoes', {}).get('ferreiro', {}).get('nivel', 1)

            embed = discord.Embed(title="🔥 Fornalha", description=f"**Nível da sua Fornalha:** `{nivel_fornalha_cidade}`", color=discord.Color.orange())
            
            # --- FORMATAÇÃO CORRIGIDA AQUI ---
            req_fornalha_str = f"`{recipe['nivel_fornalha']}` ({'✅' if nivel_fornalha_cidade >= recipe['nivel_fornalha'] else '❌'})"
            req_ferreiro_str = f"`{recipe['nivel_ferreiro']}` ({'✅' if nivel_ferreiro_jogador >= recipe['nivel_ferreiro'] else '❌'})"
            
            requisitos_value = (
                f"**Requer Nível da Fornalha:** {req_fornalha_str}\n"
                f"**Requer Nível de Ferreiro:** {req_ferreiro_str}"
            )
            
            embed.add_field(
                name=f"Refinar: {item_final_template.get('emote', '📦')} {item_final_template.get('nome')}",
                value=requisitos_value,
                inline=False
            )

            ingredientes_str = ""
            for ingrediente in recipe['ingredientes']:
                template_id = ingrediente['template_id']
                qtd_necessaria = ingrediente['quantidade']
                qtd_jogador = self.stackable_inventory.get(template_id, 0)
                
                emote_ingrediente = self.item_templates_cache.get(template_id, {}).get('emote', '❔')
                nome_ingrediente = self.item_templates_cache.get(template_id, {}).get('nome', template_id)
                
                status_emoji = "✅" if qtd_jogador >= qtd_necessaria else "❌"
                ingredientes_str += f"{emote_ingrediente} {nome_ingrediente}: `{qtd_jogador}/{qtd_necessaria}` {status_emoji}\n"
            
            embed.add_field(name="Ingredientes Necessários", value=ingredientes_str or "Nenhum", inline=False)
            embed.set_footer(text=f"Receita {self.current_recipe_index + 1}/{len(ORDERED_FORNALHA_RECIPES)}")

        else:
            # --- EMBED PARA ESTADO OCUPADO OU PRONTO ---
            termina_em = refino_status.get('termina_em')
            if datetime.now(timezone.utc) >= termina_em:
                embed = discord.Embed(title="🎉 Refino Concluído!", description="Seus materiais estão prontos para serem coletados!", color=discord.Color.gold())
            else:
                embed = discord.Embed(title="🔥 Refinando...", description=f"Seus materiais estão na fornalha.\n\n**Conclusão em:** <t:{int(termina_em.timestamp())}:R>", color=discord.Color.dark_orange())

        return embed

    # --- BOTÕES COMO CLASSES INTERNAS (MÉTODO MAIS ROBUSTO) ---

    class PrevRecipeButton(ui.Button):
        def __init__(self, parent_view: 'FornalhaView'):
            super().__init__(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="prev_recipe")
            self.parent_view = parent_view
        
        async def callback(self, interaction: discord.Interaction):
            self.parent_view.current_recipe_index -= 1
            self.parent_view.update_nav_buttons()
            embed = self.parent_view.create_embed()
            await interaction.response.edit_message(embed=embed, view=self.parent_view)

    # --- BOTÃO REFINAR COM LÓGICA IMPLEMENTADA ---
    class RefineItemButton(ui.Button):
        def __init__(self, parent_view: 'FornalhaView'):
            super().__init__(label="Refinar", style=discord.ButtonStyle.success, emoji="🔥", custom_id="refine_item")
            self.parent_view = parent_view
            
        async def callback(self, interaction: discord.Interaction):
            parent = self.parent_view
            await interaction.response.defer(ephemeral=True)

            # 1. PEGA O ESTADO ATUAL
            user_id_str = str(parent.author.id)
            char_ref = db.collection('characters').document(user_id_str)
            
            char_doc = char_ref.get()
            char_data = char_doc.to_dict()
            cidade_doc = db.collection('cidades').document(str(interaction.guild.id)).get()
            cidade_data = cidade_doc.to_dict()
            inventario_atual = {item.id: item.to_dict().get('quantidade', 0) for item in char_ref.collection('inventario_empilhavel').stream()}

            # 2. VERIFICAÇÕES DE SEGURANÇA
            if 'fornalha_ativa' in char_data:
                return await interaction.followup.send("🔥 Você já tem um item a ser refinado na fornalha!", ephemeral=True)
            
            recipe_id = ORDERED_FORNALHA_RECIPES[parent.current_recipe_index]
            recipe = FORNALHA_RECIPES[recipe_id]

            nivel_fornalha_cidade = cidade_data.get('construcoes', {}).get('FORNALHA', {}).get('nivel', 0)
            nivel_ferreiro_jogador = char_data.get('profissoes', {}).get('ferreiro', {}).get('nivel', 1)

            if nivel_fornalha_cidade < recipe['nivel_fornalha']:
                return await interaction.followup.send("❌ O nível da Fornalha da cidade é muito baixo para esta receita!", ephemeral=True)
            if nivel_ferreiro_jogador < recipe['nivel_ferreiro']:
                return await interaction.followup.send(f"❌ Você não tem o nível de Ferreiro necessário! (Requer: {recipe['nivel_ferreiro']})", ephemeral=True)
            
            for ingrediente in recipe['ingredientes']:
                if inventario_atual.get(ingrediente['template_id'], 0) < ingrediente['quantidade']:
                    return await interaction.followup.send("❌ Você não tem os materiais necessários!", ephemeral=True)

            # 3. CALCULA O TEMPO FINAL (COM BÓNUS DE PROFISSÃO)
            tempo_base_s = recipe['tempo_s']
            # Exemplo: -1% de tempo por nível de Ferreiro acima do nível 1
            eficiencia_ferreiro = (nivel_ferreiro_jogador - 1) * 0.01
            tempo_final_s = int(tempo_base_s * (1 - eficiencia_ferreiro))
            termina_em = datetime.now(timezone.utc) + timedelta(seconds=tempo_final_s)

            # 4. PREPARA E EXECUTA AS ALTERAÇÕES NO FIREBASE
            batch = db.batch()
            for ingrediente in recipe['ingredientes']:
                material_ref = char_ref.collection('inventario_empilhavel').document(ingrediente['template_id'])
                batch.update(material_ref, {'quantidade': firestore.Increment(-ingrediente['quantidade'])})

            refino_data = {
                'recipe_id': recipe_id,
                'inicia_em': firestore.SERVER_TIMESTAMP,
                'termina_em': termina_em
            }
            batch.update(char_ref, {'fornalha_ativa': refino_data})
            batch.commit()

            # 5. ATUALIZA A INTERFACE
            parent.char_data['fornalha_ativa'] = refino_data
            parent.update_view()
            embed = parent.create_embed()
            await interaction.edit_original_response(embed=embed, view=parent)
            await interaction.followup.send(f"🔥 Você começou a refinar **{recipe['nome']}**!", ephemeral=True)

    class NextRecipeButton(ui.Button):
        def __init__(self, parent_view: 'FornalhaView'):
            super().__init__(label="➡️", style=discord.ButtonStyle.secondary, custom_id="next_recipe")
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            self.parent_view.current_recipe_index += 1
            self.parent_view.update_nav_buttons()
            embed = self.parent_view.create_embed()
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
    # --- BOTÃO COLETAR COM LÓGICA IMPLEMENTADA ---
    class CollectItemsButton(ui.Button):
        def __init__(self, parent_view: 'FornalhaView'):
            super().__init__(label="Coletar Itens", style=discord.ButtonStyle.success, emoji="🎉", custom_id="collect_items")
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            parent = self.parent_view
            await interaction.response.defer(ephemeral=True)
            
            # 1. PEGA O ESTADO ATUAL
            user_id_str = str(parent.author.id)
            char_ref = db.collection('characters').document(user_id_str)
            
            char_doc = char_ref.get()
            if not char_doc.exists: return
            char_data = char_doc.to_dict()

            refino_status = char_data.get('fornalha_ativa')
            if not refino_status:
                return await interaction.followup.send("Você não tem nada para coletar.", ephemeral=True)

            recipe_id = refino_status.get('recipe_id')
            recipe = FORNALHA_RECIPES.get(recipe_id)
            if not recipe:
                char_ref.update({'fornalha_ativa': firestore.DELETE_FIELD})
                return await interaction.followup.send("Erro: Receita não encontrada. O refino foi cancelado.", ephemeral=True)

            # 2. CALCULA E CONCEDE AS RECOMPENSAS
            # Concede XP de Ferreiro
            xp_ganho = recipe.get('xp_concedido', 0)
            if xp_ganho > 0:
                grant_profession_xp(user_id_str, "ferreiro", xp_ganho)
            
            # Adiciona o item refinado ao inventário empilhável
            item_criado_id = recipe['item_criado_template_id']
            quantidade_criada = recipe.get('quantidade_criada', 1)
            item_ref = char_ref.collection('inventario_empilhavel').document(item_criado_id)
            item_ref.set({'quantidade': firestore.Increment(quantidade_criada)}, merge=True)
            
            # 3. LIMPA O ESTADO E ATUALIZA A INTERFACE
            char_ref.update({'fornalha_ativa': firestore.DELETE_FIELD})
            
            parent.char_data['fornalha_ativa'] = {}
            parent.update_view()
            embed = parent.create_embed()
            await interaction.edit_original_response(embed=embed, view=parent)

            # 4. ENVIA MENSAGEM DE SUCESSO
            nome_item = parent.item_templates_cache.get(item_criado_id, {}).get('nome', 'Item')
            await interaction.followup.send(f"✅ Você coletou **{quantidade_criada}x {nome_item}** e ganhou `{xp_ganho}` de XP de Ferreiro!", ephemeral=True)