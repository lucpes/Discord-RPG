# cogs/admin_cog.py
import discord
import random
from discord.ext import commands
from firebase_config import db
from data.stats_library import format_stat
from .item_cog import get_and_increment_item_id
from data.construcoes_library import CONSTRUCOES
from datetime import datetime, timedelta, timezone

# Importa nossa nova função de busca
from utils.converters import find_player_by_game_id

# Importa o 'bucket' que configuramos
from firebase_config import db, bucket
from data.stats_library import format_stat


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="criaritem")
    @commands.is_owner()
    async def criaritem_prefix(self, ctx: commands.Context, template_id: str, id_do_jogo: int):
        """
        [Dono] Cria um item para um jogador usando o ID do Jogo.
        Uso: !criaritem <template_id> <id_do_jogo>
        """
        # --- LÓGICA DE BUSCA ADICIONADA ---
        alvo, alvo_id_str = await find_player_by_game_id(ctx, id_do_jogo)
        if not alvo:
            await ctx.reply(f"❌ Jogador com ID de Jogo `{id_do_jogo}` não encontrado.")
            return

        # O resto da lógica continua, usando o 'alvo' que encontramos
        template_ref = db.collection('item_templates').document(template_id)
        template_doc = template_ref.get()
        if not template_doc.exists:
            await ctx.reply(f"❌ Template com ID `{template_id}` não encontrado.")
            return

        template_data = template_doc.to_dict()
        stats_gerados = {s: random.randint(v['min'], v['max']) for s, v in template_data.get('stats_base', {}).items()}
        transaction = db.transaction()
        item_id = get_and_increment_item_id(transaction)
        item_ref = db.collection('items').document(str(item_id))
        item_data = {"template_id": template_id, "owner_id": alvo_id_str, "stats_gerados": stats_gerados, "encantamentos_aplicados": []}
        item_ref.set(item_data)
        inventory_ref = db.collection('characters').document(alvo_id_str).collection('inventario').document(str(item_id))
        inventory_ref.set({'equipado': False})

        rarity = template_data.get("raridade", "COMUM").upper()
        embed = discord.Embed(
            title="✨ Item Forjado Pelo Mestre do Jogo! ✨",
            description=f"Um novo item foi criado e entregue para {alvo.mention}.",
            color=discord.Color.gold()
        )
        embed.add_field(name="Nome do Item", value=f"**{template_data['nome']}** `[ID: {item_id}]`", inline=False)
        embed.add_field(name="Raridade", value=f"**{rarity.capitalize()}**", inline=False)
        stats_str = "\n".join([format_stat(s, v) for s, v in stats_gerados.items()]) or "Nenhum atributo base."
        embed.add_field(name="Atributos", value=stats_str, inline=False)
        embed.set_footer(text=f"Template base: {template_id}")
        await ctx.reply(embed=embed)

    @commands.command(name="darxp")
    @commands.is_owner()
    async def darxp_prefix(self, ctx: commands.Context, id_do_jogo: int, quantidade: int):
        """
        [Dono] Concede XP a um jogador usando o ID do Jogo.
        Uso: !darxp <id_do_jogo> <quantidade>
        """
        if quantidade <= 0:
            await ctx.reply("A quantidade de XP deve ser positiva.")
            return
        
        # --- LÓGICA DE BUSCA ADICIONADA ---
        alvo, alvo_id_str = await find_player_by_game_id(ctx, id_do_jogo)
        if not alvo:
            await ctx.reply(f"❌ Jogador com ID de Jogo `{id_do_jogo}` não encontrado.")
            return
            
        # Importamos a lógica de XP aqui para evitar importação circular
        from game.leveling_system import grant_xp
        result = grant_xp(user_id=alvo_id_str, amount=quantidade)

        if not result["success"]:
            await ctx.reply(f"❌ Erro: {result.get('reason', 'Desconhecido')}")
            return

        if result["leveled_up"]:
            embed = discord.Embed(title="🎉 LEVEL UP! 🎉", description=f"{alvo.mention} subiu de nível!", color=discord.Color.brand_green())
            embed.add_field(name="Nível Anterior", value=f"`{result['original_level']}`", inline=True)
            embed.add_field(name="Novo Nível", value=f"`{result['new_level']}`", inline=True)
            embed.add_field(name="XP Ganho", value=f"`{result['xp_ganho']}`", inline=True)
            embed.set_footer(text=f"XP Atual: {result['xp_atual']} / {result['xp_para_upar']}")
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"✅ {alvo.mention} recebeu `{result['xp_ganho']}` de XP.\nXP Atual: `{result['xp_atual']}` / `{result['xp_para_upar']}`")
            
    # --- A NOVA VIEW DE MELHORIA ---
