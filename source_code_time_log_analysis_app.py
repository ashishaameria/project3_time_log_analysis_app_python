import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
from datetime import datetime, timedelta
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkinter import ttk
from tkinter import font

# Global variables
current_task = None
start_time = None
log_file = "time_log.csv"
circle_fill_time = 0
circle_filled = 0
chart_canvas = None

# ------------------------------ CSV File Management ------------------------------ #

def ensure_csv_file():
    """Ensure the CSV file exists and has the correct header."""
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as file:
            writer = csv.writer(file)
           

def read_csv_lines():
    """Read lines from the CSV file."""
    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            return file.readlines()
    return []

# ------------------------------ Logging Functions ------------------------------ #

def log_task(task, start_time, end_time):
    """Log task details into the CSV file."""
    duration = round((end_time - start_time).total_seconds() / 60)
    with open(log_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().date(), task, start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), duration])

def calculate_average_filling_time(task):
    """Calculate the average filling time for a task over the last 7 days."""
    today = datetime.now().date()
    dates = [(today - timedelta(days=i)) for i in range(7)]
    total_duration = 0
    date_log = {date: 0 for date in dates}
    
    lines = read_csv_lines()
    for row in lines[1:]:  # Skip header line
        log_date, logged_task, _, _, duration = row.strip().split(',')
        log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        if log_date in dates and logged_task == task:
            date_log[log_date] += float(duration)

    total_duration = sum(date_log.values())
    average = total_duration / 7
    return average + 10

# ------------------------------ Task Management Functions ------------------------------ #

def start_task():
    """Start tracking a task and log the circle filling times."""
    global current_task, start_time, circle_fill_time
    if task_var.get() in ["Main", "Secondary"]:
        current_task = task_var.get()
        start_time = datetime.now()
        circle_fill_time = calculate_average_filling_time(current_task)
        
        label_fill_time.config(text=f"Filling Time: {format_duration(circle_fill_time)}")
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        
        # Enable the floating circle button once the task starts
        floating_circle_button.config(state="normal")


def stop_task():
    """Stop tracking the current task and reset the circle/floating circle."""
    global current_task, start_time, circle_filled, floating_window

    if current_task and start_time:
        end_time = datetime.now()
        log_task(current_task, start_time, end_time)

        reset_task_variables()
        update_totals()
        show_entries_for_today()
        reset_circle()
        update_chart()
        
        # Check if floating_window exists and destroy it if so
        if 'floating_window' in globals() and floating_window is not None:
            floating_window.destroy()
            floating_window = None  # Optionally reset the reference to None
        
        # Re-enable the floating circle button after stopping the task
        floating_circle_button.config(state="normal")


def reset_task_variables():
    """Reset task-related variables to their initial states."""
    global current_task, start_time, circle_filled, circle_fill_time
    current_task = None
    start_time = None
    circle_filled = 0
    label_fill_time.config(text="Filling Time: 0.00 mins")
    start_button.config(state="normal")
    stop_button.config(state="disabled")
    # Reset the floating circle button if needed
    floating_circle_button.config(state="normal")

def reset_circle():
    """Reset the circle to its original unfilled state."""
    global circle_filled
    circle_filled = 0
    canvas.delete("circle")
    canvas.create_oval(50, 50, 150, 150, outline="black", width=2, fill="white")

def format_duration(total_minutes):
    """Format the duration from minutes to hours and minutes."""
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours} hr {minutes} mins" if hours > 0 else f"{minutes} mins"

# ------------------------------ Circle Update Functions ------------------------------ #

def update_circle():
    """Update the circle to reflect the elapsed time."""
    if current_task:
        elapsed_time = (datetime.now() - start_time).total_seconds() / 60
        circle_filled = min(elapsed_time / circle_fill_time, 1.0)
        canvas.delete("circle")
        canvas.create_oval(50, 50, 150, 150, outline="black", width=2, fill="white")
        if circle_filled < 1.0:
            canvas.create_arc(50, 50, 150, 150, start=90, extent=-360 * circle_filled, fill="blue", tags="circle")
        else:
            canvas.create_oval(50, 50, 150, 150, outline="black", width=2, fill="blue", tags="circle")
    root.after(1000, update_circle)  # Update every second

