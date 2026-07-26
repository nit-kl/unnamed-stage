"""
Build body_blockout_rebuild_v1.blend for Uta Shiranagi.

Creates orthographic reference planes from turnaround.png and a mirrored
Voxel blockout body at 157cm / ~7.3 heads. Run with:

  blender --background --python scripts/blender/build_body_blockout_rebuild_v1.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
CHAR_DIR = ROOT / "blender" / "characters" / "uta_shiranagi"
REVIEW_DIR = CHAR_DIR / "reviews"
REF_TURNAROUND = ROOT / "references" / "uta-shiranagi" / "turnaround.png"
BLEND_PATH = CHAR_DIR / "body_blockout_rebuild_v1.blend"

HEIGHT = 1.57
HEADS = 7.3
HEAD = HEIGHT / HEADS
CROTCH_Z = 4.2 * HEAD  # modeling-details: crotch-to-sole ~4.2 heads
SHOULDER_HALF = (2.1 * HEAD) * 0.5
ARM_LEN = 2.7 * HEAD
CHIN_Z = HEIGHT - HEAD
SHOULDER_Z = CHIN_Z - 0.22 * HEAD
HIP_Z = CROTCH_Z + 0.15 * HEAD
WAIST_Z = (SHOULDER_Z + HIP_Z) * 0.52
KNEE_Z = CROTCH_Z * 0.52
ANKLE_Z = 0.07


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.cameras,
        bpy.data.collections,
        bpy.data.lights,
    ):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def setup_units() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    # Blender 5.x uses EEVEE Next
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1536
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("World_White") if not bpy.data.worlds else bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World_White")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.92, 0.92, 0.94, 1.0)
        bg.inputs[1].default_value = 1.0


def ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def link_only(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def new_mat(name: str, color: tuple[float, float, float, float], alpha: float = 1.0) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.55
    if alpha < 1.0:
        mat.blend_method = "BLEND"
        if hasattr(mat, "shadow_method"):
            mat.shadow_method = "NONE"
    return mat


def add_empty(name: str, location: Vector, collection: bpy.types.Collection) -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.03
    empty.location = location
    link_only(empty, collection)
    return empty


def add_cube(
    name: str,
    location: Vector,
    scale: Vector,
    collection: bpy.types.Collection,
    mat: bpy.types.Material | None = None,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    link_only(obj, collection)
    bm_verts = [
        (-1, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, 1, 1),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh.from_pydata(bm_verts, [], faces)
    mesh.update()
    obj.location = location
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    return obj


def add_uv_sphere(
    name: str,
    location: Vector,
    scale: Vector,
    collection: bpy.types.Collection,
    mat: bpy.types.Material | None = None,
    segments: int = 16,
    rings: int = 10,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        radius=1.0,
        location=location,
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name
    obj.scale = scale
    link_only(obj, collection)
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


def crop_turnaround_panels() -> dict[str, Path]:
    """Split turnaround into front / right / back image crops (pixel space)."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    src = bpy.data.images.load(str(REF_TURNAROUND))
    w, h = src.size
    # Equal 4-panel layout: front, right, back, left
    panel_w = w // 4
    # Blender image pixels: bottom-left origin, RGBA float
    pixels = list(src.pixels)
    panels = {
        "front": 0,
        "right": 1,
        "back": 2,
    }
    out: dict[str, Path] = {}
    for name, idx in panels.items():
        x0 = idx * panel_w
        x1 = (idx + 1) * panel_w if idx < 3 else w
        pw = x1 - x0
        # Trim a little footer/header whitespace by keeping full height;
        # character is centered in each panel on this sheet.
        cropped = bpy.data.images.new(f"crop_{name}", width=pw, height=h, alpha=True)
        new_pixels = [1.0] * (pw * h * 4)
        for y in range(h):
            for x in range(pw):
                sx = x0 + x
                si = (y * w + sx) * 4
                di = (y * pw + x) * 4
                new_pixels[di : di + 4] = pixels[si : si + 4]
        cropped.pixels = new_pixels
        path = REVIEW_DIR / f"ref_panel_{name}.png"
        cropped.filepath_raw = str(path)
        cropped.file_format = "PNG"
        cropped.save()
        out[name] = path
    return out


