extends SceneTree

func _init():
	var glb = load("res://assets/models/shiba/ShibaInu.glb").instantiate()
	var skel: Skeleton3D = glb.get_node("AnimalArmature/Skeleton3D")
	var bone_idx = skel.find_bone("Head")
	print("Head bone idx:", bone_idx)
	if bone_idx >= 0:
		var bone_name = skel.get_bone_name(bone_idx)
		print("Found bone:", bone_name)
		var attachment = BoneAttachment3D.new()
		attachment.bone_name = "Head"
		skel.add_child(attachment)
		print("BoneAttachment3D attached successfully!")
	quit()
