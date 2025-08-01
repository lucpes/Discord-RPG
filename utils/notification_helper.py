# utils/notification_helper.py
import discord
from discord.ext import commands

async def send_dm(bot: commands.Bot, user_id: int, embed: discord.Embed):
    """
    Tenta enviar um embed para a mensagem direta de um usuário.
    Lida com erros caso o usuário tenha DMs desativadas.
    """
    try:
        # Busca o objeto de usuário do Discord a partir do ID
        user = await bot.fetch_user(user_id)
        # Tenta enviar a mensagem direta
        await user.send(embed=embed)
        print(f"Notificação de DM enviada com sucesso para {user.name} (ID: {user_id})")
    except discord.Forbidden:
        # Ocorre se o usuário bloqueou o bot ou desativou DMs do servidor
        print(f"AVISO: Não foi possível enviar DM para o usuário {user_id}. Ele pode ter as DMs desativadas.")
    except Exception as e:
        # Para outros erros inesperados
        print(f"ERRO ao tentar enviar DM para o usuário {user_id}: {e}")