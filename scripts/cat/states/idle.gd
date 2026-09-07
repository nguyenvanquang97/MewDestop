class_name IdleState
extends CatState

var timer: float = 0.0
var duration: float = 6.0

func enter(_prev: String) -> void:
	cat.play_animation("Idle")
	duration = randf_range(cat.behavior.min_idle_duration, cat.behavior.max_idle_duration)
	timer = 0.0

func update(delta: float) -> void:
	timer += delta
	if timer >= duration:
		var next = cat.behavior.decide_next_state(cat.stats.current_mood)
		if next != "Idle":
			cat.change_state(next)
		else:
			# Reset idle timer with fresh random duration
			timer = 0.0
			duration = randf_range(cat.behavior.min_idle_duration, cat.behavior.max_idle_duration)
