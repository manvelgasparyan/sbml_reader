import numpy , libsbml, os, math, re, sys, tkinter, sympy, json
from tkinter import filedialog, simpledialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QSizePolicy
from PyQt5.QtGui import QFont
#==========================================================================================================================================
#==========================================================================================================================================
numpy.set_printoptions(threshold=numpy.inf)     #Adjust NumPy display settings to print the entire array without truncation
bold = "\033[1m"     #ANSI escape code for bold text
reset = "\033[0m"    #Reset ANSI escape code
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function can be used to read of an SBML file. Upon execution, it 
initiates a dialog prompting the user to select the desired SBML file for 
reading. The output comprises both the model and the file path.
"""
root = tkinter.Tk()
root.withdraw()  
def read_sbml_file():
    try:
        file_path = filedialog.askopenfilename(
            parent=root,
            title="Select SBML file",
            filetypes=[("All files", "*.*")]
        )
        if not file_path:
            print("No file selected.")
            return None, None
        
        reader = libsbml.SBMLReader()
        document = reader.readSBMLFromFile(file_path)
        if document.getNumErrors() > 0:
            print("Encountered the following SBML errors:")
            document.printErrors()
            return None, None
        
        model = document.getModel()
        file_name = os.path.splitext(os.path.basename(file_path))[0] 
        return model, file_path, file_name
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the title and the data, and visualizes the table.
"""
class DataTableWindow(QMainWindow):  
    #---
    def __init__(self, title, data):
        super().__init__()

        self.title = title
        self.data = data
        self.initUI()
    #--- 
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 800, 600)

        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(len(self.data))
        self.tableWidget.setHorizontalHeaderLabels(list(self.data.keys()))
        self.tableWidget.setRowCount(len(self.data[next(iter(self.data))]))

        for i, key in enumerate(self.data):
            for j, value in enumerate(self.data[key]):
                self.tableWidget.setItem(j, i, QTableWidgetItem(str(value)))

        self.scrollArea = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollArea)
        self.scrollLayout.addWidget(self.tableWidget)

        # Set central widget and scroll area's size policy to ignore the size hint
        self.scrollArea.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.setCentralWidget(self.scrollArea)

        self.resizeColumnsToContents()
    #---
    def resizeColumnsToContents(self):
        for i in range(self.tableWidget.columnCount()):
            self.tableWidget.resizeColumnToContents(i)
#---
app = QApplication.instance()  # Check if QApplication instance already exists
if not app:
    app = QApplication(sys.argv)  # If not, create a new instance
