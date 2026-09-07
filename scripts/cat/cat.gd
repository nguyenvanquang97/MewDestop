class_name Cat
extends Node3D

## Core 3D Cat Controller: manages 3D visual model, dynamic 3D multi-angle rotation,
## cursor head-tracking (look-at), emotes (heart/zzz/fish/question), and state machine.

signal clicked()
signal right_clicked(screen_pos: Vector2)

@onready var visual_root: Node3D = $VisualRoot
@onready var drop_shadow: MeshInstance3D = get_node_or_null("DropShadow")
@onready var emote_bubble: Node = get_node_or_null("EmoteBubble")
@onready var cat_model: Node3D = get_node_or_null("VisualRoot/CatModel")
@onready var shiba_model: Node3D = get_node_or_null("VisualRoot/ShibaModel")
@onready var cat_anim_player: AnimationPlayer = get_node_or_null("VisualRoot/CatModel/AnimationPlayer")
@onready var shiba_anim_player: AnimationPlayer = get_node_or_null("VisualRoot/ShibaModel/AnimationPlayer")
@onready var animation_player: AnimationPlayer = get_node_or_null("VisualRoot/CatModel/AnimationPlayer")

var pet_type: String = "cat" # "cat" or "shiba"
var _shiba_initialized: bool = false

var states: Dictionary = {}
var current_state: CatState
var current_state_name: String = ""

const DrinkState = preload("res://scripts/cat/states/drink.gd")

var behavior: CatBehaviorConfig = CatBehaviorConfig.new()
var stats: CatStats = CatStats.new()

@export var base_scale: float = 1.0

var camera: Camera3D
var screen_manager: ScreenManager

var current_screen_x: float = 600.0
var current_screen_y: float = 900.0
var facing_direction: float = 1.0 # 1.0 = Right, -1.0 = Left

# 3D Dynamic Rotation & Head-tracking
var target_rotation_y: float = 0.0
var target_tilt_z: float = 0.0
var target_pitch_x: float = 0.0

# Eye blinking & Emote timers
var _blink_timer: float = 3.0
var _is_blinking: bool = false
var _blink_duration: float = 0.12

# Mouse interaction tracking
var is_mouse_down_on_cat: bool = false
var mouse_down_time: float = 0.0
var mouse_down_pos: Vector2 = Vector2.ZERO
const CLICK_THRESHOLD_TIME: float = 0.25
const CLICK_THRESHOLD_DIST: float = 10.0

# Procedural animation parameters
var _proc_anim_time: float = 0.0
const MilkBowlScene = preload("res://scenes/items/MilkBowl.tscn")
var milk_bowl: MilkBowlItem = null

var skeleton: Skeleton3D = null
var neck_bone_idx: int = -1
var head_bone_idx: int = -1
var spine_bone_idx: int = -1
var tail_bone_idx: int = -1
var left_elbow_idx: int = -1
var right_elbow_idx: int = -1
var _drink_bend_weight: float = 0.0

func _ready() -> void:
	process_priority = 10
	scale = Vector3.ONE * base_scale
	_setup_animations()
	_setup_cartoon_materials()
	_setup_shiba_animations()
	_setup_shiba_materials()
	_setup_milk_bowl()
	_setup_states()
	set_pet_type(pet_type)

func set_pet_type(type: String) -> void:
	pet_type = type.to_lower()
	if pet_type != "shiba":
		pet_type = "cat"

	if not cat_model:
		cat_model = get_node_or_null("VisualRoot/CatModel")
	if not shiba_model:
		shiba_model = get_node_or_null("VisualRoot/ShibaModel")
	if not cat_anim_player:
		cat_anim_player = get_node_or_null("VisualRoot/CatModel/AnimationPlayer")
	if not shiba_anim_player:
		shiba_anim_player = get_node_or_null("VisualRoot/ShibaModel/AnimationPlayer")

	if pet_type == "shiba":
		if cat_model:
			cat_model.visible = false
		if shiba_model:
			shiba_model.visible = true
		animation_player = shiba_anim_player
		_setup_shiba_animations()
		_setup_shiba_materials()
	else:
		if cat_model:
			cat_model.visible = true
		if shiba_model:
			shiba_model.visible = false
		animation_player = cat_anim_player

	play_animation(current_state_name if current_state_name != "" else "Idle")

