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
    
    """self.list_of_profiles contains list of dictionaries with 
        the following structure:
        ('name' : string                      # name of the profile, 
         'db_name' : string                   # name of file with the database of tracks,
         'path_to_removable_media' : string   # path to removable media
         'activate_search' : boolean          # if true, default track list output is search, else is list of tracks
         'default_profile' : boolean          # usually last used profile should be loaded by default)
    """
    #list_of_profiles = []

    def __init__(self,path_to_profiles='./.profiles'):
        
        self.active_profile = {}
        self.load_profiles()

    def profiles_path_exists(self, path_to_profiles='./.profiles'):
        
        if not os.path.exists(path_to_profiles) or \
        not os.path.isdir(path_to_profiles):
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
        if self.profiles_path_exists(path_to_profiles):
            if os.path.exists(os.path.join(path_to_profiles,profile_filename)):
                f = open(os.path.join(path_to_profiles,profile_filename),'rb')
                self.list_of_profiles = pickle.load(f)
                f.close()
            else:
                self.list_of_profiles = []
    
    def save_profiles(self, path_to_profiles='./.profiles', profile_filename='.profilelist.pfl'):
        if self.profiles_path_exists(path_to_profiles):
            f = open(os.path.join(path_to_profiles,profile_filename),'wb+')
            pickle.dump(self.list_of_profiles,f)
            f.close()
    
    def create_new_profile(self, profile_name, path_to_removable_media, path_to_profiles='./.profiles'):

        for prof in self.list_of_profiles:
            prof['default_profile'] = False
        
        self.list_of_profiles.append({'name' : profile_name,
                                      'db_name' : '.' + profile_name + '.tdb',
                                      'path_to_removable_media' : path_to_removable_media,
                                      'default_profile' : True,
                                      'activate_search' : False})
        self.save_profiles()

    def delete_profile(self, profile_name):

        self.list_of_profiles[:] = [tup for tup in self.list_of_profiles if tup['name'] != profile_name]
        self.save_profiles()

    def get_profile(self, profile_name):
        profile = {}
        for current_profile in self.list_of_profiles:
            if current_profile['name'] == profile_name:
                profile = current_profile
        return profile

    def get_default_profile(self):
        profile = {}
        for current_profile in self.list_of_profiles:
            if current_profile['default_profile'] == True:
                profile = current_profile
        return profile

class TrackListManager():

    """self.track_list contains list of dictionaries with 
        the following structure:
        ('folder_name' : string               # name of the folder, containig tracks, 
         'tracks' : list                      # list of lists with the following structure:
                                                ['filename of track':string, 'delete_mark':boolean]
         
    """
    
    def __init__(self, path_to_profiles='./.profiles/'):
        
        self.active_folder = ''
        self.track_list = []

    def profiles_path_exists(self, path_to_profiles='./.profiles'):
        
        if not os.path.exists(path_to_profiles) or \
        not os.path.isdir(path_to_profiles):
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

        def clear_file_names(path_to_removable_media):

            codepage = 'utf16'
            allowed_chars = string.digits + string.letters + '.- '
            allowed_chars = unicode(allowed_chars)
            allowed_chars = allowed_chars + u'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя'
            
            path_to_removable_media = unicode(path_to_removable_media)
            
            if os.path.exists(path_to_removable_media):

                for folder in os.listdir(path_to_removable_media):
                    
                    path = os.path.join(path_to_removable_media, folder)
                    if os.path.isdir(path):

                        for track in os.listdir(path):
                            
                            new_file_name = track
                            


                            if new_file_name.endswith(('.mp3','.wav','.aac','.flac','.wma'),) and \
                            os.path.isfile(os.path.join(path, track)):

                                new_file_name = filter(allowed_chars.__contains__, new_file_name)
                               
                                Logger.info(track + ' [] ' + new_file_name)
                                if new_file_name <> track:

                                    previous_path_to_file = os.path.join(path, track)
                                    #previos_path_to_file = previos_path_to_file.encode(codepage)

                                    new_path_to_file = os.path.join(path, new_file_name)
                                    #new_path_to_file = new_path_to_file.encode(codepage)

                                    Logger.info('previos_path_to_file:' + previous_path_to_file + str(type(previous_path_to_file)))
                                    #Logger.info('new_path_to_file:' + new_path_to_file + str(type(new_path_to_file)))
                                    #Logger.info('Exists:' + str(os.path.exists(new_path_to_file)))
                                    #Logger.info('new_path_to_file:' + str(os.path.exists(new_path_to_file)))
                                    while os.path.exists(new_path_to_file):
                                        tmp_file_name, tmp_file_extension = os.path.splitext(new_path_to_file)
                                        new_path_to_file = tmp_file_name + u'-RENAMED' + tmp_file_extension
                                        Logger.info('new_path_to_file:' + new_path_to_file + str(type(new_path_to_file)))   
                                    
                                    Logger.info('previos_path_to_file:' + previous_path_to_file + str(type(previous_path_to_file)))
                                    os.rename(previous_path_to_file, new_path_to_file)

