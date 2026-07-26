shader_type canvas_item;

uniform float motion_amount : hint_range(0.0, 1.0) = 0.25;
uniform float song_energy : hint_range(0.0, 1.0) = 0.0;
uniform vec4 glow_tint : source_color = vec4(0.55, 0.82, 1.0, 1.0);

void vertex() {
	float vertical = smoothstep(0.0, 1.0, UV.y);
	float sway = sin(TIME * 1.35 + UV.y * 4.0) * motion_amount;
	VERTEX.x += sway * mix(1.8, 5.5, vertical);
}

void fragment() {
	vec4 base = texture(TEXTURE, UV);
	float soft_glow = song_energy * 0.08 * (1.0 - base.a);
	COLOR = vec4(base.rgb + glow_tint.rgb * soft_glow, base.a) * COLOR;
}

