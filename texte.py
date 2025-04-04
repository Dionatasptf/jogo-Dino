import pygame
import os
import random
import textwrap
import time
import math
import json

# Inicialização
pygame.init()
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Batalha de Dinossauros")

# Inicializar o mixer de áudio
pygame.mixer.init()

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERDE = (0, 200, 0)
VERMELHO = (200, 0, 0)
VERMELHO_ESCURO = (150, 0, 0)
AZUL = (0, 0, 200)
AMARELO = (200, 200, 0)
CINZA = (150, 150, 150)
CINZA_ESCURO = (50, 50, 50)
MARROM = (139, 69, 19)

# Fontes
fonte = pygame.font.SysFont("Arial", 24)
fonte_pequena = pygame.font.SysFont("Arial", 18)
fonte_dialogo = pygame.font.SysFont("Arial", 16)

try:
    fonte_dino = pygame.font.Font("assets/dino_font.ttf", 20)
except:
    fonte_dino = pygame.font.SysFont("Arial", 18)

# Carregar imagens
def carregar_imagem(nome_arquivo, escala=None):
    if not os.path.exists("assets"):
        os.makedirs("assets")
    
    caminho = os.path.join("assets", nome_arquivo)
    try:
        img = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.scale(img, escala) if escala else img
    except:
        surf = pygame.Surface(escala if escala else (100, 100), pygame.SRCALPHA)
        if nome_arquivo == "fundo_menu.jpg":
            for y in range(escala[1] if escala else 100):
                azul = 50 + int(100 * y / (escala[1] if escala else 100))
                pygame.draw.line(surf, (0, 0, azul), (0, y), (escala[0] if escala else 100, y))
        elif nome_arquivo == "fundo_dino.jpg":
            for y in range(escala[1] if escala else 100):
                marrom = (100 + int(50 * y / (escala[1] if escala else 100)), 
                          50 + int(20 * y / (escala[1] if escala else 100)), 
                          10)
                pygame.draw.line(surf, marrom, (0, y), (escala[0] if escala else 100, y))
        else:
            cores = {
                "fundo_batalha.jpg": (50, 50, 80),
                "velociraptor.png": VERDE,
                "t-rex.png": VERMELHO,
                "dilofossauro.png": AZUL,
                "botao_ataque.png": (150, 0, 0),
                "botao_defesa.png": (0, 0, 150),
                "botao_proximo.png": (0, 100, 0)
            }
            cor = cores.get(nome_arquivo, BRANCO)
            pygame.draw.rect(surf, cor, (0, 0, *escala) if escala else (0, 0, 100, 100))
        return surf

# Carregar sons
def carregar_som(nome_arquivo):
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
    
    caminho = os.path.join("sounds", nome_arquivo)
    try:
        return pygame.mixer.Sound(caminho)
    except:
        fonte_erro = fonte_pequena.render(f"Erro: {nome_arquivo} não encontrado", True, VERMELHO)
        tela.blit(fonte_erro, (10, 10))
        pygame.display.flip()
        time.sleep(1)
        print(f"Erro ao carregar {nome_arquivo}. Usando silêncio como fallback.")
        return None

# Recursos
recursos = {
    "fundo": carregar_imagem("fundo_batalha.jpg", (LARGURA, ALTURA)),
    "fundo_menu": carregar_imagem("fundo_menu.jpg", (LARGURA, ALTURA)),
    "fundo_dino": carregar_imagem("fundo_dino.jpg", (LARGURA, ALTURA)),
    "velociraptor": carregar_imagem("velociraptor.png", (150, 150)),
    "t_rex": carregar_imagem("t-rex.png", (200, 200)),
    "dilofossauro": carregar_imagem("dilofossauro.png", (150, 150)),
    "botao_atacar": carregar_imagem("botao_ataque.png", (150, 40)),
    "botao_defender": carregar_imagem("botao_defesa.png", (150, 40)),
    "botao_proximo": carregar_imagem("botao_proximo.png", (70, 25))
}

