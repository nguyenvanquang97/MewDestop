class_name ContextMenu
extends Control

## GTA V Action/Weapon Wheel Context Menu (Vòng quay vũ khí GTA 5 - Bản Phóng To Cực Nét)
## Extra Large 480px diameter for high-resolution & Retina displays.

signal action_triggered(action_name: String)

@onready var center_hub: Control = %CenterHub
@onready var lbl_icon: Label = %LblIcon
@onready var lbl_title: Label = %LblTitle
@onready var lbl_desc: Label = %LblDesc

const WHEEL_SIZE: float = 480.0
const CENTER: Vector2 = Vector2(240.0, 240.0)
const RADIUS_OUTER: float = 216.0
const RADIUS_INNER: float = 88.0
const RADIUS_CENTER: float = 80.0
const DEADZONE_RADIUS: float = 60.0

var hovered_index: int = -1
var _current_tween: Tween = null
var _slice_containers: Array[Control] = []

# GTA V Wheel Segments (automatically distributed across 360°)
const SLICES: Array[Dictionary] = [
	{
		"action": "feed",
		"icon": "🐟",
		"title": "CHO ĂN",
		"desc": "+35 NO NÊ  •  +15 VUI VẺ",
		"color": Color(1.0, 0.65, 0.12) # GTA Amber Gold
	},
	{
		"action": "drink_milk",
		"icon": "🥛",
		"title": "UỐNG SỮA",
		"desc": "+25 NO NÊ  •  +20 THỂ LỰC",
		"color": Color(0.92, 0.95, 1.0) # Cream White Milk
	},
	{
		"action": "play",
		"icon": "🧶",
		"title": "CHƠI ĐÙA",
		"desc": "+20 HƯNG PHẤN  •  -15 THỂ LỰC",
		"color": Color(1.0, 0.82, 0.18) # Bright Gold
	},
	{
		"action": "pet",
		"icon": "❤️",
		"title": "VUỐT VE",
		"desc": "+10 THÂN THIẾT  •  MÈO RỪ RỪ",
		"color": Color(1.0, 0.38, 0.60) # Neon Pink
	},
	{
		"action": "sleep",
		"icon": "💤",
		"title": "ĐI NGỦ",
		"desc": "HỒI PHỤC THỂ LỰC  •  TIẾT KIỆM PIN",
		"color": Color(0.40, 0.60, 1.0) # Sky Blue
	},
	{
		"action": "switch_screen",
		"icon": "🖥️",
		"title": "ĐỔI MÀN",
		"desc": "CHUYỂN SANG MÀN HÌNH KHÁC",
		"color": Color(0.18, 0.88, 0.70) # Mint Turquoise
	},
	{
		"action": "switch_pet",
		"icon": "🐾",
		"title": "ĐỔI PET",
		"desc": "CHUYỂN ĐỔI: 🐱 MÈO ⇄ 🐕 SHIBA",
		"color": Color(0.96, 0.58, 0.18) # Warm Shiba Orange
	},
	{
		"action": "quit",
		"icon": "✕",
		"title": "THOÁT",
		"desc": "LƯU TRẠNG THÁI  •  ĐÓNG ỨNG DỤNG",
		"color": Color(0.96, 0.30, 0.30) # Coral Red
	}
]

var is_open: bool = false

func _ready() -> void:
	hide()
	custom_minimum_size = Vector2(WHEEL_SIZE, WHEEL_SIZE)
	size = Vector2(WHEEL_SIZE, WHEEL_SIZE)
	pivot_offset = CENTER
	mouse_filter = MOUSE_FILTER_STOP
	_setup_slice_elements()

func _setup_slice_elements() -> void:
	for c in _slice_containers:
		c.queue_free()
	_slice_containers.clear()

	var n = SLICES.size()
	var angular_span = TAU / float(n)
	var r_mid = (RADIUS_INNER + RADIUS_OUTER) * 0.52

	for i in range(n):
		var s = SLICES[i]
		var mid_angle = (-PI * 0.5) + (i * angular_span)
		var icon_pos = CENTER + Vector2(cos(mid_angle), sin(mid_angle)) * r_mid

		# Container to hold both large Icon and Text on the slice
		var container = VBoxContainer.new()
		container.custom_minimum_size = Vector2(100, 64)
		container.size = Vector2(100, 64)
		container.pivot_offset = Vector2(50, 32)
		container.position = icon_pos - Vector2(50, 32)
		container.mouse_filter = Control.MOUSE_FILTER_IGNORE
		container.alignment = BoxContainer.ALIGNMENT_CENTER
		container.add_theme_constant_override("separation", 2)

		# Icon Label
		var lbl_i = Label.new()
		lbl_i.name = "Icon"
		lbl_i.text = s["icon"]
		lbl_i.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_i.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		lbl_i.add_theme_font_size_override("font_size", 30)
		lbl_i.mouse_filter = Control.MOUSE_FILTER_IGNORE
		container.add_child(lbl_i)

		# Title Label on slice
		var lbl_t = Label.new()
		lbl_t.name = "Title"
		lbl_t.text = s["title"]
		lbl_t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl_t.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		lbl_t.add_theme_font_size_override("font_size", 13)
		lbl_t.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
		lbl_t.add_theme_color_override("font_outline_color", Color(0.06, 0.07, 0.12))
		lbl_t.add_theme_constant_override("outline_size", 4)
		lbl_t.mouse_filter = Control.MOUSE_FILTER_IGNORE
		container.add_child(lbl_t)

		add_child(container)
		_slice_containers.append(container)

