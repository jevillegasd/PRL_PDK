"""
PRL PDK Component - Taper (Compatible with SiEPIC tools)
Notice: Information in this file is confidential.
Based on work of the SiEPIC project

Description:
This Python file implements a parameteric cell called "Waveguide". This is the base cell for all waveguides in the technology
Parameters:
  -
  -
(C) NYUAD 2023

Version history:  
  Juan Villegas 2022/09/01: Initial Release
"""

import pya
class Waveguide(pya.PCellDeclarationHelper):

  def __init__(self):
    super(Waveguide, self).__init__()
    
    from SiEPIC.utils import get_technology, get_technology_by_name, load_Waveguides_by_Tech
    self.technology_name = 'PRL_PDK'
    
    self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)   
    
    # declare the parameters
    p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default = self.waveguide_types[0]['name'])
    for wa in self.waveguide_types:
        p.add_choice(wa['name'],wa['name'])
    self.param("path", self.TypeShape, "Path", default = pya.DPath([pya.DPoint(0,0), pya.DPoint(10,0), pya.DPoint(10,10)], 0.5))
    self.param("dbu", self.TypeDouble, "dbu", default = 0.001, hidden = True)
    self.cellName="Waveguide"
    
  def display_text_impl(self):
    return "%s_%s" % (self.cellName, self.path)
  
  def coerce_parameters_impl(self):
    self.layout.cleanup([])  
    pass
                      
  def can_create_from_shape_impl(self):
    return self.shape.is_path()
  
  def transformation_from_shape_impl(self):
    return Trans(Trans.R0,0,0)
  
  def parameters_from_shape_impl(self):
    self.path = self.shape.path
  
  def produce_impl(self):
    
    from SiEPIC.utils.layout import layout_waveguide4
    
    if self.layout.technology_name == '':
        lv = pya.Application.instance().main_window().current_view()
        if lv == None:
          self.layout.technology_name = self.technology_name
          self.layout.dbu = 0.005
        else:
          ly = lv.active_cellview().layout()
          self.layout.technology_name = ly.technology_name
          self.layout.dbu = ly.dbu
              
    self.waveguide_length = layout_waveguide4(self.cell, self.path, self.waveguide_type, debug=True)*1e-6;
    
    
    #Modify SPICE parameters
    from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech
    component = self.cell.find_components()[0];
    component.TECHNOLOGY = get_technology_by_name(self.technology_name)
    
    waveguide_types = load_Waveguides_by_Tech(self.technology_name)   
    width = 0
    for wg_type in self.waveguide_types:
       width = float(wg_type['width'])*1e-6 if wg_type['name'] == self.waveguide_type else width
    
    std_param = component.params_dict()
    params = {}
    
    # In SiEPIC version 0.3.92, to measure waveguide length the first SPICE param needs to be the length
    params['wg_length'] = ('%2.6E'%(self.waveguide_length))
    params['width'] = ('%2.4E'%width)
    params['delay compensation'] = 0
    
    #from . import tii_tools
    #tii_tools.set_SPICE_params(component, params) 
    set_SPICE_params(component, params) 
    
    print("PRL_PDK.%s: length %s um, complete" % (self.cellName, self.waveguide_length*1e6))

def set_SPICE_params(component, arg, verbose = False):
      def pdic2str(arg): #A Dictionary of SPICE parameters to a string
        str_ = ''
        keys = list(arg.keys())
        for i in range(0, len(arg)):
              if keys[i].find(' ',0)==-1:
                str_ += keys[i] + '=' + str(arg[keys[i]])
              else:
                str_ += '"'+ keys[i] +'"'+ '=' + str(arg[keys[i]])
                
              if i < len(arg) - 1: str_ +=  ' '
        return str_
      
      if isinstance(arg, str):
          spice_str = arg.replace('Spice_param:', '', 1)
      elif isinstance(arg, dict):
          spice_str = pdic2str(arg)
      else:
        return False
      newSPICE_text =  "Spice_param:" + spice_str;  
      
      cell = component.cell
      cell_idx = cell.cell_index()
      
      ly = cell.layout()
      LayerDevRecN  = ly.layer(component.TECHNOLOGY['DevRec']) 
      iter_sh = cell.begin_shapes_rec(LayerDevRecN)

      while not(iter_sh.at_end()): # Find cell where SPICE params are stored
          if iter_sh.shape().is_text():
            shape = iter_sh.shape();
            text = shape.text
            if text.string.find("Spice_param:") > -1:
                new_text = pya.Text(newSPICE_text, shape.text_trans,shape.text_size ,-1);
                new_text.halign = text.halign
                shape.text = new_text
                component.params = spice_str
                return True
          iter_sh.next()
          
      if cell._is_const_object():
          cell_inst = cell.layout().cell(cell_idx) # Need to do this to avoid error (See KLayout issue #235)
      else:
          cell_inst = cell

      t = pya.Trans(pya.Trans.R0,pya.Point(0,0)) # Coordinates are with respect to the cell center
      new_text  = pya.Text(newSPICE_text, t,0.1/ly.dbu ,-1);
      cell_inst.shapes(LayerDevRecN).insert(new_text)
      component.params = spice_str
      return True