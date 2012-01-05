""" GTK GUI module for pypass """
# -*- coding: utf-8 -*-

# Copyright (c) 2011 Pierre-Yves Chibon <pingou AT pingoured DOT fr>
# Copyright (c) 2011 Johan Cwiklinski <johan AT x-tnd DOT be>
#
# This file is part of pypass.
#
# pypass is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pypass is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pypass.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import logging

try:
    import pypass.pyp as pyp
    from pypass import __version__, __author__, __copyright__
    from pypass import __license_text__, __application__, __locale_dir__
    from pypass import __url__, __credits__
    from pypass.pypobj import PypFolder, PypAccount
except ImportError:
    # Application isn't installed
    import src.pyp as pyp
    from src import __version__, __author__, __copyright__, __credits__
    from src import __license_text__, __application__, __locale_dir__
    from src import __url__
    from src.pypobj import PypFolder, PypAccount

LOG = logging.getLogger(__name__)
if not LOG.handlers:
    try:
        LOG.addHandler(logging.NullHandler())
    except AttributeError:
        LOG.addHandler(pyp.PypNullHandler())

try:
    import pygtk
    pygtk.require("2.0")
except ImportError:
    pass
try:
    import gtk
except ImportError:
    LOG.error(_("GTK is not available."))
    sys.exit(1)
import gtk.glade
import gettext

#that way, GUI is not translated (but should be)
#gettext.install(__application__, __locale_dir__)

#solution found there:
#http://www.daa.com.au/pipermail/pygtk/2007-March/013586.html
#locale.setlocale(locale.LC_ALL, '')
# see http://bugzilla.gnome.org/show_bug.cgi?id=344926 for why the
# next two commands look repeated.
gtk.glade.bindtextdomain(__application__, __locale_dir__)
gtk.glade.textdomain(__application__)
gettext.bindtextdomain(__application__, __locale_dir__)
gettext.textdomain(__application__)


def file_browse(dialog_action, title, pathname, file_name="",
                types=None):
    """This function is used to browse for a pyWine file.
    It can be either a save or open dialog depending on
    what dialog_action is.
    The path to the file will be returned if the user
    selects one, however a blank string will be returned
    if they cancel or do not select one.
    dialog_action - The open or save mode for the dialog either
    gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SAVE
    file_name - Default name when doing a save
    source:
    http://www.pygtk.org/articles/extending-our-pygtk-application/extending-our-pygtk-application.htm
    """

    if (dialog_action == gtk.FILE_CHOOSER_ACTION_OPEN):
        dialog_buttons = (gtk.STOCK_CANCEL,
                            gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OPEN,
                            gtk.RESPONSE_OK)
    else:
        dialog_buttons = (gtk.STOCK_CANCEL,
                            gtk.RESPONSE_CANCEL,
                            gtk.STOCK_SAVE,
                            gtk.RESPONSE_OK)

    file_dialog = gtk.FileChooserDialog(title=title,
                action=dialog_action,
                buttons=dialog_buttons)
    #set the filename if we are saving
    if (dialog_action == gtk.FILE_CHOOSER_ACTION_SAVE):
        file_dialog.set_current_name(file_name)
    file_dialog.set_current_folder(pathname)
    file_dialog.set_default_response(gtk.RESPONSE_OK)

    if types is not None and isinstance(types, dict):
        for typek in types.keys():
            filefilter = gtk.FileFilter()
            filefilter.set_name(typek)
            for element in types[typek]:
                filefilter.add_mime_type(element)
            file_dialog.add_filter(filefilter)
    #Create and add the 'all files' filter
    filefilter = gtk.FileFilter()
    filefilter.set_name("All files")
    filefilter.add_pattern("*")
    file_dialog.add_filter(filefilter)

    #Init the return value
    result = None
    if file_dialog.run() == gtk.RESPONSE_OK:
        result = file_dialog.get_filename()
    file_dialog.destroy()

    return result


def _dialog(dialog):
    """ Display a dialog window """
    dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    dialog.set_modal(True)
    dialog.set_keep_above(True)
    dialog.show_all()
    result = dialog.run()
    dialog.hide()
    return result


