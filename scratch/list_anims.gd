extends SceneTree
func _init():
	var glb = load("res://assets/models/shiba/ShibaInu.glb").instantiate()
	var ap: AnimationPlayer = glb.get_node("AnimationPlayer")
	for anim in ap.get_animation_list():
		print("Animation: ", anim)
	quit()