func _process(_delta: float) -> void:
	if not visible or not is_inside_tree():
		return
	_update_mouse_selection()

## Directional mouse raycast to detect active slice
func _update_mouse_selection(local_pos: Vector2 = Vector2.INF) -> void:
	if local_pos == Vector2.INF:
		if not is_inside_tree():
			return
		local_pos = get_local_mouse_position()

	var diff = local_pos - CENTER
	var dist = diff.length()

	var new_index = -1
	if dist >= DEADZONE_RADIUS and dist <= (RADIUS_OUTER + 35.0):
		var angle_deg = rad_to_deg(diff.angle())
		var n = SLICES.size()
		var span_deg = 360.0 / float(n)
		# Normalize so North (-90 deg) is slice 0
		var norm_angle = wrapf(angle_deg + 90.0 + (span_deg * 0.5), 0.0, 360.0)
		new_index = int(norm_angle / span_deg)
		new_index = clampi(new_index, 0, n - 1)

	if new_index != hovered_index:
		hovered_index = new_index
		_update_center_hub()
		_update_slice_icons()
		queue_redraw()

func _update_slice_icons() -> void:
	for i in range(_slice_containers.size()):
		var c = _slice_containers[i]
		var lbl_t: Label = c.get_node_or_null("Title")
		if i == hovered_index:
			c.scale = Vector2(1.25, 1.25)
			c.modulate = Color(1.0, 1.0, 1.0, 1.0)
			if lbl_t:
				lbl_t.add_theme_color_override("font_color", Color(0.1, 0.1, 0.15))
				lbl_t.add_theme_color_override("font_outline_color", Color(1.0, 1.0, 1.0))
		else:
			c.scale = Vector2.ONE
			c.modulate = Color(0.92, 0.92, 0.98, 0.90)
			if lbl_t:
				lbl_t.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
				lbl_t.add_theme_color_override("font_outline_color", Color(0.06, 0.07, 0.12))

func _update_center_hub() -> void:
	_ensure_nodes()
	if not lbl_title or not lbl_desc or not lbl_icon:
		return

	if hovered_index >= 0 and hovered_index < SLICES.size():
		var s = SLICES[hovered_index]
		lbl_icon.text = s["icon"]
		lbl_title.text = s["title"]
		lbl_desc.text = s["desc"]
		lbl_title.add_theme_color_override("font_color", s["color"])
		lbl_desc.add_theme_color_override("font_color", s["color"].lightened(0.30))
		
		# Snappy punch bounce on center hub
		if is_inside_tree():
			var tw = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			center_hub.scale = Vector2(1.10, 1.10)
			tw.tween_property(center_hub, "scale", Vector2.ONE, 0.12)
	else:
		lbl_icon.text = "🐾"
		lbl_title.text = "NEKODESK"
		lbl_desc.text = "CHỌN HÀNH ĐỘNG"
		lbl_title.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
		lbl_desc.add_theme_color_override("font_color", Color(0.80, 0.82, 0.90))

func _ensure_nodes() -> void:
	if not center_hub:
		center_hub = %CenterHub if has_node("%CenterHub") else find_child("CenterHub", true, false)
	if not lbl_icon:
		lbl_icon = %LblIcon if has_node("%LblIcon") else find_child("LblIcon", true, false)
	if not lbl_title:
		lbl_title = %LblTitle if has_node("%LblTitle") else find_child("LblTitle", true, false)
	if not lbl_desc:
		lbl_desc = %LblDesc if has_node("%LblDesc") else find_child("LblDesc", true, false)

func _gui_input(event: InputEvent) -> void:
	if not is_open:
		return

	if event is InputEventMouseMotion:
		_update_mouse_selection(event.position)
	elif event is InputEventMouseButton:
		if event.pressed:
			if event.button_index == MOUSE_BUTTON_LEFT:
				_update_mouse_selection(event.position)
				if hovered_index >= 0 and hovered_index < SLICES.size():
					var action = SLICES[hovered_index]["action"]
					_on_action(action)
					accept_event()
				elif (event.position - CENTER).length() < DEADZONE_RADIUS:
					close_menu()
					accept_event()
			elif event.button_index == MOUSE_BUTTON_RIGHT:
				close_menu()
				accept_event()
		else:
			# Consume mouse button release to prevent bubbling to cat
			accept_event()