func toggle_pet_type() -> void:
	if pet_type == "cat":
		set_pet_type("shiba")
		show_emote("🐶")
	else:
		set_pet_type("cat")
		show_emote("heart")

func _setup_shiba_animations() -> void:
	if not shiba_anim_player:
		shiba_anim_player = get_node_or_null("VisualRoot/ShibaModel/AnimationPlayer")
	if not shiba_anim_player or _shiba_initialized:
		return
	_shiba_initialized = true
	shiba_anim_player.process_priority = -10
	for a_name in ["Idle", "Idle_2", "Walk", "Gallop", "Eating"]:
		if shiba_anim_player.has_animation(a_name):
			var a = shiba_anim_player.get_animation(a_name)
			a.loop_mode = Animation.LOOP_LINEAR
	if shiba_anim_player.has_animation("Death"):
		var d = shiba_anim_player.get_animation("Death")
		d.loop_mode = Animation.LOOP_NONE
	if shiba_anim_player.has_animation("Gallop_Jump"):
		var gj = shiba_anim_player.get_animation("Gallop_Jump")
		gj.loop_mode = Animation.LOOP_NONE
	if not shiba_anim_player.animation_finished.is_connected(_on_animation_finished):
		shiba_anim_player.animation_finished.connect(_on_animation_finished)

func _setup_shiba_materials() -> void:
	var mesh_inst: MeshInstance3D = find_child("ShibaInu", true, false)
	if not mesh_inst or not mesh_inst.mesh:
		return
	var surf_count = mesh_inst.mesh.get_surface_count()
	for surf in range(surf_count):
		var base_mat: Material = mesh_inst.get_active_material(surf)
		if not base_mat or not (base_mat is StandardMaterial3D):
			continue
		var std_mat: StandardMaterial3D = base_mat.duplicate()
		std_mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
		std_mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
		std_mat.roughness = 0.4
		std_mat.metallic = 0.0

		var outline_mat = StandardMaterial3D.new()
		outline_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		outline_mat.albedo_color = Color(0.12, 0.10, 0.15, 1.0)
		outline_mat.cull_mode = BaseMaterial3D.CULL_FRONT
		outline_mat.grow = true
		outline_mat.grow_amount = 0.015
		std_mat.next_pass = outline_mat
		mesh_inst.set_surface_override_material(surf, std_mat)

func _on_animation_finished(anim_name: String) -> void:
	if current_state_name == "Walk":
		var walk_state: WalkState = states.get("Walk") as WalkState
		if walk_state and walk_state.is_running and pet_type == "shiba" and walk_state.total_distance >= 1000.0:
			play_animation("Gallop")
		else:
			play_animation("walk")
	elif current_state_name == "Idle":
		play_animation("idle")
	elif current_state_name == "Sit":
		play_animation("sit")
	elif current_state_name == "Drink":
		play_animation("drink")

func _setup_animations() -> void:
	if not cat_anim_player:
		cat_anim_player = get_node_or_null("VisualRoot/CatModel/AnimationPlayer")
	if not cat_anim_player:
		return
	cat_anim_player.process_priority = -10
	for anim_name in ["walk", "idle"]:
		if cat_anim_player.has_animation(anim_name):
			var a = cat_anim_player.get_animation(anim_name)
			a.loop_mode = Animation.LOOP_LINEAR

	if not cat_anim_player.animation_finished.is_connected(_on_animation_finished):
		cat_anim_player.animation_finished.connect(_on_animation_finished)

	skeleton = find_child("Skeleton3D", true, false)
	if skeleton:
		neck_bone_idx = skeleton.find_bone("Joint3")
		head_bone_idx = skeleton.find_bone("Joint4")
		spine_bone_idx = skeleton.find_bone("Joint2")
		tail_bone_idx = skeleton.find_bone("Joint7")
		left_elbow_idx = skeleton.find_bone("Joint14")
		right_elbow_idx = skeleton.find_bone("Joint17")

	_create_sit_drink_animation()

