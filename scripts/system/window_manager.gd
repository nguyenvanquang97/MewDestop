class_name WindowManager
extends Node

## Manages transparent borderless window, always-on-top, Retina scaling,
## and click-through (mouse passthrough) for macOS desktop pet.

signal window_resized(new_size: Vector2i)
signal screen_changed(new_screen_id: int)

@export var always_on_top: bool = true
@export var borderless: bool = true
@export var transparent: bool = true

var current_screen_id: int = 0
var screen_size: Vector2i = Vector2i(1920, 1080)
var scale_factor: float = 1.0
var _last_passthrough_poly: PackedVector2Array = PackedVector2Array()

func _ready() -> void:
	setup_window()
	get_viewport().size_changed.connect(_on_viewport_size_changed)

func setup_window(target_screen: int = -1) -> void:
	var screen_count = DisplayServer.get_screen_count()

	# Check CLI arguments for --screen=N or numeric arg
	if target_screen == -1:
		for arg in OS.get_cmdline_args():
			if arg.begins_with("--screen="):
				target_screen = arg.replace("--screen=", "").to_int()
			elif arg == "0" or arg == "1" or arg == "2":
				target_screen = arg.to_int()
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--screen="):
				target_screen = arg.replace("--screen=", "").to_int()
			elif arg == "0" or arg == "1" or arg == "2":
				target_screen = arg.to_int()

	# If multiple screens exist and user requested or target is valid, use target screen;
	# default to screen 1 (secondary display) when multiple displays are connected!
	if target_screen >= 0 and target_screen < screen_count:
		current_screen_id = target_screen
	elif screen_count > 1:
		current_screen_id = 1
	else:
		current_screen_id = DisplayServer.window_get_current_screen()

	DisplayServer.window_set_current_screen(current_screen_id)
	screen_size = DisplayServer.screen_get_size(current_screen_id)
	scale_factor = DisplayServer.screen_get_scale(current_screen_id)

	# Set background clear color to fully transparent
	RenderingServer.set_default_clear_color(Color(0, 0, 0, 0))
	get_viewport().transparent_bg = true

	# Set window geometry to cover the screen
	# macOS note: Setting height 1px smaller ensures Godot's backend sets
	# setHidesOnDeactivate:NO so the desktop pet never disappears when clicking other apps!
	var effective_size = Vector2i(screen_size.x, screen_size.y - 1)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_position(DisplayServer.screen_get_position(current_screen_id))
	DisplayServer.window_set_size(effective_size)

	# Configure window flags
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, borderless)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, always_on_top)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_TRANSPARENT, transparent)
	DisplayServer.window_move_to_foreground()

	# Low power / 30 FPS default for background desktop companion
	Engine.max_fps = 30
	OS.low_processor_usage_mode = true

	print("[WindowManager] Initialized screen %d of %d (%dx%d, scale=%.1f, pos=%s)" % [
		current_screen_id, screen_count, screen_size.x, screen_size.y, scale_factor, DisplayServer.screen_get_position(current_screen_id)
	])

func switch_screen(target_screen: int) -> void:
	var screen_count = DisplayServer.get_screen_count()
	if target_screen < 0 or target_screen >= screen_count:
		push_warning("[WindowManager] Screen %d out of bounds (count: %d)" % [target_screen, screen_count])
		return

	current_screen_id = target_screen
	DisplayServer.window_set_current_screen(current_screen_id)
	screen_size = DisplayServer.screen_get_size(current_screen_id)
	scale_factor = DisplayServer.screen_get_scale(current_screen_id)
	DisplayServer.window_set_position(DisplayServer.screen_get_position(current_screen_id))
	DisplayServer.window_set_size(Vector2i(screen_size.x, screen_size.y - 1))
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, always_on_top)
	_last_passthrough_poly.clear()

	print("[WindowManager] Switched to screen %d (%dx%d, pos=%s)" % [
		current_screen_id, screen_size.x, screen_size.y, DisplayServer.screen_get_position(current_screen_id)
	])

	screen_changed.emit(current_screen_id)
	window_resized.emit(screen_size)

func toggle_screen() -> void:
	var count = DisplayServer.get_screen_count()
	if count <= 1:
		print("[WindowManager] Only 1 screen detected, cannot toggle.")
		return
	var next_screen = (current_screen_id + 1) % count
	switch_screen(next_screen)

func set_always_on_top(enabled: bool) -> void:
	always_on_top = enabled
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, enabled)

## Updates the interactive region on macOS.
## Only areas inside this polygon receive mouse clicks;
## all other areas click through directly to desktop/underlying apps!
func update_mouse_passthrough(interactive_poly: PackedVector2Array) -> void:
	if interactive_poly == _last_passthrough_poly:
		return
	_last_passthrough_poly = interactive_poly
	DisplayServer.window_set_mouse_passthrough(interactive_poly)

## Creates a rectangular interactive region from a 2D bounding rect (e.g. around the cat).
func update_passthrough_from_rect(rect: Rect2, padding: float = 16.0) -> void:
	var padded_rect = rect.grow(padding)
	var poly = PackedVector2Array([
		Vector2(padded_rect.position.x, padded_rect.position.y),
		Vector2(padded_rect.end.x, padded_rect.position.y),
		Vector2(padded_rect.end.x, padded_rect.end.y),
		Vector2(padded_rect.position.x, padded_rect.end.y)
	])
	update_mouse_passthrough(poly)

## Merges multiple interactive 2D rects (e.g. cat + context menu) into a composite passthrough polygon.
func update_passthrough_from_rects(rects: Array[Rect2], padding: float = 16.0) -> void:
	if rects.is_empty():
		update_mouse_passthrough(PackedVector2Array())
		return

	# If single rect, directly create polygon
	if rects.size() == 1:
		update_passthrough_from_rect(rects[0], padding)
		return

	# If multiple, calculate bounding envelope or merge
	var combined_rect: Rect2 = rects[0].grow(padding)
	for i in range(1, rects.size()):
		combined_rect = combined_rect.merge(rects[i].grow(padding))

	var poly = PackedVector2Array([
		Vector2(combined_rect.position.x, combined_rect.position.y),
		Vector2(combined_rect.end.x, combined_rect.position.y),
		Vector2(combined_rect.end.x, combined_rect.end.y),
		Vector2(combined_rect.position.x, combined_rect.end.y)
	])
	update_mouse_passthrough(poly)

func _on_viewport_size_changed() -> void:
	var new_size = DisplayServer.window_get_size()
	if new_size != screen_size:
		screen_size = new_size
		window_resized.emit(new_size)
