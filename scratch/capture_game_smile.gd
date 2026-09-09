extends SceneTree

func _init():
	var root = Viewport.new()
	# Create subviewport to render
	var vp = SubViewport.new()
	vp.size = Vector2i(800, 800)
	vp.transparent_bg = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	
	var world3d = World3D.new()
	var env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.98, 0.77, 0.15, 1.0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1.0, 1.0, 1.0)
	world3d.environment = env
	vp.world_3d = world3d
	
	var cat_scene = load("res://scenes/Cat.tscn")
	var cat = cat_scene.instantiate()
	vp.add_child(cat)
	
	var cam = Camera3D.new()
	cam.position = Vector3(0, 0.8, 2.2)
	cam.look_at(Vector3(0, 0.45, 0))
	vp.add_child(cam)
	
	var light = DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45, 30, 0)
	light.light_energy = 1.2
	vp.add_child(light)
	
	root_node.add_child(vp)
	
	# Play Happy_TongueWag
	var anim_player = cat.get_node_or_null("AnimationPlayer")
	if not anim_player:
		for child in cat.get_children():
			if child is AnimationPlayer:
				anim_player = child
				break
			for sub in child.get_children():
				if sub is AnimationPlayer:
					anim_player = sub
					break
	
	if anim_player:
		print("Playing Happy_TongueWag...")
		anim_player.play("Happy_TongueWag")
		anim_player.seek(0.4, true)
	
	await process_frame
	await process_frame
	
	var img = vp.get_texture().get_image()
	if img:
		img.save_png("/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/godot_game_smile_cap.png")
		print("Saved godot_game_smile_cap.png successfully!")
	quit()