func _create_sit_drink_animation() -> void:
	if not cat_anim_player:
		cat_anim_player = get_node_or_null("VisualRoot/CatModel/AnimationPlayer")
	if not cat_anim_player:
		return
	var lib: AnimationLibrary = cat_anim_player.get_animation_library("")
	if not lib or not lib.has_animation("idle"):
		return
	if lib.has_animation("sit_drink"):
		lib.remove_animation("sit_drink")

	var idle = lib.get_animation("idle")
	var sit: Animation = idle.duplicate()
	sit.loop_mode = Animation.LOOP_LINEAR
	sit.length = 2.0

	var find_t = func(name_part: String, track_type: int) -> int:
		for t in range(sit.get_track_count()):
			if name_part in str(sit.track_get_path(t)) and sit.track_get_type(t) == track_type:
				return t
		return -1

	var set_static_key = func(name_part: String, track_type: int, val: Variant):
		var t = find_t.call(name_part, track_type)
		if t >= 0:
			while sit.track_get_key_count(t) > 0:
				sit.track_remove_key(t, 0)
			sit.track_insert_key(t, 0.0, val)
			sit.track_insert_key(t, 2.0, val)

	# 1. Hông hạ thấp & nghiêng lên thành dáng ngồi vững chắc trên sàn
	set_static_key.call("Joint1", Animation.TYPE_POSITION_3D, Vector3(0.0, 3.0, -0.6))
	set_static_key.call("Joint1", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(28.0)))

	# 2. Ngực nghiêng về phía trước hướng về đĩa sữa
	set_static_key.call("Joint2", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-2.0)))

	# 3. Hai đùi sau gập về phía trước sát sườn
	set_static_key.call("Joint19", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-55.0)))
	set_static_key.call("Joint23", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-55.0)))

	# 4. Hai đầu gối sau gập gập xuống sàn
	set_static_key.call("Joint20", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(80.0)))
	set_static_key.call("Joint24", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(80.0)))

	# 5. Cổ chân & bàn chân sau duỗi phẳng trên sàn
	set_static_key.call("Joint21", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-35.0)))
	set_static_key.call("Joint25", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-35.0)))

	# 6. Hai chân trước chống thẳng trên sàn phía sau đĩa sữa (không dẫm vào đĩa)
	set_static_key.call("Joint13", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-18.0)))
	set_static_key.call("Joint16", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-18.0)))
	set_static_key.call("Joint14", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(6.0)))
	set_static_key.call("Joint17", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(6.0)))

	# 7. Cổ và đầu cúi xuống thanh thoát, biểu cảm tự nhiên, nhấp nhô nhẹ nhàng liếm sữa
	var t_neck = find_t.call("Joint3", Animation.TYPE_ROTATION_3D)
	if t_neck >= 0:
		while sit.track_get_key_count(t_neck) > 0:
			sit.track_remove_key(t_neck, 0)
		sit.track_insert_key(t_neck, 0.0, Quaternion(Vector3.RIGHT, deg_to_rad(-45.0)))
		sit.track_insert_key(t_neck, 0.5, Quaternion(Vector3.RIGHT, deg_to_rad(-52.0)))
		sit.track_insert_key(t_neck, 1.0, Quaternion(Vector3.RIGHT, deg_to_rad(-45.0)))
		sit.track_insert_key(t_neck, 1.5, Quaternion(Vector3.RIGHT, deg_to_rad(-52.0)))
		sit.track_insert_key(t_neck, 2.0, Quaternion(Vector3.RIGHT, deg_to_rad(-45.0)))

	var t_head = find_t.call("Joint4", Animation.TYPE_ROTATION_3D)
	if t_head >= 0:
		while sit.track_get_key_count(t_head) > 0:
			sit.track_remove_key(t_head, 0)
		sit.track_insert_key(t_head, 0.0, Quaternion(Vector3.RIGHT, deg_to_rad(-20.0)))
		sit.track_insert_key(t_head, 0.5, Quaternion(Vector3.RIGHT, deg_to_rad(-26.0)))
		sit.track_insert_key(t_head, 1.0, Quaternion(Vector3.RIGHT, deg_to_rad(-20.0)))
		sit.track_insert_key(t_head, 1.5, Quaternion(Vector3.RIGHT, deg_to_rad(-26.0)))
		sit.track_insert_key(t_head, 2.0, Quaternion(Vector3.RIGHT, deg_to_rad(-20.0)))

	lib.add_animation("sit_drink", sit)
	sit_drink_anim_ready = true

