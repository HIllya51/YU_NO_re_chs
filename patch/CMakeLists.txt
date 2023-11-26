cmake_minimum_required(VERSION 3.16)

project(patch)


add_executable(loader loader.cpp) 

include_directories(.)
include_directories(lib)
add_library(patch MODULE patch.cpp  lib/InlineHook.c lib/LDasm.c)  

target_link_libraries(patch )


# include_directories(lib/minhook/include)
# add_library(patch MODULE patch.cpp ) 

# target_link_libraries(patch minhook )