class UpgradeView(discord.ui.View):
    def __init__(self, author: discord.User, cidade_data: dict):
        super().__init__(timeout=300)
        self.author = author
        self.cidade_data = cidade_data
        self.selected_building_id = None

        # Cria as opções para o menu dropdown
        options = []
        construcoes_atuais = self.cidade_data.get('construcoes', {})
        for building_id, building_info in CONSTRUCOES.items():
            nivel_atual = construcoes_atuais.get(building_id, {}).get('nivel', 0)
            options.append(discord.SelectOption(
                label=f"{building_info['nome']} (Nível {nivel_atual})",
                value=building_id,
                emoji=building_info['emoji']
            ))
        
        self.select_menu = discord.ui.Select(placeholder="Selecione uma construção para ver os detalhes...", options=options)
        self.select_menu.callback = self.on_select
        self.add_item(self.select_menu)
        
        self.upgrade_button = discord.ui.Button(label="Iniciar Melhoria", style=discord.ButtonStyle.success, disabled=True)
        self.upgrade_button.callback = self.on_upgrade
        self.add_item(self.upgrade_button)

    async def on_select(self, interaction: discord.Interaction):
        """Chamado quando uma construção é selecionada no menu."""
        self.selected_building_id = self.select_menu.values[0]
        
        # Cria o novo embed com os detalhes da melhoria
        embed = self.create_embed()
        
        self.upgrade_button.disabled = False # Ativa o botão de melhoria
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_upgrade(self, interaction: discord.Interaction):
        """Chamado quando o botão 'Iniciar Melhoria' é clicado."""
        await interaction.response.defer(ephemeral=True)
        
        # 1. Verifica se já há uma construção em andamento
        if self.cidade_data.get('construcao_em_andamento'):
            await interaction.followup.send("❌ Já existe uma melhoria em andamento nesta cidade!", ephemeral=True)
            return

        # 2. Pega os dados da construção e do próximo nível
        building_info = CONSTRUCOES[self.selected_building_id]
        nivel_atual = self.cidade_data['construcoes'][self.selected_building_id]['nivel']
        
        if nivel_atual >= len(building_info.get('niveis', [])):
            await interaction.followup.send("✅ Esta construção já está no nível máximo!", ephemeral=True)
            return

        upgrade_data = building_info['niveis'][nivel_atual]
        custo = upgrade_data['custo']
        
        # 3. Verifica o nível do Centro da Vila (a regra que criamos!)
        if self.selected_building_id != "CENTRO_VILA":
            nivel_centro_vila = self.cidade_data['construcoes']['CENTRO_VILA']['nivel']
            if nivel_atual >= nivel_centro_vila:
                await interaction.followup.send(f"❌ A {building_info['nome']} não pode ter um nível maior que o Centro da Vila (Nível {nivel_centro_vila})!", ephemeral=True)
                return

        # 4. Verifica se a cidade tem recursos suficientes
        tesouro_cidade = self.cidade_data.get('tesouro', {})
        for recurso, valor in custo.items():
            if tesouro_cidade.get(recurso, 0) < valor:
                await interaction.followup.send(f"❌ A cidade não tem recursos suficientes! Precisa de {valor} {recurso}, mas só tem {tesouro_cidade.get(recurso, 0)}.", ephemeral=True)
                return
        
        # 5. Se tudo estiver certo, inicia a construção!
        # Deduz os recursos
        for recurso, valor in custo.items():
            tesouro_cidade[recurso] -= valor
        
        # Define a construção em andamento
        tempo_s = upgrade_data['tempo_s']
        termina_em = datetime.now(timezone.utc) + timedelta(seconds=tempo_s)
        construcao_em_andamento = {
            "id_construcao": self.selected_building_id,
            "nivel_alvo": nivel_atual + 1,
            "termina_em": termina_em
        }

        # Atualiza o Firebase
        cidade_ref = db.collection('cidades').document(str(interaction.guild_id))
        cidade_ref.update({
            'tesouro': tesouro_cidade,
            'construcao_em_andamento': construcao_em_andamento
        })

        await interaction.followup.send(f"✅ Melhoria da **{building_info['nome']}** para o **Nível {nivel_atual + 1}** iniciada! Ela estará pronta em <t:{int(termina_em.timestamp())}:R>.", ephemeral=True)
        self.stop()
        await interaction.message.delete()

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🏗️ Painel de Melhoria da Cidade", description="Selecione uma construção para ver os custos e tempo de melhoria.", color=discord.Color.orange())
        
        # Mostra os recursos atuais da cidade
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

