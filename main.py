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

# Conceptual new textures for biomes (map to existing ones for now)
snow_texture = safe_load_texture('assets/white_wool.png') # Assuming white wool exists, or use another placeholder
if not snow_texture: snow_texture = stone_texture # Fallback
sandstone_texture = safe_load_texture('assets/sand.png') # Placeholder, use sand if no specific sandstone

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
    'door': None, # Special entity, no direct texture in this map
    'pokeball': None, # Special entity
    'foxfox': None, # Special entity
    'particleblock': purplewool_texture, # Example
    'snow': snow_texture, # New biome block
    'sandstone': sandstone_texture # New biome block
}

# Define collectible blocks for drop/pickup logic.
collectible_blocks = ['dirt','grass','stone','sponge','crackedtile','darkshingle','darkwood',
                      'lightwood','treetrunkdark','treetrunklight','treeleaves','crackedglyphs',
                      'emerald','gold','redbrick','redcement','ruby','sand','seashells','steel',
                      'stripedwatercolor','yellowwool','blackfiligree','bluewool','greenwool',
                      'purplewool','redwool',
                      'snow', 'sandstone'] # Added new biome blocks

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

BLOCK_TYPES = [ # Ensure this list is comprehensive for inventory/UI purposes
    'dirt','grass','stone','water','sponge',
    'crackedtile','darkshingle','darkwood','lightwood',
    'treetrunkdark','treetrunklight','treeleaves',
    'crackedglyphs','emerald','gold','redbrick','redcement','ruby',
    'sand','seashells','steel','stripedwatercolor','yellowwool',
    'blackfiligree','bluewool','greenwool','purplewool','redwool',
    DOOR, POKEBALL, FOXFOX, PARTICLE_BLOCK,
    'snow', 'sandstone' # Added new biome blocks
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
        music_length = 180 # Default length if not found

def update_music():
    global current_music, music_start_time, music_length
    if not music_on:
        if current_music and current_music.playing:
            current_music.pause()
        return
    else: # music_on is True
        if current_music and not current_music.playing:
            # Check if it was paused or finished
            if current_music.time > 0 and current_music.length > 0 and current_music.time < current_music.length:
                 current_music.resume()
            else: # Finished or never started properly
                 start_random_music()
        elif not current_music: # No music object exists
            start_random_music()

    if current_music and current_music.playing: # Check if it's time for the next track
        elapsed = time.time() - music_start_time
        if music_length > 0 and elapsed >= music_length - 0.1: # Small buffer
            start_random_music()
    elif music_on and not current_music: # If music is on but nothing is playing (e.g. after a track failed to load)
        start_random_music()


def init_music():
    if not os.path.exists('assets/sounds'):
        return
    for fname in os.listdir('assets/sounds'):
        if fname.lower().endswith('.mp3'):
            music_tracks.append(os.path.join('assets/sounds', fname))
    if music_tracks: # Only start music if tracks were found
        start_random_music()

def play_sound_once(sound):
    if sound and not sound.playing: # Add a check for sound existence
        sound.play()

#############################################
# 6b) Water Physics Constants
#############################################
WATER_LEVEL = 0.0 # This might be dynamically set or less relevant with biome water levels
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
        self.pivot = Entity(position=self.base_pos + Vec3(0.5,0,0.5)) # Pivot for rotation
        self.parent = self.pivot # Door model will be parented to pivot
        self.model = 'cube' # Placeholder, should be a door model
        self.texture = darkwood_texture # Example texture
        self.scale = (1,2,0.2) # Example scale for a door panel
        self.position = Vec3(-0.5,0,0) # Position relative to pivot
        self.collider = BoxCollider(self, center=Vec3(0.5,1,0.1), size=(1,2,0.2)) # Adjust collider
        self.color = color.white # Reset color if texture applied
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
        if door_sound: door_sound.play()
        self.is_animating = True
        if self.open: # If open, close it
            self.target_rot = self.closed_rotation
            # Re-enable collider when closed, adjust its position/size if needed
            self.collider = BoxCollider(self, center=Vec3(0.5,1,0.1), size=(1,2,0.2))
            self.open = False
        else: # If closed, open it
            self.target_rot = self.open_rotation
            self.collider = None # Disable collider when open
            self.open = True

class PokeballEntity(Entity):
    def __init__(self, base_pos):
        super().__init__()
        self.base_pos = Vec3(*base_pos)
        self.position = self.base_pos + Vec3(0.5,0.25,0.5) # Centered on block, slightly above ground
        self.model = load_model('assets/pokeball.gltf') # Ensure this path is correct
        if not self.model: self.model = 'sphere' # Fallback model
        self.scale = 0.25 # Smaller scale
        self.collider = BoxCollider(self, center=Vec3(0,0.5,0), size=Vec3(1,1,1)) # Relative to entity's origin
        self.color = color.white # In case model has no color/texture
    def rotate_self(self):
        self.rotation_y += 30

class FoxfoxEntity(Entity):
    def __init__(self, base_pos):
        super().__init__()
        self.base_pos = Vec3(*base_pos)
        self.position = self.base_pos + Vec3(0.5,0.375,0.5) # Centered, adjust Y based on model
        self.model = load_model('assets/foxfox.gltf') # Ensure path is correct
        if not self.model: self.model = 'cube' # Fallback
        self.scale = 0.375 # Adjust scale
        self.collider = BoxCollider(self, center=Vec3(0,0.5,0), size=Vec3(1,1,1)) # Relative
        self.color = color.white
    def rotate_self(self):
        self.rotation_y += 30

class ParticleBlockEntity(Entity): # This is a standard block, not an entity to be placed separately usually
    def __init__(self, base_pos): # This class might be redundant if PARTICLE_BLOCK is just a type
        super().__init__(model='cube', position=Vec3(*base_pos) + Vec3(0.5,0.5,0.5), texture=purplewool_texture)
        # This entity is more for *effects* originating from a block, not the block itself.
        # The actual block 'particleblock' would be part of the chunk mesh.
        # This class could be used to manage particle emitters AT the block's location.
        self.settings = {'size': 0.1, 'particle_count': 50, 'start_color': color.red, 
                         'end_color': color.yellow, 'lifetime': 2, 'gravity': 0.1, 'speed': 1.0}
        self.shrink_index = 0 
        # If this entity is meant to BE the block, it needs a collider and to be handled by world.set_block
        # If it's just an effect manager, it might not need a collider.
        # For now, assume it's an effect tied to a 'particleblock' type in self.blocks.
        self.visible = False # The effect manager itself is not visible.
    def update(self):
        # Logic for spawning particles based on self.settings if this is an emitter
        pass


#############################################
# 9) BFS Water Spread Functions
#############################################
water_spread_queue = []
def process_water_spread():
    now = time.time()
    processed_in_step = 0
    max_processed_per_step = 10 # Limit water spread per frame

    for ev_idx in range(len(water_spread_queue) -1, -1, -1): # Iterate backwards for safe removal
        if processed_in_step >= max_processed_per_step:
            break
        
        ev = water_spread_queue[ev_idx]
        if ev['time_to_spread'] <= now:
            water_spread_queue.pop(ev_idx) # Remove event
            pos_to_fill = ev['pos']
            dist_remaining = ev['dist']
            # direction_of_spread = ev['direction'] # Not used in current spread logic

            # Check if block at pos_to_fill is air (None)
            if world.get_block(pos_to_fill) is None:
                world.set_block(pos_to_fill, 'water') # Place water block
                processed_in_step += 1
                if dist_remaining > 0:
                    # Schedule further spread from the newly placed water block
                    # Spread to horizontal neighbors and one block down
                    # Original function spread_water_slowly had more complex directionality
                    # This is a simplified re-spread:
                    simple_spread_offsets = [(1,0,0), (-1,0,0), (0,0,1), (0,0,-1), (0,-1,0)]
                    for off in simple_spread_offsets:
                        next_pos = (pos_to_fill[0]+off[0], pos_to_fill[1]+off[1], pos_to_fill[2]+off[2])
                        # Check if next_pos is air before scheduling
                        if world.get_block(next_pos) is None:
                             # Spread with slightly less distance, fixed delay
                            schedule_water_spread(next_pos, dist_remaining -1, Vec3(0,0,0), delay=0.3)


def schedule_water_spread(pos, dist, direction, delay=0.2): # Direction currently not used in simplified spread
    # Check if a spread event for this position is already scheduled to avoid duplicates
    for existing_event in water_spread_queue:
        if existing_event['pos'] == pos:
            return # Already scheduled for this position

    water_spread_queue.append({
        'pos': pos,
        'dist': dist,
        'direction': direction, # Retained for potential future use
        'time_to_spread': time.time() + delay
    })

# Original spread_water_slowly is effectively replaced by logic in process_water_spread
# and schedule_water_spread. If more complex directional spread is needed, it would be revived.

def soak_up_water(center_pos, radius=5): # BFS for soaking
    visited_soak = set()
    queue_soak = deque()
    queue_soak.append((center_pos, 0)) # (position, distance_traveled)
    
    # 3D offsets for checking all neighbors
    soak_offsets = []
    for dx_soak in [-1,0,1]:
        for dy_soak in [-1,0,1]:
            for dz_soak in [-1,0,1]:
                if dx_soak==0 and dy_soak==0 and dz_soak==0:
                    continue
                soak_offsets.append((dx_soak,dy_soak,dz_soak))

    blocks_soaked = 0
    while queue_soak:
        (current_x, current_y, current_z), dist = queue_soak.popleft()

        if dist > radius: # Stop if beyond soak radius
            continue
        if (current_x, current_y, current_z) in visited_soak: # Already processed
            continue
        visited_soak.add((current_x, current_y, current_z))

        if world.get_block((current_x, current_y, current_z)) == 'water':
            world.set_block((current_x, current_y, current_z), None) # Remove water
            blocks_soaked +=1

        # Add neighbors to queue
        for off_s_x, off_s_y, off_s_z in soak_offsets:
            next_x, next_y, next_z = current_x + off_s_x, current_y + off_s_y, current_z + off_s_z
            next_dist = dist + 1
            if next_dist <= radius: # Only add if within radius
                queue_soak.append(((next_x, next_y, next_z), next_dist))
    if blocks_soaked > 0: print(f"Sponge soaked {blocks_soaked} water blocks.")


#############################################
# 10) Bubble Particles
#############################################
class BubbleParticle(Entity):
    def __init__(self, start_pos):
        super().__init__(parent=scene, model='quad', texture='circle', # Ensure 'circle' texture exists
                         scale=random.uniform(0.05, 0.15), position=start_pos, billboard=True)
        self.color = color.rgba(180,180,255,random.randint(100,180)) # Light blueish
        self.lifetime = random.uniform(1.0, 2.5)
        self.spawn_time = time.time()
        self.y_vel = random.uniform(0.3, 0.8) # Upward velocity
        self.x_drift = random.uniform(-0.1, 0.1) # Sideways drift
        self.z_drift = random.uniform(-0.1, 0.1)

    def update(self):
        dt_bubbles = time.dt
        self.position += Vec3(self.x_drift*dt_bubbles, self.y_vel*dt_bubbles, self.z_drift*dt_bubbles)
        
        age = time.time() - self.spawn_time
        if age > self.lifetime:
            destroy(self)
            return
        
        # Fade out based on age
        ratio_bubbles = age / self.lifetime
        self.alpha = 1 - ratio_bubbles

bubble_timer = 0 # Global timer for bubble spawning
def spawn_bubbles_update(): # Call this in main update loop
    global bubble_timer
    if not player or not world: return
    
    # Check if player's head is in water
    player_head_y = player.y + player.height - 0.1 # Approximate head position
    if world.get_block((floor(player.x), floor(player_head_y), floor(player.z))) == 'water':
        bubble_timer += time.dt
        if bubble_timer > 0.5: # Spawn bubbles every 0.5 seconds
            bubble_timer = 0
            for _ in range(random.randint(1,3)): # Spawn 1 to 3 bubbles
                # Spawn bubbles near player's camera/head
                spawn_pos_bubbles = player.camera_pivot.world_position +                                     player.camera_pivot.forward * random.uniform(0.1, 0.5) +                                     Vec3(random.uniform(-0.3,0.3), 
                                         random.uniform(-0.2,0.2), 
                                         random.uniform(-0.3,0.3))
                BubbleParticle(spawn_pos_bubbles)


#############################################
# 11) Debris and Pickup Items
#############################################
class Debris(Entity): # Visual effect for block breaking
    def __init__(self, block_world_position, block_type_debris):
        # Ensure texture exists for debris, fallback if not
        debris_texture = texture_mapping.get(block_type_debris, stone_texture) 
        
        super().__init__(model='cube', texture=debris_texture,
                         scale=random.uniform(0.05, 0.15),
                         position=Vec3(*block_world_position) + Vec3(0.5,0.5,0.5)) # Center of block
        
        self.start_time_debris = time.time()
        self.lifetime_debris = random.uniform(0.8, 1.5) # Shorter lifetime for debris
        
        # Initial velocity outwards from block center
        self.velocity_debris = Vec3(random.uniform(-2,2),
                                    random.uniform(2,5), # Upwards pop
                                    random.uniform(-2,2))
        self.angular_velocity_debris = Vec3(random.uniform(-180,180),
                                            random.uniform(-180,180),
                                            random.uniform(-180,180))
        self.gravity_debris = 9.8

    def update(self):
        dt_debris = time.dt
        
        # Basic physics: gravity and velocity
        self.velocity_debris.y -= self.gravity_debris * dt_debris
        self.position += self.velocity_debris * dt_debris
        
        # Rotation
        self.rotation_x += self.angular_velocity_debris.x * dt_debris
        self.rotation_y += self.angular_velocity_debris.y * dt_debris
        self.rotation_z += self.angular_velocity_debris.z * dt_debris
        
        # Lifetime check
        if time.time() - self.start_time_debris > self.lifetime_debris:
            destroy(self)

class PickupItem(Entity): # Item that can be collected by player
    def __init__(self, item_type_pickup, world_position_pickup):
        pickup_texture = texture_mapping.get(item_type_pickup, stone_texture) # Fallback texture
        
        super().__init__(parent=scene, model='cube', texture=pickup_texture,
                         scale=0.25, # Slightly larger than debris
                         position=Vec3(*world_position_pickup) + Vec3(0.5,0.5,0.5), # Center of block
                         collider='box' # Add collider for raycast or collision based pickup
                        )
        self.item_type_pickup = item_type_pickup
        self.velocity_pickup = Vec3(random.uniform(-0.5,0.5), 2, random.uniform(-0.5,0.5)) # Slight pop up
        self.gravity_pickup = 9.8
        self.pickup_radius_sq = 1.5**2 # Radius for player to pick up (squared for efficiency)
        self.lifetime_pickup = 45.0 # Longer lifetime for pickups (e.g., 45 seconds)
        self.spawn_time_pickup = time.time()
        self.grounded_pickup = False

    def update(self):
        dt_pickup = time.dt

        if not self.grounded_pickup:
            self.velocity_pickup.y -= self.gravity_pickup * dt_pickup
            self.position += self.velocity_pickup * dt_pickup
            
            # Simple ground collision check (assuming ground is around y=integer levels)
            # This would be more robust with raycasting or checking actual block below
            block_below_pos = (floor(self.position.x), floor(self.position.y - 0.1), floor(self.position.z))
            if world.get_block(block_below_pos) is not None:
                self.position.y = floor(self.position.y) + 0.25 # Settle on ground (adjust 0.25 to half of scale)
                self.grounded_pickup = True
                self.velocity_pickup = Vec3(0,0,0) # Stop movement

        # Bobbing animation when grounded
        if self.grounded_pickup:
            self.rotation_y += 30 * dt_pickup # Gentle rotation
            self.position.y = floor(self.position.y) + 0.25 + sin(time.time() * 2) * 0.05 # Bobbing

        # Lifetime check
        if time.time() - self.spawn_time_pickup > self.lifetime_pickup:
            destroy(self)
            return
        
        # Player pickup check
        if player and distance_xz_sq(self.world_position, player.world_position) < self.pickup_radius_sq:
            # Check Y distance as well
            if abs(self.world_position.y - (player.world_position.y + player.height/2)) < player.height:
                if add_item_to_inventory(self.item_type_pickup):
                    destroy(self) # Item picked up

def distance_xz_sq(pos1, pos2): # Helper for squared XZ distance
    return (pos1.x - pos2.x)**2 + (pos1.z - pos2.z)**2


def add_item_to_inventory(item_type_to_add):
    global inventory_ui
    if not inventory_ui: return False

    # Try to stack in hotbar first
    for i in range(len(inventory_ui.hotbar_data)):
        slot = inventory_ui.hotbar_data[i]
        if slot and slot.get('item') == item_type_to_add and slot.get('count', 0) < 100:
            slot['count'] += 1
            inventory_ui.update_all_slots()
            return True
    # Try to add to empty hotbar slot
    for i in range(len(inventory_ui.hotbar_data)):
        if inventory_ui.hotbar_data[i] is None:
            inventory_ui.hotbar_data[i] = {'item': item_type_to_add, 'count': 1}
            inventory_ui.update_all_slots()
            return True
            
    # Try to stack in main inventory
    for i in range(len(inventory_ui.inventory_data)):
        slot = inventory_ui.inventory_data[i]
        if slot and slot.get('item') == item_type_to_add and slot.get('count', 0) < 100:
            slot['count'] += 1
            inventory_ui.update_all_slots()
            return True
    # Try to add to empty main inventory slot
    for i in range(len(inventory_ui.inventory_data)):
        if inventory_ui.inventory_data[i] is None:
            inventory_ui.inventory_data[i] = {'item': item_type_to_add, 'count': 1}
            inventory_ui.update_all_slots()
            return True
            
    print(f"Inventory full. Cannot pick up {item_type_to_add}.")
    return False

def spawn_pickup(item_type_to_spawn, block_world_pos_spawn):
    # Spawn slightly above the block's original position
    pickup_spawn_pos = (block_world_pos_spawn[0], block_world_pos_spawn[1] + 0.5, block_world_pos_spawn[2])
    PickupItem(item_type_to_spawn, pickup_spawn_pos)


#############################################
# Helper Class: SlotOutline
#############################################
class SlotOutline(Entity):
    def __init__(self, parent, thickness=0.01, outline_color=color.lime, **kwargs):
        super().__init__(parent=parent, **kwargs) # Pass kwargs to Entity
        self.thickness = thickness
        self.outline_color = outline_color
        # Create border parts, ensure Z is behind slot content slightly if needed
        z_offset_border = -0.01 
        self.top_border = Entity(parent=self, model='quad', color=self.outline_color, 
                                scale=(1, self.thickness), position=(0, 0.5 - self.thickness/2, z_offset_border), origin=(0,0))
        self.bottom_border = Entity(parent=self, model='quad', color=self.outline_color, 
                                   scale=(1, self.thickness), position=(0, -0.5 + self.thickness/2, z_offset_border), origin=(0,0))
        self.left_border = Entity(parent=self, model='quad', color=self.outline_color, 
                                 scale=(self.thickness, 1 - 2*self.thickness), position=(-0.5 + self.thickness/2, 0, z_offset_border), origin=(0,0))
        self.right_border = Entity(parent=self, model='quad', color=self.outline_color, 
                                  scale=(self.thickness, 1 - 2*self.thickness), position=(0.5 - self.thickness/2, 0, z_offset_border), origin=(0,0))
        # Scale the SlotOutline itself to match the slot size it outlines
        self.scale = (0.11, 0.11) # Match InventorySlotUI scale by default


#############################################
# 12) Inventory UI System (Hotbar + Main Inventory)
#############################################
class InventorySlotUI(Button):
    def __init__(self, slot_data_ref, **kwargs): # slot_data_ref is a direct reference to the list item
        super().__init__(model='quad', **kwargs)
        self.slot_data_ref = slot_data_ref # Store reference to the actual data slot
        self.scale = (0.1, 0.1) # Slightly smaller for padding if outline is parent
        self.background_color = color.rgba(0,0,0,150) # Default background
        self.texture_scale = (0.9,0.9) # Scale texture within the slot
        self.count_text_label = None
        self.update_visual()

    def update_visual(self):
        current_data = self.slot_data_ref() # Call the lambda to get current data
        
        if current_data and current_data.get('item'):
            item_texture_visual = texture_mapping.get(current_data['item'])
            self.texture = item_texture_visual if item_texture_visual else None # Use texture if found
            self.color = color.white if item_texture_visual else color.gray # Gray if no texture
            
            item_count_visual = current_data.get('count', 1)
            if self.count_text_label: # Destroy old text if it exists
                destroy(self.count_text_label)
                self.count_text_label = None

            if item_count_visual > 1: # Only show count if more than 1
                self.count_text_label = Text(
                    text=str(item_count_visual),
                    parent=self, # Parent to the slot itself
                    origin=(0.5, -0.5), # Bottom-right alignment within slot
                    scale=3, # Scale relative to slot's own scale
                    position=(0.45, -0.45), # Position in bottom-right
                    z = -0.1, # Ensure text is on top
                    color=color.yellow
                )
        else: # Slot is empty
            self.texture = None
            self.color = color.rgba(0,0,0,150) # Empty slot color
            if self.count_text_label:
                destroy(self.count_text_label)
                self.count_text_label = None
        
        # self.border_color = color.white # Default border for Button, can be customized

class InventoryUI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui) # Main container for all inventory UI
        
        # Data for hotbar (9 slots) and main inventory (27 slots)
        self.hotbar_data = [None for _ in range(9)]
        self.inventory_data = [None for _ in range(27)] # 3 rows of 9

        self.hotbar_elements_ui = [] # Ursina Button entities for hotbar
        self.inventory_elements_ui = [] # Ursina Button entities for main inventory

        hotbar_y_pos = -0.45
        slot_size_ui = 0.10
        slot_spacing_ui = 0.01
        total_slot_dim_ui = slot_size_ui + slot_spacing_ui

        # Create Hotbar UI
        for i in range(9):
            pos_x_hotbar = (-4 * total_slot_dim_ui) + (i * total_slot_dim_ui) # Centered hotbar
            # Pass a lambda that gets the current data for this slot
            slot_ui_hotbar = InventorySlotUI(lambda i=i: self.hotbar_data[i], 
                                             parent=self, position=(pos_x_hotbar, hotbar_y_pos), scale=slot_size_ui)
            self.hotbar_elements_ui.append(slot_ui_hotbar)

        self.hotbar_selected_index = 0
        # Highlight for selected hotbar slot
        self.hotbar_highlight_ui = Entity(parent=self, model='quad', color=color.rgba(255,255,0,100), 
                                        scale=(slot_size_ui*1.1, slot_size_ui*1.1), z=0.1) # Slightly behind slots
        self.update_hotbar_highlight_pos()


        # Main Inventory Panel (initially disabled)
        self.inventory_panel_ui = Entity(parent=camera.ui, scale=(total_slot_dim_ui * 9.5, total_slot_dim_ui * 3.5),
                                        color=color.rgba(50,50,50,200), enabled=False) # Dark semi-transparent panel
        
        # Create Main Inventory UI Slots (parented to inventory_panel_ui)
        start_x_inv = - (total_slot_dim_ui * 9 / 2) + slot_size_ui / 2 
        start_y_inv = (total_slot_dim_ui * 3 / 2) - slot_size_ui / 2 - total_slot_dim_ui * 0.2 # Adjust Y to be within panel

        for i in range(27):
            row_inv = i // 9
            col_inv = i % 9
            pos_x_inv = start_x_inv + col_inv * total_slot_dim_ui
            pos_y_inv = start_y_inv - row_inv * total_slot_dim_ui
            slot_ui_inv = InventorySlotUI(lambda i=i: self.inventory_data[i],
                                          parent=self.inventory_panel_ui, position=(pos_x_inv, pos_y_inv), scale=slot_size_ui)
            self.inventory_elements_ui.append(slot_ui_inv)
            
        self.dragged_item_data = None # Holds {'item': type, 'count': num}
        self.dragged_item_origin_is_hotbar = False # True if from hotbar, False if from main inv
        self.dragged_item_origin_idx = -1
        self.drag_icon_ui = None # Entity for visual drag icon
        self.inventory_open_state = False # Tracks if main inventory is open

    def update_hotbar_highlight_pos(self):
         # Position highlight over the selected hotbar slot
        selected_slot_entity = self.hotbar_elements_ui[self.hotbar_selected_index]
        self.hotbar_highlight_ui.position = selected_slot_entity.position
        self.hotbar_highlight_ui.z = selected_slot_entity.z + 0.01 # Ensure highlight is slightly behind slot content

    def toggle_inventory(self):
        self.inventory_open_state = not self.inventory_open_state
        self.inventory_panel_ui.enabled = self.inventory_open_state
        
        if self.inventory_open_state:
            if player: player.disable()
            mouse.locked = False
            mouse.visible = True
            self.update_all_slots() # Refresh visuals when opening
        else: # Closing inventory
            if player: player.enable()
            mouse.locked = True
            mouse.visible = False
            # If an item was being dragged, return it to origin or find new slot
            if self.dragged_item_data:
                self.return_dragged_item() 


    def update_all_slots(self): # Call to refresh all slot visuals
        for slot_widget in self.hotbar_elements_ui:
            slot_widget.update_visual()
        for slot_widget in self.inventory_elements_ui:
            slot_widget.update_visual()
        self.update_hotbar_highlight_pos()


    def update(self): # Main update for InventoryUI (e.g., drag icon position)
        if self.inventory_open_state: # Only update drag icon if inventory is open
            if self.dragged_item_data:
                if not self.drag_icon_ui: # Create drag icon if it doesn't exist
                    item_tex = texture_mapping.get(self.dragged_item_data['item'])
                    self.drag_icon_ui = Entity(parent=camera.ui, model='quad', 
                                               texture=item_tex if item_tex else None,
                                               color=color.white if item_tex else color.dark_gray,
                                               scale=(0.08, 0.08), z=-0.2) # Ensure on top
                    self.drag_icon_ui.ignore = True # So it doesn't block hovering other slots
                
                # Update drag icon texture if item changed (shouldn't happen mid-drag)
                # self.drag_icon_ui.texture = texture_mapping.get(self.dragged_item_data['item'])
                self.drag_icon_ui.position = mouse.position # Follow mouse
            else: # No item being dragged
                if self.drag_icon_ui: # Destroy icon if it exists
                    destroy(self.drag_icon_ui)
                    self.drag_icon_ui = None
        elif self.drag_icon_ui : # Inventory closed but drag icon exists (shouldn't happen if return_dragged_item works)
             destroy(self.drag_icon_ui)
             self.drag_icon_ui = None


    def handle_click_on_slot(self, slot_list_data, slot_idx, is_hotbar_list):
        clicked_slot_current_data = slot_list_data[slot_idx]

        if not self.dragged_item_data: # Not dragging anything -> Pick up from this slot
            if clicked_slot_current_data: # If slot has an item
                self.dragged_item_data = clicked_slot_current_data.copy() # Take the whole stack
                slot_list_data[slot_idx] = None # Empty the clicked slot
                self.dragged_item_origin_is_hotbar = is_hotbar_list
                self.dragged_item_origin_idx = slot_idx
        else: # Currently dragging an item -> Try to place in this slot
            if not clicked_slot_current_data: # Target slot is empty
                slot_list_data[slot_idx] = self.dragged_item_data # Place whole stack
                self.dragged_item_data = None # Item placed
            else: # Target slot has an item -> Try to stack or swap
                if clicked_slot_current_data['item'] == self.dragged_item_data['item']: # Same item type
                    can_take = 100 - clicked_slot_current_data['count']
                    if can_take > 0:
                        take_amount = min(can_take, self.dragged_item_data['count'])
                        clicked_slot_current_data['count'] += take_amount
                        self.dragged_item_data['count'] -= take_amount
                        if self.dragged_item_data['count'] <= 0:
                            self.dragged_item_data = None # All of dragged item stacked
                else: # Different item types -> Swap
                    # Store target slot's item temporarily
                    temp_item_from_target_slot = clicked_slot_current_data.copy()
                    # Place dragged item into target slot
                    slot_list_data[slot_idx] = self.dragged_item_data
                    # Now, the item originally from target slot becomes the new dragged item
                    self.dragged_item_data = temp_item_from_target_slot
                    # Origin of this new dragged item is the slot we just interacted with
                    self.dragged_item_origin_is_hotbar = is_hotbar_list
                    self.dragged_item_origin_idx = slot_idx
        self.update_all_slots()


    def return_dragged_item(self):
        if self.dragged_item_data:
            origin_list = self.hotbar_data if self.dragged_item_origin_is_hotbar else self.inventory_data
            
            if origin_list[self.dragged_item_origin_idx] is None: # Original slot is still empty
                origin_list[self.dragged_item_origin_idx] = self.dragged_item_data
            else: # Original slot was filled, try to add to any empty slot or stack
                if not add_item_to_inventory(self.dragged_item_data['item']): # This needs to handle count too
                    # If cannot add (e.g. full), for now, just drop it (log it)
                    print(f"Could not return dragged item {self.dragged_item_data['item']} to inventory. Item lost (or implement drop).")

            self.dragged_item_data = None
            if self.drag_icon_ui:
                destroy(self.drag_icon_ui)
                self.drag_icon_ui = None
            self.update_all_slots()


    def input(self, key): # Input handling when inventory is open
        if not self.inventory_open_state: return

        if key == 'left mouse down':
            # Check hotbar slots
            for i, slot_widget in enumerate(self.hotbar_elements_ui):
                if slot_widget.hovered:
                    self.handle_click_on_slot(self.hotbar_data, i, True)
                    return 
            # Check main inventory slots
            for i, slot_widget in enumerate(self.inventory_elements_ui):
                if slot_widget.hovered:
                    self.handle_click_on_slot(self.inventory_data, i, False)
                    return
            # If clicked outside any slot and dragging an item, return it
            if self.dragged_item_data and not mouse.hovered_entity:
                 self.return_dragged_item()

        elif key == 'right mouse down':
            if self.dragged_item_data: # If dragging a stack, try to place one item
                target_slot_widget = None
                target_list_data = None
                target_idx = -1
                is_hotbar_target = False

                for i, slot_widget in enumerate(self.hotbar_elements_ui):
                    if slot_widget.hovered:
                        target_slot_widget = slot_widget; target_list_data = self.hotbar_data; 
                        target_idx = i; is_hotbar_target = True; break
                if not target_slot_widget:
                    for i, slot_widget in enumerate(self.inventory_elements_ui):
                        if slot_widget.hovered:
                            target_slot_widget = slot_widget; target_list_data = self.inventory_data; 
                            target_idx = i; is_hotbar_target = False; break
                
                if target_slot_widget:
                    if target_list_data[target_idx] is None: # Target is empty
                        target_list_data[target_idx] = {'item': self.dragged_item_data['item'], 'count': 1}
                        self.dragged_item_data['count'] -= 1
                    elif target_list_data[target_idx]['item'] == self.dragged_item_data['item'] and                          target_list_data[target_idx]['count'] < 100: # Target has same item, can stack
                        target_list_data[target_idx]['count'] += 1
                        self.dragged_item_data['count'] -= 1
                    
                    if self.dragged_item_data['count'] <= 0:
                        self.dragged_item_data = None # All items placed one by one
                    self.update_all_slots()


