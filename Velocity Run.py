from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math, random, time

# ============ Window / Camera  ============
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W / WIN_H
FOVY   = 70.0

third_person = True
cam_angle  = 90.0
cam_radius = 140.0
cam_height = 85.0
fov_boost  = 0.0

# ============ Track / Lanes ============
LANE_W = 30.0
LANES  = (-LANE_W, 0.0, +LANE_W)

FLOOR_SEG_LEN = 120.0
FLOOR_COUNT   = 24
FLOOR_HALF_W  = 90.0
CEILING_Z     = 120.0

# ============ Player ============
player_lane = 1
player_x    = LANES[player_lane]
jump_v      = 0.0
jump_z      = 0.0
is_crouch   = False
crouch_t    = 0.0

RUN_SPEED_BASE = 80.0
run_speed      = RUN_SPEED_BASE

# ============ Health / Score ============
hp_max = 100
hp     = hp_max
score  = 0
dist   = 0.0

# ============ World Pools ============
obstacles = []   # dict: {kind, lane, y, h, color, ...}  or rotor {...}
gems      = []   # dict: {lane, y, z}
bullets   = []   # dict: {lane, x, y, z}

# ============ Cheats ============
cheat_on     = False
gravity_flip = False
magnet_on    = False

# ============ Gem / Magnet tuning ============
GROUND_GEM_Z = 3.0
AIR_GEM_Z    = 50.0
GEM_RADIUS   = 3.6
PICKUP_RADIUS = 8.5
MAGNET_PULL_RADIUS = FLOOR_HALF_W * 2.0
MAGNET_PULL_SPEED  = 6.0

# ============ Hit & Slow ============
SLOW_DURATION = 3.0
SLOW_FACTOR   = 0.6
slow_timer    = 0.0
HIT_COOLDOWN  = 0.5
hit_cd        = 0.0

# ============ Stars (space) outside the road ============
STAR_COUNT       = 180
STAR_SIDE_MARGIN = 20.0
STAR_X_RANGE     = FLOOR_HALF_W * 8.0
STAR_X_MIN       = FLOOR_HALF_W + STAR_SIDE_MARGIN
STAR_Y_FRONT     = 2200.0
STAR_Z_MIN       = 10.0
STAR_Z_MAX       = CEILING_Z - 5.0
stars            = []     # list of dicts {x,y,z,r,g,b}
planet_pos       = (-180.0, 900.0, 90.0)

# ============ Spawning cadence (kept; includes anti-stall) ============
SPAWN_STEP_MIN    = 140.0
SPAWN_STEP_JITTER = 40.0
next_spawn_y      = 0.0
rotor_cooldown    = 0

# --- Ability Gem (rare, glowing) ---
ABILITY_GEM_CHANCE = 0.50     # ~6% of gem spawns are ability gems
ABILITY_DURATION   = 10.0         # seconds
score_multiplier = 1
# --- First Aid (health pickup) ---
FIRST_AID_CHANCE = 0.15   # 5% chance; adjust to control rareness
FIRST_AID_HEAL   = 40     # HP restored per pickup

ability         = None           # None | 'high_jump' | 'mult_score' | 'multishot'
ability_timer   = 0.0

# Jump caps (so high-jump can really go higher)
JUMP_MAX_Z_BASE  = 46.0
JUMP_MAX_Z_BOOST = 28.0


# ============ Bullets ============
BULLET_SPEED  = 240.0
BULLET_SIZE   = 2.5
FIRE_COOLDOWN = 0.15
fire_cd       = 0.0

_last = time.time()

# ---------------- Utility ----------------
def lane_x(i): return LANES[max(0, min(2, i))]
def clamp(v, a, b): return max(a, min(b, v))

# ---------- Text  ----------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_text_centered_bottom(y, s, font=GLUT_BITMAP_HELVETICA_18):
    # Approximate width (Helvetica18 ~10 px / char) to avoid glutBitmapWidth
    x = (WIN_W - 10*len(s)) // 2
    draw_text(x, y, s, font)

