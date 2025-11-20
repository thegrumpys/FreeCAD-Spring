# SPDX-License-Identifier: LGPL-2.1-or-later

add_subdirectory(libspringarea)
add_subdirectory(libspringocct)

IF (BUILD_GUI)
    PYSIDE_WRAP_RC(Spring_QRC_SRCS Resources/Spring.qrc)
ENDIF (BUILD_GUI)

SET(Spring_SRCS
    Init.py
    InitGui.py
    Spring.py
    SpringGui.py
)
SOURCE_GROUP("" FILES ${Spring_SRCS})

SET(SpringGuiIcon_SVG
    Resources/icons/SpringWorkbench.svg
)

ADD_CUSTOM_TARGET(Spring ALL
    SOURCES ${Spring_SRCS} ${Spring_QRC_SRCS} ${SpringGuiIcon_SVG}
)

fc_copy_sources(Spring "${CMAKE_BINARY_DIR}/Mod/Spring" ${Spring_SRCS})
fc_copy_sources(Spring "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_DATADIR}/Mod/Spring" ${SpringGuiIcon_SVG})

IF (BUILD_GUI)
    fc_target_copy_resource(Spring
        ${CMAKE_CURRENT_BINARY_DIR}
        ${CMAKE_BINARY_DIR}/Mod/Spring
        Spring_rc.py)
ENDIF (BUILD_GUI)

INSTALL(
    FILES
        ${Spring_SRCS}
        ${Spring_QRC_SRCS}
    DESTINATION
        Mod/Spring
)

INSTALL(FILES ${SpringGuiIcon_SVG} DESTINATION "Mod/Spring/Resources/icons")
