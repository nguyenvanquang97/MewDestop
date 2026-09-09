extends SceneTree

func _init():
	print("--- Starting Test Play Action ---")
	var screen_mgr = load("res://scripts/system/screen_manager.gd").new()
	screen_mgr.update_screen_metrics(0)
	
	var cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 4.5
	root.add_child(cam)
	
	var cat_scene = load("res://scenes/Cat.tscn").instantiate()
	cat_scene.pet_type = "shiba"
	root.add_child(cat_scene)
	cat_scene._ready()
	cat_scene.initialize(cam, screen_mgr)
	
	print("Initial state:", cat_scene.current_state_name)
	print("Has Play state:", cat_scene.states.has("Play"))
	print("Has ToyBall:", cat_scene.toy_ball != null)
	
	# Trigger Play state
	cat_scene.change_state("Play")
	print("Changed to Play state:", cat_scene.current_state_name)
	
	var play_state = cat_scene.current_state
	print("Target screen x:", play_state.target_screen.x, "dog x:", cat_scene.current_screen_x)
	
	# Simulate 0.35s (Anticipation -> Throwing)
	for i in range(25):
		cat_scene._process(0.016)
		cat_scene._physics_process(0.016)
	print("Phase at 0.4s:", play_state.current_phase, "Ball visible:", cat_scene.toy_ball.visible)
	
	# Simulate 0.6s (Throwing -> Chasing)
	for i in range(40):
		cat_scene._process(0.016)
		cat_scene._physics_process(0.016)
	print("Phase at 1.0s:", play_state.current_phase, "Anim:", cat_scene.shiba_anim_player.current_animation)
	
	# Simulate chase until catch
	var steps = 0
	while play_state.current_phase == PlayState.Phase.CHASING and steps < 200:
		cat_scene._process(0.016)
		cat_scene._physics_process(0.016)
		steps += 1
	print("Chased in", steps, "steps. Phase now:", play_state.current_phase, "Anim:", cat_scene.shiba_anim_player.current_animation)
	print("Ball state:", cat_scene.toy_ball.state)
	
	# Simulate catch -> celebrating
	for i in range(40):
		cat_scene._process(0.016)
		cat_scene._physics_process(0.016)
	print("Celebration phase:", play_state.current_phase, "Anim:", cat_scene.shiba_anim_player.current_animation)
	print("Dog happiness:", cat_scene.stats.happiness)
	
	# Simulate through finish
	for i in range(180):
		cat_scene._process(0.016)
		cat_scene._physics_process(0.016)
	print("Final state after celebration:", cat_scene.current_state_name)
	
	print("--- Test Play Action SUCCESS! ---")
	cat_scene.queue_free()
	cam.queue_free()
	quit()
