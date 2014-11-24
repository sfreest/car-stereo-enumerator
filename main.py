# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.base import runTouchApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.factory import Factory
from kivy.properties import (ObjectProperty, ListProperty, StringProperty)
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from functools import partial
from kivy.logger import Logger
from kivy.uix.behaviors import ButtonBehavior

import os, glob, pickle, string

class ProfileManager():
    
    """
        self.list_of_profiles contains list of dictionaries with 
        the following structure:
        ('name' : string                      # name of the profile, 
         'db_name' : string                   # name of file with the database of tracks,
         'path_to_removable_media' : string   # path to removable media
         'activate_search' : boolean          # if true, default track list output is search, else is list of tracks
         'default_profile' : boolean          # usually last used profile should be loaded by default)
    """
    
    def __init__(self,path_to_profiles='./.profiles'):
        
        self.active_profile = {}
        self.load_profiles()

    def profiles_path_exists(self, path_to_profiles='./.profiles'):
        
        """
            Checks existence of profile directory and try to create it if not.
        """
        if not os.path.exists(path_to_profiles) or not os.path.isdir(path_to_profiles):
            
            try:
                os.makedirs(path_to_profiles)
                return True
            
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
                return False
        else:
            return True

    def load_profiles(self, path_to_profiles='./.profiles', profile_filename='.profilelist.pfl'):
        """
            Loads profile from file
        """

        if self.profiles_path_exists(path_to_profiles):
            
            if os.path.exists(os.path.join(path_to_profiles,profile_filename)):
                
                f = open(os.path.join(path_to_profiles,profile_filename),'rb')
                self.list_of_profiles = pickle.load(f)
                f.close()
            
            else:
                self.list_of_profiles = []
    
    def save_profiles(self, path_to_profiles='./.profiles', profile_filename='.profilelist.pfl'):
        """
            Saves profile to file 
        """
        if self.profiles_path_exists(path_to_profiles):
            
            f = open(os.path.join(path_to_profiles,profile_filename),'wb+')
            pickle.dump(self.list_of_profiles,f)
            f.close()
    
    def create_new_profile(self, profile_name, path_to_removable_media, path_to_profiles='./.profiles'):
        """
            Creates new profile:
                profile_name: string               #name of profile
                path_to_removable_media: string:   #path to folder with tracks to manage
        """

        #Make every profile not default, last loaded profile (in this case is new one) will become default.
        for prof in self.list_of_profiles:
            prof['default_profile'] = False
        
        #Adding new profile
        self.list_of_profiles.append({'name' : profile_name,
                                      'db_name' : '.' + profile_name + '.tdb',
                                      'path_to_removable_media' : path_to_removable_media,
                                      'default_profile' : True,
                                      'activate_search' : False})
        self.save_profiles()

    def delete_profile(self, profile_name):
        """
            Deletes profile
        """
        #Using list slice [:] to have list bu value, not pointer to it.
        self.list_of_profiles[:] = [tup for tup in self.list_of_profiles if tup['name'] != profile_name]
        self.save_profiles()

    def get_profile(self, profile_name):
        """
            Returns profile by name
        """
        profile = {}
        
        for current_profile in self.list_of_profiles:
            if current_profile['name'] == profile_name:
                profile = current_profile
        return profile

    def get_default_profile(self):
        """
            Returns default profile
        """
        profile = {}
        
        for current_profile in self.list_of_profiles:
            if current_profile['default_profile'] == True:
                profile = current_profile
        return profile

