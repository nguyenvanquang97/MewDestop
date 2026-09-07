extends SceneTree

func _init():
	var cat_scene = load("res://scenes/Cat.tscn").instantiate()
	cat_scene.pet_type = "shiba"
	root.add_child(cat_scene)
	cat_scene._ready()
	
	print("Initial anim: ", cat_scene.shiba_anim_player.current_animation)
	cat_scene.change_state("Pet")
	print("In Pet state anim: ", cat_scene.shiba_anim_player.current_animation)
	cat_scene.queue_free()
	quit()