# ------------------------------ Totals and Entries Functions ------------------------------ #

def update_totals():
    """Calculate and display totals for each task."""
    total_main = total_secondary = 0
    today = datetime.now().date()
    lines = read_csv_lines()

    for row in lines[1:]:
        log_date, task, _, _, duration = row.strip().split(',')
        if datetime.strptime(log_date, "%Y-%m-%d").date() == today:
            if task == "Main":
                total_main += float(duration)
            elif task == "Secondary":
                total_secondary += float(duration)

    label_main_total.config(text=f"Main Task Total: {format_duration(total_main)}")
    label_secondary_total.config(text=f"Secondary Task Total: {format_duration(total_secondary)}")

def show_entries_for_today():
    """Display today's entries in a table format."""
    today = datetime.now().date()
    for item in tree.get_children():
        tree.delete(item)

    lines = read_csv_lines()
    for index, row in enumerate(lines):
        log_date, task, start, end, duration = row.strip().split(',')
        if datetime.strptime(log_date, "%Y-%m-%d").date() == today:
            formatted_date = datetime.strptime(log_date, "%Y-%m-%d").strftime("%d-%b-%y")
            tree.insert("", tk.END, values=(formatted_date, task, start, end, f"{duration} mins"), tags=('evenrow' if index % 2 == 0 else 'oddrow',))


# ------------------------------ Deletion Functions ------------------------------ #

def custom_confirm_dialog(message, font_size=14):
    """Create a custom confirmation dialog with a larger font size."""
    dialog = tk.Toplevel(root)
    dialog.title("Confirm Deletion")
    dialog.geometry("400x180")
    dialog.transient(root)
    dialog.grab_set()

    label = tk.Label(dialog, text=message, font=("Helvetica", font_size))
    label.pack(pady=20)

    user_input = tk.StringVar()
    entry = tk.Entry(dialog, textvariable=user_input, font=("Helvetica", font_size))
    entry.pack(pady=10)

    ok_button = tk.Button(dialog, text="OK", command=lambda: dialog.grab_release() or dialog.destroy(), font=("Helvetica", font_size), width=15, height=2)
    ok_button.pack(pady=10)

    dialog.wait_window(dialog)
    return user_input.get()

