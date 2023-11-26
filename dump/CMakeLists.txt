cmake_minimum_required(VERSION 3.16)

project(dump)


add_executable(injector injector.cpp) 

include_directories(.)
add_library(dumper MODULE dumper.cpp  ) 

target_link_libraries(dumper )