class TrackListManager():
    """
        self.track_list contains list of dictionaries with 
        the following structure:
        ('folder_name' : string               # name of the folder, containig tracks, 
         'tracks' : list                      # list of lists with the following structure:
                                                ['filename of track':string, 'delete_mark':boolean]
    """
    
    def __init__(self, path_to_profiles='./.profiles/'):
        
        self.active_folder = ''
        self.track_list = []

    def profiles_path_exists(self, path_to_profiles='./.profiles'):
        """
            Checks existence of profile directory and try to create it if not.
        """
        
        if not os.path.exists(path_to_profiles) or not os.path.isdir(path_to_profiles):
            
            try:
                
                os.makedirs(path_to_profiles)
                return True
            
            except OSError as exception:
                
                if exception.errno != errno.EEXIST:
                    raise
                
                return False
        
        else:
            return True
        
    def create_new_track_list(self, path_to_removable_media, track_list_filename, 
                              screenmanager_widget,  path_to_profiles='./.profiles'):
        """
            Creates new track list. 
                path_to_removable_media: string              #path to folder with manageble tracks
                track_list_filename: string                  #file where track list will be saved
                screenmanager_widget: ScreenManager object   #if passed screen with loading progress will be shown
        """


        def clear_file_names(path_to_removable_media):
            """
                function clears tracks' filenames from not allowed characters
            """

            #allowed_chars contains allowed for filenames characters in unicode
            allowed_chars = string.digits + string.letters + '.- '
            allowed_chars = unicode(allowed_chars)
            allowed_chars = allowed_chars + u'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя'
            
            path_to_removable_media = unicode(path_to_removable_media)
            
            if os.path.exists(path_to_removable_media):

                #iterating only top level folders (car stereo can't see more deep hierarchy)
                for folder in os.listdir(path_to_removable_media):
                    
                    path = os.path.join(path_to_removable_media, folder)
                    if os.path.isdir(path):

                        #iterating tracks in folder:
                        for track in os.listdir(path):
                            
                            new_file_name = track
                            
                            if new_file_name.endswith(('.mp3','.wav','.aac','.flac','.wma'),) and \
                            os.path.isfile(os.path.join(path, track)):

                                #remove every not allowed character from filename
                                new_file_name = filter(allowed_chars.__contains__, new_file_name)
                                
                                #if there was not allowed characters, should rename track
                                if new_file_name <> track:

                                    previous_path_to_file = os.path.join(path, track)
                                    
                                    new_path_to_file = os.path.join(path, new_file_name)
                                    
                                    #checking another file haven't same file name after deleting not allowed characters
                                    while os.path.exists(new_path_to_file):

                                        #split filename and extension
                                        tmp_file_name, tmp_file_extension = os.path.splitext(new_path_to_file)
                                        new_path_to_file = tmp_file_name + u'-RENAMED' + tmp_file_extension
                                                                            
                                    os.rename(previous_path_to_file, new_path_to_file)

