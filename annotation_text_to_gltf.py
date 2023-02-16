import os
import trimesh
import dataclasses
from trimesh.visual import texture, TextureVisuals
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from annotation_text_extract import *

@dataclasses.dataclass
class AnnotationFaces:
    vertices: list
    normals: list
    faces: list

@dataclasses.dataclass
class TextureAtlas:
    image: Image
    textures: list

@dataclasses.dataclass
class TextureInfo:
    id: str
    text: str
    topx: int
    topy: int
    width: int
    height: int

def create_annotation_texture_atlas(
    annotations: list,
    texture_atlas_size_pixel: int,
    font: ImageFont) -> TextureAtlas:
    """
    annotation配列をもとにテクスチャアトラス情報を生成
    """
    img = Image.new(
        "RGB", 
        (texture_atlas_size_pixel, texture_atlas_size_pixel),
        (255, 255, 255))

    all_textures = []
    ix = 0
    iy = 0
    maxHeight = 0
    draw = ImageDraw.Draw(img)
    # 注記テキストを1枚のテクスチャアトラス画像の中に詰め込む。
    # ※引数で指定されたサイズの画像の左上から単純に画像を敷き詰めて行っているだけの雑な実装です。
    # ちゃんとした実相を参考にしたい人は「TextureAtlas 長方形詰込み」などで検索して調べてみてください。
    for annotation in annotations:
        id = annotation.id
        text = annotation.literal
        (w, h) = get_text_dimensions(text, font)
        if h > maxHeight:
            maxHeight = h
        if (ix + w > texture_atlas_size_pixel):
            ix = 0
            iy += maxHeight
            maxHeight = 0 
        tx = ix
        ty = iy
        ix += w
        t = TextureInfo(id=id, text=text, topx = tx, topy = ty, width=w, height=h)
        all_textures.append(t)
        draw_text(draw, text, font, tx, ty)
    return TextureAtlas(
        image = img, 
        textures = all_textures)

def create_trimesh_texture_visuals(texture_atlas: TextureAtlas) -> TextureVisuals:
    """
    TextureAtlasからtrimeshのテクスチャ情報を生成
    """
    uvs = []
    for tx in texture_atlas.textures:
        texture_atlas_w = texture_atlas.image.width
        texture_atlas_h = texture_atlas.image.height
        topy = texture_atlas_h - tx.topy
        topx = tx.topx
        w = tx.width
        h = tx.height
        bottomy = topy - h
        rightx = topx + w
        img = texture_atlas.image
        uv_left = topx / texture_atlas_w
        uv_right = rightx / texture_atlas_w
        uv_bottom = bottomy / texture_atlas_h
        uv_top = topy / texture_atlas_h
        uvs.append([uv_left, uv_bottom])
        uvs.append([uv_right, uv_bottom])
        uvs.append([uv_right, uv_top])
        uvs.append([uv_left, uv_top])
    material = texture.SimpleMaterial(image=img)
    return TextureVisuals(uv=uvs, material=material)

def draw_text(draw, text: str, font, x: int, y: int):
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

def get_text_dimensions(text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()
    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return (text_width, text_height)

def append_annotation_face(
    annotation: IfcAnnotationText,
    vertices: list,
    normals: list,
    faces: list):
    vs = annotation.calc_face_vertices()
    """
    vs[3]     vs[2]
       +------+
       |    / |
       |   /  |
       |  /   |
       | /    |
       +------+
    vs[0]     vs[1]
    0-2-3, 0-1-2のfaceを追加
    """
    idx0 = len(vertices)
    vertices.append(vs[0])
    vertices.append(vs[1])
    vertices.append(vs[2])
    vertices.append(vs[3])
    faces.append([idx0, idx0 + 2, idx0 + 3])
    faces.append([idx0, idx0 + 1, idx0 + 2])
    normals.append(np.cross(vs[2] - vs[0], vs[3] - vs[0]))
    normals.append(np.cross(vs[1] - vs[0], vs[2] - vs[0]))

def create_annotation_faces(annotations: list) -> AnnotationFaces:
    """
    annotation要素をもとに板ポリゴンのvertices, normals, facesを生成
    """
    vertices = []
    normals = []
    faces = []
    uvs = []
    for annotation in annotations:
        append_annotation_face(annotation, vertices, normals, faces)
    return AnnotationFaces(vertices, normals, faces)

# 動作確認：
ifc_path = "./test_data/AC20-FZK-Haus.ifc"

## ここは実在するフォントを選ぶ
font_path = "C:/Windows/Fonts/meiryob.ttc"
font = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", 32)
image_size = 512
output_path = "output/annotations.glb"
os.makedirs("output", exist_ok=True)

# モデルの読み込み
model = ifcopenshell.open(ifc_path)

# ifcAnnotationTextの情報を抽出
annotation_texts = collect_ifc_annotation_text(model)

# 板ポリゴン生成
faces = create_annotation_faces(annotation_texts)

# テクスチャ生成
texture_atlas = create_annotation_texture_atlas(annotation_texts, image_size, font)
tex_visual = create_trimesh_texture_visuals(texture_atlas)

# メッシュ生成
mesh = trimesh.Trimesh(
    vertices=faces.vertices,
    faces=faces.faces,
    face_normals=faces.normals,
    visual=tex_visual,
    validate=True,
    process=False
    )

# glb形式で保存
mesh.export(file_type="glb", file_obj=output_path)

# テクスチャ画像を確認したい場合はここをコメントアウト。
os.makedirs("texture", exist_ok=True)
texture_atlas_path = "texture/annotations.png"
texture_atlas.image.save(texture_atlas_path)

#meshを目視したい人はここをコメントアウト。
mesh.show()
