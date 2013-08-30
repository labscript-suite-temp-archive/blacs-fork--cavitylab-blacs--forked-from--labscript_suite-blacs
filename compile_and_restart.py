import sys
import os
import subprocess
from Queue import Queue

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import QUiLoader

from qtutils import *
import runmanager
from subproc_utils.qt_components import OutputBox

class CompileAndRestart(QDialog):
    def __init__(self, blacs, globals_files,connection_table_labscript, output_path):
        QDialog.__init__(self,blacs['ui'])
        self.globals_files = globals_files
        self.labscript_file = connection_table_labscript
        self.output_path = output_path
        self.tempfilename = self.output_path.strip('.h5')+'.temp.h5'
        self.blacs = blacs
        
        self.ui = QUiLoader().load(os.path.join(os.path.dirname(os.path.realpath(__file__)),'compile_and_restart.ui'))
        self.output_box = OutputBox(self.ui.verticalLayout)       
        self.ui.restart.setEnabled(False)
        
        # Connect buttons
        self.ui.restart.clicked.connect(self.restart)
        self.ui.compile.clicked.connect(self.compile)
        self.ui.cancel.clicked.connect(self.reject)
        
        self.ui.setParent(self)
        self.ui.show()        
        self.show()

        self.compile()

    def closeEvent(self,event):
        if not self.ui.cancel.isEnabled():        
            event.ignore()            
        else:
            event.accept()
    
    def on_activate_default(self,window):
        if self.button_restart.get_sensitive():
            self.restart()
        elif self.button_compile.get_sensitive():
            self.compile()
                
    def compile(self):
        self.ui.compile.setEnabled(False)
        self.ui.cancel.setEnabled(False)
        self.ui.restart.setEnabled(False)
        self.ui.label.setText('Recompiling connection table')
        runmanager.compile_labscript_with_globals_files_async(self.labscript_file,
            self.globals_files, self.tempfilename, self.output_box.port, self.finished_compiling)
    
    @inmain_decorator(True)    
    def finished_compiling(self, success):
        self.ui.compile.setEnabled(True)
        self.ui.cancel.setEnabled(True)
        if success:
            self.ui.restart.setEnabled(True)
            self.ui.label.setText('Compilation succeeded, restart when ready')
            try:
                os.remove(self.output_path)
            except OSError:
                 # File doesn't exist, no need to delete then:
                pass
            try:
                os.rename(self.tempfilename,self.output_path)
            except OSError:
                self.output_box.queue.put(['stderr','Couldn\'t replace existing connection table h5 file. Is it open in another process?'])
                self.ui.label.setText('Compilation failed.')
                self.ui.restart.setEnabled(False)
                os.remove(self.tempfilename)
        else:
            self.ui.restart.setEnabled(False)
            self.ui.label.setText('Compilation failed. Please fix the errors in the connection table (python file) and try again')
            try:
                os.remove(self.tempfilename)
            except Exception:
                pass
                
    def restart(self):
        #gobject.timeout_add(100, self.blacs.destroy)
        QTimer.singleShot(100, self.blacs['ui'].close)
        self.accept()        
        self.blacs['set_relaunch'](True)
        
        #self.blacs.qt_application.aboutToQuit.connect(self.relaunch)
        #gtk.quit_add(0,self.relaunch)
    
        
if __name__ == '__main__':
    #gtk.threads_init()
    globals_file = '/home/bilbo/labconfig/bilbo-laptop_calibrations.h5'
    labscript_file = '/home/bilbo/labconfig/bilbo-laptop.py'
    output_path = '/home/bilbo/Desktop/pythonlib/BLACS/connectiontables/bilbo-laptop.h5'
    #compile_and_restart = CompileAndRestart(None, [], labscript_file, output_path)
    #gtk.main()