def make_ref_plane(
    name: str,
    image_path: Path,
    location: Vector,
    rotation_euler: tuple[float, float, float],
    width: float,
    height: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    img = bpy.data.images.load(str(image_path), check_existing=True)
    mat = new_mat(f"MAT_{name}", (1, 1, 1, 1), alpha=0.55)
    mat.blend_method = "BLEND"
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    tex = nodes.new("ShaderNodeTexImage")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    tex.image = img
    links.new(tex.outputs["Color"], emit.inputs["Color"])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    # Use luminance-ish: keep drawn lines, soft white bg
    links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    # Fallback if alpha is opaque: mix by inverted brightness via math
    # Simpler approach: emission only with alpha from texture
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    emit = nodes.new("ShaderNodeEmission")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    invert = nodes.new("ShaderNodeInvert")
    rgb2bw = nodes.new("ShaderNodeRGBToBW")
    tex.image = img
    links.new(tex.outputs["Color"], emit.inputs["Color"])
    links.new(tex.outputs["Color"], rgb2bw.inputs["Color"])
    links.new(rgb2bw.outputs["Val"], invert.inputs["Color"])
    # Fac: show image where not white
    links.new(invert.outputs["Color"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    emit.inputs["Strength"].default_value = 0.85

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rotation_euler
    obj.scale = (width * 0.5, height * 0.5, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Plane default faces +Z; we rotate into place. Recenter so feet at Z=0:
    # After scale apply, local verts span ~[-w/2,w/2] x [-h/2,h/2].
    # Shift object so bottom edge sits on Z=0 in world after rotation.
    link_only(obj, collection)
    obj.data.materials.append(mat)
    obj.hide_render = False
    obj.show_in_front = True
    return obj


def place_reference_planes(panel_paths: dict[str, Path]) -> None:
    col = ensure_collection("REFERENCES")
    # Character figure height in each cropped panel ≈ content height.
    # Use image aspect: panel is (w/4) x h of source.
    src = bpy.data.images.load(str(REF_TURNAROUND), check_existing=True)
    panel_aspect = (src.size[0] / 4) / src.size[1]
    # Fit character height to 1.57m. Sheet has labels/margins; use scale factor.
    fig_height = HEIGHT * 1.12  # include ahoge / headroom from sheet
    fig_width = fig_height * panel_aspect

    # Front: plane on Y-, looking toward +Y (camera at +Y looking -Y... wait)
    # Blender front view looks down -Y. Character faces -Y or +Y?
    # Convention here: character faces -Y (toward front camera at -Y looking +Y).
    # Actually standard: character faces +Y or -Y. Doc cameras:
    # cam_front_ref compares to front. Place ref behind character on +Y or -Y.
    front = make_ref_plane(
        "ref_front",
        panel_paths["front"],
        location=Vector((0.0, 0.55, fig_height * 0.5)),
        rotation_euler=(math.pi / 2, 0.0, 0.0),
        width=fig_width,
        height=fig_height,
        collection=col,
    )
    # Right view: character right is +X; camera at +X looking -X.
    # Reference plane on +X, rotated to face -X.
    right = make_ref_plane(
        "ref_right",
        panel_paths["right"],
        location=Vector((0.55, 0.0, fig_height * 0.5)),
        rotation_euler=(math.pi / 2, 0.0, math.pi / 2),
        width=fig_width,
        height=fig_height,
        collection=col,
    )
    back = make_ref_plane(
        "ref_back",
        panel_paths["back"],
        location=Vector((0.0, -0.55, fig_height * 0.5)),
        rotation_euler=(math.pi / 2, 0.0, math.pi),
        width=fig_width,
        height=fig_height,
        collection=col,
    )
    for obj in (front, right, back):
        obj.display_type = "TEXTURED"


def add_cameras() -> None:
    col = ensure_collection("CAMERAS")
    dist = 3.2
    specs = [
        ("cam_front_ref", Vector((0.0, -dist, HEIGHT * 0.5)), (math.pi / 2, 0.0, 0.0)),
        ("cam_right_ref", Vector((dist, 0.0, HEIGHT * 0.5)), (math.pi / 2, 0.0, math.pi / 2)),
        ("cam_back_ref", Vector((0.0, dist, HEIGHT * 0.5)), (math.pi / 2, 0.0, math.pi)),
    ]
    for name, loc, rot in specs:
        cam_data = bpy.data.cameras.new(name)
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = HEIGHT * 1.25
        cam = bpy.data.objects.new(name, cam_data)
        cam.location = loc
        cam.rotation_euler = rot
        link_only(cam, col)


def add_proportion_guides() -> None:
    col = ensure_collection("PROPORTION_GUIDES")
    marks = {
        "guide_floor": 0.0,
        "guide_ankle": ANKLE_Z,
        "guide_knee": KNEE_Z,
        "guide_crotch": CROTCH_Z,
        "guide_hip": HIP_Z,
        "guide_waist": WAIST_Z,
        "guide_shoulder": SHOULDER_Z,
        "guide_chin": CHIN_Z,
        "guide_head_top": HEIGHT,
    }
    for name, z in marks.items():
        add_empty(name, Vector((0.0, 0.0, z)), col)
    # Head-unit rulers on +X
    for i in range(int(HEADS) + 1):
        add_empty(f"guide_headunit_{i}", Vector((0.35, 0.0, i * HEAD)), col)


def build_body_parts() -> list[bpy.types.Object]:
    col = ensure_collection("BODY_BLOCKS")
    mat = new_mat("MAT_BodyBlock", (0.82, 0.78, 0.76, 1.0))
    parts: list[bpy.types.Object] = []

    def cube(name, loc, scale):
        obj = add_cube(name, loc, scale, col, mat)
        parts.append(obj)
        return obj

    def sphere(name, loc, scale):
        obj = add_uv_sphere(name, loc, scale, col, mat)
        parts.append(obj)
        return obj

    # Right-half head / neck (Mirror completes left). Keep a thin clip at X=0.
    head = sphere(
        "blk_head_R",
        Vector((HEAD * 0.18, 0, CHIN_Z + HEAD * 0.48)),
        Vector((HEAD * 0.28, HEAD * 0.40, HEAD * 0.50)),
    )
    cube(
        "blk_jaw_R",
        Vector((HEAD * 0.12, -HEAD * 0.05, CHIN_Z + HEAD * 0.18)),
        Vector((HEAD * 0.20, HEAD * 0.22, HEAD * 0.16)),
    )
    cube(
        "blk_nose",
        Vector((0.0, -HEAD * 0.38, CHIN_Z + HEAD * 0.42)),
        Vector((HEAD * 0.04, HEAD * 0.08, HEAD * 0.07)),
    )
    cube(
        "blk_neck_R",
        Vector((HEAD * 0.07, 0.01, (CHIN_Z + SHOULDER_Z) * 0.5)),
        Vector((HEAD * 0.12, HEAD * 0.17, (CHIN_Z - SHOULDER_Z) * 0.45)),
    )

    # Right-half torso blocks (x >= 0). Mirror completes left.
    chest_depth = HEAD * 0.34
    waist_depth = HEAD * 0.30
    hip_depth = HEAD * 0.33
    cube(
        "blk_chest_R",
        Vector((SHOULDER_HALF * 0.35, 0.0, (SHOULDER_Z + WAIST_Z) * 0.55)),
        Vector((SHOULDER_HALF * 0.55, chest_depth, (SHOULDER_Z - WAIST_Z) * 0.42)),
    )
    cube(
        "blk_bust_R",
        Vector((SHOULDER_HALF * 0.28, -chest_depth * 0.55, SHOULDER_Z - 0.35 * HEAD)),
        Vector((HEAD * 0.14, HEAD * 0.10, HEAD * 0.12)),
    )
    cube(
        "blk_waist_R",
        Vector((SHOULDER_HALF * 0.28, 0.0, WAIST_Z)),
        Vector((SHOULDER_HALF * 0.38, waist_depth, HEAD * 0.18)),
    )
    cube(
        "blk_pelvis_R",
        Vector((SHOULDER_HALF * 0.30, 0.0, HIP_Z)),
        Vector((SHOULDER_HALF * 0.45, hip_depth, HEAD * 0.22)),
    )
    # Deltoid / shoulder softener
    sphere(
        "blk_deltoid_R",
        Vector((SHOULDER_HALF * 0.95, 0.0, SHOULDER_Z - 0.05 * HEAD)),
        Vector((HEAD * 0.16, HEAD * 0.14, HEAD * 0.15)),
    )
    sphere(
        "blk_hip_soft_R",
        Vector((SHOULDER_HALF * 0.55, 0.0, CROTCH_Z + 0.05 * HEAD)),
        Vector((HEAD * 0.16, HEAD * 0.14, HEAD * 0.14)),
    )

    # A-pose arm: ~30 deg from downward axis, in XZ / XY
    a_angle = math.radians(28)
    shoulder = Vector((SHOULDER_HALF * 1.02, 0.0, SHOULDER_Z - 0.08 * HEAD))
    upper_len = ARM_LEN * 0.42
    fore_len = ARM_LEN * 0.38
    hand_len = ARM_LEN * 0.20

    def arm_dir():
        # Down and out
        return Vector((math.sin(a_angle), 0.02, -math.cos(a_angle))).normalized()

    d = arm_dir()
    upper_c = shoulder + d * (upper_len * 0.5)
    elbow = shoulder + d * upper_len
    # Forearm slightly more inward toward thigh
    d2 = Vector((math.sin(a_angle * 0.85), 0.04, -math.cos(a_angle * 0.85))).normalized()
    fore_c = elbow + d2 * (fore_len * 0.5)
    wrist = elbow + d2 * fore_len

    upper = cube("blk_upperarm_R", upper_c, Vector((HEAD * 0.11, HEAD * 0.10, upper_len * 0.5)))
    upper.rotation_euler = (0.0, a_angle, 0.0)
    fore = cube("blk_forearm_R", fore_c, Vector((HEAD * 0.09, HEAD * 0.085, fore_len * 0.5)))
    fore.rotation_euler = (0.0, a_angle * 0.85, 0.0)
    hand = cube("blk_hand_R", wrist + d2 * (hand_len * 0.35), Vector((HEAD * 0.08, HEAD * 0.035, hand_len * 0.35)))
    hand.rotation_euler = (0.1, a_angle * 0.85, 0.2)
    # Simple separated fingertips (front readability)
    tip_base = wrist + d2 * (hand_len * 0.75)
    for i, side in enumerate((-0.03, -0.01, 0.01, 0.03)):
        tip = cube(
            f"blk_finger_R_{i}",
            tip_base + Vector((side, -0.01, -0.01)),
            Vector((HEAD * 0.018, HEAD * 0.016, HEAD * 0.05)),
        )
        tip.rotation_euler = (0.15, a_angle * 0.85, 0.0)
    thumb = cube(
        "blk_thumb_R",
        wrist + Vector((-0.01, -0.03, 0.0)) + d2 * 0.03,
        Vector((HEAD * 0.02, HEAD * 0.035, HEAD * 0.04)),
    )
    thumb.rotation_euler = (0.6, 0.2, 0.5)

    # Legs
    thigh_len = (CROTCH_Z - KNEE_Z) * 0.95
    shin_len = (KNEE_Z - ANKLE_Z) * 0.95
    hip_joint = Vector((SHOULDER_HALF * 0.42, 0.0, CROTCH_Z - 0.02))
    thigh_c = Vector((hip_joint.x, 0.02, CROTCH_Z - thigh_len * 0.5))
    knee = Vector((hip_joint.x * 0.95, 0.03, KNEE_Z))
    shin_c = Vector((knee.x, 0.02, KNEE_Z - shin_len * 0.5))
    cube("blk_thigh_R", thigh_c, Vector((HEAD * 0.15, HEAD * 0.16, thigh_len * 0.5)))
    sphere("blk_knee_R", knee, Vector((HEAD * 0.11, HEAD * 0.12, HEAD * 0.10)))
    cube("blk_shin_R", shin_c, Vector((HEAD * 0.11, HEAD * 0.125, shin_len * 0.5)))
    # Foot connected to ankle, short toe (side silhouette)
    ankle = Vector((knee.x, 0.0, ANKLE_Z))
    sphere("blk_ankle_R", ankle, Vector((HEAD * 0.08, HEAD * 0.09, HEAD * 0.07)))
    cube(
        "blk_foot_R",
        Vector((ankle.x, -HEAD * 0.08, ANKLE_Z * 0.45)),
        Vector((HEAD * 0.09, HEAD * 0.16, ANKLE_Z * 0.45)),
    )
    cube(
        "blk_toe_R",
        Vector((ankle.x, -HEAD * 0.22, 0.02)),
        Vector((HEAD * 0.08, HEAD * 0.08, 0.02)),
    )

    cube(
        "blk_spine_R",
        Vector((HEAD * 0.06, 0.0, (SHOULDER_Z + HIP_Z) * 0.5)),
        Vector((HEAD * 0.10, HEAD * 0.28, (SHOULDER_Z - HIP_Z) * 0.48)),
    )
    return parts


def join_body(parts: list[bpy.types.Object]) -> bpy.types.Object:
    col = ensure_collection("BODY")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = "body_base"
    body.data.name = "body_base"
    # Apply rotation/scale on blocks before join already partially done; ensure clean.
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    body.location = (0.0, 0.0, 0.0)
    body.rotation_euler = (0.0, 0.0, 0.0)
    body.scale = (1.0, 1.0, 1.0)

    # Origin to feet center on floor
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    # Move so min Z = 0 and X/Y centered
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = body.evaluated_get(depsgraph)
    coords = [body.matrix_world @ Vector(v.co) for v in eval_obj.data.vertices]
    min_z = min(c.z for c in coords)
    center_x = 0.5 * (min(c.x for c in coords) + max(c.x for c in coords))
    center_y = 0.5 * (min(c.y for c in coords) + max(c.y for c in coords))
    body.location -= Vector((center_x, center_y, min_z))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Modifiers: Mirror then Voxel then Subdivision (non-destructive)
    mirror = body.modifiers.new("Mirror_Symmetry", "MIRROR")
    mirror.use_axis[0] = True
    mirror.use_clip = True
    mirror.merge_threshold = 0.001

    voxel = body.modifiers.new("Voxel_Unify", "REMESH")
    voxel.mode = "VOXEL"
    voxel.voxel_size = 0.012
    voxel.adaptivity = 0.0

    sub = body.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1

    link_only(body, col)
    # Hide raw block collection clutter
    blocks = bpy.data.collections.get("BODY_BLOCKS")
    if blocks:
        blocks.hide_viewport = True
        blocks.hide_render = True
    return body


def verify(body: bpy.types.Object) -> dict:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = body.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    coords = [eval_obj.matrix_world @ Vector(v.co) for v in mesh.vertices]
    min_x = min(c.x for c in coords)
    max_x = max(c.x for c in coords)
    min_z = min(c.z for c in coords)
    max_z = max(c.z for c in coords)
    # Mesh island / non-manifold via bmesh on evaluated
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(mesh)
    islands = len(bm.edges)  # placeholder
    bm.verts.ensure_lookup_table()
    # Connected islands
    visited = set()
    island_count = 0
    from collections import deque

    vert_link = {v.index: [e.other_vert(v).index for e in v.link_edges] for v in bm.verts}
    for v in bm.verts:
        if v.index in visited:
            continue
        island_count += 1
        q = deque([v.index])
        visited.add(v.index)
        while q:
            i = q.popleft()
            for j in vert_link[i]:
                if j not in visited:
                    visited.add(j)
                    q.append(j)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    result = {
        "height": max_z - min_z,
        "min_z": min_z,
        "min_x": min_x,
        "max_x": max_x,
        "verts": len(mesh.vertices),
        "faces": len(mesh.polygons),
        "islands": island_count,
        "non_manifold_edges": non_manifold,
        "location": tuple(body.location),
        "scale": tuple(body.scale),
    }
    bm.free()
    eval_obj.to_mesh_clear()
    print("VERIFY", result)
    return result


def render_reviews() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    # Soft key light
    light_data = bpy.data.lights.new(name="Key", type="AREA")
    light_data.energy = 40
    light_data.size = 3.0
    light = bpy.data.objects.new("light_key", light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = (1.5, -1.2, 2.2)

    for cam_name, filename in (
        ("cam_front_ref", "rebuild_v1_front.png"),
        ("cam_right_ref", "rebuild_v1_right.png"),
        ("cam_back_ref", "rebuild_v1_back.png"),
    ):
        cam = bpy.data.objects.get(cam_name)
        if not cam:
            continue
        scene.camera = cam
        scene.render.filepath = str(REVIEW_DIR / filename)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)


def main() -> None:
    CHAR_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    setup_units()
    panel_paths = crop_turnaround_panels()
    place_reference_planes(panel_paths)
    add_cameras()
    add_proportion_guides()
    parts = build_body_parts()
    body = join_body(parts)
    result = verify(body)
    # Nudge height to 1.57 if small error after voxel
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = body.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    coords = [eval_obj.matrix_world @ Vector(v.co) for v in mesh.vertices]
    min_z = min(c.z for c in coords)
    max_z = max(c.z for c in coords)
    h = max_z - min_z
    eval_obj.to_mesh_clear()
    if h > 1e-6:
        body.scale = (1.0, 1.0, HEIGHT / h)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        # re-floor
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = body.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        coords = [eval_obj.matrix_world @ Vector(v.co) for v in mesh.vertices]
        min_z = min(c.z for c in coords)
        eval_obj.to_mesh_clear()
        body.location.z -= min_z
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    result = verify(body)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print("SAVED", BLEND_PATH)
    render_reviews()
    meta = REVIEW_DIR / "rebuild_v1_verify.txt"
    meta.write_text("\n".join(f"{k}={v}" for k, v in result.items()) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