######################End of clear_file_names()###################################################################################################                            

        #if passed screen with loading progress will be shown
        if screenmanager_widget != None:
            show_load_widget = True
            trackscanscreen = screenmanager_widget.get_screen('trackscanscreen')

        path_to_removable_media = unicode(path_to_removable_media)

        if self.profiles_path_exists(path_to_profiles):
            if os.path.exists(path_to_removable_media):
                
                if show_load_widget:
                    screenmanager_widget.current = 'trackscanscreen'

                #delete not allowed characters from filenames
                clear_file_names(path_to_removable_media)
                

                #Collecting folders for progress bar:
                for folder in os.listdir(path_to_removable_media):
                    path = os.path.join(path_to_removable_media, folder)
                    if os.path.isdir(path):
                        self.track_list.append({'folder_name':folder, 'tracks':[]})
                
                #Progress bar:
                if show_load_widget:
                    trackscanscreen.ids.progress_bar_scan.max = len(self.track_list)
                
                #Iterating collected folders:
                for element in self.track_list:

                    if show_load_widget:
                        trackscanscreen.ids.trackscanscreen_current_scanning_folder.text = \
                        'Now scanning: ' + path_to_removable_media + element['folder_name']
                        trackscanscreen.ids.progress_bar_scan.value = self.track_list.index(element)

                    current_folder_tracks = []
                    current_path = os.path.join(path_to_removable_media, element['folder_name'])
                    
                    #Collecting tracks:
                    for track in os.listdir(current_path):
                        
                        #Need only musical files with certain extensions                        
                        if track.endswith(('.mp3','.wav','.aac','.flac','.wma'),) and \
                        os.path.isfile(os.path.join(current_path, track)):

                            current_folder_tracks.append([track, False])
                    #Adding list of tracks to dict {'folder_name':string, 'tracks':[]}
                    element['tracks'] = current_folder_tracks

                #save tracks structure
                self.save_track_list(track_list_filename)

                #return True will stop bubbling on_release event 
                return True
               

    def save_track_list(self, track_list_filename, path_to_profiles='./.profiles'):
        """
            Saves track list structure to track_list_filename
        """

        if self.profiles_path_exists(path_to_profiles):
            f = open(os.path.join(path_to_profiles,track_list_filename),'wb+')
            pickle.dump(self.track_list,f)
            f.close()

    def load_track_list(self, track_list_filename, path_to_profiles='./.profiles'):
        """
            Loads track list structure from track_list_filename
        """
        
        if self.profiles_path_exists(path_to_profiles):
            if os.path.exists(os.path.join(path_to_profiles,track_list_filename)):
                f = open(os.path.join(path_to_profiles,track_list_filename),'rb')
                self.track_list = pickle.load(f)
                f.close()

    def choose_tracklist(self, track_list_filename, path_to_removable_media,
                        screenmanager_widget=None, path_to_profiles='./.profiles'):
        """
            If tracks structure earlier was scanned and save - loads it, else creating new one and saving it.
            Handler for button_profile_ok on ProfileScreen
        """
        if self.profiles_path_exists(path_to_profiles):
            
            if os.path.exists(os.path.join(path_to_profiles,track_list_filename)):
                self.load_track_list(track_list_filename)
            else:
                self.create_new_track_list(path_to_removable_media,track_list_filename, screenmanager_widget)

    def get_current_tracklist_in_folder_name(self, folder_name):
        """
            Returns tracks structure ([track_filename:String, mark_to_delete:Boolean]) for folder_name
        """
        
        for tr_rec in self.track_list:
            if tr_rec['folder_name'] == folder_name:
                return tr_rec['tracks']
        return []

class CLabel(ButtonBehavior, Label):
    bgcolor = ListProperty([0,0,0])

class DigitInput(TextInput):
    """
        TextInput which allows entering only digits
    """
    def insert_text(self, substring, from_undo=False):
        
        digit_range = [str(i) for i in range(10)]
    
        if substring not in digit_range:
            s = ''
        else:
            s = substring  
        return super(DigitInput, self).insert_text(s, from_undo=from_undo)

class BaseScreenManager(ScreenManager):
    pass

class TrackScanScreen(Screen):
    pass

