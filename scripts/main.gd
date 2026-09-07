class_name Main
extends Node3D

## Main Coordinator: Orchestrates window, screen, 3D world, cat, UI,
## and dynamic mouse passthrough click-through.

@onready var window_manager: WindowManager = $WindowManager
@onready var screen_manager: ScreenManager = $ScreenManager
@onready var save_manager: SaveManager = $SaveManager

@onready var camera: Camera3D = $Camera3D
@onready var cat: Cat = $Cat
@onready var context_menu: ContextMenu = %ContextMenu

var _save_timer: float = 0.0
const AUTO_SAVE_INTERVAL: float = 60.0 # Auto save every 1 minute

var _mouse_udp: PacketPeerUDP = null
var _mouse_listener_pid: int = -1
const MOUSE_LISTENER_PORT: int = 45455

func _ready() -> void:
	print("[Main] Initializing NekoDesk 3D...")
	
	# Connect save manager
	var saved_data = save_manager.load_game()
	if not saved_data.is_empty():
		cat.stats.from_dict(saved_data)
		if saved_data.has("pet_type"):
			cat.set_pet_type(saved_data["pet_type"])
		if saved_data.has("screen_id"):
			var saved_screen: int = int(saved_data["screen_id"])
			if saved_screen != window_manager.current_screen_id and saved_screen < DisplayServer.get_screen_count():
				window_manager.switch_screen(saved_screen)

	save_manager.save_loaded.connect(func(_data, offline_secs):
		cat.stats.apply_offline_time(offline_secs)
	)

	# Connect window screen changes and resizes
	window_manager.screen_changed.connect(_on_screen_changed)
	window_manager.window_resized.connect(func(_new_size):
		screen_manager.update_screen_metrics(window_manager.current_screen_id)
	)

	# Initialize cat
	screen_manager.update_screen_metrics(window_manager.current_screen_id)
	cat.initialize(camera, screen_manager)
	cat.clicked.connect(_on_cat_clicked)
	cat.right_clicked.connect(_on_cat_right_clicked)

	# Context menu signals
	context_menu.action_triggered.connect(_on_menu_action)

	# Setup global mouse listener
	_setup_mouse_listener()

	# Initial passthrough update
	_update_click_through()

func _process(delta: float) -> void:
	# Keep the click-through passthrough mask tightly aligned with the cat & menu
	_update_click_through()

	# Process global mouse wheel clicks from helper
	_process_mouse_udp()

	# Periodic autosave
	_save_timer += delta
	if _save_timer >= AUTO_SAVE_INTERVAL:
		_save_timer = 0.0
		_save_current_state()

	# IPC command listener for agent autonomous testing & control
	if FileAccess.file_exists("res://command.txt"):
		var fa = FileAccess.open("res://command.txt", FileAccess.READ)
		if fa:
			var cmd = fa.get_as_text().strip_edges()
			fa.close()
			DirAccess.remove_absolute(ProjectSettings.globalize_path("res://command.txt"))
			print("[IPC] Executing test command: ", cmd)
			if cmd.begins_with("run_to:"):
				var coords = cmd.replace("run_to:", "").split(",")
				if coords.size() >= 2:
					cat.run_to(Vector2(coords[0].to_float(), coords[1].to_float()))
			else:
				match cmd:
					"drink", "drink_milk":
						_on_menu_action("drink_milk")
					"feed":
						_on_menu_action("feed")
					"sleep":
						_on_menu_action("sleep")
					"walk", "play":
						_on_menu_action("play")
					"run":
						cat.run_to(Vector2(cat.current_screen_x + 300.0, cat.current_screen_y))
					"pet":
						_on_menu_action("pet")
					"switch_pet", "toggle_pet":
						_on_menu_action("switch_pet")
					"shiba":
						cat.set_pet_type("shiba")
						_save_current_state()
					"cat":
						cat.set_pet_type("cat")
						_save_current_state()
					"drink_capture":
						_on_menu_action("drink_milk")
						get_tree().create_timer(1.5).timeout.connect(func():
							var img = get_viewport().get_texture().get_image()
							if img:
								img.save_png("/Users/macbook/.gemini/antigravity-ide/brain/775a4a21-a944-4fea-ac01-52918f0dae09/shiba_eating_captured_live.png")
								print("[IPC] Saved shiba_eating_captured_live.png")
						)
					"capture":
						var img = get_viewport().get_texture().get_image()
						if img:
							img.save_png("/Users/macbook/.gemini/antigravity-ide/brain/775a4a21-a944-4fea-ac01-52918f0dae09/cat_live_capture.png")
							print("[IPC] Saved cat_live_capture.png")

func _input(event: InputEvent) -> void:
	# Handle context menu mouse interception: prevent clicks on menu from bubbling to cat
	if context_menu and context_menu.visible:
		if event is InputEventMouse:
			var menu_rect = context_menu.get_menu_rect()
			if menu_rect.has_point(event.position):
				# Event is inside context menu bounds: let menu handle it, do not pass to cat
				return
			elif event is InputEventMouseButton and event.pressed:
				if event.button_index == MOUSE_BUTTON_LEFT:
					context_menu.close_menu()
					get_viewport().set_input_as_handled()
					return
				elif event.button_index == MOUSE_BUTTON_RIGHT:
					context_menu.close_menu()

	# Hotkeys for fast testing
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_D:
			_on_menu_action("drink_milk")
		elif event.keycode == KEY_F:
			_on_menu_action("feed")
		elif event.keycode == KEY_C:
			_on_menu_action("switch_pet")
		elif event.keycode == KEY_M:
			# 'M' hotkey: Run to current mouse cursor position
			_handle_middle_click_global()

	# Handle middle click directly on window / pet
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_MIDDLE:
			_handle_middle_click_global()

	# Forward mouse events to cat
	if cat:
		cat.handle_mouse_input(event)

