import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from plantuml import PlantUML
from PIL import Image, ImageTk
import io
import os
import openai
from openai import OpenAI

# Configure PlantUML server
plantuml_url = "https://www.plantuml.com/plantuml/png/"
plantuml = PlantUML(url=plantuml_url)

# OpenAI API key
# Azure OpenAI configuration from environment variables
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')  # Fetch the API key from environment variable
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')  # Fetch the endpoint from environment variable
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')  # Fetch deployment name from environment variable

# Set OpenAI API base and key to use Azure service
openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
#openai.api_version = "2023-05-15"  # Use the appropriate API version for Azure OpenAI


conversation_history=[] 

def generate_diagram():
    uml_code = uml_text.get("1.0", tk.END)
    try:
        # Generate diagram from UML code
        response = plantuml.processes(uml_code)
        img = Image.open(io.BytesIO(response))
        img = ImageTk.PhotoImage(img)

        # Update the image label
        img_label.config(image=img)
        img_label.image = img
    except Exception as e:
        print(f"An error occurred: {e}")

def open_uml_file():
    uml_file_path = filedialog.askopenfilename(filetypes=[("PlantUML Files", "*.puml")])
    if uml_file_path:
        with open(uml_file_path, "r") as file:
            uml_code = file.read()
            uml_text.config(fg='black')
            uml_text.delete("1.0", tk.END)
            uml_text.insert(tk.END, uml_code)

def open_details_file():
    llm_details_file_path = filedialog.askopenfilename(filetypes=[("SPEC Text files", "*.spec")])
    if llm_details_file_path:
        with open(llm_details_file_path, "r") as file:
            details = file.read()
            uml_text.config(fg='orange')
            details_text.delete("1.0", tk.END)
            details_text.insert(tk.END, details)

#Call to OpenAI to create teh first code from the information.
def generate_code():
    global conversation_history
    uml_code = uml_text.get("1.0", tk.END).strip()
    details = details_text.get("1.0",tk.END).strip()
    language = language_var.get()
    
    if not uml_code:
        messagebox.showwarning("Input Error", "Please enter or load PlantUML code.")
        return

    if language == "Select Language":
        messagebox.showwarning("Input Error", "Please select a programming language.")
        return
    
    
    if language == 'PseudoCode':
        prompt = f'Generate FSM code based on the following UML diagram in Pseudo Code:\n\nUML Code:\n{uml_code}'
    elif language == 'SystemVerilog':
        prompt = f'Generate FSM code based on the following UML diagram in System Verilog HDL. Since this is synchronous code, use a clock and Reset. The this UML Code to infer the design :\n\nUML Code:\n{uml_code}'
    elif language == 'Verilog':
        prompt = f'Generate FSM code based on the following UML diagram in classical Verilog HDL. Since this is synchronous code, use a clock and Reset. The this UML Code to infer the design :\n\nUML Code:\n{uml_code}'
    elif language == 'VHDL':
        prompt = f'Generate FSM code based on the following UML diagram in classical VHDL. Since this is synchronous code, use a clock and Reset. The this UML Code to infer the design :\n\nUML Code:\n{uml_code}'
    elif language == 'System Verilog Testbench':
        prompt = f'Generate a system verilog testbench for the FSM code based on the UML Code to infer the design :\n\nUML Code:\n{uml_code}. \nMake sure to have the ports identified correctly from teh UML, and include clock and reset.'
    elif language == 'System Verilog Assertion':
        prompt = f'Examine the UML code provided: {uml_code}.\n Use this information to draft some system verilog perty assertions that must be used. Example: If the design is in one state then it can not have signals for other state changed, etc. Use system verilog assertions syntax'
    elif language == 'Testplan':
        prompt = f'Based on the UML specified by teh followwing UML code, come up with a strong testplan that results in a high coverage:\n\nUML Code:\n{uml_code}'
    else :
        prompt = f"Generate FSM code based on the following UML diagram in {language}:\n\nUML Code:\n{uml_code}"
    print(f'The prompt is : {prompt+details}')
    code_text.config(fg='red')
    code_text.delete("1.0", tk.END)
    code_text.insert(tk.END,f"\n\nCreate a {language} for the given specifications...\n\n",("user","user"))
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or any other model you prefer
            messages=[
                {"role": "system", "content": "You are an expert Computer enginer proficient in software and hardware development. You are master of Verilog, SystemVerilog, VHDL, C++ and other languagaes and frameworks."}, 
                {"role": "user", "content": prompt+"\n"+details}
            ],
            stream=False,
            max_tokens=1500,
            temperature=0.5
        )
        code = response.choices[0].message.content
        #print(response.text.strip())
        # Display the generated code
        #code_text.delete("1.0", tk.END)
        code_text.config(fg='blue')  
        code_text.insert(tk.END, f"\n\n{code}\n\n",("assistant","assistant"))
    except Exception as e:
        print(f"An error occurred: {e}")
    conversation_history.append({"role": "user", "content":prompt+"\n"+details})
    conversation_history.append({"role": "assistant", "content":code})

