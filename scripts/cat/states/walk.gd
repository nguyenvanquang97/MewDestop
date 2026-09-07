class_name WalkState
extends CatState

## Natural organic walking state:
## 1. Pre-turns body towards target before taking steps (eliminates drifting).
## 2. Smooth acceleration (ease-in) and deceleration (braking).
## 3. Synchronizes leg animation playback speed with ground speed (zero foot-sliding).
## 4. Adds gentle organic curvature to the walking path.

var start_pos: Vector2 = Vector2.ZERO
var target_pos: Vector2 = Vector2.ZERO
var total_distance: float = 0.0

var max_walk_speed: float = 120.0 # Screen pixels/sec (natural cat stroll)
var run_speed: float = 320.0 # Screen pixels/sec (energetic sprint)
var current_speed: float = 0.0
var accel: float = 240.0 # Normal acceleration rate
var run_accel: float = 650.0 # Fast acceleration rate
var decel_distance: float = 85.0 # Distance to begin braking
var arrived_threshold: float = 12.0

var is_running: bool = false
var has_target_override: bool = false
var target_override: Vector2 = Vector2.ZERO

# Kinematics & Stride Synchronization Constants
# Derived from: Camera Ortho (size=4.5m), Viewport 1080p -> 240 px/m (or 480 px/m on 4K), Model Scale 0.33
const V_NATURAL_WALK: float = 82.3 # Natural zero-sliding velocity for Walk at 1.0x (px/s)
const V_NATURAL_GALLOP: float = 270.0 # Natural zero-sliding velocity for Gallop at 1.0x (px/s with spine extension)

# Sprint Distance-Velocity Scaling Constants
const SPRINT_MIN_DISTANCE: float = 1000.0 # Under 1000px: walk comfortably. Over 1000px: sprint Gallop!
const WALK_PACE_SPEED: float = 180.0 # Comfortable walking pace (px/s)
const MIN_SPRINT_SPEED: float = 650.0 # Minimum sprint velocity when gallop engages (px/s)
const MAX_SPRINT_SPEED: float = 1100.0 # Top sprint velocity across large 4K screens (px/s)
const SPRINT_ALPHA: float = 15.0 # Distance acceleration scaling coefficient

# Pre-turn phase parameters
var _is_pre_turning: bool = true
var _turn_timer: float = 0.0
const PRE_TURN_DURATION: float = 0.32 # Short pause to rotate body first
const RUN_PRE_TURN_DURATION: float = 0.12 # Snappy turn when running

# Organic wandering curve
var _curve_amplitude: float = 0.0
var _active_slope: float = 0.0

func _update_ground_slope() -> void:
	var delta_pos = target_pos - start_pos
	if absf(delta_pos.x) > 1.0:
		var slope = atan2(delta_pos.y, absf(delta_pos.x))
		_active_slope = clampf(slope * 0.55, -deg_to_rad(28.0), deg_to_rad(28.0))
	else:
		_active_slope = 0.0
	if cat:
		cat.target_pitch_x = _active_slope

func enter(_prev: String) -> void:
	var rect = cat.screen_manager.get_walkable_screen_rect()
	var current_pos = Vector2(cat.current_screen_x, cat.current_screen_y)
	start_pos = current_pos

	if has_target_override:
		target_pos = Vector2(
			clampf(target_override.x, rect.position.x, rect.end.x),
			clampf(target_override.y, rect.position.y, rect.end.y)
		)
		has_target_override = false
		target_override = Vector2.ZERO
		_curve_amplitude = 0.0 if is_running else randf_range(-15.0, 15.0)
	else:
		is_running = false
		# Pick random 2D destination within comfortable natural radius
		var angle = randf_range(0.0, TAU)
		var distance = randf_range(220.0, 650.0)
		var candidate = current_pos + Vector2(cos(angle), sin(angle)) * distance

		target_pos = Vector2(
			clampf(candidate.x, rect.position.x, rect.end.x),
			clampf(candidate.y, rect.position.y, rect.end.y)
		)
		_curve_amplitude = randf_range(-25.0, 25.0)

	total_distance = (target_pos - start_pos).length()
	current_speed = 0.0
	_is_pre_turning = true
	_turn_timer = 0.0
	_update_ground_slope()

	# Aim cat towards target direction FIRST
	var initial_diff = target_pos - current_pos
	cat.orient_toward_vector(initial_diff)
	cat.play_animation("Idle")

