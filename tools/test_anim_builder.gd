extends SceneTree

func _init():
	var scene = load("res://scenes/Cat.tscn").instantiate()
	var anim_player: AnimationPlayer = scene.find_child("AnimationPlayer", true, false)
	var lib = anim_player.get_animation_library("")
	var idle = lib.get_animation("idle")
	var sit: Animation = idle.duplicate()
	sit.loop_mode = Animation.LOOP_LINEAR
	sit.length = 2.0

	# Helper to find track by name substring and type
	var find_t = func(name_part: String, track_type: int) -> int:
		for t in range(sit.get_track_count()):
			if name_part in str(sit.track_get_path(t)) and sit.track_get_type(t) == track_type:
				return t
		return -1

	# Helper to set a key on a track
	var set_val = func(name_part: String, track_type: int, val: Variant):
		var t = find_t.call(name_part, track_type)
		if t >= 0:
			while sit.track_get_key_count(t) > 0:
				sit.track_remove_key(t, 0)
			sit.track_insert_key(t, 0.0, val)
			# Add end key for loop
			sit.track_insert_key(t, 2.0, val)
			print("Set track ", str(sit.track_get_path(t)), " = ", val)

	# Joint1: Hips (drop down and pitch up)
	set_val.call("Joint1", Animation.TYPE_POSITION_3D, Vector3(0.0, 4.4, -0.6))
	set_val.call("Joint1", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(25.0)))

	# Joint2: Chest (pitch down slightly to stay upright)
	set_val.call("Joint2", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-20.0)))

	# Rear thighs (fold forward)
	set_val.call("Joint19", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-55.0)))
	set_val.call("Joint23", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-55.0)))

	# Rear knees (fold down/back)
	set_val.call("Joint20", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(80.0)))
	set_val.call("Joint24", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(80.0)))

	# Rear ankles (feet planted flat)
	set_val.call("Joint21", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-35.0)))
	set_val.call("Joint25", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-35.0)))

	# Neck & Head (gentle glance towards bowl)
	set_val.call("Joint3", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-18.0)))
	set_val.call("Joint4", Animation.TYPE_ROTATION_3D, Quaternion(Vector3.RIGHT, deg_to_rad(-12.0)))

	lib.add_animation("sit_drink", sit)
	print("Success! Created sit_drink animation.")
	quit()
