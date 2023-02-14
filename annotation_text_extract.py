import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np
import dataclasses

from ifc_common import *

@dataclasses.dataclass
class IfcContextOfItems:
    ifc_openshell_item: object
    # WorldCoordinateSystem(IfcAxis2Placement3D)をtransform matrix(4x4)に変換したものを格納
    world_coord_system: np.ndarray
    # 参考：
    # https://www.jstage.jst.go.jp/article/shase/45/275/45_17/_pdf/-char/ja
    # https://www.jstage.jst.go.jp/article/shase/45/275/45_17/_pdf


@dataclasses.dataclass
class IfcAnnotation: 
    ifc_openshell_item: object
    global_id: str
    # ObjectPlacementをtransform matrix(4x4)に変換したものを格納
    local_placement:  np.ndarray
    context_of_items: IfcContextOfItems

@dataclasses.dataclass
class IfcAnnotationText:
    """
      p3-------------p2
      |              | |
      |   (Text)     | | sizeInY
      |              | |
      p0------------p1 
       -- sizeInX --

      上記のようなテキストがあった場合、メンバ変数には以下の値が格納される。
       - literal ... (Textの内容)
       - size_in_x ... p0p1の長さ
       - size_in_y ... p0p3の長さ
      
      calc_face_vertices()のメソッドでp0, p1, p2, p3座標のリストを返却する。
    """
    ifc_openshell_item: object
    # 
    id: str
    # 親要素のIfcAnnotation
    parent: IfcAnnotation
    # Placement(IfcAxis2Placement2D)をtransform matrix(4x4)に変換したものを格納
    placement: np.ndarray
    # 
    size_in_x: float
    # 
    size_in_y: float
    # 
    literal: str

    def calc_face_vertices(self):
        m1 = self.parent.local_placement
        m2 = self.parent.context_of_items.world_coord_system
        m3 = self.placement
        m = np.dot(np.dot(m1, m2), m3)

        # 変換行列を合成して[0,0]～[sx, sy]のbounding boxを座標変換する。
        sx = self.size_in_x
        sy = self.size_in_y
        p0 = np.dot(m, np.array([ 0,  0, 0, 1]))
        p1 = np.dot(m, np.array([sx,  0, 0, 1]))
        p2 = np.dot(m, np.array([sx, sy, 0, 1]))
        p3 = np.dot(m, np.array([ 0, sy, 0, 1]))
        return np.array([
            np.delete(p0, 3),
            np.delete(p1, 3),
            np.delete(p2, 3),
            np.delete(p3, 3)])

def append_ifc_annotation_text(
    name: str,
    parent: IfcAnnotation, 
    item: object, 
    dest: list):

    if name == "ContextOfItems":
        """
        ContextOfItems(IfcGeometricRepresentationSubContext#15265): ContextIdentifier=Annotation, ContextType=Plan, CoordinateSpaceDimension=None, Precision=None, WorldCoordinateSystem=None, TrueNorth=None, TargetScale=0.01, TargetView=PLAN_VIEW, UserDefinedTargetView=None
            ParentContext(IfcGeometricRepresentationContext#374): ContextIdentifier=None, ContextType=Plan, CoordinateSpaceDimension=3, Precision=1e-05
                WorldCoordinateSystem(IfcAxis2Placement3D#371): 
                    Location(IfcCartesianPoint#369): Coordinates=(0.0, 0.0, 0.0)
                    Axis(IfcDirection#367): DirectionRatios=(0.0, 0.0, 1.0)
                    RefDirection(IfcDirection#365): DirectionRatios=(1.0, 0.0, 0.0)
                TrueNorth(IfcDirection#372): DirectionRatios=(0.766044443119, 0.642787609687)
        """
        a2p = get_axis2placement(item.ParentContext.WorldCoordinateSystem)
        parent.context_of_items = IfcContextOfItems(ifc_openshell_item=item, world_coord_system= a2p)
        return True
    elif item.is_a("IfcTextLiteralWithExtent"):
        """
        Item[0](IfcTextLiteralWithExtent#75793): Literal=50, Path=LEFT, BoxAlignment=bottom-left
            Placement(IfcAxis2Placement2D#75792): 
                Location(IfcCartesianPoint#75790): Coordinates=(13.5399999976, 10.620000015)
                RefDirection(IfcDirection#75788): DirectionRatios=(0.0, 1.0)
            Extent(IfcPlanarExtent#75787): SizeInX=0.549829, SizeInY=0.4
        """
        id = get_ifc_instance_id(item)
        a2p = get_axis2placement(item.Placement)
        literal = item.Literal
        size_in_x, size_in_y = item.Extent
        ifc_text = IfcAnnotationText(
            id = id,
            ifc_openshell_item=item,
            parent=parent,
            placement=a2p,
            size_in_x = size_in_x,
            size_in_y = size_in_y,
            literal=literal)
        dest.append(ifc_text)
        return False
    return True


def collect_ifc_annotation_text(model) -> list:
    annotations_items = model.by_type("IfcAnnotation")
    annotation_texts = []
    for annotations_item in annotations_items:
        gid = get_global_id(annotations_item)
        #print(f"Extracting IfcTextLiteralWithExtent of ifcAnnotation[{gid}]")
        annotation = to_ifc_annotation(annotations_item)
        callback = lambda _lv, name, item : append_ifc_annotation_text(
                name, annotation, item, annotation_texts)
        for_each_recursively(gid, annotations_item, callback, 0)
    return annotation_texts

def to_ifc_annotation(item):
    ensure_type(item, "IfcAnnotation")
    global_id = get_global_id(item)
    local_placement = ifcopenshell.util.placement.get_local_placement(item.ObjectPlacement)
    return IfcAnnotation(
        ifc_openshell_item = item,
        global_id=global_id, 
        local_placement= local_placement,
        context_of_items=None)

"""
#test: 
model = ifcopenshell.open('./test_data/AC20-FZK-Haus.ifc')
texts = collect_ifc_annotation_text(model)
for text in texts:
    vs = text.calc_face_vertices()
    print(f"[{text.literal}]:{vs[0]},{vs[1]},{vs[2]},{vs[3]}")
"""

# IfcTextLiteralWithExtent
# https://standards.buildingsmart.org/IFC/DEV/IFC4_3/RC1/HTML/schema/ifcpresentationdefinitionresource/lexical/ifctextliteralwithextent.htm

# ifcaxis2placement3dの仕様
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x/FINAL/HTML/ifcgeometryresource/lexical/ifcaxis2placement3d.html
# Axis ... Z軸
# RefDirection ... X軸
