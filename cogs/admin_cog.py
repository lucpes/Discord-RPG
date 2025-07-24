# cogs/admin_cog.py
import discord
import random
from discord.ext import commands
from firebase_config import db
from data.stats_library import format_stat
from .item_cog import get_and_increment_item_id

# Importa nossa nova função de busca
from utils.converters import find_player_by_game_id

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

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))