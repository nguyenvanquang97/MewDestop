extends SceneTree

func _init():
	var scene = load("res://scenes/Cat.tscn").instantiate()
	var anim_player: AnimationPlayer = scene.find_child("AnimationPlayer", true, false)
	var lib = anim_player.get_animation_library("")
	var idle = lib.get_animation("idle")
	var sit = idle.duplicate()
	lib.add_animation("sit_drink", sit)
	print("Added sit_drink! Has anim: ", anim_player.has_animation("sit_drink"))
	quit()