var sit_drink_anim_ready: bool = false

func _setup_cartoon_materials() -> void:
	var mesh_inst: MeshInstance3D = find_child("cat", true, false)
	if not mesh_inst:
		return
	var base_mat: StandardMaterial3D = mesh_inst.get_active_material(0)
	if not base_mat:
		base_mat = StandardMaterial3D.new()
	else:
		base_mat = base_mat.duplicate()

	# Apply Anime Cel-shading / Toon Shader
	base_mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	base_mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
	base_mat.roughness = 0.35
	base_mat.metallic = 0.0
	
	# Anime Rim Lighting for crisp silhouette separation
	base_mat.rim_enabled = true
	base_mat.rim = 0.7
	base_mat.rim_tint = 0.5

	# Hand-drawn Cartoon Ink Outline
	var outline_mat = StandardMaterial3D.new()
	outline_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	outline_mat.albedo_color = Color(0.1, 0.1, 0.15, 1.0)
	outline_mat.cull_mode = BaseMaterial3D.CULL_FRONT
	outline_mat.grow = true
	outline_mat.grow_amount = 0.08
	base_mat.next_pass = outline_mat

	mesh_inst.set_surface_override_material(0, base_mat)

func initialize(cam: Camera3D, scr_mgr: ScreenManager) -> void:
	camera = cam
	screen_manager = scr_mgr
	current_screen_x = screen_manager.screen_width * 0.5
	current_screen_y = screen_manager.screen_height * 0.5
	sync_world_position_from_screen()
	change_state("Idle")

func _setup_states() -> void:
	states["Idle"] = IdleState.new()
	states["Walk"] = WalkState.new()
	states["Sit"] = SitState.new()
	states["Sleep"] = SleepState.new()
	states["Dragged"] = DraggedState.new()
	states["Pet"] = PetState.new()
	states["Drink"] = DrinkState.new()

	for state_name in states:
		var s: CatState = states[state_name]
		s.cat = self
		s.name = state_name
		add_child(s)

func _setup_milk_bowl() -> void:
	if milk_bowl:
		milk_bowl.queue_free()
	milk_bowl = MilkBowlScene.instantiate()
	milk_bowl.visible = false
	add_child(milk_bowl)

func show_milk_bowl(show: bool) -> void:
	if not milk_bowl:
		return
	if show:
		var yaw = target_rotation_y
		var heading = Vector3(sin(yaw), 0.0, cos(yaw))
		# Place bowl right on floor plane where paws rest, centered in front
		var dist = 0.92 if pet_type == "shiba" else 0.44
		milk_bowl.position = heading * dist
		milk_bowl.position.y = -0.135 if pet_type == "shiba" else 0.0
		milk_bowl.rotation = Vector3(0.0, yaw, 0.0)
		milk_bowl.pop_in()
	else:
		milk_bowl.pop_out()

func set_milk_bowl_lapping(active: bool) -> void:
	if milk_bowl and milk_bowl.has_method("set_lapping"):
		milk_bowl.set_lapping(active)