# ---------- Camera ----------
def setupCamera():
    leg_h   = 12.0 if not is_crouch else 7.0
    torso_h = 14.0 if not is_crouch else 9.0
    head_r  = 6.0
    base_plane = CEILING_Z if gravity_flip else 0.0
    center_z   = (base_plane - jump_z) if gravity_flip else (base_plane + jump_z)
    head_z = center_z + leg_h + torso_h + head_r

    eyeX = player_x; eyeY = 10.0; eyeZ = head_z

    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(FOVY + fov_boost, ASPECT, 0.5, 4000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    if third_person:
        rad = math.radians(cam_angle)
        cx = eyeX + cam_radius * math.cos(rad)
        cy = 10.0 - cam_radius * math.sin(rad)
        cz = cam_height
        gluLookAt(cx, cy, cz, eyeX, 10.0, head_z - (2.0 if gravity_flip else 0.0), 0, 0, 1)
    else:
        gluLookAt(eyeX, 10.2, head_z, eyeX, 70.0, head_z, 0, 0, 1)

# ---------- HUD  ----------
def draw_hud():
    eff_speed = run_speed * (SLOW_FACTOR if slow_timer > 0.0 else 1.0)

    # Top-left texts
    glColor3f(1, 1, 1)
    draw_text(12, WIN_H-26, f"Gems Collected: {score}")
    draw_text(12, WIN_H-50, f"Score(Distance): {int(dist)} m")
    draw_text(12, WIN_H-74, f"Speed: {int(eff_speed)} u/s")
    # === Ability Display ===
    ability_text = ability if (ability and ability_timer > 0.0) else "None"
    draw_text(12, WIN_H-160, f"Ability: {ability_text} ({int(ability_timer)}s)")
    draw_text(12, WIN_H-190, f"Cheat Mode: {"ON" if cheat_on else "OFF"}")
    # --- 2D overlay (disable depth so bar always renders correctly) ---
    glDisable(GL_DEPTH_TEST)

    W, H = 260, 16
    x0, y0 = 12, WIN_H - 130

    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    # Caption
    glColor3f(1, 1, 1)
    draw_text(x0, y0 + H + 6, f"Health: {hp}/{hp_max}")

    # Background (dark red)
    glColor3f(0.25, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex3f(x0,     y0,     0); glVertex3f(x0+W,   y0,     0)
    glVertex3f(x0+W,   y0+H,   0); glVertex3f(x0,     y0+H,   0)
    glEnd()

    # Fill width based on HP
    pct = 0.0 if hp_max <= 0 else clamp(float(hp) / float(hp_max), 0.0, 1.0)
    if pct > 0.0:
        ww = W * pct
        glColor3f(0.9, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(x0,     y0,     0); glVertex3f(x0+ww,  y0,     0)
        glVertex3f(x0+ww,  y0+H,   0); glVertex3f(x0,     y0+H,   0)
        glEnd()

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    # Re-enable for the 3D world
    glEnable(GL_DEPTH_TEST)


# ---------- Geometry ----------
def draw_floor(y0):
    glColor3f(0.14,0.14,0.17)
    glBegin(GL_QUADS)
    glVertex3f(-FLOOR_HALF_W, y0, 0.0)
    glVertex3f(+FLOOR_HALF_W, y0, 0.0)
    glVertex3f(+FLOOR_HALF_W, y0+FLOOR_SEG_LEN, 0.0)
    glVertex3f(-FLOOR_HALF_W, y0+FLOOR_SEG_LEN, 0.0)
    glEnd()

    glColor3f(0.25,0.25,0.3)
    for lx in LANES:
        glBegin(GL_QUADS)
        glVertex3f(lx-1.0, y0, 0.1)
        glVertex3f(lx+1.0, y0, 0.1)
        glVertex3f(lx+1.0, y0+FLOOR_SEG_LEN, 0.1)
        glVertex3f(lx-1.0, y0+FLOOR_SEG_LEN, 0.1)
        glEnd()

def draw_walls(y0):
    h=25.0
    glColor3f(0.18,0.24,0.38)
    glBegin(GL_QUADS)
    glVertex3f(-FLOOR_HALF_W, y0, 0.0)
    glVertex3f(-FLOOR_HALF_W, y0+FLOOR_SEG_LEN, 0.0)
    glVertex3f(-FLOOR_HALF_W, y0+FLOOR_SEG_LEN, h)
    glVertex3f(-FLOOR_HALF_W, y0, h)
    glEnd()

    glColor3f(0.16,0.20,0.34)
    glBegin(GL_QUADS)
    glVertex3f(+FLOOR_HALF_W, y0, 0.0)
    glVertex3f(+FLOOR_HALF_W, y0+FLOOR_SEG_LEN, 0.0)
    glVertex3f(+FLOOR_HALF_W, y0+FLOOR_SEG_LEN, h)
    glVertex3f(+FLOOR_HALF_W, y0, h)
    glEnd()

def draw_player():
    base = CEILING_Z if gravity_flip else 0.0
    leg_h   = 12.0 if not is_crouch else 7.0
    torso_h = 14.0 if not is_crouch else 9.0
    head_r  = 6.0
    arm_len = 12.0
    gun_len = 22.0
    px = player_x; py = 10.0
    cz = (base - jump_z) if gravity_flip else (base + jump_z)

    # legs
    glColor3f(0.20,0.20,0.75)
    glPushMatrix(); glTranslatef(px-4.0, py, cz + leg_h*0.5); glScalef(4,3,leg_h); glutSolidCube(1.0); glPopMatrix()
    glPushMatrix(); glTranslatef(px+4.0, py, cz + leg_h*0.5); glScalef(4,3,leg_h); glutSolidCube(1.0); glPopMatrix()

    # torso
    glColor3f(0.18,0.75,0.85)
    torso_z0 = cz + leg_h
    glPushMatrix(); glTranslatef(px, py, torso_z0 + torso_h*0.5); glScalef(10,6,torso_h); glutSolidCube(1.0); glPopMatrix()

    # head
    glColor3f(0.95,0.88,0.78)
    head_z = torso_z0 + torso_h + head_r
    glPushMatrix(); glTranslatef(px, py, head_z); gluSphere(gluNewQuadric(), head_r, 16, 12); glPopMatrix()

    # arms (cylinders)
    glColor3f(0.85,0.30,0.30)
    glPushMatrix(); glTranslatef(px-6.5, py, torso_z0 + torso_h*0.8); glRotatef(-90,1,0,0); gluCylinder(gluNewQuadric(),1.8,1.8,arm_len,12,1); glPopMatrix()
    glPushMatrix(); glTranslatef(px+6.5, py, torso_z0 + torso_h*0.8); glRotatef(-90,1,0,0); gluCylinder(gluNewQuadric(),1.8,1.8,arm_len,12,1); glPopMatrix()

    # gun
    glColor3f(0.20,0.22,0.28)
    gun_z = torso_z0 + torso_h*0.75
    glPushMatrix()
    glTranslatef(px, py+2.0, gun_z); glRotatef(-90,1,0,0)
    gluCylinder(gluNewQuadric(),2.0,2.0,gun_len,16,1)
    glTranslatef(0,0,gun_len); glRotatef(-90,1,0,0); glScalef(4,4,4); glutSolidCube(1.0)
    glPopMatrix()

def draw_obstacle(o, now):
    if o["kind"]=="wall":
        x = lane_x(o["lane"]); y = o["y"]; h=o["h"]
        r,g,b = o["color"]
        glPushMatrix(); glTranslatef(x,y,h*0.5); glColor3f(r,g,b); glScalef(16,10,h); glutSolidCube(1.0); glPopMatrix()
    elif o["kind"]=="rotor":
        y=o["y"]; z=o["z"]; ang=(now*o["rot_speed"])%360.0
        bar_len=o.get("len",80.0)
        glPushMatrix(); glTranslatef(0.0,y,z); glRotatef(ang,0,0,1); glColor3f(0.95,0.85,0.25); glScalef(bar_len,3.5,3.5); glutSolidCube(1.0); glPopMatrix()

def draw_gem(g):
    x, y, z = lane_x(g["lane"]), g["y"], g["z"]
    glPushMatrix()
    glTranslatef(x, y, z)

    if g.get("type") == "ability":
        # rainbow glow
        t = time.time() * 3.0
        r = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(t + 0.0))
        gC = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(t + 2.1))
        b = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(t + 4.2))
        glColor3f(r, gC, b)
        gluSphere(gluNewQuadric(), GEM_RADIUS, 12, 10)

    elif g.get("type") == "firstaid":
        glPushMatrix()

        # raise medkit above ground (half size + margin)
        glTranslatef(0, 0, 8.0)   # can adjust if scale differently

        # --- Red Medkit Cube ---
        glScalef(12, 12, 12)   # larger cube for medkit
        glColor3f(0.9, 0.1, 0.1)  # red body
        glutSolidCube(1.0)

        # --- White Cross on Front Face (facing player) ---
        glTranslatef(0, -0.51, 0)  # move to front face (-y direction)
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        # vertical bar
        glVertex3f(-0.15, 0.0, -0.4); glVertex3f(+0.15, 0.0, -0.4)
        glVertex3f(+0.15, 0.0, +0.4); glVertex3f(-0.15, 0.0, +0.4)
        # horizontal bar
        glVertex3f(-0.4, 0.0, -0.15); glVertex3f(+0.4, 0.0, -0.15)
        glVertex3f(+0.4, 0.0, +0.15); glVertex3f(-0.4, 0.0, +0.15)
        glEnd()

        glPopMatrix()



    else:
        glColor3f(0.35,0.95,0.5)
        gluSphere(gluNewQuadric(), GEM_RADIUS, 12, 10)

    glPopMatrix()