#############################################
# 13) Custom Player with New Swimming Logic
#############################################
class CustomPlayer(FirstPersonController):
    def __init__(self):
        super().__init__(model="character.glb", jump_height=1.5, speed=8, jump_duration=0.4) # Tuned jump
        self.collider = BoxCollider(self, center=Vec3(0,1,0), size=Vec3(0.8,1.8,0.8)) # Standard player size
        self.cursor.visible = False # Hide default FPC cursor if using custom UI

        self.last_click_time = 0 # For block interaction cooldown
        # Third person camera setup
        self.is_third_person = False
        self.default_cam_pivot_pos = self.camera_pivot.position.y # Store original height
        self.third_person_cam_dist = 5 
        self.third_person_cam_height = 1.0 

        # Swimming related attributes
        self.in_water = False
        self.was_in_water = False # To detect entry/exit
        self.buoyancy_force = 12.0 # Upward force in water
        self.water_friction = 3.0  # Resistance in water - Renamed for clarity
        self.swim_move_force = 300.0 # Force for swimming movement
        self.max_swim_speed_vertical = 2.0 # Max speed for bobbing/sinking
        self.max_swim_speed_horizontal = 4.0 # Max speed for horizontal swimming


    def update(self):
        # Player dimensions based on BoxCollider(center=Vec3(0,1,0), size=Vec3(0.6,2,0.6))
        # Player's feet are at self.y, player's head top is at self.y + 2.0.
        player_height = 2.0

        # Upward clipping check
        if hasattr(self, 'velocity') and self.velocity.y > 0: # Check if FPC uses self.velocity
            target_head_top_y = self.y + player_height + (self.velocity.y * time.dt)
            potential_ceiling_block_y = floor(target_head_top_y)
            block_at_potential_ceiling = world.get_block((floor(self.x), potential_ceiling_block_y, floor(self.z)))

            if block_at_potential_ceiling and block_at_potential_ceiling != 'water':
                current_head_top_y = self.y + player_height
                if current_head_top_y <= potential_ceiling_block_y:
                    self.y = potential_ceiling_block_y - player_height - 0.01 # 0.01 is an epsilon
                    self.velocity.y = 0 # Stop upward movement
        
        # --- Water Physics ---
        self.check_water_status() # Updates self.in_water

        if self.in_water:
            if not self.was_in_water: # Just entered water
                if waterjump_sound: waterjump_sound.play()
                self.velocity.y *= 0.3 # Dampen vertical speed on entry
            
            # Apply buoyancy (counteracts gravity)
            self.velocity.y += self.buoyancy_force * time.dt
            # Apply water drag (dampens all movement)
            self.velocity.x *= (1 - self.water_friction * time.dt)
            self.velocity.y *= (1 - self.water_friction * time.dt * 0.5) # Less Y drag than buoyancy
            self.velocity.z *= (1 - self.water_friction * time.dt)

            # Limit vertical speed in water (bobbing/sinking)
            if abs(self.velocity.y) > self.max_swim_speed_vertical:
                self.velocity.y = self.max_swim_speed_vertical * sign(self.velocity.y)

            # Swimming controls
            if held_keys['space']: # Swim up
                self.velocity.y += self.swim_move_force * 0.05 * time.dt # Adjusted force application
            # Forward/backward/sideways swimming (uses FPC's direction calculation)
            # Need to apply force based on player's facing direction
            # This part is tricky as FPC applies velocity directly.
            # We might need to adjust FPC's ground_control or air_control when in water.
            # For now, let's allow FPC's movement but heavily damped by drag.
            # A more advanced approach would be custom movement logic here.
            
        self.was_in_water = self.in_water
        
        # --- Call base FPC update AFTER water physics modifications ---
        # Modify gravity for FPC based on water status for THIS frame
        original_gravity = self.gravity
        if self.in_water:
            self.gravity = original_gravity * UNDERWATER_GRAVITY_FACTOR # Reduced gravity in water
        
        super().update() # This applies gravity, movement according to FPC logic
        
        self.gravity = original_gravity # Restore original gravity for next frame's logic

        # Head-knocker prevention (reactive, after super().update())
        # Player feet at self.y, head top at self.y + player_height (2.0)
        player_height = 2.0 # Define it again in case it's needed locally
        
        head_check_world_y = self.y + player_height - 0.1 
        head_block_coord = (floor(self.x), floor(head_check_world_y), floor(self.z))
        block_at_head = world.get_block(head_block_coord)

        if block_at_head and block_at_head != 'water':
            feet_check_world_y = self.y + 0.1 
            feet_block_coord = (floor(self.x), floor(feet_check_world_y), floor(self.z))
            block_at_feet = world.get_block(feet_block_coord)

            if not block_at_feet or block_at_feet == 'water':
                if hasattr(self, 'previous_position') and self.previous_position != self.position:
                    self.position = self.previous_position
                else:
                    self.y = floor(head_check_world_y) - player_height - 0.01

                if hasattr(self, 'velocity') and self.velocity.y > 0:
                     self.velocity.y = 0
        
        # --- Camera Perspective ---
        if self.is_third_person:
            target_cam_pos = self.position + Vec3(0, self.third_person_cam_height, 0) - (self.forward * self.third_person_cam_dist)
            # Simple obstacle avoidance for camera (raycast from player to target_cam_pos)
            cam_hit = raycast(self.world_position + Vec3(0,self.height/2,0) , (target_cam_pos - self.world_position).normalized(), 
                              distance=self.third_person_cam_dist, ignore=[self])
            if cam_hit.hit:
                self.camera_pivot.world_position = lerp(self.camera_pivot.world_position, cam_hit.world_point - self.forward*0.2, time.dt * 10)
            else:
                self.camera_pivot.world_position = lerp(self.camera_pivot.world_position, target_cam_pos, time.dt * 10)
            self.camera_pivot.rotation_x = self.rotation_x # Match player pitch
        else: # First person
            self.camera_pivot.position = Vec3(0, self.default_cam_pivot_pos, 0) # Reset to default relative pos
        
        # Fall damage (example, can be expanded)
        if self.air_time > self.jump_duration + 0.3 and self.velocity.y < -10: # If falling fast after jump peak
            # print(f"High fall, velocity Y: {self.velocity.y}")
            # Implement fall damage logic here
            pass


    def check_water_status(self):
        if not world: self.in_water = False; return

        # Check points around player for water contact
        # Feet, waist, head level checks
        positions_to_check = [
            self.position + Vec3(0, 0.1, 0),  # Feet
            self.position + Vec3(0, self.height * 0.5, 0), # Waist
            self.position + Vec3(0, self.height * 0.9, 0)  # Head
        ]
        self.in_water = False
        for pos_w_check in positions_to_check:
            block_at_pos = world.get_block((floor(pos_w_check.x), floor(pos_w_check.y), floor(pos_w_check.z)))
            if block_at_pos == 'water':
                self.in_water = True
                break
    
    def input(self, key): # Player specific inputs (like camera toggle)
        super().input(key) # Allow FPC to handle its inputs (movement, jump)
        if key == 'f5': # Toggle camera perspective
            self.is_third_person = not self.is_third_person
            if self.is_third_person:
                self.camera_pivot.parent = scene # Detach from player's direct rotation for smoothing
            else:
                self.camera_pivot.parent = self # Re-attach for first person
                self.camera_pivot.rotation = (0,0,0) # Reset local rotation


