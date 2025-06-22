import pygame
import math

# Inicializar Pygame
pygame.init()

# Dimensiones de la pantalla
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Stickman Rope Adventure"
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(SCREEN_TITLE)

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)

# Control de FPS
clock = pygame.time.Clock()
FPS = 60

# Clase del Jugador (Stickman)
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.color = BLACK
        # Dibujo simple del stickman: un rectángulo para el cuerpo y un círculo para la cabeza
        # Cuerpo
        self.body_width = 20
        self.body_height = 40
        # Cabeza
        self.head_radius = 10

        # Crear una superficie para el stickman
        # La altura total es la cabeza + cuerpo + un pequeño espacio si es necesario
        self.image = pygame.Surface([self.body_width, self.body_height + self.head_radius * 2], pygame.SRCALPHA)
        # No rellenar con color aquí, lo haremos al dibujar las partes

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Dibujar las partes del stickman en su superficie `self.image`
        # Cabeza (círculo) - se dibuja relativa a la superficie self.image
        pygame.draw.circle(self.image, self.color, (self.body_width // 2, self.head_radius), self.head_radius)
        # Cuerpo (rectángulo) - se dibuja debajo de la cabeza
        pygame.draw.rect(self.image, self.color, (0, self.head_radius * 2 -1 , self.body_width, self.body_height)) # -1 para solapar un poco

        self.change_x = 0
        self.change_y = 0
        self.is_jumping = False
        self.gravity = 0.8
        self.jump_strength = -15

        # Atributos de la cuerda
        self.is_rope_swinging = False
        self.rope_anchor_pos = None
        self.rope_length = 0
        self.rope_max_length = 300  # Longitud máxima de la cuerda
        self.rope_color = (50, 50, 50) # Gris oscuro para la cuerda

        # Variables para la física del péndulo (simplificado)
        self.angle = 0
        self.angular_velocity = 0
        self.angular_acceleration = 0

        # Para un dibujo más detallado del stickman (opcional por ahora)
        # self.limbs = []

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        # Dibujar la cuerda si está activa
        if self.is_rope_swinging and self.rope_anchor_pos:
            # Punto de origen de la cuerda en el jugador (ej. centro superior del cuerpo)
            player_rope_attach_x = self.rect.centerx
            player_rope_attach_y = self.rect.top + self.head_radius
            pygame.draw.line(surface, self.rope_color, self.rope_anchor_pos, (player_rope_attach_x, player_rope_attach_y), 2)

    def update(self):
        if self.is_rope_swinging and self.rope_anchor_pos:
            # Lógica de balanceo (Péndulo)
            # Vector del ancla al jugador
            dx = self.rect.centerx - self.rope_anchor_pos[0]
            dy = self.rect.centery - self.rope_anchor_pos[1] # Usar centery para el cálculo físico

            current_distance_to_anchor = math.sqrt(dx**2 + dy**2)

            # Ángulo actual del jugador con respecto al ancla (vertical hacia abajo es 0)
            self.angle = math.atan2(dx, dy) # atan2(x,y) para ángulo correcto con vertical

            # Aceleración angular (simplificación de g * sin(theta) / L)
            # Usamos una constante para la "fuerza" del swing
            self.angular_acceleration = -0.01 * math.sin(self.angle) # Ajustar este valor para la "fuerza"

            self.angular_velocity += self.angular_acceleration
            self.angular_velocity *= 0.99 # Amortiguación angular (damping)

            # Convertir velocidad angular a velocidad lineal
            self.change_x = self.angular_velocity * self.rope_length * math.cos(self.angle)
            self.change_y = -self.angular_velocity * self.rope_length * math.sin(self.angle) # Negativo por la dirección del ángulo

            # Aplicar movimiento
            self.rect.x += self.change_x
            self.rect.y += self.change_y

            # Corregir la distancia para mantener la longitud de la cuerda
            # Después de mover, si la distancia no es la correcta, ajustarla.
            final_dx = self.rect.centerx - self.rope_anchor_pos[0]
            final_dy = self.rect.centery - self.rope_anchor_pos[1]
            final_dist = math.sqrt(final_dx**2 + final_dy**2)

            if final_dist > 0: # Evitar división por cero
                correction_factor = self.rope_length / final_dist
                self.rect.centerx = self.rope_anchor_pos[0] + final_dx * correction_factor
                self.rect.centery = self.rope_anchor_pos[1] + final_dy * correction_factor

        else: # Movimiento normal (no balanceándose)
            original_change_x = self.change_x # Guardar por si se necesita para el input

            # Aplicar gravedad si no está en el suelo o si recién soltó la cuerda y va hacia arriba
            # La condición de suelo se manejará con colisiones de plataforma
            if self.is_jumping or self.change_y < 0 or not self.on_ground(platform_sprites):
                 self.change_y += self.gravity

            # Mover horizontalmente
            self.rect.x += self.change_x
            # Comprobar colisiones horizontales
            hit_list_x = pygame.sprite.spritecollide(self, platform_sprites, False)
            for platform_hit in hit_list_x:
                if self.change_x > 0: # Moviéndose a la derecha
                    self.rect.right = platform_hit.rect.left
                elif self.change_x < 0: # Moviéndose a la izquierda
                    self.rect.left = platform_hit.rect.right
                # Detener movimiento horizontal si hay colisión
                if self.is_rope_swinging:
                    self.angular_velocity *= -0.7 # Rebote si se está balanceando
                    # No necesariamente queremos detener change_x aquí si el rebote de angular_velocity ya lo maneja
                else:
                    self.change_x = 0 # Detener movimiento horizontal normal si no se balancea


            # Mover verticalmente
            self.rect.y += self.change_y
            # Comprobar colisiones verticales
            hit_list_y = pygame.sprite.spritecollide(self, platform_sprites, False)
            self.is_jumping = True # Asumir que está saltando/cayendo hasta que se demuestre lo contrario
            for platform_hit in hit_list_y:
                if self.change_y > 0: # Moviéndose hacia abajo (aterrizando)
                    self.rect.bottom = platform_hit.rect.top
                    self.change_y = 0
                    self.is_jumping = False # Aterrizó
                elif self.change_y < 0: # Moviéndose hacia arriba (golpeando cabeza)
                    self.rect.top = platform_hit.rect.bottom
                    self.change_y = 0
                # Si está balanceándose y golpea una plataforma verticalmente, podría necesitar lógica adicional
                # por ahora, simplemente detiene el movimiento vertical.
                if self.is_rope_swinging :
                    # Si golpea desde abajo mientras se balancea, podría necesitar soltar la cuerda o ajustar la física.
                    # Por ahora, simplemente detenemos la velocidad vertical del balanceo.
                    # Esto es una simplificación.
                    pass # La corrección de longitud de cuerda ya maneja parte de esto.
                         # La velocidad angular se verá afectada naturalmente.

            # Si después de todas las colisiones verticales sigue "saltando" y no hay suelo debajo,
            # asegurarse de que is_jumping siga True.
            # La comprobación de on_ground al principio de la sección de gravedad lo maneja.


        # Mantener al jugador dentro de la pantalla (horizontalmente)
        # Las colisiones con plataformas deben manejar esto dentro del nivel,
        # pero los bordes de la pantalla son el límite final.
        if self.rect.left < 0:
            self.rect.left = 0
            if self.is_rope_swinging: self.angular_velocity *= -0.7
            # change_x ya debería ser 0 por colisión con plataforma si la hubiera, o por la propia pared
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            if self.is_rope_swinging: self.angular_velocity *= -0.7

    def on_ground(self, platforms):
        # Comprobar si el jugador está parado sobre una plataforma
        # Mover temporalmente al jugador hacia abajo 1 pixel para la comprobación
        self.rect.y += 1
        hit_list = pygame.sprite.spritecollide(self, platforms, False)
        self.rect.y -= 1 # Devolver al jugador a su posición original
        return len(hit_list) > 0

    def go_left(self):
        if not self.is_rope_swinging:
            self.change_x = -5

    def go_right(self):
        if not self.is_rope_swinging:
            self.change_x = 5

    def stop_x(self):
        # Solo detener el movimiento inducido por el jugador, no el del balanceo
        if not self.is_rope_swinging:
            # Si el jugador está presionando una tecla de movimiento, change_x será seteado de nuevo.
            # Esto es para detener el deslizamiento si no hay input.
            # Necesitamos una forma de saber si el jugador está activamente presionando una tecla.
            # Por ahora, simplemente lo ponemos a 0 si no se está balanceando.
            # Esto se maneja mejor en el bucle de eventos.
            pass # El control de stop se maneja mejor en el bucle de eventos KEYDOWN/KEYUP


    def jump(self):
        # Solo puede saltar si está en el "suelo" (detectado por colisión) y no se está balanceando
        if self.on_ground(platform_sprites) and not self.is_rope_swinging:
            self.is_jumping = True
            self.change_y = self.jump_strength

    def attach_rope(self, pos):
        if not self.is_rope_swinging: # Solo anclar si no está ya anclado
            self.is_rope_swinging = True
            self.rope_anchor_pos = pos

            player_attach_point_x = self.rect.centerx
            player_attach_point_y = self.rect.centery

            dx = player_attach_point_x - self.rope_anchor_pos[0]
            dy = player_attach_point_y - self.rope_anchor_pos[1]
            current_distance = math.sqrt(dx**2 + dy**2)

            self.rope_length = min(current_distance, self.rope_max_length)
            if self.rope_length < 20: # Longitud mínima de la cuerda
                self.rope_length = 20

            # Inicializar ángulo y velocidad angular para el nuevo balanceo
            self.angle = math.atan2(dx, dy)
            # Heredar parte de la velocidad actual como velocidad tangencial inicial
            # Proyectar la velocidad actual sobre la dirección tangencial a la cuerda
            current_velocity_magnitude = math.sqrt(self.change_x**2 + self.change_y**2)
            if current_velocity_magnitude > 0:
                 # Vector normal a la cuerda (dirección tangencial)
                tangent_dx = -dy
                tangent_dy = dx
                # Normalizar vector tangencial
                tangent_norm = math.sqrt(tangent_dx**2 + tangent_dy**2)
                if tangent_norm > 0:
                    tangent_dx /= tangent_norm
                    tangent_dy /= tangent_norm
                    # Proyección de la velocidad actual sobre la tangente
                    tangential_speed = self.change_x * tangent_dx + self.change_y * tangent_dy
                    self.angular_velocity = tangential_speed / self.rope_length
                else:
                    self.angular_velocity = 0
            else:
                 self.angular_velocity = 0

            self.angular_acceleration = 0
            self.is_jumping = False # No se puede estar saltando y balanceando al mismo tiempo
            # Detener movimiento horizontal inducido por teclas
            self.change_x = 0


    def detach_rope(self):
        if self.is_rope_swinging:
            self.is_rope_swinging = False
            self.rope_anchor_pos = None
            # La velocidad lineal (change_x, change_y) ya debería estar actualizada por el último frame del swing
            # así que el jugador será "lanzado" con esa velocidad.
            # Considerar si está en el aire para la gravedad
            if not self.on_ground(platform_sprites): # Usar on_ground para consistencia
                self.is_jumping = True # Para que la gravedad actúe correctamente después de soltar

# Clase para las Plataformas
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=BLACK):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Crear instancia del jugador
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60) # Ajustar Y si es necesario con plataformas

