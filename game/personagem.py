# game/personagem.py

from .item import Item, Arma # Importa as classes do mesmo pacote 'game'

class Personagem:
    """Representa o personagem de um jogador no RPG."""
    def __init__(self, user_id: int, nome: str):
        self.user_id = user_id  # ID do usuário do Discord
        self.nome = nome
        
        # Atributos básicos do RPG
        self.nivel = 1
        self.xp = 0
        self.xp_para_upar = 100
        self.hp_max = 50
        self.hp_atual = 50
        self.ataque_base = 5
        
        # Inventário e Equipamento
        self.inventario: list[Item] = []
        self.arma_equipada: Arma | None = None # Pode ter uma arma equipada ou não
        
        self.dinheiro = 10

    @property
    def ataque_total(self) -> int:
        """Calcula o ataque total somando o base com o da arma."""
        dano_arma = self.arma_equipada.dano if self.arma_equipada else 0
        return self.ataque_base + dano_arma

    def receber_dano(self, quantidade: int):
        """Reduz o HP do personagem."""
        self.hp_atual -= quantidade
        if self.hp_atual < 0:
            self.hp_atual = 0

    def esta_vivo(self) -> bool:
        """Verifica se o personagem tem HP > 0."""
        return self.hp_atual > 0

    def __str__(self):
        """Representação em texto do personagem, útil para o comando /perfil."""
        status_arma = self.arma_equipada.nome if self.arma_equipada else "Nenhuma"
        return (
            f"**{self.nome}** (Nível {self.nivel})\n"
            f"❤️ HP: {self.hp_atual}/{self.hp_max}\n"
            f"⚔️ Ataque: {self.ataque_total}\n"
            f"✨ XP: {self.xp}/{self.xp_para_upar}\n"
            f"💰 Dinheiro: {self.dinheiro}\n"
            f"🗡️ Arma Equipada: {status_arma}"
        )