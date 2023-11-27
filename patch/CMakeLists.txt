cmake_minimum_required(VERSION 3.16)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

add_compile_options(
  /std:c++17
  /MP
  /wd4018 
  /wd4819 
  /wd4244
  /wd4267
  /DVERSION="${VERSION}"
  /DUNICODE 
  /D_UNICODE
)
project(patch)


add_executable(loader loader.cpp) 

include_directories(.)
include_directories(lib)
add_library(patch MODULE patch.cpp  lib/InlineHook.c lib/LDasm.c)  

target_link_libraries(patch )


# include_directories(lib/minhook/include)
# add_library(patch MODULE patch.cpp ) 

# target_link_libraries(patch minhook )