# Build helper for the FreeCAD Spring workbench hybrid Python/C++ module

BUILD_DIR ?= build
GENERATOR ?=
CMAKE ?= cmake
PYTHON ?= python3

# Additional flags to hand to CMake during configuration
CMAKE_ARGS ?=
EXTRA_CMAKE_ARGS ?=

PLATFORMS := linux linux-aarch64 macos windows

.PHONY: all clean $(addprefix configure-,$(PLATFORMS)) $(addprefix build-,$(PLATFORMS)) $(addprefix stage-,$(PLATFORMS))

all: build-macos

define CONFIGURE_template
configure-$(1):
	$(CMAKE) -S src -B $(BUILD_DIR)/$(1) $(GENERATOR) $(CMAKE_ARGS) $(EXTRA_CMAKE_ARGS) -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE="$(PYTHON)" -DSPRING_TARGET_PLATFORM=$(1)

build-$(1): configure-$(1)
	$(CMAKE) --build $(BUILD_DIR)/$(1) --config Release
endef

$(foreach plat,$(PLATFORMS),$(eval $(call CONFIGURE_template,$(plat))))

define STAGE_template
stage-$(1): build-$(1)
	@$(PYTHON) scripts/stage_artifacts.py "$(BUILD_DIR)" "$(1)"
endef

$(foreach plat,$(PLATFORMS),$(eval $(call STAGE_template,$(plat))))

clean:
	rm -rf $(BUILD_DIR)