# --- O COG DE ADMINISTRAÇÃO ---
class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="configurar_cidade")
    @commands.has_permissions(administrator=True)
    async def configurar_cidade(self, ctx: commands.Context):
        cidade_id = str(ctx.guild.id)
        cidade_ref = db.collection('cidades').document(cidade_id)
        cidade_doc = cidade_ref.get()

        if not cidade_doc.exists:
            # Funda a cidade
            construcoes_iniciais = {}
            for building_id in CONSTRUCOES.keys():
                if building_id in ["CENTRO_VILA", "MINA", "FLORESTA"]:
                    construcoes_iniciais[building_id] = {"nivel": 1}
                else:
                    construcoes_iniciais[building_id] = {"nivel": 0}

            cidade_data = {
                "nome": ctx.guild.name,
                "descricao": "Uma cidade pronta para crescer.",
                "construcoes": construcoes_iniciais,
                "prefeito_id": str(ctx.author.id),
                "tesouro": {"MOEDAS": 1000} # Tesouro inicial
            }
            cidade_ref.set(cidade_data)
            await ctx.reply(f"✅ A cidade de **{ctx.guild.name}** foi fundada! Use `!configurar_cidade` novamente para abrir o painel de melhorias.")
        else:
            # Abre o painel de melhorias
            cidade_data = cidade_doc.to_dict()
            view = UpgradeView(author=ctx.author, cidade_data=cidade_data)
            embed = view.create_embed()
            await ctx.send(embed=embed, view=view)
        
        
    # --- NOVA FERRAMENTA DE DIAGNÓSTICO ---
    @commands.command(name="debugstorage")
    @commands.is_owner()
    async def debug_storage(self, ctx: commands.Context, *, file_path: str):
        """[Dono] Testa a conexão e a geração de URL para um arquivo no Firebase Storage."""
        
        await ctx.send(f"🔎 **Iniciando diagnóstico para o caminho:** `{file_path}`")
        
        report = []
        
        # 1. Verifica a conexão com o bucket
        try:
            report.append(f"✅ **Bucket Conectado:** `{bucket.name}`")
        except Exception as e:
            report.append(f"❌ **Falha na Conexão com o Bucket:** `{e}`")
            await ctx.send("\n".join(report))
            return
            
        # 2. Verifica se o arquivo (blob) existe no caminho especificado
        blob = bucket.blob(file_path)
        if blob.exists():
            report.append(f"✅ **Arquivo Encontrado:** O arquivo `{file_path}` existe no Storage.")
        else:
            report.append(f"❌ **Arquivo NÃO Encontrado:** Verifique se o caminho e o nome do arquivo estão **exatamente** corretos (incluindo letras maiúsculas/minúsculas e a extensão `.png`).")
            await ctx.send("\n".join(report))
            return
            
        # 3. Tenta gerar a URL assinada
        try:
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=15)
            signed_url = blob.generate_signed_url(expiration=expiration_time)
            report.append(f"✅ **URL Gerada com Sucesso!**")
            
            # Envia a URL para teste
            await ctx.send("\n".join(report))
            
            embed = discord.Embed(title="Teste de Imagem")
            embed.set_image(url=signed_url)
            await ctx.send("**Teste a URL abaixo no seu navegador e veja se a imagem aparece no embed:**", embed=embed)
            await ctx.send(f"Link direto (expira em 15 min):\n{signed_url}")
            
        except Exception as e:
            report.append(f"❌ **Falha ao Gerar URL Assinada:** `{e}`")
            report.append("\n**Causa Mais Provável:** A conta de serviço do bot (`firebase-adminsdk-...`) não tem a permissão **'Criador de token da conta de serviço' (Service Account Token Creator)** no Google Cloud IAM. Por favor, verifique o Passo 4 da nossa conversa anterior novamente.")
            await ctx.send("\n".join(report))

    # --- NOVA FERRAMENTA DE DIAGNÓSTICO DEFINITIVA ---
    @commands.command(name="listarstorage")
    @commands.is_owner()
    async def listar_storage(self, ctx: commands.Context, *, prefixo: str = None):
        """[Dono] Lista os arquivos no Firebase Storage a partir de um prefixo (pasta)."""
        
        if prefixo is None:
            await ctx.send("Por favor, forneça um prefixo (pasta) para listar. Ex: `!listarstorage Img-Personagens/`")
            return

        try:
            blobs = bucket.list_blobs(prefix=prefixo)
            file_list = [blob.name for blob in blobs]

            if not file_list:
                await ctx.send(f"Nenhum arquivo encontrado no caminho `{prefixo}`. Verifique o nome da pasta.")
                return

            # Formata a lista para exibição
            formatted_list = "```\n" + "\n".join(f"- {name}" for name in file_list) + "\n```"
            
            embed = discord.Embed(
                title=f"📦 Arquivos Encontrados em '{prefixo}'",
                description=f"Estes são os caminhos exatos que o bot está vendo. Copie e cole o caminho desejado no seu arquivo `data/classes_data.py`.\n{formatted_list}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Ocorreu um erro ao listar os arquivos: `{e}`")
            

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))