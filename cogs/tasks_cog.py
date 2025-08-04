# cogs/tasks_cog.py
import discord
import random
from discord.ext import commands, tasks
from firebase_config import db
from firebase_admin import firestore
from datetime import datetime, timezone, timedelta
from data.construcoes_library import CONSTRUCOES
from ui.views import PortalAbertoView # Importa nossa nova View

class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_constructions.start()
        self.verificar_portais_abissais.start() # Inicia a nova tarefa

    def cog_unload(self):
        self.check_constructions.cancel()
        self.verificar_portais_abissais.cancel() # Cancela a nova tarefa se o cog for descarregado

    @tasks.loop(minutes=1.0)
    async def check_constructions(self):
        # ... (sua função de verificar construções continua aqui, sem alterações)
        now = datetime.now(timezone.utc)
        query = db.collection('cidades').where('construcao_em_andamento.termina_em', '<=', now)
        docs_finalizados = query.stream()

        for doc in docs_finalizados:
            try:
                cidade_data = doc.to_dict()
                construcao_info = cidade_data.get('construcao_em_andamento')
                if not construcao_info: continue
                cidade_ref = doc.reference
                building_id = construcao_info['id_construcao']
                nivel_alvo = construcao_info['nivel_alvo']
                update_path = f"construcoes.{building_id}.nivel"
                cidade_ref.update({
                    update_path: nivel_alvo,
                    'construcao_em_andamento': firestore.DELETE_FIELD 
                })
                print(f"✅ Construção '{building_id}' na cidade '{cidade_data['nome']}' (ID: {doc.id}) concluída!")
            except Exception as e:
                print(f"❌ Erro ao processar construção finalizada para a cidade {doc.id}: {e}")

    # --- NOVA TAREFA PARA O PORTAL ABISSAL ---
    @tasks.loop(hours=1) # Roda a cada 10 minutos
    async def verificar_portais_abissais(self):
        now = datetime.now(timezone.utc)
        cidades_ref = db.collection('cidades').stream()

        for cidade_doc in cidades_ref:
            cidade_id = cidade_doc.id
            cidade_data = cidade_doc.to_dict()
            portal_data = cidade_data.get('portal_abissal_ativo', {})
            
            # 1. Verifica se um portal ativo já expirou
            if portal_data and portal_data.get('fecha_em') <= now:
                print(f"Fechando portal expirado na cidade {cidade_id}...")
                try:
                    channel = await self.bot.fetch_channel(portal_data['channel_id'])
                    message = await channel.fetch_message(portal_data['message_id'])
                    # Edita a mensagem para mostrar que o portal fechou
                    embed = message.embeds[0]
                    embed.title = "🌀 O Portal Abissal Fechou! 🌀"
                    embed.description = "A fenda se fechou. Aguarde até que ela se abra novamente."
                    embed.color = discord.Color.dark_grey()
                    await message.edit(embed=embed, view=None)
                except Exception as e:
                    print(f"Não foi possível editar a mensagem do portal na cidade {cidade_id}. Erro: {e}")
                
                # Limpa os dados do portal no Firebase
                cidade_doc.reference.update({"portal_abissal_ativo": firestore.DELETE_FIELD})
                continue # Pula para a próxima cidade

            # 2. Se já existe um portal ativo e válido, não faz nada
            if portal_data:
                continue

            # 3. Verifica se a cidade pode abrir um novo portal
            proxima_abertura = cidade_data.get('proxima_abertura_portal')
            if proxima_abertura and proxima_abertura > now:
                continue # Ainda não é hora de abrir

            portal_construcao = cidade_data.get('construcoes', {}).get('PORTAL_ABISSAL')
            if not portal_construcao or portal_construcao.get('nivel', 0) == 0:
                continue # A cidade não tem um portal ou ele está no nível 0

            # 4. É HORA DE ABRIR UM NOVO PORTAL!
            nivel_portal = portal_construcao['nivel']
            regras_nivel = CONSTRUCOES['PORTAL_ABISSAL']['niveis'][nivel_portal - 1]
            
            channel_id = cidade_data.get('configuracoes', {}).get('portal_channel_id')
            if not channel_id:
                print(f"AVISO: Cidade {cidade_id} tem um portal, mas nenhum canal configurado.")
                continue

            # Sorteia o Tier da fenda (de 1 até o nível do portal)
            tier_sorteado = random.randint(1, nivel_portal)
            duracao_min = regras_nivel['duracao_min']
            frequencia_h = regras_nivel['frequencia_h']
            
            try:
                channel = await self.bot.fetch_channel(channel_id)
                view = PortalAbertoView(tier_maximo=tier_sorteado)
                
                fecha_em = now + timedelta(minutes=duracao_min)
                
                embed = discord.Embed(
                    title=f"🌀 O Portal Abissal se Abriu (Tier {tier_sorteado})! 🌀",
                    description=f"Uma fenda instável para outra dimensão surgiu. Reúna seus aliados e entre para enfrentar os perigos que aguardam!\n\n**A fenda se fechará em:** <t:{int(fecha_em.timestamp())}:R>",
                    color=discord.Color.purple()
                )
                embed.set_image(url="https://i.imgur.com/ph1nHyJ.jpeg")
                
                message = await channel.send(embed=embed, view=view)
                
                # Salva os dados do portal ativo no Firebase
                novo_portal_data = {
                    "message_id": message.id, "channel_id": channel.id,
                    "tier_maximo_aberto": tier_sorteado,
                    "abre_em": now, "fecha_em": fecha_em
                }
                proxima_abertura_ts = now + timedelta(hours=frequencia_h)

                cidade_doc.reference.update({
                    "portal_abissal_ativo": novo_portal_data,
                    "proxima_abertura_portal": proxima_abertura_ts
                })
                print(f"Portal de Tier {tier_sorteado} aberto com sucesso na cidade {cidade_id}!")

            except Exception as e:
                print(f"Falha ao abrir portal na cidade {cidade_id}. Erro: {e}")


    @check_constructions.before_loop
    @verificar_portais_abissais.before_loop # Adiciona a mesma espera para a nova tarefa
    async def before_tasks(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(TasksCog(bot))