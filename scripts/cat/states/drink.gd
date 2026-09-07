class_name DrinkState
extends CatState

## Cat drinking milk state:
## 1. Pops up the beautiful 3D cartoon milk saucer in front of the cat.
## 2. Cat crouches, bends neck and head down to the saucer, and laps milk rhythmically.
## 3. Milk level decreases dynamically, splash particles emit softly.
## 4. Cat finishes drinking, raises head, pops a heart emote, and returns to Idle.

var timer: float = 0.0
const DURATION: float = 3.8
var _lapping_active: bool = false

func enter(_prev: String) -> void:
	timer = 0.0
	_lapping_active = false
	cat.play_animation("sit_drink")
	# Orient cat to a natural 3/4 profile angle
	cat.target_rotation_y = deg_to_rad(30.0) if cat.facing_direction >= 0 else deg_to_rad(-30.0)
	cat.show_milk_bowl(true)

func exit() -> void:
	cat.set_milk_bowl_lapping(false)
	cat.show_milk_bowl(false)

func update(delta: float) -> void:
	timer += delta

	# Phase 1: 0.0 -> 0.35s: Bowl pops in, cat starts bending down
	if timer < 0.35:
		cat.set_milk_bowl_level(1.0)
	# Phase 2: 0.35 -> 3.1s: Actively lapping milk
	elif timer < 3.1:
		if not _lapping_active:
			_lapping_active = true
			cat.set_milk_bowl_lapping(true)
		# Progressively lower milk level
		var progress = (timer - 0.35) / 2.75
		var milk_ratio = 1.0 - progress * 0.75 # lowers to 25%
		cat.set_milk_bowl_level(milk_ratio)
	# Phase 3: 3.1 -> 3.8s: Done drinking! Satisfied, head lifts up, heart emote
	else:
		if _lapping_active:
			_lapping_active = false
			cat.set_milk_bowl_lapping(false)
			cat.show_emote("heart")
			cat.stats.modify_stat("hunger", -30.0)
			cat.stats.modify_stat("energy", 20.0)
			cat.stats.modify_stat("happiness", 25.0)

	if timer >= DURATION:
		cat.change_state("Idle")

