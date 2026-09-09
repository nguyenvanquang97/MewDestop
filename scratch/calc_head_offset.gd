extends SceneTree

func _init():
	var glb = load("res://assets/models/shiba/ShibaInu.glb").instantiate()
	var skel: Skeleton3D = glb.get_node("AnimalArmature/Skeleton3D")
	var head_idx = skel.find_bone("Head")
	var head_rest = skel.get_bone_global_pose(head_idx)
	print("Head rest global pose in skel:")
	print("  origin: ", head_rest.origin)
	print("  basis: ", head_rest.basis)
	
	# Target ball in skel space: (0.0, 2.32, 2.38)
	var ball_skel = Vector3(0.0, 2.32, 2.38)
	var local_offset = head_rest.basis.inverse() * (ball_skel - head_rest.origin)
	print("Calculated local offset from Head bone:", local_offset)
	
	# Verify with animations
	var ap: AnimationPlayer = glb.get_node("AnimationPlayer")
	for anim_name in ["Fetch_Chomp", "Fetch_Celebrate_HoldBall"]:
		ap.play(anim_name)
		ap.seek(0.5, true)
		var p = skel.get_bone_global_pose(head_idx)
		var posed_ball = p.origin + p.basis * local_offset
		print("In ", anim_name, " at 0.5s:")
		print("  Head origin: ", p.origin)
		print("  Posed ball in skel: ", posed_ball)
	quit()
