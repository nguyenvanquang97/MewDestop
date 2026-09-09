extends SceneTree

func _init():
	_run()

func _run():
	var glb = load("res://assets/models/shiba/ShibaInu.glb").instantiate()
	root.add_child(glb)
	var skel: Skeleton3D = glb.get_node("AnimalArmature/Skeleton3D")
	var anim_player: AnimationPlayer = glb.get_node("AnimationPlayer")
	
	var jaw_idx = skel.find_bone("Jaw")
	var attach = BoneAttachment3D.new()
	attach.bone_name = "Jaw"
	attach.bone_idx = jaw_idx
	skel.add_child(attach)
	
	anim_player.play("Happy_TongueWag")
	anim_player.seek(0.5, true)
	await process_frame
	
	print("Jaw origin in skel:", skel.get_bone_global_pose(jaw_idx).origin)
	
	# The mouth cavity center in model space is around: Y = 2.26, Z = 2.38
	var target_mouth_in_skel = Vector3(0.0, 2.26, 2.38)
	var jaw_transform = skel.get_bone_global_pose(jaw_idx)
	var needed_local_offset = jaw_transform.basis.inverse() * (target_mouth_in_skel - jaw_transform.origin)
	print("Target mouth in model space:", target_mouth_in_skel)
	print("Needed local offset in Jaw bone space:", needed_local_offset)
	
	# Notice: in Cat.tscn, ShibaModel is scaled by 0.33!
	# Does BoneAttachment3D exist inside ShibaModel (inside the 0.33 scale)
	# or at visual root?
	# In Cat.tscn, ShibaHeadAttachment is added to `skel` which is inside ShibaModel!
	# So BoneAttachment3D's local coordinates are in Blender/GLTF model units!
	# But wait, does global_transform account for ShibaModel's 0.33 scale?
	# Let's check!
	quit()
