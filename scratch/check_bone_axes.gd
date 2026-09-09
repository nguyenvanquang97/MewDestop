extends SceneTree

func _init():
	var glb = load("res://assets/models/shiba/ShibaInu.glb").instantiate()
	var skel: Skeleton3D = glb.get_node("AnimalArmature/Skeleton3D")
	var jaw_idx = skel.find_bone("Jaw")
	var head_idx = skel.find_bone("Head")
	print("Jaw rest: ", skel.get_bone_rest(jaw_idx))
	print("Head rest: ", skel.get_bone_rest(head_idx))
	
	var anim_player: AnimationPlayer = glb.get_node("AnimationPlayer")
	anim_player.play("Happy_TongueWag")
	anim_player.seek(0.5, true)
	
	var jaw_pose = skel.get_bone_global_pose(jaw_idx)
	print("Jaw global pose in Happy_TongueWag:")
	print("  origin: ", jaw_pose.origin)
	print("  basis.x (local X in skel): ", jaw_pose.basis.x)
	print("  basis.y (local Y in skel): ", jaw_pose.basis.y)
	print("  basis.z (local Z in skel): ", jaw_pose.basis.z)
	
	quit()
