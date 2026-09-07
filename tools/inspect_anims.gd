extends SceneTree

func _init():
	var scene = load("res://scenes/Cat.tscn").instantiate()
	var anim_player: AnimationPlayer = scene.find_child("AnimationPlayer", true, false)
	var idle = anim_player.get_animation("idle")
	for t in range(idle.get_track_count()):
		var path = idle.track_get_path(t)
		var type = idle.track_get_type(t)
		if idle.track_get_key_count(t) > 0:
			var val = idle.track_get_key_value(t, 0)
			print(path, " [", type, "] = ", val)
	quit()
