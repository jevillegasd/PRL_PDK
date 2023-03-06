import pya
import SiEPIC
# PCell template
# This macro template provides the framework for a PCell library

# It is recommended to put PCell code into namespaces.
# TODO: change the module name

# The PCell declaration
# Each PCell must provide a declaration. It is recommended to use the PCell name as the class name.
# TODO: change the class name

class Wireguide(pya.PCellDeclarationHelper):

  def __init__(self):
    from pya import DPoint, DPath
    # Important: initialize the super class
    super(Wireguide, self).__init__()
    # declare the parameters
    
    self.param("path", self.TypeShape, "Path", default = DPath([DPoint(0,0), DPoint(-100,0), DPoint(-100,100)],5))
    self.param("radius", self.TypeDouble, "Radius / Chamfer length", default = 50.0)                                                                            
    self.param("width", self.TypeDouble, "Width", default = 10.0, hidden = True)
    self.param("adiab", self.TypeBoolean, "Use curved corners", default = False)
    self.param("bezier", self.TypeBoolean, "Unused Setting", default = False, hidden = True)
    self.param("layers", self.TypeList, "Layers", default = ['M1P'])
    self.param("widths", self.TypeList, "Widths", default =  [2.0])
    self.param("offsets", self.TypeList, "Offsets", default = [0])
    return
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Wireguide_%s" % self.path
  
  def coerce_parameters_impl(self):
    return
          
  def can_create_from_shape_impl(self):
    return self.shape.is_path()

  def transformation_from_shape_impl(self):
    return Trans(Trans.R0,0,0)

  def parameters_from_shape_impl(self):
    self.path = self.shape.dpath
    return
        
  def produce_impl(self):
    from SiEPIC.utils import arc_xy, arc_bezier, angle_vector, angle_b_vectors, inner_angle_b_vectors, translate_from_normal, get_technology_by_name
    from math import cos, sin, pi, sqrt
    import pya
    from SiEPIC.extend import to_itype
    
    print("Wireguide")
    
    TECHNOLOGY = get_technology_by_name('PRL_PDK')
    
    dbu = self.layout.dbu
    wg_width = to_itype(self.width,dbu)
    path = self.path.to_itype(dbu)
    bezier = self.adiab #Using adiab only as a placeholder, no refactoring to match SiEPIC Wireguide GUI
    
    if not (len(self.layers)==len(self.widths) and len(self.layers)==len(self.offsets) and len(self.offsets)==len(self.widths)):
      raise Exception("There must be an equal number of layers, widths and offsets")
    path.unique_points()
    turn=0
    
    
    def chamfer_xy(x, y, length, theta_start, theta_stop):
        # function to create a symmetric chamfer (45 deg)
        # length: chamfer length
        # w: waveguide width
        # length units in dbu
        # theta_start, theta_stop: angles for the of the start and end of the chamfer (in degrees)
    
        from math import pi, cos, sin
        pts = []
        turn = (theta_stop - theta_start)*pi/180.0   
        angle = (theta_stop - theta_start)*pi/2 / 180.0        
        
        pts.append(pya.Point.from_dpoint(pya.DPoint(
                  -length *(cos(angle)/ 1), 0)))
        pts.append(pya.Point.from_dpoint(pya.DPoint(
                  0, length * sin(angle)/ 1)))
                  
        return pya.Path(pts,0).transformed(pya.Trans((theta_start/90)/1,False, x,y)).get_points()
    
    for lr in range(0, len(self.layers)):
      layer = self.layout.layer(TECHNOLOGY[self.layers[lr]])
      width = to_itype(self.widths[lr],dbu)
      offset = to_itype(self.offsets[lr],dbu)

      pts = path.get_points()
      wg_pts = [pts[0]]
      for i in range(1,len(pts)-1):
        turn = ((angle_b_vectors(pts[i]-pts[i-1],pts[i+1]-pts[i])+90)%360-90)/90
        dis1 = pts[i].distance(pts[i-1])
        dis2 = pts[i].distance(pts[i+1])
        angle = angle_vector(pts[i]-pts[i-1])/90
        pt_radius = to_itype(self.radius, dbu)
        
        # determine the radius, based on how much space is available
        if len(pts)==3:
          pt_radius = min (dis1, dis2, pt_radius)
        else:
          if i==1:
            if dis1 <= pt_radius:
              pt_radius = dis1
          elif dis1 < 2*pt_radius:
            pt_radius = dis1/2
          if i==len(pts)-2:
            if dis2 <= pt_radius:
              pt_radius = dis2
          elif dis2 < 2*pt_radius:
            pt_radius = dis2/2
            
        # wireguide bends:
        if(not bezier):
          def angle_origin(p0,p1):
            return angle_b_vectors(pya.Point(1,0),p1-p0)
          
          start_angle = angle_origin(pts[i-1],pts[i])
          stop_angle  = angle_origin(pts[i],pts[i+1]) 
          turn_pts = chamfer_xy(pts[i].x, pts[i].y, pt_radius, start_angle, stop_angle)
          wg_pts += turn_pts
        else:
          wg_pts += pya.Path(arc_xy(-pt_radius, pt_radius, pt_radius, 270, 270 + inner_angle_b_vectors(pts[i-1]-pts[i], pts[i+1]-pts[i]),DevRec='DevRec' in self.layers[lr]), 0).transformed(Trans(angle, turn < 0, pts[i])).get_points()
      
      wg_pts += [pts[-1]]
      wg_pts = pya.Path(wg_pts, 0).unique_points().get_points()
      wg_polygon = pya.Path(wg_pts, width)
      self.cell.shapes(layer).insert(wg_polygon) # insert the wireguide
       
      if layer == self.layout.layer(TECHNOLOGY['P1P']) or  layer == self.layout.layer(TECHNOLOGY['M1P']):
        waveguide_length = wg_polygon.area() / width * dbu

    #Generate Pins
    pts = path.get_points()
    LayerPinRecN = self.layout.layer(TECHNOLOGY['PinRecM'])
    
    # insert pins to wireguide
    t1 = pya.Trans(angle_vector(pts[0]-pts[1])/90, False, pts[0])
    self.cell.shapes(LayerPinRecN).insert(pya.Path([pya.Point(-50, 0), pya.Point(50, 0)], wg_width).transformed(t1))
    self.cell.shapes(LayerPinRecN).insert(pya.Text("pin1", t1, 0.3/dbu, -1))
    
    t = pya.Trans(angle_vector(pts[-1]-pts[-2])/90, False, pts[-1])
    self.cell.shapes(LayerPinRecN).insert(pya.Path([pya.Point(-50, 0), pya.Point(50, 0)], wg_width).transformed(t))
    self.cell.shapes(LayerPinRecN).insert(pya.Text("pin2", t, 0.3/dbu, -1))
	
    LayerDevRecN = self.layout.layer(TECHNOLOGY['DevRec'])
    
    # Compact model information
    angle_vec = angle_vector(pts[0]-pts[1])/90
    halign = 0 # left
    angle=0
    pt2=pts[0]
    pt3=pts[0]
    if angle_vec == 0: # horizontal
      halign = 2 # right
      angle=0
      pt2=pts[0] + pya.Point(0,  wg_width)
      pt3=pts[0] + pya.Point(0, -wg_width)
    if angle_vec == 2: # horizontal
      halign = 0 # left
      angle = 0
      pt2=pts[0] + pya.Point(0,  wg_width)
      pt3=pts[0] + pya.Point(0, -wg_width)
    if angle_vec == 1: # vertical
      halign = 2 # right
      angle = 1
      pt2=pts[0] + pya.Point( wg_width,0)
      pt3=pts[0] + pya.Point(-wg_width,0)
    if angle_vec == -1: # vertical
      halign = 0 # left
      angle = 1
      pt2=pts[0] + pya.Point(wg_width,0)
      pt3=pts[0] + pya.Point(-wg_width,0)
      
    return

