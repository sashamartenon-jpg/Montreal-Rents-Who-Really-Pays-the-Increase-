"""openpyxl écrit les graphiques avant les images : les images couvrent les graphiques. Ici, images d'abord (fond), graphiques par-dessus."""
import openpyxl.drawing.spreadsheet_drawing as sd
from openpyxl.chart._chart import ChartBase
from openpyxl.drawing.image import Image
from openpyxl.packaging.relationship import Relationship
from openpyxl.drawing.spreadsheet_drawing import _check_anchor, OneCellAnchor, TwoCellAnchor, SHEET_DRAWING_NS


def _write(self):
    anchors = []
    for idx, obj in enumerate(self.images + self.charts, 1):
        anchor = _check_anchor(obj)
        if isinstance(obj, ChartBase):
            rel = Relationship(type="chart", Target=obj.path)
            anchor.graphicFrame = self._chart_frame(idx)
        elif isinstance(obj, Image):
            rel = Relationship(type="image", Target=obj.path)
            child = anchor.pic or anchor.groupShape and anchor.groupShape.pic
            if not child:
                anchor.pic = self._picture_frame(idx)
            else:
                child.blipFill.blip.embed = "rId{0}".format(idx)
        anchors.append(anchor)
        self._rels.append(rel)
    for a in anchors:
        if isinstance(a, OneCellAnchor):
            self.oneCellAnchor.append(a)
        elif isinstance(a, TwoCellAnchor):
            self.twoCellAnchor.append(a)
        else:
            self.absoluteAnchor.append(a)
    tree = self.to_tree()
    tree.set('xmlns', SHEET_DRAWING_NS)
    return tree


sd.SpreadsheetDrawing._write = _write