def dialog_window(message, error=None, action=gtk.MESSAGE_ERROR):
    """
    Display a dialog window with the given message.

    Action precise the     type of dialog to display, the return signal is
    handled accordingly.

    message -- a string of text which is displayed in the dialog
    error -- a string with another part of the message displayed on
    a second line
    action -- a GTK Message Type Constants giving the type of window
    displayed _link: http://www.pygtk.org/docs/pygtk/gtk-constants.html#gtk-message-type-constants
    """
    dialog = gtk.MessageDialog(None, 0, action)
    dialog.set_markup("<b>" + "Error" + "</b>")
    if error is not None:
        message = message + "\n %s" % error
    dialog.format_secondary_markup(message)
    if action == gtk.MESSAGE_ERROR:
        dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_YES)
    elif action == gtk.MESSAGE_WARNING:
        dialog.add_buttons(gtk.STOCK_CANCEL,
                            gtk.RESPONSE_CANCEL,
                            gtk.STOCK_OK,
                            gtk.RESPONSE_YES)
    elif action == gtk.MESSAGE_QUESTION:
        dialog.add_buttons(gtk.STOCK_NO,
                            gtk.RESPONSE_NO,
                            gtk.STOCK_OK,
                            gtk.RESPONSE_YES)
    return _dialog(dialog)


