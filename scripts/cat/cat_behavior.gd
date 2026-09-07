class_name CatBehaviorConfig
extends RefCounted

## Configurable autonomous behavior probabilities and duration timers.

var min_idle_duration: float = 5.0
var max_idle_duration: float = 12.0

# Base probabilities (summing up to 100)
var prob_walk: float = 30.0
var prob_sit: float = 25.0
var prob_sleep: float = 15.0
var prob_idle: float = 30.0

## Selects the next autonomous state weighted by current mood
func decide_next_state(mood: String = "NORMAL") -> String:
	var w_walk = prob_walk
	var w_sit = prob_sit
	var w_sleep = prob_sleep
	var w_idle = prob_idle

	# Modulate weights by mood
	match mood:
		"TIRED":
			w_sleep *= 3.0
			w_walk *= 0.3
		"HAPPY", "EXCITED":
			w_walk *= 1.8
			w_sleep *= 0.4
		"HUNGRY":
			w_sit *= 1.5
			w_sleep *= 0.5
		"SAD":
			w_sit *= 1.8
			w_walk *= 0.5

	var total = w_walk + w_sit + w_sleep + w_idle
	var roll = randf_range(0.0, total)

	if roll < w_walk:
		return "Walk"
	roll -= w_walk

	if roll < w_sit:
		return "Sit"
	roll -= w_sit

	if roll < w_sleep:
		return "Sleep"

	return "Idle"
