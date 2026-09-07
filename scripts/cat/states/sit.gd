class_name SitState
extends CatState

var timer: float = 0.0
var duration: float = 8.0

func enter(_prev: String) -> void:
	cat.play_animation("Sit")
	duration = randf_range(6.0, 14.0)
	timer = 0.0

func update(delta: float) -> void:
	timer += delta
	if timer >= duration:
		cat.change_state("Idle")