#############################################
# 14) Free Camera
#############################################
free_cam_mode = False
free_cam = None # Will hold the EditorCamera instance
class CustomEditorCamera(EditorCamera): # Inherit for any customizations
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = 20 # Faster default speed
        self.zoom_speed = 1 # Keep zoom speed reasonable

    def update(self): # EditorCamera has its own update, call it
        super().update() 
        # Add custom controls if needed, e.g., shift for speed boost
        current_speed = self.speed
        if held_keys['left shift'] or held_keys['right shift']:
            current_speed *= 3
        
        # Movement relative to camera's own orientation
        if held_keys['w']: self.position += self.forward * current_speed * time.dt
        if held_keys['s']: self.position -= self.forward * current_speed * time.dt
        if held_keys['d']: self.position += self.right * current_speed * time.dt
        if held_keys['a']: self.position -= self.right * current_speed * time.dt
        if held_keys['e'] or held_keys['space']: self.position += self.up * current_speed * time.dt # Move up
        if held_keys['q'] or held_keys['c']: self.position -= self.up * current_speed * time.dt     # Move down


def toggle_free_camera():
    global free_cam_mode, free_cam, player
    
    free_cam_mode = not free_cam_mode
    if free_cam_mode:
        if player: player.disable() # Disable player when free cam is on
        if not free_cam: # Create free_cam if it doesn't exist
            free_cam = CustomEditorCamera(rotation_speed=200, enabled=True)
        free_cam.enabled = True
        free_cam.position = player.camera_pivot.world_position if player else camera.position
        free_cam.rotation = player.camera_pivot.world_rotation if player else camera.rotation
        mouse.locked = False # Unlock mouse for free cam
        mouse.visible = True
        print("Free Camera Activated.")
    else: # Turning free cam OFF
        if free_cam: free_cam.disable()
        if player: 
            player.enable() # Re-enable player
            mouse.locked = True
            mouse.visible = False
        else: # No player, just revert mouse state
            mouse.locked = False 
            mouse.visible = True
        print("Free Camera Deactivated.")


#############################################
# 15) Simplified Water Functions (debug_init_water_entity, update_water_mesh)
# These are now OBSOLETE due to combined mesh in Chunk.build_mesh()
# They can be safely removed or commented out.
#############################################

#############################################
# 16) Voxel World Classes (Chunk, World, etc.)
#############################################
from math import ceil # Added for atlas calculation

# Global constant for terrain generation, can be tuned
BIOME_NOISE_FREQUENCY = 0.008 # Controls the size of biomes

def generate_terrain_height(x, z, seed, max_terrain_height): # Renamed for clarity
    base_freq_height = 0.012
    hill_freq_height = 0.04
    detail_freq_height = 0.08
    
    # Multiple noise layers for more interesting height variation
    base_noise = pnoise2(x * base_freq_height, z * base_freq_height, octaves=2, persistence=0.5, lacunarity=2.0, base=seed)
    hill_noise = pnoise2(x * hill_freq_height, z * hill_freq_height, octaves=3, persistence=0.4, lacunarity=2.0, base=seed + 1)
    detail_noise = pnoise2(x * detail_freq_height, z * detail_freq_height, octaves=4, persistence=0.3, lacunarity=2.0, base=seed + 2)
    
    # Combine noise layers with different weights
    # base_noise is usually -1 to 1. Scale to 0-1 for combining.
    combined_noise = ( (base_noise + 1)/2 * 0.6 +    # Base terrain shape
                       (hill_noise + 1)/2 * 0.3 +    # Hills and valleys
                       (detail_noise + 1)/2 * 0.1 )  # Finer details
    
    # Apply a non-linear transformation (e.g., power) to shape terrain
    # Power > 1 flattens valleys and sharpens peaks. Power < 1 does opposite.
    shaped_noise = combined_noise ** 1.2 # Experiment with this value
    
    # Scale to desired max_terrain_height
    # Ensure minimum height (e.g., at least 1 block above world bottom if using -max_height)
    # Let's assume height is relative to y=0 for simplicity here.
    # So, final height is how many blocks *above* y=0.
    calculated_height = floor(shaped_noise * max_terrain_height)
    
    # Ensure height is at least a minimum, e.g. 1, so there's always a ground layer
    # This depends on how y-coordinates are handled (0 as sea level vs. 0 as world bottom)
    # If max_terrain_height is the height *above* a base_level (e.g. y=0 is water plane)
    final_height = max(1, calculated_height) 
    return final_height


