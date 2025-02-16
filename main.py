#############################################
#           main.py - Complete Script       #
#############################################

import os, json, time, random
from math import floor, sin, cos, pi, radians, exp
from collections import deque

# Try to import ijson for streaming JSON parsing; if unavailable, warn.
try:
    import ijson
except ImportError:
    print("[WARNING] ijson not installed. Streaming mode will use full JSON load.")
    ijson = None

# Import from Ursina and Panda3D:
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.editor_camera import EditorCamera
from ursina import InputField  # Use InputField directly from ursina.
from panda3d.core import Shader as PandaShader

# Import perlin noise functions.
from noise import pnoise2, pnoise3

#############################################
# Directional Helper Function (Compass)
#############################################
def get_cardinal(angle):
    angle = angle % 360
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = int((angle + 22.5) // 45) % 8
    return directions[index]

#############################################
# 1) Initialize Ursina Application
#############################################
app = Ursina()
camera.clear_color = color.rgb(135,206,235)
mouse.locked = False
mouse.visible = True

# Global flag for inventory UI open state.
inventory_open = False

# Command input variables.
command_mode = False
command_input_field = None

#############################################
# 2) Utility: Safe Texture Loader
#############################################
def safe_load_texture(path):
    try:
        return load_texture(path, filtering=None)
    except Exception as e:
        print(f"[TEXTURE ERROR] Could not load texture '{path}': {e}")
        return None

# Load textures.
dirt_texture          = safe_load_texture('assets/dirt.png')
grass_texture         = safe_load_texture('assets/grass.png')
stone_texture         = safe_load_texture('assets/stone.png')
water_texture         = safe_load_texture('assets/water.png')
sponge_texture        = safe_load_texture('assets/sponge.png')
crackedtile_texture   = safe_load_texture('assets/crackedtile.png')
darkshingle_texture   = safe_load_texture('assets/darkshingle.png')
darkwood_texture      = safe_load_texture('assets/darkwood.png')
lightwood_texture     = safe_load_texture('assets/lightwood.png')
treetrunkdark_texture = safe_load_texture('assets/treetrunkdark.png')
treetrunklight_texture= safe_load_texture('assets/treetrunklight.png')
treeleaves_texture    = safe_load_texture('assets/treeleaves.png')
# Additional block textures.
crackedglyphs_texture     = safe_load_texture('assets/crackedglyphs.png')
emerald_texture           = safe_load_texture('assets/emerald.png')
gold_texture              = safe_load_texture('assets/gold.png')
redbrick_texture          = safe_load_texture('assets/redbrick.png')
redcement_texture         = safe_load_texture('assets/redcement.png')
ruby_texture              = safe_load_texture('assets/ruby.png')
sand_texture              = safe_load_texture('assets/sand.png')
seashells_texture         = safe_load_texture('assets/seashells.png')
steel_texture             = safe_load_texture('assets/steel.png')
stripedwatercolor_texture = safe_load_texture('assets/stripedwatercolor.png')
yellowwool_texture        = safe_load_texture('assets/yellowwool.png')
blackfiligree_texture     = safe_load_texture('assets/blackfiligree.png')
bluewool_texture          = safe_load_texture('assets/bluewool.png')
greenwool_texture         = safe_load_texture('assets/greenwool.png')
purplewool_texture        = safe_load_texture('assets/purplewool.png')
redwool_texture           = safe_load_texture('assets/redwool.png')

print(f"[DEBUG] Water texture loaded: {water_texture is not None}")

#############################################
# Global Texture Mapping Dictionary
#############################################
texture_mapping = {
    'dirt': dirt_texture,
    'grass': grass_texture,
    'stone': stone_texture,
    'water': water_texture,
    'sponge': sponge_texture,
    'crackedtile': crackedtile_texture,
    'darkshingle': darkshingle_texture,
    'darkwood': darkwood_texture,
    'lightwood': lightwood_texture,
    'treetrunkdark': treetrunkdark_texture,
    'treetrunklight': treetrunklight_texture,
    'treeleaves': treeleaves_texture,
    'crackedglyphs': crackedglyphs_texture,
    'emerald': emerald_texture,
    'gold': gold_texture,
    'redbrick': redbrick_texture,
    'redcement': redcement_texture,
    'ruby': ruby_texture,
    'sand': sand_texture,
    'seashells': seashells_texture,
    'steel': steel_texture,
    'stripedwatercolor': stripedwatercolor_texture,
    'yellowwool': yellowwool_texture,
    'blackfiligree': blackfiligree_texture,
    'bluewool': bluewool_texture,
    'greenwool': greenwool_texture,
    'purplewool': purplewool_texture,
    'redwool': redwool_texture,
    'door': None,
    'pokeball': None,
    'foxfox': None,
    'particleblock': purplewool_texture
}

# Define collectible blocks for drop/pickup logic.
collectible_blocks = ['dirt','grass','stone','sponge','crackedtile','darkshingle','darkwood',
                      'lightwood','treetrunkdark','treetrunklight','treeleaves','crackedglyphs',
                      'emerald','gold','redbrick','redcement','ruby','sand','seashells','steel',
                      'stripedwatercolor','yellowwool','blackfiligree','bluewool','greenwool',
                      'purplewool','redwool']

#############################################
# 3) Custom Shaders
#############################################
daynight_vertex_code = '''
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;
void main(){
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0;
}
'''

daynight_fragment_code = '''
#version 140
uniform sampler2D p3d_Texture0;
uniform float time_of_day;
in vec2 uv;
out vec4 fragColor;
vec3 sky_gradient(float t) {
    vec3 night = vec3(0.02,0.03,0.1);
    vec3 dawn = vec3(0.5,0.3,0.1);
    vec3 day = vec3(0.4,0.6,1.0);
    vec3 sunset = vec3(1.0,0.4,0.1);
    float sun_height = sin(time_of_day);
    if(sun_height < -0.2) return night;
    if(sun_height < 0.0) return mix(night, dawn, smoothstep(-0.2,0.0,sun_height));
    if(sun_height < 0.2) return mix(dawn, day, smoothstep(0.0,0.2,sun_height));
    if(sun_height < 0.5) return day;
    return mix(day, sunset, smoothstep(0.5,1.0,sun_height));
}
void main(){
    vec3 color = sky_gradient(time_of_day);
    if(sin(time_of_day) < -0.3){
        float star = step(0.999, fract(sin(dot(uv,vec2(12.9898,78.233))) * 43758.5453));
        color += star * smoothstep(-0.5,-0.3,sin(time_of_day));
    }
    fragColor = vec4(color,1.0);
}
'''

daynight_shader = Shader(vertex=daynight_vertex_code, fragment=daynight_fragment_code)

block_lighting_vertex_code = '''
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;
void main(){
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0;
}
'''

block_lighting_fragment_code = '''
#version 140
uniform sampler2D p3d_Texture0;
uniform float time_of_day;
in vec2 uv;
out vec4 fragColor;
void main(){
    vec4 texColor = texture(p3d_Texture0, uv);
    float light = 0.6 + 0.4 * max(sin(time_of_day), 0.0);
    fragColor = vec4(texColor.rgb * light, texColor.a);
}
'''

block_lighting_shader = Shader(vertex=block_lighting_vertex_code, fragment=block_lighting_fragment_code)

#############################################
# 4) Water System
#############################################
# The water entity uses its texture and transparency settings.

#############################################
# 5) Special Block Type Constants
#############################################
DOOR     = 'door'
POKEBALL = 'pokeball'
FOXFOX   = 'foxfox'
PARTICLE_BLOCK = 'particleblock'

BLOCK_TYPES = [
    'dirt','grass','stone','water','sponge',
    'crackedtile','darkshingle','darkwood','lightwood',
    'treetrunkdark','treetrunklight','treeleaves',
    'crackedglyphs','emerald','gold','redbrick','redcement','ruby',
    'sand','seashells','steel','stripedwatercolor','yellowwool',
    'blackfiligree','bluewool','greenwool','purplewool','redwool',
    DOOR, POKEBALL, FOXFOX, PARTICLE_BLOCK
]

door_entities = {}
pokeball_entities = {}
foxfox_entities = {}
particleblock_entities = {}

#############################################
# 6a) Audio Definitions
#############################################
dig_sound      = Audio('assets/sounds/digsound.wav', autoplay=False)
water_sound    = Audio('assets/sounds/water.wav', autoplay=False)
sponge_sound   = Audio('assets/sounds/sponge.wav', autoplay=False)
door_sound     = Audio('assets/sounds/doorsound.wav', autoplay=False)
pokeball_sound = Audio('assets/sounds/pokeball.wav', autoplay=False)
foxfox_sound   = Audio('assets/sounds/foxfox.wav', autoplay=False)

try:
    waterjump_sound = Audio('assets/sounds/waterjump.wav', autoplay=False)
except:
    waterjump_sound = None

music_tracks = []
music_on = True
current_music = None
current_track = None
last_track = None
music_start_time = 0
music_length = 0

def pick_next_track():
    if not music_tracks:
        return None
    choices = [t for t in music_tracks if t != last_track]
    return random.choice(choices) if choices else music_tracks[0]

def start_random_music():
    global current_music, current_track, last_track, music_start_time, music_length
    if not music_on or not music_tracks:
        return
    nxt = pick_next_track()
    if not nxt:
        return
    last_track = current_track
    current_track = nxt
    if current_music:
        destroy(current_music)
        current_music = None
    current_music = Audio(nxt, loop=False, autoplay=True)
    music_start_time = time.time()
    try:
        music_length = current_music.length
    except:
        music_length = 180

def update_music():
    global current_music, music_start_time, music_length
    if not music_on:
        if current_music and current_music.playing:
            current_music.pause()
        return
    else:
        if current_music and not current_music.playing:
            current_music.resume()
    if current_music:
        elapsed = time.time() - music_start_time
        if elapsed >= music_length - 0.1:
            start_random_music()
    else:
        start_random_music()

def init_music():
    if not os.path.exists('assets/sounds'):
        return
    for fname in os.listdir('assets/sounds'):
        if fname.lower().endswith('.mp3'):
            music_tracks.append(os.path.join('assets/sounds', fname))
    start_random_music()

def play_sound_once(sound):
    if not sound.playing:
        sound.play()

#############################################
# 6b) Water Physics Constants
#############################################
WATER_LEVEL = 0.0
UNDERWATER_GRAVITY_FACTOR = 0.2
BUOYANCY = 0.5
WATER_DRAG = 0.9
SWIM_FORCE = 2.0

#############################################
# 7) Cube Faces and Normals
#############################################
CUBE_FACES = {
    'up': [(0,1,0), (1,1,0), (1,1,1), (0,1,1)],
    'down': [(0,0,1), (1,0,1), (1,0,0), (0,0,0)],
    'north': [(0,0,0), (1,0,0), (1,1,0), (0,1,0)],
    'south': [(1,0,1), (0,0,1), (0,1,1), (1,1,1)],
    'east': [(1,0,0), (1,0,1), (1,1,1), (1,1,0)],
    'west': [(0,0,1), (0,0,0), (0,1,0), (0,1,1)]
}
FACE_NORMALS = {
    'up': Vec3(0,1,0),
    'down': Vec3(0,-1,0),
    'north': Vec3(0,0,-1),
    'south': Vec3(0,0,1),
    'east': Vec3(1,0,0),
    'west': Vec3(-1,0,0)
}

#############################################
# 8) Special Block Entities
#############################################
class Door(Entity):
    def __init__(self, base_pos):
        super().__init__()
        self.base_pos = Vec3(*base_pos)
        self.open = False
        self.pivot = Entity(position=self.base_pos + Vec3(0.5,0,0.5))
        self.parent = self.pivot
        self.scale = (0.25,2,1)
        self.color = color.rgba(255,0,0,180)
        self.position = Vec3(0,1,0)
        self.collider = BoxCollider(self, center=Vec3(0,0,0), size=Vec3(0.25,2,1))
        self.is_animating = False
        self.closed_rotation = 0
        self.open_rotation = -90
        self.target_rot = 0
    def update(self):
        if self.is_animating:
            step = 150 * time.dt
            diff = self.target_rot - self.pivot.rotation_y
            if abs(diff) < step:
                self.pivot.rotation_y = self.target_rot
                self.is_animating = False
            else:
                self.pivot.rotation_y += step if diff > 0 else -step
    def toggle(self):
        door_sound.play()
        self.is_animating = True
        if self.open:
            self.target_rot = self.closed_rotation
            self.collider = BoxCollider(self, center=Vec3(0,0,0), size=Vec3(0.25,2,1))
            self.open = False
        else:
            self.target_rot = self.open_rotation
            self.collider = None
            self.open = True

class PokeballEntity(Entity):
    def __init__(self, base_pos):
        super().__init__()
        self.base_pos = Vec3(*base_pos)
        self.position = self.base_pos + Vec3(0.5,0,0.5)
        self.model = load_model('pokeball.gltf') or 'cube'
        self.scale = 0.5
        self.collider = BoxCollider(self, center=Vec3(0,0.5,0), size=Vec3(1,1,1))
        self.color = color.white
    def rotate_self(self):
        self.rotation_y += 30

class FoxfoxEntity(Entity):
    def __init__(self, base_pos):
        super().__init__()
        self.base_pos = Vec3(*base_pos)
        self.position = self.base_pos + Vec3(0.5,0,0.5)
        self.model = load_model('foxfox.gltf') or 'cube'
        self.scale = 0.75
        self.collider = BoxCollider(self, center=Vec3(0,0.5,0), size=Vec3(1,1,1))
        self.color = color.white
    def rotate_self(self):
        self.rotation_y += 30

class ParticleBlockEntity(Entity):
    def __init__(self, base_pos):
        super().__init__()
        self.base_pos = Vec3(*base_pos)
        self.position = self.base_pos + Vec3(0.5,0,0.5)
        self.model = 'cube'
        self.scale = 1
        self.collider = BoxCollider(self, center=Vec3(0,0,0), size=Vec3(1,1,1))
        self.settings = {'size': 0.1, 'particle_count': 50, 'start_color': color.red, 'end_color': color.yellow, 'lifetime': 2, 'gravity': 0.1}
        self.shrink_index = 0
    def update(self):
        pass

#############################################
# 9) BFS Water Spread Functions
#############################################
water_spread_queue = []
def process_water_spread():
    now = time.time()
    for ev in water_spread_queue[:]:
        if ev['time_to_spread'] <= now:
            water_spread_queue.remove(ev)
            pos = ev['pos']
            dist = ev['dist']
            direction = ev['direction']
            if not world.get_block(pos):
                world.set_block(pos, 'water')
                if dist > 0:
                    spread_water_slowly(pos, dist, direction)
def schedule_water_spread(pos, dist, direction, delay=0.2):
    water_spread_queue.append({
        'pos': pos,
        'dist': dist,
        'direction': direction,
        'time_to_spread': time.time() + delay
    })
def spread_water_slowly(source_pos, dist, direction):
    if dist <= 0:
        return
    offsets = [
        (0,-1,0),
        (int(direction.x),0,int(direction.z)),
        (1,0,0),
        (-1,0,0),
        (0,0,1),
        (0,0,-1)
    ]
    for off in offsets:
        nx = source_pos[0] + off[0]
        ny = source_pos[1] + off[1]
        nz = source_pos[2] + off[2]
        schedule_water_spread((nx,ny,nz), dist-1, direction, 0.2)
def soak_up_water(center_pos, radius=5):
    visited = set()
    queue = deque()
    queue.append((center_pos, 0))
    offsets = []
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            for dz in [-1,0,1]:
                if dx==0 and dy==0 and dz==0:
                    continue
                offsets.append((dx,dy,dz))
    while queue:
        (x,y,z), dist_traveled = queue.popleft()
        if dist_traveled > radius:
            continue
        if (x,y,z) in visited:
            continue
        visited.add((x,y,z))
        if world.get_block((x,y,z))=='water':
            world.set_block((x,y,z), None)
        for off in offsets:
            nx, ny, nz = x+off[0], y+off[1], z+off[2]
            nd = dist_traveled+1
            if nd <= radius:
                queue.append(((nx,ny,nz), nd))

#############################################
# 10) Bubble Particles
#############################################
class BubbleParticle(Entity):
    def __init__(self, start_pos):
        super().__init__(parent=scene, model='quad', texture='circle',
                         scale=0.1, position=start_pos, billboard=True)
        self.color = color.rgba(0,0,255,150)
        self.lifetime = 1.5
        self.spawn_time = time.time()
        self.y_vel = 0.6
    def update(self):
        dt = time.dt
        self.position += Vec3(0, self.y_vel*dt, 0)
        if time.time()-self.spawn_time > self.lifetime:
            destroy(self)
            return
        ratio = (time.time()-self.spawn_time)/self.lifetime
        self.color = color.rgba(0,0,255,int(150*(1-ratio)))
def spawn_bubbles():
    if not player:
        return
    for _ in range(3):
        pivot = player.camera_pivot.world_position
        offset = player.camera_pivot.forward*1.2 + Vec3(random.uniform(-0.2,0.2),
                                                        random.uniform(-0.2,0.2),
                                                        random.uniform(-0.2,0.2))
        spawn_pos = pivot + offset
        BubbleParticle(spawn_pos)

#############################################
# 11) Debris and Pickup Items
#############################################
class Debris(Entity):
    def __init__(self, block_position, block_type):
        super().__init__(collider='box')
        self.start_time = time.time()
        self.lifetime = 3.0
        pos_vec = Vec3(*block_position)
        self.position = pos_vec + Vec3(random.uniform(-0.05,0.05),
                                       random.uniform(-0.05,0.05),
                                       random.uniform(-0.05,0.05))
        self.model = 'cube'
        self.scale = 0.05
        self.velocity = Vec3(random.uniform(-3,3),
                             random.uniform(3,6),
                             random.uniform(-3,3))
        self.angular_velocity = Vec3(random.uniform(-30,30),
                                     random.uniform(-30,30),
                                     random.uniform(-30,30))
        self.gravity = 9.8
        self.texture = texture_mapping.get(block_type, None)
        self.color = color.white
    def update(self):
        dt = time.dt
        ground_level = floor(self.position.y)
        if self.position.y <= ground_level+0.05 and self.velocity.y < 0:
            self.velocity.y = -self.velocity.y * 0.7
            self.velocity.x *= 0.8
            self.velocity.z *= 0.8
        self.velocity.y -= self.gravity * dt
        self.position += self.velocity * dt
        self.rotation_x += self.angular_velocity.x * dt
        self.rotation_y += self.angular_velocity.y * dt
        self.rotation_z += self.angular_velocity.z * dt
        if time.time()-self.start_time > self.lifetime:
            destroy(self)

# Modified PickupItem: now a small 3D cube with collision and gravity.
class PickupItem(Entity):
    def __init__(self, item_type, position):
        super().__init__(parent=scene, model='cube', texture=texture_mapping.get(item_type),
                         scale=0.3, position=position)
        self.item_type = item_type
        self.velocity = Vec3(0,0,0)
        self.gravity = 9.8
        self.pickup_radius = 1.0
        self.lifetime = 30
        self.spawn_time = time.time()
        self.collider = BoxCollider(self)
    def update(self):
        dt = time.dt
        self.velocity.y -= self.gravity * dt
        self.position += self.velocity * dt
        hit = raycast(origin=self.world_position, direction=Vec3(0,-1,0), distance=0.2, ignore=[self])
        if hit.hit:
            self.velocity.y = 0
        if time.time()-self.spawn_time > self.lifetime:
            destroy(self)
            return
        if player and distance(self.world_position, player.world_position) < self.pickup_radius:
            if add_item_to_inventory(self.item_type):
                destroy(self)

def add_item_to_inventory(item_type):
    global inventory_ui
    for i in range(len(inventory_ui.hotbar_data)):
        slot = inventory_ui.hotbar_data[i]
        if slot and slot.get('item')==item_type and slot.get('count',1)<100:
            inventory_ui.hotbar_data[i]['count'] += 1
            return True
    for i in range(len(inventory_ui.hotbar_data)):
        if inventory_ui.hotbar_data[i] is None:
            inventory_ui.hotbar_data[i] = {'item': item_type, 'count': 1}
            return True
    for i in range(len(inventory_ui.inventory_data)):
        slot = inventory_ui.inventory_data[i]
        if slot and slot.get('item')==item_type and slot.get('count',1)<100:
            inventory_ui.inventory_data[i]['count'] += 1
            return True
    for i in range(len(inventory_ui.inventory_data)):
        if inventory_ui.inventory_data[i] is None:
            inventory_ui.inventory_data[i] = {'item': item_type, 'count': 1}
            return True
    print("Inventory full, cannot pick up", item_type)
    return False

def spawn_pickup(item_type, position):
    PickupItem(item_type, (position[0]+0.5, position[1]+0.5, position[2]+0.5))

#############################################
# Helper Class: SlotOutline
#############################################
class SlotOutline(Entity):
    def __init__(self, parent, thickness=0.01, outline_color=color.lime, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.thickness = thickness
        self.outline_color = outline_color
        self.top = Entity(parent=self, model='quad', color=self.outline_color, scale=(0.11, thickness), position=(0, 0.11/2, 0))
        self.bottom = Entity(parent=self, model='quad', color=self.outline_color, scale=(0.11, thickness), position=(0, -0.11/2, 0))
        self.left_border = Entity(parent=self, model='quad', color=self.outline_color, scale=(thickness, 0.11), position=(-0.11/2, 0, 0))
        self.right_border = Entity(parent=self, model='quad', color=self.outline_color, scale=(thickness, 0.11), position=(0.11/2, 0, 0))

#############################################
# 12) Inventory UI System (Hotbar + Main Inventory)
#############################################
class InventorySlotUI(Button):
    def __init__(self, slot_data, **kwargs):
        super().__init__(model='quad', **kwargs)
        self.slot_data = slot_data
        self.scale = (0.11, 0.11)
        self.background_color = color.rgba(0,0,0,150)
        self.texture_scale = (1,1)
        self.count_text = None
        self.update_visual()

    def update_visual(self):
        if self.slot_data and self.slot_data.get('item'):
            self.texture = texture_mapping.get(self.slot_data['item'])
            self.color = color.white
            count = self.slot_data.get('count', 1)
            if self.count_text:
                destroy(self.count_text)
            self.count_text = Text(
                text=str(count),
                parent=self,
                origin=(0.4, 0.4),
                scale=1,
                color=color.yellow,
                position=(0.04, 0.04),
                z=-1
            )
        else:
            self.texture = None
            self.color = color.rgba(0,0,0,150)
            if self.count_text:
                destroy(self.count_text)
                self.count_text = None
        self.border_color = color.white

class InventoryUI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.hotbar_data = [None for _ in range(9)]
        self.hotbar_elements = []
        for i in range(9):
            pos_x = -0.5 + i*0.12
            slot = InventorySlotUI(self.hotbar_data[i], parent=self, position=(pos_x, -0.45))
            self.hotbar_elements.append(slot)
        self.hotbar_selected = 0
        self.hotbar_highlight = SlotOutline(parent=self, position=self.hotbar_elements[0].position)
        self.inventory_data = [None for _ in range(27)]
        self.inventory_panel = Panel(parent=camera.ui, scale=(0.65,0.65),
                                      color=color.rgba(0,0,0,0), enabled=False)
        self.inventory_elements = []
        cell_size = 0.12
        grid_cols = 9
        grid_rows = 3
        start_x = -0.5
        start_y = 0.3
        for i in range(27):
            row = i // grid_cols
            col = i % grid_cols
            pos_x = start_x + col * cell_size
            pos_y = start_y - row * cell_size
            slot = InventorySlotUI(self.inventory_data[i], parent=self.inventory_panel, position=(pos_x, pos_y))
            self.inventory_elements.append(slot)
        self.dragged_item = None
        self.dragged_slot = None
        self.inventory_open = False

    def toggle_inventory(self):
        self.inventory_open = not self.inventory_open
        self.inventory_panel.enabled = self.inventory_open
        if self.inventory_open:
            player.disable()
            mouse.locked = False
            mouse.visible = True
        else:
            player.enable()
            mouse.locked = True
            mouse.visible = False

    def update_hotbar(self):
        for i, slot in enumerate(self.hotbar_elements):
            slot.slot_data = self.hotbar_data[i]
            slot.update_visual()
        self.hotbar_highlight.position = self.hotbar_elements[self.hotbar_selected].position

    def update_inventory(self):
        for i, slot in enumerate(self.inventory_elements):
            slot.slot_data = self.inventory_data[i]
            slot.update_visual()

    def update(self):
        self.update_hotbar()
        self.update_inventory()
        if self.dragged_item:
            if not hasattr(self, 'drag_icon') or self.drag_icon is None:
                self.drag_icon = Entity(parent=camera.ui, model='quad', scale=(0.11,0.11),
                                        texture=texture_mapping.get(self.dragged_item.get('item')),
                                        color=color.white, z=-1)
                self.drag_icon.ignore = True
            else:
                self.drag_icon.texture = texture_mapping.get(self.dragged_item.get('item'))
            self.drag_icon.position = mouse.position
        else:
            if hasattr(self, 'drag_icon') and self.drag_icon:
                destroy(self.drag_icon)
                self.drag_icon = None

    # New Inventory Drag/Drop Input
    def input(self, key):
        if self.inventory_open:
            if key == 'left mouse down':
                for slot in self.inventory_elements + self.hotbar_elements:
                    if slot.hovered:
                        self.dragged_slot = slot
                        if slot.slot_data:
                            self.dragged_item = slot.slot_data.copy()
                            slot.slot_data = None
                            slot.update_visual()
                        break
            elif key == 'left mouse up':
                if self.dragged_item:
                    target = None
                    for slot in self.inventory_elements + self.hotbar_elements:
                        if slot.hovered:
                            target = slot
                            break
                    if target:
                        if not target.slot_data:
                            target.slot_data = self.dragged_item
                            target.update_visual()
                        else:
                            if target.slot_data.get('item') == self.dragged_item.get('item'):
                                total = target.slot_data.get('count', 1) + self.dragged_item.get('count', 1)
                                if total <= 100:
                                    target.slot_data['count'] = total
                                    self.dragged_item = None
                                else:
                                    target.slot_data['count'] = 100
                                    self.dragged_item['count'] = total - 100
                            else:
                                old_target = target.slot_data
                                target.slot_data = self.dragged_item
                                if self.dragged_slot:
                                    self.dragged_slot.slot_data = old_target
                                    self.dragged_slot.update_visual()
                            target.update_visual()
                    else:
                        if self.dragged_slot:
                            self.dragged_slot.slot_data = self.dragged_item
                            self.dragged_slot.update_visual()
                    self.dragged_item = None
                    self.dragged_slot = None
            elif key == 'right mouse down':
                if self.dragged_item and self.dragged_item.get('count', 1) > 1:
                    target = None
                    for slot in self.inventory_elements + self.hotbar_elements:
                        if slot.hovered and not slot.slot_data:
                            target = slot
                            break
                    if target:
                        split_amount = self.dragged_item['count'] // 2
                        target.slot_data = {
                            'item': self.dragged_item['item'],
                            'count': split_amount
                        }
                        self.dragged_item['count'] -= split_amount
                        target.update_visual()
                        if self.dragged_slot:
                            self.dragged_slot.update_visual()

#############################################
# 13) Custom Player with New Swimming Logic
#############################################
class CustomPlayer(FirstPersonController):
    def __init__(self):
        super().__init__(model="character.glb", jump_height=1.2, speed=15)
        self.last_click_time = 0
        self.is_third_person = False
        self.third_person_offset = Vec3(0, 1.5, -4)
        self.first_person_offset = Vec3(0, 1.5, 0)
        self.transition_speed = 4
        self.collider = BoxCollider(self, center=Vec3(0,1,0), size=Vec3(0.6,2,0.6))
        self.gravity = 1
        self.water_check_offsets = [0, 0.5, 1, 1.5]
        self.was_underwater = False
        self.swim_velocity = 0
        self.max_swim_speed = 5
        self.swim_acceleration = 10
        self.water_drag = 2
        self.buoyancy = 9
        self.water_level = 0
        self.surface_bob_height = 1.2
        self.surface_bob_strength = 3
    def update(self):
        body_checks = []
        for y_off in self.water_check_offsets:
            body_checks.append(world.get_block((floor(self.x), floor(self.y + y_off), floor(self.z))))
        currently_underwater = any(b == 'water' for b in body_checks)
        head_in_water = (world.get_block((floor(self.x), floor(self.y + 1.5), floor(self.z))) == 'water')
        if currently_underwater and not self.was_underwater:
            if waterjump_sound:
                waterjump_sound.play()
            self.swim_velocity = 0
        if currently_underwater:
            self.gravity = 0.2
            if held_keys['space']:
                self.swim_velocity = min(self.swim_velocity + self.swim_acceleration * time.dt, self.max_swim_speed)
            else:
                self.swim_velocity = max(self.swim_velocity - self.water_drag * time.dt, 0)
            self.y += self.swim_velocity * time.dt
            if head_in_water:
                target_y = floor(self.y) + self.surface_bob_height
                y_diff = target_y - self.y
                self.y += y_diff * self.surface_bob_strength * time.dt
            else:
                self.y += self.buoyancy * time.dt
            self.direction *= 0.8
        else:
            self.gravity = 1
            self.swim_velocity = 0
        self.was_underwater = currently_underwater
        super().update()
        if currently_underwater and not head_in_water:
            surface_y = floor(self.y + 1.5)
            if abs(self.y - surface_y) < 0.1:
                self.y = surface_y
        target_pos = self.third_person_offset if self.is_third_person else self.first_person_offset
        self.camera_pivot.position = lerp(self.camera_pivot.position, target_pos, self.transition_speed * time.dt)
        if self.is_third_person:
            behind_pos = self.camera_pivot.world_position
            behind_dir = -self.camera_pivot.forward
            hit = raycast(origin=behind_pos, direction=behind_dir, ignore=[self], distance=1.5)
            if hit.hit and hit.entity and hit.entity.collider != 'box':
                self.camera_pivot.position += behind_dir * 0.3

#############################################
# 14) Free Camera
#############################################
free_cam_mode = False
free_cam = None
class CustomEditorCamera(EditorCamera):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = 10
    def update(self):
        super().update()
        if held_keys['w']:
            self.position += self.forward * self.speed * time.dt
        if held_keys['s']:
            self.position -= self.forward * self.speed * time.dt
        if held_keys['a']:
            self.position -= self.right * self.speed * time.dt
        if held_keys['d']:
            self.position += self.right * self.speed * time.dt
        if held_keys['space']:
            self.position += Vec3(0, self.speed * time.dt, 0)
        if held_keys['shift']:
            self.position += Vec3(0, -self.speed * time.dt, 0)
def toggle_free_camera():
    global free_cam_mode, free_cam, player
    if not free_cam_mode:
        free_cam = CustomEditorCamera()
        free_cam.position = player.camera_pivot.world_position
        free_cam.rotation = player.camera_pivot.world_rotation
        player.disable()
        mouse.locked = True
        mouse.visible = False
        free_cam_mode = True
    else:
        if free_cam:
            free_cam.disable()
            free_cam = None
        player.enable()
        mouse.locked = True
        mouse.visible = False
        free_cam_mode = False

#############################################
# 15) Simplified Water Functions
#############################################
def debug_init_water_entity(chunk):
    try:
        chunk.water_entity = Entity(
            model=None,
            texture=water_texture,
            color=color.rgba(60,120,255,180),
            double_sided=True,
            transparency=True
        )
        return True
    except Exception as e:
        print(e)
        return False

def update_water_mesh(chunk, water_mesh):
    try:
        if water_mesh and water_mesh.vertices:
            chunk.water_entity.model = water_mesh
            chunk.water_entity.visible = True
            return True
        else:
            chunk.water_entity.visible = False
            chunk.water_entity.model = None
            return False
    except Exception as e:
        print(e)
        return False

#############################################
# 16) Voxel World Classes (Chunk, World, etc.)
#############################################
def generate_terrain_height(x, z, seed, max_height):
    base_freq = 0.015
    hill_freq = 0.05
    detail_freq = 0.1
    base = pnoise2(x*base_freq, z*base_freq, octaves=1, base=seed)
    hill = pnoise2(x*hill_freq, z*hill_freq, octaves=1, base=seed+1)
    detail = pnoise2(x*detail_freq, z*detail_freq, octaves=1, base=seed+2)
    combined = 0.7*base + 0.2*hill + 0.1*detail
    sigmoid = 1/(1+exp(-combined*5))
    height = int(sigmoid * max_height)
    if height < 1:
        height = 1
    return height

class Chunk:
    def __init__(self, world_ref, chunk_pos, generate_terrain=True):
        self.world = world_ref
        self.chunk_pos = chunk_pos
        self.blocks = {}
        if not debug_init_water_entity(self):
            self.water_entity = Entity(model=None)
        self.dirt_entity = Entity(model=None, texture=dirt_texture, collider='mesh')
        self.grass_entity = Entity(model=None, texture=grass_texture, collider='mesh')
        self.sponge_entity = Entity(model=None, collider='mesh')
        if sponge_texture:
            self.sponge_entity.texture = sponge_texture
        else:
            self.sponge_entity.color = color.yellow
        self.stone_entity = Entity(model=None, collider='mesh')
        if stone_texture:
            self.stone_entity.texture = stone_texture
        else:
            self.stone_entity.color = color.gray
        self.crackedtile_entity = Entity(model=None, collider='mesh')
        if crackedtile_texture:
            self.crackedtile_entity.texture = crackedtile_texture
        else:
            self.crackedtile_entity.color = color.rgb(100,100,100)
        self.darkshingle_entity = Entity(model=None, collider='mesh')
        if darkshingle_texture:
            self.darkshingle_entity.texture = darkshingle_texture
        else:
            self.darkshingle_entity.color = color.rgb(40,40,40)
        self.darkwood_entity = Entity(model=None, collider='mesh')
        if darkwood_texture:
            self.darkwood_entity.texture = darkwood_texture
        else:
            self.darkwood_entity.color = color.brown
        self.lightwood_entity = Entity(model=None, collider='mesh')
        if lightwood_texture:
            self.lightwood_entity.texture = lightwood_texture
        else:
            self.lightwood_entity.color = color.rgb(200,180,130)
        self.treetrunkdark_entity = Entity(model=None, collider='mesh')
        if treetrunkdark_texture:
            self.treetrunkdark_entity.texture = treetrunkdark_texture
        else:
            self.treetrunkdark_entity.color = color.rgb(60,35,20)
        self.treetrunklight_entity = Entity(model=None, collider='mesh')
        if treetrunklight_texture:
            self.treetrunklight_entity.texture = treetrunklight_texture
        else:
            self.treetrunklight_entity.color = color.rgb(140,120,100)
        self.treeleaves_entity = Entity(model=None, collider='mesh')
        if treeleaves_texture:
            self.treeleaves_entity.texture = treeleaves_texture
        else:
            self.treeleaves_entity.color = color.green
        self.crackedglyphs_entity = Entity(model=None, texture=crackedglyphs_texture, collider='mesh')
        self.emerald_entity = Entity(model=None, texture=emerald_texture, collider='mesh')
        self.gold_entity = Entity(model=None, texture=gold_texture, collider='mesh')
        self.redbrick_entity = Entity(model=None, texture=redbrick_texture, collider='mesh')
        self.redcement_entity = Entity(model=None, texture=redcement_texture, collider='mesh')
        self.ruby_entity = Entity(model=None, texture=ruby_texture, collider='mesh')
        self.sand_entity = Entity(model=None, texture=sand_texture, collider='mesh')
        self.seashells_entity = Entity(model=None, texture=seashells_texture, collider='mesh')
        self.steel_entity = Entity(model=None, texture=steel_texture, collider='mesh')
        self.stripedwatercolor_entity = Entity(model=None, texture=stripedwatercolor_texture, collider='mesh')
        self.yellowwool_entity = Entity(model=None, texture=yellowwool_texture, collider='mesh')
        self.blackfiligree_entity = Entity(model=None, texture=blackfiligree_texture, collider='mesh')
        self.bluewool_entity = Entity(model=None, texture=bluewool_texture, collider='mesh')
        self.greenwool_entity = Entity(model=None, texture=greenwool_texture, collider='mesh')
        self.purplewool_entity = Entity(model=None, texture=purplewool_texture, collider='mesh')
        self.redwool_entity = Entity(model=None, texture=redwool_texture, collider='mesh')
        if generate_terrain:
            self.generate_terrain()
    def generate_terrain(self):
        seed = 42
        max_height = 20
        water_level = int(0.4 * max_height)
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = self.chunk_pos[0] + x
                wz = self.chunk_pos[1] + z
                height = generate_terrain_height(wx, wz, seed, max_height)
                top_block = 'grass' if height > water_level else 'water'
                for y in range(-max_height, height):
                    if y == height-1:
                        self.blocks[(wx,y,wz)] = top_block
                    elif height-y <= 5:
                        self.blocks[(wx,y,wz)] = 'dirt'
                    else:
                        self.blocks[(wx,y,wz)] = 'stone'
                for y in range(height, water_level):
                    self.blocks[(wx,y,wz)] = 'water'
        self.carve_caves(seed)
        self.place_trees_in_chunk(seed)
    def carve_caves(self, seed):
        cave_threshold = 0.8
        cave_freq = 0.04
        surface_heights = {}
        for (x,y,z), block in self.blocks.items():
            if block == 'grass':
                key = (x,z)
                if key not in surface_heights or y > surface_heights[key]:
                    surface_heights[key] = y
        new_blocks = {}
        for (x,y,z), block in self.blocks.items():
            if block in ['stone','dirt']:
                if (x,z) in surface_heights and y > surface_heights[(x,z)] - 8:
                    new_blocks[(x,y,z)] = block
                    continue
                if self.is_near_water((x,y,z), 3):
                    new_blocks[(x,y,z)] = block
                    continue
                noise_val = pnoise3(x*cave_freq, y*cave_freq, z*cave_freq, base=seed+100)
                if noise_val > cave_threshold:
                    probability = (noise_val-cave_threshold)/(1-cave_threshold)
                    if random.random() < probability:
                        new_blocks[(x,y,z)] = None
                    else:
                        new_blocks[(x,y,z)] = block
                else:
                    new_blocks[(x,y,z)] = block
            else:
                new_blocks[(x,y,z)] = block
        self.blocks = new_blocks
        for (x,z), surface_y in surface_heights.items():
            if self.blocks.get((x,surface_y,z))=='grass':
                if random.random() < 0.05:
                    mouth_radius = random.randint(1,2)
                    mouth_depth = random.randint(1,2)
                    for dx in range(-mouth_radius, mouth_radius+1):
                        for dz in range(-mouth_radius, mouth_radius+1):
                            for dy in range(1, mouth_depth+1):
                                pos = (x+dx, surface_y-dy, z+dz)
                                if self.blocks.get(pos) not in [None,'water']:
                                    self.blocks[pos] = None
    def is_near_water(self, pos, radius):
        x,y,z = pos
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                for dz in range(-radius, radius+1):
                    if (x+dx,y+dy,z+dz) in self.blocks:
                        if self.blocks[(x+dx,y+dy,z+dz)] == 'water':
                            return True
        return False
    def place_trees_in_chunk(self, seed):
        tree_seed = seed+200
        tree_chance_freq = 0.1
        tree_positions = []
        for x in range(self.chunk_pos[0], self.chunk_pos[0]+CHUNK_SIZE):
            for z in range(self.chunk_pos[1], self.chunk_pos[1]+CHUNK_SIZE):
                col_y = [y for (wx,y,wz) in self.blocks if wx==x and wz==z and self.blocks[(wx,y,wz)] is not None]
                if not col_y:
                    continue
                surface_y = max(col_y)
                if self.blocks.get((x,surface_y,z)) != 'grass':
                    continue
                if any(abs(x-tx)<=2 and abs(z-tz)<=2 for (tx,tz) in tree_positions):
                    continue
                can_place = True
                for ty in range(surface_y+1, surface_y+7):
                    if (x,ty,z) in self.blocks and self.blocks[(x,ty,z)] is not None:
                        can_place = False
                        break
                if not can_place:
                    continue
                tree_noise = pnoise2(x*tree_chance_freq, z*tree_chance_freq, base=tree_seed)
                if tree_noise > 0.5:
                    water_level = int(0.4*20)
                    if surface_y < water_level:
                        continue
                    trunk_height = 4
                    for ty in range(surface_y+1, surface_y+1+trunk_height):
                        self.blocks[(x,ty,z)] = 'treetrunkdark'
                    top = surface_y+trunk_height
                    for lx in range(x-1, x+2):
                        for lz in range(z-1, z+2):
                            self.blocks[(lx,top,lz)] = 'treeleaves'
                    self.blocks[(x,top+1,z)] = 'treeleaves'
                    tree_positions.append((x,z))
    def remove(self):
        destroy(self.water_entity)
        destroy(self.dirt_entity)
        destroy(self.grass_entity)
        destroy(self.sponge_entity)
        destroy(self.stone_entity)
        destroy(self.crackedtile_entity)
        destroy(self.darkshingle_entity)
        destroy(self.darkwood_entity)
        destroy(self.lightwood_entity)
        destroy(self.treetrunkdark_entity)
        destroy(self.treetrunklight_entity)
        destroy(self.treeleaves_entity)
        destroy(self.crackedglyphs_entity)
        destroy(self.emerald_entity)
        destroy(self.gold_entity)
        destroy(self.redbrick_entity)
        destroy(self.redcement_entity)
        destroy(self.ruby_entity)
        destroy(self.sand_entity)
        destroy(self.seashells_entity)
        destroy(self.steel_entity)
        destroy(self.stripedwatercolor_entity)
        destroy(self.yellowwool_entity)
        destroy(self.blackfiligree_entity)
        destroy(self.bluewool_entity)
        destroy(self.greenwool_entity)
        destroy(self.purplewool_entity)
        destroy(self.redwool_entity)
    def debug_water_mesh_creation(self):
        submesh_data = {'water': {'verts': [], 'uvs': [], 'norms': [], 'tris': []}}
        idx_offset = 0
        for bpos, bdata in self.blocks.items():
            actual_type = bdata if not isinstance(bdata, dict) else bdata.get("type", bdata)
            if actual_type != 'water':
                continue
            bx,by,bz = bpos
            for face_name, face_verts in CUBE_FACES.items():
                nx = bx+FACE_NORMALS[face_name].x
                ny = by+FACE_NORMALS[face_name].y
                nz = bz+FACE_NORMALS[face_name].z
                neighbor = self.world.get_block((nx,ny,nz))
                if isinstance(neighbor, dict):
                    neighbor = neighbor.get("type", neighbor)
                if (neighbor is None) or (neighbor!='water'):
                    data = submesh_data['water']
                    base = idx_offset
                    for i,v in enumerate(face_verts):
                        vx = bx+v[0]
                        vy = by+v[1]
                        vz = bz+v[2]
                        data['verts'].append((vx,vy,vz))
                        data['uvs'].append((i in (1,2), i>=2))
                        data['norms'].append(FACE_NORMALS[face_name])
                    data['tris'].extend([(base+0, base+1, base+2), (base+2, base+3, base+0)])
                    idx_offset += 4
        return submesh_data['water']
    def build_mesh(self):
        submesh_data = {
            'dirt': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'grass': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'stone': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'water': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'sponge': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'crackedtile': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'darkshingle': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'darkwood': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'lightwood': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'treetrunkdark': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'treetrunklight': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'treeleaves': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'crackedglyphs': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'emerald': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'gold': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'redbrick': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'redcement': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'ruby': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'sand': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'seashells': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'steel': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'stripedwatercolor': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'yellowwool': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'blackfiligree': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'bluewool': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'greenwool': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'purplewool': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
            'redwool': {'verts': [], 'uvs': [], 'norms': [], 'tris': []},
        }
        idx_offset = { key: 0 for key in submesh_data.keys() }
        for bpos, bdata in self.blocks.items():
            actual_type = bdata if not isinstance(bdata, dict) else bdata.get("type", bdata)
            if actual_type in (DOOR, POKEBALL, FOXFOX):
                continue
            if actual_type not in submesh_data:
                continue
            bx,by,bz = bpos
            for face_name, face_verts in CUBE_FACES.items():
                nx = bx+FACE_NORMALS[face_name].x
                ny = by+FACE_NORMALS[face_name].y
                nz = bz+FACE_NORMALS[face_name].z
                neighbor = self.world.get_block((nx,ny,nz))
                if isinstance(neighbor, dict):
                    neighbor = neighbor.get("type", neighbor)
                if actual_type=='water':
                    should_draw_face = (neighbor is None) or (neighbor!='water')
                else:
                    should_draw_face = (neighbor != actual_type)
                if not should_draw_face:
                    continue
                data = submesh_data[actual_type]
                base = idx_offset[actual_type]
                for i,v in enumerate(face_verts):
                    vx = bx+v[0]
                    vy = by+v[1]
                    vz = bz+v[2]
                    data['verts'].append((vx,vy,vz))
                    data['uvs'].append((i in (1,2), i>=2))
                    data['norms'].append(FACE_NORMALS[face_name])
                data['tris'].extend([(base+0, base+1, base+2), (base+2, base+3, base+0)])
                idx_offset[actual_type] += 4
        def make_mesh(d):
            if not d['verts']:
                return None
            return Mesh(vertices=d['verts'], uvs=d['uvs'], normals=d['norms'],
                        triangles=d['tris'], mode='triangle', static=True)
        dm = make_mesh(submesh_data['dirt'])
        if dm:
            self.dirt_entity.model = dm
            self.dirt_entity.collider = 'mesh'
            self.dirt_entity.shader = block_lighting_shader
            self.dirt_entity.double_sided = True
            self.dirt_entity.static = True
        else:
            self.dirt_entity.model = None
            self.dirt_entity.collider = None
        gm = make_mesh(submesh_data['grass'])
        if gm:
            self.grass_entity.model = gm
            self.grass_entity.collider = 'mesh'
            self.grass_entity.shader = block_lighting_shader
            self.grass_entity.double_sided = True
            self.grass_entity.static = True
        else:
            self.grass_entity.model = None
            self.grass_entity.collider = None
        stm = make_mesh(submesh_data['stone'])
        if stm:
            self.stone_entity.model = stm
            self.stone_entity.collider = 'mesh'
            self.stone_entity.shader = block_lighting_shader
            self.stone_entity.double_sided = True
            self.stone_entity.static = True
            if not stone_texture:
                self.stone_entity.color = color.gray
        else:
            self.stone_entity.model = None
            self.stone_entity.collider = None
        water_data = self.debug_water_mesh_creation()
        if water_data['verts']:
            wm = Mesh(vertices=water_data['verts'],
                      uvs=water_data['uvs'],
                      normals=water_data['norms'],
                      triangles=water_data['tris'],
                      mode='triangle',
                      static=True)
            self.water_entity.model = wm
            self.water_entity.visible = True
            self.water_entity.double_sided = True
            self.water_entity.static = True
        else:
            self.water_entity.visible = False
            self.water_entity.model = None
        sm = make_mesh(submesh_data['sponge'])
        if sm:
            self.sponge_entity.model = sm
            self.sponge_entity.collider = 'mesh'
            self.sponge_entity.shader = block_lighting_shader
            self.sponge_entity.double_sided = True
            self.sponge_entity.static = True
            if not sponge_texture:
                self.sponge_entity.color = color.yellow
        else:
            self.sponge_entity.model = None
            self.sponge_entity.collider = None
        ctm = make_mesh(submesh_data['crackedtile'])
        if ctm:
            self.crackedtile_entity.model = ctm
            self.crackedtile_entity.collider = 'mesh'
            self.crackedtile_entity.shader = block_lighting_shader
            self.crackedtile_entity.double_sided = True
            self.crackedtile_entity.static = True
            if not crackedtile_texture:
                self.crackedtile_entity.color = color.rgb(100,100,100)
        else:
            self.crackedtile_entity.model = None
            self.crackedtile_entity.collider = None
        dsm = make_mesh(submesh_data['darkshingle'])
        if dsm:
            self.darkshingle_entity.model = dsm
            self.darkshingle_entity.collider = 'mesh'
            self.darkshingle_entity.shader = block_lighting_shader
            self.darkshingle_entity.double_sided = True
            self.darkshingle_entity.static = True
            if not darkshingle_texture:
                self.darkshingle_entity.color = color.rgb(40,40,40)
        else:
            self.darkshingle_entity.model = None
            self.darkshingle_entity.collider = None
        dwm = make_mesh(submesh_data['darkwood'])
        if dwm:
            self.darkwood_entity.model = dwm
            self.darkwood_entity.collider = 'mesh'
            self.darkwood_entity.shader = block_lighting_shader
            self.darkwood_entity.double_sided = True
            self.darkwood_entity.static = True
            if not darkwood_texture:
                self.darkwood_entity.color = color.brown
        else:
            self.darkwood_entity.model = None
            self.darkwood_entity.collider = None
        lwm = make_mesh(submesh_data['lightwood'])
        if lwm:
            self.lightwood_entity.model = lwm
            self.lightwood_entity.collider = 'mesh'
            self.lightwood_entity.shader = block_lighting_shader
            self.lightwood_entity.double_sided = True
            self.lightwood_entity.static = True
            if not lightwood_texture:
                self.lightwood_entity.color = color.rgb(200,180,130)
        else:
            self.lightwood_entity.model = None
            self.lightwood_entity.collider = None
        ttdm = make_mesh(submesh_data['treetrunkdark'])
        if ttdm:
            self.treetrunkdark_entity.model = ttdm
            self.treetrunkdark_entity.collider = 'mesh'
            self.treetrunkdark_entity.shader = block_lighting_shader
            self.treetrunkdark_entity.double_sided = True
            self.treetrunkdark_entity.static = True
            if not treetrunkdark_texture:
                self.treetrunkdark_entity.color = color.rgb(60,35,20)
        else:
            self.treetrunkdark_entity.model = None
            self.treetrunkdark_entity.collider = None
        ttltm = make_mesh(submesh_data['treetrunklight'])
        if ttltm:
            self.treetrunklight_entity.model = ttltm
            self.treetrunklight_entity.collider = 'mesh'
            self.treetrunklight_entity.shader = block_lighting_shader
            self.treetrunklight_entity.double_sided = True
            self.treetrunklight_entity.static = True
            if not treetrunklight_texture:
                self.treetrunklight_entity.color = color.rgb(140,120,100)
        else:
            self.treetrunklight_entity.model = None
            self.treetrunklight_entity.collider = None
        tlm = make_mesh(submesh_data['treeleaves'])
        if tlm:
            self.treeleaves_entity.model = tlm
            self.treeleaves_entity.collider = 'mesh'
            self.treeleaves_entity.shader = block_lighting_shader
            self.treeleaves_entity.double_sided = True
            self.treeleaves_entity.static = True
            if not treeleaves_texture:
                self.treeleaves_entity.color = color.green
        else:
            self.treeleaves_entity.model = None
            self.treeleaves_entity.collider = None
        cgm = make_mesh(submesh_data['crackedglyphs'])
        if cgm:
            self.crackedglyphs_entity.model = cgm
            self.crackedglyphs_entity.collider = 'mesh'
            self.crackedglyphs_entity.shader = block_lighting_shader
            self.crackedglyphs_entity.double_sided = True
            self.crackedglyphs_entity.static = True
        else:
            self.crackedglyphs_entity.model = None
            self.crackedglyphs_entity.collider = None
        em = make_mesh(submesh_data['emerald'])
        if em:
            self.emerald_entity.model = em
            self.emerald_entity.collider = 'mesh'
            self.emerald_entity.shader = block_lighting_shader
            self.emerald_entity.double_sided = True
            self.emerald_entity.static = True
        else:
            self.emerald_entity.model = None
            self.emerald_entity.collider = None
        gm_new = make_mesh(submesh_data['gold'])
        if gm_new:
            self.gold_entity.model = gm_new
            self.gold_entity.collider = 'mesh'
            self.gold_entity.shader = block_lighting_shader
            self.gold_entity.double_sided = True
            self.gold_entity.static = True
        else:
            self.gold_entity.model = None
            self.gold_entity.collider = None
        rb = make_mesh(submesh_data['redbrick'])
        if rb:
            self.redbrick_entity.model = rb
            self.redbrick_entity.collider = 'mesh'
            self.redbrick_entity.shader = block_lighting_shader
            self.redbrick_entity.double_sided = True
            self.redbrick_entity.static = True
        else:
            self.redbrick_entity.model = None
            self.redbrick_entity.collider = None
        rc = make_mesh(submesh_data['redcement'])
        if rc:
            self.redcement_entity.model = rc
            self.redcement_entity.collider = 'mesh'
            self.redcement_entity.shader = block_lighting_shader
            self.redcement_entity.double_sided = True
            self.redcement_entity.static = True
        else:
            self.redcement_entity.model = None
            self.redcement_entity.collider = None
        ru = make_mesh(submesh_data['ruby'])
        if ru:
            self.ruby_entity.model = ru
            self.ruby_entity.collider = 'mesh'
            self.ruby_entity.shader = block_lighting_shader
            self.ruby_entity.double_sided = True
            self.ruby_entity.static = True
        else:
            self.ruby_entity.model = None
            self.ruby_entity.collider = None
        sn = make_mesh(submesh_data['sand'])
        if sn:
            self.sand_entity.model = sn
            self.sand_entity.collider = 'mesh'
            self.sand_entity.shader = block_lighting_shader
            self.sand_entity.double_sided = True
            self.sand_entity.static = True
        else:
            self.sand_entity.model = None
            self.sand_entity.collider = None
        ss = make_mesh(submesh_data['seashells'])
        if ss:
            self.seashells_entity.model = ss
            self.seashells_entity.collider = 'mesh'
            self.seashells_entity.shader = block_lighting_shader
            self.seashells_entity.double_sided = True
            self.seashells_entity.static = True
        else:
            self.seashells_entity.model = None
            self.seashells_entity.collider = None
        st = make_mesh(submesh_data['steel'])
        if st:
            self.steel_entity.model = st
            self.steel_entity.collider = 'mesh'
            self.steel_entity.shader = block_lighting_shader
            self.steel_entity.double_sided = True
            self.steel_entity.static = True
        else:
            self.steel_entity.model = None
            self.steel_entity.collider = None
        sw = make_mesh(submesh_data['stripedwatercolor'])
        if sw:
            self.stripedwatercolor_entity.model = sw
            self.stripedwatercolor_entity.collider = 'mesh'
            self.stripedwatercolor_entity.shader = block_lighting_shader
            self.stripedwatercolor_entity.double_sided = True
            self.stripedwatercolor_entity.static = True
        else:
            self.stripedwatercolor_entity.model = None
            self.stripedwatercolor_entity.collider = None
        yw = make_mesh(submesh_data['yellowwool'])
        if yw:
            self.yellowwool_entity.model = yw
            self.yellowwool_entity.collider = 'mesh'
            self.yellowwool_entity.shader = block_lighting_shader
            self.yellowwool_entity.double_sided = True
            self.yellowwool_entity.static = True
        else:
            self.yellowwool_entity.model = None
            self.yellowwool_entity.collider = None
        bfil = make_mesh(submesh_data['blackfiligree'])
        if bfil:
            self.blackfiligree_entity.model = bfil
            self.blackfiligree_entity.collider = 'mesh'
            self.blackfiligree_entity.shader = block_lighting_shader
            self.blackfiligree_entity.double_sided = True
            self.blackfiligree_entity.static = True
        else:
            self.blackfiligree_entity.model = None
            self.blackfiligree_entity.collider = None
        bw = make_mesh(submesh_data['bluewool'])
        if bw:
            self.bluewool_entity.model = bw
            self.bluewool_entity.collider = 'mesh'
            self.bluewool_entity.shader = block_lighting_shader
            self.bluewool_entity.double_sided = True
            self.bluewool_entity.static = True
        else:
            self.bluewool_entity.model = None
            self.bluewool_entity.collider = None
        gw = make_mesh(submesh_data['greenwool'])
        if gw:
            self.greenwool_entity.model = gw
            self.greenwool_entity.collider = 'mesh'
            self.greenwool_entity.shader = block_lighting_shader
            self.greenwool_entity.double_sided = True
            self.greenwool_entity.static = True
        else:
            self.greenwool_entity.model = None
            self.greenwool_entity.collider = None
        pw = make_mesh(submesh_data['purplewool'])
        if pw:
            self.purplewool_entity.model = pw
            self.purplewool_entity.collider = 'mesh'
            self.purplewool_entity.shader = block_lighting_shader
            self.purplewool_entity.double_sided = True
            self.purplewool_entity.static = True
        else:
            self.purplewool_entity.model = None
            self.purplewool_entity.collider = None
        rw = make_mesh(submesh_data['redwool'])
        if rw:
            self.redwool_entity.model = rw
            self.redwool_entity.collider = 'mesh'
            self.redwool_entity.shader = block_lighting_shader
            self.redwool_entity.double_sided = True
            self.redwool_entity.static = True
        else:
            self.redwool_entity.model = None
            self.redwool_entity.collider = None
    def set_block(self, pos, btype):
        if btype is None:
            if pos in self.blocks:
                del self.blocks[pos]
        else:
            self.blocks[pos] = btype
        self.build_mesh()

class VoxelWorld:
    def __init__(self):
        self.chunks = {}
    def get_block(self, pos):
        cx = (pos[0]//CHUNK_SIZE)*CHUNK_SIZE
        cz = (pos[2]//CHUNK_SIZE)*CHUNK_SIZE
        cpos = (cx,cz)
        if cpos not in self.chunks:
            return None
        return self.chunks[cpos].blocks.get(pos, None)
    def set_block(self, pos, btype):
        cx = (pos[0]//CHUNK_SIZE)*CHUNK_SIZE
        cz = (pos[2]//CHUNK_SIZE)*CHUNK_SIZE
        cpos = (cx,cz)
        if cpos not in self.chunks:
            self.chunks[cpos] = Chunk(self, cpos, generate_terrain=False)
        chunk = self.chunks[cpos]
        chunk.set_block(pos, btype)
        x_in = pos[0]-cx
        z_in = pos[2]-cz
        neighbors = []
        if x_in==0:
            neighbors.append((cx-CHUNK_SIZE,cz))
        if x_in==CHUNK_SIZE-1:
            neighbors.append((cx+CHUNK_SIZE,cz))
        if z_in==0:
            neighbors.append((cx,cz-CHUNK_SIZE))
        if z_in==CHUNK_SIZE-1:
            neighbors.append((cx,cz+CHUNK_SIZE))
        for np in neighbors:
            if np in self.chunks:
                self.chunks[np].build_mesh()

class World:
    def __init__(self, filename=None, force_new=False, streaming_mode=False):
        self.streaming_mode = streaming_mode
        self.vworld = VoxelWorld()
        self.chunks = self.vworld.chunks
        if not streaming_mode:
            if filename:
                if force_new and os.path.exists(os.path.join('save', filename)):
                    os.remove(os.path.join('save', filename))
                    print("Forcing new world: removed old save.")
                    self.generate_chunks()
                else:
                    self.load_world(filename)
            else:
                self.load_world()
        else:
            self.chunks = {}
    def generate_chunks(self):
        print(f"Generating new world. CHUNK_SIZE={CHUNK_SIZE}, WORLD_SIZE={WORLD_SIZE}.")
        self.chunks.clear()
        for x in range(-WORLD_SIZE, WORLD_SIZE):
            for z in range(-WORLD_SIZE, WORLD_SIZE):
                cpos = (x*CHUNK_SIZE, z*CHUNK_SIZE)
                c = Chunk(self.vworld, cpos, generate_terrain=True)
                self.chunks[cpos] = c
        for c in self.chunks.values():
            c.build_mesh()
        print("Finished generating new world.")
    def update_chunks(self, player_position):
        if not self.streaming_mode:
            return
        cx = (int(player_position.x)//CHUNK_SIZE)*CHUNK_SIZE
        cz = (int(player_position.z)//CHUNK_SIZE)*CHUNK_SIZE
        load_radius = 8
        desired = set()
        for dx in range(-load_radius, load_radius+1):
            for dz in range(-load_radius, load_radius+1):
                desired.add((cx+dx*CHUNK_SIZE, cz+dz*CHUNK_SIZE))
        for cpos in list(self.chunks.keys()):
            if cpos not in desired:
                self.chunks[cpos].remove()
                del self.chunks[cpos]
        for cpos in desired:
            if cpos not in self.chunks:
                self.chunks[cpos] = Chunk(self.vworld, cpos, generate_terrain=True)
                self.chunks[cpos].build_mesh()
    def save_world(self):
        global current_save_name
        file_path = os.path.join('save', current_save_name)
        print(f"Saving world to {file_path}...")
        data = {}
        for cpos, chunk in self.chunks.items():
            ckey = f"{cpos[0]},{cpos[1]}"
            data[ckey] = {}
            for bpos, bdata in chunk.blocks.items():
                bx,by,bz = bpos
                data[ckey][f"{bx},{by},{bz}"] = bdata
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print("World saved.")
    def load_world(self, filename=None):
        if filename is None:
            filename = current_save_name
        file_path = os.path.join('save', filename)
        if not os.path.exists(file_path):
            print(f"No '{file_path}' found. Generating new world...")
            self.generate_chunks()
            return
        print(f"Found '{file_path}'. Attempting to load.")
        if self.streaming_mode and ijson is not None:
            load_limit = 5*CHUNK_SIZE
            with open(file_path, 'r') as f:
                parser = ijson.kvitems(f, '')
                for key, blockdict in parser:
                    try:
                        cx,cz = map(int, key.split(','))
                    except:
                        continue
                    if abs(cx) <= load_limit and abs(cz) <= load_limit:
                        c = Chunk(self.vworld, (cx,cz), generate_terrain=False)
                        for bk, bdata in blockdict.items():
                            try:
                                bx,by,bz = map(int, bk.split(','))
                                c.blocks[(bx,by,bz)] = bdata
                            except:
                                pass
                        self.chunks[(cx,cz)] = c
                        c.build_mesh()
            print("Streaming world loaded (partial).")
        else:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                for ckey, blockdict in data.items():
                    try:
                        cx,cz = map(int, ckey.split(','))
                    except:
                        continue
                    c = Chunk(self.vworld, (cx,cz), generate_terrain=False)
                    for bk, bdata in blockdict.items():
                        try:
                            bx,by,bz = map(int, bk.split(','))
                            c.blocks[(bx,by,bz)] = bdata
                        except:
                            pass
                    self.chunks[(cx,cz)] = c
                for c in self.chunks.values():
                    c.build_mesh()
                print("World loaded successfully.")
            except Exception as e:
                print(f"Error loading save: {e}. Generating new world instead.")
                self.chunks.clear()
                self.generate_chunks()
        for chunk in self.chunks.values():
            for pos, bdata in chunk.blocks.items():
                actual_type = bdata if not isinstance(bdata, dict) else bdata.get("type", bdata)
                rot = 0
                if isinstance(bdata, dict):
                    rot = bdata.get("rotation", 0)
                if actual_type == DOOR:
                    if pos not in door_entities:
                        door = Door(pos)
                        door.pivot.rotation_y = rot
                        door_entities[pos] = door
                elif actual_type == POKEBALL:
                    if pos not in pokeball_entities:
                        pb = PokeballEntity(pos)
                        pb.rotation_y = rot
                        pokeball_entities[pos] = pb
                elif actual_type == FOXFOX:
                    if pos not in foxfox_entities:
                        ff = FoxfoxEntity(pos)
                        ff.rotation_y = rot
                        foxfox_entities[pos] = ff
                elif actual_type == PARTICLE_BLOCK:
                    if pos not in particleblock_entities:
                        pb = ParticleBlockEntity(pos)
                        particleblock_entities[pos] = pb
    def set_block(self, pos, btype):
        self.vworld.set_block(pos, btype)
    def get_block(self, pos):
        return self.vworld.get_block(pos)

#############################################
# 17) Menus
#############################################
current_save_name = "world_save.json"
CHUNK_SIZE = 4
WORLD_SIZE = 4
world = None
player = None
game_menu = None
inventory_ui = None
sky = None
vox_time_text = None
local_time_text = None
song_text = None
coords_text = None
compass_text = None

#############################################
# New Helper: Find Safe Spawn Height
#############################################
def find_safe_spawn_height(world, x, z):
    """Find the highest solid block at given x,z coordinates"""
    for y in range(50, -1, -1):
        if world.get_block((x, y-1, z)) in ['grass', 'stone', 'dirt']:
            return y + 1
    return 25

#############################################
# Menus: New Game, Start, Load, Save
#############################################
class NewGameMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        mouse.locked = False
        mouse.visible = True
        self.panel = Panel(parent=self, scale=(0.6,0.7), color=color.azure)
        Text(parent=self.panel, text='Enter World Settings', y=0.3, scale=1.2)
        Text(parent=self.panel, text='Chunk Size (blocks per side):', x=-0.25, y=0.1)
        self.chunk_size_field = InputField(parent=self.panel, scale=(0.2,0.1), x=0.15, y=0.1, text='4')
        Text(parent=self.panel, text='World Size (chunks per side):', x=-0.25, y=-0.05)
        self.world_size_field = InputField(parent=self.panel, scale=(0.2,0.1), x=0.15, y=-0.05, text='4')
        self.calc_text = Text(parent=self.panel, text='', y=-0.2, scale=0.8)
        self.update_calc_text()
        Button(parent=self.panel, text='Start!', y=-0.35, scale=(0.3,0.1), on_click=self.start_game)
        Button(parent=self.panel, text='Back', y=-0.45, scale=(0.3,0.1), on_click=self.go_back)
        self.chunk_size_field.on_value_changed = self.update_calc_text
        self.world_size_field.on_value_changed = self.update_calc_text
    def update_calc_text(self):
        try:
            cs = int(self.chunk_size_field.text)
        except:
            cs = 4
        try:
            ws = int(self.world_size_field.text)
        except:
            ws = 4
        blocks_per_chunk = cs * 300 * cs
        total_chunks = (2*ws)**2
        self.calc_text.text = f"Each chunk: {cs}×300×{cs} = {blocks_per_chunk} blocks\nTotal chunks: {total_chunks}"
    def start_game(self):
        try:
            cs = int(self.chunk_size_field.text)
        except:
            cs = 4
        try:
            ws = int(self.world_size_field.text)
        except:
            ws = 4
        global CHUNK_SIZE, WORLD_SIZE
        CHUNK_SIZE = cs
        WORLD_SIZE = ws
        streaming_mode = True if ws > 10 else False
        destroy(self)
        create_game(filename=None, force_new=True, streaming_mode=streaming_mode)
    def go_back(self):
        destroy(self)
        StartMenu()

class StartMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        mouse.locked = False
        mouse.visible = True
        self.panel = Panel(parent=self, scale=(0.6,0.7), color=color.gray)
        Text(parent=self.panel, text='Vox-World by DaddyCodymon', scale=1.5, y=0.3)
        Button(parent=self.panel, text='New Game', y=0.05, scale=(0.3,0.1), on_click=self.go_new_game)
        Button(parent=self.panel, text='Load Game', y=-0.05, scale=(0.3,0.1), on_click=self.go_load_game)
        Button(parent=self.panel, text='Quit', y=-0.15, scale=(0.3,0.1), on_click=application.quit)
    def go_new_game(self):
        destroy(self)
        NewGameMenu()
    def go_load_game(self):
        destroy(self)
        LoadGameMenu()

class LoadGameMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        mouse.locked = False
        mouse.visible = True
        self.panel = Panel(parent=self, scale=(0.6,0.7), color=color.gray)
        Text(parent=self.panel, text='Select a .json to load:', y=0.3)
        y_offset = 0.2
        save_folder = 'save'
        file_list = []
        if os.path.exists(save_folder):
            file_list = [f for f in os.listdir(save_folder) if f.lower().endswith('.json')]
        if not file_list:
            Text(parent=self.panel, text='(No .json found in /save)', y=0)
        else:
            for fname in file_list:
                def load_func(fn=fname):
                    return lambda: self.load_selected(fn)
                Button(parent=self.panel, text=fname, y=y_offset, scale=(0.4,0.1), on_click=load_func(fname))
                y_offset -= 0.12
        Button(parent=self.panel, text='Back', y=-0.25, scale=(0.3,0.1), on_click=self.go_back)
    def load_selected(self, filename):
        global current_save_name
        current_save_name = filename
        destroy(self)
        create_game(filename=filename, force_new=False)
    def go_back(self):
        destroy(self)
        StartMenu()

class SaveAsMenu(Entity):
    def __init__(self, parent_menu):
        super().__init__(parent=camera.ui)
        self.parent_menu = parent_menu
        self.parent_menu.enabled = False
        self.panel = Panel(parent=self, scale=(0.5,0.3), color=color.gray)
        Text(parent=self.panel, text='Save File Name:', y=0.1)
        self.input_field = InputField(parent=self.panel, scale=(0.5,0.08), y=0)
        self.input_field.text = current_save_name
        Button(parent=self.panel, text='Confirm', color=color.azure, y=-0.1, scale=(0.3,0.1), on_click=self.confirm_save)
        Button(parent=self.panel, text='Cancel', color=color.red, y=-0.22, scale=(0.3,0.1), on_click=self.cancel)
    def confirm_save(self):
        fn = self.input_field.text.strip()
        if not fn.lower().endswith('.json'):
            fn += '.json'
        destroy(self)
        self.parent_menu.save_and_quit(fn)
    def cancel(self):
        self.parent_menu.enabled = True
        destroy(self)

class GameMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False)
        self.panel = Panel(parent=self, scale=(0.5,0.6), color=color.dark_gray)
        Text(parent=self.panel, text='Game Menu', y=0.3)
        Button(parent=self.panel, text='Save & Quit', y=0, scale=(0.3,0.1), on_click=self.ask_save_name)
        Button(parent=self.panel, text='Resume', y=0.1, scale=(0.3,0.1), on_click=self.resume_game)
        self.music_button = Button(parent=self.panel, text='Music: ON', y=-0.1, scale=(0.3,0.1), on_click=self.toggle_music)
    def ask_save_name(self):
        SaveAsMenu(self)
    def save_and_quit(self, chosen_name):
        global current_save_name
        current_save_name = chosen_name
        if world:
            world.save_world()
        application.quit()
    def resume_game(self):
        self.enabled = False
        mouse.locked = True
        mouse.visible = False
        player.enable()
    def toggle_music(self):
        global music_on
        music_on = not music_on
        if not music_on:
            if current_music and current_music.playing:
                current_music.pause()
            self.music_button.text = 'Music: OFF'
        else:
            self.music_button.text = 'Music: ON'
            if current_music and not current_music.playing:
                current_music.resume()
            else:
                if not current_music:
                    start_random_music()

#############################################
# 18) Update Shader Uniforms (Simplified)
#############################################
def update_shader_uniforms():
    if player:
        sun_angle = (time.time()-start_time)/full_cycle_time*2*pi
        scene.set_shader_input("time_of_day", sun_angle)
        sky.set_shader_input("time_of_day", sun_angle)

#############################################
# 19) New Safe Spawn Helper & Create Game Function
#############################################
def find_safe_spawn_height(world, x, z):
    """Find the highest solid block at given x,z coordinates"""
    for y in range(50, -1, -1):
        if world.get_block((x, y-1, z)) in ['grass', 'stone', 'dirt']:
            return y + 1
    return 25

full_cycle_time = 20*60
start_time = time.time()

world = None
player = None
game_menu = None
inventory_ui = None
sky = None
vox_time_text = None
local_time_text = None
song_text = None
coords_text = None
compass_text = None

last_chunk_update = 0

def create_game(filename=None, force_new=False, streaming_mode=False):
    global world, player, game_menu, inventory_ui, sky, vox_time_text, local_time_text, song_text, coords_text, compass_text
    for e in camera.ui.children[:]:
        if e is not mouse:
            destroy(e)
    print("\n[GAME] Creating game now...")
    global bubble_timer
    bubble_timer = 0
    global CHUNK_SIZE, WORLD_SIZE
    world = World(filename=filename, force_new=force_new, streaming_mode=streaming_mode)
    player = CustomPlayer()
    spawn_x, spawn_z = 0, 0
    safe_y = find_safe_spawn_height(world, spawn_x, spawn_z)
    player.position = Vec3(spawn_x, safe_y, spawn_z)
    def ensure_safe_spawn():
        if player.position.y < 0:
            player.position = Vec3(spawn_x, safe_y, spawn_z)
            player.velocity = Vec3(0, 0, 0)
    invoke(ensure_safe_spawn, delay=0.5)
    invoke(ensure_safe_spawn, delay=1.0)
    player.model.hide()
    player.rotation = (0,0,0)
    player.camera_pivot.rotation = (0,0,0)
    game_menu = GameMenu()
    inventory_ui = InventoryUI()
    sky = Entity(model='sphere', scale=500, double_sided=True, shader=daynight_shader)
    sky.set_shader_input("time_of_day", 0.0)
    init_music()
    vox_time_text = Text(text='Vox Time: ', parent=camera.ui, position=(0.5,0.45), scale=1.2)
    local_time_text = Text(text='Local Time:', parent=camera.ui, position=(0.5,0.40), scale=1.2)
    song_text = Text(text='Song: None', parent=camera.ui, position=(0.45,0.35), scale=1.2)
    coords_text = Text(text='Coords: X=0 Y=0 Z=0', parent=camera.ui, position=(-0.85,0.45), scale=1.2)
    compass_text = Text(text='Facing: ' + get_cardinal(player.rotation_y), parent=camera.ui, position=(-0.85,0.40), scale=1.2)
    mouse.locked = True
    mouse.visible = False
    print("[GAME] Game created successfully.")

#############################################
# 20) Main Update Function
#############################################
def update():
    global last_chunk_update
    update_shader_uniforms()
    update_music()
    process_water_spread()
    if world and world.streaming_mode:
        if time.time()-last_chunk_update > 0.5:
            world.update_chunks(player.position)
            last_chunk_update = time.time()
    if free_cam_mode:
        return
    if not player:
        return
    if inventory_ui and inventory_ui.inventory_open:
        inventory_ui.update()
        return
    if vox_time_text and local_time_text and song_text:
        in_game_seconds = (time.time()-start_time)%full_cycle_time
        total_in_game_minutes = in_game_seconds/full_cycle_time*24*60
        hours_24 = int(total_in_game_minutes//60)%24
        minute = int(total_in_game_minutes%60)
        if hours_24==0:
            hour = 12; ampm = 'AM'
        elif hours_24<12:
            hour = hours_24; ampm = 'AM'
        elif hours_24==12:
            hour = 12; ampm = 'PM'
        else:
            hour = hours_24-12; ampm = 'PM'
        vox_time_text.text = f"Vox Time: {hour:02d}:{minute:02d} {ampm}"
        local_time_text.text = "Local Time: " + time.strftime("%I:%M %p")
        if current_track:
            from os.path import basename
            song_text.text = "Song: " + basename(current_track)
        else:
            song_text.text = "Song: None"
    if coords_text and compass_text:
        coords_text.text = f"Coords: X={player.x:.1f} Y={player.y:.1f} Z={player.z:.1f}"
        compass_text.text = "Facing: " + get_cardinal(player.rotation_y)
    if game_menu and game_menu.enabled:
        return
    if time.time()-player.last_click_time > 0.15:
        if mouse.left:
            remove_block()
            player.last_click_time = time.time()
        elif mouse.right:
            slot = inventory_ui.hotbar_data[inventory_ui.hotbar_selected]
            if not slot:
                return
            btype = slot['item']
            place_block(btype)
            slot['count'] -= 1
            if slot['count'] <= 0:
                inventory_ui.hotbar_data[inventory_ui.hotbar_selected] = None
            player.last_click_time = time.time()

#############################################
# 21) Raycast Helper Functions
#############################################
def do_raycast(distance=8):
    if not player:
        return None
    return raycast(origin=player.camera_pivot.world_position,
                   direction=player.camera_pivot.forward,
                   distance=distance, ignore=[player], debug=False)
def get_pointed_block_coord(remove=True):
    hit = do_raycast()
    if hit and hit.hit:
        shift = -0.001 if remove else 0.001
        hp = hit.world_point + (hit.world_normal*shift)
        bx = floor(hp.x)
        by = floor(hp.y)
        bz = floor(hp.z)
        return (bx,by,bz), hit
    else:
        candidate = player.camera_pivot.world_position + player.camera_pivot.forward*2
        base_candidate = (floor(candidate.x), floor(candidate.y), floor(candidate.z))
        for dx in range(-1,2):
            for dy in range(-1,2):
                for dz in range(-1,2):
                    pos = (base_candidate[0]+dx, base_candidate[1]+dy, base_candidate[2]+dz)
                    if world and world.get_block(pos)==PARTICLE_BLOCK:
                        return (pos,None)
        return None

#############################################
# 22) Place/Remove Block Functions
#############################################
def place_block(btype):
    if not world:
        return
    data = get_pointed_block_coord(remove=False)
    if not data:
        return
    (bx,by,bz), hit = data
    if btype==DOOR:
        if world.get_block((bx,by,bz)):
            return
        d = Door((bx,by,bz))
        door_entities[(bx,by,bz)] = d
        world.set_block((bx,by,bz), DOOR)
        return
    elif btype==POKEBALL:
        if world.get_block((bx,by,bz)):
            return
        pb = PokeballEntity((bx,by,bz))
        pokeball_entities[(bx,by,bz)] = pb
        world.set_block((bx,by,bz), {"type": POKEBALL, "rotation": pb.rotation_y})
        return
    elif btype==FOXFOX:
        if world.get_block((bx,by,bz)):
            return
        ff = FoxfoxEntity((bx,by,bz))
        foxfox_entities[(bx,by,bz)] = ff
        world.set_block((bx,by,bz), {"type": FOXFOX, "rotation": ff.rotation_y})
        return
    elif btype==PARTICLE_BLOCK:
        if world.get_block((bx,by,bz)):
            return
        pb = ParticleBlockEntity((bx,by,bz))
        particleblock_entities[(bx,by,bz)] = pb
        world.set_block((bx,by,bz), PARTICLE_BLOCK)
        return
    if not world.get_block((bx,by,bz)):
        world.set_block((bx,by,bz), btype)
        if btype=='water':
            water_sound.play()
            cx = (bx//CHUNK_SIZE)*CHUNK_SIZE
            cz = (bz//CHUNK_SIZE)*CHUNK_SIZE
            chunk = world.chunks.get((cx,cz))
            if chunk:
                chunk.build_mesh()
            if player:
                spread_water_slowly((bx,by,bz),5,direction=player.forward)
            else:
                spread_water_slowly((bx,by,bz),5,direction=Vec3(0,0,1))
        elif btype=='sponge':
            sponge_sound.play()
            near_water = False
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    for dz in [-1,0,1]:
                        if dx==0 and dy==0 and dz==0:
                            continue
                        if world.get_block((bx+dx,by+dy,bz+dz))=='water':
                            near_water = True
                            break
                    if near_water:
                        break
                if near_water:
                    soak_up_water((bx,by,bz),5)

def remove_block():
    if not world:
        return
    data = get_pointed_block_coord(remove=True)
    if not data:
        return
    (bx,by,bz), hit = data
    saved = world.get_block((bx,by,bz))
    if isinstance(saved, dict):
        existing_block = saved.get("type", saved)
    else:
        existing_block = saved
    if not existing_block:
        return
    if existing_block==DOOR:
        base = (bx,by,bz)
        if base in door_entities:
            d = door_entities[base]
            d.disable()
            Debris((bx,by,bz), existing_block)
            del door_entities[base]
        world.set_block((bx,by,bz), None)
        return
    if existing_block==POKEBALL:
        base = (bx,by,bz)
        if base in pokeball_entities:
            pokeball_entities[base].disable()
            del pokeball_entities[base]
        for _ in range(8):
            Debris((bx,by,bz), existing_block)
        world.set_block((bx,by,bz), None)
        return
    if existing_block==FOXFOX:
        base = (bx,by,bz)
        if base in foxfox_entities:
            foxfox_entities[base].disable()
            del foxfox_entities[base]
        for _ in range(8):
            Debris((bx,by,bz), existing_block)
        world.set_block((bx,by,bz), None)
        return
    if existing_block==PARTICLE_BLOCK:
        base = (bx,by,bz)
        if base in particleblock_entities:
            particleblock_entities[base].disable()
            del particleblock_entities[base]
        for _ in range(32):
            Debris((bx,by,bz), existing_block)
        world.set_block((bx,by,bz), None)
        return
    world.set_block((bx,by,bz), None)
    for _ in range(32):
        Debris((bx,by,bz), existing_block)
    dig_sound.play()
    if existing_block in collectible_blocks:
        spawn_pickup(existing_block, (bx,by,bz))

#############################################
# 23) Input Handling
#############################################
def input(key):
    if key=='tab':
        if inventory_ui:
            inventory_ui.toggle_inventory()
        return
    if inventory_ui and inventory_ui.inventory_open:
        inventory_ui.input(key)
        return
    if key=='enter':
        global command_mode, command_input_field
        if not command_mode:
            command_mode = True
            if player:
                player.disable()
            mouse.locked = False
            mouse.visible = True
            command_input_field = InputField(parent=camera.ui, scale=(0.5,0.1),
                                              position=(0,-0.3), background_color=color.rgba(0,0,0,150))
            command_input_field.placeholder_text = "Enter command..."
            return
        else:
            cmd = command_input_field.text.strip()
            destroy(command_input_field)
            command_input_field = None
            command_mode = False
            if player:
                player.enable()
            mouse.locked = True
            mouse.visible = False
            try:
                if cmd.lower().startswith("set time"):
                    parts = cmd.split()
                    if len(parts)>=3:
                        time_str = parts[2].lower()
                        if time_str.endswith("am") or time_str.endswith("pm"):
                            period = time_str[-2:]
                            hour_part = time_str[:-2]
                            hour_val = int(hour_part)
                            if hour_val<1 or hour_val>12:
                                print("Invalid hour. Use 1-12 with am/pm.")
                                return
                            hour_24 = 0 if (period=="am" and hour_val==12) else (hour_val if period=="am" else (12 if hour_val==12 else hour_val+12))
                            desired_angle = (hour_24/24.0)*2*pi
                            global start_time
                            start_time = time.time() - (desired_angle*full_cycle_time)/(2*pi)
                            print(f"Time set to {hour_val}{period.upper()} (24-hour: {hour_24}:00)")
                        else:
                            print("Time format error. Use e.g. '1am' or '2pm'.")
                    else:
                        print("Time command format error. Use 'Set time <hour><am/pm>'.")
                elif cmd.lower().startswith("move"):
                    parts = cmd.split()
                    if len(parts)>=4:
                        try:
                            x_str = parts[1]
                            y_str = parts[2]
                            z_str = parts[3]
                            x_val = float(x_str[1:]) if x_str.lower().startswith('x') else float(x_str)
                            y_val = float(y_str[1:]) if y_str.lower().startswith('y') else float(y_str)
                            z_val = float(z_str[1:]) if z_str.lower().startswith('z') else float(z_str)
                            player.position = Vec3(x_val,y_val,z_val)
                            print(f"Moved player to {x_val}, {y_val}, {z_val}")
                        except Exception as e:
                            print("Move command error:", e)
                    else:
                        print("Move command format error. Use 'Move x<number> y<number> z<number>'.")
            except Exception as e:
                print("Error processing command:", e)
            return
    if command_mode:
        return
    if game_menu and game_menu.enabled:
        return
    if key=='v':
        toggle_free_camera()
        return
    if not player:
        return
    if key=='escape':
        game_menu.enabled = not game_menu.enabled
        mouse.locked = not game_menu.enabled
        mouse.visible = game_menu.enabled
    elif key=='scroll up':
        inventory_ui.hotbar_selected = (inventory_ui.hotbar_selected+1)%len(inventory_ui.hotbar_data)
    elif key=='scroll down':
        inventory_ui.hotbar_selected = (inventory_ui.hotbar_selected-1)%len(inventory_ui.hotbar_data)
    elif key=='e':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==DOOR:
                if (bx,by,bz) in door_entities:
                    door_entities[(bx,by,bz)].toggle()
            elif block_type==POKEBALL:
                play_sound_once(pokeball_sound)
            elif block_type==FOXFOX:
                play_sound_once(foxfox_sound)
            elif block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    print(f"Interacting with particle block at {(bx,by,bz)}. Current shrink index: {pb.shrink_index}")
                    pb.shrink_index = (pb.shrink_index+1)%4
                    scale_values = [0.1,0.075,0.05,0.025]
                    pb.settings['size'] = scale_values[pb.shrink_index]
                    pb.scale = scale_values[pb.shrink_index]
                    print(f"New shrink index: {pb.shrink_index}. New particle size: {scale_values[pb.shrink_index]}")
    elif key=='r':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    if not hasattr(pb, 'density_index'):
                        pb.density_index = 0
                    density_values = [50,38,25,13]
                    pb.density_index = (pb.density_index+1)%len(density_values)
                    pb.settings['particle_count'] = density_values[pb.density_index]
                    print(f"Particle block at {(bx,by,bz)}: New density: {density_values[pb.density_index]}")
    elif key=='t':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    if not hasattr(pb, 'start_color_index'):
                        pb.start_color_index = 0
                    start_color_options = [color.rgb(255,0,0), color.rgb(0,255,0), color.rgb(0,0,255), color.rgb(255,255,255)]
                    pb.start_color_index = (pb.start_color_index+1)%len(start_color_options)
                    pb.settings['start_color'] = start_color_options[pb.start_color_index]
                    print(f"Particle block at {(bx,by,bz)}: New start color: {start_color_options[pb.start_color_index]}")
    elif key=='y':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    if not hasattr(pb, 'end_color_index'):
                        pb.end_color_index = 0
                    end_color_options = [color.rgb(255,255,0), color.rgb(255,0,255), color.rgb(0,255,255), color.rgb(0,0,0)]
                    pb.end_color_index = (pb.end_color_index+1)%len(end_color_options)
                    pb.settings['end_color'] = end_color_options[pb.end_color_index]
                    print(f"Particle block at {(bx,by,bz)}: New end color: {end_color_options[pb.end_color_index]}")
    elif key=='u':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    if not hasattr(pb, 'gravity_index'):
                        pb.gravity_index = 0
                    gravity_values = [0.1,0.075,0.05,0.025]
                    pb.gravity_index = (pb.gravity_index+1)%len(gravity_values)
                    pb.settings['gravity'] = gravity_values[pb.gravity_index]
                    print(f"Particle block at {(bx,by,bz)}: New gravity: {gravity_values[pb.gravity_index]}")
    elif key=='i':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    if not hasattr(pb, 'lifetime_index'):
                        pb.lifetime_index = 0
                    lifetime_values = [2,1.5,1,0.5]
                    pb.lifetime_index = (pb.lifetime_index+1)%len(lifetime_values)
                    pb.settings['lifetime'] = lifetime_values[pb.lifetime_index]
                    print(f"Particle block at {(bx,by,bz)}: New lifetime: {lifetime_values[pb.lifetime_index]}")
    elif key=='o':
        hit = do_raycast()
        if hit and hit.hit:
            shift = -0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==PARTICLE_BLOCK:
                if (bx,by,bz) in particleblock_entities:
                    pb = particleblock_entities[(bx,by,bz)]
                    if not hasattr(pb, 'speed_index'):
                        pb.speed_index = 0
                    speed_values = [2,1.5,1,0.5]
                    pb.speed_index = (pb.speed_index+1)%len(speed_values)
                    pb.settings['speed'] = speed_values[pb.speed_index]
                    print(f"Particle block at {(bx,by,bz)}: New speed: {speed_values[pb.speed_index]}")
    elif key=='m':
        hit = do_raycast()
        if hit and hit.hit:
            shift = 0.001
            wp = hit.world_point+(hit.world_normal*shift)
            bx = floor(wp.x)
            by = floor(wp.y)
            bz = floor(wp.z)
            saved = world.get_block((bx,by,bz))
            if isinstance(saved, dict):
                block_type = saved.get("type", saved)
            else:
                block_type = saved
            if block_type==POKEBALL:
                if (bx,by,bz) in pokeball_entities:
                    entity = pokeball_entities[(bx,by,bz)]
                    entity.rotate_self()
                    world.set_block((bx,by,bz), {"type": POKEBALL, "rotation": entity.rotation_y})
            elif block_type==FOXFOX:
                if (bx,by,bz) in foxfox_entities:
                    entity = foxfox_entities[(bx,by,bz)]
                    entity.rotate_self()
                    world.set_block((bx,by,bz), {"type": FOXFOX, "rotation": entity.rotation_y})

#############################################
# 24) Launch the Game
#############################################
StartMenu()
app.run()
