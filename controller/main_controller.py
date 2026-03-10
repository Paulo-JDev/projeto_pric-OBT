# controller/main_controller.py

import logging
import time

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer

class MainController:
    def __init__(self, view, base_dir):
        self.view = view
        self.base_dir = base_dir

        # Inicialização tardia dos módulos pesados
        self._contratos_ready = False
        self._atas_ready = False

        self._contratos_failed = False
        self._atas_failed = False

        self.contratos_controller = None
        self.atas_model = None
        self.atas_view = None
        self.atas_controller = None
        self.backup_controller = None
        self.auto_controller = None

        # Cache de classes para reduzir import nos cliques da Home
        self._info_dialog_cls = None
        self._help_dialog_cls = None
        self._backup_controller_cls = None

        # Índices no stacked_widget (home já existe na posição 0)
        self._home_index = 0
        self._contratos_index = None
        self._atas_index = None

        # Conecta botões leves primeiro
        self.view.info_button.clicked.connect(self.show_info_dialog)
        self.view.backup_button.clicked.connect(self.show_backup_dialog)
        self.view.help_button.clicked.connect(self.show_help_dialog)
        self.view.automation_button.clicked.connect(self.show_automation_dialog)
        self.view.automation_button.setEnabled(False)

        # Navegação pronta desde o início; módulos pesados entram sob demanda.
        self.view.nav_list.currentRowChanged.connect(self.switch_module)
        self.view.nav_list.setCurrentRow(self._home_index)
        self.view.nav_list.setEnabled(True)

        # Pré-aquecimento leve e faseado dos módulos da Home para reduzir interrupções nos cliques.
        QTimer.singleShot(600, self._preload_info_dialog)
        QTimer.singleShot(900, self._preload_help_dialog)
        QTimer.singleShot(1200, self._preload_backup_controller)

    def _safe_cursor_load(self, loader):
        """Executa carregamento pesado com cursor de espera e handling robusto."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            start_time = time.perf_counter()
            loader()
            elapsed = time.perf_counter() - start_time
            logging.info("%s executado em %.2fs", loader.__name__, elapsed)
            return True
        except KeyboardInterrupt:
            logging.warning("Inicialização interrompida por KeyboardInterrupt em %s", loader.__name__)
            return False
        except Exception as exc:
            logging.exception("Falha ao carregar módulo em %s: %s", loader.__name__, exc)
            QMessageBox.critical(
                self.view,
                "Falha ao carregar módulo",
                f"Não foi possível carregar o módulo solicitado.\n\nDetalhes: {exc}",
            )
            return False
        finally:
            QApplication.restoreOverrideCursor()
    
    def _preload_info_dialog(self):
        if self._info_dialog_cls is None:
            start_time = time.perf_counter()
            from view.info_dialog import InfoDialog
            self._info_dialog_cls = InfoDialog
            logging.info("Preload InfoDialog em %.2fs", time.perf_counter() - start_time)

    def _preload_help_dialog(self):
        if self._help_dialog_cls is None:
            start_time = time.perf_counter()
            from view.help_dialog import HelpDialog
            self._help_dialog_cls = HelpDialog
            logging.info("Preload HelpDialog em %.2fs", time.perf_counter() - start_time)

    def _preload_backup_controller(self):
        if self._backup_controller_cls is None:
            start_time = time.perf_counter()
            from backup.controller.backup_controller import BackupController
            self._backup_controller_cls = BackupController
            logging.info("Preload BackupController em %.2fs", time.perf_counter() - start_time)

    def _load_contratos_module(self):
        """Carrega Contratos após a janela renderizar."""
        from Contratos.controller.uasg_controller import UASGController

        self.contratos_controller = UASGController(self.base_dir, self.view)
        self._contratos_index = self.view.stacked_widget.addWidget(self.contratos_controller.view)
        self._contratos_ready = True
        self._contratos_failed = False
        self.view.automation_button.setEnabled(True)

    def _load_atas_module(self):
        """Carrega Atas de forma independente para manter responsividade."""
        from atas.model.atas_model import AtasModel
        from atas.view.atas_view import AtasView
        from atas.controller.atas_controller import AtasController

        self.atas_model = AtasModel()
        self.atas_view = AtasView()
        self.atas_controller = AtasController(self.atas_model, self.atas_view)
        self._atas_index = self.view.stacked_widget.addWidget(self.atas_view)
        self._atas_ready = True
        self._atas_failed = False

        """self.view.nav_list.currentRowChanged.connect(self.switch_module)
        self.view.nav_list.setCurrentRow(0)
        self.view.nav_list.setEnabled(True)"""

    def switch_module(self, nav_index):
        # Home
        if nav_index == 0:
            self.view.stacked_widget.setCurrentIndex(self._home_index)
            return
        # Contratos
        if nav_index == 1:
            if not self._contratos_ready and not self._contratos_failed:
                ok = self._safe_cursor_load(self._load_contratos_module)
                if not ok:
                    self._contratos_failed = True
                    self.view.nav_list.setCurrentRow(self._home_index)
                    return

            if self._contratos_ready and self._contratos_index is not None:
                self.view.stacked_widget.setCurrentIndex(self._contratos_index)
            return
        
        # Atas
        if nav_index == 2:
            if not self._atas_ready and not self._atas_failed:
                ok = self._safe_cursor_load(self._load_atas_module)
                if not ok:
                    self._atas_failed = True
                    self.view.nav_list.setCurrentRow(self._home_index)
                    return

            if self._atas_ready and self._atas_index is not None:
                self.view.stacked_widget.setCurrentIndex(self._atas_index)
            return

    def run(self):
        self.view.show()

    def show_info_dialog(self):
        """Abre a janela de Informações do Projeto."""
        try:
            if self._info_dialog_cls is None:
                self._preload_info_dialog()
            dialog = self._info_dialog_cls(self.view)
            dialog.exec()
        except KeyboardInterrupt:
            logging.warning("Ação 'Informações' interrompida por KeyboardInterrupt.")
        except Exception as exc:
            logging.exception("Erro ao abrir Informações: %s", exc)
            QMessageBox.critical(self.view, "Erro", f"Não foi possível abrir Informações.\n\nDetalhes: {exc}")

    def show_backup_dialog(self):
        """Abre a janela do módulo de Backup com importação tardia."""
        try:
            if self._backup_controller_cls is None:
                self._preload_backup_controller()
            self.backup_controller = self._backup_controller_cls(self.view)
            self.backup_controller.show()
        except KeyboardInterrupt:
            logging.warning("Ação 'Backup' interrompida por KeyboardInterrupt.")
        except Exception as exc:
            logging.exception("Erro ao abrir Backup: %s", exc)
            QMessageBox.critical(self.view, "Erro", f"Não foi possível abrir Backup.\n\nDetalhes: {exc}")

    def show_automation_dialog(self):
        """Abre a janela do módulo de Automações quando Contratos estiver pronto."""
        if not self._contratos_ready:
            # Tenta carregar contratos no clique, para evitar bloqueio no boot.
            ok = self._safe_cursor_load(self._load_contratos_module)
            if not ok:
                self._contratos_failed = True
                return

        from auto.controller.auto_controller import AutoController

        self.auto_controller = AutoController(self.view, self.base_dir, self.contratos_controller)
        self.auto_controller.show()

    def show_help_dialog(self):
        try:
            if self._help_dialog_cls is None:
                self._preload_help_dialog()
            dialog = self._help_dialog_cls(self.view)
            dialog.exec()
        except KeyboardInterrupt:
            logging.warning("Ação 'Ajuda' interrompida por KeyboardInterrupt.")
        except Exception as exc:
            logging.exception("Erro ao abrir Ajuda: %s", exc)
            QMessageBox.critical(self.view, "Erro", f"Não foi possível abrir Ajuda.\n\nDetalhes: {exc}")
