extends Node2D

const FRAME_SIZE := Vector2(1920.0, 1080.0)
const DURATION := 86.0
const BPM := 112.0
const SONG_START := 10.0
const BEAT_SECONDS := 60.0 / BPM
const BAR_SECONDS := BEAT_SECONDS * 4.0
const CHARACTER_SHADER: Shader = preload("res://godot/shaders/uta_motion.gdshader")
const POSE_TEXTURES: Array[Texture2D] = [
	preload("res://godot/assets/character/uta_front_prototype_v4.png"),
	preload("res://godot/assets/character/uta_pose_verse_v1.png"),
	preload("res://godot/assets/character/uta_pose_chorus_v1.png"),
	preload("res://godot/assets/character/uta_pose_reach_v1.png"),
]
const POSE_NAMES := ["neutral", "verse", "chorus", "reach"]
const LYRIC_CUES := [
	[10.0, "白い地平に　ひとりぶんの影"],
	[12.3, "呼ばれた気がして　振り向いた"],
	[14.6, "知らない昨日を　探すより先に"],
	[16.9, "胸の奥で　音が息をした"],
	[19.2, "震える指先　マイクに触れたら"],
	[21.5, "まぶしい誰かが　すぐ消えた"],
	[23.8, "思い出せなくて　それでもなぜか"],
	[26.1, "この場所に立つ意味を知ってる"],
	[29.0, "空っぽのままでも　声は生まれる"],
	[33.4, "最初の一音を　ここに灯そう"],
	[38.0, "ここから、まだ　何もない空へ"],
	[40.2, "私の「今」を響かせて"],
	[42.4, "答えじゃなくていい　名前のない願い"],
	[45.0, "消えないように歌うよ"],
	[47.4, "ここから、まだ　ひとりでも歌う"],
	[49.6, "見えない誰かに届くまで"],
	[51.8, "昨日を知らないこの心で"],
	[54.0, "明日をはじめてみたい"],
	[56.5, "もしもこの声を"],
	[59.0, "覚えてる人がいるなら"],
	[61.6, "私はここにいる"],
	[64.0, "ここから、まだ　終わらない音を"],
	[67.0, "白い世界に置いていく"],
	[70.0, "誰かがどこかで聞いているなら"],
	[73.0, "もう一度　歌えるから"],
	[76.4, "ここから——"],
	[78.0, "まだ"],
	[79.6, ""],
]

var timeline := 0.0
var paused := false
var capture_mode := false
var capture_frames := 0
var movie_mode := false
var movie_end_frames := 0
var character_root: Node2D
var pose_sprites: Array[Sprite2D] = []
var pose_materials: Array[ShaderMaterial] = []
var current_pose := -1
var pose_hit := 0.0
var character_shadow: EllipseDrawing
var microphone: MicrophoneDrawing
var flower: FlowerDrawing
var stage_fx: StageDrawing
var memory_flash: MemoryFlashDrawing
var title_label: Label
var cue_label: Label
var lyric_label: Label
var world_label: Label
var progress_bar: ColorRect
var progress_bg: ColorRect
var help_label: Label
var camera: Camera2D


func _ready() -> void:
	_build_scene()
	var all_args := OS.get_cmdline_args()
	capture_mode = "--capture" in OS.get_cmdline_user_args() or "--capture" in all_args
	movie_mode = "--movie" in OS.get_cmdline_user_args() or "--movie" in all_args
	if movie_mode:
		title_label.visible = false
		help_label.visible = false
		progress_bg.visible = false
		progress_bar.visible = false
	print("LIVE #001 edit v2 ready. Capture: %s, movie: %s" % [capture_mode, movie_mode])
	if capture_mode:
		timeline = 44.0
		_update_sequence(0.0)