def draw_bullet(b):
    glPushMatrix(); glTranslatef(b["x"], b["y"], b["z"]); glColor3f(0.95,0.95,0.95); glScalef(BULLET_SIZE,BULLET_SIZE,BULLET_SIZE); glutSolidCube(1.0); glPopMatrix()

# ---------- Stars / Planet  ----------
def init_space_theme():
    global stars
    stars=[]
    for _ in range(STAR_COUNT):
        side = -1.0 if random.random()<0.5 else 1.0
        sx = side * random.uniform(STAR_X_MIN, STAR_X_RANGE)
        sy = random.uniform(0.0, STAR_Y_FRONT)
        sz = random.uniform(STAR_Z_MIN, STAR_Z_MAX)
        c  = random.uniform(0.8, 1.0)
        stars.append({"x":sx,"y":sy,"z":sz,"r":c,"g":c,"b":c})

def draw_space_theme():
    # Draw background stars first so the floor/quads overdraw road area (no depth test)
    glPointSize(2.0)
    glBegin(GL_POINTS)
    for s in stars:
        glColor3f(s["r"], s["g"], s["b"])
        glVertex3f(s["x"], s["y"], s["z"])
    glEnd()

    # Distant gray planet
    glPushMatrix()
    glTranslatef(planet_pos[0], planet_pos[1], planet_pos[2])
    glColor3f(0.6,0.6,0.62)
    gluSphere(gluNewQuadric(), 60.0, 20, 16)
    glPopMatrix()

