"""
PRL PDK Component - MMI (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "MMI", that generates a parametric multimode interferometer.
Parameters:
  -
  -
(C) NYUAD 2023

Version history:  
  Juan Villegas 2022/08/16: Initial Release

import pya
from SiEPIC.utils import get_technology_by_name
  
"""
import pya
from SiEPIC .utils import get_technology_by_name

class MMI(pya.PCellDeclarationHelper):
  def __init__(self):
    super(MMI, self).__init__()
    self.technology_name = 'PRL_PDK'
    TECHNOLOGY = get_technology_by_name(self.technology_name)
    
    # Load waveguide types as parameters
    #from SiEPIC.utils import load_Waveguides_by_Tech
    #self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)
    #p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default = self.waveguide_types[0]['name'])
    #for wa in self.waveguide_types:
    #    p.add_choice(wa['name'],wa['name'])
    
    
    self.param("wg_width"   , self.TypeDouble, "Waveguide Width", default = 1.0, hidden = False)
    self.param("num_inp"    , self.TypeInt, "Number of inputs", default = 2)           
    self.param("num_out"    , self.TypeInt, "Number of outputs", default = 2)     
    self.param("mmi_width"  , self.TypeDouble, "MMI width", default = 6.0)
    self.param("mmi_length" , self.TypeDouble, "MMI length", default = 20.0)
    
    self.param("input_spacing", self.TypeDouble, "Input Spacing", default =1.2)
    self.param("output_spacing", self.TypeDouble, "Output Spacing", default =2.0)
   
    self.param("taper_length", self.TypeDouble, "Port taper length", default = 3.0)
    self.param("taper_width", self.TypeDouble, "Port taper end width", default = 1.2)
    
    self.param("layer_wg"   , self.TypeLayer, "Waveguide Layer", default = TECHNOLOGY['Si'])
    # Following layers are relevant for DRCs
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    
    #Hidden params
    #self.param("wg_width", self.TypeDouble, "Waveguide Width", default = 1.0, hidden = True)

    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "MMI %sx%s, Len:%s-Width:%.3f" % \
    (self.num_inp,self.num_out, self.mmi_length, self.mmi_width)
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
    ly = self.layout
    dbu = self.layout.dbu
    shapes = self.cell.shapes
    TECHNOLOGY = get_technology_by_name('PRL_PDK')
    Layer = ly.layer(self.layer_wg)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    
    # Create port tapers
    p1 = pya.Point(0, self.wg_width/dbu/2)
    p2 = pya.Point(self.taper_length/dbu, self.taper_width/dbu/2)
    p3 = pya.Point(self.taper_length/dbu, -self.taper_width/dbu/2)
    p4 = pya.Point(0, -self.wg_width/dbu/2)
    
    poly_p = [p1,p2,p3,p4]
    taper_shape = pya.Polygon(poly_p)
    t = pya.Trans(pya.Trans.R0,0,0)
    
    from SiEPIC._globals import PIN_LENGTH as pin_length

    w = self.wg_width/dbu
    input_spacing = self.input_spacing/dbu
    output_spacing = self.output_spacing/dbu
    
    pin = pya.Path([ pya.Point(pin_length/2,0),  pya.Point(-pin_length/2,0)], w)
    
    for i in range(0, self.num_inp):
      t = pya.Trans(pya.Trans.R0,0,(i*(input_spacing + w)))
      shapes(Layer).insert(taper_shape.transformed(t))
      
      # Pins on the inputs:
      shapes(LayerPinRecN).insert(pin.transformed(t))
      text =  pya.Text ("opt%s"%(i+1), t)
      shape = shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu
      shape.text_halign = -1
    
    y_c = (self.num_inp-1)*(input_spacing + w)/2
    y_out0 = y_c - (self.num_out-1)*(output_spacing + w)/2
    
    for i in range(0, self.num_out):
      t = pya.Trans(pya.Trans.R180,(self.taper_length*2 +  self.mmi_length)/dbu,y_out0 + i*(output_spacing + w))
      shapes(Layer).insert(taper_shape.transformed(t)) 
    
      # Pins on the outputs:
      shapes(LayerPinRecN).insert(pin.transformed(t))
      text =  pya.Text ("opt%s"%(i+ self.num_inp+1), t*pya.Trans.R180)
      shape = shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu
      shape.text_halign = 2
    
    core = pya.Box(self.taper_length/dbu,y_c - (self.mmi_width/2)/dbu,self.taper_length/dbu +  self.mmi_length/dbu, y_c + (self.mmi_width/2)/dbu)
    shapes(Layer).insert(core)
    
    #Device recognition
    core = pya.Box(0,y_c-(self.mmi_width/2)/dbu,self.taper_length/dbu*2 +  self.mmi_length/dbu, y_c+(self.mmi_width/2)/dbu)
    shapes(LayerDevRecN).insert(core)
    
    # Compact model information
    text_heigth =  0.2/dbu
    t =  pya.Trans( pya.Trans.R0, 0, -text_heigth*4)
    text =  pya.Text ('Lumerical_INTERCONNECT_library=Design kits/NA', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = text_heigth
    t =  pya.Trans( pya.Trans.R0, 0, -text_heigth*6)
    text =  pya.Text ('Component=NA', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = text_heigth
    t =  pya.Trans( pya.Trans.R0, 0, -text_heigth*8)
    text =  pya.Text ('Spice_param:NA', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = text_heigth
    
    return