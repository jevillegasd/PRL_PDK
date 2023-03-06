"""
Ligentec PDK Component - Ring (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "Ring"
Parameters:
  -
  -
(C) NYUAD 2022

Version history:  
  Juan Villegas 2022/08/15: Initial Release
"""

import pya

from SiEPIC.utils import arc_to_waveguide, arc_wg, get_technology_by_name
     
class Ring(pya.PCellDeclarationHelper):
  def __init__(self):
    # Important: initialize the super class
    super(Ring, self).__init__()
    # declare the parameters
    TECHNOLOGY = get_technology_by_name('PRL_PDK')

    # declare the parameters
    self.param("layer", self.TypeLayer, "Waveguide Layer", default = TECHNOLOGY['Si'])
    self.param("width_bus", self.TypeDouble,  "Width Bus Waveguides", default = 1.0)
    self.param("width_ring", self.TypeDouble,  "Width Ring", default = 1.0)
    self.param("radius", self.TypeDouble, "Radius", default = 50)
    self.param("gap", self.TypeDouble, "Gap Through", default = 0.3)
    self.param("use_drop", self.TypeBoolean, "Use drop port", default = True)
    self.param("gap_drop", self.TypeDouble, "Gap Drop", default = 0.3)
    self.param("use_heater", self.TypeBoolean, "Insert Heater", default = False)
    self.param("layerM", self.TypeLayer, "Metal Layer", default = TECHNOLOGY['M1_heater'])
    self.param("widthM", self.TypeDouble,  "Metal Width", default = 3.0)
    self.param("round_end", self.TypeBoolean, "Use round ends", default = True)

    #Parametes for the Component MOdel
    self.param("use_GCM", self.TypeBoolean, "Use Generic Component Model", default = True)
    self.param("loss", self.TypeDouble,  "Loss (dB/cm)", default = 11.262)
    self.param("ne", self.TypeDouble,  "Effective Index (ne)", default = 2.253075)
    self.param("ng", self.TypeDouble,  "Group Index (ng)", default = 2.635705)
    self.param("dn", self.TypeDouble,  "Dispersion (dn/dw)", default = 400.0)
    
    # Following layers are relevant for SiEPIC
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("pinrecm", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRecM'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Ring_%s" % self.radius
  
  def coerce_parameters_impl(self):
    pass
        
  def produce_impl(self):
    from SiEPIC.utils import arc
    from SiEPIC.extend import to_itype
    from numpy import pi
    TECHNOLOGY = get_technology_by_name('Ligentec_AN800')
    
    if self.layout.technology_name == '':
        lv = pya.Application.instance().main_window().current_view()
        if lv == None:
          self.layout.technology_name = self.technology_name
          self.layout.dbu = 0.005
        else:
          self.layout.technology_name = lv.active_cellview().layout().technology_name
          self.layout.dbu = lv.active_cellview().layout().dbu
    ly = self.layout
    dbu = ly.dbu

    LayerWG = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerPinRecMN = ly.layer(self.pinrecm)
    LayerDevRecN = ly.layer(self.devrec)
    
    radius = to_itype(self.radius,dbu)
    width = to_itype(self.width_bus,dbu)
    width_ring = to_itype(self.width_ring,dbu)
    gap = to_itype(self.gap,dbu)
    gap_drop = to_itype(self.gap_drop,dbu)
    clearance = to_itype(5,dbu)

    wg_length = (radius + width)*2
    
    self.length = 2*pi*self.radius
    
    shapes = self.cell.shapes
    
    poly = pya.Polygon(arc(radius+width_ring/2, 0, 360))
    hole = pya.Polygon(arc(radius-width_ring/2, 0, 360))
    poly.insert_hole(hole.get_points())
    t = pya.Trans(pya.Trans.R0, wg_length/2, radius+gap+(width_ring+width)/2)
    self.cell.shapes(LayerWG).insert(poly.transformed(t))
    
    # Waveguide clearance 
    poly = pya.Polygon(arc(radius+clearance, 0, 360))
    hole = pya.Polygon(arc(radius-clearance, 0, 360))
    poly.insert_hole(hole.get_points())
    t = pya.Trans(pya.Trans.R0, wg_length/2, radius+gap+(width_ring+width)/2)
    clear_shapes = [poly.transformed(t)]
    
    # bus waveguides
    waveguide = pya.Box(0, -width/2, wg_length, width/2 ) 
    t = pya.Trans(pya.Trans.R0, 0, 0) 
    shapes(LayerWG).insert(waveguide.transformed(t))
    
    poly = pya.Box(0, -clearance, wg_length, clearance) 
    t = pya.Trans(pya.Trans.R0, 0, 0)
    clear_shapes += [poly.transformed(t)]
    
    y_drop = 2*radius+(width_ring+width)+gap+gap_drop
    
    if self.use_drop:
      t1 = pya.Trans(pya.Trans.R0, 0, y_drop)
      shapes(LayerWG).insert(waveguide.transformed(t1))
      clear_shapes += [poly.transformed(t)]
      
    proc = pya.EdgeProcessor()
    merged = proc.merge_to_polygon(clear_shapes,0, True,True)
    shapes(LayerDevRecN).insert(merged[0].transformed(t))
    
    
    # Create the pins on the waveguides, as short paths:
    from SiEPIC._globals import PIN_LENGTH as pin_length
    pin_length = pin_length*dbu/0.001 #PIN_LENGTH is sort of fixed for good only for dbu=0.001
    if pin_length <50:
      pin_length = 50
  
    # Heaters
    if self.use_heater:
      from numpy import pi, cos, sin, tan, arccos, linspace, flip
      m_angle = 60;
      LayerM = ly.layer(self.layerM)
      #shape = arc_wg(radius, to_itype(self.widthM,dbu), -m_angle, 180+m_angle, DevRec=None)
      #metal_shapes = [shape]
      m_width = to_itype(self.widthM,dbu);
      t = pya.Trans(pya.Trans.R0, wg_length/2, radius+gap+(width_ring+width)/2)
      e_angle = 90;
      pin_width = to_itype(15,dbu)

      arr = []            
      #x0_offset = to_itype(3.0*cos(m_angle/180*pi),dbu)
      x0 = int(radius*(cos(m_angle/180*pi)))# -int(x0_offset/2)
      y0 = -int(radius*(sin(m_angle/180*pi)))#+ int(m_width*cos(m_angle/180*pi))
      
      if (self.round_end):
          #Connection in the inpout
          arr0 = []
          npoints = 31
          dh = to_itype(20,dbu)/npoints;
          ang_v = linspace(90-m_angle,e_angle,npoints);
          xa = x0;
          ya = y0;
          for i in range(0,npoints):
            dx = dh*cos(ang_v[i]/180*pi)
            dy = dh*sin(ang_v[i]/180*pi)
            xa -= dx;
            ya -= dy;
            arr0.append(pya.Point(int(xa),int(ya) ))
            
          for i in range(1,npoints):
            arr.append(arr0[npoints-i])
          
          #Heater path
          npoints = 361
          ang_v = linspace(-m_angle,360-2*m_angle,npoints);
          for a  in ang_v:
             arr.append (pya.Point(radius*cos(a/180*pi), radius*sin(a/180*pi)))
          
          #Connection in the output
          npoints = 31
          ang_v = linspace(90-m_angle,e_angle,npoints);  
          xa = -x0;
          ya = y0;
          for i in range(0,npoints):
            dx = dh*cos(ang_v[i]/180*pi)
            dy = dh*sin(ang_v[i]/180*pi)
            xa += dx;
            ya -= dy;
            arr.append(pya.Point(int(xa),int(ya) ))
          metal_shapes = [pya.Path(arr, m_width).polygon()]   
          
          x_pin =    arr[-1].x 
          y_pin =    arr[-1].y-int(pin_width/2)+int(m_width/2)
          #Taper
          metal_shapes += [pya.Polygon([  
            pya.Point(arr[-1].x+int(m_width/2),arr[0].y), pya.Point(arr[-1].x-int(m_width/2),arr[0].y),  
            pya.Point(arr[-1].x-int(pin_width/2),y_pin), pya.Point(arr[-1].x+int(pin_width/2),y_pin) ])]
          metal_shapes += [pya.Polygon([  
            pya.Point(arr[0].x+int(m_width/2),arr[0].y), pya.Point(arr[0].x-int(m_width/2),arr[0].y),  
            pya.Point(arr[0].x-int(pin_width/2),y_pin), pya.Point(arr[0].x+int(pin_width/2),y_pin) ])]
          
         
      else:
          
          x0_offset = to_itype(3.0*cos(m_angle/180*pi),dbu)
          x0 = int(radius*(cos(m_angle/180*pi))) - int(x0_offset/2)
          y0 = -int(radius*(sin(m_angle/180*pi))) + int(m_width*cos(m_angle/180*pi))
          x1 = x0 + pin_width
          b_angle = arccos(x1/radius)
          y1 = -int(radius*(sin(b_angle)))-m_width/2
          y2 = y0-to_itype(3.0,dbu)
          
          shape = arc_wg(radius, to_itype(self.widthM,dbu), -m_angle, 180+m_angle, DevRec=None)
          metal_shapes = [shape]
          
          metal_shapes += [pya.Polygon([ pya.Point(-x0,y0),  pya.Point(-x1,y0),pya.Point(-x1,y1) ])]
          metal_shapes += [pya.Polygon([ pya.Point(-x0,y0),  pya.Point(-x1,y0),pya.Point(-x1,y2), pya.Point(-x0,y2) ]), ]
          metal_shapes += [pya.Polygon([ pya.Point(x0,y0),  pya.Point(x1,y0),pya.Point(x1,y1) ])]
          metal_shapes += [pya.Polygon([ pya.Point(x0,y0),  pya.Point(x1,y0),pya.Point(x1,y2), pya.Point(x0,y2)])]
          
          x_pin =    x0+int(pin_width/2)
          y_pin =    y2
       
      merged = proc.merge_to_polygon(metal_shapes,0, True,True)
      shapes(LayerM).insert(merged[0].transformed(t))
      
      #Electrical pins
      t_pin = pya.Trans(t, -x_pin,y_pin)
      if LayerM == ly.layer(TECHNOLOGY['P1P']):
          #Draw connection to P1R and VIAS, and PINS for P1R
          pass
      else:
          #Draw Metal Pins
          pin = pya.Path([ pya.Point(0,-pin_length/2),  pya.Point(0,pin_length/2)], pin_width)
          text_size = 0.4/dbu
          
      shapes(LayerPinRecMN).insert(pin.transformed(t_pin))
      text =  pya.Text ("1ele1", t_pin)
      shape = shapes(LayerPinRecMN).insert(text)
      shape.text_size = text_size
      shape.text_halign = -1
      
      t_pin = pya.Trans(t, x_pin,y_pin)
      shapes(LayerPinRecMN).insert(pin.transformed(t_pin))
      text =  pya.Text ("ele2", t_pin)
      shape = shapes(LayerPinRecMN).insert(text)
      shape.text_size = text_size
      shape.text_halign = -1
      
    else:
      #Generic Empty Electrical pins
      pin = pya.Path([ pya.Point(0,0),  pya.Point(0,0)], width)
      t_pin = pya.Trans(pya.Trans.R0, 0,0)
      text_size = 0.01/dbu       
    
      shapes(LayerPinRecMN).insert(pin.transformed(t_pin))
      text =  pya.Text ("1ele1", t_pin)
      shape = shapes(LayerPinRecMN).insert(text)
      shape.text_size = text_size
      shape.text_halign = -1
    
    # Pins
    pin = pya.Path([ pya.Point(pin_length/2,0),  pya.Point(-pin_length/2,0)], width)
    
    shapes(LayerPinRecN).insert(pin.transformed(pya.Trans(pya.Trans.R0, 0, 0)))
    text =  pya.Text ("0opt1", (pya.Trans(pya.Trans.R0, 0, 0)))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = -1
    
    # second Pin is electrical for comaptibility with standard ring model in interconnet
    
    shapes(LayerPinRecN).insert(pin.transformed(pya.Trans(pya.Trans.R180, wg_length, 0)))
    text =  pya.Text ("2opt2",pya.Trans(pya.Trans.R0, wg_length, 0))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = 1
    
    
    if self.use_drop:
      shapes(LayerPinRecN).insert(pin.transformed(pya.Trans(pya.Trans.R0, -0, y_drop)))
      text =  pya.Text ("3opt3", pya.Trans(pya.Trans.R0, -0, y_drop))
      shape = shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu
      shape.text_halign = -1
      
      shapes(LayerPinRecN).insert(pin.transformed(pya.Trans(pya.Trans.R180, wg_length, y_drop)))
      text =  pya.Text ("4opt4", pya.Trans(pya.Trans.R0, wg_length, y_drop))
      shape = shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu
      shape.text_halign = 1
    
    
    
    # Compact model information
    # Waveguide infpo from MODE simulation
    # TE: n_eff = 2.253075   n_g = 2.635705   dn/dlambda = 400 ps/nm/km   loss = 11.262 dB/cm (220 x 500 nm Silicon Waveguides)
    # TE: n_eff = 1.7482   n_g = 2.12186   dn/dlambda = 10 ps/nm/km   loss = 0.2 dB/cm (800 x 1000 Silicon Nitride Waveguides)
    
    
    text_heigth =  0.2/dbu
    t =  pya.Trans( pya.Trans.R0, 0, -text_heigth*4)
    text =  pya.Text ('Lumerical_INTERCONNECT_library=Modulators/Optical', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = text_heigth
    
    t =  pya.Trans( pya.Trans.R0, 0, -text_heigth*6)
    if self.use_GCM:
      text =  pya.Text ('Component="Optical Ring Modulator"', t)
    else:
      text =  pya.Text ('Component=NA', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = text_heigth
    
    t =  pya.Trans( pya.Trans.R0, 0, -text_heigth*8)
    if self.use_GCM:
      if not self.use_drop:
        text =  pya.Text ('Spice_param:"length"= %.3fu "loss"=%.3f "effective index"=%.3f "group index"=%.3f "dispersion"=%.3f'%(
                          self.length, self.loss, self.ne, self.ng, self.dn), t)
      else:
        text =  pya.Text ('Spice_param:"length"= %.3fu "loss"=%.3f "effective index"=%.3f "group index"=%.3f "dispersion"=%.3f'%(
                          self.length, self.loss, self.ne, self.ng, self.dn), t)
    else:
      text =  pya.Text ('Spice_param: NA',t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = text_heigth
         
    return
