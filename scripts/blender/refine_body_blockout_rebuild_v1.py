"""
Body Rebuild v1: fused metaball blockout + crotch cut for distinct legs.
"""

from __future__ import annotations

import math
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
CHAR_DIR = ROOT / "blender" / "characters" / "uta_shiranagi"
REVIEW_DIR = CHAR_DIR / "reviews"
REF_TURNAROUND = ROOT / "references" / "uta-shiranagi" / "turnaround.png"
BLEND_PATH = CHAR_DIR / "body_blockout_rebuild_v1.blend"

HEIGHT = 1.57
HEAD = HEIGHT / 7.3
CROTCH_Z = 4.15 * HEAD
SHOULDER_HALF = 0.95 * HEAD
ARM_LEN = 2.5 * HEAD
CHIN_Z = HEIGHT - HEAD
SHOULDER_Z = CHIN_Z - 0.20 * HEAD
HIP_Z = CROTCH_Z + 0.06 * HEAD
WAIST_Z = SHOULDER_Z * 0.50 + HIP_Z * 0.50
ANKLE_Z = 0.05
# Post-fusion slim (keeps 1 island; thins metaball bulk toward turnaround)
SLIM_X = 0.58
SLIM_Y = 0.70


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.metaballs,
        bpy.data.images,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.collections,
    ):
        for item in list(coll):
            if getattr(item, "users", 1) == 0:
                coll.remove(item)


def setup_scene() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1152
    scene.render.image_settings.file_format = "PNG"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.70, 0.72, 0.76, 1.0)
        bg.inputs[1].default_value = 0.55


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


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def mat_body() -> bpy.types.Material:
    mat = bpy.data.materials.new("MAT_BodyBlock")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.60, 0.47, 0.43, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.42
    return mat


