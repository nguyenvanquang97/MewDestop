class_name IdleState
extends CatState

var timer: float = 0.0
var duration: float = 6.0
var _exhausted_emote_timer: float = 0.0
const EXHAUSTED_EMOTE_INTERVAL: float = 12.0

func enter(_prev: String) -> void:
	if cat.stats and cat.stats.is_exhausted() and cat.pet_type == "shiba":
		cat.play_animation("Idle_2_HeadLow")
	else:
		cat.play_animation("Idle")

	duration = randf_range(cat.behavior.min_idle_duration, cat.behavior.max_idle_duration)
	timer = 0.0
	_exhausted_emote_timer = 0.0

func update(delta: float) -> void:
	timer += delta

	# Periodic visual cues when hungry, thirsty, or exhausted
	if cat.stats and cat.stats.is_exhausted():
		_exhausted_emote_timer += delta
		if _exhausted_emote_timer >= EXHAUSTED_EMOTE_INTERVAL:
			_exhausted_emote_timer = 0.0
			if cat.stats.thirst >= 75.0:
				cat.show_emote("milk")
			elif cat.stats.hunger >= 75.0:
				cat.show_emote("hungry")
			else:
				cat.show_emote("sweat")
			if cat.pet_type == "shiba":
				cat.play_animation("Idle_2_HeadLow")

	if timer >= duration:
		var next = cat.behavior.decide_next_state(cat.stats.current_mood)
		if next != "Idle":
			cat.change_state(next)
		else:
			# Reset idle timer with fresh random duration
			timer = 0.0
			duration = randf_range(cat.behavior.min_idle_duration, cat.behavior.max_idle_duration)
			if cat.stats and cat.stats.is_exhausted() and cat.pet_type == "shiba":
				cat.play_animation("Idle_2_HeadLow")
			else:
				cat.play_animation("Idle")

