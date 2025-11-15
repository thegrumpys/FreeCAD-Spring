add_subdirectory(App)
add_subdirectory(Gui)

set(Spring_PY_FILES
    Init.py
    InitGui.py
    Workbench.py
    SpringCommands.py
    SpringTools.py
    __init__.py
)

install(FILES ${Spring_PY_FILES}
    DESTINATION Mod/Spring
)

install(DIRECTORY Resources
    DESTINATION Mod/Spring
)
