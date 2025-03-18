def refresh_uasg_menu(self):
        """Atualiza o menu com as UASGs carregadas."""
        menu = self.view.menu_button.menu()
        menu.clear()  # Limpa o menu antes de adicionar as UASGs

        if not self.loaded_uasgs:
            # Se não houver UASGs carregadas, desabilita o botão
            self.view.menu_button.setEnabled(False)
            print("Nenhuma UASG carregada. Botão desabilitado.")
        else:
            # Se houver UASGs carregadas, habilita o botão e adiciona as UASGs ao menu
            self.view.menu_button.setEnabled(True)
            for uasg in self.loaded_uasgs:
                print(f"➕ Adicionando UASG {uasg} ao menu.")
                action = menu.addAction(f"UASG {uasg}")
                action.triggered.connect(lambda checked, uasg=uasg: self.update_table(uasg))