######################End of clear_file_names()###################################################################################################                            

        if screenmanager_widget != None:
            show_load_widget = True
            trackscanscreen = screenmanager_widget.get_screen('trackscanscreen')

        path_to_removable_media = unicode(path_to_removable_media)

        if self.profiles_path_exists(path_to_profiles):
            if os.path.exists(path_to_removable_media):
                if show_load_widget:
                    screenmanager_widget.current = 'trackscanscreen'

                clear_file_names(path_to_removable_media)
                

                #Collectiong folders
                for folder in os.listdir(path_to_removable_media):
                    path = os.path.join(path_to_removable_media, folder)
                    if os.path.isdir(path):
                        self.track_list.append({'folder_name':folder, 'tracks':[]})
                
                if show_load_widget:
                    trackscanscreen.ids.progress_bar_scan.max = len(self.track_list)
                
                #Collectiong files:
                for element in self.track_list:

                    if show_load_widget:
                        trackscanscreen.ids.trackscanscreen_current_scanning_folder.text = \
                        'Now scanning: ' + path_to_removable_media + element['folder_name']
                        trackscanscreen.ids.progress_bar_scan.value = self.track_list.index(element)

                    current_folder_tracks = []
                    current_path = os.path.join(path_to_removable_media, element['folder_name'])
                    for track in os.listdir(current_path):

                        
                        if track.endswith(('.mp3','.wav','.aac','.flac','.wma'),) and \
                        os.path.isfile(os.path.join(current_path, track)):

                            current_folder_tracks.append([track, False])

                    element['tracks'] = current_folder_tracks

                self.save_track_list(track_list_filename)

                return True
            else:
                return False

    def save_track_list(self, track_list_filename, path_to_profiles='./.profiles'):

         if self.profiles_path_exists(path_to_profiles):
            f = open(os.path.join(path_to_profiles,track_list_filename),'wb+')
            pickle.dump(self.track_list,f)
            f.close()

    def load_track_list(self, track_list_filename, path_to_profiles='./.profiles'):
        if self.profiles_path_exists(path_to_profiles):
            if os.path.exists(os.path.join(path_to_profiles,track_list_filename)):
                f = open(os.path.join(path_to_profiles,track_list_filename),'rb')
                self.track_list = pickle.load(f)
                f.close()

    def choose_tracklist(self, track_list_filename, path_to_removable_media,
                        screenmanager_widget=None, path_to_profiles='./.profiles'):
        if self.profiles_path_exists(path_to_profiles):
            
            if os.path.exists(os.path.join(path_to_profiles,track_list_filename)):
                self.load_track_list(track_list_filename)
            else:
                self.create_new_track_list(path_to_removable_media,track_list_filename, screenmanager_widget)

    def get_current_tracklist_in_folder_name(self, folder_name):
        
        for tr_rec in self.track_list:
            if tr_rec['folder_name'] == folder_name:
                return tr_rec['tracks']
        return []

class CLabel(ButtonBehavior, Label):
    bgcolor = ListProperty([0,0,0])