# Sons
sons = {
    "velociraptor_attack1": carregar_som("velociraptor_attack1.wav"),
    "velociraptor_attack2": carregar_som("velociraptor_attack2.mp3"),
    "dilofossauro_attack1": carregar_som("dilofossauro_attack1.wav"),
    "dilofossauro_attack2": carregar_som("dilofossauro_attack2.wav"),
    "t_rex_attack1": carregar_som("t_rex_attack1.wav"),
    "t_rex_attack2": carregar_som("t_rex_attack2.wav.ogg"),
    "defend": carregar_som("defend.wav"),
    "battle_music": "sounds/battle_music.mp3"
}

class Dinossauro:
    def __init__(self, nome, sprite, x, y, tipo, vida, ataque, defesa, ataques, chance_critico, cor_contorno):
        self.nome = nome
        self.sprite = sprite
        self.x = x
        self.y = y
        self.pos_inicial_x = x
        self.pos_inicial_y = y
        self.tipo = tipo
        self.vida = vida
        self.vida_max = vida
        self.ataque = ataque
        self.defesa = defesa
        self.ataques = ataques
        self.chance_critico = chance_critico
        self.chance_critico_atual = chance_critico
        self.cor_contorno = cor_contorno
        self.status = {"veneno": 0, "sangramento": 0, "atordoado": 0}
        self.defesa_ativa = False
        self.animacao_ataque = False
        self.frame_animacao = 0
        self.pulsacao = 0

class Botao:
    def __init__(self, x, y, sprite, texto, descricao=None):
        self.rect = pygame.Rect(x, y, sprite.get_width(), sprite.get_height())
        self.sprite = sprite
        self.texto = texto
        self.descricao = descricao or []
        self.hover = False
        self.visivel = True
    
    def desenhar(self, tela):
        if not self.visivel:
            return
        tela.blit(self.sprite, self.rect)
        texto_render = fonte_pequena.render(self.texto, True, BRANCO)
        tela.blit(texto_render, (
            self.rect.x + (self.rect.width - texto_render.get_width()) // 2,
            self.rect.y + (self.rect.height - texto_render.get_height()) // 2
        ))
        
        if self.hover and self.descricao:
            max_width = max(fonte_dino.size(linha)[0] for linha in self.descricao) + 20
            height = len(self.descricao) * 20 + 20
            tooltip_x = self.rect.x
            tooltip_y = self.rect.y - height - 10
            if tooltip_y < 0:
                tooltip_y = self.rect.y + self.rect.height + 10
            pygame.draw.rect(tela, (40, 40, 40), (tooltip_x, tooltip_y, max_width, height), border_radius=5)
            pygame.draw.rect(tela, (100, 100, 100), (tooltip_x, tooltip_y, max_width, height), 2, border_radius=5)
            for i, linha in enumerate(self.descricao):
                texto = fonte_dino.render(linha, True, BRANCO)
                tela.blit(texto, (tooltip_x + 10, tooltip_y + 10 + i * 20))
    
    def verificar_clique(self, pos):
        if not self.visivel:
            return False
        self.hover = self.rect.collidepoint(pos)
        return self.hover

