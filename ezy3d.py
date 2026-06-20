# ================================================================
#  MACOS FIX: Panda3D shaders uitschakelen + compat mode
# ================================================================
import platform
from panda3d.core import AntialiasAttrib


# Ursina imports
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

window.fullscreen = False
window.title = "BlockGame"


from threedeeinput import DoomInput3D


# ================================================================
#  CUSTOM CROUCHING FIRST PERSON CONTROLLER
# ================================================================
class CrouchFirstPersonController(FirstPersonController):
    def __init__(self, crouch_height=1, crouch_speed_factor=0.4, **kwargs):
        super().__init__(**kwargs)
        self.crouch_height = crouch_height
        self.crouch_speed_factor = crouch_speed_factor
        self.stand_height = self.height
        self.walk_speed = self.speed
        self.crouching = False

    def update(self):
        # SHIFT = crouch
        if held_keys['shift']:
            if not self.crouching:
                self.crouching = True
                self.height = self.crouch_height
                self.camera_pivot.y = self.height
                self.speed = self.walk_speed * self.crouch_speed_factor
        else:
            if self.crouching:
                self.crouching = False
                self.height = self.stand_height
                self.camera_pivot.y = self.height
                self.speed = self.walk_speed

        super().update()


# ================================================================
#  BLOCK ENTITY
# ================================================================
class Block(Entity):
    def __init__(self, position=(0,0,0), scale=1, texture='white_cube', color=color.gray):
        super().__init__(
            model='cube',
            texture=texture,
            color=color,
            position=position,
            scale=scale,
            collider='box'
        )


# ================================================================
#  MAIN WORLD CLASS
# ================================================================
class C00lWorld:
    BlockClass = Block

    def __init__(self, world_width=50, world_depth=50, block_size=1):

        # Start Ursina engine
        self.app = Ursina()

        # macOS shader fix
        if platform.system() == "Darwin":
            print(">>> macOS detected: disabling shaders")
            render.setShaderOff()
            render.setAntialias(AntialiasAttrib.MNone)

        # World settings
        self.world_width = world_width
        self.world_depth = world_depth
        self.block_size = block_size

        # Player
        self.player = None
        self.player_model = None

        # Blocks
        self.blocks = {}
        self.block_textures = ['white_cube', 'brick', 'shore', 'grass', 'noise']
        self.block_texture_index = 0
        self.block_texture = self.block_textures[0]

        # Debug
        self.debug_text = None

        # Third person
        self.third_person = False
        self.third_person_distance = 4
        self.third_person_height = 1.4

        # Update loop
        self.update_helper = Entity(parent=scene, visible=False)
        self.update_helper.update = self._custom_update

        # Input routing
        window.input = self.input


    # ================================================================
    #  WORLD SETUP
    # ================================================================
    def test_plane(self):

        # Ground
        Entity(
            model='plane',
            scale=(self.world_width, 1, self.world_depth),
            texture='white_cube',
            color=color.green,
            texture_scale=(self.world_width, self.world_depth),
            collider='box',
            y=0
        )

        # Player
        self.player = CrouchFirstPersonController(
            height=1,
            crouch_height=0.6,
            crouch_speed_factor=0.4,
            y=2,
            origin_y=-.5,
            speed=7,
            mouse_sensitivity=Vec2(0, 0),   # UIT! DoomInput3D doet dit nu
            jump_height=1,
            jump_up_duration=0.2,
            fall_after=0.2,
            gravity=1
        )

        # DOOM-style input controller
        self.input3d = DoomInput3D(self, self.player)

        # Player model (visible in 3rd person)
        self.player_model = Entity(
            parent=scene,
            model='cube',
            color=color.azure,
            scale=Vec3(1, 1, 1),
            position=self.player.position + Vec3(0, 0.5, 0),
            collider=None,
            enabled=False
        )

        Sky(color=color.cyan)

        # Debug text
        self.debug_text = Text(
            text='',
            origin=(-.5,.5),
            y=.45,
            x=-0.6,
            scale=1.5,
            background=True
        )
        self.debug_text.enabled = False


    # ================================================================
    #  UPDATE LOOP
    # ================================================================
    def _custom_update(self):

        # DOOM-style camera input
        self.input3d.update()

        # Sync player model to player (for third person)
        if self.player and self.player_model:
            self.player_model.position = self.player.position + Vec3(0, 0.5, 0)
            self.player_model.rotation_y = self.player.rotation_y

        # Third-person camera follow
        if self.third_person and self.player:
            camera.parent = scene
            target_position = (
                self.player.world_position
                - self.player.forward * self.third_person_distance
                + Vec3(0, self.third_person_height, 0)
            )
            camera.position = lerp(camera.position, target_position, min(1, 6 * time.dt))
            camera.look_at(self.player.world_position + Vec3(0, self.third_person_height, 0))

        # First-person camera
        elif self.player:
            camera.parent = self.player
            camera.position = Vec3(0, self.player.height, 0)

        # Debug text
        if self.debug_text.enabled:
            self.debug_text.text = f"XYZ: {self.player.x:.1f} {self.player.y:.1f} {self.player.z:.1f}"


    # ================================================================
    #  INPUT HANDLING
    # ================================================================
    def input(self, key):

        # DOOM-style LMB/RMB
        self.input3d.input(key)

        # Debug toggle
        if key == 'f3':
            self.debug_text.enabled = not self.debug_text.enabled

        # Third-person toggle
        if key == 'f7':
            self.third_person = not self.third_person
            self.player_model.enabled = self.third_person

        # Cycle block textures
        if key == 'f4':
            self.block_texture_index = (self.block_texture_index + 1) % len(self.block_textures)
            self.block_texture = self.block_textures[self.block_texture_index]
            print(f"Texture: {self.block_texture}")


    # ================================================================
    #  START GAME LOOP
    # ================================================================
    def start(self):
        self.app.run()