class DigitInput(TextInput):
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
        self.total_counter = 0
        self.marked_to_del = 0

        self.bgcolor_marked = [1,.6,.2]
        self.textcolor_marked = [0,0,0]

        self.bgcolor = [.2,.2,.2]
        self.textcolor = [.5,.5,.5]
    
    def on_pre_enter(self):
        if not self.name:
            Clock.schedule_once(lambda dt: self.on_pre_enter())
            return
        if manager_of_profile_list.active_profile != {}:
            manager_of_track_list.active_folder = ''
            self.generate_folder_buttons()

    def switch_show_search(self):
        
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

        #if not current_label.collide_point(*touch.pos):
        #    return
        
        # if main screen is search mode, no need of updating header
        update_header = not manager_of_profile_list.active_profile['activate_search']        

        if track_dict[1] == True: #If marked to delete, should unmark
            
            self.marked_to_del -= 1
            current_label.bgcolor = self.bgcolor
            track_dict[1] = not track_dict[1]
            if update_header:
                self.ids.mainscreen_header.text = '[%s]: total: [%s], del: [%s]' % \
                    (manager_of_track_list.active_folder, str(self.total_counter), str(self.marked_to_del))
            manager_of_track_list.save_track_list(manager_of_profile_list.active_profile['db_name'])
        
        else:
           
            self.marked_to_del += 1
            current_label.bgcolor = self.bgcolor_marked
            track_dict[1] = not track_dict[1]
            if update_header:
                self.ids.mainscreen_header.text = '[%s]: total: [%s], del: [%s]' % \
                    (manager_of_track_list.active_folder, str(self.total_counter), str(self.marked_to_del))
            manager_of_track_list.save_track_list(manager_of_profile_list.active_profile['db_name'])   


        return True


    def generate_track_view(self, button_object):
        manager_of_track_list.active_folder = button_object.text

        if manager_of_profile_list.active_profile['activate_search']:
            self.generate_track_search_output()
        else:
            self.generate_track_list_output()            

    def show_finded_track(self, button_object):
        
        #Find dynamicaly created widgets by ids

        children = self.children[:]
        while children:
            child = children.pop()
            if child.id == 'digitinput_search':
                digitinput_search = child
            if child.id == 'grid_for_track_output':
                grid_for_track_output = child
            
            children.extend(child.children)

        grid_for_track_output.clear_widgets()

        tracks_in_folder = manager_of_track_list.get_current_tracklist_in_folder_name(manager_of_track_list.active_folder)
        index_of_track = int(digitinput_search.text) - 1

        if (index_of_track > 0 and index_of_track < len(tracks_in_folder)):
            
            tr = tracks_in_folder[index_of_track]
           

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

        self.ids.mainscreen_header.text = '[%s]' % (manager_of_track_list.active_folder) 
        


    def generate_track_search_output(self):

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
        
        dgtinpt = DigitInput(id = 'digitinput_search', text='',multiline=False,size_hint=(0.6, 1))
        button_search = Button(text='search',size_hint=(0.4,1))
        button_search.bind(on_release=self.show_finded_track)

        blo_search.add_widget(dgtinpt)
        
        blo_search.add_widget(button_search)

        #grid for finded track output
        grid = GridLayout(id = 'grid_for_track_output', cols=1, spacing=(0,10), size_hint=(1,.8), 
                row_force_default=True, row_default_height=50)

        blo_root.add_widget(grid)

        self.ids.mainscreen_header.text = '[%s]' % (manager_of_track_list.active_folder)

    def generate_track_list_output(self):

        self.ids.mainscreen_default_output.clear_widgets()
        tracks_in_folder = manager_of_track_list.get_current_tracklist_in_folder_name(manager_of_track_list.active_folder)
        
        grid = GridLayout(cols=1, spacing=(0,10), size_hint_y=None, 
                padding = [10,10,10,10],row_force_default=True, row_default_height=50)
        grid.bind(minimum_height=grid.setter('height'))
        
        
        self.total_counter = 0
        self.marked_to_del = 0

        for tr in tracks_in_folder:
            
            track_number = self.total_counter = tracks_in_folder.index(tr) + 1
           

            #tr[1] contains delete mark
            if tr[1] == True:

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

        sv = self.ids.mainscreen_default_output
        sv.add_widget(grid)


        self.ids.mainscreen_header.text = '[%s]: total: [%s], del: [%s]' % \
        (manager_of_track_list.active_folder, str(self.total_counter), str(self.marked_to_del))   

    def generate_folder_buttons(self):
        
        self.ids.mainscreen_default_output.clear_widgets()
        manager_of_track_list.active_folder = ''

        if manager_of_track_list.track_list == []:
            grid = GridLayout(cols=1, spacing=50, size_hint_y=None)
            grid.bind(minimum_height=grid.setter('height'))
            but = Button(text='Scan removable media' ,strip=True,
                text_size=(300,300),halign='center',valign='middle')
            grid.add_widget(but)
            sv = self.ids.mainscreen_default_output
            sv.add_widget(grid)
            but.texture_update()

        else:

            grid = GridLayout(cols=2, spacing=(25,10), size_hint_y=None, 
                padding = [10,10,10,10], row_force_default=True, row_default_height=100)
            grid.bind(minimum_height=grid.setter('height'))
            sv = self.ids.mainscreen_default_output
            sv.add_widget(grid)
            self.total_counter = 0 #Count folders to display it number in header
            for tr_rec in manager_of_track_list.track_list:
                self.total_counter += 1 
                folder_name = tr_rec['folder_name']
                but = Button(text=folder_name, size_hint_y=None,
                halign='center',valign='middle')
                but.bind(on_release=self.generate_track_view)
                grid.add_widget(but)
            self.ids.mainscreen_header.text = 'Folders: %s' % str(self.total_counter)

            return False

    def delete_marked_files(self):

        def delete_track_phisicaly(path_to_removable_media, folder_name, track_dict):

            if track_dict[1] == False:
                return False

            try:
                os.remove(os.path.join(path_to_removable_media, folder_name, track_dict[0]))
                return True
            except:
                return False

        


        path_to_removable_media = manager_of_profile_list.active_profile['path_to_removable_media']
        track_list_filename = manager_of_profile_list.active_profile['db_name']

        if not os.path.exists(path_to_removable_media):
            return

        for rec in manager_of_track_list.track_list:
            
            folder_name = rec['folder_name']

            rec['tracks'][:] = [tup for tup in rec['tracks'] if not delete_track_phisicaly(path_to_removable_media, folder_name, tup)]

        manager_of_track_list.save_track_list(track_list_filename)
        self.generate_folder_buttons()          


