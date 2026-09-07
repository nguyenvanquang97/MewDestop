class_name DraggedState
extends CatState

var is_held: bool = true
var fall_velocity_y: float = 0.0
const GRAVITY: float = 980.0 # Screen pixels per second squared

func enter(_prev: String) -> void:
	is_held = true
	fall_velocity_y = 0.0
	cat.play_animation("Dragged")
	cat.show_emote("sweat")

func update(_delta: float) -> void:
	if is_held:
		# Follow current mouse cursor position smoothly
		var mouse_pos = cat.get_viewport().get_mouse_position()
		var clamped_pos = cat.screen_manager.clamp_screen_pos(mouse_pos)
		cat.current_screen_x = clamped_pos.x
		cat.current_screen_y = clamped_pos.y
		cat.sync_world_position_from_screen()

func handle_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT and not event.pressed:
			# Released mouse: place cat at current spot safely
			is_held = false
			var safe_pos = cat.screen_manager.clamp_screen_pos(Vector2(cat.current_screen_x, cat.current_screen_y))
			cat.current_screen_x = safe_pos.x
			cat.current_screen_y = safe_pos.y
			cat.sync_world_position_from_screen()
			cat.play_animation("Pet")
			cat.change_state("Idle")
