"""
PRL PDK Component - Bend (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "Bend", that generates a waveguide circular bend (arc).
Parameters:
  -
  -
(C) NYUAD 2023

Version history:  
  Juan Villegas 2022/08/15: Initial Release
"""

import pya

from math import pi, cos, sin
from SiEPIC.utils import arc, points_per_circle, arc_wg, get_technology_by_name, angle_vector


# Debug Juan: This is a modified version of the same fucntions, here until we can push this to update SiEPIC tools origin

# Take a list of points and create a polygon of width 'width'. Explicitly decides to make the ends Manhattan
def arc_to_waveguide(pts, width, manhattan = True):
    return pya.Polygon( translate_from_normal(pts, -width / 2.0, manhattan) + translate_from_normal(pts[::-1], -width / 2.0, manhattan))

# Translate each point by its normal a distance 'trans' and explicitly make ends manhattan
def translate_from_normal(pts, trans,  manhattan = True):
    #  pts = [pya.DPoint(pt) for pt in pts]
    pts = [pt.to_dtype(1) for pt in pts]
    if len(pts) < 2:
        return pts    
    from math import cos, sin, pi
    d = 1. / (len(pts) - 1)
    a = angle_vector(pts[1] - pts[0]) * pi / 180 + (pi / 2 if trans > 0 else -pi / 2)
    tpts = [pts[0] + pya.DPoint(abs(trans) * cos(a), abs(trans) * sin(a))]

    for i in range(1, len(pts) - 1):
        dpt = (pts[i + 1] - pts[i - 1]) * (2 / d)
        tpts.append(pts[i] + pya.DPoint(-dpt.y, dpt.x) * (trans / 1 / dpt.abs()))

    a = angle_vector(pts[-1] - pts[-2]) * pi / 180 + (pi / 2 if trans > 0 else -pi / 2)
    tpts.append(pts[-1] + pya.DPoint(abs(trans) * cos(a), abs(trans) * sin(a)))

    # Make ends manhattan
    if manhattan:
      if abs(tpts[0].x - pts[0].x) > abs(tpts[0].y - pts[0].y):
          tpts[0].y = pts[0].y
      else:
          tpts[0].x = pts[0].x
      if abs(tpts[-1].x - pts[-1].x) > abs(tpts[-1].y - pts[-1].y):
          tpts[-1].y = pts[-1].y
      else:
          tpts[-1].x = pts[-1].x
    return [pt.to_itype(1) for pt in tpts]

    
class Bend(pya.PCellDeclarationHelper):
  def __init__(self):
    super(Bend, self).__init__()
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('PRL_PDK')

    # declare the parameters
    self.param("waveguide", self.TypeLayer, "Waveguide Layer", default = TECHNOLOGY['Si'])
    self.param("angle", self.TypeDouble, "Angle", default = 90)
    self.param("radius", self.TypeDouble, "Radius", default = 10)
    self.param("bezier", self.TypeList, "Type", choices = [["Circular Curve",0],["Bezier Curve",1]])
    
    self.param("wg_width", self.TypeDouble, "Waveguide Width", default = 0.5)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    # hidden parameters, can be used to query this component:
    self.param("p1", self.TypeShape, "DPoint location of pin1", default = pya.Point(-10000, 0), hidden = True, readonly = True)
    self.param("p2", self.TypeShape, "DPoint location of pin2", default = pya.Point(0, 10000), hidden = True, readonly = True)
    

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_Bend(R= %.3f, <%.1f °)"%(self.radius, self.angle)

  def can_create_from_shape_impl(self):
    return False


  def produce(self, layout, layers, parameters, cell):
    
    TECHNOLOGY = get_technology_by_name('PRL_PDK')
    
    self._layers = layers
    self.cell = cell
    self._param_values = parameters
    self.layout = layout

    # cell: layout cell to place the layout
    # LayerSiN: which layer to use
    # r: radius
    # w: waveguide width
    # length units in dbu

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    LayerWg = self.layout.layer(self.waveguide)
    LayerPinRecN = self.layout.layer(self.pinrec)
    LayerDevRecN = self.layout.layer(self.devrec)
      
    w = int(round(self.wg_width/dbu))
    r = int(round(self.radius/dbu))
    angle = int(round(self.angle))
    if angle>180: 
      angle = 180
    bezier = self.bezier
    
    # draw the bends
    dy = r*sin((90-angle)/180*pi)
    dx = r*cos((90-angle)/180*pi)
    x = 0
    y = r
      
    t_shape = pya.Trans(pya.Trans.R0,x, y)
    arc_shape = arc_to_waveguide(arc(r, 270, 270+angle), w, manhattan = False)
    shapes(LayerWg).insert(arc_shape.transformed(t_shape))
    
    # Create the pins on the waveguides, as short paths:
    from SiEPIC._globals import PIN_LENGTH as pin_length
    if pin_length <100:
      pin_length = 100
      
    # Pin on the top side:
    p2 = [pya.Point(0, -pin_length/2), pya.Point(0, pin_length/2)]
    p2c = pya.Point(0, 0)
    self.set_p2 = p2c
    self.p2 = p2c
    v =  pya.Vector(dx, r-dy)
    
    t = pya.ICplxTrans(1,angle-90,False,v)
    pin = pya.Path(p2, w)

    pin_ptr = shapes(LayerPinRecN).insert(pin)
    pin_ptr.transform(t)
    t = pya.Trans(0,False, dx, r-dy)
    text = pya.Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Pin on the left side:
    p1 = [pya.Point(pin_length/2+x,0), pya.Point(-pin_length/2+x,0)]
    p1c = pya.Point(x,0)
    self.set_p1 = p1c
    self.p1 = p1c
    pin = pya.Path(p1, w)
    shapes(LayerPinRecN).insert(pin)
    t = pya.Trans(pya.Trans.R0, x, 0)
    text = pya.Text("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Create the device recognition layer, wg_width away from the waveguides.
    self.cell.shapes(LayerDevRecN).insert(arc_to_waveguide(arc(r, 270, 270+angle), w*3, manhattan = False).transformed(t_shape))
    
    TextSize = 500
    # Compact model information
    t = pya.Trans(pya.Trans.R0, x+r/10, 0)
    text = pya.Text ("Lumerical_INTERCONNECT_library=Design kits/LIGENTEC_PDK", t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = TextSize
    t = pya.Trans(pya.Trans.R0, x+r/10, TextSize*2)
    text = pya.Text ('Component=LGT_Arc_waveguide', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = TextSize
    t = pya.Trans(pya.Trans.R0, x+r/10, TextSize*4)
    text = pya.Text ('Spice_param:theta=%.3fu width=%.3fu radius=%.3fu "delay compensation"=%.3fu'% (self.angle, self.wg_width, self.radius, 0.0), t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = TextSize

