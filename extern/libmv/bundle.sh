#!/bin/sh

#BRANCH="keir"
#BRANCH="Matthias-Fauconneau"
BRANCH="Nazg-Gul"

if [ -d ./.svn ]; then
  echo "This script is supposed to work only when using git-svn"
  exit 1
fi

repo="git://github.com/${BRANCH}/libmv.git"
tmp=`mktemp -d`

git clone $repo $tmp/libmv

#git --git-dir $tmp/libmv/.git --work-tree $tmp/libmv log --since="1 month ago" > ChangeLog
git --git-dir $tmp/libmv/.git --work-tree $tmp/libmv log -n 50 > ChangeLog

for p in `cat ./patches/series`; do
  echo "Applying patch $p..."
  cat ./patches/$p | patch -d $tmp/libmv -p1
done

rm -rf libmv
rm -rf third_party

cat "files.txt" | while read f; do
  mkdir -p `dirname $f`
  cp $tmp/libmv/src/$f $f
done

rm -rf $tmp

chmod 664 ./third_party/glog/src/windows/*.cc ./third_party/glog/src/windows/*.h ./third_party/glog/src/windows/glog/*.h

sources=`find ./libmv -type f -iname '*.cc' -or -iname '*.cpp' -or -iname '*.c' | sed -r 's/^\.\//\t/' | sort -d`
headers=`find ./libmv -type f -iname '*.h' | sed -r 's/^\.\//\t/' | sort -d`

third_sources=`find ./third_party -type f -iname '*.cc' -or -iname '*.cpp' -or -iname '*.c' | grep -v glog | sed -r 's/^\.\//\t/' | sort -d`
third_headers=`find ./third_party -type f -iname '*.h' | grep -v glog | sed -r 's/^\.\//\t/' | sort -d`

third_glog_sources=`find ./third_party -type f -iname '*.cc' -or -iname '*.cpp' -or -iname '*.c' | grep glog | grep -v windows | sed -r 's/^\.\//\t\t/' | sort -d`
third_glog_headers=`find ./third_party -type f -iname '*.h' | grep glog | grep -v windows | sed -r 's/^\.\//\t\t/' | sort -d`

src_dir=`find ./libmv -type f -iname '*.cc' -exec dirname {} \; -or -iname '*.cpp' -exec dirname {} \; -or -iname '*.c' -exec dirname {} \; | sed -r 's/^\.\//\t/' | sort -d | uniq`
src_third_dir=`find ./third_party -type f -iname '*.cc' -exec dirname {} \; -or -iname '*.cpp' -exec dirname {} \; -or -iname '*.c' -exec dirname {} \; | sed -r 's/^\.\//\t/'  | sort -d | uniq`
src=""
win_src=""
for x in $src_dir $src_third_dir; do
  t=""

  if test  `echo "$x" | grep -c glog ` -eq 1; then
    continue;
  fi

  if stat $x/*.cpp > /dev/null 2>&1; then
    t="src += env.Glob('`echo $x'/*.cpp'`')"
  fi

  if stat $x/*.c > /dev/null 2>&1; then
    if [ -z "$t" ]; then
      t="src += env.Glob('`echo $x'/*.c'`')"
    else
      t="$t + env.Glob('`echo $x'/*.c'`')"
    fi
  fi

  if stat $x/*.cc > /dev/null 2>&1; then
    if [ -z "$t" ]; then
      t="src += env.Glob('`echo $x'/*.cc'`')"
    else
      t="$t + env.Glob('`echo $x'/*.cc'`')"
    fi
  fi

  if test `echo $x | grep -c windows ` -eq 0; then
    if [ -z "$src" ]; then
      src=$t
    else
      src=`echo "$src\n$t"`
    fi
  else
    if [ -z "$win_src" ]; then
      win_src=`echo "    $t"`
    else
      win_src=`echo "$win_src\n    $t"`
    fi
  fi
done

cat > CMakeLists.txt << EOF
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# The Original Code is Copyright (C) 2011, Blender Foundation
# All rights reserved.
#
# Contributor(s): Blender Foundation,
#                 Sergey Sharybin
#
# ***** END GPL LICENSE BLOCK *****

# NOTE: This file is automatically generated by bundle.sh script
#       If you're doing changes in this file, please update template
#       in that script too

set(INC
	.
	../Eigen3
	third_party/ssba
	third_party/ldl/Include
	../colamd/Include
)

set(INC_SYS
	\${PNG_INCLUDE_DIR}
	\${ZLIB_INCLUDE_DIRS}
)


# XXX - FIXME
# this is a momentary hack to find unwind.h in 10.6.sdk
if(APPLE)
	if(\${CMAKE_OSX_DEPLOYMENT_TARGET} STREQUAL "10.6")
		list(APPEND INC_SYS
			\${CMAKE_OSX_SYSROOT}/Developer/usr/llvm-gcc-4.2/lib/gcc/i686-apple-darwin10/4.2.1/include
		)
	endif()
endif()
# XXX - END


set(SRC
	libmv-capi.cpp
${sources}

${third_sources}

	libmv-capi.h
${headers}

${third_headers}
)

if(WIN32)
	list(APPEND SRC
		third_party/glog/src/logging.cc
		third_party/glog/src/raw_logging.cc
		third_party/glog/src/utilities.cc
		third_party/glog/src/vlog_is_on.cc
		third_party/glog/src/windows/port.cc

		third_party/glog/src/utilities.h
		third_party/glog/src/stacktrace_generic-inl.h
		third_party/glog/src/stacktrace.h
		third_party/glog/src/stacktrace_x86_64-inl.h
		third_party/glog/src/base/googleinit.h
		third_party/glog/src/base/mutex.h
		third_party/glog/src/base/commandlineflags.h
		third_party/glog/src/stacktrace_powerpc-inl.h
		third_party/glog/src/stacktrace_x86-inl.h
		third_party/glog/src/config.h
		third_party/glog/src/stacktrace_libunwind-inl.h
		third_party/glog/src/windows/glog/raw_logging.h
		third_party/glog/src/windows/glog/vlog_is_on.h
		third_party/glog/src/windows/glog/logging.h
		third_party/glog/src/windows/glog/log_severity.h
		third_party/glog/src/windows/port.h
		third_party/glog/src/windows/config.h
	)

	list(APPEND INC
		third_party/glog/src/windows
	)

	if(NOT MINGW)
		list(APPEND INC
			third_party/msinttypes
		)
	endif()

	if(MSVC)
		set(MSVC_OFLAGS O1 O2 Ox)
		foreach(FLAG \${MSVC_OFLAGS})
			string(REPLACE "\${FLAG}" "Od" CMAKE_CXX_FLAGS_RELEASE "\${CMAKE_CXX_FLAGS_RELEASE}")
			string(REPLACE "\${FLAG}" "Od" CMAKE_C_FLAGS_RELWITHDEBINFO "\${CMAKE_C_FLAGS_RELWITHDEBINFO}")
		endforeach()
	endif()
else()
	list(APPEND SRC
${third_glog_sources}

${third_glog_headers}
	)

	list(APPEND INC
		third_party/glog/src
	)
endif()

add_definitions(
	-DV3DLIB_ENABLE_SUITESPARSE
	-DGOOGLE_GLOG_DLL_DECL=
)

blender_add_lib(extern_libmv "\${SRC}" "\${INC}" "\${INC_SYS}")
EOF

cat > SConscript << EOF
#!/usr/bin/python

# NOTE: This file is automatically generated by bundle.sh script
#       If you're doing changes in this file, please update template
#       in that script too

import sys
import os

Import('env')

defs = []

cflags_libmv = Split(env['CFLAGS'])
ccflags_libmv = Split(env['CCFLAGS'])
cxxflags_libmv = Split(env['CXXFLAGS'])

defs.append('V3DLIB_ENABLE_SUITESPARSE')
defs.append('GOOGLE_GLOG_DLL_DECL=')

src = env.Glob("*.cpp")
$src

incs = '. ../Eigen3'
incs += ' ' + env['BF_PNG_INC']
incs += ' ' + env['BF_ZLIB_INC']

if env['OURPLATFORM'] in ('win32-vc', 'win32-mingw', 'linuxcross', 'win64-vc', 'win64-mingw'):
    incs += ' ./third_party/glog/src/windows ./third_party/glog/src/windows/glog'
    if env['OURPLATFORM'] in ('win32-vc', 'win64-vc'):
        incs += ' ./third_party/msinttypes'
${win_src}
    src += ['./third_party/glog/src/logging.cc', './third_party/glog/src/raw_logging.cc', './third_party/glog/src/utilities.cc', './third_party/glog/src/vlog_is_on.cc']
    src += ['./third_party/glog/src/windows/port.cc']

    if env['OURPLATFORM'] in ('win32-vc', 'win64-vc'):
        cflags_libmv.append('/Od')
        ccflags_libmv.append('/Od')
        cxxflags_libmv.append('/Od')

        if not env['BF_DEBUG']:
            defs.append('NDEBUG')
    else:
        if not env['BF_DEBUG']:
            cflags_libmv += Split(env['REL_CFLAGS'])
            ccflags_libmv += Split(env['REL_CCFLAGS'])
            cxxflags_libmv += Split(env['REL_CXXFLAGS'])
else:
    src += env.Glob("third_party/glog/src/*.cc")
    incs += ' ./third_party/glog/src'
    if not env['BF_DEBUG']:
        cflags_libmv += Split(env['REL_CFLAGS'])
        ccflags_libmv += Split(env['REL_CCFLAGS'])
        cxxflags_libmv += Split(env['REL_CXXFLAGS'])

incs += ' ./third_party/ssba ./third_party/ldl/Include ../colamd/Include'

env.BlenderLib ( libname = 'extern_libmv', sources=src, includes=Split(incs), defines=defs, libtype=['extern', 'player'], priority=[20,137], compileflags=cflags_libmv, cc_compileflags=ccflags_libmv, cxx_compileflags=cxxflags_libmv )
EOF
