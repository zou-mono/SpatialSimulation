from qgis._core import QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSingleSymbolRenderer, \
    QgsSimpleFillSymbolLayer, QgsFillSymbolLayer, Qgis

from UICore.Gv import land_type_dict
from UICore.common import get_qgis_style, get_field_index_no_case


def categrorized_renderer(layer, index, render_field, color_ramp=None, spec_dict=None):
    unique_values = layer.uniqueValues(index)

    # fill categories
    categories = []
    for unique_value in unique_values:
        symbol = None

        # initialize the default symbol for this geometry type
        if spec_dict is not None:
            if unique_value in spec_dict:
                symbol = spec_dict[unique_value]
        else:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

        # create renderer object
        if unique_value in land_type_dict:
            category = QgsRendererCategory(unique_value, symbol, land_type_dict[unique_value])
        else:
            category = QgsRendererCategory(unique_value, symbol, str(unique_value))
        # entry for the list of category items
        categories.append(category)

    renderer = QgsCategorizedSymbolRenderer(render_field, categories)
    if color_ramp is not None:
        renderer.updateColorRamp(color_ramp)
    if renderer is not None:
        layer.setRenderer(renderer)
        layer.triggerRepaint()


def single_renderer(layer, type=Qgis.SymbolType.Fill, color='cyan', outline_color='#000000', opacity=1, bReprint=True):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    layer_style = {}
    layer_style['color'] = color  # '%d, %d, %d' % (150, 150, 150)
    layer_style['outline_color'] = outline_color  # '#232323'

    symbol_layer = None
    if type == Qgis.SymbolType.Fill:
        symbol_layer = QgsSimpleFillSymbolLayer.create(layer_style)

    if symbol_layer is not None:
        symbol.changeSymbolLayer(0, symbol_layer)
    symbol.setOpacity(opacity)

    if bReprint:
        singleRenderer = QgsSingleSymbolRenderer(symbol)
        if singleRenderer is not None:
            layer.setRenderer(singleRenderer)
            layer.triggerRepaint()

    return symbol