func _process(delta: float) -> void:
	if not paused and not capture_mode:
		if movie_mode:
			timeline = minf(timeline + delta, DURATION)
			if timeline >= DURATION:
				movie_end_frames += 1
		else:
			timeline = fmod(timeline + delta, DURATION)
	_update_sequence(delta)
	queue_redraw()
	if movie_mode and movie_end_frames >= 2:
		get_tree().quit()
	if capture_mode:
		capture_frames += 1
		if capture_frames >= 3:
			_capture_preview()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		paused = not paused
	elif event.is_action_pressed("ui_cancel"):
		get_tree().quit()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_R:
		timeline = 0.0


func _build_scene() -> void:
	stage_fx = StageDrawing.new()
	stage_fx.name = "WhiteWorld"
	add_child(stage_fx)

	character_shadow = EllipseDrawing.new()
	character_shadow.position = Vector2(820.0, 966.0)
	character_shadow.ellipse_size = Vector2(250.0, 28.0)
	character_shadow.color = Color(0.30, 0.48, 0.62, 0.11)
	add_child(character_shadow)

	character_root = Node2D.new()
	character_root.name = "UtaPoseRig"
	character_root.position = Vector2(820.0, 1015.0)
	add_child(character_root)

	for index in POSE_TEXTURES.size():
		var sprite := Sprite2D.new()
		sprite.name = "UtaPose_%s" % POSE_NAMES[index]
		sprite.texture = POSE_TEXTURES[index]
		sprite.centered = true
		sprite.position = Vector2(0.0, -417.75)
		sprite.scale = Vector2(0.50, 0.50)
		sprite.modulate.a = 0.0
		var material := ShaderMaterial.new()
		material.shader = CHARACTER_SHADER
		sprite.material = material
		character_root.add_child(sprite)
		pose_sprites.append(sprite)
		pose_materials.append(material)
	_set_pose(0)

	microphone = MicrophoneDrawing.new()
	microphone.position = Vector2(1110.0, 940.0)
	add_child(microphone)

	flower = FlowerDrawing.new()
	flower.position = Vector2(930.0, 954.0)
	add_child(flower)

	memory_flash = MemoryFlashDrawing.new()
	memory_flash.visible = false
	add_child(memory_flash)

	camera = Camera2D.new()
	camera.name = "Camera2D"
	camera.position = FRAME_SIZE * 0.5
	camera.enabled = true
	add_child(camera)

	_build_interface()


func _build_interface() -> void:
	var interface := CanvasLayer.new()
	interface.name = "Interface"
	add_child(interface)

	title_label = _make_label("LIVE #001 // GODOT 2D PERFORMANCE PROTOTYPE", 24, Color(0.28, 0.42, 0.55, 0.82))
	title_label.position = Vector2(64.0, 50.0)
	interface.add_child(title_label)

	cue_label = _make_label("", 21, Color(0.30, 0.48, 0.66, 0.88))
	cue_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	cue_label.position = Vector2(900.0, 50.0)
	cue_label.size = Vector2(920.0, 50.0)
	interface.add_child(cue_label)

	lyric_label = _make_label("", 34, Color(0.18, 0.30, 0.42, 1.0))
	lyric_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lyric_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lyric_label.position = Vector2(310.0, 930.0)
	lyric_label.size = Vector2(1300.0, 82.0)
	lyric_label.add_theme_color_override("font_shadow_color", Color(0.97, 0.99, 1.0, 0.96))
	lyric_label.add_theme_constant_override("shadow_offset_x", 3)
	lyric_label.add_theme_constant_override("shadow_offset_y", 3)
	interface.add_child(lyric_label)

	world_label = _make_label("WORLD 0.01%", 54, Color(0.64, 0.84, 1.0, 1.0))
	world_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	world_label.position = Vector2(660.0, 475.0)
	world_label.size = Vector2(600.0, 90.0)
	world_label.modulate.a = 0.0
	interface.add_child(world_label)

	help_label = _make_label("SPACE  一時停止   R  最初から   ESC  終了", 18, Color(0.37, 0.48, 0.58, 0.62))
	help_label.position = Vector2(64.0, 1010.0)
	interface.add_child(help_label)

	progress_bg = ColorRect.new()
	progress_bg.position = Vector2(64.0, 1050.0)
	progress_bg.size = Vector2(1792.0, 3.0)
	progress_bg.color = Color(0.35, 0.48, 0.58, 0.12)
	interface.add_child(progress_bg)

	progress_bar = ColorRect.new()
	progress_bar.position = progress_bg.position
	progress_bar.size = Vector2(0.0, 3.0)
	progress_bar.color = Color(0.42, 0.72, 0.94, 0.70)
	interface.add_child(progress_bar)


