import xml.etree.ElementTree as ET
from tkinter import Tk, filedialog

# Hide the root Tk window
Tk().withdraw()

# Open file chooser
file_path = filedialog.askopenfilename(
    title="Select XML file",
    filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
)

if not file_path:
    print("❌ No file selected")
else:
    # Parse XML
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find all managedObject elements
    managed_objects = root.findall(".//managedObject")

    total_subs = 0  # counter for all <p> subelements

    for i, mo in enumerate(managed_objects, start=1):
        # Count <p> subelements inside each managedObject
        p_elements = mo.findall("p")
        count = len(p_elements)
        total_subs += count
        print(f"ManagedObject {i} has {count} <p> subelements")

    # Print totals
    print("\n===================================")
    print(f"✅ Total ManagedObjects found: {len(managed_objects)}")
    print(f"✅ Total <p> subelements found: {total_subs}")
