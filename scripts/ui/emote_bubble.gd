class_name EmoteBubble
extends Node3D

## 3D Billboard Emote Bubble: displays floating animated emotion icons
## (❤️, 💤, 🐟, ❓, 💧, ✨) above the cat's head.

@onready var label: Label3D = $Label3D
var _current_tween: Tween

func _ready() -> void:
	if not label:
		label = Label3D.new()
		label.name = "Label3D"
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.font_size = 54
		label.pixel_size = 0.005
		label.outline_size = 6
		label.outline_modulate = Color(0, 0, 0, 0.5)
		label.render_priority = 10
		add_child(label)

	scale = Vector3.ZERO
	visible = false

## Plays a bouncing, floating pop animation for the given emoji
func pop(emoji: String, duration: float = 1.8) -> void:
	if not label:
		return

	label.text = emoji
	visible = true
	position = Vector3(0, 1.1, 0)
	scale = Vector3.ZERO
	label.modulate.a = 1.0

	if _current_tween and _current_tween.is_valid():
		_current_tween.kill()

	_current_tween = create_tween().set_parallel(true)
	
	# Pop scale effect (spring bounce)
	_current_tween.tween_property(self, "scale", Vector3.ONE * 1.15, 0.2)\
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	
	# Float upward
	_current_tween.tween_property(self, "position:y", 1.5, duration)\
		.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	
	# Fade out near the end
	_current_tween.tween_property(label, "modulate:a", 0.0, 0.4)\
		.set_delay(duration - 0.4)\
		.set_trans(Tween.TRANS_SINE)

	_current_tween.chain().tween_callback(func(): visible = false)
