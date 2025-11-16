# SPDX-License-Identifier: LGPL-2.1-or-later

include_directories(
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_CURRENT_BINARY_DIR}
)

set(SpringGui_LIBS
    Spring
    FreeCADGui
)

qt_add_resources(Spring_QRC_SRCS Resources/Spring.qrc)

SET(SpringGui_SRCS
    ${Spring_QRC_SRCS}
    AppSpringGui.cpp
    Command.cpp
    PreCompiled.h
    Workbench.cpp
    Workbench.h
)

add_library(SpringGui SHARED ${SpringGui_SRCS})
target_link_libraries(SpringGui ${SpringGui_LIBS})

SET_BIN_DIR(SpringGui SpringGui /Mod/Spring)
SET_PYTHON_PREFIX_SUFFIX(SpringGui)

install(TARGETS SpringGui DESTINATION ${CMAKE_INSTALL_LIBDIR})