class MainScreen(Screen):

    def __init__(self,**kwargs):
        
        super(MainScreen,self).__init__(**kwargs)
        
        #used to show count of tracks in folder
        self.total_counter = 0

        #used to show number of tracks marked for deleting
        self.marked_to_del = 0

        #background color of Clabel object wich showing tracks marked for delete
        self.bgcolor_marked = [1,.6,.2]
        #text color of Clabel object wich showing tracks marked for delete
        self.textcolor_marked = [0,0,0]

        #color of Clabel object wich showing tracks NOT marked for delete
        self.bgcolor = [.2,.2,.2]
        #text color of Clabel object wich showing tracks NOT marked for delete
        self.textcolor_marked = [0,0,0]
        self.textcolor = [.5,.5,.5]
    
    def on_pre_enter(self):

        #lets this Screen widget to load fully before any actions (prevents bug when children widgets
        #yet is not loaded but progammed actions for it begins, what couses crashes)    
        if not self.name:
            Clock.schedule_once(lambda dt: self.on_pre_enter())
            return
        
        #when coming to this screen folders buttons shoul be shown
        if manager_of_profile_list.active_profile != {}:
            manager_of_track_list.active_folder = ''
            self.generate_folder_buttons()

    def switch_show_search(self):
        """
            Handler for show search CheckBox
            Switches tracks view between list of tracks and search string.
            Also saves this chose to profile fot default output
        """
        
        if self.ids.checkbox_show_search.active:
            
            manager_of_profile_list.active_profile['activate_search'] = self.ids.checkbox_show_search.active
            manager_of_profile_list.save_profiles()
            if manager_of_track_list.active_folder != '':
                self.generate_track_search_output()
            
            return True   
        
        else:
            
            manager_of_profile_list.active_profile['activate_search'] = self.ids.checkbox_show_search.active
            manager_of_profile_list.save_profiles()
            if manager_of_track_list.active_folder != '':       
                self.generate_track_list_output()
            
            return True

    def mark_track_to_delete(self, track_dict, current_label):
        """
            Marks cliked track for deleting
            track_dict:        [trackname, mark_to_delete] in manager_of_track_list{folder_name}[tracklist]
            current_label:     Cliced Label widget 
        """
        #if view is list of tracks, header text will be updated
        update_header = not manager_of_profile_list.active_profile['activate_search']        

        if track_dict[1] == True: #If marked to delete, should unmark
            
            #header text counter
            self.marked_to_del -= 1
            
            #change bg_color
            current_label.bgcolor = self.bgcolor
            
            #change mark_to_delete to False
            track_dict[1] = not track_dict[1]
            
            #update header text
            if update_header:
                self.ids.mainscreen_header.text = '[%s]: total: [%s], del: [%s]' % \
                    (manager_of_track_list.active_folder, str(self.total_counter), str(self.marked_to_del))
            
            #save tracklist
            manager_of_track_list.save_track_list(manager_of_profile_list.active_profile['db_name'])
        
        else:
            
            #header text counter   
            self.marked_to_del += 1
            
            #change bg_color
            current_label.bgcolor = self.bgcolor_marked
            
            #change mark_to_delete to False
            track_dict[1] = not track_dict[1]
            
            #update header text
            if update_header:
                self.ids.mainscreen_header.text = '[%s]: total: [%s], del: [%s]' % \
                    (manager_of_track_list.active_folder, str(self.total_counter), str(self.marked_to_del))
            
            #save tracklist
            manager_of_track_list.save_track_list(manager_of_profile_list.active_profile['db_name'])   

        return True


    def generate_track_view(self, button_object):
        """
            Handles click to button folder, shows track list or track searcher due to
            activate_search CheckBox
            button_object: clicked Button object
        """

        #set folder at Button object text as active
        manager_of_track_list.active_folder = button_object.text

        #if search activated will show search text input:
        if manager_of_profile_list.active_profile['activate_search']:
            self.generate_track_search_output()

        #if search not activated will show list of tracks
        else:
            self.generate_track_list_output()            

    def show_finded_track(self, button_object):
        """
            Shows finded track (in serach mode)
        """
        
        #Find dynamicaly created widgets by ids:
        children = self.children[:]
        while children:
            child = children.pop()
            if child.id == 'digitinput_search':
                digitinput_search = child
            if child.id == 'grid_for_track_output':
                grid_for_track_output = child
            children.extend(child.children)

        #Clear earlier found track
        grid_for_track_output.clear_widgets()

        #get list ot tracks and delete marks in active folder
        tracks_in_folder = manager_of_track_list.get_current_tracklist_in_folder_name(manager_of_track_list.active_folder)

        if digitinput_search.text == "":
            return

        index_of_track = int(digitinput_search.text) - 1

        #do nothing if typed number of track not in list
        if (index_of_track >= 0 and index_of_track < len(tracks_in_folder)):
            
            tr = tracks_in_folder[index_of_track]
            
            #SHOW FINDED TRACK:

            #tr[1] contains delete mark
            if tr[1] == True:

                lb_text = '[b][size=50]' + str(index_of_track + 1) + '[/size][/b]' + ' ' + tr[0]

                lb = CLabel(text=lb_text, bgcolor=self.bgcolor_marked)
                lb.bind(on_release=partial(self.mark_track_to_delete, tr))
                grid_for_track_output.add_widget(lb)
            
            else:
                
                lb_text = '[b][size=50]' + str(index_of_track + 1) + '[/size][/b]' + ' ' + tr[0]

                lb = CLabel(text=lb_text, bgcolor=self.bgcolor)
                lb.bind(on_release=partial(self.mark_track_to_delete, tr))
                grid_for_track_output.add_widget(lb)

        #update header
        self.ids.mainscreen_header.text = '[%s]' % (manager_of_track_list.active_folder) 
        


    def generate_track_search_output(self):
        """
            Generates search view (when activate_search checkbox is marked)
        """

        #clear main scroll view oputput
        self.ids.mainscreen_default_output.clear_widgets()

        #main scroll view oputput, declared in kv file
        sv = self.ids.mainscreen_default_output

        #declaring root boxlayot on scroll view
        blo_root = BoxLayout(id='box_layout_root_in_scroll_view',
                            size_hint=(1,1), orientation='vertical', padding=[10,10,10,10])
        
        sv.add_widget(blo_root)

        #box layout for serach text input and button 'search'
        blo_search = BoxLayout(size_hint=(1,.2), orientation='horizontal')
        blo_root.add_widget(blo_search)
        
        #text input for number of track
        dgtinpt = DigitInput(id = 'digitinput_search', text='',multiline=False,size_hint=(0.6, 1))
        
        #button for start search
        button_search = Button(text='search',size_hint=(0.4,1))
        button_search.bind(on_release=self.show_finded_track)

        blo_search.add_widget(dgtinpt)
        
        blo_search.add_widget(button_search)

        #grid for finded track output
        grid = GridLayout(id = 'grid_for_track_output', cols=1, spacing=(0,10), size_hint=(1,.8), 
                row_force_default=True, row_default_height=50)

        blo_root.add_widget(grid)

        #update header
        self.ids.mainscreen_header.text = '[%s]' % (manager_of_track_list.active_folder)

    def generate_track_list_output(self):
        """
            Generates list view (when activate_search checkbox is not marked)
        """
        
        #Clear widgets for futher dynamical generating
        self.ids.mainscreen_default_output.clear_widgets()        

        #get list ot tracks and delete marks in active folder
        tracks_in_folder = manager_of_track_list.get_current_tracklist_in_folder_name(manager_of_track_list.active_folder)
        
        #GridLayout for Labels with tracks
        grid = GridLayout(cols=1, spacing=(0,10), size_hint_y=None, 
                padding = [10,10,10,10],row_force_default=True, row_default_height=50)
        #For proper work of ScrollView
        grid.bind(minimum_height=grid.setter('height'))
        
        #counters for header
        self.total_counter = 0
        self.marked_to_del = 0

        #Iterating tracks:
        for tr in tracks_in_folder:
            
            track_number = self.total_counter = tracks_in_folder.index(tr) + 1
           
            #DYNAMICLAY GENERATE TRACK LABEL:

            #tr[1] contains delete mark
            if tr[1] == True:

                #for header text
                self.marked_to_del += 1

                lb_text = '[b][size=50]' + str(track_number) + '[/size][/b]' + ' ' + tr[0]

                lb = CLabel(text=lb_text, bgcolor=self.bgcolor_marked)
                lb.bind(on_release=partial(self.mark_track_to_delete, tr))
                grid.add_widget(lb)
            
            else:
                
                lb_text = '[b][size=50]' + str(track_number) + '[/size][/b]' + ' ' + tr[0]

                lb = CLabel(text=lb_text, bgcolor=self.bgcolor)
                lb.bind(on_release=partial(self.mark_track_to_delete, tr))
                grid.add_widget(lb)

        #Show GridLayout with generated Labels
        sv = self.ids.mainscreen_default_output
        sv.add_widget(grid)

        #Upadte header
        self.ids.mainscreen_header.text = '[%s]: total: [%s], del: [%s]' % \
        (manager_of_track_list.active_folder, str(self.total_counter), str(self.marked_to_del))   

    def generate_folder_buttons(self):
        """
            Generate buttons with folder names on MainScreen
        """
        
        #Clear widgets
        self.ids.mainscreen_default_output.clear_widgets()
        
        #No folder choosen when folders are being shown
        manager_of_track_list.active_folder = ''

        #If there is no folders - generate Button for rescan removable media:
        if manager_of_track_list.track_list == []:

            #Grid layout which will contain this button
            grid = GridLayout(cols=1, spacing=50, size_hint_y=None)
            grid.bind(minimum_height=grid.setter('height'))
            
            #Button for rescan
            but = Button(text='Scan removable media' ,strip=True,
                text_size=(300,300),halign='center',valign='middle')
            
            grid.add_widget(but)
            
            #Show
            sv = self.ids.mainscreen_default_output
            sv.add_widget(grid)
            
        else:

            #Grid layout which will contain all folder buttons
            grid = GridLayout(cols=2, spacing=(25,10), size_hint_y=None, 
                padding = [10,10,10,10], row_force_default=True, row_default_height=100)
            grid.bind(minimum_height=grid.setter('height'))
            
            sv = self.ids.mainscreen_default_output
            sv.add_widget(grid)
            
            #Count folders to display it number in header:
            self.total_counter = 0
            
            #Iterating folders: manager_of_track_list.track_list[{'folder_name'}]
            for tr_rec in manager_of_track_list.track_list:

                #header text counter
                self.total_counter += 1

                #folder name for button text
                folder_name = tr_rec['folder_name']
                
                #Create Button
                but = Button(text=folder_name, size_hint_y=None,
                halign='center',valign='middle')
                but.bind(on_release=self.generate_track_view)
                
                grid.add_widget(but)
            
            #update header
            self.ids.mainscreen_header.text = 'Folders: %s' % str(self.total_counter)

            
    def delete_marked_files(self):
        """
            Deletes marked tracks psisicaly
        """

        def delete_track_phisicaly(path_to_removable_media, folder_name, track_dict):

            if track_dict[1] == False:
                return False

            try:
                os.remove(os.path.join(path_to_removable_media, folder_name, track_dict[0]))
                return True
            except:
                return False

