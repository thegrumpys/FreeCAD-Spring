# SPDX-License-Identifier: LGPL-2.1-or-later

set(Spring_LIBS
    FreeCADApp
)

SET(Spring_SRCS
    AppSpring.cpp
    PreCompiled.h
)

add_library(Spring SHARED ${Spring_SRCS})
target_link_libraries(Spring ${Spring_LIBS})


SET_BIN_DIR(Spring Spring /Mod/Spring)
SET_PYTHON_PREFIX_SUFFIX(Spring)

install(TARGETS Spring DESTINATION ${CMAKE_INSTALL_LIBDIR})