def _reseed_star(i, front_y):
    side = -1.0 if random.random()<0.5 else 1.0
    sx = side * random.uniform(STAR_X_MIN, STAR_X_RANGE)
    sy = front_y + random.uniform(200.0, 600.0)
    sz = random.uniform(STAR_Z_MIN, STAR_Z_MAX)
    c  = random.uniform(0.8, 1.0)
    stars[i].update({"x":sx,"y":sy,"z":sz,"r":c,"g":c,"b":c})

# ---------- World init / reset ----------
floor_segments=[]

def reset_world():
    global player_lane, player_x, jump_v, jump_z, is_crouch, crouch_t
    global run_speed, hp, score, dist, obstacles, gems, bullets
    global third_person, cheat_on, gravity_flip, magnet_on, fov_boost
    global floor_segments, next_spawn_y, rotor_cooldown
    global ability, ability_timer
    rotor_cooldown=0

    ability=None; ability_timer=0.0
    player_lane=1; player_x=LANES[player_lane]
    jump_v=0.0; jump_z=0.0; is_crouch=False; crouch_t=0.0
    run_speed=RUN_SPEED_BASE; hp=hp_max; score=0; dist=0.0
    obstacles=[]; gems=[]; bullets=[]
    third_person=True; cheat_on=False; gravity_flip=False; magnet_on=False; fov_boost=0.0

    floor_segments=[]; y=-FLOOR_SEG_LEN
    for _ in range(FLOOR_COUNT):
        floor_segments.append(y); y += FLOOR_SEG_LEN

    # seed rows near player
    base_seed=180.0; seed_step=140.0
    for i in range(10):
        spawn_ahead(distance=base_seed + seed_step*i)
    next_spawn_y = (base_seed + seed_step*(10-1)) + SPAWN_STEP_MIN
    ability = None
    ability_timer = 0.0
