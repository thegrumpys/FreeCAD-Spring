set(SpringGui_SRCS
    SpringGui.cpp
    SpringGuiPy.cpp
)

set(SpringGui_HDRS
    SpringGui.h
)

set(Spring_RESOURCES
    Resources/Spring.qrc
)

qt_add_resources(Spring_QRC ${Spring_RESOURCES})

add_library(SpringGui SHARED ${SpringGui_SRCS} ${SpringGui_HDRS} ${Spring_QRC})

set_target_properties(SpringGui PROPERTIES PREFIX "")

target_link_libraries(SpringGui PUBLIC FreeCADGui SpringApp)

target_include_directories(SpringGui
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)

install(TARGETS SpringGui DESTINATION ${CMAKE_INSTALL_LIBDIR}/Mod/Spring)
install(FILES ${SpringGui_HDRS} DESTINATION include/Mod/Spring/Gui)
install(DIRECTORY Resources/icons DESTINATION Mod/Spring/Gui/Resources)
