# This is a part of the external Repeat One Song plugin for Rhythmbox
#
# Author: Eduardo Mucelli Rezende Oliveira
# E-mail: edumucelli@gmail.com or eduardom@dcc.ufmg.br
# Version: 0.2 for Rhythmbox 2.96 to 2.98
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

# This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# This plugin provides the "repeat one song" feature to Rhythmbox
# Active it by clicking on the Repeat one button in the Toolbar,
# by menu Control -> Repeat one, or using Ctrl + E shortcut

from gi.repository import GObject, RB, Peas, Gtk
import os.path, gettext
import rb

# The XML which defines the buttons within the menu bar, toolbar and their respective actions 
ui_str = \
        """
        <ui>
            <menubar name="MenuBar">
                <menu name="ControlMenu" action="Control">
                  <menuitem name="control_menu_repeat_one" action="RepeatOne"/>
                </menu>
            </menubar>
            <toolbar name="ToolBar">
                <placeholder name="ToolBarPluginPlaceholder">
                    <toolitem name="repeat_one" action="RepeatOne"/>
                </placeholder>
            </toolbar>
        </ui>
        """


class RepeatOneSong (GObject.Object, Peas.Activatable):
    __gtype_name__ = 'RepeatOneSong'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        super(RepeatOneSong, self).__init__()

    def switch_repeat_status(self, control):
        # Although there is only one action, it could be used throughout all the code as 'self.action'
        # However, the proper way to proceed it to put the actions within a group then retrieve them with get_action
        action = self.action_group.get_action('RepeatOne')                  # selects the action to repeat the current song
        self.repeat = action.get_active()                                   # indicates whether the button is checked or not
        player = self.shell.props.shell_player
        if self.repeat:
            ret, shuffle, self.repeat_all = player.get_playback_state()
            player.set_playback_state(shuffle, 1)
        else:
            ret, shuffle, repeat_all = player.get_playback_state()
            player.set_playback_state(shuffle, self.repeat_all)

    def switch_repeat_all_status(self, action):
        if not action.get_active() and self.repeat:
            self.repeat = False
            self.repeat_all = 0
            action_repeat_one = self.action_group.get_action('RepeatOne')
            action_repeat_one.set_active(False)

    def load_icon(self):
        """Deals with the addition of the icon into the toolbar. The icon is named as 'repeat-one-song',
           which will be later on used as the last parameter of the gtk.ToggleAction inside generate_ui"""
        icon_file_name = rb.find_plugin_file(self, "icon.svg")
        iconsource = Gtk.IconSource()
        iconsource.set_filename(icon_file_name)
        iconset = Gtk.IconSet()
        iconset.add_source(iconsource)
        iconfactory = Gtk.IconFactory()
        iconfactory.add("repeat-one-song", iconset)
        iconfactory.add_default()

    def generate_ui(self):
        """Define the actions attached to the switch_repeat_status method, the translatable labels, and toolbar button icons
           At the end it is necessary to mixin the XML string to add such features to the RB's UI"""
        self.action_group = Gtk.ActionGroup('RepeatOneActionGroup')         

        # Creates the action toggle
        # RepeatOne (the named action), translatable string of Control menu), translatable string of Toolbar, icon defined above (see load_icon())
        action = Gtk.ToggleAction("RepeatOne", _("Repeat one"), _("Repeat the current song when it's finished"), "repeat-one-song")
        self.action_group.add_action_with_accel(action, "<Control>E")       # add shortcut
        action.connect("activate", self.switch_repeat_status)               # when the button gets triggered

        manager = self.shell.props.ui_manager
        manager.insert_action_group(self.action_group, 0)
        self.uid = manager.add_ui_from_string(ui_str)                       # mixes in defined XML with RB
        manager.ensure_update()

        action = manager.get_action('/ToolBar/Repeat')
        action.connect("activate", self.switch_repeat_all_status)

    def do_activate(self):                                                  # when loading the applet
        self.shell = self.object
        self.db = self.shell.props.db
        self.repeat = False

        self.one_song_state_normal, self.one_song_state_eos = range(2)
        self.one_song_state = self.one_song_state_normal

        self.load_icon()                                                    # necessary load icon first ...
        self.generate_ui()                                                  # ... because it is used here 

        player = self.shell.props.shell_player
        player.connect('playing-song-changed', self.on_song_change)         # changed song, player.do_next() calls on_elapsed_changed
        player.props.player.connect('eos', self.on_gst_player_eos)          # eos -> on_song_change

    def do_deactivate(self):                                                # when unloading applet
        if self.repeat:
            player = self.shell.props.shell_player
            ret, shuffle, repeat_all = player.get_playback_state()
            player.set_playback_state(shuffle, self.repeat_all)

        for attr in (self.db, self.shell, self.repeat,                      # delete global attributes if possible
                     self.one_song_state_normal, self.one_song_state_eos):
            if attr:
                del attr
        manager = self.shell.props.ui_manager
        manager.remove_ui(self.uid)
        manager.remove_action_group(self.action_group)
        manager.ensure_update()

    def on_gst_player_eos(self, gst_player, stream_data, early=0):
        if self.repeat:
            self.one_song_state = self.one_song_state_eos

    def on_song_change(self, player, time):                              # when song has changed ...
        if self.one_song_state == self.one_song_state_eos:
            self.one_song_state = self.one_song_state_normal
            player.do_previous()
