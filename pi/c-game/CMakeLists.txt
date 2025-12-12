cmake_minimum_required(VERSION 3.11)
project(c-raylib-test)

include(FetchContent)

# Generate compile_commands.json
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Dependencies
set(RAYLIB_VERSION 5.5)

FetchContent_Declare(
    raylib
    URL "https://github.com/raysan5/raylib/archive/refs/tags/${RAYLIB_VERSION}.tar.gz"
)

#FetchContent_MakeAvailable(raylib)
#set(ENV{PKG_CONFIG_PATH} "/usr/local/lib/arm-linux-gnueabihf/pkgconfig:$ENV{PKG_CONFIG_PATH}")
#find_package(PkgConfig REQUIRED)
#pkg_check_modules(RAYLIB REQUIRED RAYLIB)

# Find header
find_path(RAYLIB_INCLUDE_DIR
    NAMES raylib.h
    PATHS
        /usr/local/include
        /usr/include
)

# Find library
find_library(RAYLIB_LIBRARY
    NAMES raylib
    PATHS
        /usr/local/lib
        /usr/local/lib/arm-linux-gnueabihf
        /usr/lib/arm-linux-gnueabihf
        /usr/lib
)

message(STATUS "RAYLIB_INCLUDE_DIR = ${RAYLIB_INCLUDE_DIR}")
message(STATUS "RAYLIB_LIBRARY     = ${RAYLIB_LIBRARY}")

if (NOT RAYLIB_INCLUDE_DIR OR NOT RAYLIB_LIBRARY)
    message(FATAL_ERROR "Could not find raylib. Check raylib install paths.")
endif()


# Our Project
add_executable(${PROJECT_NAME})
add_subdirectory(src)

set_target_properties(${PROJECT_NAME} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/${PROJECT_NAME})

set_property(TARGET ${PROJECT_NAME} PROPERTY VS_DEBUGGER_WORKING_DIRECTORY $<TARGET_FILE_DIR:${PROJECT_NAME}>)

if ("${PLATFORM}" STREQUAL "Web")
    add_custom_command(
        TARGET ${PROJECT_NAME} PRE_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/src/resources $<TARGET_FILE_DIR:${PROJECT_NAME}>/../resources
    )
    #DEPENDS ${PROJECT_NAME}
else()
    add_custom_command(
        TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/src/resources $<TARGET_FILE_DIR:${PROJECT_NAME}>/resources
    )
    #DEPENDS ${PROJECT_NAME}
endif()

#set(raylib_VERBOSE 1)
#target_link_libraries(${PROJECT_NAME} raylib atomic)

target_include_directories(${PROJECT_NAME} PRIVATE ${RAYLIB_INCLUDE_DIR})
target_link_libraries(${PROJECT_NAME} PRIVATE
    ${RAYLIB_LIBRARY}
    m          # libm  - math functions: sin, cos, sqrt, pow, etc.
    dl         # libdl - dlopen/dlsym/dlclose
    pthread    # libpthread - threads used by miniaudio & glfw
    atomic     # libatomic - __atomic_* on 32-bit ARM
)

set(OPENGL_VERSION "2.1")
set (GRAPHICS GRAPHICS_API_OPENGL_21)

# Web Configurations
if ("${PLATFORM}" STREQUAL "Web")
    # Tell Emscripten to build an example.html file.
    set_target_properties(${PROJECT_NAME} PROPERTIES SUFFIX ".html")
    target_link_options(${PROJECT_NAME} PUBLIC -sUSE_GLFW=3 PUBLIC --preload-file resources)
endif()

# Checks if OSX and links appropriate frameworks (Only required on MacOS)
if (APPLE)
    target_link_libraries(${PROJECT_NAME} "-framework IOKit")
    target_link_libraries(${PROJECT_NAME} "-framework Cocoa")
    target_link_libraries(${PROJECT_NAME} "-framework OpenGL")
endif()

target_compile_definitions(${PROJECT_NAME} PRIVATE
    $<$<CONFIG:Debug>:_DEBUG>
)