def spawn_ahead(distance=240.0):
    global rotor_cooldown
    def _rand_col(): return (random.uniform(0.4,1.0), random.uniform(0.4,1.0), random.uniform(0.4,1.0))
    y=distance
    if rotor_cooldown<=0:
        kind = random.choices(["rotor","wall","gems"], weights=[35,55,10], k=1)[0]
    else:
        kind = random.choices(["wall","gems","rotor"], weights=[70,25,5], k=1)[0]

    if kind=="wall":
        obstacles.append({"kind":"wall","lane":random.randint(0,2),"y":y,"h":random.choice([18.0,28.0,40.0]),"color":_rand_col(),"hits":0})
        rotor_cooldown = max(0, rotor_cooldown-1)
    elif kind=="rotor":
        obstacles.append({"kind":"rotor","lane":1,"y":y,"z":random.choice([12.0,22.0,34.0]),"rot_speed":random.choice([90.0,120.0,180.0]),"len":random.choice([70.0,80.0,90.0]),"center":True})
        rotor_cooldown = random.randint(3,5)
    elif kind=="gems":
        lane = random.randint(0,2)
        z_choice = GROUND_GEM_Z  # always on ground (first-aid should be reachable)

        roll = random.random()
        if roll < ABILITY_GEM_CHANCE:
            gems.append({"lane": lane, "y": y, "z": z_choice, "type": "ability"})
        elif roll < ABILITY_GEM_CHANCE + FIRST_AID_CHANCE:
            gems.append({"lane": lane, "y": y, "z": z_choice, "type": "firstaid"})
        else:
            gems.append({"lane": lane, "y": y, "z": random.choice([GROUND_GEM_Z, AIR_GEM_Z])})
        rotor_cooldown = max(0, rotor_cooldown-1)

    


# ---------- Collision helpers ----------
def player_bbox():
    px=player_x; py=10.0; hw=6.5; hh=8.0 if is_crouch else 12.0
    pz=(CEILING_Z if gravity_flip else 0.0)
    z=(pz - jump_z) if gravity_flip else (pz + jump_z)
    return px,py,z,hw,hh

def obstacle_hit(o):
    """
    Return one of: 'wall_soft', 'wall_hard', 'rotor', or None.
    """
    px, py, pz, hw, hh = player_bbox()
    kind = o["kind"]

    if kind == "wall":
        ox = lane_x(o["lane"])
        oy = o["y"]
        if abs(oy - py) < 12.0 and abs(ox - px) < (hw + 6.0):
            top = o["h"]
            cat = 'wall_hard' if top >= 20.0 else 'wall_soft'
            if not gravity_flip:
                if pz < (top - 2.0):
                    return cat
            else:
                if (CEILING_Z - pz) > (CEILING_Z - top + 2.0):
                    return cat
        return None

    if kind == "rotor":
        # --- rotor center ---
        cx = 0.0 if o.get("center", True) else lane_x(o["lane"])
        cy = o["y"]
        cz = o["z"]

        # --- player full vertical span (feet -> head) ---
        leg_h   = 12.0 if not is_crouch else 7.0
        torso_h = 14.0 if not is_crouch else 9.0
        head_r  = 6.0
        base_plane = CEILING_Z if gravity_flip else 0.0
        center_z   = (base_plane - jump_z) if gravity_flip else (base_plane + jump_z)
        z_bottom   = center_z
        z_top      = center_z + leg_h + torso_h + 2.0 * head_r  # includes head

        # --- rotor thickness in Z (scaled cube, half-thickness ~1.75) ---
        bar_half_thick_z = 1.75
        rotor_low  = cz - bar_half_thick_z
        rotor_high = cz + bar_half_thick_z

        # Strict vertical overlap: rotor slab intersects player span
        if rotor_high < z_bottom or rotor_low > z_top:
            return None

        # --- lateral overlap in rotor's local frame (same as draw) ---
        ang_deg = (time.time() * o["rot_speed"]) % 360.0
        ang = math.radians(ang_deg)

        dx = px - cx
        dy = py - cy
        local_x =  dx * math.cos(ang) + dy * math.sin(ang)   # along bar length
        local_y = -dx * math.sin(ang) + dy * math.cos(ang)   # across bar width

        half_len = 0.5 * o.get("len", 80.0)
        half_w   = 1.75

        # Inflate a bit for player's footprint so edge grazes register
        inflate_x = hw + 1.0
        inflate_y = 3.0

        if (abs(local_x) <= (half_len + inflate_x)) and (abs(local_y) <= (half_w + inflate_y)):
            return 'rotor'
        return None

    return None