func set_milk_bowl_level(ratio: float) -> void:
	if milk_bowl and milk_bowl.has_method("set_milk_level"):
		milk_bowl.set_milk_level(ratio)

func change_state(new_state_name: String) -> void:
	if not states.has(new_state_name):
		push_warning("[Cat] State '%s' not found! Falling back to Idle." % new_state_name)
		new_state_name = "Idle"

	if current_state:
		current_state.exit()

	var prev = current_state_name
	current_state_name = new_state_name
	current_state = states[new_state_name]
	current_state.enter(prev)

func _process(delta: float) -> void:
	stats.update(delta)
	if current_state:
		current_state.update(delta)

	_update_blinking(delta)
	_update_look_at_cursor(delta)
	_update_procedural_animation(delta)
	_update_drop_shadow()

func _physics_process(delta: float) -> void:
	if current_state:
		current_state.physics_update(delta)

func play_animation(anim_name: String) -> void:
	var target_player: AnimationPlayer = shiba_anim_player if pet_type == "shiba" else cat_anim_player
	if not target_player:
		target_player = animation_player
	if not target_player:
		return

	var mapped = anim_name.to_lower()
	if pet_type == "shiba":
		match mapped:
			"walk", "run": mapped = "Walk"
			"gallop": mapped = "Gallop"
			"gallop_jump", "jump": mapped = "Gallop_Jump"
			"idle": mapped = "Idle"
			"sit": mapped = "Idle_2_HeadLow"
			"drink", "eat", "sit_drink": mapped = "Eating"
			"sleep": mapped = "Death"
			"pet", "play", "dragged": mapped = "Jump_ToIdle"
			_:
				if target_player.has_animation(anim_name):
					mapped = anim_name
				else:
					mapped = "Idle"
	else:
		match mapped:
			"walk", "run": mapped = "walk"
			"idle": mapped = "idle"
			"sit", "sit_drink", "drink":
				mapped = "sit_drink" if target_player.has_animation("sit_drink") else "idle"
			"sleep": mapped = "dead"
			"pet", "play", "dragged": mapped = "attack"
			_:
				if target_player.has_animation(anim_name):
					mapped = anim_name
				else:
					mapped = "idle"

	if target_player.has_animation(mapped):
		target_player.play(mapped)

func is_galloping() -> bool:
	var target_player: AnimationPlayer = shiba_anim_player if pet_type == "shiba" else cat_anim_player
	if not target_player:
		target_player = animation_player
	if target_player and target_player.is_playing():
		if target_player.current_animation.to_lower().begins_with("gallop"):
			return true
	if current_state_name == "Walk" and current_state and current_state.get("is_running") == true and pet_type == "shiba":
		return true
	return false

## Sets dynamic 3D heading smoothly (avoids flat 2D cardboard look)
func set_facing_direction(dir: float) -> void:
	facing_direction = signf(dir)
	if facing_direction == 0.0:
		facing_direction = 1.0

	if current_state_name == "Walk":
		if is_galloping():
			target_rotation_y = deg_to_rad(90.0) if facing_direction > 0 else deg_to_rad(-90.0)
		else:
			target_rotation_y = deg_to_rad(82.0) if facing_direction > 0 else deg_to_rad(-82.0)
	elif current_state_name == "Sit":
		target_rotation_y = deg_to_rad(25.0) if facing_direction > 0 else deg_to_rad(-25.0)
	else:
		target_rotation_y = deg_to_rad(15.0) if facing_direction > 0 else deg_to_rad(-15.0)

## Smoothly rotates cat towards actual 2D movement vector across 360 degrees
func orient_toward_vector(dir: Vector2) -> void:
	if dir.length_squared() < 0.001:
		return
	facing_direction = 1.0 if dir.x >= 0.0 else -1.0
	if is_galloping():
		# Direct lateral heading (Left/Right) in screen plane; incline along ground slope is handled via target_pitch_x
		target_rotation_y = deg_to_rad(90.0) if facing_direction > 0 else deg_to_rad(-90.0)
	else:
		# Subtle 3D perspective angle for casual stroll
		target_rotation_y = deg_to_rad(85.0) if facing_direction > 0 else deg_to_rad(-85.0)

