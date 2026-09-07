class_name CatStats
extends RefCounted

## Virtual pet stats: Hunger, Energy, Happiness, Affection, and Mood.

signal stats_changed(stats_dict: Dictionary)
signal mood_changed(new_mood: String)

var hunger: float = 20.0     # 0 (full) to 100 (starving)
var energy: float = 85.0     # 0 (exhausted) to 100 (energetic)
var happiness: float = 80.0  # 0 (depressed) to 100 (ecstatic)
var affection: float = 40.0  # 0 (unfriendly) to 100 (bonded)

var current_mood: String = "NORMAL"

# Rates per hour (3600 seconds)
const HUNGER_RATE_PER_HOUR: float = 8.0
const ENERGY_DECAY_PER_HOUR: float = 5.0
const HAPPINESS_DECAY_PER_HOUR: float = 4.0

func _init() -> void:
	recalculate_mood()

func update(delta: float) -> void:
	var hours = delta / 3600.0
	hunger = clampf(hunger + HUNGER_RATE_PER_HOUR * hours, 0.0, 100.0)
	energy = clampf(energy - ENERGY_DECAY_PER_HOUR * hours, 0.0, 100.0)
	happiness = clampf(happiness - HAPPINESS_DECAY_PER_HOUR * hours, 0.0, 100.0)
	recalculate_mood()

func modify_stat(stat_name: String, amount: float) -> void:
	match stat_name:
		"hunger":
			hunger = clampf(hunger + amount, 0.0, 100.0)
		"energy":
			energy = clampf(energy + amount, 0.0, 100.0)
		"happiness":
			happiness = clampf(happiness + amount, 0.0, 100.0)
		"affection":
			affection = clampf(affection + amount, 0.0, 100.0)
	
	recalculate_mood()
	stats_changed.emit(to_dict())

func feed(amount: float = 30.0) -> void:
	modify_stat("hunger", -amount)
	modify_stat("happiness", 10.0)

func recalculate_mood() -> void:
	var old_mood = current_mood
	if energy < 25.0:
		current_mood = "TIRED"
	elif hunger > 75.0:
		current_mood = "HUNGRY"
	elif happiness > 80.0 and energy > 50.0:
		current_mood = "HAPPY"
	elif happiness < 30.0:
		current_mood = "SAD"
	else:
		current_mood = "NORMAL"

	if current_mood != old_mood:
		mood_changed.emit(current_mood)

func apply_offline_time(seconds: float) -> void:
	var hours = seconds / 3600.0
	# Pet gets hungry and loses some energy while offline, but clamped safely so it never dies
	hunger = clampf(hunger + HUNGER_RATE_PER_HOUR * hours * 0.7, 0.0, 95.0)
	energy = clampf(energy + 10.0 * hours, 0.0, 100.0) # Rested while away
	happiness = clampf(happiness - HAPPINESS_DECAY_PER_HOUR * hours * 0.5, 20.0, 100.0)
	recalculate_mood()

func to_dict() -> Dictionary:
	return {
		"hunger": hunger,
		"energy": energy,
		"happiness": happiness,
		"affection": affection,
		"mood": current_mood
	}

func from_dict(data: Dictionary) -> void:
	hunger = float(data.get("hunger", hunger))
	energy = float(data.get("energy", energy))
	happiness = float(data.get("happiness", happiness))
	affection = float(data.get("affection", affection))
	recalculate_mood()
