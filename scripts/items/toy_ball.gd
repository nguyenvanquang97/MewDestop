class_name ToyBallItem
extends Node3D

## 3D Stylized Bouncy Toy Ball with dynamic bounces,
## rotational rolling physics, dynamic drop shadow, and particle effects.

signal landed(bounce_number: int)
signal settled

@onready var model_root: Node3D = $ModelRoot
@onready var ball_mesh: MeshInstance3D = $ModelRoot/BallMesh
@onready var seam_mesh: MeshInstance3D = $ModelRoot/SeamMesh
@onready var drop_shadow: MeshInstance3D = $DropShadow
@onready var bounce_particles: CPUParticles3D = $BounceParticles
@onready var catch_particles: CPUParticles3D = $CatchParticles

enum State { IDLE, THROWN, RESTING, CAUGHT, POP_OUT }
var state: State = State.IDLE

# Trajectory parameters
var _start_world: Vector3 = Vector3.ZERO
var _first_bounce_world: Vector3 = Vector3.ZERO
var _target_world: Vector3 = Vector3.ZERO
var _has_explicit_first_bounce: bool = false
var _flight_time: float = 0.0
var _flight_duration: float = 1.2
var _max_height: float = 0.9
var _spin_axis: Vector3 = Vector3.FORWARD
var _spin_speed: float = 14.0

# Target screen coordinates
var target_screen_pos: Vector2 = Vector2.ZERO

# Bone attachment tracking for CAUGHT state
var _attach_target: Node3D = null
var _attach_offset: Vector3 = Vector3.ZERO

# Bounces timings (fraction of total duration: 0.0 -> 0.50 -> 0.85 -> 1.0)
const BOUNCE_1_END: float = 0.50
const BOUNCE_2_END: float = 0.85
var _last_bounce: int = 0

var _tween: Tween = null

func _ensure_nodes() -> void:
	if not model_root:
		model_root = get_node_or_null("ModelRoot")
	if not ball_mesh:
		ball_mesh = get_node_or_null("ModelRoot/BallMesh")
	if not seam_mesh:
		seam_mesh = get_node_or_null("ModelRoot/SeamMesh")
	if not drop_shadow:
		drop_shadow = get_node_or_null("DropShadow")
	if not bounce_particles:
		bounce_particles = get_node_or_null("BounceParticles")
	if not catch_particles:
		catch_particles = get_node_or_null("CatchParticles")

func _ready() -> void:
	top_level = true
	_ensure_nodes()
	visible = false
	if bounce_particles:
		bounce_particles.emitting = false
	if catch_particles:
		catch_particles.emitting = false

func _process(delta: float) -> void:
	match state:
		State.THROWN:
			_update_thrown(delta)
		State.CAUGHT:
			_update_caught()
		State.RESTING:
			_update_shadow(0.0)

## Throws the ball from start_pos to target_pos in world coordinates
func throw_ball(start_pos: Vector3, target_pos: Vector3, duration: float = 1.2, height: float = 0.95) -> void:
	_ensure_nodes()
	if _tween and _tween.is_valid():
		_tween.kill()

	_start_world = start_pos
	_first_bounce_world = target_pos
	_target_world = target_pos
	_has_explicit_first_bounce = false
	_flight_duration = maxf(duration, 0.5)
	_max_height = height
	_flight_time = 0.0
	_last_bounce = 0

	# Calculate spin axis perpendicular to movement direction
	var move_dir = (_target_world - _start_world)
	move_dir.y = 0.0
	if move_dir.length_squared() > 0.001:
		_spin_axis = Vector3.UP.cross(move_dir.normalized()).normalized()
	else:
		_spin_axis = Vector3.FORWARD

	global_position = _start_world
	model_root.position = Vector3.ZERO
	model_root.rotation = Vector3.ZERO
	scale = Vector3.ONE
	visible = true
	state = State.THROWN

## Throws the ball so its first ground bounce lands precisely at first_bounce_pos,
## followed by smaller forward hops settling at settle_pos
func throw_ball_to_first_bounce(start_pos: Vector3, first_bounce_pos: Vector3, settle_pos: Vector3, duration: float = 1.25, height: float = 0.95) -> void:
	_ensure_nodes()
	if _tween and _tween.is_valid():
		_tween.kill()

	_start_world = start_pos
	_first_bounce_world = first_bounce_pos
	_target_world = settle_pos
	_has_explicit_first_bounce = true
	_flight_duration = maxf(duration, 0.5)
	_max_height = height
	_flight_time = 0.0
	_last_bounce = 0

	# Calculate spin axis perpendicular to movement direction
	var move_dir = (_first_bounce_world - _start_world)
	move_dir.y = 0.0
	if move_dir.length_squared() > 0.001:
		_spin_axis = Vector3.UP.cross(move_dir.normalized()).normalized()
	else:
		_spin_axis = Vector3.FORWARD

	global_position = _start_world
	model_root.position = Vector3.ZERO
	model_root.rotation = Vector3.ZERO
	scale = Vector3.ONE
	visible = true
	state = State.THROWN

