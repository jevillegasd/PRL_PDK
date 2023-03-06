"""
PRL PDK Component - Taper (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "Taper"
Parameters:
  -
  -
(C)  NYUAD 2023

Version history:  
  Juan Villegas 2022/08/15: Initial Release
"""

import pya
from SiEPIC.utils import get_technology_by_name
    
class Taper(pya.PCellDeclarationHelper):

  def __init__(self):
    super(Taper, self).__init__()
    TECHNOLOGY = get_technology_by_name('PRL_PDK')
    self.param("waveguide", self.TypeLayer, "Waveguide Layer", default = TECHNOLOGY['X1P'])
    self.param("w_01", self.TypeDouble, "Input Width", default = 1.0)
    self.param("w_02", self.TypeDouble, "Output Width", default = 2.0)
    self.param("length", self.TypeDouble, "Taper Length", default = 20.0)
    
    # Following parameters are importnat for DRCs
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_Taper(L= %.3f, w0=%.1f, w1=%.1f)"%(self.length, self.w_01, self.w_02)
  
  def coerce_parameters_impl(self):
    pass
    # TODO: use x to access parameter x and set_x to modify it's value 
  
  def produce_impl(self):
    from SiEPIC.extend import to_itype
    TECHNOLOGY = get_technology_by_name('PRL_PDK')
    dbu = self.layout.dbu
    shapes = self.cell.shapes
    w1 =  to_itype(self.w_01,dbu)
    w2 =  to_itype(self.w_02,dbu)
    
    Layer = self.layout.layer(self.waveguide)
    LayerPinRecN = self.layout.layer(self.pinrec)
    LayerDevRecN = self.layout.layer(self.devrec)
    
    y0 = to_itype(self.w_01/2,dbu)
    x1 = to_itype(self.length,dbu)
    y1 = to_itype(self.w_02/2,dbu)
    # Create Polygon Structure
    p1 = pya.Point(0,y0)
    p2 = pya.Point(x1, y1)
    p3 = pya.Point(x1, -y1)
    p4 = pya.Point(0, -y0)
    
    poly_p = [p1,p2,p3,p4]
    taper_shape = pya.Polygon(poly_p)
    t = pya.Trans(pya.Trans.R0,0,0)
    shapes(Layer).insert(taper_shape.transformed(t))
    
    # Create PINS
    from SiEPIC._globals import PIN_LENGTH as pin_length
    if pin_length <20:
      pin_length = 20
      
    # Pin on the left
    p1 = [pya.Point(pin_length/2, 0), -pya.Point(pin_length/2,0)]
    pin = pya.Path(p1, w1)
    shapes(LayerPinRecN).insert(pin)
    shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(0,False, 0,0)))
    
    # Pin on the rigth
    p2 = [pya.Point(x1-pin_length/2, 0), pya.Point(x1+pin_length/2,0)]
    pin = pya.Path(p2, w2)
    shapes(LayerPinRecN).insert(pin)
    shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(0,False, self.length/dbu,0)))
    
    # Create the device recognition layer, wg_width away from the waveguides.
    self.cell.shapes(LayerDevRecN).insert(pya.Box(0,-self.w_02/dbu/2-1000, self.length/dbu,self.w_02/dbu/2+1000))
      
    # Add text description and Compact Model (CML) information 
    TextSize = 500
    shape = shapes(LayerDevRecN).insert(pya.Text ("Lumerical_INTERCONNECT_library=", pya.Trans(pya.Trans.R0,0, -TextSize)))
    shape.text_size = TextSize
    
    shape = shapes(LayerDevRecN).insert(pya.Text ('Component=', pya.Trans(pya.Trans.R0,0, -TextSize*3)))
    shape.text_size = TextSize

    shape = shapes(LayerDevRecN).insert( pya.Text ('Spice_param:', pya.Trans(pya.Trans.R0,0, -TextSize*5)))
    shape.text_size = TextSize

    return