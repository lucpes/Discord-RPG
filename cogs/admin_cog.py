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
            
    # --- NOVO COMANDO PARA CONFIGURAR A CIDADE ---
    @commands.command(name="configurar_cidade")
    @commands.has_permissions(administrator=True)
    async def configurar_cidade(self, ctx: commands.Context):
        """[Admin Servidor] Inicializa o servidor atual como uma cidade no jogo."""
        
        cidade_id = str(ctx.guild.id)
        cidade_ref = db.collection('cidades').document(cidade_id)

        if cidade_ref.get().exists:
            await ctx.reply(f"❗ A cidade de **{ctx.guild.name}** já está configurada no jogo.")
            return

        # --- NOVA LÓGICA DE CRIAÇÃO DE CONSTRUÇÕES ---
        construcoes_iniciais = {}
        for building_id in CONSTRUCOES.keys():
            # Mina e Floresta começam no nível 1, o resto no nível 0.
            if building_id in ["MINA", "FLORESTA"]:
                construcoes_iniciais[building_id] = {"nivel": 1}
            else:
                construcoes_iniciais[building_id] = {"nivel": 0}

        # Salva a nova cidade no Firebase
        cidade_data = {
            "nome": ctx.guild.name,
            "descricao": "Uma cidade pronta para crescer sob uma nova liderança.",
            "construcoes": construcoes_iniciais,
            # --- SALVA O ID DO PREFEITO ---
            "prefeito_id": str(ctx.author.id) 
        }
        cidade_ref.set(cidade_data)

        await ctx.reply(f"✅ A cidade de **{ctx.guild.name}** foi fundada com sucesso e você, {ctx.author.mention}, é o(a) novo(a) Prefeito(a)!")
        
        
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