func _make_label(text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_shadow_color", Color(1, 1, 1, 0.8))
	label.add_theme_constant_override("shadow_offset_x", 1)
	label.add_theme_constant_override("shadow_offset_y", 1)
	return label


func _update_sequence(delta: float) -> void:
	var ending := smoothstep(82.3, 84.2, timeline)
	var energy := _song_energy()
	var beat_position := maxf(0.0, timeline - SONG_START) / BEAT_SECONDS
	var beat_phase := fmod(beat_position, 1.0)
	var beat_pulse := pow(1.0 - beat_phase, 5.0) if timeline >= SONG_START else 0.0
	var section := _section_name()

	var next_pose := _pose_for_timeline()
	if next_pose != current_pose:
		_set_pose(next_pose)
		pose_hit = 1.0
	pose_hit = maxf(0.0, pose_hit - delta * 6.0)

	var intro_alpha := smoothstep(0.5, 2.8, timeline)
	var character_alpha := intro_alpha * (1.0 - ending)
	for sprite in pose_sprites:
		sprite.modulate.a = character_alpha if sprite == pose_sprites[current_pose] else 0.0

	var side_amplitude: float = lerpf(7.0, 54.0, energy)
	var step_wave: float = sin(beat_position * PI * 0.5)
	var lift: float = absf(sin(beat_position * PI)) * lerpf(3.0, 18.0, energy)
	var pre_move: float = smoothstep(4.0, 7.0, timeline)
	var base_x: float = lerpf(760.0, 820.0, pre_move)
	character_root.position = Vector2(base_x + step_wave * side_amplitude, 1015.0 - lift)
	character_root.rotation = sin(beat_position * PI * 0.5) * lerp(0.002, 0.018, energy)
	var breath := sin(timeline * 2.2) * 0.006
	var hit_scale := 1.0 + pose_hit * 0.028 + beat_pulse * energy * 0.010
	character_root.scale = Vector2(hit_scale - breath * 0.2, hit_scale + breath)

	character_shadow.position.x = character_root.position.x
	character_shadow.position.y = 966.0
	character_shadow.modulate.a = character_alpha * (1.0 - lift / 65.0)
	character_shadow.scale.x = 1.0 - lift / 150.0

	for material in pose_materials:
		material.set_shader_parameter("motion_amount", 0.16 + energy * 0.84)
		material.set_shader_parameter("song_energy", energy)

	microphone.modulate.a = smoothstep(2.0, 4.0, timeline) * (1.0 - ending)
	microphone.glow = energy * (0.25 + beat_pulse * 0.55)
	microphone.queue_redraw()

	_update_camera(section, beat_position, energy, ending)

	var flash_distance := absf(timeline - 6.15)
	memory_flash.visible = flash_distance < 0.09
	memory_flash.energy = clampf(1.0 - flash_distance / 0.09, 0.0, 1.0)
	memory_flash.queue_redraw()

	stage_fx.timeline = timeline
	stage_fx.song_energy = energy
	stage_fx.beat_pulse = beat_pulse
	stage_fx.section = section
	stage_fx.ending = ending
	stage_fx.queue_redraw()

	flower.growth = smoothstep(80.1, 81.5, timeline) * (1.0 - ending)
	flower.pulse = 0.5 + 0.5 * sin(timeline * 3.0)
	flower.queue_redraw()

	lyric_label.text = _current_lyric()
	lyric_label.modulate.a = (1.0 - ending) * smoothstep(9.6, 10.2, timeline)
	cue_label.text = _cue_text(section)
	world_label.modulate.a = smoothstep(83.2, 84.7, timeline)
	progress_bar.size.x = 1792.0 * timeline / DURATION


func _song_energy() -> float:
	if timeline < 9.2 or timeline >= 79.6:
		return 0.0
	if timeline < 10.0:
		return smoothstep(9.2, 10.0, timeline) * 0.28
	if timeline < 29.0:
		return 0.38
	if timeline < 38.0:
		return lerp(0.48, 0.72, smoothstep(29.0, 38.0, timeline))
	if timeline < 56.5:
		return 0.92
	if timeline < 64.0:
		return 0.48
	if timeline < 76.4:
		return 1.0
	return lerp(0.72, 0.18, smoothstep(76.4, 79.6, timeline))


func _section_name() -> String:
	if timeline < 7.0:
		return "PROLOGUE"
	if timeline < 10.0:
		return "INTRO"
	if timeline < 29.0:
		return "VERSE"
	if timeline < 38.0:
		return "PRE-CHORUS"
	if timeline < 56.5:
		return "CHORUS"
	if timeline < 64.0:
		return "BRIDGE"
	if timeline < 76.4:
		return "FINAL REFRAIN"
	if timeline < 79.6:
		return "OUTRO"
	return "AFTERGLOW"


func _pose_for_timeline() -> int:
	if timeline < SONG_START:
		return 0
	var bar_index := int(floor((timeline - SONG_START) / BAR_SECONDS))
	if timeline < 29.0:
		return 1 if bar_index % 4 != 3 else 0
	if timeline < 38.0:
		return 3 if bar_index % 2 == 1 else 1
	if timeline < 56.5:
		return 2 if bar_index % 2 == 0 else 1
	if timeline < 64.0:
		return 3
	if timeline < 76.4:
		return 2 if bar_index % 2 == 0 else 3
	if timeline < 79.6:
		return 3
	return 0


func _set_pose(index: int) -> void:
	current_pose = clampi(index, 0, pose_sprites.size() - 1)
	for sprite_index in pose_sprites.size():
		pose_sprites[sprite_index].visible = sprite_index == current_pose


func _update_camera(section: String, beat_position: float, energy: float, ending: float) -> void:
	var zoom_target := 1.0
	var pan := Vector2.ZERO
	if section == "VERSE":
		zoom_target = lerp(1.035, 1.085, smoothstep(10.0, 29.0, timeline))
		pan = Vector2(-28.0, -4.0)
	elif section == "PRE-CHORUS":
		zoom_target = lerp(1.08, 1.13, smoothstep(29.0, 38.0, timeline))
		pan = Vector2(-34.0, -12.0)
	elif section == "CHORUS":
		zoom_target = 1.055 + 0.025 * sin(floor(beat_position / 4.0) * PI * 0.5)
		pan = Vector2(sin(beat_position * PI * 0.25) * 22.0 - 16.0, -8.0)
	elif section == "BRIDGE":
		zoom_target = lerp(1.14, 1.19, smoothstep(56.5, 64.0, timeline))
		pan = Vector2(-46.0, -18.0)
	elif section == "FINAL REFRAIN":
		zoom_target = 1.075 + absf(sin(beat_position * PI * 0.25)) * 0.035
		pan = Vector2(sin(beat_position * PI * 0.25) * 30.0 - 18.0, -10.0)
	elif section == "OUTRO":
		zoom_target = lerp(1.12, 1.04, smoothstep(76.4, 79.6, timeline))
	camera.zoom = Vector2.ONE * lerp(zoom_target, 1.0, ending)
	camera.position = FRAME_SIZE * 0.5 + pan * (1.0 - ending)
	camera.rotation = sin(beat_position * PI * 0.125) * energy * 0.0025


func _current_lyric() -> String:
	var lyric := ""
	for cue in LYRIC_CUES:
		if timeline >= float(cue[0]):
			lyric = str(cue[1])
		else:
			break
	return lyric


func _cue_text(section: String) -> String:
	if timeline < 4.0:
		return "……ここ、どこ？"
	if timeline < 6.0:
		return "一本だけのマイク"
	if timeline < 7.0:
		return ""
	if timeline < 79.6:
		return "%s  //  112 BPM" % section
	if timeline < 82.2:
		return "……届いた？　　……懐かしい。"
	return ""


func _capture_preview() -> void:
	capture_mode = false
	var image: Image = get_viewport().get_texture().get_image()
	if image == null:
		push_error("Preview capture is unavailable with the current rendering driver.")
		get_tree().quit(4)
		return
	var path := "C:/tmp/unnamed-stage-live001-v2.png"
	var error := image.save_png(path)
	if error != OK:
		push_error("Preview capture failed: %d" % error)
	else:
		print("Preview saved: %s" % path)
	get_tree().quit(error)


class StageDrawing extends Node2D:
	var timeline := 0.0
	var song_energy := 0.0
	var beat_pulse := 0.0
	var section := "PROLOGUE"
	var ending := 0.0

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, FRAME_SIZE), Color(0.965, 0.975, 0.985, 1.0))
		var visible_alpha := 1.0 - ending
		draw_line(
			Vector2(0.0, 920.0),
			Vector2(FRAME_SIZE.x, 920.0),
			Color(0.52, 0.72, 0.86, 0.10 * visible_alpha),
			2.0
		)

		var beam_alpha := song_energy * (0.018 + beat_pulse * 0.035) * visible_alpha
		if section in ["CHORUS", "FINAL REFRAIN"]:
			draw_colored_polygon(
				PackedVector2Array([Vector2(220, 0), Vector2(500, 0), Vector2(860, 920), Vector2(650, 920)]),
				Color(0.45, 0.78, 1.0, beam_alpha)
			)
			draw_colored_polygon(
				PackedVector2Array([Vector2(1420, 0), Vector2(1700, 0), Vector2(1210, 920), Vector2(1000, 920)]),
				Color(0.62, 0.84, 1.0, beam_alpha)
			)

		var center := Vector2(900.0, 930.0)
		for index in 9:
			var radius := 120.0 + index * 135.0 + fmod(timeline * (32.0 + song_energy * 28.0), 135.0)
			var alpha := song_energy * maxf(0.012, 0.075 - index * 0.007) * visible_alpha
			var width := 2.0 + beat_pulse * song_energy * 3.0
			draw_arc(center, radius, PI, TAU, 96, Color(0.40, 0.73, 0.95, alpha), width)

		for index in 36:
			var seed := float(index * 47 % 101) / 101.0
			var x := 80.0 + seed * 1760.0
			var speed := 10.0 + float(index % 5) * 3.0 + song_energy * 8.0
			var y := 100.0 + fmod(float(index * 83) + timeline * speed, 760.0)
			var pulse := 0.5 + 0.5 * sin(timeline * 2.0 + index)
			var radius := 1.5 + pulse * 2.0 + beat_pulse * song_energy * 2.2
			draw_circle(Vector2(x, y), radius, Color(0.47, 0.78, 1.0, song_energy * 0.22 * visible_alpha))

		if section in ["CHORUS", "FINAL REFRAIN"]:
			for index in 11:
				var x := 220.0 + index * 148.0
				var height := 28.0 + (0.4 + 0.6 * sin(timeline * 3.0 + index * 1.7)) * 70.0 * song_energy
				draw_rect(
					Rect2(x, 918.0 - height, 3.0, height),
					Color(0.38, 0.72, 0.96, (0.08 + beat_pulse * 0.15) * visible_alpha)
				)

		if ending > 0.0:
			draw_rect(Rect2(Vector2.ZERO, FRAME_SIZE), Color(0.025, 0.045, 0.070, ending))