## Dynamically sets or updates destination while running
func set_destination(dest: Vector2, run: bool = true) -> void:
	if not cat or not cat.screen_manager:
		return
	var rect = cat.screen_manager.get_walkable_screen_rect()
	var current_pos = Vector2(cat.current_screen_x, cat.current_screen_y)
	start_pos = current_pos
	target_pos = Vector2(
		clampf(dest.x, rect.position.x, rect.end.x),
		clampf(dest.y, rect.position.y, rect.end.y)
	)
	total_distance = (target_pos - start_pos).length()
	is_running = run
	_is_pre_turning = true
	_turn_timer = 0.0
	_curve_amplitude = 0.0 if run else randf_range(-15.0, 15.0)
	_update_ground_slope()

	var initial_diff = target_pos - current_pos
	cat.orient_toward_vector(initial_diff)
	cat.play_animation("Idle")

func exit() -> void:
	is_running = false
	_active_slope = 0.0
	if cat:
		cat.target_pitch_x = 0.0
		cat.set_walk_animation_speed(1.0)

func update(delta: float) -> void:
	var current_pos = Vector2(cat.current_screen_x, cat.current_screen_y)
	var diff = target_pos - current_pos
	var dist = diff.length()
	var dir = diff.normalized() if dist > 0.001 else Vector2.ZERO

	# Determine if this movement warrants Gallop sprint (distance >= 1000px)
	var should_gallop: bool = is_running and cat.pet_type == "shiba" and total_distance >= SPRINT_MIN_DISTANCE

	# Phase 1: Pre-turn in place so the cat faces the goal before stepping
	var turn_limit = RUN_PRE_TURN_DURATION if is_running else PRE_TURN_DURATION
	if _is_pre_turning:
		_turn_timer += delta
		cat.orient_toward_vector(diff)
		if _turn_timer >= turn_limit:
			_is_pre_turning = false
			cat.play_animation("Gallop" if should_gallop else "Walk")
		return

	# Phase 2: Check arrival
	if dist <= arrived_threshold:
		cat.target_pitch_x = 0.0
		if is_running:
			is_running = false
			cat.change_state("Pet")
			return
		cat.change_state("Idle")
		return

	# Phase 3: Kinematic Distance-Velocity & Acceleration curves
	var active_max_speed: float = max_walk_speed
	var active_accel: float = accel

	if should_gallop:
		# Gallop sprint: fast velocity scaled with distance
		active_max_speed = clampf(MIN_SPRINT_SPEED + SPRINT_ALPHA * sqrt(total_distance), MIN_SPRINT_SPEED, MAX_SPRINT_SPEED)
		active_accel = active_max_speed * 2.8 # Snappy, instantaneous sprint response
	elif is_running:
		# Running command but distance < 1000px: comfortable brisk walk
		active_max_speed = WALK_PACE_SPEED
		active_accel = accel * 1.6
	else:
		# Normal spontaneous stroll
		active_max_speed = max_walk_speed
		active_accel = accel

	var target_speed = active_max_speed
	var active_decel_dist = decel_distance * (1.6 if should_gallop else 1.0)
	if dist < active_decel_dist:
		# Smooth braking near destination
		var decel_factor = clampf(dist / active_decel_dist, 0.18, 1.0)
		target_speed = active_max_speed * decel_factor
		# Smoothly level out body pitch as pet brakes to a halt at destination point
		cat.target_pitch_x = lerpf(0.0, _active_slope, dist / active_decel_dist)
	else:
		cat.target_pitch_x = _active_slope

	# Ramp up/down speed
	current_speed = move_toward(current_speed, target_speed, active_accel * delta)

	# Determine appropriate animation
	var desired_anim: String = "Gallop" if should_gallop else "Walk"
	if cat.animation_player and (not cat.animation_player.is_playing() or cat.animation_player.current_animation.to_lower() != desired_anim.to_lower()):
		cat.play_animation(desired_anim)

	# Synchronize leg animation speed to actual movement speed (Zero Foot-Sliding)
	if desired_anim == "Gallop":
		var gallop_ratio = clampf(current_speed / V_NATURAL_GALLOP, 0.85, 1.35)
		cat.set_walk_animation_speed(gallop_ratio)
	else:
		var walk_ratio = clampf(current_speed / V_NATURAL_WALK, 0.75, 1.4)
		cat.set_walk_animation_speed(walk_ratio)

	# Calculate step with slight lateral organic curvature
	var step_dist = minf(current_speed * delta, dist)
	var step = dir * step_dist

	# Add gentle organic curve perpendicular to movement direction (only during stroll)
	if not is_running and total_distance > 50.0 and dist > 30.0:
		var progress = 1.0 - (dist / total_distance)
		var perp = Vector2(-dir.y, dir.x)
		var curve_nudge = perp * cos(progress * PI) * (_curve_amplitude * delta * 0.8)
		step += curve_nudge

	cat.current_screen_x += step.x
	cat.current_screen_y += step.y
	cat.sync_world_position_from_screen()

	# Continuously update 360-degree heading to match velocity vector
	cat.orient_toward_vector(step)
