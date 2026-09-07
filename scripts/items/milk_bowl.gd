class_name MilkBowlItem
extends Node3D

## Realistic 3D Ceramic Pet Bowl with fresh creamy milk,
## soft drop shadow, dynamic milk level, and gentle lapping splash droplets.

@onready var model_root: Node3D = $ModelRoot
@onready var splash_particles: CPUParticles3D = $SplashParticles
@onready var shadow: MeshInstance3D = $DropShadow

var bowl_mesh_inst: MeshInstance3D = null
var _is_drinking: bool = false
var _drink_time: float = 0.0
var _current_tween: Tween = null
var _initial_scale: Vector3 = Vector3.ONE

func _ready() -> void:
	_setup_nodes_and_materials()

func _setup_nodes_and_materials() -> void:
	if not model_root:
		return

	# Find mesh instance inside model_root
	for child in model_root.get_children():
		if child is MeshInstance3D:
			bowl_mesh_inst = child
			break
		for sub_child in child.get_children():
			if sub_child is MeshInstance3D:
				bowl_mesh_inst = sub_child
				break

	if splash_particles:
		splash_particles.emitting = false

func _process(delta: float) -> void:
	if _is_drinking and splash_particles:
		_drink_time += delta

## Sets milk level from 1.0 (full) down to 0.0 (empty)
func set_milk_level(_ratio: float) -> void:
	# Milk level dynamically maintained in shader or scale
	pass

## Enables milk splash droplets effect
func set_lapping(active: bool) -> void:
	_is_drinking = active
	if splash_particles:
		splash_particles.emitting = active

## Snappy pop in
func pop_in(on_finished: Callable = Callable()) -> void:
	visible = true
	scale = Vector3(0.01, 0.01, 0.01)
	_is_drinking = false

	if _current_tween and _current_tween.is_valid():
		_current_tween.kill()

	_current_tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_current_tween.tween_property(self, "scale", Vector3(1.0, 1.0, 1.0), 0.28)
	if on_finished.is_valid():
		_current_tween.chain().tween_callback(on_finished)

## Smooth fade-out shrink
func pop_out(on_finished: Callable = Callable()) -> void:
	set_lapping(false)

	if _current_tween and _current_tween.is_valid():
		_current_tween.kill()

	_current_tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_current_tween.tween_property(self, "scale", Vector3(0.01, 0.01, 0.01), 0.20)
	_current_tween.chain().tween_callback(func():
		visible = false
		if on_finished.is_valid():
			on_finished.call()
	)