def delete_entries_today():
    """Delete all entries for today."""
    confirmation = custom_confirm_dialog("Type 'reset' to delete all entries for today.")
    
    if confirmation == "reset":
        today = datetime.now().date()
        lines = read_csv_lines()

        with open(log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for line in lines[1:]:  # Skip header line
                log_date, task, start, end, duration = line.strip().split(',')
                if datetime.strptime(log_date, "%Y-%m-%d").date() != today:
                    writer.writerow([log_date, task, start, end, duration])
        
        show_entries_for_today()
        update_totals()
        update_chart()
        messagebox.showinfo("Success", "Today's entries have been deleted.")

def delete_all_entries():
    """Delete all entries from the CSV file."""
    confirmation = custom_confirm_dialog("Type 'reset' to delete all entries.")
    
    if confirmation == "reset":
        if os.path.exists(log_file):
            os.remove(log_file)
        ensure_csv_file()
        show_entries_for_today()
        update_totals()
        update_chart()
        messagebox.showinfo("Success", "All entries have been deleted.")

def delete_last_entry():
    """Delete the last entry from the CSV file."""
    confirmation = custom_confirm_dialog("Type 'reset' to delete the last entry.")
    
    if confirmation == "reset":
        lines = read_csv_lines()
        
        if len(lines) <= 1:  # Only header or no entries
            os.remove(log_file)
            ensure_csv_file()
            show_entries_for_today()
            update_totals()
            update_chart()
            messagebox.showinfo("Success", "The last entry has been deleted.")
            return

        with open(log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            for line in lines[:-1]:  # Exclude the last entry
                writer.writerow(line.strip().split(','))
        
        show_entries_for_today()
        update_totals()
        update_chart()
        messagebox.showinfo("Success", "The last entry has been deleted.")

# ------------------------------ Import and Export Functions ------------------------------ #

def sequential_import():
    """Import old Excel and CSV files, combine the data, and export to a new CSV file."""
    messagebox.showinfo(
        "Import Information", 
        "You can proceed with just the old Excel file if the old CSV file is not available or is empty."
    )
    
    # Step 1: Import old Excel file
    file_path = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx;*.xls")],
        title="Select the old Excel file"
    )
    if file_path:
        try:
            excel_data = pd.read_excel(file_path, header=None)
            messagebox.showinfo("Success", "Old Excel file imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import Excel file: {e}")
            return
    else:
        messagebox.showwarning("Warning", "No Excel file selected. Process aborted.")
        return
    
    # Step 2: Import old CSV file (optional)
    import_csv = messagebox.askyesno("Optional CSV Import", "Do you want to import an old CSV file as well?")
    
    if import_csv:
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="Select the old CSV file"
        )
        if file_path:
            try:
                csv_data = pd.read_csv(file_path, header=None)
                if csv_data.empty:
                    messagebox.showinfo("Info", "The CSV file is empty. Proceeding with Excel data only.")
                    csv_data = None
                else:
                    messagebox.showinfo("Success", "Old CSV file imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import CSV file: {e}")
                return
        else:
            messagebox.showwarning("Warning", "No CSV file selected. Continuing with Excel data only.")
            csv_data = None
    else:
        csv_data = None
    
    # Process and export new CSV file
    try:
        combined_data = pd.concat([excel_data, csv_data], ignore_index=True) if csv_data is not None else excel_data.copy()
        
        combined_data.dropna(subset=[0], inplace=True)
        combined_data[0] = pd.to_datetime(combined_data[0], errors='coerce')
        combined_data = combined_data.dropna(subset=[0])
        combined_data.sort_values(by=0, inplace=True)
        combined_data[2] = combined_data[2].astype(str).str.extract(r'(\d{2}:\d{2})')[0]
        combined_data[3] = combined_data[3].astype(str).str.extract(r'(\d{2}:\d{2})')[0]

        combined_data.to_csv(log_file, index=False, header=False)
        messagebox.showinfo("Success", f"New CSV file '{log_file}' generated successfully!")
        
        update_totals()
        show_entries_for_today()
        update_chart()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process and export CSV file: {e}")




#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#