#############end of delete_marked_files()####################################################################

        #root folder:
        path_to_removable_media = manager_of_profile_list.active_profile['path_to_removable_media']
        
        #file name of saved track list
        track_list_filename = manager_of_profile_list.active_profile['db_name']

        if not os.path.exists(path_to_removable_media):
            return

        #Iteratin folders:
        for rec in manager_of_track_list.track_list:
            
            folder_name = rec['folder_name']

            #If track marked for delete, delete_track_phisicaly() will delete it and track will not
            #be stored in new list of tracks rec['tracks'][:] (slice used for store value, not pointer)
            rec['tracks'][:] = [tup for tup in rec['tracks'] if not delete_track_phisicaly(path_to_removable_media, folder_name, tup)]

        #save new tracklist after deleting
        manager_of_track_list.save_track_list(track_list_filename)

        #show folder buttons
        self.generate_folder_buttons()   

class ProfileScreen(Screen):

    def on_pre_enter(self, *args):

        #lets this Screen widget to load fully before any actions (prevents bug when children widgets
        #yet is not loaded but progammed actions for it begins, what couses crashes)
        if not self.name:
            Clock.schedule_once(lambda dt: self.on_pre_enter())
            return

        #Loading profiles' list to let choose one
        manager_of_profile_list.load_profiles()
        list_of_profiles = manager_of_profile_list.list_of_profiles
        
        #Spinner letting choose profile
        profile_spinner = self.ids.profile_spinner
        profile_spinner.generate_spinner_profile_selector(list_of_profiles)

    def button_profile_ok_release(self):
        """
            Handler for button_profile_ok_release
        """
        button_text = self.ids.profile_spinner.text
        if button_text == '' or button_text == None:
            raise ValueError('Profile name is empty')

        if button_text == 'New..':
            self.parent.current = 'newprofilescreen'
        
        else:
            #get choosen profile
            profile = manager_of_profile_list.get_profile(button_text)

            #Load track list or scan if it doesn't exist
            manager_of_track_list.choose_tracklist(profile['db_name'], profile['path_to_removable_media'],self.parent)
            
            #set active profile
            manager_of_profile_list.active_profile = profile

            #switch to main screen
            self.parent.current = 'mainscreen'

    def button_profile_delete_release(self):
        """
            Handler for button_profile_delete
        """

        button_text = self.ids.profile_spinner.text
        
        if button_text == 'New..':
            pass
        
        else:
            manager_of_profile_list.delete_profile(button_text)
            self.on_pre_enter()

