from PyQt5.QtGui import QColor
from qgis._core import QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSingleSymbolRenderer, \
    QgsSimpleFillSymbolLayer, QgsFillSymbolLayer, Qgis, QgsRuleBasedRenderer, QgsWkbTypes, QgsMarkerSymbol, \
    QgsLineSymbol, QgsFillSymbol, QgsGraduatedSymbolRenderer

from UICore.Gv import land_type_dict, model_layer_meta as g_lm
from UICore.common import get_qgis_style, get_field_index_no_case

color_unselected_land = '#969696'
color_land_type = {
    1: '#FFC312',
    2: '#C4E538',
    3: '#12CBC4',
    4: '#FDA7DF',
    5: '#ED4C67',
    6: '#F79F1F',
    7: '#A3CB38',
    8: '#1289A7',
    9: '#D980FA',
    10: '#B53471',
    11: '#EE5A24',
    12: '#009432',
    13: '#0652DD',
    14: '#9980FA',
    15: '#833471',
    16: '#EA2027',
    17: '#006266',
    18: '#1B1464'
}


# 渲染io字段，0单独为一种颜色，1按照type类别赋予颜色
def landio_renderer(layer):
    fni_io, io_field_name = get_field_index_no_case(layer, g_lm.name_io)
    fni_type, type_field_name = get_field_index_no_case(layer, g_lm.name_type)

    unique_values = layer.uniqueValues(fni_type)

    # 定义rules: label, expression, color name, scale
    rules = [('未选中',
              '{}=0'.format(io_field_name),
              {
                  'color': color_unselected_land,
                  'outline_color': color_unselected_land,
                  'opacity': 0.2
              },
              None)]
    for type_index in unique_values:
        rules.append((
            land_type_dict[type_index],
            '{}=1 and {}={}'.format(io_field_name, type_field_name, type_index),
            {
                'color': color_land_type[type_index],
                'outline_color': color_land_type[type_index],
                'opacity': 1.0
            },
            None
        ))

    ruled_renderer(layer, rules)


def graduated_render(layer, field, classes, color_ramp, mode):
    symbol = validatedDefaultSymbol(layer.geometryType())
    renderer = QgsGraduatedSymbolRenderer.createRenderer(layer, field, classes, mode, symbol, color_ramp)

    renderer = QgsRuleBasedRenderer.convertFromRenderer(renderer)
    root_rule = renderer.rootRule()
    rule = root_rule.children()[0].clone()
    rule.setLabel("空值")
    rule.setFilterExpression("{} is NULL".format(field))
    rule.symbol().setColor(QColor(color_unselected_land))
    rule.symbol().setOpacity(0.2)
    root_rule.appendChild(rule)

    if renderer is not None:
        layer.setRenderer(renderer)
        layer.triggerRepaint()


def ruled_renderer(layer, rules):
    geo_type = layer.geometryType()
    symbol = QgsSymbol.defaultSymbol(geo_type)
    renderer = QgsRuleBasedRenderer(symbol)

    # get the "root" rule
    root_rule = renderer.rootRule()

    for label, expression, color, scale in rules:
        # create a clone (i.e. a copy) of the default rule
        rule = root_rule.children()[0].clone()
        # set the label, expression and color
        rule.setLabel(label)
        rule.setFilterExpression(expression)

        if geo_type == QgsWkbTypes.GeometryType.PolygonGeometry:
            symbol_layer = QgsSimpleFillSymbolLayer.create({
                'color': color['color'],
                'outline_color': color['outline_color']
            })

            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # rule.setSymbol(symbol)
        else:
            rule.symbol().setColor(QColor(color['color']))

        opacity = color['opacity']
        if opacity is not None:
            rule.symbol().setOpacity(opacity)
        # set the scale limits if they have been specified
        if scale is not None:
            rule.setMinimumScale(scale[0])
            rule.setMaximumScale(scale[1])
        # append the rule to the list of rules
        root_rule.appendChild(rule)

    # delete the default rule
    root_rule.removeChildAt(0)

    # apply the renderer to the layer
    if renderer is not None:
        layer.setRenderer(renderer)
        # refresh the layer on the map canvas
        layer.triggerRepaint()


def categrorized_renderer(layer, index, data, render_field, color_ramp=None, spec_dict=None):
    unique_values = layer.uniqueValues(index)

    # fill categories
    categories = []
    for unique_value in unique_values:
        symbol = None

        # initialize the default symbol for this geometry type
        symbol = validatedDefaultSymbol(layer.geometryType())
        if spec_dict is not None:
            if unique_value in spec_dict:
                symbol_layer = spec_dict[unique_value]
                symbol.changeSymbolLayer(0, symbol_layer)

        # create renderer object
        if unique_value in data:
            category = QgsRendererCategory(unique_value, symbol, data[unique_value])
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


def validatedDefaultSymbol(geometryType):
    symbol = QgsSymbol.defaultSymbol(geometryType)
    if symbol is None:
        if geometryType == QgsWkbTypes.GeometryType.PointGeometry:
            symbol = QgsMarkerSymbol()
        elif geometryType == QgsWkbTypes.GeometryType.LineGeometry:
            symbol = QgsLineSymbol()
        elif geometryType == QgsWkbTypes.GeometryType.PolygonGeometry:
            symbol = QgsFillSymbol()
    return symbol
