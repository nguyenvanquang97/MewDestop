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
var current_speed: float = 0.0
var accel: float = 240.0 # Acceleration rate
var decel_distance: float = 85.0 # Distance to begin braking
var arrived_threshold: float = 10.0

# Pre-turn phase parameters
var _is_pre_turning: bool = true
var _turn_timer: float = 0.0
const PRE_TURN_DURATION: float = 0.32 # Short pause to rotate body first

# Organic wandering curve
var _curve_amplitude: float = 0.0

func enter(_prev: String) -> void:
	var rect = cat.screen_manager.get_walkable_screen_rect()
	var current_pos = Vector2(cat.current_screen_x, cat.current_screen_y)
	start_pos = current_pos

	# Pick random 2D destination within comfortable natural radius
	var angle = randf_range(0.0, TAU)
	var distance = randf_range(220.0, 650.0)
	var candidate = current_pos + Vector2(cos(angle), sin(angle)) * distance

	target_pos = Vector2(
		clampf(candidate.x, rect.position.x, rect.end.x),
		clampf(candidate.y, rect.position.y, rect.end.y)
	)

	total_distance = (target_pos - start_pos).length()
	current_speed = 0.0
	_is_pre_turning = true
	_turn_timer = 0.0

	# Randomize a slight organic lateral bend to the path (-25 to +25 pixels)
	_curve_amplitude = randf_range(-25.0, 25.0)

	# Aim cat towards target direction FIRST
	var initial_diff = target_pos - current_pos
	cat.orient_toward_vector(initial_diff)
	cat.play_animation("Idle")

func exit() -> void:
	cat.set_walk_animation_speed(1.0)

func update(delta: float) -> void:
	var current_pos = Vector2(cat.current_screen_x, cat.current_screen_y)
	var diff = target_pos - current_pos
	var dist = diff.length()

	# Phase 1: Pre-turn in place so the cat faces the goal before stepping
	if _is_pre_turning:
		_turn_timer += delta
		cat.orient_toward_vector(diff)
		if _turn_timer >= PRE_TURN_DURATION:
			_is_pre_turning = false
			cat.play_animation("Walk")
		return

	# Phase 2: Check arrival
	if dist <= arrived_threshold:
		cat.change_state("Idle")
		return

	# Phase 3: Acceleration & Deceleration curves
	var target_speed = max_walk_speed
	if dist < decel_distance:
		# Smooth braking near destination
		var decel_factor = clampf(dist / decel_distance, 0.25, 1.0)
		target_speed = max_walk_speed * decel_factor

	# Ramp up/down speed
	current_speed = move_toward(current_speed, target_speed, accel * delta)

	# CRITICAL: Ensure walk animation is playing continuously while stepping
	if cat.animation_player and (not cat.animation_player.is_playing() or cat.animation_player.current_animation != "walk"):
		cat.play_animation("Walk")

	# Synchronize leg animation speed to actual movement speed (no sliding)
	var speed_ratio = clampf(current_speed / max_walk_speed, 0.5, 1.3)
	cat.set_walk_animation_speed(speed_ratio)

	# Calculate step with slight lateral organic curvature
	var dir = diff.normalized()
	var step_dist = minf(current_speed * delta, dist)
	var step = dir * step_dist

	# Add gentle organic curve perpendicular to movement direction
	if total_distance > 50.0 and dist > 30.0:
		var progress = 1.0 - (dist / total_distance)
		var perp = Vector2(-dir.y, dir.x)
		var curve_nudge = perp * cos(progress * PI) * (_curve_amplitude * delta * 0.8)
		step += curve_nudge

	cat.current_screen_x += step.x
	cat.current_screen_y += step.y
	cat.sync_world_position_from_screen()

	# Continuously update 360-degree heading to match velocity vector
	cat.orient_toward_vector(step)
