# cogs/admin_cog.py
import discord
import random
from discord.ext import commands
from firebase_config import db, bucket # Importa o bucket também
from data.stats_library import format_stat
from datetime import datetime, timedelta, timezone

# Importa as funções de ajuda
from utils.converters import find_player_by_game_id
from utils.notification_helper import send_dm
from cogs.item_cog import get_and_increment_item_id

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- COMANDOS MOVIDOS PARA DENTRO DA CLASSE ---

    @commands.command(name="criaritem")
    # @commands.is_owner()
    async def criaritem_prefix(self, ctx: commands.Context, template_id: str, id_do_jogo: int):
        """
        [Dono] Cria um item para um jogador usando o ID do Jogo.
        """
        alvo, alvo_id_str = await find_player_by_game_id(ctx, id_do_jogo)
        if not alvo:
            await ctx.reply(f"❌ Jogador com ID de Jogo `{id_do_jogo}` não encontrado.")
            return

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
        # --- LÓGICA DE DURABILIDADE ADICIONADA AQUI ---
        if template_data.get("tipo") == "FERRAMENTA":
            atributos = template_data.get("atributos_ferramenta", {})
            durabilidade_max = atributos.get("durabilidade_max", 100)
            # Define a durabilidade atual igual à máxima no momento da criação
            item_data["durabilidade_atual"] = durabilidade_max
            
        item_ref.set(item_data)
        # --- CORREÇÃO APLICADA AQUI ---
        # Salva a referência do item na coleção correta: 'inventario_equipamentos'
        inventory_ref = db.collection('characters').document(alvo_id_str).collection('inventario_equipamentos').document(str(item_id))
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
        """
        if quantidade <= 0:
            await ctx.reply("A quantidade de XP deve ser positiva.")
            return
        
        alvo, alvo_id_str = await find_player_by_game_id(ctx, id_do_jogo)
        if not alvo:
            await ctx.reply(f"❌ Jogador com ID de Jogo `{id_do_jogo}` não encontrado.")
            return
            
        from game.leveling_system import grant_xp
        result = grant_xp(user_id=alvo_id_str, amount=quantidade)

        if not result["success"]:
            await ctx.reply(f"❌ Erro: {result.get('reason', 'Desconhecido')}")
            return

        if result["leveled_up"]:
            await ctx.reply(f"🎉 **LEVEL UP!** {alvo.mention} recebeu `{quantidade}` de XP e subiu para o **nível {result['new_level']}**!")
            
            level_up_embed = discord.Embed(
                title="🎉 LEVEL UP! (Concedido por um Admin) 🎉",
                description=f"Parabéns! Você avançou para um novo nível!",
                color=discord.Color.brand_green()
            )
            level_up_embed.add_field(name="Nível Anterior", value=f"`{result['original_level']}`")
            level_up_embed.add_field(name="Novo Nível", value=f"`{result['new_level']}`")
            await send_dm(self.bot, alvo.id, level_up_embed)
        else:
            await ctx.reply(f"✅ {alvo.mention} recebeu `{result['xp_ganho']}` de XP.")

    @commands.command(name="debugstorage")
    @commands.is_owner()
    async def debug_storage(self, ctx: commands.Context, *, file_path: str):
        """[Dono] Testa a conexão e a URL para um arquivo no Firebase Storage."""
        await ctx.send(f"🔎 **Iniciando diagnóstico para o caminho:** `{file_path}`")
        report = []
        try:
            report.append(f"✅ **Bucket Conectado:** `{bucket.name}`")
        except Exception as e:
            report.append(f"❌ **Falha na Conexão com o Bucket:** `{e}`")
            await ctx.send("\n".join(report))
            return
            
        blob = bucket.blob(file_path)
        if blob.exists():
            report.append(f"✅ **Arquivo Encontrado:** O arquivo `{file_path}` existe no Storage.")
        else:
            report.append(f"❌ **Arquivo NÃO Encontrado:** Verifique o caminho exato.")
            await ctx.send("\n".join(report))
            return
            
        try:
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=15)
            signed_url = blob.generate_signed_url(expiration=expiration_time)
            report.append(f"✅ **URL Gerada com Sucesso!**")
            await ctx.send("\n".join(report))
            
            embed = discord.Embed(title="Teste de Imagem")
            embed.set_image(url=signed_url)
            await ctx.send("**Teste o embed:**", embed=embed)
            
        except Exception as e:
            report.append(f"❌ **Falha ao Gerar URL Assinada:** `{e}`")
            await ctx.send("\n".join(report))

    @commands.command(name="listarstorage")
    @commands.is_owner()
    async def listar_storage(self, ctx: commands.Context, *, prefixo: str = None):
        """[Dono] Lista os arquivos no Firebase Storage a partir de uma pasta."""
        if prefixo is None:
            await ctx.send("Por favor, forneça um prefixo (pasta) para listar.")
            return

        try:
            blobs = bucket.list_blobs(prefix=prefixo)
            file_list = [blob.name for blob in blobs]
            if not file_list:
                await ctx.send(f"Nenhum arquivo encontrado no caminho `{prefixo}`.")
                return

            formatted_list = "```\n" + "\n".join(f"- {name}" for name in file_list) + "\n```"
            embed = discord.Embed(
                title=f"📦 Arquivos Encontrados em '{prefixo}'",
                description=f"Caminhos exatos que o bot está vendo:\n{formatted_list}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Ocorreu um erro ao listar os arquivos: `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))