"""
PRL PDK Component - Ring (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "SBend"
Parameters:
  -
  -
(C) NYUAD 2023

Version history:  
  Juan Villegas 2022/08/15: Initial Release
"""

from . import *
from pya import *
import pya

from SiEPIC.utils import get_technology_by_name


class SBend(pya.PCellDeclarationHelper):
  """
  Input: 
  """
  def __init__(self):


    # Important: initialize the super class
    super(SBend, self).__init__()
    TECHNOLOGY = get_technology_by_name('PRL_PDK')

    # declare the parameters
    self.param("length", self.TypeDouble, "Waveguide length", default = 20.0)     
    self.param("height", self.TypeDouble, "Waveguide offset height", default = 4.0)     
    self.param("wg_width", self.TypeDouble, "Waveguide width (microns)", default = 1.0)       
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Si'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])


  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_SBend_%s-%.3f" % \
    (self.length, self.wg_width)
  
  def coerce_parameters_impl(self):
    pass


  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
  
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    from SiEPIC.utils.layout import layout_waveguide_sbend, layout_waveguide_sbend_bezier

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    length = self.length / dbu
    w = self.wg_width / dbu
    h = self.height / dbu
   
#    waveguide_length = layout_waveguide_sbend(self.cell, LayerSiN, pya.Trans(Trans.R0, 0,0), w, r, h, length)
    waveguide_length = layout_waveguide_sbend_bezier(self.cell, LayerSiN, Trans(), w*dbu, w*dbu, h*dbu, length*dbu) / dbu
    
    from SiEPIC._globals import PIN_LENGTH as pin_length

    # Pins on the waveguide:
    x = length
    t = Trans(Trans.R0, x,h)
    pin = Path([Point(-pin_length/2,0), Point(pin_length/2,0)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = 2

    x = 0
    t = Trans(Trans.R0, x,0)
    pin = Path([Point(pin_length/2,0), Point(-pin_length/2,0)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu


    # Compact model information
    t = Trans(Trans.R0, 0, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/LIGENTEC_PDK', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, w*2)
    text = Text ('Component=LGT_Sine_bend', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, -w*2)
    text = Text \
      ('Spice_param:x_length=%.3fu jog=%.3fu width=%.3fu "delay compensation"=%.1f' %\
      (self.length, self.height, self.wg_width, 0.0), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
#    t = Trans(Trans.R0, 0, -w*3)
#    text = Text ('Extra length = %.4fu, Shortest length = %.4fu' % (straight_l*dbu, (length-2*straight_l)*dbu), t )
#    shape = shapes(LayerDevRecN).insert(text)
#    shape.text_size = 0.1/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    box1 = Box(0, min(-w*3,h-w*3), length, max(w*3,h+w*3))
    shapes(LayerDevRecN).insert(box1)
    
#    print('2020/11/28 update')