## Draws the iconic GTA V segmented donut wheel (Extra Large)
func _draw() -> void:
	var n = SLICES.size()
	var angular_span = TAU / float(n) # 60 degrees in radians
	var gap_rad = deg_to_rad(2.4)      # Angular gap between slices

	# Outer subtle drop shadow ring
	draw_circle(CENTER, RADIUS_OUTER + 12.0, Color(0.0, 0.0, 0.0, 0.45))

	for i in range(n):
		var is_hovered = (i == hovered_index)
		var s = SLICES[i]
		
		# Center angle for slice i: slice 0 is -PI/2 (North)
		var mid_angle = (-PI * 0.5) + (i * angular_span)
		var start_angle = mid_angle - (angular_span * 0.5) + (gap_rad * 0.5)
		var end_angle = mid_angle + (angular_span * 0.5) - (gap_rad * 0.5)

		# Outer & Inner radii (hovered slice pops outward with mechanical snap!)
		var r_out = RADIUS_OUTER + (9.0 if is_hovered else 0.0)
		var r_in = RADIUS_INNER - (3.0 if is_hovered else 0.0)

		# Build polygon vertices for annular sector
		var points = PackedVector2Array()
		var steps = 18

		# Outer arc
		for step in range(steps + 1):
			var a = lerpf(start_angle, end_angle, float(step) / float(steps))
			points.append(CENTER + Vector2(cos(a), sin(a)) * r_out)

		# Inner arc (reverse direction)
		for step in range(steps, -1, -1):
			var a = lerpf(start_angle, end_angle, float(step) / float(steps))
			points.append(CENTER + Vector2(cos(a), sin(a)) * r_in)

		# Shading and highlights
		var fill_color: Color
		var border_color: Color
		var border_width: float

		if is_hovered:
			# GTA V Signature Amber Gold Highlight
			fill_color = Color(s["color"].r, s["color"].g, s["color"].b, 0.96)
			border_color = Color(1.0, 1.0, 1.0, 1.0)
			border_width = 3.5
		else:
			# Sleek dark frosted glass
			fill_color = Color(0.08, 0.09, 0.15, 0.90)
			border_color = Color(1.0, 1.0, 1.0, 0.20)
			border_width = 2.0

		# Draw filled slice polygon
		draw_colored_polygon(points, fill_color)

		# Close polyline for crisp border
		var outline_points = points.duplicate()
		outline_points.append(points[0])
		draw_polyline(outline_points, border_color, border_width, true)

	# Center Hub Base Circles
	draw_circle(CENTER, RADIUS_CENTER + 3.0, Color(0.05, 0.06, 0.10, 0.98))
	var center_rim_color = SLICES[hovered_index]["color"] if hovered_index >= 0 else Color(1.0, 1.0, 1.0, 0.40)
	draw_arc(CENTER, RADIUS_CENTER + 3.0, 0.0, TAU, 48, center_rim_color, 3.0, true)

## Shows the GTA V wheel smoothly centered at screen_pos
func show_at(target_center: Vector2) -> void:
	if _slice_containers.is_empty():
		_setup_slice_elements()

	var vp_size = get_viewport_rect().size if is_inside_tree() else Vector2(1920, 1080)
	var half = Vector2(WHEEL_SIZE * 0.5, WHEEL_SIZE * 0.5)

	# Clamp to remain completely on screen
	var clamped_x = clampf(target_center.x - half.x, 15.0, vp_size.x - WHEEL_SIZE - 15.0)
	var clamped_y = clampf(target_center.y - half.y, 15.0, vp_size.y - WHEEL_SIZE - 15.0)
	global_position = Vector2(clamped_x, clamped_y)

	hovered_index = -1
	_update_center_hub()
	_update_slice_icons()
	is_open = true
	show()
	queue_redraw()

	# Snappy GTA V popup animation
	if _current_tween and _current_tween.is_valid():
		_current_tween.kill()

	scale = Vector2(0.35, 0.35)
	modulate.a = 0.0

	_current_tween = create_tween().set_parallel(true)
	_current_tween.tween_property(self, "scale", Vector2.ONE, 0.18)\
		.set_trans(Tween.TRANS_BACK)\
		.set_ease(Tween.EASE_OUT)
	_current_tween.tween_property(self, "modulate:a", 1.0, 0.14)

func close_menu() -> void:
	if not visible:
		return

	is_open = false
	if _current_tween and _current_tween.is_valid():
		_current_tween.kill()

	_current_tween = create_tween().set_parallel(true)
	_current_tween.tween_property(self, "scale", Vector2(0.4, 0.4), 0.12)\
		.set_trans(Tween.TRANS_QUAD)\
		.set_ease(Tween.EASE_IN)
	_current_tween.tween_property(self, "modulate:a", 0.0, 0.10)

	_current_tween.chain().tween_callback(func():
		hide()
		hovered_index = -1
	)

func _on_action(action_name: String) -> void:
	close_menu()
	action_triggered.emit(action_name)

## Returns the composite bounding rect for macOS mouse passthrough
func get_menu_rect() -> Rect2:
	if not visible:
		return Rect2()
	return Rect2(global_position, size)
