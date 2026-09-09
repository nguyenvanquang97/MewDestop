extends SceneTree

func _init():
	var glb = load("res://assets/models/shiba/ShibaInu.glb").instantiate()
	var anim_player = glb.get_node("AnimationPlayer")
	for anim_name in ["Fetch_Chomp"]:
		var anim = anim_player.get_animation(anim_name)
		print("--- Anim: ", anim_name, " (length: ", anim.length, ") ---")
		for i in range(anim.get_track_count()):
			var path = str(anim.track_get_path(i))
			print("  Track %d: %s (type: %d)" % [i, path, anim.track_get_type(i)])
		print("--- Anim: ", anim_name, " (length: ", anim.length, ") ---")
		for i in range(anim.get_track_count()):
			var path = str(anim.track_get_path(i))
			if "Eye" in path or "Tongue" in path or "Smile" in path:
				print("  Track: ", path)
	quit()
