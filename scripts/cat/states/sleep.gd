class_name SleepState
extends CatState

var timer: float = 0.0
var duration: float = 20.0
var emote_timer: float = 0.0

func enter(_prev: String) -> void:
	cat.play_animation("Sleep")
	cat.show_emote("sleep")
	duration = randf_range(15.0, 30.0)
	timer = 0.0
	emote_timer = 0.0
	
	# Power saving: reduce frame rate during sleep
	Engine.max_fps = 15

func exit() -> void:
	# Restore normal 30 FPS upon waking
	Engine.max_fps = 30

func update(delta: float) -> void:
	timer += delta
	emote_timer += delta
	if emote_timer >= 4.5:
		emote_timer = 0.0
		cat.show_emote("sleep")

	# Recover 1 energy per second while sleeping
	cat.stats.modify_stat("energy", 1.0 * delta)
	
	if timer >= duration:
		cat.change_state("Idle")