class ProfileScreen(Screen):
    
    def on_pre_enter(self, *args):
        if not self.name:
            Clock.schedule_once(lambda dt: self.on_pre_enter())
            return

        
        manager_of_profile_list.load_profiles()
        list_of_profiles = manager_of_profile_list.list_of_profiles
        profile_spinner = self.ids.profile_spinner
        profile_spinner.generate_spinner_profile_selector(list_of_profiles)

    def button_profile_ok_release(self):
        button_text = self.ids.profile_spinner.text
        if button_text == '' or button_text == None:
            raise ValueError('Profile name is empty')

        if button_text == 'New..':
            self.parent.current = 'newprofilescreen'
        else:
            profile = manager_of_profile_list.get_profile(button_text)
            manager_of_track_list.choose_tracklist(profile['db_name'], profile['path_to_removable_media'],self.parent)
            manager_of_profile_list.active_profile = profile
            self.parent.current = 'mainscreen'

    def button_profile_delete_release(self):

        button_text = self.ids.profile_spinner.text
        
        if button_text == 'New..':
            pass
        else:
            manager_of_profile_list.delete_profile(button_text)
            self.on_pre_enter()

class NewProfileScreen(Screen):
    
    loadfile = ObjectProperty(None)
    text_input_path_to_removable_media = ObjectProperty(None)
    text_input_new_profile = ObjectProperty(None)

    def on_pre_enter(self):
        if not self.name:
            Clock.schedule_once(lambda dt: self.on_pre_enter())
            return

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Choose folder", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        #with open(os.path.join(path, filename[0])) as stream:
        #    self.text_input_new_profile.text = stream.read()
        self.text_input_path_to_removable_media.text = path

        self.dismiss_popup()

    def create_new_profile(self):
        self.text_input_new_profile.text = self.text_input_new_profile.text.strip()
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

        manager_of_profile_list.create_new_profile(self.text_input_new_profile.text, self.text_input_path_to_removable_media.text)
        self.parent.current = 'profilescreen'

class SpinnerProfileSelect(Spinner):
    """docstring for ClassName"""
    def __init__(self,**kwargs):
        super(SpinnerProfileSelect,self).__init__(**kwargs)
        list_of_profiles = manager_of_profile_list.list_of_profiles
        self.generate_spinner_profile_selector(list_of_profiles)

    def generate_spinner_profile_selector(self,list_of_profiles):
        self.values = ()
        spinner_values = ['New..']
        default_spinner_value = 'New..'
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

        manager_of_profile_list.active_profile = manager_of_profile_list.get_default_profile()
        if manager_of_profile_list.active_profile == {}:
            bsm.current = 'profilescreen'
        else:
            manager_of_track_list.load_track_list(manager_of_profile_list.active_profile['db_name'])
            bsm.current = 'mainscreen'
        
        return bsm
        

Factory.register('LoadDialog', cls=LoadDialog)
        
if __name__ == '__main__':
    manager_of_profile_list = ProfileManager()
    manager_of_track_list = TrackListManager()

    CarStereoEnumeratorApp().run()