## Adjusts walk animation playback speed to match actual ground velocity (eliminates foot sliding)
func set_walk_animation_speed(ratio: float) -> void:
	var target_player: AnimationPlayer = shiba_anim_player if pet_type == "shiba" else cat_anim_player
	if not target_player:
		target_player = animation_player
	if target_player:
		target_player.speed_scale = clampf(ratio, 0.35, 1.5)

## Smoothly turns cat to look towards mouse cursor when idle or sitting
func _update_look_at_cursor(_delta: float) -> void:
	if current_state_name != "Idle" and current_state_name != "Sit":
		return
	if not camera or not screen_manager:
		return

	var mouse_screen = DisplayServer.mouse_get_position()
	var cur_screen = DisplayServer.window_get_current_screen()
	var screen_pos = DisplayServer.screen_get_position(cur_screen)
	var local_mouse_x = mouse_screen.x - screen_pos.x
	var diff_x = local_mouse_x - current_screen_x

	if absf(diff_x) < 550.0 and absf(diff_x) > 30.0:
		# Angle towards mouse cursor with soft clamping (up to +/- 35 degrees)
		var gaze_angle = clampf(diff_x / 450.0, -0.6, 0.6)
		target_rotation_y = gaze_angle

## Simulates natural eye blinking
func _update_blinking(delta: float) -> void:
	_blink_timer -= delta
	if _blink_timer <= 0.0:
		_is_blinking = true
		_blink_timer = randf_range(2.8, 5.5)
		# Blink finishes after short duration
		get_tree().create_timer(_blink_duration).timeout.connect(func(): _is_blinking = false)

## Shows floating animated 3D emote icon (❤️, 💤, 🐟, ❓, 💧, ✨)
func show_emote(type: String) -> void:
	if not emote_bubble:
		return
	var emoji = "❤️"
	match type:
		"heart": emoji = "❤️"
		"pet": emoji = "🐶" if pet_type == "shiba" else "❤️"
		"sleep": emoji = "💤"
		"hungry", "fish", "feed": emoji = "🍖" if pet_type == "shiba" else "🐟"
		"milk", "drink": emoji = "🥛"
		"question": emoji = "❓"
		"sweat": emoji = "💧"
		"sparkle": emoji = "✨"
		"play": emoji = "🎾" if pet_type == "shiba" else "🧶"
		_: emoji = type
	emote_bubble.pop(emoji)

func sync_world_position_from_screen() -> void:
	if not camera or not screen_manager:
		return
	var world_pos = screen_manager.screen_to_world(
		Vector2(current_screen_x, current_screen_y),
		camera,
		0.0
	)
	global_position = world_pos

## Returns the 2D bounding rectangle of the cat projected onto screen space
func get_screen_bounding_rect() -> Rect2:
	if not camera:
		return Rect2(current_screen_x - 100, current_screen_y - 100, 200, 200)

	var foot_screen = camera.unproject_position(global_position)
	var head_screen = camera.unproject_position(global_position + Vector3(0, 1.1 * scale.y, 0))
	var cat_h = maxf(absf(foot_screen.y - head_screen.y) * 1.4, 140.0)
	var cat_w = cat_h * 1.2
	var min_y = minf(foot_screen.y, head_screen.y) - 20.0
	var rect = Rect2(foot_screen.x - cat_w * 0.5, min_y, cat_w, cat_h)
	if milk_bowl and milk_bowl.visible:
		var bowl_screen = camera.unproject_position(milk_bowl.global_position)
		var bowl_rect = Rect2(bowl_screen.x - 70.0, bowl_screen.y - 45.0, 140.0, 90.0)
		rect = rect.merge(bowl_rect)
	return rect

