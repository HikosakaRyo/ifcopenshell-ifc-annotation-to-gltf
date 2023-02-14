import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np
from collections.abc import Callable

def for_each_recursively(
    item_name: str,
    item, 
    callback: Callable[[int, str, object], bool],
    level: int = 0):
    if not callback(level, item_name, item):
        return
    ensure_has_get_info(item)
    info = item.get_info()
    for k in info.keys():
        v = info[k]
        if has_get_info(v):
            for_each_recursively(k, v, callback, level + 1)
    # Representations属性を持っている場合は子要素としてたどる
    for idx, r in enumerate(get_representations(item)):
        for_each_recursively(f"Representation[{idx}]", r, callback, level + 1)
    # Items属性を持っている場合は子要素としてたどる
    for idx, i in enumerate(get_items(item)):
        for_each_recursively(f"Item[{idx}]", i, callback, level + 1)
    for idx, e in enumerate(get_elements(item)):
        for_each_recursively(f"Element[{idx}]", e, callback, level + 1)

def has_child_item(item):
    return has_get_info(item) or has_representations(item) or has_items(item) or has_elements(item)

def dump_ifc_item_callback(
        indent: int,
        item_name: str,
        item: object):
    istr = " " * indent
    ensure_has_get_info(item)
    info = item.get_info()
    type_and_id = f'{get_ifc_type(item)}#{get_ifc_instance_id(item)}'
    attr_strs = []
    if hasattr(item, "ObjectPlacement"):
        attr_strs.append(f"obj_place={get_obj_placement_string(item)}")
    
    dump_ignore_att = {"type", "id", "Items", "Representations", "Elements"}

    for k in info.keys():
        if k in dump_ignore_att or has_get_info(info[k]):
            continue
        attr_strs.append(f"{k}={info[k]}")
    attr_line = ", ".join(attr_strs)
    print(f"{istr}{item_name}({type_and_id}): {attr_line}")
    return True

def dump_ifc_item(
    root_item_name: str,
    item, 
    indent : int):
    """
    指定IFC要素の子階層を辿ってツリー表示する。
    """
    for_each_recursively(root_item_name, item, dump_ifc_item_callback, 0)

def get_obj_placement_string(obj):
    matrix = ifcopenshell.util.placement.get_local_placement(obj.ObjectPlacement)
    return (f"({matrix[0, 3]}, {matrix[1, 3]}, {matrix[2, 3]})")

def has_get_info(obj):
    m = getattr(obj, 'get_info', None)
    return callable(m)

def has_representations(obj):
    return hasattr(obj, 'Representations')

def get_representations(obj):
    if has_representations(obj):
        return obj.Representations
    else:
        return []

def has_items(obj):
    return hasattr(obj, 'Items')

def get_items(obj):
    if has_items(obj):
        return obj.Items
    else:
        return []

def has_elements(obj):
    return hasattr(obj, 'Elements')

def get_elements(obj):
    if has_elements(obj):
        return obj.Elements
    else:
        return []

def ensure_has_get_info(item):
    if not has_get_info(item):
        raise RuntimeError(f"{item} doesn't has get_info")

def ensure_type(item, expected_type):
    ensure_has_get_info(item)
    info = item.get_info()
    if not "type" in info.keys():
        raise RuntimeError(f"{item} doesn't has type attribute")
    ifc_type = info["type"]
    if expected_type != ifc_type:
        raise RuntimeError(f"unexpected ifc_type. expected:{expected_type}, actual={ifc_type}")

def get_global_id(item):
    ensure_has_get_info(item)
    info = item.get_info()
    return info["GlobalId"]

def get_ifc_type(item):
    ensure_has_get_info(item)
    info = item.get_info()
    return info["type"]

def get_ifc_instance_id(item):
    ensure_has_get_info(item)
    info = item.get_info()
    return info["id"]

# 以下のifcopenshell.util.placement.get_axis2placementと同じ処理だがx.resize(3)の箇所で
# cannot resize an array that references or is referenced
# のエラーが出たのでrefcheck=Falseの引数を指定するように修正。
# https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.7.0/src/ifcopenshell-python/ifcopenshell/util/placement.py
def get_axis2placement(plc):
    if plc.is_a("IfcAxis2Placement3D"):
        z = np.array(plc.Axis.DirectionRatios if plc.Axis else (0, 0, 1))
        x = np.array(plc.RefDirection.DirectionRatios if plc.RefDirection else (1, 0, 0))
        o = plc.Location.Coordinates
    elif plc.is_a("IfcAxis2Placement2D"):
        z = np.array((0, 0, 1))
        if plc.RefDirection:
            a, b = plc.RefDirection.DirectionRatios
            x = np.array([a, b])
            #x = np.resize(x, 3)
            x.resize(3, refcheck=False) 
        else:
            x = np.array((1, 0, 0))
        o = (*plc.Location.Coordinates, 0.0)
    return ifcopenshell.util.placement.a2p(o, z, x)