def refine_code():
    global conversation_history
    uml_code = uml_text.get("1.0", tk.END).strip()
    llm_chat = chat_with_llm.get("1.0",tk.END).strip()
    language = language_var.get()
    if language == "Select Language":
        messagebox.showwarning("Input Error", "Please select a programming language.")
        return
    if {language} != 'Testplan':
        prompt = f"You are an expert designer in {language}:\nRefer to the past history and rewrite the code making sure your strictly incorporate all of the following instructions: {llm_chat}"
    elif {language} == 'Testplan':
        prompt = f"You are an expert in testplan design. For teh HDL code under consideration, build a very detailed testpaln. you can refer the UML too as given my following UML spec. {uml_code}\n"
    print(f'The prompt is : {prompt}') 
    code_text.config(fg='red')

    code_text.insert(tk.END, f"\n\n{llm_chat}\n\n",("user","user"))
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or any other model you prefer
            messages=conversation_history,
            stream=False,
            max_tokens=1500,
            temperature=0.5
        )
        code = response.choices[0].message.content
        #print(response.text.strip())
        # Display the generated code
        #code_text.delete("1.0", tk.END)
        code_text.config(fg='blue') 
        code_text.insert(tk.END,f"\n\n{code}\n\n",("assistant","assistant"))
    except Exception as e:
        print(f"An error occurred: {e}")
    print(f"The original data renst is {conversation_history}\n******\n The new data sent is {prompt} ")
    conversation_history.append({"role": "user", "content":prompt})
    conversation_history.append({"role": "assistant", "content":code})
    print(f"*-------The updated data  is {conversation_history} ------***")






# Function to handle the removal of placeholder text when the user types
def on_entry_click(event, text_widget, placeholder_text):
    if text_widget.get("1.0", tk.END).strip() == placeholder_text:
        text_widget.delete("1.0", tk.END)  # Clear the textbox content
        text_widget.config(fg='black')     # Set text color to black

def on_focusout(event, text_widget, placeholder_text):
    if text_widget.get("1.0", tk.END).strip() == "":
        text_widget.insert("1.0", placeholder_text)  # Restore placeholder text
        text_widget.config(fg='gray')                # Set placeholder text color to gray

# Function to create text box with placeholder text
align_user='left'
def create_scrolled_text(parent, placeholder_text, xwidth, yheight):
    text_widget = scrolledtext.ScrolledText(parent, width=xwidth, height=yheight)
    text_widget.insert("1.0", placeholder_text)
    text_widget.config(fg='gray')
    text_widget.bind("<FocusIn>", lambda event: on_entry_click(event, text_widget, placeholder_text))
    text_widget.bind("<FocusOut>", lambda event: on_focusout(event, text_widget, placeholder_text))
    return text_widget



# Main application window
root = tk.Tk()
root.title("HDL Generator 0.1 (Beta)")

# Create frames for left, middle, and right sections
left_frame = tk.Frame(root)
#middle_frame = tk.Frame(root)
right_frame = tk.Frame(root)

# Pack frames on the screen
#left_frame.grid(row=0, column=0, padx=50, pady=100)
#middle_frame.grid(row=0, column=1, padx=10, pady=10)
#right_frame.grid(row=0, column=1, padx=50, pady=100)
# Layout for left and right sections
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

#top_frame = tk.Frame(root)
#top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

#bottom_frame = tk.Frame(root)
#bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

# UML FILE READ/TYPE
#Textbox
uml_text = create_scrolled_text(left_frame, "Upload a UML file or type the PlantUML here ...",40,10)
uml_text.pack(side=tk.TOP,pady=5,fill=tk.BOTH, expand=True,)


#FSM Image Display area
# Image label to show PlantUML diagram
img_label = tk.Label(left_frame)
img_label.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

#Buttons for the exceution
open_uml_button = tk.Button(left_frame, text="Open UML File", command=open_uml_file)
open_uml_button.pack(side=tk.LEFT, padx=5)
generate_button = tk.Button(left_frame, text="Generate FSM Diagram", command=generate_diagram)
generate_button.pack(side=tk.LEFT, padx=5)


#Open/Type the deatils 
#Textbox
details_text = create_scrolled_text(right_frame, "Add any details to write the first version of code - example clock name, reset poarity etc...", 40, 2)
details_text.pack(side=tk.TOP,pady=5, fill=tk.BOTH, expand=True)
#Button
open_additional_details_button = tk.Button(right_frame, text="Open spec file", command=open_details_file)
open_additional_details_button.pack(side=tk.TOP, padx=5)



language_var = tk.StringVar(value="Select Language")
language_menu = tk.OptionMenu(right_frame, language_var, "PseudoCode", "SystemVerilog", "Verilog", "VHDL", "C++", "Python", "System Verilog Testbench", "Verilog Formal Assertions", "Testplan")
language_menu.pack(side=tk.TOP, padx=30, pady=30)




code_text = create_scrolled_text(right_frame, "The generated codes will appear here...",40,30)
code_text.pack(pady=5,side=tk.TOP, padx=5, fill=tk.BOTH, expand=True)

generate_code_button = tk.Button(right_frame, text="Generate Code", command=generate_code)
generate_code_button.pack(side=tk.TOP, padx=5)


chat_with_llm = create_scrolled_text(right_frame, "Talk with the LLM to refine the code",40,2)
chat_with_llm.pack(side=tk.TOP, pady=20, padx=30, fill=tk.BOTH, expand=True)

regenerate_button = tk.Button(right_frame, text="Refine Code", command=refine_code)
regenerate_button.pack(side=tk.BOTTOM, padx=5)

code_text.tag_configure("assistant", justify='left')
code_text.tag_configure("user", justify='right')
code_text.tag_configure("assistant", foreground='black')
code_text.tag_configure("user", foreground='blue')





# Code display area on the right
#code_text = scrolledtext.ScrolledText(right_frame, width=50, height=40)
#code_text.pack(fill=tk.BOTH, expand=True)


# Run the application
root.mainloop()
