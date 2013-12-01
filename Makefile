.PHONY: default all clean superclean

bundle_expak := true
bundle_pkg_resources := true

unar := unar -q
zip := zip -q
curl := curl

utils := ffmpeg sox

win_utils := $(addsuffix .exe,$(addprefix util/win/,$(utils)))
mac_utils := $(addprefix util/mac/,$(utils))


# must begin with "ffmpeg-"
ffmpeg_win_dist := ffmpeg-20131123-git-638d79a-win32-static.7z
ffmpeg_win_url := http://ffmpeg.zeranoe.com/builds/win32/static/$(ffmpeg_win_dist)
ffmpeg_win_exe := ffmpeg-20131123-git-638d79a-win32-static/bin/ffmpeg.exe
ffmpeg_win_txt := ffmpeg: FFmpeg (www.ffmpeg.org) 32-bit build 20131123 for Windows, from ffmpeg.zeranoe.com

# must begin with "sox-"
sox_win_dist := sox-14.4.1a-win32.zip
sox_win_url := http://softlayer-dal.dl.sourceforge.net/project/sox/sox/14.4.1/$(sox_win_dist)
sox_win_exe := sox-14.4.1/sox.exe
sox_win_txt := sox: SoX 32-bit version 14.4.1a for Windows, from sox.sourceforge.net
# Supporting the extra files this way is bogus -- the file is generated if and
# only if the associated exe is. Need better makefile mojo.
sox_win_extras := sox-14.4.1/zlib1.dll

ffmpeg_mac_dist_src := SnowLeopard_Lion_Mountain_Lion_Mavericks_04.11.2013.zip
# must begin with "ffmpeg-"
ffmpeg_mac_dist := ffmpeg-$(ffmpeg_mac_dist_src)
ffmpeg_mac_url := http://ffmpegmac.net/resources/$(ffmpeg_mac_dist_src)
ffmpeg_mac_exe := ffmpeg
ffmpeg_mac_txt := ffmpeg: FFmpeg (www.ffmpeg.org) 64-bit build 04.11.2013 for OS X, from ffmpegmac.net

# must begin with "sox-"
sox_mac_dist := sox-14.4.1-macosx.zip
sox_mac_url := http://softlayer-dal.dl.sourceforge.net/project/sox/sox/14.4.1/$(sox_mac_dist)
sox_mac_exe := sox-14.4.1/sox
sox_mac_txt := sox: SoX 32-bit version 14.4.1 for OS X, from sox.sourceforge.net


sources := $(shell find quakesounds_src -type f)

win_util_dists := $(addprefix util_dists/win/,$(foreach dist,$(addsuffix _win_dist, $(utils)),$($(dist))))
mac_util_dists := $(addprefix util_dists/mac/,$(foreach dist,$(addsuffix _mac_dist, $(utils)),$($(dist))))

empty :=
space := $(empty) $(empty)


.SECONDEXPANSION:

.PRECIOUS: $(win_util_dists) $(mac_util_dists) $(win_utils) $(mac_utils)


default: all

util/win/%.exe: util_dists/win/$$(%_win_dist)
	@echo "Extracting $@"
	$(eval util := $(basename $(@F)))
	@mkdir -p util_staging
	@$(unar) -o util_staging $<
	@mkdir -p util/win
	@cp util_staging/$($(util)_win_exe) $@
	@if [ -n "$($(util)_win_extras)" ]; then cp util_staging/$($(util)_win_extras) $(@D); fi
	@echo $($(util)_win_txt) > util/win/$(util)_info.txt
	@echo $(util).exe > util/win/$(util)_exename.txt
	@rm -rf util_staging

util/mac/%: util_dists/mac/$$(%_mac_dist)
	@echo "Extracting $@"
	$(eval util := $(basename $(@F)))
	@mkdir -p util_staging
	@$(unar) -o util_staging $<
	@mkdir -p util/mac
	@cp util_staging/$($(util)_mac_exe) $@
	@if [ -n "$($(util)_mac_extras)" ]; then cp util_staging/$($(util)_mac_extras) $(@D); fi
	@echo $($(util)_mac_txt) > util/mac/$(util)_info.txt
	@rm -rf util_staging

util_dists/win/%:
	@echo "Downloading $@"
	$(eval util := $(word 1,$(subst -,$(space),$(@F))))
	@mkdir -p util_dists/win
	@$(curl) $($(util)_win_url) -o $@

util_dists/mac/%:
	@echo "Downloading $@"
	$(eval util := $(word 1,$(subst -,$(space),$(@F))))
	@mkdir -p util_dists/mac
	@$(curl) $($(util)_mac_url) -o $@

build/%/quakesounds.py: $$(%_utils) $(sources)
	@echo "Building $@"
	@rm -rf build/$*
	@mkdir -p build/$*
	@cp -r quakesounds_src build/$*/
	@if $(bundle_expak); then cp bundled_modules/expak.py build/$*/quakesounds_src/; fi
	@if $(bundle_pkg_resources); then cp bundled_modules/pkg_resources.py build/$*/quakesounds_src/; fi
	@-cp util/$*/* build/$*/quakesounds_src/res/
	@cd build/$*/quakesounds_src; $(zip) -r ../quakesounds.zip *
	@echo '#!/usr/bin/env python' | cat - build/$*/quakesounds.zip > build/$*/quakesounds.py
	@chmod +x build/$*/quakesounds.py
	@rm build/$*/quakesounds.zip
	@rm -rf build/$*/quakesounds_src

all: build/noarch/quakesounds.py build/win/quakesounds.py build/mac/quakesounds.py

clean:
	rm -rf build

superclean: clean
	rm -rf util_staging
	rm -rf util_dists
	rm -rf util