# ------------------------------------ Helper Functions --------------------------------------------
def format_duration(minutes):
    """Format duration in minutes to hours and minutes."""
    hours = int(minutes // 60)
    minutes = int(minutes % 60)
    return f"{hours}h {minutes}m"


def format_duration_for_chart(minutes):
    """Format duration in minutes to 'hh:mm' for the Y-axis."""
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    return f"{hours:02d}:{remaining_minutes:02d}"

# ------------------------------------ Chart/Analysis Functions ------------------------------------

def calculate_task_totals(period, task_type_chart):
    """Calculate total durations for the selected task ('Main' or 'Secondary') over the specified period."""
    today = datetime.now().date()

    # Determine period days and dates to analyze
    period_days = {'7days': 7, '14days': 14, '30days': 30}[period]
    dates = [(today - timedelta(days=i)) for i in range(period_days)]

    task_logs = {"Main": {}, "Secondary": {}}

    # Initialize task_logs for all dates with zero values
    for date in dates:
        task_logs["Main"][date] = 0
        task_logs["Secondary"][date] = 0

    # Read logs from file
    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                log_date, task, start, end, duration = row
                log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
                if log_date in dates:
                    task_logs[task][log_date] += float(duration)  # Sum durations for each day

    # Extract the data for the selected task
    selected_task_totals = [task_logs[task_type_chart].get(date, 0) for date in dates]
    return dates, selected_task_totals

def update_chart():
    """Update the chart based on the selected period and task."""
    global chart_canvas  # Use the global variable for chart canvas
    period = period_var.get()  # Get the period from the selected radio button
    task_type_chart = task_var_chart.get()  # Get the selected task type ('Main' or 'Secondary')
    
    dates, totals = calculate_task_totals(period, task_type_chart)  # Calculate total durations
    
    # If the chart already exists, clear it instead of creating a new one
    if chart_canvas is not None:
        chart_canvas.get_tk_widget().destroy()

    # Create a new chart
    fig, ax = plt.subplots(figsize=(10, 5))  # Adjust the figure size if needed

    # Adjust the width of the bars
    bar_width = 0.5  # Adjust this value to change the width of the bars
    x = range(len(dates))
    ax.bar(x, totals, color='skyblue', width=bar_width)

    # Format the dates for readability (X-Axis)
    ax.set_xticks(x)
    ax.set_xticklabels([date.strftime("%d-%b") for date in dates], rotation=45, ha="right")

    # Format the time (Y-Axis)
    max_duration = max(totals) if totals else 0
    max_minutes = max(int(max_duration // 30 + 1) * 30, 180)  # Ensure the y-axis goes up to at least 3 hours (180 mins)
    ax.set_yticks([i * 30 for i in range((max_minutes // 30) + 1)])  # Create ticks every 30 minutes
    ax.set_yticklabels([format_duration_for_chart(i * 30) for i in range((max_minutes // 30) + 1)])

    # Add horizontal gridlines
    ax.yaxis.grid(True)

    # Calculate and plot the average line
    if totals:
        average_duration = np.mean(totals)
        ax.axhline(y=average_duration, color='red', linestyle='--', label=f'Avg: {format_duration_for_chart(average_duration)}')
        ax.text(x[-1], average_duration + 10, f'Avg: {format_duration_for_chart(average_duration)}', color='red', verticalalignment='bottom')

    ax.set_xlabel('Date')
    ax.set_ylabel('Total Duration (hh:mm)')
    ax.set_title(f'{task_type_chart} Task Duration Over Selected Period')

    # Embed the matplotlib figure in the Tkinter window
    chart_canvas = FigureCanvasTkAgg(fig, master=analysis_tab)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Close the figure to avoid memory issues
    plt.close(fig)

    # Refocus the Tkinter window in case it minimizes
    root.deiconify()  # Ensure window is restored if minimized
    root.lift()  # Bring the window to the top

# ------------------------------------ Floating Circle Functions -----------------------------------
def open_floating_circle():
    """Open a floating window with a circular progress indicator and disable the floating button."""
    global floating_window, canvas_floating, floating_circle_filled, floating_task, floating_circle_fill_time, floating_start_time

    # Calculate the time already passed since the main task started
    elapsed_time_for_main_circle = (datetime.now() - start_time).total_seconds() / 60

    # Calculate the remaining fill time for the floating circle
    floating_circle_fill_time = max(circle_fill_time - elapsed_time_for_main_circle, 0)

    # Initialize the floating circle filled percentage based on the elapsed time
    floating_circle_filled = elapsed_time_for_main_circle / circle_fill_time if circle_fill_time > 0 else 0.0
    floating_task = True  # Status of the floating circle task

    # Open the floating window
    floating_window = tk.Toplevel(root)
    
    # Remove title bar and set the window to always stay on top
    floating_window.overrideredirect(True)
    floating_window.attributes("-topmost", True)
    floating_window.geometry("100x100")
    floating_window.resizable(False, False)

    # Create the floating circle canvas
    canvas_floating = tk.Canvas(floating_window, width=100, height=100)
    canvas_floating.pack(fill="both", expand=False)

    # Disable the floating circle button after the window is opened
    floating_circle_button.config(state="disabled")

    def update_floating_circle():
        """Update the floating circle based on elapsed time."""
        global floating_circle_filled
        if floating_task:
            elapsed_time = (datetime.now() - start_time).total_seconds() / 60  # Minutes passed since task start
            remaining_time = max(circle_fill_time - elapsed_time, 0)  # Remaining time for floating circle
            floating_circle_filled = min(elapsed_time / circle_fill_time, 1.0)  # Calculate fill percentage (0 to 1)

            # Clear previous drawings
            canvas_floating.delete("circle")

            # Draw the unfilled circle
            canvas_floating.create_oval(20, 20, 80, 80, outline="black", width=2, fill="white")

            # Draw the filled portion of the circle
            if floating_circle_filled < 1.0:
                canvas_floating.create_arc(20, 20, 80, 80, start=90, extent=-360 * floating_circle_filled, fill="blue", tags="circle")
            else:
                canvas_floating.create_oval(20, 20, 80, 80, outline="black", width=2, fill="blue", tags="circle")

        # Schedule the next update after 1 second
        floating_window.after(1000, update_floating_circle)

    update_floating_circle()


    # Create the right-click menu
    right_click_menu = tk.Menu(floating_window, tearoff=0, font=menu_font_style)
    right_click_menu.add_command(label="Stop", command=stop_floating_circle)
    

    # Modify the Close command to enable the floating circle button when the window is closed
    def close_floating_window():
        floating_window.destroy()
        floating_circle_button.config(state="normal")  # Re-enable the floating circle button

    right_click_menu.add_command(label="Close", command=close_floating_window)

    def show_context_menu(event):
        right_click_menu.tk_popup(event.x_root, event.y_root)

    floating_window.bind("<Button-3>", show_context_menu)

    # Dragging functionality for the floating window
    def on_drag_start(event):
        floating_window._drag_start_x = event.x
        floating_window._drag_start_y = event.y

    def on_drag_motion(event):
        dx = event.x - floating_window._drag_start_x
        dy = event.y - floating_window._drag_start_y
        floating_window.geometry(f"+{floating_window.winfo_x() + dx}+{floating_window.winfo_y() + dy}")

    floating_window.bind("<Button-1>", on_drag_start)
    floating_window.bind("<B1-Motion>", on_drag_motion)

def reset_floating_circle():
    """Reset the floating circle to its initial state."""
    global floating_window, canvas_floating
    if 'canvas_floating' in globals() and canvas_floating and canvas_floating.winfo_exists():
        canvas_floating.delete("circle")
        canvas_floating.create_oval(20, 20, 80, 80, outline="black", width=2, fill="white")

def stop_floating_circle():
    """Stop the floating circle and close the floating window."""
    global floating_window, canvas_floating
    
    stop_task()  # This will reset the main window circle, stop the task, and log the data
    reset_floating_circle()
    if floating_window:
        floating_window.destroy()

# ------------------------------------ Main application window -----------------------------------

# Define the main application window
root = tk.Tk()
root.title("Time Log Application")

# Task Variable
task_var = tk.StringVar()
task_var.set("Main")


#---------------------------------------All pages control---------------------------------------

# Define the font style for the rest of the widgets - all click buttons 
font_style = font.Font(family="Helvetica", size=14)  # Increased font size

# Create Tabs
tab_control = ttk.Notebook(root)
entry_tab = ttk.Frame(tab_control)
analysis_tab = ttk.Frame(tab_control)
settings_tab = ttk.Frame(tab_control)
tab_control.add(entry_tab, text="Entries")
tab_control.add(analysis_tab, text="Analysis")
tab_control.add(settings_tab, text="Settings")
tab_control.pack(expand=1, fill='both')

# ------------------------------------ Page 1 - Font size -----------------------------------

# Define font style for the menu items - floating circle right click
menu_font_style = font.Font(family="Helvetica", size=12)  # Adjust the size as needed

#--------------------------Page 1 - Radio button selection changes style----------------------

# Function to update radio button styles for Entry Tab
def update_radio_styles():
    if task_var.get() == "Main":
        radio_main.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")
        radio_secondary.config(fg="black", font=(None, 12), bg="white")
    else:
        radio_main.config(fg="black", font=(None, 12), bg="white")
        radio_secondary.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")


#-----------------------------Page 1 - Radio buttons & labels------------------------------------

# Entry Tab Widgets
tk.Label(entry_tab, text="Select Task:", font=font_style).pack()

# Create Radio Buttons with labels that change style when selected (Entry Tab)
radio_main = tk.Radiobutton(entry_tab, text="Main Task", variable=task_var, value="Main", command=lambda: [update_radio_styles(), update_time_period_styles(), update_task_type_styles()], font=font_style)
radio_secondary = tk.Radiobutton(entry_tab, text="Secondary Task", variable=task_var, value="Secondary", command=lambda: [update_radio_styles(), update_time_period_styles(), update_task_type_styles()], font=font_style)
radio_main.pack()
radio_secondary.pack()

# Call the function once to set the initial styles (Entry Tab)
update_radio_styles()

start_button = tk.Button(entry_tab, text="Start Task", command=start_task, font=font_style)
start_button.pack()

stop_button = tk.Button(entry_tab, text="Stop Task", command=stop_task, state="disabled", font=font_style)
stop_button.pack()

label_fill_time = tk.Label(entry_tab, text="Filling Time: 0.00 mins", font=font_style)
label_fill_time.pack()

canvas = tk.Canvas(entry_tab, width=200, height=200)
canvas.pack()

floating_circle_button = tk.Button(entry_tab, text="Floating Circle", command=open_floating_circle, state="disabled", font=font_style)
floating_circle_button.pack(pady=10)


label_main_total = tk.Label(entry_tab, text="Main Task Total: 0.00 hours", font=font_style)
label_main_total.pack()

label_secondary_total = tk.Label(entry_tab, text="Secondary Task Total: 0.00 hours", font=font_style)
label_secondary_total.pack()

#-------------------------Page 1 - Todays log table, font size & table effect------------------

columns = ("Date", "Task", "Start Time", "End Time", "Duration")
tree = ttk.Treeview(entry_tab, columns=columns, show='headings')
tree.heading("Date", text="Date")
tree.heading("Task", text="Task")
tree.heading("Start Time", text="Start Time")
tree.heading("End Time", text="End Time")
tree.heading("Duration", text="Duration")
tree.pack(fill='both', expand=True)

# Define tags for odd and even rows with different background colors
tree.tag_configure('oddrow', background="white")
tree.tag_configure('evenrow', background="#f0f0f0")  # Light gray color


# Define a larger font style for the notebook tabs 
tab_font_style = font.Font(family="Helvetica", size=16)  # Adjust the size as needed

# Create a Style object
style = ttk.Style()
style.configure('TNotebook.Tab', font=tab_font_style)  # Apply the font style to the notebook tabs

# Style for Treeview (add this to increase font size for Treeview rows and headers)
style.configure("Treeview", font=("Helvetica", 14), rowheight=25)  # Adjust row height and font size
style.configure("Treeview.Heading", font=("Helvetica", 16, "bold"))

# Set gridlines for rows and columns using bordercolor and borderwidth
style.configure("Treeview", 
                background="white",
                foreground="black",
                rowheight=25,  # Adjust row height for better spacing
                fieldbackground="white",
                bordercolor="black",  # Set color of the borders (gridlines)
                borderwidth=1)        # Width of the gridlines

# Add border for the headings
style.configure("Treeview.Heading", bordercolor="black", borderwidth=1, font=("Helvetica", 16, "bold"))

#----------------------Page 2 - Radio button selection changes style----------------------------

# Function to update radio button styles for Analysis Tab (Time Period Selection)
def update_time_period_styles():
    for rb in [radio_7days, radio_14days, radio_30days]:
        rb.config(fg="black", font=(None, 12), bg="white")  # Reset all styles
    if period_var.get() == "7days":
        radio_7days.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")
    elif period_var.get() == "14days":
        radio_14days.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")
    else:  # 30 days
        radio_30days.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")

# Function to update radio button styles for Analysis Tab (Task Type Selection)
def update_task_type_styles():
    for rb in [radio_main_task, radio_secondary_task]:
        rb.config(fg="black", font=(None, 12), bg="white")  # Reset all styles
    if task_var_chart.get() == "Main":
        radio_main_task.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")
    else:  # Secondary
        radio_secondary_task.config(fg="blue", font=(None, 12, 'bold'), bg="yellow")


#-----------------------------Page 2 - Analysis seletion buttons----------------------------------

# Analysis Tab Widgets - Column Chart will replace Treeview
control_frame = tk.Frame(analysis_tab)
control_frame.pack(fill='x', pady=10)

time_period_frame = tk.Frame(control_frame)
time_period_frame.pack(side="left", anchor="w")

period_var = tk.StringVar(value="7days")
radio_7days = tk.Radiobutton(time_period_frame, text="Last 7 Days", variable=period_var, value="7days", command=lambda: [update_time_period_styles(), update_task_type_styles(), update_chart()], font=font_style)
radio_14days = tk.Radiobutton(time_period_frame, text="Last 14 Days", variable=period_var, value="14days", command=lambda: [update_time_period_styles(), update_task_type_styles(), update_chart()], font=font_style)
radio_30days = tk.Radiobutton(time_period_frame, text="Last 30 Days", variable=period_var, value="30days", command=lambda: [update_time_period_styles(), update_task_type_styles(), update_chart()], font=font_style)

# Pack time period radio buttons
radio_7days.pack(anchor="w", pady=5)
radio_14days.pack(anchor="w", pady=5)
radio_30days.pack(anchor="w", pady=5)

# Call the function once to set the initial styles (Time Period)
update_time_period_styles()

# Replace Mean/Median with Task Type Selection
task_type_frame = tk.Frame(control_frame)
task_type_frame.pack(side="right", anchor="e")

task_var_chart = tk.StringVar(value="Main")
radio_main_task = tk.Radiobutton(task_type_frame, text="Main Task", variable=task_var_chart, value="Main", command=lambda: [update_task_type_styles(), update_time_period_styles(), update_chart()], font=font_style)
radio_secondary_task = tk.Radiobutton(task_type_frame, text="Secondary Task", variable=task_var_chart, value="Secondary", command=lambda: [update_task_type_styles(), update_time_period_styles(), update_chart()], font=font_style)

# Pack task type radio buttons
radio_main_task.pack(anchor="w", pady=5)
radio_secondary_task.pack(anchor="w", pady=5)

# Call the function once to set the initial styles (Task Type)
update_task_type_styles()

#--------------------------------------Page 3 - Buttons--------------------------------------------

# In the Settings Tab section, add the "Delete Last Entry" button

# Settings Tab Widgets
tk.Button(settings_tab, text="Delete Today's Entries", command=delete_entries_today, font=font_style).pack(pady=10)
tk.Button(settings_tab, text="Delete All Entries", command=delete_all_entries, font=font_style).pack(pady=10)

# New Button for Deleting the Last Entry
tk.Button(settings_tab, text="Delete Last Entry", command=delete_last_entry, font=font_style).pack(pady=10)

tk.Button(settings_tab, text="Import and Export Data", command=sequential_import, font=font_style).pack(pady=10)  # Changed from ttk.Button to tk.Button

# -------------------------------- Application Initialization and Main Loop ---------------------------

# Start updating the circle every second
update_circle()

# Update totals, entries, and analysis on startup
update_totals()
show_entries_for_today()
update_chart()

# Run the application
root.mainloop()