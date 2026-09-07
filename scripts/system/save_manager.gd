class_name SaveManager
extends Node

## Handles local JSON persistence (user://save.json) and offline progression calculation.

var save_path: String = "user://save.json"

# Maximum offline time to progress in seconds (e.g. 12 hours = 43200s) to prevent runaway stats
const MAX_OFFLINE_SECONDS: float = 43200.0

signal save_loaded(stats_data: Dictionary, offline_seconds: float)

func _ready() -> void:
	# Check if user:// is writable; if not (e.g. sandboxed test), use local fallback
	var test_file = FileAccess.open("user://.test_write", FileAccess.WRITE)
	if not test_file:
		save_path = "res://user_data/save.json"
		DirAccess.make_dir_absolute("res://user_data")
	else:
		test_file.close()
		DirAccess.remove_absolute("user://.test_write")

func save_game(stats_data: Dictionary) -> bool:
	var data_to_save = stats_data.duplicate()
	data_to_save["last_seen"] = int(Time.get_unix_time_from_system())
	data_to_save["version"] = 1

	var json_str = JSON.stringify(data_to_save, "\t")
	var file = FileAccess.open(save_path, FileAccess.WRITE)
	if not file:
		push_error("[SaveManager] Failed to write save file at %s: %s" % [save_path, FileAccess.get_open_error()])
		return false

	file.store_string(json_str)
	file.close()
	print("[SaveManager] State saved successfully at %s" % save_path)
	return true

func load_game() -> Dictionary:
	if not FileAccess.file_exists(save_path):
		print("[SaveManager] No existing save found at %s. Using default stats." % save_path)
		return {}

	var file = FileAccess.open(save_path, FileAccess.READ)
	if not file:
		push_error("[SaveManager] Failed to read save file at %s" % save_path)
		return {}

	var content = file.get_as_text()
	file.close()

	var json = JSON.new()
	var err = json.parse(content)
	if err != OK:
		push_error("[SaveManager] Corrupt save file: %s" % json.get_error_message())
		return {}

	var data: Dictionary = json.get_data()
	var last_seen: int = int(data.get("last_seen", 0))
	var current_time: int = int(Time.get_unix_time_from_system())

	var offline_seconds: float = 0.0
	if last_seen > 0 and current_time > last_seen:
		offline_seconds = minf(float(current_time - last_seen), MAX_OFFLINE_SECONDS)

	print("[SaveManager] Save loaded. Offline duration: %.1f minutes" % (offline_seconds / 60.0))
	save_loaded.emit(data, offline_seconds)
	return data
