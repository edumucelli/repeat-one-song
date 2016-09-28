# This is a part of the external Repeat One Song plugin for Rhythmbox
#
# Author: Eduardo Mucelli Rezende Oliveira
# E-mail: edumucelli@gmail.com or eduardom@dcc.ufmg.br
# Version: 0.1 (Stable)
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

import rhythmdb, rb
import gtk, gtk.glade, gconf
import os.path, gettext

# o XML que define os botoes da barra de menus, do menu Controle, e a acao que sera mapeada para eles
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

class RepeatOneSong (rb.Plugin):

    def switch_repeat_status(self, control):
        # como existe apenas uma acao, a mesma poderia ter sido tratada como self.action em todo o codigo,
        # mas a boa pratica eh colocar as acoes em um grupo e busca-la com o get_action
        action = self.action_group.get_action('RepeatOne')                              # seleciona a acao de repetir a musica atual
        self.repeat = action.get_active()                                               # indica se o botao esta marcado, ou desmarcado
        player = self.shell.props.shell_player
        if self.repeat:
            shuffle, self.repeat_all = player.get_playback_state()
            player.set_playback_state(shuffle, 1)
        else:
            shuffle, repeat_all = player.get_playback_state()
            player.set_playback_state(shuffle, self.repeat_all)
            
    def switch_repeat_all_status(self, action):
        if not action.get_active() and self.repeat:
            self.repeat = False
            self.repeat_all = 0
            action_repeat_one = self.action_group.get_action('RepeatOne')
            action_repeat_one.set_active(False)

    def load_icon(self):
        """Trata a adicao do icone na barra de ferramentas. O icone eh nomeado 'repeat-one-song' e 
           posteriormente sera usado como o ultimo parametro do 'gtk.ToggleAction' no metodo generate_ui"""
        icon_file_name = self.find_file("icon.svg")
        root_path = os.path.dirname(icon_file_name) + "/repeat-one-song"
        iconsource = gtk.IconSource()
        iconsource.set_filename(icon_file_name)
        iconset = gtk.IconSet()
        iconset.add_source(iconsource)
        iconfactory = gtk.IconFactory()
        iconfactory.add("repeat-one-song", iconset)
        iconfactory.add_default()

    def generate_ui(self):
        """Define as a acao (ligada ao metodo switch_repeat_status), os rotulos traduzives, icone do botao que fica na barra de tarefas.
           Ao final, eh necessario ainda mesclar a string do xml para adicionar tais funcionalidades na ui do Rhythmbox"""
        self.action_group = gtk.ActionGroup('RepeatOneActionGroup')                                             # cria agrupador de acoes
                                                                                                                # cria uma acao toggle (on/off)
        # RepeatOne (the named action), translatable string of Control menu), translatable string of Toolbar, icon defined above (see load_icon())
        action = gtk.ToggleAction("RepeatOne", _("Repeat one"), _("Repeat the current song when it's finished"), "repeat-one-song");
        self.action_group.add_action_with_accel(action, "<Control>E")                                           # adiciona esta acao no grupo + atalho
        action.connect("activate", self.switch_repeat_status)                                                   # quando o botao for acionado
        
        manager = self.shell.get_ui_manager()
        manager.insert_action_group(self.action_group, 0)
        self.uid = manager.add_ui_from_string(ui_str)                                                           # mescla xml definido com o do RB
        manager.ensure_update()
        
        action = manager.get_action('/ToolBar/Repeat')                                                          
        action.connect("activate", self.switch_repeat_all_status)

    def __init__(self):
        rb.Plugin.__init__(self)

    def activate(self, shell):                                                                                  # when loading the applet
        self.shell = shell
        self.db = shell.props.db
        self.repeat = False

        self.one_song_state_normal, self.one_song_state_eos = range(2)
        self.one_song_state = self.one_song_state_normal

        self.load_icon()                                                                                        # necessary load icon first ...
        self.generate_ui()                                                                                      # ... because it is used here 

        player = self.shell.props.shell_player
        player.connect('playing-song-changed', self.on_song_change)         # mudou a musica. o player.do_next() invoca o on_elapsed_changed
        player.props.player.connect('eos', self.on_gst_player_eos)          # eos -> on_song_change

    def deactivate(self, shell):                                            # when unloading applet
        if self.repeat:
            player = self.shell.props.shell_player
            shuffle, repeat_all = player.get_playback_state()
            player.set_playback_state(shuffle, self.repeat_all)
        
        for attr in (self.db, self.shell, self.repeat,                      # delete global attributes if possible
                     self.one_song_state_normal, self.one_song_state_eos):
            if attr:
                del attr
        manager = shell.get_ui_manager()
        manager.remove_ui(self.uid)
        manager.remove_action_group(self.action_group)
        manager.ensure_update()

    def on_gst_player_eos(self, gst_player, stream_data, early=0):
        if self.repeat:
            self.one_song_state = self.one_song_state_eos
           
    def on_song_change(self, player, time):                                 # quando mudar a musica ...
        if self.one_song_state == self.one_song_state_eos:
            self.one_song_state = self.one_song_state_normal
            player.do_previous()