# ---------- Update ----------
game_over=False
def update(dt):
    global run_speed, fov_boost, dist, score, hp, game_over
    global floor_segments, obstacles, gems, bullets
    global next_spawn_y, slow_timer, hit_cd, fire_cd, stars
    global ability, ability_timer, score_multiplier

    if game_over:
        return
    
    # ---- ability timer / effects ----
    if ability_timer > 0.0:
        ability_timer = max(0.0, ability_timer - dt)
        if ability == "mult_score":
            score_multiplier = 2
        else:
            score_multiplier = 1
        if ability_timer == 0.0:
            # reset when expired
            ability = None
            score_multiplier = 1

    # ---- timers ----
    if slow_timer > 0.0: slow_timer = max(0.0, slow_timer - dt)
    if hit_cd    > 0.0: hit_cd    = max(0.0, hit_cd - dt)
    if fire_cd   > 0.0: fire_cd   = max(0.0, fire_cd - dt)

    # ---- speed / FOV ----
    run_speed += 0.02
    eff_speed = run_speed * (SLOW_FACTOR if slow_timer > 0.0 else 1.0)
    fov_boost = clamp((eff_speed - RUN_SPEED_BASE) * 0.04, 0.0, 20.0)

    # ---- move world backward (player forward) ----
    dy = eff_speed * dt
    dist += dy * 0.25
    score += int(dy * 0.05 * score_multiplier)


    # recycle floor strips
    for i in range(len(floor_segments)):
        floor_segments[i] -= dy
    for i in range(len(floor_segments)):
        if floor_segments[i] < -FLOOR_SEG_LEN * 2.0:
            floor_segments[i] += FLOOR_SEG_LEN * FLOOR_COUNT

    # move obstacles / gems
    for o in obstacles: o["y"] -= dy
    for g in gems:      g["y"] -= dy

    # ---- bullets forward + cull ----
    if bullets:
        for b in bullets: b["y"] += BULLET_SPEED * dt
        far_front = max(max(floor_segments), max((o["y"] for o in obstacles), default=0.0)) + 900.0
        bullets[:] = [b for b in bullets if b["y"] < far_front]

    # ---- bullet vs walls (10 hits destroy) ----
    if bullets and obstacles:
        keep_bullets = []
        for b in bullets:
            hit = False
            for o in obstacles:
                if o["kind"] != "wall": continue
                if o["lane"] != b["lane"]: continue
                if abs(b["y"] - o["y"]) <= 8.0 and b["z"] <= (o["h"] + 1.0):
                    o["hits"] = o.get("hits", 0) + 1
                    hit = True
                    break
            if not hit: keep_bullets.append(b)
        bullets[:] = keep_bullets
        obstacles[:] = [o for o in obstacles if not (o["kind"] == "wall" and o.get("hits", 0) >= 10)]

