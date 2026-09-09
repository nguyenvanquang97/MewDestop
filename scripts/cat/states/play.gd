class_name PlayState
extends CatState

## Play / Fetch state:
## 1. User/System throws a bouncy 3D toy ball out across the screen.
## 2. Dog perks up excitedly, turns, and gallops full speed chasing the ball.
## 3. Lunges and chomps down on the ball ("đớp"), catching it in mouth with sparkles.
## 4. Celebrates with Happy_TongueWag (smiling eyes ⌒ ⌒, pink tongue, wagging tail).
## 5. Satisfies happiness stat and returns to Idle.

enum Phase {
	ANTICIPATION,  # 0.0 -> 0.3s: perks up, emote 'play'
	THROWING,      # 0.3 -> 1.0s: ball arcs and bounces, dog turns to track it
	CHASING,       # sprints excitedly with Gallop towards ball target
	CATCHING,      # pounces and bites the ball (Attack animation)
	CELEBRATING,   # Happy_TongueWag wagging tail and squinting smile
	FINISHED       # pop out ball and return to Idle
}

var current_phase: Phase = Phase.ANTICIPATION
var phase_timer: float = 0.0
var ball_snapped: bool = false

var custom_first_bounce_screen: Vector2 = Vector2.ZERO
var first_bounce_screen: Vector2 = Vector2.ZERO
var first_bounce_world: Vector3 = Vector3.ZERO
var target_screen: Vector2 = Vector2.ZERO
var target_world: Vector3 = Vector3.ZERO
var throw_direction: float = 1.0

# Chasing parameters (Unified Locomotion)
var current_speed: float = 0.0
var total_chase_dist: float = 0.0
var catch_distance_threshold: float = 50.0 # px distance to trigger bite

func enter(_prev: String) -> void:
	current_phase = Phase.ANTICIPATION
	phase_timer = 0.0
	ball_snapped = false

	# 1. Pop excited emote
	cat.show_emote("play")
	cat.play_animation("idle")

	# 2. Determine throw target on screen
	var rect = cat.screen_manager.get_walkable_screen_rect()
	var current_x = cat.current_screen_x
	var current_y = cat.current_screen_y
	var ball_radius = 0.045 if cat.pet_type == "shiba" else 0.06

	if custom_first_bounce_screen != Vector2.ZERO:
		# User explicitly double-clicked or requested a target position!
		first_bounce_screen = custom_first_bounce_screen
		first_bounce_screen.x = clampf(first_bounce_screen.x, rect.position.x + 80.0, rect.end.x - 80.0)
		first_bounce_screen.y = current_y

		# Determine throw direction from cat's current position to first bounce
		if first_bounce_screen.x >= current_x:
			throw_direction = 1.0
		else:
			throw_direction = -1.0

		# Settle target: hops and rolls forward ~80px in throw direction
		var roll_dist = 80.0 * throw_direction
		target_screen.x = clampf(first_bounce_screen.x + roll_dist, rect.position.x + 60.0, rect.end.x - 60.0)
		target_screen.y = current_y

		# Reset custom request
		custom_first_bounce_screen = Vector2.ZERO
	else:
		# Default autonomous throw
		var space_right = rect.end.x - current_x
		var space_left = current_x - rect.position.x

		if space_right >= space_left:
			throw_direction = 1.0
			var dist = clampf(space_right * 0.70, 380.0, 750.0)
			target_screen.x = current_x + dist
		else:
			throw_direction = -1.0
			var dist = clampf(space_left * 0.70, 380.0, 750.0)
			target_screen.x = current_x - dist

		target_screen.x = clampf(target_screen.x, rect.position.x + 100.0, rect.end.x - 100.0)
		target_screen.y = current_y
		first_bounce_screen.x = lerpf(current_x, target_screen.x, 0.70)
		first_bounce_screen.y = current_y

	# World coordinates: Ball rests on the floor plane where dog walks
	first_bounce_world = cat.screen_manager.screen_to_world(first_bounce_screen, cat.camera, 0.0)
	first_bounce_world.y = cat.global_position.y + ball_radius

	target_world = cat.screen_manager.screen_to_world(target_screen, cat.camera, 0.0)
	target_world.y = cat.global_position.y + ball_radius

func exit() -> void:
	if cat.toy_ball and cat.toy_ball.visible:
		cat.toy_ball.pop_out()
	cat.target_pitch_x = 0.0
	cat.set_walk_animation_speed(1.0)
	current_speed = 0.0

