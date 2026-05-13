import dearpygui.dearpygui as dpg

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=600, height=300)

dpg.show_imgui_demo()

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()