# This is a part of the external Repeat One Song plugin for Rhythmbox
#
# Author: Eduardo Mucelli Rezende Oliveira
# E-mail: edumucelli@gmail.com or eduardom@dcc.ufmg.br
# Version: 0.4 for Rhythmbox 3.0.1 or later
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

# This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# This plugin provides the "repeat one song" feature for Rhythmbox
# Activate the plugin by going on Rhythmbox -> Plugins -> Repeat One Song
# Repeat the current song: menu Edit -> Repeat current song, or using Ctrl + E shortcut

from gi.repository import Gio, GObject, GLib, Peas
# from gi.repository import RB
# import os.path, gettext


class RepeatOneSong (GObject.Object, Peas.Activatable):
    __gtype_name__ = 'RepeatOneSong'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)

    # Controls the flag that indicates whether the toggle 'repeat'
    # is active or not.
    def switch_repeat_status(self, action, parameter):
        action.set_state(GLib.Variant.new_boolean(not action.get_state()))
        self.repeat = action.get_state().get_boolean()
        # player = self.shell.props.shell_player
        # if self.repeat:
        #    ret, shuffle, self.repeat_all = player.get_playback_state()
        #    player.set_playback_state(shuffle, 1)
        # else:
        #    ret, shuffle, repeat_all = player.get_playback_state()
        #    player.set_playback_state(shuffle, self.repeat_all)

    # Looks like there is a bug on gstreamer player and a seg fault
    # happens as soon as the 'eos' callback is called.
    # https://bugs.launchpad.net/ubuntu/+source/rhythmbox/+bug/1239218
    # However, newer Rhythmbox versions do not suffer from it anymore
    def on_gst_player_eos(self, gst_player, stream_data, early=0):
        # EOS signal means that the song changed because the song is over.
        # ie. the user did not explicitly change the song.
        # https://developer.gnome.org/rhythmbox/unstable/RBPlayer.html#RBPlayer-eos
        if self.repeat:
            self.one_song_state = self.one_song_state_eos

    def on_song_change(self, player, time):
        if self.one_song_state == self.one_song_state_eos:
            self.one_song_state = self.one_song_state_normal
            player.do_previous()

    # This is a hacky old method to 'repeat' the current song as soon as it
    # reaches the last second. Will be the used until the bug mentioned on the
    # comments above gets fixed.
    # This might be improved keeping a instance variable with the duration and
    # updating it on_song_change. Therefore, it would not be
    # necessary to query the duration every time
    # def on_elapsed_change(self, player, time):
    #     if self.repeat:
    #         duration = player.get_playing_song_duration()
    #         if duration > 0:
    #             # Repeat on the last two seconds of the song. Previously the
    #             # last second was used but RB now seems to use the last second
    #             # to prepare things for the next song of the list
    #             if time >= duration - 2:
    #                 player.set_playing_time(0)

    def do_activate(self):
        self.__action = Gio.SimpleAction.new_stateful('repeatone', None, GLib.Variant('b', False))
        self.__action.connect('activate', self.switch_repeat_status)

        app = Gio.Application.get_default()
        app.add_action(self.__action)

        item = Gio.MenuItem()
        item.set_label(_("Repeat current song"))
        # Keyboard shortcut
        item.set_attribute_value('accel', GLib.Variant("s", "<Ctrl>E"))
        item.set_detailed_action('app.repeatone')
        app.add_plugin_menu_item('edit', 'repeatone', item)

        self.repeat = False

        self.shell = self.object

        self.one_song_state_normal, self.one_song_state_eos = range(2)
        self.one_song_state = self.one_song_state_normal

        player = self.shell.props.shell_player

        player.connect('playing-song-changed', self.on_song_change)
        player.props.player.connect('eos', self.on_gst_player_eos)
        # player.connect('elapsed-changed', self.on_elapsed_change)

    def do_deactivate(self):
        app = Gio.Application.get_default()
        app.remove_action('repeatone')
        app.remove_plugin_menu_item('edit', 'repeatone')
        del self.__action
