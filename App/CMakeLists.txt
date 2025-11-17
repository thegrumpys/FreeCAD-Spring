# SPDX-License-Identifier: LGPL-2.1-or-later

set(Spring_LIBS
    ${OCC_LIBRARIES}
    ${OCC_DEBUG_LIBRARIES}
    FreeCADApp
    Part
)

SET(Spring_SRCS
    AppSpring.cpp
    CompressionSpringFeature.cpp
    CompressionSpringFeature.h
    PreCompiled.h
)

add_library(Spring SHARED ${Spring_SRCS})
target_include_directories(
    Spring
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/..
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_BINARY_DIR}/src
)
target_include_directories(Spring SYSTEM PUBLIC ${OCC_INCLUDE_DIR})
target_link_directories(Spring PUBLIC ${OCC_LIBRARY_DIR})
target_link_libraries(Spring ${Spring_LIBS})


SET_BIN_DIR(Spring Spring /Mod/Spring)
SET_PYTHON_PREFIX_SUFFIX(Spring)

install(TARGETS Spring DESTINATION ${CMAKE_INSTALL_LIBDIR})
