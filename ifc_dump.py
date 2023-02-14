import ifcopenshell
from ifc_common import *

# 表示位置がずれてるIfcAnnotationの情報をIfcOpenShellでダンプしてみる
gid = "0OL3LCjon8C8eMGVs718Tk"

model = ifcopenshell.open('./test_data/AC20-FZK-Haus.ifc')
annotations = model.by_type("IfcAnnotation")

for a in annotations:
    if get_global_id(a) == gid:
        dump_ifc_item("", a, 0)

# IfcTextLiteralWithExtent
# https://standards.buildingsmart.org/IFC/DEV/IFC4_3/RC1/HTML/schema/ifcpresentationdefinitionresource/lexical/ifctextliteralwithextent.htm