## Orders the pet to rush/sprint towards the specified 2D screen coordinate
func run_to(screen_pos: Vector2) -> void:
	if not screen_manager:
		return

	var target = screen_manager.clamp_screen_pos(screen_pos)

	# If currently drinking or sleeping, interrupt immediately and pack bowl
	if milk_bowl and milk_bowl.visible:
		show_milk_bowl(false)

	# Snappy alert emote
	show_emote("❗")

	var walk_state: WalkState = states.get("Walk") as WalkState
	if not walk_state:
		return

	if current_state_name == "Walk":
		walk_state.set_destination(target, true)
	else:
		walk_state.has_target_override = true
		walk_state.target_override = target
		walk_state.is_running = true
		change_state("Walk")

## Resets mouse down/drag tracking so pending clicks or drags are aborted
func cancel_mouse_interaction() -> void:
	is_mouse_down_on_cat = false

## Handles mouse input forwarded from Main or Area3D
func handle_mouse_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mouse_pos = event.position
		var hit_rect = get_screen_bounding_rect().grow(10.0)

		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				if hit_rect.has_point(mouse_pos):
					is_mouse_down_on_cat = true
					mouse_down_time = Time.get_ticks_msec() / 1000.0
					mouse_down_pos = mouse_pos
			else:
				if is_mouse_down_on_cat:
					is_mouse_down_on_cat = false
					var press_duration = (Time.get_ticks_msec() / 1000.0) - mouse_down_time
					var dist = mouse_pos.distance_to(mouse_down_pos)

					if current_state_name == "Dragged":
						current_state.handle_input(event)
					elif press_duration < CLICK_THRESHOLD_TIME and dist < CLICK_THRESHOLD_DIST:
						clicked.emit()
						change_state("Pet")

		elif event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
			if hit_rect.has_point(mouse_pos):
				right_clicked.emit(mouse_pos)

		elif event.button_index == MOUSE_BUTTON_MIDDLE and event.pressed:
			run_to(mouse_pos)

	elif event is InputEventMouseMotion:
		if is_mouse_down_on_cat and current_state_name != "Dragged":
			var dist = event.position.distance_to(mouse_down_pos)
			if dist > CLICK_THRESHOLD_DIST:
				change_state("Dragged")

	if current_state:
		current_state.handle_input(event)

## Keeps drop shadow grounded with inverse-scale height cue
func _update_drop_shadow() -> void:
	if not drop_shadow or not visual_root:
		return
	var height = visual_root.position.y
	drop_shadow.position = Vector3(0, 0.02, 0)
	var shadow_scale = clampf(1.0 - height * 0.7, 0.45, 1.15)
	drop_shadow.scale = Vector3(shadow_scale, 1.0, shadow_scale)

