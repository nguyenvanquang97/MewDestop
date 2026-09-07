class_name ScreenManager
extends Node

## Handles desktop coordinates, margins, macOS Dock offset, and Screen <-> 3D World conversions.

@export var top_margin: float = 80.0
@export var bottom_margin: float = 80.0
@export var left_margin: float = 80.0
@export var right_margin: float = 80.0

var screen_width: float = 1920.0
var screen_height: float = 1080.0

func _ready() -> void:
	update_screen_metrics()

func update_screen_metrics(screen_id: int = -1) -> void:
	if screen_id == -1:
		screen_id = DisplayServer.window_get_current_screen()
	var size = DisplayServer.screen_get_size(screen_id)
	screen_width = float(size.x)
	screen_height = float(size.y)

## Y coordinate on screen corresponding to the virtual floor (above macOS Dock)
func get_floor_screen_y(screen_id: int = -1) -> float:
	if screen_id == -1:
		screen_id = DisplayServer.window_get_current_screen()
	var usable = DisplayServer.screen_get_usable_rect(screen_id)
	var screen_pos = DisplayServer.screen_get_position(screen_id)
	var usable_bottom = float(usable.position.y - screen_pos.y + usable.size.y)
	return minf(usable_bottom - 50.0, screen_height - 70.0)

## Full-screen 2D safe area for free roaming (both horizontal and vertical)
func get_walkable_screen_rect(screen_id: int = -1) -> Rect2:
	if screen_id == -1:
		screen_id = DisplayServer.window_get_current_screen()
	var usable = DisplayServer.screen_get_usable_rect(screen_id)
	var screen_pos = DisplayServer.screen_get_position(screen_id)
	var usable_top = float(usable.position.y - screen_pos.y)
	var usable_bottom = float(usable.position.y - screen_pos.y + usable.size.y)
	var min_y = maxf(usable_top + 60.0, top_margin)
	var max_y = minf(usable_bottom - 60.0, screen_height - bottom_margin)
	var min_x = left_margin
	var max_x = screen_width - right_margin
	return Rect2(min_x, min_y, maxf(max_x - min_x, 100.0), maxf(max_y - min_y, 100.0))

## Minimum and Maximum walkable X coordinates on screen
func get_walkable_screen_range() -> Vector2:
	return Vector2(left_margin, screen_width - right_margin)

## Clamps screen X and Y within margins
func clamp_screen_pos(pos: Vector2) -> Vector2:
	var rect = get_walkable_screen_rect()
	return Vector2(
		clampf(pos.x, rect.position.x, rect.end.x),
		clampf(pos.y, rect.position.y, rect.end.y)
	)

func clamp_screen_x(x: float) -> float:
	var range_x = get_walkable_screen_range()
	return clampf(x, range_x.x, range_x.y)

## Converts a 2D screen coordinate to 3D world coordinates on plane Z = z_depth
func screen_to_world(screen_pos: Vector2, camera: Camera3D, z_depth: float = 0.0) -> Vector3:
	if camera == null:
		return Vector3.ZERO
	var ray_origin = camera.project_ray_origin(screen_pos)
	return Vector3(ray_origin.x, ray_origin.y, z_depth)

func screen_to_world_floor(screen_pos: Vector2, camera: Camera3D, _floor_y: float = 0.0) -> Vector3:
	return screen_to_world(screen_pos, camera, 0.0)

## Converts 3D world coordinate to 2D screen coordinate
func world_to_screen(world_pos: Vector3, camera: Camera3D) -> Vector2:
	if camera == null:
		return Vector2.ZERO
	return camera.unproject_position(world_pos)
