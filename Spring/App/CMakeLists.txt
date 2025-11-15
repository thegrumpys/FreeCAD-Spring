set(SpringApp_SRCS
    SpringModule.cpp
    SpringFeature.cpp
    CompressionSpringFeature.cpp
    ExtensionSpringFeature.cpp
    TorsionSpringFeature.cpp
)

set(SpringApp_HDRS
    SpringModule.h
    SpringFeature.h
    CompressionSpringFeature.h
    ExtensionSpringFeature.h
    TorsionSpringFeature.h
)

add_library(SpringApp SHARED ${SpringApp_SRCS} ${SpringApp_HDRS})

set_target_properties(SpringApp PROPERTIES PREFIX "")

target_link_libraries(SpringApp PUBLIC FreeCADApp FreeCADPart)

target_include_directories(SpringApp
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
)

foreach(_occ_var OCC_INCLUDE_DIR OCC_INCLUDE_DIRS OpenCASCADE_INCLUDE_DIR OpenCASCADE_INCLUDE_DIRS)
    if(DEFINED ${_occ_var})
        target_include_directories(SpringApp PRIVATE ${${_occ_var}})
    endif()
endforeach()

install(TARGETS SpringApp DESTINATION ${CMAKE_INSTALL_LIBDIR}/Mod/Spring)
install(FILES ${SpringApp_HDRS} DESTINATION include/Mod/Spring/App)
