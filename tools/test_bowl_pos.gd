extends SceneTree

func _init():
	var cat = load("res://scenes/Cat.tscn").instantiate()
	var main = Node3D.new()
	main.add_child(cat)
	cat._ready()
	cat.visual_root.rotation.x = 0.20
	var skel: Skeleton3D = cat.find_child("Skeleton3D", true, false)
	var left_paw = skel.find_bone("Joint15")
	var paw_trans = skel.get_bone_global_pose(left_paw)
	print("Paw model trans: ", paw_trans.origin)
	var paw_world = skel.global_transform * paw_trans.origin
	print("Paw world pos: ", paw_world)
	quit()