# ---- stars scroll + recycle (continuous, no gaps) ----r
    if stars:
        # scroll all stars
        for s in stars:
            s["y"] -= dy * 0.35

        # find the current "front" of the star field (furthest y among stars)
        current_front = max(s["y"] for s in stars)

        # when a star goes behind, respawn it just ahead of the current front
        for i, s in enumerate(stars):
            if s["y"] < -200.0:
                _reseed_star(i, current_front)


    # ---- scheduled spawning (with anti-stall guard) ----
    farthest_y = max([o["y"] for o in obstacles], default=0.0)
    front_limit = max(max(floor_segments), farthest_y) + 600.0
    if next_spawn_y > front_limit + 1200.0:
        next_spawn_y = front_limit + SPAWN_STEP_MIN
    while next_spawn_y <= front_limit:
        spawn_ahead(distance=next_spawn_y)
        next_spawn_y += SPAWN_STEP_MIN + random.uniform(0.0, SPAWN_STEP_JITTER)

    # small ahead-density guard
    ahead_items = sum(1 for o in obstacles if o["y"] > 300.0) + sum(1 for g in gems if g["y"] > 300.0)
    if ahead_items < 24:
        safety_limit = max(farthest_y, max(floor_segments)) + 1800.0
        while next_spawn_y <= safety_limit:
            spawn_ahead(distance=next_spawn_y)
            next_spawn_y += SPAWN_STEP_MIN + random.uniform(0.0, SPAWN_STEP_JITTER)

    # ---- cull behind ----
    obstacles[:] = [o for o in obstacles if o["y"] > -30.0]
    gems[:]      = [g for g in gems      if g["y"] > -30.0]

    # ---- jump physics ----
    if jump_v != 0.0:
        j = globals()["jump_z"]
        j += jump_v * dt
        j_new = jump_v - (90.0 * dt)
        if j <= 0.0 and j_new < 0.0:
            j = 0.0; globals()["jump_v"] = 0.0
        else:
            globals()["jump_v"] = j_new
        globals()["jump_z"] = clamp(j, 0.0, 46.0)

    # ---- crouch smoothing ----
    if is_crouch: globals()["crouch_t"] = min(0.2, crouch_t + dt)
    else:         globals()["crouch_t"] = max(0.0, crouch_t - dt)

    # ---- obstacle collision → HP & slow ----
    if hit_cd == 0.0:
        for o in obstacles:
            cat = obstacle_hit(o)
            if cat:
                if cat == 'wall_hard':
                    hp = max(0, hp - 100)
                elif cat in ('wall_soft', 'rotor'):
                    hp = max(0, hp - 20); slow_timer = SLOW_DURATION
                hit_cd = HIT_COOLDOWN
                break

    if hp <= 0 and not game_over:
        game_over = True

    # ---- GEM COLLECTION (magnet pull scales with speed) ----
    px, py, pz, hw, hh = player_bbox()

    leg_h   = 12.0 if not is_crouch else 7.0
    torso_h = 14.0 if not is_crouch else 9.0
    head_r  = 6.0
    base_plane = CEILING_Z if gravity_flip else 0.0
    center_z   = (base_plane - jump_z) if gravity_flip else (base_plane + jump_z)
    z_bottom = center_z
    z_top    = center_z + leg_h + torso_h + 2.0 * head_r
    z_low, z_high = (min(z_bottom, z_top), max(z_bottom, z_top))

    pickup = globals().get("GEM_PICKUP_RADIUS", globals().get("PICKUP_RADIUS", 6.0))
    radial_threshold = hw + pickup
    radial2 = radial_threshold * radial_threshold
    vert_pad = pickup

    MAG_R  = MAGNET_PULL_RADIUS
    MAG_R2 = MAG_R * MAG_R

    # scale factor grows with speed (≥ 1.0)
    speed_scale = max(1.0, eff_speed / RUN_SPEED_BASE)

    keep = []
    for g in gems:
        gx, gy, gz = lane_x(g["lane"]), g["y"], g["z"]

        # Magnet (unchanged except for variable names)
        if cheat_on and magnet_on:
            dxm = gx - px
            dym = gy - py
            if (dxm*dxm + dym*dym) <= MAG_R2:
                if g["lane"] < player_lane:   g["lane"] += 1
                elif g["lane"] > player_lane: g["lane"] -= 1
                gx = lane_x(g["lane"])
                t = clamp(MAGNET_PULL_SPEED * max(1.0, eff_speed / RUN_SPEED_BASE) * dt, 0.0, 1.0)
                gy = g["y"] = gy + (py - gy) * t
                gz = g["z"] = gz + (pz - gz) * t

        dx = gx - px
        dy_ = gy - py
        if (dx*dx + dy_*dy_) <= radial2 and (gz >= (z_low - vert_pad)) and (gz <= (z_high + vert_pad)):
            if g.get("type") == "ability":
                # random power
                ability = random.choice(["high_jump", "mult_score", "multishot"])
                ability_timer = ABILITY_DURATION
                score_multiplier = 2 if ability == "mult_score" else 1
                score += 3 * score_multiplier  # small bonus
            elif g.get("type") == "firstaid":
                # heal
                
                hp = min(hp_max, hp + FIRST_AID_HEAL)
            else:
                score += 1 * score_multiplier

            # collected → do not keep
            continue

        keep.append(g)

    gems[:] = keep



