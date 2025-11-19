# SPDX-License-Identifier: LGPL-2.1-or-later

IF (BUILD_GUI)
    PYSIDE_WRAP_RC(Sprung_QRC_SRCS Resources/Sprung.qrc)
ENDIF (BUILD_GUI)

SET(Sprung_SRCS
    Init.py
    InitGui.py
    Sprung.py
    SprungGui.py
)
SOURCE_GROUP("" FILES ${Sprung_SRCS})

SET(SprungGuiIcon_SVG
    Resources/icons/SprungWorkbench.svg
)

ADD_CUSTOM_TARGET(Sprung ALL
    SOURCES ${Sprung_SRCS} ${Sprung_QRC_SRCS} ${SprungGuiIcon_SVG}
)

fc_copy_sources(Sprung "${CMAKE_BINARY_DIR}/Mod/Sprung" ${Sprung_SRCS})
fc_copy_sources(Sprung "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_DATADIR}/Mod/Sprung" ${SprungGuiIcon_SVG})

IF (BUILD_GUI)
    fc_target_copy_resource(Sprung
        ${CMAKE_CURRENT_BINARY_DIR}
        ${CMAKE_BINARY_DIR}/Mod/Sprung
        Sprung_rc.py)
ENDIF (BUILD_GUI)

INSTALL(
    FILES
        ${Sprung_SRCS}
        ${Sprung_QRC_SRCS}
    DESTINATION
        Mod/Sprung
)

INSTALL(FILES ${SprungGuiIcon_SVG} DESTINATION "Mod/Sprung/Resources/icons")
