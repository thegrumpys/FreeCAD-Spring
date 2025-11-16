# SPDX-License-Identifier: LGPL-2.1-or-later

add_subdirectory(App)
if(BUILD_GUI)
    add_subdirectory(Gui)
endif(BUILD_GUI)

set(Spring_Scripts
    Init.py
)

if(BUILD_GUI)
    list (APPEND Spring_Scripts InitGui.py)
endif(BUILD_GUI)

add_custom_target(SpringScripts ALL
    SOURCES ${Spring_Scripts}
)

fc_target_copy_resource_flat(SpringScripts
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_BINARY_DIR}/Mod/Spring
    ${Spring_Scripts}
)

install(
    FILES
        ${Spring_Scripts}
    DESTINATION
        Mod/Spring
)
