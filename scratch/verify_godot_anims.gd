extends SceneTree

func _init():
	var cat_scene = load("res://scenes/Cat.tscn").instantiate()
	var anim_players = cat_scene.find_children("*", "AnimationPlayer", true, false)
	for ap in anim_players:
		print("AnimationPlayer: ", ap.name, " (parent: ", ap.get_parent().name, ")")
		print("  Animations: ", ap.get_animation_list())
	cat_scene.free()
	quit()