class NewProfileScreen(Screen):

    """
        Screen when user creating new profile
    """
    
    #Properties for load dialog
    loadfile = ObjectProperty(None)
    text_input_path_to_removable_media = ObjectProperty(None)
    text_input_new_profile = ObjectProperty(None)

    def on_pre_enter(self):

        #lets this Screen widget to load fully before any actions (prevents bug when children widgets
        #yet is not loaded but progammed actions for it begins, what couses crashes)
        if not self.name:
            Clock.schedule_once(lambda dt: self.on_pre_enter())
            return

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):

        #show load dialog
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Choose folder", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        
        self.text_input_path_to_removable_media.text = path
        self.dismiss_popup()

    def create_new_profile(self):

        self.text_input_new_profile.text = self.text_input_new_profile.text.strip()
        
        #Invalid form input checking
        if self.text_input_new_profile.text == '' or self.text_input_path_to_removable_media.text == '':
            
            popup_error = Popup(title='Error', 
                            content=Label(text='Please, enter profile name and path to removable media.',strip=True,text_size=(self.width*0.45,None)),
                          auto_dismiss=True, size_hint=[.5,.5])
            popup_error.open()
            return
        
        for tup in manager_of_profile_list.list_of_profiles:
            if tup['name'] == self.text_input_new_profile.text or tup['name'] == 'New..':
                popup_error = Popup(title='Error', 
                            content=Label(text='Profile with same name is already exists.',strip=True,text_size=(self.width*0.45,None)),
                          auto_dismiss=True, size_hint=[.5,.5])
                popup_error.open()
                return

        #create new profile with input given
        manager_of_profile_list.create_new_profile(self.text_input_new_profile.text, self.text_input_path_to_removable_media.text)
        self.parent.current = 'profilescreen'