func update(delta: float) -> void:
	phase_timer += delta

	match current_phase:
		Phase.ANTICIPATION:
			if phase_timer >= 0.28:
				_start_throw()

		Phase.THROWING:
			# Pre-turn dog toward ball trajectory
			cat.set_facing_direction(throw_direction)
			if phase_timer >= 0.55:
				_start_chase()

		Phase.CHASING:
			_update_chase(delta)

		Phase.CATCHING:
			# At t ~ 0.48s (Frame 11-12 of Fetch_Chomp), the dog's mouth is wide open
			# and clamped down right on the ground touching the ball.
			# Snap ball to mouth at floor level (0px jump):
			var bite_trigger_time = 0.48 if cat.pet_type == "shiba" else 0.15
			if not ball_snapped and phase_timer >= bite_trigger_time:
				ball_snapped = true
				if cat.toy_ball:
					var mouth_node = cat.get_mouth_attach_node()
					var offset = cat.get_mouth_attach_offset()
					cat.toy_ball.snap_to_mouth(mouth_node, offset)
					cat.show_emote("heart")

			# Wait for head to raise up smoothly carrying the ball (t >= 1.45s)
			var catch_duration = 1.45 if cat.pet_type == "shiba" else 0.65
			if phase_timer >= catch_duration:
				_start_celebration()

		Phase.CELEBRATING:
			if phase_timer >= 2.6:
				_finish_play()

func _get_dog_target_screen_x() -> float:
	# Calculate the exact world position where dog must stand
	# so that when lunging in Fetch_Chomp, mouth reaches target_world.x exactly
	var forward_reach = 0.60 if cat.pet_type == "shiba" else 0.18
	var stop_world_x = target_world.x - (throw_direction * forward_reach)
	if cat.camera:
		var stop_screen = cat.camera.unproject_position(Vector3(stop_world_x, target_world.y, target_world.z))
		return stop_screen.x
	var stop_offset = 150.0 if cat.pet_type == "shiba" else 40.0
	return target_screen.x - (throw_direction * stop_offset)

func _start_throw() -> void:
	current_phase = Phase.THROWING
	phase_timer = 0.0

	var start_world = cat.global_position + Vector3(0.0, 0.35, 0.0)
	if cat.toy_ball:
		cat.toy_ball.throw_ball_to_first_bounce(start_world, first_bounce_world, target_world, 1.25, 0.95)

func _start_chase() -> void:
	current_phase = Phase.CHASING
	phase_timer = 0.0
	current_speed = 0.0
	total_chase_dist = absf(_get_dog_target_screen_x() - cat.current_screen_x)

	cat.set_facing_direction(throw_direction)
	if cat.pet_type == "shiba":
		cat.play_animation("Gallop")
	else:
		cat.play_animation("walk")

func _update_chase(delta: float) -> void:
	var target_dog_x = _get_dog_target_screen_x()
	var diff = target_dog_x - cat.current_screen_x
	var dist = absf(diff)

	# Face movement direction strictly along lateral axis (90 deg)
	cat.set_facing_direction(throw_direction)

	# Unified sprint locomotion step & stride animation sync
	var is_sprint = (cat.pet_type == "shiba")
	var step_data = cat.calculate_locomotion_step(current_speed, dist, total_chase_dist, delta, is_sprint)
	current_speed = step_data.new_speed
	var step_dist = step_data.step_dist

	# Move toward ball
	if dist <= step_dist:
		cat.current_screen_x = target_dog_x
		cat.sync_world_position_from_screen()
		cat.set_walk_animation_speed(1.0)

		# Ensure ball has landed or is near landing before initiating bite
		var ball_ready = true
		if cat.toy_ball and not cat.toy_ball.is_resting():
			if cat.toy_ball._flight_time < cat.toy_ball._flight_duration * 0.80:
				ball_ready = false
		if ball_ready:
			_catch_ball()
	else:
		var move_dir = signf(diff)
		cat.current_screen_x += move_dir * step_dist
		cat.sync_world_position_from_screen()

func _catch_ball() -> void:
	current_phase = Phase.CATCHING
	phase_timer = 0.0
	ball_snapped = false

	# Ensure dog is at the exact reach distance from the actual ball position
	if cat.toy_ball:
		target_world = cat.toy_ball.get_resting_world_position()
		var forward_reach = 0.60 if cat.pet_type == "shiba" else 0.18
		var stop_world_x = target_world.x - (throw_direction * forward_reach)
		if cat.camera:
			cat.current_screen_x = cat.camera.unproject_position(Vector3(stop_world_x, target_world.y, 0.0)).x
			cat.sync_world_position_from_screen()

	# Keep facing 90 deg directly into the ball
	cat.set_facing_direction(throw_direction)

	# Lunge down and scoop-chomp the ball at ground level!
	if cat.pet_type == "shiba":
		cat.play_animation("Fetch_Chomp")
	else:
		cat.play_animation("attack")

func _start_celebration() -> void:
	current_phase = Phase.CELEBRATING
	phase_timer = 0.0

	# Wag tail happily holding ball in mouth!
	cat.play_animation("fetch_celebrate" if cat.pet_type == "shiba" else "idle")
	cat.show_emote("heart")

	# Stat boosts
	cat.stats.modify_stat("happiness", 35.0)
	cat.stats.modify_stat("energy", -8.0)
	cat.stats.modify_stat("affection", 15.0)

func _finish_play() -> void:
	current_phase = Phase.FINISHED
	cat.set_walk_animation_speed(1.0)
	if cat.toy_ball:
		cat.toy_ball.pop_out(func():
			cat.change_state("Idle")
		)
	else:
		cat.change_state("Idle")
