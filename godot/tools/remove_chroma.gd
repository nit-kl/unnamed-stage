extends SceneTree


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		push_error("Usage: --script godot/tools/remove_chroma.gd -- <input> <output>")
		quit(2)
		return

	var image := Image.load_from_file(args[0])
	if image.is_empty():
		push_error("Could not load input image: %s" % args[0])
		quit(3)
		return

	image.convert(Image.FORMAT_RGBA8)
	for y in image.get_height():
		for x in image.get_width():
			var color := image.get_pixel(x, y)
			var chroma: float = color.g - maxf(color.r, color.b)
			var alpha: float = 1.0 - smoothstep(0.0, 0.30, chroma)
			if alpha < 0.995:
				color.g = minf(color.g, (color.r + color.b) * 0.5)
			color.a *= alpha
			image.set_pixel(x, y, color)

	var error := image.save_png(args[1])
	if error != OK:
		push_error("Could not save output image: %s (error %d)" % [args[1], error])
		quit(error)
		return

	print("Saved transparent sprite: %s" % args[1])
	quit()