#---
def get_table(title, data):
    # Set application font to system font
    font = QFont()
    font.setPointSize(14)  # Set the font size as per your preference
    app.setFont(font)

    window = DataTableWindow(title, data)
    window.show()
    app.exec_()
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the information 
about model species as output.
"""
def get_model_species (model):
    #---    
    #Species ID
    buffered_species_id = [species.getId() for species in model.getListOfSpecies() if species.getConstant()]
    #Buffered species names
    buffered_species_names = [species.getName() for species in model.getListOfSpecies() if species.getConstant()]
    #---
    #Intial species ID
    species_id = [species.getId() for species in model.getListOfSpecies()]
    species_id = [item for item in species_id if item not in buffered_species_id]
    #Species Names
    species_names = [species.getName() for species in model.getListOfSpecies()]
    species_names = [item for item in species_names if item not in buffered_species_names]
    #---
    #Get the vector of initial concentrations
    initial_concentrations_ox = [model.getSpecies(id).getInitialConcentration() for id in species_id]
    initial_amounts_ox = [model.getSpecies(id).getInitialAmount() for id in species_id]
    #initial_concentrations = [initial_amounts_ox[i] if initial_amounts_ox[i] != 0 else initial_concentrations_ox[i] for i in range(len(species_id))]
    initial_concentrations = [initial_amounts_ox[i] if initial_amounts_ox[i] != 0 and not math.isnan(initial_amounts_ox[i]) else initial_concentrations_ox[i] for i in range(len(species_id))]
    #---
    #Values of Buffered species
    buffered_concentrations_ox = [species.getInitialConcentration() for species in model.getListOfSpecies() if species.getConstant()]
    buffered_amounts_ox = [species.getInitialAmount() for species in model.getListOfSpecies() if species.getConstant()]
    buffered_concentrations = [buffered_amounts_ox[i] if buffered_amounts_ox[i] != 0 and not math.isnan(buffered_amounts_ox[i]) else buffered_concentrations_ox[i] for i in range(len(buffered_species_id))]
    #---
    return species_id, species_names, buffered_species_id, buffered_species_names, initial_concentrations, buffered_concentrations
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the information 
about model reactions as output.
"""
def get_model_reactions (model):
    #---
    #Buffered species
    _, _, buffered_species_id, buffered_species_names, _, _ = get_model_species (model)
    #---
    #The reaction IDs
    reactions_id = [reaction.getId() for reaction in model.getListOfReactions()]
    #---
    #The reaction names
    reactions_names = [reaction.getName() for reaction in model.getListOfReactions()]
    #---
    reactions_info_species_name = []
    for reaction in model.getListOfReactions():
        react = " + ".join([f"{s.getStoichiometry()}*{model.getSpecies(s.getSpecies()).getName()}" for s in reaction.getListOfReactants()])
        prod = " + ".join([f"{s.getStoichiometry()}*{model.getSpecies(s.getSpecies()).getName()}" for s in reaction.getListOfProducts()])
        direction = "<--->" if reaction.getReversible() else "--->"
        reactions_info_species_name.append(f"{react} {direction} {prod}")
    #---
    reactions_info_species_id = []
    for reaction in model.getListOfReactions():
        react = " + ".join([f"{s.getStoichiometry()}*{model.getSpecies(s.getSpecies()).getId()}" for s in reaction.getListOfReactants()])
        prod = " + ".join([f"{s.getStoichiometry()}*{model.getSpecies(s.getSpecies()).getId()}" for s in reaction.getListOfProducts()])
        direction = "<--->" if reaction.getReversible() else "--->"
        reactions_info_species_id.append(f"{react} {direction} {prod}")    
    #---
    return reactions_id, reactions_names, reactions_info_species_id, reactions_info_species_name
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the information 
about model parameters and the model compartments as output.
"""
def get_model_parameters (model):
    #---
    #Get the list of global parameters 
    parameter_id = [parameter.getId() for parameter in model.getListOfParameters()]
    #---
    parameter_values = [parameter.getValue() for parameter in model.getListOfParameters()]
    #---
    #Get the list of parameters from reaction kinetics
    kinetic_parameter_id = [parameter.getId() for i in range(model.getNumReactions()) 
                                    for j in range(model.getReaction(i).getKineticLaw().getNumParameters()) 
                                        if model.getReaction(i).getKineticLaw() is not None
                                            for parameter in model.getReaction(i).getKineticLaw().getListOfParameters()]
    #---
    kinetic_parameter_values = [parameter.getValue() for i in range(model.getNumReactions()) 
                                                  for j in range(model.getReaction(i).getKineticLaw().getNumParameters()) 
                                                      if model.getReaction(i).getKineticLaw() is not None
                                                          for parameter in model.getReaction(i).getKineticLaw().getListOfParameters()]
    #---
    #Combine the parameters
    parameter_id.extend(kinetic_parameter_id)
    parameter_values.extend(kinetic_parameter_values)
    #---    
    #Get the compartments and their size
    compartment_id = [compartment.getId() for compartment in model.getListOfCompartments()]
    compartment_size = [model.getCompartment(i).getSize() for i in range(model.getNumCompartments())]
    #---
    return parameter_id, parameter_values, compartment_id, compartment_size
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the information 
about model functions as output.
"""
def get_model_functions (model):
    #---
    def extract_arguments(Inside):
        Arguments = []

        #Function to check if a character is a mathematical symbol
        def is_math_symbol(char):
            return char in ('+', '-', '*', '/', '^', '(', ')')

        #Loop until a mathematical symbol is encountered
        while Inside:
              #Find the index of the first comma
              comma_index = Inside.find(',')

              #If there is no comma or the comma is at the start, break the loop
              if comma_index == -1 or comma_index == 0:
                 break

              #Extract the part before the first comma
              part = Inside[:comma_index].strip()

              #If the part contains a mathematical symbol, break the loop
              if any(is_math_symbol(c) for c in part):
                 break

              #Add the part to Arguments and remove it from Inside along with the comma
              Arguments.append(part)
              Inside = Inside[comma_index+1:].strip()
        return Arguments, Inside
    #---
    #Get the list of functions in the model
    function_id_list = []
    function_list = []
    #---
    for i in range(model.getNumFunctionDefinitions()):
        function = model.getFunctionDefinition(i)
        function_id = function.getId()
        math_ast = function.getMath()
        math_string = libsbml.formulaToString(math_ast)
        function_id_list.append(function_id)
        function_list.append(math_string)
    #---
    arguments = []
    expressions = []
    for i in range(len(function_id_list)):
        #---
        inside_parentheses_i = re.search(r'lambda\((.*)\)', function_list[i]).group(1)
        #print("Inside parantheses:", inside_parentheses_i)
        #---
        arguments_i, expression_i = extract_arguments(inside_parentheses_i)
        #---
        arguments.append(arguments_i)
        expressions.append(expression_i)
        #---
    return function_id_list, function_list, arguments, expressions
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the information 
about model reaction rates as output.
"""
def get_model_rates_1 (model):
    #---
    #Get the species
    species_id, species_names, buffered_species_id, buffered_species_names, _, _ = get_model_species(model)
    #---
    #Species Ids
    species_ids = species_id + buffered_species_id
    #---
    #Species Names
    species_names = species_names + buffered_species_names
    #---
    reaction_rate_species_ID = []
    for reaction in model.getListOfReactions():
        reaction_rate_formula = reaction.getKineticLaw().getFormula() if reaction.getKineticLaw() else None
        if reaction_rate_formula:
           reaction_rate_species_ID.append(reaction_rate_formula)  
    #---
    reaction_rate_species_Names = reaction_rate_species_ID.copy()
    for i, formula in enumerate(reaction_rate_species_Names):
        for species_id, species_name in zip(species_ids, species_names):
            formula = formula.replace(species_id, species_name)
        reaction_rate_species_Names[i] = formula
    #---
    return reaction_rate_species_ID, reaction_rate_species_Names
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function replaces the functions in reaction rates with the 
corresponding expressions
"""
def get_model_rates_2(model):
    #---
    function_id, _, arguments, expressions = get_model_functions(model)
    #---
    reaction_rate_species_ID, reaction_rate_species_Names = get_model_rates_1 (model)
    #---
    reaction_rate_species_ID_new = reaction_rate_species_ID.copy()
    reaction_rate_species_Names_new = reaction_rate_species_Names.copy()
    #---
    for j in range(len(reaction_rate_species_ID_new)):
        #---
        f_j =  [[func, re.search(re.escape(func) + r'\((.*?)\)', reaction_rate_species_ID_new[j]).group(1)] for func in function_id if re.search(re.escape(func) + r'\((.*?)\)', reaction_rate_species_ID_new[j])]
        for i in range(len(f_j)):
            elem_ji = f_j[i]
            #---
            new_id = elem_ji[0]
            new_args = elem_ji[1].split(',')
            new_name = new_id+ '(' + ','.join(new_args) + ')'
            #---
            old_arg = arguments[function_id.index(new_id)]
            old_expres = expressions[function_id.index(new_id)]
            #---
            new_expess = old_expres
            for z in range(len(old_arg)):
                new_expess = new_expess.replace(old_arg[z], new_args[z]) 
            #---
            reaction_rate_species_ID_new[j] = reaction_rate_species_ID_new[j].replace(new_name, new_expess)     
    #---
    for j in range(len(reaction_rate_species_Names_new)):
        #---
        f_j =  [[func, re.search(re.escape(func) + r'\((.*?)\)', reaction_rate_species_Names_new[j]).group(1)] for func in function_id if re.search(re.escape(func) + r'\((.*?)\)', reaction_rate_species_Names_new[j])]
        for i in range(len(f_j)):
            elem_ji = f_j[i]
            #---
            new_id = elem_ji[0]
            new_args = elem_ji[1].split(',')
            new_name = new_id+ '(' + ','.join(new_args) + ')'
            #---
            old_arg = arguments[function_id.index(new_id)]
            old_expres = expressions[function_id.index(new_id)]
            #---
            new_expess = old_expres
            for z in range(len(old_arg)):
                new_expess = new_expess.replace(old_arg[z], new_args[z]) 
            #---
            reaction_rate_species_Names_new[j] = reaction_rate_species_Names_new[j].replace(new_name, new_expess)     
    #---
    return reaction_rate_species_ID_new, reaction_rate_species_Names_new
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the stoichiometric 
matrix as output.
"""
def get_stoichiometric_matrix (model):
    reactions = model.getListOfReactions()
    metabolites = model.getListOfSpecies()
    metabolite_indices = {met.getId(): i for i, met in enumerate(metabolites)}
    num_metabolites = len(metabolites)
    num_reactions = len(reactions)
    stoichiometric_matrix = numpy.zeros((num_metabolites, num_reactions))
    for i, reaction in enumerate(reactions):
        for reactant in reaction.getListOfReactants():
            metabolite_id = reactant.getSpecies()
            coeff = reactant.getStoichiometry()
            stoichiometric_matrix[metabolite_indices[metabolite_id], i] -= coeff
        for product in reaction.getListOfProducts():
            metabolite_id = product.getSpecies()
            coeff = product.getStoichiometry()
            stoichiometric_matrix[metabolite_indices[metabolite_id], i] += coeff
    #---
    buffered_species_id = [species.getId() for species in model.getListOfSpecies() if species.getConstant()]
    buffered_indices_list = [buffered_species_id.index(string) for string in buffered_species_id]
    stoichiometric_matrix = numpy.delete(stoichiometric_matrix, buffered_indices_list, axis=0)
    #---        
    return stoichiometric_matrix
#==========================================================================================================================================
#==========================================================================================================================================
"""
This Python function takes the model as input and returns the model as a system 
of ordinary differential equations as output.
"""
def get_ode_model_sym (model):
    #---
    stoichiometric_matrix = get_stoichiometric_matrix (model)
    #---
    species_id, _, buffered_species_id, _, _, _ = get_model_species (model) 
    #---
    reaction_rate_species_ID, _ = get_model_rates_2 (model)
    #---
    parameter_id, _, compartment_id, _ = get_model_parameters (model)
    #---
    s_1, s_2, p_i, c_i = len(stoichiometric_matrix), len(buffered_species_id), len(parameter_id), len(compartment_id)
    #---
    p, c = sympy.symbols(f'p1:{p_i+1}'), sympy.symbols(f'c1:{c_i+1}')
    #---
    xx, bb = sympy.symbols(f'x1:{s_1+1}'), sympy.symbols(f'b1:{s_2+1}')
    #---
    sorted_species_id = sorted(species_id, key=len, reverse=True)
    indices_list_x = [species_id.index(string) for string in sorted_species_id]
    x = [item for sublist in sympy.Matrix([xx[i] for i in indices_list_x]).tolist() for item in sublist]
    #---
    sorted_buffered_species_id = sorted(buffered_species_id, key=len, reverse=True)
    buffered_indices_list_b = [buffered_species_id.index(string) for string in sorted_buffered_species_id]
    b = [item for sublist in sympy.Matrix([bb[i] for i in buffered_indices_list_b]).tolist() for item in sublist]
    #---
    for i, y in enumerate(c):
        for j, _ in enumerate(reaction_rate_species_ID):
            reaction_rate_species_ID[j] = reaction_rate_species_ID[j].replace(compartment_id[i], str(y))
    #---
    for i, y in enumerate(p):
        for j, _ in enumerate(reaction_rate_species_ID):
            reaction_rate_species_ID[j] = reaction_rate_species_ID[j].replace(parameter_id[i], str(y))
    #---
    for i, y in enumerate(x):
        for j, _ in enumerate(reaction_rate_species_ID):
            reaction_rate_species_ID[j] = reaction_rate_species_ID[j].replace(sorted_species_id[i], str(y))
    #---
    for i, y in enumerate(b):
        for j, _ in enumerate(reaction_rate_species_ID):
            reaction_rate_species_ID[j] = reaction_rate_species_ID[j].replace(sorted_buffered_species_id[i], str(y))
    #---
    reaction_rate_species_ID = sympy.Matrix(reaction_rate_species_ID)
    #---
    stoichiometric_matrix = sympy.Matrix(stoichiometric_matrix)
    #---    
    dx_dt_ID = stoichiometric_matrix*reaction_rate_species_ID
    dx_dt_ID = [item for sublist in dx_dt_ID.tolist() for item in sublist]
    reaction_rate_species_ID = [item for sublist in reaction_rate_species_ID.tolist() for item in sublist]
    #---
    return reaction_rate_species_ID, dx_dt_ID
#==========================================================================================================================================
#==========================================================================================================================================
#1. Extract and print the model ID
model, file_path, file_name = read_sbml_file()
#---
#2. Extract and print species
species_id, species_names, buffered_species_id, buffered_species_names, initial_concentrations, buffered_concentrations = get_model_species (model)
#==========================================================================================================================================
#==========================================================================================================================================
#3. Extract and print the functions
function_id, function_list, arguments, expressions = get_model_functions(model)
#==========================================================================================================================================
#==========================================================================================================================================
#4. Extract and print the reactions
reactions_id, reactions_names, reactions_info_species_id, reactions_info_species_name = get_model_reactions (model)
#==========================================================================================================================================
#==========================================================================================================================================
#5. Extract and print model parameters
parameter_id, parameter_values, compartment_id, compartment_size = get_model_parameters (model)
#==========================================================================================================================================
#==========================================================================================================================================
#6. Extract and print the reaction rates
reaction_rate_species_ID, reaction_rate_species_Names = get_model_rates_1 (model)
#---
reaction_rate_species_ID_new, reaction_rate_species_Names_new = get_model_rates_2 (model)
#==========================================================================================================================================
#==========================================================================================================================================
#7. Extract the stoichiometric matrix
stoichiometric_matrix = get_stoichiometric_matrix (model)
#==========================================================================================================================================
#==========================================================================================================================================
#8. Extract the system of ordinary differential equations
rates_sym, odes_sym = get_ode_model_sym (model)
#==========================================================================================================================================
#==========================================================================================================================================
print(f"{bold}BioModel ID:\n{reset}{file_name}\n")
#---
print(f"{bold}\nThe list of species:\n{reset}{species_id}\n\n{bold}The species names:\n{reset}{species_names}\n")
print(f"{bold}\nThe list of buffered species:\n{reset}{buffered_species_id}\n\n{bold}The buffered species names:\n{reset}{buffered_species_names}\n")
print(f"{bold}\nThe initial concentrations:\n{reset}{initial_concentrations}")
print(f"{bold}\nBuffeed concentrations:\n{reset}{buffered_concentrations}")
#---
print(f"{bold}\nThe reactions IDs:\n{reset}{reactions_id}\n\n{bold}The reaction names:\n{reset}{reactions_names}\n")
print(f"{bold}\nThe reactions interms of the species names:\n{reset}{reactions_info_species_name}\n")
print(f"{bold}\nThe reactions interms of the species IDs:\n{reset}{reactions_info_species_id}\n")
#---
print(f"{bold}\nThe list of functions:{reset}")
if function_list:
    for i, f in enumerate(function_list):
        print(f"{bold}Function{reset} {i+1}:")
        id = function_id[i]
        args_i = arguments[i]
        exp_i = expressions[i]
        print("ID:", id)
        print("Arguments:", args_i)
        print("Expression:", exp_i)
else:
    print([])   
#---    
print(f"{bold}\nThe number of parameters:\n{reset}{len(parameter_id)}\n\n{bold}The parameters:\n{reset}{parameter_id}\n\n{bold}The parameters values:\n{reset}{parameter_values}\n")
print(f"{bold}\nThe number of compartments:\n{reset}{len(compartment_id)}\n\n{bold}The compartments:\n{reset}{compartment_id}\n\n{bold}The compartment size:{reset}{compartment_size}{bold}\n")
#---
print(f"{bold}\nThe reaction rates in terms of species names:\n{reset}{reaction_rate_species_Names}\n")
print(f"{bold}\nThe reaction rates in terms of species names without functions:\n{reset}{reaction_rate_species_Names_new}\n")
print(f"{bold}\nThe reaction rates in terms of species IDs:\n{reset}{reaction_rate_species_ID}\n")
print(f"{bold}\nThe reaction rates in terms of species IDs without functions:\n{reset}{reaction_rate_species_ID_new}\n")
#---
print(f"{bold}\nThe simplified rates:\n{reset}{rates_sym}\n")
print(f"{bold}\nThe simplified system of ordinary differential equations:\n{reset}{odes_sym}\n")
#==========================================================================================================================================
#==========================================================================================================================================
#Table 1: Species
title_species = f"{file_name}: List of species"
#---
s = len(species_id)
b = len(buffered_species_id)
#---
#Create DataFrame
data_species = {
                'Species symbol': sympy.symbols(f'X1:{s+1}') + sympy.symbols(f'B1:{b+1}'),
                'Species concentrations': sympy.symbols(f'x1:{s+1}') + sympy.symbols(f'b1:{b+1}'),
                'Species ID': species_id + buffered_species_id, 
                'Species Name': species_names + buffered_species_names, 
                'Buffered': ['False'] * len(species_id) + ['True'] * len(buffered_species_id),
                'Initial concentrations': initial_concentrations + buffered_concentrations
                }
#----------------------------------------------------------------------------
#Table 2: Reactions
title_reactions = f"{file_name}: List of reactions"
#---
data_reactions = {
                  'Reation ID': reactions_id, 
                  'Reaction Name': reactions_names, 
                  'Reactions w/h IDs': reactions_info_species_id,
                  'Reactions w/h Names': reactions_info_species_name,
                  'Rates w/h IDs': reaction_rate_species_ID,
                  'Rates w/h IDs w/n functions': reaction_rate_species_ID_new,
                  'Rates w/h Names': reaction_rate_species_Names,
                  'Rates w/h Names w/n functions': reaction_rate_species_Names_new,
                  'Symplified rates': rates_sym                  
                 }
#----------------------------------------------------------------------------
#Table 3: Parameters
title_parameters = f"{file_name}: List of parameters "
#---
data_parameters = {
                  'Parameter Symbol': sympy.symbols(f'p1:{len(parameter_id)+1}'),
                  'Parameter ID': parameter_id, 
                  'Parameter Value': parameter_values
                  }
#----------------------------------------------------------------------------
#Table 4: Compartments
title_compartments = f"{file_name}: List of compartments"
#---
data_compartments = {
                  'Compartment symbol': sympy.symbols(f'c1:{len(compartment_id)+1}'),
                  'Compartment ID': compartment_id,
                  'Compartment Size': compartment_size
                  }
#----------------------------------------------------------------------------
#Table 5: Functions
title_functions = f"{file_name}: List of functions"
#---
data_functions = {
                  'Function ID': function_id, 
                  'Function Arguments': arguments, 
                  'Function Expression': expressions,
                 } 
#----------------------------------------------------------------------------
#Table 6: system of ODEs 
title_ode = f"{file_name}: The system of ordinary differential equations"
#---
data_ode = {
            'Species ID': species_id,
            'Species Name': species_names,
            'Species Concentration':  sympy.symbols(f'x1:{len(species_id)+1}'),
            'Simplified system of ODEs': odes_sym,
           }
#----------------------------------------------------------------------------
#Get the tables
#---
get_table(title_species, data_species)
#---
get_table(title_parameters, data_parameters)
#---
get_table(title_compartments, data_compartments)
#---
if function_id:
    get_table(title_functions, data_functions)
#---
get_table(title_reactions, data_reactions)
#---
get_table(title_ode, data_ode)
#==========================================================================================================================================
#==========================================================================================================================================
#Define the outputs we want to save as .json
selected_outputs = {
    "Species ID": species_id,
    "Species Names": species_names,
    "Buffered Species ID": buffered_species_id,
    "Buffered Species Names": buffered_species_names,
    "Initial Concentrations": initial_concentrations,
    "Buffered Concentrations": buffered_concentrations,
    "Function IDs": function_id,
    "Function Arguments": arguments,
    "Function Expressions": expressions,
    "Parameter IDs": parameter_id,
    "Parameter Values": parameter_values,
    "Compartment ID": compartment_id,
    "Compartment Size": compartment_size,
    "Reaction ID": reactions_id,
    "Reactions in Terms of Species Ids": reactions_info_species_id,
    "Reactions in Terms of Species Names": reactions_info_species_name,
    "Reaction Rates in Terms of Species Ids": reaction_rate_species_ID,
    "Reaction Rates in Terms of Species Names": reaction_rate_species_Names,
    "Stoichiometric matrix": stoichiometric_matrix.tolist()
}
#------------------------------------------------------------------------------
#Define the file path for the json file
json_file_path = str(file_name) + ".json"
#Save the outputs to the json file
with open(json_file_path, "w") as json_file:
    json.dump(selected_outputs, json_file, indent=4)
    json_file.write('\n')
print(bold + "\nThe outputs saved to:\n" + reset, json_file_path)    
#==========================================================================================================================================
#==========================================================================================================================================