# Grupos de Sprites
all_sprites = pygame.sprite.Group()
platform_sprites = pygame.sprite.Group()

all_sprites.add(player)

# Crear algunas plataformas de ejemplo
platforms_data = [
    (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, (50,150,50)), # Suelo principal
    (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 150, 200, 20, (0,100,0)),
    (100, SCREEN_HEIGHT - 250, 150, 20, (0,100,0)),
    (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 350, 150, 20, (0,100,0)),
    (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 450, 100, 20, (0,100,0)) # Plataforma alta
]

for p_data in platforms_data:
    platform = Platform(*p_data)
    all_sprites.add(platform)
    platform_sprites.add(platform)


# Bucle principal del juego
running = True
while running:
    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Eventos de Teclado
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                player.go_left()
            elif event.key == pygame.K_RIGHT:
                player.go_right()
            elif event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                player.jump()

        if event.type == pygame.KEYUP:
            # Detener movimiento si se suelta la tecla y no se está presionando la opuesta
            if event.key == pygame.K_LEFT and player.change_x < 0:
                keys = pygame.key.get_pressed()
                if not keys[pygame.K_RIGHT]: # Solo detener si la otra no está presionada
                    player.change_x = 0 # Usar change_x directamente aquí para detener
            elif event.key == pygame.K_RIGHT and player.change_x > 0:
                keys = pygame.key.get_pressed()
                if not keys[pygame.K_LEFT]:
                     player.change_x = 0

        # Eventos de Ratón para la cuerda
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Botón izquierdo del ratón
                if player.is_rope_swinging:
                    player.detach_rope()
                else:
                    player.attach_rope(event.pos) # event.pos es la posición del clic

    # Lógica de actualización del juego
    # Actualizar estado de las teclas para movimiento continuo si no se está balanceando
    if not player.is_rope_swinging:
        keys = pygame.key.get_pressed()
        # Mantenemos el change_x actual a menos que una tecla lo cambie
        # Esto permite que el jugador se deslice si no hay fricción o si se detiene explícitamente
        # Para un control más directo, reseteamos change_x y luego lo seteamos si hay input
        player.change_x = 0 # Comentar esto para tener deslizamiento
        if keys[pygame.K_LEFT]:
            player.go_left() # Llama al método que setea change_x
        if keys[pygame.K_RIGHT]:
            player.go_right() # Llama al método que setea change_x


    all_sprites.update() # Actualiza al jugador y cualquier otra cosa en all_sprites

    # Renderizado
    screen.fill(LIGHT_BLUE)  # Color de fondo
    all_sprites.draw(screen) # Dibuja todos los sprites (jugador y plataformas)

    # Actualizar la pantalla
    pygame.display.flip()

    # Controlar FPS
    clock.tick(FPS)

# Salir de Pygame
pygame.quit()
