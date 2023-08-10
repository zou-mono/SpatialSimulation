from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QTableWidget, QWidget

from UICore.common import get_qgis_style, get_field_index_no_case


def table_default_style(tbl: QTableWidget):
    color = tbl.palette().color(QPalette.Button)
    tbl.horizontalHeader().setStyleSheet(
        "QHeaderView::section {{ background-color: {}}}".format(color.name()))
    tbl.verticalHeader().setStyleSheet(
        "QHeaderView::section {{ background-color: {}}}".format(color.name()))
    tbl.setStyleSheet(
        "QTableCornerButton::section {{ color: {}; border: 1px solid; border-color: {}}}".format(color.name(),
                                                                                                 color.name()))

