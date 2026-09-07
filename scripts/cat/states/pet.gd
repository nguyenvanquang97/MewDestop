class_name PetState
extends CatState

var timer: float = 0.0
const DURATION: float = 1.8

func enter(_prev: String) -> void:
	timer = 0.0
	cat.play_animation("Pet")
	cat.show_emote("heart")
	cat.stats.modify_stat("happiness", 10.0)
	cat.stats.modify_stat("affection", 5.0)

func update(delta: float) -> void:
	timer += delta
	if timer >= DURATION:
		cat.change_state("Idle")