def mat_ref(img: bpy.types.Image) -> bpy.types.Material:
    mat = bpy.data.materials.new(f"MAT_REF_{img.name}")
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    rgb2bw = nodes.new("ShaderNodeRGBToBW")
    map_range = nodes.new("ShaderNodeMapRange")
    map_range.inputs["From Min"].default_value = 0.48
    map_range.inputs["From Max"].default_value = 0.95
    map_range.inputs["To Min"].default_value = 1.0
    map_range.inputs["To Max"].default_value = 0.0
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.05, 0.15, 0.40, 1.0)
    emission.inputs["Strength"].default_value = 5.0
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(tex.outputs["Color"], rgb2bw.inputs["Color"])
    links.new(rgb2bw.outputs["Val"], map_range.inputs["Value"])
    links.new(map_range.outputs["Result"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def count_islands(mesh) -> tuple[int, int]:
    bm = bmesh.new()
    bm.from_mesh(mesh)
    visited = set()
    islands = 0
    link = {v.index: [e.other_vert(v).index for e in v.link_edges] for v in bm.verts}
    for v in bm.verts:
        if v.index in visited:
            continue
        islands += 1
        q = deque([v.index])
        visited.add(v.index)
        while q:
            i = q.popleft()
            for j in link[i]:
                if j not in visited:
                    visited.add(j)
                    q.append(j)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    return islands, non_manifold


def detect_panels(img: bpy.types.Image):
    w, h = img.size
    pix = img.pixels[:]
    hist = [0.0] * w
    for x in range(w):
        s = 0.0
        for y in range(0, h, 2):
            i = (y * w + x) * 4
            s += max(0.0, 0.85 - (pix[i] + pix[i + 1] + pix[i + 2]) / 3.0)
        hist[x] = s
    sm = [0.0] * w
    k = 20
    for i in range(w):
        a, b = max(0, i - k), min(w, i + k + 1)
        sm[i] = sum(hist[a:b]) / (b - a)
    maxima = []
    for i in range(30, w - 30):
        if sm[i] == max(sm[i - 30 : i + 31]) and sm[i] > 1.0:
            if not maxima or i - maxima[-1] > 120:
                maxima.append(i)
    centers = sorted(sorted(maxima, key=lambda i: sm[i], reverse=True)[:4])
    if len(centers) < 4:
        centers = [w // 8, 3 * w // 8, 5 * w // 8, 7 * w // 8]
    bounds = []
    for idx, c in enumerate(centers[:3]):
        x0 = int((centers[idx - 1] + c) * 0.5) if idx else max(0, int(c - (centers[1] - c) * 0.55))
        x1 = int((c + centers[idx + 1]) * 0.5)
        y_dark = []
        for y in range(h):
            row = 0.0
            for x in range(x0, x1, 2):
                i = (y * w + x) * 4
                row += max(0.0, 0.85 - (pix[i] + pix[i + 1] + pix[i + 2]) / 3.0)
            if row > 0.8:
                y_dark.append(y)
        y0, y1 = (min(y_dark), max(y_dark)) if y_dark else (int(h * 0.08), int(h * 0.95))
        pad = int((y1 - y0) * 0.02)
        b = (x0, max(0, y0 - pad), x1, min(h - 1, y1 + pad))
        print(f"PANEL {idx} center={c} bounds={b}")
        bounds.append(b)
    return bounds


def save_crop(img, bounds, path: Path):
    x0, y0, x1, y1 = bounds
    pw, ph = x1 - x0, y1 - y0
    w = img.size[0]
    pix = img.pixels[:]
    cropped = bpy.data.images.new(path.stem, width=pw, height=ph, alpha=True)
    out = [1.0] * (pw * ph * 4)
    for y in range(ph):
        for x in range(pw):
            si = ((y0 + y) * w + (x0 + x)) * 4
            di = (y * pw + x) * 4
            out[di : di + 4] = pix[si : si + 4]
    cropped.pixels = out
    cropped.filepath_raw = str(path)
    cropped.file_format = "PNG"
    cropped.save()
    return cropped


def character_v_bounds(img: bpy.types.Image) -> tuple[float, float]:
    """Return normalized (v_feet, v_crown) in image UV space (0=bottom, 1=top)."""
    w, h = img.size
    pix = img.pixels[:]
    rows = []
    for y in range(h):
        ink = 0.0
        for x in range(0, w, 2):
            i = (y * w + x) * 4
            ink += max(0.0, 0.82 - (pix[i] + pix[i + 1] + pix[i + 2]) / 3.0)
        rows.append(ink)
    thr = max(rows) * 0.08
    ys = [y for y, v in enumerate(rows) if v > thr]
    if not ys:
        return 0.02, 0.98
    y0, y1 = min(ys), max(ys)
    # Trim ahoge/label slack: keep most of figure, bias crown down slightly
    span = y1 - y0
    y1 = int(y0 + span * 0.97)
    return y0 / h, y1 / h


def add_refs(crops):
    col = ensure_collection("REFERENCES")
    for name in ("front", "right", "back"):
        img = crops[name]
        v0, v1 = character_v_bounds(img)
        # Map character feet..crown to world Z=0..HEIGHT
        content_frac = max(0.35, v1 - v0)
        fig_h = HEIGHT / content_frac
        aspect = img.size[0] / max(1, img.size[1])
        fig_w = fig_h * aspect
        bpy.ops.mesh.primitive_plane_add(size=1.0)
        obj = bpy.context.active_object
        obj.name = f"ref_{name}"
        obj.scale = (fig_w / 2, fig_h / 2, 1)
        bpy.ops.object.transform_apply(scale=True)
        for v in obj.data.vertices:
            v.co.x *= -1
        # Plane center so UV v0 sits on Z=0
        z_center = fig_h * (0.5 - v0)
        if name == "front":
            obj.rotation_euler = (math.pi / 2, 0, 0)
            obj.location = (0, 0.45, z_center)
        elif name == "right":
            obj.rotation_euler = (math.pi / 2, 0, math.pi / 2)
            obj.location = (0.45, 0, z_center)
        else:
            obj.rotation_euler = (math.pi / 2, 0, math.pi)
            obj.location = (0, -0.45, z_center)
        obj.data.materials.append(mat_ref(img))
        obj.show_in_front = True
        link_only(obj, col)
        print(f"REF {name}: v_feet={v0:.3f} v_crown={v1:.3f} fig_h={fig_h:.3f}")


def add_cameras():
    col = ensure_collection("CAMERAS")
    target = Vector((0, 0, HEIGHT * 0.5))
    for name, loc in {
        "cam_front_ref": Vector((0, -2.5, HEIGHT * 0.5)),
        "cam_right_ref": Vector((2.5, 0, HEIGHT * 0.5)),
        "cam_back_ref": Vector((0, 2.5, HEIGHT * 0.5)),
    }.items():
        data = bpy.data.cameras.new(name)
        data.type = "ORTHO"
        data.ortho_scale = HEIGHT * 1.12
        cam = bpy.data.objects.new(name, data)
        cam.location = loc
        look_at(cam, target)
        link_only(cam, col)


def add_guides():
    col = ensure_collection("PROPORTION_GUIDES")
    for name, z in {
        "guide_floor": 0.0,
        "guide_ankle": ANKLE_Z,
        "guide_knee": CROTCH_Z * 0.54,
        "guide_crotch": CROTCH_Z,
        "guide_hip": HIP_Z,
        "guide_waist": WAIST_Z,
        "guide_shoulder": SHOULDER_Z,
        "guide_chin": CHIN_Z,
        "guide_head_top": HEIGHT,
    }.items():
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "PLAIN_AXES"
        e.empty_display_size = 0.03
        e.location = (0, 0, z)
        link_only(e, col)


def ball(mb, loc: Vector, radius: float):
    e = mb.elements.new(type="BALL")
    e.co = loc
    e.radius = radius
    e.stiffness = 2.0


def build_body():
    """Known-good fused metaball at 8x, shrink, cut crotch slot, polish."""
    S = 8.0
    mb = bpy.data.metaballs.new("body_meta")
    mb.resolution = 0.12
    mb.render_resolution = 0.10
    mb.threshold = 0.2
    obj = bpy.data.objects.new("body_meta_obj", mb)
    bpy.context.scene.collection.objects.link(obj)

    def H(v):
        return v * S

    h = H(HEAD)
    chin = H(CHIN_Z)
    shoulder_z = H(SHOULDER_Z)
    waist_z = H(WAIST_Z)
    hip_z = H(HIP_Z)
    crotch_z = H(CROTCH_Z)
    ankle_z = H(ANKLE_Z)
    sh = H(SHOULDER_HALF)
    arm_len = H(ARM_LEN)

    # Fuse first with reliable radii, then slim with SLIM_X/SLIM_Y
    ball(mb, Vector((0, -0.02 * S, chin + h * 0.50)), h * 0.70)
    ball(mb, Vector((0, 0.0, (chin + shoulder_z) * 0.5)), h * 0.45)
    ball(mb, Vector((0, 0.0, (shoulder_z + waist_z) * 0.5)), h * 0.85)
    ball(mb, Vector((0, -0.08 * S, shoulder_z - 0.25 * h)), h * 0.40)
    ball(mb, Vector((0, 0.0, waist_z)), h * 0.65)
    ball(mb, Vector((0, 0.0, hip_z)), h * 0.70)
    ball(mb, Vector((0, 0.0, crotch_z + 0.05 * S)), h * 0.55)

    a = math.radians(26)
    for side in (-1.0, 1.0):
        ball(mb, Vector((side * sh * 0.45, 0.0, shoulder_z)), h * 0.55)
        ball(mb, Vector((side * sh * 0.90, 0.0, shoulder_z - 0.02 * h)), h * 0.50)
        d = Vector((side * math.sin(a), 0.02 * S, -math.cos(a))).normalized()
        shoulder = Vector((side * sh * 0.95, 0.0, shoulder_z - 0.04 * h))
        for i in range(6):
            p = shoulder + d * (arm_len * 0.92 * i / 5)
            ball(mb, p, h * 0.42 if i < 4 else h * 0.34)
        hip = Vector((side * sh * 0.28, 0.015 * S, crotch_z - 0.01 * S))
        ankle = Vector((side * sh * 0.26, 0.0, ankle_z))
        for i in range(7):
            p = hip.lerp(ankle, i / 6)
            ball(mb, p, h * 0.48 if i < 4 else h * 0.40)
        ball(mb, Vector((ankle.x, -0.08 * S, ankle_z * 0.45)), h * 0.32)
        ball(mb, Vector((ankle.x, -0.14 * S, 0.02 * S)), h * 0.22)

    print("META_ELEMENTS", len(mb.elements))
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.view_layer.update()
    bpy.ops.object.convert(target="MESH")
    body = bpy.context.active_object
    body.name = "body_base"
    body.data.name = "body_base"
    body.data.materials.clear()
    body.data.materials.append(mat_body())

    islands_8x, _ = count_islands(body.data)
    print("ISLANDS_AFTER_CONVERT_8X", islands_8x, "verts", len(body.data.vertices))
    if islands_8x != 1:
        voxel = body.modifiers.new("Voxel_Unify_8x", "REMESH")
        voxel.mode = "VOXEL"
        voxel.voxel_size = 0.10
        bpy.ops.object.modifier_apply(modifier="Voxel_Unify_8x")
        islands_8x, _ = count_islands(body.data)
        print("ISLANDS_AFTER_VOXEL_8X", islands_8x)
    if islands_8x != 1:
        raise RuntimeError(f"Expected fused metaball, got {islands_8x} islands")

    # Slim toward turnaround proportions (width/depth only; keep height)
    for v in body.data.vertices:
        v.co.x *= SLIM_X
        v.co.y *= SLIM_Y
    body.data.update()

    # Shrink to meters
    body.scale = (1 / S, 1 / S, 1 / S)
    bpy.ops.object.transform_apply(scale=True)
    body_col = ensure_collection("BODY")
    link_only(body, body_col)

    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    coords = [Vector(v.co) for v in body.data.vertices]
    min_z = min(c.z for c in coords)
    cx = 0.5 * (min(c.x for c in coords) + max(c.x for c in coords))
    cy = 0.5 * (min(c.y for c in coords) + max(c.y for c in coords))
    body.location = (-cx, -cy, -min_z)
    bpy.ops.object.transform_apply(location=True)

    coords = [Vector(v.co) for v in body.data.vertices]
    h_now = max(c.z for c in coords) - min(c.z for c in coords)
    s = HEIGHT / h_now
    body.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    coords = [Vector(v.co) for v in body.data.vertices]
    body.location.z -= min(c.z for c in coords)
    coords = [Vector(v.co) for v in body.data.vertices]
    cx = 0.5 * (min(c.x for c in coords) + max(c.x for c in coords))
    cy = 0.5 * (min(c.y for c in coords) + max(c.y for c in coords))
    body.location -= Vector((cx, cy, 0))
    bpy.ops.object.transform_apply(location=True)

    # Region slim: torso + limb thickness (keep arm/leg span roughly)
    hip_axis = 0.11
    for v in body.data.vertices:
        z = v.co.z
        ax = abs(v.co.x)
        if z > CHIN_Z:  # head: mild
            v.co.x *= 0.90
            v.co.y *= 0.88
        elif ax > 0.10 and z > CROTCH_Z * 0.95:  # arms
            v.co.y *= 0.62
            # slight radial shrink around current x (keep reach)
            v.co.x = v.co.x * 0.92 + (0.14 if v.co.x > 0 else -0.14) * 0.08
        elif z < CROTCH_Z * 1.02:  # legs
            target = hip_axis if v.co.x >= 0 else -hip_axis
            v.co.x = target + (v.co.x - target) * 0.52
            v.co.y *= 0.60
        else:  # torso core
            v.co.x *= 0.72
            v.co.y *= 0.74
        if WAIST_Z - 0.07 < z < WAIST_Z + 0.09:
            t = 1.0 - abs(z - WAIST_Z) / 0.09
            v.co.x *= 1.0 - 0.22 * max(0.0, t)
            v.co.y *= 1.0 - 0.12 * max(0.0, t)
    body.data.update()

    # Light polish before crotch cut (keeps pelvis thick enough for a bridge)
    voxel = body.modifiers.new("Voxel_Polish", "REMESH")
    voxel.mode = "VOXEL"
    voxel.voxel_size = 0.012
    bpy.ops.object.modifier_apply(modifier="Voxel_Polish")

    # Crotch slot: stop below pelvis so legs stay attached
    cut_top = CROTCH_Z * 0.78
    cut_height = cut_top - 0.02
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.02 + cut_height * 0.5))
    cutter = bpy.context.active_object
    cutter.name = "crotch_cutter"
    cutter.scale = (0.042, 0.28, cut_height * 0.5)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    mod = body.modifiers.new("CrotchCut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    try:
        mod.solver = "EXACT"
    except TypeError:
        pass
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier="CrotchCut")
    bpy.data.objects.remove(cutter, do_unlink=True)

    islands_cut, _ = count_islands(body.data)
    print("ISLANDS_AFTER_CROTCH_CUT", islands_cut)
    if islands_cut != 1:
        for vs in (0.016, 0.022, 0.030):
            voxel = body.modifiers.new(f"Voxel_Heal_{vs}", "REMESH")
            voxel.mode = "VOXEL"
            voxel.voxel_size = vs
            bpy.ops.object.modifier_apply(modifier=f"Voxel_Heal_{vs}")
            islands_cut, _ = count_islands(body.data)
            print("ISLANDS_AFTER_HEAL", vs, islands_cut)
            if islands_cut == 1:
                break

    # Floor again
    coords = [Vector(v.co) for v in body.data.vertices]
    body.location.z -= min(c.z for c in coords)
    bpy.ops.object.transform_apply(location=True)
    coords = [Vector(v.co) for v in body.data.vertices]
    h_now = max(c.z for c in coords) - min(c.z for c in coords)
    s = HEIGHT / h_now
    body.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    coords = [Vector(v.co) for v in body.data.vertices]
    body.location.z -= min(c.z for c in coords)
    bpy.ops.object.transform_apply(location=True)

    mirror = body.modifiers.new("Mirror_Symmetry", "MIRROR")
    mirror.use_axis[0] = True
    mirror.show_viewport = False
    mirror.show_render = False
    voxel = body.modifiers.new("Voxel_Unify", "REMESH")
    voxel.mode = "VOXEL"
    voxel.voxel_size = 0.012
    voxel.show_viewport = False
    voxel.show_render = False
    sub = body.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1

    body["rebuild_method"] = "metaball_fuse_slim_crotch"
    body["slim_x"] = SLIM_X
    body["slim_y"] = SLIM_Y
    return body


def verify(body):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(deps)
    mesh = ev.to_mesh()
    coords = [ev.matrix_world @ Vector(v.co) for v in mesh.vertices]
    islands, non_manifold = count_islands(mesh)
    raw_islands, _ = count_islands(body.data)
    result = {
        "height": max(c.z for c in coords) - min(c.z for c in coords),
        "min_z": min(c.z for c in coords),
        "min_x": min(c.x for c in coords),
        "max_x": max(c.x for c in coords),
        "verts": len(mesh.vertices),
        "faces": len(mesh.polygons),
        "islands": islands,
        "raw_islands": raw_islands,
        "non_manifold_edges": non_manifold,
        "location": tuple(body.location),
        "scale": tuple(body.scale),
    }
    ev.to_mesh_clear()
    print("VERIFY", result)
    return result


def render_reviews():
    scene = bpy.context.scene
    for energy, loc in ((100, (2.0, -1.8, 2.5)), (40, (-1.5, 1.5, 1.8)), (30, (0, -1, 3))):
        ld = bpy.data.lights.new("L", "AREA")
        ld.energy = energy
        ld.size = 2.5
        o = bpy.data.objects.new("light", ld)
        scene.collection.objects.link(o)
        o.location = loc

    refs = {
        "front": bpy.data.objects.get("ref_front"),
        "right": bpy.data.objects.get("ref_right"),
        "back": bpy.data.objects.get("ref_back"),
    }

    def set_refs(visible_name: str | None):
        for name, obj in refs.items():
            if obj is None:
                continue
            obj.hide_render = visible_name is None or name != visible_name

    for cam, fn, visible_ref in (
        ("cam_front_ref", "rebuild_v1_front.png", "front"),
        ("cam_right_ref", "rebuild_v1_right.png", "right"),
        ("cam_back_ref", "rebuild_v1_back.png", "back"),
        ("cam_front_ref", "rebuild_v1_front_body.png", None),
        ("cam_right_ref", "rebuild_v1_right_body.png", None),
        ("cam_back_ref", "rebuild_v1_back_body.png", None),
    ):
        set_refs(visible_ref)
        scene.camera = bpy.data.objects[cam]
        scene.render.filepath = str(REVIEW_DIR / fn)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", fn)
    for obj in refs.values():
        if obj:
            obj.hide_render = False


def main():
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()
    setup_scene()
    src = bpy.data.images.load(str(REF_TURNAROUND))
    panels = detect_panels(src)
    crops = {
        name: save_crop(src, b, REVIEW_DIR / f"ref_panel_{name}.png")
        for name, b in zip(("front", "right", "back"), panels)
    }
    add_refs(crops)
    add_cameras()
    add_guides()
    body = build_body()
    result = verify(body)
    if result["raw_islands"] != 1:
        raise RuntimeError(f"Expected 1 mesh island, got {result['raw_islands']}")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print("SAVED", BLEND_PATH)
    render_reviews()
    (REVIEW_DIR / "rebuild_v1_verify.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in result.items()) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
