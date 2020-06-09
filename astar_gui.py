import threading
import json
import os
from astar_model import AStarModel
from tkinter.ttk import Progressbar
from tkinter import (Tk, Frame, Button, Label, Entry, Checkbutton, Scale, Canvas, messagebox, filedialog,
                     StringVar, IntVar,
                     DISABLED, NORMAL,
                     W, S, NW, EW, NSEW,
                     BOTTOM, TOP, LEFT,
                     X, Y,
                     HORIZONTAL,
                     YES)


class AStarView(Tk):
    def __init__(self, width=15):
        Tk.__init__(self)
        self.title('A* Search Visualizer')

        # Application version
        self.__VERSION = '1.0.0'

        # Grid width slider range
        self.__MAX_GRID_WIDTH = 100
        self.__MIN_GRID_WIDTH = 2

        # Width of the control frame in pixels (you can modify this)
        self.__CONTROL_DIM_WIDTH = 250

        # Width of the grid in pixels (you can modify this)
        self.__GRID_DIM_WIDTH = 800

        # Calculate the correct dimensions for the root frame (8px offsets prevent grid clipping from grid border thickness)
        self.geometry('{}x{}'.format(
            self.__CONTROL_DIM_WIDTH + self.__GRID_DIM_WIDTH + 8, self.__GRID_DIM_WIDTH + 8))

        # Disable application resizing
        self.resizable(0, 0)

        # Event bindings
        self.bind('<ButtonPress-1>', self.__on_m1_down)
        self.bind('<B1-Motion>', self.__on_m1_down)
        self.bind('<ButtonPress-3>', self.__on_m3_down)
        self.bind('<B3-Motion>', self.__on_m3_down)
        self.bind('<KeyPress>', self.__on_key_press)
        self.bind('<KeyRelease>', self.__on_key_release)

        # Toggles when certain keys are held down
        self.__EDIT_MODE = {
            'setStart': False,
            'setEnd': False,
        }

        # Button colours (you can change these)
        self.__COLOUR_RECONFIGURE_BUTTON = 'coral'
        self.__COLOUR_HOW_TO_USE_BUTTON = 'SlateGray2'
        self.__COLOUR_ABOUT_BUTTON = 'SlateGray1'
        self.__COLOUR_IMPORT_MAZE_BUTTON = 'sandy brown'
        self.__COLOUR_EXPORT_MAZE_BUTTON = 'dark salmon'

        # Maze colours (you can change these)
        self.__COLOUR_EMPTY = 'white'
        self.__COLOUR_WALL = 'gray25'
        self.__COLOUR_START = 'pale green'
        self.__COLOUR_END = 'salmon'
        self.__COLOUR_UNSOLVED = 'thistle'
        self.__COLOUR_SOLVED = 'lemon chiffon'
        self.__COLOUR_PATH = 'light slate blue'

        # Dictionary for when update_gui() is called
        self.__SYMBOL_TO_COLOUR = {
            ' ': self.__COLOUR_EMPTY,
            'W': self.__COLOUR_WALL,
            'S': self.__COLOUR_START,
            'E': self.__COLOUR_END,
            '?': self.__COLOUR_UNSOLVED,
            'X': self.__COLOUR_SOLVED,
            'P': self.__COLOUR_PATH
        }

        # Dialog messages
        self.__DIALOG_MESSAGES = {
            'help': ('Holding left-click places walls\n'
                     'Holding right-click removes walls\n\n'
                     'Holding [S] while pressing left-click sets the start point\n'
                     'Holding [E] while pressing left-click sets the end point\n\n'
                     'Press [space] to start / stop the solver\n'
                     'Press [Esc] to close the application'),

            'about': ('This application visualizes the A* search algorithm.\n\n'
                      'Made by Jonathan Mack\n'
                      'v{}'.format(self.__VERSION)),
        }

        # Contains the GUI representaiton of model.settings
        self.cb_values = {}

        # Disables mouse and keyboard events while True
        self.__is_reconfiguring = False

        # Initialize the backing model
        self.__initialize_model(width, width)

        # Initialize the GUI
        self.__initialize_gui()

    def __initialize_model(self, nRow, nCol):
        ''' Initializes the backing model for the view.

        Args:
            nRow::[int]
                The number of rows in the model
            nCol::[int]
                The number of columns in the model

        Returns:
            None
        '''
        self.model = AStarModel(view=self, nRow=nRow, nCol=nCol)

        # Set the model settings to the GUI settings during reconfiguration
        self.__handle_cb()

        # Disable print to console
        self.model.set_setting('enablePrintToConsole', False)

    def __initialize_gui(self):
        ''' Initializes the GUI.

        Args:
            None

        Returns:
            None
        '''
        self.__initialize_control_frame()
        self.__initialize_grid_frame()

    def __initialize_control_frame(self):
        ''' Initializes the control frame which contains application options.

        Args:
            None

        Returns:
            None
        '''
        # The control frame itself
        control_frame = Frame(self, width=self.__CONTROL_DIM_WIDTH)
        control_frame.pack_propagate(0)
        control_frame.pack(side=LEFT, fill=Y)

        # Initialize children frames
        self.__initialize_configuration_frame(control_frame)
        self.__initialize_options_frame(control_frame)
        self.__initialize_import_export_frame(control_frame)
        self.__initialize_stats_frame(control_frame)
        self.__initialize_help_frame(control_frame)

        # Initialize the Start / Stop button
        self.start_stop_button = Button(control_frame,
                                        text='START',
                                        bg='pale green',
                                        relief='flat',
                                        pady=20,
                                        command=self.__toggle_solver)
        self.start_stop_button.pack(side=BOTTOM, fill=X)

        # Interactive GUI components are disabled during reconfiguration
        self.__interactive_gui_components = [self.grid_width_slider,
                                             self.__reconfigure_button,
                                             self.__cb_diagonal,
                                             self.__cb_grid_lines,
                                             self.__how_to_use_button,
                                             self.__about_button,
                                             self.__import_button,
                                             self.__export_button,
                                             self.start_stop_button]

    def __initialize_configuration_frame(self, master):
        ''' Initializes the configuration frame which is a child of the control frame.

        Args:
            master::[tk.Frame]
                The parent frame of this frame (the control frame)

        Returns:
            None
        '''
        # The configuration frame itself
        configuration_frame = Frame(master)
        configuration_frame.pack(anchor=W, padx=20, pady=20, fill=X)

        # Allow grid components to fill the width of the frame
        configuration_frame.grid_columnconfigure(0, weight=1)
        configuration_frame.grid_columnconfigure(1, weight=1)

        # Configuration label
        configuration_label = Label(
            configuration_frame, text='CONFIGURATION', font=('Helvetica', 16))
        configuration_label.grid(row=0, column=0, sticky=W, columnspan=2)

        # Grid width label
        self.grid_width_label = Label(
            configuration_frame, text='Grid width: {}'.format(self.model.get_nrow()))
        self.grid_width_label.grid(row=1, column=0, sticky=W, columnspan=2)

        # Grid width slider
        self.grid_width_slider = Scale(configuration_frame,
                                       width=20,
                                       from_=self.__MIN_GRID_WIDTH,
                                       to=self.__MAX_GRID_WIDTH,
                                       orient=HORIZONTAL,
                                       showvalue=False)

        # Set default slider value
        self.grid_width_slider.set(self.model.get_nrow())

        # Slider bindings
        self.grid_width_slider.bind(
            '<B1-Motion>', self.__handle_grid_width_slider_change)
        self.grid_width_slider.bind(
            '<ButtonRelease-1>', self.__handle_grid_width_slider_change)
        self.grid_width_slider.grid(row=2, column=0, sticky=EW, columnspan=2)

        # Reconfigure button
        self.__reconfigure_button = Button(
            configuration_frame,
            text='Reconfigure',
            bg=self.__COLOUR_RECONFIGURE_BUTTON,
            command=self.__handle_reconfigure)
        self.__reconfigure_button.grid(row=3,
                                       column=0,
                                       sticky=EW,
                                       columnspan=2)

        # Progress bar for reconfiguration
        self.__progress_bar = Progressbar(
            configuration_frame,
            orient=HORIZONTAL,
            mode='indeterminate')

    def __initialize_options_frame(self, master):
        ''' Initializes the options frame which is a child of the control frame.

        Args:
            master::[tk.Frame]
                The parent frame of this frame (the control frame)

        Returns:
            None
        '''
        # The options frame itself
        options_frame = Frame(master)
        options_frame.pack(anchor=W, padx=20, pady=20, fill=X)

        # Allow grid components to fill the width of the frame
        options_frame.grid_columnconfigure(0, weight=1)

        # Options label
        options_label = Label(
            options_frame,
            text='OPTIONS',
            font=('Helvetica', 16))
        options_label.grid(row=0, column=0, sticky=W, columnspan=2)

        # Allow diagonal movement Checkbutton
        self.allow_diagonals = IntVar(
            value=self.model.get_setting('allowDiagonals'))
        self.cb_values['allowDiagonals'] = self.allow_diagonals
        self.__cb_diagonal = Checkbutton(
            options_frame,
            text='Allow diagonal movement',
            variable=self.allow_diagonals,
            command=self.__handle_cb)
        self.__cb_diagonal.grid(row=1, column=0, sticky=W)

        # Show grid lines Checkbutton
        self.show_grid_lines = IntVar(value=True)
        self.__cb_grid_lines = Checkbutton(
            options_frame,
            text='Show grid lines',
            variable=self.show_grid_lines,
            command=self.__handle_show_grid_lines)
        self.__cb_grid_lines.grid(row=2, column=0, sticky=W)

    def __initialize_import_export_frame(self, master):
        ''' Initializes the Import / Export frame which is a child of the control frame.

        Args:
            master::[tk.Frame]
                The parent frame of this frame (the control frame)

        Returns:
            None
        '''
        # The Import / Export frame itself
        import_export_frame = Frame(master)
        import_export_frame.pack(anchor=W, padx=20, pady=20, fill=X)

        # Allow grid components to fill the width of the frame
        import_export_frame.grid_columnconfigure(0, weight=1)
        import_export_frame.grid_columnconfigure(1, weight=1)

        # Import / Export label
        import_export_label = Label(
            import_export_frame,
            text='IMPORT / EXPORT',
            font=('Helvetica', 16)
        )
        import_export_label.grid(row=0, column=0, sticky=W, columnspan=2)

        # Import button
        self.__import_button = Button(import_export_frame,
                                      text="Import Maze",
                                      bg=self.__COLOUR_IMPORT_MAZE_BUTTON,
                                      command=self.__handle_import)
        self.__import_button.grid(row=1, column=0, sticky=EW)

        # Export button
        self.__export_button = Button(import_export_frame,
                                      text="Export Maze",
                                      bg=self.__COLOUR_EXPORT_MAZE_BUTTON,
                                      command=self.__handle_export)
        self.__export_button.grid(row=1, column=1, sticky=EW)

    def __initialize_stats_frame(self, master):
        ''' Initializes the stats frame which is a child of the control frame.

        Args:
            master::[tk.Frame]
                The parent frame of this frame (the control frame)

        Returns:
            None
        '''
        # The stats frame itself
        stats_frame = Frame(master)
        stats_frame.pack(anchor=W, padx=20, pady=20, fill=X)

        # Allow grid components to fill the width of the frame
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=5)

        # Stats label
        stats_label = Label(
            stats_frame,
            text='STATS',
            font=('Helvetica', 16)
        )
        stats_label.grid(row=0, column=0, sticky=W, columnspan=2)

        # Unsolved label
        self.unsolved_label_var = StringVar()
        unsolved_static_label = Label(
            stats_frame,
            text='# Unsolved Nodes',
            bg=self.__COLOUR_UNSOLVED,
            anchor=W
        )
        unsolved_static_label.grid(row=1, column=0, sticky=EW)

        unsolved_dynamic_label = Label(
            stats_frame,
            textvariable=self.unsolved_label_var
        )
        unsolved_dynamic_label.grid(row=1, column=1, sticky=W)

        # Solved label
        self.solved_label_var = StringVar()
        solved_static_label = Label(
            stats_frame,
            text='# Solved Nodes',
            bg=self.__COLOUR_SOLVED,
            anchor=W
        )
        solved_static_label.grid(row=2, column=0, sticky=EW)

        solved_dynamic_label = Label(
            stats_frame,
            textvariable=self.solved_label_var
        )
        solved_dynamic_label.grid(row=2, column=1, sticky=W)

        # Path label
        self.path_label_var = StringVar()
        path_static_label = Label(
            stats_frame,
            text='# Path Nodes',
            bg=self.__COLOUR_PATH,
            anchor=W
        )
        path_static_label.grid(row=3, column=0, sticky=EW)

        path_dynamic_label = Label(
            stats_frame,
            textvariable=self.path_label_var
        )
        path_dynamic_label.grid(row=3, column=1, sticky=W)

        # Elapsed time label
        self.elapsed_label_var = StringVar()
        elapsed_time_static_label = Label(
            stats_frame,
            text='Elapsed Time (s)'
        )
        elapsed_time_static_label.grid(row=4, column=0, sticky=W)

        elapsed_time_dynamic_label = Label(
            stats_frame,
            textvariable=self.elapsed_label_var
        )
        elapsed_time_dynamic_label.grid(row=4, column=1, sticky=W)

    def __initialize_help_frame(self, master):
        # The help frame itself
        help_frame = Frame(master)
        help_frame.pack(anchor=W, padx=20, pady=20, fill=X)

        # Allow grid components to fill the width of the frame
        help_frame.grid_columnconfigure(0, weight=1)
        help_frame.grid_columnconfigure(1, weight=1)

        # Help label
        help_label = Label(help_frame, text='HELP', font=('Helvetica', 16))
        help_label.grid(row=0, column=0, sticky=W, columnspan=2)

        # How to Use button
        self.__how_to_use_button = Button(help_frame,
                                          text='How to Use',
                                          bg=self.__COLOUR_HOW_TO_USE_BUTTON,
                                          command=lambda title='How to Use', message=self.__DIALOG_MESSAGES['help']: self.__show_info_dialog(title, message))
        self.__how_to_use_button.grid(row=1, column=0, sticky=EW)

        # About button
        self.__about_button = Button(help_frame,
                                     text='About',
                                     bg=self.__COLOUR_ABOUT_BUTTON,
                                     command=lambda title='About', message=self.__DIALOG_MESSAGES['about']: self.__show_info_dialog(title, message))
        self.__about_button.grid(row=1, column=1, sticky=EW)

    def __initialize_grid_frame(self):
        self.grid_frame = Frame(self,
                                height=self.__GRID_DIM_WIDTH,
                                width=self.__GRID_DIM_WIDTH,
                                highlightbackground='gray',
                                highlightthickness=3)

        # Create blank canvas
        self.canvas = Canvas(self.grid_frame,
                             height=self.__GRID_DIM_WIDTH,
                             width=self.__GRID_DIM_WIDTH,
                             bg='white')

        self.canvas.pack()
        self.grid_frame.pack(side=LEFT)

        # Colour the entire grid initially
        self.__POS_TO_SQUARE = {}

        all_indices = [(x, y) for x in range(self.model.get_nrow())
                       for y in range(self.model.get_ncol())]

        self.update_gui(maze=self.model.get_curr_maze(),
                        diff_positions=all_indices,
                        is_rapid_config=False)

    '''
    GUI HANDLERS.
    '''

    def __handle_reconfigure(self, is_importing=False, loaded_maze=None):

        def reconfiguration_thread():
            # Disable mouse and keyboard events
            self.__is_reconfiguring = True

            # Change the grid width slider before the GUI is disabled
            if is_importing:
                # Move the grid width slider to the new grid width
                self.grid_width_slider.set(loaded_maze['gridWidth'])

                # Update the grid width label
                self.grid_width_label.configure(
                    text='Grid width: {}'.format(self.grid_width_slider.get()))

            # Disable interactive GUI components
            self.__disable_gui()

            # Set the new grid width to the one in the imported file if importing, otherwise use the slider value
            print('{}...'.format(
                'Importing maze' if is_importing else 'Reconfiguring'))

            new_width = loaded_maze['gridWidth'] if is_importing else int(
                self.grid_width_slider.get())

            # Replace the Reconfigure button with the progress bar
            self.__reconfigure_button.grid_remove()
            self.__progress_bar.grid(row=3, column=0, sticky=EW, columnspan=2)
            self.__progress_bar.start()

            # The long reconfiguration task
            reconfigure(new_width=new_width,
                        is_importing=is_importing,
                        loaded_maze=loaded_maze)

            # Replace the progress bar with the Reconfigure button
            self.__progress_bar.stop()
            self.__progress_bar.grid_forget()
            self.__reconfigure_button.grid(
                row=3, column=0, sticky=EW, columnspan=2)

            # Re-enable mouse and keyboard events
            self.__is_reconfiguring = False

            # Re-enable interactive GUI components
            self.__enable_gui()

            print('{} complete!'.format(
                'Import' if is_importing
                else 'Reconfiguration'))

            # Show success dialog
            self.__show_info_dialog(
                title='{} Complete'.format(
                    'Import' if is_importing else 'Reconfiguration'),
                message='Successfully {} a {} x {} maze!'.format('imported' if is_importing else 'configured',
                                                                 self.model.get_nrow(),
                                                                 self.model.get_ncol()))

        def reconfigure(new_width, is_importing, loaded_maze):
            # Recreate the backing model and redraw the GUI
            self.__initialize_model(new_width, new_width)
            self.__POS_TO_SQUARE = {}
            self.canvas.delete('all')

            # Colour the entire grid initially
            all_indices = [(x, y) for x in range(self.model.get_nrow())
                           for y in range(self.model.get_ncol())]

            self.update_gui(maze=self.model.get_curr_maze(),
                            diff_positions=all_indices,
                            is_rapid_config=False)

            # Update model with the imported data if the reconfiguration was triggered by an import
            if is_importing and loaded_maze is not None:
                self.model.import_maze_data(loaded_maze)

        # Make sure that the solver is stopped
        if not self.model.is_solving():
            # Display confirmation dialog
            is_reconfiguring = messagebox.askyesno(title='Reconfigure',
                                                   message=('Are you sure you want to reconfigure?\n'
                                                            'All walls will be erased.'),
                                                   icon='warning')
            if is_reconfiguring == YES:
                threading.Thread(target=reconfiguration_thread).start()
        else:
            messagebox.showerror(title='Failed to Reconfigure',
                                 message='Cannot reconfigure while the solver is running.')

    def __handle_grid_width_slider_change(self, event):
        self.grid_width_label.configure(
            text='Grid width: {}'.format(self.grid_width_slider.get()))

    def __handle_cb(self):
        for k, v in self.cb_values.items():
            self.model.set_setting(k, bool(v.get()))

    def __handle_show_grid_lines(self):
        # Determine outline colour
        outline_colour = 'gray' if self.show_grid_lines.get() else ''

        # Colour all square outlines
        for pos in self.__POS_TO_SQUARE:
            square = self.__POS_TO_SQUARE[pos]
            self.canvas.itemconfig(square, outline=outline_colour)

    def __handle_import(self):
        if not self.model.is_solving():
            # Display load file dialog
            filename = filedialog.askopenfilename(parent=self,
                                                  title='Import Maze',
                                                  initialdir=os.getcwd() + '/sample_mazes')

            if filename != '':
                try:
                    # Read the contents of the file
                    with open(filename, 'r') as file:
                        content = file.readlines()

                    # Assign the file contents to a dictionary
                    loaded_maze = json.loads(content[0])

                    # Reconfigure the maze using the imported data
                    self.__handle_reconfigure(
                        is_importing=True, loaded_maze=loaded_maze)
                except:
                    print('Failed to import maze from {}: Incompatible or corrupted file'.format(
                        filename))

    def __handle_export(self):
        if not self.model.is_solving():
            # Display save file dialog
            filetypes = [('JSON', '*.json')]
            filename = filedialog.asksaveasfilename(parent=self,
                                                    title='Export Maze',
                                                    initialfile='my_astar_maze',
                                                    defaultextension='.json',
                                                    filetypes=filetypes)

            # Prepare the current maze configuration data
            curr_maze = {
                'gridWidth': self.model.get_nrow(),
                'start': self.model.get_start(),
                'end': self.model.get_end(),
                'walls': list(self.model.get_walls())
            }

            # Write to the file
            if filename != '':
                with open(filename, 'w') as file:
                    file.write(json.dumps(curr_maze))
                print('Successfully exported maze configuration to {}.'.format(filename))

    '''
    EVENT HANDLERS.
    '''

    def __on_m1_down(self, event):
        self.__handle_mouse_down(event, True)

    def __on_m3_down(self, event):
        self.__handle_mouse_down(event, False)

    def __handle_mouse_down(self, event, is_setting_wall):
        def is_event_pos_valid():
            return 0 <= event.x <= self.__GRID_DIM_WIDTH and 0 <= event.y <= self.__GRID_DIM_WIDTH

        def calculate_square_pos():
            square_pos_x = int(event.x // self.__SQUARE_WIDTH)
            square_pos_y = int(event.y // self.__SQUARE_WIDTH)
            return (square_pos_x, square_pos_y)

        # Validate that the solver is stopped, the GUI is not reconfiguring, and the position is good
        if (not self.model.is_solving()
            and not self.__is_reconfiguring
            and event.widget == self.canvas
                and is_event_pos_valid()):

            square_pos = calculate_square_pos()

            if self.__EDIT_MODE['setStart']:
                self.model.set_start(square_pos)
            elif self.__EDIT_MODE['setEnd']:
                self.model.set_end(square_pos)
            else:
                self.model.set_wall(square_pos, is_setting_wall)

    def __on_key_press(self, event):
        ''' Hanldes keyboard events.

        [space] - Start / stop the solver
        [Esc] - Quit the application
        [S] - Toggle set start node
        [E] - Toggle set end node

        Args:
            event::[tkinter.Event]
                The keyboard event.

        Returns:
            None
        '''
        key_code = event.keysym

        # Only handle keyboard events when the GUI is not reconfiguring
        if not self.__is_reconfiguring:

            # Press [space] to start / stop the solver
            if key_code == 'space':
                self.__toggle_solver()

            # Press [Esc] to quit the application
            elif key_code == 'Escape':
                if not self.model.is_solving():
                    # Display confirmation dialog
                    is_quitting = messagebox.askyesno(title='Exit Application',
                                                      message='Are you sure you want to exit the application?',
                                                      icon='warning')
                    if is_quitting == YES:
                        print('Closing application...')
                        self.destroy()
                else:
                    print(
                        'Cannot close the application while the solver is running.')
                    messagebox.showerror(title='Failed to Close Application',
                                         message='Cannot close the application while the solver is running.')

            # Edit mode toggles
            elif key_code == 's':
                self.__EDIT_MODE['setStart'] = True
            elif key_code == 'e':
                self.__EDIT_MODE['setEnd'] = True

    def __on_key_release(self, event):
        key_code = event.keysym

        if key_code == 's':
            self.__EDIT_MODE['setStart'] = False
        elif key_code == 'e':
            self.__EDIT_MODE['setEnd'] = False

    def __handle_wall_click(self, pos):
        self.model.set_wall(pos, True)

    '''
    UTILITY METHODS.
    '''

    def __toggle_solver(self):
        if not self.model.is_solving():
            # Disable everything in the GUI except the Start / Stop button and the Show grid lines Checkbutton
            self.__disable_gui()
            self.start_stop_button.configure(state=NORMAL)
            self.__cb_grid_lines.configure(state=NORMAL)
            self.model.solve()
        else:
            print('Solver stopped.')
            self.__enable_gui()
            self.model.stop_solving()

    def __disable_gui(self):
        for component in self.__interactive_gui_components:
            component.configure(state=DISABLED)

    def __enable_gui(self):
        for component in self.__interactive_gui_components:
            component.configure(state=NORMAL)

    def __show_info_dialog(self, title, message):
        messagebox.showinfo(title, message)

    def __show_error_dialog(self, title, message):
        messagebox.showerror(title, message)

    '''
    UPDATE METHOD.
    '''

    def __calculate_square_width(self):
        # Update the square width depending on the new model
        self.__SQUARE_WIDTH = self.__GRID_DIM_WIDTH / self.model.get_nrow()

    def update_gui(self, maze, diff_positions, is_rapid_config):
        ''' Updates the GUI by colouring the grid labels contained in diff_indices according to the maze symbols.
        Also updates the stats frame.

        Args:
            maze::[list[list]]
                A 2D array containing symbols that represent the maze
            diff_indices::[list]
                A list containing the positions of nodes that have changed since the previous update

        Returns:
            None
        '''
        # Configure the Start / Stop button to display the appropriate text and colour
        if self.model.is_solving():
            self.start_stop_button.configure(text='STOP', bg='salmon')
        elif not self.__is_reconfiguring:
            # Re-enable the GUI if the solver is done
            self.__enable_gui()
            self.start_stop_button.configure(text='START', bg='pale green')

        # Update the square width based on the current number of rows in the model
        self.__calculate_square_width()

        # Determine outline colour
        outline_colour = 'gray' if self.show_grid_lines.get() else ''

        # Update grid by colouring the appropriate square
        for (x, y) in diff_positions:

            # Create a square at (x, y) if it does not yet exist
            if (x, y) not in self.__POS_TO_SQUARE:
                square = self.canvas.create_rectangle(x * self.__SQUARE_WIDTH,
                                                      y * self.__SQUARE_WIDTH,
                                                      (x + 1) *
                                                      self.__SQUARE_WIDTH,
                                                      (y + 1) *
                                                      self.__SQUARE_WIDTH,
                                                      fill=self.__SYMBOL_TO_COLOUR[maze[x][y]],
                                                      outline=outline_colour,
                                                      tag='to-delete')
                self.__POS_TO_SQUARE[(x, y)] = square

            # Configure the square at (x, y) since it exists
            else:
                self.canvas.itemconfig(self.__POS_TO_SQUARE[(
                    x, y)], fill=self.__SYMBOL_TO_COLOUR[maze[x][y]])

        # Update stats
        self.unsolved_label_var.set(str(self.model.get_stat('numUnsolved')))
        self.solved_label_var.set(str(self.model.get_stat('numSolved')))
        self.path_label_var.set(str(self.model.get_stat('numPath')))
        self.elapsed_label_var.set(str(self.model.get_stat('elapsedTime')))

        # Handle GUI updates differently if the update is caused by a wall config or not
        if is_rapid_config:
            # update_idletasks() prevents fatal crashes when setting / removing nodes rapidly
            self.update_idletasks()
        else:
            # update() allows the user to stop the solver and prevents calls to model.solve() from queueing
            self.update()


def main():
    print('Starting application...')
    app = AStarView()
    app.mainloop()


if __name__ == '__main__':
    main()
