class_name CatState
extends Node

## Base class for all Cat states.

var cat: Cat

func enter(_previous_state: String) -> void:
	pass

func exit() -> void:
	pass

func update(_delta: float) -> void:
	pass

func physics_update(_delta: float) -> void:
	pass

func handle_input(_event: InputEvent) -> void:
	pass