func _update_thrown(delta: float) -> void:
	_flight_time += delta
	var t = clampf(_flight_time / _flight_duration, 0.0, 1.0)

	# Horizontal interpolation
	var current_xz: Vector3
	if _has_explicit_first_bounce:
		if t <= BOUNCE_1_END:
			# First arc: travels from launch point to first bounce point (phase 0.0 -> 1.0)
			var phase = t / BOUNCE_1_END
			current_xz = _start_world.lerp(_first_bounce_world, phase)
		else:
			# Subsequent hops: travels from first bounce to resting settle target
			var phase = (t - BOUNCE_1_END) / (1.0 - BOUNCE_1_END)
			var roll_phase = ease(phase, 0.75) # Decelerates smoothly into rest
			current_xz = _first_bounce_world.lerp(_target_world, roll_phase)
	else:
		var horiz_t = ease(t, 0.85)
		current_xz = _start_world.lerp(_target_world, horiz_t)

	# Vertical bounce curve: 3 distinct parabolic hops
	var current_y = 0.0
	var bounce_idx = 0
	var start_y_offset = 0.0

	var floor_y = _first_bounce_world.y if _has_explicit_first_bounce else _target_world.y

	if t <= BOUNCE_1_END:
		# First big arc: 0.0 to 0.50
		var phase = t / BOUNCE_1_END
		current_y = 4.0 * _max_height * phase * (1.0 - phase)
		start_y_offset = maxf(_start_world.y - floor_y, 0.0) * (1.0 - phase)
		bounce_idx = 1
	elif t <= BOUNCE_2_END:
		# Second medium bounce: 0.50 to 0.85
		var phase = (t - BOUNCE_1_END) / (BOUNCE_2_END - BOUNCE_1_END)
		current_y = 4.0 * (_max_height * 0.38) * phase * (1.0 - phase)
		bounce_idx = 2
	else:
		# Third tiny settling hop: 0.85 to 1.0
		var phase = (t - BOUNCE_2_END) / (1.0 - BOUNCE_2_END)
		current_y = 4.0 * (_max_height * 0.12) * phase * (1.0 - phase)
		bounce_idx = 3

	# Ground collision / impact bounce trigger
	if bounce_idx > _last_bounce and _last_bounce > 0:
		_trigger_bounce_impact(bounce_idx)
	_last_bounce = bounce_idx

	# Set position
	global_position = Vector3(current_xz.x, floor_y + current_y + start_y_offset, current_xz.z)

	# Rolling tumble rotation
	var current_speed = (1.0 - t * 0.5) * _spin_speed
	model_root.rotate(_spin_axis, current_speed * delta)

	# Update drop shadow
	_update_shadow(current_y + start_y_offset)

	# Landing finished
	if t >= 1.0:
		state = State.RESTING
		global_position = _target_world
		_update_shadow(0.0)
		_trigger_bounce_impact(3)
		settled.emit()

func _trigger_bounce_impact(b_num: int) -> void:
	landed.emit(b_num)
	if bounce_particles:
		bounce_particles.restart()
		bounce_particles.emitting = true

func _update_shadow(height: float) -> void:
	if not drop_shadow:
		return
	# Keep shadow flat on floor beneath the ball
	drop_shadow.global_position = Vector3(global_position.x, _target_world.y + 0.003, global_position.z)
	drop_shadow.rotation = Vector3.ZERO
	# Shadow expands and fades as height increases
	var h_clamped = clampf(height / _max_height, 0.0, 1.0)
	var shadow_scale = lerpf(0.55, 0.90, h_clamped)
	drop_shadow.scale = Vector3(shadow_scale, 1.0, shadow_scale)

## Returns the exact 3D world coordinate where the ball rests on the ground
func get_resting_world_position() -> Vector3:
	return _target_world

func is_resting() -> bool:
	return state == State.RESTING or state == State.IDLE

var _is_transitioning_to_mouth: bool = false
var _mouth_transition_time: float = 0.0
var _mouth_transition_duration: float = 0.05
var _pre_snap_pos: Vector3 = Vector3.ZERO

## Snaps the ball into the dog's mouth smoothly with zero teleportation pop
func snap_to_mouth(target_node: Node3D, offset: Vector3 = Vector3.ZERO) -> void:
	_ensure_nodes()
	state = State.CAUGHT
	_attach_target = target_node
	_attach_offset = offset
	_pre_snap_pos = global_position
	_mouth_transition_time = 0.0
	_is_transitioning_to_mouth = true

	if catch_particles:
		catch_particles.restart()
		catch_particles.emitting = true

	# Little snappy bite squash & stretch effect!
	if model_root:
		if _tween and _tween.is_valid():
			_tween.kill()
		_tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		_tween.tween_property(model_root, "scale", Vector3(1.20, 0.88, 1.15), 0.08)
		_tween.chain().tween_property(model_root, "scale", Vector3(1.0, 1.0, 1.0), 0.12)

func _update_caught() -> void:
	if _attach_target and is_instance_valid(_attach_target):
		var target_mouth_pos = _attach_target.global_position + _attach_target.global_transform.basis * _attach_offset
		if _is_transitioning_to_mouth:
			_mouth_transition_time += get_process_delta_time()
			var t = clampf(_mouth_transition_time / _mouth_transition_duration, 0.0, 1.0)
			global_position = _pre_snap_pos.lerp(target_mouth_pos, t)
			if t >= 1.0:
				_is_transitioning_to_mouth = false
		else:
			global_position = target_mouth_pos
		if drop_shadow:
			drop_shadow.global_position = Vector3(global_position.x, _target_world.y + 0.003, global_position.z)

## Smooth fade out shrink when finishing play
func pop_out(on_finished: Callable = Callable()) -> void:
	state = State.POP_OUT
	if _tween and _tween.is_valid():
		_tween.kill()

	_tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	_tween.tween_property(self, "scale", Vector3(0.001, 0.001, 0.001), 0.25)
	_tween.chain().tween_callback(func():
		visible = false
		state = State.IDLE
		if on_finished.is_valid():
			on_finished.call()
	)
