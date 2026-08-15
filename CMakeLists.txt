cmake_minimum_required(VERSION 3.20)
project(icpc_2026_huawei_challenge LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS ON)
option(CHALLENGE_ENABLE_SANITIZERS "Enable AddressSanitizer and UBSan" OFF)

add_executable(solver src/main.cpp)
target_include_directories(solver PRIVATE include)

add_library(xr2023
  practice/xr2023/src/oracle.cpp
  practice/xr2023/src/xr.cpp
)
target_include_directories(xr2023 PUBLIC practice/xr2023/include)

add_executable(xr_solver practice/xr2023/src/solver_main.cpp)
target_link_libraries(xr_solver PRIVATE xr2023)

add_executable(xr_scorer practice/xr2023/src/scorer_main.cpp)
target_link_libraries(xr_scorer PRIVATE xr2023)

add_executable(xr_generator practice/xr2023/src/generator_main.cpp)
target_link_libraries(xr_generator PRIVATE xr2023)

add_executable(xr_oracle practice/xr2023/src/oracle_main.cpp)
target_link_libraries(xr_oracle PRIVATE xr2023)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(solver PRIVATE
    -Wall -Wextra -Wshadow -Wconversion -Wpedantic
  )
  if(CHALLENGE_ENABLE_SANITIZERS)
    target_compile_options(solver PRIVATE
      -fsanitize=address,undefined -fno-omit-frame-pointer
    )
    target_link_options(solver PRIVATE -fsanitize=address,undefined)
  endif()
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(foundation_test tests/foundation_test.cpp)
  target_include_directories(foundation_test PRIVATE include)
  if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(foundation_test PRIVATE
      -Wall -Wextra -Wshadow -Wconversion -Wpedantic
    )
    if(CHALLENGE_ENABLE_SANITIZERS)
      target_compile_options(foundation_test PRIVATE
        -fsanitize=address,undefined -fno-omit-frame-pointer
      )
      target_link_options(foundation_test PRIVATE -fsanitize=address,undefined)
    endif()
  endif()
  add_test(NAME foundation_test COMMAND foundation_test)

  add_executable(xr2023_test practice/xr2023/tests/xr_test.cpp)
  target_link_libraries(xr2023_test PRIVATE xr2023)
  target_compile_definitions(xr2023_test PRIVATE
    XR2023_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/practice/xr2023/data"
  )
  add_test(NAME xr2023_test COMMAND xr2023_test)
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  foreach(target xr2023 xr_solver xr_scorer xr_generator xr_oracle)
    target_compile_options(${target} PRIVATE
      -Wall -Wextra -Wshadow -Wconversion -Wpedantic
    )
    if(CHALLENGE_ENABLE_SANITIZERS)
      target_compile_options(${target} PRIVATE
        -fsanitize=address,undefined -fno-omit-frame-pointer
      )
      target_link_options(${target} PRIVATE -fsanitize=address,undefined)
    endif()
  endforeach()
  if(BUILD_TESTING)
    target_compile_options(xr2023_test PRIVATE
      -Wall -Wextra -Wshadow -Wconversion -Wpedantic
    )
    if(CHALLENGE_ENABLE_SANITIZERS)
      target_compile_options(xr2023_test PRIVATE
        -fsanitize=address,undefined -fno-omit-frame-pointer
      )
      target_link_options(xr2023_test PRIVATE -fsanitize=address,undefined)
    endif()
  endif()
endif()