# ---------- Render ----------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setupCamera()

    # background (stars first so floor overdraws road)
    draw_space_theme()

    # floor/walls
    for y in floor_segments:
        draw_floor(y); draw_walls(y)

    now=time.time()
    for o in obstacles: draw_obstacle(o, now)
    for g in gems:      draw_gem(g)
    if third_person:    draw_player()
    for b in bullets:   draw_bullet(b)

    draw_hud()

    if game_over:
        glColor3f(0.9,0.1,0.1)
        draw_text_centered_bottom(72, "GAME OVER!! Press R to Restart")
       
    glutSwapBuffers()

# ---------- Input ----------
def current_gun_z():
    base = CEILING_Z if gravity_flip else 0.0
    leg_h   = 12.0 if not is_crouch else 7.0
    torso_h = 14.0 if not is_crouch else 9.0
    center  = (base - jump_z) if gravity_flip else (base + jump_z)
    torso_z0 = center + leg_h
    return torso_z0 + torso_h*0.75

def fire_bullet():
    global fire_cd, bullets
    if fire_cd > 0.0:
        return

    lanes_to_fire = [player_lane]
    if ability == "multishot" and ability_timer > 0.0:
        if player_lane > 0: lanes_to_fire.append(player_lane - 1)
        if player_lane < 2: lanes_to_fire.append(player_lane + 1)

    by = 16.0
    bz = current_gun_z()
    for ln in lanes_to_fire:
        bullets.append({"lane": ln, "x": lane_x(ln), "y": by, "z": bz})

    fire_cd = FIRE_COOLDOWN

def keyboardListener(key, x, y):
    global player_lane, player_x, jump_v, is_crouch
    global cheat_on, gravity_flip, magnet_on, third_person, game_over
    if key==b'a' and not game_over:
        player_lane=max(0, player_lane-1); player_x=lane_x(player_lane)
    if key==b'd' and not game_over:
        player_lane=min(2, player_lane+1); player_x=lane_x(player_lane)
    if key==b' ' and not game_over:
        if is_crouch: is_crouch=False
        if jump_v==0.0 and not is_crouch:
            jump_impulse = 60.0
            if ability == "high_jump" and ability_timer > 0.0:
                jump_impulse = 90.0
            globals()["jump_v"] = jump_impulse

    if key==b'x'  and not game_over:
        is_crouch = not is_crouch
    if key==b'c':
        cheat_on = not cheat_on
        if not cheat_on: gravity_flip=False; magnet_on=False
    if key==b'f' and cheat_on: gravity_flip = not gravity_flip
    if key==b'v' and cheat_on: magnet_on = not magnet_on
    if key==b'r':
        reset_world(); 
        game_over=False

def specialKeyListener(key, x, y):
    global cam_angle, cam_height
    if third_person:
        if key==GLUT_KEY_LEFT:  cam_angle += 2.0
        if key==GLUT_KEY_RIGHT: cam_angle -= 2.0
        if key==GLUT_KEY_UP:    cam_height += 5.0
        if key==GLUT_KEY_DOWN:  cam_height = max(50.0, cam_height-5.0)

def mouseListener(button, state, x, y):
    global third_person
    if button==GLUT_RIGHT_BUTTON and state==GLUT_DOWN:
        third_person = not third_person
    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        fire_bullet()

# ---------- Idle ----------
def idle():
    global _last, fire_cd
    now=time.time()
    dt=max(0.0, min(0.05, now-_last))
    _last=now
    if fire_cd>0.0: fire_cd=max(0.0, fire_cd-dt)
    update(dt)
    glutPostRedisplay()

# ---------- Init ----------
def main():
    random.seed(7)
    reset_world()
    init_space_theme()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Velocity Run - 3D Endless Runner")
    glEnable(GL_DEPTH_TEST)  
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__=="__main__":
    main()