class PyPassGui(object):
    """ Class handling the gtk gui for pypass """

    def __init__(self, pypass, options):
        """ Instantiate the window and set basic elements """
        self.pypass = pypass
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "ui", "pypass.glade"))
        self.builder.set_translation_domain(__application__)
        self.mainwindow = self.builder.get_object('mainwindow')
        self.mainwindow.set_title("PyPass")

        self.set_button_toolbar()

        ## source to put the icons in the TreeView:
        ## http://www.eurion.net/python-snippets/snippet/Tree%20View%20Column.html

        ## Handles the tree view in the main window
        # retrieve the TreeView
        treeview = self.builder.get_object("treefolderview")
        # create the TreeViewColumns to display the data
        col0 = gtk.TreeViewColumn("")
        treeview.append_column(col0)

        # create a CellRenderers to render the data
        cellpb = gtk.CellRendererPixbuf()
        cell = gtk.CellRendererText()

        # add the cells to the columns - 2
        col0.pack_start(cellpb, False)
        col0.pack_start(cell, True)

        # set the cell attributes to the appropriate liststore column
        col0.set_attributes(cellpb, stock_id=1)
        col0.set_attributes(cell, text=0)

        # filename contains the name of the file which has been opened
        # This way if you open a file and press ctrl+s you save in the file
        # you opened not in the default one.
        self.filename = None
        # key is the key you select, if it is None it will use the default
        # if set in the configuration file.
        self.key = None
        # created reflects whether the database was new/manually created
        self.created = False
        self.data = PypFolder()

        if options.filename is not None:
            self.filename = options.filename
        self.pypass.load_data(filename=self.filename)
        if self.pypass.data is not None and self.pypass.data != "":
            self.load_password_tree(self.pypass.json_to_tree())

        # Add the images on the button :-)
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.get_settings().set_long_property('gtk-button-images',
                                                    True, '')

        dic = {
            "on_buttonQuit_clicked": self.quit,
            "on_windowMain_destroy": self.quit,
            "gtk_main_quit": self.quit,
            "show_about": self.show_about,
            "cursor_changed": self.on_account_selected,
            "add_entry": self.add_entry,
            "add_folder": self.add_folder,
            "edit_entry": self.edit_entry,
            "remove_entry": self.remove_entry,
            "generate_password": self.generate_password,
            "save_database": self.save_database,
            "save_as_database": self.save_as_database,
            "open_database": self.open_database,
            "set_key": self.set_key,
            "menu_new_db": self.new_database,
        }
        self.builder.connect_signals(dic)

        self.update_status_bar(_("Welcome into pypass"))

        self.modified_db = False

        self.mainwindow.show()
        gtk.main()

    def set_button_toolbar(self):
        """ Set the button toolbar with their logo """
        butons = {
                    "b_open": gtk.STOCK_OPEN,
                    "b_save": gtk.STOCK_SAVE,
                    "b_folder": gtk.STOCK_DIRECTORY,
                    "b_add": gtk.STOCK_ADD,
                    "b_edit": gtk.STOCK_EDIT,
                    "b_del": gtk.STOCK_REMOVE,
                    "b_quit": gtk.STOCK_QUIT,
                    "b_about": gtk.STOCK_ABOUT,
                    }
        self.set_button_img(butons)

    def set_button_img(self, butons):
        """ For a given hash of button, set the image """
        for buton in butons.keys():
            butonopen = self.builder.get_object(buton)
            img = gtk.image_new_from_stock(butons[buton],
                                            gtk.ICON_SIZE_LARGE_TOOLBAR)
            butonopen.set_image(img)

    def load_password_tree(self, obj, parent=None):
        """
        Load a given tree into the treefolderview using the
        load_pypfolder function
        """
        self.data = obj
        treeview = self.builder.get_object("treefolderview")
        treestore = gtk.TreeStore(str, str, str)
        self.load_pypfolder(treestore, obj, parent)
        treeview.set_model(treestore)

    def load_pypfolder(self, treestore, obj, parent=None):
        """
        Loads the given PypFolder into the given treestore with the
        given parent
        This function is recursive to load the whole tree in memory including
        children folders and accounts
        """
        for folder in obj.folders:
            icon = gtk.STOCK_DIRECTORY
            parent2 = treestore.append(parent, [folder.name, icon, "folder"])
            self.load_pypfolder(treestore, folder, parent2)
        for account in obj.accounts:
            icon = gtk.STOCK_DIALOG_AUTHENTICATION
            treestore.append(parent, [account.name, icon, "account"])

    def show_about(self, widget):
        """ Show the about diaglog """
        about = self.builder.get_object("aboutdialog")
        about.set_name("PyPass")
        about.set_version(__version__)
        about.set_copyright(__copyright__)
        about.set_authors(__credits__)
        about.set_comments('\n'.join(__author__))
        about.set_license(__license_text__)
        about.set_website(__url__)
        _logo_path = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "..", "data", "PyPass.png")
        about.set_logo(gtk.gdk.pixbuf_new_from_file(_logo_path))

        _dialog(about)

    def new_database(self, widget):
        """ Set a new database """
        if self.modified_db:
            result = dialog_window(_("This database has been modified",
            "Do you want to save it before continuing?"),
                    action=gtk.MESSAGE_QUESTION)
            if result == gtk.RESPONSE_YES:
                self.save_database()
        self.data = PypFolder()
        self.filename = None
        self.created = True
        self.load_password_tree(self.data)

    def quit(self, widget):
        """ Quit the application """
        LOG.info(_("Exiting..."))
        if self.modified_db:
            dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING)
            dialog.set_markup("<b>" + _("Error") + "</b>")
            dialog.format_secondary_markup(
                    _("Do you want to save file before quit?"))
            dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_NO, gtk.RESPONSE_NO,
                                gtk.STOCK_YES, gtk.RESPONSE_YES,)
            result = _dialog(dialog)
            if result == gtk.RESPONSE_YES:
                outcome = self.save_database()
                if outcome is not True:
                    return
            elif result == gtk.RESPONSE_CANCEL:
                self.mainwindow.show()
                return
        sys.exit(0)

    def set_combox_type(self):
        """ Set the different options in the combobox of the new entry
        dialog """

        options = {
            "website": "",
            "server": gtk.STOCK_NETWORK,
            "ftp": "",
            "Email": "",
        }

        combo = self.builder.get_object("combo_type")
        store = gtk.ListStore(str, str)
        opts = options.keys()
        opts.sort()
        for opt in opts:
            store.append([opt, options[opt]])
        combo.set_model(store)

        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 0)

        combo.set_active(0)

    def set_keys_list(self, hide=True):
        """ Set all the keys retrieved from pypass into the list """
        keys = self.pypass.list_recipients()
        treeview = self.builder.get_object("treeviewkey")
        column_str = gtk.TreeViewColumn(_('Key ID'))
        treeview.append_column(column_str)
        cell = gtk.CellRendererText()
        column_str.pack_start(cell, True)
        column_str.add_attribute(cell, "text", 0)

        column_str = gtk.TreeViewColumn('')
        treeview.append_column(column_str)
        cell1 = gtk.CellRendererText()
        column_str.pack_start(cell1, True)
        column_str.add_attribute(cell1, "text", 1)

        store = gtk.ListStore(str, str)
        treeview.set_model(store)
        for key in keys:
            store.append([key['keyid'], " ".join(key['uids'])])

    def set_folder_dialog(self):
        """
        Reads the dialogaddentry ui file and adjust the dialog to make it
        the folder dialog (remove some item and resize it).
        """
        self.builder.add_from_file(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "ui", "dialogaddentry.glade"))
        butons = {
                "b_add_entry": gtk.STOCK_OK,
                "b_cancel_entry": gtk.STOCK_CANCEL,
                }
        self.set_button_img(butons)
        self.set_combox_type()

        for objname in ("label7", "label8", "label3", "label5", "label4",
                    "entry_user", "entry_url", "entry_password",
                    "b_generate_password", "combo_type"):
            obj = self.builder.get_object(objname)
            obj.destroy()

        add = self.builder.get_object("dialogaddentry")
        add.set_title(_("Add a folder"))
        add.set_size_request(400, 150)

    def set_entry_dialog(self):
        """ Add the entry dialog to the current window """
        self.builder.add_from_file(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "ui", "dialogaddentry.glade"))
        butons = {
                "b_add_entry": gtk.STOCK_OK,
                "b_cancel_entry": gtk.STOCK_CANCEL,
                }
        self.set_button_img(butons)
        self.set_combox_type()

        dic = {"generate_password": self.generate_password}
        self.builder.connect_signals(dic)

    def open_database(self, widget=None):
        """ Open a selected database """
        # get database file
        filename = file_browse(gtk.FILE_CHOOSER_ACTION_OPEN,
                               _("Open a database"),
                                os.path.expanduser('~'))
        if filename is not None:
            self.pypass.load_data(filename=filename)
            self.filename = filename
            self.created = False
            if self.pypass.data is not None and self.pypass.data != "":
                self.load_password_tree(self.pypass.json_to_tree())
            return

    def save_database(self, widget=None):
        """ Save the current database """
        if not self.pypass.is_default_in_keyring():
            result = dialog_window(_("The key set as to encrypt this file is not" \
            " installed in this machine, do you want to continue ?"),
            action=gtk.MESSAGE_QUESTION)
            if result == gtk.RESPONSE_NO:
                return
        if self.created:
            self.save_as_database()
        print self.key
        self.pypass.data_from_json(self.data)
        outcome = self.pypass.crypt(force=True, recipients=self.key,
                                    filename=self.filename)
        if outcome == "key_not_found":
            result = dialog_window(_("The database could not be saved!"),
            _("The key could not be found"),
            action=gtk.MESSAGE_ERROR)
            return

        if outcome is not True:
            result = dialog_window(_("The database could not be saved!"),
            action=gtk.MESSAGE_ERROR)
            return
        self.update_status_bar(_("Database saved"))
        self.modified_db = False
        return True

    def save_as_database(self, widget=None):
        """ Save the current database in a selected file """
        filename = file_browse(gtk.FILE_CHOOSER_ACTION_SAVE,
                               _("Save a database"),
                                os.path.expanduser('~'))
        if filename is None:
            return
        self.pypass.data_from_json(self.data)
        outcome = self.pypass.crypt(recipients=self.key,
                                    filename=filename)
        if outcome == "file_exists":
            result = dialog_window(_("This database already exists"),
            _("Do you want to overrite it ?"),
            action=gtk.MESSAGE_QUESTION)
            if result != gtk.RESPONSE_YES:
                return
            else:
                outcome = self.pypass.crypt(force=True,
                                    recipients=self.key,
                                    filename=self.filename)

        self.update_status_bar(_("Database saved"))
        self.modified_db = False

    def on_account_selected(self, widget=None):
        """ Display the account in the window when selected on the tree """
        selection = self.builder.get_object("treefolderview").get_selection()
        (model, itera) = selection.get_selected()
        folderspath = pyp.get_folder_path(model, itera, [])
        txtpass = self.builder.get_object("labelpass")

        if itera is None:
            txtpass.set_text(" ")
            return

        item = self.pypass.get_item(self.data, folderspath,
            model[itera][2], model[itera][0])

        if item is None:
            txtpass.set_text(" ")
            return
        elif isinstance(item, PypFolder):
            content = ""
            content += "<b>Name:</b> %s \n" % item.name
            content += "<b>Description:</b> %s \n" % \
                    item.description
            txtpass.set_text(content)
            txtpass.set_use_markup(True)
            return
        elif isinstance(item, PypAccount):
            content = ""
            content += "<b>Name:</b> %s \n" % item.name
            content += "<b>Password:</b> %s \n" % item.password
            keys = item.extras.keys()
            keys.sort()
            for key in keys:
                if key not in ('name', 'password'):
                    if key.lower() == 'url':
                        content += "<b>%s:</b> <a href='%s'>" \
                            "%s</a> \n" % (key, item.extras[key],
                                            item.extras[key])
                    else:
                        content += "<b>%s:</b> %s \n" % (
                                key, item.extras[key])

            txtpass.set_text(content)
            txtpass.set_use_markup(True)
            return
        else:
            txtpass.set_text(" ")

    def set_key(self, widget):
        """
        Display the window in which the user can choose one the key
        which are installed on the machine, set this key in the config file
        """
        self.builder.add_from_file(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "ui", "dialogkeychooser.glade"))
        butons = {
                "b_ok_key": gtk.STOCK_OK,
                "b_cancel_key": gtk.STOCK_CANCEL,
                }
        self.set_button_img(butons)
        self.set_keys_list()
        self.builder.get_object("label_password").set_text(_("Other key:"))
        self.builder.get_object("entry_key_password").set_visibility(True)

        add = self.builder.get_object("dialogkeychooser")
        if _dialog(add) == 1:
            selection = self.builder.get_object("treeviewkey").get_selection()
            (model, itera) = selection.get_selected()
            otherk = self.builder.get_object("entry_key_password").get_text()
            if itera is None and (otherk is None or otherk == ""):
                LOG.warning("No key selected")
                return

            key = None
            if itera is not None:
                key = model[itera][0]
            if otherk is not None and otherk != "":
                key = otherk
            if key is None:
                LOG.error("bug")

            LOG.debug(key)
            self.key = key
            self.pypass.set_recipient(key[:8])

    def edit_entry(self, widget):
        """ Edit an entry from the tree """
        (model, itera) = self.get_path()
        if itera is None:
            return

        folderspath = pyp.get_folder_path(model, itera, [])
        item = self.pypass.get_item(self.data, folderspath,
                model[itera][2], model[itera][0])

        if item is None:
            return

        if isinstance(item, PypAccount):
            self.set_entry_dialog()
            # Name
            entry_name = self.builder.get_object("entry_name")
            entry_name.set_text(item.name)
            entry_name.set_editable(False)  # Name cannot be changed
            # Password
            entry_password = self.builder.get_object("entry_password")
            entry_password.set_text(item.password)
            # Extras info
            if "user" in item.extras.keys():
                self.builder.get_object("entry_user").set_text(
                        item.extras["user"])
            if "url" in item.extras.keys():
                self.builder.get_object("entry_url").set_text(
                        item.extras["url"])
            if "description" in item.extras.keys():
                self.builder.get_object("entry_description").set_text(
                        item.extras["description"])
            item = self.get_password_from_dialog()

        else:
            self.set_folder_dialog()
            # Name
            entry_name = self.builder.get_object("entry_name")
            entry_name.set_text(item.name)
            entry_name.set_editable(False)  # Name cannot be changed
            # Password
            if item.description is not None:
                entry_description = self.builder.get_object("entry_description")
                entry_description.set_text(item.description)
            item = self.get_folder_from_dialog()
        if item is None:
            return
        self.data = self.pypass.replace_item(self.data, model,
                                                itera, item)
        self.load_password_tree(self.data)
        self.on_account_selected()
        self.update_status_bar(_("Account updated"))
        self.modified_db = True

    def remove_entry(self, widget):
        """ Remove an entry from the tree """
        (model, itera) = self.get_path()
        folderspath = pyp.get_folder_path(model, itera, [])
        item = self.pypass.get_item(self.data, folderspath,
                model[itera][2], model[itera][0])
        result = dialog_window(_("You are going to remove %s.") % item.name,
            _("Do you want to continue ?"),
            action=gtk.MESSAGE_QUESTION)
        if result == gtk.RESPONSE_NO:
            return
        elif result == gtk.RESPONSE_YES:
            self.data = self.pypass.remove_item(self.data, model, itera,
                item)
            self.load_password_tree(self.data)
            self.on_account_selected()
            self.update_status_bar(_("Item removed"))
            self.modified_db = True

    def get_folder_from_dialog(self):
        """
        Display the addentry dialog and returns the PypFolder object
        """
        add = self.builder.get_object("dialogaddentry")
        if _dialog(add) == 1:
            name = self.builder.get_object("entry_name").get_text()
            description = \
                self.builder.get_object("entry_description").get_text()

            if name is None or name == "":
                dialog_window(_("Could not create the folder."),
                    _("Name was missing."),
                    gtk.MESSAGE_ERROR)
                return
            else:
                if description is None or description == "":
                    folder = PypFolder(name)
                else:
                    folder = PypFolder(name, description)
                add.destroy()
                return folder

    def get_password_from_dialog(self):
        """
        Display the addentry dialog and returns the PypAccount object
        """
        add = self.builder.get_object("dialogaddentry")
        if _dialog(add) == 1:
            name = self.builder.get_object("entry_name").get_text()
            password = self.builder.get_object("entry_password").get_text()
            user = self.builder.get_object("entry_user").get_text()
            url = self.builder.get_object("entry_url").get_text()
            description = \
                self.builder.get_object("entry_description").get_text()
            passtype = self.builder.get_object("combo_type").get_active()

            if "" in (name, password):
                dialog_window(_("Could not add the account"),
                    _("Name and password are both required."),
                    gtk.MESSAGE_ERROR)
                return
            else:
                account = PypAccount(name, password)
                if url is not "":
                    account.extras['url'] = url
                if user is not "":
                    account.extras['user'] = user
                if description is not "":
                    account.extras['description'] = description
                add.destroy()
                return account

    def add_entry(self, widget):
        """ Display the dialog to add an entry to the database """
        self.set_entry_dialog()
        account = self.get_password_from_dialog()
        if account is None:
            return
        (model, itera) = self.get_path()
        data = self.pypass.add_account(
                                    self.data, model, itera, account)
        if data == "duplicate_entry":
            dialog_window(_("Could not add the account"),
            _("There is already an account with this name."),
            gtk.MESSAGE_ERROR)
            return
        self.load_password_tree(data)
        self.update_status_bar(_("Account added"))
        self.modified_db = True

    def add_folder(self, widget):
        """ Display the dialog to add a folder to the database """
        self.set_folder_dialog()
        folder = self.get_folder_from_dialog()
        if folder is None:
            return

        (model, itera) = self.get_path()
        data = self.pypass.add_folder(self.data, model, itera, folder)
        if data == "duplicate_entry":
            dialog_window(_("Could not add the folder"),
            _("There is already a folder with this name."),
            gtk.MESSAGE_ERROR)
            return
        self.load_password_tree(data)
        self.update_status_bar(_("Folder added"))
        self.modified_db = True

    def update_status_bar(self, entry):
        """ Update the status bar with the given text """
        stbar = self.builder.get_object('statusbar')
        stbar.push(1, entry)

    def get_path(self):
        """ Retrieve the path selected """
        selection = self.builder.get_object("treefolderview").get_selection()
        return selection.get_selected()

    def generate_password(self, widget):
        """ Generate a random password """
        password = self.pypass.generate_password()
        entry = self.builder.get_object("entry_password")
        entry.set_text(password)
        return