class MicrophoneDrawing extends Node2D:
	var glow := 0.0

	func _draw() -> void:
		if glow > 0.01:
			draw_circle(Vector2(-39.0, -545.0), 42.0 + glow * 12.0, Color(0.42, 0.75, 1.0, glow * 0.10))
		draw_line(Vector2(0.0, -505.0), Vector2(0.0, 0.0), Color(0.29, 0.39, 0.47, 0.88), 8.0)
		draw_line(Vector2(-85.0, 0.0), Vector2(85.0, 0.0), Color(0.29, 0.39, 0.47, 0.72), 7.0)
		draw_line(Vector2(0.0, -505.0), Vector2(-30.0, -535.0), Color(0.29, 0.39, 0.47, 0.88), 8.0)
		draw_circle(Vector2(-39.0, -545.0), 23.0, Color(0.22, 0.32, 0.40, 0.98))
		draw_circle(Vector2(-39.0, -545.0), 16.0, Color(0.56, 0.66, 0.72, 0.92))
		for offset in [-8.0, 0.0, 8.0]:
			draw_line(Vector2(-52.0, -545.0 + offset), Vector2(-26.0, -545.0 + offset), Color(0.25, 0.35, 0.42, 0.6), 2.0)


class FlowerDrawing extends Node2D:
	var growth := 0.0
	var pulse := 0.0

	func _draw() -> void:
		if growth <= 0.001:
			return
		var stem_top := Vector2(0.0, lerp(0.0, -58.0, growth))
		draw_line(Vector2.ZERO, stem_top, Color(0.24, 0.55, 0.55, growth), 4.0)
		var bloom_scale := smoothstep(0.35, 1.0, growth)
		draw_circle(stem_top, 30.0 * bloom_scale, Color(0.35, 0.72, 1.0, growth * (0.05 + pulse * 0.05)))
		for index in 5:
			var angle := -PI * 0.5 + TAU * index / 5.0
			var petal_center := stem_top + Vector2(cos(angle), sin(angle)) * 13.0 * bloom_scale
			draw_circle(petal_center, 10.0 * bloom_scale, Color(0.25, 0.66, 1.0, 0.92 * growth))
		draw_circle(stem_top, 6.0 * bloom_scale, Color(0.73, 0.91, 1.0, growth))