class SpinnerProfileSelect(Spinner):
    
    def __init__(self,**kwargs):
        super(SpinnerProfileSelect,self).__init__(**kwargs)
        #Get list of profiles to disply
        list_of_profiles = manager_of_profile_list.list_of_profiles
        #Generate spinner
        self.generate_spinner_profile_selector(list_of_profiles)

    def generate_spinner_profile_selector(self,list_of_profiles):
        self.values = ()

        #For creating new profile:
        spinner_values = ['New..']
        default_spinner_value = 'New..'

        #dispatching list of profiles to spinner
        for cur_profile in list_of_profiles:
            spinner_values.append(cur_profile['name'])
            if cur_profile['default_profile'] == True:
                default_spinner_value = cur_profile['name'] 
        self.text = default_spinner_value
        self.values = spinner_values 

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None) 

class CarStereoEnumeratorApp(App):
    """docstring for ClassName"""
    def build(self,*args):

        bsm = BaseScreenManager()

        #Get and store default profile
        manager_of_profile_list.active_profile = manager_of_profile_list.get_default_profile()
        
        # If there is no default prifile swtich to profile screen
        # for creating new one
        if manager_of_profile_list.active_profile == {}:
            bsm.current = 'profilescreen'
        #else load track list from default profile
        else:
            manager_of_track_list.load_track_list(manager_of_profile_list.active_profile['db_name'])
            bsm.current = 'mainscreen'
        
        return bsm
        
#Factory for Load Dialog
Factory.register('LoadDialog', cls=LoadDialog)
        
if __name__ == '__main__':
    manager_of_profile_list = ProfileManager()
    manager_of_track_list = TrackListManager()

    CarStereoEnumeratorApp().run()