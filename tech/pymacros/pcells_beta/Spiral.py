"""
PRL PDK Component - Spiral (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "Spiral"
Parameters:
  -
  -
(C) NYUAD 2023

Version history:  
  Juan Villegas 2022/08/15: Initial Release
"""

import pya
from SiEPIC.utils import get_technology_by_name
from pya import *

class Spiral(pya.PCellDeclarationHelper):
  def __init__(self):
    super(Spiral, self).__init__()
    self.technology_name = 'PRL_PDK'
    TECHNOLOGY = get_technology_by_name(self.technology_name)
    from SiEPIC.utils import load_Waveguides_by_Tech
    self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)
    
    p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default = self.waveguide_types[0]['name'])
    for wa in self.waveguide_types:
        p.add_choice(wa['name'],wa['name'])
    
    self.param("length", self.TypeDouble, "Target Waveguide length", default = 3000.0)           
    self.param("wg_spacing", self.TypeDouble, "Waveguide spacing (microns)", default = 10.0)     
    self.param("spiral_ports", self.TypeBoolean, "Ports on the same side? 0/1", default = False)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    
    #Hidden params
    self.param("wg_width", self.TypeDouble, "Waveguide Width", default = 1.0, hidden = True)
    self.param("min_radius", self.TypeDouble, "Minimum Radius", default = 20.0, hidden = True)
    self.param("radius", self.TypeDouble, "Radius", default = 20.0, hidden = True)
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "spiral_Len:%s-Spa:%.3f" % \
    (self.length, self.wg_spacing)
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
    if self.layout.technology_name == '':
        lv = pya.Application.instance().main_window().current_view()
        if lv == None:
          self.layout.technology_name = self.technology_name
          self.layout.dbu = 0.005
        else:
          self.layout.technology_name = lv.active_cellview().layout().technology_name
          self.layout.dbu = lv.active_cellview().layout().dbu
    ly = self.layout
    
    TECHNOLOGY = get_technology_by_name('Ligentec_AN800') 
    shapes = self.cell.shapes
    dbu = self.layout.dbu
    
    
    # Load parameters for the chosen waveguide type
    params = [t for t in self.waveguide_types if t['name'] == self.waveguide_type]
    if type(params) == type([]) and len(params) > 0:
        params = params[0]
    else:
        print('Error: waveguide type not found in PDK waveguides')
        raise Exception('error: waveguide type (%s) not found in PDK waveguides'%waveguide_type)
    
    # Load layer information
    layers = []
    for c in params['component']:
      layers.append(c)

    from SiEPIC.utils import points_per_circle, translate_from_normal
    from SiEPIC.extend import to_itype, to_dtype
    from numpy import sin, cos
    # Load other parameters
    self.min_radius = float(params['radius'])
    self.wg_width =  float(layers[0]['width'])
    spacing = self.wg_spacing+self.wg_width;
    
    layerWaveguides = ly.layer(TECHNOLOGY[layers[0]['layer']])
    layerPinRecN = ly.layer(self.pinrec)
    layerDevRecN = ly.layer(self.devrec)
  
    from scipy import pi
    import numpy as np
   
    def ph_spiral_length(r, spacing, N):
      d = 2*(2*r)
      D = d+spacing*4*N
      lspiral1 = spiral_length(d,D, N)
      lspiral2 = spiral_length(d+spacing,D+spacing, N)
      if self.spiral_ports: 
        lspiral2  += spiral_length(D,D+4*spacing, N)/2
      slength = 2*pi*r 
      return slength + lspiral1 + lspiral2 
    
    def spiral_length(d, D, N):
      return pi*N*(d+D)/2
    
    #Find parameters for approximate length of spiral
    r = self.min_radius
    d = 2*r
    D = d+2*(spacing*2)
    
    # Initial guess for the number of turns
    L_spiral = (self.length- 2*(2*pi* r))
    N = np.floor(L_spiral/(pi*(d+D)/2  +  pi*(d+spacing+D+spacing)/2  )   )       +1
    
    
    # Closer guess 
    L_spiral2 = self.length+1
    while L_spiral2 > self.length:
      N-= 1
      L_spiral2= ph_spiral_length(r, spacing ,N)
    N = 1 if N <=0 else N
    
    #Find exact radius
    from scipy import optimize
    new_r = 0
    new_r = optimize.newton(lambda r: ph_spiral_length(r, spacing, N) - self.length, r)
    self.radius = new_r if new_r>= self.min_radius else self.min_radius

    print('Corrected radius:%s, L=%s'%( self.radius,ph_spiral_length(new_r, spacing, N) ))
    
    # Get a full turn of points from a spiral
    def get_spiral_points(a, r, angle = 2*pi, start_angle = 0):
      wg_pts = []
      npoints = int(points_per_circle(r)*(angle/(2*pi))) # number of points per circle.
      dtetha = angle / npoints  # increment, in radians, for each point:   
      for i in range(0, npoints+1):
        t = i*dtetha + start_angle
        xa = to_itype((a*t + r) * cos(t),dbu);
        ya = to_itype((a*t + r) * sin(t),dbu);
        #wg_pts.append(pya.Point.from_dpoint(pya.DPoint(xa/dbu, ya/dbu)))
        wg_pts.append(pya.Point(xa,ya))
      return wg_pts
    
    def get_s_points(r, angle = 2*pi, trans = pya.Trans.R0):
      wg_pts = []
      npoints = int(points_per_circle(r)) # number of points per circle.
      dtetha = angle / npoints  # increment, in radians, for each point:   
      for i in range(0, npoints+1):
        t = i*dtetha
        if abs(t)<pi :
          xa = r * cos(t)
        else: 
          xa = - r * cos(t)-2*r
        ya = r * sin(t);
        #wg_pts.append(pya.Point.from_dpoint(pya.DPoint(xa/dbu, ya/dbu))*trans)
        wg_pts.append(pya.Point(to_itype(xa,dbu), to_itype(ya,dbu))*trans)
      return wg_pts
    
    
    # Draw waveguide from a polyline
    def draw_poly_wg(pts,layers, t = pya.Trans(0,0)):
      turn = 0
      for c in layers:
        layer = ly.layer(TECHNOLOGY[c['layer']])
        width = to_itype(c['width'], dbu)
        offset = to_itype(c['offset'], dbu)
        
        wg_polygon = pya.Polygon(translate_from_normal(pts, width/2 + (offset if turn > 0 else - offset)) +
                               translate_from_normal(pts, -width/2 + (offset if turn > 0 else - offset))[::-1])
        shapes(layer).insert(wg_polygon.transformed(t))
        if layer == layerWaveguides:
          area = wg_polygon.area()
          length = to_dtype(area,dbu)/width
      return length
    
    #Draw  Archimedes Spiral
    # r = b + a * theta
    b = self.radius
    a = 2*spacing/(2*pi)
    
    drawn_length = 0 
    drawn_length2 = 0   

    # Centre S-shape connecting waveguide        
    t = pya.Trans(pya.Trans.R0,to_itype(b,dbu),0)
    r = b
    pts = (get_s_points(r , -2*pi, t))
    
    def reverse(arg):
      return [arg[len(arg) - i] for i in range(1, len(arg)+1)]
      
    # Inner Spiral
    r = 2* b
    d = 2*r
    D = d+2*spacing*N
    pts = reverse(pts) + (get_spiral_points(a, r, angle = 2*pi*N))
    
    # Outer Spiral
    if not self.spiral_ports:
      pts2 = get_spiral_points(a, r+spacing, angle = 2*pi*N, start_angle = -pi) 
    else:
      pts2 = get_spiral_points(a, r+spacing, angle = 2*pi*N+pi, start_angle = -pi) 

    pts = reverse(pts) + (pts2)
    
    path = pya.Path(pts,0.0).unique_points()
    
    drawn_length += draw_poly_wg(path.get_points(), layers, t = pya.Trans.R0)
    
    print("spiral length: %s microns" % drawn_length)     
    
    # Pins on the waveguide:
    from SiEPIC._globals import PIN_LENGTH as pin_length
    
   
    
    x = pts[0].x 
    w = to_itype(self.wg_width,dbu)
    t = Trans(Trans.R0, x,0)
    pin = Path([Point(0,-pin_length/2), Point(0,pin_length/2)], w)
    pin_t = pin.transformed(t)
    shapes(layerPinRecN).insert(pin_t)
    text = Text ("pin2", t)
    shape = shapes(layerPinRecN).insert(text)
    shape.text_size = to_itype(0.4,dbu)


    x = pts[-1].x 
    if self.spiral_ports:
      pin = Path([Point(0,-pin_length/2), Point(0,pin_length/2)], w)
    else:
      pin = Path([Point(0,pin_length/2), Point(0,-pin_length/2)], w)
    
    t = Trans(Trans.R0, x,0)
    
    pin_t = pin.transformed(t)
    shapes(layerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(layerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Compact model information
    t = Trans(Trans.R0, -abs(x), -abs(x)/2)
    text = Text ('Length=%.3fu' % drawn_length, t)
    shape = shapes(layerDevRecN).insert(text)
    shape.text_size = 10/dbu
    
    t = Trans(Trans.R0, 0, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/%s'%params['CML'], t)
    shape = shapes(layerDevRecN).insert(text)
    shape.text_size = 1/dbu
    
    t = Trans(Trans.R0, 0, 3/dbu)
    text = Text ('Component=%s'%params['model'], t)
    shape = shapes(layerDevRecN).insert(text)
    shape.text_size = 1/dbu
    
    t = Trans(Trans.R0, 0, -3/dbu)
    text = Text \
      ('Spice_param:wg_length=%.3fu width=%.3fu min_radius=%.3fu' %\
      (drawn_length, self.wg_width, (self.radius)), t )
    shape = shapes(layerDevRecN).insert(text)
    shape.text_size = 1/dbu

    return