class CaixaDialogo:
    def __init__(self, x, y, largura, altura):
        self.rect = pygame.Rect(x, y, largura, altura)
        self.mensagens = []
        self.mensagem_atual = ""
        self.indice_mensagem = 0
        self.botao_proximo = Botao(x + largura - 80, y + altura - 30, 
                                  recursos["botao_proximo"], 
                                  "Próximo")
        self.botao_proximo.visivel = False
        self.turno_jogador = False
    
    def adicionar_mensagem(self, mensagem, turno_jogador=False):
        self.turno_jogador = turno_jogador
        self.mensagens = []
        for linha in mensagem.split('\n'):
            linhas_quebradas = textwrap.wrap(linha, width=60)
            self.mensagens.extend(linhas_quebradas)
        self.indice_mensagem = 0
        if self.mensagens:
            self.mensagem_atual = self.mensagens[self.indice_mensagem]
    
    def proxima_mensagem(self):
        self.indice_mensagem += 1
        if self.indice_mensagem < len(self.mensagens):
            self.mensagem_atual = self.mensagens[self.indice_mensagem]
            return False
        return True
    
    def desenhar(self, tela):
        pygame.draw.rect(tela, (0, 0, 0, 200), self.rect, border_radius=10)
        pygame.draw.rect(tela, (100, 100, 100), self.rect, 2, border_radius=10)
        
        y_pos = self.rect.y + 10
        texto = fonte_dialogo.render(self.mensagem_atual, True, BRANCO)
        tela.blit(texto, (self.rect.x + 10, y_pos))
        
        if self.mensagens and self.indice_mensagem < len(self.mensagens) - 1:
            self.botao_proximo.visivel = True
            self.botao_proximo.desenhar(tela)
        elif not self.turno_jogador:
            self.botao_proximo.visivel = True
            self.botao_proximo.desenhar(tela)
        else:
            self.botao_proximo.visivel = False

def desenhar_barra_vida_e_sangramento(dino, x, y):
    largura = 200
    altura = 15
    espacamento = 5
    
    pygame.draw.rect(tela, VERMELHO, (x, y, largura, altura))
    vida_largura = max(0, largura * (dino.vida / dino.vida_max))
    pygame.draw.rect(tela, VERDE, (x, y, vida_largura, altura))
    
    texto = fonte_pequena.render(f"{dino.nome}: {dino.vida}/{dino.vida_max}", True, BRANCO)
    tela.blit(texto, (x, y - 20))
    
    if dino.status["sangramento"] > 0:
        sangramento_largura = largura * (dino.status["sangramento"] / 3)
        pygame.draw.rect(tela, VERMELHO_ESCURO, (x, y + altura + espacamento, sangramento_largura, altura))

def aplicar_efeito(alvo, efeito):
    if efeito and random.random() <= 0.8:
        if efeito == "veneno":
            alvo.status["veneno"] = 3
            return f"{alvo.nome} foi envenenado!"
        elif efeito == "sangramento":
            alvo.status["sangramento"] = min(3, alvo.status["sangramento"] + 1)
            return f"{alvo.nome} está sangrando!"
        elif efeito == "atordoar" and random.random() <= 0.5:
            alvo.status["atordoado"] = 1
            return f"{alvo.nome} foi atordoado!"
    return ""

def processar_status(dino):
    dano_total = 0
    mensagens = []
    if dino.status["veneno"] > 0:
        dano = 2
        dano_total += dano
        dino.status["veneno"] -= 1
        mensagens.append(f"☠️ Veneno: -{dano} HP (Restam: {dino.status['veneno']} turnos)")
    
    if dino.status["sangramento"] > 0:
        dano = 2 * dino.status["sangramento"]
        dano_total += dano
        mensagens.append(f"💉 Sangramento: -{dano} HP")
        dino.status["sangramento"] -= 1
    
    dino.vida = max(0, dino.vida - dano_total)
    return mensagens

def desenhar_dinossauro_com_destaque(tela, dino, tempo):
    dino.pulsacao = math.sin(tempo * 3) * 5
    sombra = pygame.Surface((dino.sprite.get_width() + 20, dino.sprite.get_height() + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 100), (0, 0, sombra.get_width(), sombra.get_height()))
    tela.blit(sombra, (dino.x - 10, dino.y + dino.sprite.get_height() - 20))
    
    contorno = pygame.transform.scale(dino.sprite, 
                                     (int(dino.sprite.get_width() + 10 + dino.pulsacao), 
                                      int(dino.sprite.get_height() + 10 + dino.pulsacao)))
    contorno.fill(dino.cor_contorno, special_flags=pygame.BLEND_RGBA_MULT)
    tela.blit(contorno, (dino.x - 5 - dino.pulsacao / 2, dino.y - 5 - dino.pulsacao / 2))
    
    tela.blit(dino.sprite, (dino.x, dino.y))