class MemoryFlashDrawing extends Node2D:
	var energy := 0.0

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, FRAME_SIZE), Color(0.08, 0.18, 0.34, energy * 0.96))
		for index in 70:
			var x := 80.0 + float(index * 193 % 1760)
			var y := 660.0 + float(index * 79 % 260)
			var hue := float(index % 5) / 5.0
			var color := Color.from_hsv(0.52 + hue * 0.13, 0.55, 1.0, energy * 0.85)
			draw_line(Vector2(x, y), Vector2(x + sin(index) * 8.0, y - 30.0 - index % 40), color, 5.0)
		draw_rect(Rect2(420.0, 100.0, 1080.0, 420.0), Color(0.68, 0.85, 1.0, energy * 0.16))
		draw_line(Vector2(520.0, 520.0), Vector2(960.0, 160.0), Color(0.92, 0.98, 1.0, energy * 0.55), 40.0)
		draw_line(Vector2(1400.0, 520.0), Vector2(960.0, 160.0), Color(0.92, 0.98, 1.0, energy * 0.55), 40.0)


class EllipseDrawing extends Node2D:
	var ellipse_size := Vector2(100.0, 20.0)
	var color := Color(0, 0, 0, 0.1)

	func _draw() -> void:
		var points := PackedVector2Array()
		for index in 64:
			var angle := TAU * index / 64.0
			points.append(Vector2(cos(angle) * ellipse_size.x, sin(angle) * ellipse_size.y))
		draw_colored_polygon(points, color)