func _update_click_through() -> void:
	if not window_manager or not cat:
		return

	var rects: Array[Rect2] = []
	rects.append(cat.get_screen_bounding_rect())

	if context_menu and context_menu.visible:
		rects.append(context_menu.get_menu_rect())

	window_manager.update_passthrough_from_rects(rects, 16.0)

func _on_screen_changed(new_screen_id: int) -> void:
	screen_manager.update_screen_metrics(new_screen_id)
	cat.current_screen_x = screen_manager.screen_width * 0.5
	cat.current_screen_y = screen_manager.screen_height * 0.5
	cat.sync_world_position_from_screen()
	_update_click_through()
	_save_current_state()

func _on_cat_clicked() -> void:
	if context_menu.visible:
		context_menu.close_menu()
	cat.show_emote("heart")

func _on_cat_right_clicked(screen_pos: Vector2) -> void:
	if cat:
		cat.cancel_mouse_interaction()
	context_menu.show_at(screen_pos)

func _on_menu_action(action: String) -> void:
	if cat:
		cat.cancel_mouse_interaction()
	match action:
		"feed":
			cat.stats.feed(35.0)
			cat.show_emote("fish")
			cat.play_animation("Pet")
		"drink_milk":
			cat.change_state("Drink")
		"play":
			cat.show_emote("play")
			cat.change_state("Walk")
		"sleep":
			cat.change_state("Sleep")
		"pet":
			cat.change_state("Pet")
		"switch_screen":
			window_manager.toggle_screen()
		"switch_pet":
			cat.toggle_pet_type()
			_save_current_state()
		"quit":
			_save_current_state()
			get_tree().quit()

func _save_current_state() -> void:
	if save_manager and cat and cat.stats:
		var data = cat.stats.to_dict()
		data["pet_type"] = cat.pet_type
		if window_manager:
			data["screen_id"] = window_manager.current_screen_id
		save_manager.save_game(data)

func _setup_mouse_listener() -> void:
	_mouse_udp = PacketPeerUDP.new()
	var err = _mouse_udp.bind(MOUSE_LISTENER_PORT, "127.0.0.1")
	if err != OK:
		push_warning("[Main] Failed to bind UDP port %d for mouse listener (error: %d)" % [MOUSE_LISTENER_PORT, err])
	else:
		print("[Main] Mouse listener UDP bound to 127.0.0.1:%d" % MOUSE_LISTENER_PORT)

	# Launch Python helper if on macOS
	if OS.get_name() == "macOS":
		var script_path = ProjectSettings.globalize_path("res://tools/mouse_listener.py")
		if FileAccess.file_exists("res://tools/mouse_listener.py"):
			_mouse_listener_pid = OS.create_process("python3", [script_path])
			print("[Main] Started global mouse listener process (PID: %d)" % _mouse_listener_pid)

func _process_mouse_udp() -> void:
	if not _mouse_udp or not cat:
		return

	var had_click: bool = false
	while _mouse_udp.get_available_packet_count() > 0:
		var _pkt = _mouse_udp.get_packet()
		had_click = true

	if had_click:
		_handle_middle_click_global()

func _handle_middle_click_global() -> void:
	if not window_manager or not cat:
		return

	var global_mouse = DisplayServer.mouse_get_position()

	# Determine which screen the mouse cursor is currently on
	var target_screen = window_manager.current_screen_id
	var screen_count = DisplayServer.get_screen_count()
	for i in range(screen_count):
		var s_pos = DisplayServer.screen_get_position(i)
		var s_size = DisplayServer.screen_get_size(i)
		var s_rect = Rect2i(s_pos, s_size)
		if s_rect.has_point(global_mouse):
			target_screen = i
			break

	# If mouse is on a different monitor, switch window to that monitor
	if target_screen != window_manager.current_screen_id:
		window_manager.switch_screen(target_screen)

	var cur_screen = window_manager.current_screen_id
	var screen_pos = DisplayServer.screen_get_position(cur_screen)
	var local_x = float(global_mouse.x - screen_pos.x)
	var local_y = float(global_mouse.y - screen_pos.y)

	print("[Main] Middle click at global %s -> screen %d local (%.1f, %.1f)" % [
		global_mouse, cur_screen, local_x, local_y
	])

	# If context menu was open, close it
	if context_menu and context_menu.visible:
		context_menu.close_menu()

	cat.run_to(Vector2(local_x, local_y))

func _exit_tree() -> void:
	_cleanup()

func _cleanup() -> void:
	if _mouse_listener_pid > 0:
		OS.kill(_mouse_listener_pid)
		_mouse_listener_pid = -1
	if _mouse_udp:
		_mouse_udp.close()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_cleanup()
		_save_current_state()
		get_tree().quit()