class Chunk:
    def __init__(self, world_ref, chunk_pos, generate_terrain_on_init=True): # Renamed arg
        self.world = world_ref # Reference to the VoxelWorld instance
        self.chunk_pos = chunk_pos # Base position of this chunk (e.g., (0,0), (16,0))
        self.blocks = {} # Dictionary to store blocks: (world_x,y,z) -> block_type_string

        # Combined mesh entity for opaque terrain using a texture atlas
        self.opaque_terrain_entity = Entity(model=None, collider='mesh', shader=block_lighting_shader,
                                            texture='atlas_texture.png', static=True)
        
        # Entity for water (transparent blocks)
        self.water_entity = Entity(model=None, texture=water_texture, 
                                   color=color.rgba(60,120,255,180), # Water color and alpha
                                   double_sided=True, transparency=True, static=True)
       
        if generate_terrain_on_init:
            self.generate_terrain()

    def generate_terrain(self):
        seed = 42 # World seed
        max_height_gen = 30  # Max height of terrain generation from y=0
        water_level_gen = 10 # Y-level for water surface
        
        # Use the global BIOME_NOISE_FREQUENCY
        biome_freq_local = BIOME_NOISE_FREQUENCY 

        for x_offset_chunk in range(CHUNK_SIZE):
            for z_offset_chunk in range(CHUNK_SIZE):
                wx = self.chunk_pos[0] + x_offset_chunk # World X
                wz = self.chunk_pos[1] + z_offset_chunk # World Z

                # Generate terrain height for this column (relative to y=0)
                terrain_column_height = generate_terrain_height(wx, wz, seed, max_height_gen)
                
                # Biome determination based on noise (temperature, humidity) and height
                temp_noise_val = (pnoise2(wx * biome_freq_local, wz * biome_freq_local, octaves=2, base=seed + 10) + 1) / 2 # 0-1
                humidity_noise_val = (pnoise2(wx * biome_freq_local, wz * biome_freq_local, octaves=2, base=seed + 20) + 1) / 2 # 0-1

                current_biome_name = "plains" # Default
                top_block_terrain = "grass"
                surface_material_terrain = "dirt"
                underwater_ground_material = "sand" # Default for under water bodies

                # --- Biome Logic ---
                # Mountainous terrain (high elevation)
                if terrain_column_height > max_height_gen * 0.65: 
                    current_biome_name = "mountains"
                    if temp_noise_val < 0.35: # Cold high mountains -> Snow
                        top_block_terrain = "snow"
                        surface_material_terrain = "snow" # Snow all the way down a bit
                    else: # Rocky mountains
                        top_block_terrain = "stone"
                        surface_material_terrain = "stone"
                # Desert (hot and dry, not too high)
                elif temp_noise_val > 0.7 and humidity_noise_val < 0.3 and terrain_column_height <= max_height_gen * 0.5:
                    current_biome_name = "desert"
                    top_block_terrain = "sand"
                    surface_material_terrain = "sandstone" # Or just more 'sand'
                # Forest (moderate temp, high humidity, not too high)
                elif temp_noise_val > 0.35 and temp_noise_val < 0.75 and humidity_noise_val > 0.55 and terrain_column_height <= max_height_gen * 0.6:
                    current_biome_name = "forest"
                    top_block_terrain = "grass" # Could be 'forest_floor' or 'podzol'
                    surface_material_terrain = "dirt"
                # Plains (default for moderate conditions)
                else: 
                    current_biome_name = "plains"
                    top_block_terrain = "grass"
                    surface_material_terrain = "dirt"

                # Beach areas if land is near water level (and not a mountain)
                if terrain_column_height > water_level_gen -1 and terrain_column_height <= water_level_gen + 2                     and current_biome_name not in ["mountains", "desert"]: # Beaches don't form on steep mountains
                    current_biome_name = "beach" # Override biome if it's a beach
                    top_block_terrain = "sand"
                    surface_material_terrain = "sand"


                # --- Block Placement Loop (from world bottom up to terrain_column_height) ---
                # Assuming world bottom is at y = -max_height_gen or some negative value.
                # For simplicity, let's assume y=0 is a base reference, and terrain goes above/below.
                # Let's define world_bottom_y for clarity.
                world_bottom_y = -max_height_gen // 2 # Example: terrain can go down to -15 if max_height_gen is 30

                for y_current in range(world_bottom_y, terrain_column_height):
                    if y_current == terrain_column_height - 1: # Topmost block of the land
                        self.blocks[(wx, y_current, wz)] = top_block_terrain
                    elif y_current >= terrain_column_height - 4: # Surface layer (3 blocks below top)
                        self.blocks[(wx, y_current, wz)] = surface_material_terrain
                    else: # Deeper underground
                        self.blocks[(wx, y_current, wz)] = "stone"
                
                # --- Water Placement ---
                # Fill with water from terrain_column_height up to water_level_gen if terrain is below water level
                if terrain_column_height <= water_level_gen:
                    for y_water_fill in range(terrain_column_height, water_level_gen + 1):
                        # Place underwater ground material if this level was meant to be land but is now water due to biome context
                        if y_water_fill == terrain_column_height -1 and current_biome_name in ["ocean", "lake", "river"]: # A bit redundant, top_block would be this
                             self.blocks[(wx, y_water_fill, wz)] = underwater_ground_material
                        else: # Fill with water
                             self.blocks[(wx, y_water_fill, wz)] = "water"
                    # Ensure the block just below water surface (if it's land) is appropriate (e.g. sand for beach)
                    if self.blocks.get((wx, water_level_gen, wz)) == 'water' and                        current_biome_name == "beach": # If it's a beach and water is at water_level_gen
                        if self.blocks.get((wx, water_level_gen -1, wz)) != 'water': # and block below is land
                           self.blocks[(wx, water_level_gen -1, wz)] = "sand" # Make it sand


        self.carve_caves(seed) 
        self.place_ores_in_chunk(seed) # Call ore placement
        self.place_trees_in_chunk(seed, water_level_gen, max_height_gen) # Pass water_level for tree checks

    def place_ores_in_chunk(self, seed):
        ore_types_info = {
            'gold': {'texture': gold_texture, 'chance': 0.02, 'min_y': -25, 'max_y': 10, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 50},
            'emerald': {'texture': emerald_texture, 'chance': 0.015, 'min_y': -30, 'max_y': 5, 'host': ['stone'], 'noise_octaves': 2, 'noise_seed_offset': 60},
            'ruby': {'texture': ruby_texture, 'chance': 0.018, 'min_y': -28, 'max_y': 8, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 70}
        }
        ore_noise_freq = 0.08

        # Iterate over a copy of block positions as self.blocks might be modified
        block_positions = list(self.blocks.keys()) 
        for b_pos in block_positions:
            bx, by, bz = b_pos
            current_block = self.blocks.get(b_pos) # Use .get() for safety, though key should exist

            if current_block is None: # Skip if block was already removed (e.g. by cavegen)
                continue

            for ore_name, ore_data in ore_types_info.items():
                if current_block in ore_data['host']:
                    if ore_data['min_y'] <= by <= ore_data['max_y']:
                        # pnoise3 returns values between -1 and 1.
                        noise_val = pnoise3(bx * ore_noise_freq, 
                                            by * ore_noise_freq, 
                                            bz * ore_noise_freq, 
                                            octaves=ore_data['noise_octaves'], 
                                            base=seed + ore_data['noise_seed_offset'])
                        
                        # Normalize noise_val to be 0-1 for comparison with chance
                        normalized_noise_val = (noise_val + 1) / 2.0 
                        
                        # If chance is 0.02 (2%), we want to place ore if noise is in the top 2% of its range.
                        # So, if normalized_noise_val (0 to 1) is greater than (1.0 - 0.02) = 0.98.
                        if normalized_noise_val > (1.0 - ore_data['chance']):
                            self.blocks[b_pos] = ore_name
                            # The ore_name (e.g., 'gold') should already be in texture_mapping and collectible_blocks
                            # from the global setup. No need to add them here.
                            break # Ore placed, no need to check other ore types for this block position
    
    def place_ores_in_chunk(self, seed):
        ore_types_info = {
            'gold': {'texture': gold_texture, 'chance': 0.02, 'min_y': -25, 'max_y': 10, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 50},
            'emerald': {'texture': emerald_texture, 'chance': 0.015, 'min_y': -30, 'max_y': 5, 'host': ['stone'], 'noise_octaves': 2, 'noise_seed_offset': 60},
            'ruby': {'texture': ruby_texture, 'chance': 0.018, 'min_y': -28, 'max_y': 8, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 70}
        }
        ore_noise_freq = 0.08

        block_positions = list(self.blocks.keys()) # Iterate over a copy
        for b_pos in block_positions:
            bx, by, bz = b_pos
            current_block = self.blocks.get(b_pos)

            for ore_name, ore_data in ore_types_info.items():
                if current_block in ore_data['host']:
                    if ore_data['min_y'] <= by <= ore_data['max_y']:
                        # pnoise3 returns values between -1 and 1.
                        noise_val = pnoise3(bx * ore_noise_freq, 
                                            by * ore_noise_freq, 
                                            bz * ore_noise_freq, 
                                            octaves=ore_data['noise_octaves'], 
                                            base=seed + ore_data['noise_seed_offset'])
                        
                        # Normalize noise_val to be 0-1
                        normalized_noise_val = (noise_val + 1) / 2.0 
                        
                        if normalized_noise_val > (1.0 - ore_data['chance']):
                            self.blocks[b_pos] = ore_name
                            # Textures and collectible status are handled by global lists/dicts
                            break # Ore placed, move to next block position
    
    def place_ores_in_chunk(self, seed):
        ore_types_info = {
            'gold': {'texture': gold_texture, 'chance': 0.02, 'min_y': -25, 'max_y': 10, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 50},
            'emerald': {'texture': emerald_texture, 'chance': 0.015, 'min_y': -30, 'max_y': 5, 'host': ['stone'], 'noise_octaves': 2, 'noise_seed_offset': 60},
            'ruby': {'texture': ruby_texture, 'chance': 0.018, 'min_y': -28, 'max_y': 8, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 70}
        }
        ore_noise_freq = 0.08

        block_positions = list(self.blocks.keys()) # Iterate over a copy
        for b_pos in block_positions:
            bx, by, bz = b_pos
            current_block = self.blocks.get(b_pos)

            for ore_name, ore_data in ore_types_info.items():
                if current_block in ore_data['host']:
                    if ore_data['min_y'] <= by <= ore_data['max_y']:
                        # pnoise3 returns values between -1 and 1.
                        noise_val = pnoise3(bx * ore_noise_freq, 
                                            by * ore_noise_freq, 
                                            bz * ore_noise_freq, 
                                            octaves=ore_data['noise_octaves'], 
                                            base=seed + ore_data['noise_seed_offset'])
                        
                        # To use 'chance' as a direct probability (e.g., 0.02 for 2% chance),
                        # we can scale noise_val (which is -1 to 1) to a 0-1 range,
                        # and then check if a random number is less than the chance,
                        # potentially modulated by the noise value to create veins.
                        # A simpler approach for vein-like structures is to use a threshold on noise.
                        # If noise_val (raw, -1 to 1) is above a certain high threshold, place ore.
                        # The provided logic "noise_val > (1.0 - ore_data['chance'])" assumes noise_val is 0-1.
                        # Let's normalize noise_val to 0-1 for this.
                        normalized_noise_val = (noise_val + 1) / 2.0 # Now 0.0 to 1.0
                        
                        # The condition `normalized_noise_val > (1.0 - ore_data['chance'])` means:
                        # if chance is 0.02, then 1.0 - chance is 0.98. We need noise > 0.98.
                        # This makes ore very rare, which is often desired.
                        if normalized_noise_val > (1.0 - ore_data['chance']):
                            self.blocks[b_pos] = ore_name
                            # Global texture_mapping and collectible_blocks should already contain these ores.
                            break # Ore placed, no need to check other ore types for this block
    
    def place_ores_in_chunk(self, seed):
        ore_types_info = {
            'gold': {'texture': gold_texture, 'chance': 0.02, 'min_y': -25, 'max_y': 10, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 50},
            'emerald': {'texture': emerald_texture, 'chance': 0.015, 'min_y': -30, 'max_y': 5, 'host': ['stone'], 'noise_octaves': 2, 'noise_seed_offset': 60},
            'ruby': {'texture': ruby_texture, 'chance': 0.018, 'min_y': -28, 'max_y': 8, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 70}
        }
        ore_noise_freq = 0.08

        block_positions = list(self.blocks.keys()) # Iterate over a copy
        for b_pos in block_positions:
            bx, by, bz = b_pos
            current_block = self.blocks.get(b_pos)

            for ore_name, ore_data in ore_types_info.items():
                if current_block in ore_data['host']:
                    if ore_data['min_y'] <= by <= ore_data['max_y']:
                        noise_val = pnoise3(bx * ore_noise_freq, by * ore_noise_freq, bz * ore_noise_freq, 
                                            octaves=ore_data['noise_octaves'], base=seed + ore_data['noise_seed_offset'])
                        # Normalize noise_val to be 0-1 if it's not already (pnoise3 output is -1 to 1)
                        normalized_noise_val = (noise_val + 1) / 2 
                        
                        # Compare with chance. Higher chance means more ore.
                        # So if normalized_noise_val is very high (close to 1), it's more likely to pass the check.
                        # If ore_data['chance'] is 0.02, then we need noise > 0.98 for it to be ore.
                        # This seems reversed. Let's try: if normalized_noise_val < ore_data['chance']
                        # No, the original logic: noise_val > (1.0 - ore_data['chance']) is correct if noise_val is 0-1
                        # Let's stick to the brief's example: noise_val > (1.0 - ore_data['chance'])
                        # but ensure noise_val is in 0-1 range for this comparison.
                        # So, if pnoise3 gives -1 to 1, then (pnoise3_val + 1) / 2 gives 0 to 1.
                        if normalized_noise_val > (1.0 - ore_data['chance']):
                            self.blocks[b_pos] = ore_name
                            # Textures and collectible status should already be handled by global lists/dicts
                            break # Ore placed, move to next block position
    
    def place_ores_in_chunk(self, seed):
        ore_types_info = {
            'gold': {'texture': gold_texture, 'chance': 0.02, 'min_y': -25, 'max_y': 10, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 50},
            'emerald': {'texture': emerald_texture, 'chance': 0.015, 'min_y': -30, 'max_y': 5, 'host': ['stone'], 'noise_octaves': 2, 'noise_seed_offset': 60},
            'ruby': {'texture': ruby_texture, 'chance': 0.018, 'min_y': -28, 'max_y': 8, 'host': ['stone'], 'noise_octaves': 1, 'noise_seed_offset': 70}
        }
        ore_noise_freq = 0.08

        block_positions = list(self.blocks.keys()) # Iterate over a copy
        for b_pos in block_positions:
            bx, by, bz = b_pos
            current_block = self.blocks.get(b_pos)

            for ore_name, ore_data in ore_types_info.items():
                if current_block in ore_data['host']:
                    if ore_data['min_y'] <= by <= ore_data['max_y']:
                        noise_val = pnoise3(bx * ore_noise_freq, by * ore_noise_freq, bz * ore_noise_freq, 
                                            octaves=ore_data['noise_octaves'], base=seed + ore_data['noise_seed_offset'])
                        # Normalize noise_val to be 0-1 if it's not already (pnoise3 output is -1 to 1)
                        normalized_noise_val = (noise_val + 1) / 2 
                        
                        # Compare with chance. Higher chance means more ore.
                        # So if normalized_noise_val is very high (close to 1), it's more likely to pass the check.
                        # If ore_data['chance'] is 0.02, then we need noise > 0.98 for it to be ore.
                        # This seems reversed. Let's try: if normalized_noise_val < ore_data['chance']
                        # No, the original logic: noise_val > (1.0 - ore_data['chance']) is correct if noise_val is 0-1
                        # Let's stick to the brief's example: noise_val > (1.0 - ore_data['chance'])
                        # but ensure noise_val is in 0-1 range for this comparison.
                        # So, if pnoise3 gives -1 to 1, then (pnoise3_val + 1) / 2 gives 0 to 1.
                        if normalized_noise_val > (1.0 - ore_data['chance']):
                            self.blocks[b_pos] = ore_name
                            # Textures and collectible status should already be handled by global lists/dicts
                            break # Ore placed, move to next block position
    
    def carve_caves(self, seed):
        cave_noise_freq = 0.05 # Frequency of cave noise
        cave_threshold_val = 0.75 # Noise values above this become caves
        
        # To avoid carving surface too much, find approx surface Y for each column
        surface_y_map = {}
        for wx_cave in range(self.chunk_pos[0], self.chunk_pos[0] + CHUNK_SIZE):
            for wz_cave in range(self.chunk_pos[1], self.chunk_pos[1] + CHUNK_SIZE):
                max_y_col = -1000
                for y_col_check in range(30, -30, -1): # Scan a reasonable height range
                    if (wx_cave, y_col_check, wz_cave) in self.blocks and                        self.blocks[(wx_cave, y_col_check, wz_cave)] != 'water':
                        max_y_col = y_col_check
                        break
                if max_y_col > -1000:
                    surface_y_map[(wx_cave, wz_cave)] = max_y_col
        
        # Iterate through blocks that are 'stone' or 'dirt' (or biome specific like 'sandstone')
        # Create a copy of keys to iterate over, as self.blocks might change
        blocks_to_check_for_caves = list(self.blocks.keys())

        for b_pos_key in blocks_to_check_for_caves:
            bx, by, bz = b_pos_key
            current_block_type_cave = self.blocks.get(b_pos_key)

            if current_block_type_cave in ['stone', 'dirt', 'sandstone', 'snow']: # Blocks that can be carved
                # Protect surface layers (e.g., don't carve within 5 blocks of surface)
                surface_y_current_col = surface_y_map.get((bx,bz), by) # Default to current y if no surface found (should not happen)
                if by > surface_y_current_col - 6: 
                    continue

                # 3D Perlin noise for cave generation
                cave_noise_3d = pnoise3(bx * cave_noise_freq, 
                                        by * cave_noise_freq, 
                                        bz * cave_noise_freq, 
                                        octaves=2, base=seed + 30)
                
                if abs(cave_noise_3d) > cave_threshold_val: # abs() creates more tunnel-like caves
                    self.blocks[b_pos_key] = None # Carve out block (set to air)

    def is_near_water(self, pos, radius): # Helper to check if near water (used by old cavegen, might be useful)
        x_check,y_check,z_check = pos
        for dx_water_check in range(-radius, radius+1):
            for dy_water_check in range(-radius, radius+1):
                for dz_water_check in range(-radius, radius+1):
                    check_pos_water = (x_check+dx_water_check, y_check+dy_water_check, z_check+dz_water_check)
                    if self.blocks.get(check_pos_water) == 'water':
                        return True
        return False

    def place_ores_in_chunk(self, seed):
        ore_types_info = { # Define ore types, their rarity, depth, and host block
            'gold': {'texture': gold_texture, 'chance': 0.02, 'min_y': -25, 'max_y': 10, 'host': ['stone']},
            'emerald': {'texture': emerald_texture, 'chance': 0.015, 'min_y': -30, 'max_y': 5, 'host': ['stone']},
            'ruby': {'texture': ruby_texture, 'chance': 0.018, 'min_y': -28, 'max_y': 8, 'host': ['stone']}
            # Add more ores: 'coal', 'iron', 'diamond' with different params
        }
        ore_noise_freq = 0.08 # Frequency for ore vein noise

        # Iterate through stone blocks primarily for ore placement
        # Make a copy of block positions to iterate, as we might modify self.blocks
        block_positions_in_chunk = list(self.blocks.keys())

        for b_pos_ore in block_positions_in_chunk:
            bx_ore, by_ore, bz_ore = b_pos_ore
            current_block_for_ore = self.blocks.get(b_pos_ore)

            for ore_name, ore_data in ore_types_info.items():
                if current_block_for_ore in ore_data['host']: # Check if current block can host this ore
                    if ore_data['min_y'] <= by_ore <= ore_data['max_y']: # Check depth
                        # Use 3D Perlin noise to create ore veins/patches
                        ore_vein_noise = pnoise3(bx_ore * ore_noise_freq, 
                                                 by_ore * ore_noise_freq, 
                                                 bz_ore * ore_noise_freq, 
                                                 octaves=1, base=seed + 50 + hash(ore_name)%100) # Seed per ore
                        
                        if ore_vein_noise > (1.0 - ore_data['chance']): # Higher noise value = higher chance
                            self.blocks[b_pos_ore] = ore_name # Replace block with ore
                            # Add this ore to texture_mapping if not already (though it should be)
                            if ore_name not in texture_mapping:
                                texture_mapping[ore_name] = ore_data['texture']
                            if ore_name not in collectible_blocks:
                                collectible_blocks.append(ore_name)
                            break # Ore placed, no need to check other ore types for this block


    def place_trees_in_chunk(self, seed, current_water_level, current_max_height): # Pass relevant levels
        tree_seed_offset = seed + 200
        tree_density_noise_freq = 0.06 
        tree_placement_noise_freq = 0.12
        
        # Use global BIOME_NOISE_FREQUENCY for consistency
        biome_freq_tree = BIOME_NOISE_FREQUENCY
        
        min_tree_spacing_sq = 3**2 # Squared distance for faster checks

        placed_tree_locations = [] # Store (wx, wz) of placed trees for spacing

        for x_offset_tree in range(CHUNK_SIZE):
            for z_offset_tree in range(CHUNK_SIZE):
                wx_t = self.chunk_pos[0] + x_offset_tree
                wz_t = self.chunk_pos[1] + z_offset_tree

                # Find the actual surface Y and block type at (wx_t, wz_t)
                surface_y_tree = -1000 # Default if no ground
                block_on_surface_tree = None
                # Scan from a bit above max_height down to world bottom for ground
                for y_scan_tree in range(current_max_height + 5, -current_max_height // 2 -1, -1):
                    b_check = self.blocks.get((wx_t, y_scan_tree, wz_t))
                    if b_check is not None and b_check != 'water': # Found solid ground
                        surface_y_tree = y_scan_tree
                        block_on_surface_tree = b_check
                        break 
                
                if block_on_surface_tree is None: continue # No suitable ground

                # --- Biome check for tree suitability ---
                temp_tree_raw = (pnoise2(wx_t * biome_freq_tree, wz_t * biome_freq_tree, octaves=2, base=seed + 10) + 1) / 2
                humidity_tree_raw = (pnoise2(wx_t * biome_freq_tree, wz_t * biome_freq_tree, octaves=2, base=seed + 20) + 1) / 2
                
                tree_can_grow_here = False
                tree_type_to_place = 'treetrunkdark' # Default tree type
                leaves_type_to_place = 'treeleaves'
                
                if block_on_surface_tree == 'grass': # Trees mostly on grass
                    if temp_tree_raw > 0.4 and humidity_tree_raw > 0.55: # Forest-like conditions
                        tree_can_grow_here = True
                        # Could vary tree_type_to_place here based on more specific biome checks
                    elif 0.25 <= temp_tree_raw <= 0.75 and 0.25 <= humidity_tree_raw <= 0.7: # Plains
                        if random.random() < 0.15: # Lower chance for trees in plains
                             tree_can_grow_here = True
                elif block_on_surface_tree == 'sand' and temp_tree_raw > 0.6 and humidity_tree_raw < 0.35: # Oasis in desert?
                    if random.random() < 0.05: # Very rare palm-like trees on sand
                        tree_can_grow_here = True
                        # tree_type_to_place = 'palmtrunk' # If palm tree assets existed
                        # leaves_type_to_place = 'palmleaves'

                if not tree_can_grow_here or surface_y_tree <= current_water_level: # No trees underwater
                    continue

                # Check spacing from other trees
                too_close_to_other_tree = False
                for prev_tx, prev_tz in placed_tree_locations:
                    if (wx_t - prev_tx)**2 + (wz_t - prev_tz)**2 < min_tree_spacing_sq:
                        too_close_to_other_tree = True; break
                if too_close_to_other_tree: continue

                # Check for clear space above for tree height (e.g., 5-7 blocks)
                required_clear_height = 6
                clear_space_for_tree = True
                for y_clear_offset in range(1, required_clear_height + 1):
                    if self.blocks.get((wx_t, surface_y_tree + y_clear_offset, wz_t)) is not None:
                        clear_space_for_tree = False; break
                if not clear_space_for_tree: continue

                # Use Perlin noise for final tree placement chance
                tree_placement_noise_val = (pnoise2(wx_t * tree_placement_noise_freq, wz_t * tree_placement_noise_freq, octaves=1, base=tree_seed_offset) +1)/2
                
                # Modulate placement chance by a biome-density factor (e.g. from tree_density_noise)
                density_mod_noise = (pnoise2(wx_t * tree_density_noise_freq, wz_t * tree_density_noise_freq, octaves=1, base=tree_seed_offset+5) +1)/2
                final_tree_chance = tree_placement_noise_val * (density_mod_noise * 0.5 + 0.5) # Bias towards denser areas

                if final_tree_chance > 0.65: # Adjust threshold for overall density
                    actual_trunk_height = random.randint(4, 7)
                    
                    # Place trunk blocks
                    for y_trunk_offset in range(1, actual_trunk_height + 1):
                        self.blocks[(wx_t, surface_y_tree + y_trunk_offset, wz_t)] = tree_type_to_place
                    
                    # Place leaves (example: simple spherical or conical canopy)
                    canopy_base_y = surface_y_tree + actual_trunk_height
                    canopy_radius = random.randint(2,3) # Radius of leaves from trunk top
                    for ly_offset in range(canopy_radius +1): # Iterate vertically for canopy height
                        for lx_offset in range(-canopy_radius, canopy_radius + 1):
                            for lz_offset in range(-canopy_radius, canopy_radius + 1):
                                # Simple sphere-like canopy shape
                                if lx_offset**2 + lz_offset**2 + (ly_offset - canopy_radius/2)**2 <= canopy_radius**2:
                                    # Ensure leaves don't replace trunk top, and are above trunk base
                                    if not (lx_offset == 0 and lz_offset == 0 and ly_offset == 0):
                                        # Check if block is already occupied (e.g. by another part of this tree's leaves)
                                        if self.blocks.get((wx_t + lx_offset, canopy_base_y + ly_offset, wz_t + lz_offset)) is None:
                                             self.blocks[(wx_t + lx_offset, canopy_base_y + ly_offset, wz_t + lz_offset)] = leaves_type_to_place
                    
                    # Ensure top of trunk has leaves directly above it
                    self.blocks[(wx_t, canopy_base_y +1, wz_t)] = leaves_type_to_place 
                    placed_tree_locations.append((wx_t, wz_t))

    def remove(self):
        # Destroy Ursina entities associated with this chunk
        destroy(self.opaque_terrain_entity)
        destroy(self.water_entity)
        self.blocks.clear() # Clear block data

    def build_mesh(self):
        # Combined geometry lists for opaque terrain
        combined_vertices = []
        combined_uvs = []
        combined_normals = []
        combined_triangles = []
        combined_colors = [] # Added colors, assuming white for now
        opaque_idx_offset = 0

        # Water mesh data (as before)
        water_vertices = []
        water_uvs = []
        water_normals = []
        water_triangles = []
        water_colors = [] # Assuming consistent color for water, or handle per-vertex if needed
        water_idx_offset = 0

        # --- Texture Atlas Setup ---
        # Create an ordered list of unique textures from texture_mapping
        unique_textures = []
        texture_to_id = {}
        # Sort items for consistent ID assignment
        sorted_texture_mapping_items = sorted(texture_mapping.items(), key=lambda item: item[0])

        for tex_name, tex_obj in sorted_texture_mapping_items:
            if tex_obj and isinstance(tex_obj, Texture): # Ensure it's an actual texture object
                if tex_obj not in texture_to_id:
                    texture_to_id[tex_obj] = len(unique_textures)
                    unique_textures.append(tex_obj)
        
        NUM_TEXTURES_TOTAL = len(unique_textures)
        ATLAS_GRID_WIDTH = 16 # Example: 16 textures wide
        if NUM_TEXTURES_TOTAL == 0: # Avoid division by zero if no textures
            ATLAS_GRID_HEIGHT = 1 
        else:
            ATLAS_GRID_HEIGHT = ceil(NUM_TEXTURES_TOTAL / ATLAS_GRID_WIDTH)
        
        uv_scale_x = 1.0 / ATLAS_GRID_WIDTH
        uv_scale_y = 1.0 / ATLAS_GRID_HEIGHT
        # --- End Texture Atlas Setup ---

        for bpos, bdata_mesh in self.blocks.items():
            actual_type_mesh = bdata_mesh if not isinstance(bdata_mesh, dict) else bdata_mesh.get("type", bdata_mesh)

            if actual_type_mesh in (DOOR, POKEBALL, FOXFOX, PARTICLE_BLOCK): 
                continue # Skip special entities for combined meshes
            
            is_water_block = (actual_type_mesh == 'water')
            
            bx_mesh, by_mesh, bz_mesh = bpos
            for face_name_mesh, face_verts_mesh in CUBE_FACES.items():
                nx_mesh = bx_mesh + FACE_NORMALS[face_name_mesh].x
                ny_mesh = by_mesh + FACE_NORMALS[face_name_mesh].y
                nz_mesh = bz_mesh + FACE_NORMALS[face_name_mesh].z
                
                neighbor_block_data_mesh = self.world.get_block((nx_mesh, ny_mesh, nz_mesh))
                neighbor_type_mesh = neighbor_block_data_mesh if not isinstance(neighbor_block_data_mesh, dict) \
                                   else neighbor_block_data_mesh.get("type", neighbor_block_data_mesh)

                should_draw_face_mesh = False
                if is_water_block:
                    should_draw_face_mesh = (neighbor_type_mesh is None) or (neighbor_type_mesh != 'water')
                else: # Opaque blocks
                    should_draw_face_mesh = (neighbor_type_mesh is None) or \
                                            (neighbor_type_mesh == 'water') # Draw if neighbor is air or water
                                            # More complex culling (e.g. different opaque types) could be added here if needed

                if not should_draw_face_mesh:
                    continue

                # Select the correct lists and offset based on block type
                if is_water_block:
                    current_verts_list = water_vertices
                    current_uvs_list = water_uvs
                    current_norms_list = water_normals
                    current_tris_list = water_triangles
                    current_colors_list = water_colors
                    base_idx_mesh = water_idx_offset
                else: # Opaque block
                    current_verts_list = combined_vertices
                    current_uvs_list = combined_uvs
                    current_norms_list = combined_normals
                    current_tris_list = combined_triangles
                    current_colors_list = combined_colors
                    base_idx_mesh = opaque_idx_offset

                # Get texture ID for UV calculation (only for opaque blocks)
                texture_id_for_uv = -1
                if not is_water_block:
                    actual_texture_obj = texture_mapping.get(actual_type_mesh)
                    if actual_texture_obj and actual_texture_obj in texture_to_id:
                        texture_id_for_uv = texture_to_id[actual_texture_obj]
                    else:
                        # print(f"[WARN] Texture for '{actual_type_mesh}' not in atlas map. Skipping face.")
                        continue # Skip this face if texture not found/mapped for atlas

                uv_offset_x = 0
                uv_offset_y = 0
                if not is_water_block and texture_id_for_uv != -1:
                    texture_column = texture_id_for_uv % ATLAS_GRID_WIDTH
                    texture_row = texture_id_for_uv // ATLAS_GRID_WIDTH
                    uv_offset_x = texture_column * uv_scale_x
                    # Adjust for Ursina's UV origin (typically top-left for textures, but Mesh UVs are bottom-left)
                    # If atlas rows are from top (0) to bottom (GRID_HEIGHT-1):
                    uv_offset_y = (ATLAS_GRID_HEIGHT - 1 - texture_row) * uv_scale_y 
                    # If atlas rows are from bottom (0) to top (GRID_HEIGHT-1) which is more standard for UV atlases:
                    # uv_offset_y = texture_row * uv_scale_y


                for i_vert, v_local_mesh in enumerate(face_verts_mesh):
                    vx_m, vy_m, vz_m = bx_mesh + v_local_mesh[0], by_mesh + v_local_mesh[1], bz_mesh + v_local_mesh[2]
                    current_verts_list.append((vx_m, vy_m, vz_m))
                    current_norms_list.append(FACE_NORMALS[face_name_mesh])
                    current_colors_list.append(color.white) # Default to white, can be changed

                    if is_water_block:
                        # Standard UVs for water (assumes water_texture is not part of the atlas)
                        current_uvs_list.append((i_vert in (1, 2), i_vert >= 2)) 
                    elif texture_id_for_uv != -1 : # Opaque block with valid texture ID
                        # Original face UVs (quad: (0,0), (1,0), (1,1), (0,1) -> map to i_vert)
                        # Standard UV mapping for a quad:
                        # Vertex 0: (0,0)
                        # Vertex 1: (1,0)
                        # Vertex 2: (1,1)
                        # Vertex 3: (0,1)
                        original_face_uv_x = 1.0 if i_vert == 1 or i_vert == 2 else 0.0
                        original_face_uv_y = 1.0 if i_vert == 2 or i_vert == 3 else 0.0
                        
                        # Apply scale and offset for atlas
                        final_uv_x = original_face_uv_x * uv_scale_x + uv_offset_x
                        final_uv_y = original_face_uv_y * uv_scale_y + uv_offset_y
                        current_uvs_list.append((final_uv_x, final_uv_y))
                    else: # Should not happen if skipped above, but as fallback:
                        current_uvs_list.append((0,0)) # Fallback UV

                current_tris_list.extend([(base_idx_mesh + 0, base_idx_mesh + 1, base_idx_mesh + 2), 
                                          (base_idx_mesh + 2, base_idx_mesh + 3, base_idx_mesh + 0)])
                
                if is_water_block:
                    water_idx_offset += 4
                else:
                    opaque_idx_offset += 4
        
        # --- Finalize Opaque Terrain Mesh ---
        if combined_vertices:
            self.opaque_terrain_entity.model = Mesh(vertices=combined_vertices, uvs=combined_uvs,
                                                    normals=combined_normals, triangles=combined_triangles,
                                                    colors=combined_colors, mode='triangle', static=True)
            self.opaque_terrain_entity.collider = 'mesh' # Enable collider
            self.opaque_terrain_entity.visible = True
        else:
            self.opaque_terrain_entity.model = None
            self.opaque_terrain_entity.collider = None 
            self.opaque_terrain_entity.visible = False

        # --- Finalize Water Mesh ---
        if water_vertices:
            self.water_entity.model = Mesh(vertices=water_vertices, uvs=water_uvs,
                                           normals=water_normals, triangles=water_triangles,
                                           colors=water_colors, mode='triangle', static=True)
            self.water_entity.visible = True
        else:
            self.water_entity.model = None
            self.water_entity.visible = False
            
    def set_block(self, pos, btype): # pos is world coordinates
        # Update own block dictionary
        if btype is None: # Removing block
            if pos in self.blocks:
                del self.blocks[pos]
        else: # Placing or changing block
            self.blocks[pos] = btype
        
        self.build_mesh() # Rebuild this chunk's mesh first

        # Determine if the modified block is on a boundary and rebuild neighbors if so
        # Relative position of the block within this chunk
        block_x_rel_to_chunk = pos[0] - self.chunk_pos[0]
        block_z_rel_to_chunk = pos[2] - self.chunk_pos[1]

        # Check X boundaries
        if block_x_rel_to_chunk == 0:
            self.world.rebuild_chunk_at((self.chunk_pos[0] - CHUNK_SIZE, self.chunk_pos[1]))
        elif block_x_rel_to_chunk == CHUNK_SIZE - 1:
            self.world.rebuild_chunk_at((self.chunk_pos[0] + CHUNK_SIZE, self.chunk_pos[1]))
        # Check Z boundaries
        if block_z_rel_to_chunk == 0:
            self.world.rebuild_chunk_at((self.chunk_pos[0], self.chunk_pos[1] - CHUNK_SIZE))
        elif block_z_rel_to_chunk == CHUNK_SIZE - 1:
            self.world.rebuild_chunk_at((self.chunk_pos[0], self.chunk_pos[1] + CHUNK_SIZE))
        
        # Optional: Could also rebuild diagonal neighbors if on a corner, though less critical for visuals.


class VoxelWorld: # Container for all Chunks
    def __init__(self):
        self.chunks = {} # (cx, cz) -> Chunk instance

    def get_block(self, world_pos): # world_pos is (x,y,z)
        px, py, pz = floor(world_pos[0]), floor(world_pos[1]), floor(world_pos[2])
        
        chunk_coord_x = (px // CHUNK_SIZE) * CHUNK_SIZE
        chunk_coord_z = (pz // CHUNK_SIZE) * CHUNK_SIZE
        target_chunk_coord = (chunk_coord_x, chunk_coord_z)

        if target_chunk_coord in self.chunks:
            return self.chunks[target_chunk_coord].blocks.get((px, py, pz), None)
        return None # Chunk not found

    def set_block(self, world_pos, block_type_set): # world_pos is (x,y,z)
        px_set, py_set, pz_set = floor(world_pos[0]), floor(world_pos[1]), floor(world_pos[2])

        chunk_coord_x_set = (px_set // CHUNK_SIZE) * CHUNK_SIZE
        chunk_coord_z_set = (pz_set // CHUNK_SIZE) * CHUNK_SIZE
        target_chunk_coord_set = (chunk_coord_x_set, chunk_coord_z_set)

        if target_chunk_coord_set not in self.chunks:
            # This case implies creating a chunk if it doesn't exist.
            # This might be okay for dynamic worlds, but for pre-generated or streaming,
            # chunks should ideally be managed by the World class's load/update_chunks.
            # For now, let's assume if set_block is called, the chunk should exist or be made.
            # print(f"[VoxelWorld] Auto-creating chunk at {target_chunk_coord_set} due to set_block.")
            self.chunks[target_chunk_coord_set] = Chunk(self, target_chunk_coord_set, generate_terrain_on_init=False)
            # generate_terrain=False because we are about to set a specific block, not bulk generate.
            # If this new chunk needs terrain, it should be handled by a separate call.

        self.chunks[target_chunk_coord_set].set_block((px_set, py_set, pz_set), block_type_set)
        # The Chunk's set_block method now handles rebuilding itself and its direct neighbors.

    def rebuild_chunk_at(self, chunk_coord_rebuild): # Helper for Chunk to call
        if chunk_coord_rebuild in self.chunks:
            self.chunks[chunk_coord_rebuild].build_mesh()


class World: # High-level game world manager
    def __init__(self, filename=None, force_new_world=False, use_streaming_mode=False): # Renamed args
        self.streaming_mode = use_streaming_mode
        self.vworld = VoxelWorld() # Underlying voxel data and chunk container
        self.chunks = self.vworld.chunks # Direct reference for convenience (active chunks)
        self.saved_chunk_data = {} # Cache for chunk data from save file in streaming mode

        save_folder_path = 'save'
        if not os.path.exists(save_folder_path):
            os.makedirs(save_folder_path)

        if self.streaming_mode:
            self.chunks.clear() # Ensure active chunks start empty for streaming
            if force_new_world:
                print("[STREAMING INIT] Force_new_world is true. Starting fresh, not loading save file into cache.")
                self.saved_chunk_data.clear() # Ensure cache is empty
                # If a save file exists with the current name, it might be good to remove it here too.
                # For now, just clearing the cache is sufficient as per prompt.
                save_file_to_potentially_remove = os.path.join(save_folder_path, filename if filename else current_save_name)
                if os.path.exists(save_file_to_potentially_remove):
                    try:
                        os.remove(save_file_to_potentially_remove)
                        print(f"[STREAMING INIT] Removed old save file '{save_file_to_potentially_remove}' due to force_new_world.")
                    except OSError as e:
                        print(f"[STREAMING INIT] Error removing old save file '{save_file_to_potentially_remove}': {e}")
            else: # Streaming mode, not forcing new world -> try to load save into cache
                load_file_path_stream_cache = os.path.join(save_folder_path, filename if filename else current_save_name)
                print(f"[STREAMING INIT] Attempting to load save file '{load_file_path_stream_cache}' into cache.")
                try:
                    with open(load_file_path_stream_cache, 'r') as f_cache:
                        full_saved_data = json.load(f_cache)
                        self.saved_chunk_data = full_saved_data.get("chunks", {})
                        # Load world settings if they exist in the save file (e.g., CHUNK_SIZE)
                        # This is important so that chunk key generation in update_chunks uses correct CHUNK_SIZE
                        # if it was different in the loaded world.
                        saved_settings_cache = full_saved_data.get("world_settings")
                        if saved_settings_cache:
                            global CHUNK_SIZE, WORLD_SIZE # Allow updating these from save
                            CHUNK_SIZE = saved_settings_cache.get("chunk_size", CHUNK_SIZE)
                            WORLD_SIZE = saved_settings_cache.get("world_radius_chunks", WORLD_SIZE) # Less critical for streaming
                            print(f"[STREAMING INIT] Loaded settings from save cache: ChunkSize={CHUNK_SIZE}, WorldRadius={WORLD_SIZE}")
                        print(f"[STREAMING INIT] Loaded {len(self.saved_chunk_data)} chunks into cache from '{load_file_path_stream_cache}'.")
                except FileNotFoundError:
                    print(f"[STREAMING INIT] Save file '{load_file_path_stream_cache}' not found. Starting with empty cache.")
                    self.saved_chunk_data = {}
                except json.JSONDecodeError as e_json:
                    print(f"[STREAMING INIT] Error decoding JSON from '{load_file_path_stream_cache}': {e_json}. Starting with empty cache.")
                    self.saved_chunk_data = {}
            # Initial chunks around player will be loaded by update_chunks.
        
        else: # Not streaming mode
            if filename:
                full_file_path_load = os.path.join(save_folder_path, filename)
                if force_new_world and os.path.exists(full_file_path_load):
                    os.remove(full_file_path_load)
                    print(f"Forcing new world: removed old save '{full_file_path_load}'.")
                    self.generate_all_chunks() # This will populate self.chunks directly
                elif os.path.exists(full_file_path_load): # File exists, try to load
                    self.load_world_from_file(filename) # This populates self.chunks
                else: # File doesn't exist, generate new
                    print(f"Save file '{full_file_path_load}' not found. Generating new world.")
                    self.generate_all_chunks()
            else: # No filename, try default or generate new
                default_save_name_init = current_save_name # from global
                if os.path.exists(os.path.join(save_folder_path, default_save_name_init)):
                    self.load_world_from_file(default_save_name_init)
                else:
                    print("No default save found. Generating new world.")
                    self.generate_all_chunks()

    def generate_all_chunks(self): # For non-streaming mode
        print(f"Generating new world (non-streaming). CHUNK_SIZE={CHUNK_SIZE}, WORLD_SIZE (radius)={WORLD_SIZE}.")
        self.vworld.chunks.clear() # Clear any existing chunks in VoxelWorld

        # WORLD_SIZE is radius in chunks from (0,0)
        for x_chunk_gen_idx in range(-WORLD_SIZE, WORLD_SIZE + 1): # Inclusive range for full size
            for z_chunk_gen_idx in range(-WORLD_SIZE, WORLD_SIZE + 1):
                chunk_base_coords = (x_chunk_gen_idx * CHUNK_SIZE, z_chunk_gen_idx * CHUNK_SIZE)
                new_chunk_instance = Chunk(self.vworld, chunk_base_coords, generate_terrain_on_init=True)
                self.chunks[chunk_base_coords] = new_chunk_instance
        
        for chk_to_build in self.chunks.values():
            chk_to_build.build_mesh()
        print("Finished generating new world (non-streaming).")

    def update_chunks(self, player_world_pos): # For streaming mode
        if not self.streaming_mode: return

        player_chunk_x_base_stream = (floor(player_world_pos.x) // CHUNK_SIZE) * CHUNK_SIZE
        player_chunk_z_base_stream = (floor(player_world_pos.z) // CHUNK_SIZE) * CHUNK_SIZE
        
        # Define view distance in chunks (e.g., 8 chunks radius -> 17x17 area)
        stream_view_radius_chunks = 8 
        
        currently_desired_chunks = set()
        for dx_stream_offset in range(-stream_view_radius_chunks, stream_view_radius_chunks + 1):
            for dz_stream_offset in range(-stream_view_radius_chunks, stream_view_radius_chunks + 1):
                coord_key_desired = (player_chunk_x_base_stream + dx_stream_offset * CHUNK_SIZE, 
                                     player_chunk_z_base_stream + dz_stream_offset * CHUNK_SIZE)
                currently_desired_chunks.add(coord_key_desired)

        # Unload chunks no longer in desired set
        loaded_chunk_keys = list(self.chunks.keys())
        for loaded_key in loaded_chunk_keys:
            if loaded_key not in currently_desired_chunks:
                self.chunks[loaded_key].remove() # Ursina entity cleanup
                del self.chunks[loaded_key]
        
        # Load new chunks that are desired but not loaded
        for desired_key in currently_desired_chunks:
            if desired_key not in self.chunks:
                new_chunk_instance = None
                chunk_key_str = f"{desired_key[0]},{desired_key[1]}"

                if chunk_key_str in self.saved_chunk_data:
                    # Load from cache
                    # print(f"[STREAMING] Loading chunk {desired_key} from saved_chunk_data cache.")
                    new_chunk_instance = Chunk(self.vworld, desired_key, generate_terrain_on_init=False)
                    block_data_for_this_chunk = self.saved_chunk_data[chunk_key_str]
                    
                    for bk_str, bdata_val in block_data_for_this_chunk.items():
                        try:
                            bx, by, bz = map(int, bk_str.split(','))
                            new_chunk_instance.blocks[(bx, by, bz)] = bdata_val
                        except ValueError:
                            # print(f"[WARN] update_chunks: Malformed block key '{bk_str}' in cached chunk {chunk_key_str}")
                            continue # Skip malformed block key
                    
                    # Recreate special entities for this loaded chunk
                    self._recreate_special_entities_for_chunk(block_data_for_this_chunk)
                else:
                    # Generate new chunk if not in cache
                    # print(f"[STREAMING] Generating new chunk {desired_key} as it's not in cache.")
                    new_chunk_instance = Chunk(self.vworld, desired_key, generate_terrain_on_init=True)
                
                if new_chunk_instance:
                    self.chunks[desired_key] = new_chunk_instance
                    new_chunk_instance.build_mesh() # Build mesh for the new/loaded chunk

    def _recreate_special_entities_for_chunk(self, chunk_block_data_dict):
        # Helper to recreate special entities for a chunk based on its block data.
        # chunk_block_data_dict is the dict of blocks for this specific chunk,
        # e.g., self.saved_chunk_data[chunk_key_string]
        if not chunk_block_data_dict:
            return

        for block_pos_str, block_data_val in chunk_block_data_dict.items():
            try:
                # Block positions are world coordinates, already stored as such in save file
                bx, by, bz = map(int, block_pos_str.split(','))
                pos_tuple = (bx, by, bz)
            except ValueError:
                # print(f"[WARN] _recreate_special_entities: Malformed block position string '{block_pos_str}'")
                continue

            actual_type = block_data_val
            rotation = 0
            if isinstance(block_data_val, dict):
                actual_type = block_data_val.get("type", block_data_val)
                rotation = block_data_val.get("rotation", 0)
            
            # Ensure global entity dicts are used and entities are not duplicated
            if actual_type == DOOR:
                if pos_tuple not in door_entities:
                    # Check if this is the "bottom" part of a door if that data is stored
                    # For simplicity, assume any DOOR entry from save needs an entity if not present
                    door_obj = Door(pos_tuple)
                    door_obj.pivot.rotation_y = rotation
                    # Check if door is open based on rotation, or add 'open_state' to save data if needed
                    if abs(rotation - door_obj.open_rotation) < 1: # Simple check
                        door_obj.open = True
                        door_obj.collider = None
                    else:
                        door_obj.open = False
                    door_entities[pos_tuple] = door_obj
            elif actual_type == POKEBALL:
                if pos_tuple not in pokeball_entities:
                    pb_obj = PokeballEntity(pos_tuple)
                    pb_obj.rotation_y = rotation # Pokeballs might also have a saved rotation
                    pokeball_entities[pos_tuple] = pb_obj
            elif actual_type == FOXFOX:
                if pos_tuple not in foxfox_entities:
                    ff_obj = FoxfoxEntity(pos_tuple)
                    ff_obj.rotation_y = rotation # Foxfox entities might also have a saved rotation
                    foxfox_entities[pos_tuple] = ff_obj
            # PARTICLE_BLOCK is a terrain block type, not usually a separate global entity unless
            # it manages an effect. If ParticleBlockEntity instances are needed globally:
            # elif actual_type == PARTICLE_BLOCK:
            #     if pos_tuple not in particleblock_entities:
            #         # particleblock_entities[pos_tuple] = ParticleBlockEntity(pos_tuple)
            #         pass # Assuming ParticleBlockEntity is for effects, may not need recreation this way.

    def save_world(self): # Saves current world state to JSON
        global current_save_name # Uses the global save name
        save_file_path_actual = os.path.join('save', current_save_name)
        
        print(f"Saving world to '{save_file_path_actual}'...")
        data_to_save_json = {}
        # Include world settings like CHUNK_SIZE, WORLD_SIZE for potential future use on load
        data_to_save_json["world_settings"] = {
            "chunk_size": CHUNK_SIZE,
            "world_radius_chunks": WORLD_SIZE # Note: This is radius if non-streaming
        }
        data_to_save_json["chunks"] = {}

        for chunk_coord_key_save, chunk_inst_save in self.chunks.items():
            json_key_for_chunk = f"{chunk_coord_key_save[0]},{chunk_coord_key_save[1]}"
            data_to_save_json["chunks"][json_key_for_chunk] = {} # Init dict for this chunk's blocks
            
            for block_pos_key_save, block_data_val_save in chunk_inst_save.blocks.items():
                json_key_for_block = f"{block_pos_key_save[0]},{block_pos_key_save[1]},{block_pos_key_save[2]}"
                data_to_save_json["chunks"][json_key_for_chunk][json_key_for_block] = block_data_val_save
        
        try:
            with open(save_file_path_actual, 'w') as f_save:
                json.dump(data_to_save_json, f_save, indent=2) # Use indent for readability
            print("World saved successfully.")
        except Exception as e_save:
            print(f"Error saving world to '{save_file_path_actual}': {e_save}")

    def load_world_from_file(self, save_filename_to_load): # Loads world from JSON
        global CHUNK_SIZE, WORLD_SIZE # Allow updating these from save if present
        
        # This method is primarily for non-streaming mode full loads.
        # In streaming mode, __init__ handles populating self.saved_chunk_data.
        # If this method IS called in streaming mode (e.g. by a command),
        # it should ideally clear active chunks and then let update_chunks repopulate from the new cache.
        # For now, the main __init__ logic handles the streaming mode startup.
        
        # The following logic is for NON-STREAMING mode.
        if self.streaming_mode:
            print(f"[WARNING] load_world_from_file called in streaming mode for '{save_filename_to_load}'. This is unusual.")
            print("Clearing active chunks and saved_chunk_data cache. World will reload based on new file via update_chunks.")
            for chunk_inst in self.chunks.values(): # Destroy existing active chunk entities
                chunk_inst.remove()
            self.chunks.clear()
            self.saved_chunk_data.clear()
            
            # Populate self.saved_chunk_data from the new file.
            load_file_path_stream_reload = os.path.join('save', save_filename_to_load)
            try:
                with open(load_file_path_stream_reload, 'r') as f_reload_cache:
                    full_saved_data_reload = json.load(f_reload_cache)
                    self.saved_chunk_data = full_saved_data_reload.get("chunks", {})
                    saved_settings_reload = full_saved_data_reload.get("world_settings")
                    if saved_settings_reload:
                        global CHUNK_SIZE, WORLD_SIZE
                        CHUNK_SIZE = saved_settings_reload.get("chunk_size", CHUNK_SIZE)
                        WORLD_SIZE = saved_settings_reload.get("world_radius_chunks", WORLD_SIZE)
                        print(f"[STREAMING RELOAD] Loaded settings: ChunkSize={CHUNK_SIZE}")
                    print(f"[STREAMING RELOAD] Loaded {len(self.saved_chunk_data)} chunks into cache from '{load_file_path_stream_reload}'.")
            except FileNotFoundError:
                print(f"[STREAMING RELOAD] File '{load_file_path_stream_reload}' not found. Cache is empty.")
            except json.JSONDecodeError as e_json_reload:
                print(f"[STREAMING RELOAD] Error decoding JSON from '{load_file_path_stream_reload}': {e_json_reload}. Cache is empty.")
            # update_chunks will then handle loading from this new cache.
            return

        load_file_path_actual = os.path.join('save', save_filename_to_load)
        if not os.path.exists(load_file_path_actual):
            print(f"Save file '{load_file_path_actual}' not found for loading. Generating new world.")
            self.generate_all_chunks() # Non-streaming default
            return

        print(f"Loading world from '{load_file_path_actual}'...")
        self.vworld.chunks.clear() # Clear any existing data

        try:
            with open(load_file_path_actual, 'r') as f_load:
                loaded_world_data = json.load(f_load)

            # Load world settings if they exist in the save file
            saved_settings = loaded_world_data.get("world_settings")
            if saved_settings:
                CHUNK_SIZE = saved_settings.get("chunk_size", CHUNK_SIZE)
                WORLD_SIZE = saved_settings.get("world_radius_chunks", WORLD_SIZE)
                print(f"Loaded settings from save: ChunkSize={CHUNK_SIZE}, WorldRadius={WORLD_SIZE}")
            
            loaded_chunks_data = loaded_world_data.get("chunks", {})
            for json_chunk_key_load, blocks_dict_load in loaded_chunks_data.items():
                try:
                    cx_ld, cz_ld = map(int, json_chunk_key_load.split(','))
                    chunk_coord_ld = (cx_ld, cz_ld)
                    
                    # Create chunk instance, generate_terrain=False as we're loading its blocks
                    newly_loaded_chunk = Chunk(self.vworld, chunk_coord_ld, generate_terrain_on_init=False)
                    
                    for json_block_key_load, block_val_load in blocks_dict_load.items():
                        try:
                            bx_ld, by_ld, bz_ld = map(int, json_block_key_load.split(','))
                            newly_loaded_chunk.blocks[(bx_ld, by_ld, bz_ld)] = block_val_load
                        except ValueError: pass # Skip malformed block keys
                    
                    self.chunks[chunk_coord_ld] = newly_loaded_chunk
                except ValueError: pass # Skip malformed chunk keys
            
            # After all blocks loaded, build meshes and (for non-streaming) create special entities
            for chunk_coord_loaded, loaded_chunk_inst_build in self.chunks.items():
                loaded_chunk_inst_build.build_mesh() # Build visual mesh
                
                # Re-create special entities (Doors, Pokeballs etc.) based on loaded block data
                # This is for non-streaming mode full load.
                # For streaming, special entities are handled per-chunk in update_chunks.
                if not self.streaming_mode:
                    # Construct the string key as it would be in saved_chunk_data
                    # to pass to a potential common helper, or inline logic carefully.
                    # Here, we directly iterate this specific chunk's blocks.
                    for b_pos_special_load, b_data_special_load in loaded_chunk_inst_build.blocks.items():
                        actual_type_special_load = b_data_special_load
                        rot_special_load = 0
                        if isinstance(b_data_special_load, dict):
                            actual_type_special_load = b_data_special_load.get("type", b_data_special_load)
                            rot_special_load = b_data_special_load.get("rotation", 0)

                        # Ensure global entity dicts are used
                        if actual_type_special_load == DOOR and b_pos_special_load not in door_entities:
                            door_ent = Door(b_pos_special_load); door_ent.pivot.rotation_y = rot_special_load
                            door_entities[b_pos_special_load] = door_ent
                        elif actual_type_special_load == POKEBALL and b_pos_special_load not in pokeball_entities:
                            pb_ent = PokeballEntity(b_pos_special_load); pb_ent.rotation_y = rot_special_load
                            pokeball_entities[b_pos_special_load] = pb_ent
                        elif actual_type_special_load == FOXFOX and b_pos_special_load not in foxfox_entities:
                            ff_ent = FoxfoxEntity(b_pos_special_load); ff_ent.rotation_y = rot_special_load
                            foxfox_entities[b_pos_special_load] = ff_ent
                        # ParticleBlockEntity might need special handling here if it's managed globally

            print("World loaded successfully from file (non-streaming).")

        except json.JSONDecodeError as e_json_decode:
            print(f"Error decoding JSON from '{load_file_path_actual}': {e_json_decode}. Generating new world.")
            self.generate_all_chunks()
        except Exception as e_load_other:
            print(f"An unexpected error occurred loading world: {e_load_other}. Generating new world.")
            self.generate_all_chunks()


    def set_block(self, world_pos_set, block_type_to_set):
        self.vworld.set_block(world_pos_set, block_type_to_set)

    def get_block(self, world_pos_get):
        return self.vworld.get_block(world_pos_get)


#############################################
# 17) Menus (Globals are now defined near top of section 19)
#############################################
current_save_name = "my_world.json" # Default save name
CHUNK_SIZE = 16 # Default chunk dimensions (can be changed by New Game menu)
WORLD_SIZE = 4  # Default world radius in chunks for non-streaming (can be changed)
BIOME_NOISE_FREQUENCY = 0.008 # Moved here to be global

#############################################
# New Helper: Find Safe Spawn Height
#############################################
def find_safe_spawn_height(world_to_check, x_coord_spawn, z_coord_spawn):
    # Scan from a reasonable height downwards to find solid ground
    # Max height for scan could be related to max_height_gen used in Chunk.generate_terrain
    y_scan_start = 30 
    y_scan_end = -20 
    for y_coord_s in range(y_scan_start, y_scan_end - 1, -1):
        block_below_player = world_to_check.get_block((x_coord_spawn, y_coord_s -1, z_coord_spawn))
        # Check for common non-water, solid blocks suitable for spawning
        if block_below_player and block_below_player != 'water': # Simplified check
            return y_coord_s # Spawn on top of this block
    return 25 # Fallback spawn height if no suitable ground found


#############################################
# Menus: New Game, Start, Load, Save (Class definitions from before, ensure they use globals correctly)
#############################################
class NewGameMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, ignore_paused=True)
        mouse.locked = False
        mouse.visible = True
        self.panel = Panel(parent=self, scale=(0.6,0.7), color=color.color(0,0,0,0.8))
        Text(parent=self.panel, text='New World Settings', y=0.4, origin=(0,0), scale=1.3)
        
        y_offset_ngm = 0.25
        # Chunk Size
        Text(parent=self.panel, text='Chunk Size (e.g., 16):', x=-0.4, y=y_offset_ngm, origin=(-0.5,0))
        self.chunk_size_input = InputField(parent=self.panel, x=0.2, y=y_offset_ngm, limit_content_to="0123456789", default_value=str(CHUNK_SIZE))
        y_offset_ngm -= 0.15
        # World Size (Radius for non-streaming, View distance factor for streaming)
        Text(parent=self.panel, text='World Radius (chunks, e.g., 4):', x=-0.4, y=y_offset_ngm, origin=(-0.5,0))
        self.world_size_input = InputField(parent=self.panel, x=0.2, y=y_offset_ngm, limit_content_to="0123456789", default_value=str(WORLD_SIZE))
        y_offset_ngm -=0.15
        # World Name
        Text(parent=self.panel, text='World Name:', x=-0.4, y=y_offset_ngm, origin=(-0.5,0))
        self.world_name_input = InputField(parent=self.panel, x=0.2, y=y_offset_ngm, default_value="My 자동 생성 World")


        y_offset_ngm -= 0.2
        Button(parent=self.panel, text='Create World', y=y_offset_ngm -0.05, scale=(0.4,0.1), color=color.azure, on_click=self.action_start_new_game)
        Button(parent=self.panel, text='Back to Main Menu', y=y_offset_ngm - 0.18, scale=(0.4,0.08), on_click=self.action_go_back)

    def action_start_new_game(self):
        global CHUNK_SIZE, WORLD_SIZE, current_save_name
        try:
            cs = int(self.chunk_size_input.text)
            CHUNK_SIZE = max(8, min(cs, 32)) # Clamp chunksize e.g. 8-32
        except ValueError: CHUNK_SIZE = 16 # Default
        try:
            ws = int(self.world_size_input.text)
            WORLD_SIZE = max(1, min(ws, 16)) # Clamp world radius e.g. 1-16
        except ValueError: WORLD_SIZE = 4 # Default
        
        world_name_text = self.world_name_input.text.strip()
        if not world_name_text: world_name_text = "NewWorld"
        current_save_name = "".join(c for c in world_name_text if c.isalnum() or c in (' ','_')).rstrip() + ".json"
        if not current_save_name.endswith(".json"): current_save_name += ".json"


        # Determine streaming based on total chunks (World is (2*R+1) x (2*R+1) chunks if R is radius)
        total_world_chunks_dim = (2 * WORLD_SIZE + 1)
        use_streaming_ngm = True if total_world_chunks_dim**2 > 100 else False # e.g. >10x10 area

        destroy(self)
        create_game(filename=current_save_name, force_new_world=True, use_streaming_mode=use_streaming_ngm)

    def action_go_back(self):
        destroy(self)
        StartMenu()


class StartMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, ignore_paused=True) # Main menu should ignore pause
        mouse.locked = False
        mouse.visible = True
        # Optional: Add a background image/panel
        # Panel(parent=self, color=color.dark_gray, scale=(window.aspect_ratio, 1)) 
        # Text(parent=self, text="Voxel Game Title", y=0.3, scale=3, origin=(0,0))
        
        menu_button_y_start = 0.1
        menu_button_spacing = -0.12
        Button(parent=self, text='New Game', y=menu_button_y_start, scale=(0.3,0.1), color=color.azure, on_click=self.action_new_game)
        Button(parent=self, text='Load Game', y=menu_button_y_start + menu_button_spacing, scale=(0.3,0.1), color=color.azure, on_click=self.action_load_game)
        Button(parent=self, text='Quit Game', y=menu_button_y_start + 2*menu_button_spacing, scale=(0.3,0.1), color=color.red, on_click=application.quit)

    def action_new_game(self):
        destroy(self)
        NewGameMenu()
    def action_load_game(self):
        destroy(self)
        LoadGameMenu()

class LoadGameMenu(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui, ignore_paused=True)
        mouse.locked = False
        mouse.visible = True
        self.panel = Panel(parent=self, scale_x=0.7, scale_y=0.8, color=color.color(0,0,0,0.8))
        Text(parent=self.panel, text='Load Saved World', y=0.45, origin=(0,0))

        save_files_path = 'save'
        json_save_files = [f for f in os.listdir(save_files_path) if f.endswith('.json')] if os.path.exists(save_files_path) else []
        
        y_button_offset_load = 0.3
        if not json_save_files:
            Text(parent=self.panel, text='No save files found.', y=0, origin=(0,0))
        else:
            for idx, filename_load in enumerate(json_save_files):
                if idx >= 5: Text(parent=self.panel, text=f"...and {len(json_save_files)-5} more", y=y_button_offset_load - 0.05); break # Limit displayed files
                btn_load = Button(parent=self.panel, text=filename_load, y=y_button_offset_load, scale_x=0.9, scale_y=0.12)
                btn_load.on_click = Func(self.action_load_selected_world, filename_load) # Use Func for arguments
                y_button_offset_load -= 0.15
        
        Button(parent=self.panel, text='Back', y=-0.4, scale=(0.3,0.1), on_click=self.action_go_back_load)

    def action_load_selected_world(self, filename_to_load_selected):
        global current_save_name
        current_save_name = filename_to_load_selected
        
        # Heuristic for streaming: if file size > 500KB, enable streaming.
        # This is a placeholder, could be more sophisticated (e.g. read metadata from JSON)
        use_streaming_load = False
        try:
            file_path_load_check = os.path.join('save', filename_to_load_selected)
            if os.path.exists(file_path_load_check) and os.path.getsize(file_path_load_check) > 500 * 1024:
                use_streaming_load = True
        except OSError: pass # Ignore if file check fails

        destroy(self)
        create_game(filename=filename_to_load_selected, force_new_world=False, use_streaming_mode=use_streaming_load)

    def action_go_back_load(self):
        destroy(self)
        StartMenu()


class SaveAsMenu(Entity):
    def __init__(self, game_menu_parent_ref): # Expecting the GameMenu instance
        super().__init__(parent=camera.ui, ignore_paused=True)
        self.game_menu_ref = game_menu_parent_ref
        self.game_menu_ref.enabled = False # Disable game menu while this is up

        self.panel = Panel(parent=self, scale=(0.5,0.35), color=color.dark_gray)
        Text(parent=self.panel, text='Save World As:', y=0.3, origin=(0,0))
        self.filename_input_save = InputField(parent=self.panel, default_value=current_save_name, y=0.05, scale_x=0.9)
        Button(parent=self.panel, text='Save', color=color.azure, y=-0.15, scale=(0.3,0.15), on_click=self.action_confirm_and_save)
        Button(parent=self.panel, text='Cancel', y=-0.32, scale=(0.3,0.1), on_click=self.action_cancel_save)

    def action_confirm_and_save(self):
        new_filename_save = self.filename_input_save.text.strip()
        if not new_filename_save: new_filename_save = "UnnamedWorld"
        if not new_filename_save.lower().endswith(".json"):
            new_filename_save += ".json"
        
        self.game_menu_ref.execute_save_and_quit(new_filename_save) # Call method on GameMenu
        destroy(self) # Destroy SaveAsMenu

    def action_cancel_save(self):
        self.game_menu_ref.enabled = True # Re-enable GameMenu
        destroy(self)


class GameMenu(Entity): # In-game pause menu
    def __init__(self):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True) # Start disabled
        self.panel = Panel(parent=self, scale=(0.4,0.5), color=color.color(0,0,0,0.8))
        Text(parent=self.panel, text='Game Paused', y=0.4, origin=(0,0))
        
        btn_y = 0.2
        Button(parent=self.panel, text='Resume Game', y=btn_y, scale=(0.8,0.15), color=color.green, on_click=self.action_resume)
        btn_y -= 0.2
        self.music_btn_game_menu = Button(parent=self.panel, text=f'Music: {"ON" if music_on else "OFF"}', 
                                          y=btn_y, scale=(0.8,0.15), on_click=self.action_toggle_music)
        btn_y -= 0.2
        Button(parent=self.panel, text='Save & Quit', y=btn_y, scale=(0.8,0.15), color=color.red, on_click=self.action_save_quit_prompt)

    def action_resume(self):
        self.enabled = False
        if player: player.enable()
        mouse.locked = True
        mouse.visible = False

    def action_toggle_music(self):
        global music_on, current_music
        music_on = not music_on
        self.music_btn_game_menu.text = f'Music: {"ON" if music_on else "OFF"}'
        if not music_on and current_music and current_music.playing:
            current_music.pause()
        elif music_on : # If turning on
            if current_music and not current_music.playing:
                 if current_music.time > 0 and current_music.length > 0 and current_music.time < current_music.length:
                    current_music.resume()
                 else: start_random_music() # Was finished or not started
            elif not current_music:
                start_random_music()


    def action_save_quit_prompt(self):
        SaveAsMenu(self) # Show the "Save As" dialog, passing self

    def execute_save_and_quit(self, final_filename_to_save): # Called by SaveAsMenu
        global current_save_name
        current_save_name = final_filename_to_save
        if world:
            world.save_world()
        application.quit()


#############################################
# 18) Update Shader Uniforms (Simplified)
#############################################
def update_shader_uniforms(): # Called every frame in main update
    if player and sky and hasattr(sky, 'shader'): # Ensure sky and its shader are ready
        current_time_in_cycle = (time.time() - start_time) % full_cycle_time
        sun_angle_shader = (current_time_in_cycle / full_cycle_time) * 2 * pi
        
        # Apply to scene (for block_lighting_shader) and sky (for daynight_shader)
        scene.set_shader_input("time_of_day", sun_angle_shader)
        if sky.shader: # Double check shader on sky
             sky.set_shader_input("time_of_day", sun_angle_shader)

#############################################
# 19) Create Game Function 
#############################################
# Global game state variables (defined earlier, ensure they are accessible)
full_cycle_time = 20 * 60  # e.g., 20 minutes for a full day-night cycle
start_time = time.time()  # Real-world time game logic started or day cycle began

world = None
player = None
game_menu = None # In-game pause menu
inventory_ui = None
sky = None # Sky entity
# UI Text elements
vox_time_text, local_time_text, song_text, coords_text, compass_text = None,None,None,None,None
last_chunk_update_time = 0 # For streaming mode chunk update throttling

def create_game(filename=None, force_new_world=False, use_streaming_mode=False):
    global world, player, game_menu, inventory_ui, sky
    global vox_time_text, local_time_text, song_text, coords_text, compass_text
    global start_time, CHUNK_SIZE, WORLD_SIZE # Make sure these are global

    # Clear previous UI (e.g., from main menu)
    for child_ui in camera.ui.children[:]:
        if child_ui not in (mouse, Tooltip.default_tooltip): # Keep mouse and default tooltip
            destroy(child_ui)

    print(f"[GAME INIT] Creating world. File: {filename}, New: {force_new_world}, Stream: {use_streaming_mode}")
    print(f"[SETTINGS] ChunkSize: {CHUNK_SIZE}, WorldRadius: {WORLD_SIZE} (for non-streamed generation)")

    start_time = time.time() # Reset day cycle timer for new game

    world = World(filename=filename, force_new_world=force_new_world, use_streaming_mode=use_streaming_mode)
    player = CustomPlayer() # Create player instance

    spawn_x_player, spawn_z_player = 0.5, 0.5 # Try to spawn near center of a block
    safe_y_player = find_safe_spawn_height(world, spawn_x_player, spawn_z_player)
    player.position = Vec3(spawn_x_player, safe_y_player, spawn_z_player)
    
    # Delayed check to prevent falling through world if spawn calculation is slow/off
    invoke(lambda: player.position.y if player.y < -10 else None, player.y == find_safe_spawn_height(world, player.x, player.z) + 0.5, delay=1.0)

    player.model.visible = False # Hide default FPC model if custom is used or no model desired
    player.rotation = (0,0,0)
    player.camera_pivot.rotation = (0,0,0) # Reset pitch

    game_menu = GameMenu()
    inventory_ui = InventoryUI()
    sky = Entity(model='sphere', texture='sky_default', scale=500, double_sided=True, shader=daynight_shader) # Ensure sky_default texture exists or remove
    if not sky.texture: sky.color = color.skyblue # Fallback sky color
    sky.set_shader_input("time_of_day", 0.5) # Mid-day start for shader

    init_music()

    # UI Text elements setup (positions can be fine-tuned)
    text_scale_val = 1.1
    vox_time_text = Text(parent=camera.ui, position=window.top_right - Vec2(0.02,0.02), origin=(1,1), scale=text_scale_val)
    local_time_text = Text(parent=camera.ui, position=window.top_right - Vec2(0.02,0.06), origin=(1,1), scale=text_scale_val)
    song_text = Text(parent=camera.ui, position=window.top_right - Vec2(0.02,0.10), origin=(1,1), scale=text_scale_val,text="Song: Loading...")
    coords_text = Text(parent=camera.ui, position=window.top_left + Vec2(0.02,-0.02), origin=(-1,1), scale=text_scale_val)
    compass_text = Text(parent=camera.ui, position=window.top_left + Vec2(0.02,-0.06), origin=(-1,1), scale=text_scale_val)

    mouse.locked = True
    mouse.visible = False
    if player: player.enable()
    
    # Initial chunk load for streaming mode around player
    if use_streaming_mode and world:
        world.update_chunks(player.position)

    print("[GAME INIT] Game creation complete.")


#############################################
# 20) Main Update Function
#############################################
def update():
    global last_chunk_update_time 

    if not player or not world : return # Essential components not ready

    update_shader_uniforms()
    update_music()
    process_water_spread() 
    spawn_bubbles_update() # Handle bubble spawning if player is underwater

    if world.streaming_mode:
        if time.time() - last_chunk_update_time > 0.2: # Stream chunks slightly more often
            world.update_chunks(player.position)
            last_chunk_update_time = time.time()

    if free_cam_mode: 
        if free_cam and free_cam.enabled: free_cam.update() # Make sure free_cam has update method
        return # Skip player/game logic if free cam is active

    if inventory_ui and inventory_ui.inventory_open_state: # Check state variable
        inventory_ui.update() # For drag icon, etc.
        return 
    
    if game_menu and game_menu.enabled:
        return # Game menu is open

    # Update UI Text
    current_game_time_sec = (time.time() - start_time) % full_cycle_time
    hours_game = int((current_game_time_sec / full_cycle_time) * 24)
    minutes_game = int(((current_game_time_sec / full_cycle_time) * 24 * 60) % 60)
    ampm_game = "AM" if hours_game < 12 or hours_game == 24 else "PM"
    display_hour_game = hours_game % 12
    if display_hour_game == 0: display_hour_game = 12
    if vox_time_text: vox_time_text.text = f"VoxTime: {display_hour_game:02d}:{minutes_game:02d} {ampm_game}"
    if local_time_text: local_time_text.text = "Local: " + time.strftime("%I:%M %p")
    if song_text: 
        song_name = os.path.basename(current_track).rsplit('.',1)[0] if current_track else "None"
        song_text.text = f"Song: {song_name}"
    if coords_text: coords_text.text = f"XYZ: {player.x:.1f}, {player.y:.1f}, {player.z:.1f}"
    if compass_text: compass_text.text = "Face: " + get_cardinal(player.rotation_y)

    # Player block interaction (moved from input to update for click cooldown)
    if player.enabled and mouse.locked:
        if time.time() - player.last_click_time > 0.2: # Slightly longer cooldown
            if mouse.left:
                remove_block()
                player.last_click_time = time.time()
            elif mouse.right:
                if inventory_ui and inventory_ui.hotbar_data[inventory_ui.hotbar_selected_index]:
                    item_to_place = inventory_ui.hotbar_data[inventory_ui.hotbar_selected_index]['item']
                    place_block(item_to_place) 
                    player.last_click_time = time.time()


#############################################
# 21) Raycast Helper Functions
#############################################
def do_raycast(distance_rc=10): # Increased default distance
    if not player or not hasattr(player, 'camera_pivot'): return None
    return raycast(origin=player.camera_pivot.world_position,
                   direction=player.camera_pivot.forward,
                   distance=distance_rc, ignore=[player], debug=False)

def get_pointed_block_coord(is_removing_block=True):
    hit_data = do_raycast()
    if hit_data and hit_data.hit:
        # If removing, target the block hit. If placing, target the block in front of the hit face.
        offset_multiplier = 0.5 if is_removing_block else -0.5 # Small offset into or away from block
        target_world_point = hit_data.world_point + hit_data.world_normal * offset_multiplier
        
        block_coord_final = (floor(target_world_point.x), 
                             floor(target_world_point.y), 
                             floor(target_world_point.z))
        return block_coord_final, hit_data # Return coord and original hit_info
    else: # Fallback for particle block interaction if raycast misses solid terrain
        if not player or not hasattr(player, 'camera_pivot'): return None
        # Check a point slightly in front of player for certain interactions
        # This is less precise and should be used sparingly.
        # check_pos_fallback = player.camera_pivot.world_position + player.camera_pivot.forward * 1.5
        # coord_fallback = (floor(check_pos_fallback.x), floor(check_pos_fallback.y), floor(check_pos_fallback.z))
        # if world and world.get_block(coord_fallback) == PARTICLE_BLOCK: # Example for specific block
        #     return coord_fallback, None
        return None


#############################################
# 22) Place/Remove Block Functions
#############################################
def place_block(block_type_place):
    if not world or not player or not inventory_ui: return

    placement_target_data = get_pointed_block_coord(is_removing_block=False) # False for placement
    if not placement_target_data: return
    (tx, ty, tz), _ = placement_target_data

    # Prevent placing inside player's collider space
    player_collider_min = player.position + player.collider.center - player.collider.size/2
    player_collider_max = player.position + player.collider.center + player.collider.size/2
    if player_collider_min.x < tx + 1 and player_collider_max.x > tx and        player_collider_min.y < ty + 1 and player_collider_max.y > ty and        player_collider_min.z < tz + 1 and player_collider_max.z > tz:
        # print("Cannot place block inside player.")
        return

    existing_block_at_place_target = world.get_block((tx, ty, tz))
    # Allow placing in air (None) or replacing water
    if existing_block_at_place_target is not None and existing_block_at_place_target != 'water':
        # print(f"Cannot place block: target occupied by {existing_block_at_place_target}")
        return 

    # Special block types
    if block_type_place == DOOR:
        # Ensure space for door (e.g., two blocks high)
        if world.get_block((tx,ty+1,tz)) is None or world.get_block((tx,ty+1,tz)) == 'water':
            door_obj = Door((tx,ty,tz)); door_entities[(tx,ty,tz)] = door_obj
            world.set_block((tx,ty,tz), {"type": DOOR, "bottom": True, "rotation": player.rotation_y}) # Mark bottom part
            world.set_block((tx,ty+1,tz), {"type": DOOR, "bottom": False, "rotation": player.rotation_y}) # Mark top part
        else: return # Not enough space
    elif block_type_place == POKEBALL:
        pb_obj = PokeballEntity((tx,ty,tz)); pokeball_entities[(tx,ty,tz)] = pb_obj
        world.set_block((tx,ty,tz), {"type": POKEBALL, "rotation": player.rotation_y})
    elif block_type_place == FOXFOX:
        ff_obj = FoxfoxEntity((tx,ty,tz)); foxfox_entities[(tx,ty,tz)] = ff_obj
        world.set_block((tx,ty,tz), {"type": FOXFOX, "rotation": player.rotation_y})
    elif block_type_place == PARTICLE_BLOCK: # This is a regular block type now
        world.set_block((tx,ty,tz), PARTICLE_BLOCK)
        # ParticleBlockEntity could be used to manage effects *at* this block if needed,
        # but the block itself is just data in the chunk.
        # if (tx,ty,tz) not in particleblock_entities: # Create an effect manager if desired
        #    particleblock_entities[(tx,ty,tz)] = ParticleBlockEntity((tx,ty,tz))
    else: # Regular block
        world.set_block((tx,ty,tz), block_type_place)
        if block_type_place == 'water':
            if water_sound: water_sound.play()
            schedule_water_spread((tx,ty,tz), 5, player.forward if player else Vec3(0,0,1), delay=0.1)
        elif block_type_place == 'sponge':
            if sponge_sound: sponge_sound.play()
            soak_up_water((tx,ty,tz), radius=4) # Sponge effect

    # Decrement from inventory (this should be robust)
    selected_slot_idx = inventory_ui.hotbar_selected_index
    hotbar_item_data = inventory_ui.hotbar_data[selected_slot_idx]
    if hotbar_item_data and hotbar_item_data['item'] == block_type_place:
        hotbar_item_data['count'] -= 1
        if hotbar_item_data['count'] <= 0:
            inventory_ui.hotbar_data[selected_slot_idx] = None
        inventory_ui.update_all_slots() # Refresh UI


def remove_block():
    if not world or not player: return
    removal_target_data = get_pointed_block_coord(is_removing_block=True)
    if not removal_target_data: return
    (rx, ry, rz), _ = removal_target_data

    block_to_remove_data = world.get_block((rx,ry,rz))
    if not block_to_remove_data: return # Nothing to remove

    actual_block_type_removed = block_to_remove_data
    is_special_dict = isinstance(block_to_remove_data, dict)
    if is_special_dict:
        actual_block_type_removed = block_to_remove_data.get("type", block_to_remove_data)

    # Handle multi-block structures like doors
    if actual_block_type_removed == DOOR:
        # Remove both parts of the door if it's a two-block door
        is_bottom_part = block_to_remove_data.get("bottom", True) if is_special_dict else True
        other_part_y = ry + 1 if is_bottom_part else ry -1
        world.set_block((rx,ry,rz), None)
        world.set_block((rx,other_part_y,rz), None) # Remove other part
        if (rx,ry,rz) in door_entities: destroy(door_entities.pop((rx,ry,rz)))
        if (rx,other_part_y,rz) in door_entities: destroy(door_entities.pop((rx,other_part_y,rz))) # Also remove other entity if exists
    elif actual_block_type_removed in [POKEBALL, FOXFOX, PARTICLE_BLOCK]: # Other special entities/blocks
        world.set_block((rx,ry,rz), None) # Remove from world data
        if actual_block_type_removed == POKEBALL and (rx,ry,rz) in pokeball_entities:
            destroy(pokeball_entities.pop((rx,ry,rz)))
        elif actual_block_type_removed == FOXFOX and (rx,ry,rz) in foxfox_entities:
            destroy(foxfox_entities.pop((rx,ry,rz)))
        # For PARTICLE_BLOCK, if it had an associated effect entity in particleblock_entities:
        # if actual_block_type_removed == PARTICLE_BLOCK and (rx,ry,rz) in particleblock_entities:
        #    destroy(particleblock_entities.pop((rx,ry,rz)))
    else: # Regular block
        world.set_block((rx,ry,rz), None)

    if dig_sound: dig_sound.play()
    for _ in range(random.randint(3, 6)): # Fewer debris
        Debris((rx,ry,rz), actual_block_type_removed) # Pass the actual type string
    
    if actual_block_type_removed in collectible_blocks:
        spawn_pickup(actual_block_type_removed, (rx,ry,rz))


#############################################
# 23) Input Handling
#############################################
def input(key_input): # Renamed arg to avoid conflict with 'key' variable in loops
    global command_mode, command_input_field, free_cam_mode # Globals for state
    
    if not player or not inventory_ui or not game_menu: # Core components not ready
        if key_input == 'escape': application.quit() # Basic quit if game not loaded
        return

    # --- UI Mode Checks (Inventory, Game Menu, Command Input) ---
    if key_input == 'tab' and not command_mode : # Toggle inventory if not typing command
        inventory_ui.toggle_inventory()
        return 
    if inventory_ui.inventory_open_state:
        inventory_ui.input(key_input) # Let inventory handle its input
        return
    if game_menu.enabled: # Game menu handles its own (button clicks)
        if key_input == 'escape': game_menu.action_resume() # Allow Esc to close menu
        return
    if command_mode: # Command input field active
        if key_input == 'enter': # Execute command
            cmd_text_input = command_input_field.text.strip()
            destroy(command_input_field); command_input_field = None
            command_mode = False
            if player: player.enable()
            mouse.locked = True; mouse.visible = False
            process_command(cmd_text_input)
        # InputField handles text input itself, so no other key processing here
        return

    # --- Game World Interactions (Player must be enabled) ---
    if key_input == 'enter' and not command_mode: # Open command input
        command_mode = True
        if player: player.disable()
        mouse.locked = False; mouse.visible = True
        command_input_field = InputField(parent=camera.ui, scale_x=0.8, scale_y=0.07,
                                          position=(0, -0.45), text_color=color.black,
                                          background_color=color.rgba(220,220,220,200))
        command_input_field.placeholder = "Type command (e.g., 'fly', 'set time 14:30', 'spawn dirt 10')"
        command_input_field.activate()
        return

    if not player.enabled: return # Further inputs require player to be active

    if key_input == 'escape': # Open/Close Game Menu
        game_menu.enabled = not game_menu.enabled
        mouse.locked = not game_menu.enabled
        mouse.visible = game_menu.enabled
        if game_menu.enabled: player.disable()
        else: player.enable()

    elif key_input.isdigit() and key_input != '0': # Hotbar 1-9
        inventory_ui.hotbar_selected_index = int(key_input) - 1
        inventory_ui.update_hotbar_highlight_pos()
    elif key_input == '0': # Hotbar 0 (maps to 9th slot, index 8)
        inventory_ui.hotbar_selected_index = 8 
        inventory_ui.update_hotbar_highlight_pos()
    elif key_input == 'scroll up':
        inventory_ui.hotbar_selected_index = (inventory_ui.hotbar_selected_index - 1 + 9) % 9
        inventory_ui.update_hotbar_highlight_pos()
    elif key_input == 'scroll down':
        inventory_ui.hotbar_selected_index = (inventory_ui.hotbar_selected_index + 1) % 9
        inventory_ui.update_hotbar_highlight_pos()

    elif key_input == 'v': toggle_free_camera()
    elif key_input == 'f5': player.input('f5') # Player camera toggle

    elif key_input == 'e': # Interact
        pointed_interact_data = get_pointed_block_coord(is_removing_block=True)
        if pointed_interact_data:
            (pix, piy, piz), _ = pointed_interact_data
            block_val_interact = world.get_block((pix,piy,piz))
            block_type_actual_interact = block_val_interact.get("type") if isinstance(block_val_interact, dict) else block_val_interact

            if block_type_actual_interact == DOOR and (pix,piy,piz) in door_entities:
                door_entities[(pix,piy,piz)].toggle()
            # Add other 'e' interactions for other blocks here (e.g. Pokeball, FoxFox sounds)
            elif block_type_actual_interact == POKEBALL: play_sound_once(pokeball_sound)
            elif block_type_actual_interact == FOXFOX: play_sound_once(foxfox_sound)

    # Let player instance handle its own movement inputs via its FPC base class
    if hasattr(player, 'input'): player.input(key_input)


def process_command(cmd_full_str): # Command processing logic
    global start_time, player, world # Access globals
    if not cmd_full_str: return
    parts_cmd = cmd_full_str.lower().split()
    command_verb = parts_cmd[0]
    args_cmd = parts_cmd[1:]

    if command_verb == "set" and len(args_cmd) >= 2 and args_cmd[0] == "time":
        time_str_cmd = args_cmd[1] # e.g., "6am", "18:30"
        hour_set_cmd = -1
        try:
            if ":" in time_str_cmd: # HH:MM
                h_cmd, m_cmd = map(int, time_str_cmd.split(':'))
                if 0 <= h_cmd <= 23 and 0 <= m_cmd <= 59: hour_set_cmd = h_cmd + m_cmd/60.0
            else: # 6am, 12pm
                is_pm_cmd = "pm" in time_str_cmd
                hour_val_cmd = int(time_str_cmd.replace("am","").replace("pm",""))
                if 1 <= hour_val_cmd <= 11: hour_set_cmd = hour_val_cmd + (12 if is_pm_cmd else 0)
                elif hour_val_cmd == 12: hour_set_cmd = 0 if not is_pm_cmd else 12 # 12am is 0, 12pm is 12
            
            if hour_set_cmd != -1:
                time_fraction_cmd = hour_set_cmd / 24.0
                start_time = time.time() - (time_fraction_cmd * full_cycle_time) # Adjust cycle start
                print(f"Time set to ~{time_str_cmd.upper()}.")
                update_shader_uniforms() # Refresh sky
            else: print(f"Invalid time: {time_str_cmd}. Use HH:MM or 1-12am/pm.")
        except ValueError: print("Time format error.")
    elif command_verb == "tp" and len(args_cmd) == 3 and player: # Teleport
        try:
            player.position = Vec3(float(args_cmd[0]), float(args_cmd[1]), float(args_cmd[2]))
            print(f"Teleported to {player.position}.")
        except ValueError: print("Invalid coordinates for tp. Use numbers.")
    elif command_verb == "fly" and player:
        player.gravity = 0 if player.gravity > 0 else 1 # Toggle gravity
        print(f"Fly mode {'activated' if player.gravity == 0 else 'deactivated'}.")
    elif command_verb == "give" and len(args_cmd) >= 1: # Give item
        item_name_give = args_cmd[0]
        count_give = int(args_cmd[1]) if len(args_cmd) >= 2 and args_cmd[1].isdigit() else 1
        if item_name_give in texture_mapping or item_name_give in [DOOR,POKEBALL,FOXFOX,PARTICLE_BLOCK]: # Check if item is known
            for _ in range(count_give): add_item_to_inventory(item_name_give)
            print(f"Gave {count_give} of {item_name_give}.")
        else: print(f"Unknown item: {item_name_give}")
    else:
        print(f"Unknown command or incorrect arguments: '{cmd_full_str}'")


#############################################
# 24) Launch the Game
#############################################
if __name__ == '__main__':
    if not os.path.exists('save'): # Ensure save directory exists
        os.makedirs('save')
    
    # Set window properties before app.run() if needed
    # window.title = 'Voxel Game Advanced'
    # window.fullscreen = False 
    
    StartMenu() # Display the main menu to start
    app.run()
