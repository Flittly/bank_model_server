cmake_minimum_required(VERSION 3.20)
project(TextureBuilder)

# Set C++ standard and ABI
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Print compiler information
message(STATUS "C Compiler: ${CMAKE_C_COMPILER}")
message(STATUS "CXX Compiler: ${CMAKE_CXX_COMPILER}")

# Include directories and libraries for third-party dependencies
add_subdirectory(${CMAKE_SOURCE_DIR}/thirdparty/json)
include_directories(
    ${CMAKE_SOURCE_DIR}/thirdparty/stb/include
    ${CMAKE_SOURCE_DIR}/thirdparty/quikgrid/include
    ${CMAKE_SOURCE_DIR}/thirdparty/json/include
)

# Add third-party libraries
add_library(stb ${CMAKE_SOURCE_DIR}/thirdparty/stb/stb_image.cpp)
add_library(quikgrid
    ${CMAKE_SOURCE_DIR}/thirdparty/quikgrid/contour.cpp
    ${CMAKE_SOURCE_DIR}/thirdparty/quikgrid/gridxtyp.cpp
    ${CMAKE_SOURCE_DIR}/thirdparty/quikgrid/scatdata.cpp
    ${CMAKE_SOURCE_DIR}/thirdparty/quikgrid/surfgrid.cpp
    ${CMAKE_SOURCE_DIR}/thirdparty/quikgrid/xpand.cpp
)

# Collect libraries
list(APPEND LIBS
    stb
    quikgrid
    nlohmann_json::nlohmann_json
)

# Detect platform and configure GDAL and PROJ accordingly
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    # macOS specific configuration for PROJ and GDAL
    find_package(PROJ REQUIRED CONFIG)
    find_package(GDAL REQUIRED)

    list(APPEND LIBS PROJ::proj GDAL::GDAL)
else()
    # Linux specific configuration for PROJ and GDAL

    # Using Conda environment for compiler
    if(DEFINED ENV{CONDA_PREFIX})
        set(CMAKE_C_COMPILER $ENV{CONDA_PREFIX}/bin/x86_64-conda-linux-gnu-gcc CACHE PATH "C compiler")
        set(CMAKE_CXX_COMPILER $ENV{CONDA_PREFIX}/bin/x86_64-conda-linux-gnu-g++ CACHE PATH "CXX compiler")
    endif()

    # Function to find GDAL and PROJ paths dynamically
    function(find_gdal_and_proj)
        # Find gdal-config executable
        find_program(GDAL_CONFIG_EXECUTABLE gdal-config)
        if (NOT GDAL_CONFIG_EXECUTABLE)
            message(FATAL_ERROR "gdal-config not found")
        endif()

        # Use gdal-config to find GDAL prefix path
        execute_process(
            COMMAND ${GDAL_CONFIG_EXECUTABLE} --prefix
            OUTPUT_VARIABLE GDAL_PREFIX
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        message(STATUS "GDAL_PREFIX: ${GDAL_PREFIX}")

        # Set GDAL include and library paths
        find_path(GDAL_INCLUDE_DIR gdal.h PATHS ${GDAL_PREFIX}/include)
        find_library(GDAL_LIBRARY gdal PATHS ${GDAL_PREFIX}/lib)
        message(STATUS "GDAL include dir: ${GDAL_INCLUDE_DIR}")
        message(STATUS "GDAL library: ${GDAL_LIBRARY}")

        # Find proj executable
        find_program(PROJ_EXECUTABLE proj)
        if (NOT PROJ_EXECUTABLE)
            message(FATAL_ERROR "proj not found")
        endif()

        # Use proj command to find PROJ version
        execute_process(
            COMMAND ${PROJ_EXECUTABLE} --version
            OUTPUT_VARIABLE PROJ_VERSION
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        message(STATUS "PROJ_VERSION: ${PROJ_VERSION}")

        # Set PROJ include and library paths
        find_path(PROJ_INCLUDE_DIR proj.h PATHS ${GDAL_PREFIX}/include $ENV{CONDA_PREFIX}/include)
        find_library(PROJ_LIBRARY proj PATHS ${GDAL_PREFIX}/lib $ENV{CONDA_PREFIX}/lib)
        message(STATUS "PROJ include dir: ${PROJ_INCLUDE_DIR}")
        message(STATUS "PROJ library: ${PROJ_LIBRARY}")

        # Set GDAL and PROJ include and library paths
        set(GDAL_INCLUDE_DIRS ${GDAL_INCLUDE_DIR} PARENT_SCOPE)
        set(GDAL_LIBRARIES ${GDAL_LIBRARY} PARENT_SCOPE)
        set(PROJ_INCLUDE_DIRS ${PROJ_INCLUDE_DIR} PARENT_SCOPE)
        set(PROJ_LIBRARIES ${PROJ_LIBRARY} PARENT_SCOPE)
    endfunction()

    # Call the function to find GDAL and PROJ paths
    find_gdal_and_proj()

    # Include GDAL and PROJ directories
    include_directories(${GDAL_INCLUDE_DIRS} ${PROJ_INCLUDE_DIRS})

    # Add GDAL and PROJ libraries to the list
    list(APPEND LIBS ${GDAL_LIBRARIES} ${PROJ_LIBRARIES})
endif()

# Define the executable
aux_source_directory(${CMAKE_SOURCE_DIR}/src SRC_FILES)
add_executable(${PROJECT_NAME} ${SRC_FILES} source/main.cpp source/cesium_cartesian3.cpp source/FlowField.cpp)

# Define the include directories
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

# Define the link libraries
target_link_libraries(${PROJECT_NAME} PRIVATE ${LIBS} stdc++)