def tela_inicio():
    botao_jogar = Botao(LARGURA//2 - 75, ALTURA//2 - 50, recursos["botao_atacar"], "JOGAR")
    botao_opcoes = Botao(LARGURA//2 - 75, ALTURA//2 + 20, recursos["botao_defender"], "OPÇÕES")
    
    while True:
        tela.blit(recursos["fundo_menu"], (0, 0))
        titulo = fonte.render("BATALHA DE DINOSSAUROS", True, AMARELO)
        subtitulo = fonte_pequena.render("Um combate jurássico!", True, BRANCO)
        tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 150))
        tela.blit(subtitulo, (LARGURA//2 - subtitulo.get_width()//2, 200))
        
        botao_jogar.desenhar(tela)
        botao_opcoes.desenhar(tela)
        
        versao = fonte_pequena.render("Versão 1.0", True, CINZA)
        tela.blit(versao, (LARGURA - versao.get_width() - 20, ALTURA - 30))
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return "sair"
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if botao_jogar.verificar_clique(pygame.mouse.get_pos()):
                    return "jogar"
                elif botao_opcoes.verificar_clique(pygame.mouse.get_pos()):
                    mostrar_opcoes()
        
        pygame.display.flip()

def mostrar_opcoes():
    botao_voltar = Botao(LARGURA//2 - 75, ALTURA - 100, recursos["botao_defender"], "VOLTAR")
    volume = 0.5
    dificuldade = "Normal"
    botao_facil = Botao(LARGURA//2, 300, recursos["botao_atacar"], "Fácil")
    botao_normal = Botao(LARGURA//2 + 160, 300, recursos["botao_atacar"], "Normal")
    
    while True:
        tela.blit(recursos["fundo_menu"], (0, 0))
        titulo = fonte.render("OPÇÕES", True, BRANCO)
        tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 100))
        
        texto_volume = fonte_pequena.render("Volume:", True, BRANCO)
        tela.blit(texto_volume, (LARGURA//2 - 150, 200))
        pygame.draw.rect(tela, CINZA, (LARGURA//2, 200, 200, 20), border_radius=10)
        pygame.draw.rect(tela, VERDE, (LARGURA//2, 200, int(200 * volume), 20), border_radius=10)
        
        texto_dificuldade = fonte_pequena.render(f"Dificuldade: {dificuldade}", True, BRANCO)
        tela.blit(texto_dificuldade, (LARGURA//2 - 150, 300))
        botao_facil.desenhar(tela)
        botao_normal.desenhar(tela)
        
        controles = [
            "CONTROLES:",
            "- Clique nos botões para atacar ou defender",
            "- Clique em Próximo para avançar",
            "- S/N para reiniciar ou sair no final"
        ]
        
        for i, linha in enumerate(controles):
            texto = fonte_pequena.render(linha, True, BRANCO)
            tela.blit(texto, (LARGURA//2 - texto.get_width()//2, 350 + i*25))
        
        botao_voltar.desenhar(tela)
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if botao_voltar.verificar_clique(pygame.mouse.get_pos()):
                    return dificuldade
                if botao_facil.verificar_clique(pygame.mouse.get_pos()):
                    dificuldade = "Fácil"
                if botao_normal.verificar_clique(pygame.mouse.get_pos()):
                    dificuldade = "Normal"
                if LARGURA//2 <= pygame.mouse.get_pos()[0] <= LARGURA//2 + 200 and 200 <= pygame.mouse.get_pos()[1] <= 220:
                    volume = (pygame.mouse.get_pos()[0] - LARGURA//2) / 200
                    pygame.mixer.music.set_volume(volume)
            if evento.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    if LARGURA//2 <= pygame.mouse.get_pos()[0] <= LARGURA//2 + 200 and 200 <= pygame.mouse.get_pos()[1] <= 220:
                        volume = (pygame.mouse.get_pos()[0] - LARGURA//2) / 200
                        pygame.mixer.music.set_volume(volume)
        
        pygame.display.flip()

def tela_selecao():
    velociraptor, dilofossauro, _ = criar_dinossauros()
    
    desc_velociraptor = [
        "Velociraptor",
        "Tipo: Carnívoro Ágil",
        "HP: 80 | ATQ: 22 | DEF: 6 | Crit: 25%+",
        "Ataques:",
        "- Arranhão (14 + sangrar)",  # Ajustado
        "- Mordida (22)"              # Ajustado
    ]
    
    desc_dilofossauro = [
        "Dilofossauro",
        "Tipo: Venenoso Astuto",
        "HP: 70 | ATQ: 20 | DEF: 8 | Crit: 15%+",
        "Ataques:",
        "- Mordida (17 + sangrar)",      # Ajustado
        "- Veneno da Morte (11 + veneno)"  # Ajustado
    ]
    
    botoes = [
        Botao(150, 250, recursos["velociraptor"], "Velociraptor", desc_velociraptor),
        Botao(450, 250, recursos["dilofossauro"], "Dilofossauro", desc_dilofossauro)
    ]
    
    while True:
        tela.blit(recursos["fundo_dino"], (0, 0))
        titulo = fonte.render("ESCOLHA SEU DINOSSAURO", True, AMARELO)
        tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 50))
        
        instrucao = fonte_pequena.render("Passe o mouse para ver as informações", True, BRANCO)
        tela.blit(instrucao, (LARGURA//2 - instrucao.get_width()//2, 100))
        
        mouse_pos = pygame.mouse.get_pos()
        for botao in botoes:
            botao.verificar_clique(mouse_pos)
            botao.desenhar(tela)
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return None
            if evento.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if botoes[0].verificar_clique(pos):
                    return velociraptor
                elif botoes[1].verificar_clique(pos):
                    return dilofossauro
        
        pygame.display.flip()

def animar_ataque(dino, alvo):
    if dino.animacao_ataque:
        velocidade = 5 + (dino.ataque // 5)
        if dino.frame_animacao < 10:
            if dino.x < alvo.x:
                dino.x += velocidade
            else:
                dino.x -= velocidade
            dino.frame_animacao += 1
        elif dino.frame_animacao < 15:
            alvo.y = alvo.pos_inicial_y + math.sin(dino.frame_animacao * 2) * 5
            dino.frame_animacao += 1
        else:
            dino.animacao_ataque = False
            dino.frame_animacao = 0
            dino.x, dino.y = dino.pos_inicial_x, dino.pos_inicial_y
            alvo.y = alvo.pos_inicial_y

def batalha(jogador, inimigo, dificuldade="Normal"):
    if dificuldade == "Fácil":
        inimigo.vida = int(inimigo.vida * 0.8)
        inimigo.vida_max = inimigo.vida
        inimigo.ataque = int(inimigo.ataque * 0.8)
    
    altura_plataforma = 40
    plataforma_y = ALTURA - altura_plataforma - 100
    
    jogador.x, jogador.y = 120, plataforma_y - jogador.sprite.get_height()
    inimigo.x, inimigo.y = 530, plataforma_y - inimigo.sprite.get_height()
    jogador.pos_inicial_x, jogador.pos_inicial_y = jogador.x, jogador.y
    inimigo.pos_inicial_x, inimigo.pos_inicial_y = inimigo.x, inimigo.y
    
    if jogador.nome == "Velociraptor":
        botoes = [
            Botao(50, ALTURA - 100, recursos["botao_atacar"], "Arranhão", ["Ataque básico"]),
            Botao(210, ALTURA - 100, recursos["botao_atacar"], "Mordida", ["Ataque especial"]),
            Botao(130, ALTURA - 50, recursos["botao_defender"], "Esquiva", ["Reduz dano recebido"])
        ]
    else:  # Dilofossauro
        botoes = [
            Botao(50, ALTURA - 100, recursos["botao_atacar"], "Mordida", ["Ataque básico"]),
            Botao(210, ALTURA - 100, recursos["botao_atacar"], "Veneno da Morte", ["Ataque especial"]),
            Botao(130, ALTURA - 50, recursos["botao_defender"], "Escuridão", ["Reduz dano recebido"])
        ]
    
    caixa_dialogo = CaixaDialogo(50, 100, 700, 100)
    caixa_dialogo.adicionar_mensagem(f"Turno de {jogador.nome}! Escolha sua ação.", turno_jogador=True)
    
    try:
        pygame.mixer.music.load(sons["battle_music"])
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except:
        print("Erro ao carregar música de fundo.")

    clock = pygame.time.Clock()
    turno_jogador = True
    esperando_input = True
    rodada = 1
    tempo = 0
    
    while True:
        tempo += 0.016
        
        tela.blit(recursos["fundo"], (0, 0))
        
        plataforma = pygame.Rect(0, plataforma_y, LARGURA, altura_plataforma)
        pygame.draw.rect(tela, MARROM, plataforma)
        pygame.draw.rect(tela, CINZA_ESCURO, plataforma, 2)
        
        animar_ataque(jogador, inimigo)
        animar_ataque(inimigo, jogador)
        
        desenhar_dinossauro_com_destaque(tela, inimigo, tempo)
        desenhar_dinossauro_com_destaque(tela, jogador, tempo)
        
        desenhar_barra_vida_e_sangramento(jogador, 50, 50)
        desenhar_barra_vida_e_sangramento(inimigo, LARGURA - 250, 50)
        
        texto_rodada = fonte_pequena.render(
            f"Rodada: {rodada} | Turno: {'Jogador' if turno_jogador else 'T-Rex'} | Crit: {int(jogador.chance_critico_atual * 100)}%",
            True, BRANCO
        )
        tela.blit(texto_rodada, (LARGURA//2 - texto_rodada.get_width()//2, 10))
        
        if turno_jogador and esperando_input and not jogador.animacao_ataque and not inimigo.animacao_ataque:
            for botao in botoes:
                botao.verificar_clique(pygame.mouse.get_pos())
                botao.desenhar(tela)
        
        caixa_dialogo.desenhar(tela)
        
        if jogador.vida <= 0 or inimigo.vida <= 0:
            pygame.mixer.music.stop()
            resultado = "derrota" if jogador.vida <= 0 else "vitoria"
            tela.blit(recursos["fundo"], (0, 0))
            texto_fim = fonte.render(
                "Você foi derrotado!" if resultado == "derrota" else "Você venceu!",
                True, VERMELHO if resultado == "derrota" else VERDE
            )
            tela.blit(texto_fim, (LARGURA//2 - texto_fim.get_width()//2, ALTURA//2))
            
            texto_novamente = fonte.render("Deseja jogar novamente? (S/N)", True, BRANCO)
            tela.blit(texto_novamente, (LARGURA//2 - texto_novamente.get_width()//2, ALTURA//2 + 50))
            pygame.display.flip()
            
            while True:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        pygame.quit()
                        return "sair"
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_s:
                            return "reiniciar"
                        elif evento.key == pygame.K_n:
                            return "sair"
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.mixer.music.stop()
                pygame.quit()
                return "sair"
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if not esperando_input and caixa_dialogo.botao_proximo.verificar_clique(pos):
                    if caixa_dialogo.proxima_mensagem():
                        esperando_input = True
                        turno_jogador = not turno_jogador
                        
                        if turno_jogador:
                            rodada += 1
                            if inimigo.status["sangramento"] > 0:
                                jogador.chance_critico_atual = min(0.35, jogador.chance_critico_atual + 0.05)
                                caixa_dialogo.adicionar_mensagem(
                                    f"Turno de {jogador.nome}! Buff de sangramento: Chance crítica aumentada para {int(jogador.chance_critico_atual * 100)}%.",
                                    turno_jogador=True
                                )
                            else:
                                caixa_dialogo.adicionar_mensagem(
                                    f"Turno de {jogador.nome}! Escolha sua ação.",
                                    turno_jogador=True
                                )
                        else:
                            mensagem = ""
                            if inimigo.status["atordoado"] > 0:
                                mensagem = f"{inimigo.nome} está atordoado e perdeu o turno!"
                                inimigo.status["atordoado"] -= 1
                            else:
                                vida_baixa = inimigo.vida < inimigo.vida_max * 0.3
                                jogador_com_status = jogador.status["veneno"] > 0 or jogador.status["sangramento"] > 0
                                
                                if not inimigo.defesa_ativa and vida_baixa and random.random() < 0.6:
                                    inimigo.defesa_ativa = True
                                    mensagem = f"{inimigo.nome} está defendendo!"
                                    if sons["defend"]:
                                        sons["defend"].play()
                                else:
                                    ataques_disponiveis = list(inimigo.ataques.items())
                                    if not jogador_com_status and random.random() < 0.7:
                                        ataques_com_efeito = [atq for atq in ataques_disponiveis if atq[1][1]]
                                        if ataques_com_efeito:
                                            nome_ataque, (dano, efeito, som) = random.choice(ataques_com_efeito)
                                        else:
                                            nome_ataque, (dano, efeito, som) = random.choice(ataques_disponiveis)
                                    else:
                                        nome_ataque, (dano, efeito, som) = max(ataques_disponiveis, key=lambda x: x[1][0])
                                    
                                    critico = random.random() < inimigo.chance_critico_atual
                                    dano_final = max(1, dano - (jogador.defesa // 2))
                                    if critico:
                                        dano_final = int(dano_final * 1.5)
                                        mensagem += "CRÍTICO! "
                                    if jogador.defesa_ativa:
                                        dano_final = dano_final // 2
                                    jogador.vida -= dano_final
                                    mensagem += f"{inimigo.nome} usou {nome_ataque}! (-{dano_final} HP)"
                                    if efeito:
                                        mensagem += "\n" + aplicar_efeito(jogador, efeito)
                                    if inimigo.status["veneno"] > 0 and random.random() < 0.5:
                                        dano_veneno = 5
                                        inimigo.vida -= dano_veneno
                                        mensagem += f"\n{inimigo.nome} sofreu {dano_veneno} de dano por atacar envenenado!"
                                    inimigo.animacao_ataque = True
                                    if som:
                                        som.play()
                            
                            caixa_dialogo.adicionar_mensagem(mensagem)
                            esperando_input = False
                            jogador.defesa_ativa = False
                            status_msg_jogador = processar_status(jogador)
                            status_msg_inimigo = processar_status(inimigo)
                            if status_msg_jogador or status_msg_inimigo:
                                mensagem += "\n" + "\n".join(status_msg_jogador + status_msg_inimigo)
                                caixa_dialogo.adicionar_mensagem(mensagem)
                
                elif turno_jogador and esperando_input and not jogador.animacao_ataque:
                    for i, botao in enumerate(botoes):
                        if botao.verificar_clique(pos):
                            if jogador.status["atordoado"] > 0:
                                mensagem = f"{jogador.nome} está atordoado e perdeu o turno!"
                                jogador.status["atordoado"] -= 1
                            else:
                                mensagem = ""
                                if i == 2:
                                    jogador.defesa_ativa = True
                                    mensagem = f"{jogador.nome} usou {botoes[i].texto}!"
                                    if sons["defend"]:
                                        sons["defend"].play()
                                else:
                                    nome_ataque = list(jogador.ataques.keys())[i]
                                    dano, efeito, som = jogador.ataques[nome_ataque]
                                    critico = random.random() < jogador.chance_critico_atual
                                    dano_final = max(1, dano - (inimigo.defesa // 2))
                                    if critico:
                                        dano_final = int(dano_final * 1.5)
                                        mensagem += "CRÍTICO! "
                                    if inimigo.defesa_ativa:
                                        dano_final = dano_final // 2
                                    inimigo.vida -= dano_final
                                    mensagem += f"{jogador.nome} usou {botoes[i].texto}! (-{dano_final} HP)"
                                    if efeito:
                                        mensagem += "\n" + aplicar_efeito(inimigo, efeito)
                                    if jogador.status["veneno"] > 0 and random.random() < 0.5:
                                        dano_veneno = 5
                                        jogador.vida -= dano_veneno
                                        mensagem += f"\n{jogador.nome} sofreu {dano_veneno} de dano por atacar envenenado!"
                                    jogador.animacao_ataque = True
                                    if som:
                                        som.play()
                            
                            caixa_dialogo.adicionar_mensagem(mensagem)
                            esperando_input = False
                            inimigo.defesa_ativa = False
                            status_msg_jogador = processar_status(jogador)
                            status_msg_inimigo = processar_status(inimigo)
                            if status_msg_jogador or status_msg_inimigo:
                                mensagem += "\n" + "\n".join(status_msg_jogador + status_msg_inimigo)
                                caixa_dialogo.adicionar_mensagem(mensagem)
        
        pygame.display.flip()
        clock.tick(60)

def criar_dinossauros():
    altura_base = ALTURA - 150
    
    velociraptor = Dinossauro(
        nome="Velociraptor", 
        sprite=recursos["velociraptor"], 
        x=120, 
        y=altura_base - recursos["velociraptor"].get_height() + 20,
        tipo="Carnívoro", 
        vida=80, 
        ataque=22,
        defesa=6,
        ataques={
            "arranhão": [14, "sangramento", sons["velociraptor_attack1"]],  # Ataque 1 ajustado
            "mordida": [22, None, sons["velociraptor_attack2"]]             # Ataque 2 ajustado
        },
        chance_critico=0.25,
        cor_contorno=VERDE
    )

    dilofossauro = Dinossauro(
        nome="Dilofossauro", 
        sprite=recursos["dilofossauro"], 
        x=120, 
        y=altura_base - recursos["dilofossauro"].get_height() + 20,
        tipo="Venenoso", 
        vida=70, 
        ataque=20,
        defesa=8,
        ataques={
            "mordida": [17, "sangramento", sons["dilofossauro_attack1"]],      # Ataque 1 ajustado
            "veneno_da_morte": [11, "veneno", sons["dilofossauro_attack2"]]     # Ataque 2 ajustado
        },
        chance_critico=0.15,
        cor_contorno=AZUL
    )

    t_rex = Dinossauro(
        nome="T-Rex", 
        sprite=recursos["t_rex"], 
        x=530, 
        y=altura_base - recursos["t_rex"].get_height() - 20,
        tipo="Carnívoro", 
        vida=100, 
        ataque=15,
        defesa=12,
        ataques={
            "t_rex_attack1": [12, "sangramento", sons["t_rex_attack1"]],
            "t_rex_attack2": [18, "atordoar", sons["t_rex_attack2"]]
        },
        chance_critico=0.20,
        cor_contorno=VERMELHO
    )

    return velociraptor, dilofossauro, t_rex

def salvar_progresso(dinossauro_escolhido):
    with open("progresso.json", "w") as f:
        json.dump({"dinossauro": dinossauro_escolhido.nome}, f)

def carregar_progresso():
    try:
        with open("progresso.json", "r") as f:
            data = json.load(f)
            return data["dinossauro"]
    except:
        return None

def main():
    while True:
        acao = tela_inicio()
        
        if acao == "sair":
            break
        elif acao == "jogar":
            jogador = tela_selecao()
            if not jogador:
                break
            salvar_progresso(jogador)
            ultimo_dino = carregar_progresso()
            print(f"Último dinossauro escolhido: {ultimo_dino}")
            dificuldade = mostrar_opcoes() or "Normal"
            _, _, inimigo = criar_dinossauros()
            resultado = batalha(jogador, inimigo, dificuldade)
            if resultado == "sair":
                break
            elif resultado == "reiniciar":
                continue
    
    pygame.quit()

if __name__ == "__main__":
    main()