## Multi-action lively 3D motion with natural breathing, banking, and eye blinks
func _update_procedural_animation(delta: float) -> void:
	if not visual_root:
		return
	_proc_anim_time += delta

	# Smooth 3D Yaw interpolation
	visual_root.rotation.y = lerp_angle(visual_root.rotation.y, target_rotation_y, delta * 7.5)

	# Blink squashes height by 4% momentarily
	var blink_factor = 0.96 if _is_blinking else 1.0

	match current_state_name:
		"Idle":
			# Breathing bob + subtle head tilt + 3D downward viewing pitch
			var bob = sin(_proc_anim_time * 2.8) * 0.025
			visual_root.position.y = bob
			visual_root.rotation.z = lerp_angle(visual_root.rotation.z, sin(_proc_anim_time * 1.4) * 0.03, delta * 6.0)
			visual_root.rotation.x = lerp_angle(visual_root.rotation.x, 0.20, delta * 6.0)
			visual_root.scale = Vector3(1.0 + bob * 0.4, (1.0 - bob * 0.4) * blink_factor, 1.0 + bob * 0.4)

		"Walk":
			var is_gallop = is_galloping()
			if is_gallop:
				# Gallop sprint: Natural skeletal animation handles spine and leg dynamics
				# Pitch body along ground slope vector defined by start and end points
				visual_root.rotation.x = lerp_angle(visual_root.rotation.x, target_pitch_x, delta * 8.0)
				visual_root.position.y = lerpf(visual_root.position.y, 0.0, delta * 8.0)
				# Dynamic bank into turns
				var angle_diff = wrapf(target_rotation_y - visual_root.rotation.y, -PI, PI)
				var bank = clampf(-angle_diff * 0.25, -0.10, 0.10)
				visual_root.rotation.z = lerp_angle(visual_root.rotation.z, bank, delta * 9.0)
				visual_root.scale = Vector3(1.0, blink_factor, 1.0)
			else:
				var trot = sin(_proc_anim_time * 13.0)
				var bounce = absf(sin(_proc_anim_time * 13.0)) * 0.04
				# Dynamic bank into turns based on turning rate
				var angle_diff = wrapf(target_rotation_y - visual_root.rotation.y, -PI, PI)
				var bank = clampf(-angle_diff * 0.25, -0.12, 0.12)
				visual_root.position.y = bounce
				visual_root.rotation.z = lerp_angle(visual_root.rotation.z, bank + trot * 0.03, delta * 9.0)
				visual_root.rotation.x = lerp_angle(visual_root.rotation.x, target_pitch_x, delta * 6.0)
				# Cartoon squash and stretch on each step!
				var sq_y = 1.0 - bounce * 0.8
				var st_xz = 1.0 + bounce * 0.4
				visual_root.scale = Vector3(st_xz, sq_y * blink_factor, st_xz)

		"Sit":
			# Lower, cozy squat with tilted cute head
			visual_root.position.y = lerpf(visual_root.position.y, -0.07, delta * 6.0)
			visual_root.rotation.z = lerp_angle(visual_root.rotation.z, 0.06, delta * 6.0)
			visual_root.rotation.x = lerp_angle(visual_root.rotation.x, 0.16, delta * 6.0)
			visual_root.scale = Vector3(1.08, 0.92 * blink_factor, 1.08)

		"Sleep":
			# Curled up, deep calm breathing
			var breath = sin(_proc_anim_time * 1.5) * 0.035
			visual_root.position.y = lerpf(visual_root.position.y, -0.12, delta * 4.0)
			visual_root.rotation.z = lerp_angle(visual_root.rotation.z, 0.12, delta * 4.0)
			visual_root.rotation.x = lerp_angle(visual_root.rotation.x, 0.22, delta * 4.0)
			visual_root.scale = Vector3(1.15, (0.80 + breath), 1.15)

		"Dragged":
			# Dangling stretch, pendulum sway
			visual_root.position.y = 0.0
			visual_root.rotation.z = sin(_proc_anim_time * 6.0) * 0.2
			visual_root.rotation.x = 0.0
			visual_root.scale = Vector3(0.85, 1.25, 0.85)

		"Pet":
			# Rapid happy purr vibration + spring squash
			var purr = sin(_proc_anim_time * 26.0) * 0.035
			visual_root.position.y = absf(sin(_proc_anim_time * 8.0)) * 0.04
			visual_root.rotation.z = purr
			visual_root.scale = Vector3(1.15 + purr, 1.10 - purr, 1.15 + purr)

		"Drink":
			# Soft natural posture standing beside bowl, gentle calm breathing
			var bob = sin(_proc_anim_time * 2.8) * 0.02
			visual_root.position.y = lerpf(visual_root.position.y, -0.03 + bob, delta * 6.0)
			visual_root.rotation.x = lerp_angle(visual_root.rotation.x, 0.20, delta * 6.0)
			visual_root.rotation.z = lerp_angle(visual_root.rotation.z, 0.02, delta * 6.0)
			visual_root.scale = Vector3(1.02, 0.98 * blink_factor, 1.02)
